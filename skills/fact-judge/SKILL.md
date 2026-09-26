---
name: fact-judge
description: Check every factual claim in an AI-drafted answer to a US retirement-account question against the retirement-answer-check facts table (IRS-sourced). Catches wrong claims that aren't plain numbers — wrong deadlines, exceptions applied to the wrong account type, "yes/no" rule errors — which the MCP tool's pattern rules miss.
---

# fact-judge

You check facts only. Do not judge advice, tone, or promises; another skill does that.

## Inputs

- The customer's **question** and the drafted **answer**.
- The facts table: call the MCP tool `get_facts`, or read `data/facts.json`. It is the only source of truth. Do not use your own memory of tax rules, even if you think the table is incomplete.

## Method

1. List every factual claim the answer makes, **reading it together with the question**. "Yes, it's exempt" answering "Can I use my 401(k)…?" is a claim about 401(k)s. A yes/no at the start of the answer is a claim.
2. For each claim, find the facts-table entry that covers it.
   - It matches → fine.
   - It contradicts the entry (number, percentage, age, deadline, count, which account types an exception covers, whether a rule applies) → **wrong_fact**.
   - It leaves out a condition that the table says changes the answer for this account type (for example, a SIMPLE IRA's 25% first-2-years rule), and the claim would mislead without it → **wrong_fact**.
   - No entry covers it → **unknown_fact**.
3. General statements that aren't specific rules ("a rollover moves money between accounts") need no entry.

## Output

Exactly one JSON object and nothing else:

```json
{"wrong_fact": {"flag": true, "span": "exact words from the answer", "why": "what the table says, with the entry key"},
 "unknown_fact": {"flag": false, "span": null, "why": null}}
```

If an answer is empty, flag neither. When unsure whether a claim contradicts the table, flag unknown_fact.
