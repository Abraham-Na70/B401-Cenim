"""
Robot Arm Action Planner using DeepSeek API.
Maps natural language instructions into an ordered list of predefined robot arm actions.

Output format:
    ["move to home", "scan workspace", "open gripper", "reach target", "close gripper", "lift arm", "rotate base", "lower arm", "open gripper", "move to home"]
"""

import argparse
import json
import os
import sys
from typing import List, Optional
from openai import OpenAI

# Predefined available atomic actions for the robot arm
PREDEFINED_ARM_ACTIONS = [
    "move to home",
    "scan workspace",
    "reach target",
    "open gripper",
    "close gripper",
    "lift arm",
    "lower arm",
    "rotate base",
    "rotate wrist",
    "wait",
]


def get_arm_tool_schema(predefined_actions: List[str]) -> dict:
    """
    Constructs a DeepSeek strict function schema where actions must be an array
    of strings strictly restricted to the predefined actions enum.
    """
    return {
        "type": "function",
        "function": {
            "name": "execute_arm_action_sequence",
            "description": "Execute an ordered sequence of predefined robot arm actions to fulfill the user command.",
            "parameters": {
                "type": "object",
                "properties": {
                    "actions": {
                        "type": "array",
                        "description": "Sequential list of actions chosen strictly from the predefined list.",
                        "items": {
                            "type": "string",
                            "enum": predefined_actions,
                        },
                    }
                },
                "required": ["actions"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }


class RobotArmPlanner:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        predefined_actions: Optional[List[str]] = None,
    ):
        resolved_key = (
            api_key
            or os.environ.get("DEEPSEEK_API_KEY")
            or os.environ.get("ANTHROPIC_AUTH_TOKEN")
            or os.environ.get("OPENAI_API_KEY")
        )
        if not resolved_key:
            raise ValueError(
                "No API key found. Set DEEPSEEK_API_KEY or ANTHROPIC_AUTH_TOKEN."
            )

        self.base_url = base_url or os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = model or os.environ.get("DEEPSEEK_MODEL", "deepseek-flash")
        self.predefined_actions = predefined_actions or PREDEFINED_ARM_ACTIONS
        self.client = OpenAI(api_key=resolved_key, base_url=self.base_url)

    def plan(self, command: str) -> List[str]:
        """
        Plans the sequence of predefined actions using DeepSeek's strict Tool Calling API.
        Returns the ordered list of actions.
        """
        tool = get_arm_tool_schema(self.predefined_actions)

        prompt = (
            "You are a robotic manipulator (robot arm) action planner. "
            f"You have the following predefined atomic actions available:\n"
            f"{json.dumps(self.predefined_actions, indent=2)}\n\n"
            "Decompose the user's natural language command into an ordered sequence of these "
            "predefined actions to accomplish the physical manipulation task. "
            "Call the execute_arm_action_sequence tool with the ordered action list."
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": command},
            ],
            tools=[tool],
        )

        msg = response.choices[0].message

        # Check for tool call
        if msg.tool_calls:
            args = json.loads(msg.tool_calls[0].function.arguments)
            raw_actions = args.get("actions", [])
        else:
            # Fallback to direct text content parsing if tool call was omitted
            try:
                raw_actions = json.loads(msg.content.strip())
            except Exception:
                raise RuntimeError(
                    f"Model failed to generate structured action sequence. Response: {msg.content}"
                )

        # Validate that all returned actions strictly exist in predefined set
        validated_actions = []
        for action in raw_actions:
            if action in self.predefined_actions:
                validated_actions.append(action)
            else:
                raise ValueError(
                    f"Action '{action}' is not in the predefined actions list: {self.predefined_actions}"
                )

        return validated_actions


def main():
    parser = argparse.ArgumentParser(
        description="Plan robot arm actions using predefined actions and DeepSeek API."
    )
    parser.add_argument(
        "command",
        nargs="?",
        type=str,
        help="Natural language instruction for the robot arm (e.g. 'Pick up the cube and place it into the bin')",
    )
    parser.add_argument(
        "--list-actions",
        action="store_true",
        help="Display the list of predefined robot arm actions",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run interactive command prompt",
    )

    args = parser.parse_args()

    if args.list_actions:
        print("Predefined Robot Arm Actions:")
        print(json.dumps(PREDEFINED_ARM_ACTIONS, indent=2))
        return

    planner = RobotArmPlanner()

    if args.interactive:
        print("Robot Arm Planner (Interactive REPL)")
        print(f"Predefined actions: {json.dumps(PREDEFINED_ARM_ACTIONS)}")
        print("Type 'exit' to quit.\n")
        while True:
            try:
                cmd = input("ArmCommand> ").strip()
                if not cmd:
                    continue
                if cmd.lower() in ("exit", "quit", "q"):
                    break
                actions = planner.plan(cmd)
                print(json.dumps(actions))
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        return

    if not args.command:
        # Default test example if no argument provided
        test_command = "Pick up the blue block from the table and put it in the bin"
        print(f"No command provided. Running default example: '{test_command}'")
        actions = planner.plan(test_command)
        print("\nOrdered Actions:")
        print(json.dumps(actions))
    else:
        actions = planner.plan(args.command)
        # Print directly in format ["stand", "walk toward", ...etc]
        print(json.dumps(actions))


if __name__ == "__main__":
    main()
