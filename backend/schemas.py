from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# --- Warehouse ---
class WarehouseCreate(BaseModel):
    name: str
    location_desc: str = ""

class WarehouseOut(BaseModel):
    id: int
    name: str
    location_desc: str

    model_config = {"from_attributes": True}


# --- StorageLocation ---
class LocationCreate(BaseModel):
    warehouse_id: int
    shelf: str
    level: int
    position: str = ""

class LocationUpdate(BaseModel):
    shelf: Optional[str] = None
    level: Optional[int] = None
    position: Optional[str] = None

class LocationOut(BaseModel):
    id: int
    warehouse_id: int
    shelf: str
    level: int
    position: str
    full_code: str
    warehouse_name: Optional[str] = ""

    model_config = {"from_attributes": True}


# --- Material ---
class MaterialCreate(BaseModel):
    name: str
    spec: str = ""
    unit: str = "个"
    category: str = "consumable"
    sub_category: str = "direct_consumption"
    has_individual_tracking: bool = False
    low_stock_threshold: int = 5
    icon: str = "📦"
    color_idx: int = 0

class MaterialUpdate(BaseModel):
    name: Optional[str] = None
    spec: Optional[str] = None
    unit: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    has_individual_tracking: Optional[bool] = None
    low_stock_threshold: Optional[int] = None
    icon: Optional[str] = None
    color_idx: Optional[int] = None

class MaterialOut(BaseModel):
    id: int
    name: str
    spec: str
    unit: str
    category: str
    sub_category: str
    has_individual_tracking: bool
    low_stock_threshold: int
    icon: str
    color_idx: int
    total_quantity: int = 0
    borrowed_quantity: int = 0
    available_quantity: int = 0

    model_config = {"from_attributes": True}


# --- Inventory Item ---
class InventoryItemCreate(BaseModel):
    material_id: int
    warehouse_id: int
    location_id: Optional[int] = None
    prefix: str = "AC"
    start_num: int = 1
    count: int = 1

class InventoryItemOut(BaseModel):
    id: int
    material_id: int
    code: str
    status: str
    borrowed_by: Optional[str] = None
    borrow_time: Optional[str] = None
    warehouse_id: int
    location_id: Optional[int] = None
    warehouse_name: Optional[str] = ""
    location_code: Optional[str] = ""

    model_config = {"from_attributes": True}


# --- Inventory Batch ---
class InventoryBatchCreate(BaseModel):
    material_id: int
    warehouse_id: int
    location_id: Optional[int] = None
    quantity: int

class InventoryBatchUpdate(BaseModel):
    quantity: int

class InventoryBatchOut(BaseModel):
    id: int
    material_id: int
    warehouse_id: int
    location_id: Optional[int] = None
    quantity: int
    warehouse_name: Optional[str] = ""
    location_code: Optional[str] = ""

    model_config = {"from_attributes": True}


# --- Inventory Summary ---
class InventorySummary(BaseModel):
    material_id: int
    total_quantity: int
    borrowed_quantity: int
    available_quantity: int
    batches: List[InventoryBatchOut] = []
    items: Optional[List[InventoryItemOut]] = None


# --- Borrow / Return ---
class BorrowRequest(BaseModel):
    material_id: int
    quantity: int = Field(default=1, ge=1, le=10000)
    borrower: str
    item_code: Optional[str] = None
    warehouse_id: Optional[int] = None

class ReturnRequest(BaseModel):
    material_id: int
    quantity: int = Field(default=1, ge=1, le=10000)
    returned_by: str
    item_code: Optional[str] = None
    warehouse_id: Optional[int] = None

class BorrowHistoryOut(BaseModel):
    id: int
    material_id: int
    action: str
    quantity: int
    borrower: Optional[str] = None
    returned_by: Optional[str] = None
    item_code: Optional[str] = None
    warehouse_id: Optional[int] = None
    created_at: str
    material_name: Optional[str] = ""

    model_config = {"from_attributes": True}


# --- Admin ---
class AdminVerify(BaseModel):
    password: str

class AdminChangePassword(BaseModel):
    old_password: str
    new_password: str


# --- Common response ---
class ApiResponse(BaseModel):
    ok: bool
    data: Optional[object] = None
    msg: str = ""


# --- Transfer ---
class TransferRequest(BaseModel):
    material_id: int
    from_warehouse_id: int
    to_warehouse_id: int
    quantity: int = Field(default=1, ge=1, le=10000)
    location_id: Optional[int] = None


# --- Inbound ---
class InboundRequest(BaseModel):
    material_id: int
    warehouse_id: int
    location_id: Optional[int] = None
    quantity: int = Field(default=1, ge=1, le=1000000)


# --- Warehouse Stats ---
class WarehouseStatsOut(BaseModel):
    id: int
    name: str
    location_desc: str
    materials_count: int = 0
    total_quantity: int = 0
    low_stock_count: int = 0


class WarehouseDetailOut(BaseModel):
    id: int
    name: str
    location_desc: str
    materials: list = []
    locations: list = []


# --- Material Warehouse Breakdown ---
class MaterialWarehouseBreakdown(BaseModel):
    warehouse_id: int
    warehouse_name: str
    quantity: int = 0
    location_code: Optional[str] = ""


# --- Import ---
class ImportResult(BaseModel):
    imported: int = 0
    skipped: int = 0
    errors: List[str] = []


# --- Auth / RBAC ---
class AuthLoginRequest(BaseModel):
    credential: str = ""
    external_subject: Optional[str] = None
    student_no: Optional[str] = None
    name: Optional[str] = None
    role: str = "student"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: int
    external_subject: str
    student_no: Optional[str] = None
    name: str
    role: str
    status: str

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    role: Optional[str] = None
    status: Optional[str] = None


class TokenPairOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


# --- Borrow applications ---
class BorrowApplicationCreate(BaseModel):
    material_id: int
    quantity: int = Field(default=1, ge=1, le=10000)
    item_code: Optional[str] = None
    warehouse_id: Optional[int] = None
    purpose: str = Field(default="", max_length=500)


class BorrowApplicationReview(BaseModel):
    note: str = Field(default="", max_length=500)
    reservation_hours: int = Field(default=48, ge=1, le=168)


class BorrowApplicationAction(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=100)
    warehouse_id: Optional[int] = None


class BorrowApplicationOut(BaseModel):
    id: int
    applicant_id: int
    applicant_name: str
    student_no: Optional[str] = None
    material_id: int
    material_name: str
    quantity: int
    item_code: Optional[str] = None
    warehouse_id: Optional[int] = None
    status: str
    purpose: str
    review_note: str
    expires_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ScanResolveRequest(BaseModel):
    payload: str = Field(min_length=3, max_length=300)
