# Complete System Manual & Runbook: DeepSeek Distributed Robot Teleoperation

A complete, end-to-end operational guide for translating natural language instructions into strictly formatted robot arm actions using the **DeepSeek API**, and remotely transmitting them across a **Campus VPN** from **PC 1 (Operator at Home)** to **PC 2 (Robot Controller in Campus Lab)**.

---

## Table of Contents
1. [System Architecture](#1-system-architecture)
2. [Prerequisites & Installation](#2-prerequisites--installation)
3. [Robot Arm Action Space](#3-robot-arm-action-space)
4. [Step-by-Step Setup: PC 2 (Campus Lab Computer)](#4-step-by-step-setup-pc-2-campus-lab-computer)
5. [Step-by-Step Setup: PC 1 (Home Computer via Campus VPN)](#5-step-by-step-setup-pc-1-home-computer-via-campus-vpn)
6. [Emergency Stop (E-STOP) Safety Operation](#6-emergency-stop-e-stop-safety-operation)
7. [Local Single-Machine Testing (Loopback Development)](#7-local-single-machine-testing-loopback-development)
8. [Automated Verification & Benchmark Suites](#8-automated-verification--benchmark-suites)
9. [Hardware Integration: Connecting Real Robot Arms](#9-hardware-integration-connecting-real-robot-arms)
10. [Troubleshooting & Campus Firewall Workarounds](#10-troubleshooting--campus-firewall-workarounds)
11. [Quick Command Cheat Sheet](#11-quick-command-cheat-sheet)

---

## 1. System Architecture

```
┌────────────────────────────────────────────────────────┐
│                   PC 1: Home / Remote                  │
│                                                        │
│  User Input: "Pick up the blue cube and bin it"       │
│        │                                               │
│        ▼                                               │
│  DeepSeek API (deepseek-flash / Strict Tool Calling)  │
│        │                                               │
│        ▼                                               │
│  Strict Ordered Actions:                               │
│  ["move to home", "scan workspace", "reach target",    │
│   "open gripper", "close gripper", "lift arm", ...]    │
│        │                                               │
│        ▼                                               │
│  commander_station.py (WebSocket Client)               │
└────────────────────────┬───────────────────────────────┘
                         │
                         ▼
        ╔═════════════════════════════════╗
        ║    Campus VPN Encrypted Tunnel  ║
        ║   (10.x.x.x or 172.16.x.x IP)   ║
        ╚═════════════════════════════════╝
                         │
                         ▼
┌────────────────────────────────────────────────────────┐
│               PC 2: Campus Lab Workstation             │
│                                                        │
│  robot_server.py (WebSocket Server on Port 8765)       │
│        │                                               │
│        ├─► 1. Handshake & Liveness ACK                 │
│        ├─► 2. Validates plan against predefined enum   │
│        ├─► 3. Executes actions step-by-step            │
│        ├─► 4. Streams real-time progress to PC 1       │
│        └─► 5. Listens for Emergency Stop (E-STOP)      │
│                                                        │
│  Execution Engine: Simulation OR Physical Hardware     │
│  (USB Serial / ROS 2 / Dynamixel / UR Driver)          │
└────────────────────────────────────────────────────────┘
```

---

## 2. Prerequisites & Installation

### Hardware & Network Requirements
- **PC 1 (Commander)**: Any laptop or desktop with internet access and your university's **Campus VPN Client** (e.g. Cisco AnyConnect / Secure Client, OpenVPN, FortiClient, GlobalProtect).
- **PC 2 (Robot Controller)**: Lab computer connected to the campus network (via Ethernet or lab Wi-Fi) and physically hooked to your robot arm (or running simulation).

### Python Dependencies
Both machines require **Python 3.10+**. Install the dependencies:

```bash
pip install openai pydantic websockets
```

### Configure DeepSeek API Key (on PC 1)
On **PC 1**, set your DeepSeek API key (or `ANTHROPIC_AUTH_TOKEN`):

```bash
export DEEPSEEK_API_KEY="your-deepseek-api-key-here"
```

To persist it across terminal sessions:
```bash
echo 'export DEEPSEEK_API_KEY="your-deepseek-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

---

## 3. Robot Arm Action Space

All robot arm commands are constrained to an **immutable set of 10 atomic actions**. DeepSeek is strictly bound via JSON Schema `enum` to only select from these exact strings:

| Action String | Description |
| :--- | :--- |
| `"move to home"` | Returns arm to safe default resting configuration |
| `"scan workspace"` | Uses vision/depth sensor to locate objects and verify state |
| `"reach target"` | Trajectory planning to align end-effector above the target item |
| `"open gripper"` | Actuates end-effector jaws / suction gripper to release |
| `"close gripper"` | Actuates end-effector jaws to clamp / grip object |
| `"lift arm"` | Raises manipulator vertically to avoid collisions |
| `"lower arm"` | Descends manipulator toward surface |
| `"rotate base"` | Rotates waist / base joint toward target bin or workstation |
| `"rotate wrist"` | Rotates wrist / roll joint (e.g. pouring, turning) |
| `"wait"` | Pauses execution for settling or safety clearance |

To view the action list from the terminal:
```bash
python3 arm_planner.py --list-actions
```

---

## 4. Step-by-Step Setup: PC 2 (Campus Lab Computer)

Perform these steps on the **PC located in the campus robotics lab**:

### Step 4.1: Find PC 2's Campus IP Address
Open a terminal on PC 2 and run:
```bash
hostname -I
```
*(Alternatively: `ip -br a`)*

Look for an IP address assigned by the campus network (typically `10.x.x.x`, `172.16.x.x`, or `192.168.x.x`).  
**Write this down as `<PC2_CAMPUS_IP>`.**

### Step 4.2: Open Local Firewall Port (8765)
If PC 2 runs Ubuntu Linux, allow inbound TCP traffic on port `8765`:
```bash
sudo ufw allow 8765/tcp
```
Verify the firewall status:
```bash
sudo ufw status
```

### Step 4.3: Start the Robot Controller Server

#### Option A: Simulation Mode (Safe for dry-runs and development)
```bash
python3 robot_server.py --port 8765
```
*In simulation mode, each action is safely logged with simulated timing delays (default: 0.8s per step).*

#### Option B: Real Hardware Mode (Physical robot arm)
```bash
python3 robot_server.py --port 8765 --hardware
```
*In hardware mode, `robot_server.py` invokes the `execute_hardware_action()` hook for each step.*

Leave this terminal open and running in the lab.

---

## 5. Step-by-Step Setup: PC 1 (Home Computer via Campus VPN)

Perform these steps on your **home laptop/PC**:

### Step 5.1: Connect to Campus VPN
Launch your university's VPN client and connect. Ensure you are authenticated and have an active tunnel IP.

### Step 5.2: Test Network Reachability with the Diagnostic Tool
Before dispatching commands, run the automated diagnostic tool:

```bash
python3 check_connection.py <PC2_CAMPUS_IP>
```

#### Expected Healthy Output:
```text
======================================================================
 🔍 CAMPUS VPN & ROBOT NETWORK REACHABILITY DIAGNOSTIC
 Target PC 2 IP : 10.4.153.21
 Target Port    : 8765
======================================================================

[Step 1/4] Checking Local Network Interfaces on PC 1:
  • Interface: tun0         IP: 10.100.4.12/24    (Likely Campus VPN)

[Step 2/4] Testing ICMP Ping to 10.4.153.21 ...
  ✅ Host is reachable via ICMP: Ping responded successfully

[Step 3/4] Testing TCP Connection to 10.4.153.21:8765 ...
  ✅ TCP Port 8765 is OPEN! (Round-trip time: 14.2ms)

[Step 4/4] Testing Application WebSocket Handshake ...
  ✅ Handshake verified! Robot status: READY_IDLE, Actions: 10

======================================================================
 🎉 ALL CHECKS PASSED! Connection between PC 1 and PC 2 is 100% READY.
======================================================================
```

### Step 5.3: Transmit Robot Commands

#### Single Command Execution
```bash
python3 commander_station.py --host <PC2_CAMPUS_IP> "Pick up the blue block from the table and put it in the bin"
```

#### What Happens in the Terminal:
1. DeepSeek receives your natural language input.
2. DeepSeek generates the strictly validated action plan:
   `["move to home", "scan workspace", "reach target", "open gripper", "lower arm", "close gripper", "lift arm", "rotate base", "reach target", "lower arm", "open gripper", "move to home"]`
3. Plan is sent over the VPN to PC 2 via WebSocket.
4. PC 2 acknowledges and streams live step-by-step progress:
   ```text
   [██████████████░░░░░░░░░░░]  57.1% | Step 04/07: ✅ reach target (SUCCESS 0.81s)
   [█████████████████░░░░░░░░]  71.4% | Step 05/07: ⏳ close gripper (RUNNING 0.00s)
   ```
5. Displays final completion report.

#### Interactive REPL Session
To keep a continuous command session open:
```bash
python3 commander_station.py --host <PC2_CAMPUS_IP> --interactive
```

---

## 6. Emergency Stop (E-STOP) Safety Operation

Safety is paramount in remote robot teleoperation. This system implements an instant hardware abort protocol:

### How to Trigger an E-STOP:
1. **During Command Execution**: Press **`Ctrl+C`** in the terminal on PC 1.
2. **In Interactive REPL**: Type **`estop`**, **`stop`**, or **`abort`**.

### What Happens Behind the Scenes:
1. PC 1 sends a high-priority `EMERGENCY_STOP` packet over the WebSocket.
2. PC 2 catches the signal, immediately cancels the running execution task, and stops physical arm actuators.
3. PC 2 sends back `EMERGENCY_STOP_ACK` and marks the plan status as `ABORTED`.
4. The robot controller enters a safe idle state.

---

## 7. Local Single-Machine Testing (Loopback Development)

You can test the entire distributed pipeline on a single computer without needing the VPN or lab hardware:

### Terminal 1: Run Robot Server locally
```bash
python3 robot_server.py --port 8765 --step-delay 0.3
```

### Terminal 2: Run Commander Client
```bash
python3 commander_station.py --host 127.0.0.1 "Pick up the wrench on the bench and lift it up"
```

---

## 8. Automated Verification & Benchmark Suites

The repository contains three diagnostic test suites:

### 1. Teleoperation Integration Test Suite
Verifies network handshakes, real-time streaming, and emergency abort behavior:
```bash
python3 test_distributed_teleop.py
```
*(Runs an automated loopback server, dispatches multi-step plans, tests E-STOP, and checks assertion results).*

### 2. DeepSeek Tool Calling Strictness Suite
Evaluates DeepSeek API's server-side strictness rules (forced tool_choice rejection, conversation history sequencing, schema rejection, and Pydantic validation):
```bash
python3 test_strictness.py
```

### 3. 20-Prompt Benchmark & Hallucination Audit
Stress-tests DeepSeek across 20 diverse prompts (manipulation, complex multi-step, ambiguous, out-of-domain, adversarial injections):
```bash
python3 benchmark_20_prompts.py
```
*(Results and adherence logs are saved to `benchmark_results.json`).*

---

## 9. Hardware Integration: Connecting Real Robot Arms

In [`robot_server.py`](file:///home/faiq/data/kuliah/cenim/robot_server.py), the `RobotArmExecutor` class includes a clean integration hook:

```python
class RobotArmExecutor:
    def __init__(self, step_delay_seconds: float = 0.8, hardware_mode: bool = False):
        self.step_delay = step_delay_seconds
        self.hardware_mode = hardware_mode
        # Initialize your serial port or ROS 2 node here:
        # self.serial = serial.Serial('/dev/ttyUSB0', 115200)

    def execute_hardware_action(self, action: str):
        """
        HARDWARE HOOK:
        Replace or extend this method to send real commands to your robot arm:
        """
        logger.info(f"  [HARDWARE DRIVER] Executing physical action: '{action}'")

        # Example 1: Microcontroller / Arduino Serial
        # self.serial.write(f"{action}\n".encode())

        # Example 2: ROS 2 Action / Service Client
        # self.ros2_arm_client.send_goal(action)

        # Example 3: Dynamixel SDK / Custom Servos
        # self.dxl_controller.move_named_pose(action)
```

Launch with:
```bash
python3 robot_server.py --port 8765 --hardware
```

---

## 10. Troubleshooting & Campus Firewall Workarounds

### Issue 1: `check_connection.py` fails on Step 3: "Port 8765 is CLOSED or BLOCKED"

#### Causes & Fixes:
1. **Server not running on PC 2**: Ensure `python3 robot_server.py --port 8765` is running in the lab terminal.
2. **Local firewall on PC 2**: Run `sudo ufw allow 8765/tcp` on PC 2.
3. **Campus IT Subnet Isolation**:
   - Some universities isolate the VPN IP pool (e.g., `10.200.x.x`) and block incoming connections to student lab PCs (`10.4.x.x`).
   - **Fix via Tailscale (Zero-Config VPN Mesh)**:
     1. Install Tailscale on PC 2: `curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up`
     2. Install Tailscale on PC 1 and log in to the same free account.
     3. Tailscale assigns PC 2 a static private IP (e.g., `100.75.20.10`) that punches through campus NAT/firewalls with WireGuard encryption.
     4. On PC 1, simply point to the Tailscale IP:
        ```bash
        python3 commander_station.py --host 100.75.20.10 "Move to home"
        ```

### Issue 2: DeepSeek API Error: "Thinking mode does not support this tool_choice"
- **Cause**: Passing forced `tool_choice={'type': 'function', ...}` or `"required"` on reasoning models.
- **Fix**: The code already leaves `tool_choice="auto"` by default with prompt grounding. Never force `tool_choice` dicts on `deepseek-flash` or reasoning endpoints.

### Issue 3: DeepSeek API Error: "The reasoning_content in thinking mode must be passed back"
- **Cause**: Multi-turn tool execution stripped the assistant's `reasoning_content`.
- **Fix**: The included `planner.py` automatically captures and preserves `reasoning_content` in conversation histories.

---

## 11. Quick Command Cheat Sheet

| Task | Location | Command |
| :--- | :---: | :--- |
| **Check PC 2 Campus IP** | PC 2 (Lab) | `hostname -I` |
| **Open Firewall Port** | PC 2 (Lab) | `sudo ufw allow 8765/tcp` |
| **Start Server (Simulation)** | PC 2 (Lab) | `python3 robot_server.py --port 8765` |
| **Start Server (Real Robot)** | PC 2 (Lab) | `python3 robot_server.py --port 8765 --hardware` |
| **Test VPN Connection** | PC 1 (Home) | `python3 check_connection.py <PC2_IP>` |
| **Send Single Command** | PC 1 (Home) | `python3 commander_station.py --host <PC2_IP> "Pick up red mug"` |
| **Start Interactive Session** | PC 1 (Home) | `python3 commander_station.py --host <PC2_IP> --interactive` |
| **Emergency Stop (E-STOP)** | PC 1 (Home) | Press `Ctrl+C` or type `estop` |
| **Run Integration Tests** | Anywhere | `python3 test_distributed_teleop.py` |
| **Run Strictness Diagnostic** | Anywhere | `python3 test_strictness.py` |
| **Run 20-Prompt Benchmark** | Anywhere | `python3 benchmark_20_prompts.py` |
| **List Predefined Actions** | Anywhere | `python3 arm_planner.py --list-actions` |
