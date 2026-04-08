ReadEcho Pro - GPU Accelerated Reading Assistant
功能描述：
这是一个基于PyQt6的桌面应用程序，集成了OpenAI Whisper语音识别和Ollama大语言模型，
用于辅助阅读和笔记记录。
主要功能模块：
1. 数据库管理 (DBManager)
    - 使用SQLite存储笔记
    - 支持保存笔记标题、内容和类型
2. 模型加载线程 (ModelLoaderThread)
    - 在后台预加载Whisper模型
    - 支持GPU加速（CUDA）
3. AI处理线程 (AIProcessThread)
    - 生成摘要：根据书籍标题调用Ollama生成中文摘要
    - 语音笔记：使用Whisper进行语音转文本，再用Ollama优化文本质量
4. 主应用窗口 (ReadEchoPro)
    - 书籍标题输入框
    - 内容显示区域
    - 生成摘要按钮：输入书名自动生成摘要
    - 录音按钮：录制10秒音频，自动转录并生成读书笔记
核心特性：
- GPU加速（支持NVIDIA CUDA）
- 异步处理，不阻塞UI
- 深色主题界面
- 自动保存笔记到数据库
