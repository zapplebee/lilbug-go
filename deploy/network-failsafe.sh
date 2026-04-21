#!/bin/sh
set -eu

AP_CONN="lilbug-rover"

sleep 60

if /usr/sbin/ip route | grep -q '^default '; then
  exit 0
fi

if /usr/bin/nmcli -t -f NAME connection show --active | grep -Fxq "$AP_CONN"; then
  exit 0
fi

/usr/local/bin/network-rollback.sh
