import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "council_tool.py"
SAMPLE = ROOT / "examples" / "sequential-vs-random-codes.json"


class CouncilToolTest(unittest.TestCase):
    def test_validate_input_sample(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "validate-input", str(SAMPLE)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("input OK", result.stdout)

    def test_render_and_validate_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "sample.html"
            render = subprocess.run(
                [sys.executable, str(SCRIPT), "render", str(SAMPLE), "--output", str(output)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(render.returncode, 0, render.stderr)
            self.assertTrue(output.exists())

            validate = subprocess.run(
                [sys.executable, str(SCRIPT), "validate-html", str(output)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(validate.returncode, 0, validate.stderr)
            self.assertIn("html OK", validate.stdout)


if __name__ == "__main__":
    unittest.main()
