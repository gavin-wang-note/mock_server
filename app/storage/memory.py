from typing import Dict, List, Optional
from app.models.route import Route


class MemoryStorage:
    """内存存储系统"""
    
    def __init__(self):
        """初始化内存存储"""
        self.routes: Dict[str, Route] = {}
        self.request_history: List[Dict] = []
        self.response_history: List[Dict] = []
    
    def add_route(self, route: Route) -> None:
        """添加路由"""
        self.routes[route.id] = route
    
    def remove_route(self, route_id: str) -> None:
        """移除路由"""
        if route_id in self.routes:
            del self.routes[route_id]
    
    def update_route(self, route: Route) -> None:
        """更新路由"""
        self.routes[route.id] = route
    
    def get_route(self, route_id: str) -> Optional[Route]:
        """获取路由"""
        return self.routes.get(route_id)
    
    def get_all_routes(self) -> List[Route]:
        """获取所有路由"""
        return list(self.routes.values())
    
    def add_request(self, request_data: Dict) -> None:
        """添加请求记录"""
        self.request_history.append(request_data)
        # 限制历史记录数量
        if len(self.request_history) > 1000:
            self.request_history.pop(0)
    
    def add_response(self, response_data: Dict) -> None:
        """添加响应记录"""
        self.response_history.append(response_data)
        # 限制历史记录数量
        if len(self.response_history) > 1000:
            self.response_history.pop(0)
    
    def get_request_history(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """获取请求历史"""
        return self.request_history[offset:offset + limit]
    
    def get_response_history(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """获取响应历史"""
        return self.response_history[offset:offset + limit]
    
    def clear_history(self) -> None:
        """清空历史记录"""
        self.request_history.clear()
        self.response_history.clear()
    
    def clear_all(self) -> None:
        """清空所有数据"""
        self.routes.clear()
        self.clear_history()
    
    def get_stats(self) -> Dict[str, int]:
        """获取存储统计信息"""
        return {
            "routes_count": len(self.routes),
            "request_history_count": len(self.request_history),
            "response_history_count": len(self.response_history)
        }
    
    def clear(self) -> None:
        """清空所有数据"""
        self.clear_all()


# 创建全局内存存储实例
memory_storage = MemoryStorage()
