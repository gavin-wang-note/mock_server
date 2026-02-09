import pytest
from fastapi.testclient import TestClient
from app.core.server import app
from app.api.mock import add_route
from app.models.route import Route, RouteMatchRule, RouteResponse


class TestMock:
    """测试Mock API端点"""

    def setup_method(self):
        """设置测试环境"""
        self.client = TestClient(app)
        # 创建测试路由
        self.test_route = Route(
            id="test-mock-route",
            name="Mock测试路由",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/test",
                methods=["GET"],
                headers={},
                query_params={},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content={"message": "Mock Test", "timestamp": "{{now}}"},
                delay=0.0
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )
        # 添加测试路由
        add_route(self.test_route)

    def test_mock_get_request(self):
        """测试GET请求"""
        response = self.client.get("/api/test")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Mock Test"
        assert "timestamp" in data

    def test_mock_post_request(self):
        """测试POST请求"""
        # 创建POST路由
        post_route = Route(
            id="test-mock-post",
            name="Mock POST测试路由",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/test",
                methods=["POST"],
                headers={},
                query_params={},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=201,
                headers={"Content-Type": "application/json"},
                content={"message": "Created", "name": "{{body.name}}"},
                delay=0.0
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )
        add_route(post_route)
        # 发送POST请求
        response = self.client.post("/api/test", json={"name": "Test User"})
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Created"
        assert data["name"] == "Test User"

    def test_mock_route_not_found(self):
        """测试未找到路由的情况"""
        response = self.client.get("/api/not-found")
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "No matching route found"

    def test_mock_with_path_params(self):
        """测试带路径参数的路由"""
        # 创建带路径参数的路由
        param_route = Route(
            id="test-mock-param",
            name="Mock参数测试路由",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/users/{id}",
                methods=["GET"],
                headers={},
                query_params={},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content={"user_id": "{{path.id}}", "message": "User {{path.id}}"},
                delay=0.0
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )
        add_route(param_route)
        # 测试带参数的请求
        response = self.client.get("/api/users/456")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "456"
        assert data["message"] == "User 456"
