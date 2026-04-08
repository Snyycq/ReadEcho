import sys
import sqlite3
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QTextEdit, QLineEdit, QLabel)
from PyQt6.QtCore import QThread, pyqtSignal
import ollama

# --- DB Manager Class ---
class DBManager:
    def __init__(self):
        self.conn = sqlite3.connect('readecho.db')
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS books 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
             title TEXT, 
             summary TEXT)
        ''')
        self.conn.commit()

    def save_book(self, title, summary):
        self.cursor.execute("INSERT INTO books (title, summary) VALUES (?, ?)", (title, summary))
        self.conn.commit()

# --- AI Thread Class ---
class AIThread(QThread):
    finished_signal = pyqtSignal(str)

    def __init__(self, user_input):
        super().__init__()
        self.user_input = user_input

    def run(self):
        try:
            # Using prompt in English but asking for Chinese response
            prompt = f"Please summarize the book '{self.user_input}' in Chinese."
            response = ollama.chat(model='qwen2.5:7b', messages=[
                {'role': 'user', 'content': prompt}
            ])
            content = response['message']['content']
            self.finished_signal.emit(content)
        except Exception as e:
            self.finished_signal.emit(f"Error: {str(e)}")

# --- Main Window ---
class ReadEchoMain(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DBManager()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('ReadEcho - Local AI Library')
        self.setGeometry(300, 300, 600, 500)

        layout = QVBoxLayout()

        self.label = QLabel("Enter book name to generate summary and save to DB:")
        layout.addWidget(self.label)

        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        layout.addWidget(self.result_display)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Book name here...")
        layout.addWidget(self.input_field)

        self.btn = QPushButton('Generate and Save')
        self.btn.clicked.connect(self.start_ai_task)
        layout.addWidget(self.btn)

        self.setLayout(layout)

    def start_ai_task(self):
        book_name = self.input_field.text()
        if not book_name: return

        self.btn.setEnabled(False)
        self.btn.setText("AI is thinking...")
        
        self.ai_thread = AIThread(book_name)
        self.ai_thread.finished_signal.connect(self.on_ai_finished)
        self.ai_thread.start()

    def on_ai_finished(self, result):
        self.result_display.append(f"<b>Summary:</b>\n{result}\n")
        
        book_name = self.input_field.text()
        self.db.save_book(book_name, result)
        self.result_display.append("<i>--- Saved to Local Database ---</i>")

        self.btn.setEnabled(True)
        self.btn.setText("Generate and Save")
        self.input_field.clear()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ReadEchoMain()
    window.show()
    sys.exit(app.exec())