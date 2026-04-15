# ReadEcho Pro 文档中心

## 📌 说明

本文件夹 `docs/` 中只保留三份核心说明文档，分别负责：

- `README.md`：项目说明与使用指南
- `CHANGELOG.md`：每日更新日志与版本记录
- `DEVELOPMENT.md`：工程结构、文件说明与开发计划

如果你需要快速了解项目、安装使用、调试或者开发维护，请直接从这里开始。

---

## 🚀 项目简介

**ReadEcho Pro** 是一个基于 PyQt6 的智能阅读助手，整合了：

- OpenAI Whisper 语音识别
- Ollama 大语言模型
- SQLite 数据库
- GPU 加速和模型缓存

它可以帮助你：

- 语音转文字
- 书籍摘要生成
- 智能问答
- 书架管理
- 录音笔记

---

## ✨ 核心功能

- **语音转写**：Whisper 驱动，支持多种音频格式
- **AI 摘要**：Ollama 自动生成书籍摘要
- **智能问答**：根据书籍内容回答问题
- **书籍管理**：添加、搜索、分页显示书籍
- **主题切换**：深色/浅色模式支持
- **日志诊断**：完整日志记录和错误排查

---

## ⚙️ 运行环境要求

```
Python 3.9+
Windows 10+ / Linux / macOS
推荐：NVIDIA GPU + CUDA
``` 

---

## ▶️ 如何使用

1. 激活项目虚拟环境：
   ```powershell
   & .\venv_ai\Scripts\Activate.ps1
   ```

2. 运行应用：
   ```powershell
   python main.py
   ```

3. 启动后操作：
   - 添加书籍
   - 选择书籍后生成摘要
   - 录制语音笔记并自动转写
   - 提问书籍内容，获得智能回答

---

## 📂 项目结构概览

```
ReadEcho/
├── main.py              # 应用入口
├── config.py            # 配置与日志
├── app_services.py      # 服务协调层
├── database_manager.py  # SQLite 数据库管理
├── ai_processor.py      # Whisper 与 Ollama AI 处理
├── recording_manager.py # 录音管理
├── ui_builder.py        # PyQt6 UI 构建
├── event_handler.py     # 事件处理与信号
├── utils.py             # 工具函数
├── validators.py        # 输入验证工具
├── model_cache.py       # Whisper 模型缓存
├── __init__.py          # 包初始化
└── docs/                # 文档仓库
    ├── README.md
    ├── CHANGELOG.md
    └── DEVELOPMENT.md
```

---

## 📌 额外说明

- `docs/CHANGELOG.md` 包含每日更新日志，便于追踪每天的改动
- `docs/DEVELOPMENT.md` 包含详细工程结构、文件说明与开发计划
- `log.txt` 已迁移至 `docs/log.txt`，用于记录原始日更日志

---

## 📘 建议阅读顺序

1. 先读 `docs/README.md`：了解项目与使用方式
2. 再读 `docs/CHANGELOG.md`：查看每日更新记录
3. 最后读 `docs/DEVELOPMENT.md`：理解工程结构与开发计划
