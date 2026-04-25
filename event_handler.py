"""
ReadEcho Pro 事件处理器模块
处理所有用户交互事件和业务事件回调

新UI布局：
- 左侧：书架 + 笔记本
- 中间：笔记详情 + 添加笔记
- 右侧：AI对话 + 提问
"""

from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt
from config import LOGGER

# 常量定义
DATA_ROLE = Qt.ItemDataRole.UserRole
NOTE_PREVIEW_LENGTH = 30
DIALOG_WIDTH = 400
DIALOG_HEIGHT = 150


def _refresh_button_style(button):
    """刷新按钮样式（消除重复的 unpolish/polish 模式）"""
    button.style().unpolish(button)
    button.style().polish(button)


class VoiceRecordingController:
    """通用语音录音控制器，消除 note/qa 两套录音逻辑的重复"""

    def __init__(self, services, button, chat_display, thread_attr_name):
        """
        Args:
            services: 服务层实例
            button: 录音按钮控件
            chat_display: 聊天显示控件
            thread_attr_name: 主窗口上存储线程的属性名（如 "note_thread" 或 "qa_thread"）
        """
        self.services = services
        self.button = button
        self.chat_display = chat_display
        self.thread_attr_name = thread_attr_name
        self._on_transcribed_callback = None

    def set_on_transcribed(self, callback):
        """设置转录完成后的回调函数"""
        self._on_transcribed_callback = callback

    def toggle(self, is_recording):
        """切换录音状态"""
        if is_recording:
            self._stop()
        else:
            self._start()

    def _start(self):
        """开始录音"""
        if self.services.start_recording():
            self.button.setText("⏹")
            self.button.setProperty("class", "danger")
            _refresh_button_style(self.button)
            self.chat_display.append("<b>[系统]:</b> 正在录音... 点击停止结束")
            return True
        else:
            self.chat_display.append("<b>[错误]:</b> 启动录音失败")
            return False

    def _stop(self):
        """停止录音"""
        self.button.setText("⏳")
        self.button.setEnabled(False)

        thread = self.services.stop_recording()
        setattr(self.button.window(), self.thread_attr_name, thread) if hasattr(self.button, 'window') else None
        thread.recording_ready.connect(self._on_recorded)
        thread.start()

    def _on_recorded(self, file_path):
        """录音完成回调"""
        if file_path.startswith("Error"):
            self.chat_display.append(f"<b>[系统]:</b> ❌ {file_path}")
            self.reset_button()
            return

        self.button.setText("🔄")

        thread = self.services.create_transcription_thread(
            file_path, self.services.current_book_title, self._on_transcribed
        )
        thread.start()

    def _on_transcribed(self, note_type, content):
        """转录完成回调"""
        if note_type == "Error":
            self.chat_display.append(f"<b>[错误]:</b> {content}")
            self.reset_button()
            return

        if self._on_transcribed_callback:
            self._on_transcribed_callback(note_type, content)

    def reset_button(self):
        """重置按钮状态"""
        self.button.setEnabled(True)
        self.button.setText("🎤")
        self.button.setProperty("class", "")
        _refresh_button_style(self.button)


class EventHandler:
    """事件处理器，管理所有UI事件和业务事件"""

    def __init__(self, main_window):
        """
        初始化事件处理器

        Args:
            main_window: ReadEchoPro主窗口实例
        """
        self.window = main_window
        self.services = main_window.services
        self.current_note_id = None

        # 初始化录音控制器
        self._note_recording = VoiceRecordingController(
            services=main_window.services,
            button=main_window.voice_note_btn,
            chat_display=main_window.ai_chat_display,
            thread_attr_name="note_thread"
        )
        self._note_recording.set_on_transcribed(self._on_voice_note_transcribed)

        self._qa_recording = VoiceRecordingController(
            services=main_window.services,
            button=main_window.voice_ask_btn,
            chat_display=main_window.ai_chat_display,
            thread_attr_name="qa_thread"
        )
        self._qa_recording.set_on_transcribed(self._on_voice_qa_transcribed)

    # --- 书籍管理事件 ---

    def on_book_selected(self, item):
        """当选择书籍时"""
        data = item.data(DATA_ROLE)
        if not data or not isinstance(data, dict):
            return

        book_id = data.get("book_id")
        title = data.get("title", "")
        author = data.get("author", "")

        # 更新标题显示
        display_text = f"{title}"
        if author:
            display_text += f" - {author}"
        self.window.title_display.setText(display_text)

        # 设置当前书籍
        self.services.set_current_book(book_id, title)

        # 加载该书籍的笔记列表
        self.load_notes_for_book(book_id)

    def load_notes_for_book(self, book_id):
        """加载指定书籍的笔记列表（录音笔记 + 问答记录）"""
        self.window.notes_list.clear()
        self.current_note_id = None

        if not book_id:
            return

        # 加载录音笔记
        recordings = self.services.get_recordings_by_book(book_id)
        for rec_id, file_path, text, timestamp in recordings:
            if len(text) > NOTE_PREVIEW_LENGTH:
                display_text = f"📝 {timestamp}: {text[:NOTE_PREVIEW_LENGTH]}..."
            else:
                display_text = f"📝 {timestamp}: {text}"
            self.window.notes_list.addItem(display_text)
            item = self.window.notes_list.item(self.window.notes_list.count() - 1)
            item.setData(DATA_ROLE, {"type": "recording", "id": rec_id, "text": text, "timestamp": timestamp})

        # 加载问答记录
        qa_records = self.services.get_qa_by_book(book_id)
        for qa_id, question, answer, timestamp in qa_records:
            if len(question) > NOTE_PREVIEW_LENGTH:
                display_text = f"💬 {timestamp}: {question[:NOTE_PREVIEW_LENGTH]}..."
            else:
                display_text = f"💬 {timestamp}: {question}"
            self.window.notes_list.addItem(display_text)
            item = self.window.notes_list.item(self.window.notes_list.count() - 1)
            item.setData(
                DATA_ROLE,
                {"type": "qa", "id": qa_id, "question": question, "answer": answer, "timestamp": timestamp}
            )

    def on_note_selected(self, item):
        """当选择笔记时"""
        data = item.data(DATA_ROLE)
        if not data or not isinstance(data, dict):
            return

        self.current_note_id = data.get("id")
        note_type = data.get("type")

        self.window.note_display.clear()

        # 录音笔记可编辑，QA笔记只读
        if note_type == "recording":
            text = data.get("text", "")
            timestamp = data.get("timestamp", "")
            self.window.note_display.setPlainText(text)
            self.window.save_note_btn.setVisible(True)
        elif note_type == "qa":
            question = data.get("question", "")
            answer = data.get("answer", "")
            timestamp = data.get("timestamp", "")
            self.window.note_display.append("<b>💬 AI问答</b>")
            self.window.note_display.append(f"<b>时间:</b> {timestamp}")
            self.window.note_display.append("<hr>")
            self.window.note_display.append(f"<b>问题:</b> {question}")
            self.window.note_display.append("<b>回答:</b>")
            self.window.note_display.append(f"<pre>{answer}</pre>")
            self.window.note_display.setReadOnly(True)
            self.window.save_note_btn.setVisible(False)

    def show_add_book_dialog(self):
        """显示添加书籍对话框"""
        dialog = QDialog(self.window)
        dialog.setWindowTitle("添加书籍")
        dialog.setFixedSize(DIALOG_WIDTH, DIALOG_HEIGHT)

        layout = QVBoxLayout()

        # 书名输入
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("书名:"))
        title_input = QLineEdit()
        title_input.setPlaceholderText("请输入书名")
        title_layout.addWidget(title_input)
        layout.addLayout(title_layout)

        # 作者输入
        author_layout = QHBoxLayout()
        author_layout.addWidget(QLabel("作者:"))
        author_input = QLineEdit()
        author_input.setPlaceholderText("请输入作者（可选）")
        author_layout.addWidget(author_input)
        layout.addLayout(author_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        confirm_btn = QPushButton("确认")
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(confirm_btn)
        layout.addLayout(btn_layout)

        dialog.setLayout(layout)

        # 连接信号
        cancel_btn.clicked.connect(dialog.reject)
        confirm_btn.clicked.connect(dialog.accept)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            title = title_input.text().strip()
            author = author_input.text().strip()

            if not title:
                QMessageBox.warning(self.window, "提示", "书名不能为空")
                return

            try:
                book_id = self.services.add_book(title, author)
                self.refresh_bookshelf()
                self.services.set_current_book(book_id, title)
                self.window.title_display.setText(f"{title}" + (f" - {author}" if author else ""))
                self.load_notes_for_book(book_id)
                self.window.ai_chat_display.append(f"<b>[系统]:</b> 已添加书籍《{title}》")
            except Exception as e:
                QMessageBox.warning(self.window, "错误", f"添加书籍失败: {e}")

    def refresh_bookshelf(self, search_query=""):
        """刷新本地书架列表"""
        self.window.book_list.clear()
        books = self.services.get_books(search_query)
        for book_id, title, author in books:
            item_text = f"{title}"
            if author:
                item_text += f" - {author}"
            self.window.book_list.addItem(item_text)
            item = self.window.book_list.item(self.window.book_list.count() - 1)
            item.setData(
                256,
                {
                    "book_id": book_id,
                    "title": title,
                    "author": author,
                },
            )

    def delete_selected_book(self):
        """删除当前选中的书籍"""
        book_id = self.services.current_book_id
        if not book_id:
            self.window.ai_chat_display.append("<b>[系统]:</b> 请先选择要删除的书籍")
            return

        result = QMessageBox.question(
            self.window,
            "删除书籍",
            "确定要删除该书籍及其所有笔记吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if result != QMessageBox.StandardButton.Yes:
            return

        try:
            self.services.delete_book(book_id)
            self.services.clear_current_book()
            self.window.title_display.clear()
            self.refresh_bookshelf()
            self.window.notes_list.clear()
            self.window.note_display.clear()
            self.window.ai_chat_display.append("<b>[系统]:</b> 已删除书籍")
        except Exception as e:
            self.window.ai_chat_display.append(f"<b>[错误]:</b> 删除书籍失败: {e}")

    # --- 笔记管理事件 ---

    def add_text_note(self):
        """添加文本笔记"""
        book_id = self.services.current_book_id
        if not book_id:
            self.window.ai_chat_display.append("<b>[系统]:</b> 请先选择书籍")
            return

        note_text = self.window.note_text_input.text().strip()
        if not note_text:
            self.window.ai_chat_display.append("<b>[系统]:</b> 请输入笔记内容")
            return

        try:
            # 保存为录音类型（手动笔记）
            file_path = f"manual_note_{book_id}"
            self.services.add_recording(book_id, file_path, note_text)
            self.window.note_text_input.clear()
            self.load_notes_for_book(book_id)
            self.window.ai_chat_display.append("<b>[系统]:</b> 已添加笔记")
        except Exception as e:
            self.window.ai_chat_display.append(f"<b>[错误]:</b> 添加笔记失败: {e}")

    def toggle_voice_note(self):
        """切换语音笔记录音状态"""
        book_id = self.services.current_book_id
        if not book_id:
            self.window.ai_chat_display.append("<b>[系统]:</b> 请先选择书籍")
            return

        if self.window.is_recording:
            self.window.is_recording = False
            self._note_recording._stop()
        else:
            if self._note_recording._start():
                self.window.is_recording = True

    def _on_voice_note_transcribed(self, note_type, content):
        """语音笔记转录完成"""
        book_id = self.services.current_book_id
        if book_id:
            file_path = self.services.get_temp_audio_file()
            self.services.add_recording(book_id, file_path, content)
            self.load_notes_for_book(book_id)
            self.window.ai_chat_display.append("<b>[系统]:</b> 语音笔记已保存")

        self._note_recording.reset_button()

    def save_note_edit(self):
        """保存笔记编辑"""
        if not self.current_note_id:
            return

        selected_items = self.window.notes_list.selectedItems()
        if not selected_items:
            return

        data = selected_items[0].data(DATA_ROLE)
        if not data or data.get("type") != "recording":
            return

        new_text = self.window.note_display.toPlainText().strip()
        if not new_text:
            self.window.ai_chat_display.append("<b>[系统]:</b> 笔记内容不能为空")
            return

        try:
            self.services.update_recording_text(self.current_note_id, new_text)
            self.load_notes_for_book(self.services.current_book_id)
            self.window.ai_chat_display.append("<b>[系统]:</b> 笔记已保存")
        except Exception as e:
            self.window.ai_chat_display.append(f"<b>[错误]:</b> 保存笔记失败: {e}")

    def delete_selected_note(self):
        """删除选中的笔记"""
        if not self.current_note_id:
            self.window.ai_chat_display.append("<b>[系统]:</b> 请先选择要删除的笔记")
            return

        selected_items = self.window.notes_list.selectedItems()
        if not selected_items:
            return

        data = selected_items[0].data(DATA_ROLE)
        if not data:
            return

        result = QMessageBox.question(
            self.window,
            "删除笔记",
            "确定要删除该笔记吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if result != QMessageBox.StandardButton.Yes:
            return

        try:
            note_type = data.get("type")
            note_id = data.get("id")

            if note_type == "recording":
                self.services.delete_recording(note_id)
            # QA记录暂不支持单独删除

            self.load_notes_for_book(self.services.current_book_id)
            self.window.note_display.clear()
            self.window.ai_chat_display.append("<b>[系统]:</b> 已删除笔记")
        except Exception as e:
            self.window.ai_chat_display.append(f"<b>[错误]:</b> 删除笔记失败: {e}")

    # --- AI问答事件 ---

    def ask_ai_text_question(self):
        """手动输入问题问AI"""
        book_id = self.services.current_book_id
        if not book_id:
            self.window.ai_chat_display.append("<b>[系统]:</b> 请先选择书籍")
            return

        question = self.window.ai_question_input.text().strip()
        if not question:
            self.window.ai_chat_display.append("<b>[系统]:</b> 请输入问题")
            return

        self._process_ai_question(question)
        self.window.ai_question_input.clear()

    def ask_ai_voice_question(self):
        """语音提问AI"""
        book_id = self.services.current_book_id
        if not book_id:
            self.window.ai_chat_display.append("<b>[系统]:</b> 请先选择书籍")
            return

        if self.window.is_recording:
            self.window.is_recording = False
            self._qa_recording._stop()
        else:
            if self._qa_recording._start():
                self.window.is_recording = True

    def _on_voice_qa_transcribed(self, note_type, content):
        """语音提问转录完成"""
        question = content.strip()
        if not question:
            self.window.ai_chat_display.append("<b>[系统]:</b> 未检测到语音内容")
            self._qa_recording.reset_button()
            return

        self._process_ai_question(question)

    def _process_ai_question(self, question):
        """处理AI问题"""
        title = self.services.current_book_title
        self.window.last_question = question

        # 显示问题
        self.window.ai_chat_display.append(
            f"<div style='padding: 10px; margin: 8px 0; border: 1px solid #4a4a6a; border-radius: 8px;'>"
            f"<b>👤 问题:</b> {question}"
            "</div>"
        )

        # 禁用按钮
        self.window.ask_ai_btn.setEnabled(False)
        self.window.ask_ai_btn.setText("⏳")
        self.window.voice_ask_btn.setEnabled(False)
        self.window.voice_ask_btn.setText("⏳")

        # 启动AI线程
        self.window.thread = self.services.create_qa_thread(question, title, self._on_ai_answer_ready)
        self.window.thread.start()

    def _on_ai_answer_ready(self, note_type, content):
        """AI回答准备就绪"""
        self._qa_recording.reset_button()
        self.window.ask_ai_btn.setEnabled(True)
        self.window.ask_ai_btn.setText("➤")

        if note_type == "Error":
            self.window.ai_chat_display.append(f"<b>[错误]:</b> {content}")
            return

        # 显示回答
        self.window.ai_chat_display.append(
            f"<div style='padding: 10px; margin: 8px 0; border: 1px solid #4a4a6a; border-radius: 8px;'>"
            f"<b>🤖 回答:</b><br/><pre style='white-space: pre-wrap;'>{content}</pre>"
            "</div>"
        )

        # 保存到数据库
        book_id = self.services.current_book_id
        if book_id:
            self.services.add_qa(book_id, self.window.last_question, content)
            self.load_notes_for_book(book_id)

    # --- 模型加载事件 ---

    def on_model_ready(self, model):
        """Whisper模型加载完成的回调"""
        self.services.set_stt_model(model)
        self.window.stt_model = model
        self.window.ai_chat_display.append("<b>[系统]:</b> Whisper模型已就绪，GPU加速已启用")

    # --- 右键菜单 ---

    def show_book_context_menu(self, position):
        """显示书架右键菜单"""
        from PyQt6.QtWidgets import QMenu

        item = self.window.book_list.itemAt(position)
        if not item:
            return

        data = item.data(DATA_ROLE)
        if not data or not isinstance(data, dict):
            return

        book_id = data.get("book_id")
        if not book_id:
            return

        menu = QMenu(self.window)
        edit_action = menu.addAction("✏️ 编辑")
        delete_action = menu.addAction("🗑️ 删除书籍")

        action = menu.exec(self.window.book_list.mapToGlobal(position))
        if action == edit_action:
            self.edit_selected_book(book_id)
        elif action == delete_action:
            self.delete_selected_book()

    def edit_selected_book(self, book_id=None):
        """编辑当前选中的书籍信息"""
        if not book_id:
            book_id = self.services.current_book_id
        if not book_id:
            self.window.ai_chat_display.append("<b>[系统]:</b> 请先选择要编辑的书籍")
            return

        # 获取当前书籍信息
        data = None
        for i in range(self.window.book_list.count()):
            item = self.window.book_list.item(i)
            item_data = item.data(DATA_ROLE)
            if item_data and item_data.get("book_id") == book_id:
                data = item_data
                break

        if not data:
            return

        current_title = data.get("title", "")
        current_author = data.get("author", "")

        # 创建编辑对话框
        dialog = QDialog(self.window)
        dialog.setWindowTitle("编辑书籍")
        dialog.setFixedSize(DIALOG_WIDTH, DIALOG_HEIGHT)

        layout = QVBoxLayout()

        # 书名输入
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("书名:"))
        title_input = QLineEdit()
        title_input.setText(current_title)
        title_input.setPlaceholderText("请输入书名")
        title_layout.addWidget(title_input)
        layout.addLayout(title_layout)

        # 作者输入
        author_layout = QHBoxLayout()
        author_layout.addWidget(QLabel("作者:"))
        author_input = QLineEdit()
        author_input.setText(current_author)
        author_input.setPlaceholderText("请输入作者（可选）")
        author_layout.addWidget(author_input)
        layout.addLayout(author_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        confirm_btn = QPushButton("确认")
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(confirm_btn)
        layout.addLayout(btn_layout)

        dialog.setLayout(layout)

        # 连接信号
        cancel_btn.clicked.connect(dialog.reject)
        confirm_btn.clicked.connect(dialog.accept)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_title = title_input.text().strip()
            new_author = author_input.text().strip()

            if not new_title:
                QMessageBox.warning(self.window, "提示", "书名不能为空")
                return

            try:
                self._update_book_info(book_id, new_title, new_author)
                self.refresh_bookshelf()
                self.services.set_current_book(book_id, new_title)
                self.window.title_display.setText(f"{new_title}" + (f" - {new_author}" if new_author else ""))
                self.window.ai_chat_display.append("<b>[系统]:</b> 书籍信息已更新")
            except Exception as e:
                QMessageBox.warning(self.window, "错误", f"更新书籍失败: {e}")

    def _update_book_info(self, book_id, new_title, new_author):
        """更新书籍信息到数据库"""
        try:
            self.services.db.cursor.execute(
                "UPDATE books SET title = ?, author = ? WHERE id = ?",
                (new_title, new_author, book_id)
            )
            self.services.db.conn.commit()
            LOGGER.info(f"书籍信息已更新: ID={book_id}")
        except Exception as e:
            self.services.db.conn.rollback()
            raise e

    def show_note_context_menu(self, position):
        """显示笔记右键菜单"""
        from PyQt6.QtWidgets import QMenu

        item = self.window.notes_list.itemAt(position)
        if not item:
            return

        menu = QMenu(self.window)
        delete_action = menu.addAction("🗑️ 删除笔记")

        action = menu.exec(self.window.notes_list.mapToGlobal(position))
        if action == delete_action:
            self.delete_selected_note()

    def cleanup(self) -> None:
        """清理事件处理器资源。"""
        return


def create_event_handler(main_window):
    """
    创建事件处理器实例

    Args:
        main_window: ReadEchoPro主窗口实例

    Returns:
        EventHandler: 事件处理器实例
    """
    return EventHandler(main_window)
