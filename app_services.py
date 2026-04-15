"""
ReadEcho Pro 应用服务模块
整合所有业务逻辑服务，提供统一的接口
"""

from database_manager import DBManager
from ai_processor import AIService
from recording_manager import RecordingService
from config import SAMPLE_RATE, TEMP_AUDIO_FILE


class AppServices:
    """应用服务管理器，整合所有业务逻辑服务"""

    def __init__(self):
        """初始化所有服务"""
        self.db = DBManager()
        self.ai_service = AIService()
        self.recording_service = RecordingService()
        self.current_book_id = None
        self.current_book_title = ""
        self.dark_mode = True
        self.stt_model = None  # Whisper模型，由AI服务管理

    # --- 数据库服务封装 ---

    def add_book(self, title, author=""):
        """添加新书籍"""
        book_id = self.db.add_book(title, author)
        self.current_book_id = book_id
        self.current_book_title = title
        return book_id

    def get_books(self, search_query=""):
        """获取书籍列表"""
        return self.db.get_books(search_query)

    def get_book_by_title(self, title):
        """根据书名获取书籍ID"""
        return self.db.get_book_by_title(title)

    def add_note(self, title, content, note_type="Summary"):
        """添加笔记"""
        self.db.add_note(title, content, note_type)

    def add_recording(self, book_id, file_path, transcribed_text):
        """添加录音记录"""
        self.db.add_recording(book_id, file_path, transcribed_text)

    def get_recordings_by_book(self, book_id):
        """获取指定书籍的录音记录"""
        return self.db.get_recordings_by_book(book_id)

    def add_qa(self, book_id, question, answer):
        """添加问答记录"""
        self.db.add_qa(book_id, question, answer)

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

    def create_qa_thread(self, question, book_title, callback):
        """创建问答线程"""
        return self.ai_service.create_qa_thread(question, book_title, callback)

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

    # --- 主题管理 ---

    def toggle_theme(self):
        """切换主题"""
        self.dark_mode = not self.dark_mode
        return self.dark_mode

    def get_theme_mode(self):
        """获取当前主题模式"""
        return self.dark_mode

    # --- 当前书籍管理 ---

    def set_current_book(self, book_id, title):
        """设置当前选中的书籍"""
        self.current_book_id = book_id
        self.current_book_title = title

    def get_current_book(self):
        """获取当前选中的书籍信息"""
        return {
            'id': self.current_book_id,
            'title': self.current_book_title
        }

    def clear_current_book(self):
        """清除当前选中的书籍"""
        self.current_book_id = None
        self.current_book_title = ""

    # --- 实用方法 ---

    def get_sample_rate(self):
        """获取采样率"""
        return SAMPLE_RATE

    def get_temp_audio_file(self):
        """获取临时音频文件路径"""
        return TEMP_AUDIO_FILE

    def close(self):
        """关闭所有服务"""
        # 关闭数据库连接
        if hasattr(self.db, 'close'):
            self.db.close()

        # 清理录音资源
        self.cleanup_recording()

    def __del__(self):
        """析构函数，确保资源被释放"""
        self.close()


# 服务工厂函数
def create_app_services():
    """创建应用服务实例"""
    return AppServices()