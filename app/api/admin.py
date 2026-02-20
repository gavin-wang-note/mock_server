from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import time
import uuid
import os
from app.models.route import Route, RouteCreate, RouteUpdate
from app.models.request import Request as RequestModel, RequestFilter
from app.api.mock import add_route, remove_route, update_route, get_all_routes, get_request_history, get_response_history
from app.core.security import authenticate_user, create_access_token
from app.core.config import config

# 创建路由处理实例
router = APIRouter(tags=["admin"])

# 根路径处理
@router.get("/admin", response_class=HTMLResponse)
async def admin_root(request: Request):
    """管理界面根路径"""
    # 获取最近24小时的请求历史，限制为100条
    start_time = time.time() - (24 * 3600)
    end_time = time.time()
    requests = get_request_history(limit=100, start_time=start_time, end_time=end_time)
    
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "routes": get_all_routes(),
            "requests": requests[:50],
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
@router.get("/admin/")
async def admin_dashboard(request: Request):
    """管理界面"""
    # 获取所有路由
    routes = get_all_routes()
    
    # 获取最近24小时的请求历史，限制为100条
    start_time = time.time() - (24 * 3600)
    end_time = time.time()
    requests = get_request_history(limit=100, start_time=start_time, end_time=end_time)
    
    # 渲染模板
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "routes": routes,
            "requests": requests[:50],
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
@router.get("/admin/routes", response_model=List[Route])
async def get_routes(current_user: dict = Depends(get_current_user)):
    """获取所有路由"""
    return get_all_routes()


@router.post("/admin/routes", response_model=Route)
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


@router.get("/admin/routes/{route_id}", response_model=Route)
async def get_route(route_id: str, current_user: dict = Depends(get_current_user)):
    """获取指定路由"""
    routes = get_all_routes()
    for route in routes:
        if route.id == route_id:
            return route
    
    raise HTTPException(status_code=404, detail="路由不存在")


@router.put("/admin/routes/{route_id}", response_model=Route)
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


@router.delete("/admin/routes/{route_id}")
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
    hours: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """获取请求历史"""
    # 计算时间范围
    start_time = None
    end_time = None
    if hours:
        start_time = time.time() - (hours * 3600)
        end_time = time.time()
    
    # 获取请求历史，传入时间范围过滤
    requests = get_request_history(limit=limit * 2, offset=offset, start_time=start_time, end_time=end_time)
    
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
    from app.storage.database import db_storage
    
    # 从数据库中获取请求记录
    req = db_storage.get_request_by_id(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="请求不存在")
    
    # 从数据库中获取对应的响应记录
    response = db_storage.get_response_by_request_id(request_id)
    
    return {
        "request": req,
        "response": response
    }


@router.delete("/requests")
async def clear_requests(current_user: dict = Depends(get_current_user)):
    """清空请求历史"""
    from app.api.mock import request_history, response_history
    from app.storage.database import db_storage
    
    # 清空内存中的历史记录
    request_history.clear()
    response_history.clear()
    
    # 清空数据库中的历史记录
    db_storage.clear_requests()
    
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
    from app.services.config_manager import config_manager
    
    # 保存配置更新
    config_manager.save_config(config_update)
    
    return {"message": "配置更新成功", "config": config_update}


@router.post("/config/backup")
async def backup_config(env: str = 'default', backup_name: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """备份配置"""
    from app.services.config_manager import config_manager
    
    backup_file = config_manager.backup_config(env, backup_name)
    return {"message": "配置备份成功", "backup_file": backup_file}


@router.post("/config/restore")
async def restore_config(backup_file: str, env: str = 'default', current_user: dict = Depends(get_current_user)):
    """从备份恢复配置"""
    from app.services.config_manager import config_manager
    
    success = config_manager.restore_config(backup_file, env)
    if success:
        return {"message": "配置恢复成功"}
    else:
        raise HTTPException(status_code=400, detail="配置恢复失败")


@router.get("/config/backups")
async def get_backups(current_user: dict = Depends(get_current_user)):
    """获取所有备份"""
    from app.services.config_manager import config_manager
    
    backups = config_manager.get_all_backups()
    return backups


@router.get("/config/history")
async def get_config_history(env: str = 'default', limit: int = 10, current_user: dict = Depends(get_current_user)):
    """获取配置变更历史"""
    from app.services.config_manager import config_manager
    
    history = config_manager.get_config_history(env, limit)
    return history


@router.post("/config/switch")
async def switch_env(env: str, current_user: dict = Depends(get_current_user)):
    """切换环境"""
    from app.services.config_manager import config_manager
    
    success = config_manager.switch_env(env)
    if success:
        return {"message": "环境切换成功", "env": env}
    else:
        raise HTTPException(status_code=400, detail="环境切换失败")


@router.get("/config/envs")
async def get_envs(current_user: dict = Depends(get_current_user)):
    """获取所有环境"""
    from app.services.config_manager import config_manager
    
    envs = ['default', 'development', 'testing', 'production']
    return {"envs": envs, "current_env": config_manager.get_current_env()}


# 管理界面
@router.get("/admin/ui", response_class=HTMLResponse)
async def admin_ui(request: Request):
    """管理界面"""
    # 获取最近24小时的请求历史，限制为100条
    start_time = time.time() - (24 * 3600)
    end_time = time.time()
    requests = get_request_history(limit=100, start_time=start_time, end_time=end_time)
    
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "routes": get_all_routes(),
            "requests": requests[:50],
            "config": config
        }
    )


# 数据管理
@router.post("/data/cleanup")
async def cleanup_data(
    max_age_days: Optional[int] = None,
    max_records: Optional[int] = None,
    archive: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    """清理数据"""
    from app.services.data_manager import data_manager
    
    result = data_manager.cleanup_requests(max_age_days, max_records, archive)
    return {"message": "数据清理完成", "result": result}


@router.get("/data/archives")
async def get_archives(current_user: dict = Depends(get_current_user)):
    """获取所有归档"""
    from app.services.data_manager import data_manager
    
    archives = data_manager.get_archives()
    return archives


@router.post("/data/restore")
async def restore_archive(archive_file: str, current_user: dict = Depends(get_current_user)):
    """从归档恢复数据"""
    from app.services.data_manager import data_manager
    
    success = data_manager.restore_archive(archive_file)
    if success:
        return {"message": "归档恢复成功"}
    else:
        raise HTTPException(status_code=400, detail="归档恢复失败")


@router.delete("/data/archives/{archive_file}")
async def delete_archive(archive_file: str, current_user: dict = Depends(get_current_user)):
    """删除归档"""
    from app.services.data_manager import data_manager
    
    # 构建完整路径
    full_path = os.path.join(os.path.dirname(config.storage.db_path), 'archives', archive_file)
    success = data_manager.delete_archive(full_path)
    if success:
        return {"message": "归档删除成功"}
    else:
        raise HTTPException(status_code=400, detail="归档删除失败")


@router.get("/data/cleanup/strategy")
async def get_cleanup_strategy(current_user: dict = Depends(get_current_user)):
    """获取清理策略"""
    from app.services.data_manager import data_manager
    
    strategy = data_manager.get_cleanup_strategy()
    return strategy


@router.put("/data/cleanup/strategy")
async def set_cleanup_strategy(strategy: dict, current_user: dict = Depends(get_current_user)):
    """设置清理策略"""
    from app.services.data_manager import data_manager
    
    success = data_manager.set_cleanup_strategy(strategy)
    if success:
        return {"message": "清理策略设置成功", "strategy": strategy}
    else:
        raise HTTPException(status_code=400, detail="清理策略设置失败")


@router.post("/data/cleanup/auto")
async def run_auto_cleanup(current_user: dict = Depends(get_current_user)):
    """运行自动清理"""
    from app.services.data_manager import data_manager
    
    result = data_manager.run_auto_cleanup()
    return {"message": "自动清理完成", "result": result}


# 数据统计和分析
@router.get("/admin/analytics/request-trend")
async def get_request_trend(hours: int = 24, interval: str = 'hour', current_user: dict = Depends(get_current_user)):
    """获取请求趋势"""
    from app.services.analytics import analytics_manager
    
    trend = analytics_manager.get_request_trend(hours, interval)
    return trend


@router.get("/admin/analytics/response-time")
async def get_response_time_stats(hours: int = 24, current_user: dict = Depends(get_current_user)):
    """获取响应时间统计"""
    from app.services.analytics import analytics_manager
    
    stats = analytics_manager.get_response_time_stats(hours)
    return stats


@router.get("/admin/analytics/status-codes")
async def get_status_code_stats(hours: int = 24, current_user: dict = Depends(get_current_user)):
    """获取状态码统计"""
    from app.services.analytics import analytics_manager
    
    stats = analytics_manager.get_status_code_stats(hours)
    return stats


@router.get("/admin/analytics/methods")
async def get_method_stats(hours: int = 24, current_user: dict = Depends(get_current_user)):
    """获取请求方法统计"""
    from app.services.analytics import analytics_manager
    
    stats = analytics_manager.get_method_stats(hours)
    return stats


@router.get("/admin/analytics/paths")
async def get_path_stats(hours: int = 24, limit: int = 10, current_user: dict = Depends(get_current_user)):
    """获取路径统计"""
    from app.services.analytics import analytics_manager
    
    stats = analytics_manager.get_path_stats(hours, limit)
    return stats


@router.get("/admin/analytics/summary")
async def get_summary_stats(current_user: dict = Depends(get_current_user)):
    """获取汇总统计"""
    from app.services.analytics import analytics_manager
    
    stats = analytics_manager.get_summary_stats()
    return stats


# 测试路由
@router.get("/admin/test")
async def test_route():
    """测试路由"""
    return {"message": "测试成功"}

# 导出路由
@router.get("/admin/routes-export")
async def export_routes():
    """导出所有路由为 JSON 文件"""
    from fastapi.responses import Response
    import json
    import time
    
    # 获取所有路由
    routes = get_all_routes()
    
    # 转换为可序列化的格式，与导入格式兼容
    routes_data = []
    for route in routes:
        # 处理响应对象，确保格式与导入兼容
        response_data = {}
        if hasattr(route.response, 'model_dump'):
            raw_response = route.response.model_dump()
            # 转换字段名：status_code -> status
            if 'status_code' in raw_response:
                response_data['status'] = raw_response['status_code']
            elif 'status' in raw_response:
                response_data['status'] = raw_response['status']
            # 复制内容字段
            if 'content' in raw_response:
                response_data['content'] = raw_response['content']
            # 复制延迟字段
            if 'delay' in raw_response:
                response_data['delay'] = raw_response['delay']
            # 复制头部字段
            if 'headers' in raw_response and raw_response['headers']:
                response_data['headers'] = raw_response['headers']
        else:
            # 直接使用原始响应数据
            response_data = route.response
        
        # 处理匹配规则
        match_rule_data = {}
        if hasattr(route.match_rule, 'model_dump'):
            raw_match_rule = route.match_rule.model_dump()
            # 只保留必要的字段
            if 'path' in raw_match_rule:
                match_rule_data['path'] = raw_match_rule['path']
            if 'methods' in raw_match_rule:
                match_rule_data['methods'] = raw_match_rule['methods']
        else:
            match_rule_data = route.match_rule
        
        # 构建路由对象，与 sample-routes.json 格式一致
        route_dict = {
            "name": route.name,
            "match_rule": match_rule_data,
            "response": response_data,
            "enabled": route.enabled,
            "tags": route.tags if route.tags else []
        }
        
        # 只在有值时添加 validator 字段
        if route.validator:
            if hasattr(route.validator, 'model_dump'):
                route_dict['validator'] = route.validator.model_dump()
            else:
                route_dict['validator'] = route.validator
        
        routes_data.append(route_dict)
    
    # 生成 JSON 字符串
    json_str = json.dumps(routes_data, indent=2, ensure_ascii=False)
    
    # 生成文件名
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"routes_export_{timestamp}.json"
    
    # 返回 JSON 文件
    return Response(
        content=json_str,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
