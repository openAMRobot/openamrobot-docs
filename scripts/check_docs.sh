#!/usr/bin/env bash
set -u

failures=0
warnings=0

fail() { printf 'ERROR: %s\n' "$1"; failures=$((failures + 1)); }
warn() { printf 'WARN: %s\n' "$1"; warnings=$((warnings + 1)); }

for path in README.md LICENSE .gitignore .editorconfig CHANGELOG.md; do
  [[ -e "$path" ]] || fail "missing $path"
done

if [[ -f README.md ]]; then
  lines=$(wc -l < README.md)
  (( lines <= 300 )) || fail "README.md has $lines lines; maximum is 300"

  first_command=$(awk 'substr($0,1,3)==sprintf("%c%c%c",96,96,96){print NR; exit}' README.md)
  if [[ -n "$first_command" ]] && (( first_command > 25 )); then
    fail "first fenced block starts at line $first_command; target is line 25 or earlier"
  elif [[ -z "$first_command" ]]; then
    warn "README.md contains no fenced command block"
  fi

  if grep -Ein '(^|[^[:alnum:]_])(TODO|TBD)([^[:alnum:]_]|$)' README.md >/dev/null; then
    fail "README.md contains TODO or TBD markers"
  fi

  grep -Eiq 'status:|##[[:space:]]+status' README.md || warn "README.md has no explicit status"
  grep -Eiq '##[[:space:]]+repository boundaries' README.md || warn "README.md has no Repository boundaries section"
fi

while IFS= read -r -d '' image; do
  bytes=$(wc -c < "$image")
  (( bytes <= 1048576 )) || fail "$image exceeds 1 MB"
done < <(find . -path './.git' -prune -o -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.gif' -o -iname '*.webp' \) -print0)

if (( failures > 0 )); then
  printf '\nDocumentation check failed: %d error(s), %d warning(s).\n' "$failures" "$warnings"
  exit 1
fi

printf '\nDocumentation check passed with %d warning(s).\n' "$warnings"
