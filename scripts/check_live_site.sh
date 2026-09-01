#!/usr/bin/env bash
set -euo pipefail

site_url="${1:-https://docs.openamrobot.ai}"
http_url="${site_url/https:\/\//http:\/\/}"

http_headers=$(curl --silent --show-error --max-redirs 0 --head "$http_url/" 2>&1 || true)
grep -Eq '^HTTP/.* 30[1278]' <<<"$http_headers" || { echo "HTTP root does not redirect permanently"; exit 1; }
grep -Eiq '^location: https://' <<<"$http_headers" || { echo "HTTP root does not redirect to HTTPS"; exit 1; }

for path in / /start-here/ /paths/ /reference/ /robots.txt /sitemap.xml /llms.txt; do
  output_file="/tmp/openamrobot-live-check"
  curl --fail --silent --show-error --retry 5 --retry-all-errors --max-time 30 "$site_url$path" -o "$output_file"
  [[ -s "$output_file" ]] || { echo "Empty response: $path"; exit 1; }
done

curl --fail --silent --show-error --retry 5 "$site_url/" | grep -Fq 'Build robots. Train them for real work.'
curl --fail --silent --show-error --retry 5 "$site_url/start-here/" | grep -Fq 'Start with the task in front of you'
curl --fail --silent --show-error --retry 5 "$site_url/paths/" | grep -Fq 'Domain Expert'

echo "Live documentation smoke test passed: $site_url"
