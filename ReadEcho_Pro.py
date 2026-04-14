import sys
import sqlite3
import torch
import whisper
import ollama
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                             QTextEdit, QLineEdit, QLabel, QHBoxLayout,
                             QListWidget, QGroupBox, QInputDialog)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtCore import QTimer

import os
import subprocess

# 替换为你电脑上 ffmpeg.exe 所在的文件夹路径
# 注意：路径里用的是双反斜杠 \\ 或者单斜杠 /
ffmpeg_path = r'E:\ffmpeg-8.1-essentials_build\ffmpeg-8.1-essentials_build\bin'
os.environ["PATH"] += os.pathsep + ffmpeg_path

# --- Database Setup ---
class DBManager:
    def __init__(self):
        self.conn = sqlite3.connect('readecho_v1.db')
        self.cursor = self.conn.cursor()
        # 现有表格：笔记（总结、语音笔记）
        self.cursor.execute('CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, title TEXT, content TEXT, type TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
        # 新表格：书籍
        self.cursor.execute('CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY, title TEXT, author TEXT, added_date DATETIME DEFAULT CURRENT_TIMESTAMP)')
        # 新表格：录音历史（与书籍关联）
        self.cursor.execute('CREATE TABLE IF NOT EXISTS recordings (id INTEGER PRIMARY KEY, book_id INTEGER, file_path TEXT, transcribed_text TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(book_id) REFERENCES books(id))')
        # 新表格：AI问答
        self.cursor.execute('CREATE TABLE IF NOT EXISTS qa (id INTEGER PRIMARY KEY, book_id INTEGER, question TEXT, answer TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(book_id) REFERENCES books(id))')
        self.conn.commit()

    def add_note(self, title, content, note_type="Summary"):
        self.cursor.execute("INSERT INTO notes (title, content, type) VALUES (?, ?, ?)", (title, content, note_type))
        self.conn.commit()

    # 书籍相关方法
    def add_book(self, title, author=""):
        self.cursor.execute("INSERT INTO books (title, author) VALUES (?, ?)", (title, author))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_books(self, search_query=""):
        if search_query:
            self.cursor.execute("SELECT id, title, author FROM books WHERE title LIKE ? OR author LIKE ? ORDER BY added_date DESC",
                               (f"%{search_query}%", f"%{search_query}%"))
        else:
            self.cursor.execute("SELECT id, title, author FROM books ORDER BY added_date DESC")
        return self.cursor.fetchall()

    def get_book_by_title(self, title):
        self.cursor.execute("SELECT id FROM books WHERE title = ?", (title,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    # 录音相关方法
    def add_recording(self, book_id, file_path, transcribed_text):
        self.cursor.execute("INSERT INTO recordings (book_id, file_path, transcribed_text) VALUES (?, ?, ?)",
                           (book_id, file_path, transcribed_text))
        self.conn.commit()

    def get_recordings_by_book(self, book_id):
        self.cursor.execute("SELECT id, file_path, transcribed_text, timestamp FROM recordings WHERE book_id = ? ORDER BY timestamp DESC", (book_id,))
        return self.cursor.fetchall()

    # 问答相关方法
    def add_qa(self, book_id, question, answer):
        self.cursor.execute("INSERT INTO qa (book_id, question, answer) VALUES (?, ?, ?)", (book_id, question, answer))
        self.conn.commit()

class ModelLoaderThread(QThread):
    model_loaded = pyqtSignal(object)

    def run(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        # 用 tiny 模型，快速但精度足够（base太慢）
        model = whisper.load_model("tiny", device=device)
        self.model_loaded.emit(model)

# --- AI Logic Thread (Whisper + Ollama) ---
class RecordingFinishThread(QThread):
    """处理录音完成的后台线程，避免卡UI"""
    recording_ready = pyqtSignal(str)  # 发出音频文件路径
    
    def __init__(self, recording_data, fs, file_path):
        super().__init__()
        self.recording_data = recording_data
        self.fs = fs
        self.file_path = file_path
    
    def run(self):
        try:
            # 立即停止录音，不要等待
            sd.stop()
            
            # 小延迟，确保数据被完全读取
            import time
            time.sleep(0.1)
            
            # 直接保存，不裁剪
            write(self.file_path, self.fs, self.recording_data)
            self.recording_ready.emit(self.file_path)
        except Exception as e:
            err_msg = f"Error: {str(e)}"
            self.recording_ready.emit(err_msg)

class AIProcessThread(QThread):
    result_ready = pyqtSignal(str, str) 

    def __init__(self, action_type, data, book_title, stt_model): # 增加 stt_model 参数
        super().__init__()
        self.action_type = action_type
        self.data = data
        self.book_title = book_title
        self.stt_model = stt_model # 存下来直接用

    def run(self):
        try:
            if self.action_type == "Summarize":
                # --- 这里补上了 Summarize 的逻辑，防止点击总结没反应 ---
                prompt = f"Please provide a detailed summary of the book '{self.data}' in Chinese. Include main plots and key thoughts."
                resp = ollama.chat(model='qwen2.5:7b', messages=[{'role': 'user', 'content': prompt}])
                self.result_ready.emit("Summary", resp['message']['content'])

            elif self.action_type == "VoiceNote":
                if self.stt_model is None:
                    raise Exception("Model not loaded yet! Please wait a moment.")

                # 使用 Whisper 转录音频为文字，不进行 AI 分析
                result = self.stt_model.transcribe(
                    self.data,
                    fp16=torch.cuda.is_available(),
                    beam_size=1
                )
                transcribed_text = result['text']
                self.result_ready.emit("VoiceNote", transcribed_text)

            elif self.action_type == "Q&A":
                # AI问答功能
                question = self.data  # data应该是问题
                prompt = f"关于书籍《{self.book_title}》的问题：{question}\n请用中文详细回答这个问题。"
                resp = ollama.chat(model='qwen2.5:7b', messages=[{'role': 'user', 'content': prompt}])
                self.result_ready.emit("Q&A", resp['message']['content'])

        except Exception as e:
            print(f"[ERROR in AIProcessThread] {str(e)}")
            self.result_ready.emit("Error", str(e))

# --- Main App ---
class ReadEchoPro(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DBManager()
        self.fs = 44100
        self.stt_model = None  # 初始设为空
        self.is_recording = False  # 录音状态标志
        self.recording_data = None  # 保存录音数据
        self.last_question = ""  # 存储最后的问题
        self.initUI()
        
        # 启动后台预加载模型，不卡住 UI
        QTimer.singleShot(100, self.preload_whisper) 

    def preload_whisper(self):
        self.display.append("<b>[System]:</b> Warm-up 3060 Ti... Loading Whisper Model...")
        # 建立一个临时线程只负责加载
        self.load_thread = ModelLoaderThread()
        self.load_thread.model_loaded.connect(self.on_model_ready)
        self.load_thread.start()

    def on_model_ready(self, model):
        self.stt_model = model
        self.display.append("<b>[System]:</b> Whisper Model Ready! GPU Accelerated.")

    def initUI(self):
        self.setWindowTitle('ReadEcho Pro - GPU Accelerated')
        self.setGeometry(300, 300, 900, 700)

        self.dark_mode = True
        self.dark_stylesheet = """
            QWidget { background-color: #2b2b2b; color: #ffffff; font-family: 'Segoe UI'; }
            QTextEdit { background-color: #1e1e1e; border: 1px solid #3c3c3c; border-radius: 5px; padding: 10px; }
            QLineEdit { background-color: #3c3c3c; border: 1px solid #555555; padding: 5px; border-radius: 3px; color: #ffffff; }
            QPushButton { background-color: #0d6efd; border-radius: 5px; padding: 8px; font-weight: bold; color: #ffffff; }
            QPushButton:hover { background-color: #0b5ed7; }
            QPushButton:disabled { background-color: #444444; color: #888888; }
            QListWidget { background-color: #3c3c3c; border: 1px solid #555555; border-radius: 5px; }
            QGroupBox { font-weight: bold; border: 2px solid #555555; border-radius: 5px; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }
        """
        self.light_stylesheet = """
            QWidget { background-color: #f3f4f6; color: #111111; font-family: 'Segoe UI'; }
            QTextEdit { background-color: #ffffff; border: 1px solid #d1d5db; border-radius: 5px; padding: 10px; color: #111111; }
            QLineEdit { background-color: #ffffff; border: 1px solid #9ca3af; padding: 5px; border-radius: 3px; color: #111111; }
            QPushButton { background-color: #2563eb; border-radius: 5px; padding: 8px; font-weight: bold; color: #ffffff; }
            QPushButton:hover { background-color: #1d4ed8; }
            QPushButton:disabled { background-color: #d1d5db; color: #6b7280; }
            QListWidget { background-color: #ffffff; border: 1px solid #d1d5db; border-radius: 5px; }
            QGroupBox { font-weight: bold; border: 2px solid #d1d5db; border-radius: 5px; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }
        """

        # 主布局：左右两栏
        main_layout = QHBoxLayout()

        # 左侧栏：书架和搜索
        left_widget = QWidget()
        left_layout = QVBoxLayout()

        # 搜索框
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search books...")
        self.search_btn = QPushButton("Search")
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        left_layout.addLayout(search_layout)

        # 书架列表
        self.book_list = QListWidget()
        left_layout.addWidget(QLabel("Bookshelf:"))
        left_layout.addWidget(self.book_list)

        # 添加书籍按钮（占位）
        self.add_book_btn = QPushButton("Add New Book")
        left_layout.addWidget(self.add_book_btn)

        left_widget.setLayout(left_layout)
        main_layout.addWidget(left_widget, 1)  # 比例1

        # 右侧栏：操作、总结、录音历史
        right_widget = QWidget()
        right_layout = QVBoxLayout()

        # 书籍信息组
        book_info_group = QGroupBox("Current Book")
        book_info_layout = QVBoxLayout()
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Book title...")
        book_info_layout.addWidget(QLabel("Title:"))
        book_info_layout.addWidget(self.title_input)
        book_info_group.setLayout(book_info_layout)
        right_layout.addWidget(book_info_group)

        # 操作按钮组
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()

        self.sum_btn = QPushButton("Generate Summary")
        self.sum_btn.clicked.connect(self.start_summary)
        actions_layout.addWidget(self.sum_btn)

        self.voice_btn = QPushButton("Start Recording")
        self.voice_btn.clicked.connect(self.toggle_recording)
        actions_layout.addWidget(self.voice_btn)

        # AI问答输入
        qa_layout = QHBoxLayout()
        self.qa_input = QLineEdit()
        self.qa_input.setPlaceholderText("Ask a question about the book...")
        self.qa_btn = QPushButton("Ask AI")
        qa_layout.addWidget(self.qa_input)
        qa_layout.addWidget(self.qa_btn)
        actions_layout.addLayout(qa_layout)

        actions_group.setLayout(actions_layout)
        right_layout.addWidget(actions_group)

        # 总结显示组
        summary_group = QGroupBox("Summary")
        summary_layout = QVBoxLayout()
        self.display = QTextEdit()
        self.display.setReadOnly(True)
        summary_layout.addWidget(self.display)
        summary_group.setLayout(summary_layout)
        right_layout.addWidget(summary_group, 2)  # 比例2，占用更多空间

        # 录音历史组
        history_group = QGroupBox("Recording History")
        history_layout = QVBoxLayout()
        self.recording_list = QListWidget()
        history_layout.addWidget(self.recording_list)
        self.view_recording_btn = QPushButton("View Selected Recording")
        history_layout.addWidget(self.view_recording_btn)
        history_group.setLayout(history_layout)
        right_layout.addWidget(history_group, 1)  # 比例1

        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget, 2)  # 比例2，右侧更宽

        # 主题切换小按钮（右上角）
        self.theme_btn = QPushButton()  # 文本稍后设置
        self.theme_btn.setFixedSize(40, 40)
        self.theme_btn.clicked.connect(self.toggle_theme)

        # 需要将主题按钮放在右上角，使用覆盖布局或添加到主布局
        # 简单方法：创建一个容器widget，将主题按钮放在布局的右上角
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)

        # 顶部放置主题按钮（右对齐）
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        top_bar.addWidget(self.theme_btn)
        container_layout.addLayout(top_bar)

        # 添加主布局
        container_layout.addLayout(main_layout)
        container.setLayout(container_layout)

        self.setLayout(container_layout)

        # 连接新功能信号
        self.search_btn.clicked.connect(self.search_books)
        self.add_book_btn.clicked.connect(self.add_new_book)
        self.book_list.itemClicked.connect(self.on_book_selected)
        self.qa_btn.clicked.connect(self.ask_ai_question)
        self.view_recording_btn.clicked.connect(self.view_selected_recording)

        # 初始加载书架
        self.refresh_bookshelf()

        self.apply_theme()

    def refresh_bookshelf(self, search_query=""):
        """刷新书架列表"""
        self.book_list.clear()
        books = self.db.get_books(search_query)
        for book_id, title, author in books:
            item_text = f"{title}"
            if author:
                item_text += f" - {author}"
            self.book_list.addItem(item_text)
            # 存储book_id作为item的数据
            item = self.book_list.item(self.book_list.count() - 1)
            item.setData(256, book_id)  # 256是Qt.UserRole

    def search_books(self):
        """搜索书籍"""
        query = self.search_input.text()
        self.refresh_bookshelf(query)

    def add_new_book(self):
        """添加新书籍"""
        title, ok = QInputDialog.getText(self, "Add New Book", "Enter book title:")
        if ok and title:
            author, ok2 = QInputDialog.getText(self, "Add New Book", "Enter author (optional):")
            author = author if ok2 else ""
            self.db.add_book(title, author)
            self.refresh_bookshelf()
            self.display.append(f"<b>[System]:</b> Added book '{title}' to bookshelf.")

    def on_book_selected(self, item):
        """当选择书籍时"""
        book_id = item.data(256)
        if book_id:
            # 这里可以加载书籍的详细信息、录音历史等
            # 暂时只设置标题输入框
            title = item.text().split(" - ")[0]  # 移除作者部分
            self.title_input.setText(title)
            # 加载录音历史
            self.load_recordings_for_book(book_id)

    def load_recordings_for_book(self, book_id):
        """加载指定书籍的录音历史"""
        self.recording_list.clear()
        recordings = self.db.get_recordings_by_book(book_id)
        for rec_id, file_path, text, timestamp in recordings:
            # 截断过长的文本
            display_text = text[:50] + "..." if len(text) > 50 else text
            item_text = f"{timestamp}: {display_text}"
            self.recording_list.addItem(item_text)
            item = self.recording_list.item(self.recording_list.count() - 1)
            item.setData(256, rec_id)  # 存储recording_id

    def ask_ai_question(self):
        """询问AI关于书籍的问题"""
        title = self.title_input.text()
        question = self.qa_input.text()
        if not title:
            self.display.append("<b>[System]:</b> Please select or enter a book title first.")
            return
        if not question:
            self.display.append("<b>[System]:</b> Please enter a question.")
            return

        # 存储问题以便后续使用
        self.last_question = question

        # 禁用按钮，显示处理中
        self.qa_btn.setEnabled(False)
        self.qa_btn.setText("Processing...")
        self.display.append(f"<b>[AI Q&A]:</b> Question about '{title}': {question}")

        # 启动AI处理线程
        self.thread = AIProcessThread("Q&A", question, title, self.stt_model)
        self.thread.result_ready.connect(self.on_qa_finished)
        self.thread.start()

        self.qa_input.clear()

    def view_selected_recording(self):
        """查看选中的录音"""
        selected_items = self.recording_list.selectedItems()
        if not selected_items:
            return
        item = selected_items[0]
        rec_id = item.data(256)
        if rec_id:
            # 这里应该显示完整的录音文本
            # 暂时显示占位信息
            self.display.append(f"<b>[Recording View]:</b> Selected recording ID: {rec_id}")
            self.display.append("<i>录音查看功能正在开发中...</i>")

    def start_summary(self):
        title = self.title_input.text()
        if not title: return
        self.sum_btn.setEnabled(False)
        # 修正点：末尾加上 self.stt_model
        self.thread = AIProcessThread("Summarize", title, title, self.stt_model)
        self.thread.result_ready.connect(self.on_finished)
        self.thread.start()

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self):
        if self.dark_mode:
            self.setStyleSheet(self.dark_stylesheet)
            self.theme_btn.setText("☀️")  # 深色模式显示太阳（切换到浅色）
        else:
            self.setStyleSheet(self.light_stylesheet)
            self.theme_btn.setText("🌙")  # 浅色模式显示月亮（切换到深色）

    def toggle_recording(self):
        """切换录音状态：开始 or 结束"""
        if not self.is_recording:
            self.begin_recording()
        else:
            self.stop_recording()

    def begin_recording(self):
        """开始录音"""
        title = self.title_input.text()
        if not title: 
            self.display.append("<b>[System]:</b> Please enter a book title first.")
            return
        
        self.is_recording = True
        self.voice_btn.setText("Stop Recording")
        self.voice_btn.setStyleSheet("""
            QPushButton { background-color: #dc3545; border-radius: 5px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #c82333; }
        """)
        self.display.append("<b>[System]:</b> Recording started... Press 'Stop Recording' to finish.")
        
        # 改成预分配较小缓冲（30秒）而不是300秒，避免 sd.wait() 过长
        self.recording_data = sd.rec(int(30 * self.fs), samplerate=self.fs, channels=1, dtype=np.float32)

    def stop_recording(self):
        """结束录音"""
        self.is_recording = False
        self.voice_btn.setText("Saving...")
        self.voice_btn.setEnabled(False)
        
        # 在后台线程处理录音完成，不卡UI
        self.finish_thread = RecordingFinishThread(self.recording_data, self.fs, "temp_note.wav")
        self.finish_thread.recording_ready.connect(self.on_recording_saved)
        self.finish_thread.start()

    def on_recording_saved(self, file_path):
        """录音文件保存完成后的回调"""
        if file_path.startswith("Error"):
            self.display.append(f"<b>[System]:</b> ❌ {file_path}")
            self.voice_btn.setEnabled(True)
            self.voice_btn.setText("Start Recording")
            return
        
        self.voice_btn.setText("Transcribing...")
        
        # 启动 AI 处理线程进行转录
        self.thread = AIProcessThread("VoiceNote", file_path, self.title_input.text(), self.stt_model)
        self.thread.result_ready.connect(self.on_finished)
        self.thread.start()

    def format_summary_content(self, content):
        """格式化总结内容，使其更有条理"""
        # 如果内容已经是HTML格式，直接返回
        if "<" in content and ">" in content:
            return content

        # 简单的格式化规则：
        # 1. 将"1."、"2."等数字列表转换为有序列表
        # 2. 将"- "、"* "等转换为无序列表
        # 3. 将段落分隔开
        lines = content.split('\n')
        formatted_lines = []
        in_list = False
        list_type = None  # "ol" 或 "ul"

        for line in lines:
            line = line.strip()
            if not line:
                if in_list:
                    formatted_lines.append("</li></ul>" if list_type == "ul" else "</li></ol>")
                    in_list = False
                    list_type = None
                formatted_lines.append("<p></p>")
                continue

            # 检查是否是有序列表项
            if line[:2] in ["1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9."] or line[:3] in ["10.", "11.", "12.", "13.", "14.", "15."]:
                if not in_list or list_type != "ol":
                    if in_list:
                        formatted_lines.append("</li></ul>" if list_type == "ul" else "</li></ol>")
                    formatted_lines.append("<ol>")
                    in_list = True
                    list_type = "ol"
                item_text = line[line.find('.')+1:].strip()
                formatted_lines.append(f"<li>{item_text}</li>")
            # 检查是否是无序列表项
            elif line[:2] in ["- ", "* ", "• "]:
                if not in_list or list_type != "ul":
                    if in_list:
                        formatted_lines.append("</li></ul>" if list_type == "ul" else "</li></ol>")
                    formatted_lines.append("<ul>")
                    in_list = True
                    list_type = "ul"
                item_text = line[2:].strip()
                formatted_lines.append(f"<li>{item_text}</li>")
            else:
                if in_list:
                    formatted_lines.append("</li></ul>" if list_type == "ul" else "</li></ol>")
                    in_list = False
                    list_type = None
                # 普通段落
                formatted_lines.append(f"<p>{line}</p>")

        # 关闭最后一个列表
        if in_list:
            formatted_lines.append("</li></ul>" if list_type == "ul" else "</li></ol>")

        return ''.join(formatted_lines)

    def on_finished(self, note_type, content):
        title = self.title_input.text()

        # 格式化内容
        if note_type == "Summary":
            formatted_content = self.format_summary_content(content)
            self.display.append(f"<h3>📚 {note_type} - {title}</h3>")
            self.display.append(formatted_content)
            self.display.append("<hr>")
        else:
            self.display.append(f"<b>[{note_type}]:</b>\n{content}\n")

        if note_type == "VoiceNote":
            # 获取或创建书籍
            book_id = self.db.get_book_by_title(title)
            if book_id is None:
                # 书籍不存在，创建它
                book_id = self.db.add_book(title, "")

            # 添加录音记录到数据库（暂时使用固定文件路径，实际应该使用录音文件路径）
            file_path = "temp_note.wav"  # 实际的录音文件路径
            self.db.add_recording(book_id, file_path, content)

            # 刷新录音历史列表
            if book_id:
                self.load_recordings_for_book(book_id)

            # 也添加到notes表保持兼容性
            self.db.add_note(title, content, note_type)
        else:
            # 其他类型的笔记（如Summary）
            self.db.add_note(title, content, note_type)

        self.sum_btn.setEnabled(True)
        self.voice_btn.setEnabled(True)
        self.voice_btn.setText("Start Recording")
        self.voice_btn.setStyleSheet("")
        self.apply_theme()

    def on_qa_finished(self, note_type, content):
        """处理问答完成的结果"""
        if note_type == "Error":
            self.display.append(f"<b>[Error]:</b> {content}")
            self.qa_btn.setEnabled(True)
            self.qa_btn.setText("Ask AI")
            return

        title = self.title_input.text()

        # 显示问答结果
        self.display.append(f"<h3>❓ Q&A - {title}</h3>")
        self.display.append(f"<div style='background-color: #3c3c3c; padding: 10px; border-radius: 5px; margin: 5px 0;'><b>Question:</b> {self.last_question}</div>")
        self.display.append(f"<div style='background-color: #2d3748; padding: 10px; border-radius: 5px; margin: 10px 0;'><b>Answer:</b> {content}</div>")
        self.display.append("<hr>")

        # 保存到数据库
        book_id = self.db.get_book_by_title(title)
        if book_id is None:
            book_id = self.db.add_book(title, "")

        # 存储问题和答案到数据库
        self.db.add_qa(book_id, self.last_question, content)

        # 重新启用按钮
        self.qa_btn.setEnabled(True)
        self.qa_btn.setText("Ask AI")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = ReadEchoPro()
    win.show()
    sys.exit(app.exec())
