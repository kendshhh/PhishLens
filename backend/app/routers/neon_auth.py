"""Same-origin proxy for the extension's Managed Better Auth requests."""

from urllib.parse import urlsplit

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Authentication"])

# The release package pins this ID through the public key in extension/manifest.json.
# Keep it exact: this proxy must not become an open Auth relay for arbitrary extensions.
EXTENSION_ORIGIN = "chrome-extension://ceneonaedddlkdocdapimkfggbjcchlb"
API_ORIGINS = {
    "phishlens-staging.onrender.com": "https://phishlens-staging.onrender.com",
    "phishlens-api-ocvt.onrender.com": "https://phishlens-api-ocvt.onrender.com",
}
METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}
HOP_BY_HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "content-length",
    "content-encoding",
}


def _auth_base_url() -> str:
    import os

    value = os.getenv("NEON_AUTH_BASE_URL", "").strip().rstrip("/")
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.port is not None or parsed.query or parsed.fragment
            or ".neonauth." not in parsed.hostname or not parsed.hostname.endswith(".aws.neon.tech")
            or not parsed.path.endswith("/auth")):
        raise HTTPException(503, "Authentication configuration unavailable")
    return value


def _cors(response: Response, origin: str) -> Response:
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = ", ".join(sorted(METHODS))
    response.headers["Access-Control-Expose-Headers"] = "set-auth-jwt, content-type"
    response.headers["Vary"] = "Origin"
    return response


def _rewrite_cookie(value: str) -> str:
    parts = [part.strip() for part in value.split(";") if part.strip()]
    if not parts:
        return value
    attributes = [parts[0]]
    has_secure = False
    for part in parts[1:]:
        key = part.split("=", 1)[0].strip().lower()
        if key == "domain" or key == "samesite":
            continue
        if key == "secure":
            has_secure = True
        attributes.append(part)
    if not has_secure:
        attributes.append("Secure")
    attributes.append("SameSite=None")
    return "; ".join(attributes)


@router.api_route("/api/auth/{auth_path:path}", methods=METHODS, include_in_schema=False)
async def neon_auth_proxy(auth_path: str, request: Request) -> Response:
    """Forward extension Auth traffic through an HTTPS origin Neon trusts.

    Neon Managed Better Auth rejects the extension's custom-scheme Origin. The
    API forwards requests with its own trusted HTTPS Origin and relays the
    session cookie back to the extension's exact, pinned origin.
    """
    origin = request.headers.get("origin", "")
    if origin != EXTENSION_ORIGIN:
        raise HTTPException(403, "Extension origin is not allowed")

    api_origin = API_ORIGINS.get(request.url.hostname or "")
    if api_origin is None:
        raise HTTPException(404, "Authentication proxy unavailable")

    if request.method == "OPTIONS":
        response = Response(status_code=204)
        requested_headers = request.headers.get("access-control-request-headers", "")
        if requested_headers:
            response.headers["Access-Control-Allow-Headers"] = requested_headers
        return _cors(response, origin)

    if request.method not in METHODS:
        raise HTTPException(405, "Method not allowed")

    upstream = _auth_base_url() + "/" + auth_path
    raw_query = request.scope.get("query_string", b"").decode("latin-1")
    if raw_query:
        upstream += "?" + raw_query

    headers = {
        name: value for name, value in request.headers.items()
        if name.lower() not in HOP_BY_HOP_HEADERS | {"host", "origin", "referer"}
        and not name.lower().startswith("sec-fetch-")
    }
    headers["origin"] = api_origin
    headers["referer"] = api_origin + "/"

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=5.0), follow_redirects=False) as client:
            result = await client.request(
                request.method,
                upstream,
                headers=headers,
                content=await request.body(),
            )
    except httpx.HTTPError:
        return _cors(JSONResponse({"message": "Authentication service is temporarily unavailable"}, status_code=503), origin)

    response = Response(content=result.content, status_code=result.status_code)
    for name in ("content-type", "cache-control", "location", "retry-after", "www-authenticate", "set-auth-jwt"):
        value = result.headers.get(name)
        if value is not None:
            response.headers[name] = value
    for cookie in result.headers.get_list("set-cookie"):
        response.raw_headers.append((b"set-cookie", _rewrite_cookie(cookie).encode("latin-1")))
    return _cors(response, origin)
