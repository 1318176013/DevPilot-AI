import httpx

from app.core.config import get_settings

settings = get_settings()


async def check_qdrant() -> bool:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"{settings.qdrant_url.rstrip('/')}/readyz")
        response.raise_for_status()
    return True
