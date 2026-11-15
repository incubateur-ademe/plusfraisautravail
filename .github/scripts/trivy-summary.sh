#!/usr/bin/env bash
# Sums up the Trivy JSON report FILE of NAME (the lockfiles, an image):
# - the counts by severity go to the job output `summary`, for run-report.sh;
# - the HIGH and CRITICAL vulnerabilities that have a fix go to the run's
#   summary page, and fail the step.
set -euo pipefail
name=$1 file=$2

counts=$(jq -r '
    [.Results[]?.Vulnerabilities[]?.Severity] as $found
    | ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    | map(. as $severity | "\($found | map(select(. == $severity)) | length) \($severity | ascii_downcase)")
    | join(", ")' "$file")
to_fix=$(jq -r '
    .Results[]? | .Target as $target | .Vulnerabilities[]?
    | select((.Severity == "HIGH" or .Severity == "CRITICAL") and (.FixedVersion // "") != "")
    | "| \($target) | \(.PkgName) | \(.InstalledVersion) | \(.FixedVersion) | \(.Severity) | \(.VulnerabilityID) |"' "$file")

if [ -z "$to_fix" ]; then
    echo "summary=✅ $name: $counts" >> "$GITHUB_OUTPUT"
    exit 0
fi
echo "summary=❌ $name: $counts, $(wc -l <<< "$to_fix" | tr -d ' ') to fix" >> "$GITHUB_OUTPUT"
{
    echo "### 🔍 Trivy, $name: HIGH and CRITICAL vulnerabilities with a fix"
    echo
    echo "| Where | Package | Installed | Fixed in | Severity | Id |"
    echo "| --- | --- | --- | --- | --- | --- |"
    echo "$to_fix"
} >> "$GITHUB_STEP_SUMMARY"
exit 1
