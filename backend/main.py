import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed()
    yield


app = FastAPI(title="一站式物资管理系统 API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers import materials, warehouses, inventory, borrow, import_, admin, transfer, reports

app.include_router(materials.router, prefix="/api", tags=["Materials"])
app.include_router(warehouses.router, prefix="/api", tags=["Warehouses"])
app.include_router(inventory.router, prefix="/api", tags=["Inventory"])
app.include_router(borrow.router, prefix="/api", tags=["Borrow"])
app.include_router(import_.router, prefix="/api", tags=["Import"])
app.include_router(admin.router, prefix="/api", tags=["Admin"])
app.include_router(transfer.router, prefix="/api", tags=["Transfer"])
app.include_router(reports.router, prefix="/api", tags=["Reports"])


@app.get("/api/health")
def health():
    return {"ok": True, "msg": "API is running"}