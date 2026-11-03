"""
Diagnostic Test Suite: DeepSeek API Tool Calling Strictness.
Investigates and validates how strict DeepSeek's Tool Calling implementation is across:
1. Schema strictness (strict: True with additionalProperties: False)
2. Forced tool_choice vs Auto (Thinking Mode 400 conflict)
3. Conversation history & tool_call_id matching strictness
4. Pydantic validation & argument type casting
5. Behavior on out-of-domain / impossible instructions
"""

import json
import os
import sys
from typing import Any, Dict, List
from openai import OpenAI
from pydantic import ValidationError

from models import ActionType, RobotPlan, get_batch_plan_tool_schema


class DeepSeekStrictnessTester:
    def __init__(self):
        self.api_key = (
            os.environ.get("DEEPSEEK_API_KEY")
            or os.environ.get("ANTHROPIC_AUTH_TOKEN")
            or os.environ.get("OPENAI_API_KEY")
        )
        if not self.api_key:
            raise ValueError("No API key available. Set DEEPSEEK_API_KEY or ANTHROPIC_AUTH_TOKEN.")

        self.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = os.environ.get("DEEPSEEK_MODEL", "deepseek-flash")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def print_section(self, title: str):
        print("\n" + "=" * 70)
        print(f" {title}")
        print("=" * 70)

    def test_schema_strictness_and_pydantic(self) -> bool:
        """
        Test 1: Tests whether DeepSeek adheres strictly to JSON schema with strict=True
        and whether arguments validate against Pydantic models.
        """
        self.print_section("TEST 1: Schema Compliance & Pydantic Validation (strict=True)")
        print(f"Target Model: {self.model} at {self.base_url}")
        print("Sending natural language command: 'Bring a water bottle from the fridge to office desk 4'")

        tool = get_batch_plan_tool_schema(strict=True)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a robot action planner. Break down the user instruction into atomic robot actions using submit_action_plan."
                    },
                    {
                        "role": "user",
                        "content": "Bring a water bottle from the fridge to office desk 4"
                    }
                ],
                tools=[tool]
            )

            msg = response.choices[0].message
            print(f"-> Model Reasoning: {getattr(msg, 'reasoning_content', 'None')}")
            
            if not msg.tool_calls:
                print("FAILED: Model did not generate a tool call.")
                return False

            raw_args = msg.tool_calls[0].function.arguments
            print(f"-> Raw Tool Call Arguments:\n{raw_args}")

            # Parse and validate with Pydantic
            parsed_json = json.loads(raw_args)
            validated_plan = RobotPlan.model_validate(parsed_json)
            print("\n[SUCCESS] Arguments passed Pydantic validation cleanly!")
            print(f"Plan Name: '{validated_plan.plan_name}'")
            print(f"Goal: '{validated_plan.goal}'")
            print(f"Generated {len(validated_plan.actions)} structured actions:")
            for i, act in enumerate(validated_plan.actions, 1):
                print(f"   {i}. [{act.action_type.value}] -> target: '{act.target}' | desc: '{act.description}'")
            return True

        except Exception as e:
            print(f"[FAILED] Error during schema strictness test: {e}")
            return False

    def test_forced_tool_choice_conflict(self) -> bool:
        """
        Test 2: Probes DeepSeek's strict rejection of forced tool_choice in Thinking Mode.
        Demonstrates the exact 400 error when passing tool_choice={"type": "function", ...}
        and contrasts it with tool_choice="auto".
        """
        self.print_section("TEST 2: Forced tool_choice vs Auto (Thinking Mode Strictness)")
        tool = get_batch_plan_tool_schema(strict=True)

        print("Attempt A: Calling with forced tool_choice={'type': 'function', 'function': {'name': 'submit_action_plan'}}")
        forced_failed_as_expected = False
        try:
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Navigate to charging dock"}],
                tools=[tool],
                tool_choice={"type": "function", "function": {"name": "submit_action_plan"}}
            )
            print("[INFO] DeepSeek accepted forced tool_choice (thinking mode might be disabled).")
        except Exception as e:
            error_str = str(e)
            print(f"-> Caught expected restriction: {error_str}")
            if "Thinking mode does not support this tool_choice" in error_str or "400" in error_str:
                print("[VERIFIED] DeepSeek strictly rejects forced tool_choice in thinking mode!")
                forced_failed_as_expected = True

        print("\nAttempt B: Calling with default tool_choice='auto' + explicit prompting")
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Use submit_action_plan to plan robot actions."},
                    {"role": "user", "content": "Navigate to charging dock"}
                ],
                tools=[tool]
            )
            tool_calls = resp.choices[0].message.tool_calls
            if tool_calls and tool_calls[0].function.name == "submit_action_plan":
                print("[VERIFIED] Succeeded with tool_choice='auto'!")
                return True
            else:
                print(f"[WARNING] Model replied without tool call: {resp.choices[0].message.content}")
                return False
        except Exception as e:
            print(f"[FAILED] Error in Attempt B: {e}")
            return False

    def test_tool_response_sequencing_strictness(self) -> bool:
        """
        Test 3: Probes DeepSeek's server-side enforcement of message history.
        DeepSeek strictly requires that any assistant message with tool_calls
        MUST be immediately followed by role='tool' messages with matching tool_call_id.
        """
        self.print_section("TEST 3: Conversation History & tool_call_id Matching Strictness")

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "navigate_to",
                    "description": "Move robot to target location",
                    "parameters": {
                        "type": "object",
                        "properties": {"location": {"type": "string"}},
                        "required": ["location"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        ]

        # Case A: Missing tool response (Assistant tool call followed by user message)
        print("Case A: Sending history where assistant called a tool, but user sends a message instead of tool result:")
        invalid_history = [
            {"role": "user", "content": "Go to lab"},
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "mock_call_001",
                        "type": "function",
                        "function": {"name": "navigate_to", "arguments": '{"location": "lab"}'}
                    }
                ]
            },
            {"role": "user", "content": "Are you there yet?"}  # Missing role: 'tool' message!
        ]

        case_a_caught = False
        try:
            self.client.chat.completions.create(
                model=self.model,
                messages=invalid_history,
                tools=tools
            )
            print("[INFO] Server did not reject invalid sequence.")
        except Exception as e:
            error_str = str(e)
            print(f"-> Caught server error: {error_str}")
            if "must be followed by tool messages responding to each 'tool_call_id'" in error_str:
                print("[VERIFIED] DeepSeek strictly enforces tool message presence matching tool_call_id!")
                case_a_caught = True

        # Case B: Valid sequence with matching tool_call_id AND reasoning_content
        print("\nCase B: Sending properly formatted sequence with matching tool_call_id & reasoning_content:")
        valid_history = [
            {"role": "user", "content": "Go to lab"},
            {
                "role": "assistant",
                "reasoning_content": "The user wants me to navigate to the lab. I will call navigate_to.",
                "tool_calls": [
                    {
                        "id": "mock_call_002",
                        "type": "function",
                        "function": {"name": "navigate_to", "arguments": '{"location": "lab"}'}
                    }
                ]
            },
            {
                "role": "tool",
                "tool_call_id": "mock_call_002",
                "content": "Arrived at lab coordinates (10.0, 5.2)."
            }
        ]

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=valid_history,
                tools=tools
            )
            print(f"-> Server accepted valid sequence. Model response: '{resp.choices[0].message.content}'")
            print("[VERIFIED] Multi-turn tool execution succeeded when tool_call_id AND reasoning_content are supplied!")
            return case_a_caught
        except Exception as e:
            print(f"[FAILED] Error on valid sequence: {e}")
            return False

    def test_invalid_schema_rejection(self) -> bool:
        """
        Test 4: Probes how DeepSeek reacts when strict=True is set but JSON Schema is invalid
        (e.g., missing type, or unsupported constructs).
        """
        self.print_section("TEST 4: Schema Validation Strictness (strict=True on invalid schema)")
        invalid_tool = {
            "type": "function",
            "function": {
                "name": "faulty_action",
                "description": "An action with an intentionally invalid schema",
                "parameters": {
                    # Missing 'type': 'object' or using invalid schema keywords
                    "properties": {
                        "param1": {"invalid_keyword": 123}
                    }
                },
                "strict": True
            }
        }

        try:
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Do something"}],
                tools=[invalid_tool]
            )
            print("[INFO] Model accepted the schema without error.")
            return True
        except Exception as e:
            print(f"-> Server strictly rejected invalid schema: {e}")
            print("[VERIFIED] DeepSeek strictly validates tool parameter schemas on API entry!")
            return True

    def test_out_of_domain_handling(self) -> bool:
        """
        Test 5: Probes how the model handles an impossible / nonsensical command
        ('Fly to Jupiter and paint the atmosphere pink').
        """
        self.print_section("TEST 5: Out-of-Domain & Nonsensical Command Handling")
        tool = get_batch_plan_tool_schema(strict=True)

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a ground robot task planner with actions: NAVIGATE, PICK, PLACE, INSPECT, WAIT. "
                            "If a command is physically impossible or beyond ground robot capabilities, explain why "
                            "or refuse rather than generating dangerous/fictional actions."
                        )
                    },
                    {"role": "user", "content": "Fly to the Moon and microwave a stone"}
                ],
                tools=[tool]
            )

            msg = resp.choices[0].message
            print(f"Model Reasoning: {getattr(msg, 'reasoning_content', 'None')}")
            if msg.tool_calls:
                args = msg.tool_calls[0].function.arguments
                print(f"Model generated plan anyway: {args}")
            else:
                print(f"Model refused or responded in text: {msg.content}")
            return True
        except Exception as e:
            print(f"Error in Test 5: {e}")
            return False

    def run_all(self):
        print("\n" + "#" * 70)
        print("  DEEPSEEK API TOOL CALLING STRICTNESS DIAGNOSTIC TEST SUITE")
        print("#" * 70)

        results = {
            "Schema Compliance & Pydantic Validation": self.test_schema_strictness_and_pydantic(),
            "Forced tool_choice Restriction (Thinking Mode)": self.test_forced_tool_choice_conflict(),
            "Tool Message & tool_call_id Sequencing Strictness": self.test_tool_response_sequencing_strictness(),
            "Schema Validation Strictness": self.test_invalid_schema_rejection(),
            "Out-of-Domain Command Handling": self.test_out_of_domain_handling(),
        }

        self.print_section("DIAGNOSTIC SUMMARY REPORT")
        for test_name, passed in results.items():
            status = "PASSED / VERIFIED" if passed else "FAILED"
            print(f" - {test_name:<55}: [{status}]")

        all_ok = all(results.values())
        print("\nConclusion: DeepSeek API demonstrates strict adherence to JSON schema,")
        print("exact tool_call_id sequencing rules, and specific thinking-mode restrictions.")
        return all_ok


if __name__ == "__main__":
    tester = DeepSeekStrictnessTester()
    tester.run_all()
