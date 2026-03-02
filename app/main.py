# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager

from sqlalchemy.exc import IntegrityError

from app.api.routers import auth_router, user_router, admin_router
from app.api.exception_handlers import (
    invalid_credentials_handler,
    invalid_token_handler,
    token_expired_handler,
    not_found_handler, integrity_error_handler, validation_error_handler, permission_denied_handler,
)
from app.exceptions.auth_exceptions import (
    InvalidCredentials,
    InvalidToken,
    TokenExpired,
)
from app.exceptions.common_exceptions import NotFoundError, ValidationError, PermissionDenied
from app.infrastructure.db.database import init_db


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

@app.get("/")
async def root():
    return {"status": "RPAFastAPI is running"}

app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(admin_router.router)

app.add_exception_handler(InvalidCredentials, invalid_credentials_handler)
app.add_exception_handler(InvalidToken, invalid_token_handler)
app.add_exception_handler(TokenExpired, token_expired_handler)
app.add_exception_handler(NotFoundError, not_found_handler)
app.add_exception_handler(ValidationError, validation_error_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(PermissionDenied, permission_denied_handler)