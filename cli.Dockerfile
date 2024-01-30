# docker build -t robusta-cli -f cli.Dockerfile .
# docker run -it --rm --net host -v ~/.aws:/root/.aws -v ~/.config/gcloud:/root/.config/gcloud -v ${PWD}:/workingdir -w=/workingdir -v ~/.kube:/root/.kube robusta-cli robusta gen-config
FROM python:3.9-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl \
       gnupg \
       lsb-release \
       unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Google Cloud SDK and Gcloud Auth Plugin
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -

RUN apt-get update \
    && apt-get install -y google-cloud-sdk google-cloud-sdk-gke-gcloud-auth-plugin \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf awscliv2.zip ./aws

# Install Kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin

RUN pip install -U robusta-cli --no-cache

CMD ["/bin/sh"]
