import re
from typing import Dict, List, Optional, Tuple, Any
from app.models.route import Route, RouteMatchRule


class Router:
    """路由匹配服务"""
    
    def __init__(self):
        self.routes: Dict[str, Route] = {}
    
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
    
    def match_route(self, method: str, path: str, headers: Dict[str, str], 
                    query_params: Dict[str, Any], body: Optional[Any] = None) -> Optional[Tuple[Route, Dict[str, Any]]]:
        """匹配路由
        
        Args:
            method: HTTP方法
            path: 请求路径
            headers: HTTP头部
            query_params: 查询参数
            body: 请求体
            
        Returns:
            匹配的路由和提取的路径参数，若未匹配则返回None
        """
        # 按优先级排序路由（更具体的路由优先）
        sorted_routes = sorted(
            [r for r in self.routes.values() if r.enabled],
            key=lambda x: (-self._route_specificity(x.match_rule), x.id)
        )
        
        for route in sorted_routes:
            # 检查HTTP方法是否匹配
            if method not in route.match_rule.methods:
                continue
            
            # 匹配路径
            path_params = self._match_path(path, route.match_rule.path, route.match_rule.use_regex)
            if path_params is None:
                continue
            
            # 匹配头部
            if not self._match_headers(headers, route.match_rule.headers):
                continue
            
            # 匹配查询参数
            if not self._match_query_params(query_params, route.match_rule.query_params):
                continue
            
            # 匹配请求体
            if not self._match_body(body, route.match_rule.body):
                continue
            
            return route, path_params
        
        return None
    
    def _route_specificity(self, match_rule: RouteMatchRule) -> int:
        """计算路由的特异性得分（用于排序）"""
        score = 0
        
        # 路径长度得分
        score += len(match_rule.path.split('/'))
        
        # 路径参数得分（越少越具体）
        score -= match_rule.path.count('{') * 2
        
        # 通配符得分（越少越具体）
        score -= match_rule.path.count('*') * 3
        
        # 方法数量得分（越少越具体）
        score -= len(match_rule.methods) * 0.5
        
        # 头部匹配得分
        if match_rule.headers:
            score += len(match_rule.headers) * 2
        
        # 查询参数匹配得分
        if match_rule.query_params:
            score += len(match_rule.query_params) * 2
        
        # 请求体匹配得分
        if match_rule.body:
            score += 5
        
        return score
    
    def _match_path(self, request_path: str, route_path: str, use_regex: bool) -> Optional[Dict[str, str]]:
        """匹配路径
        
        Args:
            request_path: 请求路径
            route_path: 路由路径
            use_regex: 是否使用正则表达式
            
        Returns:
            提取的路径参数，若不匹配则返回None
        """
        if use_regex:
            # 使用正则表达式匹配
            try:
                pattern = re.compile(route_path)
                match = pattern.match(request_path)
                if match:
                    return match.groupdict()
            except re.error:
                pass
            return None
        
        # 标准路径匹配（支持RESTful风格和通配符）
        request_parts = request_path.strip('/').split('/')
        route_parts = route_path.strip('/').split('/')
        
        if len(request_parts) != len(route_parts) and '*' not in route_parts:
            return None
        
        path_params = {}
        
        for i, (req_part, route_part) in enumerate(zip(request_parts, route_parts)):
            if route_part == '*':
                # 通配符匹配
                break
            elif route_part.startswith('{') and route_part.endswith('}'):
                # 路径参数匹配
                param_name = route_part[1:-1]
                path_params[param_name] = req_part
            elif req_part != route_part:
                # 完全匹配失败
                return None
        
        # 检查通配符位置
        if '*' in route_parts:
            wildcard_index = route_parts.index('*')
            if len(request_parts) < wildcard_index:
                return None
        
        return path_params
    
    def _match_headers(self, request_headers: Dict[str, str], route_headers: Optional[Dict[str, Any]]) -> bool:
        """匹配头部"""
        if not route_headers:
            return True
        
        for key, expected_value in route_headers.items():
            if key not in request_headers:
                return False
            
            actual_value = request_headers[key]
            
            if isinstance(expected_value, list):
                if actual_value not in expected_value:
                    return False
            elif expected_value != actual_value:
                return False
        
        return True
    
    def _match_query_params(self, request_params: Dict[str, Any], route_params: Optional[Dict[str, Any]]) -> bool:
        """匹配查询参数"""
        if not route_params:
            return True
        
        for key, expected_value in route_params.items():
            if key not in request_params:
                return False
            
            actual_value = request_params[key]
            
            if isinstance(expected_value, list):
                if actual_value not in expected_value:
                    return False
            elif expected_value != actual_value:
                return False
        
        return True
    
    def _match_body(self, request_body: Optional[Any], route_body: Optional[Dict[str, Any]]) -> bool:
        """匹配请求体"""
        if not route_body:
            return True
        
        if not request_body:
            return False
        
        if not isinstance(request_body, dict):
            return False
        
        # 递归匹配请求体
        return self._deep_match(request_body, route_body)
    
    def _deep_match(self, actual: Any, expected: Any) -> bool:
        """深度匹配对象"""
        if isinstance(expected, dict):
            if not isinstance(actual, dict):
                return False
            
            for key, value in expected.items():
                if key not in actual:
                    return False
                if not self._deep_match(actual[key], value):
                    return False
            
            return True
        elif isinstance(expected, list):
            if not isinstance(actual, list):
                return False
            
            if len(expected) != len(actual):
                return False
            
            for a, e in zip(actual, expected):
                if not self._deep_match(a, e):
                    return False
            
            return True
        else:
            return actual == expected
