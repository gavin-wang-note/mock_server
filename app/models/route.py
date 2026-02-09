from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field


class RouteMatchRule(BaseModel):
    """路由匹配规则"""
    # 路径匹配
    path: str = Field(..., description="路由路径，支持RESTful风格如/api/users/{id}")
    methods: List[str] = Field(..., description="HTTP方法列表，如[GET, POST]")
    
    # 高级匹配规则
    headers: Optional[Dict[str, Union[str, List[str]]]] = Field(default=None, description="HTTP头部匹配规则")
    query_params: Optional[Dict[str, Union[str, List[str]]]] = Field(default=None, description="查询参数匹配规则")
    body: Optional[Dict[str, Any]] = Field(default=None, description="请求体匹配规则")
    
    # 正则表达式匹配标志
    use_regex: bool = Field(default=False, description="是否使用正则表达式匹配")


class RouteResponse(BaseModel):
    """路由响应配置"""
    status_code: int = Field(default=200, description="HTTP状态码")
    headers: Optional[Dict[str, str]] = Field(default=None, description="响应头部")
    content: Any = Field(default=None, description="响应内容")
    content_type: str = Field(default="application/json", description="响应内容类型")
    delay: float = Field(default=0.0, description="响应延迟（秒）")
    delay_range: Optional[List[float]] = Field(default=None, description="随机延迟范围 [min, max]")


class RouteValidator(BaseModel):
    """路由验证规则"""
    required_fields: Optional[List[str]] = Field(default=None, description="必填字段列表")
    field_types: Optional[Dict[str, str]] = Field(default=None, description="字段类型验证")
    field_ranges: Optional[Dict[str, List[Any]]] = Field(default=None, description="字段值范围验证")
    validate_jwt: bool = Field(default=False, description="是否验证JWT令牌")
    error_response: Optional[RouteResponse] = Field(default=None, description="验证失败的错误响应")


class Route(BaseModel):
    """路由定义"""
    id: str = Field(..., description="路由唯一标识符")
    name: str = Field(..., description="路由名称")
    enabled: bool = Field(default=True, description="是否启用")
    match_rule: RouteMatchRule = Field(..., description="匹配规则")
    response: RouteResponse = Field(..., description="响应配置")
    validator: Optional[RouteValidator] = Field(default=None, description="验证规则")
    tags: Optional[List[str]] = Field(default=None, description="路由标签")
    created_at: float = Field(..., description="创建时间戳")
    updated_at: float = Field(..., description="更新时间戳")


class RouteCreate(BaseModel):
    """创建路由请求"""
    name: str = Field(..., description="路由名称")
    match_rule: RouteMatchRule = Field(..., description="匹配规则")
    response: RouteResponse = Field(..., description="响应配置")
    validator: Optional[RouteValidator] = Field(default=None, description="验证规则")
    tags: Optional[List[str]] = Field(default=None, description="路由标签")


class RouteUpdate(BaseModel):
    """更新路由请求"""
    name: Optional[str] = Field(default=None, description="路由名称")
    enabled: Optional[bool] = Field(default=None, description="是否启用")
    match_rule: Optional[RouteMatchRule] = Field(default=None, description="匹配规则")
    response: Optional[RouteResponse] = Field(default=None, description="响应配置")
    validator: Optional[RouteValidator] = Field(default=None, description="验证规则")
    tags: Optional[List[str]] = Field(default=None, description="路由标签")
