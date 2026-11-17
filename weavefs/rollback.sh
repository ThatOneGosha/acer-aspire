#!/usr/bin/env bash
set -euo pipefail

prefix="${1:-pure}"
profile="${2:-default}"

RECIPES_DIR="/etc/weavefs"

source="/tmp/${prefix}-rollback-$(date +%Y%m%d_%H%M%S_%N)"
target="/mnt/acer-disk-bottom/@root"

true > "$source"
shopt -s nullglob

for recipe in "${RECIPES_DIR}"/*.json; do
    echo "# $recipe" >> "$source"
    weavefs --recipe "$recipe" --profile "$profile" --pipe rollback "$prefix" | tee -a "$source"
done

weavefs --set-writable burn --src "$source" --dst "$target"
