# Limitations

- **Model, not git.** Behaviour is mapped to git v2.35.2 sources and the two
  commits above. Later git releases changed this area; they are **not**
  modelled and nothing here describes them.
- **Never executes configuration.** `command_valued_keys_in_repo_config`
  lists key *names* only (`core.fsmonitor`, `core.pager`, `core.editor`,
  `core.sshcommand`, `core.hookspath`). Their values are never read as
  commands. The list is not exhaustive.
- POSIX uid ownership only. Windows ownership (SIDs, Administrators group)
  and `sudo` handling are not modelled.
- `is_git_directory` is simplified (HEAD file + `objects/` + `refs/`).
- Path comparison is exact string equality, as `fspathcmp` with
  `ignore_case` unset at that early stage; this is my reading of the code,
  not a tested git run.
- `~user/` interpolation is not modelled (reported in the trace).
- A ceiling entry of `/` is ignored by this model; git's exact handling of
  that case is not modelled.
- Includes (`include.path`) in system/global config are not modelled.
- CI configuration is included; at the time of the local commit it had only
  been run locally, not on a hosted runner.
