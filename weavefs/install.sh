#!/usr/bin/env bash
set -euo pipefail
sudo curl -L -o /usr/local/bin/weavefs https://github.com/ThatOneGosha/weavefs/releases/download/v2026.08.21/weavefs \
  && sudo chmod +x /usr/local/bin/weavefs
