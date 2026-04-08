# -*- coding: utf-8 -*-
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLineEdit
import ollama

class ReadEchoTest(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # 窗口标题改为英文，避免编码冲突
        self.setWindowTitle('ReadEcho - Ollama Test')
        self.setGeometry(300, 300, 500, 400)

        layout = QVBoxLayout()

        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        layout.addWidget(self.result_display)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter book name or thoughts...")
        layout.addWidget(self.input_field)

        self.btn = QPushButton('Ask AI')
        self.btn.clicked.connect(self.call_ollama)
        layout.addWidget(self.btn)

        self.setLayout(layout)

    def call_ollama(self):
        user_input = self.input_field.text()
        if not user_input:
            return

        self.result_display.append(f"<b>User:</b> {user_input}")
        
        try:
            # 这里的 model 确保是你电脑上有的，比如 qwen2.5:7b 或 llama3
            # 如果不确定，可以在命令行输入 ollama list 查看
            response = ollama.chat(model='qwen2.5:7b', messages=[
                {
                    'role': 'user',
                    'content': f'Summary this book or organize the thoughts: {user_input}',
                },
            ])
            ai_msg = response['message']['content']
            self.result_display.append(f"<b>AI:</b> {ai_msg}\n")
        except Exception as e:
            self.result_display.append(f"<b>Error:</b> {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ReadEchoTest()
    ex.show()
    sys.exit(app.exec())