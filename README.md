# 🥗 Recipe & Grocery Planner — AI Agent

An AI agent that runs **entirely on your local machine** using [Ollama](https://ollama.com).
It plans weekly meals, manages your pantry, calculates nutrition, and writes shopping lists
to a file — all orchestrated by a local LLM that decides when and how to use its tools.

Built as part of an AI Agent assignment using plain Python and the `ollama` library.

---

## Requirements

- Python 3.11 or higher
- [Ollama](https://ollama.com) installed and running

---

## Setup

### 1. Install Ollama

Download and install from [https://ollama.com](https://ollama.com), then start it.
On Windows it runs as a system tray application after install.

### 2. Pull the model

```bash
ollama pull qwen3:4b
```

This downloads the model (~2.5 GB). Only needed once.

### 3. Clone the repo and install dependencies

```bash
git clone <your-repo-url>
cd recipe-planner-agent
pip install -r requirements.txt
```

### 4. Run the agent

```bash
python main.py
```

---

## Example Prompts

Try these to explore different capabilities:

**1. Meal planning (uses `manage_pantry` + `search_recipes`)**
```
Plan a 5-day vegetarian meal plan. I have pasta, eggs, and rice at home.
```

**2. Nutrition lookup (uses `calculate_nutrition`)**
```
What are the calories in Lentil Soup for 3 servings?
```

**3. Shopping list generation (uses `manage_pantry` + `write_shopping_list`)**
```
Write my shopping list for the week to a file.
```

You can also chain requests across turns — conversation history is kept, so follow-ups work:
```
You: Plan a 3-day meal plan.
Agent: [responds with plan]
You: Make day 2 cheaper.
Agent: [adjusts using existing context]
```

---

## Project Structure

```
recipe-planner-agent/
├── main.py                  # Entry point — CLI loop and startup checks
├── agent.py                 # Agent loop: message history, tool dispatch, logging
├── tools/
│   ├── __init__.py          # Exports TOOL_REGISTRY (list of tool functions)
│   ├── recipe_search.py     # Tool 1: Search recipes by ingredient and diet
│   ├── nutrition.py         # Tool 2: Calculate nutrition for a recipe
│   ├── pantry.py            # Tool 3: Read/write pantry inventory (pantry.json)
│   └── shopping_list.py     # Tool 4: Generate and write shopping list to file
├── data/
│   ├── recipes.json         # 15 mock recipes with ingredients and nutrition data
│   ├── pantry.json          # Persistent pantry inventory (modified at runtime)
│   └── shopping_list.txt    # Written by the agent when requested
├── requirements.txt
├── .env                     # Not committed — placeholder for future API keys
└── .gitignore
```

---

## How the Agent Works

The agent runs a loop inside `agent.py`:

1. The user's message + full conversation history is sent to `qwen3:4b` via Ollama.
2. If the model wants information, it returns a **tool call** (not text) — specifying which function to run and with what arguments.
3. The agent runs the Python function, logs the call and result to the terminal, and feeds the result back to the model.
4. Steps 1–3 repeat until the model produces a **plain text answer**.
5. The agent has a **10-step safety limit** to prevent infinite loops.

The tool-call trace is visible in the terminal during every run — this is required for the demo.

---

## Tools

| Tool | Purpose | Reads | Writes |
|---|---|---|---|
| `search_recipes` | Find recipes by ingredient or diet filter | `recipes.json` | — |
| `calculate_nutrition` | Calories, protein, carbs, fat for any recipe | `recipes.json` | — |
| `manage_pantry` | View, add, or remove pantry items | `pantry.json` | `pantry.json` |
| `write_shopping_list` | Compute what to buy, save to file | `recipes.json`, `pantry.json` | `shopping_list.txt` |

---

## Model

| | |
|---|---|
| **Model** | `qwen3:4b` |
| **Size** | ~2.5 GB |
| **Why** | Supports native tool/function calling, runs within 8 GB RAM, reliable JSON argument generation |
| **Fallback** | `llama3.2:3b` (lighter, weaker tool calling) |

---

## AI Tool Usage

This project was built with assistance from AI coding tools (Antigravity / Claude).
The AI was used for:
- Scaffolding boilerplate file structures
- Suggesting docstring formats compatible with the Ollama tool schema
- Explaining the ollama library's tool-calling API

All code was reviewed, understood, and adapted by the team. Every line is explainable in the viva.

---

## Credits

- [Ollama](https://ollama.com) — local LLM runtime
- [Qwen3](https://ollama.com/library/qwen3) by Alibaba Cloud — the language model
- [python-dotenv](https://pypi.org/project/python-dotenv/) — environment variable management
