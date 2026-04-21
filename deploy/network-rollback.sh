#!/bin/sh
set -eu

AP_CONN="lilbug-rover"
FORWARDING_FILE="/etc/sysctl.d/90-lilbug-forwarding.conf"
BACKUP_DIR="/var/backups/lilbug-network"
HOSTAPD_CONF="/etc/hostapd/hostapd.conf"
DNSMASQ_DROPIN="/etc/dnsmasq.d/lilbug-rover.conf"

log() {
  logger -t lilbug-network "$1"
  printf '%s\n' "$1"
}

log "running network rollback"

mkdir -p "$BACKUP_DIR"

if [ -f "$FORWARDING_FILE" ]; then
  rm -f "$FORWARDING_FILE"
  /usr/sbin/sysctl -q -w net.ipv4.ip_forward=0 || true
fi

/usr/bin/systemctl stop hostapd dnsmasq 2>/dev/null || true

if [ -f "$HOSTAPD_CONF" ]; then
  rm -f "$HOSTAPD_CONF"
fi

if [ -f "$DNSMASQ_DROPIN" ]; then
  rm -f "$DNSMASQ_DROPIN"
fi

/usr/sbin/ip addr flush dev wlan1 || true
/usr/bin/nmcli device set wlan1 managed yes || true

if /usr/sbin/nft list table ip lilbugnat >/dev/null 2>&1; then
  /usr/sbin/nft delete table ip lilbugnat || true
fi

if /usr/bin/nmcli -t -f NAME connection show | grep -Fxq "$AP_CONN"; then
  /usr/bin/nmcli connection modify "$AP_CONN" connection.autoconnect no || true
  /usr/bin/nmcli connection down "$AP_CONN" || true
  /usr/bin/nmcli connection delete "$AP_CONN" || true
fi

/usr/bin/systemctl restart NetworkManager

log "network rollback complete"
