"""
Network Protocol for Distributed Robot Teleoperation.
Defines message schemas, types, and serialization utilities for reliable communication
between PC 1 (Commander Station) and PC 2 (Robot Controller Server).
"""

from enum import Enum
import json
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    # Handshake & Liveness
    HANDSHAKE = "HANDSHAKE"
    HANDSHAKE_ACK = "HANDSHAKE_ACK"
    HEARTBEAT = "HEARTBEAT"
    HEARTBEAT_ACK = "HEARTBEAT_ACK"

    # Plan Dispatch & Execution
    PLAN_DISPATCH = "PLAN_DISPATCH"
    PLAN_ACK = "PLAN_ACK"
    STEP_PROGRESS = "STEP_PROGRESS"
    PLAN_COMPLETE = "PLAN_COMPLETE"

    # Safety & Control
    EMERGENCY_STOP = "EMERGENCY_STOP"
    EMERGENCY_STOP_ACK = "EMERGENCY_STOP_ACK"
    ERROR = "ERROR"


class StepStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


class PlanStatus(str, Enum):
    RECEIVED = "RECEIVED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


class NetworkMessage(BaseModel):
    """Universal envelope for all teleoperation network packets."""
    msg_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    msg_type: MessageType
    timestamp: float = Field(default_factory=time.time)
    payload: Dict[str, Any] = Field(default_factory=dict)

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, raw: str) -> "NetworkMessage":
        data = json.loads(raw)
        return cls.model_validate(data)


# ---------------------------------------------------------------------------
# Specific Payload Helper Constructors
# ---------------------------------------------------------------------------

def make_handshake(client_id: str = "pc1_commander") -> NetworkMessage:
    return NetworkMessage(
        msg_type=MessageType.HANDSHAKE,
        payload={"client_id": client_id, "version": "1.0"},
    )


def make_handshake_ack(server_status: str, available_actions: List[str]) -> NetworkMessage:
    return NetworkMessage(
        msg_type=MessageType.HANDSHAKE_ACK,
        payload={
            "server_status": server_status,
            "available_actions": available_actions,
            "server_time": time.time(),
        },
    )


def make_plan_dispatch(
    actions: List[str],
    source_prompt: str,
    plan_id: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
) -> NetworkMessage:
    p_id = plan_id or f"plan_{int(time.time())}_{str(uuid.uuid4())[:6]}"
    return NetworkMessage(
        msg_type=MessageType.PLAN_DISPATCH,
        payload={
            "plan_id": p_id,
            "source_prompt": source_prompt,
            "actions": actions,
            "total_steps": len(actions),
            "parameters": parameters or {},
        },
    )


def make_plan_ack(plan_id: str, accepted: bool, message: str) -> NetworkMessage:
    return NetworkMessage(
        msg_type=MessageType.PLAN_ACK,
        payload={
            "plan_id": plan_id,
            "accepted": accepted,
            "status": PlanStatus.RECEIVED.value if accepted else PlanStatus.FAILED.value,
            "message": message,
        },
    )


def make_step_progress(
    plan_id: str,
    step_index: int,
    total_steps: int,
    action: str,
    status: StepStatus,
    message: str = "",
    elapsed_s: float = 0.0,
) -> NetworkMessage:
    return NetworkMessage(
        msg_type=MessageType.STEP_PROGRESS,
        payload={
            "plan_id": plan_id,
            "step_index": step_index,
            "total_steps": total_steps,
            "action": action,
            "status": status.value,
            "message": message,
            "elapsed_s": round(elapsed_s, 2),
        },
    )


def make_plan_complete(
    plan_id: str,
    status: PlanStatus,
    completed_steps: int,
    total_steps: int,
    total_duration_s: float,
    message: str = "",
) -> NetworkMessage:
    return NetworkMessage(
        msg_type=MessageType.PLAN_COMPLETE,
        payload={
            "plan_id": plan_id,
            "status": status.value,
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "total_duration_s": round(total_duration_s, 2),
            "message": message,
        },
    )


def make_emergency_stop(reason: str = "Operator manual abort") -> NetworkMessage:
    return NetworkMessage(
        msg_type=MessageType.EMERGENCY_STOP,
        payload={"reason": reason, "timestamp": time.time()},
    )


def make_emergency_stop_ack(halted_at_step: Optional[int] = None) -> NetworkMessage:
    return NetworkMessage(
        msg_type=MessageType.EMERGENCY_STOP_ACK,
        payload={"status": "HALTED", "halted_at_step": halted_at_step},
    )
