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

# The OpenAMRobot 2.0 reference pages must not state values the decisions register has retired
# (BOM-ISSUE-IN-FORCE, FRAMES-REP105, CAMERAS, NAV-LIDAR, BATTERY-PLACEMENT).
retired_2_0='BOM Issue 7\.7([^0-9]|$)|Issue 7\.7 \||x =? ?0\.195 m|142\.5 mm|\(0\.376, 0, 0\.0445\)|0\.376, 0, 0\.0445|7\.1 mm|10 mm standoffs|222\.0 mm|25 percent'
for page in docs/reference/openamrobot-2/*.md; do
  [[ -f "$page" ]] || continue
  while IFS= read -r hit; do
    fail "$page:${hit%%:*} states a retired 2.0 value: ${hit#*:}"
  done < <(grep -nEo "$retired_2_0" "$page")
done

if (( failures > 0 )); then
  printf '\nDocumentation check failed: %d error(s), %d warning(s).\n' "$failures" "$warnings"
  exit 1
fi

printf '\nDocumentation check passed with %d warning(s).\n' "$warnings"
