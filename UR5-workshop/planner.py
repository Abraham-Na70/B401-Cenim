"""
Robot Action Planner powered by DeepSeek API.
Converts natural language commands into structured robot action plans via Tool Calling.
Supports:
1. Batch Planning (generating an end-to-end RobotPlan in one turn)
2. Interactive Agent Planning (closed-loop execution with simulated robot feedback)
"""

import json
import os
from typing import Any, Callable, Dict, List, Optional, Tuple
from openai import OpenAI
from pydantic import ValidationError

from models import (
    ActionType,
    RobotAction,
    RobotPlan,
    get_batch_plan_tool_schema,
    get_discrete_action_tools_schema,
)


class RobotActionPlanner:
    """
    Translates natural language instructions into structured robot actions using DeepSeek API.
    """

    DEFAULT_SYSTEM_PROMPT = (
        "You are an expert autonomous robot task planner. "
        "Your task is to decompose high-level human instructions into a sequence of atomic, "
        "physically feasible robot action commands. "
        "Strictly adhere to the tool schema and provide clear, precise targets and descriptions."
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        # Resolve API key from arguments or environment
        resolved_key = (
            api_key
            or os.environ.get("DEEPSEEK_API_KEY")
            or os.environ.get("ANTHROPIC_AUTH_TOKEN")
            or os.environ.get("OPENAI_API_KEY")
        )
        if not resolved_key:
            raise ValueError(
                "No API key found. Please set DEEPSEEK_API_KEY or ANTHROPIC_AUTH_TOKEN environment variable."
            )

        self.base_url = base_url or os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.model = model or os.environ.get("DEEPSEEK_MODEL", "deepseek-flash")

        self.client = OpenAI(
            api_key=resolved_key,
            base_url=self.base_url,
        )

    def plan_batch(
        self,
        user_command: str,
        system_prompt: Optional[str] = None,
        strict_schema: bool = True,
    ) -> Tuple[RobotPlan, Optional[str]]:
        """
        Generate an end-to-end structured RobotPlan from a natural language command.
        
        Returns:
            Tuple of (validated RobotPlan, reasoning_content_if_available)
        """
        prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        tools = [get_batch_plan_tool_schema(strict=strict_schema)]

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Command to plan: {user_command}"},
        ]

        # NOTE: DeepSeek Thinking Mode throws HTTP 400 if tool_choice is forced with a dict.
        # We leave tool_choice as default ("auto") to avoid the Thinking Mode conflict.
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
        )

        choice = response.choices[0]
        message = choice.message
        reasoning = getattr(message, "reasoning_content", None)

        if not message.tool_calls:
            # If the model replied with text instead of tool call, check if text contains JSON or raise error
            raise RuntimeError(
                f"Model did not call 'submit_action_plan'. Response text: {message.content}"
            )

        tool_call = message.tool_calls[0]
        if tool_call.function.name != "submit_action_plan":
            raise RuntimeError(f"Unexpected tool called: {tool_call.function.name}")

        try:
            raw_args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError as err:
            raise ValueError(
                f"Failed to parse tool call arguments as JSON: {tool_call.function.arguments}"
            ) from err

        try:
            plan = RobotPlan.model_validate(raw_args)
        except ValidationError as err:
            raise ValueError(f"Tool call arguments failed Pydantic validation: {err}") from err

        return plan, reasoning

    def plan_interactive(
        self,
        user_command: str,
        max_steps: int = 8,
        custom_executor: Optional[Callable[[str, Dict[str, Any]], str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes a reactive agent loop using discrete action tools.
        Follows DeepSeek's strict tool sequencing requirement:
        Every assistant message with 'tool_calls' is immediately answered with matching tool messages.
        """
        tools = get_discrete_action_tools_schema(strict=True)

        system_msg = (
            "You are an interactive robot task controller. Execute the user's command step-by-step "
            "by invoking the available robot action tools. After receiving tool execution results, "
            "determine the next step or conclude when the goal is achieved."
        )

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_command},
        ]

        execution_history: List[Dict[str, Any]] = []

        def default_simulator(func_name: str, args: Dict[str, Any]) -> str:
            if func_name == "navigate_to":
                return f"Successfully navigated to {args.get('location')}. Status: ARRIVED."
            elif func_name == "pick_object":
                return f"Grasper closed around {args.get('object_name')}. Status: GRASP_SUCCESS."
            elif func_name == "place_object":
                return f"Released {args.get('object_name')} onto {args.get('target_surface')}. Status: PLACED."
            elif func_name == "inspect_target":
                return f"Sensor scan of {args.get('target')} completed. Status: NORMAL, NO_OBSTACLE."
            elif func_name == "wait_seconds":
                return f"Paused for {args.get('seconds')} seconds ({args.get('reason')}). Status: RESUMED."
            return "Command executed successfully."

        executor = custom_executor or default_simulator

        for step in range(1, max_steps + 1):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
            )

            assistant_msg = response.choices[0].message
            tool_calls = assistant_msg.tool_calls

            # Store assistant response in history (DeepSeek strictly requires reasoning_content to be preserved)
            reasoning = getattr(assistant_msg, "reasoning_content", None)
            asst_dict: Dict[str, Any] = {
                "role": "assistant",
                "content": assistant_msg.content or "",
            }
            if reasoning is not None:
                asst_dict["reasoning_content"] = reasoning

            if tool_calls:
                asst_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ]
            messages.append(asst_dict)

            # If no tool calls, model has finished the plan
            if not tool_calls:
                execution_history.append({
                    "step": step,
                    "type": "final_completion",
                    "content": assistant_msg.content,
                })
                break

            # STRICT REQUIREMENT: Respond to EVERY tool call with matching tool_call_id
            for tc in tool_calls:
                func_name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}

                # Execute action via robot simulator / executor
                result = executor(func_name, args)

                execution_history.append({
                    "step": step,
                    "action": func_name,
                    "arguments": args,
                    "result": result,
                })

                # Append tool response
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

        return execution_history
