from typing import Dict, Optional, Any
import time
from pydantic import BaseModel, Field


class Response(BaseModel):
    """响应记录"""
    id: str = Field(..., description="响应唯一标识符")
    request_id: str = Field(..., description="关联的请求ID")
    timestamp: float = Field(..., description="响应时间戳")
    status_code: int = Field(..., description="HTTP状态码")
    headers: Dict[str, str] = Field(..., description="响应头部")
    content: Optional[Any] = Field(default=None, description="响应内容")
    content_type: str = Field(default="application/json", description="响应内容类型")
    response_time: float = Field(..., description="响应时间（秒）")
    delay_applied: float = Field(default=0.0, description="应用的延迟时间（秒）")


class ErrorResponse(BaseModel):
    """错误响应"""
    code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="错误详细信息")
    timestamp: float = Field(default_factory=time.time, description="错误时间戳")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(default="healthy", description="服务状态")
    timestamp: float = Field(default_factory=time.time, description="检查时间戳")
    version: str = Field(..., description="服务版本")
    uptime: float = Field(..., description="服务运行时间（秒）")
    stats: Dict[str, Any] = Field(default_factory=dict, description="服务统计信息")
