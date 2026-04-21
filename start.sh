#!/bin/bash
set -e
cat > /etc/tayga.conf << EOF
tun-device nat64
ipv6-addr ${NAT64_IPV6_ADDR}
prefix 64:ff9b::/96
ipv4-addr ${NAT64_IPV4_GW}
dynamic-pool ${NAT64_IPV4_POOL}
data-dir /var/db/tayga
EOF
ip tuntap del dev nat64 mode tun 2>/dev/null || true
tayga --mktun
ip link set nat64 up
ip link set nat64 mtu 8980
ip addr add ${NAT64_IPV4_GW} dev nat64
ip route add 64:ff9b::/96 dev nat64 || true
ip route add ${NAT64_IPV4_POOL} dev nat64 || true
sysctl -w net.ipv4.ip_forward=1
sysctl -w net.ipv6.conf.all.forwarding=1
iptables -t nat -C POSTROUTING -s ${NAT64_IPV4_POOL} -j MASQUERADE 2>/dev/null || \
    iptables -t nat -A POSTROUTING -s ${NAT64_IPV4_POOL} -j MASQUERADE
python3 /pref64-ra.py &
exec tayga --nodetach --config /etc/tayga.conf
