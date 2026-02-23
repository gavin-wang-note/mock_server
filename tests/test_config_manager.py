import pytest
from app.services.config_manager import config_manager
import os
import tempfile
import yaml


class TestConfigManager:
    """测试配置管理器功能"""

    def test_get_current_env(self):
        """测试获取当前环境"""
        env = config_manager.get_current_env()
        assert env is not None
        assert isinstance(env, str)

    def test_get_config_history(self):
        """测试获取配置历史"""
        history = config_manager.get_config_history("default", 10)
        assert isinstance(history, list)

    def test_save_config(self):
        """测试保存配置"""
        # 测试保存配置到默认环境
        config_data = {
            "server": {
                "host": "127.0.0.1",
                "port": 8080
            }
        }
        success = config_manager.save_config(config_data, "default")
        assert success

    def test_load_config(self):
        """测试加载配置"""
        # 测试加载默认环境配置
        config_data = config_manager.load_config("default")
        assert isinstance(config_data, dict)

    def test_backup_config(self):
        """测试备份配置"""
        # 测试备份配置
        backup_path = config_manager.backup_config("default")
        assert backup_path is not None
        assert isinstance(backup_path, str)
        assert os.path.exists(backup_path)
        
        # 清理备份文件
        if os.path.exists(backup_path):
            os.remove(backup_path)

    def test_restore_config(self):
        """测试恢复配置"""
        # 先创建一个备份
        backup_path = config_manager.backup_config("default")
        
        try:
            # 测试恢复配置
            success = config_manager.restore_config(backup_path, "default")
            assert success
        finally:
            # 清理备份文件
            if os.path.exists(backup_path):
                os.remove(backup_path)

    def test_get_all_backups(self):
        """测试获取所有备份"""
        backups = config_manager.get_all_backups()
        assert isinstance(backups, list)

    def test_switch_env(self):
        """测试切换环境"""
        # 先为development环境创建一个配置文件
        dev_config = {
            "server": {
                "host": "127.0.0.1",
                "port": 8080
            }
        }
        config_manager.save_config(dev_config, "development")
        
        # 测试切换到development环境
        success = config_manager.switch_env("development")
        assert success

        # 测试切换回默认环境
        success = config_manager.switch_env("default")
        assert success

