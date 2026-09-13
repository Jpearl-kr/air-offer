from fastapi import FastAPI

from app.api.v1.router import router as api_v1_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="air-offer API", version="0.1.0")
app.include_router(api_v1_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}
