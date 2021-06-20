set -o xtrace
telepresence connect
telepresence intercept -n robusta robusta-runner --port 5000:http --env-file example.env
# on WSL we also run socat to forward traffic from wsl to windows
if grep -qi microsoft /proc/version; then
  # put your Windows public IP here, but don't the Windows WSL ip because it doesn't work :(
  socat tcp-listen:5000,fork tcp:192.168.14.97:5000
fi

telepresence leave robusta-runner-robusta

