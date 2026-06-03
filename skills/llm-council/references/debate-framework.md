# Debate Framework & Rubric

The rubric the LLM Council applies to keep debates technical, adversarial, and decisive.

## Core principles

1. **Steelman, then attack.** Engage the strongest version of an opposing position, never a strawman. A challenge that only beats a weak reading is wasted.
2. **Falsifiable or actionable.** Every claim should either be checkable (evidence, measurement, benchmark) or lead to an action. Drop claims that are neither.
3. **Named tradeoffs, not pros/cons.** State the tradeoff as "X buys us A at the cost of B." Generic "it's more scalable" is banned; say scalable in which dimension, measured how, at what cost.
4. **Disagreement is the product.** If everyone agrees in Round 1, the debate failed. Surface the real axis of disagreement before converging.
5. **Commit.** The Judge must land on a recommendation, conditional if necessary. "It depends" is only acceptable when paired with the deciding variable.

## Per-round expectations

### Naive Single-Model Take — the baseline (before Round 1)
- Produce the answer a single one-shot model gives the *bare* question: no codebase grounding, no debate, no adversarial pressure. 2–4 sentences.
- Write it in the register such answers genuinely have — agreeable, hedgy, generic best-practice, often "it depends." This is a **fair control**, not a strawman; do not fabricate a deliberately weak answer.
- End with one line naming why it's insufficient *here*: ungrounded in the real code, hedges instead of committing, surfaces no concrete tradeoff or failure mode.
- Purpose: make the council's grounded, adversarial, committed verdict legible by contrast — it shows what the structure adds over a one-shot answer.

### Round 1 — Opening Positions
- Each debater takes a clear stance, not a survey of options.
- Ground the stance in the persona's lens (mechanism, theory, systems, risk, user value).
- State the single most important reason for the stance.

### Peer Rating (Anonymized) — between Round 1 and Round 2
- Strip author labels from the five opening positions; re-label `Position A`–`Position E` in shuffled order.
- Each persona scores the *other* four positions (own = `—`) on a 1–10 composite:
  - **Rigor** — is the reasoning sound, mechanism-grounded, and free of unstated leaps?
  - **Usefulness** — does it move the decision forward with something actionable?
- Every score gets a one-line critique. Anchor the scale: 9–10 decisive and well-supported; 7–8 strong with a gap; 5–6 reasonable but assumes too much or isn't actionable; ≤4 weak or pattern-matched.
- Report per-position column averages, rank them, then reveal the Position → persona mapping. The ranking should foreshadow (not pre-empt) the Judge's "best argument" call.

### Per-round verdict
- End each persona's turn in Rounds 1–3 with a one-line **Verdict:** — their crisp current stance.
- The verdict should visibly shift when a challenge lands; if it doesn't change, that's a deliberate "holding" signal.

### Round 2 — Challenges
- Address at least one other persona **by name**.
- The objection must be specific: a failure mode, a missing assumption, a cost the other ignored, or contradicting evidence.
- No agreeing in this round. If you mostly agree, find the seam where you don't.

### Round 3 — Rebuttals
- Respond to the challenge directly.
- Updating your position is a strength: say what the challenge changed and what survived.
- Defending unchanged: explain why the objection doesn't bite.

### Final Verdict — Judge
Fill every field:
- **Best argument** — the single most decisive point made, and by whom.
- **Biggest risk** — the failure mode most likely to matter, with trigger conditions.
- **Key tradeoff** — the central X-vs-Y the decision turns on.
- **Consensus** — what all/most personas actually agreed on (may be narrow).
- **Recommendation** — a committed call; conditional form allowed ("Do X unless Y, then Z").
- **Confidence level** — low / medium / high, with a one-line reason tied to evidence quality.
- **Next 3 actions** — concrete, ordered, each doable by a person this week.

## Calibrating confidence

- **High** — strong evidence or well-understood mechanism; low downside if wrong; reversible.
- **Medium** — reasonable evidence with notable gaps, or meaningful but bounded downside.
- **Low** — thin evidence, high uncertainty, or large/irreversible downside. Pair with what would raise confidence.

## Output depth

- **quick** — 1–2 sentences per persona per round; compressed verdict; skip examples.
- **standard** — 2–4 sentences per persona per round; full verdict.
- **deep** — full paragraphs; concrete numbers, examples, and references; full verdict with reasoning shown.

## Anti-patterns to avoid

- A Naive Single-Model Take written as a strawman (deliberately bad) rather than the genuine one-shot answer — it must be a fair baseline or the contrast is dishonest.
- Vague scale/perf claims with no dimension or number.
- Personas that all sound the same — each must argue from its lens.
- Premature consensus in Rounds 1–2.
- A verdict that restates the debate without choosing.
- Hedged recommendations with no deciding variable.
- Listing risks without trigger conditions or likelihood.

## Validation checklist (self-check before ending)

Before emitting the final output, confirm every box. A failed box means the run is incomplete — fix it before finishing.

- [ ] The Naive Single-Model Take is present (2–4 sentences, fair not strawman) with a one-line "why this is risky" note, before the council content.
- [ ] Peer rating table is present, with column averages, a ranking, **and** the Position → persona reveal.
- [ ] Every Round 1–3 turn ends with a `Verdict:` line.
- [ ] The Judge filled **all** Final Verdict fields (best argument, biggest risk, key tradeoff, consensus, recommendation, confidence, next 3 actions).
- [ ] The recommendation is committed; it is conditional **only** with an explicit "unless Y" deciding variable.
- [ ] No generic "more scalable" / "more reliable" claims without a named dimension and number.
- [ ] If the topic referenced a repo/path, Context states what exists and what doesn't.
- [ ] If an architecture/design topic, the ADR snippet is included.
