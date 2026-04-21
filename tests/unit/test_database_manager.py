"""
database_manager.py 单元测试
测试数据库管理功能
"""

import pytest
import sys
import os
import sqlite3

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database_manager import DBManager  # noqa: E402


class TestDBManager:
    """测试数据库管理器"""

    @pytest.fixture
    def db(self, temp_db_path):
        """创建测试数据库实例"""
        db = DBManager(database_file=temp_db_path)
        yield db
        db.close()

    class TestInitialization:
        """测试数据库初始化"""

        def test_tables_created(self, db):
            """测试表是否正确创建"""
            cursor = db.conn.cursor()

            # 检查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            assert "notes" in tables
            assert "books" in tables
            assert "recordings" in tables
            assert "qa" in tables

        def test_indexes_created(self, db):
            """测试索引是否正确创建"""
            cursor = db.conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cursor.fetchall()]

            assert "idx_books_title" in indexes
            assert "idx_recordings_book_id" in indexes
            assert "idx_qa_book_id" in indexes

    class TestBookOperations:
        """测试书籍操作"""

        def test_add_book_success(self, db):
            """测试成功添加书籍"""
            book_id = db.add_book("测试书籍", "测试作者")
            assert book_id is not None
            assert isinstance(book_id, int)
            assert book_id > 0

        def test_add_book_without_author(self, db):
            """测试添加无作者的书籍"""
            book_id = db.add_book("测试书籍")
            assert book_id is not None

        def test_add_book_invalid_title_raises_error(self, db):
            """测试添加无效标题书籍应抛出错误"""
            with pytest.raises((ValueError, sqlite3.Error)):
                db.add_book("")

        def test_get_books_empty(self, db):
            """测试获取空书籍列表"""
            books = db.get_books()
            assert books == []

        def test_get_books_with_data(self, db):
            """测试获取书籍列表"""
            db.add_book("书籍1", "作者1")
            db.add_book("书籍2", "作者2")

            books = db.get_books()
            assert len(books) == 2
            assert books[0][1] == "书籍1"  # title
            assert books[0][2] == "作者1"  # author

        def test_get_books_search(self, db):
            """测试搜索书籍"""
            db.add_book("Python编程", "张三")
            db.add_book("Java编程", "李四")

            results = db.get_books(search_query="Python")
            assert len(results) == 1
            assert results[0][1] == "Python编程"

        def test_get_books_pagination(self, db):
            """测试书籍分页"""
            # 添加多本书籍
            for i in range(10):
                db.add_book(f"书籍{i}", f"作者{i}")

            # 测试分页
            books = db.get_books(limit=5, offset=0)
            assert len(books) == 5

            books = db.get_books(limit=5, offset=5)
            assert len(books) == 5

        def test_get_books_count(self, db):
            """测试获取书籍数量"""
            assert db.get_books_count() == 0

            db.add_book("书籍1")
            db.add_book("书籍2")

            assert db.get_books_count() == 2

        def test_get_book_by_title_found(self, db):
            """测试通过标题找到书籍"""
            book_id = db.add_book("测试书籍")
            found_id = db.get_book_by_title("测试书籍")
            assert found_id == book_id

        def test_get_book_by_title_not_found(self, db):
            """测试通过标题未找到书籍"""
            found_id = db.get_book_by_title("不存在的书")
            assert found_id is None

    class TestRecordingOperations:
        """测试录音操作"""

        @pytest.fixture
        def book_id(self, db):
            """创建测试书籍"""
            return db.add_book("测试书籍", "测试作者")

        def test_add_recording_success(self, db, book_id, temp_audio_file):
            """测试成功添加录音"""
            db.add_recording(book_id, temp_audio_file, "转录文本")

            recordings = db.get_recordings_by_book(book_id)
            assert len(recordings) == 1
            assert recordings[0][2] == "转录文本"

        def test_add_recording_invalid_book_id(self, db):
            """测试无效书籍ID添加录音应抛出错误"""
            with pytest.raises(ValueError):
                db.add_recording(0, "/path/to/audio.wav", "文本")

        def test_add_recording_invalid_path(self, db, book_id):
            """测试无效路径添加录音应抛出错误"""
            with pytest.raises(ValueError):
                db.add_recording(book_id, "invalid_path.exe", "文本")

        def test_get_recordings_empty(self, db, book_id):
            """测试获取空录音列表"""
            recordings = db.get_recordings_by_book(book_id)
            assert recordings == []

        def test_get_recordings_multiple(self, db, book_id, temp_audio_file, tmp_path):
            """测试获取多条录音"""
            first_file = tmp_path / "audio1.wav"
            first_file.write_bytes(b"RIFF$$$$WAVEfmt ")
            second_file = tmp_path / "audio2.wav"
            second_file.write_bytes(b"RIFF$$$$WAVEfmt ")

            db.add_recording(book_id, str(first_file), "文本1")
            db.add_recording(book_id, str(second_file), "文本2")

            recordings = db.get_recordings_by_book(book_id)
            assert len(recordings) == 2
            # 按时间倒序排列
            assert recordings[0][2] == "文本2"
            assert recordings[1][2] == "文本1"

        def test_get_recordings_invalid_book_id(self, db):
            """测试无效书籍ID获取录音"""
            with pytest.raises(ValueError):
                db.get_recordings_by_book(0)

        def test_update_recording_text(self, db, book_id, temp_audio_file):
            """测试更新录音文本"""
            db.add_recording(book_id, temp_audio_file, "旧文本")
            rec_id = db.get_recordings_by_book(book_id)[0][0]
            db.update_recording(rec_id, "新文本")
            updated = db.get_recording_by_id(rec_id)
            assert updated[3] == "新文本"

        def test_delete_recording(self, db, book_id, temp_audio_file):
            """测试删除录音"""
            db.add_recording(book_id, temp_audio_file, "删除文本")
            rec_id = db.get_recordings_by_book(book_id)[0][0]
            db.delete_recording(rec_id)
            assert db.get_recordings_by_book(book_id) == []

    class TestQAOperations:
        """测试问答操作"""

        @pytest.fixture
        def book_id(self, db):
            """创建测试书籍"""
            return db.add_book("测试书籍", "测试作者")

        def test_add_qa_success(self, db, book_id):
            """测试成功添加问答"""
            db.add_qa(book_id, "问题内容", "答案内容")

            qa_list = db.get_qa_by_book(book_id)
            assert len(qa_list) == 1
            assert qa_list[0][1] == "问题内容"
            assert qa_list[0][2] == "答案内容"

        def test_add_qa_invalid_book_id(self, db):
            """测试无效书籍ID添加问答应抛出错误"""
            with pytest.raises(ValueError):
                db.add_qa(0, "问题", "答案")

        def test_add_qa_invalid_question(self, db, book_id):
            """测试无效问题添加问答应抛出错误"""
            with pytest.raises(ValueError):
                db.add_qa(book_id, "", "答案")

        def test_get_qa_pagination(self, db, book_id):
            """测试问答分页"""
            for i in range(10):
                db.add_qa(book_id, f"问题{i}", f"答案{i}")

            qa_list = db.get_qa_by_book(book_id, limit=5, offset=0)
            assert len(qa_list) == 5

    class TestNoteOperations:
        """测试笔记操作"""

        def test_add_note_success(self, db):
            """测试成功添加笔记"""
            db.add_note("笔记标题", "笔记内容", "Summary")

            # 验证笔记是否添加成功
            cursor = db.conn.cursor()
            cursor.execute("SELECT * FROM notes WHERE title = ?", ("笔记标题",))
            note = cursor.fetchone()
            assert note is not None
            assert note[2] == "笔记内容"

        def test_add_note_invalid_title(self, db):
            """测试无效标题添加笔记应抛出错误"""
            with pytest.raises(ValueError):
                db.add_note("", "内容", "Summary")

    class TestErrorHandling:
        """测试错误处理"""

        def test_rollback_on_error(self, db):
            """测试错误时回滚"""
            # 先添加一个有效书籍
            db.add_book("有效书籍")

            # 尝试添加无效录音（应该失败）
            try:
                db.add_recording(999, "/path/audio.wav", "文本")
            except Exception:
                pass

            # 验证数据库连接仍然有效
            books = db.get_books()
            assert len(books) == 1

        def test_connection_close(self, db):
            """测试关闭连接"""
            db.close()
            # 验证连接已关闭
            with pytest.raises(sqlite3.Error):
                db.cursor.execute("SELECT 1")
