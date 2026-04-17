"""
ReadEcho Pro UI构建模块
负责创建和设置应用程序的用户界面组件
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLineEdit, QLabel, QListWidget, QGroupBox
)
from PyQt6.QtCore import Qt
from config import WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_X, WINDOW_Y


def create_main_window(widget):
    """
    设置主窗口的基本属性

    Args:
        widget: ReadEchoPro实例（QWidget子类）
    """
    widget.setWindowTitle(WINDOW_TITLE)
    widget.setGeometry(WINDOW_X, WINDOW_Y, WINDOW_WIDTH, WINDOW_HEIGHT)
    widget.dark_mode = True


def create_theme_button(widget):
    """
    创建主题切换按钮

    Args:
        widget: ReadEchoPro实例

    Returns:
        QPushButton: 主题按钮
    """
    theme_btn = QPushButton()
    theme_btn.setFixedSize(40, 40)
    # 信号连接由 main.py 的 _connect_signals 统一处理
    return theme_btn


def create_left_panel(widget):
    """
    创建左侧面板（书架和搜索）

    Args:
        widget: ReadEchoPro实例

    Returns:
        dict: 包含左侧面板控件和布局的字典
    """
    # 左侧栏：书架和搜索
    left_widget = QWidget()
    left_layout = QVBoxLayout()

    # 搜索框
    search_layout = QHBoxLayout()
    widget.search_input = QLineEdit()
    widget.search_input.setPlaceholderText("Search online books...")
    widget.search_btn = QPushButton("Search")
    search_layout.addWidget(widget.search_input)
    search_layout.addWidget(widget.search_btn)
    left_layout.addLayout(search_layout)

    # 书架列表
    widget.book_list = QListWidget()
    left_layout.addWidget(QLabel("Bookshelf:"))
    left_layout.addWidget(widget.book_list)

    # 添加书籍按钮
    widget.add_book_btn = QPushButton("Import Selected Book")
    left_layout.addWidget(widget.add_book_btn)

    # 删除书籍按钮
    widget.delete_book_btn = QPushButton("Delete Selected Book")
    widget.delete_book_btn.setProperty('class', 'danger')
    left_layout.addWidget(widget.delete_book_btn)

    left_widget.setLayout(left_layout)

    return {
        'widget': left_widget,
        'layout': left_layout,
        'weight': 1
    }


def create_center_panel(widget):
    """
    创建中间面板（当前书籍、操作和录音历史）

    Args:
        widget: ReadEchoPro实例

    Returns:
        dict: 包含中间面板控件和布局的字典
    """
    center_widget = QWidget()
    center_layout = QVBoxLayout()

    # 书籍信息组
    book_info_group = QGroupBox("Current Book")
    book_info_layout = QVBoxLayout()
    widget.title_input = QLineEdit()
    widget.title_input.setPlaceholderText("Book title...")
    book_info_layout.addWidget(QLabel("Title:"))
    book_info_layout.addWidget(widget.title_input)
    book_info_group.setLayout(book_info_layout)
    center_layout.addWidget(book_info_group)

    # 操作按钮组
    actions_group = QGroupBox("Actions")
    actions_layout = QVBoxLayout()

    widget.voice_btn = QPushButton("Start Recording")
    widget.voice_btn.setFixedHeight(36)
    widget.voice_btn.setStyleSheet("font-weight: bold; padding: 6px;")
    actions_layout.addWidget(widget.voice_btn)

    qa_layout = QHBoxLayout()
    widget.qa_input = QLineEdit()
    widget.qa_input.setPlaceholderText("Ask a question about the book...")
    widget.qa_btn = QPushButton("Ask AI")
    widget.qa_btn.setFixedHeight(32)
    qa_layout.addWidget(widget.qa_input)
    qa_layout.addWidget(widget.qa_btn)
    actions_layout.addLayout(qa_layout)

    actions_group.setLayout(actions_layout)
    center_layout.addWidget(actions_group)

    # 录音历史组
    history_group = QGroupBox("Recording History")
    history_layout = QVBoxLayout()
    widget.recording_list = QListWidget()
    widget.recording_list.setMinimumHeight(180)
    history_layout.addWidget(widget.recording_list)

    btn_layout = QHBoxLayout()
    widget.view_recording_btn = QPushButton("View")
    widget.edit_recording_btn = QPushButton("Edit")
    widget.delete_recording_btn = QPushButton("Delete")

    for btn in (widget.view_recording_btn, widget.edit_recording_btn, widget.delete_recording_btn):
        btn.setFixedHeight(30)
        btn.setFixedWidth(100)
        btn_layout.addWidget(btn)

    widget.delete_recording_btn.setProperty('class', 'danger')
    history_layout.addLayout(btn_layout)

    history_group.setLayout(history_layout)
    center_layout.addWidget(history_group)

    center_widget.setLayout(center_layout)

    return {
        'widget': center_widget,
        'layout': center_layout,
        'weight': 2
    }


def create_notes_panel(widget):
    """
    创建右侧Notes输出面板

    Args:
        widget: ReadEchoPro实例

    Returns:
        dict: 包含Notes面板控件和布局的字典
    """
    notes_widget = QWidget()
    notes_layout = QVBoxLayout()

    notes_group = QGroupBox("Terminal")
    notes_group_layout = QVBoxLayout()
    widget.display = QTextEdit()
    widget.display.setReadOnly(True)
    widget.display.setMinimumHeight(260)
    # 固定终端样式：黑色背景、白色文字、固定边框
    widget.display.setStyleSheet("""
        QTextEdit {
            background-color: #000000;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 5px;
            padding: 10px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
        }
    """)
    notes_group_layout.addWidget(widget.display)

    notes_group_layout.addWidget(QLabel("Search Results:"))
    widget.search_results_list = QListWidget()
    widget.search_results_list.setMinimumHeight(150)
    notes_group_layout.addWidget(widget.search_results_list)

    notes_group.setLayout(notes_group_layout)

    notes_layout.addWidget(notes_group)
    notes_widget.setLayout(notes_layout)

    return {
        'widget': notes_widget,
        'layout': notes_layout,
        'weight': 2
    }


def create_container_layout(main_layout, theme_btn):
    """
    创建容器布局，包含主题按钮和主布局

    Args:
        main_layout: 主水平布局
        theme_btn: 主题切换按钮

    Returns:
        QVBoxLayout: 容器布局
    """
    container_layout = QVBoxLayout()
    container_layout.setContentsMargins(0, 0, 0, 0)

    # 顶部放置主题按钮（右对齐）
    top_bar = QHBoxLayout()
    top_bar.addStretch()
    top_bar.addWidget(theme_btn)
    container_layout.addLayout(top_bar)

    # 添加主布局
    container_layout.addLayout(main_layout)

    return container_layout


def setup_ui(widget):
    """
    设置完整的用户界面

    Args:
        widget: ReadEchoPro实例
    """
    # 设置窗口基本属性
    create_main_window(widget)

    # 创建主题按钮
    widget.theme_btn = create_theme_button(widget)

    # 创建主布局
    main_layout = QHBoxLayout()

    # 创建左侧面板
    left_panel = create_left_panel(widget)
    main_layout.addWidget(left_panel['widget'], left_panel['weight'])

    # 创建中间面板（书籍/操作/录音历史）
    center_panel = create_center_panel(widget)
    main_layout.addWidget(center_panel['widget'], center_panel['weight'])

    # 创建右侧Notes输出面板
    notes_panel = create_notes_panel(widget)
    main_layout.addWidget(notes_panel['widget'], notes_panel['weight'])

    # 创建容器布局（包含主题按钮）
    container_layout = create_container_layout(main_layout, widget.theme_btn)

    # 设置主窗口布局
    widget.setLayout(container_layout)

    return widget


def connect_ui_signals(widget):
    """
    连接UI控件的信号

    Args:
        widget: ReadEchoPro实例
    """
    # 连接新功能信号
    widget.search_btn.clicked.connect(widget.search_books)
    widget.add_book_btn.clicked.connect(widget.import_selected_book)
    widget.delete_book_btn.clicked.connect(widget.delete_selected_book)
    widget.book_list.itemClicked.connect(widget.on_book_selected)
    widget.search_results_list.itemClicked.connect(widget.on_search_result_selected)
    widget.qa_btn.clicked.connect(widget.ask_ai_question)
    widget.view_recording_btn.clicked.connect(widget.view_selected_recording)
    widget.edit_recording_btn.clicked.connect(widget.edit_selected_recording)
    widget.delete_recording_btn.clicked.connect(widget.delete_selected_recording)