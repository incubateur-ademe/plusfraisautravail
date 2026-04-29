from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pfat_api.config import settings
from pfat_api.routes import alerts, health


def create_app() -> FastAPI:
    app = FastAPI(
        title="pfat-api",
        description="API gateway aggregating alert sources for plusfraisautravail.beta.gouv.fr.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(alerts.router)

    return app


app = create_app()
