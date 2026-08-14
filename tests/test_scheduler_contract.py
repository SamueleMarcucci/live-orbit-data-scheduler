from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"


class SchedulerContractTests(unittest.TestCase):
    def test_public_workflows_never_run_pull_request_code(self) -> None:
        for path in WORKFLOW_DIR.glob("*.yml"):
            with self.subTest(workflow=path.name):
                source = path.read_text()
                self.assertNotIn("pull_request:", source)
                self.assertIn("runs-on: ubuntu-latest", source)

    def test_private_source_checkout_is_read_only_and_sha_pinned(self) -> None:
        for path in WORKFLOW_DIR.glob("*.yml"):
            with self.subTest(workflow=path.name):
                source = path.read_text()
                self.assertIn("repository: SamueleMarcucci/satellite-catalog-mirror", source)
                self.assertIn("ssh-key: ${{ secrets.MIRROR_DEPLOY_KEY }}", source)
                self.assertIn("persist-credentials: false", source)
                self.assertIn("actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803", source)

    def test_intended_cadences_are_preserved(self) -> None:
        self.assertIn('cron: "2-59/5 * * * *"', (WORKFLOW_DIR / "update-snapshot.yml").read_text())
        self.assertIn('cron: "17 * * * *"', (WORKFLOW_DIR / "update-catalog.yml").read_text())
        self.assertIn('cron: "29 * * * *"', (WORKFLOW_DIR / "update-insights.yml").read_text())


if __name__ == "__main__":
    unittest.main()
