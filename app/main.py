# app/main.py
import os

from fastapi import FastAPI
from contextlib import asynccontextmanager

from sqlalchemy.exc import IntegrityError
from starlette.staticfiles import StaticFiles

from app.api.routers import auth_router, user_router, admin_router, character_router, game_router
from app.api.exception_handlers import (
    integrity_error_handler, validation_error_handler, EXCEPTION_MAP,
    app_exception_handler,
)
from app.core.logging_config import setup_logging
from app.exceptions.common_exceptions import ValidationError
from app.infrastructure.db.database import init_db
from app.utils.files import get_base_dir

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown (если нужно)


app = FastAPI(
    title="RPAFastAPI",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/images", StaticFiles(directory=os.path.join(get_base_dir(), "images")), name="images")

@app.get("/")
async def root():
    return {"status": "RPAFastAPI is running"}

app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(admin_router.router)
app.include_router(character_router.router)
app.include_router(game_router.router)

for exc_class in EXCEPTION_MAP:
    app.add_exception_handler(exc_class, app_exception_handler)

app.add_exception_handler(ValidationError, validation_error_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
