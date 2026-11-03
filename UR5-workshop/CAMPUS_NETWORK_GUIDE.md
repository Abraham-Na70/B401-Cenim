# Distributed Robot Teleoperation: Campus VPN Setup & Deployment Guide

This guide explains how to operate your robot arm remotely when **PC 1 (Commander / Operator)** is located outside the campus network (e.g. at home) and **PC 2 (Robot Controller)** is located inside the campus lab.

---

## Architecture Overview

```
[PC 1: Home / Off-Campus]
  │ (User: "Pick up the blue block and put it in the bin")
  │ -> DeepSeek API plans action sequence: ["move to home", "reach target", ...]
  │
  ▼ [Campus VPN Client: Cisco AnyConnect / OpenVPN / FortiClient]
═════════════════════════════════════════════════════════════════════
  │ (Encrypted VPN Tunnel through Campus Gateway)
  ▼
[Campus Lab Subnet: 10.x.x.x or 172.x.x.x]
  │
  ▼
[PC 2: Campus Lab Workstation]
  │ -> robot_server.py listens on port 8765
  │ -> Validates and executes action sequence step-by-step
  │ -> Streams real-time progress back to PC 1
  ▼
[Robot Arm Hardware / Simulation]
```

---

## Step 1: Prepare PC 2 (Campus Lab Computer)

Run these steps on **PC 2** inside the lab:

### 1. Find PC 2's Campus IP Address

Open terminal on PC 2 and run:

```bash
hostname -I
```

or

```bash
ip -br a
```

_Look for an IP like `10.x.x.x`, `172.16.x.x`, or `192.168.x.x` (write this down as `<PC2_CAMPUS_IP>`)._

### 2. Allow Incoming Port 8765 on Linux Firewall (UFW)

Ensure the local Ubuntu firewall allows incoming connections on port 8765:

```bash
sudo ufw allow 8765/tcp
```

### 3. Start the Robot Controller Server

```bash
# For simulation mode:
python3 robot_server.py --port 8765

# Or for real physical hardware mode:
python3 robot_server.py --port 8765 --hardware
```

Leave this running in the lab terminal.

---

## Step 2: Prepare PC 1 (Home / Off-Campus Computer)

Run these steps on **PC 1** at home:

### 1. Connect to Campus VPN

Start your university's VPN client (e.g., OpenVPN, Cisco Secure Client / AnyConnect, GlobalProtect, or WireGuard) and log in.

### 2. Verify Connectivity with the Diagnostic Tool

Before sending robot commands, verify that your VPN routes traffic to the lab subnet:

```bash
python3 check_connection.py <PC2_CAMPUS_IP>
```

_This tool automatically checks local VPN interfaces, pings PC 2, tests TCP port 8765, and performs a live application handshake._

---

## Step 3: Send Natural Language Robot Commands from PC 1

Once `check_connection.py` reports success, you can command the robot from home!

### A. Send a Single Command

```bash
python3 commander_station.py --host <PC2_CAMPUS_IP> "Pick up the blue block from the table and put it in the bin"
```

### B. Interactive REPL Session

```bash
python3 commander_station.py --host <PC2_CAMPUS_IP> --interactive
```

### C. Emergency Stop (E-STOP)

- While a plan is executing, press **`Ctrl+C`** in the terminal on PC 1.
- Or type **`estop`** in interactive mode.
- PC 1 immediately transmits an `EMERGENCY_STOP` packet, and PC 2 aborts arm motion instantly.

---

## Troubleshooting & Campus Network Firewalls

### Case 1: `check_connection.py` reports "Ping failed" or "Port 8765 closed"

- **Cause**: Some campus IT networks isolate the VPN subnet from general lab subnets and block incoming ports to lab workstations.
- **Solution 1 (Lab Static Route)**: Ask your lab network admin to allow port 8765 from the campus VPN subnet to PC 2's IP.
- **Solution 2 (Zero-Config Mesh with Tailscale)**:
  If campus IT blocks cross-subnet traffic, install [Tailscale](https://tailscale.com) on both PC 1 and PC 2:
  1. On PC 2: `curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up`
  2. On PC 1: Install Tailscale and log in with the same free account.
  3. Tailscale gives PC 2 a static private IP (e.g. `100.x.x.x`) that traverses any campus NAT or firewall with WireGuard encryption.
  4. Run:
     ```bash
     python3 commander_station.py --host 100.x.x.x "Pick up the wrench"
     ```

---

## Connecting Real Robot Arm Hardware

In `robot_server.py`, locate the `execute_hardware_action` method in `RobotArmExecutor`:

```python
def execute_hardware_action(self, action: str):
    # Example for Serial / USB microcontroller:
    # serial_port.write(f"{action}\n".encode())

    # Example for ROS 2:
    # ros2_node.send_action_goal(action)

    # Example for Dynamixel / Robot SDK:
    # dxl_arm.execute_named_trajectory(action)
```

When running with `--hardware`, `robot_server.py` invokes this method for each step in the action plan.
