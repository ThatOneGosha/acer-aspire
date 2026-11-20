#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -eq 0 ]; then
    echo "ОШИБКА: Запускай от обычного пользователя (без sudo/root)!"
    exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== [1/5] Снос Dropbear и установка OpenSSH + Mosh + Tailscale ==="
sudo xbps-remove -y dropbear 2>/dev/null || true
sudo xbps-install -Sy openssh mosh tailscale sops

echo "=== [2/5] Включение служб runit (sshd, tailscaled) ==="
[ -L /var/service/sshd ] || sudo ln -s /etc/sv/sshd /var/service/
[ -L /var/service/tailscaled ] || sudo ln -s /etc/sv/tailscaled /var/service/
sudo sv up sshd tailscaled

echo "=== [3/5] Настройка SSH-доступа (железные права и ключ) ==="
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
chmod 755 "$HOME"

PUB_KEY="$(sops -d --output-type raw --extract '["netbook_ssh"]["public_key"]' secrets/ssh.yaml | tr -d '\r\n')"
touch "$HOME/.ssh/authorized_keys"
chmod 600 "$HOME/.ssh/authorized_keys"

if ! grep -qxF "$PUB_KEY" "$HOME/.ssh/authorized_keys"; then
    echo "$PUB_KEY" >> "$HOME/.ssh/authorized_keys"
fi

echo "=== [4/5] Поднятие Tailscale намертво (без Tailscale SSH) ==="
TS_KEY="$(sops -d --output-type raw --extract '["key"]' secrets/tailscale.yaml | tr -d '\r\n')"
sudo tailscale up --auth-key="$TS_KEY" --hostname=home-pc --ssh=false --reset

echo "=== [5/5] Запрет сна при закрытии крышки ==="
if [ -f /etc/elogind/logind.conf ]; then
    sudo sed -i 's/^#*HandleLidSwitch=.*/HandleLidSwitch=ignore/' /etc/elogind/logind.conf
    sudo sed -i 's/^#*HandleLidSwitchExternalPower=.*/HandleLidSwitchExternalPower=ignore/' /etc/elogind/logind.conf
    sudo sed -i 's/^#*HandleLidSwitchDocked=.*/HandleLidSwitchDocked=ignore/' /etc/elogind/logind.conf
fi

PC_IP="$(tailscale ip -4)"
echo "=========================================="
echo "ПК ГОТОВ НАМЕРТВО!"
echo "Для подключения с нетбука используй:"
echo "mosh $USER@$PC_IP"
echo "=========================================="
