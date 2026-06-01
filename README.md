# LLM Council — Agent Skill

**LLM Council** is a **Cursor / Claude Code Agent Skill** that runs a structured 5-persona debate (plus Judge), blind peer-rates opening arguments, and outputs a committed verdict—**markdown**, an optional **ADR snippet**, and **offline HTML** under [`llm-council-output/`](llm-council-output/).

Use it to pressure-test architecture choices, design decisions, tech comparisons (`X vs Y`), papers, and red-team plans—not a single-shot pros/cons list.

**Landing page:** open [`index.html`](index.html) in a browser (offline-friendly).

## Quick start

1. **Install** all skills: `./scripts/install-skills.sh` (see [Install](#install)).
2. **Open** this repo in Cursor or Claude Code and start a **new session** (skills load at startup).
3. **Invoke** with a trigger phrase, for example:

```text
LLM Council: Should we use Kafka or RabbitMQ for ~10k events/sec? Small ops team; need replay.
```

**Code-aware** (reads the fixture repo before debating):

```text
/llm-council Should Acme URL shortener use Postgres or Redis for persistence?
```

4. **Review** example HTML: [`kafka-vs-rabbitmq.html`](llm-council-output/kafka-vs-rabbitmq.html) · [`postgres-vs-redis.html`](llm-council-output/postgres-vs-redis.html)

Full procedure and output contract: [`skills/llm-council/SKILL.md`](skills/llm-council/SKILL.md).

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
| [`skills/llm-council/`](skills/llm-council/) | Council debate skill — rubric, architecture reference, HTML assets, OpenAI agent config |
| [`skills/frontend-skills/`](skills/frontend-skills/) | Frontend design skill (`name: frontend-design`) |
| [`Acme URL shortener/`](Acme%20URL%20shortener/) | **Code-aware fixture** — minimal URL shortener to debate against real code |
| [`llm-council-output/`](llm-council-output/) | **Example debates** — self-contained HTML (offline-shareable) |
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

## Why this is a strong Agent Skill

- **Procedure, not vibes** — numbered rounds; Judge only speaks in the final verdict  
- **Progressive disclosure** — rubric in [`references/debate-framework.md`](skills/llm-council/references/debate-framework.md); architecture in [`references/architecture.md`](skills/llm-council/references/architecture.md)  
- **Deterministic output contract** — markdown template + HTML class/`data-*` schema in `SKILL.md`  
- **Bundled assets** — `assets/council-style.css` and `assets/council.js` inlined into each HTML artifact  
- **Portable** — [`agents/openai.yaml`](skills/llm-council/agents/openai.yaml) mirrors the same roster and flow  

## Skill packages (`skills/`)

```
skills/
├── llm-council/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── references/debate-framework.md
│   └── assets/
└── frontend-skills/
    └── SKILL.md                    # name: frontend-design
```

The `skills/` directory is **not** auto-loaded by agents. Install into a discovery path (below), then start a **new session**.

Keep `skills/llm-council/` files **in sync** when you change personas, rounds, or the HTML contract.

## Install

### Install script (recommended)

From the repo root:

```bash
./scripts/install-skills.sh
```

This installs **every** package under `skills/` using each skill’s `name:` from `SKILL.md` frontmatter (e.g. `frontend-skills/` → `frontend-design`).

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
cp -R skills/frontend-skills ~/.cursor/skills/frontend-design
```

**Discovery:** `description` in `SKILL.md` frontmatter drives auto-triggering. After edits under `skills/`, re-run the install script (or use `--symlink`).

In some managed environments, writing to `~/.cursor/skills` or `.cursor/skills` may require running the script in a normal terminal (outside the sandbox).

## How to invoke

**Generic debate:**

```text
Run an LLM Council debate: Should we use Kafka or RabbitMQ for our event pipeline?
Context: ~10k events/sec, at-least-once delivery, small ops team.
Criteria: operational simplicity, replay, cost.
```

**Against the Acme fixture** (see [`Acme URL shortener/sample-questions`](Acme%20URL%20shortener/sample-questions)):

```text
/llm-council Should this repo use Postgres or Redis for persistence?
```

```text
/llm-council Is base-62 the right encoding for this shortener, or should we use UUIDs?
```

**Optional inputs:**

| Input | Required | Notes |
|-------|----------|--------|
| Topic / question | Yes | What to debate |
| Context | No | Constraints, stack, scale, deadlines |
| Decision criteria | No | Inferred if omitted |
| Output depth | No | `quick`, `standard` (default), or `deep` |

## Acme URL shortener (code-aware fixture)

[`Acme URL shortener/`](Acme%20URL%20shortener/) is a minimal in-memory URL shortener with base-62 codes. It exists so council debates cite real modules, tests, and limitations—not an imagined system.

| File | Role |
|------|------|
| `shortener.py` | `encode`/`decode` and `Shortener` (shorten, resolve, stats) |
| `cli.py` | CLI: `shorten`, `resolve`, `stats` |
| `test_shortener.py` | Test suite |

**CLI** (state resets each invocation; codes do not persist between commands):

```bash
cd "Acme URL shortener"
python3 cli.py shorten https://example.com   # -> https://sh.rt/1
python3 cli.py resolve 1                      # -> https://example.com
python3 cli.py stats 1                        # -> https://example.com (N clicks)
```

**Tests:**

```bash
cd "Acme URL shortener" && pytest -q
```

If `pytest` is not available:

```bash
cd "Acme URL shortener" && python3 -c "
import test_shortener as t
for n in dir(t):
    if n.startswith('test_'): getattr(t, n)(); print('PASS', n)"
```

More detail: [`Acme URL shortener/README.md`](Acme%20URL%20shortener/README.md).

## Development workflow

1. Edit files under `skills/` (keep `llm-council` SKILL.md, `agents/openai.yaml`, and `references/debate-framework.md` aligned).
2. Run `./scripts/install-skills.sh` (or re-copy manually).
3. Restart the agent session.
4. Run a debate against `Acme URL shortener/` or your own topic.
5. Commit example output under `llm-council-output/` when useful.

See [`CLAUDE.md`](CLAUDE.md) for sandbox and sync notes.

## Example output

| Artifact | Topic |
|----------|--------|
| [`kafka-vs-rabbitmq.html`](llm-council-output/kafka-vs-rabbitmq.html) | Messaging / event pipeline |
| [`postgres-vs-redis.html`](llm-council-output/postgres-vs-redis.html) | Persistence (code-aware fixture) |

Open any `.html` file in a browser—no server required. Markdown structure matches [`skills/llm-council/SKILL.md`](skills/llm-council/SKILL.md).

## License

No license file is included. Add one if you plan to distribute the skill publicly.
