import json
from pathlib import Path

RECIPES_FILE = Path(__file__).parent.parent / "data" / "recipes.json"
PANTRY_FILE = Path(__file__).parent.parent / "data" / "pantry.json"
OUTPUT_DIR = Path(__file__).parent.parent / "data"


def write_shopping_list(meal_plan: list[str], filename: str = "shopping_list.txt") -> str:
    """Generate a shopping list for a given meal plan by comparing required recipe ingredients
    against the current pantry inventory, then write the result to a text file.

    Args:
        meal_plan: List of recipe names to include in the shopping plan.
                   Example: ['Pasta Primavera', 'Egg Fried Rice', 'Lentil Soup']
        filename: Output filename for the shopping list. Default is 'shopping_list.txt'.
                  The file is saved in the data/ directory.

    Returns:
        A JSON string with the output file path, the list of items to buy,
        items already in the pantry, and any recipe names that were not recognised.
    """
    if not meal_plan:
        return json.dumps({"error": "meal_plan cannot be empty. Provide at least one recipe name."})

    # ── Type coercion (small models sometimes send args as strings) ────────
    if isinstance(meal_plan, str):
        try:
            meal_plan = json.loads(meal_plan)
        except json.JSONDecodeError:
            cleaned = meal_plan.strip().strip("[]")
            meal_plan = [i.strip().strip("'\"") for i in cleaned.split(",") if i.strip()]

    if not isinstance(meal_plan, list):
        return json.dumps({"error": "meal_plan must be a list of recipe name strings."})

    # Sanitise filename — strip any path traversal attempts
    safe_name = Path(filename).name
    if not safe_name:
        safe_name = "shopping_list.txt"
    if not safe_name.endswith(".txt"):
        safe_name += ".txt"
    output_path = OUTPUT_DIR / safe_name

    # Load recipes
    try:
        recipes_data = json.loads(RECIPES_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return json.dumps({"error": "Recipe database not found at data/recipes.json."})
    except json.JSONDecodeError:
        return json.dumps({"error": "Recipe database is corrupted."})

    recipe_map = {r["name"].lower(): r for r in recipes_data.get("recipes", [])}

    # Collect all required ingredients from all recipes in the meal plan
    required: set[str] = set()
    not_found: list[str] = []

    for name in meal_plan:
        if not isinstance(name, str) or not name.strip():
            continue
        recipe = recipe_map.get(name.lower().strip())
        if recipe:
            required.update(ing.lower().strip() for ing in recipe.get("ingredients", []))
        else:
            not_found.append(name)

    # Load pantry and subtract items we already have
    if PANTRY_FILE.exists():
        try:
            pantry_data = json.loads(PANTRY_FILE.read_text(encoding="utf-8"))
            pantry = pantry_data.get("items", [])
        except json.JSONDecodeError:
            pantry = []
    else:
        pantry = []

    pantry_set = {i.lower().strip() for i in pantry}

    to_buy = sorted(required - pantry_set)
    already_have = sorted(required & pantry_set)

    # Build the file contents
    lines = [
        "=" * 40,
        "       SHOPPING LIST",
        "=" * 40,
        "",
        "Meal plan:",
    ]
    for name in meal_plan:
        lines.append(f"  • {name}")
    lines += [
        "",
        f"Items to buy ({len(to_buy)}):",
    ]
    if to_buy:
        for item in to_buy:
            lines.append(f"  □ {item}")
    else:
        lines.append("  (You already have everything!)")

    lines += [
        "",
        f"Already in pantry ({len(already_have)}):",
    ]
    for item in already_have:
        lines.append(f"  ✓ {item}")

    if not_found:
        lines += [
            "",
            "⚠  Recipes not recognised (check spelling):",
        ]
        for name in not_found:
            lines.append(f"  - {name}")

    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")

    return json.dumps({
        "file_written": str(output_path),
        "items_to_buy": to_buy,
        "items_count": len(to_buy),
        "already_in_pantry": already_have,
        "recipes_not_found": not_found,
    })
