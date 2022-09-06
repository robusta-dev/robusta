docker buildx build \
  --platform linux/arm64,linux/amd64  \
  --tag $IMAGE \
  --push \
  $BUILD_CONTEXT