from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from services.import_service import import_from_excel

router = APIRouter()


MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("/import/excel")
async def import_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        return {"ok": False, "data": None, "msg": "仅支持 .xlsx 或 .xls 文件"}

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        return {"ok": False, "data": None, "msg": f"文件过大，最大支持 {MAX_UPLOAD_SIZE // 1024 // 1024} MB"}

    result = import_from_excel(db, contents)
    return {"ok": True, "data": result, "msg": f"导入完成: {result['imported']} 条成功, {result['skipped']} 条跳过"}