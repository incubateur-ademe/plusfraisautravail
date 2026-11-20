#!/usr/bin/env bash
# Scaleway Serverless Containers of infra/envs/prod, found by name: no
# container id to keep in GitHub variables. Needs SCW_SECRET_KEY.
#
#   scw-container.sh redeploy NAME IMAGE   roll IMAGE out on NAME
#   scw-container.sh run NAME [BUILD]      POST /run once NAME is ready (and its
#                                          GET / answers BUILD), print the answer
#   scw-container.sh serving NAME BUILD    wait until the public NAME answers BUILD
#                                          on /healthz/: its new revision serves
#   scw-container.sh delete_tags IMAGE PREFIX   delete the registry tags PREFIX* of IMAGE
set -euo pipefail

api="https://api.scaleway.com/containers/v1/regions/fr-par/containers"
auth="X-Auth-Token: $SCW_SECRET_KEY"

# The container's JSON, empty while it does not exist or the API fails.
container() {
    curl -fsS "$api?name=$1" -H "$auth" | jq -c --arg n "$1" '.containers[] | select(.name == $n)' || true
}
field() { container "$1" | jq -r ".$2 // empty"; }

# Retries COMMAND every 10 s for MINUTES.
wait_until() {
    local minutes=$1 error=$2
    shift 2
    for _ in $(seq $((minutes * 6))); do
        "$@" && return
        sleep 10
    done
    echo "::error::$error" >&2
    return 1
}

exists() { [ -n "$(container "$1")" ]; }
is_ready() { [ "$(field "$1" status)" = ready ]; }
# After a PATCH, the API reports the new image while the old revision may
# still answer: only the container itself tells which build runs.
serves() { [ "$(curl -fsS --max-time 10 "$1/" -H "$auth" || true)" = "$2" ]; }

redeploy() {
    local name=$1 image=$2
    # The infrastructure apply of the same push may still be creating it.
    wait_until 5 "Container $name not found: has the infrastructure been applied?" exists "$name"
    # Retried: a container still being created refuses the update.
    wait_until 2 "Container $name did not take the image $image" patch_image "$name" "$image"
}

# An update always redeploys. Fails unless the API answers with the new image.
patch_image() {
    curl -fsS -X PATCH "$api/$(field "$1" id)" -H "$auth" -H "Content-Type: application/json" \
        -d "$(jq -n --arg image "$2" '{image: $image}')" | jq -e --arg image "$2" '.image == $image' > /dev/null
}

run() {
    local name=$1 build=${2:-} url
    wait_until 10 "Container $name not ready after 10 min" is_ready "$name"
    url=$(field "$name" public_endpoint)
    url=${url%/}
    [ -z "$build" ] || wait_until 10 "Container $name does not serve $build" serves "$url" "$build"
    # Longer than the container's own timeout (timeout_seconds), so its answer
    # arrives rather than a client-side cut.
    curl --fail-with-body -sS --max-time 1900 -X POST "$url/run" -H "$auth"
}

healthz() { [ "$(curl -fsS --max-time 10 "$1/healthz/" || true)" = "$2" ]; }

# Scaleway accepts an image before it starts: only the answer of the container
# tells that the rollout worked.
serving() {
    local name=$1 build=$2 url
    url=$(field "$name" public_endpoint)
    wait_until 10 "Container $name does not serve $build: its rollout failed" healthz "${url%/}" "$build"
}

delete_tags() {
    local registry="https://api.scaleway.com/registry/v1/regions/fr-par" image tags ids="" page=1
    image=$(curl -fsS "$registry/images?name=$1" -H "$auth" | jq -r '.images[0].id // empty')
    # Nothing was ever pushed.
    [ -n "$image" ] || return 0
    # Every page is read before the first deletion, which would shift them.
    while :; do
        tags=$(curl -fsS "$registry/images/$image/tags?page_size=100&page=$page" -H "$auth")
        [ "$(jq '.tags | length' <<< "$tags")" -gt 0 ] || break
        ids+=" $(jq -r --arg prefix "$2" '.tags[] | select(.name | startswith($prefix)) | .id' <<< "$tags")"
        page=$((page + 1))
    done
    for tag in $ids; do curl -fsS -X DELETE "$registry/tags/$tag" -H "$auth" > /dev/null; done
}

"$@"
