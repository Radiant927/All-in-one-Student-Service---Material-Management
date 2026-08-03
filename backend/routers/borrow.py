from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from schemas import BorrowRequest, ReturnRequest, ApiResponse
from services.inventory_service import borrow_material, return_material

router = APIRouter()


@router.post("/borrow")
def borrow(body: BorrowRequest, db: Session = Depends(get_db)):
    result = borrow_material(db, body.material_id, body.quantity, body.borrower,
                             body.item_code, body.warehouse_id)
    return result


@router.post("/return")
def return_item(body: ReturnRequest, db: Session = Depends(get_db)):
    result = return_material(db, body.material_id, body.quantity, body.returned_by,
                             body.item_code, body.warehouse_id)
    return result


@router.get("/history")
def list_history(
    material_id: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    from models import BorrowHistory, Material
    query = db.query(BorrowHistory).order_by(BorrowHistory.id.desc())
    if material_id:
        query = query.filter(BorrowHistory.material_id == material_id)
    total = query.count()
    rows = query.offset(offset).limit(limit).all()
    data = []
    for r in rows:
        m = db.query(Material).filter(Material.id == r.material_id).first()
        data.append({
            "id": r.id, "material_id": r.material_id, "action": r.action,
            "quantity": r.quantity, "borrower": r.borrower, "returned_by": r.returned_by,
            "item_code": r.item_code, "warehouse_id": r.warehouse_id,
            "created_at": r.created_at,
            "material_name": (m.icon + " " + m.name) if m else "未知物资"
        })
    return {"ok": True, "data": {"total": total, "rows": data}, "msg": ""}