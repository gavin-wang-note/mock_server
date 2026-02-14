from typing import Dict, Optional, Any
from pydantic import BaseModel, Field


class Request(BaseModel):
    """请求记录"""
    id: str = Field(..., description="请求唯一标识符")
    timestamp: float = Field(..., description="请求时间戳")
    method: str = Field(..., description="HTTP方法")
    path: str = Field(..., description="请求路径")
    query_params: Optional[Dict[str, Any]] = Field(default=None, description="查询参数")
    headers: Dict[str, str] = Field(..., description="HTTP头部")
    body: Optional[Any] = Field(default=None, description="请求体")
    client_ip: str = Field(..., description="客户端IP地址")
    matched_route_id: Optional[str] = Field(default=None, description="匹配的路由ID")
    response_status: Optional[int] = Field(default=None, description="响应状态码")
    response_time: Optional[float] = Field(default=None, description="响应时间（秒）")


class RequestFilter(BaseModel):
    """请求过滤条件"""
    start_time: Optional[datetime] = Field(default=None, description="开始时间")
    end_time: Optional[datetime] = Field(default=None, description="结束时间")
    method: Optional[str] = Field(default=None, description="HTTP方法")
    path: Optional[str] = Field(default=None, description="请求路径")
    status_code: Optional[int] = Field(default=None, description="响应状态码")
    client_ip: Optional[str] = Field(default=None, description="客户端IP地址")
    limit: int = Field(default=100, description="返回记录数限制")
    offset: int = Field(default=0, description="分页偏移量")
