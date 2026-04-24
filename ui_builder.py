"""
ReadEcho Pro UI构建模块
负责创建和设置应用程序的用户界面组件

新布局：
- 左侧：上半书架，下半笔记本（选中书籍的笔记列表）
- 中间：选中的笔记详情 + 语音/手动输入笔记
- 右侧：AI对话框 + 语音/手动问AI
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLineEdit,
    QLabel,
    QListWidget,
    QGroupBox,
    QSplitter,
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


def create_left_panel(widget):
    """
    创建左侧面板（上半书架 + 下半笔记本）

    Args:
        widget: ReadEchoPro实例

    Returns:
        dict: 包含左侧面板控件和布局的字典
    """
    left_widget = QWidget()
    left_layout = QVBoxLayout()

    # 上半部分：书架
    left_layout.addWidget(QLabel("📚 书架"))
    widget.book_list = QListWidget()
    left_layout.addWidget(widget.book_list, 1)

    # 添加书籍按钮
    widget.add_book_btn = QPushButton("➕ 添加书籍")
    widget.add_book_btn.setFixedHeight(32)
    left_layout.addWidget(widget.add_book_btn)

    # 下半部分：笔记本（选中书籍的笔记列表）
    left_layout.addWidget(QLabel("📝 笔记本"))
    widget.notes_list = QListWidget()
    left_layout.addWidget(widget.notes_list, 1)

    left_widget.setLayout(left_layout)

    return {"widget": left_widget, "layout": left_layout, "weight": 1}


def create_center_panel(widget):
    """
    创建中间面板（选中笔记详情 + 输入笔记）

    Args:
        widget: ReadEchoPro实例

    Returns:
        dict: 包含中间面板控件和布局的字典
    """
    center_widget = QWidget()
    center_layout = QVBoxLayout()

    # 书名显示
    title_layout = QHBoxLayout()
    widget.title_display = QLineEdit()
    widget.title_display.setReadOnly(True)
    widget.title_display.setPlaceholderText("请从书架选择书籍")
    widget.title_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title_layout.addWidget(widget.title_display)
    center_layout.addLayout(title_layout)

    # 笔记详情显示区域
    note_group = QGroupBox("📝 笔记详情")
    note_group_layout = QVBoxLayout()
    widget.note_display = QTextEdit()
    widget.note_display.setPlaceholderText("选中笔记后可直接编辑...")
    note_group_layout.addWidget(widget.note_display)
    # 保存编辑按钮
    widget.save_note_btn = QPushButton("💾 保存编辑")
    widget.save_note_btn.setFixedHeight(28)
    widget.save_note_btn.setVisible(False)
    note_group_layout.addWidget(widget.save_note_btn)
    note_group.setLayout(note_group_layout)
    center_layout.addWidget(note_group, 3)

    # 添加笔记区域
    add_note_group = QGroupBox("✏️ 添加笔记")
    add_note_layout = QVBoxLayout()

    # 手动输入笔记（输入框 + 语音按钮 + 添加按钮）
    text_input_layout = QHBoxLayout()
    widget.note_text_input = QLineEdit()
    widget.note_text_input.setPlaceholderText("输入笔记内容...")
    text_input_layout.addWidget(widget.note_text_input)
    widget.voice_note_btn = QPushButton("🎤")
    widget.voice_note_btn.setFixedSize(36, 36)
    widget.voice_note_btn.setToolTip("语音输入笔记")
    text_input_layout.addWidget(widget.voice_note_btn)
    widget.add_note_btn = QPushButton("➤")
    widget.add_note_btn.setFixedSize(36, 36)
    widget.add_note_btn.setToolTip("添加笔记")
    text_input_layout.addWidget(widget.add_note_btn)
    add_note_layout.addLayout(text_input_layout)

    add_note_group.setLayout(add_note_layout)
    center_layout.addWidget(add_note_group)

    center_widget.setLayout(center_layout)

    return {"widget": center_widget, "layout": center_layout, "weight": 2}


def create_right_panel(widget):
    """
    创建右侧面板（AI对话 + 输入问题）

    Args:
        widget: ReadEchoPro实例

    Returns:
        dict: 包含右侧面板控件和布局的字典
    """
    right_widget = QWidget()
    right_layout = QVBoxLayout()

    # AI对话显示区域
    chat_group = QGroupBox("🤖 AI助手")
    chat_group_layout = QVBoxLayout()
    widget.ai_chat_display = QTextEdit()
    widget.ai_chat_display.setReadOnly(True)
    chat_group_layout.addWidget(widget.ai_chat_display)
    chat_group.setLayout(chat_group_layout)
    right_layout.addWidget(chat_group, 3)

    # 提问区域
    ask_group = QGroupBox("💬 向AI提问")
    ask_layout = QVBoxLayout()

    # 手动输入问题（输入框 + 语音按钮 + 提问按钮）
    question_input_layout = QHBoxLayout()
    widget.ai_question_input = QLineEdit()
    widget.ai_question_input.setPlaceholderText("输入问题...")
    question_input_layout.addWidget(widget.ai_question_input)
    widget.voice_ask_btn = QPushButton("🎤")
    widget.voice_ask_btn.setFixedSize(36, 36)
    widget.voice_ask_btn.setToolTip("语音提问")
    question_input_layout.addWidget(widget.voice_ask_btn)
    widget.ask_ai_btn = QPushButton("➤")
    widget.ask_ai_btn.setFixedSize(36, 36)
    widget.ask_ai_btn.setToolTip("提问")
    question_input_layout.addWidget(widget.ask_ai_btn)
    ask_layout.addLayout(question_input_layout)

    ask_group.setLayout(ask_layout)
    right_layout.addWidget(ask_group)

    right_widget.setLayout(right_layout)

    return {"widget": right_widget, "layout": right_layout, "weight": 1}


def setup_ui(widget):
    """
    设置完整的用户界面

    新布局：
    - 左侧：上半书架 + 下半笔记本
    - 中间：笔记详情 + 添加笔记
    - 右侧：AI对话 + 提问

    Args:
        widget: ReadEchoPro实例
    """
    # 设置窗口基本属性
    create_main_window(widget)

    # 创建主分割器（支持拖拽调整宽度）
    main_splitter = QSplitter()
    main_splitter.setOrientation(Qt.Orientation.Horizontal)
    main_splitter.setHandleWidth(4)

    # 创建左侧面板（书架 + 笔记本）
    left_panel = create_left_panel(widget)
    main_splitter.addWidget(left_panel["widget"])

    # 创建中间面板（笔记详情 + 添加笔记）
    center_panel = create_center_panel(widget)
    main_splitter.addWidget(center_panel["widget"])

    # 创建右侧面板（AI对话 + 提问）
    right_panel = create_right_panel(widget)
    main_splitter.addWidget(right_panel["widget"])

    # 设置初始宽度比例 1:2:1
    main_splitter.setSizes([250, 500, 250])

    # 设置主窗口布局
    outer_layout = QVBoxLayout()
    outer_layout.setContentsMargins(0, 0, 0, 0)
    outer_layout.addWidget(main_splitter)
    widget.setLayout(outer_layout)

    return widget


def connect_ui_signals(widget):
    """
    连接UI控件的信号

    Args:
        widget: ReadEchoPro实例
    """
    # 书籍管理
    widget.book_list.itemClicked.connect(widget.on_book_selected)
    widget.add_book_btn.clicked.connect(widget.show_add_book_dialog)

    # 笔记管理
    widget.notes_list.itemClicked.connect(widget.on_note_selected)
    widget.add_note_btn.clicked.connect(widget.add_text_note)
    widget.voice_note_btn.clicked.connect(widget.toggle_voice_note)

    # AI提问
    widget.ask_ai_btn.clicked.connect(widget.ask_ai_text_question)
    widget.voice_ask_btn.clicked.connect(widget.ask_ai_voice_question)

    # 书籍右键菜单
    widget.book_list.setContextMenuPolicy(3)  # CustomContextMenu
    widget.book_list.customContextMenuRequested.connect(widget.show_book_context_menu)

    # 笔记右键菜单
    widget.notes_list.setContextMenuPolicy(3)  # CustomContextMenu
    widget.notes_list.customContextMenuRequested.connect(widget.show_note_context_menu)
