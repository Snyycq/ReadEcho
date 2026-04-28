"""
ReadEcho Pro AI处理模块
包含所有AI相关的线程和功能：Whisper转录、DeepSeek/Ollama总结和问答
"""

from PyQt6.QtCore import QThread, pyqtSignal
from typing import Optional, Callable

from config import (
    WHISPER_MODEL, AI_PROVIDER,
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    OLLAMA_MODEL, OLLAMA_BASE_URL, LOGGER
)
from utils.validators import InputValidator
from core.model_cache import model_cache


def chat_completion(prompt: str, model: str = None) -> str:
    """
    统一的 AI 调用接口，屏蔽 provider 差异

    Args:
        prompt: 用户输入的提示文本
        model: 模型名称（可选，默认使用配置中的模型）

    Returns:
        AI 生成的响应文本

    Raises:
        RuntimeError: 如果 AI 调用失败
    """
    try:
        # 判断使用哪个 provider
        use_ollama = False
        if model:
            if model.startswith("qwen") or model.startswith("llama") or model.startswith("mistral"):
                use_ollama = True
        elif AI_PROVIDER == "ollama":
            use_ollama = True

        if use_ollama:
            import ollama
            ollama_model = model or OLLAMA_MODEL
            resp = ollama.chat(
                model=ollama_model,
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            return resp["message"]["content"]
        else:
            import openai
            deepseek_model = model or DEEPSEEK_MODEL
            client = openai.OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
            resp = client.chat.completions.create(
                model=deepseek_model,
                messages=[{"role": "user", "content": prompt}]
            )
            return resp.choices[0].message.content
    except Exception as e:
        LOGGER.error(f"AI调用失败 ({AI_PROVIDER}): {e}")
        raise RuntimeError(f"AI调用失败: {str(e)}")


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

            if model is None:
                error_msg = "Whisper模型加载失败: torch或whisper未安装"
                LOGGER.error(error_msg)
                self.error_occurred.emit(error_msg)
                return

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

    def __init__(self, action_type: str, data: str, book_title: str, stt_model: Optional[object],
                 model: Optional[str] = None):
        """
        初始化AI处理线程

        Args:
            action_type: 操作类型 ("Summarize", "VoiceNote", "Q&A")
            data: 输入数据（书名、音频文件路径或问题）
            book_title: 书籍标题
            stt_model: 已加载的Whisper模型（用于语音转录）
            model: AI模型名称（可选）
        """
        super().__init__()
        self.action_type = action_type
        self.data = data
        self.book_title = book_title
        self.stt_model = stt_model
        self.model = model

    def run(self):
        """执行AI处理任务"""
        try:
            LOGGER.info(f"[DEBUG-转录] 开始处理AI任务: {self.action_type}")
            LOGGER.debug(f"[DEBUG-转录] 数据: {self.data[:50] if self.data else 'None'}...")
            LOGGER.debug(f"[DEBUG-转录] 书籍标题: {self.book_title}")
            LOGGER.debug(f"[DEBUG-转录] STT模型: {self.stt_model}")

            if self.action_type == "Summarize":
                self.progress_updated.emit("正在生成摘要...")
                self._generate_summary()
            elif self.action_type == "VoiceNote":
                LOGGER.debug("[DEBUG-转录] 进入语音转录流程...")
                self.progress_updated.emit("正在转录音频...")
                self._transcribe_audio()
            elif self.action_type == "Q&A":
                self.progress_updated.emit("正在回答问题...")
                self._answer_question()
            else:
                raise ValueError(f"未知的操作类型: {self.action_type}")

        except FileNotFoundError as e:
            error_msg = f"文件未找到: {str(e)}"
            LOGGER.error(f"[DEBUG-转录] {error_msg}")
            self.error_occurred.emit(error_msg)
            self.result_ready.emit("Error", error_msg)
        except RuntimeError as e:
            error_msg = f"运行时错误: {str(e)}"
            LOGGER.error(f"[DEBUG-转录] {error_msg}")
            self.error_occurred.emit(error_msg)
            self.result_ready.emit("Error", error_msg)
        except Exception as e:
            error_msg = f"AI处理失败: {str(e)}"
            LOGGER.error(f"[DEBUG-转录] {error_msg}", exc_info=True)
            self.error_occurred.emit(error_msg)
            self.result_ready.emit("Error", error_msg)

    def _generate_summary(self):
        """生成书籍总结"""
        try:
            book_title = InputValidator.validate_book_title(self.data)
            prompt = f"请为书籍《{book_title}》提供一个详细的摘要。包括主要情节和关键思想。使用中文回答。"

            LOGGER.debug(f"调用AI生成摘要: 模型={self.model or AI_PROVIDER}")
            summary = chat_completion(prompt, self.model)

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
            LOGGER.debug("[DEBUG-转录] 进入 _transcribe_audio 方法")

            if self.stt_model is None:
                LOGGER.error("[DEBUG-转录] STT模型为 None")
                raise RuntimeError("模型尚未加载，请稍候")

            LOGGER.debug(f"[DEBUG-转录] STT模型类型: {type(self.stt_model)}")

            import torch
            import sys
            import os

            # 验证音频文件
            LOGGER.debug(f"[DEBUG-转录] 验证音频文件: {self.data}")
            audio_path = InputValidator.validate_audio_file(self.data)
            LOGGER.info(f"[DEBUG-转录] 开始转录音频: {audio_path}")

            # 检查文件是否存在
            if not os.path.exists(audio_path):
                LOGGER.error(f"[DEBUG-转录] 音频文件不存在: {audio_path}")
                raise FileNotFoundError(f"音频文件不存在: {audio_path}")

            file_size = os.path.getsize(audio_path)
            LOGGER.debug(f"[DEBUG-转录] 音频文件大小: {file_size} bytes")

            # 修复 tqdm 的 stdout/stderr 问题（Windows 环境）
            class SafeStream:
                def __init__(self):
                    self._file = open(os.devnull, 'w')
                def write(self, s):
                    pass
                def flush(self):
                    pass
                def close(self):
                    self._file.close()

            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = SafeStream()
            sys.stderr = SafeStream()

            try:
                LOGGER.debug("[DEBUG-转录] 开始调用 Whisper transcribe...")
                # 使用Whisper转录音频
                result = self.stt_model.transcribe(
                    audio_path, fp16=torch.cuda.is_available(), beam_size=1, verbose=False
                )
                LOGGER.debug(f"[DEBUG-转录] Whisper 转录完成，结果类型: {type(result)}")
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

            if not result or "text" not in result:
                LOGGER.error(f"[DEBUG-转录] 转录结果无效: {result}")
                raise RuntimeError("转录失败，未获得结果")

            transcribed_text = result["text"].strip()
            LOGGER.debug(f"[DEBUG-转录] 转录文本长度: {len(transcribed_text)}")
            if not transcribed_text:
                LOGGER.warning("[DEBUG-转录] 转录结果为空文本")

            LOGGER.debug("[DEBUG-转录] 开始纠正转录文本...")
            corrected_text = self._correct_transcription(transcribed_text)
            LOGGER.info(f"[DEBUG-转录] 转录成功，最终文本长度: {len(corrected_text)}")
            self.result_ready.emit("VoiceNote", corrected_text)
        except Exception as e:
            LOGGER.error(f"[DEBUG-转录] 音频转录失败: {e}", exc_info=True)
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
            corrected = chat_completion(prompt)
            if corrected and corrected.strip():
                return corrected.strip()
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

            LOGGER.debug(f"调用AI回答问题: 模型={self.model or AI_PROVIDER}")
            answer = chat_completion(prompt, self.model)

            if not answer:
                raise RuntimeError("生成的答案为空")

            LOGGER.info("问答完成")
            self.result_ready.emit("Q&A", answer)
        except Exception as e:
            LOGGER.error(f"回答问题失败: {e}")
            raise


def split_text_into_chunks(text: str, max_chunk_size: int = 8000, min_chunk_size: int = 1000) -> list:
    """将文本按段落边界分段（优化版：更大段落减少处理次数）

    Args:
        text: 要分段的文本
        max_chunk_size: 每段最大字符数（默认8000，比原来大一倍）
        min_chunk_size: 最小段落大小，低于此值合并到前一段

    Returns:
        分段后的文本列表
    """
    if not text or len(text) <= max_chunk_size:
        return [text] if text else []

    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if not para.strip():
            continue

        if len(current_chunk) + len(para) + 2 <= max_chunk_size:
            current_chunk = (current_chunk + "\n\n" + para).strip()
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = para.strip()

    if current_chunk:
        # 最后一段太短，合并到前一段
        if chunks and len(current_chunk) < min_chunk_size:
            chunks[-1] += "\n\n" + current_chunk
        else:
            chunks.append(current_chunk)

    return chunks if chunks else [text[:max_chunk_size]]


class ChunkedAIThread(QThread):
    """分段 AI 处理线程：将长文本分段总结后再合并（优化版：更大段落+进度条）"""

    result_ready = pyqtSignal(str, str)
    progress_updated = pyqtSignal(str)  # 发送进度信息，格式: "progress:百分比:消息"

    def __init__(self, action_type: str, full_text: str, book_title: str,
                 model: str = None, max_chunk_size: int = 8000, max_workers: int = 3):
        super().__init__()
        self.action_type = action_type  # "summary" 或 "mindmap"
        self.full_text = full_text
        self.book_title = book_title
        self.model = model
        self.max_chunk_size = max_chunk_size
        self.max_workers = max_workers  # 并发数

    def _emit_progress(self, percent: int, message: str):
        """发送进度信息"""
        self.progress_updated.emit(f"progress:{percent}:{message}")

    def run(self):
        try:
            chunks = split_text_into_chunks(self.full_text, self.max_chunk_size)
            total = len(chunks)
            LOGGER.info(f"文本分段完成: {total} 段，每段最大 {self.max_chunk_size} 字符")

            if total == 1:
                # 单段，直接处理
                self._emit_progress(10, "正在分析书籍内容...")
                result = self._process_single_chunk(chunks[0])
                self._emit_progress(100, "分析完成")
                self.result_ready.emit("Summary", result)
                return

            # 多段，使用线程池并发处理
            from concurrent.futures import ThreadPoolExecutor, as_completed

            chunk_summaries = []
            completed_count = 0

            # 计算进度：0-80% 用于分段处理，80-100% 用于合并
            segment_percent = 80

            with ThreadPoolExecutor(max_workers=min(self.max_workers, total)) as executor:
                # 提交所有任务
                future_to_idx = {
                    executor.submit(self._process_single_chunk, chunk): i
                    for i, chunk in enumerate(chunks)
                }

                # 按完成顺序收集结果
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    completed_count += 1
                    percent = int(completed_count / total * segment_percent)
                    self._emit_progress(percent, f"正在分析第 {completed_count}/{total} 段...")

                    try:
                        summary = future.result()
                        chunk_summaries.append((idx, summary))
                        LOGGER.info(f"第 {idx+1}/{total} 段分析完成")
                    except Exception as e:
                        LOGGER.error(f"第 {idx+1} 段分析失败: {e}")
                        chunk_summaries.append((idx, f"[处理失败: {str(e)}]"))

            # 按原始顺序排序
            chunk_summaries.sort(key=lambda x: x[0])
            summaries = [s[1] for s in chunk_summaries]

            # 合并所有段落总结
            self._emit_progress(85, "正在合并总结...")
            final_result = self._merge_summaries(summaries)
            self._emit_progress(100, "完成")
            self.result_ready.emit("Summary", final_result)
            LOGGER.info("分段总结完成")

        except Exception as e:
            error_msg = f"分段AI处理失败: {str(e)}"
            LOGGER.error(error_msg, exc_info=True)
            self.result_ready.emit("Error", error_msg)

    def _process_single_chunk(self, chunk: str) -> str:
        """处理单个文本段落"""
        # 截取前3000字符用于处理
        short_chunk = chunk[:3000] + "..." if len(chunk) > 3000 else chunk

        if self.action_type == "mindmap":
            prompt = f"用树状结构列出核心主题和关键点：\n{short_chunk}"
        else:
            prompt = f"详细总结这段内容的要点，包含3-5个主要观点：\n{short_chunk}"

        return chat_completion(prompt, self.model)

    def _merge_summaries(self, summaries: list) -> str:
        """合并多个段落总结为最终结果（总-分-总结构）"""
        # 截取每个总结的前800字符
        short_summaries = [s[:800] for s in summaries]
        combined = "\n\n".join(
            f"【第{i+1}部分】{s}" for i, s in enumerate(short_summaries)
        )

        if self.action_type == "mindmap":
            merge_prompt = (
                f"请为《{self.book_title}》生成详细的思维导图，使用树状结构。\n"
                f"要求：顶层为书名，第二层为主要章节/主题，第三层为关键内容和要点。\n"
                f"使用 Unicode 树状符号（├── └── │）展示层级关系。\n\n"
                f"各部分内容：\n{combined}"
            )
        else:
            merge_prompt = (
                f"请为《{self.book_title}》撰写一份详细的书籍总结，采用【总-分-总】结构：\n\n"
                f"【总体概述】（100-150字）：简要介绍这本书的主题、作者背景和核心价值。\n\n"
                f"【核心内容】（分点展开）：\n"
                f"- 详细列出3-5个主要观点/章节\n"
                f"- 每个观点用2-3句话解释说明\n"
                f"- 包含具体例子或关键论述\n\n"
                f"【总结与推荐】（50-100字）：总结阅读价值和适合人群。\n\n"
                f"各部分内容：\n{combined}"
            )

        return chat_completion(merge_prompt, self.model)


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
        self, question: str, book_title: str, callback: Callable, model: Optional[str] = None
    ) -> AIProcessThread:
        """
        创建问答线程

        Args:
            question: 问题文本
            book_title: 书籍标题
            callback: 结果回调函数
            model: AI模型名称（可选）

        Returns:
            AIProcessThread实例
        """
        try:
            question = InputValidator.validate_question(question)
            book_title = InputValidator.validate_book_title(book_title)
            thread = AIProcessThread("Q&A", question, book_title, self.stt_model, model)
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
