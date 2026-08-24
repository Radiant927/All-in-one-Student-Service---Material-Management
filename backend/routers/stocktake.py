from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from database import get_db
from models import Stocktake, StocktakeEntry, Material, Warehouse, StorageLocation, InventoryBatch
from schemas import StocktakeCreate, StocktakeEntryIn, ApiResponse

router = APIRouter()


def _now():
    return datetime.now().isoformat()


def _batch_quantity(db, material_id, warehouse_id, location_id):
    """计算某物资在某仓库/位置的账面数量（个体追踪物资按 items 计数）"""
    from models import InventoryItem
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        return 0
    if m.has_individual_tracking:
        q = db.query(InventoryItem).filter(
            InventoryItem.material_id == material_id,
            InventoryItem.warehouse_id == warehouse_id,
        )
        if location_id:
            q = q.filter(InventoryItem.location_id == location_id)
        return q.count()
    q = db.query(InventoryBatch).filter(
        InventoryBatch.material_id == material_id,
        InventoryBatch.warehouse_id == warehouse_id,
    )
    if location_id:
        q = q.filter(InventoryBatch.location_id == location_id)
    total = 0
    for b in q.all():
        total += b.quantity
    return total


def _entry_out(e: StocktakeEntry):
    loc_code = ""
    if e.location:
        loc_code = e.location.full_code
    return {
        "id": e.id,
        "material_id": e.material_id,
        "material_name": e.material.name if e.material else "",
        "material_spec": e.material.spec if e.material else "",
        "warehouse_id": e.warehouse_id,
        "warehouse_name": e.warehouse.name if e.warehouse else "",
        "location_id": e.location_id,
        "location_code": loc_code,
        "book_quantity": e.book_quantity,
        "actual_quantity": e.actual_quantity,
        "difference": e.difference,
    }


@router.post("/stocktake")
def create_stocktake(body: StocktakeCreate, db: Session = Depends(get_db)):
    """创建盘点单，自动按当前库存生成账面快照明细"""
    now = _now()
    st = Stocktake(status="in_progress", note=body.note, created_at=now)
    db.add(st)
    db.flush()

    materials = db.query(Material).all()
    warehouses = db.query(Warehouse).all()
    count = 0
    for m in materials:
        for w in warehouses:
            qty = _batch_quantity(db, m.id, w.id, None)
            if qty <= 0:
                continue
            entry = StocktakeEntry(
                stocktake_id=st.id,
                material_id=m.id,
                warehouse_id=w.id,
                location_id=None,
                book_quantity=qty,
                actual_quantity=None,
                difference=0,
            )
            db.add(entry)
            count += 1
    db.commit()
    db.refresh(st)
    return {"ok": True, "data": {"id": st.id, "entries": count}, "msg": f"创建盘点单成功，共 {count} 条待盘点项"}


@router.get("/stocktake")
def list_stocktakes(db: Session = Depends(get_db)):
    items = db.query(Stocktake).order_by(Stocktake.id.desc()).all()
    data = [{"id": s.id, "status": s.status, "note": s.note,
             "created_at": s.created_at, "completed_at": s.completed_at,
             "entries_count": len(s.entries),
             "discrepancy_count": sum(1 for e in s.entries if e.difference != 0)} for s in items]
    return {"ok": True, "data": data, "msg": ""}


@router.get("/stocktake/{stocktake_id}")
def get_stocktake(stocktake_id: int, db: Session = Depends(get_db)):
    st = db.query(Stocktake).filter(Stocktake.id == stocktake_id).first()
    if not st:
        raise HTTPException(status_code=404, detail="盘点单不存在")
    entries = [_entry_out(e) for e in st.entries]
    return {"ok": True, "data": {
        "id": st.id, "status": st.status, "note": st.note,
        "created_at": st.created_at, "completed_at": st.completed_at,
        "entries": entries,
        "total_book": sum(e.book_quantity for e in st.entries),
        "total_actual": sum((e.actual_quantity or 0) for e in st.entries),
        "total_difference": sum(e.difference for e in st.entries),
    }, "msg": ""}


@router.put("/stocktake/{stocktake_id}/entry/{entry_id}")
def update_entry(stocktake_id: int, entry_id: int, body: StocktakeEntryIn,
                 db: Session = Depends(get_db)):
    st = db.query(Stocktake).filter(Stocktake.id == stocktake_id).first()
    if not st:
        raise HTTPException(status_code=404, detail="盘点单不存在")
    if st.status == "completed":
        raise HTTPException(status_code=400, detail="盘点单已完成，无法修改")
    e = db.query(StocktakeEntry).filter(
        StocktakeEntry.id == entry_id,
        StocktakeEntry.stocktake_id == stocktake_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="盘点明细不存在")
    e.actual_quantity = body.actual_quantity
    e.difference = body.actual_quantity - e.book_quantity
    db.commit()
    return {"ok": True, "data": _entry_out(e), "msg": "清点数量已更新"}


@router.post("/stocktake/{stocktake_id}/complete")
def complete_stocktake(stocktake_id: int, apply_fix: bool = False, db: Session = Depends(get_db)):
    """完成盘点。apply_fix=True 时把库存修正为实际数量。"""
    st = db.query(Stocktake).filter(Stocktake.id == stocktake_id).first()
    if not st:
        raise HTTPException(status_code=404, detail="盘点单不存在")
    if st.status == "completed":
        raise HTTPException(status_code=400, detail="盘点单已完成")

    from models import InventoryItem
    changes = []
    skip = []
    for e in st.entries:
        if e.actual_quantity is None:
            e.actual_quantity = e.book_quantity
            e.difference = 0
        if not apply_fix or e.difference == 0:
            continue
        m = e.material
        if not m:
            continue
        if not m.has_individual_tracking:
            # 非个体追踪：直接修正批次数量
            batch = db.query(InventoryBatch).filter(
                InventoryBatch.material_id == e.material_id,
                InventoryBatch.warehouse_id == e.warehouse_id,
            ).first()
            if batch:
                batch.quantity = e.actual_quantity
                batch.updated_at = _now()
                changes.append(f"{m.name}: {e.book_quantity}->{e.actual_quantity}")
        else:
            # 个体追踪：通过增删 inventory_items 对齐数量
            items = db.query(InventoryItem).filter(
                InventoryItem.material_id == e.material_id,
                InventoryItem.warehouse_id == e.warehouse_id,
                InventoryItem.status == "available",
            ).all()
            cur = len(items)
            if e.actual_quantity < cur:
                # 删除多余可用个体
                n_del = cur - e.actual_quantity
                for it in items[:n_del]:
                    db.delete(it)
                changes.append(f"{m.name}: {cur}->{e.actual_quantity}（删除 {n_del} 个）")
            elif e.actual_quantity > cur:
                skip.append(f"{m.name} 实际多于账面，需人工补录 {e.actual_quantity - cur} 个个体")
                e.actual_quantity = cur
                e.difference = cur - e.book_quantity

    st.status = "completed"
    st.completed_at = _now()
    db.commit()
    msg = "盘点完成" if not apply_fix else f"盘点完成，已修正 {len(changes)} 项库存"
    if skip:
        msg += "；" + "；".join(skip)
    return {"ok": True, "data": {"fixed": changes, "skipped": skip},
            "msg": msg}
