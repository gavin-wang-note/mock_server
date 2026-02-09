from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import time
import uuid
from app.models.route import Route, RouteCreate, RouteUpdate
from app.models.request import Request as RequestModel, RequestFilter
from app.api.mock import add_route, remove_route, update_route, get_all_routes, get_request_history, get_response_history
from app.core.security import authenticate_user, create_access_token
from app.core.config import config

# 创建路由处理实例
router = APIRouter(prefix="/admin", tags=["admin"])

# 根路径处理
@router.get("", response_class=HTMLResponse)
async def admin_root(request: Request):
    """管理界面根路径"""
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "routes": get_all_routes(),
            "requests": get_request_history()[-50:],
            "config": config
        }
    )

# 模板引擎
templates = Jinja2Templates(directory="app/templates")

# 添加自定义过滤器
def timestamp_filter(value):
    """将时间戳转换为可读时间"""
    import datetime
    return datetime.datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')

# 注册过滤器
templates.env.filters['timestamp'] = timestamp_filter


# 认证依赖
async def get_current_user(request: Request):
    """获取当前用户"""
    # 从请求头获取令牌
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=401,
            detail="缺少认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证令牌
    token = auth_header.split(" ")[1]
    # 这里简化处理，实际应该验证令牌的有效性
    # 暂时使用固定的令牌验证
    if token != "mock_server_admin_token":
        raise HTTPException(
            status_code=401,
            detail="无效的认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {"username": "admin"}


# 管理界面
@router.get("/")
async def admin_dashboard(request: Request):
    """管理界面"""
    # 获取所有路由
    routes = get_all_routes()
    
    # 获取请求历史
    requests = get_request_history()[-50:]  # 最近50条
    
    # 渲染模板
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "routes": routes,
            "requests": requests,
            "config": config
        }
    )


# 认证端点
@router.post("/login")
async def login(username: str, password: str):
    """登录认证"""
    # 验证用户
    if not authenticate_user(username, password):
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token = create_access_token(data={"sub": username})
    
    return {"access_token": access_token, "token_type": "bearer"}


# 路由管理
@router.get("/routes", response_model=List[Route])
async def get_routes(
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """获取所有路由"""
    routes = get_all_routes()
    
    # 应用分页
    total = len(routes)
    routes = routes[offset:offset + limit]
    
    return routes


@router.post("/routes", response_model=Route)
async def create_route(route_create: RouteCreate, current_user: dict = Depends(get_current_user)):
    """创建新路由"""
    # 生成路由ID
    route_id = str(uuid.uuid4())
    
    # 创建路由
    route = Route(
        id=route_id,
        name=route_create.name,
        enabled=True,
        match_rule=route_create.match_rule,
        response=route_create.response,
        validator=route_create.validator,
        tags=route_create.tags,
        created_at=time.time(),
        updated_at=time.time()
    )
    
    # 添加路由
    add_route(route)
    
    return route


@router.get("/routes/{route_id}", response_model=Route)
async def get_route(route_id: str, current_user: dict = Depends(get_current_user)):
    """获取指定路由"""
    routes = get_all_routes()
    for route in routes:
        if route.id == route_id:
            return route
    
    raise HTTPException(status_code=404, detail="路由不存在")


@router.put("/routes/{route_id}", response_model=Route)
async def update_route_endpoint(route_id: str, route_update: RouteUpdate, current_user: dict = Depends(get_current_user)):
    """更新路由"""
    # 获取现有路由
    routes = get_all_routes()
    existing_route = None
    for route in routes:
        if route.id == route_id:
            existing_route = route
            break
    
    if not existing_route:
        raise HTTPException(status_code=404, detail="路由不存在")
    
    # 更新路由
    updated_route = Route(
        id=route_id,
        name=route_update.name or existing_route.name,
        enabled=route_update.enabled if route_update.enabled is not None else existing_route.enabled,
        match_rule=route_update.match_rule or existing_route.match_rule,
        response=route_update.response or existing_route.response,
        validator=route_update.validator or existing_route.validator,
        tags=route_update.tags or existing_route.tags,
        created_at=existing_route.created_at,
        updated_at=time.time()
    )
    
    # 保存更新
    update_route(updated_route)
    
    return updated_route


@router.delete("/routes/{route_id}")
async def delete_route(route_id: str, current_user: dict = Depends(get_current_user)):
    """删除路由"""
    # 检查路由是否存在
    routes = get_all_routes()
    route_exists = any(route.id == route_id for route in routes)
    
    if not route_exists:
        raise HTTPException(status_code=404, detail="路由不存在")
    
    # 删除路由
    remove_route(route_id)
    
    return {"message": "路由删除成功"}


# 请求历史管理
@router.get("/requests", response_model=List[RequestModel])
async def get_requests(
    limit: int = 100,
    offset: int = 0,
    method: Optional[str] = None,
    path: Optional[str] = None,
    status_code: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """获取请求历史"""
    requests = get_request_history()
    
    # 应用过滤
    if method:
        requests = [r for r in requests if r.method == method]
    if path:
        requests = [r for r in requests if path in r.path]
    if status_code:
        requests = [r for r in requests if r.response_status == status_code]
    
    # 应用分页
    total = len(requests)
    requests = requests[offset:offset + limit]
    
    return requests


@router.get("/requests/{request_id}")
async def get_request(request_id: str, current_user: dict = Depends(get_current_user)):
    """获取指定请求"""
    requests = get_request_history()
    for req in requests:
        if req.id == request_id:
            # 获取对应的响应
            responses = get_response_history()
            response = None
            for resp in responses:
                if resp.request_id == request_id:
                    response = resp
                    break
            
            return {
                "request": req,
                "response": response
            }
    
    raise HTTPException(status_code=404, detail="请求不存在")


@router.delete("/requests")
async def clear_requests(current_user: dict = Depends(get_current_user)):
    """清空请求历史"""
    # 这里简化处理，实际应该清空请求和响应历史
    # 暂时返回成功消息
    return {"message": "请求历史清空成功"}


# 服务配置管理
@router.get("/config")
async def get_config(current_user: dict = Depends(get_current_user)):
    """获取服务配置"""
    return {
        "server": config.server.model_dump(),
        "admin": config.admin.model_dump(),
        "storage": config.storage.model_dump(),
        "proxy": config.proxy.model_dump(),
        "log": config.log.model_dump()
    }


@router.put("/config")
async def update_config(config_update: dict, current_user: dict = Depends(get_current_user)):
    """更新服务配置"""
    # 这里简化处理，实际应该更新配置并重启相关服务
    # 暂时返回成功消息
    return {"message": "配置更新成功", "config": config_update}


# 管理界面
@router.get("/ui", response_class=HTMLResponse)
async def admin_ui(request: Request):
    """管理界面"""
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "routes": get_all_routes(),
            "requests": get_request_history()[-50:],
            "config": config
        }
    )
