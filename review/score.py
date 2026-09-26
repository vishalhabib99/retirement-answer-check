"""Score a reviewer's decisions against the answer key.

Usage: python review/score.py DECISIONS.json KEY.json
       python review/score.py --policy approve_all|reject_all|follow_flags|perfect QUEUE_HTML KEY.json

DECISIONS.json is what review.html downloads: {"reviewer": ..., "decisions":
[{"id", "action": "approve"|"reject", "seconds", "note"}]}. Only known-answer
items are scored. --policy scores a scripted reviewer, to show what each metric
catches; it is not a person.
"""
from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

LABELS = {
    "bad_flagged": "Caught bad answers the checker flagged",
    "bad_unflagged": "Caught bad answers with no flag (automation-bias check)",
    "good": "Approved good answers (not over-rejecting)",
}


def score(decisions: list[dict], key: dict) -> dict:
    by_id = {d["id"]: d for d in decisions}
    out = {}
    for kind in LABELS:
        ids = [i for i, e in key.items() if e.get("kind") == kind]
        done = [i for i in ids if i in by_id]
        right = [i for i in done if by_id[i]["action"] == key[i]["expected_action"]]
        out[kind] = {"right": len(right), "answered": len(done), "total": len(ids)}
    secs = [d["seconds"] for d in decisions if isinstance(d.get("seconds"), (int, float))]
    out["median_seconds"] = statistics.median(secs) if secs else None
    out["live_reviewed"] = sum(1 for i in by_id if not key.get(i, {}).get("known"))
    return out


def report(s: dict, who: str) -> str:
    lines = [f"Reviewer: {who}"]
    for kind, label in LABELS.items():
        r = s[kind]
        pct = f"{100 * r['right'] / r['answered']:.0f}%" if r["answered"] else "n/a"
        lines.append(f"  {label}: {r['right']}/{r['answered']} ({pct})"
                     + (f", {r['total'] - r['answered']} skipped" if r["answered"] < r["total"] else ""))
    if s["median_seconds"] is not None:
        lines.append(f"  Median time per item: {s['median_seconds']:.0f}s")
    lines.append(f"  Live items reviewed: {s['live_reviewed']} (not scored)")
    return "\n".join(lines)


def _queue_from_html(path: Path) -> list[dict]:
    m = re.search(r"const QUEUE = (\[.*?\]);\n", path.read_text(), re.S)
    return json.loads(m.group(1).replace("<\\/", "</"))


def policy_decisions(policy: str, queue: list[dict], key: dict) -> list[dict]:
    if policy == "approve_all":
        act = lambda it: "approve"
    elif policy == "reject_all":
        act = lambda it: "reject"
    elif policy == "follow_flags":
        act = lambda it: "reject" if it["flags"] else "approve"
    elif policy == "perfect":
        act = lambda it: key[it["id"]].get("expected_action", "reject" if it["flags"] else "approve")
    else:
        raise SystemExit(f"unknown policy {policy}")
    return [{"id": it["id"], "action": act(it), "seconds": None} for it in queue]


def main() -> None:
    args = sys.argv[1:]
    if args and args[0] == "--policy":
        policy, queue_path, key_path = args[1], Path(args[2]), Path(args[3])
        key = json.loads(key_path.read_text())
        decisions = policy_decisions(policy, _queue_from_html(queue_path), key)
        print(report(score(decisions, key), f"scripted policy '{policy}' (not a person)"))
        return
    data = json.loads(Path(args[0]).read_text())
    print(report(score(data["decisions"], json.loads(Path(args[1]).read_text())), data.get("reviewer") or "unnamed"))


if __name__ == "__main__":
    main()
