#!/usr/bin/env python3
"""Run LLM Council as an executable agents.yaml workflow.

This runner makes the agents-track behavior explicit: each configured persona
gets its own model call for each debate round, and the Judge is called only for
Round 4. The final output still goes through the same validated JSON ->
Markdown -> self-contained HTML pipeline as run_debate.py.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

from council_tool import validate_input_data
from run_debate import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    parse_debate_json,
    response_text,
    write_artifacts,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AGENTS_CONFIG = ROOT / "skills" / "llm-council" / "agents" / "agents.yaml"

PERSONA_ID_MAP = {
    "first_principles_thinker": "first_principles",
    "research_scientist": "research",
    "systems_engineer": "systems",
    "skeptic_red_team": "skeptic",
    "product_user_advocate": "product",
    "security_engineer": "security",
}


def load_config(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)


def agent_by_id(config: dict) -> dict[str, dict]:
    return {agent["id"]: agent for agent in config["agents"]}


def flow_step(config: dict, round_id: int | float) -> dict:
    for step in config["flow"]:
        if step["round"] == round_id:
            return step
    raise ValueError(f"agents config has no flow step for round {round_id}")


def debater_ids(config: dict) -> list[str]:
    return list(flow_step(config, 1)["participants"])


def renderer_persona_id(agent_id: str) -> str:
    if agent_id not in PERSONA_ID_MAP:
        raise ValueError(f"agent {agent_id!r} cannot be rendered as a council persona")
    return PERSONA_ID_MAP[agent_id]


def call_agent(
    client: object,
    model: str,
    max_tokens: int,
    agent: dict,
    shared_rules: str,
    prompt: str,
) -> dict:
    system = (
        f"Agent ID: {agent['id']}\n"
        f"Role: {agent['role']}\n\n"
        f"{agent['system']}\n\n"
        f"Shared council rules:\n{shared_rules}\n\n"
        "Return only valid JSON for your assigned turn."
    )
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": agent.get("temperature", 0.7),
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }
    message = client.messages.create(**kwargs)
    return parse_debate_json(response_text(message))


def call_agent_with_retry(
    client: object,
    model: str,
    max_tokens: int,
    agent: dict,
    shared_rules: str,
    prompt: str,
    max_retries: int = 2,
) -> dict:
    delay = 2.0
    for attempt in range(max_retries + 1):
        try:
            return call_agent(client, model, max_tokens, agent, shared_rules, prompt)
        except Exception as exc:
            if attempt == max_retries:
                raise
            print(
                f"  [retry {attempt + 1}/{max_retries}] {agent['id']}: {exc}",
                file=sys.stderr,
            )
            time.sleep(delay)
            delay *= 2


def run_parallel(tasks: list) -> list:
    """Run a list of zero-argument callables concurrently, preserving order."""
    results = [None] * len(tasks)
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        futures = {executor.submit(task): i for i, task in enumerate(tasks)}
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    return results


def load_client() -> object:
    try:
        import anthropic
    except ImportError:
        sys.exit("anthropic package not installed. Run: pip install -r requirements.txt")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY environment variable is not set")
    return anthropic.Anthropic(api_key=api_key)


def render_context(topic: str, context: str, depth: str) -> str:
    parts = [f"Topic: {topic}", f"Output depth: {depth}"]
    if context:
        parts.append(f"Context: {context}")
    return "\n".join(parts)


def prompt_json_schema(schema: str) -> str:
    return f"Return JSON only with this exact shape:\n{schema}"


def normalize_turn(agent_id: str, data: dict, target_required: bool = False) -> dict:
    turn = {
        "persona_id": renderer_persona_id(agent_id),
        "text": data["text"],
        "verdict": data["verdict"],
    }
    if target_required:
        turn["target"] = data["target"]
    return turn


def transcript_turns(title: str, turns: list[dict]) -> str:
    lines = [title]
    for turn in turns:
        target = f" -> {turn['target']}" if "target" in turn else ""
        lines.append(
            f"- {turn['persona_id']}{target}: {turn['text']}\n"
            f"  Verdict: {turn['verdict']}"
        )
    return "\n".join(lines)


def build_positions(topic: str, round1: list[dict]) -> list[dict]:
    positions = []
    for idx, turn in enumerate(round1):
        positions.append(
            {
                "source_index": idx,
                "persona_id": turn["persona_id"],
                "summary": turn["verdict"],
            }
        )
    random.Random(topic).shuffle(positions)
    for idx, item in enumerate(positions):
        item["id"] = chr(ord("A") + idx)
    return [{key: item[key] for key in ("id", "persona_id", "summary")} for item in positions]


def positions_prompt(positions: list[dict]) -> str:
    return "\n".join(
        f"Position {item['id']}: {item['summary']}"
        for item in positions
    )


def normalize_rating_row(agent_id: str, data: dict, positions: list[dict]) -> dict:
    persona_id = renderer_persona_id(agent_id)
    raw_cells = {cell.get("position_id"): cell for cell in data.get("cells", [])}
    cells = []
    for position in positions:
        if position["persona_id"] == persona_id:
            cells.append({"self": True})
            continue
        cell = raw_cells.get(position["id"])
        if not cell:
            raise ValueError(f"missing peer rating for Position {position['id']} from {agent_id}")
        cells.append({"score": cell["score"], "note": cell["note"]})
    return {"persona_id": persona_id, "cells": cells}


def build_peer_rating(positions: list[dict], ratings: list[dict]) -> dict:
    averages = []
    for idx, position in enumerate(positions):
        scores = [
            row["cells"][idx]["score"]
            for row in ratings
            if not row["cells"][idx].get("self")
        ]
        averages.append({"position_id": position["id"], "score": round(sum(scores) / len(scores), 1)})

    position_lookup = {item["id"]: item for item in positions}
    ranking = []
    for item in sorted(averages, key=lambda row: row["score"], reverse=True):
        position = position_lookup[item["position_id"]]
        ranking.append(
            {
                "position_id": item["position_id"],
                "score": item["score"],
                "summary": position["summary"],
            }
        )

    return {
        "positions": positions,
        "ratings": ratings,
        "averages": averages,
        "ranking": ranking,
        "reveal_summary": "The blind scoring ranked the opening arguments before the persona mapping was revealed.",
    }


def build_trace(data: dict) -> str:
    return "\n\n".join(
        [
            f"Topic: {data['topic']}",
            "Naive baseline:\n"
            f"{data['naive']['answer']}\nRisk: {data['naive']['risk']}",
            transcript_turns("Round 1", data["round1"]),
            "Peer rating:\n" + json.dumps(data["peer_rating"], indent=2),
            transcript_turns("Round 2", data["round2"]),
            transcript_turns("Round 3", data["round3"]),
            "Final verdict:\n" + json.dumps(data["final_verdict"], indent=2),
        ]
    )


def run_agents(
    topic: str,
    context: str = "",
    depth: str = "standard",
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    config_path: Path = DEFAULT_AGENTS_CONFIG,
    client: object | None = None,
) -> tuple[dict, list[dict]]:
    config = load_config(config_path)
    agents = agent_by_id(config)
    shared_rules = config.get("shared_rules", "")
    client = client or load_client()

    calls: list[dict] = []

    base_context = render_context(topic, context, depth)

    # Round 0 — single naive baseline call
    naive_agent = agents["naive_baseline"]
    print("  Round 0: naive baseline...", file=sys.stderr)
    naive = call_agent_with_retry(
        client,
        model,
        max_tokens,
        naive_agent,
        shared_rules,
        "\n\n".join(
            [
                base_context,
                flow_step(config, 0)["instruction"],
                prompt_json_schema('{"answer": "2-4 sentence baseline", "risk": "one-line risk"}'),
            ]
        ),
    )
    calls.append({"round": 0, "agent_id": naive_agent["id"], "role": naive_agent["role"]})

    # Round 1 — 5 opening positions in parallel
    print("  Round 1: 5 opening positions (parallel)...", file=sys.stderr)
    r1_agent_ids = debater_ids(config)
    r1_prompt = "\n\n".join(
        [
            base_context,
            "Round 1 - Opening Positions.",
            flow_step(config, 1)["instruction"],
            prompt_json_schema('{"text": "opening position", "verdict": "one-line stance"}'),
        ]
    )

    def _r1_task(agent_id: str) -> dict:
        result = call_agent_with_retry(
            client, model, max_tokens, agents[agent_id], shared_rules, r1_prompt
        )
        return normalize_turn(agent_id, result)

    round1 = run_parallel([lambda aid=aid: _r1_task(aid) for aid in r1_agent_ids])
    calls.extend(
        {"round": 1, "agent_id": aid, "role": agents[aid]["role"]} for aid in r1_agent_ids
    )

    # Round 1.5 — blind peer rating, 5 calls in parallel
    print("  Round 1.5: blind peer rating (parallel)...", file=sys.stderr)
    positions = build_positions(topic, round1)
    r15_instruction = flow_step(config, 1.5)["instruction"]
    anon_positions_text = positions_prompt(positions)

    def _r15_task(agent_id: str) -> dict:
        own_position = next(
            p["id"] for p in positions if p["persona_id"] == renderer_persona_id(agent_id)
        )
        prompt = "\n\n".join(
            [
                base_context,
                "Round 1.5 - Peer Rating (anonymized).",
                r15_instruction,
                "Opening positions, anonymized:",
                anon_positions_text,
                f"Your own Position ID: {own_position}. Mark it as self and do not score it.",
                prompt_json_schema(
                    '{"cells": [{"position_id": "A", "score": 1-10, "note": "one-line critique"}, {"position_id": "B", "self": true}]}'
                ),
            ]
        )
        result = call_agent_with_retry(
            client, model, max_tokens, agents[agent_id], shared_rules, prompt
        )
        return normalize_rating_row(agent_id, result, positions)

    ratings = run_parallel([lambda aid=aid: _r15_task(aid) for aid in r1_agent_ids])
    calls.extend(
        {"round": 1.5, "agent_id": aid, "role": agents[aid]["role"]} for aid in r1_agent_ids
    )
    peer_rating = build_peer_rating(positions, ratings)

    # Round 2 — challenges, 5 calls in parallel
    print("  Round 2: challenges (parallel)...", file=sys.stderr)
    r1_transcript = transcript_turns("Round 1 openings", round1)
    peer_rating_summary = json.dumps(peer_rating["ranking"], indent=2)
    r2_instruction = flow_step(config, 2)["instruction"]

    def _r2_task(agent_id: str) -> dict:
        prompt = "\n\n".join(
            [
                base_context,
                r1_transcript,
                "Peer rating summary:",
                peer_rating_summary,
                "Round 2 - Challenges.",
                r2_instruction,
                prompt_json_schema(
                    '{"target": "persona role name being challenged", "text": "specific challenge", "verdict": "one-line stance"}'
                ),
            ]
        )
        result = call_agent_with_retry(
            client, model, max_tokens, agents[agent_id], shared_rules, prompt
        )
        return normalize_turn(agent_id, result, target_required=True)

    round2 = run_parallel([lambda aid=aid: _r2_task(aid) for aid in r1_agent_ids])
    calls.extend(
        {"round": 2, "agent_id": aid, "role": agents[aid]["role"]} for aid in r1_agent_ids
    )

    # Round 3 — rebuttals, 5 calls in parallel
    print("  Round 3: rebuttals (parallel)...", file=sys.stderr)
    r2_transcript = transcript_turns("Round 2 challenges", round2)
    r3_instruction = flow_step(config, 3)["instruction"]

    def _r3_task(agent_id: str) -> dict:
        prompt = "\n\n".join(
            [
                base_context,
                r1_transcript,
                r2_transcript,
                "Round 3 - Rebuttals.",
                r3_instruction,
                prompt_json_schema('{"text": "rebuttal or update", "verdict": "one-line stance"}'),
            ]
        )
        result = call_agent_with_retry(
            client, model, max_tokens, agents[agent_id], shared_rules, prompt
        )
        return normalize_turn(agent_id, result)

    round3 = run_parallel([lambda aid=aid: _r3_task(aid) for aid in r1_agent_ids])
    calls.extend(
        {"round": 3, "agent_id": aid, "role": agents[aid]["role"]} for aid in r1_agent_ids
    )

    # Round 4 — Judge only (gated; never called before this point)
    print("  Round 4: judge synthesizing verdict...", file=sys.stderr)
    judge_agent = agents["judge_synthesizer"]
    judge_result = call_agent_with_retry(
        client,
        model,
        max_tokens,
        judge_agent,
        shared_rules,
        "\n\n".join(
            [
                base_context,
                "Round 4 - Final Verdict. You have not participated in Rounds 1-3.",
                flow_step(config, 4)["instruction"],
                transcript_turns("Round 1 openings", round1),
                "Peer rating:",
                json.dumps(peer_rating, indent=2),
                transcript_turns("Round 2 challenges", round2),
                transcript_turns("Round 3 rebuttals", round3),
                "Return only the final artifact fields below. Do not include round1, round2, round3, naive, peer_rating, or topic.",
                prompt_json_schema(
                    """{
  "title": "short artifact title",
  "subtitle": "one sentence subtitle",
  "context": {
    "paragraphs": ["context paragraph"],
    "criteria": [{"label": "1. Criterion", "text": "criterion explanation"}],
    "assumption": "stated assumption"
  },
  "stance_buckets": [{"key": "topic-option", "tone": "accent"}],
  "evolution": {
    "summary": "how stances changed",
    "rows": [{"persona_id": "first_principles|research|systems|skeptic|product", "rounds": [{"stance": "bucket-key", "label": "short label"}], "final_stance": "final stance"}]
  },
  "final_verdict": {
    "best_argument": "...",
    "biggest_risk": "...",
    "key_tradeoff": "...",
    "consensus": "...",
    "recommendation": "...",
    "confidence": {"level": "low|medium|medium-high|high", "label": "MEDIUM", "pill_class": "low|med|high", "score": 0-100, "text": "..."},
    "next_actions": ["action 1", "action 2", "action 3"]
  },
  "adr": {"status": "proposed", "decision": "...", "consequences": "..."},
  "bottom_line": "one sentence bottom line",
  "footer_codebase": "repo/path or standalone decision"
}"""
                ),
            ]
        ),
    )
    calls.append({"round": 4, "agent_id": judge_agent["id"], "role": judge_agent["role"]})

    data = {
        "title": judge_result["title"],
        "subtitle": judge_result["subtitle"],
        "topic": topic,
        "naive": naive,
        "context": judge_result["context"],
        "round1": round1,
        "peer_rating": peer_rating,
        "round2": round2,
        "round3": round3,
        "stance_buckets": judge_result["stance_buckets"],
        "evolution": judge_result["evolution"],
        "final_verdict": judge_result["final_verdict"],
        "adr": judge_result.get("adr"),
        "bottom_line": judge_result["bottom_line"],
        "footer_codebase": judge_result["footer_codebase"],
    }
    validate_input_data(data)
    return data, calls


def write_trace(path: str, data: dict, calls: list[dict]) -> None:
    trace = {
        "calls": calls,
        "transcript": build_trace(data),
    }
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(trace, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", required=True, help="The ADR/RFC decision to debate")
    parser.add_argument("--context", default="", help="Constraints, repo notes, scale, deadlines")
    parser.add_argument(
        "--depth",
        choices=["quick", "standard", "deep"],
        default="standard",
        help="Verbosity per persona turn",
    )
    parser.add_argument("--output", help="Write Markdown debate to this file")
    parser.add_argument("--html-output", help="Write self-contained HTML to this path")
    parser.add_argument("--json-output", help="Write validated council JSON to this file")
    parser.add_argument("--trace-output", help="Write call order and transcript trace JSON")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Anthropic model id (default: LLM_COUNCIL_MODEL or claude-opus-4-8)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help="Maximum tokens per model call",
    )
    parser.add_argument(
        "--agents-config",
        default=str(DEFAULT_AGENTS_CONFIG),
        help="Path to agents.yaml",
    )
    args = parser.parse_args()

    print(f"Running agents.yaml council on: {args.topic!r}", file=sys.stderr)
    print(f"Model: {args.model}  |  Depth: {args.depth}", file=sys.stderr)

    data, calls = run_agents(
        args.topic,
        context=args.context,
        depth=args.depth,
        model=args.model,
        max_tokens=args.max_tokens,
        config_path=Path(args.agents_config),
    )
    markdown, html_path, json_path = write_artifacts(
        data,
        output=args.output,
        html_output=args.html_output,
        json_output=args.json_output,
    )

    if args.trace_output:
        write_trace(args.trace_output, data, calls)
        print(f"Trace written to: {args.trace_output}", file=sys.stderr)

    if args.output:
        print(f"Debate written to: {args.output}", file=sys.stderr)
    else:
        print(markdown, end="")

    print(f"HTML written to: {html_path}", file=sys.stderr)
    if json_path:
        print(f"Validated JSON written to: {json_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
