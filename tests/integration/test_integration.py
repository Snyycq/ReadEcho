"""
集成测试
测试模块之间的交互
"""

import pytest
import sys
import os
import tempfile

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app_services import AppServices


class TestBookRecordingWorkflow:
    """测试书籍和录音的完整工作流"""

    @pytest.fixture
    def services(self, temp_db_path):
        """创建测试服务实例"""
        services = AppServices(db_path=temp_db_path)
        yield services
        services.close()

    def test_add_book_and_recording(self, services, temp_audio_file):
        """测试添加书籍和录音的完整流程"""
        book_id = services.add_book("测试书籍", "测试作者")
        assert book_id is not None

        services.add_recording(book_id, temp_audio_file, "转录文本内容")

        recordings = services.get_recordings_by_book(book_id)
        assert len(recordings) == 1
        assert recordings[0][2] == "转录文本内容"

    def test_add_book_and_qa(self, services):
        """测试添加书籍和问答的完整流程"""
        book_id = services.add_book("测试书籍")
        assert book_id is not None

        services.add_qa(book_id, "问题1", "答案1")
        services.add_qa(book_id, "问题2", "答案2")

        qa_list = services.get_qa_by_book(book_id)
        assert len(qa_list) == 2

    def test_complete_workflow(self, services, tmp_path):
        """测试完整工作流：书籍 -> 录音 -> 问答"""
        book_id = services.add_book("工作流测试书", "作者")
        audio1 = tmp_path / "audio1.wav"
        audio1.write_bytes(b"RIFF$$$$WAVEfmt ")
        audio2 = tmp_path / "audio2.wav"
        audio2.write_bytes(b"RIFF$$$$WAVEfmt ")
        services.add_recording(book_id, str(audio1), "录音内容1")
        services.add_recording(book_id, str(audio2), "录音内容2")

        services.add_qa(book_id, "问题1", "答案1")
        services.add_qa(book_id, "问题2", "答案2")

        assert len(services.get_recordings_by_book(book_id)) == 2
        assert len(services.get_qa_by_book(book_id)) == 2

    def test_multiple_books_isolation(self, services, tmp_path):
        """测试多书籍数据隔离"""
        book1_id = services.add_book("书籍1")
        book2_id = services.add_book("书籍2")

        audio1 = tmp_path / "audio1.wav"
        audio1.write_bytes(b"RIFF$$$$WAVEfmt ")
        audio2 = tmp_path / "audio2.wav"
        audio2.write_bytes(b"RIFF$$$$WAVEfmt ")
        services.add_recording(book1_id, str(audio1), "书籍1的录音")
        services.add_recording(book2_id, str(audio2), "书籍2的录音")

        services.add_qa(book1_id, "书籍1的问题", "书籍1的答案")
        services.add_qa(book2_id, "书籍2的问题", "书籍2的答案")

        book1_recordings = services.get_recordings_by_book(book1_id)
        book2_recordings = services.get_recordings_by_book(book2_id)

        assert len(book1_recordings) == 1
        assert len(book2_recordings) == 1
        assert book1_recordings[0][2] == "书籍1的录音"
        assert book2_recordings[0][2] == "书籍2的录音"

        book1_qa = services.get_qa_by_book(book1_id)
        book2_qa = services.get_qa_by_book(book2_id)

        assert len(book1_qa) == 1
        assert len(book2_qa) == 1


class TestThemeSwitching:
    """测试主题切换功能"""

    @pytest.fixture
    def services(self, temp_db_path):
        """创建测试服务实例"""
        services = AppServices(db_path=temp_db_path)
        yield services
        services.close()

    def test_theme_toggle_persistence(self, services):
        """测试主题切换状态保持"""
        initial_mode = services.get_theme_mode()

        new_mode = services.toggle_theme()
        assert new_mode != initial_mode

        current_mode = services.get_theme_mode()
        assert current_mode == new_mode

    def test_multiple_theme_toggles(self, services):
        """测试多次主题切换"""
        modes = []
        for _ in range(5):
            modes.append(services.toggle_theme())

        for i in range(1, len(modes)):
            assert modes[i] != modes[i-1]


class TestServiceLifecycle:
    """测试服务生命周期"""

    def test_service_startup_shutdown(self, temp_db_path):
        """测试服务启动和关闭"""
        services = AppServices(db_path=temp_db_path)
        try:
            assert services.db is not None
            book_id = services.add_book("生命周期测试")
            assert book_id is not None
        finally:
            services.close()

    def test_service_restart(self, temp_db_path, temp_audio_file):
        """测试服务重启后数据持久化"""
        services1 = AppServices(db_path=temp_db_path)
        book_id = services1.add_book("持久化测试书")
        services1.add_recording(book_id, temp_audio_file, "录音内容")
        services1.close()

        services2 = AppServices(db_path=temp_db_path)
        recordings = services2.get_recordings_by_book(book_id)
        assert len(recordings) == 1
        assert recordings[0][2] == "录音内容"
        services2.close()


class TestErrorRecovery:
    """测试错误恢复"""

    @pytest.fixture
    def services(self, temp_db_path):
        """创建测试服务实例"""
        services = AppServices(db_path=temp_db_path)
        yield services
        services.close()

    def test_invalid_operation_recovery(self, services):
        """测试无效操作后的恢复"""
        with pytest.raises(Exception):
            services.add_recording(999, "/invalid/path", "文本")

        book_id = services.add_book("恢复测试")
        assert book_id is not None

    def test_partial_failure_isolation(self, services):
        """测试部分失败隔离"""
        book_id = services.add_book("隔离测试")

        try:
            services.add_recording(999, "/invalid", "文本")
        except Exception:
            pass

        services.add_qa(book_id, "问题", "答案")
        qa_list = services.get_qa_by_book(book_id)
        assert len(qa_list) == 1
