from typing import Dict, List, Optional, Any, Tuple
from app.models.route import RouteValidator
from app.core.security import verify_token


class Validator:
    """请求验证服务"""
    
    def validate_request(self, validator: RouteValidator, body: Optional[Dict[str, Any]] = None, 
                        headers: Optional[Dict[str, str]] = None) -> Tuple[bool, Optional[str]]:
        """验证请求
        
        Args:
            validator: 验证规则
            body: 请求体
            headers: HTTP头部
            
        Returns:
            (是否验证通过, 错误消息)
        """
        # 验证必填字段
        if validator.required_fields:
            if not body:
                return False, f"请求体不能为空，缺少必填字段: {', '.join(validator.required_fields)}"
            
            missing_fields = [field for field in validator.required_fields if field not in body]
            if missing_fields:
                return False, f"缺少必填字段: {', '.join(missing_fields)}"
        
        # 验证字段类型
        if validator.field_types and body:
            for field, expected_type in validator.field_types.items():
                if field in body:
                    if not self._validate_type(body[field], expected_type):
                        return False, f"字段 {field} 类型错误，期望类型: {expected_type}"
        
        # 验证字段值范围
        if validator.field_ranges and body:
            for field, range_values in validator.field_ranges.items():
                if field in body:
                    if not self._validate_range(body[field], range_values):
                        return False, f"字段 {field} 值超出范围"
        
        # 验证JWT令牌
        if validator.validate_jwt:
            if not headers:
                return False, "缺少HTTP头部"
            
            auth_header = headers.get('Authorization')
            if not auth_header:
                return False, "缺少Authorization头部"
            
            if not auth_header.startswith('Bearer '):
                return False, "Authorization头部格式错误"
            
            token = auth_header.split(' ')[1]
            if not verify_token(token):
                return False, "无效的JWT令牌"
        
        return True, None
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """验证字段类型"""
        expected_type = expected_type.lower()
        
        if expected_type == 'string':
            return isinstance(value, str)
        elif expected_type == 'number':
            return isinstance(value, (int, float))
        elif expected_type == 'integer':
            return isinstance(value, int)
        elif expected_type == 'boolean':
            return isinstance(value, bool)
        elif expected_type == 'array':
            return isinstance(value, list)
        elif expected_type == 'object':
            return isinstance(value, dict)
        elif expected_type == 'null':
            return value is None
        
        return True
    
    def _validate_range(self, value: Any, range_values: List[Any]) -> bool:
        """验证字段值范围
        
        range_values 格式:
        - [min, max]: 数值范围
        - [value1, value2, ...]: 枚举值
        - [min,]: 最小值
        - [:, max]: 最大值
        """
        if not range_values:
            return True
        
        # 处理数值范围
        if len(range_values) == 2 and all(isinstance(v, (int, float)) for v in range_values):
            min_val, max_val = range_values
            if isinstance(value, (int, float)):
                return min_val <= value <= max_val
        
        # 处理枚举值
        if value in range_values:
            return True
        
        # 处理最小值
        if len(range_values) == 1 and isinstance(range_values[0], (int, float)):
            if isinstance(value, (int, float)):
                return value >= range_values[0]
        
        return False
