FROM ghcr.io/coreemu/core-ubuntu:v9.2.1

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /uvx /bin/
# Set up the virtual environment
ENV VIRTUAL_ENV=/opt/core/venv
ENV UV_PROJECT_ENVIRONMENT=/opt/core/venv
ENV PATH="/opt/core/venv/bin:$PATH"

# Install dependencies for sharing GPG keys
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gnupg2 && \
    rm -rf /var/lib/apt/lists/*

# Install service dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends sysstat bwm-ng && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY .python-version pyproject.toml uv.lock README.md ./
RUN uv sync --inexact --frozen
