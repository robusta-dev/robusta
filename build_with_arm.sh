docker buildx build \
  --platform linux/arm64,linux/amd64  \
  --tag $IMAGE \
  --push=$PUSH_IMAGE \
  $BUILD_CONTEXT