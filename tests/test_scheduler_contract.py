from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"
DATA_WORKFLOWS = (
    "owner-alerts.yml",
    "refresh-all-data.yml",
    "update-catalog.yml",
    "update-ephemeris.yml",
    "update-field-guide.yml",
    "update-insights.yml",
    "update-snapshot.yml",
)
APP_DATA_WORKFLOWS = (
    "update-ephemeris.yml",
    "update-field-guide.yml",
)
MIRROR_DATA_WORKFLOWS = tuple(
    name for name in DATA_WORKFLOWS if name not in APP_DATA_WORKFLOWS
)


class SchedulerContractTests(unittest.TestCase):
    def test_public_workflows_never_run_pull_request_code(self) -> None:
        for path in WORKFLOW_DIR.glob("*.yml"):
            with self.subTest(workflow=path.name):
                source = path.read_text()
                self.assertNotIn("pull_request:", source)
                self.assertIn("runs-on: ubuntu-latest", source)

    def test_private_source_checkout_is_read_only_and_sha_pinned(self) -> None:
        for name in MIRROR_DATA_WORKFLOWS:
            path = WORKFLOW_DIR / name
            with self.subTest(workflow=path.name):
                source = path.read_text()
                self.assertIn("repository: SamueleMarcucci/satellite-catalog-mirror", source)
                self.assertIn("ssh-key: ${{ secrets.MIRROR_DEPLOY_KEY }}", source)
                self.assertIn("persist-credentials: false", source)
                self.assertIn("actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803", source)

    def test_app_pipeline_checkouts_are_read_only_and_sha_pinned(self) -> None:
        for name in APP_DATA_WORKFLOWS:
            path = WORKFLOW_DIR / name
            with self.subTest(workflow=path.name):
                source = path.read_text()
                self.assertIn("repository: SamueleMarcucci/live-orbit-app-backup", source)
                self.assertIn("ssh-key: ${{ secrets.APP_DEPLOY_KEY }}", source)
                self.assertIn("persist-credentials: false", source)
                self.assertIn("actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803", source)

    def test_keepalive_cannot_receive_pipeline_secrets(self) -> None:
        source = (WORKFLOW_DIR / "scheduler-keepalive.yml").read_text()
        self.assertNotIn("secrets.", source)
        self.assertNotIn("satellite-catalog-mirror", source)
        self.assertIn("contents: write", source)

    def test_intended_cadences_are_preserved(self) -> None:
        self.assertIn('cron: "2-59/5 * * * *"', (WORKFLOW_DIR / "update-snapshot.yml").read_text())
        self.assertIn('cron: "17 * * * *"', (WORKFLOW_DIR / "update-catalog.yml").read_text())
        self.assertIn('cron: "4-59/5 * * * *"', (WORKFLOW_DIR / "update-ephemeris.yml").read_text())
        self.assertIn('cron: "17 */6 * * *"', (WORKFLOW_DIR / "update-field-guide.yml").read_text())
        self.assertIn('cron: "29 * * * *"', (WORKFLOW_DIR / "update-insights.yml").read_text())

    def test_private_pipeline_output_is_suppressed_in_public_logs(self) -> None:
        for name in DATA_WORKFLOWS:
            path = WORKFLOW_DIR / name
            with self.subTest(workflow=path.name):
                source = path.read_text()
                self.assertIn('private pipeline output suppressed', source)
                self.assertRegex(source, r'>"\$RUNNER_TEMP/[^"\n]+\.log" 2>&1')

    def test_public_repository_contains_no_high_confidence_secret_material(self) -> None:
        secret_patterns = {
            "private key": re.compile(r"-----BEGIN (?:OPENSSH|RSA|EC|DSA|PGP) PRIVATE KEY-----"),
            "GitHub token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"),
            "GitHub fine-grained token": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
            "Slack webhook": re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/_-]+"),
            "credential-bearing URL": re.compile(r"https?://[^\s/:]+:[^\s/@]+@"),
        }
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
                continue
            source = path.read_text(errors="ignore")
            for label, pattern in secret_patterns.items():
                with self.subTest(path=path.relative_to(ROOT), secret_type=label):
                    self.assertIsNone(pattern.search(source))

    def test_security_contract_workflow_has_no_pipeline_secrets(self) -> None:
        source = (WORKFLOW_DIR / "security-contract.yml").read_text()
        self.assertNotIn("secrets.", source)
        self.assertNotIn("satellite-catalog-mirror", source)
        self.assertIn("python -m unittest discover -s tests -v", source)


if __name__ == "__main__":
    unittest.main()
