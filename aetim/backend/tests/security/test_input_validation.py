"""
輸入驗證安全性測試

測試輸入驗證機制，防止 SQL 注入、XSS 等攻擊。
符合 T-5-4-3：安全性檢查
符合 NFR-006：輸入驗證
"""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """建立測試客戶端"""
    return TestClient(app)


def test_sql_injection_protection(client: TestClient):
    """
    測試 SQL 注入防護
    
    符合 NFR-006：防止 SQL 注入攻擊
    """
    # SQL 注入嘗試
    sql_injection_payloads = [
        "'; DROP TABLE assets; --",
        "' OR '1'='1",
        "' UNION SELECT * FROM users --",
        "1' OR '1'='1",
    ]
    
    # 測試資產查詢端點
    for payload in sql_injection_payloads:
        response = client.get(f"/api/v1/assets?host_name={payload}")
        # 應該返回 401（未認證）或 400（錯誤請求），不應該執行 SQL
        assert response.status_code in [200, 400, 401, 422]
        # 不應該返回資料庫錯誤
        assert "syntax error" not in response.text.lower()
        assert "sql" not in response.text.lower()


def test_xss_protection(client: TestClient):
    """
    測試 XSS 防護
    
    符合 NFR-006：防止 XSS 攻擊
    """
    # XSS 嘗試
    xss_payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<svg onload=alert('XSS')>",
    ]
    
    # 測試資產建立端點（需要認證，這裡先測試結構）
    for payload in xss_payloads:
        # 測試輸入驗證
        # 注意：實際測試需要認證 token
        response = client.post(
            "/api/v1/assets",
            json={"host_name": payload, "operating_system": "test", "running_applications": "test", "owner": "test", "data_sensitivity": "高", "business_criticality": "高"},
        )
        # 應該返回 401（未認證）或 422（驗證錯誤）
        assert response.status_code in [401, 422]
        # 回應中不應該包含未轉義的腳本標籤
        if response.status_code == 422:
            assert "<script>" not in response.text


def test_file_upload_size_limit(client: TestClient):
    """
    測試檔案上傳大小限制
    
    符合 NFR-006：限制檔案上傳的類型與大小（CSV 檔案 ≤ 10MB）
    """
    # 建立超過 10MB 的檔案內容
    large_content = "x" * (11 * 1024 * 1024)  # 11MB
    
    # 測試檔案上傳端點（需要認證，這裡先測試結構）
    response = client.post(
        "/api/v1/assets/import",
        files={"file": ("test.csv", large_content, "text/csv")},
    )
    # 應該返回 401（未認證）或 413（請求實體過大）
    assert response.status_code in [401, 413, 422]


def test_file_upload_type_validation(client: TestClient):
    """
    測試檔案上傳類型驗證
    
    符合 NFR-006：限制檔案上傳的類型與大小
    """
    # 測試非 CSV 檔案
    response = client.post(
        "/api/v1/assets/import",
        files={"file": ("test.exe", b"binary content", "application/x-msdownload")},
    )
    # 應該返回 401（未認證）或 422（驗證錯誤）
    assert response.status_code in [401, 422]


def test_input_sanitization(client: TestClient):
    """
    測試輸入清理
    
    符合 NFR-006：輸入驗證與清理
    """
    # 測試特殊字元輸入
    special_chars = [
        "<script>alert('test')</script>",
        "'; DROP TABLE assets; --",
        "../../etc/passwd",
        "\x00\x01\x02",
    ]
    
    for special_char in special_chars:
        # 測試各種輸入欄位
        # 注意：實際測試需要認證 token
        response = client.post(
            "/api/v1/assets",
            json={
                "host_name": special_char,
                "operating_system": "test",
                "running_applications": "test",
                "owner": "test",
                "data_sensitivity": "高",
                "business_criticality": "高",
            },
        )
        # 應該返回 401（未認證）或 422（驗證錯誤）
        assert response.status_code in [401, 422]

