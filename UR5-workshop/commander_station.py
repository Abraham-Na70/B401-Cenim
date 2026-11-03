"""
Commander Operator Station (Runs on PC 1 outside campus via Campus VPN).
1. Takes natural language instructions from the user.
2. Uses DeepSeek API to decompose the command into strictly validated predefined actions.
3. Transmits the plan over the network (Campus VPN) to PC 2's robot controller.
4. Streams real-time progress and supports remote Emergency Stop (E-STOP).
"""

import argparse
import asyncio
import json
import logging
import signal
import sys
import time
from typing import List, Optional
import websockets

from arm_planner import RobotArmPlanner
from network_protocol import (
    MessageType,
    NetworkMessage,
    PlanStatus,
    StepStatus,
    make_emergency_stop,
    make_handshake,
    make_plan_dispatch,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("CommanderStation")


class CommanderClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.uri = f"ws://{self.host}:{self.port}"
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.planner = RobotArmPlanner()

    async def connect(self) -> bool:
        """Connects to PC 2 and performs initial handshake."""
        logger.info(f"Connecting to PC 2 Robot Server at {self.uri} ...")
        try:
            self.websocket = await websockets.connect(
                self.uri,
                ping_interval=10,
                ping_timeout=10,
                close_timeout=5,
            )
            # Send Handshake
            handshake = make_handshake(client_id="pc1_campus_vpn_operator")
            await self.websocket.send(handshake.to_json())

            raw_reply = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
            reply = NetworkMessage.from_json(raw_reply)

            if reply.msg_type == MessageType.HANDSHAKE_ACK:
                status = reply.payload.get("server_status", "UNKNOWN")
                actions_count = len(reply.payload.get("available_actions", []))
                logger.info(f"✅ Handshake successful! Robot Status: [{status}], Available Actions: {actions_count}")
                return True
            else:
                logger.error(f"Unexpected response to handshake: {reply.msg_type}")
                return False

        except (ConnectionRefusedError, OSError) as e:
            logger.error(f"❌ Connection failed to {self.uri}: {e}")
            logger.error("Troubleshooting tips for Campus VPN:")
            logger.error("  1. Verify Campus VPN is ACTIVE on this PC.")
            logger.error("  2. Verify PC 2's campus IP is correct (e.g. 10.x.x.x or 172.x.x.x).")
            logger.error("  3. Run: python3 check_connection.py <PC2_IP>")
            return False
        except asyncio.TimeoutError:
            logger.error(f"❌ Connection timeout to {self.uri}. Handshake response not received.")
            return False

    @property
    def is_connected(self) -> bool:
        """Returns True if the WebSocket connection is alive (compatible across websockets versions)."""
        if self.websocket is None:
            return False
        if hasattr(self.websocket, "closed"):
            return not self.websocket.closed
        if hasattr(self.websocket, "state"):
            return getattr(self.websocket.state, "name", "") == "OPEN"
        return True

    async def send_emergency_stop(self):
        """Sends an immediate Emergency Stop command to PC 2."""
        if not self.is_connected:
            logger.warning("Cannot send E-STOP: WebSocket not connected.")
            return

        logger.warning("\n🚨 SENDING EMERGENCY STOP (E-STOP) TO PC 2... 🚨")
        estop = make_emergency_stop("Operator pressed Ctrl+C or sent abort")
        try:
            await self.websocket.send(estop.to_json())
            raw_ack = await asyncio.wait_for(self.websocket.recv(), timeout=3.0)
            ack = NetworkMessage.from_json(raw_ack)
            logger.info(f"🛑 E-STOP Acknowledged by Robot: {ack.payload}")
        except Exception as e:
            logger.error(f"Failed to receive E-STOP ACK: {e}")

    async def execute_remote_command(self, user_command: str) -> bool:
        """
        Translates natural language command via DeepSeek and streams execution on PC 2.
        """
        print("\n" + "=" * 65)
        print(f"🗣️  Natural Language Input: \"{user_command}\"")
        print("=" * 65)

        # Step 1: LLM Action Planning via DeepSeek
        print("🧠 [PC 1] Calling DeepSeek API to plan action sequence...")
        try:
            actions = self.planner.plan(user_command)
        except Exception as e:
            logger.error(f"DeepSeek planning failed: {e}")
            return False

        print(f"📋 [PC 1] DeepSeek generated {len(actions)} strictly formatted actions:")
        print(f"   {json.dumps(actions)}")

        # Step 2: Ensure Connection to PC 2
        if not self.is_connected:
            connected = await self.connect()
            if not connected:
                return False

        # Step 3: Dispatch Plan over Campus VPN
        dispatch_msg = make_plan_dispatch(
            actions=actions,
            source_prompt=user_command,
        )
        plan_id = dispatch_msg.payload["plan_id"]
        logger.info(f"📡 Transmitting Plan '{plan_id}' to PC 2 via WebSocket...")
        await self.websocket.send(dispatch_msg.to_json())

        # Step 4: Wait for Acceptance ACK
        raw_ack = await self.websocket.recv()
        ack = NetworkMessage.from_json(raw_ack)
        if ack.msg_type != MessageType.PLAN_ACK or not ack.payload.get("accepted"):
            logger.error(f"Plan was rejected by PC 2: {ack.payload.get('message')}")
            return False

        logger.info(f"📥 Plan accepted by PC 2. Awaiting real-time step execution...\n")

        # Step 5: Real-time progress monitoring loop
        total_steps = len(actions)
        try:
            while True:
                raw_event = await self.websocket.recv()
                event = NetworkMessage.from_json(raw_event)

                if event.msg_type == MessageType.STEP_PROGRESS:
                    step_idx = event.payload["step_index"]
                    action = event.payload["action"]
                    status = event.payload["status"]
                    elapsed = event.payload.get("elapsed_s", 0.0)

                    # Dynamic Progress Bar Display
                    progress_pct = (step_idx / total_steps) * 100
                    bar_length = 25
                    filled = int(bar_length * step_idx / total_steps)
                    bar = "█" * filled + "░" * (bar_length - filled)

                    status_icon = "⏳" if status == "RUNNING" else ("✅" if status == "SUCCESS" else "❌")
                    print(
                        f"  [{bar}] {progress_pct:5.1f}% | Step {step_idx:02d}/{total_steps:02d}: "
                        f"{status_icon} {action:<16} ({status} {elapsed:.2f}s)"
                    )

                elif event.msg_type == MessageType.PLAN_COMPLETE:
                    final_status = event.payload["status"]
                    completed = event.payload["completed_steps"]
                    duration = event.payload["total_duration_s"]
                    print("\n" + "=" * 65)
                    if final_status == PlanStatus.COMPLETED.value:
                        print(f"🎉 PLAN COMPLETED SUCCESSFULLY on PC 2!")
                    elif final_status == PlanStatus.ABORTED.value:
                        print(f"🛑 PLAN WAS ABORTED / HALTED!")
                    else:
                        print(f"❌ PLAN EXECUTION FAILED!")
                    print(f"   Completed {completed}/{total_steps} steps in {duration:.2f} seconds.")
                    print("=" * 65 + "\n")
                    return final_status == PlanStatus.COMPLETED.value

                elif event.msg_type == MessageType.EMERGENCY_STOP_ACK:
                    logger.warning(f"🛑 Emergency Stop Confirmed by Robot: {event.payload}")
                    return False

                elif event.msg_type == MessageType.ERROR:
                    logger.error(f"Robot Server error: {event.payload.get('error')}")
                    return False

        except asyncio.CancelledError:
            await self.send_emergency_stop()
            raise

    async def close(self):
        if self.is_connected:
            try:
                await self.websocket.close()
            except Exception:
                pass
        self.websocket = None


async def run_repl(client: CommanderClient):
    print("\n" + "=" * 65)
    print("  🎮 PC 1 REMOTE ROBOT COMMANDER (CAMPUS VPN READY)")
    print(f"  Target PC 2: ws://{client.host}:{client.port}")
    print("  Type your natural language command or 'exit' to quit.")
    print("  Press Ctrl+C during execution to trigger an immediate E-STOP.")
    print("=" * 65 + "\n")

    connected = await client.connect()
    if not connected:
        print("Warning: Could not connect to PC 2 initially. Will retry upon command.")

    while True:
        try:
            cmd = input("RobotCommand (PC 1)> ").strip()
            if not cmd:
                continue
            if cmd.lower() in ("exit", "quit", "q"):
                print("Exiting Commander Station...")
                break
            if cmd.lower() in ("estop", "stop", "abort"):
                await client.send_emergency_stop()
                continue

            await client.execute_remote_command(cmd)

        except KeyboardInterrupt:
            print("\n[Ctrl+C detected] Sending Emergency Stop...")
            await client.send_emergency_stop()
            break
        except Exception as e:
            logger.error(f"Command error: {e}")

    await client.close()


def main():
    parser = argparse.ArgumentParser(
        description="Commander Station (Runs on PC 1 outside campus via Campus VPN)"
    )
    parser.add_argument(
        "command",
        nargs="?",
        type=str,
        help="Natural language instruction for the robot arm",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="IP address of PC 2 (e.g. 10.x.x.x campus VPN IP or local IP)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port of PC 2 robot server (default: 8765)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start interactive command prompt (REPL)",
    )

    args = parser.parse_args()
    client = CommanderClient(host=args.host, port=args.port)

    if args.interactive or not args.command:
        asyncio.run(run_repl(client))
    else:
        async def run_single():
            connected = await client.connect()
            if not connected:
                sys.exit(1)
            try:
                success = await client.execute_remote_command(args.command)
                sys.exit(0 if success else 1)
            except KeyboardInterrupt:
                await client.send_emergency_stop()
            finally:
                await client.close()

        asyncio.run(run_single())


if __name__ == "__main__":
    main()
