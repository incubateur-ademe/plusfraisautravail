#!/usr/bin/env bash
# Self-check of trivy-summary.sh and run-report.sh on sample data:
#   .github/scripts/test-reports.sh
set -euo pipefail
cd "$(dirname "$0")"
dir=$(mktemp -d)
trap 'rm -rf "$dir"' EXIT
export GITHUB_OUTPUT=$dir/output GITHUB_STEP_SUMMARY=$dir/summary
export GITHUB_SERVER_URL=https://github.com GITHUB_REPOSITORY=o/r SHA=abc
has() { grep -qF -- "$1" "$2" || { echo "FAILED: '$1' not in $2:" >&2; cat "$2" >&2; exit 1; }; }
hasnt() { ! grep -qF -- "$1" "$2" || { echo "FAILED: '$1' in $2" >&2; exit 1; }; }

# No vulnerability, and a report without any result: passes.
echo '{"Results": [{"Target": "uv.lock"}]}' > "$dir/clean.json"
./trivy-summary.sh lockfiles "$dir/clean.json"
has "summary=✅ lockfiles: 0 critical, 0 high, 0 medium, 0 low" "$GITHUB_OUTPUT"
echo '{}' > "$dir/empty.json"
./trivy-summary.sh lockfiles "$dir/empty.json"

# A HIGH without a fix and a MEDIUM with one are counted, and pass.
echo '{"Results": [{"Target": "uv.lock", "Vulnerabilities": [
    {"Severity": "HIGH", "PkgName": "a", "InstalledVersion": "1", "VulnerabilityID": "CVE-1"},
    {"Severity": "MEDIUM", "PkgName": "b", "InstalledVersion": "1", "FixedVersion": "2", "VulnerabilityID": "CVE-2"}]}]}' > "$dir/unfixed.json"
./trivy-summary.sh lockfiles "$dir/unfixed.json"
has "summary=✅ lockfiles: 0 critical, 1 high, 1 medium, 0 low" "$GITHUB_OUTPUT"

# A HIGH with a fix fails, and is listed.
echo '{"Results": [{"Target": "uv.lock", "Vulnerabilities": [
    {"Severity": "HIGH", "PkgName": "django", "InstalledVersion": "5.0", "FixedVersion": "5.1", "VulnerabilityID": "CVE-3"}]}]}' > "$dir/fixable.json"
if ./trivy-summary.sh "cms image" "$dir/fixable.json"; then echo "FAILED: a fixable HIGH passed" >&2; exit 1; fi
has "summary=❌ cms image: 0 critical, 1 high, 0 medium, 0 low, 1 to fix" "$GITHUB_OUTPUT"
has "| uv.lock | django | 5.0 | 5.1 | HIGH | CVE-3 |" "$GITHUB_STEP_SUMMARY"

# The report of a production run where everything ran.
: > "$GITHUB_STEP_SUMMARY"
NEEDS='{"scope": {"result": "success", "outputs": {}},
    "cms": {"result": "success", "outputs": {"coverage": "91", "cms_image_trivy": "✅ cms image: 0 critical"}},
    "dependencies": {"result": "failure", "outputs": {"trivy": "❌ lockfiles: 1 high, 1 to fix"}},
    "infrastructure": {"result": "success", "outputs": {"plan": "No changes."}},
    "e2e": {"result": "success", "outputs": {"server_coverage": "70", "browser_coverage": "80"}}}' ./run-report.sh
has "| dependencies | ❌ failed |" "$GITHUB_STEP_SUMMARY"
has "Python coverage: **91 %**" "$GITHUB_STEP_SUMMARY"
has "server **70 %**, SPAs in the browser **80 %**" "$GITHUB_STEP_SUMMARY"
has "- ✅ cms image: 0 critical" "$GITHUB_STEP_SUMMARY"
has "- ❌ lockfiles: 1 high, 1 to fix" "$GITHUB_STEP_SUMMARY"
has "Infrastructure plan: No changes." "$GITHUB_STEP_SUMMARY"

# The report of a pull request where nothing was measured.
: > "$GITHUB_STEP_SUMMARY"
NEEDS='{"scope": {"result": "success", "outputs": {}},
    "cms": {"result": "skipped", "outputs": {}},
    "dependencies": {"result": "cancelled", "outputs": {}}}' ./run-report.sh
has "| cms | ➖ not touched |" "$GITHUB_STEP_SUMMARY"
has "Python coverage: not measured" "$GITHUB_STEP_SUMMARY"
has "with the \`frontend\` label" "$GITHUB_STEP_SUMMARY"
hasnt "Trivy" "$GITHUB_STEP_SUMMARY"
hasnt "Infrastructure plan" "$GITHUB_STEP_SUMMARY"

echo "ok"
