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

    def test_groups_crud(self, client):
        """测试分组管理的增删改查功能"""
        # 创建分组
        create_response = client.post(
            "/admin/groups",
            data={"group_name": "test-group"},
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert create_response.status_code == 200
        assert create_response.json()["message"] == "分组创建成功"

        # 获取分组列表
        get_response = client.get(
            "/admin/groups",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert get_response.status_code == 200
        data = get_response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

        # 更新分组
        update_response = client.put(
            "/admin/groups/test-group",
            json={"new_name": "updated-test-group"},
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["message"] == "分组更新成功"

        # 删除分组
        delete_response = client.delete(
            "/admin/groups/updated-test-group",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "分组删除成功"

    def test_groups_pagination(self, client):
        """测试分组管理的分页功能"""
        # 创建多个测试分组
        for i in range(15):
            client.post(
                "/admin/groups",
                json={"group_name": f"test-group-{i}"},
                headers={"Authorization": "Bearer mock_server_admin_token"}
            )

        # 测试第一页数据
        response_page1 = client.get(
            "/admin/groups?limit=10&offset=0",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert response_page1.status_code == 200
        data_page1 = response_page1.json()
        assert "items" in data_page1
        assert len(data_page1["items"]) <= 10

        # 测试第二页数据
        response_page2 = client.get(
            "/admin/groups?limit=10&offset=10",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert response_page2.status_code == 200
        data_page2 = response_page2.json()
        assert "items" in data_page2

        # 清理测试数据
        for i in range(15):
            client.delete(
                f"/admin/groups/test-group-{i}",
                headers={"Authorization": "Bearer mock_server_admin_token"}
            )

    def test_tags_crud(self, client):
        """测试标签管理的增删改查功能"""
        # 创建标签
        create_response = client.post(
            "/admin/tags",
            data={"tag_name": "test-tag"},
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert create_response.status_code == 200
        assert create_response.json()["message"] == "标签创建成功"

        # 获取标签列表
        get_response = client.get(
            "/admin/tags",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert get_response.status_code == 200
        data = get_response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

        # 更新标签
        update_response = client.put(
            "/admin/tags/test-tag",
            json={"new_name": "updated-test-tag"},
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["message"] == "标签更新成功"

        # 删除标签
        delete_response = client.delete(
            "/admin/tags/updated-test-tag",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "标签删除成功"

    def test_tags_pagination(self, client):
        """测试标签管理的分页功能"""
        # 创建多个测试标签
        for i in range(15):
            client.post(
                "/admin/tags",
                json={"tag_name": f"test-tag-{i}"},
                headers={"Authorization": "Bearer mock_server_admin_token"}
            )

        # 测试第一页数据
        response_page1 = client.get(
            "/admin/tags?limit=10&offset=0",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert response_page1.status_code == 200
        data_page1 = response_page1.json()
        assert "items" in data_page1
        assert len(data_page1["items"]) <= 10

        # 测试第二页数据
        response_page2 = client.get(
            "/admin/tags?limit=10&offset=10",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert response_page2.status_code == 200
        data_page2 = response_page2.json()
        assert "items" in data_page2

        # 清理测试数据
        for i in range(15):
            client.delete(
                f"/admin/tags/test-tag-{i}",
                headers={"Authorization": "Bearer mock_server_admin_token"}
            )

    def test_groups_search(self, client):
        """测试分组管理的搜索功能（支持精准查询和模糊查询）"""
        # 创建测试分组
        test_groups = ["user-management", "user-auth", "product-management", "order-processing"]
        for group in test_groups:
            client.post(
                "/admin/groups",
                data={"group_name": group},
                headers={"Authorization": "Bearer mock_server_admin_token"}
            )

        try:
            # 测试模糊查询：搜索包含"user"的分组
            response_fuzzy = client.get(
                "/admin/groups/search?query=user&exact=false",
                headers={"Authorization": "Bearer mock_server_admin_token"}
            )
            assert response_fuzzy.status_code == 200
            data_fuzzy = response_fuzzy.json()
            assert "items" in data_fuzzy
            fuzzy_groups = [item["name"] for item in data_fuzzy["items"]]
            assert "user-management" in fuzzy_groups
            assert "user-auth" in fuzzy_groups
            assert "product-management" not in fuzzy_groups

            # 测试精准查询：搜索完全匹配"user-management"的分组
            response_exact = client.get(
                "/admin/groups/search?query=user-management&exact=true",
                headers={"Authorization": "Bearer mock_server_admin_token"}
            )
            assert response_exact.status_code == 200
            data_exact = response_exact.json()
            assert "items" in data_exact
            exact_groups = [item["name"] for item in data_exact["items"]]
            assert "user-management" in exact_groups
            assert "user-auth" not in exact_groups

            # 测试无匹配结果的情况
            response_no_match = client.get(
                "/admin/groups/search?query=nonexistent-group&exact=true",
                headers={"Authorization": "Bearer mock_server_admin_token"}
            )
            assert response_no_match.status_code == 200
            data_no_match = response_no_match.json()
            assert "items" in data_no_match
            assert len(data_no_match["items"]) == 0

            # 测试搜索的分页功能
            response_paginated = client.get(
                "/admin/groups/search?query=test&limit=2&offset=0",
                headers={"Authorization": "Bearer mock_server_admin_token"}
            )
            assert response_paginated.status_code == 200
            data_paginated = response_paginated.json()
            assert "items" in data_paginated
            assert len(data_paginated["items"]) <= 2
        finally:
            # 清理测试数据
            for group in test_groups:
                client.delete(
                    f"/admin/groups/{group}",
                    headers={"Authorization": "Bearer mock_server_admin_token"}
                )

    def test_tags_search(self, client):
        """测试标签管理的搜索功能（支持精准查询和模糊查询）"""
        # 创建测试标签
        test_tags = ["api-v1", "api-v2", "user-related", "admin-only"]
        for tag in test_tags:
            client.post(
                "/admin/tags",
                data={"tag_name": tag},
                headers={"Authorization": "Bearer mock_server_admin_token"}
            )

        try:
            # 测试模糊查询：搜索包含"api"的标签
            response_fuzzy = client.get(
                "/admin/tags/search?query=api&exact=false",
                headers={"Authorization": "Bearer mock_server_admin_token"}
            )
            assert response_fuzzy.status_code == 200
            data_fuzzy = response_fuzzy.json()
            assert "items" in data_fuzzy
            fuzzy_tags = [item["name"] for item in data_fuzzy["items"]]
            assert "api-v1" in fuzzy_tags
            assert "api-v2" in fuzzy_tags
            assert "user-related" not in fuzzy_tags

            # 测试精准查询：搜索完全匹配"api-v1"的标签
            response_exact = client.get(
                "/admin/tags/search?query=api-v1&exact=true",
                headers={"Authorization": "Bearer mock_server_admin_token"}
            )
            assert response_exact.status_code == 200
            data_exact = response_exact.json()
            assert "items" in data_exact
            exact_tags = [item["name"] for item in data_exact["items"]]
            assert "api-v1" in exact_tags
            assert "api-v2" not in exact_tags

            # 测试无匹配结果的情况
            response_no_match = client.get(
                "/admin/tags/search?query=nonexistent-tag&exact=true",
                headers={"Authorization": "Bearer mock_server_admin_token"}
            )
            assert response_no_match.status_code == 200
            data_no_match = response_no_match.json()
            assert "items" in data_no_match
            assert len(data_no_match["items"]) == 0

            # 测试搜索的分页功能
            response_paginated = client.get(
                "/admin/tags/search?query=test&limit=2&offset=0",
                headers={"Authorization": "Bearer mock_server_admin_token"}
            )
            assert response_paginated.status_code == 200
            data_paginated = response_paginated.json()
            assert "items" in data_paginated
            assert len(data_paginated["items"]) <= 2
        finally:
            # 清理测试数据
            for tag in test_tags:
                client.delete(
                    f"/admin/tags/{tag}",
                    headers={"Authorization": "Bearer mock_server_admin_token"}
                )

    def test_response_sequence_crud(self, client):
        """测试响应序列的增删改查功能"""
        # 新增路由时启用响应序列
        route_data = {
            "name": "测试响应序列路由",
            "match_rule": {
                "path": "/api/test/sequence",
                "methods": ["GET"]
            },
            "response": {
                "status": 200,
                "content": {"message": "Default Response"},
                "delay": 0
            },
            "enable_sequence": True,
            "response_sequences": [
                {
                    "status_code": 200,
                    "content": {"message": "Sequence Response 1"},
                    "delay": 0,
                    "sequence_description": "First response"
                },
                {
                    "status_code": 201,
                    "content": {"message": "Sequence Response 2"},
                    "delay": 0,
                    "sequence_description": "Second response"
                },
                {
                    "status_code": 404,
                    "content": {"message": "Sequence Response 3"},
                    "delay": 0,
                    "sequence_description": "Third response"
                }
            ]
        }

        # 创建路由
        create_response = client.post(
            "/admin/routes",
            json=route_data,
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert create_response.status_code == 200
        created_route = create_response.json()
        assert created_route["name"] == "测试响应序列路由"
        assert created_route["enable_sequence"] == True
        assert len(created_route["response_sequences"]) == 3

        # 获取路由详情，验证响应序列是否正确保存
        get_response = client.get(
            f"/admin/routes/{created_route['id']}",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert get_response.status_code == 200
        retrieved_route = get_response.json()
        assert retrieved_route["enable_sequence"] == True
        assert len(retrieved_route["response_sequences"]) == 3
        assert retrieved_route["response_sequences"][0]["content"]["message"] == "Sequence Response 1"
        assert retrieved_route["response_sequences"][1]["content"]["message"] == "Sequence Response 2"
        assert retrieved_route["response_sequences"][2]["content"]["message"] == "Sequence Response 3"

        # 编辑路由，修改响应序列
        updated_route_data = {
            "name": "测试响应序列路由（更新）",
            "match_rule": {
                "path": "/api/test/sequence",
                "methods": ["GET"]
            },
            "response": {
                "status": 200,
                "content": {"message": "Default Response"},
                "delay": 0
            },
            "enable_sequence": True,
            "response_sequences": [
                {
                    "status_code": 200,
                    "content": {"message": "Updated Sequence Response 1"},
                    "delay": 0,
                    "sequence_description": "Updated first response"
                },
                {
                    "status_code": 500,
                    "content": {"message": "Updated Sequence Response 2"},
                    "delay": 0,
                    "sequence_description": "Updated second response"
                }
            ]
        }

        update_response = client.put(
            f"/admin/routes/{created_route['id']}",
            json=updated_route_data,
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert update_response.status_code == 200
        updated_route = update_response.json()
        assert updated_route["name"] == "测试响应序列路由（更新）"
        assert len(updated_route["response_sequences"]) == 2
        assert updated_route["response_sequences"][0]["content"]["message"] == "Updated Sequence Response 1"
        assert updated_route["response_sequences"][1]["content"]["message"] == "Updated Sequence Response 2"

        # 删除路由
        delete_response = client.delete(
            f"/admin/routes/{created_route['id']}",
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "路由删除成功"

    def test_response_sequence_execution(self, client):
        """测试响应序列的执行逻辑，验证顺序响应"""
        # 创建带响应序列的路由
        route_data = {
            "name": "测试响应序列执行",
            "match_rule": {
                "path": "/api/test/sequence/execution",
                "methods": ["GET"]
            },
            "response": {
                "status": 200,
                "content": {"message": "Default Response"},
                "delay": 0
            },
            "enable_sequence": True,
            "response_sequences": [
                {
                    "status_code": 200,
                    "content": {"message": "First Response"},
                    "delay": 0
                },
                {
                    "status_code": 201,
                    "content": {"message": "Second Response"},
                    "delay": 0
                },
                {
                    "status_code": 404,
                    "content": {"message": "Third Response"},
                    "delay": 0
                }
            ]
        }

        create_response = client.post(
            "/admin/routes",
            json=route_data,
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert create_response.status_code == 200
        route_id = create_response.json()["id"]

        try:
            # 第一次请求，应该返回第一个响应
            response1 = client.get("/api/test/sequence/execution")
            assert response1.status_code == 200
            assert response1.json()["message"] == "First Response"

            # 第二次请求，应该返回第二个响应
            response2 = client.get("/api/test/sequence/execution")
            assert response2.status_code == 201
            assert response2.json()["message"] == "Second Response"

            # 第三次请求，应该返回第三个响应
            response3 = client.get("/api/test/sequence/execution")
            assert response3.status_code == 404
            assert response3.json()["message"] == "Third Response"

            # 第四次请求，应该循环返回第一个响应
            response4 = client.get("/api/test/sequence/execution")
            assert response4.status_code == 200
            assert response4.json()["message"] == "First Response"
        finally:
            # 清理测试数据
            client.delete(
                f"/admin/routes/{route_id}",
                headers={"Authorization": "Bearer mock_server_admin_token"}
            )

    def test_response_sequence_disabled(self, client):
        """测试禁用响应序列的情况"""
        # 创建禁用响应序列的路由
        route_data = {
            "name": "测试禁用响应序列",
            "match_rule": {
                "path": "/api/test/sequence/disabled",
                "methods": ["GET"]
            },
            "response": {
                "status": 200,
                "content": {"message": "Default Response"},
                "delay": 0
            },
            "enable_sequence": False,
            "response_sequences": [
                {
                    "status_code": 200,
                    "content": {"message": "Sequence Response 1"},
                    "delay": 0
                }
            ]
        }

        create_response = client.post(
            "/admin/routes",
            json=route_data,
            headers={"Authorization": "Bearer mock_server_admin_token"}
        )
        assert create_response.status_code == 200
        route_id = create_response.json()["id"]

        try:
            # 请求应该返回默认响应，而不是序列响应
            response = client.get("/api/test/sequence/disabled")
            assert response.status_code == 200
            assert response.json()["message"] == "Default Response"
        finally:
            # 清理测试数据
            client.delete(
                f"/admin/routes/{route_id}",
                headers={"Authorization": "Bearer mock_server_admin_token"}
            )
