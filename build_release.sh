export DOCKER_BUILDKIT=1

docker buildx build \
  --platform linux/arm64,linux/amd64 \
  --cache-from us-central1-docker.pkg.dev/genuine-flight-317411/devel/robusta-runner:cache \
  --tag $IMAGE \
  --tag us-central1-docker.pkg.dev/genuine-flight-317411/devel/robusta-runner:cache \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --push \
  $BUILD_CONTEXT