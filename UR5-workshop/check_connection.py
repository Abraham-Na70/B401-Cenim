"""
Campus VPN Connection & Diagnostic Tool.
Run this on PC 1 (outside campus) to verify network reachability and firewall port status
to PC 2 (inside the campus lab) before running the robot commander.

Usage:
    python3 check_connection.py <PC2_IP> [--port 8765]
"""

import argparse
import asyncio
import os
import platform
import socket
import subprocess
import sys
import time
import websockets

from network_protocol import MessageType, NetworkMessage, make_handshake


def get_local_vpn_ips():
    """Detects local IP addresses, especially VPN interfaces (tun, tap, wg, ppp)."""
    ips = []
    try:
        if platform.system() != "Windows":
            output = subprocess.check_output(["ip", "-br", "a"], text=True)
            for line in output.strip().split("\n"):
                parts = line.split()
                if len(parts) >= 3 and parts[1] == "UP":
                    iface = parts[0]
                    ip_cidr = parts[2]
                    ips.append((iface, ip_cidr))
    except Exception:
        pass
    return ips


def ping_host(host: str, count: int = 3) -> tuple[bool, str]:
    """Pings the target host using system ping."""
    param = "-n" if platform.system().lower() == "windows" else "-c"
    timeout_param = "-w" if platform.system().lower() == "windows" else "-W"
    cmd = ["ping", param, str(count), timeout_param, "2", host]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        # Parse average round-trip time
        return True, "Ping responded successfully"
    except subprocess.CalledProcessError:
        return False, "Ping timed out or host unreachable"
    except Exception as e:
        return False, str(e)


def check_tcp_port(host: str, port: int, timeout: float = 3.0) -> tuple[bool, float]:
    """Checks if the TCP port is open and listening."""
    start = time.time()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        elapsed = (time.time() - start) * 1000
        if result == 0:
            return True, elapsed
        else:
            return False, elapsed
    except Exception:
        return False, 0.0


async def check_websocket_handshake(host: str, port: int, timeout: float = 5.0) -> tuple[bool, str]:
    """Tests an actual WebSocket handshake with robot_server."""
    uri = f"ws://{host}:{port}"
    try:
        async with websockets.connect(uri, close_timeout=2) as ws:
            handshake = make_handshake(client_id="connection_diagnostic")
            await ws.send(handshake.to_json())
            raw_reply = await asyncio.wait_for(ws.recv(), timeout=timeout)
            reply = NetworkMessage.from_json(raw_reply)
            if reply.msg_type == MessageType.HANDSHAKE_ACK:
                status = reply.payload.get("server_status", "UNKNOWN")
                actions = len(reply.payload.get("available_actions", []))
                return True, f"Handshake verified! Robot status: {status}, Actions: {actions}"
            return False, f"Unexpected message: {reply.msg_type}"
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(
        description="Verify network connectivity from PC 1 to PC 2 across Campus VPN"
    )
    parser.add_argument(
        "host",
        nargs="?",
        default="127.0.0.1",
        help="IP address of PC 2 (Campus Lab PC)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Target port on PC 2 (default: 8765)",
    )

    args = parser.parse_args()
    target_host = args.host
    target_port = args.port

    print("\n" + "=" * 70)
    print(" 🔍 CAMPUS VPN & ROBOT NETWORK REACHABILITY DIAGNOSTIC")
    print(f" Target PC 2 IP : {target_host}")
    print(f" Target Port    : {target_port}")
    print("=" * 70)

    # 1. Local Network / VPN Interfaces
    local_ifaces = get_local_vpn_ips()
    print("\n[Step 1/4] Checking Local Network Interfaces on PC 1:")
    vpn_active = False
    for iface, ip in local_ifaces:
        is_vpn = any(k in iface.lower() for k in ["tun", "tap", "wg", "ppp", "vpn"]) or ip.startswith("10.")
        mark = " (Likely Campus VPN)" if is_vpn else ""
        if is_vpn:
            vpn_active = True
        print(f"  • Interface: {iface:<12} IP: {ip:<18}{mark}")

    if not vpn_active and target_host not in ("127.0.0.1", "localhost"):
        print("  ⚠️  Notice: No active VPN interface (tun/wg/ppp) detected.")
        print("     Ensure your Campus VPN client (OpenVPN, Cisco AnyConnect, etc.) is connected.")

    # 2. ICMP Ping Test
    print(f"\n[Step 2/4] Testing ICMP Ping to {target_host} ...")
    ping_ok, ping_msg = ping_host(target_host)
    if ping_ok:
        print(f"  ✅ Host is reachable via ICMP: {ping_msg}")
    else:
        print(f"  ⚠️  Ping failed: {ping_msg}")
        print("     (Note: Some campus firewalls block ICMP ping while still allowing TCP).")

    # 3. TCP Port Check
    print(f"\n[Step 3/4] Testing TCP Connection to {target_host}:{target_port} ...")
    tcp_ok, rtt_ms = check_tcp_port(target_host, target_port)
    if tcp_ok:
        print(f"  ✅ TCP Port {target_port} is OPEN! (Round-trip time: {rtt_ms:.1f}ms)")
    else:
        print(f"  ❌ TCP Port {target_port} is CLOSED or BLOCKED by firewall.")
        print("\n  🛠️  Troubleshooting Checklist for PC 2 (Campus Lab PC):")
        print("     1. Is 'robot_server.py' running on PC 2?")
        print("        Command on PC 2: python3 robot_server.py --port 8765")
        print("     2. Did you open the firewall on PC 2?")
        print("        Command on PC 2: sudo ufw allow 8765/tcp")
        print("     3. Did your PC 2 IP address change?")
        print("        Check on PC 2: hostname -I")
        print("=" * 70 + "\n")
        sys.exit(1)

    # 4. WebSocket Handshake Check
    print(f"\n[Step 4/4] Testing Application WebSocket Handshake ...")
    ws_ok, ws_msg = asyncio.run(check_websocket_handshake(target_host, target_port))
    if ws_ok:
        print(f"  ✅ {ws_msg}")
        print("\n" + "=" * 70)
        print(" 🎉 ALL CHECKS PASSED! Connection between PC 1 and PC 2 is 100% READY.")
        print(f" You can now send robot commands from PC 1 using:")
        print(f"   python3 commander_station.py --host {target_host} \"Your command here\"")
        print(f"   python3 commander_station.py --host {target_host} --interactive")
        print("=" * 70 + "\n")
    else:
        print(f"  ❌ WebSocket handshake failed: {ws_msg}")
        print("=" * 70 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
