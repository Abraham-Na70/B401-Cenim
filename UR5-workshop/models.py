"""
Data models and tool schemas for the Robot Action Planner.
Defines Pydantic models for actions and plans, and provides functions to generate
DeepSeek-compatible tool definitions (supporting both strict mode and standard mode).
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    NAVIGATE = "NAVIGATE"
    PICK = "PICK"
    PLACE = "PLACE"
    INSPECT = "INSPECT"
    WAIT = "WAIT"
    OPEN = "OPEN"
    CLOSE = "CLOSE"


class RobotAction(BaseModel):
    """An atomic robot action in an execution sequence."""
    action_type: ActionType = Field(
        ...,
        description="The category of robot action (NAVIGATE, PICK, PLACE, INSPECT, WAIT, OPEN, CLOSE)."
    )
    target: str = Field(
        ...,
        description="Target destination, object, or device (e.g., 'kitchen_counter', 'red_mug', 'door')."
    )
    description: str = Field(
        ...,
        description="Human-readable explanation of what the robot does in this step."
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional execution parameters, e.g., speed, approach_vector, force, or duration."
    )


class RobotPlan(BaseModel):
    """A complete structured action plan generated from a natural language command."""
    plan_name: str = Field(..., description="Short title describing the plan.")
    goal: str = Field(..., description="High-level goal achieved by executing this plan.")
    actions: List[RobotAction] = Field(..., description="Ordered list of discrete robot actions.")
    estimated_duration_seconds: Optional[float] = Field(
        default=None,
        description="Estimated execution time in seconds, if calculable."
    )


def get_batch_plan_tool_schema(strict: bool = True) -> Dict[str, Any]:
    """
    Returns the tool definition for 'submit_action_plan'.
    Used for single-turn complete plan generation.
    """
    tool_def: Dict[str, Any] = {
        "type": "function",
        "function": {
            "name": "submit_action_plan",
            "description": "Submit a complete, ordered sequence of atomic robot actions to accomplish the user's requested command.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_name": {
                        "type": "string",
                        "description": "Short descriptive title for this plan."
                    },
                    "goal": {
                        "type": "string",
                        "description": "The high-level goal achieved by this sequence of actions."
                    },
                    "actions": {
                        "type": "array",
                        "description": "Ordered list of discrete robot actions to be executed sequentially.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "action_type": {
                                    "type": "string",
                                    "enum": [action.value for action in ActionType],
                                    "description": "Category of action to execute."
                                },
                                "target": {
                                    "type": "string",
                                    "description": "Target destination, object, or surface."
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Brief explanation of this step."
                                },
                                "parameters": {
                                    "type": "object",
                                    "description": "Additional key-value parameters like speed, grip_force, etc.",
                                    "additionalProperties": True
                                }
                            },
                            "required": ["action_type", "target", "description"],
                            "additionalProperties": False
                        }
                    },
                    "estimated_duration_seconds": {
                        "type": "number",
                        "description": "Optional estimated duration in seconds."
                    }
                },
                "required": ["plan_name", "goal", "actions"],
                "additionalProperties": False
            }
        }
    }
    if strict:
        tool_def["function"]["strict"] = True
    return tool_def


def get_discrete_action_tools_schema(strict: bool = True) -> List[Dict[str, Any]]:
    """
    Returns individual tool definitions for discrete robot actions.
    Used for step-by-step interactive agent execution loops.
    """
    tools = [
        {
            "type": "function",
            "function": {
                "name": "navigate_to",
                "description": "Move the robot base to a specified room, workstation, or coordinates.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Destination room, coordinate, or area (e.g., 'kitchen', 'lab_bench_1')."
                        },
                        "speed": {
                            "type": "string",
                            "enum": ["slow", "normal", "fast"],
                            "description": "Navigation velocity profile."
                        }
                    },
                    "required": ["location"],
                    "additionalProperties": False
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pick_object",
                "description": "Grasp an object using the robot manipulator arm.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "object_name": {
                            "type": "string",
                            "description": "Name or identifier of the object to grasp (e.g., 'red_mug', 'beaker')."
                        },
                        "surface": {
                            "type": "string",
                            "description": "The surface where the object is currently resting."
                        }
                    },
                    "required": ["object_name"],
                    "additionalProperties": False
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "place_object",
                "description": "Release the currently held object onto a target surface or container.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "object_name": {
                            "type": "string",
                            "description": "Name of the object being placed."
                        },
                        "target_surface": {
                            "type": "string",
                            "description": "The destination surface or container (e.g., 'dining_table', 'tray')."
                        }
                    },
                    "required": ["object_name", "target_surface"],
                    "additionalProperties": False
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "inspect_target",
                "description": "Use on-board visual or depth sensors to scan and verify an object or area state.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "The item or area to inspect (e.g., 'battery_indicator', 'door_handle')."
                        }
                    },
                    "required": ["target"],
                    "additionalProperties": False
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "wait_seconds",
                "description": "Pause robot execution for a specified duration.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "seconds": {
                            "type": "number",
                            "description": "Duration to wait in seconds."
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for waiting (e.g., 'cooling', 'waiting for human clearance')."
                        }
                    },
                    "required": ["seconds", "reason"],
                    "additionalProperties": False
                }
            }
        }
    ]

    if strict:
        for tool in tools:
            tool["function"]["strict"] = True

    return tools
