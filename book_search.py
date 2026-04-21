"""
ReadEcho Pro 在线书籍搜索模块
支持多数据源搜索（OpenLibrary、豆瓣、Google Books）和本地缓存
"""

import json
import sqlite3
import time
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from urllib.parse import quote

import requests
from config import (
    LOGGER,
    DOUBAN_API_KEY,
    GOOGLE_BOOKS_API_KEY,
    SEARCH_CACHE_ENABLED,
    SEARCH_CACHE_TTL,
    SEARCH_TIMEOUT,
)


@dataclass
class BookSearchResult:
    """书籍搜索结果数据类"""
    source: str  # 数据源名称：openlibrary, douban, google_books, local
    title: str
    author: str
    external_id: str  # 外部ID（如OpenLibrary的key、豆瓣的id、Google Books的volumeId）
    metadata: Dict[str, Any]  # 额外元数据

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于JSON序列化"""
        return {
            "source": self.source,
            "title": self.title,
            "author": self.author,
            "key": self.external_id,
            "metadata": self.metadata,
        }


class SearchSource(ABC):
    """搜索数据源抽象基类"""

    def __init__(self, name: str):
        self.name = name
        self.enabled = True

    @abstractmethod
    def search(self, query: str, limit: int = 25) -> List[BookSearchResult]:
        """执行搜索，返回结果列表"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查数据源是否可用（如API密钥是否配置）"""
        pass


class OpenLibrarySource(SearchSource):
    """OpenLibrary数据源"""

    def __init__(self):
        super().__init__("openlibrary")
        self.base_url = "https://openlibrary.org/search.json"

    def is_available(self) -> bool:
        """OpenLibrary始终可用（无需API密钥）"""
        return True

    def search(self, query: str, limit: int = 25) -> List[BookSearchResult]:
        """搜索OpenLibrary"""
        try:
            # 尝试标题搜索
            params = {"title": query, "limit": limit}
            response = requests.get(self.base_url, params=params, timeout=SEARCH_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("docs", []):
                title = item.get("title") or item.get("title_suggest") or "Unknown"
                authors = item.get("author_name") or []
                author = ", ".join(authors) if authors else ""
                key = item.get("key", "")

                results.append(BookSearchResult(
                    source=self.name,
                    title=title,
                    author=author,
                    external_id=key,
                    metadata={
                        "publish_year": item.get("first_publish_year"),
                        "isbn": item.get("isbn", [])[:5],  # 最多取5个ISBN
                        "language": item.get("language", []),
                    }
                ))

            LOGGER.debug(f"OpenLibrary搜索完成: {query} -> {len(results)} 结果")
            return results

        except requests.exceptions.RequestException as e:
            LOGGER.warning(f"OpenLibrary搜索失败: {e}")
            return []
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            LOGGER.warning(f"OpenLibrary响应解析失败: {e}")
            return []


class DoubanSource(SearchSource):
    """豆瓣图书数据源"""

    def __init__(self):
        super().__init__("douban")
        self.base_url = "https://api.douban.com/v2/book/search"

    def is_available(self) -> bool:
        """检查豆瓣API密钥是否配置"""
        return bool(DOUBAN_API_KEY)

    def search(self, query: str, limit: int = 25) -> List[BookSearchResult]:
        """搜索豆瓣图书"""
        if not self.is_available():
            LOGGER.debug("豆瓣API密钥未配置，跳过搜索")
            return []

        try:
            params = {
                "q": query,
                "count": min(limit, 50),  # 豆瓣API最大50
                "apikey": DOUBAN_API_KEY,
            }

            headers = {
                "User-Agent": "ReadEcho Pro/1.0 (https://github.com/yourusername/readecho)"
            }

            response = requests.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=SEARCH_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("books", []):
                title = item.get("title", "Unknown")
                author = " / ".join(item.get("author", []))
                book_id = item.get("id", "")

                # 提取更多元数据
                metadata = {
                    "publisher": item.get("publisher"),
                    "pubdate": item.get("pubdate"),
                    "price": item.get("price"),
                    "isbn13": item.get("isbn13"),
                    "summary": item.get("summary", "")[:200],  # 截断摘要
                    "rating": item.get("rating", {}).get("average"),
                    "tags": item.get("tags", [])[:5],  # 最多5个标签
                }

                results.append(BookSearchResult(
                    source=self.name,
                    title=title,
                    author=author,
                    external_id=book_id,
                    metadata=metadata
                ))

            LOGGER.debug(f"豆瓣搜索完成: {query} -> {len(results)} 结果")
            return results

        except requests.exceptions.RequestException as e:
            LOGGER.warning(f"豆瓣搜索失败: {e}")
            return []
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            LOGGER.warning(f"豆瓣响应解析失败: {e}")
            return []


class GoogleBooksSource(SearchSource):
    """Google Books数据源"""

    def __init__(self):
        super().__init__("google_books")
        self.base_url = "https://www.googleapis.com/books/v1/volumes"

    def is_available(self) -> bool:
        """检查Google Books API密钥是否配置"""
        return bool(GOOGLE_BOOKS_API_KEY)

    def search(self, query: str, limit: int = 25) -> List[BookSearchResult]:
        """搜索Google Books"""
        if not self.is_available():
            LOGGER.debug("Google Books API密钥未配置，跳过搜索")
            return []

        try:
            params = {
                "q": query,
                "maxResults": min(limit, 40),  # Google Books API最大40
                "key": GOOGLE_BOOKS_API_KEY,
                "langRestrict": "zh,en",  # 限制中英文
            }

            response = requests.get(self.base_url, params=params, timeout=SEARCH_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("items", []):
                volume_info = item.get("volumeInfo", {})
                title = volume_info.get("title", "Unknown")
                authors = volume_info.get("authors", [])
                author = ", ".join(authors) if authors else ""
                book_id = item.get("id", "")

                # 提取更多元数据
                metadata = {
                    "publisher": volume_info.get("publisher"),
                    "publishedDate": volume_info.get("publishedDate"),
                    "description": volume_info.get("description", "")[:200],
                    "pageCount": volume_info.get("pageCount"),
                    "categories": volume_info.get("categories", [])[:3],
                    "averageRating": volume_info.get("averageRating"),
                    "ratingsCount": volume_info.get("ratingsCount"),
                    "language": volume_info.get("language"),
                }

                results.append(BookSearchResult(
                    source=self.name,
                    title=title,
                    author=author,
                    external_id=book_id,
                    metadata=metadata
                ))

            LOGGER.debug(f"Google Books搜索完成: {query} -> {len(results)} 结果")
            return results

        except requests.exceptions.RequestException as e:
            LOGGER.warning(f"Google Books搜索失败: {e}")
            return []
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            LOGGER.warning(f"Google Books响应解析失败: {e}")
            return []


class SearchCache:
    """搜索缓存管理器"""

    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection
        self._init_cache_table()

    def _init_cache_table(self):
        """初始化缓存表"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS book_search_cache (
                id INTEGER PRIMARY KEY,
                query_hash TEXT UNIQUE NOT NULL,
                query_text TEXT NOT NULL,
                source TEXT NOT NULL,
                results_json TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                UNIQUE(query_hash, source)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_hash ON book_search_cache(query_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON book_search_cache(expires_at)")
        self.conn.commit()

    def _get_query_hash(self, query: str, source: str) -> str:
        """生成查询哈希"""
        text = f"{query}:{source}".lower().strip()
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def get(self, query: str, source: str) -> Optional[List[Dict[str, Any]]]:
        """从缓存获取结果"""
        if not SEARCH_CACHE_ENABLED:
            return None

        query_hash = self._get_query_hash(query, source)
        current_time = int(time.time())

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT results_json FROM book_search_cache
            WHERE query_hash = ? AND expires_at > ?
        """, (query_hash, current_time))

        row = cursor.fetchone()
        if row:
            try:
                results = json.loads(row[0])
                LOGGER.debug(f"缓存命中: {query} [{source}]")
                return results
            except json.JSONDecodeError:
                LOGGER.warning(f"缓存数据解析失败: {query} [{source}]")
                self.delete(query, source)

        return None

    def set(self, query: str, source: str, results: List[Dict[str, Any]]):
        """设置缓存"""
        if not SEARCH_CACHE_ENABLED:
            return

        query_hash = self._get_query_hash(query, source)
        current_time = int(time.time())
        expires_at = current_time + SEARCH_CACHE_TTL

        try:
            results_json = json.dumps(results, ensure_ascii=False)

            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO book_search_cache
                (query_hash, query_text, source, results_json, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (query_hash, query, source, results_json, current_time, expires_at))

            self.conn.commit()
            LOGGER.debug(f"缓存设置: {query} [{source}] -> {len(results)} 结果")
        except (sqlite3.Error, json.JSONDecodeError) as e:
            LOGGER.warning(f"缓存设置失败: {e}")

    def delete(self, query: str, source: str):
        """删除缓存"""
        query_hash = self._get_query_hash(query, source)
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM book_search_cache WHERE query_hash = ?", (query_hash,))
        self.conn.commit()

    def cleanup_expired(self):
        """清理过期缓存"""
        current_time = int(time.time())
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM book_search_cache WHERE expires_at <= ?", (current_time,))
        deleted = cursor.rowcount
        self.conn.commit()

        if deleted > 0:
            LOGGER.debug(f"清理过期缓存: {deleted} 条记录")


class BookSearchService:
    """书籍搜索服务，管理多个数据源和缓存"""

    def __init__(self, db_connection: sqlite3.Connection):
        self.sources: List[SearchSource] = [
            OpenLibrarySource(),
            DoubanSource(),
            GoogleBooksSource(),
        ]
        self.cache = SearchCache(db_connection)

        # 启用可用的数据源
        self.available_sources = [source for source in self.sources if source.is_available()]
        LOGGER.info(f"书籍搜索服务初始化: {len(self.available_sources)}/{len(self.sources)} 个数据源可用")

    def search(self, query: str, limit_per_source: int = 10) -> List[Dict[str, Any]]:
        """多数据源搜索"""
        if not query or not isinstance(query, str):
            return []

        all_results = []

        for source in self.available_sources:
            source_name = source.name

            # 尝试从缓存获取
            cached_results = self.cache.get(query, source_name)
            if cached_results is not None:
                all_results.extend(cached_results)
                continue

            # 执行搜索
            try:
                results = source.search(query, limit_per_source)

                # 转换为字典并缓存
                result_dicts = [result.to_dict() for result in results]
                self.cache.set(query, source_name, result_dicts)

                all_results.extend(result_dicts)

            except Exception as e:
                LOGGER.error(f"数据源 {source_name} 搜索异常: {e}")
                continue

        # 清理过期缓存（偶尔执行）
        if time.time() % 100 < 1:  # 约1%的概率执行清理
            self.cache.cleanup_expired()

        # 去重（基于标题和作者）
        unique_results = self._deduplicate_results(all_results)

        # 按数据源优先级排序：豆瓣 > Google Books > OpenLibrary > local
        source_priority = {"douban": 0, "google_books": 1, "openlibrary": 2, "local": 3}
        unique_results.sort(key=lambda x: source_priority.get(x["source"], 99))

        LOGGER.info(f"搜索完成: '{query}' -> {len(unique_results)} 个结果")
        return unique_results

    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """结果去重"""
        seen = set()
        deduplicated = []

        for result in results:
            # 使用标题和作者作为去重键
            title = result["title"].lower().strip()
            author = result["author"].lower().strip() if result["author"] else ""
            key = f"{title}|{author}"

            if key not in seen:
                seen.add(key)
                deduplicated.append(result)

        return deduplicated

    def clear_cache(self):
        """清空所有缓存"""
        cursor = self.cache.conn.cursor()
        cursor.execute("DELETE FROM book_search_cache")
        self.cache.conn.commit()
        LOGGER.info("搜索缓存已清空")


# 全局搜索服务实例
_search_service_instance = None

def get_search_service(db_connection: sqlite3.Connection) -> BookSearchService:
    """获取搜索服务实例（单例模式）"""
    global _search_service_instance
    if _search_service_instance is None:
        _search_service_instance = BookSearchService(db_connection)
    return _search_service_instance