---
name: llm-council
description: >-
  Run a structured LLM Council debate (5 personas + Judge) on architecture,
  design decisions, tech choices, papers, or red-team plans. Triggers: "council",
  "debate", "red team", "pressure-test", "ADR", "which should we use".
  Outputs markdown debate, optional ADR snippet, and self-contained HTML under
  llm-council-output/. Use code-aware mode when the topic references a repo path.
---

# LLM Council

Run a structured, adversarial debate among expert personas to pressure-test a topic and produce a decisive, actionable recommendation.

## Trigger phrases

**What:** A 4-round council debate (5 personas + Judge) with blind peer rating, a committed final verdict, optional ADR snippet, and self-contained HTML under `llm-council-output/`.

**When to invoke** — user message includes any of:
- `council`, `LLM Council`, `/llm-council`
- `debate`, `pressure-test`, `red team`, `red-team`
- `ADR`, `architecture decision`, `which should we use`, `X vs Y`
- A repo path or "this codebase" with a design or technology question

If optional inputs are missing, proceed with defaults — do not block on context or criteria.

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

- **Security council** — when the topic is auth, data handling, threat modeling, or the user asks for a "security council," swap **Product / User Advocate → Security Engineer**: evaluates attack surface, trust boundaries, authn/authz, data exposure, and abuse/misuse cases; names concrete threats and their blast radius.


## Code-aware mode

If the topic points at a repo, path, file, or "this codebase," ground the debate in what the code actually is **before** Round 1:

1. **Read relevant files first** — start with the `README`, then entrypoints (`main`/`cli`/`app`/server bootstrap), core modules, and tests. Tests reveal intended behavior; the README reveals intended scope. Read enough to know what exists and what doesn't — don't guess.
2. **Record findings under Context** — state concretely **what exists** (architecture, persistence, scale, dependencies) and **what doesn't** (no DB, no service layer, no queue, etc.). Cite files/functions where useful.
3. **Let personas attack the premise** — a valid position is "this is the wrong question for this codebase." If the topic assumes infrastructure or scale the repo doesn't have, surface that the literal question and its premise are two different debates, and address both.

This keeps every run grounded in the real code instead of an imagined version of it.

## Procedure

1. **Naive baseline** — Before any code reading or debate, produce a short **Naive Single-Model Take**: the answer a single, one-shot LLM would give the *bare* question with no codebase grounding and no adversarial pressure. Keep it to 2–4 sentences in the agreeable/hedgy register such answers genuinely have (generic best-practice, "it depends"), then add one line naming why it's insufficient *here* — ungrounded in the real code, hedges instead of committing, surfaces no concrete tradeoff or failure mode. This is a fair control shown for contrast, **not** a strawman; write the real one-shot answer, never a deliberately weak one.
2. **Setup** — Restate the topic and context. **If the topic references a repo/path, do Code-aware mode first** and fold its findings into Context. If criteria weren't provided, infer 2–4 decision criteria and state them explicitly. If the topic is underspecified, make reasonable assumptions and list them under Context.
3. **Round 1 — Opening Positions** — Each debater (personas 1–5) states a concrete position. No fence-sitting; each must take a stance.
4. **Peer Rating (anonymized)** — After Round 1, strip the author labels from the five opening positions and re-label them `Position A`–`Position E` in shuffled order. Each persona then scores the *other* positions blind (they skip their own, marked `—`), so ratings reflect argument quality, not reputation. Use a 1–10 composite (analytical **rigor** + **usefulness**) with a one-line critique per cell. Report column averages, a ranking, then reveal the Position → persona mapping. See the rubric for scoring guidance.
5. **Round 2 — Challenges** — Each debater challenges at least one other persona by name with a specific, technical objection. Do not let personas converge yet.
6. **Round 3 — Rebuttals** — Each debater defends or updates their position in response to the challenges. Updating a position is encouraged when an argument lands — say what changed and why.
7. **Final Verdict** — The Judge synthesizes and fills every field of the verdict template.
8. **Render HTML** — After the Markdown debate is complete, always render it to a self-contained HTML page under `llm-council-output/` (see **HTML rendering** below). This is automatic, not opt-in.

**Per-round verdict:** In every round (1, 2, 3), end each persona's turn with a one-line **Verdict:** capturing their crisp current stance for that round. This makes each persona's position trackable as it evolves across rounds.

Apply the rubric in `references/debate-framework.md` throughout.

## Output format

```markdown
# LLM Council Debate

## Topic
<topic>

## Naive Single-Model Take
> _What a single one-shot model says before the council convenes — shown as a baseline, not an endorsement._

<2–4 sentence agreeable/hedgy ungrounded answer>

**Why this is risky:** <one line — ungrounded, hedges, names no concrete tradeoff or failure mode>

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

## ADR snippet
- **Status:** proposed
- **Decision:** <the committed recommendation, one line>
- **Consequences:** <what this buys, what it costs, and what is now harder>
```

The **ADR snippet** is an optional final section that maps the verdict to the format teams use to record architecture decisions, so the output can be pasted straight into a decision log. Include it by default for architecture/design topics; omit it for purely conceptual debates.

## HTML rendering

**When.** Always. After emitting the Markdown debate, render it to a self-contained HTML page as the final step of every run — no need for the user to ask. (The Markdown above is still produced in full; the HTML is an additional artifact, not a replacement.) After writing the file, tell the user its path.

**How.** Produce a single **self-contained** `.html` file under `llm-council-output/` (named after the topic, e.g. `kafka-vs-rabbitmq.html`). Inline `assets/council-style.css` into a `<style>` block in `<head>`, and inline `assets/council.js` into a `<script>` block just before `</body>`. No external `<link>` or `<script src>` — the file must open offline as one shareable artifact. Use `llm-council-output/kafka-vs-rabbitmq.html` as the reference layout.

**Class / data contract.** The generated markup must emit these classes and attributes so the stylesheet and script light up:

- **Naive baseline** — render the Naive Single-Model Take as a `.naive` callout placed directly after the hero, before the Topic section, containing a `.naive-label` ("Single-model baseline — no council") and a `.naive-risk` line for the "why this is risky" note. This is the deliberate visual "before" that contrasts with the `.verdict`/`.bottom` "after".
- **Personas** — color each persona with `.p1`–`.p5` (1 First-Principles, 2 Research, 3 Systems, 4 Skeptic, 5 Product) and prefix every persona name with an `.avatar` glyph: 🧱 First-Principles · 🔬 Research · ⚙️ Systems · 🚩 Skeptic · 👤 Product · ⚖️ Judge.
- **Turns** — wrap each persona turn in `.turn`; render its `Verdict:` line as a `.pverdict`.
- **Convergence grid** — an `.evo` grid (rows = personas, cols = R1/R2/R3 + a final-stance label). Each round cell is a `.chip[data-stance="..."]` where the stance value is one of the topic's own option buckets (e.g. for "Postgres vs Redis" use `postgres|redis|neither|undecided`; for "Kafka vs RabbitMQ" use `kafka|rabbit|neither|undecided`). Add a `↻` `.chg` marker on a cell whose stance bucket differs from that persona's prior round, and add a matching `.chip[data-stance="..."]` color rule in the inlined `<style>` for each bucket you use.
- **Peer-rating heatmap** — give each scored `.rate-table` cell `td[data-score="N"]` (the stylesheet tints 8–10 green, 6–7 amber, ≤5 red); mark own-position cells `td.self`.
- **Ranking bars** — inside each `.rank` `<li>`, add a `.bar` with `style="--score:N"` (width = score/10) and the revealed persona's `.p1`–`.p5` class; add `.glow` to the top scorer(s).
- **Confidence gauge** — render `.gauge[data-confidence="N"]` (N = 0–100) next to the verdict's Confidence row, containing a `.val` span; the script animates the arc from 0 to N on scroll.

**Convergence grid rule.** Classify each persona's per-round `Verdict:` line into one stance bucket drawn from the topic's actual options (plus `neither` / `undecided` as catch-alls), and place a `↻` marker wherever the bucket changes from the prior round. This is what makes the visual tell the convergence story — start mixed, collapse toward consensus — so do the classification from the actual verdicts, not by guessing.

## Rules

- The Naive Single-Model Take is a fair baseline, not a strawman: write the genuine one-shot answer, then state in one line why it's insufficient (ungrounded, hedged, no committed tradeoff). Never fabricate a deliberately bad answer to flatter the council.
- Keep the debate technical and useful — every claim should be falsifiable or actionable.
- Do not let personas agree too early; manufacture genuine disagreement in Rounds 1–2.
- Avoid generic pros/cons lists. Force concrete, named tradeoffs (this vs. that, with the cost of each).
- Personas address each other by name in Round 2.
- Peer rating is **blind**: anonymize and shuffle positions before scoring, and never let a persona rate their own. Scores must be justified by a one-line critique, not vibes.
- Every persona turn in Rounds 1–3 ends with a one-line **Verdict:** stance, so positions are trackable as they evolve.
- Prefer actionable recommendations over hedged summaries. The Judge must commit to a recommendation, even if conditional ("Do X unless Y, in which case Z").
- If the topic is underspecified, make reasonable assumptions and state them rather than asking endless questions.
- Match verbosity to the requested output depth.
