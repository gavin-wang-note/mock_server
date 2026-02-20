import logging
import os
from app.core.config import config


class Logger:
    """日志管理类"""
    
    def __init__(self):
        """初始化日志配置"""
        self.logger = logging.getLogger('mock_server')
        self.logger.setLevel(self._get_log_level(config.log.level))
        
        # 清除已有的处理器
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self._get_log_level(config.log.level))
        
        # 创建文件处理器（如果配置了日志文件）
        file_handler = None
        if config.log.file:
            # 确保日志目录存在
            log_dir = os.path.dirname(config.log.file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            file_handler = logging.FileHandler(config.log.file, encoding='utf-8')
            file_handler.setLevel(self._get_log_level(config.log.level))
        
        # 定义日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 设置处理器格式
        console_handler.setFormatter(formatter)
        if file_handler:
            file_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(console_handler)
        if file_handler:
            self.logger.addHandler(file_handler)
    
    def _get_log_level(self, level_str: str) -> int:
        """将字符串日志级别转换为整数
        
        Args:
            level_str: 日志级别字符串 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            对应的日志级别整数
        """
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return level_map.get(level_str.upper(), logging.INFO)
    
    def get_logger(self) -> logging.Logger:
        """获取日志记录器实例
        
        Returns:
            配置好的日志记录器实例
        """
        return self.logger


# 创建全局日志实例
logger = Logger().get_logger()
