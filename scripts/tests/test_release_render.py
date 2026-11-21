import json
import unittest
from unittest.mock import MagicMock, patch

from scripts.release_render import (
    ReleaseRenderError,
    _service,
    deploy_image,
    verify_current_provider,
)


IMAGE = "ghcr.io/kendshhh/phishlens-api"
SERVICE = {
    "id": "srv-staging-123456",
    "type": "web_service",
    "imagePath": IMAGE,
    "autoDeployTrigger": "off",
}
IMAGE_REF = IMAGE + "@sha256:" + "a" * 64


class ReleaseRenderTests(unittest.TestCase):
    def test_image_service_is_allowed_but_git_service_is_not(self):
        with patch("scripts.release_render.api_request", return_value=dict(SERVICE)):
            self.assertEqual(_service(SERVICE["id"], IMAGE)["id"], SERVICE["id"])
        with patch("scripts.release_render.api_request", return_value=dict(SERVICE, buildSourceId="src-main")):
            with self.assertRaisesRegex(ReleaseRenderError, "Git-backed"):
                _service(SERVICE["id"], IMAGE)
        with patch("scripts.release_render.api_request", return_value=dict(SERVICE, imagePath="ghcr.io/other/app")):
            with self.assertRaisesRegex(ReleaseRenderError, "repository"):
                _service(SERVICE["id"], IMAGE)

    def test_deploy_requires_render_to_report_the_same_digest(self):
        deployment = {"id": "dep-release-1", "status": "live",
                      "image": {"ref": IMAGE_REF, "sha": "sha256:" + "a" * 64}}
        with patch("scripts.release_render._service", return_value=SERVICE), \
             patch("scripts.release_render.api_request", return_value=deployment), \
             patch("scripts.release_render.verify_health", return_value={"status": "passed"}):
            result = deploy_image(
                SERVICE["id"], IMAGE_REF, expected_image=IMAGE,
                base_url="https://phishlens-staging.onrender.com", environment="staging",
                source_sha="b" * 40, provider="tfidf", model_revision="c" * 64,
            )
        self.assertEqual(result["image"]["ref"], IMAGE_REF)

        wrong = dict(deployment, image={"ref": IMAGE_REF, "sha": "sha256:" + "d" * 64})
        with patch("scripts.release_render._service", return_value=SERVICE), \
             patch("scripts.release_render.api_request", return_value=wrong):
            with self.assertRaisesRegex(ReleaseRenderError, "resolved image digest"):
                deploy_image(
                    SERVICE["id"], IMAGE_REF, expected_image=IMAGE,
                    base_url="https://phishlens-staging.onrender.com", environment="staging",
                    source_sha="b" * 40, provider="tfidf", model_revision="c" * 64,
                )

    def test_provider_preflight_is_read_only_exact_and_refuses_disabled(self):
        response = MagicMock()
        response.status = 200
        response.read.return_value = json.dumps({"provider_mode": "gemini", "model": "gemini-2.5-flash-001"}).encode()
        response.__enter__.return_value = response
        with patch("scripts.release_render.urlopen", return_value=response) as request:
            result = verify_current_provider(
                "https://phishlens-api-ocvt.onrender.com", environment="production",
                expected_provider="gemini", expected_model_revision="gemini-2.5-flash-001",
            )
        self.assertEqual(result["revision"], "gemini-2.5-flash-001")
        self.assertEqual(request.call_args.args[0].full_url,
                         "https://phishlens-api-ocvt.onrender.com/model-info")
        response.read.return_value = b'{"provider_mode":"disabled"}'
        with patch("scripts.release_render.urlopen", return_value=response):
            with self.assertRaisesRegex(ReleaseRenderError, "disabled"):
                verify_current_provider(
                    "https://phishlens-api-ocvt.onrender.com", environment="production",
                    expected_provider="gemini", expected_model_revision="gemini-2.5-flash-001",
                )
        with self.assertRaisesRegex(ReleaseRenderError, "restricted"):
            verify_current_provider(
                "https://example.test", environment="production",
                expected_provider="gemini", expected_model_revision="x",
            )


if __name__ == "__main__":
    unittest.main()
