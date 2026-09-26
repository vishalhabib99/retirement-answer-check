import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "review"))

from build_queue import KINDS, _load, build  # noqa: E402
from score import policy_decisions, score  # noqa: E402

LIVE = _load(ROOT / "evals/heldout.jsonl") + _load(ROOT / "evals/heldout2.jsonl")
KNOWN = _load(ROOT / "evals/cases.jsonl")


def test_every_known_kind_is_seeded_and_labels_stay_out_of_the_queue():
    queue, key = build(LIVE, KNOWN, audit_rate=0.15, per_kind=2, seed=7)
    kinds = [e["kind"] for e in key.values() if e["known"]]
    assert sorted(kinds) == sorted(k for k in KINDS for _ in range(2))
    for item in queue:
        assert set(item) == {"id", "question", "answer", "reason", "flags"}


def test_known_items_look_like_live_ones():
    queue, key = build(LIVE, KNOWN, audit_rate=0.15, per_kind=2, seed=7)
    by_id = {q["id"]: q for q in queue}
    for item_id, e in key.items():
        if e.get("kind") == "bad_unflagged" or e.get("kind") == "good":
            assert by_id[item_id]["reason"] == "audit" and by_id[item_id]["flags"] == []
        if e.get("kind") == "bad_flagged":
            assert by_id[item_id]["reason"] == "flagged" and by_id[item_id]["flags"]


def test_same_seed_same_queue():
    assert build(LIVE, KNOWN, 0.15, 2, 3) == build(LIVE, KNOWN, 0.15, 2, 3)


def test_flag_follower_fails_only_the_automation_bias_check():
    queue, key = build(LIVE, KNOWN, 0.15, 2, 7)
    s = score(policy_decisions("follow_flags", queue, key), key)
    assert s["bad_flagged"]["right"] == 2
    assert s["bad_unflagged"]["right"] == 0
    assert s["good"]["right"] == 2


def test_page_contains_no_answer_key(tmp_path):
    subprocess.run([sys.executable, str(ROOT / "review/build_queue.py"), "--out", str(tmp_path)], check=True, capture_output=True)
    page = (tmp_path / "review.html").read_text()
    key = json.loads((tmp_path / "key.json").read_text())
    assert "__QUEUE__" not in page and "__QID__" not in page
    for word in ("expected_action", "source_case", '"known"', "bad_unflagged"):
        assert word not in page
    assert any(e["known"] for e in key.values())
