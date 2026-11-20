#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -eq 0 ]; then
    echo "ОШИБКА: Запускай от обычного пользователя (без sudo/root)!"
    exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== [1/4] Снос Dropbear и установка OpenSSH + Mosh + Tailscale ==="
sudo xbps-remove -y dropbear 2>/dev/null || true
sudo xbps-install -Sy openssh mosh tailscale sops

echo "=== [2/4] Включение служб runit (sshd, tailscaled) ==="
[ -L /var/service/sshd ] || sudo ln -s /etc/sv/sshd /var/service/
[ -L /var/service/tailscaled ] || sudo ln -s /etc/sv/tailscaled /var/service/
sudo sv up sshd tailscaled

echo "=== [3/4] Установка и валидация приватного ключа ==="
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

sops -d --output-type raw --extract '["netbook_ssh"]["private_key"]' secrets/ssh.yaml > "$HOME/.ssh/id_ed25519"
echo "" >> "$HOME/.ssh/id_ed25519"
chmod 600 "$HOME/.ssh/id_ed25519"

# Жесткая проверка, что OpenSSH съел ключ без ошибок
ssh-keygen -y -f "$HOME/.ssh/id_ed25519" > /dev/null

echo "=== [4/4] Поднятие Tailscale намертво ==="
TS_KEY="$(sops -d --output-type raw --extract '["key"]' secrets/tailscale.yaml | tr -d '\r\n')"
sudo tailscale up --auth-key="$TS_KEY" --hostname=acer-aspire --ssh=false --reset

echo "=========================================="
echo "НЕТБУК ГОТОВ НАМЕРТВО!"
echo "Список машин в сети:"
tailscale status
echo "=========================================="
