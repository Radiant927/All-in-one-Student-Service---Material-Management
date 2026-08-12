from sqlalchemy import Column, Integer, String, Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from database import Base


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
    status = Column(String(20), nullable=False, default="available", index=True)  # available / borrowed
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
    status = Column(String(20), nullable=False, default="in_progress", index=True)  # in_progress / completed
    note = Column(String(500), default="")
    created_at = Column(String(30), nullable=False)
    completed_at = Column(String(30), nullable=True)

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

    stocktake = relationship("Stocktake", back_populates="entries")
    material = relationship("Material")
    warehouse = relationship("Warehouse")
    location = relationship("StorageLocation")
