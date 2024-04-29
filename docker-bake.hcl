variable "TAG" {
  default = "$TAG"
}

target "default" {
  dockerfile = "Dockerfile"
  tags = ["us-central1-docker.pkg.dev/genuine-flight-317411/devel/${TAG}"]
  context = "."
}