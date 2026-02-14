import time
from app.core.server import run_server
from app.core.config import config
from app.storage.file import file_storage
from app.api.mock import add_route, get_all_routes


def main():
    """应用主入口"""
    print("=== Mock Server 启动中 ===")
    print(f"服务器地址: {config.server.host}:{config.server.port}")
    print(f"管理界面: http://{config.server.host}:{config.server.port}/admin")
    print(f"健康检查: http://{config.server.host}:{config.server.port}/health")
    print(f"API文档: http://{config.server.host}:{config.server.port}/docs")
    print("=======================")
    
    # 加载路由配置
    print("加载路由配置...")
    try:
        routes = file_storage.load_routes()
        print(f"从文件加载到 {len(routes)} 条路由")
        
        for i, route in enumerate(routes):
            try:
                add_route(route)
                print(f"加载路由 {i+1}/{len(routes)}: {route.name} -> {route.match_rule.path}")
            except Exception as e:
                print(f"添加路由失败 [{i+1}/{len(routes)}]: {route.name} -> {e}")
        
        # 如果没有路由，添加默认路由
        if len(routes) == 0:
            print("添加默认路由...")
            from app.models.route import Route, RouteCreate, RouteMatchRule, RouteResponse
            
            # 默认健康检查路由
            default_health_route = Route(
                id="health-check",
                name="健康检查",
                enabled=True,
                match_rule=RouteMatchRule(
                    path="/health",
                    methods=["GET"],
                    headers=None,
                    query_params=None,
                    body=None,
                    use_regex=False
                ),
                response=RouteResponse(
                    status_code=200,
                    content={"status": "healthy", "message": "Mock Server is running"},
                    headers={"Content-Type": "application/json"},
                    delay=0,
                    delay_range=None,
                    content_type="application/json"
                ),
                validator=None,
                tags=["default", "health"],
                created_at=time.time(),
                updated_at=time.time()
            )
            
            # 默认API测试路由
            default_api_route = Route(
                id="api-test",
                name="API测试",
                enabled=True,
                match_rule=RouteMatchRule(
                    path="/api/test",
                    methods=["GET", "POST"],
                    headers=None,
                    query_params=None,
                    body=None,
                    use_regex=False
                ),
                response=RouteResponse(
                    status_code=200,
                    content={"message": "Hello from Mock Server", "data": {"success": True}},
                    headers={"Content-Type": "application/json"},
                    delay=0,
                    delay_range=None,
                    content_type="application/json"
                ),
                validator=None,
                tags=["default", "test"],
                created_at=time.time(),
                updated_at=time.time()
            )
            
            # 添加默认路由
            add_route(default_health_route)
            add_route(default_api_route)
            print("添加了 2 条默认路由")
        
        print(f"共加载 {len(get_all_routes())} 条路由")
    except Exception as e:
        print(f"加载路由配置失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 启动服务器
    print("启动服务器...")
    run_server()


if __name__ == "__main__":
    main()
