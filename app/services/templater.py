import random
import time
from typing import Dict, Any, Optional
import json


class Templater:
    """响应模板服务"""
    
    def render_response(self, content: Any, context: Dict[str, Any] = None) -> Any:
        """渲染响应内容
        
        Args:
            content: 响应内容模板
            context: 上下文变量（包含请求参数、路径参数等）
            
        Returns:
            渲染后的响应内容
        """
        if context is None:
            context = {}
        
        # 递归处理响应内容
        return self._render_value(content, context)
    
    def _render_value(self, value: Any, context: Dict[str, Any]) -> Any:
        """递归渲染值"""
        if isinstance(value, str):
            return self._render_string(value, context)
        elif isinstance(value, dict):
            return {k: self._render_value(v, context) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._render_value(item, context) for item in value]
        else:
            return value
    
    def _render_string(self, template: str, context: Dict[str, Any]) -> str:
        """渲染字符串模板
        
        支持的模板变量：
        - {{request.*}}: 请求相关变量
        - {{path.*}}: 路径参数
        - {{query.*}}: 查询参数
        - {{body.*}}: 请求体参数
        - {{random.*}}: 随机数据
        - {{timestamp}}: 当前时间戳
        - {{now}}: 当前时间
        """
        result = template
        
        # 替换复杂变量（支持嵌套访问，如request.headers.user-agent）
        import re
        # 匹配模板变量模式：{{namespace.key1.key2...}}
        pattern = r'\{\{(\w+\.(?:[\w-]+\.)*[\w-]+)\}\}'
        matches = re.findall(pattern, result)
        
        for match in matches:
            placeholder = f"{{{{{match}}}}}"
            # 解析变量路径
            parts = match.split('.')
            if len(parts) < 2:
                continue
            
            namespace = parts[0]
            nested_keys = parts[1:]
            
            # 获取基础对象
            if namespace not in context:
                continue
            
            # 遍历嵌套键
            current = context[namespace]
            for key in nested_keys:
                # 处理特殊情况，如user-agent
                if isinstance(current, dict):
                    # 尝试直接访问
                    if key in current:
                        current = current[key]
                    else:
                        # 尝试大小写不敏感访问（适用于headers）
                        found = False
                        for k, v in current.items():
                            if k.lower() == key.lower():
                                current = v
                                found = True
                                break
                        if not found:
                            break
                else:
                    break
            else:
                # 成功遍历所有嵌套键
                if placeholder in result:
                    result = result.replace(placeholder, str(current))
        
        # 替换简单变量
        # 替换路径参数
        if 'path' in context:
            for key, value in context['path'].items():
                placeholder = f"{{{{path.{key}}}}}"
                if placeholder in result:
                    result = result.replace(placeholder, str(value))
        
        # 替换查询参数
        if 'query' in context:
            for key, value in context['query'].items():
                placeholder = f"{{{{query.{key}}}}}"
                if placeholder in result:
                    result = result.replace(placeholder, str(value))
        
        # 替换请求体参数
        if 'body' in context:
            for key, value in context['body'].items():
                placeholder = f"{{{{body.{key}}}}}"
                if placeholder in result:
                    result = result.replace(placeholder, str(value))
        
        # 替换随机数据
        if '{{random.int}}' in result:
            result = result.replace('{{random.int}}', str(random.randint(1, 1000)))
        
        if '{{random.string}}' in result:
            result = result.replace('{{random.string}}', self._generate_random_string())
        
        if '{{random.boolean}}' in result:
            result = result.replace('{{random.boolean}}', str(random.choice([True, False])))
        
        # 替换时间戳
        if '{{timestamp}}' in result:
            result = result.replace('{{timestamp}}', str(int(time.time())))
        
        if '{{now}}' in result:
            result = result.replace('{{now}}', time.strftime('%Y-%m-%d %H:%M:%S'))
        
        return result
    
    def _generate_random_string(self, length: int = 8) -> str:
        """生成随机字符串"""
        import string
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def generate_random_data(self, data_type: str, **kwargs) -> Any:
        """生成随机数据
        
        Args:
            data_type: 数据类型 (int, string, boolean, array, object)
            **kwargs: 额外参数
            
        Returns:
            生成的随机数据
        """
        if data_type == 'int':
            min_val = kwargs.get('min', 1)
            max_val = kwargs.get('max', 1000)
            return random.randint(min_val, max_val)
        
        elif data_type == 'string':
            length = kwargs.get('length', 8)
            return self._generate_random_string(length)
        
        elif data_type == 'boolean':
            return random.choice([True, False])
        
        elif data_type == 'array':
            item_type = kwargs.get('item_type', 'string')
            length = kwargs.get('length', 5)
            return [self.generate_random_data(item_type) for _ in range(length)]
        
        elif data_type == 'object':
            fields = kwargs.get('fields', {})
            return {key: self.generate_random_data(value) for key, value in fields.items()}
        
        else:
            return None
