"""
agent.py — The Agent Loop

This module contains the core logic of the AI agent.
It sends conversation messages to the local Ollama model, handles tool call
requests from the model, runs the corresponding Python functions, feeds the
results back, and repeats until the model produces a final text answer.

KEY CONCEPTS (understand these for the viva):
  - messages: A list of dicts that represents the full conversation history.
              Roles can be "system", "user", "assistant", or "tool".
  - tool_calls: When the model wants to use a tool it returns structured data
                (not plain text) telling us which function to call and with what args.
  - The loop: We keep calling ollama.chat() in a while-loop, adding results back
              to messages each time, until the model produces plain text (no tool_calls).
  - MAX_STEPS: A safety limit so the agent cannot loop forever.
"""

import json
import ollama
from tools import TOOL_REGISTRY

# ── Configuration ────────────────────────────────────────────────────────────

MODEL = "llama3.2:latest"   # Local model to use via Ollama
MAX_STEPS = 10              # Maximum tool-call iterations per user turn

# ── System Prompt ─────────────────────────────────────────────────────────────
# This message is always the first in the conversation history.
# It defines the agent's identity, capabilities, and behavioural rules.

SYSTEM_PROMPT = """You are a helpful Recipe & Grocery Planner assistant.

Your job is to help users:
- Plan weekly meals based on dietary preferences and available ingredients
- Check and update their pantry inventory
- Calculate nutritional information for meals
- Generate and save shopping lists to a file

RULES — follow these strictly:
1. Before recommending purchases, always call manage_pantry with action='read' first.
2. When creating a meal plan, always call search_recipes to find suitable recipes first.
3. When the user asks to write a shopping list, you MUST call write_shopping_list — do not just describe the list in text.
4. If a tool returns an error field, explain the issue to the user clearly and suggest a fix.
5. Be concise. Summarise tool output; never dump raw JSON at the user.
6. For dietary preferences (vegetarian, vegan), always pass them to search_recipes.

OUTPUT FORMAT for meal plans — use exactly this layout:
  Day 1 — Breakfast: [recipe] | Lunch: [recipe] | Dinner: [recipe]
  Day 2 — ...
"""

# ── Tool Dispatcher ───────────────────────────────────────────────────────────

def run_tool(name: str, args: dict) -> str:
    """
    Look up a tool function by name and call it with the given arguments.

    Args:
        name: The function name the model requested (must match a function in TOOL_REGISTRY).
        args: A dict of keyword arguments to pass to the function.

    Returns:
        The tool's return value as a string (all tools return JSON strings).
    """
    # Build a name → function mapping from the registry
    tool_map = {fn.__name__: fn for fn in TOOL_REGISTRY}
    fn = tool_map.get(name)

    if fn is None:
        # Model hallucinated a tool name that doesn't exist
        return json.dumps({"error": f"Unknown tool '{name}'. Available tools: {list(tool_map.keys())}"})

    try:
        return fn(**args)
    except TypeError as e:
        # Model passed wrong argument names or types
        return json.dumps({"error": f"Bad arguments for tool '{name}': {str(e)}"})
    except Exception as e:
        # Catch-all so a tool crash never kills the agent loop
        return json.dumps({"error": f"Tool '{name}' raised an unexpected error: {str(e)}"})


# ── Agent Loop ────────────────────────────────────────────────────────────────

def chat(messages: list[dict]) -> list[dict]:
    """
    Run one full turn of the agent loop for a single user input.

    The loop:
      1. Send the current message history + available tools to Ollama.
      2. If the model returns tool_calls → run each tool, append results to history, repeat.
      3. If the model returns plain text → append it to history and return.
      4. If the model returns an empty response → retry up to MAX_RETRIES times.
      5. If MAX_STEPS is reached → append a warning message and return.

    Args:
        messages: The full conversation history so far (mutated in-place and returned).

    Returns:
        The updated messages list with the assistant's final response appended.
    """
    MAX_RETRIES = 3
    steps = 0  # Count how many tool-call rounds we've done this turn

    while steps < MAX_STEPS:

        # ── Step A: Ask the model what to do next ────────────────────────────
        # Retry on empty response — llama3.2 occasionally returns nothing
        response = None
        for attempt in range(MAX_RETRIES):
            try:
                response = ollama.chat(
                    model=MODEL,
                    messages=messages,
                    tools=TOOL_REGISTRY,  # Pass Python functions — Ollama auto-generates JSON schemas
                )
                # Validate response is non-empty
                msg = response.message
                if msg.tool_calls or (msg.content and msg.content.strip()):
                    break  # Good response — proceed
                else:
                    print(f"\n  ⚠  Empty response from model (attempt {attempt + 1}/{MAX_RETRIES}), retrying...")
            except Exception as e:
                err = str(e)
                print(f"\n  ⚠  Model error (attempt {attempt + 1}/{MAX_RETRIES}): {err}")
                if attempt == MAX_RETRIES - 1:
                    messages.append({
                        "role": "assistant",
                        "content": f"⚠️  The model returned an error after {MAX_RETRIES} attempts: {err}"
                    })
                    return messages

        if response is None:
            messages.append({"role": "assistant", "content": "⚠️  Model returned no response after retries."})
            return messages

        msg = response.message

        # ── Step B: Model wants to call one or more tools ─────────────────────
        if msg.tool_calls:
            # Add the assistant's tool-call request to history
            # (the model needs to see its own request when we loop back)
            messages.append(msg)

            for tool_call in msg.tool_calls:
                name = tool_call.function.name
                args = tool_call.function.arguments or {}

                # ── LOG: visible in the CLI during demo ──────────────────────
                print(f"\n  🔧 Tool call : {name}")
                print(f"     Arguments : {json.dumps(args)}")

                # Run the actual Python function
                result = run_tool(name, args)

                # Truncate very long results in the log (full result still goes to model)
                log_result = result if len(result) <= 300 else result[:300] + " ... [truncated]"
                print(f"     Result    : {log_result}")

                # Add the tool's result back into the conversation history
                messages.append({
                    "role": "tool",
                    "content": result,
                    "name": name,
                })

            steps += 1
            continue  # ← Send the updated history back to the model

        # ── Step C: Model produced a final text answer ────────────────────────
        else:
            messages.append({
                "role": "assistant",
                "content": msg.content.strip()
            })
            return messages  # ← Done for this turn

    # ── Step limit reached ────────────────────────────────────────────────────
    messages.append({
        "role": "assistant",
        "content": (
            f"⚠️  I reached the {MAX_STEPS}-step limit before finishing. "
            "The task may be too complex for a single request — try breaking it into smaller steps."
        )
    })
    return messages
