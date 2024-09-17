# Build stage
FROM python:3.11-slim as builder
ENV PATH="/root/.local/bin/:$PATH"

RUN apt-get update \
    && dpkg --add-architecture arm64 \
    && apt-get install -y --no-install-recommends curl gcc patch \
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

# See https://github.com/kubernetes-client/python/issues/1921 and https://github.com/tomplus/kubernetes_asyncio/issues/247
# Fix based on files at end of https://github.com/tomplus/kubernetes_asyncio/pull/300/files
RUN echo ">>> don't deep-copy configuration for local_vars_configuration in models"
COPY scripts/client_configuration_get_default_patch.diff /app/client_configuration_get_default_patch.diff
RUN patch "/app/venv/lib/python3.11/site-packages/kubernetes/client/configuration.py" "/app/client_configuration_get_default_patch.diff"
RUN find "/app/venv/lib/python3.11/site-packages/kubernetes/client/models/" -type f -print0 | xargs -0 sed -i 's/local_vars_configuration = Configuration.get_default_copy()/local_vars_configuration = Configuration.get_default()/g'
RUN find "/app/venv/lib/python3.11/site-packages/kubernetes/client/models/" -type f -print0 | xargs -0 sed -i 's/local_vars_configuration = Configuration()/local_vars_configuration = Configuration.get_default()/g'
# Final stage
FROM python:3.11-slim

ENV ENV_TYPE=DEV
ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/app/venv
ENV PATH="/venv/bin:$PATH"
ENV PYTHONPATH=$PYTHONPATH:.:/app/src

WORKDIR /app

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

COPY --from=builder /app/venv /venv
COPY --from=builder /etc/robusta/playbooks/defaults /etc/robusta/playbooks/defaults
# Copy virtual environment and application files from the build stage
COPY --from=builder /app /app

# Run the application
# -u disables stdout buffering https://stackoverflow.com/questions/107705/disable-output-buffering
CMD [ "python3", "-u", "-m", "robusta.runner.main"]
