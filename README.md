# retirement-answer-check

Checks an AI assistant's draft answer to a US retirement-account question **before it reaches a customer**, and returns **SEND** or **REVIEW** with an IRS or FINRA source for every flag.

It is a checker, not an advisor. It never writes answers and never gives financial advice.

> Reference build by an AI product manager: [PRD](PRD.md) → [eval plan](EVAL_PLAN.md) → build → blind evals → release gate. Not affiliated with any financial firm; public IRS and FINRA sources only. Not financial or tax advice.

## What it flags

| Flag | Example it catches | Checked by |
|---|---|---|
| `wrong_fact` | "The 2026 IRA limit is $7,000" (that's 2025) · "the age-55 exception covers IRAs" · "up to two IRA rollovers a year" | Pattern rules against [`data/facts.json`](data/facts.json), then the **fact-judge** skill |
| `unknown_fact` | A 2027 limit, or any claim the facts table doesn't cover | Both layers. Unverified never means SEND |
| `personal_recommendation` | "Most people in your situation roll it over, so that's the right move for you" | Phrase rules, then the **advice-judge** skill |
| `promissory` | "Target-date funds return around 8% a year" · "you can't lose money" ([FINRA 2210(d)(1)](https://www.finra.org/rules-guidance/rulebooks/finra-rules/2210)) | Phrase rules, then the **advice-judge** skill |
| `out_of_scope` | Estate planning, insurance, Social Security, home-sale taxes | Rules |
| `empty_answer` | An empty draft | Rules |

Any flag → **REVIEW**. When a layer is unsure, it flags.

## How it works

1. **MCP server** (`check_answer`, `get_facts`). Fast, deterministic pattern rules for numbers, rules, scope, and obvious phrasing. Both tools are read-only and annotated that way.
2. **fact-judge skill.** A model reads the facts table and checks *every* claim, including ones that aren't numbers ("yes, that's exempt", "due by December 31").
3. **advice-judge skill.** A model judges the advice boundary and promissory language.

Every number in `facts.json` was read from the cited IRS page on 2026-09-26: [2026 limits](https://www.irs.gov/newsroom/401k-limit-increases-to-24500-for-2026-ira-limit-increases-to-7500), [IRA limits](https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-ira-contribution-limits), [RMDs](https://www.irs.gov/retirement-plans/retirement-plan-and-ira-required-minimum-distributions-faqs), [rollovers](https://www.irs.gov/retirement-plans/plan-participant-employee/rollovers-of-retirement-plan-and-ira-distributions), [early distributions](https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-tax-on-early-distributions).

## Results

Thresholds were [set before the first run](EVAL_PLAN.md). Two of the three case sets were written by separate agents that never saw the checker's rules or the other cases. Each held-out set was committed before it was run.

**Pattern rules alone, first run on each blind set:**

| Set | Pass | Wrong facts marked SEND |
|---|---|---|
| Held-out 1 (20 cases) | 14/20 | **1 of 5** |
| Held-out 2 (20 cases) | 15/20 | **4 of 10** |

That fails the top-harm gate. The misses were claims that aren't numbers ("exempt", "by December 31", "up to two"), or the account type appearing only in the question. Adding patterns for each miss would just fit the test set, so the fix was a second layer.

**Full system (rules + fact-judge + advice-judge), each judge run blind 3 times:**

| Gate | Result | Threshold |
|---|---|---|
| Wrong facts marked SEND | **0 of 25** (all 3 runs caught every one) | 0 |
| Personal recommendations caught | 9 of 9 | ≥ 95% |
| Promissory claims caught | 6 of 6 | ≥ 95% |
| Out of scope → REVIEW | 4 of 4 | all |
| Unknown facts → REVIEW | 2 of 2 | all |
| Empty draft → REVIEW | 1 of 1 | all |
| Clean answers sent to REVIEW | 2 of 36 (5.6%) | ≤ 20% |
| Release gate ([mcp-trust-check](https://github.com/vishalhabib99/mcp-trust-check)) | **SHIP**, 100% (A): 0 crashes, 0 reality flags, security A ([report](docs/trust-check.md)) | SHIP |

The 2 false REVIEWs were true statements the facts table doesn't cover (beneficiary RMD rules; Roth vs. traditional tax treatment). The fact judge flagged them as `unknown_fact`, as its spec says it should.

**Limits of these results:**
- 83 synthetic cases. Real traffic is messier, and a real deployment should start in shadow mode ([PRD §8](PRD.md#8-rollout-for-a-real-deployment-this-repo-is-a-reference-build)).
- The judges and the case writers are all Claude, so they may share blind spots.
- The advice judge wasn't run on held-out set 2, which has only fact cases, so its false-flag rate there wasn't measured.
- The facts table covers 2025 and 2026. It needs an update each November when the IRS publishes new limits. Until then, answers citing the new year go to REVIEW.

Raw outputs: [`evals/`](evals/) (cases, first-run logs, all judge runs).

## Use it in Claude Code

```bash
claude mcp add retirement-answer-check -- uvx --from git+https://github.com/vishalhabib99/retirement-answer-check retirement-answer-check
cp -r skills/fact-judge skills/advice-judge ~/.claude/skills/
```

Then: *"Check this draft answer: …"*. Claude calls `check_answer`, then runs both skills. Any flag means REVIEW.

Deterministic layer from Python:

```python
from retirement_answer_check import check
check("What's the IRA limit for 2026?", "It's $7,000.")
# {'decision': 'REVIEW', 'flags': [{'type': 'wrong_fact', 'span': '$7,000',
#   'reason': 'not a 2026 ira limit (that is the 2025 figure)', 'source': 'https://www.irs.gov/...'}]}
```

Run the evals: `python evals/run.py evals/heldout2.jsonl evals/judge/all_layers.json`

## License

MIT
