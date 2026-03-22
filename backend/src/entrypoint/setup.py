import logging
from collections.abc import Iterable
from contextlib import asynccontextmanager

from dishka import Provider, make_async_container
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from entrypoint.config import Config, create_config, config


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Application starting up")
    yield
    logging.info("Application shutting down")


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    return app


def create_async_container(providers: Iterable[Provider]):
    config = create_config()
    return make_async_container(
        *providers,
        context={Config: config},
    )


def configure_app(app: FastAPI, root_router: APIRouter) -> None:
    app.include_router(root_router)


def configure_middlewares(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[config.frontend.URL, config.service.URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
