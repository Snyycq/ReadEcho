"""
ReadEcho Pro EPUB 电子书读取模块
支持 EPUB 文件的解析、元数据提取和内容获取
"""

import re
from pathlib import Path
from typing import Optional
from html.parser import HTMLParser

from config import LOGGER


class HTMLTextExtractor(HTMLParser):
    """从 HTML 中提取纯文本的解析器"""

    def __init__(self):
        super().__init__()
        self._result = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = False
        if tag in ("p", "br", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li"):
            self._result.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self._result.append(data)

    def get_text(self) -> str:
        text = "".join(self._result)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def html_to_text(html_content: str) -> str:
    """将 HTML 内容转换为纯文本"""
    if not html_content:
        return ""
    extractor = HTMLTextExtractor()
    try:
        extractor.feed(html_content)
        return extractor.get_text()
    except Exception as e:
        LOGGER.warning(f"HTML解析失败: {e}")
        return html_content


class EpubReader:
    """EPUB 电子书读取器"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.book = None
        self.toc = []
        self.metadata = {}
        self._content_cache = {}

    def load(self) -> bool:
        """加载 EPUB 文件"""
        try:
            import ebooklib
            from ebooklib import epub

            if not Path(self.file_path).exists():
                raise FileNotFoundError(f"EPUB文件不存在: {self.file_path}")

            self.book = epub.read_epub(self.file_path)
            self._extract_metadata()
            self._extract_toc()
            LOGGER.info(f"EPUB加载成功: {self.metadata.get('title', '未知')}")
            return True
        except ImportError:
            LOGGER.error("ebooklib未安装，请运行: pip install ebooklib")
            raise
        except Exception as e:
            LOGGER.error(f"EPUB加载失败: {e}")
            raise

    def _extract_metadata(self):
        """提取书籍元数据"""
        try:
            self.metadata = {
                "title": self._get_metadata_value("title"),
                "author": self._get_metadata_value("creator"),
                "description": self._get_metadata_value("description"),
                "language": self._get_metadata_value("language"),
                "publisher": self._get_metadata_value("publisher"),
                "date": self._get_metadata_value("date"),
                "identifier": self._get_metadata_value("identifier"),
            }
        except Exception as e:
            LOGGER.warning(f"元数据提取失败: {e}")

    def _get_metadata_value(self, name: str) -> str:
        """获取指定名称的元数据值"""
        try:
            values = self.book.get_metadata("DC", name)
            if values:
                value = values[0][0]
                if isinstance(value, bytes):
                    value = value.decode("utf-8", errors="ignore")
                return value.strip()
        except Exception:
            pass
        return ""

    def _extract_toc(self):
        """提取目录结构"""
        self.toc = []
        try:
            from ebooklib import epub

            toc_items = self.book.toc if hasattr(self.book, 'toc') else []
            for item in toc_items:
                if isinstance(item, epub.Link):
                    self.toc.append({
                        "title": item.title,
                        "href": item.href,
                        "level": 0,
                    })
                elif isinstance(item, tuple):
                    section, items = item
                    self.toc.append({
                        "title": section.title,
                        "href": section.href,
                        "level": 0,
                    })
                    for sub_item in items:
                        if isinstance(sub_item, epub.Link):
                            self.toc.append({
                                "title": sub_item.title,
                                "href": sub_item.href,
                                "level": 1,
                            })
        except Exception as e:
            LOGGER.warning(f"目录提取失败: {e}")

    def get_metadata(self) -> dict:
        """获取书籍元数据"""
        return self.metadata.copy()

    def get_toc(self) -> list:
        """获取目录结构"""
        return self.toc.copy()

    def get_chapter_content(self, href: str) -> str:
        """获取指定章节的纯文本内容"""
        if href in self._content_cache:
            return self._content_cache[href]

        try:
            from ebooklib import epub

            # 去除fragment identifier（如 #sigil_toc_id_1）
            clean_href = href.split("#")[0] if "#" in href else href

            for item in self.book.get_items():
                if item.get_name() == clean_href:
                    html_content = item.get_content().decode("utf-8", errors="ignore")
                    text = html_to_text(html_content)
                    self._content_cache[href] = text
                    return text

            LOGGER.warning(f"章节未找到: {href}")
            return ""
        except Exception as e:
            LOGGER.error(f"获取章节内容失败: {e}")
            return ""

    def get_full_text(self) -> str:
        """获取全书纯文本（用于 AI 总结）"""
        texts = []
        for chapter in self.toc:
            content = self.get_chapter_content(chapter["href"])
            if content:
                texts.append(content)
        return "\n\n".join(texts)

    def get_chapter_by_index(self, index: int) -> tuple:
        """根据索引获取章节内容

        Returns:
            (title, content) 元组
        """
        if 0 <= index < len(self.toc):
            chapter = self.toc[index]
            content = self.get_chapter_content(chapter["href"])
            return chapter["title"], content
        return "", ""
