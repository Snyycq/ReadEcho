"""
model_cache.py 单元测试
测试模型缓存功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from model_cache import ModelCache  # noqa: E402


class TestModelCache:
    """测试模型缓存"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        cache1 = ModelCache()
        cache2 = ModelCache()
        assert cache1 is cache2

    def test_initial_state(self):
        """测试初始状态"""
        cache = ModelCache()
        assert cache.get_cached_models() == {}

    def test_get_cached_models_empty(self):
        """测试获取空模型信息"""
        cache = ModelCache()
        info = cache.get_cached_models()
        assert info == {}


class TestModelCacheCleanup:
    """测试模型缓存清理"""

    def test_clear_cache(self):
        """测试清空缓存"""
        cache = ModelCache()
        cache.clear_cache()
        assert cache.get_cached_models() == {}


class TestThreadSafety:
    """测试线程安全性（基础检查）"""

    def test_concurrent_access(self):
        """测试并发访问基础功能"""
        import threading

        cache = ModelCache()
        results = []

        def check_cache():
            results.append(len(cache.get_cached_models()))

        threads = []
        for _ in range(10):
            t = threading.Thread(target=check_cache)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(results) == 10
        assert all(r == 0 for r in results)
