"""
Main FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
import os

from webapp.routers import auth, leaderboard, runner, info, admin
from webapp.core.config import settings
from webapp.core.database import init_db


def create_app() -> FastAPI:
    init_db()   # ensure tables exist on every startup
    app = FastAPI(
        title="Debugging Championship",
        description="Elite multi-section debugging event platform",
        version="1.0.0",
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
    app.include_router(info.router,        prefix="/api",             tags=["Info"])
    app.include_router(admin.router,       prefix="/api/admin",       tags=["Admin"])

    # ── Static files (frontend) ───────────────────────────────────────────────
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app


app = create_app()
