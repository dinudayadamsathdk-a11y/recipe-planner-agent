import json
from pathlib import Path

RECIPES_FILE = Path(__file__).parent.parent / "data" / "recipes.json"


def search_recipes(
    ingredients: list[str] = None,
    diet: str = "",
    max_results: int = 5
) -> str:
    """Search the recipe database for matching recipes.

    Args:
        ingredients: Optional list of ingredients the user has or wants to use.
                     Recipes containing ANY of these are ranked higher.
        diet: Optional dietary filter. Use 'vegetarian' or 'vegan'. Leave blank for no filter.
        max_results: Maximum number of recipes to return. Default is 5.

    Returns:
        A JSON string containing a list of matching recipes with name, ingredients,
        prep time, servings, and nutrition info per serving.
    """
    # ── Type coercion (small models sometimes send args as strings) ────────
    try:
        max_results = int(max_results)
    except (ValueError, TypeError):
        max_results = 5

    # Handle ingredients passed as a string representation of a list
    if isinstance(ingredients, str):
        # Try to parse JSON-style list, e.g. '["pasta", "eggs"]'
        try:
            ingredients = json.loads(ingredients)
        except json.JSONDecodeError:
            # Try Python-style list, e.g. "['pasta', 'eggs']"
            cleaned = ingredients.strip().strip("[]")
            ingredients = [i.strip().strip("'\"") for i in cleaned.split(",") if i.strip()]

    if max_results < 1 or max_results > 20:
        return json.dumps({"error": "max_results must be between 1 and 20."})

    try:
        data = json.loads(RECIPES_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return json.dumps({"error": "Recipe database not found at data/recipes.json."})
    except json.JSONDecodeError:
        return json.dumps({"error": "Recipe database is corrupted."})

    recipes = data.get("recipes", [])

    # Filter by diet preference
    if diet and diet.strip():
        diet_lower = diet.lower().strip()
        recipes = [
            r for r in recipes
            if diet_lower in [d.lower() for d in r.get("diet", [])]
        ]

    # Rank by ingredient overlap (most matching ingredients first)
    if ingredients:
        normalized = [i.lower().strip() for i in ingredients if i.strip()]

        def overlap_score(recipe):
            recipe_ings = [ing.lower() for ing in recipe.get("ingredients", [])]
            return sum(1 for ing in normalized if ing in recipe_ings)

        recipes = sorted(recipes, key=overlap_score, reverse=True)

    results = recipes[:max_results]

    if not results:
        return json.dumps({"message": "No recipes found matching your criteria.", "recipes": []})

    return json.dumps(results, indent=2)
