from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import Optional, Any
import asyncio
import time
import uuid
import json
from app.services.router import Router
from app.services.validator import Validator
from app.services.templater import Templater
from app.core.config import config
from app.models.request import Request as RequestModel
from app.models.response import Response as ResponseModel

# 创建路由处理实例
router = APIRouter()

# 服务实例
mock_router = Router()
validator = Validator()
templater = Templater()

# 导入数据库存储
from app.storage.database import db_storage

# 请求和响应历史（内存中保留最近1000条，用于快速访问）
request_history = []
response_history = []

# 服务启动时间
server_start_time = time.time()


@router.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def mock_handler(request: Request, path: str):
    """Mock API请求处理"""
    # 生成请求ID
    request_id = str(uuid.uuid4())
    
    # 记录请求开始时间
    start_time = time.time()
    
    # 构建完整路径
    full_path = f"/api/{path}"
    
    # 获取请求信息
    method = request.method
    headers = dict(request.headers)
    query_params = dict(request.query_params)
    
    # 获取请求体
    try:
        body = await request.json()
    except:
        try:
            body = await request.form()
            body = dict(body)
        except:
            body = None
    
    # 获取客户端IP
    client_ip = request.client.host if request.client else "unknown"
    
    # 构建请求上下文
    context = {
        "request": {
            "method": method,
            "path": full_path,
            "headers": headers,
            "query_params": query_params,
            "body": body,
            "client_ip": client_ip
        }
    }
    
    # 匹配路由
    matched_route = mock_router.match_route(method, full_path, headers, query_params, body)
    
    if matched_route:
        route, path_params = matched_route
        context["path"] = path_params
        context["query"] = query_params
        context["body"] = body or {}
        
        # 验证请求
        if route.validator:
            is_valid, error_msg = validator.validate_request(route.validator, body, headers)
            if not is_valid:
                # 生成验证错误响应
                if route.validator.error_response:
                    response = await generate_response(route.validator.error_response, context)
                else:
                    response = JSONResponse(
                        status_code=400,
                        content={"error": error_msg}
                    )
                
                # 记录请求和响应
                await record_request_and_response(
                    request_id, start_time, method, full_path, headers, query_params, body, 
                    client_ip, route.id, 400, response
                )
                
                return response
        
        # 生成响应
        response = await generate_response(route.response, context)
        
        # 记录请求和响应
        await record_request_and_response(
            request_id, start_time, method, full_path, headers, query_params, body, 
            client_ip, route.id, response.status_code, response
        )
        
        return response
    else:
        # 处理未匹配的请求
        if config.proxy.enable and config.proxy.target_url:
            # 代理模式：转发到真实后端
            response = await proxy_request(method, full_path, headers, query_params, body)
            
            # 记录请求和响应
            await record_request_and_response(
                request_id, start_time, method, full_path, headers, query_params, body, 
                client_ip, None, response.status_code, response
            )
            
            return response
        else:
            # 返回404
            response = JSONResponse(
                status_code=404,
                content={"error": "No matching route found"}
            )
            
            # 记录请求和响应
            await record_request_and_response(
                request_id, start_time, method, full_path, headers, query_params, body, 
                client_ip, None, 404, response
            )
            
            return response


async def generate_response(route_response, context):
    """生成响应"""
    # 应用延迟
    if route_response.delay > 0:
        await asyncio.sleep(route_response.delay)
    elif route_response.delay_range:
        min_delay, max_delay = route_response.delay_range
        delay = (max_delay - min_delay) * time.time() % (max_delay - min_delay) + min_delay
        await asyncio.sleep(delay)
    
    # 渲染响应内容
    rendered_content = templater.render_response(route_response.content, context)
    
    # 根据内容类型创建响应
    if route_response.content_type == "application/json":
        response = JSONResponse(
            status_code=route_response.status_code,
            content=rendered_content,
            headers=route_response.headers or {}
        )
    else:
        response = PlainTextResponse(
            status_code=route_response.status_code,
            content=str(rendered_content),
            headers=route_response.headers or {}
        )
    
    return response


async def record_request_and_response(request_id, start_time, method, path, headers, query_params, body, 
                                     client_ip, route_id, status_code, response):
    """记录请求和响应"""
    # 计算响应时间
    response_time = time.time() - start_time
    
    # 记录请求
    request_record = RequestModel(
        id=request_id,
        timestamp=start_time,
        method=method,
        path=path,
        query_params=query_params,
        headers=headers,
        body=body,
        client_ip=client_ip,
        matched_route_id=route_id,
        response_status=status_code,
        response_time=response_time
    )
    # 保存到内存
    request_history.append(request_record)
    # 保存到数据库
    db_storage.save_request(request_record)
    
    # 限制历史记录数量
    if len(request_history) > 1000:
        request_history.pop(0)
    
    # 记录响应
    response_id = str(uuid.uuid4())
    response_record = ResponseModel(
        id=response_id,
        request_id=request_id,
        timestamp=time.time(),
        status_code=status_code,
        headers=dict(response.headers),
        content=response.body.decode() if hasattr(response, 'body') else None,
        content_type=response.headers.get('content-type', 'application/json'),
        response_time=response_time,
        delay_applied=0.0  # 实际应用的延迟可以从响应配置中获取
    )
    # 保存到内存
    response_history.append(response_record)
    # 保存到数据库
    db_storage.save_response(response_record)
    
    # 限制历史记录数量
    if len(response_history) > 1000:
        response_history.pop(0)


async def proxy_request(method: str, path: str, headers: dict, query_params: dict, body: Any):
    """代理请求到真实后端"""
    import httpx
    
    # 构建目标URL
    target_url = f"{config.proxy.target_url}{path}"
    
    # 移除host头部，由httpx自动设置
    headers.pop('host', None)
    
    # 发送请求
    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(target_url, headers=headers, params=query_params)
            elif method == "POST":
                response = await client.post(target_url, headers=headers, params=query_params, json=body)
            elif method == "PUT":
                response = await client.put(target_url, headers=headers, params=query_params, json=body)
            elif method == "DELETE":
                response = await client.delete(target_url, headers=headers, params=query_params)
            elif method == "PATCH":
                response = await client.patch(target_url, headers=headers, params=query_params, json=body)
            elif method == "HEAD":
                response = await client.head(target_url, headers=headers, params=query_params)
            elif method == "OPTIONS":
                response = await client.options(target_url, headers=headers, params=query_params)
            else:
                return JSONResponse(
                    status_code=405,
                    content={"error": "Method not allowed"}
                )
            
            # 构建响应
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except Exception as e:
            return JSONResponse(
                status_code=502,
                content={"error": f"Proxy error: {str(e)}"}
            )


# 辅助函数：添加路由
def add_route(route):
    """添加路由"""
    mock_router.add_route(route)


def remove_route(route_id):
    """移除路由"""
    mock_router.remove_route(route_id)


def update_route(route):
    """更新路由"""
    mock_router.update_route(route)


def get_all_routes():
    """获取所有路由"""
    return mock_router.get_all_routes()


def get_request_history(limit: int = 1000, offset: int = 0):
    """获取请求历史
    
    Args:
        limit: 返回记录数量限制
        offset: 偏移量
        
    Returns:
        请求历史列表
    """
    # 从数据库中获取请求历史
    return db_storage.get_requests(limit=limit, offset=offset)


def get_response_history():
    """获取响应历史"""
    return response_history


def get_server_uptime():
    """获取服务器运行时间"""
    return time.time() - server_start_time
