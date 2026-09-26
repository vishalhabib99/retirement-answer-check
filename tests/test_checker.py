import json
from pathlib import Path

import pytest

from retirement_answer_check import check

EVALS = Path(__file__).resolve().parents[1] / "evals"
DEV = [json.loads(line) for line in (EVALS / "cases.jsonl").read_text().splitlines() if line.strip()]


@pytest.mark.parametrize("case", DEV, ids=[c["id"] for c in DEV])
def test_dev_case(case):
    result = check(case["question"], case["answer"])
    assert result["decision"] == case["expected"]
    assert set(case["expected_flags"]) <= {f["type"] for f in result["flags"]}


def test_every_wrong_fact_flag_cites_a_source():
    for c in DEV:
        for f in check(c["question"], c["answer"])["flags"]:
            if f["type"] == "wrong_fact":
                assert f["source"], c["id"]


def test_unknown_year_is_review_not_send():
    assert check("401(k) limit for 2031?", "It's $24,500 for 2031.")["decision"] == "REVIEW"
