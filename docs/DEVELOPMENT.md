# ReadEcho Pro 开发者文档

## 1. 目标与范围

本文件主要包含：

- 工程结构与依赖关系
- 文件说明与职责划分
- 开发计划与实施建议
- 代码规范与测试建议

---

## 2. 工程结构

### 2.1 核心架构

```
main.py
├── config.py
├── app_services.py
├── database_manager.py
├── ai_processor.py
├── recording_manager.py
├── ui_builder.py
├── event_handler.py
├── utils.py
├── validators.py
├── model_cache.py
└── __init__.py
```

### 2.2 模块职责

- `main.py`
  - 应用入口与窗口生命周期管理
  - 初始化服务、UI、信号连接
  - 提供 `closeEvent` 优雅关闭机制

- `config.py`
  - 配置常量
  - 日志系统初始化
  - 样式表和主题配置

- `app_services.py`
  - 服务协调层，封装数据库、AI、录音等功能
  - 提供统一接口给界面调用
  - 管理资源关闭和清理

- `database_manager.py`
  - SQLite 数据库 CRUD
  - 表结构创建、索引、分页查询
  - 输入验证与异常处理

- `ai_processor.py`
  - Whisper 语音识别
  - Ollama 文本生成
  - 异步线程与错误/进度信号

- `recording_manager.py`
  - 音频录制与文件管理
  - 与书籍记录关联

- `ui_builder.py`
  - PyQt6 界面构建
  - 控件布局与按钮配置

- `event_handler.py`
  - UI 事件响应
  - 按钮、输入框、列表等交互逻辑

- `utils.py`
  - 常用工具函数
  - 公共数据处理逻辑

- `validators.py`
  - 输入验证与清理
  - 防注入、防路径遍历

- `model_cache.py`
  - Whisper 模型缓存管理
  - 支持模型加载、卸载、查看缓存

- `__init__.py`
  - 包初始化与导出入口

---

## 3. 文件说明

### 3.1 主要文件

| 文件 | 功能 | 说明 |
|------|------|------|
| `main.py` | 应用入口 | 初始化 UI、服务和事件处理 |
| `config.py` | 配置与日志 | 统一日志、样式和常量 |
| `app_services.py` | 服务层 | 统一调用数据库、AI、录音接口 |
| `database_manager.py` | 数据持久化 | SQLite 操作、查询优化 |
| `ai_processor.py` | AI 逻辑 | 语音转写与智能问答 |
| `recording_manager.py` | 录音管理 | 麦克风录音、文件保存 |
| `ui_builder.py` | 界面构建 | PyQt6 组件布局和样式 |
| `event_handler.py` | 事件响应 | UI 交互逻辑处理 |
| `validators.py` | 输入验证 | 防注入、防路径攻击 |
| `model_cache.py` | 模型缓存 | Whisper 模型加载缓存 |
| `__init__.py` | 包入口 | 统一导出常用类和变量 |

---

## 4. 开发计划

### 4.1 当前阶段目标

- `docs/` 统一说明文档
- 模块化代码架构稳定
- 输入验证与日志系统全覆盖
- AI 与数据库的核心流程稳定运行

### 4.2 下阶段优先级

1. **UI/UX 改进**
   - 优化布局与交互反馈
   - 增加进度提示和错误弹窗

2. **测试体系**
   - 添加单元测试与集成测试
   - 建立 `pytest` 测试目录

3. **依赖管理**
   - 生成 `requirements.txt`
   - 固定核心库版本

4. **打包和部署**
   - 维护 `ReadEcho_Pro.spec`
   - 优化 `update_exe.bat`

5. **性能监控**
   - 加入日志性能统计
   - 建立 AI 处理耗时分析

---

## 5. 开发规范

### 5.1 代码风格

- 使用 `PEP 8` 标准
- 添加类型注解
- 函数应有明确参数和返回值
- 避免全局可变状态

### 5.2 日志与异常

- 使用 `LOGGER` 记录全过程
- `debug`：调试信息
- `info`：正常业务事件
- `warning`：可恢复问题
- `error`：关键失败，使用 `exc_info=True`

### 5.3 输入验证

- 所有用户输入必须验证
- 数据库写入前进行验证
- 路径和文件名必须安全

---

## 6. 测试建议

- `database_manager.py`：验证增删改查、分页、异常 rollback
- `ai_processor.py`：验证模型加载、转录、问答输出
- `validators.py`：验证各种输入边界和非法数据
- `app_services.py`：验证服务调用顺序与资源释放

---

## 7. 版本控制与协作

### 7.1 提交规范

```bash
git checkout -b feature/your-feature
git add .
git commit -m "feat: 添加 XXX 功能"
git push origin feature/your-feature
```

### 7.2 文档更新策略

- 新功能后更新 `docs/CHANGELOG.md`
- 结构或规范改动后更新 `docs/DEVELOPMENT.md`
- 使用说明变更后更新 `docs/README.md`

---

## 8. 参考资料

- PyQt6 文档
- Python logging 文档
- SQLite 文档
- Whisper 与 Ollama 项目文档

---

*本文件为开发者参考文档，适用于功能扩展与维护规划。*