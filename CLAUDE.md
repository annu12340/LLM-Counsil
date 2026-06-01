# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A **Claude Code Skill-authoring workspace**, not a deployable application. It holds:

- `llm-council/` — the authored Skill package (`SKILL.md`, `agents/openai.yaml`, `references/debate-framework.md`). This is the primary artifact.
- `sample-repo/` — a tiny in-memory URL shortener used as a **test fixture** for exercising the Skill against real code (it is not the product).
- `llm-council-output/` — rendered debate artifacts (e.g. `kafka-vs-rabbitmq.html`) produced by running the Skill.

## Skill development — the critical workflow detail

Editing files under `llm-council/` here does **NOT** change the active Skill. Claude Code only discovers skills under:

- `~/.claude/skills/<name>/SKILL.md` (personal — currently where `llm-council` is installed), or
- `<project>/.claude/skills/<name>/SKILL.md` (project-scoped)

Consequences to remember:

- **After editing the Skill here, re-copy it to the installed location** or the change has no effect:
  `cp -R llm-council ~/.claude/skills/llm-council`
- **Skills load at session startup.** Changes only take effect after restarting Claude Code / starting a new session.
- **`<project>/.claude/skills` is blocked by a managed sandbox rule** in this workspace. Writing there (mkdir/cp) fails with "Operation not permitted" and requires `dangerouslyDisableSandbox: true`. The personal `~/.claude/skills` path has the same restriction, so installing/copying the Skill needs the sandbox disabled.
- `SKILL.md` frontmatter (`name`, `description`) is what drives discovery and auto-triggering. The `description` is the trigger signal — keep it specific about *when* to invoke.

## Skill structure (llm-council)

`SKILL.md` defines a 6-persona structured debate (5 debaters + a Judge who stays silent until the verdict) over a 4-round flow: Opening Positions → Challenges → Rebuttals → Final Verdict. `agents/openai.yaml` mirrors the same roster/flow for an OpenAI-style multi-agent runner, and `references/debate-framework.md` holds the scoring rubric. Keep these three in sync — a change to personas or rounds in one should be reflected in the others.

## sample-repo commands

The sandbox Python environment has **no pytest installed**. Two ways to run the suite:

```bash
# If pytest is available:
cd sample-repo && pytest -q

# Sandbox-safe fallback (no pytest needed) — run each test fn directly:
cd sample-repo && python3 -c "
import test_shortener as t
for n in dir(t):
    if n.startswith('test_'): getattr(t, n)(); print('PASS', n)"
```

CLI usage (state is in-memory and resets every invocation — codes do not persist between commands):

```bash
cd sample-repo
python3 cli.py shorten https://example.com   # -> https://sh.rt/1
python3 cli.py resolve 1                      # -> https://example.com
python3 cli.py stats 1                        # -> https://example.com (N clicks)
```

`shortener.py` is the core (base-62 `encode`/`decode` + the `Shortener` class with sequential ids starting at 1); `cli.py` is a thin wrapper that constructs a fresh `Shortener` per run.
