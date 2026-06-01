from fastapi import APIRouter

from app.core.database import check_database
from app.core.qdrant import check_qdrant
from app.core.redis import check_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict[str, object]:
    checks: dict[str, bool] = {
        "postgres": False,
        "redis": False,
        "qdrant": False,
    }

    try:
        checks["postgres"] = await check_database()
    except Exception:
        checks["postgres"] = False

    try:
        checks["redis"] = await check_redis()
    except Exception:
        checks["redis"] = False

    try:
        checks["qdrant"] = await check_qdrant()
    except Exception:
        checks["qdrant"] = False

    return {
        "status": "ready" if all(checks.values()) else "degraded",
        "checks": checks,
    }
