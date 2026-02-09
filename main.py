from app.core.server import run_server
from app.core.config import config
from app.storage.file import file_storage
from app.api.mock import add_route


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
        
        print(f"共加载 {len(routes)} 条路由")
    except Exception as e:
        print(f"加载路由配置失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 启动服务器
    print("启动服务器...")
    run_server()


if __name__ == "__main__":
    main()
