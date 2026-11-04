#!/usr/bin/env bash
set -euo pipefail

site_url="${1:-https://docs.openamrobot.ai}"
http_url="${site_url/https:\/\//http:\/\/}"

http_headers=$(curl --silent --show-error --max-redirs 0 --head "$http_url/" 2>&1 || true)
grep -Eq '^HTTP/.* 30[1278]' <<<"$http_headers" || { echo "HTTP root does not redirect permanently"; exit 1; }
grep -Eiq '^location: https://' <<<"$http_headers" || { echo "HTTP root does not redirect to HTTPS"; exit 1; }

# Download each required page completely. Piping curl into "grep -q" under
# pipefail can fail with curl exit 23 when grep exits early after a match.
# Never waive the HTTP, nonempty-page, or required-content assertions.
check_dir=$(mktemp -d)
trap 'rm -rf "$check_dir"' EXIT
for path in / /start-here/ /paths/ /reference/ /robots.txt /sitemap.xml /llms.txt; do
  output_file="$check_dir/$(printf '%s' "$path" | tr '/' '_')"
  curl --fail --silent --show-error --retry 5 --retry-all-errors --max-time 30 \
    "$site_url$path" -o "$output_file"
  [[ -s "$output_file" ]] || { echo "Empty response: $path"; exit 1; }
done

grep -Fq 'Build robots. Train them for real work.' "$check_dir/_"
grep -Fq 'Start with the task in front of you' "$check_dir/_start-here_"
grep -Fq 'Domain Expert' "$check_dir/_paths_"

echo "Live documentation smoke test passed: $site_url"
