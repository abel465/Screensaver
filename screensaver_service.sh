#!/bin/bash
set -euo pipefail

scriptdir="$( dirname -- "$BASH_SOURCE"; )";
root_geo=$(xwininfo -root | awk -F'[ +]' '$3 ~ /-geometry/ {print $4}')

while sleep 60; do
    xwininfo -root -tree | grep $root_geo | grep -qv "\(Desktop\|has no name\)" \
        || (( $(xprintidle) < 60000 )) \
        || $scriptdir/screensaver_from_config.py
done
