# ansible-inventory-deevnet
Deevnet Host Inventory for Ansible

---

## Setup

After cloning, configure the pre-commit hook (one-time per clone):

```bash
make install-hooks
```

This sets `core.hooksPath` to the version-controlled `hooks/` directory so the pre-commit guard stays in sync with the repo automatically.

---

## Vault Workflow

Secrets are stored in `vault.yml` files throughout the inventory and encrypted with Ansible Vault.

### Decrypt for editing

```bash
make unvault
```

Decrypts all `vault.yml` files in the repo. Only files that are currently encrypted are touched.

### Re-encrypt before committing

```bash
make vault
```

Encrypts all `vault.yml` files. Only files that are currently decrypted are touched.

### Typical workflow

```bash
make unvault          # decrypt
# edit vault files as needed
make vault            # re-encrypt
git add -u && git commit
```

---

## Pre-commit Hook

A pre-commit hook (`hooks/pre-commit`) blocks any commit that includes an unencrypted `vault.yml` file. It inspects the staged content (via `git show`) so it catches the actual data being committed, not just the working-tree state.

If the hook rejects your commit, run `make vault`, re-stage, and commit again.
