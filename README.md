# skill2 — LLM Council Skill Workspace

A **Claude Code / Cursor Agent Skill authoring workspace** for the **LLM Council** skill: a structured, multi-persona debate that pressure-tests technical decisions and produces an actionable verdict. This repository is not a deployable application—it holds the skill package, a small code fixture for exercising it, and example debate output.

## What’s in this repo

| Path | Purpose |
|------|---------|
| [`llm-council/`](llm-council/) | **Primary artifact** — the skill package (`SKILL.md`, agent config, scoring rubric) |
| [`sample-repo/`](sample-repo/) | **Test fixture** — a minimal in-memory URL shortener used to run code-aware debates against real code |
| [`llm-council-output/`](llm-council-output/) | **Example output** — rendered debate artifacts (e.g. HTML exports) |
| [`CLAUDE.md`](CLAUDE.md) | Agent-oriented notes for working in this repo (install paths, test commands, sync rules) |

## LLM Council at a glance

The skill runs a **4-round debate** among five expert personas plus a silent **Judge** who speaks only in the final round:

1. **Opening Positions** — each debater takes a concrete stance  
2. **Peer Rating (anonymized)** — blind scoring of Round 1 arguments  
3. **Challenges** — named, technical objections to other personas  
4. **Rebuttals** — defend or update positions  
5. **Final Verdict** — Judge synthesizes recommendation, risks, tradeoffs, and next steps  

**Personas:** First-Principles Thinker, Research Scientist, Systems Engineer, Skeptic / Red Team, Product / User Advocate, and Judge / Synthesizer. For security-focused topics, Product Advocate can be swapped for a **Security Engineer** persona.

**When to use it:** architecture or technology choices, design decisions, red-teaming a plan, paper critiques, or any question where you want tradeoffs surfaced and a decisive recommendation—not a generic pros/cons list.

**Code-aware mode:** If the topic references a repo or path, the skill instructs the agent to read `README`, entrypoints, core modules, and tests *before* debating, so arguments stay grounded in what the code actually does.

See [`llm-council/SKILL.md`](llm-council/SKILL.md) for the full procedure, input schema, and markdown output template (including an optional **ADR snippet** for architecture decisions).

## Repository layout (skill package)

```
llm-council/
├── SKILL.md                      # Skill definition (discovery, flow, output format)
├── agents/openai.yaml            # Same roster/flow for OpenAI-style multi-agent runners
└── references/debate-framework.md  # Scoring rubric and round expectations
```

Keep these three files **in sync** when you change personas, rounds, or output contracts.

## Install and activate the skill

Claude Code discovers skills only from:

- **Personal:** `~/.claude/skills/<name>/SKILL.md`
- **Project-scoped:** `<project>/.claude/skills/<name>/SKILL.md`

Editing files under `llm-council/` in this repo **does not** update the active skill until you copy them to an install location:

```bash
cp -R llm-council ~/.claude/skills/llm-council
```

**Important:**

- Skills load at **session startup** — restart Claude Code (or start a new session) after installing or updating.
- Skill discovery uses `SKILL.md` frontmatter (`name`, `description`). The `description` field drives when the skill auto-triggers; keep it specific about *when* to invoke.
- In some managed environments, writing to `~/.claude/skills` or `<project>/.claude/skills` may require disabling the sandbox for the copy step.

For **Cursor**, install the skill under your Cursor skills path (e.g. `~/.cursor/skills/` or project skills) following the same `SKILL.md` layout; see [Cursor Agent Skills](https://docs.cursor.com) for your environment’s conventions.

## How to invoke

Ask for a council debate on a topic, optionally with context and decision criteria:

```text
Run an LLM Council debate: Should we use Kafka or RabbitMQ for our event pipeline?
Context: ~10k events/sec, at-least-once delivery, small ops team.
Criteria: operational simplicity, replay, cost.
```

Against the sample fixture (see [`sample-repo/sample-questions`](sample-repo/sample-questions)):

```text
/llm-council Should this repo use Postgres or Redis for persistence?
```

```text
/llm-council Is base-62 the right encoding for this shortener, or should we use UUIDs?
```

**Optional inputs** (defined in the skill):

| Input | Required | Notes |
|-------|----------|--------|
| Topic / question | Yes | What to debate |
| Context | No | Constraints, stack, scale, deadlines |
| Decision criteria | No | Inferred if omitted |
| Output depth | No | `quick`, `standard` (default), or `deep` |

Output is markdown following the template in `SKILL.md` (topic, context, rounds, peer-rating table, final verdict, optional ADR snippet). You can save or export debates under `llm-council-output/` (e.g. [`kafka-vs-rabbitmq.html`](llm-council-output/kafka-vs-rabbitmq.html)).

## Sample repo (test fixture)

[`sample-repo/`](sample-repo/) is **tiny-shortener**: an in-memory URL shortener with base-62 codes. It exists so council debates can reference real modules, tests, and limitations—not an imaginary system.

| File | Role |
|------|------|
| `shortener.py` | `encode`/`decode` and `Shortener` (shorten, resolve, stats) |
| `cli.py` | CLI: `shorten`, `resolve`, `stats` |
| `test_shortener.py` | Test suite |

**CLI** (state resets each invocation; codes do not persist between commands):

```bash
cd sample-repo
python3 cli.py shorten https://example.com   # -> https://sh.rt/1
python3 cli.py resolve 1                      # -> https://example.com
python3 cli.py stats 1                        # -> https://example.com (N clicks)
```

**Tests:**

```bash
cd sample-repo && pytest -q
```

If `pytest` is not available (e.g. in a minimal sandbox):

```bash
cd sample-repo && python3 -c "
import test_shortener as t
for n in dir(t):
    if n.startswith('test_'): getattr(t, n)(); print('PASS', n)"
```

More detail: [`sample-repo/README.md`](sample-repo/README.md).

## Development workflow

1. Edit skill files under `llm-council/` (and keep `SKILL.md`, `agents/openai.yaml`, and `references/debate-framework.md` aligned).
2. Copy the package to your skills install directory (see above).
3. Restart the agent session.
4. Run a debate against `sample-repo` or your own topic; refine personas, rubric, or output template as needed.
5. Optionally commit example output under `llm-council-output/`.

Agent-specific commands and sandbox notes live in [`CLAUDE.md`](CLAUDE.md).

## Example output

[`llm-council-output/kafka-vs-rabbitmq.html`](llm-council-output/kafka-vs-rabbitmq.html) shows a rendered debate artifact. Markdown debates produced by the skill follow the structure in [`llm-council/SKILL.md`](llm-council/SKILL.md).

## License

No license file is included in this repository. Add one if you plan to distribute the skill publicly.
