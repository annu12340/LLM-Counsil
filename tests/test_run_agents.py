import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))
import run_agents  # noqa: E402


class TextBlock:
    def __init__(self, text):
        self.text = text


class Message:
    def __init__(self, payload):
        self.content = [TextBlock(json.dumps(payload))]


class FakeMessages:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        system = kwargs["system"]
        prompt = kwargs["messages"][0]["content"]
        agent_id = re.search(r"Agent ID: ([^\n]+)", system).group(1)

        if agent_id == "naive_baseline":
            return Message(
                {
                    "answer": "A one-shot model would say it depends on replay and operations.",
                    "risk": "It hedges and does not commit to an ADR-ready tradeoff.",
                }
            )

        if agent_id == "judge_synthesizer":
            return Message(final_judge_payload())

        if "Round 1 - Opening Positions" in prompt:
            return Message(
                {
                    "text": f"{agent_id} opening argument for an ADR-ready decision.",
                    "verdict": "RabbitMQ now with a Kafka trigger.",
                }
            )

        if "Round 1.5 - Peer Rating" in prompt:
            own = re.search(r"Your own Position ID: ([A-E])", prompt).group(1)
            cells = []
            for position_id in ["A", "B", "C", "D", "E"]:
                if position_id == own:
                    cells.append({"position_id": position_id, "self": True})
                else:
                    cells.append(
                        {
                            "position_id": position_id,
                            "score": 8,
                            "note": "clear and useful",
                        }
                    )
            return Message({"cells": cells})

        if "Round 2 - Challenges" in prompt:
            return Message(
                {
                    "target": "Systems Engineer",
                    "text": f"{agent_id} challenges a hidden operational assumption.",
                    "verdict": "Keep the migration trigger explicit.",
                }
            )

        if "Round 3 - Rebuttals" in prompt:
            return Message(
                {
                    "text": f"{agent_id} rebuts and preserves the conditional recommendation.",
                    "verdict": "RabbitMQ now with a written Kafka trigger.",
                }
            )

        raise AssertionError(f"unexpected prompt for {agent_id}: {prompt[:120]}")


class FakeClient:
    def __init__(self):
        self.messages = FakeMessages()


def final_judge_payload():
    rows = []
    for persona_id in ["first_principles", "research", "systems", "skeptic", "product"]:
        rows.append(
            {
                "persona_id": persona_id,
                "rounds": [
                    {"stance": "rabbit", "label": "RabbitMQ"},
                    {"stance": "rabbit", "label": "RabbitMQ"},
                    {"stance": "rabbit", "label": "RabbitMQ"},
                ],
                "final_stance": "RabbitMQ now with a Kafka trigger",
            }
        )

    return {
        "title": "Kafka vs RabbitMQ ADR",
        "subtitle": "A multi-agent council verdict for an engineering decision.",
        "context": {
            "paragraphs": ["The team needs an ADR-ready broker decision."],
            "criteria": [
                {"label": "1. Replay", "text": "whether durable replay is contractual"},
                {"label": "2. Operations", "text": "whether the team can run the system"},
            ],
            "assumption": "Replay is useful but not yet contractual.",
        },
        "stance_buckets": [
            {"key": "rabbit", "tone": "good"},
            {"key": "kafka", "tone": "accent"},
            {"key": "undecided", "tone": "muted"},
        ],
        "evolution": {
            "summary": "The council converged on RabbitMQ with a written Kafka trigger.",
            "rows": rows,
        },
        "final_verdict": {
            "best_argument": "The operations constraint was decisive.",
            "biggest_risk": "A vague replay requirement can create future migration pressure.",
            "key_tradeoff": "RabbitMQ simplicity versus Kafka replay.",
            "consensus": "Use the simpler broker until replay becomes contractual.",
            "recommendation": "Use RabbitMQ now and document the Kafka migration trigger in the ADR.",
            "confidence": {
                "level": "medium-high",
                "label": "MEDIUM-HIGH",
                "pill_class": "med",
                "score": 82,
                "text": "The decision fits the stated constraints.",
            },
            "next_actions": [
                "Write the ADR.",
                "Define the replay trigger.",
                "Instrument consumer lag and replay requests.",
            ],
        },
        "adr": {
            "status": "proposed",
            "decision": "Use RabbitMQ now with a Kafka trigger.",
            "consequences": "Lower operational load now; possible migration later.",
        },
        "bottom_line": "Use RabbitMQ now, with an explicit Kafka trigger.",
        "footer_codebase": "standalone ADR decision",
    }


class RunAgentsTest(unittest.TestCase):
    def test_agents_yaml_runner_gates_judge_until_final_round(self):
        client = FakeClient()

        data, calls = run_agents.run_agents(
            "Kafka vs RabbitMQ for the event pipeline ADR",
            context="10k events/sec, small ops team",
            depth="quick",
            model="test-model",
            max_tokens=999,
            client=client,
        )

        self.assertEqual(data["title"], "Kafka vs RabbitMQ ADR")
        self.assertEqual(len(calls), 22)
        self.assertEqual(calls[0]["agent_id"], "naive_baseline")
        self.assertEqual(calls[-1]["agent_id"], "judge_synthesizer")
        self.assertNotIn("judge_synthesizer", [call["agent_id"] for call in calls[:-1]])

        round_counts = {}
        for call in calls:
            round_counts[call["round"]] = round_counts.get(call["round"], 0) + 1
        self.assertEqual(round_counts, {0: 1, 1: 5, 1.5: 5, 2: 5, 3: 5, 4: 1})

        for api_call in client.messages.calls:
            self.assertEqual(api_call["model"], "test-model")
            self.assertEqual(api_call["max_tokens"], 999)
        judge_api_indices = [
            index
            for index, api_call in enumerate(client.messages.calls)
            if "Agent ID: judge_synthesizer" in api_call["system"]
        ]
        self.assertEqual(judge_api_indices, [21])

        self.assertEqual(
            [item["score"] for item in data["peer_rating"]["averages"]],
            [8.0, 8.0, 8.0, 8.0, 8.0],
        )


if __name__ == "__main__":
    unittest.main()
