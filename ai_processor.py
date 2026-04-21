"""
ReadEcho Pro AI处理模块
包含所有AI相关的线程和功能：Whisper转录、Ollama总结和问答
"""

import torch
import ollama
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Optional, Callable

from config import WHISPER_MODEL, OLLAMA_MODEL, LOGGER
from validators import InputValidator
from model_cache import model_cache


class ModelLoaderThread(QThread):
    """后台加载Whisper模型的线程，避免阻塞UI，使用缓存机制"""

    model_loaded = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, model_size: str = WHISPER_MODEL):
        """
        初始化模型加载线程

        Args:
            model_size: 模型大小，默认使用配置中的设置
        """
        super().__init__()
        self.model_size = model_size

    def run(self):
        """在后台线程中加载Whisper模型，使用缓存"""
        try:
            LOGGER.info(f"开始加载Whisper模型: {self.model_size}")

            # 使用缓存机制加载模型
            model = model_cache.get_whisper_model(self.model_size)
            LOGGER.info("Whisper模型加载成功")
            self.model_loaded.emit(model)
        except Exception as e:
            error_msg = f"Whisper模型加载失败: {str(e)}"
            LOGGER.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)


class AIProcessThread(QThread):
    """处理AI任务的线程：总结、语音转录、问答"""

    result_ready = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)
    progress_updated = pyqtSignal(str)

    def __init__(self, action_type: str, data: str, book_title: str, stt_model: Optional[object]):
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
            LOGGER.info(f"开始处理AI任务: {self.action_type}")

            if self.action_type == "Summarize":
                self.progress_updated.emit("正在生成摘要...")
                self._generate_summary()
            elif self.action_type == "VoiceNote":
                self.progress_updated.emit("正在转录音频...")
                self._transcribe_audio()
            elif self.action_type == "Q&A":
                self.progress_updated.emit("正在回答问题...")
                self._answer_question()
            else:
                raise ValueError(f"未知的操作类型: {self.action_type}")

        except FileNotFoundError as e:
            error_msg = f"文件未找到: {str(e)}"
            LOGGER.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.result_ready.emit("Error", error_msg)
        except RuntimeError as e:
            error_msg = f"运行时错误: {str(e)}"
            LOGGER.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.result_ready.emit("Error", error_msg)
        except Exception as e:
            error_msg = f"AI处理失败: {str(e)}"
            LOGGER.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)
            self.result_ready.emit("Error", error_msg)

    def _generate_summary(self):
        """生成书籍总结"""
        try:
            book_title = InputValidator.validate_book_title(self.data)
            prompt = f"请为书籍《{book_title}》提供一个详细的摘要。包括主要情节和关键思想。使用中文回答。"

            LOGGER.debug(f"调用Ollama生成摘要: 模型={OLLAMA_MODEL}")
            resp = ollama.chat(
                model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}], stream=False
            )

            if not resp or "message" not in resp:
                raise RuntimeError("Ollama返回了无效的响应")

            summary = resp["message"].get("content", "")
            if not summary:
                raise RuntimeError("生成的摘要为空")

            LOGGER.info("摘要生成成功")
            self.result_ready.emit("Summary", summary)
        except Exception as e:
            LOGGER.error(f"生成摘要失败: {e}")
            raise

    def _transcribe_audio(self):
        """转录音频文件为文字"""
        try:
            if self.stt_model is None:
                raise RuntimeError("模型尚未加载，请稍候")

            # 验证音频文件
            audio_path = InputValidator.validate_audio_file(self.data)
            LOGGER.info(f"开始转录音频: {audio_path}")

            # 使用Whisper转录音频
            result = self.stt_model.transcribe(
                audio_path, fp16=torch.cuda.is_available(), beam_size=1, verbose=False
            )

            if not result or "text" not in result:
                raise RuntimeError("转录失败，未获得结果")

            transcribed_text = result["text"].strip()
            if not transcribed_text:
                LOGGER.warning("转录结果为空文本")

            corrected_text = self._correct_transcription(transcribed_text)
            LOGGER.info(f"转录成功，文本长度: {len(corrected_text)}")
            self.result_ready.emit("VoiceNote", corrected_text)
        except Exception as e:
            LOGGER.error(f"音频转录失败: {e}")
            raise

    def _correct_transcription(self, text: str) -> str:
        """使用AI模型自动纠正中文转录文本中的错别字"""
        try:
            if not text or not isinstance(text, str):
                return text

            prompt = (
                "请纠正下面的中文转录文本中的错别字和明显的语义错误，"
                "保持原文意思不变，只输出纠正后的文本，不要添加额外说明：\n\n"
                f"{text}"
            )
            resp = ollama.chat(
                model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}], stream=False
            )
            if resp and "message" in resp:
                corrected = resp["message"].get("content", "").strip()
                if corrected:
                    return corrected
            return text
        except Exception as e:
            LOGGER.warning(f"纠正转录文本失败，保留原文: {e}")
            return text

    def _answer_question(self):
        """回答关于书籍的问题"""
        try:
            question = InputValidator.validate_question(self.data)
            book_title = InputValidator.validate_book_title(self.book_title)

            prompt = f"用户提问关于书籍《{book_title}》的问题：\n{question}\n\n请用中文详细回答这个问题。"

            LOGGER.debug(f"调用Ollama回答问题: 模型={OLLAMA_MODEL}")
            resp = ollama.chat(
                model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}], stream=False
            )

            if not resp or "message" not in resp:
                raise RuntimeError("Ollama返回了无效的响应")

            answer = resp["message"].get("content", "")
            if not answer:
                raise RuntimeError("生成的答案为空")

            LOGGER.info("问答完成")
            self.result_ready.emit("Q&A", answer)
        except Exception as e:
            LOGGER.error(f"回答问题失败: {e}")
            raise


class AIService:
    """AI服务管理器，提供统一的AI功能接口"""

    def __init__(self):
        """初始化AI服务"""
        self.stt_model = None
        self.model_loader = None
        LOGGER.info("AI服务初始化完成")

    def load_whisper_model(self, callback: Callable):
        """
        异步加载Whisper模型

        Args:
            callback: 模型加载完成后的回调函数
        """
        if self.model_loader and self.model_loader.isRunning():
            LOGGER.warning("模型加载已在进行中")
            return

        try:
            self.model_loader = ModelLoaderThread()
            self.model_loader.model_loaded.connect(callback)
            self.model_loader.model_loaded.connect(self._on_model_loaded)
            self.model_loader.error_occurred.connect(self._on_model_error)
            self.model_loader.start()
            LOGGER.info("模型加载线程已启动")
        except Exception as e:
            LOGGER.error(f"启动模型加载线程失败: {e}")
            raise

    def create_summary_thread(self, book_title: str, callback: Callable) -> AIProcessThread:
        """
        创建总结生成线程

        Args:
            book_title: 书籍标题
            callback: 结果回调函数

        Returns:
            AIProcessThread实例
        """
        try:
            book_title = InputValidator.validate_book_title(book_title)
            thread = AIProcessThread("Summarize", book_title, book_title, self.stt_model)
            thread.result_ready.connect(callback)
            LOGGER.debug(f"创建总结线程: {book_title}")
            return thread
        except Exception as e:
            LOGGER.error(f"创建总结线程失败: {e}")
            raise

    def create_transcription_thread(
        self, audio_path: str, book_title: str, callback: Callable
    ) -> AIProcessThread:
        """
        创建音频转录线程

        Args:
            audio_path: 音频文件路径
            book_title: 书籍标题
            callback: 结果回调函数

        Returns:
            AIProcessThread实例
        """
        try:
            audio_path = InputValidator.validate_audio_file(audio_path)
            book_title = InputValidator.validate_book_title(book_title)
            thread = AIProcessThread("VoiceNote", audio_path, book_title, self.stt_model)
            thread.result_ready.connect(callback)
            LOGGER.debug(f"创建转录线程: {audio_path}")
            return thread
        except Exception as e:
            LOGGER.error(f"创建转录线程失败: {e}")
            raise

    def create_qa_thread(
        self, question: str, book_title: str, callback: Callable
    ) -> AIProcessThread:
        """
        创建问答线程

        Args:
            question: 问题文本
            book_title: 书籍标题
            callback: 结果回调函数

        Returns:
            AIProcessThread实例
        """
        try:
            question = InputValidator.validate_question(question)
            book_title = InputValidator.validate_book_title(book_title)
            thread = AIProcessThread("Q&A", question, book_title, self.stt_model)
            thread.result_ready.connect(callback)
            LOGGER.debug(f"创建问答线程: {question[:50]}...")
            return thread
        except Exception as e:
            LOGGER.error(f"创建问答线程失败: {e}")
            raise

    def set_stt_model(self, model: object) -> None:
        """
        设置已加载的Whisper模型

        Args:
            model: Whisper模型实例
        """
        self.stt_model = model
        LOGGER.info("Whisper模型已设置")

    def _on_model_loaded(self, model: object) -> None:
        """模型加载成功的处理函数"""
        LOGGER.info("Whisper模型加载完成")
        self.set_stt_model(model)

    def _on_model_error(self, error_msg: str) -> None:
        """模型加载失败的处理函数"""
        LOGGER.error(f"模型加载错误: {error_msg}")
