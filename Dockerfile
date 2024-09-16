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
RUN poetry install --no-root --without dev --extras "all"

# Copy project source code
COPY src/ /app/src
RUN poetry install --without dev --extras "all"

# Install playbooks
COPY playbooks/ /etc/robusta/playbooks/defaults
RUN pip install --no-cache-dir /etc/robusta/playbooks/defaults

# Fixes k8s library bug - see https://github.com/kubernetes-client/python/issues/1867#issuecomment-1353813412
RUN find /app/venv/lib/python*/site-packages/kubernetes/client/rest.py -type f -exec sed -i 's:^\(.*logger.*\)$:#\1:' {} \;

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
    && pip3 install --no-cache-dir --upgrade pip \
    && apt-get install -y --no-install-recommends git ssh curl libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Patching CVE-2024-32002
RUN git config --global core.symlinks false

# Remove setuptools-65.5.1 installed from python:3.11-slim base image as fix for CVE-2024-6345 until image will be updated
RUN rm -rf /usr/local/lib/python3.11/site-packages/setuptools-65.5.1.dist-info

# Run the application
# -u disables stdout buffering https://stackoverflow.com/questions/107705/disable-output-buffering
CMD [ "python3", "-u", "-m", "robusta.runner.main"]
