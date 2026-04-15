"""
ReadEcho Pro - 主程序入口
精简版主程序，整合所有模块
"""

import sys

from PyQt6.QtWidgets import QApplication, QWidget, QInputDialog
from PyQt6.QtCore import QTimer

# 导入自定义模块
from config import (
    WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_X, WINDOW_Y,
    DARK_STYLESHEET, LIGHT_STYLESHEET
)
from utils import format_summary_content, truncate_text
from app_services import create_app_services
from ui_builder import setup_ui, connect_ui_signals
from event_handler import create_event_handler


class ReadEchoPro(QWidget):
    """ReadEcho Pro 主窗口类"""

    def __init__(self):
        super().__init__()

        # 初始化应用服务
        self.services = create_app_services()
        self.fs = self.services.get_sample_rate()

        # UI相关属性
        self.stt_model = None
        self.is_recording = False
        self.last_question = ""

        # 创建事件处理器
        self.handler = create_event_handler(self)

        # 设置UI
        self.initUI()

        # 启动后台预加载模型
        QTimer.singleShot(100, self.preload_whisper)

    def initUI(self):
        """初始化用户界面"""
        # 设置基本UI组件
        setup_ui(self)

        # 连接UI信号到事件处理器
        self._connect_signals()

        # 初始加载书架
        self.handler.refresh_bookshelf()

        # 应用主题
        self.apply_theme()

    def _connect_signals(self):
        """连接UI信号到事件处理器"""
        # 搜索和书籍管理
        self.search_btn.clicked.connect(self.handler.search_books)
        self.add_book_btn.clicked.connect(self.handler.add_new_book)
        self.book_list.itemClicked.connect(self.handler.on_book_selected)

        # AI功能
        self.sum_btn.clicked.connect(self.handler.start_summary)
        self.qa_btn.clicked.connect(self.handler.ask_ai_question)

        # 录音功能
        self.voice_btn.clicked.connect(self.handler.toggle_recording)
        self.view_recording_btn.clicked.connect(self.handler.view_selected_recording)

        # 主题切换
        self.theme_btn.clicked.connect(self.handler.toggle_theme)

    def preload_whisper(self):
        """预加载Whisper模型"""
        self.display.append("<b>[System]:</b> Warm-up 3060 Ti... Loading Whisper Model...")
        self.services.load_whisper_model(self.handler.on_model_ready)

    def apply_theme(self):
        """应用当前主题"""
        self.dark_mode = self.services.get_theme_mode()
        if self.dark_mode:
            self.setStyleSheet(DARK_STYLESHEET)
            self.theme_btn.setText("☀️")
        else:
            self.setStyleSheet(LIGHT_STYLESHEET)
            self.theme_btn.setText("🌙")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = ReadEchoPro()
    win.show()
    sys.exit(app.exec())
