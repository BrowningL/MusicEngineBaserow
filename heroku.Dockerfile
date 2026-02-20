ARG FROM_IMAGE=ghcr.io/browningl/isrcanalytics-baserow:develop
# This is pinned as version pinning is done by the CI setting FROM_IMAGE.
# hadolint ignore=DL3006
FROM $FROM_IMAGE AS image_base

ENV DATA_DIR=/baserow/data
# Ensure volume path exists and ownership stays compatible with the base image user.
RUN mkdir -p "$DATA_DIR" && \
    chown -R 9999:9999 "$DATA_DIR"
