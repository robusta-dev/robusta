# Build stage
FROM python:3.11-slim as builder
ENV PATH="/root/.local/bin/:$PATH"

RUN apt-get update \
    && dpkg --add-architecture arm64 \
    && apt-get install -y --no-install-recommends curl gcc patch \
    && pip3 install --no-cache-dir --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /app
WORKDIR /app

RUN curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.35/deb/Release.key -o /app/Release.key

ENV ENV_TYPE=DEV

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

# Patching CVE-2026-24049 (High): wheel path traversal vulnerability
RUN pip install --no-cache-dir "wheel>=0.46.2"

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
# We're installing here libexpat1, to upgrade the package to include a fix to 3 high CVEs. CVE-2024-45491,CVE-2024-45490,CVE-2024-45492
# Patching glibc for CVE-2026-0861, CVE-2026-0915, CVE-2025-15281
# We install openssh-client rather than the "ssh" metapackage: only the ssh *client* is used
# (GIT_SSH_COMMAND when cloning playbook repos over git@). The metapackage also pulls in
# openssh-server and openssh-sftp-server, which are never used and carry unfixed CVEs
# (CVE-2026-60002 (Critical) and others with no fixed Debian package available).
# gnupg2 is intentionally not installed - the kubectl apt key is consumed in ASCII-armored
# form below, which avoids the whole gnupg/dirmngr/gpgsm package family and its unfixed
# CVE-2026-24882 (High).
RUN apt-get update \
    && dpkg --add-architecture arm64 \
    && pip3 install --no-cache-dir --upgrade pip \
    && apt-get install -y --no-install-recommends git openssh-client curl fonts-dejavu-core apt-transport-https \
    && apt-get install -y --no-install-recommends libexpat1 libc6 libc-bin libcap2 \
    && rm -rf /var/lib/apt/lists/*

# Debian trixie ships no fix for libssh2/attr/acl or perl ("vulnerable, no DSA" in the
# Debian security tracker), so the patched packages are pulled from forky with a
# per-package pin. Nothing else is resolved against testing - the preferences file below
# blocks every forky package except the ones named, and the sources are removed again in
# the same layer.
# - libssh2/libattr1/libacl1: CVE-2026-58050/58051/66032/66033/66034/66035, CVE-2026-54371,
#   CVE-2026-54369/54370.
# - perl-base/perl: CVE-2026-57433, CVE-2026-13221, CVE-2026-57432, CVE-2026-15534,
#   CVE-2026-19487. forky's perl pre-depends on glibc >= 2.43, so libc6/libc-bin/
#   libc-gconv-modules-extra/libcrypt1 come along too. git hard-depends on perl (Debian
#   builds them from the same source with locked versions), so git/git-man/liberror-perl/
#   perl-modules-5.42/libperl5.42 are pulled up to forky's git 2.53.0 as well - trying to
#   pin perl-base alone makes apt remove git instead of upgrading it.
RUN echo 'deb http://deb.debian.org/debian forky main' > /etc/apt/sources.list.d/forky.list \
    && printf 'Package: libssh2-1t64 libattr1 libacl1 perl-base perl perl-modules-5.42 libperl5.42 liberror-perl git git-man libc6 libcrypt1 libc-bin libc-gconv-modules-extra\nPin: release n=forky\nPin-Priority: 990\n\nPackage: *\nPin: release n=forky\nPin-Priority: -1\n' > /etc/apt/preferences.d/99-forky \
    && apt-get update \
    && apt-get install -y --no-install-recommends libssh2-1t64 libattr1 libacl1 perl-base perl perl-modules-5.42 libperl5.42 liberror-perl git git-man libc6 libcrypt1 libc-bin libc-gconv-modules-extra \
    && rm -f /etc/apt/sources.list.d/forky.list /etc/apt/preferences.d/99-forky \
    && rm -rf /var/lib/apt/lists/*

# Patching CVE-2024-32002
RUN git config --global core.symlinks false

# Temporary setuptools CVE fix untill python:3.12-slim image will be used.
RUN rm -rf /usr/local/lib/python3.11/ensurepip/_bundled/setuptools-65.5.0-py3-none-any.whl
RUN rm -rf /usr/local/lib/python3.11/site-packages/setuptools-65.5.1.dist-info

# Patching CVE-2026-24049 (High): wheel path traversal vulnerability
# Patching CVE-2026-23949 (High): jaraco.context path traversal vulnerability (vendored in setuptools)
RUN pip3 install --no-cache-dir "wheel>=0.46.2" "setuptools>=80.10.1" \
    && rm -rf /usr/local/lib/python3.11/site-packages/setuptools/_vendor/wheel-0.45.1.dist-info

COPY --from=builder /app/venv /venv
COPY --from=builder /etc/robusta/playbooks/defaults /etc/robusta/playbooks/defaults
# Copy virtual environment and application files from the build stage
COPY --from=builder /app /app
# remove duplicated /app/venv - already copied to /venv
RUN rm -rf /app/venv
# Remove vendored wheel 0.45.1 from setuptools in venv (CVE-2026-24049)
RUN rm -rf /venv/lib/python3.11/site-packages/setuptools/_vendor/wheel*

# Set up kubectl
# apt accepts an ASCII-armored key directly via signed-by, so there is no need for
# `gpg --dearmor` (and therefore no need for gnupg2 in the runtime image).
COPY --from=builder /app/Release.key /etc/apt/keyrings/kubernetes-apt-keyring.asc
RUN chmod 0644 /etc/apt/keyrings/kubernetes-apt-keyring.asc \
    && echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.asc] https://pkgs.k8s.io/core:/stable:/v1.35/deb/ /' | tee /etc/apt/sources.list.d/kubernetes.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends kubectl \
    && rm -rf /var/lib/apt/lists/*

# Run the application
# -u disables stdout buffering https://stackoverflow.com/questions/107705/disable-output-buffering
CMD [ "python3", "-u", "-m", "robusta.runner.main"]
