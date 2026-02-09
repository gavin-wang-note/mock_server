import pytest
from app.services.router import Router
from app.models.route import Route, RouteMatchRule, RouteResponse


class TestRouter:
    """测试路由匹配服务"""

    def setup_method(self):
        """设置测试环境"""
        self.router = Router()
        # 创建测试路由
        self.route1 = Route(
            id="test-route-1",
            name="测试路由1",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/users",
                methods=["GET"],
                headers={},
                query_params={},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content={"message": "Hello"},
                delay=0.0
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )
        self.route2 = Route(
            id="test-route-2",
            name="测试路由2",
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
                content={"message": "Hello"},
                delay=0.0
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )

    def test_add_route(self):
        """测试添加路由"""
        self.router.add_route(self.route1)
        routes = self.router.get_all_routes()
        assert len(routes) == 1
        assert routes[0].id == "test-route-1"

    def test_remove_route(self):
        """测试删除路由"""
        self.router.add_route(self.route1)
        self.router.remove_route("test-route-1")
        routes = self.router.get_all_routes()
        assert len(routes) == 0

    def test_update_route(self):
        """测试更新路由"""
        self.router.add_route(self.route1)
        # 创建更新后的路由
        updated_route = Route(
            id="test-route-1",
            name="更新后的测试路由",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/users",
                methods=["GET", "POST"],
                headers={},
                query_params={},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content={"message": "Updated"},
                delay=0.0
            ),
            created_at=1234567890.0,
            updated_at=1234567891.0
        )
        self.router.update_route(updated_route)
        route = self.router.get_route("test-route-1")
        assert route.name == "更新后的测试路由"
        assert "POST" in route.match_rule.methods

    def test_match_route_exact(self):
        """测试精确路径匹配"""
        self.router.add_route(self.route1)
        matched = self.router.match_route(
            method="GET",
            path="/api/users",
            headers={},
            query_params={},
            body=None
        )
        assert matched is not None
        assert matched[0].id == "test-route-1"
        assert matched[1] == {}

    def test_match_route_with_params(self):
        """测试带参数的路径匹配"""
        self.router.add_route(self.route2)
        matched = self.router.match_route(
            method="GET",
            path="/api/users/123",
            headers={},
            query_params={},
            body=None
        )
        assert matched is not None
        assert matched[0].id == "test-route-2"
        assert matched[1] == {"id": "123"}

    def test_match_route_no_match(self):
        """测试无匹配的情况"""
        self.router.add_route(self.route1)
        matched = self.router.match_route(
            method="POST",
            path="/api/users",
            headers={},
            query_params={},
            body=None
        )
        assert matched is None

    def test_match_route_with_headers(self):
        """测试带头部匹配"""
        # 创建带头部匹配的路由
        route_with_headers = Route(
            id="test-route-3",
            name="测试路由3",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/users",
                methods=["GET"],
                headers={"X-API-Key": "test-key"},
                query_params={},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content={"message": "Hello"},
                delay=0.0
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )
        self.router.add_route(route_with_headers)
        # 带正确头部的请求
        matched_with_headers = self.router.match_route(
            method="GET",
            path="/api/users",
            headers={"X-API-Key": "test-key"},
            query_params={},
            body=None
        )
        assert matched_with_headers is not None
        # 带错误头部的请求
        matched_no_headers = self.router.match_route(
            method="GET",
            path="/api/users",
            headers={"X-API-Key": "wrong-key"},
            query_params={},
            body=None
        )
        assert matched_no_headers is None

    def test_match_route_with_query_params(self):
        """测试带查询参数匹配"""
        # 创建带查询参数匹配的路由
        route_with_query = Route(
            id="test-route-4",
            name="测试路由4",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/users",
                methods=["GET"],
                headers={},
                query_params={"page": "1", "size": "10"},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content={"message": "Hello"},
                delay=0.0
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )
        self.router.add_route(route_with_query)
        # 带正确查询参数的请求
        matched_with_query = self.router.match_route(
            method="GET",
            path="/api/users",
            headers={},
            query_params={"page": "1", "size": "10"},
            body=None
        )
        assert matched_with_query is not None
        # 带错误查询参数的请求
        matched_no_query = self.router.match_route(
            method="GET",
            path="/api/users",
            headers={},
            query_params={"page": "2", "size": "10"},
            body=None
        )
        assert matched_no_query is None

    def test_route_specificity(self):
        """测试路由特异性排序"""
        # 创建多个路由，测试排序
        route_generic = Route(
            id="test-route-generic",
            name="通用路由",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/*",
                methods=["GET"],
                headers={},
                query_params={},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content={"message": "Generic"},
                delay=0.0
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )
        route_specific = Route(
            id="test-route-specific",
            name="具体路由",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/users",
                methods=["GET"],
                headers={},
                query_params={},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content={"message": "Specific"},
                delay=0.0
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )
        self.router.add_route(route_generic)
        self.router.add_route(route_specific)
        # 匹配应该返回更具体的路由
        matched = self.router.match_route(
            method="GET",
            path="/api/users",
            headers={},
            query_params={},
            body=None
        )
        assert matched is not None
        assert matched[0].id == "test-route-specific"
