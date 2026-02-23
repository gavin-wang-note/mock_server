import pytest
from app.services.data_manager import data_manager
import time
import os


class TestDataManager:
    """测试数据管理器功能"""

    def test_cleanup_requests(self):
        """测试清理请求历史"""
        # 测试清理请求历史
        result = data_manager.cleanup_requests(max_age_days=30, max_records=10000, archive=False)
        assert isinstance(result, dict)
        assert "total_records" in result
        assert "cleaned_records" in result
        assert "kept_records" in result

    def test_get_archives(self):
        """测试获取所有归档文件"""
        archives = data_manager.get_archives()
        assert isinstance(archives, list)

    def test_get_cleanup_strategy(self):
        """测试获取清理策略"""
        strategy = data_manager.get_cleanup_strategy()
        assert isinstance(strategy, dict)
        assert "max_age_days" in strategy
        assert "max_records" in strategy
        assert "archive_before_cleanup" in strategy

    def test_set_cleanup_strategy(self):
        """测试设置清理策略"""
        # 测试设置清理策略
        new_strategy = {
            "max_age_days": 15,
            "max_records": 5000,
            "archive_before_cleanup": False
        }
        success = data_manager.set_cleanup_strategy(new_strategy)
        assert success
        
        # 验证策略是否设置成功
        strategy = data_manager.get_cleanup_strategy()
        assert strategy["max_age_days"] == 15
        assert strategy["max_records"] == 5000
        assert strategy["archive_before_cleanup"] is False
        
        # 恢复默认策略
        default_strategy = {
            "max_age_days": 30,
            "max_records": 10000,
            "archive_before_cleanup": True
        }
        data_manager.set_cleanup_strategy(default_strategy)

    def test_run_auto_cleanup(self):
        """测试运行自动清理"""
        result = data_manager.run_auto_cleanup()
        assert isinstance(result, dict)
        assert "total_records" in result
        assert "cleaned_records" in result
        assert "kept_records" in result

