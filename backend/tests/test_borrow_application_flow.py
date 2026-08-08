from conftest import login


def _bulk_material(client):
    materials = client.get("/api/materials").json()["data"]
    return next(item for item in materials if not item["has_individual_tracking"] and item["available_quantity"] > 0)


def test_approve_pickup_return_changes_stock_only_at_confirmation(client):
    student_headers, _ = login(client, "mock:student-flow", "流程学生", student_no="20260002")
    operator_headers, _ = login(client, "mock:operator-flow", "仓库操作员", role="operator")
    material = _bulk_material(client)
    initial_stock = material["available_quantity"]

    created = client.post("/api/borrow-applications", headers=student_headers, json={
        "material_id": material["id"], "quantity": 1, "purpose": "课程活动"
    })
    assert created.status_code == 200
    application_id = created.json()["data"]["id"]

    approved = client.post(
        f"/api/borrow-applications/{application_id}/approve",
        headers=operator_headers,
        json={"note": "同意", "reservation_hours": 48},
    )
    assert approved.status_code == 200
    # Physical stock is unchanged; reservable stock is reduced by one.
    after_approval = client.get(f"/api/materials/{material['id']}").json()["data"]
    assert after_approval["total_quantity"] == material["total_quantity"]
    assert after_approval["available_quantity"] == initial_stock - 1

    pickup_key = "pickup-flow-0001"
    picked_up = client.post(
        f"/api/borrow-applications/{application_id}/confirm-pickup",
        headers=operator_headers,
        json={"idempotency_key": pickup_key},
    )
    assert picked_up.status_code == 200
    duplicate = client.post(
        f"/api/borrow-applications/{application_id}/confirm-pickup",
        headers=operator_headers,
        json={"idempotency_key": pickup_key},
    )
    assert duplicate.status_code == 200
    after_pickup = client.get(f"/api/materials/{material['id']}").json()["data"]
    assert after_pickup["total_quantity"] == material["total_quantity"] - 1

    requested = client.post(
        f"/api/borrow-applications/{application_id}/request-return", headers=student_headers
    )
    assert requested.status_code == 200
    returned = client.post(
        f"/api/borrow-applications/{application_id}/confirm-return",
        headers=operator_headers,
        json={"idempotency_key": "return-flow-0001"},
    )
    assert returned.status_code == 200
    final_stock = client.get(f"/api/materials/{material['id']}").json()["data"]
    assert final_stock["total_quantity"] == material["total_quantity"]


def test_student_only_sees_own_applications(client):
    first_headers, _ = login(client, "mock:first", "第一位学生", student_no="20260003")
    second_headers, _ = login(client, "mock:second", "第二位学生", student_no="20260004")
    material = _bulk_material(client)
    client.post("/api/borrow-applications", headers=first_headers, json={
        "material_id": material["id"], "quantity": 1
    })
    mine = client.get("/api/borrow-applications/mine", headers=second_headers).json()["data"]
    assert mine["total"] == 0


def test_legacy_and_new_item_qr_are_both_resolved(client):
    student_headers, _ = login(client, "mock:scanner", "扫码学生")
    materials = client.get("/api/materials").json()["data"]
    individual = next(item for item in materials if item["has_individual_tracking"])
    items = client.get(f"/api/inventory/items/{individual['id']}").json()["data"]
    item_code = items[0]["code"]
    for payload in (f"ITEM:{item_code}", f"MATERIAL:ac-remote:{item_code}"):
        response = client.post("/api/scan/resolve", headers=student_headers, json={"payload": payload})
        assert response.status_code == 200
        assert response.json()["data"]["item"]["code"] == item_code

