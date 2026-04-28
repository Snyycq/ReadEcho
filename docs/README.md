# ReadEcho Pro 文档中心

## 说明

本文件夹 `docs/` 中只保留三份核心说明文档，分别负责：

- `README.md`：项目说明与使用指南
- `CHANGELOG.md`：每日更新日志与版本记录
- `DEVELOPMENT.md`：工程结构、文件说明与开发计划

如果你需要快速了解项目、安装使用、调试或者开发维护，请直接从这里开始。

---

## 项目简介

**ReadEcho Pro** 是一个基于 PyQt6 的智能阅读助手，整合了：

- DeepSeek / Ollama 大语言模型（支持多模型切换）
- OpenAI Whisper 语音识别（可选，需要虚拟环境）
- EPUB 电子书解析
- SQLite 数据库
- GPU 加速和模型缓存

它可以帮助你：

- 导入和阅读 EPUB 电子书
- 生成书籍总结、思维导图（大文件自动分段处理，带进度显示）
- 语音转文字
- 智能问答
- 书架管理
- 录音笔记

---

## 核心功能

- **EPUB 导入**：支持导入 EPUB 电子书，自动提取元数据和目录
- **AI 总结**：DeepSeek 自动生成书籍摘要，大文件自动分段处理
- **思维导图**：AI 生成树状结构图（Unicode 树状符号），大文件自动分段处理
- **AI 进度显示**：处理过程中实时显示进度（第 1/3 段...）
- **多模型支持**：可切换 deepseek-v4-pro、deepseek-v4-flash、qwen2.5:7b
- **语音转写**：Whisper 驱动，支持多种音频格式（需要虚拟环境）
- **智能问答**：根据书籍内容回答问题
- **书籍管理**：添加、编辑、搜索、分页显示书籍
- **在线搜书**：多数据源搜索（OpenLibrary、豆瓣、Google Books），支持本地缓存
- **笔记编辑**：选中录音笔记可直接编辑修改
- **温暖主题**：米黄色温暖界面，支持暗色主题切换
- **日志诊断**：完整日志记录和错误排查

---

## 运行环境要求

```
Python 3.12+（推荐）或 3.9+
Windows 10+ / Linux / macOS
推荐：NVIDIA GPU + CUDA（用于 Whisper 加速）
```

---

## 如何使用

### 方式一：直接启动（推荐）

双击 `start.bat` 即可启动应用，无需配置虚拟环境。

> 注意：语音转录功能需要虚拟环境，详见方式二。

### 方式二：使用虚拟环境启动

如需使用语音转录功能，请使用虚拟环境：

```bash
# 启动应用（虚拟环境模式）
start.bat --venv

# 或手动激活虚拟环境后运行
.\venv_ai\Scripts\activate
python main.py
```

### 基本操作

1. **导入书籍**
   - 点击"导入EPUB"按钮选择电子书文件
   - 或点击"添加书籍"手动添加

2. **AI 功能**
   - 选择书籍后，点击右侧提问区的"+"按钮
   - 选择"书籍总结"生成全书摘要（大文件自动分段处理）
   - 选择"思维导图"生成树状结构图
   - 处理过程中会显示进度信息

3. **模型切换**
   - 在右侧面板顶部选择 AI 模型
   - 选择 qwen2.5:7b 时会自动切换到虚拟环境

4. **语音功能**（需要虚拟环境）
   - 点击麦克风按钮录制语音笔记
   - 自动转录为文字

---

## 项目结构概览

```
ReadEcho/
├── main.py                  # 应用入口
├── config.py                # 配置、日志与主题样式
├── core/                    # 核心业务逻辑
│   ├── __init__.py
│   ├── epub_reader.py       # EPUB 电子书解析
│   ├── database_manager.py  # SQLite 数据库管理
│   └── model_cache.py       # Whisper 模型缓存
├── services/                # 服务层
│   ├── __init__.py
│   ├── app_services.py      # 服务协调层
│   ├── ai_processor.py      # AI 处理（含分段处理线程）
│   ├── recording_manager.py # 录音管理
│   └── book_search.py       # 在线书籍搜索与缓存
├── ui/                      # 界面层
│   ├── __init__.py
│   ├── ui_builder.py        # PyQt6 UI 构建
│   └── event_handler.py     # 事件处理与信号
├── utils/                   # 工具模块
│   ├── __init__.py
│   └── validators.py        # 输入验证工具
├── scripts/
│   └── start.bat            # 启动脚本
├── tests/                   # 测试
└── docs/                    # 文档
    ├── README.md
    ├── CHANGELOG.md
    └── DEVELOPMENT.md
```

---

## AI 模型配置

### DeepSeek（默认）

- 模型：deepseek-v4-pro / deepseek-v4-flash
- 需要 API Key（已内置）
- 无需本地部署

### Ollama（本地）

- 模型：qwen2.5:7b
- 需要本地安装 Ollama
- 需要使用虚拟环境启动

### 配置文件

- 环境变量：`.env` 文件
- 模型选择：`~/.readecho/model_config.txt`
- 日志目录：`~/.readecho/logs/`

---

## 常见问题

### Q: 书籍总结显示"无法获取内容"？

A: 该书籍不是通过 EPUB 导入的，没有电子书文件。请使用"导入EPUB"功能添加电子书。

### Q: 大书的总结准确吗？

A: 大文件会自动分段处理（每段约 4000 字符），逐段总结后合并。处理过程中会显示进度信息。总结基于 EPUB 原文内容，不是联网搜索。

### Q: 选择 qwen2.5:7b 后应用没有变化？

A: 选择本地模型后需要重启应用。选择时会弹窗确认是否重启。

### Q: 语音转录功能不可用？

A: 语音功能需要虚拟环境和 torch 依赖。请使用 `start.bat --venv` 启动。

### Q: 如何切换回暗色主题？

A: 在 `config.py` 中修改 `STYLESHEET = DARK_STYLESHEET`。
