# Image for the LazyFS power-cut test (see README.md in this folder).
# Needs a privileged container: docker run --privileged (FUSE needs /dev/fuse and CAP_SYS_ADMIN).
FROM rust:1.89-bookworm
RUN apt-get update \
 && apt-get install -y --no-install-recommends cmake g++ libfuse3-dev fuse3 git procps \
 && rm -rf /var/lib/apt/lists/*
# LazyFS (https://github.com/dsrhaslab/lazyfs), pinned to the commit that was tested.
ARG LAZYFS_COMMIT=3edad01aa936b81fed9bd64e47e725fc5ef6c977
RUN git clone https://github.com/dsrhaslab/lazyfs /opt/lazyfs \
 && cd /opt/lazyfs && git checkout "$LAZYFS_COMMIT" \
 && cd libs/libpcache && ./build.sh \
 && cd /opt/lazyfs/lazyfs && ./build.sh \
 && echo user_allow_other >> /etc/fuse.conf
