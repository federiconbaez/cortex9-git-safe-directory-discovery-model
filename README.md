# cortex9-git-safe-directory-discovery-model

[Español](README.es.md) · [Practice guide](PRACTICE.md)

An in-memory Python model of how git discovers a repository by walking up
from the current directory, and of the ownership check (`safe.directory`)
added for CVE-2022-24765. It compares three modes: before the fix, the fix
in commit 8959555, and the `*` value added in commit 0f85c4a.

**This is a model, not git, and not a reproduction of CVE-2022-24765.** It
never runs git, never touches the real filesystem and never executes or
evaluates configuration values. A repository config is only scanned for the
*names* of documented command-valued keys, reported as data. See
[LIMITATIONS.md](LIMITATIONS.md).

## What is modelled, and from where

| Element | Source | Code |
|---|---|---|
| Walk up: check `<dir>/.git` (directory or `gitdir:` file), then `<dir>` as a bare repo; stop at ceiling and mount point | git v2.35.2 `setup.c`, `setup_git_directory_gently_1` | `discover` |
| Ceiling = longest *proper* ancestor in `GIT_CEILING_DIRECTORIES`; the ceiling dir itself is not checked; cwd always is | same function, `longest_ancestor_length` use | `longest_ancestor_length` |
| `GIT_DIR` set → `GIT_DIR_EXPLICIT` before any ownership check | same function | `Env.git_dir` |
| `ensure_valid_ownership(dir)`: owned by current uid → OK; else read system + global config only | commit 8959555 `setup.c`; v2.35.2 `config.c` `read_very_early_config` (`ignore_repo`, `ignore_worktree`, `ignore_cmdline`) | `ensure_valid_ownership` |
| `safe_directory_cb`: empty value resets to unsafe; value equal (after `~/`, `%(prefix)/` interpolation) marks safe; last relevant value wins | commit 8959555 | same |
| Only the directory containing `.git` (or the bare dir) is checked, not intermediate dirs | commit 8959555 (calls only at those two sites) | scenario 14 |
| `*` marks every directory safe; an empty value afterwards re-enables the check | commit 0f85c4a | mode `fix_0f85c4a` |
| The threat: another user's `C:\.git`, mounted drive or scratch space picked up by a Git-aware prompt | git 2.30.3 release notes | scenario 02 |

## Run

```sh
python3 -m venv .venv && . .venv/bin/activate   # optional
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m git_safedir_model fixtures/scenarios/02_foreign_parent_repo.json
python3 scripts/gen_results.py /tmp/out && diff -r results /tmp/out
```

## Results (from `results/`)

- 02: before the fix, the walk from `/tmp/alice-work` reaches Bob's
  `/tmp/.git` and its config (with a `core.fsmonitor` key) would be parsed;
  both fixed modes return `invalid_ownership` and parse nothing.
- 04/05: listing a directory in the repo's own config or with `-c` has no
  effect; the model reports those sources as ignored.
- 06/08: an empty value resets; `*` works only with 0f85c4a (07).
- 10: `/srv/shared/` ≠ `/srv/shared` under exact comparison.
- 14: a repo you own inside a directory you don't own is accepted (only the
  top-level dir is checked).
- 15: `GIT_DIR` bypasses discovery and the check in this code path.

Licence: Apache-2.0.
