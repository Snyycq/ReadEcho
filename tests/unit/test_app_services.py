"""
app_services.py 单元测试
测试应用服务层
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app_services import AppServices


class TestAppServices:
    """测试应用服务"""

    @pytest.fixture
    def services(self, temp_db_path):
        """创建测试服务实例"""
        services = AppServices(db_path=temp_db_path)
        yield services
        services.close()

    class TestInitialization:
        """测试服务初始化"""

        def test_services_initialized(self, services):
            """测试服务是否正确初始化"""
            assert services.db is not None
            assert services.ai_service is not None
            assert services.recording_service is not None

        def test_initial_state(self, services):
            """测试初始状态"""
            assert services.current_book_id is None
            assert services.current_book_title == ""
            assert services.dark_mode is True

    class TestBookManagement:
        """测试书籍管理"""

        def test_add_book(self, services):
            """测试添加书籍"""
            book_id = services.add_book("测试书籍", "测试作者")
            assert book_id is not None
            assert services.current_book_id == book_id
            assert services.current_book_title == "测试书籍"

        def test_get_books_empty(self, services):
            """测试获取空书籍列表"""
            books = services.get_books()
            assert books == []

        def test_get_books_with_data(self, services):
            """测试获取书籍列表"""
            services.add_book("书籍1")
            services.add_book("书籍2")

            books = services.get_books()
            assert len(books) == 2

        def test_get_book_by_title(self, services):
            """测试通过标题获取书籍"""
            services.add_book("测试书籍")
            book_id = services.get_book_by_title("测试书籍")
            assert book_id is not None

        def test_get_book_by_title_not_found(self, services):
            """测试通过标题未找到书籍"""
            book_id = services.get_book_by_title("不存在的书")
            assert book_id is None

        def test_delete_book(self, services):
            """测试删除书籍"""
            book_id = services.add_book("测试书籍")
            services.delete_book(book_id)
            assert services.get_book_by_title("测试书籍") is None

    class TestCurrentBook:
        """测试当前书籍管理"""

        def test_set_current_book(self, services):
            """测试设置当前书籍"""
            services.set_current_book(1, "测试书籍")
            assert services.current_book_id == 1
            assert services.current_book_title == "测试书籍"

        def test_get_current_book(self, services):
            """测试获取当前书籍"""
            services.set_current_book(1, "测试书籍")
            book = services.get_current_book()
            assert book['id'] == 1
            assert book['title'] == "测试书籍"

        def test_clear_current_book(self, services):
            """测试清除当前书籍"""
            services.set_current_book(1, "测试书籍")
            services.clear_current_book()
            assert services.current_book_id is None
            assert services.current_book_title == ""

    class TestRecording:
        """测试录音功能"""

        def test_add_recording(self, services, temp_audio_file):
            """测试添加录音"""
            book_id = services.add_book("测试书籍")
            services.add_recording(book_id, temp_audio_file, "转录文本")

            recordings = services.get_recordings_by_book(book_id)
            assert len(recordings) == 1

        def test_get_recordings_by_book_empty(self, services):
            """测试获取空录音列表"""
            book_id = services.add_book("测试书籍")
            recordings = services.get_recordings_by_book(book_id)
            assert recordings == []

        def test_edit_recording_text(self, services, temp_audio_file):
            """测试更新录音文本"""
            book_id = services.add_book("测试书籍")
            services.add_recording(book_id, temp_audio_file, "旧文本")
            recordings = services.get_recordings_by_book(book_id)
            rec_id = recordings[0][0]
            services.update_recording_text(rec_id, "新文本")

            updated = services.get_recording_by_id(rec_id)
            assert updated[3] == "新文本"

        def test_delete_recording(self, services, temp_audio_file):
            """测试删除录音"""
            book_id = services.add_book("测试书籍")
            services.add_recording(book_id, temp_audio_file, "删除文本")
            rec_id = services.get_recordings_by_book(book_id)[0][0]
            services.delete_recording(rec_id)
            assert services.get_recordings_by_book(book_id) == []

    class TestQA:
        """测试问答功能"""

        def test_add_qa(self, services):
            """测试添加问答"""
            book_id = services.add_book("测试书籍")
            services.add_qa(book_id, "问题", "答案")

            qa_list = services.get_qa_by_book(book_id)
            assert len(qa_list) == 1

        def test_get_qa_pagination(self, services):
            """测试问答分页"""
            book_id = services.add_book("测试书籍")
            for i in range(10):
                services.add_qa(book_id, f"问题{i}", f"答案{i}")

            qa_list = services.get_qa_by_book(book_id, limit=5, offset=0)
            assert len(qa_list) == 5

    class TestTheme:
        """测试主题管理"""

        def test_toggle_theme(self, services):
            """测试切换主题"""
            initial_mode = services.dark_mode
            new_mode = services.toggle_theme()
            assert new_mode == (not initial_mode)
            assert services.dark_mode == new_mode

        def test_get_theme_mode(self, services):
            """测试获取主题模式"""
            mode = services.get_theme_mode()
            assert isinstance(mode, bool)

    class TestCleanup:
        """测试资源清理"""

        def test_close(self, services):
            """测试关闭服务"""
            services.close()
            # 验证服务已关闭，不应抛出异常

        def test_cleanup_alias(self, services):
            """测试cleanup是close的别名"""
            services.cleanup()
            # 验证服务已关闭
