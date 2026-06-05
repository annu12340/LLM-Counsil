import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SAMPLE = ROOT / "examples" / "sequential-vs-random-codes.json"

sys.path.insert(0, str(SCRIPTS))
import run_debate  # noqa: E402


class TextBlock:
    def __init__(self, text):
        self.text = text


class Message:
    def __init__(self, text):
        self.content = [TextBlock(text)]


class FakeMessages:
    def __init__(self, payload):
        self.payload = payload
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return Message("```json\n" + json.dumps(self.payload) + "\n```")


class FakeClient:
    def __init__(self, payload):
        self.messages = FakeMessages(payload)


class RunDebateTest(unittest.TestCase):
    def test_run_debate_uses_configurable_model_and_validates_model_json(self):
        payload = json.loads(SAMPLE.read_text())
        client = FakeClient(payload)

        data = run_debate.run_debate(
            "Kafka vs RabbitMQ",
            context="10k events/sec, small ops team",
            depth="quick",
            model="test-model",
            max_tokens=1234,
            client=client,
        )

        self.assertEqual(data["title"], payload["title"])
        self.assertEqual(client.messages.kwargs["model"], "test-model")
        self.assertEqual(client.messages.kwargs["max_tokens"], 1234)
        user_message = client.messages.kwargs["messages"][0]["content"]
        self.assertIn("Return ONLY valid JSON", user_message)
        self.assertIn("Context: 10k events/sec, small ops team", user_message)

    def test_write_artifacts_outputs_markdown_json_and_valid_html(self):
        payload = json.loads(SAMPLE.read_text())

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            markdown_path = out_dir / "debate.md"
            html_path = out_dir / "debate.html"
            json_path = out_dir / "debate.json"

            markdown, written_html, written_json = run_debate.write_artifacts(
                payload,
                output=str(markdown_path),
                html_output=str(html_path),
                json_output=str(json_path),
            )

            self.assertEqual(written_html, html_path)
            self.assertEqual(written_json, json_path)
            self.assertIn("# LLM Council Debate", markdown)
            self.assertIn("## Naive Single-Model Take", markdown_path.read_text())
            html = html_path.read_text()
            self.assertIn('class="naive"', html)
            self.assertIn('class="gauge"', html)
            self.assertNotIn("<link ", html)
            self.assertEqual(json.loads(json_path.read_text())["title"], payload["title"])


if __name__ == "__main__":
    unittest.main()
