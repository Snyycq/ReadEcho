"""
Pytest 配置文件
定义共享的 fixtures 和配置
"""

import pytest
import tempfile
import os
import sys

# 确保项目根目录在路径中
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


@pytest.fixture
def temp_db_path():
    """提供临时数据库文件路径"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        path = f.name
    yield path
    # 清理
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def mock_whisper_model():
    """模拟Whisper模型"""
    class MockWhisperModel:
        def __init__(self):
            self.device = "cpu"

        def transcribe(self, audio_path):
            return {"text": "这是模拟的转录文本"}

    return MockWhisperModel()


@pytest.fixture
def sample_book_data():
    """提供示例书籍数据"""
    return {
        "title": "测试书籍",
        "author": "测试作者"
    }


@pytest.fixture
def sample_recording_data():
    """提供示例录音数据"""
    return {
        "file_path": "/tmp/test_recording.wav",
        "transcribed_text": "这是测试转录文本"
    }


@pytest.fixture
def temp_audio_file(tmp_path):
    """提供一个真实存在的音频文件路径"""
    audio_file = tmp_path / "test_recording.wav"
    audio_file.write_bytes(b"RIFF$$$$WAVEfmt ")
    return str(audio_file)


@pytest.fixture
def sample_qa_data():
    """提供示例问答数据"""
    return {
        "question": "这本书讲了什么？",
        "answer": "这是一本测试书籍，主要讲述测试内容。"
    }


@pytest.fixture(scope="session")
def test_config():
    """测试配置"""
    return {
        "sample_rate": 16000,
        "temp_audio_dir": tempfile.mkdtemp(),
        "test_timeout": 30
    }
