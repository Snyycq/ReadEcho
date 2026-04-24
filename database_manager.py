"""
ReadEcho Pro 数据库管理模块
处理所有数据库操作，包括书籍、笔记、录音和问答的CRUD操作
"""

import sqlite3
from config import LOGGER
from validators import InputValidator


class DBManager:
    """数据库管理器类，封装所有数据库操作"""

    def __init__(self, database_file=None):
        """初始化数据库连接并创建必要的表"""
        try:
            if database_file is None:
                from config import DATABASE_FILE

                database_file = DATABASE_FILE

            self.database_file = database_file
            self.conn = sqlite3.connect(self.database_file, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self._create_tables()
            LOGGER.info(f"数据库初始化成功: {self.database_file}")
        except sqlite3.Error as e:
            LOGGER.error(f"数据库初始化失败: {e}")
            raise

    def _create_tables(self):
        """创建所有必要的数据库表"""
        try:
            # 现有表格：笔记（总结、语音笔记）
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    content TEXT,
                    type TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 新表格：书籍
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    author TEXT,
                    added_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 新表格：录音历史（与书籍关联）
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS recordings (
                    id INTEGER PRIMARY KEY,
                    book_id INTEGER,
                    file_path TEXT,
                    transcribed_text TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(book_id) REFERENCES books(id)
                )
            """)

            # 新表格：AI问答
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS qa (
                    id INTEGER PRIMARY KEY,
                    book_id INTEGER,
                    question TEXT,
                    answer TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(book_id) REFERENCES books(id)
                )
            """)

            # 创建索引以优化查询性能
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_books_title ON books(title)")
            self.cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_recordings_book_id ON recordings(book_id)"
            )
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_qa_book_id ON qa(book_id)")

            self.conn.commit()
            LOGGER.debug("数据库表创建成功")
        except sqlite3.Error as e:
            LOGGER.error(f"创建数据库表失败: {e}")
            raise

    def add_note(self, title, content, note_type="Summary"):
        """添加笔记（总结或语音笔记）"""
        try:
            title = InputValidator.validate_book_title(title, max_length=100)
            if not content or not isinstance(content, str):
                raise ValueError("内容不能为空")

            self.cursor.execute(
                "INSERT INTO notes (title, content, type) VALUES (?, ?, ?)",
                (title, content, note_type),
            )
            self.conn.commit()
            LOGGER.info(f"添加笔记成功: {title} ({note_type})")
        except (ValueError, sqlite3.Error) as e:
            LOGGER.error(f"添加笔记失败: {e}")
            self.conn.rollback()
            raise

    # 书籍相关方法

    def add_book(self, title, author=""):
        """添加新书籍到书架

        Args:
            title: 书籍标题
            author: 作者名称（可选）

        Returns:
            新添加书籍的ID

        Raises:
            ValueError: 如果输入无效
            sqlite3.Error: 如果数据库操作失败
        """
        try:
            title = InputValidator.validate_book_title(title)
            author = InputValidator.validate_author_name(author)

            self.cursor.execute("INSERT INTO books (title, author) VALUES (?, ?)", (title, author))
            self.conn.commit()
            book_id = self.cursor.lastrowid
            LOGGER.info(f"添加书籍成功: {title} (ID: {book_id})")
            return book_id
        except (ValueError, sqlite3.Error) as e:
            LOGGER.error(f"添加书籍失败: {e}")
            self.conn.rollback()
            raise

    def get_books(self, search_query="", limit=50, offset=0):
        """获取书籍列表，支持模糊搜索和分页

        Args:
            search_query: 搜索关键词
            limit: 返回的最大结果数
            offset: 分页偏移量

        Returns:
            书籍列表 [(id, title, author), ...]
        """
        try:
            if search_query:
                search_query = search_query.strip()
                self.cursor.execute(
                    """SELECT id, title, author FROM books
                       WHERE title LIKE ? OR author LIKE ?
                       ORDER BY added_date DESC
                       LIMIT ? OFFSET ?""",
                    (f"%{search_query}%", f"%{search_query}%", limit, offset),
                )
            else:
                self.cursor.execute(
                    """SELECT id, title, author FROM books
                       ORDER BY added_date DESC
                       LIMIT ? OFFSET ?""",
                    (limit, offset),
                )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            LOGGER.error(f"获取书籍列表失败: {e}")
            return []

    def get_books_count(self, search_query=""):
        """获取书籍总数（用于分页）

        Args:
            search_query: 搜索关键词

        Returns:
            书籍总数
        """
        try:
            if search_query:
                search_query = search_query.strip()
                self.cursor.execute(
                    "SELECT COUNT(*) FROM books WHERE title LIKE ? OR author LIKE ?",
                    (f"%{search_query}%", f"%{search_query}%"),
                )
            else:
                self.cursor.execute("SELECT COUNT(*) FROM books")
            return self.cursor.fetchone()[0]
        except sqlite3.Error as e:
            LOGGER.error(f"获取书籍计数失败: {e}")
            return 0

    def get_book_by_title(self, title):
        """根据书名获取书籍ID

        Args:
            title: 书籍标题

        Returns:
            书籍ID，不存在则返回None
        """
        try:
            title = InputValidator.validate_book_title(title)
            self.cursor.execute("SELECT id FROM books WHERE title = ?", (title,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except (ValueError, sqlite3.Error) as e:
            LOGGER.error(f"查询书籍ID失败: {e}")
            return None

    def get_recording_by_id(self, recording_id):
        """根据录音ID获取录音记录"""
        try:
            if not isinstance(recording_id, int) or recording_id <= 0:
                raise ValueError("无效的录音ID")

            self.cursor.execute(
                "SELECT id, book_id, file_path, transcribed_text, timestamp "
                "FROM recordings WHERE id = ?",
                (recording_id,),
            )
            return self.cursor.fetchone()
        except (ValueError, sqlite3.Error) as e:
            LOGGER.error(f"查询录音记录失败: {e}")
            return None

    def update_recording(self, recording_id, transcribed_text):
        """更新录音转录文本"""
        try:
            if not isinstance(recording_id, int) or recording_id <= 0:
                raise ValueError("无效的录音ID")
            if not isinstance(transcribed_text, str) or not transcribed_text.strip():
                raise ValueError("转录文本不能为空")

            self.cursor.execute(
                "UPDATE recordings SET transcribed_text = ? WHERE id = ?",
                (transcribed_text.strip(), recording_id),
            )
            self.conn.commit()
            LOGGER.info(f"录音记录已更新: {recording_id}")
        except (ValueError, sqlite3.Error) as e:
            LOGGER.error(f"更新录音记录失败: {e}")
            self.conn.rollback()
            raise

    def delete_recording(self, recording_id):
        """删除录音记录"""
        try:
            if not isinstance(recording_id, int) or recording_id <= 0:
                raise ValueError("无效的录音ID")

            self.cursor.execute("DELETE FROM recordings WHERE id = ?", (recording_id,))
            self.conn.commit()
            LOGGER.info(f"录音记录已删除: {recording_id}")
        except (ValueError, sqlite3.Error) as e:
            LOGGER.error(f"删除录音失败: {e}")
            self.conn.rollback()
            raise

    def delete_book(self, book_id):
        """删除书籍及其关联数据"""
        try:
            if not isinstance(book_id, int) or book_id <= 0:
                raise ValueError("无效的书籍ID")

            self.cursor.execute("DELETE FROM qa WHERE book_id = ?", (book_id,))
            self.cursor.execute("DELETE FROM recordings WHERE book_id = ?", (book_id,))
            self.cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
            self.conn.commit()
            LOGGER.info(f"书籍及其关联数据已删除: {book_id}")
        except (ValueError, sqlite3.Error) as e:
            LOGGER.error(f"删除书籍失败: {e}")
            self.conn.rollback()
            raise

    # 录音相关方法

    def add_recording(self, book_id, file_path, transcribed_text):
        """添加录音记录

        Args:
            book_id: 书籍ID
            file_path: 录音文件路径（或手动笔记标识符）
            transcribed_text: 转录文本

        Raises:
            ValueError: 如果输入无效
            sqlite3.Error: 如果数据库操作失败
        """
        try:
            if not isinstance(book_id, int) or book_id <= 0:
                raise ValueError("无效的书籍ID")

            # 手动笔记（以 "manual_note_" 开头）不需要音频文件验证
            if not file_path.startswith("manual_note_"):
                file_path = InputValidator.validate_audio_file(file_path)

            if not isinstance(transcribed_text, str):
                raise ValueError("转录文本必须是字符串")

            self.cursor.execute(
                "INSERT INTO recordings (book_id, file_path, transcribed_text) VALUES (?, ?, ?)",
                (book_id, file_path, transcribed_text),
            )
            self.conn.commit()
            LOGGER.info(f"添加录音成功: 书籍ID={book_id}")
        except (ValueError, sqlite3.Error) as e:
            LOGGER.error(f"添加录音失败: {e}")
            self.conn.rollback()
            raise

    def get_recordings_by_book(self, book_id):
        """获取指定书籍的所有录音记录

        Args:
            book_id: 书籍ID

        Returns:
            录音列表 [(id, file_path, transcribed_text, timestamp), ...]
        """
        try:
            if not isinstance(book_id, int) or book_id <= 0:
                raise ValueError("无效的书籍ID")

            self.cursor.execute(
                """SELECT id, file_path, transcribed_text, timestamp
                   FROM recordings WHERE book_id = ?
                   ORDER BY id DESC""",
                (book_id,),
            )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            LOGGER.error(f"获取录音列表失败: {e}")
            return []

    # 问答相关方法

    def add_qa(self, book_id, question, answer):
        """添加问答记录

        Args:
            book_id: 书籍ID
            question: 问题
            answer: 答案

        Raises:
            ValueError: 如果输入无效
            sqlite3.Error: 如果数据库操作失败
        """
        try:
            if not isinstance(book_id, int) or book_id <= 0:
                raise ValueError("无效的书籍ID")

            question = InputValidator.validate_question(question)

            if not answer or not isinstance(answer, str):
                raise ValueError("答案不能为空")

            self.cursor.execute(
                "INSERT INTO qa (book_id, question, answer) VALUES (?, ?, ?)",
                (book_id, question, answer),
            )
            self.conn.commit()
            LOGGER.info(f"添加问答记录成功: 书籍ID={book_id}")
        except (ValueError, sqlite3.Error) as e:
            LOGGER.error(f"添加问答记录失败: {e}")
            self.conn.rollback()
            raise

    def get_qa_by_book(self, book_id, limit=50, offset=0):
        """获取指定书籍的问答记录

        Args:
            book_id: 书籍ID
            limit: 返回的最大结果数
            offset: 分页偏移量

        Returns:
            问答列表 [(id, question, answer, timestamp), ...]
        """
        try:
            if not isinstance(book_id, int) or book_id <= 0:
                raise ValueError("无效的书籍ID")

            self.cursor.execute(
                """SELECT id, question, answer, timestamp
                   FROM qa WHERE book_id = ?
                   ORDER BY id DESC
                   LIMIT ? OFFSET ?""",
                (book_id, limit, offset),
            )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            LOGGER.error(f"获取问答列表失败: {e}")
            return []

    def close(self):
        """关闭数据库连接"""
        try:
            if self.conn:
                self.conn.close()
                self.conn = None
                LOGGER.info("数据库连接已关闭")
        except sqlite3.Error as e:
            LOGGER.error(f"关闭数据库连接失败: {e}")

    def __del__(self):
        """析构函数，确保数据库连接被关闭"""
        self.close()
