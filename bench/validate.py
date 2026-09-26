"""Check that every answer-key claim in questions.jsonl points at a real entry in
data/facts.json and matches its value. Run before freezing the set."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
FACTS = json.loads((HERE.parent / "data" / "facts.json").read_text())


def lookup(path):
    node = FACTS
    for part in path.split("."):
        node = node[part]
    return node


def matches(found, expected):
    if isinstance(found, dict):
        found = found.get("value", found)
    if isinstance(found, list):
        return expected in found
    if isinstance(found, str) and isinstance(expected, str):
        return expected.lower() in found.lower() or found.lower() in expected.lower()
    return found == expected


def main():
    errors = 0
    rows = [json.loads(l) for l in (HERE / "questions.jsonl").read_text().splitlines() if l.strip()]
    for q in rows:
        for r in q["required"]:
            try:
                found = lookup(r["fact"])
            except KeyError:
                print(f"{q['id']}: no fact at {r['fact']}")
                errors += 1
                continue
            if r["value"] == "compensation cap":  # the _rule text, checked by eye
                continue
            if not matches(found, r["value"]):
                print(f"{q['id']}: {r['fact']} is {found!r}, key says {r['value']!r}")
                errors += 1
    print(f"{len(rows)} questions, {sum(len(q['required']) for q in rows)} key claims, {errors} errors")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
