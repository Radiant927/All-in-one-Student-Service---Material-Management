import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from database import Base
from time_utils import utcnow


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    location_desc = Column(String(200), default="")

    locations = relationship("StorageLocation", back_populates="warehouse", cascade="all, delete-orphan")
    inventory_items = relationship("InventoryItem", back_populates="warehouse")
    inventory_batches = relationship("InventoryBatch", back_populates="warehouse")


class StorageLocation(Base):
    __tablename__ = "storage_locations"
    __table_args__ = (UniqueConstraint("warehouse_id", "full_code"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    shelf = Column(String(20), nullable=False)
    level = Column(Integer, nullable=False)
    position = Column(String(20), default="")
    full_code = Column(String(60), nullable=False)

    warehouse = relationship("Warehouse", back_populates="locations")
    inventory_items = relationship("InventoryItem", back_populates="location")
    inventory_batches = relationship("InventoryBatch", back_populates="location")


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    public_id = Column(String(36), nullable=False, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False, unique=True)
    spec = Column(String(200), default="")
    unit = Column(String(20), nullable=False, default="个")
    category = Column(String(20), nullable=False, default="consumable", index=True)  # durable / consumable
    sub_category = Column(String(30), nullable=False, default="direct_consumption")  # new_consumable / recyclable / direct_consumption
    has_individual_tracking = Column(Integer, nullable=False, default=0)
    low_stock_threshold = Column(Integer, nullable=False, default=5)
    icon = Column(String(10), default="📦")
    color_idx = Column(Integer, default=0)
    created_at = Column(String(30), nullable=False)
    updated_at = Column(String(30), nullable=False)

    inventory_items = relationship("InventoryItem", back_populates="material", cascade="all, delete-orphan")
    inventory_batches = relationship("InventoryBatch", back_populates="material", cascade="all, delete-orphan")
    borrow_history = relationship("BorrowHistory", back_populates="material", cascade="all, delete-orphan")


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)
    code = Column(String(100), nullable=False, unique=True)
    status = Column(String(20), nullable=False, default="available", index=True)  # available / borrowed / missing
    borrowed_by = Column(String(100), nullable=True)
    borrow_time = Column(String(30), nullable=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("storage_locations.id"), nullable=True)
    created_at = Column(String(30), nullable=False)

    material = relationship("Material", back_populates="inventory_items")
    warehouse = relationship("Warehouse", back_populates="inventory_items")
    location = relationship("StorageLocation", back_populates="inventory_items")


class InventoryBatch(Base):
    __tablename__ = "inventory_batches"
    __table_args__ = (UniqueConstraint("material_id", "warehouse_id", "location_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("storage_locations.id"), nullable=True)
    quantity = Column(Integer, nullable=False, default=0)
    created_at = Column(String(30), nullable=False)
    updated_at = Column(String(30), nullable=False)

    material = relationship("Material", back_populates="inventory_batches")
    warehouse = relationship("Warehouse", back_populates="inventory_batches")
    location = relationship("StorageLocation", back_populates="inventory_batches")


class BorrowHistory(Base):
    __tablename__ = "borrow_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)
    action = Column(String(20), nullable=False, index=True)  # borrow / return / transfer / inbound
    quantity = Column(Integer, nullable=False, default=1)
    borrower = Column(String(100), nullable=True)
    returned_by = Column(String(100), nullable=True)
    item_code = Column(String(100), nullable=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True, index=True)
    created_at = Column(String(30), nullable=False, index=True)

    material = relationship("Material", back_populates="borrow_history")


class AdminSetting(Base):
    __tablename__ = "admin_settings"

    key = Column(String(50), primary_key=True)
    value = Column(String(500), nullable=False)


class Stocktake(Base):
    """盘点单：一次盘点任务"""
    __tablename__ = "stocktakes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String(20), nullable=False, default="in_progress", index=True)  # in_progress / completed / cancelled
    note = Column(String(500), default="")
    created_at = Column(String(30), nullable=False)
    completed_at = Column(String(30), nullable=True)
    cancelled_at = Column(String(30), nullable=True)

    entries = relationship("StocktakeEntry", back_populates="stocktake", cascade="all, delete-orphan")


class StocktakeEntry(Base):
    """盘点明细：每条物资的账面数 vs 实际清点数"""
    __tablename__ = "stocktake_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stocktake_id = Column(Integer, ForeignKey("stocktakes.id"), nullable=False, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("storage_locations.id"), nullable=True)
    book_quantity = Column(Integer, nullable=False, default=0)   # 账面数量
    actual_quantity = Column(Integer, nullable=True)             # 实际清点数量
    difference = Column(Integer, nullable=False, default=0)      # 差异 = actual - book
    counted = Column(Boolean, nullable=False, default=False)      # 已明确完成该项清点

    stocktake = relationship("Stocktake", back_populates="entries")
    material = relationship("Material")
    warehouse = relationship("Warehouse")
    location = relationship("StorageLocation")
    item_checks = relationship(
        "StocktakeItemCheck", back_populates="entry", cascade="all, delete-orphan"
    )


class StocktakeItemCheck(Base):
    """个体追踪盘点核对记录；既保存账面快照，也保存现场额外扫码。"""
    __tablename__ = "stocktake_item_checks"
    __table_args__ = (UniqueConstraint("stocktake_entry_id", "item_code"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    stocktake_entry_id = Column(
        Integer, ForeignKey("stocktake_entries.id"), nullable=False, index=True
    )
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=True, index=True)
    item_code = Column(String(100), nullable=False)
    expected = Column(Boolean, nullable=False, default=False)
    scanned = Column(Boolean, nullable=False, default=False)
    scanned_at = Column(String(30), nullable=True)

    entry = relationship("StocktakeEntry", back_populates="item_checks")
    inventory_item = relationship("InventoryItem")



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_subject = Column(String(200), nullable=False, unique=True, index=True)
    student_no = Column(String(50), nullable=True, unique=True, index=True)
    name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default="student", index=True)
    status = Column(String(20), nullable=False, default="active", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    borrow_applications = relationship(
        "BorrowApplication", foreign_keys="BorrowApplication.applicant_id", back_populates="applicant"
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    user = relationship("User", back_populates="refresh_tokens")


class BorrowApplication(Base):
    __tablename__ = "borrow_applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    applicant_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    item_code = Column(String(100), nullable=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True, index=True)
    status = Column(String(30), nullable=False, default="submitted", index=True)
    purpose = Column(String(500), nullable=False, default="")
    review_note = Column(String(500), nullable=False, default="")
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    picked_up_at = Column(DateTime(timezone=True), nullable=True)
    returned_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    applicant = relationship("User", foreign_keys=[applicant_id], back_populates="borrow_applications")
    approver = relationship("User", foreign_keys=[approved_by])
    material = relationship("Material")
    warehouse = relationship("Warehouse")
    reservation = relationship(
        "InventoryReservation", back_populates="application", uselist=False, cascade="all, delete-orphan"
    )


class InventoryReservation(Base):
    __tablename__ = "inventory_reservations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("borrow_applications.id"), nullable=False, unique=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)
    item_code = Column(String(100), nullable=True, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    active = Column(Boolean, nullable=False, default=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    released_at = Column(DateTime(timezone=True), nullable=True)

    application = relationship("BorrowApplication", back_populates="reservation")
    material = relationship("Material")


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("borrow_applications.id"), nullable=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(20), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    item_code = Column(String(100), nullable=True)
    idempotency_key = Column(String(100), nullable=True, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, index=True)

    application = relationship("BorrowApplication")
    material = relationship("Material")
    warehouse = relationship("Warehouse")
    actor = relationship("User")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    target_type = Column(String(100), nullable=False, index=True)
    target_id = Column(String(100), nullable=True, index=True)
    result = Column(String(20), nullable=False, default="success", index=True)
    detail = Column(Text, nullable=False, default="")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, index=True)

    actor = relationship("User")
