#!/usr/bin/env bash
# Report at the end of review.yml and cd.yml, on the run's summary page: what
# ran for each product, the Python coverage, the e2e coverage (cd.yml) or
# where to find it (review.yml), the vulnerabilities Trivy found and the
# infrastructure plan. A line is only printed if the job that measures it ran.
#   NEEDS  toJSON(needs) of the calling job
#   SHA    the commit that was checked
set -euo pipefail

{
    echo "## 📋 Report"
    echo
    echo "| Product | Result |"
    echo "| --- | --- |"
    jq -r '
        {success: "✅ passed", failure: "❌ failed", cancelled: "⚪ cancelled", skipped: "➖ not touched"} as $label
        | to_entries[] | select(.key != "scope")
        | "| \(.key | gsub("_"; " ")) | \($label[.value.result]) |"' <<< "$NEEDS"
    echo
    coverage=$(jq -r '.cms.outputs.coverage // empty' <<< "$NEEDS")
    if [ -n "$coverage" ]; then
        echo "📊 Python coverage: **${coverage} %** (files below 100 % in the CMS tests job, further down this page)."
    else
        echo "📊 Python coverage: not measured, the CMS tests did not run."
    fi
    echo
    if jq -e '.e2e' <<< "$NEEDS" > /dev/null; then
        jq -r '.e2e.outputs | "🎭 E2E coverage: server **\(.server_coverage // "?") %**, SPAs in the browser **\(.browser_coverage // "?") %** of lines."' <<< "$NEEDS"
    else
        echo "🎭 E2E tests and their coverage run in their own workflow, with the \`frontend\` label: [checks of this commit]($GITHUB_SERVER_URL/$GITHUB_REPOSITORY/commit/$SHA/checks)."
    fi
    # Every `*trivy` output of the jobs: the lockfiles, each image built.
    trivy=$(jq -r '[.[].outputs // {} | to_entries[] | select(.key | endswith("trivy")) | .value | select(. != "") | "- \(.)"] | join("\n")' <<< "$NEEDS")
    if [ -n "$trivy" ]; then
        echo
        echo "🔍 Vulnerabilities (Trivy). ❌: a HIGH or CRITICAL one has a fix, listed further down this page; the lockfiles job fails and the image is not pushed."
        echo "$trivy"
    fi
    # The `plan` output of infrastructure.yml: nothing until that workflow exposes it.
    plan=$(jq -r '.infrastructure.outputs.plan // empty' <<< "$NEEDS")
    if [ -n "$plan" ]; then
        echo
        echo "🏗️ Infrastructure plan: $plan"
    fi
} >> "$GITHUB_STEP_SUMMARY"
