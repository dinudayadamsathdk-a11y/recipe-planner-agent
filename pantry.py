import json
from pathlib import Path

PANTRY_FILE = Path(__file__).parent.parent / "data" / "pantry.json"


def manage_pantry(action: str, items: list[str] = None) -> str:
    """Read, add to, or remove items from the persistent pantry inventory stored in pantry.json.

    Args:
        action: The operation to perform. Must be one of:
                'read'   - list everything currently in the pantry,
                'add'    - add one or more new items to the pantry,
                'remove' - remove one or more items from the pantry.
        items: List of ingredient names to add or remove.
               Required when action is 'add' or 'remove'. Ignored for 'read'.

    Returns:
        A JSON string containing the full pantry contents after the operation is applied.
    """
    valid_actions = {"read", "add", "remove"}
    if not action or action.lower().strip() not in valid_actions:
        return json.dumps({
            "error": f"Invalid action '{action}'. Must be one of: read, add, remove."
        })

    action = action.lower().strip()

    # Load existing pantry (create default if missing)
    if PANTRY_FILE.exists():
        try:
            data = json.loads(PANTRY_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {"items": []}
    else:
        data = {"items": []}

    current_items = [i.lower().strip() for i in data.get("items", [])]

    if action == "read":
        return json.dumps({
            "pantry": current_items,
            "total_items": len(current_items)
        })

    # 'add' and 'remove' both require an items list
    if not items:
        return json.dumps({
            "error": f"'items' list is required for action '{action}'."
        })

    # ── Type coercion (small models sometimes send args as strings) ────────
    if isinstance(items, str):
        try:
            items = json.loads(items)
        except json.JSONDecodeError:
            cleaned = items.strip().strip("[]")
            items = [i.strip().strip("'\"") for i in cleaned.split(",") if i.strip()]

    if not isinstance(items, list):
        return json.dumps({
            "error": "'items' must be a list of strings."
        })

    normalized_input = [i.lower().strip() for i in items if isinstance(i, str) and i.strip()]

    if not normalized_input:
        return json.dumps({"error": "No valid item names provided."})

    if action == "add":
        added = []
        for item in normalized_input:
            if item not in current_items:
                current_items.append(item)
                added.append(item)
        result_msg = f"Added: {added}" if added else "All items were already in the pantry."

    elif action == "remove":
        before = set(current_items)
        current_items = [i for i in current_items if i not in normalized_input]
        removed = list(before - set(current_items))
        result_msg = f"Removed: {removed}" if removed else "None of those items were in the pantry."

    # Persist changes back to disk
    data["items"] = current_items
    PANTRY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    return json.dumps({
        "pantry": current_items,
        "total_items": len(current_items),
        "action_performed": action,
        "details": result_msg
    })
