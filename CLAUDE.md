# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A **Claude Code / Cursor Agent Skill authoring workspace**. It holds:

- `skills/` — skill packages (source of truth); install with `scripts/install-skills.sh`
- `High critical project mock/` — code-aware fixture for council debates
- `llm-council-output/` — rendered debate HTML artifacts
- `index.html` — landing page

## Install skills

Agents do **not** read `skills/` automatically. Install into a discovery path, then start a **new session**:

```bash
./scripts/install-skills.sh                    # Cursor, personal (~/.cursor/skills)
./scripts/install-skills.sh --target claude    # Claude Code (~/.claude/skills)
./scripts/install-skills.sh --scope project    # .cursor/skills or .claude/skills in this repo
./scripts/install-skills.sh --symlink          # symlink from skills/ for live edits
```

Discovery paths:

- **Claude Code:** `~/.claude/skills/<name>/` or `<project>/.claude/skills/<name>/`
- **Cursor:** `~/.cursor/skills/<name>/` or `<project>/.cursor/skills/<name>/`

After editing under `skills/`, re-run the install script (unless using `--symlink`).

In some managed environments, copying to `~/.cursor/skills` or `.cursor/skills` requires running the script outside the sandbox.

## Skill packages

| Directory | `name` in SKILL.md |
|-----------|-------------------|
| `skills/llm-council/` | `llm-council` |

`skills/llm-council/`: 6-persona debate (5 debaters + Judge), 4 rounds, HTML output contract. Keep `SKILL.md`, `agents/openai.yaml`, and `references/debate-framework.md` in sync.

## Council renderer / validator

The repo includes a real local implementation of the HTML artifact contract:

```bash
./scripts/run-demo.sh
python3 scripts/council_tool.py validate-input examples/sequential-vs-random-codes.json
python3 scripts/council_tool.py render examples/sequential-vs-random-codes.json --output llm-council-output/sequential-vs-random-codes.html
python3 scripts/council_tool.py validate-html llm-council-output/sequential-vs-random-codes.html
python3 -m unittest tests.test_council_tool
```

Use this tool when changing the HTML contract or the example debate structure so the repo proves the behavior instead of only describing it.

## High critical project mock (fixture)

```bash
cd "High critical project mock"
python3 cli.py shorten https://example.com
python3 cli.py resolve 1
```

Tests (no pytest in minimal sandbox):

```bash
cd "High critical project mock" && python3 -c "
import test_shortener as t
for n in dir(t):
    if n.startswith('test_'): getattr(t, n)(); print('PASS', n)"
```

State persists to `.shortener.json`; the CLI loads it each invocation, so codes survive between commands.
