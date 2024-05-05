export DOCKER_BUILDKIT=1

docker pull robustadev/robusta-runner-dev:cache

docker buildx build \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --platform linux/arm64,linux/amd64 \
  --cache-from robustadev/robusta-runner-dev:cache \
  --tag $IMAGE \
  --tag robustadev/robusta-runner:cache \
  --push \
  $BUILD_CONTEXT