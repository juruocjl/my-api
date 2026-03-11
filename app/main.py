from pathlib import Path
from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI

from app.api.admin.providers import router as admin_provider_router
from app.api.admin.pricing import router as admin_pricing_router
from app.api.admin.stats import router as admin_stats_router
from app.api.admin.ui import router as admin_ui_router
from app.api.v1.openai_compat import router as openai_router
from app.core.auth import require_admin_auth, require_openai_auth
from app.core.config import settings
from app.core.database import Base, engine, ensure_sqlite_compatibility


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.database_url.startswith("sqlite"):
        db_path = settings.database_url.split("///", maxsplit=1)[-1]
        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await ensure_sqlite_compatibility()

    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(openai_router, dependencies=[Depends(require_openai_auth)])
app.include_router(admin_provider_router, dependencies=[Depends(require_admin_auth)])
app.include_router(admin_pricing_router, dependencies=[Depends(require_admin_auth)])
app.include_router(admin_stats_router, dependencies=[Depends(require_admin_auth)])
app.include_router(admin_ui_router)


def run() -> None:
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_reload,
    )


if __name__ == "__main__":
    run()
