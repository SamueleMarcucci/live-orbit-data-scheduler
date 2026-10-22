import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


SOURCE = (Path(__file__).resolve().parents[1] / ".github/workflows/update-ephemeris.yml").read_text()


def step(name):
    return SOURCE.split("      - name: " + name + "\n", 1)[1].split("\n      - name:", 1)[0]


class EphemerisWorkflowTests(unittest.TestCase):
    def test_only_explicit_guard_authorization_can_publish(self):
        guard = step("Guard against an active or cooling-down ephemeris writer")
        self.assertIn("id: publication_guard", guard)
        self.assertIn("--skip-if-blocked", guard)
        publish = step("Build and publish ephemeris snapshot")
        self.assertIn("if: steps.publication_guard.outputs.publication_allowed == 'true'", publish)
        self.assertIn('--diagnostic-file "$RUNNER_TEMP/ephemeris-diagnostic.json"', publish)

    def test_guard_shell_accepts_expected_skip_and_propagates_lookup_errors(self):
        script = textwrap.dedent(step("Guard against an active or cooling-down ephemeris writer").split("        run: |\n", 1)[1])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            python = root / "python"
            python.write_text('#!/bin/sh\nprintf "publication_allowed=%s\\n" "$TEST_ALLOWED" >> "$GITHUB_OUTPUT"\nprintf "private detail\\n"\nexit "$TEST_STATUS"\n')
            python.chmod(0o700)
            for allowed, status in (("false", "0"), ("true", "0"), ("false", "1")):
                with self.subTest(allowed=allowed, status=status):
                    output = root / "output"
                    output.write_text("")
                    env = {**os.environ, "PATH": directory + os.pathsep + os.environ["PATH"],
                           "RUNNER_TEMP": directory, "GITHUB_OUTPUT": str(output),
                           "TEST_ALLOWED": allowed, "TEST_STATUS": status}
                    result = subprocess.run(["bash", "-e", "-o", "pipefail", "-c", script], env=env, capture_output=True, text=True)
                    self.assertEqual(result.returncode, int(status))
                    self.assertEqual(output.read_text(), f"publication_allowed={allowed}\n")
                    self.assertNotIn("private detail", result.stdout + result.stderr)

    def test_diagnostic_report_never_prints_private_refresh_log(self):
        report = step("Report safe ephemeris diagnostics")
        self.assertIn("always() && steps.publication_guard.outputs.publication_allowed == 'true'", report)
        script = textwrap.dedent(report.split("        run: |\n", 1)[1])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ephemeris-refresh.log").write_text("private detail")
            (root / "ephemeris-diagnostic.json").write_text('{"stage":"validate","failure_category":"RuntimeError"}\n')
            result = subprocess.run(["bash", "-e", "-c", script], env={**os.environ, "RUNNER_TEMP": directory}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertIn('"stage":"validate"', result.stdout)
            self.assertNotIn("private detail", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
