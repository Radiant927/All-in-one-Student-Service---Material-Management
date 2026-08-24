from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import InventoryItem, Material, User
from schemas import ScanResolveRequest
from security import get_current_user
from services.borrow_application_service import material_available_quantity


router = APIRouter()


@router.post("/scan/resolve")
def resolve_scan(
    body: ScanResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payload = body.payload.strip()
    material = None
    item = None
    if payload.startswith("MATERIAL:ac-remote:"):
        item_code = payload.split(":", 2)[2]
        item = db.query(InventoryItem).filter(InventoryItem.code == item_code).first()
        material = item.material if item else None
    elif payload.startswith("MATERIAL:"):
        public_id = payload.split(":", 1)[1]
        material = db.query(Material).filter(Material.public_id == public_id).first()
    elif payload.startswith("ITEM:"):
        item_code = payload.split(":", 1)[1]
        item = db.query(InventoryItem).filter(InventoryItem.code == item_code).first()
        material = item.material if item else None
    else:
        raise HTTPException(status_code=422, detail="不支持的二维码格式")
    if not material:
        raise HTTPException(status_code=404, detail="未找到二维码对应的物资")
    data = {
        "material": {
            "id": material.id,
            "public_id": material.public_id,
            "name": material.name,
            "spec": material.spec,
            "unit": material.unit,
            "category": material.category,
            "has_individual_tracking": bool(material.has_individual_tracking),
            "available_quantity": material_available_quantity(db, material),
        },
        "item": None,
        "actions": ["view", "apply"],
    }
    if item:
        data["item"] = {
            "code": item.code,
            "status": item.status,
            "warehouse_id": item.warehouse_id,
            "location_id": item.location_id,
        }
    return {"ok": True, "data": data, "msg": "识别成功"}

