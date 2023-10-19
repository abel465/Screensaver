#!/bin/bash
set -euo pipefail

type=$(loginctl show-session $(loginctl | grep "$USER" | awk '{print $1}') -p Type | cut -c 6-)
scriptdir="$( dirname -- "$BASH_SOURCE"; )";

if [ "$type" = "x11" ]; then
  root_geo=$(xwininfo -root | awk -F'[ +]' '$3 ~ /-geometry/ {print $4}')

  while sleep 60; do
      xwininfo -root -tree | grep $root_geo | grep -qv "\(Desktop\|has no name\)" \
          || (( $(xprintidle) < 60000 )) \
          || $scriptdir/screensaver_from_config.py
  done
else
  swayidle -w timeout 60 $scriptdir/screensaver_from_config.py
fi
