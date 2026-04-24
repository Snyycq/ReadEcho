"""
ReadEcho Pro 在线书籍搜索模块
支持多数据源搜索（OpenLibrary、豆瓣、Google Books、网络搜索）和本地缓存
"""

import json
import sqlite3
import time
import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Callable
from urllib.parse import quote

import requests
from config import (
    LOGGER,
    DOUBAN_API_KEY,
    GOOGLE_BOOKS_API_KEY,
    SEARCH_CACHE_ENABLED,
    SEARCH_CACHE_TTL,
    SEARCH_TIMEOUT,
    WEB_SEARCH_ENABLED,
    WEB_SEARCH_TIMEOUT,
    WEB_SEARCH_MAX_RESULTS,
    WEB_SEARCH_RETRY_ATTEMPTS,
    WEB_SEARCH_RETRY_DELAY,
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
    """OpenLibrary数据源（免费，无需API密钥）"""

    def __init__(self):
        super().__init__("openlibrary")
        self.base_url = "https://openlibrary.org/search.json"
        self.max_retries = 3
        self.retry_delay = 1.0

    def is_available(self) -> bool:
        """OpenLibrary始终可用（无需API密钥）"""
        return True

    def _search_with_retry(self, params: dict, limit: int) -> Optional[dict]:
        """带重试机制的搜索请求"""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    self.base_url,
                    params=params,
                    timeout=SEARCH_TIMEOUT,
                    headers={"User-Agent": "ReadEcho Pro/1.0"}
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.Timeout:
                last_error = "请求超时"
                LOGGER.warning(f"OpenLibrary请求超时，尝试 {attempt + 1}/{self.max_retries}")
            except requests.exceptions.ConnectionError as e:
                last_error = f"网络连接错误: {e}"
                LOGGER.warning(f"OpenLibrary连接错误，尝试 {attempt + 1}/{self.max_retries}")
            except requests.exceptions.RequestException as e:
                last_error = f"请求错误: {e}"
                LOGGER.warning(f"OpenLibrary请求失败: {e}")
                break  # 非4xx/5xx错误不重试
            except json.JSONDecodeError as e:
                last_error = f"JSON解析错误: {e}"
                LOGGER.warning(f"OpenLibrary响应解析失败: {e}")
                break

            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))

        LOGGER.error(f"OpenLibrary搜索最终失败: {last_error}")
        return None

    def search(self, query: str, limit: int = 25) -> List[BookSearchResult]:
        """搜索OpenLibrary，支持多种搜索策略"""
        results = []
        seen_keys = set()

        # 策略1: 标题搜索
        params = {"title": query, "limit": limit}
        data = self._search_with_retry(params, limit)
        if data:
            for item in data.get("docs", []):
                key = item.get("key", "")
                if key in seen_keys:
                    continue
                seen_keys.add(key)

                title = item.get("title") or item.get("title_suggest") or "Unknown"
                authors = item.get("author_name") or []
                author = ", ".join(authors) if authors else ""

                results.append(BookSearchResult(
                    source=self.name,
                    title=title,
                    author=author,
                    external_id=key,
                    metadata={
                        "publish_year": item.get("first_publish_year"),
                        "isbn": item.get("isbn", [])[:5],
                        "language": item.get("language", []),
                    }
                ))

        # 策略2: 如果标题搜索结果少，尝试通用搜索
        if len(results) < 5:
            params = {"q": query, "limit": limit}
            data = self._search_with_retry(params, limit)
            if data:
                for item in data.get("docs", []):
                    key = item.get("key", "")
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                    title = item.get("title") or "Unknown"
                    authors = item.get("author_name") or []
                    author = ", ".join(authors) if authors else ""

                    results.append(BookSearchResult(
                        source=self.name,
                        title=title,
                        author=author,
                        external_id=key,
                        metadata={
                            "publish_year": item.get("first_publish_year"),
                            "isbn": item.get("isbn", [])[:5],
                            "language": item.get("language", []),
                        }
                    ))

        LOGGER.debug(f"OpenLibrary搜索完成: {query} -> {len(results)} 结果")
        return results


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


class WebSearchSource(SearchSource):
    """网络搜索数据源（使用WebSearch工具搜索书籍信息）"""

    def __init__(self, web_search_func: Optional[Callable] = None):
        super().__init__("web_search")
        self.web_search_func = web_search_func
        self._available = True
        self.search_engines = [
            "https://www.bing.com/search?q={query}",
            "https://www.google.com/search?q={query}",
            "https://duckduckgo.com/?q={query}",
        ]

    def is_available(self) -> bool:
        """检查网络搜索是否可用"""
        return self._available and self.web_search_func is not None

    def set_search_func(self, search_func: Callable):
        """设置搜索函数"""
        self.web_search_func = search_func

    def search(self, query: str, limit: int = 25) -> List[BookSearchResult]:
        """通过网络搜索查找书籍信息"""
        if not self.is_available():
            LOGGER.debug("网络搜索不可用，跳过")
            return []

        try:
            # 构建搜索查询
            search_queries = [
                f'"{query}" book author',
                f'"{query}" 书籍 作者',
                f'"{query}" ebook pdf download',
                f'"{query}" 电子书 下载',
            ]

            LOGGER.debug(f"网络搜索: {search_queries}")

            # 调用搜索函数，尝试多个查询
            all_results = []
            for search_query in search_queries:
                results = self.web_search_func(search_query)
                if results:
                    all_results.extend(results)

            if not all_results:
                LOGGER.debug(f"网络搜索无结果: {query}")
                return []

            # 解析搜索结果，提取书籍信息
            book_results = []
            seen_titles = set()

            for result in all_results[:limit * 3]:  # 扩大搜索范围，然后去重
                title, author = self._parse_book_info(result, query)
                if title and title.lower() not in seen_titles:
                    seen_titles.add(title.lower())
                    book_results.append(BookSearchResult(
                        source=self.name,
                        title=title,
                        author=author,
                        external_id=f"web_{hashlib.md5(title.encode()).hexdigest()[:8]}",
                        metadata={
                            "search_result": result,
                            "source_type": "web_search",
                            "search_query": result.get("search_query", "") if isinstance(result, dict) else ""
                        }
                    ))

            # 按相关性排序（标题匹配度）
            book_results.sort(key=lambda x: self._calculate_relevance(x["title"], query), reverse=True)

            LOGGER.debug(f"网络搜索完成: {query} -> {len(book_results)} 结果")
            return book_results[:limit]  # 返回前limit个结果

        except Exception as e:
            LOGGER.warning(f"网络搜索失败: {e}")
            return []

    def _parse_book_info(self, result: Any, original_query: str) -> tuple:
        """从搜索结果中解析书籍标题和作者"""
        title = ""
        author = ""

        # 如果结果是字典格式
        if isinstance(result, dict):
            # 优先从标准字段获取
            title = result.get("title", "")
            if not title:
                title = result.get("name", "")
                if not title:
                    title = result.get("heading", "")

            # 尝试从URL或摘要中提取
            if not title:
                url = result.get("url", "")
                if url:
                    # 从URL提取标题
                    title = url.split('/')[-1].replace('.html', '').replace('.htm', '').replace('.php', '')

            # 尝试提取作者
            snippet = result.get("snippet", "") or result.get("description", "")
            author = self._extract_author(snippet, original_query)

            # 如果仍然没有作者，尝试从其他字段获取
            if not author:
                author = result.get("author", "")
                if not author:
                    author = result.get("creator", "")

        # 如果结果是字符串格式
        elif isinstance(result, str):
            # 尝试从字符串中提取标题和作者
            lines = result.split('\n')
            for line in lines:
                line = line.strip()
                if line and not title:
                    # 第一行可能是标题
                    if original_query.lower() in line.lower():
                        title = line.split('-')[0].strip() if '-' in line else line
                    elif len(line) > 3:
                        title = line
                        break

            author = self._extract_author(result, original_query)

        # 如果标题中包含原始查询，优先使用
        if original_query and original_query.lower() in title.lower():
            pass  # 保持原标题
        elif not title:
            title = original_query

        # 清理标题和作者
        title = title[:200].strip()
        author = author[:100].strip()

        return title, author

    def _extract_author(self, text: str, book_title: str) -> str:
        """从文本中提取作者名"""
        if not text:
            return ""

        # 常见的作者模式（中英文）
        patterns = [
            r'[作著]者[：:]\s*([^\n,，]+)',
            r'[Bb]y\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'作者\s*[:：]?\s*([^\n,，]+)',
            r'([^\n,，]+)\s*[著写编]',
            r'Author:\s*([^\n,，]+)',
            r'作者：\s*([^\n,，]+)',
            r'作者\s*[:：]\s*([^\n,，]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                author = match.group(1).strip()
                # 清理作者名
                author = re.sub(r'[《》【】\[\]]', '', author)
                if author and author.lower() not in book_title.lower():
                    return author

        return ""

    def _calculate_relevance(self, title: str, query: str) -> float:
        """计算标题与查询的相关性分数"""
        if not title or not query:
            return 0.0

        title_lower = title.lower()
        query_lower = query.lower()

        # 完全匹配
        if title_lower == query_lower:
            return 1.0

        # 包含查询
        if query_lower in title_lower:
            return 0.8

        # 部分匹配
        words = query_lower.split()
        match_count = sum(1 for word in words if word in title_lower)
        return match_count / len(words) if words else 0.0


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

    def __init__(self, db_connection: sqlite3.Connection, web_search_func: Optional[Callable] = None):
        self.web_search_source = WebSearchSource(web_search_func)
        self.sources: List[SearchSource] = [
            OpenLibrarySource(),
            DoubanSource(),
            GoogleBooksSource(),
            self.web_search_source,  # 网络搜索作为后备
        ]
        self.cache = SearchCache(db_connection)

        # 启用可用的数据源
        self.available_sources = [source for source in self.sources if source.is_available()]

        # 如果网络搜索启用但不可用，记录警告
        if WEB_SEARCH_ENABLED and not self.web_search_source.is_available():
            LOGGER.warning("网络搜索已启用但不可用，请配置网络搜索函数")

        LOGGER.info(f"书籍搜索服务初始化: {len(self.available_sources)}/{len(self.sources)} 个数据源可用")

    def set_web_search_func(self, search_func: Callable):
        """设置网络搜索函数"""
        self.web_search_source.set_search_func(search_func)
        self.web_search_source._available = True
        if self.web_search_source not in self.available_sources:
            self.available_sources.append(self.web_search_source)
        LOGGER.info("网络搜索功能已启用")

    def search(self, query: str, limit_per_source: int = 10) -> List[Dict[str, Any]]:
        """多数据源搜索"""
        if not query or not isinstance(query, str):
            return []

        all_results = []
        failed_sources = []

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

                # 如果有足够结果，可以提前返回
                if len(all_results) >= limit_per_source * 2:
                    break

            except Exception as e:
                LOGGER.error(f"数据源 {source_name} 搜索异常: {e}")
                failed_sources.append(source_name)
                continue

        # 清理过期缓存（偶尔执行）
        if time.time() % 100 < 1:  # 约1%的概率执行清理
            self.cache.cleanup_expired()

        # 去重（基于标题和作者）
        unique_results = self._deduplicate_results(all_results)

        # 按相关性排序：优先显示最相关的结果
        unique_results.sort(key=lambda x: self._calculate_result_relevance(x, query), reverse=True)

        # 记录搜索统计
        if failed_sources:
            LOGGER.warning(f"搜索完成，部分数据源失败: {failed_sources}")
        LOGGER.info(f"搜索完成: '{query}' -> {len(unique_results)} 个结果")
        return unique_results

    def _calculate_result_relevance(self, result: Dict[str, Any], query: str) -> float:
        """计算结果与查询的相关性分数"""
        title = result.get("title", "").lower()
        author = result.get("author", "").lower()
        query_lower = query.lower()

        # 完全匹配
        if title == query_lower or author == query_lower:
            return 1.0

        # 包含查询
        if query_lower in title or query_lower in author:
            return 0.9

        # 部分匹配
        words = query_lower.split()
        title_match = sum(1 for word in words if word in title)
        author_match = sum(1 for word in words if word in author)

        # 综合评分
        relevance = (title_match + author_match) / (len(words) * 2) if words else 0.0

        # 数据源优先级调整
        source_priority = {
            "douban": 0.2,
            "google_books": 0.15,
            "openlibrary": 0.1,
            "web_search": 0.05,
            "local": 0.0
        }

        return relevance + source_priority.get(result["source"], 0.0)

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


def get_search_service(
    db_connection: sqlite3.Connection,
    web_search_func: Optional[Callable] = None
) -> BookSearchService:
    """获取搜索服务实例（单例模式）

    Args:
        db_connection: 数据库连接
        web_search_func: 可选的网络搜索函数，用于在网络搜索数据源中搜索书籍

    Returns:
        BookSearchService: 搜索服务实例
    """
    global _search_service_instance
    if _search_service_instance is None:
        _search_service_instance = BookSearchService(db_connection, web_search_func)
    elif web_search_func is not None:
        # 更新网络搜索函数
        _search_service_instance.set_web_search_func(web_search_func)
    return _search_service_instance