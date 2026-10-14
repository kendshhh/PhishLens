from fastapi import FastAPI

app = FastAPI(title="PhishLens API")


@app.get("/health")
def health():
    return {"status": "ok", "service": "phishlens-api"}