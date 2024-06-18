# Build stage
FROM python:3.11-slim as builder
ENV PATH="/root/.local/bin/:$PATH"

RUN apt-get update \
    && dpkg --add-architecture arm64 \
    && apt-get install -y --no-install-recommends curl gcc \
    && pip3 install --no-cache-dir --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

ENV ENV_TYPE=DEV

RUN mkdir /app
WORKDIR /app

# Create and activate virtual environment
RUN python -m venv /app/venv --upgrade-deps && \
    . /app/venv/bin/activate

ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
RUN poetry config virtualenvs.create false

# Install gcc to compile ruamel.yaml.clib, wheel is missing.
RUN pip3 install --no-cache-dir ruamel.yaml.clib==0.2.8

# Install project dependencies
COPY pyproject.toml poetry.lock /app/
RUN poetry install --no-root --only main --extras "all"

# Copy project source code
COPY src/ /app/src
RUN poetry install --no-dev --extras "all"

# Install playbooks
COPY playbooks/ /etc/robusta/playbooks/defaults
RUN pip install --no-cache-dir /etc/robusta/playbooks/defaults

# Final stage
FROM python:3.11-slim

ENV ENV_TYPE=DEV
ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/app/venv
ENV PATH="/venv/bin:$PATH"
ENV PYTHONPATH=$PYTHONPATH:.:/app/src

WORKDIR /app
COPY --from=builder /app/venv /venv
COPY --from=builder /etc/robusta/playbooks/defaults /etc/robusta/playbooks/defaults
# Copy virtual environment and application files from the build stage
COPY --from=builder /app /app

# Install necessary packages for the runtime environment
RUN apt-get update \
    && dpkg --add-architecture arm64 \
    && apt-get install -y --no-install-recommends git ssh curl libcairo2 gcc \
    && pip3 install --no-cache-dir --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

# Patching CVE-2024-32002
RUN git config --global core.symlinks false

# Run the application
CMD [ "python3", "-u", "/app/src/robusta/runner/main.py"]
