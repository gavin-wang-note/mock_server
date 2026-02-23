import pytest
import gc
import tracemalloc


@pytest.fixture(scope="session", autouse=True)
def setup_tracemalloc():
    """设置 tracemalloc 以获取对象分配回溯"""
    tracemalloc.start()
    yield
    tracemalloc.stop()


@pytest.fixture(scope="function", autouse=True)
def cleanup_db():
    """确保在测试结束后清理数据库连接"""
    # 测试开始前的设置
    yield
    # 测试结束后的清理
    # 强制垃圾回收，确保所有连接都被关闭
    gc.collect()
