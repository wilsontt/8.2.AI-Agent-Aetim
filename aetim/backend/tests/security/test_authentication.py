"""
身份驗證安全性測試

測試身份驗證與授權機制。
符合 T-5-4-3：安全性檢查
符合 AC-022-1, AC-022-2, AC-022-3, AC-022-4
"""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """建立測試客戶端"""
    return TestClient(app)


def test_unauthenticated_access(client: TestClient):
    """
    測試未認證存取保護
    
    符合 AC-022-1：OIDC/OAuth 2.0 身份驗證
    """
    # 測試受保護的端點
    protected_endpoints = [
        "/api/v1/assets",
        "/api/v1/threats",
        "/api/v1/reports",
        "/api/v1/system-status",
        "/api/v1/statistics/assets",
    ]
    
    for endpoint in protected_endpoints:
        response = client.get(endpoint)
        # 應該返回 401（未認證）
        assert response.status_code == 401, f"{endpoint} 應該需要認證"


def test_invalid_token(client: TestClient):
    """
    測試無效 Token
    
    符合 AC-022-3：登入失敗時顯示明確的錯誤訊息
    """
    # 使用無效的 token
    headers = {"Authorization": "Bearer invalid_token"}
    
    response = client.get("/api/v1/assets", headers=headers)
    # 應該返回 401（未認證）
    assert response.status_code == 401


def test_malformed_token(client: TestClient):
    """
    測試格式錯誤的 Token
    """
    # 使用格式錯誤的 token
    headers = {"Authorization": "Bearer malformed.token.here"}
    
    response = client.get("/api/v1/assets", headers=headers)
    # 應該返回 401（未認證）
    assert response.status_code == 401


def test_missing_authorization_header(client: TestClient):
    """
    測試缺少授權標頭
    """
    response = client.get("/api/v1/assets")
    # 應該返回 401（未認證）
    assert response.status_code == 401


def test_authorization_header_format(client: TestClient):
    """
    測試授權標頭格式驗證
    """
    # 測試各種格式錯誤的授權標頭
    invalid_headers = [
        {"Authorization": "InvalidFormat token"},
        {"Authorization": "Bearer"},
        {"Authorization": "Basic dXNlcjpwYXNz"},
    ]
    
    for headers in invalid_headers:
        response = client.get("/api/v1/assets", headers=headers)
        # 應該返回 401（未認證）
        assert response.status_code == 401

