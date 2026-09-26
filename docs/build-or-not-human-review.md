## Build or not: a measured human-review layer for retirement-answer-check

*Method: [/build-or-not](https://github.com/vishalhabib99/ai-pm-skills). Sections 1–3 were written and saved before any example was checked.*

**Proposal:** When the checker says REVIEW, give the reviewer a screen with each flag and its source, and **measure whether the review itself works**: whether reviewers catch errors or just approve.

**Narrowed to one checkable claim:** Widely used tools for human review of AI/LLM output do not document any built-in way to measure whether reviewers catch errors: no known-answer ("gold") items, no reviewer-accuracy metric, no agreement between reviewers.

**Precondition (the problem is real):** at least 2 published studies or official sources show people reviewing AI output miss its errors (automation bias). If fewer than 2, the decision is "don't build" regardless of the gap.

**Sample (chosen before checking):** 6 real, publicly documented human-review features, one or two per category:
1. Amazon Augmented AI (A2I), cloud platform
2. Label Studio, open-source labeling and review
3. LangSmith annotation queues, LLM observability
4. Langfuse annotation queues, open-source LLM observability
5. Arize Phoenix human annotations, open-source LLM observability
6. Braintrust human review, LLM eval platform

Selection rule: the best-known human-review features in each category that an AI team would actually pick up, named before any docs were read.

**Bar (set before checking):**
- **Hit** = the tool's official docs show **no** built-in reviewer-quality measurement (gold items, reviewer accuracy, or inter-reviewer agreement) for its review workflow. A feature that exists only in a paid tier still counts as present (not a hit).
- **Build** if the precondition holds **and** ≥ 4 of 6 are hits (the gap is common).
- **Narrow** if 2–3 are hits: the gap is partly filled, so look for what's still missing (for example, domain-sourced flags or catching rubber-stamping specifically).
- **Don't build** the measurement part if ≤ 1 is a hit: existing tools already cover it.
- **What would change my mind:** tools with gold items or reviewer-accuracy features for LLM review specifically.

---

## Results

*(filled in after checking)*
