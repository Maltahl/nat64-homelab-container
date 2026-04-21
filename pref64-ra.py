#!/usr/bin/env python3
import socket
import struct
import time
import os
import subprocess
import sys


def get_link_local(iface):
    r = subprocess.run(
        ['ip', '-6', 'addr', 'show', 'dev', iface, 'scope', 'link'],
        capture_output=True, text=True
    )
    for line in r.stdout.splitlines():
        line = line.strip()
        if line.startswith('inet6'):
            return line.split()[1].split('/')[0]
    return None


def checksum(src, dst, payload):
    ph = (socket.inet_pton(socket.AF_INET6, src) +
          socket.inet_pton(socket.AF_INET6, dst) +
          struct.pack('!I', len(payload)) + b'\x00\x00\x00\x3a')
    data = ph + payload
    if len(data) % 2:
        data += b'\x00'
    s = sum(struct.unpack('!H', data[i:i+2])[0] for i in range(0, len(data), 2))
    s = (s >> 16) + (s & 0xffff)
    s += s >> 16
    return ~s & 0xffff


def send_pref64_ra(iface, prefix='64:ff9b::', prefix_len=96, lifetime=1800, interval=30):
    src = get_link_local(iface)
    if not src:
        print(f'No link-local address on {iface}', flush=True)
        sys.exit(1)

    plc = {96: 0, 64: 1, 56: 2, 48: 3, 40: 4, 32: 5}[prefix_len]
    slpl = (((lifetime // 8) & 0x1fff) << 3) | plc
    prefix_bytes = socket.inet_pton(socket.AF_INET6, prefix)[:12]
    pref64_opt = struct.pack('!BBH', 38, 2, slpl) + prefix_bytes

    dst = 'ff02::1'
    iface_idx = socket.if_nametoindex(iface)

    sock = socket.socket(socket.AF_INET6, socket.SOCK_RAW, socket.IPPROTO_ICMPV6)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 255)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, iface_idx)

    print(f'Sending PREF64 RAs on {iface} ({prefix}/{prefix_len}) every {interval}s', flush=True)
    while True:
        pkt = struct.pack('!BBH', 134, 0, 0) + struct.pack('!BBHII', 0, 0x18, 0, 0, 0) + pref64_opt
        csum = checksum(src, dst, pkt)
        pkt = pkt[:2] + struct.pack('!H', csum) + pkt[4:]
        sock.sendto(pkt, (dst, 0, 0, iface_idx))
        print('Sent PREF64 RA', flush=True)
        time.sleep(interval)


send_pref64_ra(os.environ.get('RADVD_LAN_IFACE', 'eth0'))
