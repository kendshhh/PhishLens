"""Keep the post-deploy observer out of Render's pre-deploy check gate."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ProductionWorkflowTests(unittest.TestCase):
    def test_observer_is_manual_post_deploy_only(self):
        workflow = (ROOT / ".github/workflows/secretary-production.yml").read_text()
        triggers = workflow.split("permissions:", 1)[0]
        self.assertIn("workflow_dispatch:", triggers)
        self.assertNotIn("workflow_run:", triggers)
        self.assertNotIn("schedule:", triggers)


if __name__ == "__main__":
    unittest.main()
