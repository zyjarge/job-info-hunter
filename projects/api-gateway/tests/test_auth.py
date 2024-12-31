from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_login_success():
    """测试登录成功"""
    response = client.post(
        "/api/v1/token", data={"username": "admin", "password": "secret"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_failed():
    """测试登录失败"""
    response = client.post(
        "/api/v1/token", data={"username": "admin", "password": "wrong_password"}
    )
    assert response.status_code == 401


def test_get_user_info():
    """测试获取用户信息"""
    # 先登录获取令牌
    login_response = client.post(
        "/api/v1/token", data={"username": "admin", "password": "secret"}
    )
    token = login_response.json()["access_token"]

    # 使用令牌获取用户信息
    response = client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "admin"


def test_get_user_info_without_token():
    """测试未授权访问"""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
