from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

app = FastAPI(title="PhishLens API")


@app.get("/health")
def health():
    return {"status": "ok", "service": "phishlens-api"}


def check_database():
    from backend.core.database import engine

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


@app.get("/ready")
def readiness():
    try:
        check_database()
    except (SQLAlchemyError, RuntimeError, ValueError):
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "database": "unavailable"},
        )

    return {"status": "ready", "database": "connected"}