import yaml
import json
import os
import time
from typing import List, Optional
from app.models.route import Route
from app.core.config import config


class FileStorage:
    """文件存储系统"""
    
    def __init__(self, config_file: Optional[str] = None):
        """初始化文件存储
        
        Args:
            config_file: 配置文件路径，默认使用配置中的路径
        """
        self.config_file = config_file or config.storage.config_file
        # 确保配置文件目录存在
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
    
    def load_routes(self) -> List[Route]:
        """从文件加载路由配置
        
        Returns:
            路由列表
        """
        routes = []
        
        # 检查文件是否存在
        if not os.path.exists(self.config_file):
            return routes
        
        # 读取文件
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    data = yaml.safe_load(f)
                elif self.config_file.endswith('.json'):
                    data = json.load(f)
                else:
                    # 默认使用YAML格式
                    data = yaml.safe_load(f)
            
            # 解析路由数据
            if data and 'routes' in data:
                for route_data in data['routes']:
                    try:
                        # 添加缺失的字段
                        if 'created_at' not in route_data:
                            route_data['created_at'] = time.time()
                        if 'updated_at' not in route_data:
                            route_data['updated_at'] = time.time()
                        route = Route(**route_data)
                        routes.append(route)
                    except Exception as e:
                        print(f"解析路由失败: {e}")
        except Exception as e:
            print(f"加载配置文件失败: {e}")
        
        return routes
    
    def save_routes(self, routes: List[Route]) -> bool:
        """保存路由配置到文件
        
        Args:
            routes: 路由列表
            
        Returns:
            是否保存成功
        """
        try:
            # 构建配置数据
            data = {
                'routes': [route.model_dump() for route in routes]
            }
            
            # 写入文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
                elif self.config_file.endswith('.json'):
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    # 默认使用YAML格式
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def load_config(self) -> Optional[dict]:
        """加载完整配置
        
        Returns:
            配置字典
        """
        try:
            if not os.path.exists(self.config_file):
                return None
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    return yaml.safe_load(f)
                elif self.config_file.endswith('.json'):
                    return json.load(f)
                else:
                    return yaml.safe_load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return None
    
    def save_config(self, config_data: dict) -> bool:
        """保存完整配置
        
        Args:
            config_data: 配置字典
            
        Returns:
            是否保存成功
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
                elif self.config_file.endswith('.json'):
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                else:
                    yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def exists(self) -> bool:
        """检查配置文件是否存在
        
        Returns:
            是否存在
        """
        return os.path.exists(self.config_file)
    
    def get_file_path(self) -> str:
        """获取配置文件路径
        
        Returns:
            文件路径
        """
        return self.config_file


# 创建全局文件存储实例
file_storage = FileStorage()
