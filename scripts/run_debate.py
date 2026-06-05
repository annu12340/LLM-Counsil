#!/usr/bin/env python3
"""Run an LLM Council debate directly via the Anthropic API.

This proves debate quality from the repo itself — no Cursor or Claude Code needed.
The model returns validated council JSON; this script renders Markdown and the
self-contained HTML artifact from that same data.

Usage:
    python3 scripts/run_debate.py --topic "Kafka vs RabbitMQ"
    python3 scripts/run_debate.py --topic "Postgres or Redis?" --context "small team, read-heavy"
    python3 scripts/run_debate.py --topic "..." --depth deep --output debate.md
    python3 scripts/run_debate.py --topic "..." --json-output debate.json

Requires:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from council_tool import (
    DEFAULT_OUTPUT_DIR,
    render_html,
    render_markdown,
    slugify,
    validate_html_text,
    validate_input_data,
)

ROOT = Path(__file__).resolve().parents[1]
SKILL_MD = ROOT / "skills" / "llm-council" / "SKILL.md"
DEFAULT_MODEL = os.environ.get("LLM_COUNCIL_MODEL", "claude-opus-4-8")
DEFAULT_MAX_TOKENS = int(os.environ.get("LLM_COUNCIL_MAX_TOKENS", "16000"))

JSON_CONTRACT = """
Return ONLY valid JSON. Do not wrap it in Markdown fences and do not add prose.

The JSON must match the renderer contract used by scripts/council_tool.py:
- top-level keys: title, subtitle, topic, naive, context, round1, peer_rating,
  round2, round3, stance_buckets, evolution, final_verdict, bottom_line,
  footer_codebase; include adr for architecture/design topics.
- persona_id values must be exactly: first_principles, research, systems,
  skeptic, product. For a security council, replace product with security.
- round1, round2, round3 must each contain exactly 5 turns. round2 turns also
  need a target field. Every turn needs text and verdict.
- peer_rating.positions, peer_rating.ratings, peer_rating.averages, and
  peer_rating.ranking must each contain 5 items. Raters skip their own position
  with {"self": true}; all other cells need {"score": 1-10, "note": "..."}.
- stance_buckets must contain topic-derived option keys plus neither/undecided
  where useful. tone must be one of accent, warn, good, muted, accent-2, bad.
- evolution.rows must contain 5 personas, each with exactly 3 round entries.
  Each round stance must be one of the stance_buckets keys.
- final_verdict.confidence.score must be 0-100 and next_actions must contain
  exactly 3 strings.

Generate the full debate content in the JSON fields. The runner will validate
the JSON, render Markdown, render HTML, and validate the HTML contract.
""".strip()


def build_user_message(topic: str, context: str, depth: str) -> str:
    parts = [f"Topic: {topic}"]
    if context:
        parts.append(f"Context: {context}")
    parts.append(f"Output depth: {depth}")
    parts.append(JSON_CONTRACT)
    return "\n".join(parts)


def response_text(message: object) -> str:
    content = (
        message.get("content", message)
        if isinstance(message, dict)
        else getattr(message, "content", message)
    )
    if isinstance(content, str):
        return content

    parts = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict):
            parts.append(str(block.get("text", "")))
        else:
            parts.append(str(getattr(block, "text", "")))
    return "\n".join(part for part in parts if part)


def parse_debate_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    decoder = json.JSONDecoder()
    for match in re.finditer(r"{", text):
        try:
            data, _ = decoder.raw_decode(text[match.start() :])
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data

    raise ValueError("model response did not contain valid council JSON")


def run_debate(
    topic: str,
    context: str = "",
    depth: str = "standard",
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    client: object | None = None,
) -> dict:
    if client is None:
        try:
            import anthropic
        except ImportError:
            sys.exit("anthropic package not installed. Run: pip install -r requirements.txt")

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            sys.exit("ANTHROPIC_API_KEY environment variable is not set")

        client = anthropic.Anthropic(api_key=api_key)

    system_prompt = SKILL_MD.read_text()
    user_message = build_user_message(topic, context, depth)

    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    data = parse_debate_json(response_text(message))
    validate_input_data(data)
    return data


def write_artifacts(
    data: dict,
    output: str | None = None,
    html_output: str | None = None,
    json_output: str | None = None,
) -> tuple[str, Path, Path | None]:
    markdown = render_markdown(data)
    html = render_html(data)
    errors = validate_html_text(html)
    if errors:
        raise ValueError("rendered HTML failed contract validation: " + "; ".join(errors))

    html_path = Path(html_output) if html_output else DEFAULT_OUTPUT_DIR / f"{slugify(data['title'])}.html"
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html)

    if output:
        markdown_path = Path(output)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(markdown)

    json_path = None
    if json_output:
        json_path = Path(json_output)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(data, indent=2) + "\n")

    return markdown, html_path, json_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--topic", required=True, help="The question or decision to debate")
    parser.add_argument("--context", default="", help="Constraints, stack, scale, deadlines (optional)")
    parser.add_argument(
        "--depth",
        choices=["quick", "standard", "deep"],
        default="standard",
        help="Verbosity per persona turn (default: standard)",
    )
    parser.add_argument("--output", help="Write markdown to this file instead of stdout")
    parser.add_argument(
        "--html-output",
        help="Write the self-contained HTML artifact to this path (default: llm-council-output/<title>.html)",
    )
    parser.add_argument("--json-output", help="Write validated council JSON to this file")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Anthropic model to use (default: LLM_COUNCIL_MODEL or claude-opus-4-8)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help="Maximum response tokens (default: LLM_COUNCIL_MAX_TOKENS or 16000)",
    )
    args = parser.parse_args()

    print(f"Council convening on: {args.topic!r}", file=sys.stderr)
    print(f"Model: {args.model}  |  Depth: {args.depth}", file=sys.stderr)
    print("Running and requesting validated council JSON...", file=sys.stderr)

    data = run_debate(args.topic, args.context, args.depth, args.model, args.max_tokens)
    markdown, html_path, json_path = write_artifacts(
        data,
        output=args.output,
        html_output=args.html_output,
        json_output=args.json_output,
    )

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
