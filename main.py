"""
ReadEcho Pro - 主程序入口
GPU加速阅读助手的主应用程序

新布局：
- 左侧：书架 + 笔记本
- 中间：笔记详情 + 添加笔记
- 右侧：AI对话 + 提问
"""

import sys
from typing import Optional

from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QMessageBox,
    QPushButton,
    QListWidget,
    QTextEdit,
    QLineEdit,
)
from PyQt6.QtCore import Qt, QTimer

# 导入自定义模块
from config import (
    WINDOW_TITLE,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_X,
    WINDOW_Y,
    STYLESHEET,
    LOGGER,
)
from app_services import create_app_services
from ui_builder import setup_ui
from event_handler import create_event_handler


class ReadEchoPro(QWidget):
    """ReadEcho Pro 主窗口类

    管理应用程序的主窗口和协调各个模块之间的交互
    """

    # UI 控件声明，用于 VS Code 类型检查
    book_list: "QListWidget"
    notes_list: "QListWidget"
    add_book_btn: "QPushButton"
    title_display: "QLineEdit"
    note_display: "QTextEdit"
    note_text_input: "QLineEdit"
    add_note_btn: "QPushButton"
    voice_note_btn: "QPushButton"
    ai_chat_display: "QTextEdit"
    ai_question_input: "QLineEdit"
    ask_ai_btn: "QPushButton"
    voice_ask_btn: "QPushButton"
    save_note_btn: "QPushButton"

    def __init__(self):
        """初始化ReadEcho Pro主应用程序"""
        super().__init__()

        try:
            LOGGER.info("=" * 50)
            LOGGER.info("ReadEcho Pro 应用启动")
            LOGGER.info("=" * 50)

            # 初始化应用服务
            self.services = create_app_services()
            if not self.services:
                raise RuntimeError("应用服务初始化失败")

            self.fs = self.services.get_sample_rate()
            LOGGER.debug(f"采样率: {self.fs} Hz")

            # UI相关属性
            self.stt_model: Optional[object] = None
            self.is_recording: bool = False
            self.last_question: str = ""

            # 创建事件处理器
            self.handler = create_event_handler(self)
            if not self.handler:
                raise RuntimeError("事件处理器创建失败")

            # 设置UI
            self.initUI()

            # 设置窗口属性
            self.setWindowTitle(WINDOW_TITLE)
            self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
            self.move(WINDOW_X, WINDOW_Y)

            # 启动后台预加载模型（延迟以避免UI阻塞）
            QTimer.singleShot(500, self.preload_whisper)

            LOGGER.info("应用初始化完成")
        except Exception as e:
            error_msg = f"应用初始化失败: {str(e)}"
            LOGGER.error(error_msg, exc_info=True)
            QMessageBox.critical(None, "初始化错误", error_msg)
            sys.exit(1)

    def initUI(self) -> None:
        """初始化用户界面"""
        try:
            LOGGER.debug("开始构建UI...")

            # 设置基本UI组件
            setup_ui(self)

            # 连接UI信号到事件处理器
            self._connect_signals()

            # 初始加载书架
            self.handler.refresh_bookshelf()

            # 应用主题
            self.apply_theme()

            LOGGER.debug("UI构建完成")
        except Exception as e:
            error_msg = f"UI初始化失败: {str(e)}"
            LOGGER.error(error_msg, exc_info=True)
            raise

    def _connect_signals(self) -> None:
        """连接UI信号到事件处理器"""
        try:
            # 书籍管理
            self.book_list.itemClicked.connect(self.handler.on_book_selected)
            self.add_book_btn.clicked.connect(self.handler.show_add_book_dialog)

            # 笔记管理
            self.notes_list.itemClicked.connect(self.handler.on_note_selected)
            self.add_note_btn.clicked.connect(self.handler.add_text_note)
            self.voice_note_btn.clicked.connect(self.handler.toggle_voice_note)
            self.save_note_btn.clicked.connect(self.handler.save_note_edit)

            # AI提问
            self.ask_ai_btn.clicked.connect(self.handler.ask_ai_text_question)
            self.voice_ask_btn.clicked.connect(self.handler.ask_ai_voice_question)

            # 书籍右键菜单
            self.book_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.book_list.customContextMenuRequested.connect(self.handler.show_book_context_menu)

            # 笔记右键菜单
            self.notes_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.notes_list.customContextMenuRequested.connect(self.handler.show_note_context_menu)

            LOGGER.debug("UI信号连接完成")
        except Exception as e:
            error_msg = f"信号连接失败: {str(e)}"
            LOGGER.error(error_msg)
            raise

    def preload_whisper(self) -> None:
        """异步预加载Whisper模型"""
        try:
            LOGGER.info("开始预加载Whisper模型...")
            if hasattr(self, "ai_chat_display"):
                self.ai_chat_display.append("<b>[系统]:</b> 正在加载Whisper模型...")
            self.services.load_whisper_model(self.handler.on_model_ready)
        except Exception as e:
            error_msg = f"模型预加载失败: {str(e)}"
            LOGGER.error(error_msg)
            if hasattr(self, "ai_chat_display"):
                self.ai_chat_display.append(f"<b>[错误]:</b> {error_msg}")

    def apply_theme(self) -> None:
        """应用暗色主题"""
        try:
            self.setStyleSheet(STYLESHEET)
            if hasattr(self, "ai_chat_display"):
                self.ai_chat_display.document().setDefaultStyleSheet(
                    "body { color: #ffffff; background-color: transparent; }"
                    "p, span, div, pre, h1, h2, h3, h4, h5, h6 { color: #ffffff; }"
                )
                current_html = self.ai_chat_display.toHtml()
                self.ai_chat_display.setHtml(current_html)
            LOGGER.debug("已应用暗色主题")
        except Exception as e:
            LOGGER.error(f"主题应用失败: {str(e)}")

    def closeEvent(self, a0: Optional[QCloseEvent] = None) -> None:
        """应用关闭事件处理"""
        event = a0
        try:
            LOGGER.info("应用正在关闭...")

            # 清理资源
            if hasattr(self, "handler") and self.handler:
                self.handler.cleanup()

            if hasattr(self, "services") and self.services:
                self.services.cleanup()

            if event is not None:
                event.accept()
            LOGGER.info("应用已安全关闭")
        except Exception as e:
            LOGGER.error(f"关闭时出错: {str(e)}")
            if event is not None:
                event.accept()


def main() -> None:
    """应用程序入口点"""
    try:
        LOGGER.info(f"正在启动 {WINDOW_TITLE}...")

        app = QApplication(sys.argv)
        win = ReadEchoPro()
        win.show()

        LOGGER.info("应用窗口已显示")
        sys.exit(app.exec())
    except Exception as e:
        error_msg = f"应用启动失败: {str(e)}"
        LOGGER.critical(error_msg, exc_info=True)
        print(error_msg)
        sys.exit(1)


if __name__ == "__main__":
    main()
