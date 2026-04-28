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
├── core/
│   ├── __init__.py
│   ├── epub_reader.py
│   ├── database_manager.py
│   └── model_cache.py
├── services/
│   ├── __init__.py
│   ├── app_services.py
│   ├── ai_processor.py
│   ├── recording_manager.py
│   └── book_search.py
├── ui/
│   ├── __init__.py
│   ├── ui_builder.py
│   └── event_handler.py
├── utils/
│   ├── __init__.py
│   └── validators.py
├── scripts/
│   └── start.bat
├── tests/
└── docs/
```

### 2.2 模块职责

- `main.py`
  - 应用入口与窗口生命周期管理
  - 初始化服务、UI、信号连接
  - 提供 `closeEvent` 优雅关闭机制

- `config.py`
  - 配置常量与路径设置（支持环境变量）
  - 日志系统初始化与管理
  - 主题样式表定义（米黄色温暖主题、暗色主题）
  - AI 模型配置（DeepSeek、Ollama）
  - 模型选择持久化

- `app_services.py`
  - 服务协调层，封装数据库、AI、录音等功能
  - EPUB 导入和内容获取
  - 提供统一接口给界面调用
  - 管理资源关闭和清理

- `database_manager.py`
  - SQLite 数据库 CRUD
  - 表结构创建、索引、分页查询
  - EPUB 书籍字段扩展（file_path、description、toc_json）
  - 输入验证与异常处理

- `ai_processor.py`
  - DeepSeek API 调用（首选）
  - Ollama 本地模型调用（备用）
  - Whisper 语音识别（可选）
  - 统一的 chat_completion 接口
  - 异步线程与错误/进度信号
  - 分段 AI 处理（ChunkedAIThread）：大文件自动分段，逐段总结后合并

- `epub_reader.py`
  - EPUB 电子书解析
  - 元数据提取（标题、作者、简介）
  - 目录结构提取
  - 章节内容获取
  - HTML 到纯文本转换

- `recording_manager.py`
  - 音频录制与文件管理
  - 与书籍记录关联

- `ui_builder.py`
  - PyQt6 界面构建与布局管理
  - 三栏布局（书架、笔记详情、AI对话）
  - 模型选择器
  - AI 功能"+"菜单按钮

- `event_handler.py`
  - UI 事件响应与信号处理
  - EPUB 导入处理
  - AI 功能调用（分段总结、思维导图，通过"+"菜单触发）
  - AI 进度显示
  - 模型切换与虚拟环境重启
  - 按钮状态管理

- `utils.py`
  - 常用工具函数
  - 公共数据处理逻辑

- `validators.py`
  - 输入验证与清理
  - 防注入、防路径遍历

- `model_cache.py`
  - Whisper 模型缓存管理
  - 支持模型加载、卸载、查看缓存

- `book_search.py`
  - 多数据源在线书籍搜索（OpenLibrary、豆瓣、Google Books）
  - 智能缓存机制，减少重复API请求
  - 结果去重和优先级排序

- `__init__.py`
  - 包初始化与导出入口

---

## 3. 文件说明

### 3.1 主要文件

| 文件 | 功能 | 说明 |
|------|------|------|
| `main.py` | 应用入口 | 初始化 UI、服务和事件处理 |
| `config.py` | 配置与主题 | 日志系统、深色/浅色主题样式、CSS样式类定义 |
| `core/epub_reader.py` | EPUB解析 | 电子书元数据、目录、内容提取 |
| `core/database_manager.py` | 数据持久化 | SQLite 操作、查询优化 |
| `core/model_cache.py` | 模型缓存 | Whisper 模型加载缓存 |
| `services/app_services.py` | 服务层 | 统一调用数据库、AI、录音接口 |
| `services/ai_processor.py` | AI逻辑 | 语音转写、智能问答、分段处理线程 |
| `services/recording_manager.py` | 录音管理 | 麦克风录音、文件保存 |
| `services/book_search.py` | 在线搜书 | 多数据源搜索、智能缓存、结果去重 |
| `ui/ui_builder.py` | 界面构建 | PyQt6 组件布局、主题样式适配 |
| `ui/event_handler.py` | 事件响应 | UI 交互逻辑、分段AI处理、进度显示 |
| `utils/validators.py` | 输入验证 | 防注入、防路径攻击 |

---

## 4. 开发计划

### 4.1 当前阶段目标

- `docs/` 统一说明文档
- 模块化代码架构稳定（core/services/ui/utils 四层架构）
- 输入验证与日志系统全覆盖
- AI 分段处理与进度显示
- EPUB 导入与内容获取稳定运行

### 4.2 下阶段优先级

1. **测试体系**
   - 添加单元测试与集成测试
   - 建立 `pytest` 测试目录

2. **依赖管理**
   - 生成 `requirements.txt`
   - 固定核心库版本

3. **打包和部署**
   - 维护 `ReadEcho_Pro.spec`
   - 优化 `update_exe.bat`

4. **性能监控**
   - 加入日志性能统计
   - 建立 AI 处理耗时分析

5. **功能扩展**
   - 章节总结功能（通过"+"菜单）
   - 笔记导出功能

### 4.3 2026-04-21优化工作完成

**已完成优化：**
1. **配置管理优化**：环境变量支持、`.env`文件配置、类型安全获取函数
2. **测试覆盖分析**：生成详细覆盖率报告（总体33%），识别UI层和AI层测试缺失
3. **代码质量扫描**：使用black、flake8、mypy扫描，发现46个问题并制定修复计划
4. **工程化建设**：CI/CD流水线（GitHub Actions）、Docker容器化、开发文档完善
5. **文档结构优化**：统一文档管理，建立清晰的文档结构体系（guides/、reports/目录）
6. **在线搜书增强**：新增`book_search.py`模块，支持多数据源和智能缓存

**优化成果：**
- ✅ 配置灵活性：解决硬编码路径问题
- ✅ 测试可测量性：明确测试盲区，指导测试开发
- ✅ 代码标准化：自动化代码格式化和质量检查
- ✅ 构建自动化：完整的CI/CD流水线
- ✅ 部署标准化：Docker多阶段构建
- ✅ 文档结构化：便于维护和查找

**下一步重点：**
1. 修复flake8识别的46个代码质量问题
2. 提高测试覆盖率到50%以上
3. 运行CI/CD流水线验证配置
4. 优化Docker镜像大小和构建速度
5. 完善在线搜书功能的错误处理和用户体验

**技术债务减少：**
- 配置硬编码问题完全解决
- 测试盲区明确识别
- 代码质量问题全面扫描
- 手动流程自动化替代
- 文档分散问题统一解决

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