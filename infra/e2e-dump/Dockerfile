# Image of the nightly e2e dump container (dump.sh): Postgres 16 like production,
# with PostgreSQL Anonymizer from the Dalibo Labs repository and the AWS CLI
# (Scaleway Object Storage is S3-compatible).
# Pinned by digest (Renovate updates it): this image reads production data.
FROM postgres:16-trixie@sha256:63e83b5a3dc36a917dccb76fe1bd2ac51f1ec9c1deb47ff20d4f04233bf6eae9

ARG ANON_VERSION=3.3.2
ARG ANON_DEB_SHA256=1ddf823a97ec39d4369264b1a30e21fb0cb6975ec7a4c9865e6c103173a68723
ARG DALIBO_REPO_ASC_SHA256=5ed3ea58383868c18b2becf9bb2a344b889af5ab349a62a9fe20e196d5adc6c4

# Key and package pinned by hash: a change in the Dalibo repository fails the
# build. The key is trusted for that repository only (signed-by).
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl awscli \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://repo.dalibo.com/dalibo_labs.asc -o /etc/apt/keyrings/dalibo_labs.asc \
    && echo "${DALIBO_REPO_ASC_SHA256}  /etc/apt/keyrings/dalibo_labs.asc" | sha256sum -c - \
    && echo "deb [signed-by=/etc/apt/keyrings/dalibo_labs.asc] https://repo.dalibo.com/apt trixie main" > /etc/apt/sources.list.d/dalibo_labs.list \
    && apt-get update \
    && mkdir /tmp/anon && cd /tmp/anon && apt-get download "postgresql_anonymizer_16=${ANON_VERSION}" \
    && echo "${ANON_DEB_SHA256}  $(ls)" | sha256sum -c - \
    # Dependencies come from Debian only.
    && rm /etc/apt/sources.list.d/dalibo_labs.list \
    && apt-get install -y --no-install-recommends ./*.deb \
    && rm -rf /var/lib/apt/lists/* /tmp/anon

COPY server.py dump.sh rules.sql check.sql columns-to-declare.sql excluded-tables.txt /e2e-dump/

ENTRYPOINT []
# HTTP entry point (POST /run): Serverless Containers only run HTTP servers.
# python3 comes with awscli.
EXPOSE 8080
CMD ["python3", "/e2e-dump/server.py"]
