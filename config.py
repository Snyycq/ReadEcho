"""
ReadEcho Pro 配置文件
包含应用程序的配置参数、样式表和常量
"""

import os

# --- FFMPEG 配置 ---
# 替换为你电脑上 ffmpeg.exe 所在的文件夹路径
# 注意：路径里用的是双反斜杠 \\ 或者单斜杠 /
FFMPEG_PATH = r'E:\ffmpeg-8.1-essentials_build\ffmpeg-8.1-essentials_build\bin'

# 将ffmpeg路径添加到系统PATH
if FFMPEG_PATH not in os.environ.get('PATH', ''):
    os.environ['PATH'] += os.pathsep + FFMPEG_PATH

# --- 应用程序常量 ---
SAMPLE_RATE = 44100  # 音频采样率
RECORDING_DURATION = 30  # 录音时长（秒）
DATABASE_FILE = 'readecho_v1.db'
TEMP_AUDIO_FILE = 'temp_note.wav'

# --- 样式表 ---
# 深色模式样式
DARK_STYLESHEET = """
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

# 浅色模式样式
LIGHT_STYLESHEET = """
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

# --- AI 配置 ---
WHISPER_MODEL = "tiny"  # Whisper模型大小
OLLAMA_MODEL = "qwen2.5:7b"  # Ollama模型

# --- 窗口配置 ---
WINDOW_TITLE = 'ReadEcho Pro - GPU Accelerated'
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700
WINDOW_X = 300
WINDOW_Y = 300