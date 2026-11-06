# Sources

Local copies under `security-research-45/sources/next/` (not in this repo):

| Source | Used for | SHA-256 of copy |
|---|---|---|
| git commit 8959555cee7ec045958f9b6dd62e541affb7e7d9 (diff) | `ensure_valid_ownership`, `safe_directory_cb`, call sites, docs on scopes | 474e7cb2aeb565a0e5d21c0f75a641e6f80c4a7f0259d4818b781102e16e926f |
| git commit 0f85c4a30b072a26d74af8bbf63cc8f6a5dfc1b8 (diff) | `*` and its reset | b685b870e43b2fb4b0adfbe0adb78c09619fbfacc68f170b90b10e382b65cb42 |
| git v2.35.2 `setup.c` (raw) | discovery loop, ceiling, mount point, `GIT_DIR` | 0301d700deefdb5eaa5bf41ee56703fe47ce6c509755c0be0c5f1870a3fba55d |
| git v2.35.2 `config.c` (raw) | `read_very_early_config` options | b4e7bd8929639d697868f7c05e3231fd3321dfd0519026c3d9579cc4f5566d55 |
| git `Documentation/RelNotes/2.30.3.txt` | CVE-2022-24765 description | 8a30a32964da4b22d4b62c3df7de752ec030e9ca8e5a72fe2b9e9354015a721c |

Note: the 2.30.3 release-notes file is headed "Git v2.30.2 Release Notes"
upstream; the content is the 2.30.3 security release.
