from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import users, characters, parties, auth, bosses, rankings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.is_local and settings.dynamodb_endpoint_url:
        from app.dependencies import get_dynamo_client
        client = get_dynamo_client()
        client.create_table_if_not_exists(settings.dynamodb_table_name)
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="MapleBoss API",
        description="메이플스토리 주간 보스 스케줄러 백엔드",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.is_local else None,
        redoc_url="/redoc" if settings.is_local else None,
        redirect_slashes=False,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    prefix = "/api/v1"
    app.include_router(auth.router, prefix=prefix)
    app.include_router(users.router, prefix=prefix)
    app.include_router(characters.router, prefix=prefix)
    app.include_router(parties.router, prefix=prefix)
    app.include_router(bosses.router, prefix=prefix)
    app.include_router(rankings.router, prefix=prefix)

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()
