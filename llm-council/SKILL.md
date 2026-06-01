---
name: llm-council
description: Turn one topic, idea, architecture, design decision, paper summary, or technical problem into a structured multi-agent debate. Multiple expert personas argue, challenge each other, refine positions, and a Judge produces a final synthesized recommendation. Use when the user wants a decision pressure-tested, tradeoffs surfaced, or a "council" / "debate" / "red team" view on a technical choice.
---

# LLM Council

Run a structured, adversarial debate among expert personas to pressure-test a topic and produce a decisive, actionable recommendation.

## When to use

Invoke when the user wants to:
- Evaluate an architecture, design decision, or technology choice.
- Stress-test an idea or proposal before committing.
- Get a balanced-but-decisive recommendation with explicit tradeoffs.
- Red-team a plan for failure modes and hidden costs.
- Summarize and critique a paper or approach from multiple angles.

## Inputs

Accept or ask for:

1. **Topic / question** (required) — what to debate.
2. **Context** (optional) — constraints, scale, stack, deadlines, prior decisions.
3. **Decision criteria** (optional) — what "good" means here (e.g., latency, cost, time-to-ship, maintainability). If none given, the council infers and states them.
4. **Output depth** (optional, default `standard`):
   - `quick` — 1–2 sentences per persona per round; compressed Final Verdict.
   - `standard` — 2–4 sentences per persona per round; full Final Verdict.
   - `deep` — full paragraphs, concrete examples/numbers, references where useful.

If the topic is missing, ask for it. If only the topic is given, proceed with the defaults above — do not block on optional fields.

## Personas

Five debaters plus one judge. The Judge stays silent until the Final Verdict.

1. **First-Principles Thinker** — decomposes the topic into fundamentals, avoids hype, explains the underlying mechanism and why it works (or doesn't).
2. **Research Scientist** — evaluates theoretical soundness, references known ML/AI/SWE concepts when relevant, identifies evidence gaps and what would need to be measured.
3. **Systems Engineer** — focuses on architecture, scalability, latency, reliability, cost, observability, and implementation complexity.
4. **Skeptic / Red Team** — challenges assumptions, surfaces failure modes, risks, hidden costs, and edge cases.
5. **Product / User Advocate** — evaluates user value, usability, adoption, and practical tradeoffs.
6. **Judge / Synthesizer** — does not debate in Rounds 1–3; summarizes the strongest arguments, resolves disagreements, and gives the final recommendation and next steps.

## Procedure

1. **Setup** — Restate the topic and context. If criteria weren't provided, infer 2–4 decision criteria and state them explicitly. If the topic is underspecified, make reasonable assumptions and list them under Context.
2. **Round 1 — Opening Positions** — Each debater (personas 1–5) states a concrete position. No fence-sitting; each must take a stance.
3. **Peer Rating (anonymized)** — After Round 1, strip the author labels from the five opening positions and re-label them `Position A`–`Position E` in shuffled order. Each persona then scores the *other* positions blind (they skip their own, marked `—`), so ratings reflect argument quality, not reputation. Use a 1–10 composite (analytical **rigor** + **usefulness**) with a one-line critique per cell. Report column averages, a ranking, then reveal the Position → persona mapping. See the rubric for scoring guidance.
4. **Round 2 — Challenges** — Each debater challenges at least one other persona by name with a specific, technical objection. Do not let personas converge yet.
5. **Round 3 — Rebuttals** — Each debater defends or updates their position in response to the challenges. Updating a position is encouraged when an argument lands — say what changed and why.
6. **Final Verdict** — The Judge synthesizes and fills every field of the verdict template.

**Per-round verdict:** In every round (1, 2, 3), end each persona's turn with a one-line **Verdict:** capturing their crisp current stance for that round. This makes each persona's position trackable as it evolves across rounds.

Apply the rubric in `references/debate-framework.md` throughout.

## Output format

```markdown
# LLM Council Debate

## Topic
<topic>

## Context
<context, inferred criteria, and any stated assumptions>

## Round 1: Opening Positions
**First-Principles Thinker:** ...
_Verdict: <one-line stance>_
**Research Scientist:** ...
_Verdict: <one-line stance>_
**Systems Engineer:** ...
_Verdict: <one-line stance>_
**Skeptic / Red Team:** ...
_Verdict: <one-line stance>_
**Product / User Advocate:** ...
_Verdict: <one-line stance>_

## Peer Rating (Anonymized)
Positions A–E (shuffled, authors hidden) scored 1–10 by each persona (own = —):

| Rater \ Position | A | B | C | D | E |
|---|---|---|---|---|---|
| <persona> | n | n | — | n | n |
| ... | | | | | |
| **Average** | | | | | |

**Ranking:** 1) Position X … 2) … **Reveal:** A = <persona>, B = <persona>, …

## Round 2: Challenges
**First-Principles Thinker → <persona>:** ...
_Verdict: <one-line stance>_
**Research Scientist → <persona>:** ...
_Verdict: <one-line stance>_
**Systems Engineer → <persona>:** ...
_Verdict: <one-line stance>_
**Skeptic / Red Team → <persona>:** ...
_Verdict: <one-line stance>_
**Product / User Advocate → <persona>:** ...
_Verdict: <one-line stance>_

## Round 3: Rebuttals
**First-Principles Thinker:** ...
_Verdict: <one-line stance>_
**Research Scientist:** ...
_Verdict: <one-line stance>_
**Systems Engineer:** ...
_Verdict: <one-line stance>_
**Skeptic / Red Team:** ...
_Verdict: <one-line stance>_
**Product / User Advocate:** ...
_Verdict: <one-line stance>_

## Final Verdict
- **Best argument:** ...
- **Biggest risk:** ...
- **Key tradeoff:** ...
- **Consensus:** ...
- **Recommendation:** ...
- **Confidence level:** <low | medium | high> — <one-line why>
- **Next 3 actions:**
  1. ...
  2. ...
  3. ...
```

## Rules

- Keep the debate technical and useful — every claim should be falsifiable or actionable.
- Do not let personas agree too early; manufacture genuine disagreement in Rounds 1–2.
- Avoid generic pros/cons lists. Force concrete, named tradeoffs (this vs. that, with the cost of each).
- Personas address each other by name in Round 2.
- Peer rating is **blind**: anonymize and shuffle positions before scoring, and never let a persona rate their own. Scores must be justified by a one-line critique, not vibes.
- Every persona turn in Rounds 1–3 ends with a one-line **Verdict:** stance, so positions are trackable as they evolve.
- Prefer actionable recommendations over hedged summaries. The Judge must commit to a recommendation, even if conditional ("Do X unless Y, in which case Z").
- If the topic is underspecified, make reasonable assumptions and state them rather than asking endless questions.
- Match verbosity to the requested output depth.
