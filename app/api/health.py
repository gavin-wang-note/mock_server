import time
import json
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, HTMLResponse
from app.models.response import HealthResponse
from app.api.mock import get_server_uptime, get_request_history
from app.core.config import config

# 创建路由处理实例
router = APIRouter()


@router.get("/health")
async def health_check(request: Request):
    """健康检查端点"""
    # 获取服务运行时间
    uptime = get_server_uptime()
    
    # 获取请求历史，计算统计信息
    request_history = get_request_history()
    total_requests = len(request_history)
    
    # 计算最近5分钟的请求数
    import time
    from datetime import datetime
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
        version="V1.0.0",
        uptime=uptime,
        stats=stats
    )
    
    # 检查是否需要返回 JSON 还是 HTML
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        # 返回 HTML 页面
        health_data = response.model_dump()
        is_healthy = health_data.get("status") == "healthy"
        
        # 生成 JSON 字符串
        json_str = json.dumps(health_data, indent=2, ensure_ascii=False)
        
        # 构建 HTML 内容
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Health Check</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .health-status {{
                    text-align: center;
                    margin: 20px 0;
                    padding: 20px;
                    border-radius: 8px;
                    font-size: 18px;
                    font-weight: bold;
                }}
                .healthy {{
                    background-color: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }}
                .unhealthy {{
                    background-color: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }}
                .json-content {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid #dee2e6;
                    margin: 20px 0;
                    font-family: monospace;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }}
                .stats {{
                    margin: 20px 0;
                }}
                .stat-item {{
                    margin: 10px 0;
                    padding: 10px;
                    background-color: #f8f9fa;
                    border-radius: 4px;
                }}
                .stat-label {{
                    font-weight: bold;
                    margin-right: 10px;
                }}
                .back-link {{
                    display: block;
                    text-align: center;
                    margin-top: 30px;
                    text-decoration: none;
                    color: #4a90e2;
                    font-weight: bold;
                }}
                .back-link:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>健康检查</h1>
                <div class="health-status {'healthy' if is_healthy else 'unhealthy'}">
                    服务状态: {'健康' if is_healthy else '不健康'}
                </div>
                <div class="stats">
                    <div class="stat-item">
                        <span class="stat-label">版本:</span> {health_data.get('version')}
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">运行时间:</span> {health_data.get('uptime', 0):.2f} 秒
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">总请求数:</span> {health_data.get('stats', {}).get('total_requests', 0)}
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">最近5分钟请求数:</span> {health_data.get('stats', {}).get('recent_requests', 0)}
                    </div>
                </div>
                <h2>详细信息</h2>
                <div class="json-content">
                    {json_str}
                </div>
                <a href="/" class="back-link">返回首页</a>
            </div>
        </body>
        </html>
        '''
        
        return HTMLResponse(content=html_content)
    else:
        # 返回 JSON 响应
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
        "version": "V1.0.0",
        "description": "企业级 Python Mock Server",
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
