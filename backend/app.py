"""
Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from routers import auth, leaderboard, runner, info, admin
from routers.validator import router as validator_router
from routers.download import router as download_router
from core.config import settings
from core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialise schema once before serving requests
    init_db()
    yield
    # Shutdown: release all pooled DB connections cleanly
    from core.database import _pool
    if _pool is not None:
        _pool.closeall()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Debugging Championship",
        description="Elite multi-section debugging event platform",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs" if settings.ENV != "production" else None,
        redoc_url="/api/redoc" if settings.ENV != "production" else None,
    )

    # ── Middleware ────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if settings.ENV == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS,
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(auth.router,        prefix="/api/auth",        tags=["Auth"])
    app.include_router(leaderboard.router, prefix="/api/leaderboard", tags=["Leaderboard"])
    app.include_router(runner.router,      prefix="/api/run",         tags=["Test Runner"])
    app.include_router(validator_router,   prefix="/api/validate",    tags=["Validator"])
    app.include_router(download_router,    prefix="/api/download",    tags=["Download"])
    app.include_router(info.router,        prefix="/api",             tags=["Info"])
    app.include_router(admin.router,       prefix="/api/admin",       tags=["Admin"])
    app.include_router(admin.web_router,                               tags=["Admin UI"])


    return app


app = create_app()
