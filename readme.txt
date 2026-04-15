ReadEcho Pro - GPU Accelerated Reading Assistant

功能描述：
这是一个基于PyQt6的桌面应用程序，集成了OpenAI Whisper语音识别和Ollama大语言模型，
用于辅助阅读和笔记记录。

主要功能：
1. 书架管理
    - 添加新书到书架
    - 模糊搜索书籍
    - 录音与书籍自动关联

2. AI智能功能
    - 摘要生成：输入书名自动调用Ollama生成中文摘要
    - AI问答：针对书籍内容提问，获取AI回答
    - 语音笔记：录音自动转文字并保存

3. 录音系统
    - GPU加速语音识别（Whisper）
    - 录音与书籍绑定
    - 历史录音查看

4. 界面特性
    - 深色/浅色主题切换
    - 两栏布局，书架+操作区
    - 异步处理，不阻塞UI

项目结构（模块化架构）：
├── main.py              # 主入口
├── config.py            # 配置参数和样式表
├── database_manager.py  # 数据库管理
├── ai_processor.py      # AI处理（Whisper + Ollama）
├── recording_manager.py # 录音管理
├── app_services.py      # 服务整合层
├── ui_builder.py        # UI构建
├── event_handler.py     # 事件处理
└── utils.py             # 工具函数

核心特性：
- GPU加速（NVIDIA CUDA）
- 异步处理，不阻塞UI
- 深色/浅色主题
- SQLite数据库存储
- 模块化代码架构

依赖：
- PyQt6
- openai-whisper
- ollama
- sounddevice
- scipy
- torch (CUDA)
