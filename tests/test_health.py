import pytest
from fastapi.testclient import TestClient
from app.core.server import app


class TestHealth:
    """测试健康检查端点"""

    def setup_method(self):
        """设置测试环境"""
        self.client = TestClient(app)

    def test_health_check(self):
        """测试健康检查端点"""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "uptime" in data
        assert "stats" in data

    def test_metrics(self):
        """测试指标端点"""
        response = self.client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "uptime_seconds" in data
        assert "total_requests" in data
        assert "average_response_time" in data
        assert "method_distribution" in data
        assert "config" in data

    def test_info(self):
        """测试信息端点"""
        response = self.client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Mock Server"
        assert "version" in data
        assert "description" in data
        assert "features" in data
        assert "endpoints" in data
