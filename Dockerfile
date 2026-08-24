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

# Patching libssh2 CVE-2026-58050, CVE-2026-58051, CVE-2026-66032, CVE-2026-66033,
# CVE-2026-66034, CVE-2026-66035 (High) - libssh2 is pulled in by libcurl, which git
# and curl depend on.
# Patching attr CVE-2026-54371 (High) via libattr1, and acl CVE-2026-54369 (High) /
# CVE-2026-54370 (Medium) via libacl1 - both libraries are dependencies of coreutils
# and therefore cannot be removed.
# Debian trixie ships no fix for any of these ("vulnerable, no DSA" in the Debian
# security tracker); the patched packages only exist in forky/testing. The upgrades
# are deliberately narrow: libssh2 stays on upstream 1.11.1 (Debian revision -6 only
# adds the CVE patches), and attr/acl move to the first upstream releases that carry
# the fixes (2.6.0 and 2.4.0 respectively).
# Only these three packages may come from forky: they get an explicit per-package pin at
# 990, and every other forky package is pinned to -1, which makes it uninstallable. Do NOT
# use `apt-get -t forky` here instead - a target release raises *every* forky package to
# 990 and defeats a `Package: *` pin, so apt would happily resolve a dependency by pulling
# forky's libc6 (2.43) or libssl3t64 into the runtime image. With the negative pin, trixie
# stays the only source for everything else and an unsatisfiable dependency is an apt error
# instead. The testing sources are removed again in the same layer, so the shipped image has
# no testing repository configured.
# Two things to know when revisiting this:
#  * forky is a rolling suite, so the versions installed here drift over time. If a future
#    forky rebuild raises the libc6 floor above what trixie ships, apt will refuse the
#    install and this layer fails loudly rather than silently pulling in a new glibc.
#  * scanners that key off the distro release (docker scout, trivy, ...) still report these
#    CVEs, because the Debian trixie advisories carry no fixed version to compare against.
#    The vulnerable code really is gone - verify with `dpkg -l libssh2-1t64 libattr1 libacl1`
#    rather than the scan output.
RUN echo 'deb http://deb.debian.org/debian forky main' > /etc/apt/sources.list.d/forky.list \
    && printf 'Package: libssh2-1t64 libattr1 libacl1\nPin: release n=forky\nPin-Priority: 990\n\nPackage: *\nPin: release n=forky\nPin-Priority: -1\n' > /etc/apt/preferences.d/99-forky \
    && apt-get update \
    && apt-get install -y --no-install-recommends libssh2-1t64 libattr1 libacl1 \
    && rm -f /etc/apt/sources.list.d/forky.list /etc/apt/preferences.d/99-forky \
    && rm -rf /var/lib/apt/lists/*

# Not patched, no fix available anywhere as of this change:
# - perl CVE-2026-57433, CVE-2026-13221, CVE-2026-57432 (Critical/High) and
#   CVE-2026-15534, CVE-2026-19487 (Medium). Debian trixie has no fixed perl, and
#   perl-base is an Essential package that ships in python:3.11-slim itself, so the
#   finding cannot be dropped by removing git either. forky's perl 5.42 requires
#   glibc 2.43, i.e. replacing libc6 in the runtime image, which is not an acceptable
#   trade for these issues.
# - openssl CVE-2026-14456 (High). Upstream rates this Low and fixes it in 3.5.8,
#   which is unreleased; no Debian suite (including sid) has a fix. It only affects
#   an OpenSSL QUIC *server* (SSL listener object), which the runner never creates.

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
# kubectl is the only Go binary in the image, so it is what Go stdlib CVEs are reported
# against. The channel is deliberately left unpinned (latest patch of v1.35), which is
# what moved the reported go 1.25.12 (kubectl 1.35.7) up to go 1.26.5 (kubectl 1.35.8).
# CVE-2026-39821, CVE-2026-33818, CVE-2026-56853, CVE-2026-56858, CVE-2026-56859,
# CVE-2026-56860, CVE-2026-56862, CVE-2026-56864, CVE-2026-56865 need go 1.25.13 /
# 1.26.6 (released 2026-08-13); no Kubernetes patch release is built with those yet
# (1.35.8 and 1.36.4 are both go 1.26.5), so a rebuild once the next patch ships is
# what clears them - there is nothing to pin here.
COPY --from=builder /app/Release.key /etc/apt/keyrings/kubernetes-apt-keyring.asc
RUN chmod 0644 /etc/apt/keyrings/kubernetes-apt-keyring.asc \
    && echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.asc] https://pkgs.k8s.io/core:/stable:/v1.35/deb/ /' | tee /etc/apt/sources.list.d/kubernetes.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends kubectl \
    && rm -rf /var/lib/apt/lists/*

# Run the application
# -u disables stdout buffering https://stackoverflow.com/questions/107705/disable-output-buffering
CMD [ "python3", "-u", "-m", "robusta.runner.main"]
