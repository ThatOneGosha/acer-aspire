#!/usr/bin/env bash
set -euo pipefail

prefix="${1:-pure}"
profile="${2:-default}"

RECIPES_DIR="/etc/weavefs"

source="/tmp/${prefix}-deploy-$(date +%Y%m%d_%H%M%S_%N)"
target="/mnt/acer-disk-bottom/@snapshots/${prefix}.@root"

true > "$source"
shopt -s nullglob

for recipe in "${RECIPES_DIR}"/*.json; do
    echo "# $recipe" >> "$source"
    weavefs --recipe "$recipe" --profile "$profile" --pipe deploy "$prefix" | tee -a "$source"
done

weavefs burn --src "$source" --dst "$target"
