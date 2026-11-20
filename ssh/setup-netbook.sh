#!/usr/bin/env bash
set -euo pipefail

SUDO=""
[ "$(id -u)" -ne 0 ] && SUDO="sudo"

REAL_USER="$(id -un)"
REAL_HOME="$(getent passwd "$REAL_USER" | cut -d: -f6)"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== [1/4] Снос Dropbear и установка OpenSSH + Mosh + Tailscale ==="
$SUDO xbps-remove -y dropbear 2>/dev/null || true
$SUDO xbps-install -Sy openssh mosh tailscale sops
[ -L /var/service/sshd ] || $SUDO ln -s /etc/sv/sshd /var/service/
[ -L /var/service/tailscaled ] || $SUDO ln -s /etc/sv/tailscaled /var/service/
$SUDO sv restart tailscaled

echo "=== [2/4] Извлечение и проверка приватного ключа в $REAL_HOME/.ssh ==="
mkdir -p "$REAL_HOME/.ssh"
chmod 700 "$REAL_HOME/.ssh"

sops -d --output-type raw --extract '["netbook_ssh"]["private_key"]' secrets/ssh.yaml > "$REAL_HOME/.ssh/id_ed25519"
echo "" >> "$REAL_HOME/.ssh/id_ed25519"
chmod 600 "$REAL_HOME/.ssh/id_ed25519"

# Проверяем, что ключ валиден и совпадает с публичным ключом ПК
GEN_PUB="$(ssh-keygen -y -f "$REAL_HOME/.ssh/id_ed25519")"
if [ -f "$REPO_ROOT/ssh/authorized.pub" ]; then
    REPO_PUB="$(awk '{print $1" "$2}' "$REPO_ROOT/ssh/authorized.pub")"
    if [ "$GEN_PUB" != "$REPO_PUB" ]; then
        echo "ОШИБКА: Приватный ключ не совпадает с ssh/authorized.pub!"
        exit 1
    fi
fi

echo "=== [3/4] Поднятие Tailscale ==="
TS_KEY="$(sops -d secrets/tailscale.yaml | grep -oE 'tskey-auth-[A-Za-z0-9_-]+' | head -n 1)"
$SUDO tailscale up --auth-key="$TS_KEY" --hostname=acer-aspire --ssh=false --reset
sleep 2

echo "=== [4/4] Создание алиаса home-pc в $REAL_HOME/.ssh/config ==="
PC_IP="$(tailscale status | awk '/home-pc/ {print $1; exit}')"
cat <<EOF > "$REAL_HOME/.ssh/config"
Host home-pc
    HostName ${PC_IP:-100.69.134.9}
    User rc502
    IdentityFile $REAL_HOME/.ssh/id_ed25519
    IdentitiesOnly yes
    StrictHostKeyChecking accept-new
EOF
chmod 600 "$REAL_HOME/.ssh/config"

echo "=========================================="
echo "НОУТ ГОТОВ НАМЕРТВО!"
echo "Теперь вход на ПК всегда одной командой: mosh home-pc"
echo "=========================================="
