from datetime import datetime
from database import SessionLocal
from models import Warehouse, StorageLocation, Material, InventoryItem, InventoryBatch, BorrowHistory, AdminSetting
from routers.admin import hash_password
import os


def seed():
    db = SessionLocal()
    try:
        now = datetime.now().isoformat()

        # Warehouses
        if db.query(Warehouse).count() == 0:
            w1 = Warehouse(name="主仓库", location_desc="一楼库房")
            w2 = Warehouse(name="回收仓", location_desc="书画室旁")
            db.add_all([w1, w2])
            db.flush()

            # Default locations
            locs = [
                StorageLocation(warehouse_id=w1.id, shelf="A", level=1, position="1", full_code="A-1-1"),
                StorageLocation(warehouse_id=w1.id, shelf="A", level=1, position="2", full_code="A-1-2"),
                StorageLocation(warehouse_id=w1.id, shelf="A", level=2, position="1", full_code="A-2-1"),
                StorageLocation(warehouse_id=w2.id, shelf="B", level=1, position="1", full_code="B-1-1"),
            ]
            db.add_all(locs)
            db.flush()
        else:
            w1 = db.query(Warehouse).filter_by(name="主仓库").first()
            w2 = db.query(Warehouse).filter_by(name="回收仓").first()
            locs = db.query(StorageLocation).all()

        loc_map = {l.full_code: l for l in locs}

        # Materials
        if db.query(Material).count() == 0:
            materials = [
                Material(name="空调遥控器", spec="通用空调遥控器", unit="个", category="durable",
                         sub_category="recyclable", has_individual_tracking=1, low_stock_threshold=3,
                         icon="🎮", color_idx=0, created_at=now, updated_at=now),
                Material(name="饮用水", spec="桶装水 18.9L", unit="桶", category="consumable",
                         sub_category="direct_consumption", has_individual_tracking=0, low_stock_threshold=5,
                         icon="💧", color_idx=1, created_at=now, updated_at=now),
                Material(name="纸巾", spec="抽纸 120抽/包", unit="包", category="consumable",
                         sub_category="direct_consumption", has_individual_tracking=0, low_stock_threshold=10,
                         icon="🧻", color_idx=2, created_at=now, updated_at=now),
                Material(name="笔", spec="晨光签字笔 0.5mm 黑色", unit="支", category="consumable",
                         sub_category="recyclable", has_individual_tracking=0, low_stock_threshold=10,
                         icon="🖊️", color_idx=3, created_at=now, updated_at=now),
            ]
            db.add_all(materials)
            db.flush()

            # Inventory items for AC remote
            ac_remote = db.query(Material).filter_by(name="空调遥控器").first()
            loc_a11 = loc_map.get("A-1-1")
            if ac_remote and loc_a11:
                for i in range(1, 21):
                    code = f"AC-{str(i).zfill(3)}"
                    db.add(InventoryItem(
                        material_id=ac_remote.id, code=code, status="available",
                        warehouse_id=w1.id, location_id=loc_a11.id, created_at=now
                    ))

            # Inventory batches for consumables
            water = db.query(Material).filter_by(name="饮用水").first()
            tissues = db.query(Material).filter_by(name="纸巾").first()
            pens = db.query(Material).filter_by(name="笔").first()
            loc_a12 = loc_map.get("A-1-2")
            loc_a21 = loc_map.get("A-2-1")

            if water and loc_a12:
                # 初始总量50桶，已借出12桶，现余38桶
                db.add(InventoryBatch(material_id=water.id, warehouse_id=w1.id, location_id=loc_a12.id,
                                      quantity=50, created_at=now, updated_at=now))
                db.add(BorrowHistory(material_id=water.id, action="borrow", quantity=12,
                                     borrower="系统初始化", warehouse_id=w1.id, created_at=now))

            if tissues and loc_a21:
                # 初始总量100包，已借出30包，现余70包
                db.add(InventoryBatch(material_id=tissues.id, warehouse_id=w1.id, location_id=loc_a21.id,
                                      quantity=100, created_at=now, updated_at=now))
                db.add(BorrowHistory(material_id=tissues.id, action="borrow", quantity=30,
                                     borrower="系统初始化", warehouse_id=w1.id, created_at=now))

            if pens and loc_a21:
                # 初始总量60支，已借出18支（其中5支从回收仓借出），现余42支；回收仓余5支
                db.add(InventoryBatch(material_id=pens.id, warehouse_id=w1.id, location_id=loc_a21.id,
                                      quantity=55, created_at=now, updated_at=now))
                db.add(InventoryBatch(material_id=pens.id, warehouse_id=w2.id, location_id=loc_a21.id,
                                      quantity=5, created_at=now, updated_at=now))
                db.add(BorrowHistory(material_id=pens.id, action="borrow", quantity=13,
                                     borrower="系统初始化", warehouse_id=w1.id, created_at=now))
                db.add(BorrowHistory(material_id=pens.id, action="borrow", quantity=5,
                                     borrower="系统初始化", warehouse_id=w2.id, created_at=now))

        # Admin settings - 密码使用 SHA-256 + salt 哈希存储
        if db.query(AdminSetting).count() == 0:
            admin_password = os.getenv("ADMIN_PASSWORD", "admin888")
            db.add(AdminSetting(key="password", value=hash_password(admin_password)))

        db.commit()
        print("Seed data inserted successfully.")
    except Exception as e:
        db.rollback()
        print(f"Seed error: {e}")
        raise
    finally:
        db.close()