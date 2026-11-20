#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -eq 0 ]; then
    echo "Запускай от обычного юзера ПК (не root)!"
    exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== [1/4] Пакеты и службы (Void Linux) ==="
sudo xbps-remove -y dropbear 2>/dev/null || true
sudo xbps-install -Sy openssh mosh tailscale sops
[ -L /var/service/sshd ] || sudo ln -s /etc/sv/sshd /var/service/
[ -L /var/service/tailscaled ] || sudo ln -s /etc/sv/tailscaled /var/service/
sudo sv restart sshd tailscaled

echo "=== [2/4] Железные права и ключ доступа ==="
chmod 755 "$HOME"
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

sops -d --output-type raw --extract '["netbook_ssh"]["public_key"]' secrets/ssh.yaml | tr -d '\r\n' > "$REPO_ROOT/ssh/authorized.pub"
echo "" >> "$REPO_ROOT/ssh/authorized.pub"
cp "$REPO_ROOT/ssh/authorized.pub" "$HOME/.ssh/authorized_keys"
chmod 600 "$HOME/.ssh/authorized_keys"

echo "=== [3/4] Tailscale без перехвата SSH ==="
TS_KEY="$(sops -d secrets/tailscale.yaml | grep -oE 'tskey-auth-[A-Za-z0-9_-]+' | head -n 1)"
sudo tailscale up --auth-key="$TS_KEY" --hostname=home-pc --ssh=false --reset

echo "=== [4/4] Запрет сна при закрытии крышки ==="
if [ -f /etc/elogind/logind.conf ]; then
    sudo sed -i 's/^#*HandleLidSwitch=.*/HandleLidSwitch=ignore/' /etc/elogind/logind.conf
    sudo sed -i 's/^#*HandleLidSwitchExternalPower=.*/HandleLidSwitchExternalPower=ignore/' /etc/elogind/logind.conf
    sudo sed -i 's/^#*HandleLidSwitchDocked=.*/HandleLidSwitchDocked=ignore/' /etc/elogind/logind.conf
fi

echo "=========================================="
echo "ПК ГОТОВ НАМЕРТВО!"
echo "Твой пользователь: $USER | Tailscale IP: $(tailscale ip -4)"
echo "Запушь ssh/authorized.pub в git и запускай setup-netbook.sh на ноуте."
echo "=========================================="
