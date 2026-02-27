from fastapi import APIRouter, Depends, HTTPException, Request, Body, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import time
import uuid
import os
from app.models.route import Route, RouteCreate, RouteUpdate
from app.models.request import Request as RequestModel, RequestFilter
from app.api.mock import add_route, remove_route, update_route, get_all_routes, get_request_history, get_request_history_count, get_response_history
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


# 全局分组集合，用于存储所有创建的分组
created_groups = set()

# 全局标签集合，用于存储所有创建的标签
created_tags = set()

# 从数据库加载分组和标签
def load_groups_and_tags():
    """从数据库加载分组和标签"""
    from app.storage.database import db_storage
    global created_groups, created_tags
    
    # 加载分组
    groups_data = db_storage.get_config('created_groups')
    if groups_data:
        created_groups = set(groups_data)
    
    # 加载标签
    tags_data = db_storage.get_config('created_tags')
    if tags_data:
        created_tags = set(tags_data)

# 保存分组和标签到数据库
def save_groups_and_tags():
    """保存分组和标签到数据库"""
    from app.storage.database import db_storage
    global created_groups, created_tags
    
    # 保存分组
    db_storage.save_config('created_groups', list(created_groups))
    
    # 保存标签
    db_storage.save_config('created_tags', list(created_tags))

# 初始化时加载分组和标签
load_groups_and_tags()

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
async def login(
    username: str = Body(..., description="用户名"),
    password: str = Body(..., description="密码")
):
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
@router.get("/admin/routes")
async def get_routes(search: Optional[str] = None, limit: int = 1000, offset: int = 0, sort: Optional[str] = None, order: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """获取所有路由"""
    routes = get_all_routes()
    
    # 应用搜索过滤
    if search and search.strip():
        search_lower = search.lower()
        filtered_routes = []
        for route in routes:
            # 检查路由名称、路径、方法和分组是否包含搜索词
            name_match = search_lower in route.name.lower() if route.name else False
            path_match = False
            methods_match = False
            group_match = search_lower in route.group.lower() if route.group else False
            
            if route.match_rule:
                path_match = search_lower in route.match_rule.path.lower() if route.match_rule.path else False
                if route.match_rule.methods:
                    methods_str = ", ".join(route.match_rule.methods).lower()
                    methods_match = search_lower in methods_str
            
            if name_match or path_match or methods_match or group_match:
                filtered_routes.append(route)
        routes = filtered_routes
    
    # 应用排序
    if sort:
        reverse = order == "desc"
        
        if sort == "id":
            routes.sort(key=lambda x: x.id, reverse=reverse)
        elif sort == "name":
            routes.sort(key=lambda x: x.name or "", reverse=reverse)
        elif sort == "path":
            routes.sort(key=lambda x: x.match_rule.path if x.match_rule else "", reverse=reverse)
        elif sort == "group":
            routes.sort(key=lambda x: x.group or "", reverse=reverse)
        elif sort == "created_at":
            routes.sort(key=lambda x: x.created_at or 0, reverse=reverse)
    
    # 应用分页
    total = len(routes)
    routes = routes[offset:offset + limit]
    
    # 返回带有分页信息的数据结构
    return {
        "items": routes,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.post("/admin/routes", response_model=Route)
async def create_route(route_create: RouteCreate, current_user: dict = Depends(get_current_user)):
    """新增路由"""
    # 生成路由ID
    route_id = str(uuid.uuid4())
    
    # 自动创建不存在的分组
    if route_create.group:
        # 检查分组是否已存在
        routes = get_all_routes()
        existing_groups = set()
        for route in routes:
            if route.group:
                existing_groups.add(route.group)
        
        # 如果分组不存在，添加到全局集合
        if route_create.group not in existing_groups and route_create.group not in created_groups:
            created_groups.add(route_create.group)
            # 保存到数据库
            save_groups_and_tags()
    
    # 自动创建不存在的标签
    if route_create.tags:
        # 检查标签是否已存在
        routes = get_all_routes()
        existing_tags = set()
        for route in routes:
            if route.tags:
                existing_tags.update(route.tags)
        
        # 如果标签不存在，添加到全局集合
        tags_added = False
        for tag in route_create.tags:
            if tag not in existing_tags and tag not in created_tags:
                created_tags.add(tag)
                tags_added = True
        
        # 如果添加了新标签，保存到数据库
        if tags_added:
            save_groups_and_tags()
    
    # 创建路由
    route = Route(
        id=route_id,
        name=route_create.name,
        enabled=True,
        match_rule=route_create.match_rule,
        response=route_create.response,
        response_sequences=route_create.response_sequences,
        enable_sequence=route_create.enable_sequence,
        current_sequence_index=0,
        validator=route_create.validator,
        group=route_create.group,
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
    
    # 确定最终的分组和标签值
    final_group = route_update.group if route_update.group is not None else existing_route.group
    final_tags = route_update.tags if route_update.tags is not None else existing_route.tags
    
    # 自动创建不存在的分组
    if final_group:
        # 检查分组是否已存在
        existing_groups = set()
        for route in routes:
            if route.group:
                existing_groups.add(route.group)
        
        # 如果分组不存在，添加到全局集合
        if final_group not in existing_groups and final_group not in created_groups:
            created_groups.add(final_group)
            # 保存到数据库
            save_groups_and_tags()
    
    # 自动创建不存在的标签
    if final_tags:
        # 检查标签是否已存在
        existing_tags = set()
        for route in routes:
            if route.tags:
                existing_tags.update(route.tags)
        
        # 如果标签不存在，添加到全局集合
        tags_added = False
        for tag in final_tags:
            if tag not in existing_tags and tag not in created_tags:
                created_tags.add(tag)
                tags_added = True
        
        # 如果添加了新标签，保存到数据库
        if tags_added:
            save_groups_and_tags()
    
    # 更新路由
    updated_route = Route(
        id=route_id,
        name=route_update.name or existing_route.name,
        enabled=route_update.enabled if route_update.enabled is not None else existing_route.enabled,
        match_rule=route_update.match_rule or existing_route.match_rule,
        response=route_update.response or existing_route.response,
        response_sequences=route_update.response_sequences if route_update.response_sequences is not None else existing_route.response_sequences,
        enable_sequence=route_update.enable_sequence if route_update.enable_sequence is not None else existing_route.enable_sequence,
        current_sequence_index=existing_route.current_sequence_index,
        validator=route_update.validator or existing_route.validator,
        group=final_group,
        tags=final_tags,
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


@router.post("/admin/routes/{route_id}/reset-sequence")
async def reset_sequence_counter(route_id: str, current_user: dict = Depends(get_current_user)):
    """重置响应序列计数器"""
    # 检查路由是否存在
    routes = get_all_routes()
    route_to_update = None
    for route in routes:
        if route.id == route_id:
            route_to_update = route
            break
    
    if not route_to_update:
        raise HTTPException(status_code=404, detail="路由不存在")
    
    # 重置序列计数器
    route_to_update.current_sequence_index = 0
    
    # 更新路由
    update_route(route_to_update)
    
    return {"message": "响应序列计数器已重置"}


# 请求历史管理
@router.get("/admin/requests")
async def get_requests(
    limit: int = 100,
    offset: int = 0,
    method: Optional[str] = None,
    path: Optional[str] = None,
    status_code: Optional[int] = None,
    hours: Optional[int] = None,
    sort: Optional[str] = None,
    order: Optional[str] = None,
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
    requests = get_request_history(limit=limit, offset=offset, start_time=start_time, end_time=end_time)
    
    # 应用过滤
    if method:
        requests = [r for r in requests if r.method == method]
    if path:
        requests = [r for r in requests if path in r.path]
    if status_code:
        requests = [r for r in requests if r.response_status == status_code]
    
    # 应用排序
    if sort:
        reverse = order == "desc"
        
        if sort == "timestamp":
            requests.sort(key=lambda x: x.timestamp, reverse=reverse)
        elif sort == "method":
            requests.sort(key=lambda x: x.method, reverse=reverse)
        elif sort == "path":
            requests.sort(key=lambda x: x.path, reverse=reverse)
        elif sort == "response_status":
            requests.sort(key=lambda x: x.response_status, reverse=reverse)
        elif sort == "response_time":
            requests.sort(key=lambda x: x.response_time, reverse=reverse)
        elif sort == "client_ip":
            requests.sort(key=lambda x: x.client_ip, reverse=reverse)
    
    # 获取总记录数
    total = get_request_history_count(start_time=start_time, end_time=end_time)
    
    return {
        "items": requests,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/admin/requests/{request_id}")
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


@router.delete("/admin/requests")
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
            "group": route.group,
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


# 分组管理
@router.get("/admin/groups")
async def get_groups(limit: int = 10, offset: int = 0, current_user: dict = Depends(get_current_user)):
    """获取所有分组"""
    routes = get_all_routes()
    
    # 统计分组使用次数
    group_stats = {}
    for route in routes:
        if route.group:
            if route.group in group_stats:
                group_stats[route.group] += 1
            else:
                group_stats[route.group] = 1
    
    # 添加所有已创建但还没有关联路由的分组
    for group_name in created_groups:
        if group_name not in group_stats:
            group_stats[group_name] = 0
    
    # 转换为列表格式
    groups = []
    for group_name, count in group_stats.items():
        groups.append({
            "name": group_name,
            "count": count
        })
    
    # 按使用次数排序
    groups.sort(key=lambda x: x['count'], reverse=True)
    
    # 应用分页
    total = len(groups)
    groups = groups[offset:offset + limit]
    
    # 返回带有分页信息的数据结构
    return {
        "items": groups,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.post("/admin/groups")
async def create_group(group_name: str = Form(..., description="分组名称"), current_user: dict = Depends(get_current_user)):
    """创建分组"""
    # 检查分组是否已存在
    routes = get_all_routes()
    existing_groups = set()
    for route in routes:
        if route.group:
            existing_groups.add(route.group)
    
    # 检查是否在已创建的分组中
    if group_name in existing_groups or group_name in created_groups:
        # 返回409 Conflict状态码，表示资源已存在
        raise HTTPException(status_code=409, detail="分组名称已存在")
    
    # 将新分组添加到全局集合中
    created_groups.add(group_name)
    
    # 保存到数据库
    save_groups_and_tags()
    
    # 这里不需要特殊处理，因为分组是动态创建的
    # 当路由关联分组时，如果分组不存在，会自动创建
    return {"message": "分组创建成功", "group": group_name}


@router.put("/admin/groups/{old_name}")
async def update_group(old_name: str, request_data: dict = Body(..., description="更新数据"), current_user: dict = Depends(get_current_user)):
    """更新分组名称"""
    new_name = request_data.get("new_name")
    if not new_name:
        raise HTTPException(status_code=400, detail="新分组名称不能为空")
    
    routes = get_all_routes()
    
    # 更新所有使用该分组的路由
    updated_count = 0
    for route in routes:
        if route.group == old_name:
            route.group = new_name
            update_route(route)
            updated_count += 1
    
    # 更新已创建分组集合中的分组名称
    if old_name in created_groups:
        created_groups.remove(old_name)
        created_groups.add(new_name)
    
    # 保存到数据库
    save_groups_and_tags()
    
    return {"message": "分组更新成功", "old_name": old_name, "new_name": new_name, "updated_count": updated_count}


@router.delete("/admin/groups/{group_name}")
async def delete_group(group_name: str, current_user: dict = Depends(get_current_user)):
    """删除分组"""
    routes = get_all_routes()
    
    # 移除所有使用该分组的路由的分组信息
    updated_count = 0
    for route in routes:
        if route.group == group_name:
            route.group = None
            update_route(route)
            updated_count += 1
    
    # 从已创建分组集合中移除该分组
    if group_name in created_groups:
        created_groups.remove(group_name)
    
    # 保存到数据库
    save_groups_and_tags()
    
    return {"message": "分组删除成功", "group": group_name, "updated_count": updated_count}


# 标签管理
@router.get("/admin/tags")
async def get_tags(limit: int = 10, offset: int = 0, current_user: dict = Depends(get_current_user)):
    """获取所有标签"""
    routes = get_all_routes()
    
    # 统计标签使用次数
    tag_stats = {}
    for route in routes:
        if route.tags:
            for tag in route.tags:
                if tag in tag_stats:
                    tag_stats[tag] += 1
                else:
                    tag_stats[tag] = 1
    
    # 添加所有已创建但还没有关联路由的标签
    for tag_name in created_tags:
        if tag_name not in tag_stats:
            tag_stats[tag_name] = 0
    
    # 转换为列表格式
    tags = []
    for tag_name, count in tag_stats.items():
        tags.append({
            "name": tag_name,
            "count": count
        })
    
    # 按使用次数排序
    tags.sort(key=lambda x: x['count'], reverse=True)
    
    # 应用分页
    total = len(tags)
    tags = tags[offset:offset + limit]
    
    # 返回带有分页信息的数据结构
    return {
        "items": tags,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.post("/admin/tags")
async def create_tag(tag_name: str = Form(..., description="标签名称"), current_user: dict = Depends(get_current_user)):
    """创建标签"""
    # 检查标签是否已存在
    routes = get_all_routes()
    existing_tags = set()
    for route in routes:
        if route.tags:
            existing_tags.update(route.tags)
    
    # 检查是否在已创建的标签中
    if tag_name in existing_tags or tag_name in created_tags:
        # 返回409 Conflict状态码，表示资源已存在
        raise HTTPException(status_code=409, detail="标签名称已存在")
    
    # 将新标签添加到全局集合中
    created_tags.add(tag_name)
    
    # 保存到数据库
    save_groups_and_tags()
    
    # 这里不需要特殊处理，因为标签是动态创建的
    # 当路由关联标签时，如果标签不存在，会自动创建
    return {"message": "标签创建成功", "tag": tag_name}


@router.put("/admin/tags/{old_name}")
async def update_tag(old_name: str, request_data: dict = Body(..., description="更新数据"), current_user: dict = Depends(get_current_user)):
    """更新标签名称"""
    new_name = request_data.get("new_name")
    if not new_name:
        raise HTTPException(status_code=400, detail="新标签名称不能为空")
    
    routes = get_all_routes()
    
    # 更新所有使用该标签的路由
    updated_count = 0
    for route in routes:
        if route.tags and old_name in route.tags:
            # 替换标签名称
            route.tags = [new_name if tag == old_name else tag for tag in route.tags]
            update_route(route)
            updated_count += 1
    
    # 更新已创建标签集合中的标签名称
    if old_name in created_tags:
        created_tags.remove(old_name)
        created_tags.add(new_name)
    
    # 保存到数据库
    save_groups_and_tags()
    
    return {"message": "标签更新成功", "old_name": old_name, "new_name": new_name, "updated_count": updated_count}


@router.delete("/admin/tags/{tag_name}")
async def delete_tag(tag_name: str, current_user: dict = Depends(get_current_user)):
    """删除标签"""
    routes = get_all_routes()
    
    # 移除所有使用该标签的路由的标签信息
    updated_count = 0
    for route in routes:
        if route.tags and tag_name in route.tags:
            # 移除标签
            route.tags = [tag for tag in route.tags if tag != tag_name]
            update_route(route)
            updated_count += 1
    
    # 从已创建标签集合中移除该标签
    if tag_name in created_tags:
        created_tags.remove(tag_name)
    
    # 保存到数据库
    save_groups_and_tags()
    
    return {"message": "标签删除成功", "tag": tag_name, "updated_count": updated_count}


# 搜索API（支持精准查询和模糊查询）
@router.get("/admin/groups/search")
async def search_groups(query: str, limit: int = 10, offset: int = 0, exact: bool = False, current_user: dict = Depends(get_current_user)):
    """搜索分组（支持精准查询和模糊查询）"""
    routes = get_all_routes()
    
    # 统计分组使用次数
    group_stats = {}
    for route in routes:
        if route.group:
            if route.group in group_stats:
                group_stats[route.group] += 1
            else:
                group_stats[route.group] = 1
    
    # 添加所有已创建但还没有关联路由的分组
    for group_name in created_groups:
        if group_name not in group_stats:
            group_stats[group_name] = 0
    
    # 过滤匹配的分组
    matched_groups = []
    if query:
        query_lower = query.lower()
        for group_name, count in group_stats.items():
            if exact:
                # 精准查询：完全匹配分组名称
                if group_name == query:
                    matched_groups.append({"name": group_name, "count": count})
            else:
                # 模糊查询：部分匹配分组名称
                if query_lower in group_name.lower():
                    matched_groups.append({"name": group_name, "count": count})
    else:
        # 没有查询参数时，返回所有分组
        for group_name, count in group_stats.items():
            matched_groups.append({"name": group_name, "count": count})
    
    # 按使用次数排序
    matched_groups.sort(key=lambda x: x['count'], reverse=True)
    
    # 应用分页
    total = len(matched_groups)
    matched_groups = matched_groups[offset:offset + limit]
    
    # 返回带有分页信息的数据结构
    return {
        "items": matched_groups,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/admin/tags/search")
async def search_tags(query: str, limit: int = 10, offset: int = 0, exact: bool = False, current_user: dict = Depends(get_current_user)):
    """搜索标签（支持精准查询和模糊查询）"""
    routes = get_all_routes()
    
    # 统计标签使用次数
    tag_stats = {}
    for route in routes:
        if route.tags:
            for tag in route.tags:
                if tag in tag_stats:
                    tag_stats[tag] += 1
                else:
                    tag_stats[tag] = 1
    
    # 添加所有已创建但还没有关联路由的标签
    for tag_name in created_tags:
        if tag_name not in tag_stats:
            tag_stats[tag_name] = 0
    
    # 过滤匹配的标签
    matched_tags = []
    if query:
        query_lower = query.lower()
        for tag_name, count in tag_stats.items():
            if exact:
                # 精准查询：完全匹配标签名称
                if tag_name == query:
                    matched_tags.append({"name": tag_name, "count": count})
            else:
                # 模糊查询：部分匹配标签名称
                if query_lower in tag_name.lower():
                    matched_tags.append({"name": tag_name, "count": count})
    else:
        # 没有查询参数时，返回所有标签
        for tag_name, count in tag_stats.items():
            matched_tags.append({"name": tag_name, "count": count})
    
    # 按使用次数排序
    matched_tags.sort(key=lambda x: x['count'], reverse=True)
    
    # 应用分页
    total = len(matched_tags)
    matched_tags = matched_tags[offset:offset + limit]
    
    # 返回带有分页信息的数据结构
    return {
        "items": matched_tags,
        "total": total,
        "limit": limit,
        "offset": offset
    }
