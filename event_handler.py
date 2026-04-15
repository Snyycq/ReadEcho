"""
ReadEcho Pro 事件处理器模块
处理所有用户交互事件和业务事件回调
"""

from PyQt6.QtWidgets import QInputDialog


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

    # --- 书籍管理事件 ---

    def on_book_selected(self, item):
        """当选择书籍时"""
        book_id = item.data(256)
        if book_id:
            # 设置标题输入框
            title = item.text().split(" - ")[0]  # 移除作者部分
            self.window.title_input.setText(title)
            # 加载录音历史
            self.load_recordings_for_book(book_id)
            # 更新当前书籍
            self.services.set_current_book(book_id, title)

    def load_recordings_for_book(self, book_id):
        """加载指定书籍的录音历史"""
        self.window.recording_list.clear()
        recordings = self.services.get_recordings_by_book(book_id)
        for rec_id, file_path, text, timestamp in recordings:
            # 截断过长的文本
            display_text = text[:50] + "..." if len(text) > 50 else text
            item_text = f"{timestamp}: {display_text}"
            self.window.recording_list.addItem(item_text)
            item = self.window.recording_list.item(self.window.recording_list.count() - 1)
            item.setData(256, rec_id)  # 存储recording_id

    def search_books(self):
        """搜索书籍"""
        query = self.window.search_input.text()
        self.refresh_bookshelf(query)

    def refresh_bookshelf(self, search_query=""):
        """刷新书架列表"""
        self.window.book_list.clear()
        books = self.services.get_books(search_query)
        for book_id, title, author in books:
            item_text = f"{title}"
            if author:
                item_text += f" - {author}"
            self.window.book_list.addItem(item_text)
            # 存储book_id作为item的数据
            item = self.window.book_list.item(self.window.book_list.count() - 1)
            item.setData(256, book_id)  # 256是Qt.UserRole

    def add_new_book(self):
        """添加新书籍"""
        title, ok = QInputDialog.getText(self.window, "Add New Book", "Enter book title:")
        if ok and title:
            author, ok2 = QInputDialog.getText(self.window, "Add New Book", "Enter author (optional):")
            author = author if ok2 else ""
            self.services.add_book(title, author)
            self.refresh_bookshelf()
            self.window.display.append(f"<b>[System]:</b> Added book '{title}' to bookshelf.")

    # --- AI处理事件 ---

    def start_summary(self):
        """开始生成书籍总结"""
        title = self.window.title_input.text()
        if not title:
            return
        self.window.sum_btn.setEnabled(False)
        # 使用服务创建总结生成线程
        self.window.thread = self.services.create_summary_thread(title, self.on_finished)
        self.window.thread.start()

    def ask_ai_question(self):
        """询问AI关于书籍的问题"""
        title = self.window.title_input.text()
        question = self.window.qa_input.text()
        if not title:
            self.window.display.append("<b>[System]:</b> Please select or enter a book title first.")
            return
        if not question:
            self.window.display.append("<b>[System]:</b> Please enter a question.")
            return

        # 存储问题以便后续使用
        self.window.last_question = question

        # 禁用按钮，显示处理中
        self.window.qa_btn.setEnabled(False)
        self.window.qa_btn.setText("Processing...")
        self.window.display.append(f"<b>[AI Q&A]:</b> Question about '{title}': {question}")

        # 启动AI处理线程
        self.window.thread = self.services.create_qa_thread(question, title, self.on_qa_finished)
        self.window.thread.start()

        self.window.qa_input.clear()

    def on_finished(self, note_type, content):
        """处理AI任务完成的结果"""
        from utils import format_summary_content

        title = self.window.title_input.text()

        # 格式化内容
        if note_type == "Summary":
            formatted_content = format_summary_content(content)
            self.window.display.append(f"<h3>📚 {note_type} - {title}</h3>")
            self.window.display.append(formatted_content)
            self.window.display.append("<hr>")
        else:
            self.window.display.append(f"<b>[{note_type}]:</b>\n{content}\n")

        if note_type == "VoiceNote":
            # 获取或创建书籍
            book_id = self.services.get_book_by_title(title)
            if book_id is None:
                # 书籍不存在，创建它
                book_id = self.services.add_book(title, "")

            # 添加录音记录到数据库
            file_path = self.services.get_temp_audio_file()
            self.services.add_recording(book_id, file_path, content)

            # 刷新录音历史列表
            if book_id:
                self.load_recordings_for_book(book_id)

            # 也添加到notes表保持兼容性
            self.services.add_note(title, content, note_type)
        else:
            # 其他类型的笔记（如Summary）
            self.services.add_note(title, content, note_type)

        self.window.sum_btn.setEnabled(True)
        self.window.voice_btn.setEnabled(True)
        self.window.voice_btn.setText("Start Recording")
        self.window.voice_btn.setStyleSheet("")
        self.window.apply_theme()

    def on_qa_finished(self, note_type, content):
        """处理问答完成的结果"""
        if note_type == "Error":
            self.window.display.append(f"<b>[Error]:</b> {content}")
            self.window.qa_btn.setEnabled(True)
            self.window.qa_btn.setText("Ask AI")
            return

        title = self.window.title_input.text()

        # 显示问答结果
        self.window.display.append(f"<h3>❓ Q&A - {title}</h3>")
        self.window.display.append(
            f"<div style='background-color: #3c3c3c; padding: 10px; border-radius: 5px; margin: 5px 0;'>"
            f"<b>Question:</b> {self.window.last_question}</div>"
        )
        self.window.display.append(
            f"<div style='background-color: #2d3748; padding: 10px; border-radius: 5px; margin: 10px 0;'>"
            f"<b>Answer:</b> {content}</div>"
        )
        self.window.display.append("<hr>")

        # 保存到数据库
        book_id = self.services.get_book_by_title(title)
        if book_id is None:
            book_id = self.services.add_book(title, "")

        # 存储问题和答案到数据库
        self.services.add_qa(book_id, self.window.last_question, content)

        # 重新启用按钮
        self.window.qa_btn.setEnabled(True)
        self.window.qa_btn.setText("Ask AI")

    # --- 录音控制事件 ---

    def toggle_recording(self):
        """切换录音状态：开始 or 结束"""
        if not self.window.is_recording:
            self.begin_recording()
        else:
            self.stop_recording()

    def begin_recording(self):
        """开始录音"""
        title = self.window.title_input.text()
        if not title:
            self.window.display.append("<b>[System]:</b> Please enter a book title first.")
            return

        # 使用服务开始录音
        if self.services.start_recording():
            self.window.is_recording = True
            self.window.voice_btn.setText("Stop Recording")
            self.window.voice_btn.setStyleSheet("""
                QPushButton { background-color: #dc3545; border-radius: 5px; padding: 8px; font-weight: bold; }
                QPushButton:hover { background-color: #c82333; }
            """)
            self.window.display.append("<b>[System]:</b> Recording started... Press 'Stop Recording' to finish.")
        else:
            self.window.display.append("<b>[System]:</b> Failed to start recording.")

    def stop_recording(self):
        """结束录音"""
        self.window.is_recording = False
        self.window.voice_btn.setText("Saving...")
        self.window.voice_btn.setEnabled(False)

        # 使用服务停止录音并获取录音完成线程
        self.window.finish_thread = self.services.stop_recording()
        self.window.finish_thread.recording_ready.connect(self.on_recording_saved)
        self.window.finish_thread.start()

    def on_recording_saved(self, file_path):
        """录音文件保存完成后的回调"""
        if file_path.startswith("Error"):
            self.window.display.append(f"<b>[System]:</b> ❌ {file_path}")
            self.window.voice_btn.setEnabled(True)
            self.window.voice_btn.setText("Start Recording")
            return

        self.window.voice_btn.setText("Transcribing...")

        # 启动 AI 处理线程进行转录
        self.window.thread = self.services.create_transcription_thread(
            file_path, self.window.title_input.text(), self.on_finished
        )
        self.window.thread.start()

    def view_selected_recording(self):
        """查看选中的录音"""
        selected_items = self.window.recording_list.selectedItems()
        if not selected_items:
            return
        item = selected_items[0]
        rec_id = item.data(256)
        if rec_id:
            # 这里应该显示完整的录音文本
            # 暂时显示占位信息
            self.window.display.append(f"<b>[Recording View]:</b> Selected recording ID: {rec_id}")
            self.window.display.append("<i>录音查看功能正在开发中...</i>")

    # --- 主题管理事件 ---

    def toggle_theme(self):
        """切换主题"""
        # 使用服务切换主题
        self.window.dark_mode = self.services.toggle_theme()
        self.window.apply_theme()

    # --- 模型加载事件 ---

    def on_model_ready(self, model):
        """Whisper模型加载完成的回调"""
        self.services.set_stt_model(model)
        self.window.stt_model = model  # 保持向后兼容
        self.window.display.append("<b>[System]:</b> Whisper Model Ready! GPU Accelerated.")

    def cleanup(self) -> None:
        """清理事件处理器资源。"""
        # 目前没有特定资源需要释放，但是保留接口以便未来扩展
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
