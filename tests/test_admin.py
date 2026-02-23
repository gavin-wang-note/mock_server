import pytest
from fastapi.testclient import TestClient
from app.core.server import app
from app.models.route import Route, RouteCreate, RouteMatchRule, RouteResponse
from app.api.mock import add_route, remove_route
import time
import uuid


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def test_route():
    """创建测试路由"""
    route_id = f"test-route-{uuid.uuid4()}"
    route = Route(
        id=route_id,
        name="测试路由",
        enabled=True,
        match_rule=RouteMatchRule(
            path="/test/admin",
            methods=["GET"],
            headers=None,
            query_params=None,
            body=None,
            use_regex=False
        ),
        response=RouteResponse(
            status_code=200,
            content={"message": "Test Admin"},
            headers={"Content-Type": "application/json"},
            delay=0,
            delay_range=None,
            content_type="application/json"
        ),
        validator=None,
        tags=["test"],
        created_at=time.time(),
        updated_at=time.time()
    )
    add_route(route)
    yield route
    remove_route(route_id)


class TestAdmin:
    """测试管理界面相关功能"""

    def test_admin_root(self, client):
        """测试管理界面根路径"""
        response = client.get("/admin")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_admin_dashboard(self, client):
        """测试管理界面仪表盘"""
        response = client.get("/admin/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_admin_ui(self, client):
        """测试管理界面UI"""
        response = client.get("/admin/ui")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_login(self, client):
        """测试登录功能"""
        # 测试失败登录
        response = client.post("/login", json={"username": "admin", "password": "wrong"})
        assert response.status_code == 401
        
        # 测试成功登录
        response = client.post("/login", json={"username": "admin", "password": "password"})
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

    def test_get_routes(self, client, test_route):
        """测试获取路由列表"""
        response = client.get(
            "/admin/routes",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_get_routes_with_search(self, client, test_route):
        """测试搜索路由"""
        response = client.get(
            f"/admin/routes?search={test_route.name}",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_get_routes_with_sort(self, client, test_route):
        """测试排序路由"""
        response = client.get(
            "/admin/routes?sort=created_at&order=desc",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_get_route(self, client, test_route):
        """测试获取指定路由"""
        response = client.get(
            f"/admin/routes/{test_route.id}",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_route.id

    def test_delete_route(self, client, test_route):
        """测试删除路由"""
        response = client.delete(
            f"/admin/routes/{test_route.id}",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "路由删除成功"

    def test_get_requests(self, client):
        """测试获取请求历史"""
        response = client.get(
            "/admin/requests",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_get_config(self, client):
        """测试获取配置"""
        response = client.get(
            "/config",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "server" in data
        assert "admin" in data
        assert "storage" in data

    def test_get_envs(self, client):
        """测试获取环境列表"""
        response = client.get(
            "/config/envs",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "envs" in data
        assert isinstance(data["envs"], list)

    def test_get_cleanup_strategy(self, client):
        """测试获取清理策略"""
        response = client.get(
            "/data/cleanup/strategy",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert response.status_code == 200

    def test_get_request_trend(self, client):
        """测试获取请求趋势"""
        response = client.get(
            "/admin/analytics/request-trend",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert response.status_code == 200

    def test_get_response_time_stats(self, client):
        """测试获取响应时间统计"""
        response = client.get(
            "/admin/analytics/response-time",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert response.status_code == 200

    def test_get_status_code_stats(self, client):
        """测试获取状态码统计"""
        response = client.get(
            "/admin/analytics/status-codes",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert response.status_code == 200

    def test_get_method_stats(self, client):
        """测试获取请求方法统计"""
        response = client.get(
            "/admin/analytics/methods",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert response.status_code == 200

    def test_get_path_stats(self, client):
        """测试获取路径统计"""
        response = client.get(
            "/admin/analytics/paths",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert response.status_code == 200

    def test_get_summary_stats(self, client):
        """测试获取汇总统计"""
        response = client.get(
            "/admin/analytics/summary",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert response.status_code == 200

    def test_test_route(self, client):
        """测试测试路由"""
        response = client.get("/admin/test")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "测试成功"

    def test_routes_export(self, client):
        """测试导出路由"""
        response = client.get("/admin/routes-export")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        assert "Content-Disposition" in response.headers
