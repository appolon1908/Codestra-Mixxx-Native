#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
install -Dm755 "$SCRIPT_DIR/start-native-mixxx.sh" /home/codestra/DJONE-Mixxx/runtime/start-mixxx.sh
install -Dm644 "$SCRIPT_DIR/djone-mixxx.service" /home/codestra/.config/systemd/user/djone-mixxx.service
sudo install -Dm644 "$SCRIPT_DIR/djone-mixxx-relay.service" /etc/systemd/system/djone-mixxx-relay.service
systemctl --user daemon-reload
systemctl --user enable --now djone-mixxx.service
sudo systemctl daemon-reload
sudo systemctl enable --now djone-mixxx-relay.service
