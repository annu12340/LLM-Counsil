import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run-demo.sh"


class DemoScriptTest(unittest.TestCase):
    def test_demo_script_runs(self):
        result = subprocess.run(
            ["bash", str(SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Demo artifact ready:", result.stdout)


if __name__ == "__main__":
    unittest.main()
