"""In-memory model of git repository discovery (setup.c,
setup_git_directory_gently_1) and the ownership check added by git commit
8959555 (CVE-2022-24765), with the ``*`` value from commit 0f85c4a.

Nothing here runs git, touches the real filesystem or executes configuration.
"""
