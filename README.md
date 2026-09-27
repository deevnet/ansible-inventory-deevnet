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

### Example vaults

Beside every `vault.yml` is a plaintext `vault.example.yml`: the same keys, every value empty, and
each key's comment saying what it is and how it is generated. They exist so a vault can be rebuilt,
or a new site started, without decrypting anyone else's.

**Starting a new site.** Copy a site directory's layout for your hosts, then:

```bash
make empty-vault SITE=<site>    # create vault.yml from every example; never overwrites
# fill in each value, following its comment
make vault                      # encrypt before committing anything
```

**Keeping the examples current.** When a vault gains or loses a key, regenerate the examples with
the vaults decrypted and commit them with the change:

```bash
make unvault
make vault-examples             # scripts/vault-examples.py
make vault
```

The generator empties every value, including those of commented-out keys, and writes nothing if a
comment holds something that looks like a secret. `scripts/vault-examples.yml` lists comment
paragraphs that stay out of the public files, and hints for keys whose vault has no comment. The
pre-commit hook also rejects any `vault.example.yml` that carries a value.
