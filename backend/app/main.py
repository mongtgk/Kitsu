import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import (
    IntegrityError,
    MultipleResultsFound,
    NoResultFound,
    ProgrammingError,
    SQLAlchemyError,
)

from .config import settings
from .database import engine
from .errors import (
    AppError,
    AuthError,
    ConflictError,
    InternalError,
    NotFoundError,
    PermissionError,
    ValidationError,
    error_payload,
    resolve_error_code,
)
from .routers import (
    anime,
    auth,
    collections,
    episodes,
    favorites,
    releases,
    search,
    users,
    views,
    watch,
)
from .utils.health import check_database_connection
from .utils.migrations import run_migrations

AVATAR_DIR = Path(__file__).resolve().parent.parent / "uploads" / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()


def _resolve_log_level(value: str) -> int:
    level = logging.getLevelName(value)
    return level if isinstance(level, int) else logging.INFO


log_level = _resolve_log_level(log_level_name)

if not logging.getLogger().handlers:
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
logger = logging.getLogger("kitsu")
logger.setLevel(log_level)


def _health_response(status_text: str, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"status": status_text})

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application")
    if settings.debug:
        logger.warning("DEBUG=true — do not use in production")

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, run_migrations)
    except RuntimeError as exc:
        logger.exception("Application startup aborted due to migration failure")
        raise

    try:
        db_status = await check_database_connection(engine, include_metadata=True)
    except SQLAlchemyError as exc:
        logger.exception("Database readiness check failed during startup")
        raise RuntimeError(
            "Database not ready. Ensure DATABASE_URL is reachable and migrations are applied (e.g. with 'alembic upgrade head')."
        ) from exc
    else:
        logger.info(
            "Database ready (current_database=%s, current_schema=%s, alembic_revision=%s)",
            db_status.database or "unknown",
            db_status.schema or "unknown",
            db_status.alembic_revision or "unavailable",
        )

    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/media/avatars",
    StaticFiles(directory=AVATAR_DIR, html=False),
    name="avatars",
)

routers = [
    auth.router,
    users.router,
    anime.router,
    releases.router,
    episodes.router,
    collections.router,
    favorites.router,
    views.router,
    watch.router,
]

for router in routers:
    app.include_router(router)

app.include_router(search.router, tags=["Search"])

SAFE_HTTP_MESSAGES: dict[int, str] = {
    status.HTTP_400_BAD_REQUEST: ValidationError.message,
    status.HTTP_401_UNAUTHORIZED: AuthError.message,
    status.HTTP_403_FORBIDDEN: PermissionError.message,
    status.HTTP_404_NOT_FOUND: NotFoundError.message,
    status.HTTP_409_CONFLICT: ConflictError.message,
    status.HTTP_422_UNPROCESSABLE_ENTITY: ValidationError.message,
}


def _log_error(request: Request, status_code: int, code: str, message: str, exc: Exception | None = None) -> None:
    request_id = request.headers.get("x-request-id")
    log_message = f"[{code}] path={request.url.path} request_id={request_id or 'n/a'} message={message}"
    if status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        logger.error(log_message, exc_info=exc)
    else:
        logger.warning(log_message, exc_info=exc)


@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    _log_error(request, exc.status_code, exc.code, exc.message, exc)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(exc.code, exc.message),
    )


@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    safe_message = SAFE_HTTP_MESSAGES.get(
        exc.status_code,
        InternalError.message if exc.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR else "Request failed",
    )
    detail = exc.detail if isinstance(exc.detail, str) else ""
    log_message = detail.strip() or safe_message
    code = resolve_error_code(exc.status_code)
    _log_error(request, exc.status_code, code, log_message)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(code, safe_message),
    )


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    message = "Request validation failed"
    _log_error(request, status.HTTP_422_UNPROCESSABLE_ENTITY, ValidationError.code, message, exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_payload(ValidationError.code, message),
    )


@app.exception_handler(ValueError)
async def handle_value_error(request: Request, exc: ValueError) -> JSONResponse:
    log_message = str(exc).strip() or "Invalid request"
    _log_error(request, status.HTTP_400_BAD_REQUEST, ValidationError.code, log_message, exc)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_payload(ValidationError.code, "Invalid request"),
    )


@app.exception_handler(IntegrityError)
async def handle_integrity_error(request: Request, exc: IntegrityError) -> JSONResponse:
    message = "Request could not be completed due to a conflict"
    _log_error(request, status.HTTP_409_CONFLICT, ConflictError.code, message, exc)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=error_payload(ConflictError.code, message),
    )


@app.exception_handler(ProgrammingError)
async def handle_programming_error(request: Request, exc: ProgrammingError) -> JSONResponse:
    message = "Database not initialized. Ensure migrations are applied."
    _log_error(request, status.HTTP_500_INTERNAL_SERVER_ERROR, InternalError.code, message, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload(InternalError.code, message),
    )


@app.exception_handler(NoResultFound)
async def handle_no_result_found(request: Request, exc: NoResultFound) -> JSONResponse:
    message = "Requested resource was not found"
    _log_error(request, status.HTTP_404_NOT_FOUND, NotFoundError.code, message, exc)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=error_payload(NotFoundError.code, message),
    )


@app.exception_handler(MultipleResultsFound)
async def handle_multiple_results_found(
    request: Request, exc: MultipleResultsFound
) -> JSONResponse:
    message = "Multiple resources found where one expected"
    _log_error(request, status.HTTP_409_CONFLICT, ConflictError.code, message, exc)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=error_payload(ConflictError.code, message),
    )


@app.exception_handler(Exception)
async def handle_unhandled_exception(
    request: Request, exc: Exception
) -> JSONResponse:
    _log_error(
        request,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        InternalError.code,
        InternalError.message,
        exc,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload(InternalError.code, InternalError.message),
    )


@app.get("/health", tags=["health"])
async def healthcheck() -> Response:
    try:
        # Keep health probe lightweight; metadata logging is handled at startup
        await check_database_connection(engine, include_metadata=False)
    except SQLAlchemyError as exc:
        logger.error("Healthcheck database probe failed: %s", exc)
        return _health_response("error", status.HTTP_503_SERVICE_UNAVAILABLE)

    logger.debug("Healthcheck passed")
    return _health_response("ok", status.HTTP_200_OK)
