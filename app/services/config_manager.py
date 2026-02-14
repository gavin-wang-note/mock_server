import os
import json
import yaml
import time
from typing import Dict, Any, List, Optional
from app.core.config import config
from app.storage.database import db_storage


class ConfigManager:
    """配置管理类"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.config_dir = os.path.dirname(config.storage.config_file)
        self.env_configs = {
            'development': 'config/development.yaml',
            'testing': 'config/testing.yaml',
            'production': 'config/production.yaml'
        }
        # 确保配置目录存在
        for env_file in self.env_configs.values():
            os.makedirs(os.path.dirname(env_file), exist_ok=True)
    
    def load_config(self, env: str = 'default') -> Dict[str, Any]:
        """加载指定环境的配置
        
        Args:
            env: 环境名称
            
        Returns:
            配置字典
        """
        if env == 'default':
            config_file = config.storage.config_file
        else:
            config_file = self.env_configs.get(env, config.storage.config_file)
        
        if not os.path.exists(config_file):
            return {}
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    return yaml.safe_load(f)
                elif config_file.endswith('.json'):
                    return json.load(f)
                else:
                    return yaml.safe_load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}
    
    def save_config(self, config_data: Dict[str, Any], env: str = 'default') -> bool:
        """保存配置到指定环境
        
        Args:
            config_data: 配置字典
            env: 环境名称
            
        Returns:
            是否保存成功
        """
        if env == 'default':
            config_file = config.storage.config_file
        else:
            config_file = self.env_configs.get(env, config.storage.config_file)
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
                elif config_file.endswith('.json'):
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                else:
                    yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            # 记录配置变更历史
            self.record_config_history(config_data, env)
            
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def record_config_history(self, config_data: Dict[str, Any], env: str = 'default'):
        """记录配置变更历史
        
        Args:
            config_data: 配置字典
            env: 环境名称
        """
        history_entry = {
            'timestamp': time.time(),
            'env': env,
            'config': config_data,
            'user': 'admin'  # 实际应用中应该从认证信息中获取
        }
        
        # 保存到数据库
        db_storage.save_config(f'config_history_{env}', history_entry)
    
    def get_config_history(self, env: str = 'default', limit: int = 10) -> List[Dict[str, Any]]:
        """获取配置变更历史
        
        Args:
            env: 环境名称
            limit: 返回记录数量限制
            
        Returns:
            配置变更历史列表
        """
        # 从数据库中获取历史记录
        # 这里简化处理，实际应该查询数据库中的历史记录
        history = []
        
        # 从数据库中获取最近的配置记录
        current_config = db_storage.get_config(f'config_history_{env}')
        if current_config:
            history.append(current_config)
        
        return history
    
    def backup_config(self, env: str = 'default', backup_name: Optional[str] = None) -> str:
        """备份配置
        
        Args:
            env: 环境名称
            backup_name: 备份名称
            
        Returns:
            备份文件路径
        """
        if not backup_name:
            backup_name = f"backup_{env}_{int(time.time())}"
        
        backup_dir = os.path.join(self.config_dir, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_file = os.path.join(backup_dir, f"{backup_name}.yaml")
        
        # 加载当前配置
        current_config = self.load_config(env)
        
        # 保存到备份文件
        with open(backup_file, 'w', encoding='utf-8') as f:
            yaml.dump(current_config, f, default_flow_style=False, allow_unicode=True)
        
        # 记录备份历史
        backup_history = {
            'timestamp': time.time(),
            'env': env,
            'backup_file': backup_file,
            'backup_name': backup_name
        }
        db_storage.save_config('backup_history', backup_history)
        
        return backup_file
    
    def restore_config(self, backup_file: str, env: str = 'default') -> bool:
        """从备份恢复配置
        
        Args:
            backup_file: 备份文件路径
            env: 环境名称
            
        Returns:
            是否恢复成功
        """
        if not os.path.exists(backup_file):
            return False
        
        try:
            # 加载备份配置
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_config = yaml.safe_load(f)
            
            # 保存到指定环境
            return self.save_config(backup_config, env)
        except Exception as e:
            print(f"恢复配置失败: {e}")
            return False
    
    def get_all_backups(self) -> List[Dict[str, Any]]:
        """获取所有备份
        
        Returns:
            备份列表
        """
        backup_dir = os.path.join(self.config_dir, 'backups')
        if not os.path.exists(backup_dir):
            return []
        
        backups = []
        for backup_file in os.listdir(backup_dir):
            if backup_file.endswith('.yaml') or backup_file.endswith('.yml'):
                backup_path = os.path.join(backup_dir, backup_file)
                backup_stat = os.stat(backup_path)
                backups.append({
                    'name': backup_file,
                    'path': backup_path,
                    'size': backup_stat.st_size,
                    'mtime': backup_stat.st_mtime
                })
        
        # 按修改时间排序
        backups.sort(key=lambda x: x['mtime'], reverse=True)
        
        return backups
    
    def switch_env(self, env: str) -> bool:
        """切换环境
        
        Args:
            env: 环境名称
            
        Returns:
            是否切换成功
        """
        if env not in self.env_configs and env != 'default':
            return False
        
        # 加载指定环境的配置
        env_config = self.load_config(env)
        if not env_config:
            return False
        
        # 保存到默认配置文件
        return self.save_config(env_config, 'default')
    
    def get_current_env(self) -> str:
        """获取当前环境
        
        Returns:
            当前环境名称
        """
        # 这里简化处理，实际应该从环境变量或配置文件中获取
        return 'default'


# 创建全局配置管理器实例
config_manager = ConfigManager()
