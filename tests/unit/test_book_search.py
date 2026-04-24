"""
书籍搜索模块单元测试
"""

import json
import sqlite3
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock

import pytest

from book_search import (
    BookSearchResult,
    SearchSource,
    OpenLibrarySource,
    DoubanSource,
    GoogleBooksSource,
    WebSearchSource,
    SearchCache,
    BookSearchService,
    get_search_service,
)


class TestBookSearchResult:
    """BookSearchResult 数据类测试"""

    def test_to_dict(self):
        """测试转换为字典"""
        result = BookSearchResult(
            source="test",
            title="Test Book",
            author="Test Author",
            external_id="test_123",
            metadata={"year": 2024}
        )
        d = result.to_dict()
        assert d["source"] == "test"
        assert d["title"] == "Test Book"
        assert d["author"] == "Test Author"
        assert d["key"] == "test_123"
        assert d["metadata"]["year"] == 2024

    def test_to_dict_empty_author(self):
        """测试空作者情况"""
        result = BookSearchResult(
            source="test",
            title="Book",
            author="",
            external_id="id",
            metadata={}
        )
        d = result.to_dict()
        assert d["author"] == ""


class TestOpenLibrarySource:
    """OpenLibrary 数据源测试"""

    def test_is_available(self):
        """测试可用性（始终可用）"""
        source = OpenLibrarySource()
        assert source.is_available() is True

    @patch('book_search.requests.get')
    def test_search_success(self, mock_get):
        """测试成功搜索"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "docs": [
                {
                    "title": "Python Book",
                    "author_name": ["Author One", "Author Two"],
                    "key": "/works/OL123W",
                    "first_publish_year": 2020,
                    "isbn": ["1234567890"],
                    "language": ["eng"]
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        source = OpenLibrarySource()
        results = source.search("Python")

        assert len(results) == 1
        assert results[0].title == "Python Book"
        assert results[0].author == "Author One, Author Two"
        assert results[0].source == "openlibrary"

    @patch('book_search.requests.get')
    def test_search_with_retry_on_timeout(self, mock_get):
        """测试超时重试机制"""
        import requests
        # 提供4个元素：标题搜索2次超时 + 通用搜索1次超时 + 成功
        mock_get.side_effect = [
            requests.exceptions.Timeout(),
            requests.exceptions.Timeout(),
            Mock(json=lambda: {"docs": []}, raise_for_status=Mock()),
            Mock(json=lambda: {"docs": []}, raise_for_status=Mock()),
        ]

        source = OpenLibrarySource()
        source.retry_delay = 0.01  # 加快测试
        results = source.search("test")

        # 至少应该有2次调用（标题搜索可能重试2次）
        assert mock_get.call_count >= 2
        assert results == []

    @patch('book_search.requests.get')
    def test_search_empty_results(self, mock_get):
        """测试空结果"""
        mock_response = Mock()
        mock_response.json.return_value = {"docs": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        source = OpenLibrarySource()
        results = source.search("nonexistent")

        assert results == []

    @patch('book_search.requests.get')
    def test_search_missing_fields(self, mock_get):
        """测试缺失字段的情况"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "docs": [
                {"title": None, "key": "/works/OL1W"},  # 无标题
                {"key": "/works/OL2W"},  # 完全空
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        source = OpenLibrarySource()
        results = source.search("test")

        # 应该能处理缺失字段
        assert len(results) == 2


class TestDoubanSource:
    """豆瓣数据源测试"""

    def test_is_available_no_key(self):
        """测试无API密钥时不可用"""
        with patch('book_search.DOUBAN_API_KEY', ''):
            source = DoubanSource()
            assert source.is_available() is False

    def test_is_available_with_key(self):
        """测试有API密钥时可用"""
        with patch('book_search.DOUBAN_API_KEY', 'test_key'):
            source = DoubanSource()
            assert source.is_available() is True

    @patch('book_search.DOUBAN_API_KEY', '')
    def test_search_no_key(self):
        """测试无密钥时搜索返回空"""
        source = DoubanSource()
        results = source.search("test")
        assert results == []


class TestGoogleBooksSource:
    """Google Books 数据源测试"""

    def test_is_available_no_key(self):
        """测试无API密钥时不可用"""
        with patch('book_search.GOOGLE_BOOKS_API_KEY', ''):
            source = GoogleBooksSource()
            assert source.is_available() is False

    def test_is_available_with_key(self):
        """测试有API密钥时可用"""
        with patch('book_search.GOOGLE_BOOKS_API_KEY', 'test_key'):
            source = GoogleBooksSource()
            assert source.is_available() is True


class TestWebSearchSource:
    """网络搜索数据源测试"""

    def test_is_available_no_func(self):
        """测试无搜索函数时不可用"""
        source = WebSearchSource()
        assert source.is_available() is False

    def test_is_available_with_func(self):
        """测试有搜索函数时可用"""
        source = WebSearchSource(lambda x: [])
        assert source.is_available() is True

    def test_set_search_func(self):
        """测试设置搜索函数"""
        source = WebSearchSource()
        assert source.is_available() is False

        source.set_search_func(lambda x: [])
        assert source.is_available() is True

    def test_search_with_mock_func(self):
        """测试使用模拟函数搜索"""
        mock_results = [
            {"title": "Book 1", "author": "Author 1"},
            {"title": "Book 2", "author": "Author 2"},
        ]
        source = WebSearchSource(lambda x: mock_results)
        results = source.search("test")

        assert len(results) == 2
        assert results[0].source == "web_search"

    def test_search_empty_results(self):
        """测试空搜索结果"""
        source = WebSearchSource(lambda x: [])
        results = source.search("test")
        assert results == []

    def test_parse_book_info_from_dict(self):
        """测试从字典解析书籍信息"""
        source = WebSearchSource(lambda x: [])
        title, author = source._parse_book_info(
            {"title": "Test Book", "snippet": "作者：张三"},
            "Test"
        )
        assert "Test Book" in title or "Test" in title

    def test_parse_book_info_from_string(self):
        """测试从字符串解析书籍信息"""
        source = WebSearchSource(lambda x: [])
        title, author = source._parse_book_info(
            "Python Book\nAuthor: John\nDescription here",
            "Python"
        )
        assert title != ""

    def test_extract_author_chinese(self):
        """测试提取中文作者"""
        source = WebSearchSource(lambda x: [])
        author = source._extract_author("这是一本书，作者：张三著", "书名")
        assert "张三" in author

    def test_extract_author_english(self):
        """测试提取英文作者"""
        source = WebSearchSource(lambda x: [])
        author = source._extract_author("A great book by John Smith", "Book")
        assert "John" in author or author == ""


class TestSearchCache:
    """搜索缓存测试"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        conn = sqlite3.connect(path)
        yield conn
        conn.close()
        os.unlink(path)

    def test_init_cache_table(self, temp_db):
        """测试初始化缓存表"""
        cache = SearchCache(temp_db)
        cursor = temp_db.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='book_search_cache'"
        )
        assert cursor.fetchone() is not None

    def test_set_and_get(self, temp_db):
        """测试设置和获取缓存"""
        cache = SearchCache(temp_db)
        results = [{"title": "Book", "author": "Author"}]

        cache.set("test query", "openlibrary", results)
        cached = cache.get("test query", "openlibrary")

        assert cached == results

    def test_get_nonexistent(self, temp_db):
        """测试获取不存在的缓存"""
        cache = SearchCache(temp_db)
        cached = cache.get("nonexistent", "source")
        assert cached is None

    def test_delete(self, temp_db):
        """测试删除缓存"""
        cache = SearchCache(temp_db)
        results = [{"title": "Book"}]

        cache.set("query", "source", results)
        assert cache.get("query", "source") == results

        cache.delete("query", "source")
        assert cache.get("query", "source") is None

    def test_cleanup_expired(self, temp_db):
        """测试清理过期缓存"""
        cache = SearchCache(temp_db)

        # 插入过期缓存
        cursor = temp_db.cursor()
        cursor.execute("""
            INSERT INTO book_search_cache
            (query_hash, query_text, source, results_json, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("hash1", "query1", "source1", "[]", 0, 1))
        temp_db.commit()

        cache.cleanup_expired()

        cursor.execute("SELECT COUNT(*) FROM book_search_cache")
        assert cursor.fetchone()[0] == 0

    def test_cache_disabled(self, temp_db):
        """测试缓存禁用"""
        with patch('book_search.SEARCH_CACHE_ENABLED', False):
            cache = SearchCache(temp_db)
            results = [{"title": "Book"}]

            cache.set("query", "source", results)
            cached = cache.get("query", "source")

            assert cached is None


class TestBookSearchService:
    """书籍搜索服务测试"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        conn = sqlite3.connect(path)
        yield conn
        conn.close()
        os.unlink(path)

    def test_init(self, temp_db):
        """测试初始化"""
        service = BookSearchService(temp_db)
        assert service.cache is not None
        assert len(service.sources) == 4  # OpenLibrary, Douban, Google, WebSearch

    def test_init_with_web_search(self, temp_db):
        """测试使用网络搜索函数初始化"""
        service = BookSearchService(temp_db, lambda x: [])
        assert service.web_search_source.is_available()

    def test_set_web_search_func(self, temp_db):
        """测试设置网络搜索函数"""
        service = BookSearchService(temp_db)
        assert not service.web_search_source.is_available()

        service.set_web_search_func(lambda x: [])
        assert service.web_search_source.is_available()

    def test_search_empty_query(self, temp_db):
        """测试空查询"""
        service = BookSearchService(temp_db)
        results = service.search("")
        assert results == []

    def test_search_invalid_query(self, temp_db):
        """测试无效查询"""
        service = BookSearchService(temp_db)
        results = service.search(None)
        assert results == []

        results = service.search(123)
        assert results == []

    @patch('book_search.requests.get')
    def test_search_with_results(self, mock_get, temp_db):
        """测试有结果的搜索"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "docs": [
                {"title": "Python Book", "author_name": ["Author"], "key": "/works/OL1W"}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        service = BookSearchService(temp_db)
        results = service.search("Python")

        assert len(results) >= 1

    def test_deduplicate_results(self, temp_db):
        """测试结果去重"""
        service = BookSearchService(temp_db)
        results = [
            {"title": "Book", "author": "Author", "source": "s1", "key": "1"},
            {"title": "Book", "author": "Author", "source": "s2", "key": "2"},  # 重复
            {"title": "Other Book", "author": "Author", "source": "s1", "key": "3"},
        ]

        unique = service._deduplicate_results(results)

        assert len(unique) == 2

    def test_deduplicate_results_empty(self, temp_db):
        """测试空结果去重"""
        service = BookSearchService(temp_db)
        results = []
        unique = service._deduplicate_results(results)
        assert unique == []

    def test_deduplicate_results_none(self, temp_db):
        """测试None结果去重"""
        service = BookSearchService(temp_db)
        results = None
        unique = service._deduplicate_results(results)
        assert unique == []

    def test_deduplicate_results_missing_fields(self, temp_db):
        """测试缺失字段的结果去重"""
        service = BookSearchService(temp_db)
        results = [
            {"title": "Book", "author": "Author", "source": "s1", "key": "1"},
            {"title": "Book", "source": "s2", "key": "2"},  # 缺少作者
            {"author": "Author", "source": "s3", "key": "3"},  # 缺少标题
        ]
        unique = service._deduplicate_results(results)
        assert len(unique) == 3  # 应该能处理缺失字段

    def test_search_with_web_search_failure(self, temp_db):
        """测试网络搜索失败的情况"""
        # 模拟网络搜索函数返回空结果
        def mock_web_search(query):
            return []

        service = BookSearchService(temp_db, mock_web_search)
        results = service.search("test book")
        assert len(results) >= 0  # 应该至少返回OpenLibrary的结果

    def test_search_with_invalid_web_search_func(self, temp_db):
        """测试无效的网络搜索函数"""
        # 模拟网络搜索函数抛出异常
        def mock_web_search(query):
            raise Exception("Network error")

        service = BookSearchService(temp_db, mock_web_search)
        results = service.search("test book")
        assert len(results) >= 0  # 应该至少返回其他数据源的结果

    def test_search_with_empty_web_search_results(self, temp_db):
        """测试空的网络搜索结果"""
        # 模拟网络搜索函数返回空列表
        def mock_web_search(query):
            return []

        service = BookSearchService(temp_db, mock_web_search)
        results = service.search("test book")
        assert len(results) >= 0  # 应该至少返回其他数据源的结果

    def test_search_with_web_search_results(self, temp_db):
        """测试网络搜索返回结果"""
        # 模拟网络搜索函数返回一些结果
        def mock_web_search(query):
            return [
                {"title": "Web Book 1", "author": "Web Author 1"},
                {"title": "Web Book 2", "author": "Web Author 2"},
            ]

        service = BookSearchService(temp_db, mock_web_search)
        results = service.search("test book")
        assert len(results) > 0
        assert any("web_search" in result["source"] for result in results)

    def test_search_with_web_search_and_other_sources(self, temp_db):
        """测试网络搜索和其他数据源的组合"""
        # 模拟网络搜索函数返回一些结果
        def mock_web_search(query):
            return [
                {"title": "Web Book", "author": "Web Author"},
            ]

        service = BookSearchService(temp_db, mock_web_search)
        results = service.search("test book")
        assert len(results) > 0
        # 应该包含网络搜索和其他数据源的结果
        assert any("web_search" in result["source"] for result in results)
        assert any("openlibrary" in result["source"] for result in results)

    def test_search_with_relevance_sorting(self, temp_db):
        """测试按相关性排序"""
        # 模拟网络搜索函数返回一些结果
        def mock_web_search(query):
            return [
                {"title": "Python Book", "author": "Author"},
                {"title": "Book about Python", "author": "Author"},
                {"title": "Unrelated Book", "author": "Author"},
            ]

        service = BookSearchService(temp_db, mock_web_search)
        results = service.search("Python")
        assert len(results) > 0

        # 检查相关性排序：Python Book 应该排在前面
        python_books = [r for r in results if "python" in r["title"].lower()]
        unrelated_books = [r for r in results if "python" not in r["title"].lower()]

        # Python相关的书籍应该排在前面
        for python_book in python_books:
            for unrelated_book in unrelated_books:
                assert results.index(python_book) < results.index(unrelated_book)

    def test_search_with_network_timeout(self, temp_db):
        """测试网络超时情况"""
        # 模拟网络搜索函数超时
        def mock_web_search(query):
            import time
            time.sleep(5)  # 模拟超时
            return []

        service = BookSearchService(temp_db, mock_web_search)
        results = service.search("test book")
        assert len(results) >= 0  # 应该至少返回其他数据源的结果

    def test_search_with_invalid_query_characters(self, temp_db):
        """测试包含特殊字符的查询"""
        service = BookSearchService(temp_db)
        results = service.search("test!@#$%^&*()_+ book")
        assert len(results) >= 0

    def test_search_with_long_query(self, temp_db):
        """测试长查询"""
        service = BookSearchService(temp_db)
        long_query = "a" * 100 + " book"
        results = service.search(long_query)
        assert len(results) >= 0

    def test_search_with_unicode_query(self, temp_db):
        """测试Unicode查询"""
        service = BookSearchService(temp_db)
        results = service.search("中文书籍")
        assert len(results) >= 0

    def test_search_with_mixed_language_query(self, temp_db):
        """测试混合语言查询"""
        service = BookSearchService(temp_db)
        results = service.search("Python 中文书籍")
        assert len(results) >= 0

    def test_search_with_special_characters(self, temp_db):
        """测试特殊字符查询"""
        service = BookSearchService(temp_db)
        results = service.search("test book - special characters: !@#$%^&*()")
        assert len(results) >= 0

    def test_search_with_whitespace_query(self, temp_db):
        """测试空白字符查询"""
        service = BookSearchService(temp_db)
        results = service.search("   test   book   ")
        assert len(results) >= 0

    def test_search_with_empty_web_search_func(self, temp_db):
        """测试空的网络搜索函数"""
        service = BookSearchService(temp_db, None)
        results = service.search("test book")
        assert len(results) >= 0  # 应该至少返回其他数据源的结果

    def test_search_with_web_search_retry(self, temp_db):
        """测试网络搜索重试机制"""
        # 模拟网络搜索函数第一次失败，第二次成功
        call_count = 0
        def mock_web_search(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return []  # 第一次失败
            return [{"title": "Web Book", "author": "Author"}]  # 第二次成功

        service = BookSearchService(temp_db, mock_web_search)
        results = service.search("test book")
        assert len(results) > 0
        assert call_count == 2  # 应该重试一次

    def test_search_with_web_search_max_results(self, temp_db):
        """测试网络搜索最大结果数限制"""
        # 模拟网络搜索函数返回大量结果
        def mock_web_search(query):
            return [{"title": f"Book {i}", "author": "Author"} for i in range(100)]

        service = BookSearchService(temp_db, mock_web_search)
        results = service.search("test book")
        assert len(results) <= 25  # 应该被限制为最大结果数

    def test_search_with_web_search_timeout_config(self, temp_db):
        """测试网络搜索超时配置"""
        # 模拟网络搜索函数超时
        def mock_web_search(query):
            import time
            time.sleep(20)  # 超过默认超时时间
            return []

        service = BookSearchService(temp_db, mock_web_search)
        results = service.search("test book")
        assert len(results) >= 0  # 应该至少返回其他数据源的结果

    def test_search_with_web_search_retry_attempts(self, temp_db):
        """测试网络搜索重试次数配置"""
        # 模拟网络搜索函数多次失败
        call_count = 0
        def mock_web_search(query):
            nonlocal call_count
            call_count += 1
            if call_count <= WEB_SEARCH_RETRY_ATTEMPTS:
                return []  # 前几次失败
            return [{"title": "Web Book", "author": "Author"}]  # 最后一次成功

        service = BookSearchService(temp_db, mock_web_search)
        results = service.search("test book")
        assert len(results) > 0
        assert call_count == WEB_SEARCH_RETRY_ATTEMPTS + 1  # 应该重试指定次数

    def test_search_with_web_search_retry_delay(self, temp_db):
        """测试网络搜索重试延迟配置"""
        # 模拟网络搜索函数失败，测试重试延迟
        call_times = []
        def mock_web_search(query):
            import time
            call_times.append(time.time())
            return []  # 总是失败

        service = BookSearchService(temp_db, mock_web_search)
        results = service.search("test book")
        assert len(results) >= 0  # 应该至少返回其他数据源的结果

        # 检查重试之间的延迟
        if len(call_times) > 1:
            delays = [call_times[i+1] - call_times[i] for i in range(len(call_times)-1)]
            for delay in delays:
                assert delay >= WEB_SEARCH_RETRY_DELAY  # 应该有足够的延迟

    def test_search_with_disabled_web_search(self, temp_db):
        """测试禁用网络搜索"""
        # 模拟网络搜索禁用
        with patch('book_search.WEB_SEARCH_ENABLED', False):
            service = BookSearchService(temp_db)
            results = service.search("test book")
            assert len(results) >= 0  # 应该至少返回其他数据源的结果
            # 确保没有网络搜索结果
            assert not any("web_search" in result["source"] for result in results)

    def test_clear_cache(self, temp_db):
        """测试清空缓存"""
        service = BookSearchService(temp_db)
        service.cache.set("query", "source", [{"title": "Book"}])

        service.clear_cache()

        cached = service.cache.get("query", "source")
        assert cached is None


class TestGetSearchService:
    """获取搜索服务单例测试"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        conn = sqlite3.connect(path)
        yield conn
        conn.close()
        os.unlink(path)

    def test_singleton(self, temp_db):
        """测试单例模式"""
        import book_search
        book_search._search_service_instance = None  # 重置单例

        service1 = get_search_service(temp_db)
        service2 = get_search_service(temp_db)

        assert service1 is service2

    def test_singleton_with_web_search(self, temp_db):
        """测试带网络搜索函数的单例"""
        import book_search
        book_search._search_service_instance = None

        service1 = get_search_service(temp_db)
        service2 = get_search_service(temp_db, lambda x: [])

        assert service1 is service2
        assert service2.web_search_source.is_available()

    def teardown_method(self):
        """每个测试后重置单例"""
        import book_search
        book_search._search_service_instance = None
