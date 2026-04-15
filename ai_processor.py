"""
ReadEcho Pro AI处理模块
包含所有AI相关的线程和功能：Whisper转录、Ollama总结和问答
"""

import torch
import whisper
import ollama
from PyQt6.QtCore import QThread, pyqtSignal

from config import WHISPER_MODEL, OLLAMA_MODEL


class ModelLoaderThread(QThread):
    """后台加载Whisper模型的线程，避免阻塞UI"""

    model_loaded = pyqtSignal(object)

    def run(self):
        """在后台线程中加载Whisper模型"""
        device = "cuda" if torch.cuda.is_available() else "cpu"
        # 使用配置中指定的模型大小
        model = whisper.load_model(WHISPER_MODEL, device=device)
        self.model_loaded.emit(model)


class AIProcessThread(QThread):
    """处理AI任务的线程：总结、语音转录、问答"""

    result_ready = pyqtSignal(str, str)

    def __init__(self, action_type, data, book_title, stt_model):
        """
        初始化AI处理线程

        Args:
            action_type: 操作类型 ("Summarize", "VoiceNote", "Q&A")
            data: 输入数据（书名、音频文件路径或问题）
            book_title: 书籍标题
            stt_model: 已加载的Whisper模型（用于语音转录）
        """
        super().__init__()
        self.action_type = action_type
        self.data = data
        self.book_title = book_title
        self.stt_model = stt_model

    def run(self):
        """执行AI处理任务"""
        try:
            if self.action_type == "Summarize":
                self._generate_summary()
            elif self.action_type == "VoiceNote":
                self._transcribe_audio()
            elif self.action_type == "Q&A":
                self._answer_question()
        except Exception as e:
            print(f"[ERROR in AIProcessThread] {str(e)}")
            self.result_ready.emit("Error", str(e))

    def _generate_summary(self):
        """生成书籍总结"""
        prompt = f"Please provide a detailed summary of the book '{self.data}' in Chinese. Include main plots and key thoughts."
        resp = ollama.chat(model=OLLAMA_MODEL, messages=[{'role': 'user', 'content': prompt}])
        self.result_ready.emit("Summary", resp['message']['content'])

    def _transcribe_audio(self):
        """转录音频文件为文字"""
        if self.stt_model is None:
            raise Exception("Model not loaded yet! Please wait a moment.")

        # 使用Whisper转录音频
        result = self.stt_model.transcribe(
            self.data,
            fp16=torch.cuda.is_available(),
            beam_size=1
        )
        transcribed_text = result['text']
        self.result_ready.emit("VoiceNote", transcribed_text)

    def _answer_question(self):
        """回答关于书籍的问题"""
        question = self.data
        prompt = f"关于书籍《{self.book_title}》的问题：{question}\n请用中文详细回答这个问题。"
        resp = ollama.chat(model=OLLAMA_MODEL, messages=[{'role': 'user', 'content': prompt}])
        self.result_ready.emit("Q&A", resp['message']['content'])


class AIService:
    """AI服务管理器，提供统一的AI功能接口"""

    def __init__(self):
        self.stt_model = None
        self.model_loader = None

    def load_whisper_model(self, callback):
        """异步加载Whisper模型"""
        self.model_loader = ModelLoaderThread()
        self.model_loader.model_loaded.connect(callback)
        self.model_loader.start()

    def create_summary_thread(self, book_title, callback):
        """创建总结生成线程"""
        thread = AIProcessThread("Summarize", book_title, book_title, self.stt_model)
        thread.result_ready.connect(callback)
        return thread

    def create_transcription_thread(self, audio_path, book_title, callback):
        """创建音频转录线程"""
        thread = AIProcessThread("VoiceNote", audio_path, book_title, self.stt_model)
        thread.result_ready.connect(callback)
        return thread

    def create_qa_thread(self, question, book_title, callback):
        """创建问答线程"""
        thread = AIProcessThread("Q&A", question, book_title, self.stt_model)
        thread.result_ready.connect(callback)
        return thread

    def set_stt_model(self, model):
        """设置已加载的Whisper模型"""
        self.stt_model = model