import json
import os
import re
from copy import deepcopy

DATA_DIR = "data"

STARBOARD_KEY_RE = re.compile(r"^starboard_(channel_id|emoji|threshold|webhook_id)(?:_(\d+))?$")

KEY_MAP = {
    "channel_id": "channel",
    "emoji": "emoji",
    "threshold": "threshold",
    "webhook_id": "webhook",
}


def fix_nonsence(obj):
    """Recursively rename 'nonsence' keys to 'nonsense' and fix strings inside."""
    if isinstance(obj, dict):
        new = {}
        for k, v in obj.items():
            new_key = k
            if k == "nonsence":
                new_key = "nonsense"
            new[new_key] = fix_nonsence(v)
        return new
    elif isinstance(obj, list):
        return [fix_nonsence(i) for i in obj]
    elif isinstance(obj, str):
        return obj.replace("nonsence", "nonsense")
    else:
        return obj


def migrate_starboards(data):
    data = deepcopy(data)

    starboards = data.get("starboards", {})
    collected = {}
    keys_to_remove = []

    for key, value in data.items():
        match = STARBOARD_KEY_RE.match(key)
        if not match:
            continue

        field, index = match.groups()
        index = index or "1"

        collected.setdefault(index, {})[KEY_MAP[field]] = value
        keys_to_remove.append(key)

    if collected:
        for index, values in collected.items():
            starboards.setdefault(index, {}).update(values)
        data["starboards"] = starboards

        for key in keys_to_remove:
            data.pop(key, None)

    return data


def process_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return  # Skip invalid JSON

    original = deepcopy(data)

    data = fix_nonsence(data)
    data = migrate_starboards(data)

    if data != original:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Updated: {path}")


def main():
    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            if file.endswith(".json"):
                process_file(os.path.join(root, file))


if __name__ == "__main__":
    main()
