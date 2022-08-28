FROM python:3.9-slim

RUN apt-get update \
    && dpkg --add-architecture arm64 \
    && apt-get install -y --no-install-recommends ssh curl python3-dev libffi-dev gcc \
    && pip install ruamel.yaml.clib \
    && curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*

RUN chmod +x kubectl
RUN mv ./kubectl /usr/local/bin
RUN pip install -U robusta-cli --no-cache

CMD ["/bin/sh"]