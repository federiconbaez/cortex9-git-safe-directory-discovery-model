"""Discovery loop and ownership check, mapped to git v2.35.2 setup.c.

Modes:
  pre_fix     - no ownership check (behaviour before commit 8959555)
  fix_8959555 - ensure_valid_ownership; empty value resets; exact path match
  fix_0f85c4a - as above, plus ``*`` marks every directory safe
"""
from __future__ import annotations

import posixpath
from dataclasses import asdict, dataclass, field

from .fs import MemFS, is_git_directory, join, read_gitfile

MODES = ("pre_fix", "fix_8959555", "fix_0f85c4a")

# Documented config keys whose value is a command. Reported as data only.
COMMAND_VALUED_KEYS = ("core.fsmonitor", "core.pager", "core.editor", "core.sshcommand", "core.hookspath")


@dataclass
class Env:
    uid: int
    home: str = "/home/user"
    prefix: str = "/usr"
    ceilings: list[str] = field(default_factory=list)
    git_dir: str | None = None
    across_filesystem: bool = False
    # config scopes: lists of safe.directory values in file order
    system: list[str] = field(default_factory=list)
    global_: list[str] = field(default_factory=list)
    cmdline: list[str] = field(default_factory=list)


@dataclass
class Result:
    kind: str  # discovered, bare, explicit, invalid_ownership, hit_ceiling, hit_mount_point, none
    worktree_or_dir: str | None
    gitdir: str | None
    ownership: str | None  # owned, safe_listed, rejected, not_checked
    safe_trace: list[str]
    visited: list[str]
    repo_config_parsed: bool
    command_valued_keys_in_repo_config: list[str]
    ignored_safe_directory_sources: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def interpolate(value: str, env: Env) -> str | None:
    """git_config_pathname: ``~/`` and ``%(prefix)/``. ``~user/`` is not modelled."""
    if value.startswith("~/"):
        return env.home.rstrip("/") + value[1:]
    if value.startswith("~"):
        return None
    if value.startswith("%(prefix)/"):
        return env.prefix.rstrip("/") + value[len("%(prefix)"):]
    return value


def ensure_valid_ownership(fs: MemFS, path: str, env: Env, mode: str, trace: list[str]) -> tuple[bool, str]:
    node = fs.get(path)
    if node is not None and node.owner == env.uid:
        trace.append(f"owner uid {node.owner} == current uid")
        return True, "owned"
    is_safe = False
    # read_very_early_config: system then global; repo, worktree and
    # command-line config are ignored (opts.ignore_cmdline = 1).
    for scope, values in (("system", env.system), ("global", env.global_)):
        for v in values:
            if v == "":
                is_safe = False
                trace.append(f"{scope}: '' -> reset")
            elif v == "*" and mode == "fix_0f85c4a":
                is_safe = True
                trace.append(f"{scope}: '*' -> safe")
            else:
                interp = interpolate(v, env)
                if interp is None:
                    trace.append(f"{scope}: {v!r} -> not interpolated by this model")
                elif interp == path:  # fspathcmp; ignore_case is not yet read here
                    is_safe = True
                    trace.append(f"{scope}: {v!r} -> match")
                else:
                    trace.append(f"{scope}: {v!r} -> no match")
    return is_safe, "safe_listed" if is_safe else "rejected"


def longest_ancestor_length(path: str, ceilings: list[str]) -> int:
    """Length of the longest ceiling that is a proper ancestor of path, else -1."""
    best = -1
    for c in ceilings:
        if not c.startswith("/"):
            continue  # canonicalize_ceiling_entry drops relative entries
        c = MemFS.norm(c)
        if c == path or c == "/":
            continue
        if path.startswith(c + "/"):
            best = max(best, len(c))
    return best


def _repo_config(fs: MemFS, gitdir: str) -> list[str]:
    n = fs.get(join(gitdir, "config"))
    if n is None or n.kind != "file":
        return []
    keys, section = [], ""
    for raw in n.content.splitlines():
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
        elif "=" in line and section:
            keys.append(f"{section}.{line.split('=', 1)[0].strip().lower()}")
    return keys


def discover(fs: MemFS, cwd: str, env: Env, mode: str) -> Result:
    if mode not in MODES:
        raise ValueError(mode)
    trace: list[str] = []
    visited: list[str] = []
    ignored = ["cmdline"] if mode != "pre_fix" and env.cmdline else []
    cwd = MemFS.norm(cwd)

    def done(kind, d=None, g=None, own=None):
        """g is the candidate git dir; it is reported only if accepted."""
        parsed = kind in ("discovered", "bare", "explicit")
        cfg = _repo_config(fs, g) if g is not None else []
        keys = sorted(k for k in cfg if k in COMMAND_VALUED_KEYS) if parsed else []
        if mode != "pre_fix" and "safe.directory" in cfg:
            ignored.append("repo")
        return Result(kind, d, g if parsed else None, own, trace, visited, parsed, keys, sorted(set(ignored)))

    if env.git_dir:
        # GIT_DIR set: GIT_DIR_EXPLICIT, no ownership check at this point.
        return done("explicit", None, env.git_dir, "not_checked")

    ceil = longest_ancestor_length(cwd, env.ceilings)
    device = fs.get(cwd).device if fs.get(cwd) else None
    d = cwd
    while True:
        visited.append(d)
        dotgit = join(d, ".git")
        gitdir = None
        if fs.is_file(dotgit):
            gitdir = read_gitfile(fs, dotgit)
            if gitdir is None:
                return done("invalid_gitfile", d)
        elif is_git_directory(fs, dotgit):
            gitdir = dotgit
        if gitdir is not None:
            if mode != "pre_fix":
                ok, own = ensure_valid_ownership(fs, d, env, mode, trace)
                if not ok:
                    return done("invalid_ownership", d, gitdir, own)
            else:
                own = "not_checked"
            return done("discovered", d, gitdir, own)
        if is_git_directory(fs, d):
            if mode != "pre_fix":
                ok, own = ensure_valid_ownership(fs, d, env, mode, trace)
                if not ok:
                    return done("invalid_ownership", d, d, own)
            else:
                own = "not_checked"
            return done("bare", d, d, own)
        if d == "/":
            return done("hit_ceiling")
        parent = posixpath.dirname(d)
        if len(parent) <= ceil:
            return done("hit_ceiling")
        if not env.across_filesystem and fs.get(parent) is not None and fs.get(parent).device != device:
            return done("hit_mount_point")
        d = parent
