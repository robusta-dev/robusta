# docker build -t docs -f docs.Dockerfile .
# run -it --rm -p 8000:8000  -v ~/.kube:/root/.kube  -v ${PWD}:/robusta <image-name>
FROM python:3.9
ENV ENV_TYPE=DEV 
RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs git ssh socat wget curl libcairo2 python3-dev libffi-dev socat \
    && pip3 install --no-cache-dir --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -
RUN mv /root/.local/bin/poetry /usr/local/bin
WORKDIR /robusta
RUN poetry config virtualenvs.create false
RUN pip install -U robusta-cli --no-cache
COPY . /robusta/
# RUN poetry install --extras "all"
EXPOSE 8000

# CMD ["./docs_autobuild.sh", "--host 0.0.0.0"]
CMD ["/bin/bash"]