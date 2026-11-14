from scripts.production_deploy_smoke import verify_deployment

SHA = "8c02a7c86e8b2052d127b5a6a0422a5a80ffa9ea"
MODEL_SHA = "a" * 64


def test_production_smoke_waits_for_exact_sha_and_checks_behavior():
    urls = []
    posts = []

    def get_json(url):
        urls.append(url)
        if url.endswith("/version"):
            return {"environment": "production", "commit": SHA}
        if url.endswith("/health"):
            return {"status": "ok", "service": "phishlens-api"}
        if url.endswith("/ready"):
            return {"status": "ready", "database": "connected"}
        if url.endswith("/model-info"):
            return {
                "provider_mode": "tfidf",
                "model_sha256": MODEL_SHA,
                "supports_required_provider": True,
            }
        raise AssertionError(url)

    def post_json(url, *, payload, timeout, extra_headers=None, response_headers=None):
        posts.append((url, payload, timeout, extra_headers, response_headers))
        response_headers["x-phishlens-revision"] = SHA
        expected = "phishing" if "account will be closed" in payload["text"] else "legitimate"
        return {
            "mode": "tfidf",
            "model_revision": MODEL_SHA,
            "classification": expected,
            "risk_level": "high" if expected == "phishing" else "low",
            "evidence": [],
            "tactics": [],
        }

    report = verify_deployment(
        "https://production.example",
        SHA,
        get_json=get_json,
        post_json=post_json,
        timeout_seconds=0,
    )

    assert report["status"] == "passed"
    assert report["deployment_sha"] == SHA
    assert report["paid_provider_calls"] == report["database_writes"] == 0
    assert [item["case"] for item in report["behavior_checks"]] == ["p01-credential", "l01-meeting"]
    assert len(posts) == 2
    assert all(
        url.endswith(f"/analyses/revision/{SHA}")
        and timeout == 30
        and headers == {"X-Require-Provider": "tfidf"}
        and response_headers["x-phishlens-revision"] == SHA
        for url, _, timeout, headers, response_headers in posts
    )
    assert urls == [
        "https://production.example/version",
        "https://production.example/health",
        "https://production.example/ready",
        "https://production.example/model-info",
        "https://production.example/version",
    ]


def test_production_smoke_rejects_provider_mode_other_than_tfidf():
    def get_json(url):
        if url.endswith("/version"):
            return {"environment": "production", "commit": SHA}
        if url.endswith("/health"):
            return {"status": "ok", "service": "phishlens-api"}
        if url.endswith("/ready"):
            return {"status": "ready", "database": "connected"}
        return {
            "provider_mode": "gemini",
            "model": "gemini-test",
            "supports_required_provider": True,
        }

    try:
        verify_deployment("https://production.example", SHA, get_json=get_json)
    except RuntimeError as exc:
        assert "TF-IDF" in str(exc)
    else:
        raise AssertionError("paid provider mode must not be exercised by post-deploy smoke")


def test_production_smoke_refuses_analysis_when_provider_guard_is_not_advertised():
    posts = []

    def get_json(url):
        if url.endswith("/version"):
            return {"environment": "production", "commit": SHA}
        if url.endswith("/health"):
            return {"status": "ok", "service": "phishlens-api"}
        if url.endswith("/ready"):
            return {"status": "ready", "database": "connected"}
        if url.endswith("/model-info"):
            return {"provider_mode": "tfidf", "model_sha256": MODEL_SHA}
        raise AssertionError(url)

    def post_json(*args, **kwargs):
        posts.append((args, kwargs))
        raise AssertionError("analysis must not be attempted without provider-guard support")

    try:
        verify_deployment(
            "https://production.example",
            SHA,
            get_json=get_json,
            post_json=post_json,
        )
    except RuntimeError as exc:
        assert "does not confirm required-provider enforcement" in str(exc)
    else:
        raise AssertionError("an API without the provider guard must fail closed")
    assert posts == []


def test_production_smoke_rejects_analysis_response_from_other_revision():
    posts = []
    other_sha = "b" * 40

    def get_json(url):
        if url.endswith("/version"):
            return {"environment": "production", "commit": SHA}
        if url.endswith("/health"):
            return {"status": "ok", "service": "phishlens-api"}
        if url.endswith("/ready"):
            return {"status": "ready", "database": "connected"}
        if url.endswith("/model-info"):
            return {
                "provider_mode": "tfidf",
                "model_sha256": MODEL_SHA,
                "supports_required_provider": True,
            }
        raise AssertionError(url)

    def post_json(url, *, payload, timeout, extra_headers=None, response_headers=None):
        posts.append(url)
        response_headers["x-phishlens-revision"] = other_sha
        return {
            "mode": "tfidf",
            "model_revision": MODEL_SHA,
            "classification": "phishing",
            "risk_level": "high",
            "evidence": [],
            "tactics": [],
        }

    try:
        verify_deployment(
            "https://production.example",
            SHA,
            get_json=get_json,
            post_json=post_json,
            timeout_seconds=0,
        )
    except RuntimeError as exc:
        assert "analysis response came from a different deployment revision" in str(exc)
    else:
        raise AssertionError("smoke must reject analysis from a different deployment revision")
    assert posts == [f"https://production.example/analyses/revision/{SHA}"]


def test_production_smoke_stops_before_analysis_when_provider_is_unavailable():
    posts = []

    def get_json(url):
        if url.endswith("/version"):
            return {"environment": "production", "commit": SHA}
        if url.endswith("/health"):
            return {"status": "ok", "service": "phishlens-api"}
        if url.endswith("/ready"):
            return {"status": "ready", "database": "connected"}
        if url.endswith("/model-info"):
            return {
                "provider_mode": "unavailable",
                "accepts_tfidf_reports": False,
                "supports_required_provider": True,
            }
        raise AssertionError(url)

    def post_json(*args, **kwargs):
        posts.append((args, kwargs))
        raise AssertionError("analysis must not be attempted when the provider is unavailable")

    try:
        verify_deployment(
            "https://production.example",
            SHA,
            get_json=get_json,
            post_json=post_json,
        )
    except RuntimeError as exc:
        assert "provider_mode=unavailable" in str(exc)
    else:
        raise AssertionError("unavailable production provider must fail closed")
    assert posts == []
