"""
ReadEcho Pro 数据库管理模块
处理所有数据库操作，包括书籍、笔记、录音和问答的CRUD操作
"""

import sqlite3
from config import DATABASE_FILE


class DBManager:
    """数据库管理器类，封装所有数据库操作"""

    def __init__(self):
        """初始化数据库连接并创建必要的表"""
        self.conn = sqlite3.connect(DATABASE_FILE)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        """创建所有必要的数据库表"""
        # 现有表格：笔记（总结、语音笔记）
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY,
                title TEXT,
                content TEXT,
                type TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 新表格：书籍
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY,
                title TEXT,
                author TEXT,
                added_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 新表格：录音历史（与书籍关联）
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS recordings (
                id INTEGER PRIMARY KEY,
                book_id INTEGER,
                file_path TEXT,
                transcribed_text TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(book_id) REFERENCES books(id)
            )
        ''')

        # 新表格：AI问答
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS qa (
                id INTEGER PRIMARY KEY,
                book_id INTEGER,
                question TEXT,
                answer TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(book_id) REFERENCES books(id)
            )
        ''')

        self.conn.commit()

    def add_note(self, title, content, note_type="Summary"):
        """添加笔记（总结或语音笔记）"""
        self.cursor.execute(
            "INSERT INTO notes (title, content, type) VALUES (?, ?, ?)",
            (title, content, note_type)
        )
        self.conn.commit()

    # 书籍相关方法

    def add_book(self, title, author=""):
        """添加新书籍到书架"""
        self.cursor.execute(
            "INSERT INTO books (title, author) VALUES (?, ?)",
            (title, author)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_books(self, search_query=""):
        """获取书籍列表，支持模糊搜索"""
        if search_query:
            self.cursor.execute(
                "SELECT id, title, author FROM books WHERE title LIKE ? OR author LIKE ? ORDER BY added_date DESC",
                (f"%{search_query}%", f"%{search_query}%")
            )
        else:
            self.cursor.execute(
                "SELECT id, title, author FROM books ORDER BY added_date DESC"
            )
        return self.cursor.fetchall()

    def get_book_by_title(self, title):
        """根据书名获取书籍ID"""
        self.cursor.execute(
            "SELECT id FROM books WHERE title = ?",
            (title,)
        )
        result = self.cursor.fetchone()
        return result[0] if result else None

    # 录音相关方法

    def add_recording(self, book_id, file_path, transcribed_text):
        """添加录音记录"""
        self.cursor.execute(
            "INSERT INTO recordings (book_id, file_path, transcribed_text) VALUES (?, ?, ?)",
            (book_id, file_path, transcribed_text)
        )
        self.conn.commit()

    def get_recordings_by_book(self, book_id):
        """获取指定书籍的所有录音记录"""
        self.cursor.execute(
            "SELECT id, file_path, transcribed_text, timestamp FROM recordings WHERE book_id = ? ORDER BY timestamp DESC",
            (book_id,)
        )
        return self.cursor.fetchall()

    # 问答相关方法

    def add_qa(self, book_id, question, answer):
        """添加问答记录"""
        self.cursor.execute(
            "INSERT INTO qa (book_id, question, answer) VALUES (?, ?, ?)",
            (book_id, question, answer)
        )
        self.conn.commit()

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def __del__(self):
        """析构函数，确保数据库连接被关闭"""
        self.close()