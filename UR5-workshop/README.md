# DeepSeek Robot Action Planner & Strictness Tester

A lightweight Python tool that transforms high-level natural language instructions into validated, structured robot action commands using DeepSeek's Tool Calling API.

Includes a diagnostic test suite specifically built to probe **how strict DeepSeek's Tool Calling API is**.

---

## Features

- **End-to-End Batch Action Planning**: Converts commands like *"Go to the kitchen, pick up the red mug, and place it on the dining table"* into a structured `RobotPlan` (`Pydantic` validated) containing ordered atomic actions (`NAVIGATE`, `PICK`, `PLACE`, `INSPECT`, `WAIT`, `OPEN`, `CLOSE`).
- **Closed-Loop Reactive Agent Mode**: Emits step-by-step action tool calls, receives simulated or real robot execution feedback, and reacts iteratively.
- **DeepSeek API Strictness Diagnostic Suite**: Evaluates and demonstrates the 5 key dimensions of DeepSeek tool calling strictness.
- **ROS / Robotics Ready**: Supports `--json` export to integrate directly into ROS2 action clients, Behavior Trees, or state machines.

---

## DeepSeek API Strictness Findings

| Behavior / Requirement | DeepSeek Enforcement | Technical Explanation |
| :--- | :---: | :--- |
| **Thinking Mode `tool_choice`** | **Strict (HTTP 400)** | In models with reasoning/thinking active (e.g. `deepseek-flash`, V4, R1 variants), forced `tool_choice={'type': 'function', ...}` or `"required"` throws `HTTP 400: Thinking mode does not support this tool_choice`. Tool choice must be left as `"auto"`. |
| **Message Sequencing** | **Strict (HTTP 400)** | If an assistant message contains `tool_calls`, every call must be immediately followed by a `role: 'tool'` message with matching `tool_call_id`. Skipping responses or sending a user message throws `HTTP 400`. |
| **Schema Compliance (`strict: True`)** | **Strict (Server 400/422)** | Enforces valid JSON schema, `additionalProperties: false`, and required parameter declarations. |
| **Pydantic Model Adherence** | **High Fidelity** | Emits well-formed JSON arguments matching expected enums, action types, and structured parameters without schema drift. |

---

## Quick Start

### 1. Requirements
Ensure Python 3.10+ and requirements are installed:
```bash
pip install openai pydantic
```

### 2. Set API Key
Set your DeepSeek API key (or `ANTHROPIC_AUTH_TOKEN`):
```bash
export DEEPSEEK_API_KEY="your-deepseek-api-key"
```

---

## Usage

### 1. Run Diagnostic Strictness Test Suite
To test and verify DeepSeek API's strictness limits:
```bash
python3 main.py --test-strictness
```

### 2. Batch Plan Generation
Convert a natural language command into a full action plan:
```bash
python3 main.py "Go to the kitchen counter, pick up the red mug, and place it on the dining table"
```

Output as raw JSON (ideal for ROS / robotics pipelines):
```bash
python3 main.py "Inspect solar panel 3 and report status" --json
```

### 3. Predefined Robot Arm Action Sequence (String Array Format)
Decompose arm manipulation tasks into strictly predefined actions formatted as `["action 1", "action 2", ...]`:
```bash
python3 arm_planner.py "Pick up the blue block from the table and put it in the bin"
```
**Output:**
```json
["move to home", "scan workspace", "reach target", "open gripper", "lower arm", "close gripper", "lift arm", "rotate base", "reach target", "open gripper", "move to home"]
```

List all available predefined actions:
```bash
python3 arm_planner.py --list-actions
```

Interactive REPL:
```bash
python3 arm_planner.py --interactive
```

### 4. Reactive Agent Mode (Step-by-step)
Runs an interactive closed-loop session where the robot acts, receives execution results, and decides the next step:
```bash
python3 main.py --agent "Navigate to the charging station and inspect battery"
```

### 5. Distributed Remote Teleoperation (PC 1 Home via VPN -> PC 2 Campus Lab)

Run natural language robot commands from off-campus (PC 1) and execute them on the lab robot (PC 2).

#### Step 1: On PC 2 (in Campus Lab)
```bash
# Allow firewall port (Ubuntu)
sudo ufw allow 8765/tcp

# Run robot controller server
python3 robot_server.py --port 8765
```

#### Step 2: On PC 1 (at Home, with Campus VPN Active)
```bash
# 1. Test reachability across Campus VPN
python3 check_connection.py <PC2_CAMPUS_IP>

# 2. Send remote natural language command
python3 commander_station.py --host <PC2_CAMPUS_IP> "Pick up the blue block and place it into the bin"

# 3. Or start interactive remote REPL session
python3 commander_station.py --host <PC2_CAMPUS_IP> --interactive
```

*For complete network details, firewall troubleshooting, and hardware integration, see [CAMPUS_NETWORK_GUIDE.md](CAMPUS_NETWORK_GUIDE.md).*

---

## File Structure

- `arm_planner.py`: Robot arm action planner using DeepSeek API with strict predefined actions.
- `network_protocol.py`: Typed message envelopes and payloads for remote teleoperation.
- `robot_server.py`: WebSocket controller server running on PC 2 in the campus lab.
- `commander_station.py`: Operator station running on PC 1 (with Campus VPN) to plan and transmit commands.
- `check_connection.py`: Network reachability and firewall port diagnostic tool.
- `CAMPUS_NETWORK_GUIDE.md`: Step-by-step setup and troubleshooting guide for Campus VPN environments.
- `models.py`: Pydantic schemas for `RobotAction`, `RobotPlan`, `ActionType`, and DeepSeek tool definitions.
- `planner.py`: `RobotActionPlanner` core class supporting batch and reactive modes.
- `test_strictness.py`: 5 automated tests probing DeepSeek tool calling strictness and error conditions.
- `benchmark_20_prompts.py`: 20-prompt benchmark and hallucination audit.
- `test_distributed_teleop.py`: Automated integration tests for distributed networking and E-STOP.
- `main.py`: General command-line interface and REPL.

