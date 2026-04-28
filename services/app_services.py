"""
ReadEcho Pro 应用服务模块
整合所有业务逻辑服务，提供统一的接口
"""

from config import SAMPLE_RATE, TEMP_AUDIO_FILE, LOGGER
from core.database_manager import DBManager
from services.ai_processor import AIService
from services.recording_manager import RecordingService
from services import book_search


class AppServices:
    """应用服务管理器，整合所有业务逻辑服务"""

    def __init__(self, db_path=None):
        """初始化所有服务"""
        try:
            self.db = DBManager(database_file=db_path)
            self.ai_service = AIService()
            self.recording_service = RecordingService()
            self.current_book_id = None
            self.current_book_title = ""
            self.stt_model = None  # Whisper模型，由AI服务管理
            self.dark_mode = True  # 默认深色模式

            # 初始化书籍搜索服务
            self.search_service = book_search.get_search_service(self.db.conn)

            LOGGER.info("应用服务初始化成功")
        except Exception as e:
            LOGGER.error(f"应用服务初始化失败: {e}", exc_info=True)
            raise

    # --- 数据库服务封装 ---

    def add_book(self, title: str, author: str = "") -> int:
        """
        添加新书籍

        Args:
            title: 书籍标题
            author: 作者名称

        Returns:
            新书籍的ID
        """
        try:
            book_id = self.db.add_book(title, author)
            self.current_book_id = book_id
            self.current_book_title = title
            return book_id
        except Exception as e:
            LOGGER.error(f"添加书籍失败: {e}")
            raise

    def import_epub(self, file_path: str) -> int:
        """导入 EPUB 书籍

        Args:
            file_path: EPUB 文件路径

        Returns:
            新书籍的ID
        """
        try:
            from core.epub_reader import EpubReader
            import json

            reader = EpubReader(file_path)
            reader.load()

            metadata = reader.get_metadata()
            toc = reader.get_toc()

            title = metadata.get("title", "未知标题")
            author = metadata.get("author", "")
            description = metadata.get("description", "")
            toc_json = json.dumps(toc, ensure_ascii=False) if toc else None

            book_id = self.db.add_book(
                title=title,
                author=author,
                book_type="epub",
                file_path=file_path,
                description=description,
                toc_json=toc_json,
            )

            self.current_book_id = book_id
            self.current_book_title = title
            LOGGER.info(f"EPUB导入成功: {title} (ID: {book_id})")
            return book_id
        except Exception as e:
            LOGGER.error(f"EPUB导入失败: {e}")
            raise

    def get_book_detail(self, book_id: int):
        """获取书籍详细信息

        Args:
            book_id: 书籍ID

        Returns:
            书籍信息字典
        """
        try:
            return self.db.get_book_by_id(book_id)
        except Exception as e:
            LOGGER.error(f"获取书籍详情失败: {e}")
            return None

    def get_book_toc(self, book_id: int) -> list:
        """获取书籍目录

        Args:
            book_id: 书籍ID

        Returns:
            目录列表
        """
        try:
            import json
            book = self.db.get_book_by_id(book_id)
            if book and book.get("toc_json"):
                return json.loads(book["toc_json"])
            return []
        except Exception as e:
            LOGGER.error(f"获取书籍目录失败: {e}")
            return []

    def get_chapter_content(self, book_id: int, chapter_href: str) -> str:
        """获取章节内容

        Args:
            book_id: 书籍ID
            chapter_href: 章节路径

        Returns:
            章节纯文本内容
        """
        try:
            from core.epub_reader import EpubReader

            book = self.db.get_book_by_id(book_id)
            if not book or not book.get("file_path"):
                return ""

            reader = EpubReader(book["file_path"])
            reader.load()
            return reader.get_chapter_content(chapter_href)
        except Exception as e:
            LOGGER.error(f"获取章节内容失败: {e}")
            return ""

    def get_book_full_text(self, book_id: int) -> str:
        """获取书籍全文（用于 AI 总结）

        Args:
            book_id: 书籍ID

        Returns:
            全书纯文本
        """
        try:
            import os
            from core.epub_reader import EpubReader

            book = self.db.get_book_by_id(book_id)
            if not book:
                LOGGER.error(f"[DEBUG] 书籍不存在: book_id={book_id}")
                return ""

            file_path = book.get("file_path")
            LOGGER.debug(f"[DEBUG] 书籍文件路径: {file_path}")

            if not file_path:
                LOGGER.error(f"[DEBUG] 书籍没有文件路径: book_id={book_id}")
                return ""

            if not os.path.exists(file_path):
                LOGGER.error(f"[DEBUG] EPUB 文件不存在: {file_path}")
                return ""

            LOGGER.debug(f"[DEBUG] EPUB 文件大小: {os.path.getsize(file_path)} bytes")

            reader = EpubReader(file_path)
            reader.load()
            full_text = reader.get_full_text()
            LOGGER.debug(f"[DEBUG] 获取全文长度: {len(full_text)} 字符")
            return full_text
        except Exception as e:
            LOGGER.error(f"[DEBUG] 获取书籍全文失败: {e}", exc_info=True)
            return ""

    def get_books(self, search_query: str = "", limit: int = 50, offset: int = 0):
        """获取书籍列表"""
        try:
            return self.db.get_books(search_query, limit, offset)
        except Exception as e:
            LOGGER.error(f"获取书籍列表失败: {e}")
            return []

    def get_books_count(self, search_query: str = "") -> int:
        """获取书籍总数"""
        try:
            return self.db.get_books_count(search_query)
        except Exception as e:
            LOGGER.error(f"获取书籍计数失败: {e}")
            return 0

    def get_book_by_title(self, title: str):
        """根据书名获取书籍ID"""
        try:
            return self.db.get_book_by_title(title)
        except Exception as e:
            LOGGER.error(f"查询书籍失败: {e}")
            return None

    def search_online_books(self, query: str, limit: int = 25):
        """多数据源在线搜索图书"""
        try:
            if not query or not isinstance(query, str):
                return []

            # 使用新的搜索服务
            online_results = self.search_service.search(query, limit_per_source=limit // 3 + 1)

            # 如果在线搜索结果不足，补充本地书籍
            if len(online_results) < limit // 2:
                local_books = self.db.get_books(query, limit - len(online_results))
                for book_id, title, author in local_books:
                    online_results.append({
                        "source": "local",
                        "book_id": book_id,
                        "title": title,
                        "author": author,
                        "key": "",  # 本地书籍没有外部ID
                        "metadata": {}
                    })

            # 限制返回数量
            return online_results[:limit]

        except Exception as e:
            LOGGER.warning(f"在线搜索图书失败，回退到本地匹配: {e}")
            # 失败时回退到本地搜索
            local_books = self.db.get_books(query, limit)
            results = []
            for book_id, title, author in local_books:
                results.append(
                    {
                        "source": "local",
                        "book_id": book_id,
                        "title": title,
                        "author": author,
                        "key": "",
                        "metadata": {}
                    }
                )
            return results

    def add_note(self, title: str, content: str, note_type: str = "Summary"):
        """添加笔记"""
        try:
            self.db.add_note(title, content, note_type)
        except Exception as e:
            LOGGER.error(f"添加笔记失败: {e}")
            raise

    def add_recording(self, book_id: int, file_path: str, transcribed_text: str):
        """添加录音记录"""
        try:
            self.db.add_recording(book_id, file_path, transcribed_text)
        except Exception as e:
            LOGGER.error(f"添加录音记录失败: {e}")
            raise

    def get_recordings_by_book(self, book_id: int):
        """获取指定书籍的录音记录"""
        try:
            return self.db.get_recordings_by_book(book_id)
        except Exception as e:
            LOGGER.error(f"获取录音记录失败: {e}")
            return []

    def get_recording_by_id(self, recording_id: int):
        """根据录音ID获取录音记录"""
        try:
            return self.db.get_recording_by_id(recording_id)
        except Exception as e:
            LOGGER.error(f"查询录音记录失败: {e}")
            return None

    def update_recording_text(self, recording_id: int, transcribed_text: str):
        """更新录音转录文本"""
        try:
            self.db.update_recording(recording_id, transcribed_text)
        except Exception as e:
            LOGGER.error(f"更新录音记录失败: {e}")
            raise

    def delete_recording(self, recording_id: int):
        """删除指定录音记录"""
        try:
            self.db.delete_recording(recording_id)
        except Exception as e:
            LOGGER.error(f"删除录音记录失败: {e}")
            raise

    def delete_book(self, book_id: int):
        """删除指定书籍及其关联数据"""
        try:
            self.db.delete_book(book_id)
            if self.current_book_id == book_id:
                self.clear_current_book()
        except Exception as e:
            LOGGER.error(f"删除书籍失败: {e}")
            raise

    def add_qa(self, book_id: int, question: str, answer: str):
        """添加问答记录"""
        try:
            self.db.add_qa(book_id, question, answer)
        except Exception as e:
            LOGGER.error(f"添加问答记录失败: {e}")
            raise

    def get_qa_by_book(self, book_id: int, limit: int = 50, offset: int = 0):
        """获取问答记录"""
        try:
            return self.db.get_qa_by_book(book_id, limit, offset)
        except Exception as e:
            LOGGER.error(f"获取问答记录失败: {e}")
            return []

    # --- AI服务封装 ---

    def load_whisper_model(self, callback):
        """加载Whisper模型"""
        self.ai_service.load_whisper_model(callback)

    def create_summary_thread(self, book_title, callback):
        """创建总结生成线程"""
        return self.ai_service.create_summary_thread(book_title, callback)

    def create_transcription_thread(self, audio_path, book_title, callback):
        """创建音频转录线程"""
        return self.ai_service.create_transcription_thread(audio_path, book_title, callback)

    def create_qa_thread(self, question, book_title, callback, model=None):
        """创建问答线程"""
        return self.ai_service.create_qa_thread(question, book_title, callback, model)

    def set_stt_model(self, model):
        """设置Whisper模型"""
        self.ai_service.set_stt_model(model)
        self.stt_model = model

    def get_stt_model(self):
        """获取Whisper模型"""
        return self.ai_service.stt_model

    # --- 录音服务封装 ---

    def start_recording(self):
        """开始录音"""
        return self.recording_service.start_recording()

    def stop_recording(self):
        """停止录音并返回录音完成线程"""
        return self.recording_service.stop_recording()

    def get_recording_status(self):
        """获取录音状态"""
        return self.recording_service.get_recording_status()

    def cleanup_recording(self):
        """清理录音资源"""
        self.recording_service.cleanup()

    def get_recording_data(self):
        """获取录音数据（临时方法，待重构）"""
        # 注意：这直接访问内部属性，需要更好的封装
        return self.recording_service.recording_data

    # --- 当前书籍管理 ---

    def set_current_book(self, book_id, title):
        """设置当前选中的书籍"""
        self.current_book_id = book_id
        self.current_book_title = title

    def get_current_book(self):
        """获取当前选中的书籍信息"""
        return {"id": self.current_book_id, "title": self.current_book_title}

    def clear_current_book(self):
        """清除当前选中的书籍"""
        self.current_book_id = None
        self.current_book_title = ""

    # --- 主题管理 ---

    def toggle_theme(self):
        """切换主题模式（深色/浅色）"""
        self.dark_mode = not self.dark_mode
        LOGGER.info(f"主题已切换: {'深色' if self.dark_mode else '浅色'}模式")
        return self.dark_mode

    def get_theme_mode(self):
        """获取当前主题模式"""
        return self.dark_mode

    # --- 实用方法 ---

    def get_sample_rate(self):
        """获取采样率"""
        return SAMPLE_RATE

    def get_temp_audio_file(self):
        """获取临时音频文件路径"""
        return TEMP_AUDIO_FILE

    def close(self) -> None:
        """关闭所有服务，释放资源"""
        try:
            LOGGER.info("应用服务关闭中...")

            # 关闭数据库连接
            if hasattr(self.db, "close"):
                self.db.close()

            # 清理录音资源
            self.cleanup_recording()

            LOGGER.info("应用服务已安全关闭")
        except Exception as e:
            LOGGER.error(f"关闭应用服务时出错: {e}")

    def cleanup(self) -> None:
        """清理资源（close的别名，用于向上兼容）"""
        self.close()

    def __del__(self):
        """析构函数，确保资源被释放"""
        self.close()


# 服务工厂函数
def create_app_services():
    """创建应用服务实例"""
    return AppServices()
