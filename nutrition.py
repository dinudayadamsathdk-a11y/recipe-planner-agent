import json
from pathlib import Path

RECIPES_FILE = Path(__file__).parent.parent / "data" / "recipes.json"


def calculate_nutrition(recipe_name: str, servings: int = 1) -> str:
    """Calculate the total nutritional content for a given recipe and number of servings.

    Args:
        recipe_name: The exact name of the recipe to look up (case-insensitive).
        servings: Number of servings to calculate nutrition for. Must be between 1 and 10.

    Returns:
        A JSON string with total calories, protein grams, carbohydrate grams, and fat grams
        for the requested number of servings.
    """
    if not recipe_name or not recipe_name.strip():
        return json.dumps({"error": "recipe_name cannot be empty."})

    # ── Type coercion (small models sometimes send args as strings) ────────
    try:
        servings = int(servings)
    except (ValueError, TypeError):
        return json.dumps({"error": "servings must be a whole number between 1 and 10."})

    if servings < 1 or servings > 10:
        return json.dumps({"error": "servings must be a whole number between 1 and 10."})

    try:
        data = json.loads(RECIPES_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return json.dumps({"error": "Recipe database not found at data/recipes.json."})
    except json.JSONDecodeError:
        return json.dumps({"error": "Recipe database is corrupted."})

    name_lower = recipe_name.lower().strip()
    match = next(
        (r for r in data.get("recipes", []) if r["name"].lower() == name_lower),
        None
    )

    if not match:
        return json.dumps({
            "error": (
                f"Recipe '{recipe_name}' not found. "
                "Use search_recipes to find the correct recipe name."
            )
        })

    n = match["nutrition_per_serving"]
    return json.dumps({
        "recipe": match["name"],
        "servings_requested": servings,
        "total_calories": n["calories"] * servings,
        "total_protein_g": n["protein_g"] * servings,
        "total_carbs_g": n["carbs_g"] * servings,
        "total_fat_g": n["fat_g"] * servings,
        "note": f"Values are for {servings} serving(s). Per-serving values × {servings}."
    })
