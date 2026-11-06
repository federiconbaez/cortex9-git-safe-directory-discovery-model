import json
import unittest
from pathlib import Path

from git_safedir_model.discovery import MODES, Env, discover, interpolate, longest_ancestor_length
from git_safedir_model.fs import MemFS
from git_safedir_model.scenario import load, run

ROOT = Path(__file__).resolve().parent.parent
SC = sorted((ROOT / "fixtures/scenarios").glob("*.json"))
EXP = json.loads((ROOT / "fixtures/expected.json").read_text())

ALICE, BOB = 1000, 1001


def fs_with_repo(path, owner):
    fs = MemFS.from_spec([])
    for p in (path, path + "/.git", path + "/.git/objects", path + "/.git/refs"):
        fs.add(p, "dir", owner)
    fs.add(path + "/.git/HEAD", "file", owner, content="ref: refs/heads/main")
    return fs


class Fixtures(unittest.TestCase):
    def test_count(self):
        self.assertEqual(len(SC), 15)

    def test_expected(self):
        for p in SC:
            sc = load(p)
            r = run(sc)
            got = [[r[m]["kind"], r[m]["ownership"]] for m in MODES]
            self.assertEqual(got, EXP[sc["name"]], sc["name"])

    def test_cli_runs(self):
        from git_safedir_model.cli import main
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(main([str(SC[0]), "--mode", "fix_8959555"]), 0)
        self.assertEqual(json.loads(buf.getvalue())["kind"], "discovered")


class Rules(unittest.TestCase):
    def test_fix_never_accepts_foreign_without_listing(self):
        fs = fs_with_repo("/srv/r", BOB)
        for m in ("fix_8959555", "fix_0f85c4a"):
            self.assertEqual(discover(fs, "/srv/r", Env(uid=ALICE), m).kind, "invalid_ownership")
        self.assertEqual(discover(fs, "/srv/r", Env(uid=ALICE), "pre_fix").kind, "discovered")

    def test_only_system_and_global_respected(self):
        fs = fs_with_repo("/srv/r", BOB)
        self.assertEqual(discover(fs, "/srv/r", Env(uid=ALICE, cmdline=["/srv/r"]), "fix_8959555").kind, "invalid_ownership")
        self.assertEqual(discover(fs, "/srv/r", Env(uid=ALICE, system=["/srv/r"]), "fix_8959555").kind, "discovered")
        self.assertEqual(discover(fs, "/srv/r", Env(uid=ALICE, global_=["/srv/r"]), "fix_8959555").kind, "discovered")

    def test_last_value_order(self):
        fs = fs_with_repo("/srv/r", BOB)
        # match then reset -> rejected; reset then match -> safe
        self.assertEqual(discover(fs, "/srv/r", Env(uid=ALICE, system=["/srv/r"], global_=[""]), "fix_8959555").kind, "invalid_ownership")
        self.assertEqual(discover(fs, "/srv/r", Env(uid=ALICE, system=[""], global_=["/srv/r"]), "fix_8959555").kind, "discovered")

    def test_star_requires_0f85c4a_and_reset_overrides(self):
        fs = fs_with_repo("/srv/r", BOB)
        self.assertEqual(discover(fs, "/srv/r", Env(uid=ALICE, system=["*"]), "fix_8959555").kind, "invalid_ownership")
        self.assertEqual(discover(fs, "/srv/r", Env(uid=ALICE, system=["*"]), "fix_0f85c4a").kind, "discovered")
        self.assertEqual(discover(fs, "/srv/r", Env(uid=ALICE, system=["*"], global_=[""]), "fix_0f85c4a").kind, "invalid_ownership")

    def test_interpolation(self):
        e = Env(uid=1, home="/home/a", prefix="/opt/git")
        self.assertEqual(interpolate("~/x", e), "/home/a/x")
        self.assertEqual(interpolate("%(prefix)/x", e), "/opt/git/x")
        self.assertIsNone(interpolate("~bob/x", e))
        self.assertEqual(interpolate("/abs", e), "/abs")

    def test_ceiling_is_proper_ancestor_only(self):
        self.assertEqual(longest_ancestor_length("/a/b", ["/a"]), 2)
        self.assertEqual(longest_ancestor_length("/a", ["/a"]), -1)
        self.assertEqual(longest_ancestor_length("/ab/c", ["/a"]), -1)
        self.assertEqual(longest_ancestor_length("/a/b/c", ["/a", "/a/b", "rel"]), 4)

    def test_cwd_is_checked_even_if_ceiling(self):
        fs = fs_with_repo("/a", ALICE)
        self.assertEqual(discover(fs, "/a", Env(uid=ALICE, ceilings=["/a"]), "fix_8959555").kind, "discovered")

    def test_foreign_config_keys_reported_only_when_parsed(self):
        sc = load(ROOT / "fixtures/scenarios/02_foreign_parent_repo.json")
        r = run(sc)
        self.assertEqual(r["pre_fix"]["command_valued_keys_in_repo_config"], ["core.fsmonitor"])
        self.assertTrue(r["pre_fix"]["repo_config_parsed"])
        for m in ("fix_8959555", "fix_0f85c4a"):
            self.assertFalse(r[m]["repo_config_parsed"])
            self.assertEqual(r[m]["command_valued_keys_in_repo_config"], [])
            self.assertIsNone(r[m]["gitdir"])

    def test_only_top_level_checked(self):
        r = run(load(ROOT / "fixtures/scenarios/14_intermediate_dir_not_checked.json"))
        self.assertEqual(r["fix_8959555"]["ownership"], "owned")

    def test_fix_is_monotone_restriction(self):
        # Every scenario accepted by a fix mode is accepted by pre_fix.
        for p in SC:
            r = run(load(p))
            for m in ("fix_8959555", "fix_0f85c4a"):
                if r[m]["repo_config_parsed"]:
                    self.assertTrue(r["pre_fix"]["repo_config_parsed"], p.name)

    def test_relative_path_rejected(self):
        with self.assertRaises(ValueError):
            MemFS.norm("relative/path")


if __name__ == "__main__":
    unittest.main()


class NoConfigReadWhenRejected(unittest.TestCase):
    """The repository config must not be opened for a rejected repository."""

    def _spy_run(self, fs, cwd, env, mode):
        import git_safedir_model.discovery as disc
        calls, reads = [], []
        real_cfg, real_get = disc._repo_config, fs.get

        def spy_cfg(f, g):
            calls.append(g)
            return real_cfg(f, g)

        def spy_get(p):
            if p.endswith("/config"):
                reads.append(p)
            return real_get(p)

        disc._repo_config = spy_cfg
        fs.get = spy_get
        try:
            r = disc.discover(fs, cwd, env, mode)
        finally:
            disc._repo_config = real_cfg
            del fs.get
        return r, calls, reads

    def _foreign_with_cfg(self):
        fs = fs_with_repo("/srv/r", BOB)
        fs.add("/srv/r/.git/config", "file", BOB,
               content="[safe]\n\tdirectory = /srv/r\n[core]\n\tfsmonitor = x\n")
        return fs

    def test_invalid_ownership_never_reads_config(self):
        for m in ("fix_8959555", "fix_0f85c4a"):
            r, calls, reads = self._spy_run(self._foreign_with_cfg(), "/srv/r", Env(uid=ALICE), m)
            self.assertEqual(r.kind, "invalid_ownership")
            self.assertEqual((calls, reads), ([], []), m)
            self.assertFalse(r.repo_config_parsed)
            self.assertNotIn("repo", r.ignored_safe_directory_sources)
            self.assertEqual(r.command_valued_keys_in_repo_config, [])
            self.assertIn("repo config not read: ownership rejected", r.safe_trace)
            self.assertTrue(any(t.startswith("policy:") for t in r.safe_trace))

    def test_accepted_repo_reads_config_once(self):
        r, calls, reads = self._spy_run(self._foreign_with_cfg(), "/srv/r",
                                        Env(uid=ALICE, global_=["/srv/r"]), "fix_8959555")
        self.assertEqual(r.kind, "discovered")
        self.assertEqual(calls, ["/srv/r/.git"])
        self.assertEqual(reads, ["/srv/r/.git/config"])
        self.assertIn("repo", r.ignored_safe_directory_sources)
        self.assertEqual(r.command_valued_keys_in_repo_config, ["core.fsmonitor"])
