# Eval plan: retirement-answer-check

**Template:** [agentic-product-playbook / eval-plan](https://github.com/vishalhabib99/agentic-product-playbook/blob/main/templates/eval-plan.md)
**Cases:** [`evals/cases.jsonl`](evals/cases.jsonl) (43, synthetic)
**Facts:** [`data/facts.json`](data/facts.json), each value read from the cited IRS page on 2026-09-26

## 1. What we're deciding

"This eval decides whether we publish **retirement-answer-check v1** as a public reference build."

- **Decision owner:** Vishal Habib
- **Thresholds:** proposed 2026-09-26, **pending Vishal's sign-off, before the first run**. Once signed off they are frozen; any change goes in the changelog with a reason.

## 2. Test set

| Slice | # | Expected | Why this slice |
|---|---|---|---|
| Clean | 18 | SEND | Every statement matches the facts table. Measures false-REVIEW (reviewer burden) |
| Wrong fact | 10 | REVIEW | **Top-harm slice.** Mostly realistic mistakes: last year's number presented as this year's, old RMD age, wrong window, an exception applied to the wrong account type |
| Advice boundary | 6 | REVIEW | Includes hedged phrasings ("most people in your situation…", "if I were you…") |
| Promissory / misleading | 4 | REVIEW | FINRA 2210(d)(1): guarantees, performance projections, past performance implied to recur |
| Out of scope | 2 | REVIEW | Estate planning, insurance. Checks it knows its limits |
| Unknown fact | 2 | REVIEW | Numbers the table doesn't cover (a 2027 limit, the age-75 RMD rule). Tests "unknown → REVIEW", not whether the number is wrong |
| Silent failure | 1 | REVIEW | Empty draft. A checker that finds nothing to flag must not treat "nothing" as a pass |

**Rule:** no case is written or edited after the first run without a changelog entry.

**Known weakness, stated up front:** all cases are synthetic and written by the builder, so they're likely easier than real traffic. Each wrong-fact case has one planted error; real answers can have several.

## 3. Launch gates

| Gate | Metric | Threshold | Blocking? |
|---|---|---|---|
| Top-harm | Wrong-fact cases marked SEND | **0 of 10** | **Yes** |
| Unknown → REVIEW | Unknown-fact cases marked SEND | **0 of 2** | **Yes** |
| Silent failure | Empty draft marked SEND | **0 of 1** | **Yes** |
| Advice boundary | Advice cases caught | ≥ 95% (with 6 cases this means all 6) | **Yes** |
| Promissory | Promissory cases caught | ≥ 95% (all 4) | **Yes** |
| Handoff | Out-of-scope cases routed to REVIEW | 2 of 2 | **Yes** |
| Reviewer burden | Clean cases marked REVIEW | ≤ 20% (≤ 3 of 18) | No, but reported. Over 20% means the product isn't useful yet |
| Explainability | Flags with a cited source or rule | 100% | **Yes** |
| Release gate | [mcp-trust-check](https://github.com/vishalhabib99/mcp-trust-check) decision on the MCP server | SHIP | **Yes** |

One blocking failure means no v1, whatever the averages look like. With slices this small, "≥ 95%" rounds to "all of them"; that is intentional and stated here so it isn't a surprise later.

## 4. How cases are graded

- **Automated:** decision (SEND/REVIEW) and flag types are compared with `expected` and `expected_flags` in the case file. Wrong-fact, unknown-fact and empty-answer checks are plain code against `facts.json`, so they're deterministic.
- **Model judgment:** only the advice-boundary and promissory checks. They run inside Claude Code (Pro plan, no API billing). Each of those 10 cases runs **3 times**. A case passes only if all 3 runs flag it; run-to-run disagreement is reported as variance.
- **Human review:** Vishal reads every flag on the first run and every case where the grader and the checker disagree.

## 5. After v1

- **Re-run:** on every change to rules, prompts, or the facts table.
- **Facts refresh:** each November when the IRS announces the next year's limits. Until the new year is added, answers citing it go to REVIEW, which is the intended behavior.

## 6. Changelog

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-26 | Initial 43 cases and thresholds | — | pending |
