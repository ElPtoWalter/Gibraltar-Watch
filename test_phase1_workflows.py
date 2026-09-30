import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WORKFLOWS = ROOT / ".github" / "workflows"


def workflow(name):
    return (WORKFLOWS / name).read_text(encoding="utf-8")


class PhaseOneWorkflowTests(unittest.TestCase):
    def test_hourly_monitor_does_not_publish_editorial_products(self):
        text = workflow("update-gibraltar.yml")
        self.assertIn("update_geopolitics.py", text)
        self.assertIn("build_events.py", text)
        self.assertIn("update_observatory.py", text)
        self.assertNotIn("generate_diario_estrecho.py", text)
        self.assertNotIn("generate_newsletter.py", text)
        self.assertNotIn("unittest", text)
        self.assertNotIn("build_secure_public_site.py", text)

    def test_hourly_monitor_rebuilds_manifest_before_validation(self):
        text = workflow("update-gibraltar.yml")
        self.assertEqual(text.count("python build_publication_manifest.py"), 1)
        self.assertLess(text.index("python update_observatory.py"), text.index("python build_publication_manifest.py"))
        self.assertLess(text.index("python build_publication_manifest.py"), text.index("python validate_gibraltar.py"))

    def test_daily_newsroom_owns_diary_and_newsletter(self):
        text = workflow("diario-gibraltar.yml")
        self.assertIn("generate_diario_estrecho.py", text)
        self.assertIn("generate_newsletter.py", text)
        self.assertIn("GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}", text)
        self.assertIn("OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}", text)

    def test_ci_owns_full_tests_and_public_artifact_audit(self):
        text = workflow("phase1-newsroom-ci.yml")
        self.assertIn("python -m unittest discover -v", text)
        self.assertIn("build_secure_public_site.py", text)
        self.assertIn("audit_public_artifact.py", text)
        self.assertIn("check_public_links.py _site", text)
        self.assertIn("PHASE2_VIDEO_CONTRACT.md", text)

    def test_monitor_and_diary_dispatch_one_deploy_only_after_change(self):
        for name in ("update-gibraltar.yml", "diario-gibraltar.yml"):
            text = workflow(name)
            self.assertEqual(text.count("gh workflow run deploy-gibraltar-secure.yml"), 1)
            self.assertRegex(text, r"if: steps\.commit\.outputs\.changed == 'true'[\s\S]+gh workflow run deploy-gibraltar-secure\.yml")
        deploy = workflow("deploy-gibraltar-secure.yml")
        self.assertNotIn("workflow_run:", deploy)
        self.assertNotIn("git commit", deploy)

    def test_workflows_do_not_echo_secrets_or_enable_shell_tracing(self):
        for path in WORKFLOWS.glob("*.yml"):
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"echo\s+.*secrets\.")
            self.assertNotRegex(text, r"(?m)^\s*set\s+-x\s*$")

    def test_pilot_is_pr_scoped_read_only_and_non_publishing(self):
        text = workflow("pilot-gemini-phase1.yml")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("pull_request:", text)
        self.assertIn("branches: [codex/phase1-closure-gibraltar]", text)
        self.assertIn("github.event_name == 'push'", text)
        self.assertIn("head.repo.full_name == github.repository", text)
        self.assertIn("contents: read", text)
        self.assertNotIn("git push", text)
        self.assertNotIn("deploy-pages", text)
        self.assertNotIn("IndexNow", text)
        self.assertIn("types: [opened, reopened]", text)


if __name__ == "__main__":
    unittest.main()
