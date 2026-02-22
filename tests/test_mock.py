import pytest
from fastapi.testclient import TestClient
from app.core.server import app
from app.api.mock import add_route
from app.models.route import Route, RouteMatchRule, RouteResponse, RouteValidator
from app.core.security import create_access_token


class TestMock:
    """测试Mock API端点"""

    def setup_method(self):
        """设置测试环境"""
        from app.api.mock import mock_router
        # 清除现有的路由
        mock_router.routes.clear()
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

    def test_mock_jwt_auth_success(self):
        """测试JWT认证成功的情况"""
        # 创建JWT令牌
        token = create_access_token(data={"sub": "test-user"})
        
        # 创建需要JWT认证的路由
        jwt_route = Route(
            id="test-jwt-auth",
            name="JWT认证测试路由",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/auth/jwt",
                methods=["GET"],
                headers={},
                query_params={},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content={"message": "JWT认证成功"},
                delay=0.0
            ),
            validator=RouteValidator(
                validate_jwt=True,
                error_response=RouteResponse(
                    status_code=401,
                    headers={"Content-Type": "application/json"},
                    content={"error": "无效的认证令牌"},
                    delay=0.0
                )
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )
        add_route(jwt_route)
        
        # 发送带JWT令牌的请求
        response = self.client.get("/api/auth/jwt", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "JWT认证成功"

    def test_mock_jwt_auth_failure(self):
        """测试JWT认证失败的情况"""
        # 创建需要JWT认证的路由
        jwt_route = Route(
            id="test-jwt-auth-fail",
            name="JWT认证失败测试路由",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/auth/jwt/fail",
                methods=["GET"],
                headers={},
                query_params={},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content={"message": "JWT认证成功"},
                delay=0.0
            ),
            validator=RouteValidator(
                validate_jwt=True,
                error_response=RouteResponse(
                    status_code=401,
                    headers={"Content-Type": "application/json"},
                    content={"error": "无效的认证令牌"},
                    delay=0.0
                )
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )
        add_route(jwt_route)
        
        # 发送带无效JWT令牌的请求
        response = self.client.get("/api/auth/jwt/fail", headers={"Authorization": "Bearer invalid-token"})
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "无效的认证令牌"

    def test_mock_oauth_auth_success(self):
        """测试OAuth认证成功的情况"""
        # 创建需要OAuth认证的路由
        oauth_route = Route(
            id="test-oauth-auth",
            name="OAuth认证测试路由",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/auth/oauth",
                methods=["GET"],
                headers={},
                query_params={},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content={"message": "OAuth认证成功"},
                delay=0.0
            ),
            validator=RouteValidator(
                validate_oauth=True,
                oauth_token="valid-oauth-token",
                error_response=RouteResponse(
                    status_code=401,
                    headers={"Content-Type": "application/json"},
                    content={"error": "无效的OAuth令牌"},
                    delay=0.0
                )
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )
        add_route(oauth_route)
        
        # 发送带有效OAuth令牌的请求
        response = self.client.get("/api/auth/oauth", headers={"Authorization": "Bearer valid-oauth-token"})
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "OAuth认证成功"

    def test_mock_oauth_auth_failure(self):
        """测试OAuth认证失败的情况"""
        # 创建需要OAuth认证的路由
        oauth_route = Route(
            id="test-oauth-auth-fail",
            name="OAuth认证失败测试路由",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/auth/oauth/fail",
                methods=["GET"],
                headers={},
                query_params={},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content={"message": "OAuth认证成功"},
                delay=0.0
            ),
            validator=RouteValidator(
                validate_oauth=True,
                oauth_token="valid-oauth-token",
                error_response=RouteResponse(
                    status_code=401,
                    headers={"Content-Type": "application/json"},
                    content={"error": "无效的OAuth令牌"},
                    delay=0.0
                )
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )
        add_route(oauth_route)
        
        # 发送带无效OAuth令牌的请求
        response = self.client.get("/api/auth/oauth/fail", headers={"Authorization": "Bearer invalid-oauth-token"})
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "无效的OAuth令牌"

    def test_mock_delay(self):
        """测试响应延迟功能"""
        import time
        
        # 创建带延迟的路由
        delay_route = Route(
            id="test-mock-delay",
            name="延迟测试路由",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/delay",
                methods=["GET"],
                headers={},
                query_params={},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content={"message": "延迟测试"},
                delay=0.1  # 100ms延迟
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )
        add_route(delay_route)
        
        # 测试延迟
        start_time = time.time()
        response = self.client.get("/api/delay")
        end_time = time.time()
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "延迟测试"
        
        # 验证延迟时间
        elapsed_time = end_time - start_time
        assert elapsed_time >= 0.1, f"延迟时间不足，实际延迟: {elapsed_time}秒"

    def test_mock_server_error(self):
        """测试服务器错误场景模拟"""
        # 创建模拟服务器错误的路由
        error_route = Route(
            id="test-mock-server-error",
            name="服务器错误测试路由",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/error/server",
                methods=["GET"],
                headers={},
                query_params={},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content={"message": "正常响应"},
                delay=0.0,
                simulate_error=True,
                error_type="server_error",
                error_probability=1.0  # 100%概率发生错误
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )
        add_route(error_route)
        
        # 测试服务器错误
        response = self.client.get("/api/error/server")
        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "Internal Server Error"

    def test_mock_network_error(self):
        """测试网络错误场景模拟"""
        # 创建模拟网络错误的路由
        error_route = Route(
            id="test-mock-network-error",
            name="网络错误测试路由",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/error/network",
                methods=["GET"],
                headers={},
                query_params={},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content={"message": "正常响应"},
                delay=0.0,
                simulate_error=True,
                error_type="network_error",
                error_probability=1.0  # 100%概率发生错误
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )
        add_route(error_route)
        
        # 测试网络错误
        response = self.client.get("/api/error/network")
        assert response.status_code == 503
        data = response.json()
        assert data["error"] == "Service Unavailable"

    def test_mock_error_probability(self):
        """测试错误发生概率功能"""
        # 创建带错误概率的路由
        error_route = Route(
            id="test-mock-error-probability",
            name="错误概率测试路由",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/error/probability",
                methods=["GET"],
                headers={},
                query_params={},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content={"message": "正常响应"},
                delay=0.0,
                simulate_error=True,
                error_type="server_error",
                error_probability=0.0  # 0%概率发生错误
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )
        add_route(error_route)
        
        # 测试错误概率
        response = self.client.get("/api/error/probability")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "正常响应"

    def test_mock_dynamic_body_params(self):
        """测试基于请求体参数的动态响应"""
        # 创建基于请求体参数的动态响应路由
        dynamic_route = Route(
            id="test-mock-dynamic-body",
            name="请求体参数动态响应测试路由",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/dynamic/body",
                methods=["POST"],
                headers={},
                query_params={},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content={"message": "Hello {{body.name}}", "age": "{{body.age}}"},
                delay=0.0
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )
        add_route(dynamic_route)
        
        # 测试基于请求体参数的动态响应
        response = self.client.post("/api/dynamic/body", json={"name": "Test User", "age": 25})
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello Test User"
        assert data["age"] == "25"

    def test_mock_dynamic_query_params(self):
        """测试基于查询参数的动态响应"""
        # 创建基于查询参数的动态响应路由
        dynamic_route = Route(
            id="test-mock-dynamic-query",
            name="查询参数动态响应测试路由",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/dynamic/query",
                methods=["GET"],
                headers={},
                query_params={},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content={"message": "Hello {{query.name}}", "page": "{{query.page}}"},
                delay=0.0
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )
        add_route(dynamic_route)
        
        # 测试基于查询参数的动态响应
        response = self.client.get("/api/dynamic/query?name=Test User&page=2")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello Test User"
        assert data["page"] == "2"

    def test_mock_dynamic_headers(self):
        """测试基于请求头部的动态响应"""
        # 创建基于请求头部的动态响应路由
        dynamic_route = Route(
            id="test-mock-dynamic-headers",
            name="请求头部动态响应测试路由",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/dynamic/headers",
                methods=["GET"],
                headers={},
                query_params={},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content={"user_agent": "{{request.headers.user-agent}}"},
                delay=0.0
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )
        add_route(dynamic_route)
        
        # 测试基于请求头部的动态响应
        response = self.client.get("/api/dynamic/headers", headers={"User-Agent": "Test Agent"})
        assert response.status_code == 200
        data = response.json()
        assert data["user_agent"] == "Test Agent"

    def test_mock_dynamic_random(self):
        """测试使用随机数据的动态响应"""
        # 创建使用随机数据的动态响应路由
        dynamic_route = Route(
            id="test-mock-dynamic-random",
            name="随机数据动态响应测试路由",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/dynamic/random",
                methods=["GET"],
                headers={},
                query_params={},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content={"random_int": "{{random.int}}", "random_string": "{{random.string}}"},
                delay=0.0
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )
        add_route(dynamic_route)
        
        # 测试使用随机数据的动态响应
        response = self.client.get("/api/dynamic/random")
        assert response.status_code == 200
        data = response.json()
        assert "random_int" in data
        assert "random_string" in data
        assert data["random_int"].isdigit()
        assert len(data["random_string"]) > 0

    def test_mock_dynamic_timestamp(self):
        """测试使用时间戳的动态响应"""
        # 创建使用时间戳的动态响应路由
        dynamic_route = Route(
            id="test-mock-dynamic-timestamp",
            name="时间戳动态响应测试路由",
            enabled=True,
            match_rule=RouteMatchRule(
                path="/api/dynamic/timestamp",
                methods=["GET"],
                headers={},
                query_params={},
                body=None,
                use_regex=False
            ),
            response=RouteResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                content={"timestamp": "{{timestamp}}", "now": "{{now}}"},
                delay=0.0
            ),
            created_at=1234567890.0,
            updated_at=1234567890.0
        )
        add_route(dynamic_route)
        
        # 测试使用时间戳的动态响应
        response = self.client.get("/api/dynamic/timestamp")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "now" in data
        assert data["timestamp"].isdigit()
        assert len(data["now"]) > 0
