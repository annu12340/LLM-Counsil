# LLM Council

**LLM Council** is an AI ADR/RFC decision council for engineering teams. It turns an architecture question, design proposal, or repo-grounded technical tradeoff into a structured adversarial review, then forces a committed verdict your team can paste into an ADR, RFC, PR, or design doc.

It replaces the usual "here are some pros and cons" LLM answer with a fixed council protocol: opening stances, blind peer rating, named challenges, rebuttals, and a Judge who must commit to a recommendation with confidence, risks, tradeoffs, and three concrete next actions.

Output: **full Markdown debate**, **ADR snippet**, validated council JSON, and an **offline HTML artifact** under [`llm-council-output/`](llm-council-output/) you can drop into a PR, Slack, or wiki.

Impact target: turn a 60–90 minute ADR/RFC prep loop into a 5–10 minute council run + edit pass — roughly **80–90% less decision-artifact prep time** — while replacing one unchallenged model answer with a **22-call, 6-seat review protocol**.

**Landing page:** open [`index.html`](index.html) in a browser

## Who is this for?

| Role | Example use |
|------|-------------|
| **Staff / senior engineers** | Pressure-test an ADR before it becomes the team default |
| **Tech leads** | Turn "Kafka or RabbitMQ?" / "Postgres or Redis?" into an auditable recommendation |
| **Engineering managers** | Attach the HTML artifact to an RFC so tradeoffs and objections are visible |
| **Platform teams** | Review migrations, infrastructure bets, and operational risk with a repeatable protocol |
| **Maintainers** | Run code-aware reviews that cite real modules, tests, and missing boundaries |

You don't need Cursor or Claude Code. If you have an `ANTHROPIC_API_KEY`, you can run a debate from the terminal in two commands.

## Impact numbers

| Metric | Number | Why it matters |
|--------|--------|----------------|
| **ADR/RFC prep time reduction** | **80–90% target** | Replace a 60–90 min manual draft/review prep loop with a 5–10 min council artifact plus human edit pass |
| **Agentic review coverage** | **22 model calls** | 1 naive baseline + 5 openings + 5 blind peer ratings + 5 challenges + 5 rebuttals + 1 Judge |
| **Decision lenses per run** | **5 expert perspectives** | Fundamentals, evidence, systems/ops, red-team risk, and user/product impact |
| **Judge-gating discipline** | **100% tested** | The Judge is not called until Round 4; `tests/test_run_agents.py` asserts the final call is the only Judge call |
| **Artifact validation coverage** | **100% of committed examples** | `validate-artifacts` checks every example JSON and every committed HTML artifact |
| **Shareability overhead** | **0 external runtime deps** | Generated HTML inlines CSS/JS and opens offline in a browser |
| **Decision output density** | **3 reusable artifacts** | Markdown debate, ADR snippet, and offline HTML record from the same validated JSON |

## Quick start

### Option A — Cursor / Claude Code agent skill

Install the skill into your agent environment, then invoke it with natural language:

```bash
./scripts/install-skills.sh              # Cursor (personal)
./scripts/install-skills.sh --target claude   # Claude Code
```

Start a **new session**, then type any trigger phrase:

```text
LLM Council: Should we use Kafka or RabbitMQ for ~10k events/sec? Small ops team; need replay.
```

The skill auto-invokes on: `council`, `debate`, `pressure-test`, `red team`, `ADR`, `which should we use`, `X vs Y`, or a repo path + design question.

See [Install](#install) for scoped/symlink options, and [Trigger phrases](#trigger-phrases) for the full list.

### Option B — Python CLI (no agent required)

Don't have Cursor or Claude Code? Run a debate directly from the terminal:

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...

python3 scripts/run_agents.py --topic "ADR: Kafka vs RabbitMQ for event ingestion" --context "10k events/sec, small ops team"
python3 scripts/run_agents.py --topic "RFC: split the billing service or keep it in the monolith?" --output debate.md
python3 scripts/run_agents.py --topic "ADR: Postgres or Redis for short-link persistence?" --json-output debate.json
```

`run_agents.py` loads `skills/llm-council/agents/agents.yaml`, makes one model call per configured participant per round, keeps the Judge gated until Round 4, then renders Markdown and self-contained HTML from validated council JSON. `run_debate.py` remains as a single-call compatibility runner for cheaper/faster demos. The default model is `claude-opus-4-8`, overrideable with `--model` or `LLM_COUNCIL_MODEL`.

| Flag | Default | Notes |
|------|---------|-------|
| `--topic` | required | The ADR/RFC question or engineering decision to debate |
| `--context` | — | Repo notes, constraints, stack, scale, deadlines (optional) |
| `--depth` | `standard` | `quick` / `standard` / `deep` |
| `--output` | stdout | Write markdown to a file |
| `--html-output` | `llm-council-output/<title>.html` | Write the offline HTML artifact to a specific path |
| `--json-output` | — | Save the validated model JSON used to render both artifacts |
| `--trace-output` | — | `run_agents.py` only: save call order and transcript trace |
| `--model` | `LLM_COUNCIL_MODEL` or `claude-opus-4-8` | Anthropic model id |
| `--max-tokens` | `LLM_COUNCIL_MAX_TOKENS` or `16000` | Response budget |

## Prove the tooling locally (no API key needed)

The HTML renderer and validator run entirely offline against a pre-built example:

```bash
./scripts/run-demo.sh
```

That command validates the structured debate input, renders the HTML artifact, validates the HTML contract, and runs the unit tests — no API key required. Individual steps:

```bash
python3 scripts/council_tool.py validate-input examples/sequential-vs-random-codes.json
python3 scripts/council_tool.py render examples/sequential-vs-random-codes.json --output llm-council-output/sequential-vs-random-codes.html
python3 scripts/council_tool.py validate-html llm-council-output/sequential-vs-random-codes.html
python3 scripts/council_tool.py validate-artifacts
python3 -m unittest
```

## Key highlights

- **Executable agents.yaml runner** — `scripts/run_agents.py` runs a **22-call council** and only calls the Judge in Round 4.
- **6-role debate engine** — 5 specialist debaters + a silent Judge, run as a fixed **4-round protocol** (Opening → blind Peer Rating → Challenges → Rebuttals → Verdict), preceded by a **Round 0 naive baseline** that captures the answer a single one-shot model would give, as an honest before/after contrast.
- **Blind peer rating** — Round 1 positions are stripped of authorship, shuffled to `A`–`E`, and scored **1–10** (rigor + usefulness) by every *other* persona. Ratings reflect argument quality, not reputation — no persona scores itself.
- **Code-aware grounding** — when the topic names a repo or path, the agent reads `README` → entrypoints → core modules → tests *before* Round 1, so personas can attack the **premise** ("wrong question for this codebase"), not an imagined system.
- **Deterministic output contract** — a fixed Markdown template **and** a precise HTML class/`data-*` schema both live in `SKILL.md`, so every run is structurally identical and machine-checkable; committed examples are covered by **100% artifact validation**.
- **Self-contained HTML artifact** — each debate renders to one offline `.html` (inlined CSS/JS, **0 external runtime deps**) with a convergence grid, peer-rating heatmap, ranking bars, and a scroll-animated confidence gauge. Shareable straight into a PR, Slack, or wiki.
- **Decision-log ready** — architecture topics emit an **ADR snippet** (Status / Decision / Consequences) that pastes directly into a decision record.
- **Zero runtime dependencies** — no server, no API keys in the skill, no build step. The whole procedure runs inside the agent session.
- **Portable** — [`agents/agents.yaml`](skills/llm-council/agents/agents.yaml) mirrors the same roster, flow, temperatures, and validation checklist for OpenAI-style multi-agent runners.


## Trigger phrases

The skill auto-invokes when the user message includes any of:

| Trigger | Examples |
|---------|----------|
| Council | `council`, `LLM Council`, `/llm-council` |
| Debate / red team | `debate`, `pressure-test`, `red team`, `red-team` |
| Decisions | `ADR`, `architecture decision`, `which should we use`, `Kafka vs RabbitMQ` |
| Code-aware | A repo path or “this codebase” with a design or technology question |

Optional context and criteria can be omitted—the skill infers defaults and proceeds.

## What’s in this repo

| Path | Purpose |
|------|---------|
| [`skills/`](skills/) | **Skill packages** (source of truth) — install with [`scripts/install-skills.sh`](scripts/install-skills.sh) |
| [`skills/llm-council/`](skills/llm-council/) | Council debate skill — rubric, architecture reference, HTML assets, multi-agent config (agents.yaml) |
| [`url-shortener-fixture/`](url-shortener-fixture/) | **Code-aware fixture** — minimal URL shortener to debate against real code |
| [`llm-council-output/`](llm-council-output/) | **Example debates** — self-contained HTML (offline-shareable) |
| [`examples/`](examples/) | **Runnable structured council inputs** |
| [`scripts/council_tool.py`](scripts/council_tool.py) | Real local Markdown/HTML renderer + validator for the output contract |
| [`scripts/run_agents.py`](scripts/run_agents.py) | Executable `agents.yaml` runner; one call per persona per round, Judge gated to Round 4 |
| [`scripts/run_debate.py`](scripts/run_debate.py) | Single-call compatibility runner via Anthropic API; validates model JSON and always renders HTML |
| [`scripts/run-demo.sh`](scripts/run-demo.sh) | One-command demo proof path |
| [`CLAUDE.md`](CLAUDE.md) | Authoring notes (sync, sandbox, test commands) |

## LLM Council at a glance

**Flow** (five debaters; Judge silent until the end):

1. **Opening Positions** — concrete stance per persona  
2. **Peer Rating (anonymized)** — blind 1–10 scoring of Round 1 arguments  
3. **Challenges** — named, technical objections  
4. **Rebuttals** — defend or update positions  
5. **Final Verdict** — recommendation, risks, tradeoffs, next 3 actions  

**Personas:** First-Principles Thinker, Research Scientist, Systems Engineer, Skeptic / Red Team, Product / User Advocate, Judge / Synthesizer. For security topics, swap Product Advocate for **Security Engineer** (see `SKILL.md`).

**Outputs:**

- Markdown debate (rounds, peer-rating table, verdict, optional ADR snippet)
- Self-contained HTML under `llm-council-output/` (inlined CSS/JS; convergence grid, peer heatmap, confidence gauge)

**Code-aware mode:** If the topic references a repo or path, the agent reads `README`, entrypoints, core modules, and tests *before* Round 1 so arguments match what the code actually does.

## Technical architecture

LLM Council is a **procedure-driven Agent Skill**, not a service. The agent (Cursor or Claude Code) loads `SKILL.md` at session start, matches trigger phrases, and executes a fixed multi-round protocol in a single session. Full detail lives in [`references/architecture.md`](skills/llm-council/references/architecture.md).

### Round contract

| Phase | Participants | Purpose |
|-------|--------------|---------|
| **0 — Naive baseline** | one-shot voice | Fair single-model answer *before* the debate; the contrast anchor |
| **Setup** | Agent | Restate topic; infer 2–4 criteria; fold code-aware findings into Context |
| **1 — Opening** | 5 debaters | Concrete stance per persona; each turn ends with a one-line `Verdict:` |
| **1.5 — Peer rating** | 5 debaters | Positions shuffled to `A`–`E`; blind 1–10 (rigor + usefulness), own = `—` |
| **2 — Challenges** | 5 debaters | Named, technical objections; no early convergence |
| **3 — Rebuttals** | 5 debaters | Defend or update; `↻` marks any stance-bucket change |
| **4 — Final verdict** | Judge only | Committed recommendation + confidence + next 3 actions |

The Judge is **gated to Round 4** — it never debates in Rounds 1–3. Every debater turn ends with a `Verdict:` line so stance can be classified per round.

### Persona model

Five debaters + one Judge. The roster stays at **five seats** — swaps substitute, never add. Temperatures are tuned per lens (`agents.yaml`): hotter for the Skeptic, cold for the Judge.

| Persona | Lens | Temp |
|---------|------|------|
| 🧱 First-Principles Thinker | Mechanism, fundamentals | 0.6 |
| 🔬 Research Scientist | Evidence, theory, measurement gaps | 0.7 |
| ⚙️ Systems Engineer | Scale, reliability, cost, ops | 0.6 |
| 🚩 Skeptic / Red Team | Failure modes, hidden costs | 0.8 |
| 👤 Product / User Advocate | User value, adoption | 0.7 |
| ⚖️ Judge / Synthesizer | Synthesis only (silent until R4) | 0.3 |

**Security council swap:** for auth, data-handling, or threat-model topics, Product / User Advocate is replaced by a **Security Engineer** (attack surface, trust boundaries, authn/authz, blast radius) via `persona_swaps` in `agents.yaml`.

### HTML class / `data-*` contract

The HTML artifact is generated to a strict schema so the inlined stylesheet and script light up deterministically. Stance buckets are **topic-derived** (e.g. `postgres|redis|neither|undecided`), not hard-coded in the assets.

| Element | Classes / attributes | Behavior |
|---------|---------------------|----------|
| Naive baseline | `.naive`, `.naive-label`, `.naive-risk` | "Before" callout after the hero |
| Personas | `.p1`–`.p5`, `.avatar` glyphs | Color + emoji per debater |
| Turns | `.turn`, `.pverdict` | Per-persona block + round verdict |
| Convergence grid | `.evo`, `.chip[data-stance=…]`, `.chg` | Stance grid; `↻` on bucket change |
| Peer heatmap | `.rate-table`, `td[data-score=N]`, `td.self` | Green 8–10, amber 6–7, red ≤5 |
| Ranking bars | `.rank`, `.bar[style="--score:N"]`, `.glow` | Bar width = score/10; glow on top scorer |
| Confidence gauge | `.gauge[data-confidence=N]`, `.val` | Arc animates 0→N on scroll |

Assets are small and bundle-only: [`council-style.css`](skills/llm-council/assets/council-style.css) (~296 lines) and [`council.js`](skills/llm-council/assets/council.js) (~43 lines, scroll-reveal + gauge) are **inlined** into each output — no external `<link>` or `<script src>` at render time.

### Design properties

| Property | Mechanism |
|----------|-----------|
| **Procedure, not vibes** | Numbered rounds; Judge gated to Round 4 |
| **Adversarial by default** | Manufactured disagreement in Rounds 1–2; blind peer rating |
| **Progressive disclosure** | Rubric in `references/`; assets loaded only at HTML render |
| **Deterministic outputs** | Markdown template + HTML schema fixed in `SKILL.md` |
| **Portable** | `agents.yaml` mirrors the flow for non-Cursor runners |
| **No runtime deps** | No server, no API keys in the skill — runs entirely in the agent |

## Why this is a strong Agent Skill

- **Procedure, not vibes** — numbered rounds; Judge only speaks in the final verdict  
- **Progressive disclosure** — rubric in [`references/debate-framework.md`](skills/llm-council/references/debate-framework.md); architecture in [`references/architecture.md`](skills/llm-council/references/architecture.md)  
- **Deterministic output contract** — markdown template + HTML class/`data-*` schema in `SKILL.md`  
- **Bundled assets** — `assets/council-style.css` and `assets/council.js` inlined into each HTML artifact  
- **Portable** — [`agents/agents.yaml`](skills/llm-council/agents/agents.yaml) mirrors the same roster and flow  

## Strengths

- **Decisive, not hedged.** The Judge must commit to a recommendation — even a conditional one ("Do X unless Y, then Z") — instead of returning a balanced-but-useless pros/cons list. Underspecified topics get stated assumptions, not endless clarifying questions.
- **Bias-resistant scoring.** Blind, shuffled peer rating with self-exclusion means a position earns its rank on rigor and usefulness, not on which persona authored it.
- **Honest baseline.** The Round 0 naive take is written as a genuine one-shot answer (agreeable, hedgy, ungrounded) and then critiqued — never a strawman — so the council's added value is visible, not assumed.
- **Grounded in real code.** Code-aware mode reads the actual repo first and lets personas reject the question's premise when the codebase doesn't match it. Debates cite real modules and tests, not an imagined system.
- **Single source of truth.** `SKILL.md` defines triggers, procedure, the Markdown template, and the HTML contract in one place; `references/` and `agents.yaml` are kept in sync with it.
- **Shareable evidence.** Output is a single offline HTML file that renders the whole debate — convergence story, peer heatmap, confidence — with no server, no build, and no network.
- **Low ceremony, fast adoption.** One install script, auto-triggering by `description`, and a code-aware fixture ([`url-shortener-fixture/`](url-shortener-fixture/)) to try it against immediately.

## Why this project wins

Most "ask the LLM" decision aids collapse to one of two failure modes: a single confident-but-ungrounded answer, or a wishy-washy pros/cons dump that pushes the decision back onto you. LLM Council beats both because it is **structured, adversarial, and committed**:

1. **It manufactures disagreement before consensus.** Five distinct lenses open with hard stances, then attack each other by name before anyone is allowed to converge. That surfaces failure modes and hidden costs a single pass never reaches.
2. **It scores arguments blind.** Anonymized, shuffled, self-excluded peer rating turns "who sounds confident" into "whose argument actually holds up" — a built-in quality signal you can read off the heatmap.
3. **It refuses to fence-sit.** Every persona commits each round; the Judge commits at the end with a confidence level and the next 3 concrete actions. You leave with a decision and an ADR snippet, not homework.
4. **It tells the truth about itself.** The naive baseline makes the council's marginal value explicit and contrastable, instead of asking you to take the elaborate output on faith.
5. **It's grounded, portable, and zero-dependency.** Code-aware reads keep debates honest to the real repo; the portable agents.yaml mirror makes the protocol portable; and the self-contained HTML means the result is shareable anywhere with nothing to install.

The result is a repeatable, auditable decision artifact — the same protocol, the same template, the same machine-checkable HTML schema on every run — that you can paste into a PR or a decision log and defend.

## Skill packages (`skills/`)

```
skills/
├── llm-council/
│   ├── SKILL.md
│   ├── agents/agents.yaml
│   ├── references/debate-framework.md
│   └── assets/
```

The `skills/` directory is **not** auto-loaded by agents. Install into a discovery path (below), then start a **new session**.

Keep `skills/llm-council/` files **in sync** when you change personas, rounds, or the HTML contract.

## Install

### Install script (recommended)

From the repo root:

```bash
./scripts/install-skills.sh
```

This installs **every** package under `skills/` using each skill’s `name:` from `SKILL.md` frontmatter.
| Option | Values | Default |
|--------|--------|---------|
| `--target` | `cursor`, `claude` | `cursor` |
| `--scope` | `personal`, `project` | `personal` |
| `--symlink` | link instead of copy | off |
| `--dry-run` | print only | off |

Examples:

```bash
# Cursor, all projects (personal)
./scripts/install-skills.sh

# Claude Code
./scripts/install-skills.sh --target claude

# This repo only (commit .cursor/skills for teammates)
./scripts/install-skills.sh --scope project

# Edit skills/ in place; re-run after changes
./scripts/install-skills.sh --symlink
```

Then **start a new Agent chat** (skills load at session startup).

### Manual install

| Environment | Personal | Project-scoped |
|-------------|----------|----------------|
| **Cursor** | `~/.cursor/skills/<name>/` | `.cursor/skills/<name>/` |
| **Claude Code** | `~/.claude/skills/<name>/` | `.claude/skills/<name>/` |

```bash
cp -R skills/llm-council ~/.cursor/skills/llm-council
```

**Discovery:** `description` in `SKILL.md` frontmatter drives auto-triggering. After edits under `skills/`, re-run the install script (or use `--symlink`).

In some managed environments, writing to `~/.cursor/skills` or `.cursor/skills` may require running the script in a normal terminal (outside the sandbox).

## How to invoke

**Engineering / infrastructure:**

```text
LLM Council: Should we use Kafka or RabbitMQ for our event pipeline?
Context: ~10k events/sec, at-least-once delivery, small ops team.
```

**Service ownership / org design:**

```text
pressure-test RFC: split billing into its own service or keep it inside the monolith?
Context: 30-engineer org, monthly releases, weak observability, billing incidents are rising.
```

**Code-aware** (reads the fixture repo before debating — see [`url-shortener-fixture/sample-questions`](url-shortener-fixture/sample-questions)):

```text
/llm-council Should this repo use Postgres or Redis for persistence?
/llm-council Is base-62 the right encoding for this shortener, or should we use UUIDs?
```

**Optional inputs:**

| Input | Required | Notes |
|-------|----------|--------|
| Topic / question | Yes | What to debate |
| Context | No | Constraints, stack, scale, deadlines |
| Decision criteria | No | Inferred if omitted |
| Output depth | No | `quick`, `standard` (default), or `deep` |

## url-shortener-fixture (code-aware fixture)

[`url-shortener-fixture/`](url-shortener-fixture/) is a minimal in-memory URL shortener with base-62 codes. It exists so council debates cite real modules, tests, and limitations—not an imagined system.

| File | Role |
|------|------|
| `shortener.py` | `encode`/`decode` and `Shortener` (shorten, resolve, stats) |
| `cli.py` | CLI: `shorten`, `resolve`, `stats` |
| `test_shortener.py` | Test suite |

**CLI** (state persists to `.shortener.json`, so codes survive between commands):

```bash
cd "url-shortener-fixture"
python3 cli.py shorten https://example.com   # -> https://sh.rt/1
python3 cli.py resolve 1                      # -> https://example.com
python3 cli.py stats 1                        # -> https://example.com (N clicks)
```

**Tests:**

```bash
cd "url-shortener-fixture" && pytest -q
```

If `pytest` is not available:

```bash
cd "url-shortener-fixture" && python3 -c "
import test_shortener as t
for n in dir(t):
    if n.startswith('test_'): getattr(t, n)(); print('PASS', n)"
```

More detail: [`url-shortener-fixture/README.md`](url-shortener-fixture/README.md).

## Development workflow

1. Edit files under `skills/` (keep `llm-council` SKILL.md, `agents/agents.yaml`, and `references/debate-framework.md` aligned).
2. Run `./scripts/install-skills.sh` (or re-copy manually).
3. Restart the agent session.
4. Run an ADR/RFC debate against `url-shortener-fixture/` or your own engineering decision.
5. Commit example output under `llm-council-output/` when useful.

See [`CLAUDE.md`](CLAUDE.md) for sandbox and sync notes.

## Example output

| Artifact | Topic | Domain |
|----------|--------|--------|
| [`kafka-vs-rabbitmq.html`](llm-council-output/kafka-vs-rabbitmq.html) | Kafka vs RabbitMQ for an event pipeline (reproducible from [`examples/kafka-vs-rabbitmq.json`](examples/kafka-vs-rabbitmq.json)) | Infrastructure |
| [`sequential-vs-random-codes.html`](llm-council-output/sequential-vs-random-codes.html) | Sequential vs random short codes (code-aware; reproducible via `./scripts/run-demo.sh`) | Code design |

Open any `.html` file in a browser — no server required. To generate your own ADR/RFC review, run the agents runner; it prints/writes Markdown and renders the HTML artifact automatically:

```bash
# ADR decision
python3 scripts/run_agents.py --topic "ADR: GraphQL or REST for the mobile API?"

# RFC review with trace
python3 scripts/run_agents.py --topic "RFC: split billing from the monolith?" --context "30 engineers, rising billing incidents" --trace-output billing-council.trace.json

# Single-call compatibility runner
python3 scripts/run_debate.py --topic "ADR: Monorepo or polyrepo for a 30-engineer org?" --depth deep --output debate.md --json-output debate.json
```

Markdown and HTML are rendered from the same validated council JSON contract defined in [`scripts/council_tool.py`](scripts/council_tool.py).
