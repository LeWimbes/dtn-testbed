FROM rust:1 AS dtn-builder

# Build dtn7-rs
RUN git clone https://github.com/dtn7/dtn7-rs.git && \
    cd dtn7-rs && \
    git checkout tags/v0.21.0 -b 0.21.0 && \
    cargo install --locked --path ./core/dtn7

FROM ghcr.io/coreemu/core-ubuntu:v9.2.1

# Set custom services directory for CORE
# This setting is only required when running the CORE GUI, but it is safe to include regardless of the interface
RUN sed -i 's|^#custom_services_dir *=.*|custom_services_dir = /root/dtn-testbed/eval/core_services|' /opt/core/etc/core.conf

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /uvx /bin/
# Set up the virtual environment
ENV VIRTUAL_ENV=/opt/core/venv
ENV UV_PROJECT_ENVIRONMENT=/opt/core/venv
ENV PATH="/opt/core/venv/bin:$PATH"

# Install service dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends sysstat bwm-ng && \
    rm -rf /var/lib/apt/lists/*

# Install dtn7-rs
COPY --from=dtn-builder /usr/local/cargo/bin/dtnd /bin/

WORKDIR /root/dtn-testbed
# Copy project definitions
COPY .python-version pyproject.toml uv.lock README.md /root/dtn-testbed/
# Install testbed dependencies while keeping packages provided by the CORE environment
# Doing this before copying the source code allows us to cache the dependencies
RUN uv sync --inexact --frozen
# Copy the entire project
COPY . /root/dtn-testbed

ENTRYPOINT core-daemon
