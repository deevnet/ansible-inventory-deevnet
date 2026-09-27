#!/usr/bin/env bash
# Start a site's vault files from the committed examples.
#
# For every vault.example.yml under the site directory, create vault.yml beside
# it with every key present and every value empty - unless vault.yml already
# exists, which is never touched. Fill in the values (each key's comment says
# where it comes from), then run `make vault` before committing anything.
#
#   scripts/make-empty-vault.sh [site]     # default: mobile
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
site="${1:-mobile}"
dir="$root/$site"
[[ -d "$dir" ]] || { echo "No site directory: $site" >&2; exit 1; }

created=0 kept=0
while IFS= read -r -d '' ex; do
    vault="$(dirname "$ex")/vault.yml"
    rel="${vault#"$root"/}"
    if [[ -e "$vault" ]]; then
        echo "kept     $rel (already exists)"
        kept=$((kept + 1))
    else
        cp "$ex" "$vault"
        echo "created  $rel"
        created=$((created + 1))
    fi
done < <(find "$dir" -name vault.example.yml -print0 | sort -z)

echo
echo "$created created, $kept kept. Fill in the values, then: make vault"
