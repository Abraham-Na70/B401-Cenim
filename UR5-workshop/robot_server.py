"""
Robot Controller Receiver Server (Runs on PC 2 in Campus Lab).
Listens on WebSocket (default 0.0.0.0:8765) for action plans sent from PC 1.
Validates action sequences, coordinates execution, and streams real-time step progress.
Supports Emergency Stop (E-STOP) signals to abort motion immediately.
"""

import argparse
import asyncio
import json
import logging
import signal
import sys
import time
from typing import Any, Dict, List, Optional
import websockets

# Suppress noisy raw TCP probe / handshake abort warnings from port-scanners or health-checks
logging.getLogger("websockets.server").setLevel(logging.CRITICAL)
logging.getLogger("websockets.asyncio.server").setLevel(logging.CRITICAL)

from arm_planner import PREDEFINED_ARM_ACTIONS
from network_protocol import (
    MessageType,
    NetworkMessage,
    PlanStatus,
    StepStatus,
    make_emergency_stop_ack,
    make_handshake_ack,
    make_plan_ack,
    make_plan_complete,
    make_step_progress,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("RobotServer")


class RobotArmExecutor:
    """
    Executes atomic robot arm actions sequentially.
    Includes a simulated execution delay and a clear hook for physical robot hardware.
    """

    def __init__(self, step_delay_seconds: float = 0.8, hardware_mode: bool = False):
        self.step_delay = step_delay_seconds
        self.hardware_mode = hardware_mode
        self.is_running = False
        self.stop_requested = False

    def execute_hardware_action(self, action: str):
        """
        HARDWARE HOOK:
        Replace or extend this method to send real commands to your robot arm:
        - Example Serial: serial_port.write(f'{action}\\n'.encode())
        - Example ROS2: ros2_action_client.send_goal(action)
        - Example Dynamixel: dxl_controller.move_named_pose(action)
        """
        logger.info(f"  [HARDWARE DRIVER] Executing physical action: '{action}'")
        # Add your hardware control logic here if hardware_mode=True
        time.sleep(self.step_delay)

    async def execute_action(self, action: str) -> bool:
        """Executes a single action with support for immediate cancellation."""
        if self.stop_requested:
            return False

        if self.hardware_mode:
            # Run physical action in executor thread so we don't block the async event loop
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.execute_hardware_action, action)
        else:
            # Simulated robot arm motion
            logger.info(f"  [SIMULATION] Executing motion: '{action}' ({self.step_delay}s)...")
            await asyncio.sleep(self.step_delay)

        return not self.stop_requested


class RobotReceiverServer:
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8765,
        step_delay: float = 0.8,
        hardware_mode: bool = False,
    ):
        self.host = host
        self.port = port
        self.executor = RobotArmExecutor(step_delay_seconds=step_delay, hardware_mode=hardware_mode)
        self.active_connections = set()
        self.current_plan_task: Optional[asyncio.Task] = None

    async def handle_connection(self, websocket: Any):
        client_address = websocket.remote_address
        logger.info(f"Connected to client at {client_address}")
        self.active_connections.add(websocket)

        try:
            async for raw_message in websocket:
                try:
                    msg = NetworkMessage.from_json(raw_message)
                    await self.process_message(websocket, msg)
                except Exception as e:
                    logger.error(f"Error processing packet from {client_address}: {e}")
                    err_reply = NetworkMessage(
                        msg_type=MessageType.ERROR,
                        payload={"error": str(e)},
                    )
                    await websocket.send(err_reply.to_json())

        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"Client {client_address} disconnected ({e.code})")
        finally:
            self.active_connections.discard(websocket)

    async def process_message(self, websocket: Any, msg: NetworkMessage):
        logger.info(f"Received message: [{msg.msg_type.value}] (ID: {msg.msg_id})")

        # 1. Handshake
        if msg.msg_type == MessageType.HANDSHAKE:
            client_id = msg.payload.get("client_id", "unknown")
            logger.info(f"Handshake initiated by client: '{client_id}'")
            status_str = "EXECUTING" if self.executor.is_running else "READY_IDLE"
            ack = make_handshake_ack(
                server_status=status_str,
                available_actions=PREDEFINED_ARM_ACTIONS,
            )
            await websocket.send(ack.to_json())

        # 2. Heartbeat Ping
        elif msg.msg_type == MessageType.HEARTBEAT:
            reply = NetworkMessage(
                msg_type=MessageType.HEARTBEAT_ACK,
                payload={"server_time": time.time(), "is_busy": self.executor.is_running},
            )
            await websocket.send(reply.to_json())

        # 3. Emergency Stop (E-STOP)
        elif msg.msg_type == MessageType.EMERGENCY_STOP:
            reason = msg.payload.get("reason", "Operator Emergency Stop")
            logger.warning(f"🚨 EMERGENCY STOP RECEIVED: {reason} 🚨")
            self.executor.stop_requested = True
            if self.current_plan_task and not self.current_plan_task.done():
                self.current_plan_task.cancel()

            estop_ack = make_emergency_stop_ack()
            await websocket.send(estop_ack.to_json())

        # 4. Plan Dispatch
        elif msg.msg_type == MessageType.PLAN_DISPATCH:
            plan_id = msg.payload.get("plan_id", "unknown_plan")
            actions = msg.payload.get("actions", [])
            source_prompt = msg.payload.get("source_prompt", "")

            logger.info(f"Received Action Plan '{plan_id}' with {len(actions)} steps:")
            for idx, act in enumerate(actions, 1):
                logger.info(f"   {idx:02d}. {act}")

            # Validate actions against predefined list
            invalid_actions = [a for a in actions if a not in PREDEFINED_ARM_ACTIONS]
            if invalid_actions:
                logger.error(f"Rejected plan: Invalid actions detected: {invalid_actions}")
                rejection = make_plan_ack(
                    plan_id=plan_id,
                    accepted=False,
                    message=f"Plan rejected. Invalid actions: {invalid_actions}",
                )
                await websocket.send(rejection.to_json())
                return

            if self.executor.is_running:
                logger.warning(f"Rejected plan: Robot is currently executing another plan.")
                busy_reply = make_plan_ack(
                    plan_id=plan_id,
                    accepted=False,
                    message="Robot is currently busy executing another plan.",
                )
                await websocket.send(busy_reply.to_json())
                return

            # Accept Plan
            ack = make_plan_ack(
                plan_id=plan_id,
                accepted=True,
                message=f"Plan accepted with {len(actions)} steps. Starting execution.",
            )
            await websocket.send(ack.to_json())

            # Start execution task in background
            self.current_plan_task = asyncio.create_task(
                self.run_plan_execution(websocket, plan_id, actions)
            )

    async def run_plan_execution(
        self,
        websocket: Any,
        plan_id: str,
        actions: List[str],
    ):
        """Coordinates sequential step execution and streams progress to client."""
        self.executor.is_running = True
        self.executor.stop_requested = False
        total_steps = len(actions)
        start_time = time.time()
        completed_steps = 0
        final_status = PlanStatus.COMPLETED

        try:
            for idx, action in enumerate(actions, 1):
                if self.executor.stop_requested:
                    logger.warning(f"Execution aborted before step {idx}/{total_steps}.")
                    final_status = PlanStatus.ABORTED
                    break

                step_start = time.time()

                # Notify: STEP RUNNING
                progress_running = make_step_progress(
                    plan_id=plan_id,
                    step_index=idx,
                    total_steps=total_steps,
                    action=action,
                    status=StepStatus.RUNNING,
                    message=f"Starting '{action}'",
                    elapsed_s=0.0,
                )
                await websocket.send(progress_running.to_json())

                # Execute action
                success = await self.executor.execute_action(action)
                step_elapsed = time.time() - step_start

                if success and not self.executor.stop_requested:
                    completed_steps += 1
                    progress_done = make_step_progress(
                        plan_id=plan_id,
                        step_index=idx,
                        total_steps=total_steps,
                        action=action,
                        status=StepStatus.SUCCESS,
                        message=f"Completed '{action}' successfully",
                        elapsed_s=step_elapsed,
                    )
                    await websocket.send(progress_done.to_json())
                    logger.info(f"Step [{idx}/{total_steps}] '{action}' COMPLETED in {step_elapsed:.2f}s")
                else:
                    final_status = PlanStatus.ABORTED if self.executor.stop_requested else PlanStatus.FAILED
                    progress_fail = make_step_progress(
                        plan_id=plan_id,
                        step_index=idx,
                        total_steps=total_steps,
                        action=action,
                        status=StepStatus.ABORTED if self.executor.stop_requested else StepStatus.FAILED,
                        message=f"Action '{action}' aborted or interrupted.",
                        elapsed_s=step_elapsed,
                    )
                    await websocket.send(progress_fail.to_json())
                    break

        except asyncio.CancelledError:
            final_status = PlanStatus.ABORTED
            logger.warning(f"Plan {plan_id} task was cancelled.")
        except Exception as e:
            final_status = PlanStatus.FAILED
            logger.error(f"Error executing plan {plan_id}: {e}")
        finally:
            total_duration = time.time() - start_time
            self.executor.is_running = False

            # Send Plan Complete notification
            completion_msg = make_plan_complete(
                plan_id=plan_id,
                status=final_status,
                completed_steps=completed_steps,
                total_steps=total_steps,
                total_duration_s=total_duration,
                message=f"Execution finished with status: {final_status.value}",
            )
            try:
                await websocket.send(completion_msg.to_json())
            except Exception:
                pass
            logger.info(
                f"Plan '{plan_id}' FINISHED: Status={final_status.value} "
                f"({completed_steps}/{total_steps} steps, {total_duration:.2f}s)"
            )

    async def start(self):
        logger.info("=" * 60)
        logger.info("🤖 ROBOT CONTROLLER RECEIVER SERVER (PC 2)")
        logger.info(f"  Listening on: ws://{self.host}:{self.port}")
        logger.info(f"  Execution mode: {'HARDWARE' if self.executor.hardware_mode else 'SIMULATION'}")
        logger.info(f"  Predefined actions: {len(PREDEFINED_ARM_ACTIONS)} actions registered")
        logger.info("=" * 60)

        async with websockets.serve(self.handle_connection, self.host, self.port):
            # Keep running until cancelled
            await asyncio.Future()


def main():
    parser = argparse.ArgumentParser(
        description="Robot Controller Server (PC 2 in Campus Lab)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host interface to bind (default: 0.0.0.0, binds to all network interfaces including campus LAN)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port to listen on (default: 8765)",
    )
    parser.add_argument(
        "--step-delay",
        type=float,
        default=0.8,
        help="Simulated execution duration per action in seconds (default: 0.8s)",
    )
    parser.add_argument(
        "--hardware",
        action="store_true",
        help="Enable physical hardware execution hook (default: false, runs simulation)",
    )

    args = parser.parse_args()
    server = RobotReceiverServer(
        host=args.host,
        port=args.port,
        step_delay=args.step_delay,
        hardware_mode=args.hardware,
    )

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("\nServer shut down by user.")


if __name__ == "__main__":
    main()
