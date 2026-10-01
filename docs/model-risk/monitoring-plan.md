# Ongoing monitoring plan

SR 26-2 §V: monitoring checks "the extent to which a model is performing as intended" after approval. The metrics and triggers below are for the **shadow-mode deployment** approved in the [validation report](validation-report.md). Numbers marked *(PRD)* come from the [PRD](../../PRD.md). Numbers marked *(proposed)* are new here and need the product owner's sign-off.

## Metrics and triggers

| Metric | How it's measured | Threshold | If breached |
|---|---|---|---|
| **Wrong fact marked SEND** | A reviewer finds a wrong fact in an answer the checker passed | **Any one** *(PRD)* | Roll back to all-REVIEW (kill switch), root-cause it, add a regression case. In shadow mode it also counts against the [exit rule](../../PRD.md#8-rollout-for-a-real-deployment-this-repo-is-a-reference-build), and adding the regression case changes the checker, which starts a new run |
| Advice-boundary recall | Share of advice cases caught in shadow mode, compared with reviewer decisions | ≥ 95% over a week *(PRD)* | Roll back; re-validate RAC-3 |
| Reviewer burden | Share of clean answers sent to REVIEW | ≤ 20% *(PRD)* | Investigate; not a rollback (this is the safe direction) |
| `unknown_fact` rate | Share of answers with an unknown fact, by week | Doubles week over week *(proposed)* | Check whether facts are stale or traffic has shifted to new topics |
| Judge disagreement | Repeat a 5% sample of judge calls; share whose decision flips | > 5% *(proposed)* | Freeze judge changes; re-run evals ([F-6](validation-report.md#findings)) |
| Reviewer check catch rate | Known-answer checks in the review queue (including bad answers with no flag) | < 90% caught *(proposed)* | Retrain reviewers; audit their recent decisions (automation bias) |
| Model version | The vendor model ID recorded on every judge call | Any change | Re-run all eval sets before continuing ([F-7](validation-report.md#findings)) |

## Scheduled reviews

| When | What | How |
|---|---|---|
| **Each November** | New IRS limits: update `facts.json` (two-person check), add the year, re-run tests | A [scheduled routine](https://claude.ai/code/routines/trig_01CsB3WhNJVApzaajKBfiy3w) opens a GitHub issue when the IRS publishes the figures |
| **Each quarter** *(proposed)* | Outcomes analysis: run the frozen RetireBench questions against the major assistants, and run the checker on their answers | [`bench/`](../../bench/README.md) |
| Every change to rules, prompts or facts | All eval sets plus the release gate | CI runs the deterministic layer and [mcp-trust-check](../trust-check.md) on every push; judge evals are run by hand |
| Every release | Build the package and install it outside the repo | CI `package` job ([F-10](validation-report.md#findings)) |

## Change control

A change to rules, judge prompts, thresholds or eval cases is logged in the [eval plan changelog](../../EVAL_PLAN.md#8-changelog) with the date, the reason and who approved it. Frozen eval sets (`retirebench-v1`) are never edited. A new version gets a new tag.
