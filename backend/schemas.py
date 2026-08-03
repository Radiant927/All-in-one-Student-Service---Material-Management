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
    quantity: int = 1
    borrower: str
    item_code: Optional[str] = None
    warehouse_id: Optional[int] = None

class ReturnRequest(BaseModel):
    material_id: int
    quantity: int = 1
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


# --- Import ---
class ImportResult(BaseModel):
    imported: int = 0
    skipped: int = 0
    errors: List[str] = []