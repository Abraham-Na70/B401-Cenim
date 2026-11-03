"""
CLI Entry point for the DeepSeek Robot Action Planner.
Usage:
    python main.py "Go to the kitchen and bring me the red mug"
    python main.py --agent "Navigate to station B and inspect the conveyor"
    python main.py --test-strictness
    python main.py --interactive
"""

import argparse
import json
import sys
from planner import RobotActionPlanner
from test_strictness import DeepSeekStrictnessTester


def format_plan_output(plan, reasoning=None):
    print("\n" + "=" * 60)
    print(f"🤖 ROBOT ACTION PLAN: {plan.plan_name}")
    print("=" * 60)
    print(f"🎯 Goal: {plan.goal}")
    if plan.estimated_duration_seconds:
        print(f"⏱️ Estimated Duration: {plan.estimated_duration_seconds:.1f}s")
    if reasoning:
        print(f"\n🧠 Planner Reasoning:\n   {reasoning.strip()}")

    print("\n📋 Execution Steps:")
    for idx, action in enumerate(plan.actions, 1):
        icon = {
            "NAVIGATE": "🧭",
            "PICK": "🦾",
            "PLACE": "📦",
            "INSPECT": "🔍",
            "WAIT": "⏳",
            "OPEN": "🚪",
            "CLOSE": "🚪",
        }.get(action.action_type.value, "⚙️")

        print(f"  {idx}. {icon} [{action.action_type.value:<8}] Target: {action.target:<20}")
        print(f"     Description: {action.description}")
        if action.parameters:
            print(f"     Parameters : {action.parameters}")
    print("=" * 60 + "\n")


def run_interactive_repl(planner: RobotActionPlanner, agent_mode: bool = False):
    print("\n" + "=" * 60)
    print("  🤖 DeepSeek Robot Action Planner - Interactive REPL")
    print(f"  Mode: {'Agent (Reactive Closed-Loop)' if agent_mode else 'Batch (End-to-End Plan)'}")
    print("  Type 'exit', 'quit', or 'q' to stop.")
    print("=" * 60 + "\n")

    while True:
        try:
            cmd = input("RobotCommand> ").strip()
            if not cmd:
                continue
            if cmd.lower() in ("exit", "quit", "q"):
                print("Exiting...")
                break

            if agent_mode:
                print("\n[Running reactive agent loop with simulated robot feedback...]")
                history = planner.plan_interactive(cmd)
                for item in history:
                    if item.get("type") == "final_completion":
                        print(f"\n✅ Finished: {item.get('content')}")
                    else:
                        print(f"Step {item['step']}: Action `{item['action']}` ({item['arguments']}) -> {item['result']}")
            else:
                print("\n[Generating structured action plan via DeepSeek API...]")
                plan, reasoning = planner.plan_batch(cmd)
                format_plan_output(plan, reasoning)

        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting...")
            break
        except Exception as e:
            print(f"\n[Error]: {e}\n")


def main():
    parser = argparse.ArgumentParser(
        description="DeepSeek Robot Action Planner & Tool Calling Strictness Tester"
    )
    parser.add_argument(
        "command",
        nargs="?",
        type=str,
        help="Natural language instruction for the robot (e.g., 'Go to lab and fetch the beaker')",
    )
    parser.add_argument(
        "--agent",
        action="store_true",
        help="Run in interactive closed-loop agent mode instead of batch planning",
    )
    parser.add_argument(
        "--test-strictness",
        action="store_true",
        help="Run the DeepSeek API strictness diagnostic test suite",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start an interactive prompt session (REPL)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON format only (useful for piping into ROS / robotics systems)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override the DeepSeek model name (default: deepseek-flash)",
    )

    args = parser.parse_args()

    if args.test_strictness:
        tester = DeepSeekStrictnessTester()
        success = tester.run_all()
        sys.exit(0 if success else 1)

    try:
        planner = RobotActionPlanner(model=args.model)
    except Exception as e:
        print(f"Initialization error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.interactive:
        run_interactive_repl(planner, agent_mode=args.agent)
        return

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.agent:
        print(f"\n[Executing command in reactive agent mode]: '{args.command}'")
        history = planner.plan_interactive(args.command)
        if args.json:
            print(json.dumps(history, indent=2))
        else:
            for item in history:
                if item.get("type") == "final_completion":
                    print(f"\n🏁 Complete: {item.get('content')}")
                else:
                    print(f"Step {item['step']}: Action `{item['action']}` ({item['arguments']}) -> {item['result']}")
    else:
        try:
            plan, reasoning = planner.plan_batch(args.command)
            if args.json:
                print(plan.model_dump_json(indent=2))
            else:
                format_plan_output(plan, reasoning)
        except Exception as e:
            print(f"Planning failed: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
