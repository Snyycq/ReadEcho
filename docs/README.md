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
- **在线搜书**：多数据源搜索（OpenLibrary、豆瓣、Google Books），支持本地缓存
- **主题切换**：深色/浅色模式支持，危险按钮自动适配主题
- **终端输出**：固定黑底白字Terminal组件，不受主题切换影响，提供一致的输出体验
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
├── config.py            # 配置、日志与主题样式
├── app_services.py      # 服务协调层
├── database_manager.py  # SQLite 数据库管理
├── ai_processor.py      # Whisper 与 Ollama AI 处理
├── recording_manager.py # 录音管理
├── ui_builder.py        # PyQt6 UI 构建与Terminal组件
├── event_handler.py     # 事件处理、信号与主题适配
├── utils.py             # 工具函数
├── validators.py        # 输入验证工具
├── model_cache.py       # Whisper 模型缓存
├── book_search.py       # 多数据源在线书籍搜索与缓存
├── __init__.py          # 包初始化
└── docs/                # 文档仓库
    ├── README.md         # 项目说明与使用指南
    ├── CHANGELOG.md      # 版本更新日志
    ├── DEVELOPMENT.md    # 开发者文档
    ├── guides/           # 详细指南
    │   └── development_guide.md  # 完整开发指南
    ├── reports/          # 分析报告
    │   ├── code_quality_report.md    # 代码质量报告
    │   ├── optimization_summary.md   # 优化总结报告
    │   └── test_coverage_report.md   # 测试覆盖率报告
    └── archive/          # 归档目录（如有需要）
```

---

## 📌 额外说明

- `docs/CHANGELOG.md` 包含每日更新日志，便于追踪每天的改动
- `docs/DEVELOPMENT.md` 包含详细工程结构、文件说明与开发计划
- `docs/guides/development_guide.md` 包含完整的开发环境设置和构建部署指南
- `docs/reports/` 目录包含代码质量、测试覆盖率和优化总结分析报告

---

## 📘 建议阅读顺序

### 新用户
1. `docs/README.md` - 项目概述与快速开始
2. `docs/guides/development_guide.md` - 开发环境设置与构建

### 开发者
1. `docs/DEVELOPMENT.md` - 工程结构与开发计划
2. `docs/CHANGELOG.md` - 版本更新记录
3. `docs/reports/` - 代码质量和测试覆盖率报告

### 问题排查
1. `docs/guides/development_guide.md` - 故障排除章节
2. `docs/reports/code_quality_report.md` - 已知代码问题
