"""
AI 服務 API 整合測試

測試 AI 服務 API 端點的功能，包括：
- 提取威脅資訊 API
- 健康檢查 API
- 錯誤處理
- 日誌記錄
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.main import app


@pytest.fixture
def client():
    """建立 TestClient"""
    return TestClient(app)


class TestHealthCheckAPI:
    """健康檢查 API 測試"""
    
    def test_health_check(self, client):
        """測試健康檢查端點"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ai-service"
        assert "version" in data
    
    def test_health_check_v1(self, client):
        """測試健康檢查端點（API v1）"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_ai_health_check(self, client):
        """測試 AI 服務健康檢查端點"""
        response = client.get("/api/v1/ai/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestExtractAPI:
    """提取威脅資訊 API 測試"""
    
    def test_extract_threat_info_success(self, client):
        """測試成功提取威脅資訊"""
        request_data = {
            "text": "CVE-2024-12345 affects VMware ESXi 7.0.3. This is a phishing attack."
        }
        
        response = client.post("/api/v1/ai/extract", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "cve" in data
        assert "products" in data
        assert "ttps" in data
        assert "iocs" in data
        assert "confidence" in data
        
        assert isinstance(data["cve"], list)
        assert isinstance(data["products"], list)
        assert isinstance(data["ttps"], list)
        assert isinstance(data["iocs"], list)
        assert isinstance(data["confidence"], float)
        assert 0.0 <= data["confidence"] <= 1.0
    
    def test_extract_threat_info_with_cve(self, client):
        """測試提取包含 CVE 的威脅資訊"""
        request_data = {
            "text": "CVE-2024-12345 is a critical vulnerability"
        }
        
        response = client.post("/api/v1/ai/extract", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["cve"]) > 0
        assert "CVE-2024-12345" in data["cve"]
        assert data["confidence"] >= 0.3
    
    def test_extract_threat_info_with_products(self, client):
        """測試提取包含產品的威脅資訊"""
        request_data = {
            "text": "VMware ESXi 7.0.3 is affected"
        }
        
        response = client.post("/api/v1/ai/extract", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["products"]) > 0
        assert data["confidence"] >= 0.3
    
    def test_extract_threat_info_with_ttps(self, client):
        """測試提取包含 TTPs 的威脅資訊"""
        request_data = {
            "text": "This is a phishing attack"
        }
        
        response = client.post("/api/v1/ai/extract", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["ttps"]) > 0
        assert data["confidence"] >= 0.2
    
    def test_extract_threat_info_with_iocs(self, client):
        """測試提取包含 IOCs 的威脅資訊"""
        request_data = {
            "text": "IP: 192.168.1.1, Domain: malicious.com"
        }
        
        response = client.post("/api/v1/ai/extract", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["iocs"]) > 0
        assert data["confidence"] >= 0.2
    
    def test_extract_threat_info_empty_text(self, client):
        """測試空文字內容"""
        request_data = {
            "text": ""
        }
        
        response = client.post("/api/v1/ai/extract", json=request_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "不能為空" in data["detail"]
    
    def test_extract_threat_info_whitespace_text(self, client):
        """測試僅空白字元的文字內容"""
        request_data = {
            "text": "   "
        }
        
        response = client.post("/api/v1/ai/extract", json=request_data)
        
        assert response.status_code == 400
    
    def test_extract_threat_info_missing_text(self, client):
        """測試缺少 text 欄位"""
        request_data = {}
        
        response = client.post("/api/v1/ai/extract", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_extract_threat_info_invalid_json(self, client):
        """測試無效的 JSON"""
        response = client.post(
            "/api/v1/ai/extract",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        
        assert response.status_code == 422


class TestSummarizeAPI:
    """生成摘要 API 測試"""
    
    def test_summarize_success(self, client):
        """測試成功生成摘要"""
        request_data = {
            "content": "This is a long threat intelligence report...",
            "target_length": 200,
            "language": "zh-TW",
            "style": "executive",
        }
        
        response = client.post("/api/v1/ai/summarize", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
    
    def test_summarize_empty_content(self, client):
        """測試空內容"""
        request_data = {
            "content": "",
        }
        
        response = client.post("/api/v1/ai/summarize", json=request_data)
        
        assert response.status_code == 400


class TestTranslateToBusinessAPI:
    """轉換為業務語言 API 測試"""
    
    def test_translate_to_business_success(self, client):
        """測試成功轉換為業務語言"""
        request_data = {
            "content": "Technical description of the vulnerability...",
        }
        
        response = client.post("/api/v1/ai/translate-to-business", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
    
    def test_translate_to_business_empty_content(self, client):
        """測試空內容"""
        request_data = {
            "content": "",
        }
        
        response = client.post("/api/v1/ai/translate-to-business", json=request_data)
        
        assert response.status_code == 400


class TestErrorHandling:
    """錯誤處理測試"""
    
    def test_extract_service_error_handling(self, client):
        """測試提取服務錯誤處理"""
        # 使用 mock 讓提取服務拋出異常
        with patch("app.main.extraction_service") as mock_service:
            mock_service.extract.side_effect = Exception("Service error")
            
            request_data = {
                "text": "Test text"
            }
            
            response = client.post("/api/v1/ai/extract", json=request_data)
            
            # 應返回 500 錯誤
            assert response.status_code == 500
            data = response.json()
            assert "錯誤" in data["detail"]


class TestOpenAPIDocumentation:
    """OpenAPI 文件測試"""
    
    def test_openapi_schema_exists(self, client):
        """測試 OpenAPI Schema 存在"""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
    
    def test_openapi_paths_defined(self, client):
        """測試 OpenAPI 路徑已定義"""
        response = client.get("/openapi.json")
        schema = response.json()
        
        paths = schema["paths"]
        
        # 檢查主要端點是否存在
        assert "/api/v1/ai/extract" in paths
        assert "/api/v1/ai/summarize" in paths
        assert "/api/v1/ai/translate-to-business" in paths
        assert "/api/v1/ai/health" in paths
    
    def test_openapi_extract_endpoint_schema(self, client):
        """測試提取端點的 OpenAPI Schema"""
        response = client.get("/openapi.json")
        schema = response.json()
        
        extract_path = schema["paths"]["/api/v1/ai/extract"]
        
        # 檢查 POST 方法存在
        assert "post" in extract_path
        
        # 檢查請求模型
        post_schema = extract_path["post"]
        assert "requestBody" in post_schema
        
        # 檢查回應模型
        assert "responses" in post_schema
        assert "200" in post_schema["responses"]

