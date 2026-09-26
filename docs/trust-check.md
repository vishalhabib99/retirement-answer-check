# mcp-trust-check result

Run locally on 2026-09-26 against a clean `git archive` of the repo (what CI checks out), with the server started over stdio. Same checks as the [mcp-trust-check](https://github.com/vishalhabib99/mcp-trust-check) GitHub Action, which also runs in this repo's CI.

## mcp-trust-check — SHIP (HIGH confidence) · combined score: 100% (A)

### Release decision: ✅ SHIP

No rule fired.

**Confidence: HIGH** · needs human review: no
- mcp-fuzz called 2 of 2 tools (100%).

### mcp-doctor (static) — 100% (A)
```
mcp-doctor report
Quality:  100%  Grade: A  (2 tool(s) found)
Security: 100%  Grade: A

  [OK] check_answer (src/retirement_answer_check/server.py:14)
  [OK] get_facts (src/retirement_answer_check/server.py:36)


```

### mcp-fuzz (runtime crash resilience) — 100.0% (A)
```
mcp-fuzz: ~/code/retirement-answer-check/.venv/bin/retirement-answer-check

Crash resilience: 100% (A) — 0 crash(es), 0 timeout(s) across 4 bad-input calls
Tested 2 tool(s), skipped 0 (not read-only)
Latency: 100% (A) — 0 tool(s) flagged slow out of 2 checked (server median 2ms; single real call per tool, not a load test — see README)
Response size: 100% (A) — 0 tool(s) flagged bloated out of 2 checked (server median 2276 chars; single real call per tool, not representative of every possible input — see README)
Estimated token cost: ~1,137 tokens total across 2 tool(s) (~568 avg/call) — one call per tool, ~4 chars/token rule of thumb, not a real tokenizer — see README

  [ok] check_answer
  [ok] get_facts

```

### mcp-reality-check (runtime output fidelity) — 100.0% (A)
```
mcp-reality-check: ~/code/retirement-answer-check/.venv/bin/retirement-answer-check

Response sanity: 100% (A) — 0 flagged of 2 checkable response(s)
Tested 2 tool(s), skipped 0 (not read-only)

  [ok]  check_answer
  [ok]  get_facts

```
