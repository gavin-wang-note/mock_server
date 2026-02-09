from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class ServerConfig(BaseSettings):
    """服务器配置"""
    host: str = Field(default="0.0.0.0", description="服务器监听地址")
    port: int = Field(default=8082, description="服务器监听端口")
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


# 创建全局配置实例
config = AppConfig()
