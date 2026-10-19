"""Deploy a PR's exact commit and wait for Render to report it live."""
import json
import os
import time
import urllib.request


def main():
    key = os.environ.get("RENDER_STAGING_API_KEY")
    service = os.environ.get("RENDER_STAGING_SERVICE_ID")
    commit = os.environ["STAGING_COMMIT"]
    if not key or not service:
        raise SystemExit("Configure RENDER_STAGING_API_KEY secret and RENDER_STAGING_SERVICE_ID variable before merging.")
    if service == "srv-db7eap25b2lc73fkelpg":
        raise SystemExit("Refusing to deploy staging changes to the production service.")

    def request(path, body=None):
        req = urllib.request.Request(
            "https://api.render.com/v1/" + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)

    deploy = request(f"services/{service}/deploys", {"commitId": commit})
    deploy_id = deploy["id"]
    print(f"Waiting for staging deployment {deploy_id} of {commit}", flush=True)
    deadline = time.monotonic() + 900
    while time.monotonic() < deadline:
        status = request(f"services/{service}/deploys/{deploy_id}")
        if status["status"] == "live":
            if status.get("commit", {}).get("id") != commit:
                raise SystemExit("Render live commit does not match the requested PR commit.")
            print("Exact PR commit is live on staging.")
            return
        if status["status"] in {"build_failed", "update_failed", "pre_deploy_failed", "canceled", "deactivated"}:
            raise SystemExit("Staging deployment failed: " + status["status"])
        time.sleep(10)
    raise SystemExit("Staging deployment timed out.")


if __name__ == "__main__":
    main()
