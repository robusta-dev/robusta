export DOCKER_BUILDKIT=1

docker pull us-central1-docker.pkg.dev/genuine-flight-317411/devel/robusta-runner:cache

docker buildx build \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --platform linux/arm64,linux/amd64 \
  --cache-from us-central1-docker.pkg.dev/genuine-flight-317411/devel/robusta-runner:cache \
  --tag $IMAGE \
  --tag robustadev/robusta-runner:cache \
  --push \
  $BUILD_CONTEXT