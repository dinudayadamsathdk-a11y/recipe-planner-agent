# Makes tools/ a Python package and exports all tool functions for use by the agent.
from .recipe_search import search_recipes
from .nutrition import calculate_nutrition
from .pantry import manage_pantry
from .shopping_list import write_shopping_list

# TOOL_REGISTRY is passed directly to ollama.chat(tools=...).
# The ollama library reads each function's type hints and docstring
# to auto-generate the JSON schema the model needs to call tools correctly.
TOOL_REGISTRY = [search_recipes, calculate_nutrition, manage_pantry, write_shopping_list]
