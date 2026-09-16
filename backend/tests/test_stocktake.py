import pytest
from sqlalchemy.orm import Session

from conftest import login
from database import SessionLocal
from models import (
    InventoryBatch,
    InventoryItem,
    InventoryTransaction,
    Material,
    Stocktake,
    StorageLocation,
    Warehouse,
)


def _create(client, headers):
    response = client.post("/api/stocktake", headers=headers, json={"note": "自动化盘点"})
    assert response.status_code == 200, response.text
    stocktake_id = response.json()["data"]["id"]
    return stocktake_id, client.get(f"/api/stocktake/{stocktake_id}", headers=headers).json()["data"]


def _count_entries(client, headers, stocktake_id, detail, skip_code=None, extra_code=None):
    for entry in detail["entries"]:
        if entry["counted"]:
            continue
        if entry["is_individual"]:
            for check in entry["checks"]:
                if check["expected"] and check["item_code"] != skip_code:
                    response = client.post(
                        f"/api/stocktake/{stocktake_id}/entry/{entry['id']}/scan",
                        headers=headers,
                        json={"payload": f"ITEM:{check['item_code']}"},
                    )
                    assert response.status_code == 200, response.text
            if extra_code:
                response = client.post(
                    f"/api/stocktake/{stocktake_id}/entry/{entry['id']}/scan",
                    headers=headers,
                    json={"payload": f"ITEM:{extra_code}"},
                )
                assert response.status_code == 200, response.text
                extra_code = None
            response = client.post(
                f"/api/stocktake/{stocktake_id}/entry/{entry['id']}/confirm",
                headers=headers,
            )
            assert response.status_code == 200, response.text
        else:
            response = client.put(
                f"/api/stocktake/{stocktake_id}/entry/{entry['id']}",
                headers=headers,
                json={"actual_quantity": entry["book_quantity"]},
            )
            assert response.status_code == 200, response.text


def test_stocktake_requires_operator_and_snapshots_each_location(client):
    student_headers, _ = login(client, "mock:stocktake-student", "学生")
    denied = client.get("/api/stocktake", headers=student_headers)
    assert denied.status_code == 403

    operator_headers, _ = login(client, "mock:stocktake-operator", "操作员", role="operator")
    stocktake_id, detail = _create(client, operator_headers)
    pen_entries = [entry for entry in detail["entries"] if entry["material_name"] == "笔"]
    assert len(pen_entries) == 2
    assert {(entry["warehouse_name"], entry["location_code"]) for entry in pen_entries} == {
        ("主仓库", "A-2-1"),
        ("回收仓", "B-1-1"),
    }
    duplicate = client.post("/api/stocktake", headers=operator_headers, json={"note": "重复"})
    assert duplicate.status_code == 409
    incomplete = client.post(f"/api/stocktake/{stocktake_id}/complete", headers=operator_headers)
    assert incomplete.status_code == 409
    assert "未确认" in incomplete.json()["msg"]


def test_bulk_adjustment_updates_only_the_counted_location(client):
    headers, _ = login(client, "mock:stocktake-admin", "管理员", role="admin")
    stocktake_id, detail = _create(client, headers)
    target = next(
        entry for entry in detail["entries"]
        if entry["material_name"] == "笔" and entry["warehouse_name"] == "主仓库"
    )
    _count_entries(client, headers, stocktake_id, detail)
    changed = client.put(
        f"/api/stocktake/{stocktake_id}/entry/{target['id']}",
        headers=headers,
        json={"actual_quantity": target["book_quantity"] - 3},
    )
    assert changed.status_code == 200
    completed = client.post(
        f"/api/stocktake/{stocktake_id}/complete?apply_fix=true", headers=headers
    )
    assert completed.status_code == 200, completed.text

    db = SessionLocal()
    try:
        material = db.query(Material).filter(Material.name == "笔").one()
        main = db.query(Warehouse).filter(Warehouse.name == "主仓库").one()
        recycling = db.query(Warehouse).filter(Warehouse.name == "回收仓").one()
        assert db.query(InventoryBatch).filter_by(material_id=material.id, warehouse_id=main.id).one().quantity == 52
        assert db.query(InventoryBatch).filter_by(material_id=material.id, warehouse_id=recycling.id).one().quantity == 5
        transaction = db.query(InventoryTransaction).filter_by(action="stocktake_adjust").one()
        assert transaction.quantity == -3
    finally:
        db.close()


def test_individual_scan_marks_missing_and_adds_unique_surplus(client):
    headers, _ = login(client, "mock:stocktake-items", "管理员", role="admin")
    stocktake_id, detail = _create(client, headers)
    individual = next(entry for entry in detail["entries"] if entry["is_individual"])
    missing_code = individual["checks"][0]["item_code"]
    _count_entries(
        client,
        headers,
        stocktake_id,
        detail,
        skip_code=missing_code,
        extra_code="AC-999",
    )
    completed = client.post(
        f"/api/stocktake/{stocktake_id}/complete?apply_fix=true", headers=headers
    )
    assert completed.status_code == 200, completed.text

    db = SessionLocal()
    try:
        missing = db.query(InventoryItem).filter(InventoryItem.code == missing_code).one()
        extra = db.query(InventoryItem).filter(InventoryItem.code == "AC-999").one()
        assert missing.status == "missing"
        assert extra.status == "available"
        available = db.query(InventoryItem).filter(InventoryItem.status == "available").count()
        assert available == 20
    finally:
        db.close()


def test_individual_scan_moves_item_without_marking_it_missing(client):
    headers, _ = login(client, "mock:stocktake-item-move", "管理员", role="admin")
    db = SessionLocal()
    try:
        first = db.query(InventoryItem).order_by(InventoryItem.id).first()
        target_location = db.query(StorageLocation).filter(
            StorageLocation.warehouse_id == first.warehouse_id,
            StorageLocation.id != first.location_id,
        ).first()
        first.location_id = target_location.id
        db.commit()
        target_location_id = target_location.id
    finally:
        db.close()

    stocktake_id, detail = _create(client, headers)
    individual_entries = [entry for entry in detail["entries"] if entry["is_individual"]]
    destination = next(entry for entry in individual_entries if entry["location_id"] == target_location_id)
    origin = next(entry for entry in individual_entries if entry["id"] != destination["id"])
    moved_code = origin["checks"][0]["item_code"]

    for entry in detail["entries"]:
        if entry["is_individual"]:
            for check in entry["checks"]:
                if check["item_code"] != moved_code:
                    response = client.post(
                        f"/api/stocktake/{stocktake_id}/entry/{entry['id']}/scan",
                        headers=headers,
                        json={"payload": f"ITEM:{check['item_code']}"},
                    )
                    assert response.status_code == 200, response.text
            if entry["id"] == destination["id"]:
                response = client.post(
                    f"/api/stocktake/{stocktake_id}/entry/{entry['id']}/scan",
                    headers=headers,
                    json={"payload": f"ITEM:{moved_code}"},
                )
                assert response.status_code == 200, response.text
            response = client.post(
                f"/api/stocktake/{stocktake_id}/entry/{entry['id']}/confirm",
                headers=headers,
            )
            assert response.status_code == 200, response.text
        else:
            response = client.put(
                f"/api/stocktake/{stocktake_id}/entry/{entry['id']}",
                headers=headers,
                json={"actual_quantity": entry["book_quantity"]},
            )
            assert response.status_code == 200, response.text

    completed = client.post(
        f"/api/stocktake/{stocktake_id}/complete?apply_fix=true", headers=headers
    )
    assert completed.status_code == 200, completed.text
    db = SessionLocal()
    try:
        moved = db.query(InventoryItem).filter(InventoryItem.code == moved_code).one()
        assert moved.status == "available"
        assert moved.location_id == target_location_id
    finally:
        db.close()


def test_borrowed_item_cannot_be_reintroduced_by_stocktake(client):
    headers, _ = login(client, "mock:stocktake-borrowed", "操作员", role="operator")
    material = next(item for item in client.get("/api/materials").json()["data"] if item["has_individual_tracking"])
    item = client.get(f"/api/inventory/items/{material['id']}").json()["data"][0]
    borrowed = client.post("/api/borrow", headers=headers, json={
        "material_id": material["id"], "quantity": 1, "borrower": "测试", "item_code": item["code"]
    })
    assert borrowed.status_code == 200 and borrowed.json()["ok"]
    stocktake_id, detail = _create(client, headers)
    individual = next(entry for entry in detail["entries"] if entry["is_individual"])
    response = client.post(
        f"/api/stocktake/{stocktake_id}/entry/{individual['id']}/scan",
        headers=headers,
        json={"payload": f"ITEM:{item['code']}"},
    )
    assert response.status_code == 409
    assert "借出状态" in response.json()["msg"]


def test_missing_item_cannot_be_borrowed(client):
    headers, _ = login(client, "mock:stocktake-missing-borrow", "操作员", role="operator")
    material = next(item for item in client.get("/api/materials").json()["data"] if item["has_individual_tracking"])
    item = client.get(f"/api/inventory/items/{material['id']}").json()["data"][0]

    db = SessionLocal()
    try:
        tracked = db.query(InventoryItem).filter(InventoryItem.id == item["id"]).one()
        tracked.status = "missing"
        db.commit()
    finally:
        db.close()

    response = client.post("/api/borrow", headers=headers, json={
        "material_id": material["id"], "quantity": 1,
        "borrower": "测试", "item_code": item["code"],
    })
    assert response.status_code == 200
    assert not response.json()["ok"]
    assert "盘点缺失" in response.json()["msg"]


def test_stale_snapshot_blocks_inventory_correction(client):
    headers, _ = login(client, "mock:stocktake-stale", "管理员", role="admin")
    stocktake_id, detail = _create(client, headers)
    _count_entries(client, headers, stocktake_id, detail)
    target = next(entry for entry in detail["entries"] if not entry["is_individual"])

    db = SessionLocal()
    try:
        batch = db.query(InventoryBatch).filter(
            InventoryBatch.material_id == target["material_id"],
            InventoryBatch.warehouse_id == target["warehouse_id"],
            InventoryBatch.location_id == target["location_id"],
        ).first()
        batch.quantity += 1
        db.commit()
    finally:
        db.close()

    response = client.post(
        f"/api/stocktake/{stocktake_id}/complete?apply_fix=true", headers=headers
    )
    assert response.status_code == 409
    assert "库存已变化" in response.json()["msg"]


def test_failed_completion_rolls_back_every_adjustment(client, monkeypatch):
    headers, _ = login(client, "mock:stocktake-rollback", "管理员", role="admin")
    stocktake_id, detail = _create(client, headers)
    _count_entries(client, headers, stocktake_id, detail)
    target = next(entry for entry in detail["entries"] if not entry["is_individual"])
    response = client.put(
        f"/api/stocktake/{stocktake_id}/entry/{target['id']}",
        headers=headers,
        json={"actual_quantity": target["book_quantity"] - 1},
    )
    assert response.status_code == 200

    original_commit = Session.commit

    def fail_commit(_session):
        raise RuntimeError("simulated database failure")

    monkeypatch.setattr(Session, "commit", fail_commit)
    with pytest.raises(RuntimeError, match="simulated database failure"):
        client.post(f"/api/stocktake/{stocktake_id}/complete?apply_fix=true", headers=headers)
    monkeypatch.setattr(Session, "commit", original_commit)

    db = SessionLocal()
    try:
        persisted = db.query(Stocktake).filter(Stocktake.id == stocktake_id).one()
        assert persisted.status == "in_progress"
        batch = db.query(InventoryBatch).filter(
            InventoryBatch.material_id == target["material_id"],
            InventoryBatch.warehouse_id == target["warehouse_id"],
            InventoryBatch.location_id == target["location_id"],
        ).first()
        assert batch.quantity == target["book_quantity"]
        assert db.query(InventoryTransaction).filter_by(action="stocktake_adjust").count() == 0
    finally:
        db.close()


def test_surplus_entry_creates_a_new_location_batch(client):
    headers, _ = login(client, "mock:stocktake-surplus", "管理员", role="admin")
    stocktake_id, detail = _create(client, headers)
    water = next(item for item in client.get("/api/materials").json()["data"] if item["name"] == "饮用水")
    warehouses = client.get("/api/warehouses").json()["data"]
    main = next(item for item in warehouses if item["name"] == "主仓库")
    locations = client.get("/api/locations").json()["data"]
    location = next(item for item in locations if item["warehouse_id"] == main["id"] and item["full_code"] == "A-1-1")
    added = client.post(f"/api/stocktake/{stocktake_id}/entries", headers=headers, json={
        "material_id": water["id"],
        "warehouse_id": main["id"],
        "location_id": location["id"],
        "actual_quantity": 3,
    })
    assert added.status_code == 200, added.text
    detail = client.get(f"/api/stocktake/{stocktake_id}", headers=headers).json()["data"]
    _count_entries(client, headers, stocktake_id, detail)
    response = client.post(
        f"/api/stocktake/{stocktake_id}/complete?apply_fix=true", headers=headers
    )
    assert response.status_code == 200, response.text

    db = SessionLocal()
    try:
        batch = db.query(InventoryBatch).filter_by(
            material_id=water["id"], warehouse_id=main["id"], location_id=location["id"]
        ).one()
        assert batch.quantity == 3
    finally:
        db.close()
