"""
Automated Test Suite for Distributed Robot Teleoperation.
Verifies:
1. Connection & Handshake between PC 1 and PC 2
2. Plan transmission & execution streaming
3. Emergency Stop (E-STOP) abort behavior
"""

import asyncio
import json
import subprocess
import sys
import time
import websockets

from network_protocol import (
    MessageType,
    NetworkMessage,
    PlanStatus,
    StepStatus,
    make_emergency_stop,
    make_handshake,
    make_plan_dispatch,
)


async def run_tests():
    test_port = 8769
    print("\n" + "=" * 70)
    print(" 🧪 STARTING AUTOMATED DISTRIBUTED TELEOP INTEGRATION TESTS")
    print(f" Test Port: {test_port}")
    print("=" * 70)

    # 1. Start robot_server in background
    print("\n[Step 1] Starting robot_server.py background process...")
    server_proc = subprocess.Popen(
        [
            sys.executable,
            "robot_server.py",
            "--host",
            "127.0.0.1",
            "--port",
            str(test_port),
            "--step-delay",
            "0.15",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(1.0)  # Wait for server to bind

    uri = f"ws://127.0.0.1:{test_port}"

    try:
        # -------------------------------------------------------------
        # Test A: Handshake
        # -------------------------------------------------------------
        print("\n[Test A] Testing WebSocket Handshake...")
        async with websockets.connect(uri) as ws:
            handshake = make_handshake("automated_tester")
            await ws.send(handshake.to_json())
            raw_ack = await asyncio.wait_for(ws.recv(), timeout=3.0)
            ack = NetworkMessage.from_json(raw_ack)
            assert ack.msg_type == MessageType.HANDSHAKE_ACK, f"Wrong type: {ack.msg_type}"
            assert ack.payload.get("server_status") == "READY_IDLE"
            print("  ✅ Handshake verified! Server is READY_IDLE.")

        # -------------------------------------------------------------
        # Test B: Full Plan Dispatch & Real-Time Progress Streaming
        # -------------------------------------------------------------
        print("\n[Test B] Testing Plan Dispatch and Step-by-Step Progress Streaming...")
        test_actions = ["move to home", "scan workspace", "reach target", "open gripper", "close gripper"]
        async with websockets.connect(uri) as ws:
            # Send handshake
            await ws.send(make_handshake().to_json())
            await ws.recv()

            # Send plan
            dispatch = make_plan_dispatch(actions=test_actions, source_prompt="Pick up item")
            await ws.send(dispatch.to_json())

            # Receive PLAN_ACK
            raw_ack = await asyncio.wait_for(ws.recv(), timeout=2.0)
            ack = NetworkMessage.from_json(raw_ack)
            assert ack.msg_type == MessageType.PLAN_ACK and ack.payload["accepted"]
            print(f"  ✅ Plan accepted by server: {ack.payload['message']}")

            # Receive step-by-step progress events
            steps_completed = 0
            while True:
                event_raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
                event = NetworkMessage.from_json(event_raw)

                if event.msg_type == MessageType.STEP_PROGRESS:
                    if event.payload["status"] == StepStatus.SUCCESS.value:
                        steps_completed += 1
                        print(f"    • Step {event.payload['step_index']}/{event.payload['total_steps']} ({event.payload['action']}) finished")

                elif event.msg_type == MessageType.PLAN_COMPLETE:
                    assert event.payload["status"] == PlanStatus.COMPLETED.value
                    assert event.payload["completed_steps"] == len(test_actions)
                    print(f"  ✅ Plan Complete received! ({steps_completed}/{len(test_actions)} steps executed)")
                    break

        # -------------------------------------------------------------
        # Test C: Emergency Stop (E-STOP) Interruption
        # -------------------------------------------------------------
        print("\n[Test C] Testing Remote Emergency Stop (E-STOP)...")
        long_actions = ["move to home", "scan workspace", "rotate base", "reach target", "lower arm", "close gripper"]
        async with websockets.connect(uri) as ws:
            await ws.send(make_handshake().to_json())
            await ws.recv()

            # Dispatch plan
            await ws.send(make_plan_dispatch(actions=long_actions, source_prompt="Long plan").to_json())
            await ws.recv()  # PLAN_ACK

            # Wait for first step to start
            first_event = await ws.recv()
            print("    • Plan started execution...")

            # Send E-STOP immediately
            print("    🚨 Sending EMERGENCY_STOP signal to robot server...")
            await ws.send(make_emergency_stop("Safety test abort").to_json())

            # Read events until E-STOP confirmed
            estop_confirmed = False
            plan_aborted = False

            while True:
                msg_raw = await asyncio.wait_for(ws.recv(), timeout=3.0)
                msg = NetworkMessage.from_json(msg_raw)

                if msg.msg_type == MessageType.EMERGENCY_STOP_ACK:
                    estop_confirmed = True
                    print("  ✅ Server confirmed EMERGENCY_STOP_ACK!")

                elif msg.msg_type == MessageType.PLAN_COMPLETE:
                    if msg.payload["status"] == PlanStatus.ABORTED.value:
                        plan_aborted = True
                        print(f"  ✅ Server reported PlanStatus.ABORTED after {msg.payload['completed_steps']} steps.")
                    break

            assert estop_confirmed, "Did not receive EMERGENCY_STOP_ACK"
            assert plan_aborted, "Plan was not aborted"

        print("\n" + "=" * 70)
        print(" 🎉 ALL DISTRIBUTED TELEOP INTEGRATION TESTS PASSED (100% SUCCESS)!")
        print("=" * 70 + "\n")

    finally:
        # Terminate background server process
        server_proc.terminate()
        server_proc.wait()


if __name__ == "__main__":
    asyncio.run(run_tests())
