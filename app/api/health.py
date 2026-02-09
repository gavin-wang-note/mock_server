import time
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.models.response import HealthResponse
from app.api.mock import get_server_uptime, get_request_history
from app.core.config import config

# 创建路由处理实例
router = APIRouter()


@router.get("/health")
async def health_check():
    """健康检查端点"""
    # 获取服务运行时间
    uptime = get_server_uptime()
    
    # 获取请求历史，计算统计信息
    request_history = get_request_history()
    total_requests = len(request_history)
    
    # 计算最近5分钟的请求数
    import time
    five_minutes_ago = time.time() - 300
    recent_requests = len([r for r in request_history if r.timestamp > five_minutes_ago])
    
    # 计算请求状态码分布
    status_code_counts = {}
    for req in request_history:
        if req.response_status:
            status_code = req.response_status
            status_code_counts[status_code] = status_code_counts.get(status_code, 0) + 1
    
    # 构建统计信息
    stats = {
        "total_requests": total_requests,
        "recent_requests": recent_requests,
        "status_code_distribution": status_code_counts,
        "uptime_seconds": uptime,
        "proxy_enabled": config.proxy.enable,
        "admin_enabled": config.admin.enable
    }
    
    # 构建健康检查响应
    response = HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime=uptime,
        stats=stats
    )
    
    return JSONResponse(content=response.model_dump())


@router.get("/metrics")
async def get_metrics():
    """获取服务运行指标"""
    # 获取服务运行时间
    uptime = get_server_uptime()
    
    # 获取请求历史
    request_history = get_request_history()
    total_requests = len(request_history)
    
    # 计算平均响应时间
    total_response_time = sum(req.response_time for req in request_history if req.response_time)
    avg_response_time = total_response_time / total_requests if total_requests > 0 else 0
    
    # 计算请求方法分布
    method_counts = {}
    for req in request_history:
        method = req.method
        method_counts[method] = method_counts.get(method, 0) + 1
    
    # 构建指标响应
    metrics = {
        "uptime_seconds": uptime,
        "total_requests": total_requests,
        "average_response_time": avg_response_time,
        "method_distribution": method_counts,
        "server_time": time.time(),
        "config": {
            "host": config.server.host,
            "port": config.server.port,
            "enable_https": config.server.enable_https
        }
    }
    
    return JSONResponse(content=metrics)


@router.get("/info")
async def get_service_info():
    """获取服务信息"""
    info = {
        "name": "Mock Server",
        "version": "1.0.0",
        "description": "企业级Python Mock Server",
        "features": [
            "Dynamic routing",
            "RESTful API support",
            "Request validation",
            "Template-based responses",
            "Request history",
            "Proxy mode",
            "Health checks"
        ],
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "info": "/info"
        }
    }
    
    return JSONResponse(content=info)
