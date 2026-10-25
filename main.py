"""
main.py — Entry Point

Starts the CLI interface for the Recipe & Grocery Planner Agent.
Handles startup checks, the input loop, and conversation history across turns.
"""

import sys
import os
import ollama
from agent import chat, SYSTEM_PROMPT, MODEL

# Fix Windows console encoding for emoji output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Load environment variables from .env (e.g. OLLAMA_NUM_GPU=0 for CPU-only mode)
from dotenv import load_dotenv
load_dotenv()


# ── Startup Check ─────────────────────────────────────────────────────────────

def check_ollama() -> None:
    """
    Verify that:
      1. The Ollama server is reachable at localhost:11434
      2. The required model (qwen3:4b) has been pulled and is available

    Exits with a helpful message if either check fails.
    """
    try:
        available_models = [m.model for m in ollama.list().models]
    except Exception:
        print("\n❌  Cannot connect to Ollama.")
        print("    Make sure Ollama is installed and running:")
        print("    https://ollama.com\n")
        sys.exit(1)

    if not any(MODEL in m for m in available_models):
        print(f"\n⚠️   Model '{MODEL}' not found locally.")
        print(f"    Pull it first by running:\n")
        print(f"        ollama pull {MODEL}\n")
        sys.exit(1)


# ── Main Loop ─────────────────────────────────────────────────────────────────

def main() -> None:
    """
    Start the CLI agent loop.

    Conversation history (messages list) persists across turns, so follow-up
    requests like "make day 2 cheaper" work correctly because the model can
    see everything that was said earlier.
    """
    check_ollama()

    print("\n" + "=" * 60)
    print("  🥗  Recipe & Grocery Planner Agent")
    print("=" * 60)
    print("  Model  :", MODEL)
    print("  Type 'quit' or press Ctrl+C to exit.")
    print("=" * 60 + "\n")
    print("Example prompts to try:")
    print("  • Plan a 5-day vegetarian meal plan.")
    print("    I have pasta, eggs, and rice at home.")
    print("  • What are the calories in Lentil Soup for 3 servings?")
    print("  • Write my shopping list for the week to a file.\n")
    print("-" * 60 + "\n")

    # Conversation history — the system prompt is always the first message
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        # ── Get user input ────────────────────────────────────────────────────
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye! 👋")
            break

        if user_input.lower() in {"quit", "exit", "q", "bye"}:
            print("\nGoodbye! 👋")
            break

        if not user_input:
            continue

        # ── Append user message and run agent ─────────────────────────────────
        messages.append({"role": "user", "content": user_input})
        print("\nAgent thinking...\n" + "- " * 30)

        messages = chat(messages)

        # ── Print the assistant's final response ──────────────────────────────
        last_assistant = next(
            (m for m in reversed(messages) if m.get("role") == "assistant"),
            None
        )
        if last_assistant:
            print(f"\n🤖  Agent:\n{last_assistant['content']}")

        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
