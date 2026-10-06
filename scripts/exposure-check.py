#!/usr/bin/env python3
"""Check whether any credential ever committed in plaintext is still in the
vault (CHG-0035). Never prints a value: values stay in memory and are
compared by SHA-256 digest, or searched for as bytes.

Maintainer tool: run with the vaults decrypted (`make unvault`).

  scripts/exposure-check.py [REPO ...]

Part A reads every vault.yml blob in this repository's history that is not
ansible-vault ciphertext, and compares each value with every current one:
  LIVE      the historical value is a current vault value (under any name)
  replaced  the name still exists with a different value
  gone      the name is no longer in the vault
"replaced" and "gone" say only that the vault moved on. Whether the device
still accepts the old value is a separate check, made against the device.

Part B searches every blob in each REPO's object database (default: every
git repository beside this one, and this one) for every current vault value
of MIN_LEN characters or more, as a whole word. A hit is a current secret
present in that history. Each is counted as published (reachable from a
remote-tracking ref), local-ref-only, or unreachable (dropped stashes,
staged-then-unstaged files: on this machine only).
"""
import hashlib
import os
import pathlib
import re
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
MIN_LEN = 6
# Identifiers, not secrets: they appear in ordinary files by design.
IDENTIFIERS = ("_user", "_token_id", "_key_id")


def digest(v):
    return hashlib.sha256(str(v).encode()).hexdigest()


def leaves(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from leaves(v, f"{prefix}.{k}" if prefix else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from leaves(v, f"{prefix}[{i}]")
    elif obj is not None and not isinstance(obj, bool):
        yield prefix, str(obj)


def git(repo, *args, inp=None):
    return subprocess.run(["git", "-C", str(repo), *args], input=inp,
                          capture_output=True, check=True).stdout


def current_vault():
    names, digests, values = {}, {}, []
    for p in sorted(ROOT.rglob("vault.yml")):
        if ".git" in p.parts:
            continue
        text = p.read_text()
        if text.startswith("$ANSIBLE_VAULT"):
            sys.exit(f"{p.relative_to(ROOT)} is encrypted: run make unvault first")
        rel = p.relative_to(ROOT)
        for name, val in leaves(yaml.safe_load(text) or {}):
            d = digest(val)
            names.setdefault(name, set()).add(d)
            digests.setdefault(d, set()).add(name)
            if len(val) >= MIN_LEN and not name.endswith(IDENTIFIERS):
                values.append((f"{rel}:{name}", val))
    return names, digests, values


def part_a(names, digests):
    print("== A: plaintext vault.yml blobs in this repository's history ==")
    log = git(ROOT, "log", "--all", "--format=C %H %cs", "--name-only",
              "--", "*vault.yml").decode()
    seen, hist = set(), {}
    commit = date = None
    for line in log.splitlines():
        if line.startswith("C "):
            _, commit, date = line.split()
            continue
        if not line.strip():
            continue
        try:
            blob = git(ROOT, "rev-parse", f"{commit}:{line}").decode().strip()
        except subprocess.CalledProcessError:
            continue  # the commit deleted it
        if blob in seen:
            continue
        seen.add(blob)
        text = git(ROOT, "cat-file", "blob", blob).decode(errors="replace")
        if text.lstrip().startswith("$ANSIBLE_VAULT"):
            continue
        try:
            data = yaml.safe_load(text) or {}
        except yaml.YAMLError:
            print(f"  unparseable plaintext blob at {commit[:8]}:{line}")
            continue
        for name, val in leaves(data):
            first = hist.setdefault(name, {})
            d = digest(val)
            if d not in first or date < first[d][0]:
                first[d] = (date, line)
    if not hist:
        print("  none")
    for name in sorted(hist):
        for d, (date, path) in sorted(hist[name].items(), key=lambda x: x[1]):
            if d in digests and name.endswith(IDENTIFIERS):
                status = "unchanged (an identifier, not a secret)"
            elif d in digests:
                other = sorted(digests[d] - {name})
                status = "LIVE" + (f" (now under {', '.join(other)})" if other else "")
            elif name in names:
                status = "replaced"
            else:
                status = "gone"
            print(f"  {name:40} first {date}  {path:52} {status}")


def blobs(repo):
    listing = git(repo, "cat-file", "--batch-all-objects",
                  "--batch-check=%(objectname) %(objecttype)").decode().splitlines()
    shas = [l.split()[0] for l in listing if l.endswith(" blob")]
    out = git(repo, "cat-file", "--batch", inp="\n".join(shas).encode())
    i = 0
    while i < len(out):  # "<sha> blob <size>\n<content>\n", repeated
        nl = out.index(b"\n", i)
        sha, _, size = out[i:nl].split()
        size = int(size)
        yield sha.decode(), out[nl + 1:nl + 1 + size]
        i = nl + 1 + size + 1


def reachable(repo, *refs):
    return {l.split()[0] for l in git(repo, "rev-list", "--objects", *refs).decode().splitlines()}


def part_b(values, repos):
    print(f"\n== B: current vault values (>= {MIN_LEN} chars) in any blob ==")
    patterns = [(name, re.compile(rb"(?<![A-Za-z0-9])" + re.escape(v.encode()) + rb"(?![A-Za-z0-9])"))
                for name, v in values]
    hits = 0
    for repo in repos:
        found = {}
        for sha, content in blobs(repo):
            if content.startswith(b"$ANSIBLE_VAULT"):
                continue
            for name, pat in patterns:
                if pat.search(content):
                    found.setdefault(name, set()).add(sha)
        if not found:
            continue
        published, local = reachable(repo, "--remotes"), reachable(repo, "--all")
        for name, shas in sorted(found.items()):
            hits += 1
            pub = len(shas & published)
            loc = len((shas & local) - published)
            print(f"  {repo.name:32} {name:60} published={pub} "
                  f"local-ref-only={loc} unreachable={len(shas) - pub - loc}")
    print(f"  {hits} hit(s) across {len(repos)} repositories")


def main():
    repos = [pathlib.Path(r).resolve() for r in sys.argv[1:]] or sorted(
        p for p in ROOT.parent.iterdir() if (p / ".git").exists())
    names, digests, values = current_vault()
    part_a(names, digests)
    part_b(values, repos)


if __name__ == "__main__":
    main()
