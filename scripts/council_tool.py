#!/usr/bin/env python3
"""Render and validate LLM Council debate artifacts.

This provides a real local implementation for the HTML contract described in
skills/llm-council/SKILL.md. It takes structured JSON, emits a self-contained
HTML file, and validates either the source JSON or the generated HTML.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLE_PATH = ROOT / "skills" / "llm-council" / "assets" / "council-style.css"
SCRIPT_PATH = ROOT / "skills" / "llm-council" / "assets" / "council.js"
DEFAULT_OUTPUT_DIR = ROOT / "llm-council-output"

PERSONAS = {
    "first_principles": {
        "class": "p1",
        "name": "First-Principles Thinker",
        "short": "First-Principles",
        "avatar": "🧱",
    },
    "research": {
        "class": "p2",
        "name": "Research Scientist",
        "short": "Research Scientist",
        "avatar": "🔬",
    },
    "systems": {
        "class": "p3",
        "name": "Systems Engineer",
        "short": "Systems Engineer",
        "avatar": "⚙️",
    },
    "skeptic": {
        "class": "p4",
        "name": "Skeptic / Red Team",
        "short": "Skeptic / Red Team",
        "avatar": "🚩",
    },
    "product": {
        "class": "p5",
        "name": "Product / User Advocate",
        "short": "Product Advocate",
        "avatar": "👤",
    },
    "security": {
        "class": "p5",
        "name": "Security Engineer",
        "short": "Security Engineer",
        "avatar": "🔐",
    },
}

RANK_MEDALS = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
STANCE_TONES = {
    "accent": (
        "rgba(124,156,255,.18)",
        "var(--accent)",
        "rgba(124,156,255,.4)",
    ),
    "warn": (
        "rgba(251,191,36,.16)",
        "var(--warn)",
        "rgba(251,191,36,.4)",
    ),
    "good": (
        "rgba(74,222,128,.15)",
        "var(--good)",
        "rgba(74,222,128,.4)",
    ),
    "muted": (
        "rgba(154,163,184,.14)",
        "var(--muted)",
        "var(--border)",
    ),
    "accent-2": (
        "rgba(180,140,255,.18)",
        "var(--accent-2)",
        "rgba(180,140,255,.4)",
    ),
    "bad": (
        "rgba(248,113,113,.15)",
        "var(--bad)",
        "rgba(248,113,113,.4)",
    ),
}


def read_json(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def slugify(text: str) -> str:
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def persona_info(persona_id: str, display_name: str | None = None) -> dict:
    if persona_id not in PERSONAS:
        raise ValueError(f"unknown persona_id: {persona_id}")
    info = dict(PERSONAS[persona_id])
    if display_name:
        info["name"] = display_name
        info["short"] = display_name
    return info


def html_paragraphs(items: list[str]) -> str:
    return "\n".join(f"    <p>{escape(item)}</p>" for item in items)


def render_turn(turn: dict, challenge: bool = False) -> str:
    info = persona_info(turn["persona_id"], turn.get("display_name"))
    speaker = (
        f'<span class="speaker {info["class"]}"><span class="avatar">{info["avatar"]}</span>'
        f"{escape(info['name'])}"
    )
    if challenge:
        speaker += f' <span class="arrow">→ {escape(turn["target"])}:</span></span>'
    else:
        speaker += ":</span>"
    return (
        f'    <div class="turn">{speaker} {escape(turn["text"])}'
        f'\n      <div class="pverdict"><b>Verdict:</b> {escape(turn["verdict"])}</div></div>'
    )


def score_class(score: float) -> str:
    if score >= 8:
        return "s-hi"
    if score >= 6:
        return "s-mid"
    return "s-lo"


def render_peer_rating(data: dict) -> str:
    positions = {item["id"]: item for item in data["positions"]}
    anon = "\n".join(
        "      <div class=\"anon\"><span class=\"tag\">Position "
        f"{escape(item['id'])}</span> {escape(item['summary'])}</div>"
        for item in data["positions"]
    )

    headers = "".join(f"<th>{escape(item['id'])}</th>" for item in data["positions"])
    rows = []
    for row in data["ratings"]:
        info = persona_info(row["persona_id"], row.get("display_name"))
        cells = []
        for cell in row["cells"]:
            if cell.get("self"):
                cells.append('<td class="self">—</td>')
            else:
                score = cell["score"]
                cells.append(
                    f'<td data-score="{score}"><span class="score {score_class(score)}">{score}</span>'
                    f'<span class="note">{escape(cell["note"])}</span></td>'
                )
        rows.append(
            "      <tr>\n"
            f'        <td><span class="{info["class"]}"><span class="avatar">{info["avatar"]}</span>'
            f"{escape(info['short'])}</span></td>"
            + "".join(cells)
            + "\n      </tr>"
        )

    avg_cells = "".join(
        f'<td><span class="{score_class(item["score"])}">{item["score"]}</span></td>'
        for item in data["averages"]
    )
    ranking = []
    for idx, item in enumerate(data["ranking"]):
        pos = positions[item["position_id"]]
        pinfo = persona_info(pos["persona_id"], pos.get("display_name"))
        glow = " glow" if idx == 0 else ""
        medal = RANK_MEDALS[idx] if idx < len(RANK_MEDALS) else f"{idx + 1}."
        ranking.append(
            f'      <li><span class="bar {pinfo["class"]}{glow}" style="--score:{item["score"]}"></span>'
            f'<span class="medal">{medal}</span> <b>Position {escape(item["position_id"])}</b> — '
            f'{escape(item["summary"])} <span class="sc">{item["score"]}</span></li>'
        )

    reveal = " · ".join(
        f'{escape(item["id"])} = <span class="{persona_info(item["persona_id"], item.get("display_name"))["class"]}">'
        f'<span class="avatar">{persona_info(item["persona_id"], item.get("display_name"))["avatar"]}</span>'
        f'{escape(persona_info(item["persona_id"], item.get("display_name"))["short"])}</span>'
        for item in data["positions"]
    )

    return f"""
  <h2><span class="num">★</span> Anonymized Peer Rating</h2>
  <div class="card">
    <p style="color:var(--muted);font-size:14px;margin-top:0">The five opening positions were stripped of author labels and shuffled. Each persona scored the others <b>blind</b> (own = <span class="self">—</span>), so the numbers reflect argument quality, not who said it. Composite 1–10 = analytical <b>rigor</b> + <b>usefulness</b>.</p>
    <div class="anon-grid">
{anon}
    </div>
    <table class="rate-table">
      <tr><th>Rater \\ Position</th>{headers}</tr>
{chr(10).join(rows)}
      <tr class="avg">
        <td>Average</td>{avg_cells}
      </tr>
    </table>
    <ol class="rank">
{chr(10).join(ranking)}
    </ol>
    <p class="reveal"><b>Reveal:</b> {reveal}. {escape(data["reveal_summary"])}</p>
  </div>"""


def render_evolution(data: dict) -> str:
    rows = []
    for row in data["rows"]:
        info = persona_info(row["persona_id"], row.get("display_name"))
        rounds = []
        previous = None
        for item in row["rounds"]:
            changed = item.get("changed", False)
            marker = '<span class="chg" title="changed mind">↻</span>' if changed else ""
            rounds.append(
                f'<div class="chip" data-stance="{escape(item["stance"])}">{escape(item["label"])}{marker}</div>'
            )
            previous = item["stance"]
        rows.append(
            f'      <div class="evo-name"><span class="avatar">{info["avatar"]}</span>{escape(info["short"])}</div>\n'
            f"      {rounds[0]}\n      {rounds[1]}\n      {rounds[2]}\n"
            f'      <div class="evo-final">{escape(row["final_stance"])}</div>'
        )
    return f"""
  <h2><span class="num">↻</span> Stance Evolution — How the Council Converged</h2>
  <div class="card">
    <p style="color:var(--muted);font-size:14px;margin-top:0">{escape(data["summary"])}</p>
    <div class="evo">
      <div></div>
      <div class="evo-h">Round 1</div>
      <div class="evo-h">Round 2</div>
      <div class="evo-h">Round 3</div>
      <div class="evo-h evo-final">Final stance</div>
{chr(10).join(rows)}
    </div>
  </div>"""


def render_confidence(confidence: dict) -> str:
    pill_class = confidence.get("pill_class", "high")
    label = confidence.get("label", confidence["level"].upper())
    return (
        '<div class="vrow conf-row">'
        f'<div class="conf-text"><div class="vlabel">Confidence'
        f'<span class="pill {escape(pill_class)}">{escape(label)}</span></div>'
        f'{escape(confidence["text"])}</div>'
        f'<div class="gauge" data-confidence="{confidence["score"]}"><span class="val">0%</span></div>'
        "</div>"
    )


def render_adr(adr: dict | None) -> str:
    if not adr:
        return ""
    return f"""
  <h2>📋 ADR Snippet</h2>
  <div class="card">
    <p><b>Status:</b> {escape(adr["status"])}</p>
    <p><b>Decision:</b> {escape(adr["decision"])}</p>
    <p><b>Consequences:</b> {escape(adr["consequences"])}</p>
    </div>"""


def render_markdown_turn(turn: dict, challenge: bool = False) -> str:
    info = persona_info(turn["persona_id"], turn.get("display_name"))
    speaker = f"**{info['name']}"
    if challenge:
        speaker += f" -> {turn['target']}"
    speaker += ":**"
    return f"{speaker} {turn['text']}\n\n_Verdict: {turn['verdict']}_"


def render_markdown_peer_rating(data: dict) -> str:
    position_ids = [item["id"] for item in data["positions"]]
    position_lines = [
        f"- **Position {item['id']}** - {item['summary']}"
        for item in data["positions"]
    ]

    header = "| Rater \\ Position | " + " | ".join(position_ids) + " |"
    separator = "|---|" + "|".join("---" for _ in position_ids) + "|"
    rows = []
    for row in data["ratings"]:
        info = persona_info(row["persona_id"], row.get("display_name"))
        cells = []
        for cell in row["cells"]:
            if cell.get("self"):
                cells.append("-")
            else:
                cells.append(f'{cell["score"]} ({cell["note"]})')
        rows.append(f"| {info['short']} | " + " | ".join(cells) + " |")

    averages = [str(item["score"]) for item in data["averages"]]
    rows.append("| **Average** | " + " | ".join(averages) + " |")

    ranking = []
    for idx, item in enumerate(data["ranking"], start=1):
        ranking.append(
            f'{idx}. Position {item["position_id"]} ({item["score"]}) - {item["summary"]}'
        )

    reveal = ", ".join(
        f'{item["id"]} = {persona_info(item["persona_id"], item.get("display_name"))["short"]}'
        for item in data["positions"]
    )

    return "\n".join(
        [
            "Positions A-E (shuffled, authors hidden) scored 1-10 by each persona (own = -):",
            "",
            *position_lines,
            "",
            header,
            separator,
            *rows,
            "",
            "**Ranking:**",
            *ranking,
            "",
            f"**Reveal:** {reveal}. {data['reveal_summary']}",
        ]
    )


def render_markdown(data: dict) -> str:
    """Render validated council data to the public Markdown debate format."""
    validate_input_data(data)

    context = "\n\n".join(data["context"]["paragraphs"])
    criteria = "\n".join(
        f'- **{item["label"]}** - {item["text"]}'
        for item in data["context"]["criteria"]
    )
    round1 = "\n\n".join(render_markdown_turn(item) for item in data["round1"])
    round2 = "\n\n".join(render_markdown_turn(item, challenge=True) for item in data["round2"])
    round3 = "\n\n".join(render_markdown_turn(item) for item in data["round3"])
    actions = "\n".join(
        f"  {idx}. {item}"
        for idx, item in enumerate(data["final_verdict"]["next_actions"], start=1)
    )

    verdict = data["final_verdict"]
    confidence = verdict["confidence"]
    parts = [
        "# LLM Council Debate",
        "",
        "## Topic",
        data["topic"],
        "",
        "## Naive Single-Model Take",
        "> _What a single one-shot model says before the council convenes - shown as a baseline, not an endorsement._",
        "",
        data["naive"]["answer"],
        "",
        f"**Why this is risky:** {data['naive']['risk']}",
        "",
        "## Context",
        context,
        "",
        "**Inferred decision criteria:**",
        criteria,
        "",
        f"**Assumption:** {data['context']['assumption']}",
        "",
        "## Round 1: Opening Positions",
        round1,
        "",
        "## Peer Rating (Anonymized)",
        render_markdown_peer_rating(data["peer_rating"]),
        "",
        "## Round 2: Challenges",
        round2,
        "",
        "## Round 3: Rebuttals",
        round3,
        "",
        "## Final Verdict",
        f"- **Best argument:** {verdict['best_argument']}",
        f"- **Biggest risk:** {verdict['biggest_risk']}",
        f"- **Key tradeoff:** {verdict['key_tradeoff']}",
        f"- **Consensus:** {verdict['consensus']}",
        f"- **Recommendation:** {verdict['recommendation']}",
        f"- **Confidence level:** {confidence['level']} - {confidence['text']}",
        "- **Next 3 actions:**",
        actions,
    ]

    if data.get("adr"):
        parts.extend(
            [
                "",
                "## ADR snippet",
                f"- **Status:** {data['adr']['status']}",
                f"- **Decision:** {data['adr']['decision']}",
                f"- **Consequences:** {data['adr']['consequences']}",
            ]
        )

    return "\n".join(parts) + "\n"


def stance_css(buckets: list[dict]) -> str:
    lines = []
    for bucket in buckets:
        tone = bucket.get("tone", "muted")
        bg, color, border = STANCE_TONES[tone]
        lines.append(
            f'  .evo .chip[data-stance="{bucket["key"]}"] '
            f"{{ background: {bg}; color: {color}; border-color: {border}; }}"
        )
    return "\n".join(lines)


def render_html(data: dict) -> str:
    validate_input_data(data)
    style = STYLE_PATH.read_text()
    script = SCRIPT_PATH.read_text()
    custom_css = stance_css(data["stance_buckets"])

    context_paragraphs = "\n".join(f"    <p>{escape(item)}</p>" for item in data["context"]["paragraphs"])
    criteria = "\n".join(
        f'        <div class="crit"><b>{escape(item["label"])}</b> — {escape(item["text"])}</div>'
        for item in data["context"]["criteria"]
    )
    round1 = "\n".join(render_turn(item) for item in data["round1"])
    round2 = "\n".join(render_turn(item, challenge=True) for item in data["round2"])
    round3 = "\n".join(render_turn(item) for item in data["round3"])
    actions = "\n".join(f"        <li>{escape(item)}</li>" for item in data["final_verdict"]["next_actions"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LLM Council — {escape(data["title"])}</title>
<style>
{style}
{custom_css}
</style>
<noscript><style>.turn, .card, .evo {{ opacity: 1 !important; transform: none !important; }}</style></noscript>
</head>
<body>
<div class="wrap">

  <header class="hero">
    <span class="badge">⚖ LLM Council Debate</span>
    <h1>{escape(data["title"])}</h1>
    <p class="subtitle">{escape(data["subtitle"])}</p>
  </header>

  <div class="naive">
    <span class="naive-label">Single-model baseline — no council</span>
    <p>{escape(data["naive"]["answer"])}</p>
    <div class="naive-risk"><b>Why this is risky:</b> {escape(data["naive"]["risk"])}</div>
  </div>

  <h2>Topic</h2>
  <div class="card">
    {escape(data["topic"])}
  </div>

  <h2>Context</h2>
  <div class="card context-grid">
{context_paragraphs}
    <div>
      <div class="vlabel">Inferred decision criteria</div>
      <div class="criteria">
{criteria}
      </div>
    </div>
    <p style="color:var(--muted);font-size:14px;margin-top:6px"><b>Assumption:</b> {escape(data["context"]["assumption"])}</p>
  </div>

  <h2><span class="num">1</span> Round 1 — Opening Positions</h2>
  <div class="card">
{round1}
  </div>
{render_peer_rating(data["peer_rating"])}

  <h2><span class="num">2</span> Round 2 — Challenges</h2>
  <div class="card">
{round2}
  </div>

  <h2><span class="num">3</span> Round 3 — Rebuttals</h2>
  <div class="card">
{round3}
  </div>
{render_evolution(data["evolution"])}

  <h2>⚖ Final Verdict</h2>
  <div class="verdict">
    <div class="vrow"><div class="vlabel">Best argument</div>{escape(data["final_verdict"]["best_argument"])}</div>
    <div class="vrow"><div class="vlabel">Biggest risk</div>{escape(data["final_verdict"]["biggest_risk"])}</div>
    <div class="vrow"><div class="vlabel">Key tradeoff</div>{escape(data["final_verdict"]["key_tradeoff"])}</div>
    <div class="vrow"><div class="vlabel">Consensus</div>{escape(data["final_verdict"]["consensus"])}</div>
    <div class="vrow"><div class="vlabel">Recommendation</div><p>{escape(data["final_verdict"]["recommendation"])}</p></div>
    {render_confidence(data["final_verdict"]["confidence"])}
    <div class="vrow"><div class="vlabel">Next 3 actions</div>
      <ol class="actions">
{actions}
      </ol>
    </div>
  </div>
{render_adr(data.get("adr"))}

  <div class="bottom">
    <div class="vlabel">Bottom line</div>
    {escape(data["bottom_line"])}
  </div>

  <footer>Generated by the LLM Council tool · 5 debaters + 1 judge · grounded in <code>{escape(data["footer_codebase"])}</code></footer>

</div>
<script>
{script}
</script>
</body>
</html>
"""


def validate_input_data(data: dict) -> None:
    required = [
        "title",
        "subtitle",
        "topic",
        "naive",
        "context",
        "round1",
        "peer_rating",
        "round2",
        "round3",
        "evolution",
        "final_verdict",
        "stance_buckets",
        "bottom_line",
        "footer_codebase",
    ]
    for key in required:
        if key not in data:
            raise ValueError(f"missing required field: {key}")

    if len(data["round1"]) != 5 or len(data["round2"]) != 5 or len(data["round3"]) != 5:
        raise ValueError("round1, round2, and round3 must each contain exactly 5 turns")
    if len(data["stance_buckets"]) < 2:
        raise ValueError("stance_buckets must contain at least two buckets")
    stance_keys = {item["key"] for item in data["stance_buckets"]}
    if len(data["evolution"]["rows"]) != 5:
        raise ValueError("evolution.rows must contain exactly 5 personas")
    for row in data["evolution"]["rows"]:
        persona_info(row["persona_id"], row.get("display_name"))
        if len(row["rounds"]) != 3:
            raise ValueError("each evolution row must contain exactly 3 rounds")
        for item in row["rounds"]:
            if item["stance"] not in stance_keys:
                raise ValueError(f"unknown stance bucket in evolution: {item['stance']}")
    for round_name in ("round1", "round2", "round3"):
        for turn in data[round_name]:
            persona_info(turn["persona_id"], turn.get("display_name"))
    if len(data["peer_rating"]["positions"]) != 5:
        raise ValueError("peer_rating.positions must contain exactly 5 items")
    if len(data["peer_rating"]["ratings"]) != 5:
        raise ValueError("peer_rating.ratings must contain exactly 5 raters")
    if len(data["peer_rating"]["averages"]) != 5:
        raise ValueError("peer_rating.averages must contain exactly 5 values")
    if len(data["peer_rating"]["ranking"]) != 5:
        raise ValueError("peer_rating.ranking must contain exactly 5 values")
    for position in data["peer_rating"]["positions"]:
        persona_info(position["persona_id"], position.get("display_name"))
    for row in data["peer_rating"]["ratings"]:
        persona_info(row["persona_id"], row.get("display_name"))
        if len(row["cells"]) != 5:
            raise ValueError("each peer_rating row must contain exactly 5 cells")
        for cell in row["cells"]:
            if cell.get("self"):
                continue
            if not 1 <= cell["score"] <= 10:
                raise ValueError("peer_rating scores must be between 1 and 10")
    if len(data["final_verdict"]["next_actions"]) != 3:
        raise ValueError("final_verdict.next_actions must contain exactly 3 items")
    score = data["final_verdict"]["confidence"]["score"]
    if not 0 <= score <= 100:
        raise ValueError("final_verdict.confidence.score must be between 0 and 100")

    position_ids = [item["id"] for item in data["peer_rating"]["positions"]]
    average_ids = [item["position_id"] for item in data["peer_rating"]["averages"]]
    if position_ids != average_ids:
        raise ValueError("peer_rating.averages must follow the same position order as peer_rating.positions")
    ranking_ids = {item["position_id"] for item in data["peer_rating"]["ranking"]}
    if ranking_ids - set(position_ids):
        raise ValueError("peer_rating.ranking contains unknown position ids")


def validate_html_text(text: str) -> list[str]:
    errors = []
    required_substrings = [
        'class="naive"',
        'class="naive-label"',
        'class="naive-risk"',
        'class="rate-table"',
        'class="evo"',
        'class="rank"',
        'class="gauge"',
        'class="val"',
        'class="turn"',
        'class="pverdict"',
    ]
    for item in required_substrings:
        if item not in text:
            errors.append(f"missing required markup: {item}")

    if "<link " in text:
        errors.append("external <link> tags are not allowed in self-contained output")
    if re.search(r"<script[^>]+src=", text):
        errors.append("external <script src=...> tags are not allowed in self-contained output")
    if not re.search(r'td data-score="(?:[1-9]|10)"', text):
        errors.append("peer-rating cells with data-score are missing")
    if 'td class="self"' not in text:
        errors.append("self-rated peer cells are missing")
    if not re.search(r'class="chip" data-stance="[^"]+"', text):
        errors.append("stance chips with data-stance are missing")
    if not re.search(r'class="bar [^"]*" style="--score:[^"]+"', text):
        errors.append("ranking bars with --score are missing")
    if not re.search(r'class="gauge" data-confidence="(?:100|[1-9]?\d)"', text):
        errors.append("confidence gauge with data-confidence is missing")

    return errors


def cmd_render(args: argparse.Namespace) -> int:
    data = read_json(Path(args.input))
    html = render_html(data)
    output = Path(args.output) if args.output else DEFAULT_OUTPUT_DIR / f"{slugify(data['title'])}.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html)
    errors = validate_html_text(html)
    if errors:
        print("rendered HTML failed contract validation:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(output)
    return 0


def cmd_render_markdown(args: argparse.Namespace) -> int:
    data = read_json(Path(args.input))
    markdown = render_markdown(data)
    if args.output:
        Path(args.output).write_text(markdown)
        print(args.output)
    else:
        print(markdown, end="")
    return 0


def cmd_validate_input(args: argparse.Namespace) -> int:
    data = read_json(Path(args.input))
    try:
        validate_input_data(data)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("input OK")
    return 0


def cmd_validate_html(args: argparse.Namespace) -> int:
    text = Path(args.input).read_text()
    errors = validate_html_text(text)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("html OK")
    return 0


def cmd_validate_artifacts(args: argparse.Namespace) -> int:
    errors = []
    examples_dir = ROOT / "examples"
    output_dir = ROOT / "llm-council-output"

    json_paths = sorted(examples_dir.glob("*.json"))
    html_paths = sorted(output_dir.glob("*.html"))

    if not json_paths:
        errors.append(f"no example JSON files found in {examples_dir}")
    if not html_paths:
        errors.append(f"no HTML artifacts found in {output_dir}")

    for path in json_paths:
        try:
            validate_input_data(read_json(path))
            print(f"input OK: {path.relative_to(ROOT)}")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")

    for path in html_paths:
        try:
            html_errors = validate_html_text(path.read_text())
        except OSError as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue
        if html_errors:
            errors.extend(f"{path.relative_to(ROOT)}: {error}" for error in html_errors)
        else:
            print(f"html OK: {path.relative_to(ROOT)}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"artifact set OK: {len(json_paths)} input(s), {len(html_paths)} HTML artifact(s)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    render = sub.add_parser("render", help="render council JSON to self-contained HTML")
    render.add_argument("input", help="path to structured council JSON")
    render.add_argument("--output", help="output HTML path")
    render.set_defaults(func=cmd_render)

    render_md = sub.add_parser("render-markdown", help="render council JSON to Markdown")
    render_md.add_argument("input", help="path to structured council JSON")
    render_md.add_argument("--output", help="output Markdown path")
    render_md.set_defaults(func=cmd_render_markdown)

    validate_input = sub.add_parser("validate-input", help="validate council JSON")
    validate_input.add_argument("input", help="path to structured council JSON")
    validate_input.set_defaults(func=cmd_validate_input)

    validate_html = sub.add_parser("validate-html", help="validate rendered council HTML")
    validate_html.add_argument("input", help="path to rendered HTML file")
    validate_html.set_defaults(func=cmd_validate_html)

    validate_artifacts = sub.add_parser(
        "validate-artifacts",
        help="validate every example JSON file and committed HTML artifact",
    )
    validate_artifacts.set_defaults(func=cmd_validate_artifacts)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
