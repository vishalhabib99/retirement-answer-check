"""Deterministic layer of retirement-answer-check.

Checks an AI-drafted answer against data/facts.json and a few text rules.
Anything it can't verify goes to REVIEW; nothing unverified is ever SEND.
The advice-boundary and promissory *judgment* layer lives in the Claude Code
skill (skills/advice-judge); the phrase rules here are only a baseline.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

FACTS_PATH = Path(__file__).resolve().parents[2] / "data" / "facts.json"
FACTS = json.loads(FACTS_PATH.read_text())
SOURCES = FACTS["sources"]
CURRENT_YEAR = int(FACTS["_verified_on"][:4])

NEG = re.compile(r"\b(not|no|never|isn't|aren't|doesn't|don't|can't|cannot)\b", re.I)
PLAN = re.compile(r"401\(k\)|403\(b\)|457|\bTSP\b|\bplans?\b", re.I)
IRA = re.compile(r"\bIRAs?\b")
SIMPLE = re.compile(r"\bSIMPLE\b")
RMD = re.compile(r"\bRMDs?\b|minimum distribution", re.I)

# Contribution-limit keys per account family (values come from facts.json).
FAMILIES = {
    "simple": ["simple_limit", "simple_catch_up_50_plus"],
    "ira": ["ira_limit", "ira_limit_50_plus_total", "ira_catch_up_50_plus"],
    "plan": ["401k_403b_457_tsp_elective_deferral", "401k_catch_up_50_plus", "401k_catch_up_60_to_63"],
}
EXC = FACTS["early_distribution"]["exceptions"]
EXCEPTION_AMOUNTS = [
    (re.compile(r"home ?buyer|first home|first-time home|home purchase", re.I), 10000),
    (re.compile(r"birth|adoption", re.I), 5000),
    (re.compile(r"emergency", re.I), 1000),
]
RMD_UNVERIFIED_AGES = {75}

IN_SCOPE = re.compile(
    r"\bIRAs?\b|401\(k\)|403\(b\)|\b457\b|\bTSP\b|\bRMDs?\b|rollover|roll (it )?over|retire|pension|catch-up|"
    r"\bSIMPLE\b|\bRoth\b|target-date|stable value|minimum distribution", re.I)
OUT_OF_SCOPE = re.compile(r"\btrusts?\b|\bestate\b|insurance|\b529\b|social security|mortgage refinanc", re.I)

ADVICE = [r"\byou should\b", r"\bI'd\b", r"\bI would\b", r"\bif I were you\b",
          r"\bright (move|choice|call) for you\b", r"\bin your (situation|shoes)\b", r"\bat your age\b",
          r"\bbased on (the|your) (balance|age|income|savings)\b"]
PROMISSORY = [r"guarantee", r"\bcan'?t lose\b|\bcannot lose\b|\bwon'?t lose\b|\brisk-free\b|\bno risk\b",
              r"\bwill (\w+ly )?(grow|keep|outperform|return|earn|double)\b", r"\bsure to\b"]


def _sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]


def _flag(kind, span, reason, source=None):
    return {"type": kind, "span": span, "reason": reason, "source": SOURCES.get(source, source)}


def _year(sentence: str, answer: str, question: str) -> int:
    for text in (sentence, answer, question):
        m = re.search(r"\b(20\d\d)\b", text)
        if m:
            return int(m.group(1))
        if re.search(r"\blast year\b", text, re.I):
            return CURRENT_YEAR - 1
    return CURRENT_YEAR


def _family(text: str) -> str | None:
    if SIMPLE.search(text):
        return "simple"
    if IRA.search(text) and not PLAN.search(text.replace("IRA", "")):
        return "ira"
    if PLAN.search(text):
        return "plan"
    return None


def _money(s: str):
    for m in re.finditer(r"\$\s?([\d,]+(?:\.\d+)?)\s*(million|k)?", s, re.I):
        n = float(m.group(1).replace(",", ""))
        n *= {"million": 1e6, "k": 1e3}.get((m.group(2) or "").lower(), 1)
        yield m.group(0).strip(), int(n)


def _check_money(s, fam_ctx, answer, question, flags):
    for span, amount in _money(s):
        exc = next((v for rx, v in EXCEPTION_AMOUNTS if rx.search(s)), None)
        if exc is not None:
            if amount != exc:
                flags.append(_flag("wrong_fact", span, f"this exception's cap is ${exc:,}", "irs_early_dist"))
            continue
        fam = _family(s) or fam_ctx
        if fam is None:
            flags.append(_flag("unknown_fact", span, "dollar amount not covered by the facts table"))
            continue
        year = _year(s, answer, question)
        limits = FACTS["contribution_limits"]
        valid = {limits[k][str(year)] for k in FAMILIES[fam] if str(year) in limits[k]}
        if not valid:
            flags.append(_flag("unknown_fact", span, f"no verified {fam} limits for {year}"))
        elif amount not in valid:
            other = [y for k in FAMILIES[fam] for y, v in limits[k].items() if v == amount and y != str(year)]
            hint = f" (that is the {other[0]} figure)" if other else ""
            flags.append(_flag("wrong_fact", span, f"not a {year} {fam} limit{hint}",
                               limits[FAMILIES[fam][0]]["source"]))


def _pct_topic(t):
    if re.search(r"withh", t, re.I):
        return "withholding"
    if re.search(r"excess", t, re.I):
        return "excess"
    if RMD.search(t):
        return "rmd"
    if re.search(r"59|early|penalt|additional|before", t, re.I):
        return "early"
    return None


def _check_percent(s, question, answer, flags):
    topic = _pct_topic(s) or _pct_topic(question)
    simple_ctx = SIMPLE.search(s) or SIMPLE.search(question)
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*%", s):
        pct, span = float(m.group(1)), m.group(0)
        if topic == "withholding":
            ok, src = {FACTS["rollovers"]["plan_distribution_paid_to_participant_withholding_pct"]["value"]}, "irs_rollovers"
        elif topic == "excess":
            ok, src = {FACTS["excess_ira_contribution"]["excise_pct_per_year"]["value"]}, "irs_ira_limits"
            if re.search(r"one-time|once", s, re.I):
                flags.append(_flag("wrong_fact", "one-time", "the excess-contribution tax applies each year the excess remains", src))
        elif topic == "rmd":
            r = FACTS["rmd"]["missed_rmd_excise_pct"]
            ok, src = {r["value"], r["corrected_within_2_years_pct"]}, "irs_rmd_faq"
        elif topic == "early":
            ed = FACTS["early_distribution"]
            ok, src = {ed["additional_tax_pct"]["value"]}, "irs_early_dist"
            if simple_ctx:
                ok.add(ed["simple_ira_first_2_years_pct"]["value"])
                if pct == ed["additional_tax_pct"]["value"] and not re.search(r"\b(2|two) years\b", answer, re.I):
                    flags.append(_flag("wrong_fact", span, "SIMPLE IRA: the additional tax is 25% within the first 2 years of participation; "
                                       "stating 10% without that condition is misleading", src))
        else:
            flags.append(_flag("unknown_fact", span, "percentage not covered by the facts table"))
            continue
        if pct not in ok:
            flags.append(_flag("wrong_fact", span, f"expected {' or '.join(f'{v:g}%' for v in sorted(ok))}", src))


def _check_rules(s, question, flags):
    ctx = s + " " + question
    for m in re.finditer(r"(\d+)[- ]days?", s):
        if re.search(r"roll", ctx, re.I) and int(m.group(1)) != FACTS["rollovers"]["window_days"]["value"]:
            flags.append(_flag("wrong_fact", m.group(0), "the rollover window is 60 days", "irs_rollovers"))
    if RMD.search(s) or RMD.search(question):
        for m in re.finditer(r"\b(?:age|at|turn|turns|reach)\s+(\d{2})\b", s, re.I):
            age = int(m.group(1))
            if age in RMD_UNVERIFIED_AGES:
                flags.append(_flag("unknown_fact", m.group(0), "this RMD age is not verified in the facts table"))
            elif age != FACTS["rmd"]["start_age"]["value"]:
                flags.append(_flag("wrong_fact", m.group(0), "RMDs generally start at 73", "irs_rmd_faq"))
        if re.search(r"\bRoth\b", s) and RMD.search(s) and not NEG.search(s):
            flags.append(_flag("wrong_fact", s, "Roth IRAs and designated Roth accounts have no RMDs during the owner's lifetime", "irs_rmd_faq"))
    if re.search(r"separat", s, re.I) and re.search(r"\b55\b", ctx) and IRA.search(s) and not NEG.search(s):
        flags.append(_flag("wrong_fact", s, "the age-55 separation exception applies to plans, not IRAs", "irs_early_dist"))
    for rx, key in ((r"home ?buyer|first home|first-time home|home purchase", "first_time_homebuyer_10000"), (r"higher education|college", "higher_education")):
        if re.search(rx, s, re.I) and re.search(r"401\(k\)|403\(b\)|\bplans?\b", s, re.I) and not NEG.search(s) and not EXC[key]["plans"]:
            flags.append(_flag("wrong_fact", s, "this exception applies to IRAs, not employer plans", "irs_early_dist"))


def check(question: str, answer: str) -> dict:
    """Return {"decision": "SEND"|"REVIEW", "flags": [...]} for one draft answer."""
    answer = (answer or "").replace("’", "'")
    question = (question or "").replace("’", "'")
    flags: list[dict] = []
    if not answer.strip():
        return {"decision": "REVIEW", "flags": [_flag("empty_answer", "", "nothing to check; an empty draft is never SEND")]}

    both = question + " " + answer
    if OUT_OF_SCOPE.search(both) or not IN_SCOPE.search(both):
        flags.append(_flag("out_of_scope", "", "topic outside retirement accounts; route to a human"))

    fam_ctx = _family(question)
    for s in _sentences(answer):
        fam_ctx = _family(s) or fam_ctx
        _check_money(s, fam_ctx, answer, question, flags)
        _check_percent(s, question, answer, flags)
        _check_rules(s, question, flags)
        for rx in ADVICE:
            if (m := re.search(rx, s, re.I)):
                flags.append(_flag("personal_recommendation", m.group(0), "phrase rule: reads as a personal recommendation", "rule:advice-phrases"))
                break
        for rx in PROMISSORY:
            if (m := re.search(rx, s, re.I)):
                flags.append(_flag("promissory", m.group(0), "FINRA 2210(d)(1): promissory statement or performance projection",
                                   "https://www.finra.org/rules-guidance/rulebooks/finra-rules/2210"))
                break
    return {"decision": "REVIEW" if flags else "SEND", "flags": flags}
