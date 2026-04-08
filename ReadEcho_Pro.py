import sys
"""
ReadEcho Pro - GPU Accelerated Reading Assistant
功能描述：
这是一个基于PyQt6的桌面应用程序，集成了OpenAI Whisper语音识别和Ollama大语言模型，
用于辅助阅读和笔记记录。
主要功能模块：
1. 数据库管理 (DBManager)
    - 使用SQLite存储笔记
    - 支持保存笔记标题、内容和类型
2. 模型加载线程 (ModelLoaderThread)
    - 在后台预加载Whisper模型
    - 支持GPU加速（CUDA）
3. AI处理线程 (AIProcessThread)
    - 生成摘要：根据书籍标题调用Ollama生成中文摘要
    - 语音笔记：使用Whisper进行语音转文本，再用Ollama优化文本质量
4. 主应用窗口 (ReadEchoPro)
    - 书籍标题输入框
    - 内容显示区域
    - 生成摘要按钮：输入书名自动生成摘要
    - 录音按钮：录制10秒音频，自动转录并生成读书笔记
核心特性：
- GPU加速（支持NVIDIA CUDA）
- 异步处理，不阻塞UI
- 深色主题界面
- 自动保存笔记到数据库
"""
import sqlite3
import torch
import whisper
import ollama
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QTextEdit, QLineEdit, QLabel, QHBoxLayout)
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
        self.cursor.execute('CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, title TEXT, content TEXT, type TEXT)')
        self.conn.commit()

    def add_note(self, title, content, note_type="Summary"):
        self.cursor.execute("INSERT INTO notes (title, content, type) VALUES (?, ?, ?)", (title, content, note_type))
        self.conn.commit()

class ModelLoaderThread(QThread):
    model_loaded = pyqtSignal(object)

    def run(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        # 提前加载好
        model = whisper.load_model("base", device=device)
        self.model_loaded.emit(model)

# --- AI Logic Thread (Whisper + Ollama) ---
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
                
                print("--- GPU Transcribing (Fast Mode) ---")
                # 修正点：使用 self.stt_model
                result = self.stt_model.transcribe(
                    self.data, 
                    fp16=torch.cuda.is_available(), 
                    beam_size=1
                )
                raw_text = result['text']
                
                print("--- Refining Text with Ollama ---")
                prompt = f"The user is reading '{self.book_title}'. Below is a messy voice transcript. Please clean it up and organize it into professional Chinese reading notes: {raw_text}"
                resp = ollama.chat(model='qwen2.5:7b', messages=[{'role': 'user', 'content': prompt}])
                self.result_ready.emit("VoiceNote", resp['message']['content'])
                
        except Exception as e:
            self.result_ready.emit("Error", str(e))

# --- Main App ---
class ReadEchoPro(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DBManager()
        self.fs = 44100
        self.stt_model = None  # 初始设为空
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
        self.setGeometry(300, 300, 700, 600)
        layout = QVBoxLayout()

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Current Book Title...")
        layout.addWidget(QLabel("Book Title:"))
        layout.addWidget(self.title_input)

        self.display = QTextEdit()
        self.display.setReadOnly(True)
        layout.addWidget(self.display)

        btn_layout = QHBoxLayout()
        self.sum_btn = QPushButton("Generate Summary")
        self.sum_btn.clicked.connect(self.start_summary)
        
        self.voice_btn = QPushButton("Hold to Record (10s Test)")
        # For simplicity in this version, we use a fixed 10s recording
        # Later we can upgrade to true "Hold to Record"
        self.voice_btn.clicked.connect(self.start_voice_note)
        
        btn_layout.addWidget(self.sum_btn)
        btn_layout.addWidget(self.voice_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #ffffff; font-family: 'Segoe UI'; }
            QTextEdit { background-color: #1e1e1e; border: 1px solid #3c3c3c; border-radius: 5px; padding: 10px; }
            QLineEdit { background-color: #3c3c3c; border: 1px solid #555555; padding: 5px; border-radius: 3px; }
            QPushButton { background-color: #0d6efd; border-radius: 5px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #0b5ed7; }
            QPushButton:disabled { background-color: #444444; color: #888888; }
        """)

    def start_summary(self):
        title = self.title_input.text()
        if not title: return
        self.sum_btn.setEnabled(False)
        # 修正点：末尾加上 self.stt_model
        self.thread = AIProcessThread("Summarize", title, title, self.stt_model)
        self.thread.result_ready.connect(self.on_finished)
        self.thread.start()

    def start_voice_note(self):
        title = self.title_input.text()
        if not title: 
            self.display.append("<b>[System]:</b> Please enter a book title first.")
            return
            
        self.voice_btn.setEnabled(False)
        self.remaining_time = 10
        
        # 录音：使用 sd.rec 开启录音
        self.recording_data = sd.rec(int(10 * self.fs), samplerate=self.fs, channels=1)
        
        # 定时器逻辑
        if hasattr(self, 'timer'): self.timer.stop() # 如果有旧的定时器，先停掉
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)
        self.update_countdown()

    def update_countdown(self):
        if self.remaining_time > 0:
            self.voice_btn.setText(f"Recording... {self.remaining_time}s")
            self.remaining_time -= 1
        else:
            self.timer.stop()
            self.finish_recording()

    def finish_recording(self):
        sd.wait() # 确保录音完成
        # 3. 覆盖写入旧音频文件
        write("temp_note.wav", self.fs, self.recording_data)
        
        self.voice_btn.setText("AI Processing...")
        # 4. 启动 AI 处理线程
        # 传入 self.stt_model
        self.thread = AIProcessThread("VoiceNote", "temp_note.wav", self.title_input.text(), self.stt_model)
        self.thread.result_ready.connect(self.on_finished)
        self.thread.start()

    def on_finished(self, note_type, content):
        self.display.append(f"<b>[{note_type}]:</b>\n{content}\n")
        self.db.add_note(self.title_input.text(), content, note_type)
        self.sum_btn.setEnabled(True)
        self.voice_btn.setEnabled(True)
        self.voice_btn.setText("Hold to Record (10s Test)")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = ReadEchoPro()
    win.show()
    sys.exit(app.exec())
