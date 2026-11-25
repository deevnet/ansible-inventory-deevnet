# CLAUDE.md

Guidance for Claude Code in this repository: the Deevnet inventory, with its
secrets in Ansible Vault. These rules hold on every machine and in every
session, with or without saved memory.

## Secrets

- **Never read a vault file or a share file, by any tool.** No `cat`, `grep`,
  `Read`, `diff` or `git diff` of a `vault.yml`, decrypted or not. Exclude them
  from every search (`grep --exclude='*vault*'`). A grep of an encrypted vault
  finds nothing, so it proves nothing either: ask the user what a vault holds.
- **No credential value, and nothing about where keys or the vault password are
  kept or who holds them,** in any commit message, PR, issue, doc or log. A
  rekey or rotation is described as routine maintenance, never as a response
  to an exposure.
- **Claude cannot encrypt.** There is no vault password file. `make vault`,
  `make unvault` and the `deevnet.net` targets that seal a router backup
  prompt for the password; the user runs them.

## While the vault files are decrypted

`make unvault` leaves plaintext secrets in the working tree, and the pre-commit
hook refuses to commit them.

- **Never `git reset --hard`, `git checkout -- .`, `git stash` or `git clean`**
  while they are decrypted: a discarded plaintext file can only be recovered
  by decrypting again.
- **Stage only your own paths** (`git add <path>`), never `git add -A` or `.`.

## Changes

- **Every inventory change goes through a pull request,** even a ciphertext-only
  or certificate-only commit. Never push to `main`.
- **Check a group's members before running a play against it,** and always
  pass `--limit` to the builder collection's plays. A group can hold more hosts
  than expected (`artifact_servers` includes the temporary builder VM), and a
  play against the wrong host can start a bulk download across the core router.
