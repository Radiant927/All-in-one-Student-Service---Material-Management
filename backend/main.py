import logging
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from database import engine, Base

# Load .env from project root
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(_env_path):
        load_dotenv(_env_path)
except ImportError:
    pass

from seed import seed
from services.scheduler_service import create_scheduler
from constants import UserRole, UserStatus
from database import SessionLocal
from models import AuditLog, User
from security import decode_access_token
from logging_config import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    app_env = os.getenv("APP_ENV", "development").lower()
    if app_env != "production" or os.getenv("AUTO_CREATE_SCHEMA", "false").lower() == "true":
        Base.metadata.create_all(bind=engine)
    seed()
    scheduler = create_scheduler()
    if scheduler:
        scheduler.start()
    yield
    if scheduler:
        scheduler.shutdown(wait=False)


configure_logging(os.getenv("LOG_LEVEL", "INFO"))
app = FastAPI(title="一站式物资管理系统 API", version="2.0.0", lifespan=lifespan)


@app.middleware("http")
async def protect_legacy_write_endpoints(request: Request, call_next):
    """Protect all existing mutation routes while dedicated v2 routes use dependencies."""
    audit_actor_id = None
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path.startswith("/api/"):
        exempt_prefixes = (
            "/api/auth/",
            "/api/borrow-applications",
            "/api/scan/",
            "/api/admin/verify",
        )
        if not request.url.path.startswith(exempt_prefixes):
            authorization = request.headers.get("Authorization", "")
            if not authorization.startswith("Bearer "):
                return JSONResponse(status_code=401, content={"ok": False, "data": None, "msg": "请先登录"})
            try:
                payload = decode_access_token(authorization[7:])
                db = SessionLocal()
                try:
                    user = db.query(User).filter(User.id == int(payload["sub"])).first()
                    allowed = user and user.status == UserStatus.ACTIVE.value and user.role in {
                        UserRole.OPERATOR.value, UserRole.ADMIN.value
                    }
                    audit_actor_id = user.id if allowed else None
                finally:
                    db.close()
                if not allowed:
                    return JSONResponse(
                        status_code=403,
                        content={"ok": False, "data": None, "msg": "没有执行此操作的权限"},
                    )
            except HTTPException as exc:
                return JSONResponse(
                    status_code=exc.status_code,
                    content={"ok": False, "data": None, "msg": str(exc.detail)},
                )
    response = await call_next(request)
    if audit_actor_id and response.status_code < 400:
        audit_db = SessionLocal()
        try:
            audit_db.add(AuditLog(
                actor_id=audit_actor_id,
                action=f"legacy_api.{request.method.lower()}",
                target_type="api_route",
                target_id=request.url.path,
                result="success",
            ))
            audit_db.commit()
        except Exception:
            logging.getLogger(__name__).exception("failed to write legacy API audit log")
            audit_db.rollback()
        finally:
            audit_db.close()
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    logging.getLogger("api.access").info(
        "%s %s %s", request.method, request.url.path, response.status_code
    )
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"ok": False, "data": None, "msg": str(exc.detail)},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = "; ".join(error.get("msg", "参数错误") for error in exc.errors())
    return JSONResponse(status_code=422, content={"ok": False, "data": None, "msg": errors})

cors_origins = [x.strip() for x in os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:8080"
).split(",") if x.strip()]
if os.getenv("APP_ENV", "development").lower() == "production" and "*" in cors_origins:
    raise RuntimeError("生产环境 CORS_ORIGINS 禁止使用 *")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers import (
    admin, audit_logs, auth, borrow, borrow_applications, import_, inventory,
    materials, reports, scan, transfer, users, warehouses,
)

app.include_router(materials.router, prefix="/api", tags=["Materials"])
app.include_router(warehouses.router, prefix="/api", tags=["Warehouses"])
app.include_router(inventory.router, prefix="/api", tags=["Inventory"])
app.include_router(borrow.router, prefix="/api", tags=["Borrow"])
app.include_router(import_.router, prefix="/api", tags=["Import"])
app.include_router(admin.router, prefix="/api", tags=["Admin"])
app.include_router(transfer.router, prefix="/api", tags=["Transfer"])
app.include_router(reports.router, prefix="/api", tags=["Reports"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(audit_logs.router, prefix="/api", tags=["Audit"])
app.include_router(borrow_applications.router, prefix="/api", tags=["Borrow Applications"])
app.include_router(scan.router, prefix="/api", tags=["Scan"])
app.include_router(users.router, prefix="/api", tags=["Users"])


@app.get("/api/health")
def health():
    return {"ok": True, "data": {"version": "2.0.0"}, "msg": "API is running"}
