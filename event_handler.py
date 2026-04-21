"""
ReadEcho Pro 事件处理器模块
处理所有用户交互事件和业务事件回调
"""

from PyQt6.QtWidgets import QMessageBox, QInputDialog


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
        self.is_online_search = False
        self.current_search_results = []

    # --- 书籍管理事件 ---

    def on_book_selected(self, item):
        """当选择书籍时"""
        data = item.data(256)
        if not data or not isinstance(data, dict):
            return

        source = data.get("source")
        if source == "local":
            book_id = data.get("book_id")
            title = data.get("title", item.text().split(" - ")[0])
            self.window.title_input.setText(title)
            self.load_recordings_for_book(book_id)
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
        """执行在线模糊搜索"""
        query = self.window.search_input.text().strip()
        if not query:
            self.window.display.append(
                "<b>[System]:</b> Search query is empty. Showing local bookshelf."
            )
            self.refresh_bookshelf()
            return

        self.window.display.append(f"<b>[System]:</b> Searching online for '{query}'...")
        self.window.search_results_list.clear()
        self.current_search_results = self.services.search_online_books(query)
        self.is_online_search = True

        if not self.current_search_results:
            self.window.display.append("<b>[System]:</b> No online search results found.")
            return

        self.window.display.append(
            "<b>[System]:</b> Search results are shown in the Search Results list below. "
            "Select one and click Import Selected Book."
        )
        for result in self.current_search_results:
            if isinstance(result, dict):
                title = result.get("title", "Unknown")
                author = result.get("author", "")
            else:
                title = result[1] if len(result) > 1 else "Unknown"
                author = result[2] if len(result) > 2 else ""
                result = {
                    "source": "local",
                    "book_id": result[0] if len(result) > 0 else None,
                    "title": title,
                    "author": author,
                }

            item_text = f"{title}"
            if author:
                item_text += f" - {author}"
            self.window.search_results_list.addItem(item_text)
            item = self.window.search_results_list.item(self.window.search_results_list.count() - 1)
            item.setData(256, result)

    def on_search_result_selected(self, item):
        """当选择在线搜索结果时"""
        data = item.data(256)
        if not data or not isinstance(data, dict):
            return

        title = data.get("title", item.text().split(" - ")[0])
        author = data.get("author", "")
        self.window.title_input.setText(title)
        self.window.display.append(
            f"<b>[System]:</b> Selected online result '{title}'"
            f"{' by ' + author if author else ''}. Click Import Selected Book to add it."
        )

    def refresh_bookshelf(self, search_query=""):
        """刷新本地书架列表"""
        self.window.book_list.clear()
        self.current_search_results = []
        self.is_online_search = False
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
                    "source": "local",
                    "book_id": book_id,
                    "title": title,
                    "author": author,
                },
            )

    def import_selected_book(self):
        """导入当前选中的在线搜索结果书籍"""
        selected_items = self.window.search_results_list.selectedItems()
        if not selected_items:
            self.window.display.append(
                "<b>[System]:</b> Please select an online search result first."
            )
            return

        data = selected_items[0].data(256)
        if not isinstance(data, dict) or data.get("source") != "online":
            self.window.display.append("<b>[System]:</b> Please select an online search result.")
            return

        title = data.get("title", "").strip()
        author = data.get("author", "").strip()
        if not title:
            self.window.display.append("<b>[System]:</b> Selected online book has no title.")
            return

        book_id = self.services.add_book(title, author)
        self.window.display.append(
            f"<b>[System]:</b> Imported '{title}'{' by ' + author if author else ''}."
        )
        self.refresh_bookshelf()
        self.services.set_current_book(book_id, title)
        self.window.title_input.setText(title)

    def delete_selected_book(self):
        """删除当前选中的书籍"""
        book_id = self.services.current_book_id
        if not book_id:
            self.window.display.append("<b>[System]:</b> Please select a book to delete.")
            return

        result = QMessageBox.question(
            self.window,
            "Delete Book",
            "Are you sure you want to delete the selected book and all its associated notes?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if result != QMessageBox.StandardButton.Yes:
            return

        try:
            self.services.delete_book(book_id)
            self.services.clear_current_book()
            self.window.title_input.clear()
            self.refresh_bookshelf()
            self.window.recording_list.clear()
            self.window.display.append(f"<b>[System]:</b> Deleted book ID {book_id}.")
        except Exception as e:
            self.window.display.append(f"<b>[Error]:</b> Failed to delete book: {e}")

    # --- AI处理事件 ---

    def start_summary(self):
        """开始生成书籍总结"""
        title = self.window.title_input.text()
        if not title:
            return
        if hasattr(self.window, "sum_btn"):
            self.window.sum_btn.setEnabled(False)
        # 使用服务创建总结生成线程
        self.window.thread = self.services.create_summary_thread(title, self.on_finished)
        self.window.thread.start()

    def ask_ai_question(self):
        """询问AI关于书籍的问题"""
        title = self.window.title_input.text()
        question = self.window.qa_input.text()
        if not title:
            self.window.display.append(
                "<b>[System]:</b> Please select or enter a book title first."
            )
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
            # Terminal固定黑色背景，使用固定边框颜色
            border_color = "#555555"

            self.window.display.append(
                "<div style='padding: 12px; margin: 12px 0; border: 1px solid "
                + border_color
                + "; border-radius: 10px; background-color: transparent;'>"
                f"<b>[{note_type}]</b>"
                f"<div style='margin-top:10px; white-space: pre-wrap; line-height:1.5;'>"
                f"{content}"
                "</div>"
                "</div>"
            )

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

        if hasattr(self.window, "sum_btn"):
            self.window.sum_btn.setEnabled(True)
        self.window.voice_btn.setEnabled(True)
        self.window.voice_btn.setText("Start Recording")
        self.window.voice_btn.setProperty("class", "")
        self.window.voice_btn.style().unpolish(self.window.voice_btn)
        self.window.voice_btn.style().polish(self.window.voice_btn)
        self.window.apply_theme()

    def on_qa_finished(self, note_type, content):
        """处理问答完成的结果"""
        if note_type == "Error":
            self.window.display.append(f"<b>[Error]:</b> {content}")
            self.window.qa_btn.setEnabled(True)
            self.window.qa_btn.setText("Ask AI")
            return

        title = self.window.title_input.text()

        # Terminal固定黑色背景，使用固定边框颜色
        border_color = "#555555"

        # 显示问答结果
        from utils import format_summary_content

        formatted_answer = format_summary_content(content)
        self.window.display.append(
            "<div style='padding: 12px; margin: 12px 0; border: 1px solid "
            + border_color
            + "; border-radius: 10px; "
            + "background-color: transparent;'>"
            f"<h3 style='margin:0 0 10px 0;'>❓ Q&A - {title}</h3>"
            f"<div style='margin-bottom:10px; padding:10px; "
            f"background: transparent; border-radius:6px;'>"
            f"<b>Question:</b> {self.window.last_question}</div>"
            f"<div style='padding:10px; background: transparent; border-radius:6px;'>"
            f"<b>Answer:</b>{formatted_answer}</div>"
            "</div>"
        )
        self.window.display.append("<br>")

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
            self.window.voice_btn.setProperty("class", "danger")
            self.window.voice_btn.style().unpolish(self.window.voice_btn)
            self.window.voice_btn.style().polish(self.window.voice_btn)
            self.window.display.append(
                "<b>[System]:</b> Recording started... Press 'Stop Recording' to finish."
            )
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
            recording = self.services.get_recording_by_id(rec_id)
            if recording:
                _, _, file_path, text, timestamp = recording
                self.window.display.append(f"<b>[Recording]:</b> {timestamp}")
                self.window.display.append(f"<pre>{text}</pre>")
            else:
                self.window.display.append(
                    f"<b>[Recording View]:</b> Selected recording ID: {rec_id}"
                )

    def edit_selected_recording(self):
        """编辑选中的语音笔记文本"""
        selected_items = self.window.recording_list.selectedItems()
        if not selected_items:
            self.window.display.append("<b>[System]:</b> Please select a recording to edit.")
            return
        item = selected_items[0]
        rec_id = item.data(256)
        if not rec_id:
            return

        recording = self.services.get_recording_by_id(rec_id)
        if not recording:
            self.window.display.append(f"<b>[Error]:</b> Recording {rec_id} not found.")
            return

        _, _, file_path, text, timestamp = recording
        new_text, ok = QInputDialog.getMultiLineText(
            self.window, "Edit Recording Note", "Transcribed text:", text
        )
        if not ok or new_text is None:
            return

        try:
            self.services.update_recording_text(rec_id, new_text)
            self.load_recordings_for_book(recording[1])
            self.window.display.append(f"<b>[System]:</b> Updated recording {rec_id}.")
        except Exception as e:
            self.window.display.append(f"<b>[Error]:</b> Failed to update recording: {e}")

    def delete_selected_recording(self):
        """删除选中的语音笔记"""
        selected_items = self.window.recording_list.selectedItems()
        if not selected_items:
            self.window.display.append("<b>[System]:</b> Please select a recording to delete.")
            return
        item = selected_items[0]
        rec_id = item.data(256)
        if not rec_id:
            return

        result = QMessageBox.question(
            self.window,
            "Delete Recording",
            "Are you sure you want to delete the selected recording?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if result != QMessageBox.StandardButton.Yes:
            return

        try:
            recording = self.services.get_recording_by_id(rec_id)
            self.services.delete_recording(rec_id)
            if recording:
                self.load_recordings_for_book(recording[1])
            self.window.display.append(f"<b>[System]:</b> Deleted recording {rec_id}.")
        except Exception as e:
            self.window.display.append(f"<b>[Error]:</b> Failed to delete recording: {e}")

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
