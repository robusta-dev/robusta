export DOCKER_BUILDKIT=1

docker buildx build \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --platform linux/arm64,linux/amd64 \
  --tag $IMAGE \
  --tag robustadev/robusta-runner:cache \
  --push \
  $BUILD_CONTEXT