from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field
import os
import yaml


class ServerConfig(BaseSettings):
    """服务器配置"""
    host: str = Field(default="0.0.0.0", description="服务器监听地址")
    port: int = Field(default=8080, description="服务器监听端口")
    enable_https: bool = Field(default=False, description="是否启用HTTPS")
    https_cert: Optional[str] = Field(default=None, description="HTTPS证书路径")
    https_key: Optional[str] = Field(default=None, description="HTTPS私钥路径")
    
    class Config:
        env_prefix = "SERVER_"


class AdminConfig(BaseSettings):
    """管理界面配置"""
    enable: bool = Field(default=True, description="是否启用管理界面")
    username: str = Field(default="admin", description="管理界面用户名")
    password: str = Field(default="password", description="管理界面密码")
    enable_api: bool = Field(default=True, description="是否启用管理API")
    
    class Config:
        env_prefix = "ADMIN_"


class StorageConfig(BaseSettings):
    """存储配置"""
    enable_persistence: bool = Field(default=True, description="是否启用配置持久化")
    config_file: str = Field(default="config/default.yaml", description="配置文件路径")
    db_path: str = Field(default="data/mock_server.db", description="数据库文件路径")
    
    class Config:
        env_prefix = "STORAGE_"


class ProxyConfig(BaseSettings):
    """代理配置"""
    enable: bool = Field(default=False, description="是否启用代理模式")
    target_url: Optional[str] = Field(default=None, description="目标后端URL")
    
    class Config:
        env_prefix = "PROXY_"


class LogConfig(BaseSettings):
    """日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    file: Optional[str] = Field(default=None, description="日志文件路径")
    
    class Config:
        env_prefix = "LOG_"


def load_yaml_config(config_file: str) -> Dict[str, Any]:
    """加载YAML配置文件
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        配置字典
    """
    if not os.path.exists(config_file):
        return {}
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return {}


class AppConfig(BaseSettings):
    """应用全局配置"""
    server: ServerConfig = ServerConfig()
    admin: AdminConfig = AdminConfig()
    storage: StorageConfig = StorageConfig()
    proxy: ProxyConfig = ProxyConfig()
    log: LogConfig = LogConfig()
    
    class Config:
        env_nested_delimiter = "__"
        case_sensitive = False


# 首先加载YAML配置文件，获取默认的配置文件路径
temp_storage = StorageConfig()
config_file_path = temp_storage.config_file

# 加载YAML配置文件
yaml_config = load_yaml_config(config_file_path)

# 从YAML配置中提取各部分配置
server_from_yaml = yaml_config.get('server', {})
admin_from_yaml = yaml_config.get('admin', {})
storage_from_yaml = yaml_config.get('storage', {})
proxy_from_yaml = yaml_config.get('proxy', {})
log_from_yaml = yaml_config.get('log', {})

# 创建各个子配置类的实例，让它们从环境变量中获取值
# 注意：我们不传递任何参数，让Pydantic自己处理环境变量和默认值
server_config = ServerConfig()
admin_config = AdminConfig()
storage_config = StorageConfig()
proxy_config = ProxyConfig()
log_config = LogConfig()

# 检查环境变量是否设置了值，如果没有，就使用YAML配置中的值
# 这样可以确保环境变量的优先级高于YAML配置

# 服务器配置
if not os.getenv('SERVER_HOST') and 'host' in server_from_yaml:
    server_config.host = server_from_yaml['host']
if not os.getenv('SERVER_PORT') and 'port' in server_from_yaml:
    server_config.port = server_from_yaml['port']
if not os.getenv('SERVER_ENABLE_HTTPS') and 'enable_https' in server_from_yaml:
    server_config.enable_https = server_from_yaml['enable_https']
if not os.getenv('SERVER_HTTPS_CERT') and 'https_cert' in server_from_yaml:
    server_config.https_cert = server_from_yaml['https_cert']
if not os.getenv('SERVER_HTTPS_KEY') and 'https_key' in server_from_yaml:
    server_config.https_key = server_from_yaml['https_key']

# 管理界面配置
if not os.getenv('ADMIN_ENABLE') and 'enable' in admin_from_yaml:
    admin_config.enable = admin_from_yaml['enable']
if not os.getenv('ADMIN_USERNAME') and 'username' in admin_from_yaml:
    admin_config.username = admin_from_yaml['username']
if not os.getenv('ADMIN_PASSWORD') and 'password' in admin_from_yaml:
    admin_config.password = admin_from_yaml['password']
if not os.getenv('ADMIN_ENABLE_API') and 'enable_api' in admin_from_yaml:
    admin_config.enable_api = admin_from_yaml['enable_api']

# 存储配置
if not os.getenv('STORAGE_ENABLE_PERSISTENCE') and 'enable_persistence' in storage_from_yaml:
    storage_config.enable_persistence = storage_from_yaml['enable_persistence']
if not os.getenv('STORAGE_CONFIG_FILE') and 'config_file' in storage_from_yaml:
    storage_config.config_file = storage_from_yaml['config_file']
if not os.getenv('STORAGE_DB_PATH') and 'db_path' in storage_from_yaml:
    storage_config.db_path = storage_from_yaml['db_path']

# 代理配置
if not os.getenv('PROXY_ENABLE') and 'enable' in proxy_from_yaml:
    proxy_config.enable = proxy_from_yaml['enable']
if not os.getenv('PROXY_TARGET_URL') and 'target_url' in proxy_from_yaml:
    proxy_config.target_url = proxy_from_yaml['target_url']

# 日志配置
if not os.getenv('LOG_LEVEL') and 'level' in log_from_yaml:
    log_config.level = log_from_yaml['level']
if not os.getenv('LOG_FILE') and 'file' in log_from_yaml:
    log_config.file = log_from_yaml['file']

# 创建最终的配置实例
config = AppConfig(
    server=server_config,
    admin=admin_config,
    storage=storage_config,
    proxy=proxy_config,
    log=log_config
)
