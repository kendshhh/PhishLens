"""Fail-closed Render checks and image-digest promotion for release candidates."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


API = "https://api.render.com/v1"
TERMINAL_FAILURES = {"build_failed", "update_failed", "canceled", "deactivated", "pre_deploy_failed"}
TERMINAL_SUCCESS = {"live"}


class ReleaseRenderError(RuntimeError):
    pass


def api_request(method: str, path: str, payload: dict | None = None) -> dict | list:
    token = os.environ.get("RENDER_API_KEY", "")
    if not token:
        raise ReleaseRenderError("Render API credential is not configured")
    data = None if payload is None else json.dumps(payload).encode()
    request = Request(API + path, data=data, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    })
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read())
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        raise ReleaseRenderError("Render API request failed; response details were suppressed") from None


def _service(service_id: str, expected_image: str) -> dict:
    service = api_request("GET", f"/services/{service_id}")
    if not isinstance(service, dict) or service.get("id") != service_id:
        raise ReleaseRenderError("Render service identity could not be verified")
    if service.get("buildSourceId"):
        raise ReleaseRenderError("Render service is Git-backed; immutable image promotion is required")
    image_path = service.get("imagePath")
    if not isinstance(image_path, str):
        raise ReleaseRenderError("Render service is not configured with a prebuilt image")
    # Prebuilt-image services are manually deployed and Render documents the
    # Git autoDeploy fields as inapplicable to them. Reject an unexpected Git
    # trigger if one is returned, while allowing a missing/deprecated field.
    if service.get("autoDeployTrigger") not in (None, "off"):
        raise ReleaseRenderError("Render image service reports a Git auto-deploy trigger")
    configured = image_path.split("@", 1)[0].split(":", 1)[0].lower()
    expected = expected_image.split("@", 1)[0].split(":", 1)[0].lower()
    if configured != expected:
        raise ReleaseRenderError("Render image repository does not match the candidate repository")
    if service.get("type") not in {"web_service", "private_service"}:
        raise ReleaseRenderError("Render promotion target is not a web service")
    return service


def verify_health(base_url: str, *, environment: str, source_sha: str,
                  expected_provider: str, expected_model_revision: str) -> dict:
    expected_origin = {
        "staging": "https://phishlens-staging.onrender.com",
        "production": "https://phishlens-api-ocvt.onrender.com",
    }.get(environment)
    if base_url != expected_origin:
        raise ReleaseRenderError("Release verification is restricted to the named PhishLens origin")
    observed = {}
    for route in ("version", "health", "ready", "model-info"):
        request = Request(base_url + "/" + route, headers={"Accept": "application/json", "Cache-Control": "no-cache"})
        try:
            with urlopen(request, timeout=20) as response:
                if response.status != 200:
                    raise ReleaseRenderError(f"Post-deploy {route} check failed")
                observed[route] = json.loads(response.read())
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            raise ReleaseRenderError(f"Post-deploy {route} check failed") from None
    if observed["version"].get("environment") != environment or observed["version"].get("commit") != source_sha:
        raise ReleaseRenderError("Post-deploy version identity does not match the candidate SHA")
    if observed["health"].get("status") != "ok":
        raise ReleaseRenderError("Post-deploy health check failed")
    if observed["ready"].get("status") != "ready" or observed["ready"].get("database") != "connected":
        raise ReleaseRenderError("Post-deploy readiness check failed")
    model = observed["model-info"]
    if (model.get("provider_mode") != expected_provider
            or model.get("provider_mode") in {"disabled", "unavailable", "mock"}):
        raise ReleaseRenderError("Post-deploy model/provider identity does not match approved evidence")
    revision = model.get("model_sha256") or model.get("model_revision") or model.get("model")
    if revision != expected_model_revision:
        raise ReleaseRenderError("Post-deploy model revision does not match approved evidence")
    return {
        "version": observed["version"],
        "health": {"status": observed["health"]["status"]},
        "ready": observed["ready"],
        "model_info": {"provider_mode": model["provider_mode"], "revision": revision},
    }


def verify_current_provider(base_url: str, *, environment: str,
                            expected_provider: str, expected_model_revision: str) -> dict:
    """Read only public model identity before production deployment."""
    expected_origin = {
        "staging": "https://phishlens-staging.onrender.com",
        "production": "https://phishlens-api-ocvt.onrender.com",
    }.get(environment)
    if base_url != expected_origin:
        raise ReleaseRenderError("Provider preflight is restricted to the named PhishLens origin")
    request = Request(base_url + "/model-info", headers={"Accept": "application/json", "Cache-Control": "no-cache"})
    try:
        with urlopen(request, timeout=20) as response:
            if response.status != 200:
                raise ReleaseRenderError("Current provider preflight failed")
            model = json.loads(response.read())
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        raise ReleaseRenderError("Current provider preflight failed") from None
    provider = model.get("provider_mode")
    revision = model.get("model_sha256") or model.get("model_revision") or model.get("model")
    if (provider != expected_provider or provider in {"disabled", "unavailable", "mock"}
            or revision != expected_model_revision):
        raise ReleaseRenderError("Current provider is disabled or differs from approved model identity")
    return {"provider": provider, "revision": revision}


def deploy_image(service_id: str, image_ref: str, *, expected_image: str,
                 base_url: str, environment: str, source_sha: str,
                 provider: str, model_revision: str, timeout: int = 1200) -> dict:
    if not re.fullmatch(r"[^\s]+@sha256:[0-9a-f]{64}", image_ref or ""):
        raise ReleaseRenderError("Render image reference must use an immutable SHA-256 digest")
    _service(service_id, expected_image)
    started = api_request("POST", f"/services/{service_id}/deploys", {"imageUrl": image_ref})
    deploy_id = started.get("id") if isinstance(started, dict) else None
    if not isinstance(deploy_id, str) or not deploy_id:
        raise ReleaseRenderError("Render did not return a deployment identity")
    deadline = time.monotonic() + timeout
    deploy = started
    while time.monotonic() < deadline:
        status = deploy.get("status")
        if status in TERMINAL_FAILURES:
            raise ReleaseRenderError(f"Render image deployment failed with status {status}")
        if status in TERMINAL_SUCCESS:
            break
        time.sleep(5)
        deploy = api_request("GET", f"/services/{service_id}/deploys/{deploy_id}")
        if not isinstance(deploy, dict):
            raise ReleaseRenderError("Render deployment response is malformed")
    else:
        raise ReleaseRenderError("Render image deployment timed out")

    image = deploy.get("image")
    if not isinstance(image, dict) or image.get("ref") != image_ref:
        raise ReleaseRenderError("Render live deployment does not report the requested immutable image reference")
    expected_digest = image_ref.rsplit("@", 1)[1]
    if image.get("sha") != expected_digest:
        raise ReleaseRenderError("Render resolved image digest does not match the requested digest")
    service = _service(service_id, expected_image)
    checks = verify_health(
        base_url, environment=environment, source_sha=source_sha,
        expected_provider=provider, expected_model_revision=model_revision,
    )
    return {
        "service_id": service["id"],
        "deploy_id": deploy_id,
        "status": deploy["status"],
        "image": image,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("preflight", "deploy"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--service-id", required=True)
        sub.add_argument("--image-repository", required=True)
    deploy = subparsers.choices["deploy"]
    deploy.add_argument("--image-ref", required=True)
    deploy.add_argument("--base-url", required=True)
    deploy.add_argument("--environment", choices=("staging", "production"), required=True)
    deploy.add_argument("--source-sha", required=True)
    deploy.add_argument("--provider", required=True)
    deploy.add_argument("--model-revision", required=True)
    deploy.add_argument("--timeout", type=int, default=1200)
    provider_preflight = subparsers.add_parser("provider-preflight")
    provider_preflight.add_argument("--base-url", required=True)
    provider_preflight.add_argument("--environment", choices=("staging", "production"), required=True)
    provider_preflight.add_argument("--provider", required=True)
    provider_preflight.add_argument("--model-revision", required=True)
    args = parser.parse_args()
    try:
        if args.command == "preflight":
            service = _service(args.service_id, args.image_repository)
            result = {"status": "passed", "service_id": service["id"],
                      "deployment_mode": "manual-image", "image_repository": args.image_repository}
        elif args.command == "deploy":
            result = deploy_image(
                args.service_id, args.image_ref,
                expected_image=args.image_repository,
                base_url=args.base_url,
                environment=args.environment,
                source_sha=args.source_sha,
                provider=args.provider,
                model_revision=args.model_revision,
                timeout=args.timeout,
            )
        else:
            result = {"status": "passed", **verify_current_provider(
                args.base_url, environment=args.environment,
                expected_provider=args.provider, expected_model_revision=args.model_revision,
            )}
        print(json.dumps(result, sort_keys=True))
    except (ReleaseRenderError, OSError, ValueError) as exc:
        parser.exit(1, f"Render release gate failed: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
