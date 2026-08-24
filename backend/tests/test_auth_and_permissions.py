from conftest import login


def test_student_cannot_call_inventory_write_api(client):
    student_headers, _ = login(client, "mock:student-1", "学生一", student_no="20260001")
    response = client.post("/api/materials", headers=student_headers, json={
        "name": "无权限创建",
        "unit": "个",
        "category": "consumable",
        "sub_category": "direct_consumption",
    })
    assert response.status_code == 403
    assert response.json()["ok"] is False


def test_operator_cannot_read_admin_settings(client):
    operator_headers, _ = login(client, "mock:operator-1", "操作员", role="operator")
    response = client.get("/api/admin/settings", headers=operator_headers)
    assert response.status_code == 403


def test_refresh_token_is_rotated_and_logout_revokes_it(client):
    _, data = login(client, "mock:student-2", "学生二")
    old_refresh = data["refresh_token"]
    refreshed = client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert refreshed.status_code == 200
    assert refreshed.json()["data"]["refresh_token"] != old_refresh
    reused = client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert reused.status_code == 401


def test_only_admin_can_change_user_role(client):
    student_headers, student_data = login(client, "mock:role-target", "待授权学生")
    operator_headers, _ = login(client, "mock:role-operator", "操作员", role="operator")
    admin_headers, _ = login(client, "mock:role-admin", "管理员", role="admin")
    user_id = student_data["user"]["id"]
    denied = client.put(f"/api/users/{user_id}", headers=operator_headers, json={"role": "operator"})
    assert denied.status_code == 403
    updated = client.put(f"/api/users/{user_id}", headers=admin_headers, json={"role": "operator"})
    assert updated.status_code == 200
    assert updated.json()["data"]["role"] == "operator"
