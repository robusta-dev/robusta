docker buildx build \
  --platform linux/amd64 \
  --tag $IMAGE \
  --push \
  $BUILD_CONTEXT