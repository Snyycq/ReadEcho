# ReadEcho Pro 开发指南

本文档提供ReadEcho Pro项目的开发环境设置、构建和部署指南。

## 开发环境设置

### 1. 本地开发环境

#### 使用虚拟环境 (推荐)
```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 激活虚拟环境 (Linux/macOS)
source .venv/bin/activate

# 安装开发依赖
pip install -e ".[dev]"
```

#### 使用Docker开发环境
```bash
# 构建开发镜像
docker-compose --profile dev build

# 运行开发测试
docker-compose --profile dev up readecho-dev

# 进入开发容器
docker-compose --profile dev run --rm readecho-dev bash
```

### 2. 配置管理

#### 环境变量配置
```bash
# 复制环境变量模板
cp .env.template .env

# 编辑配置 (Windows)
notepad .env

# 编辑配置 (Linux/macOS)
nano .env
```

#### 主要配置项
- `FFMPEG_PATH`: FFmpeg可执行文件路径
- `SAMPLE_RATE`: 音频采样率 (默认: 44100)
- `WHISPER_MODEL`: Whisper模型大小 (tiny, base, small, medium, large)
- `OLLAMA_MODEL`: Ollama模型名称
- `LOG_LEVEL`: 日志级别 (DEBUG, INFO, WARNING, ERROR)

## 开发工作流

### 1. 代码质量检查
```bash
# 代码格式化检查
python -m black --check .

# 代码风格检查  
python -m flake8 --max-line-length=100 .

# 类型检查
python -m mypy . --explicit-package-bases

# 自动格式化代码
python -m black .
```

### 2. 测试
```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/unit/test_database_manager.py -v

# 运行测试并生成覆盖率报告
python -m pytest tests/ --cov=. --cov-report=html

# 打开覆盖率报告
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
```

### 3. 构建和打包
```bash
# 构建Python包
python -m build

# 检查包质量
twine check dist/*

# 本地安装测试
pip install dist/*.whl
```

## Docker部署

### 1. 构建Docker镜像
```bash
# 构建生产镜像
docker build -t readecho-pro:latest .

# 构建开发镜像
docker build -t readecho-pro:dev --target dev .

# 查看镜像
docker images | grep readecho
```

### 2. 运行Docker容器
```bash
# 使用docker run
docker run -d \
  --name readecho-pro \
  -v readecho_data:/data \
  -e DATABASE_FILE=/data/readecho.db \
  readecho-pro:latest

# 使用docker-compose
docker-compose up -d

# 查看日志
docker logs -f readecho-pro
```

### 3. Docker开发环境
```bash
# 启动开发环境
docker-compose --profile dev up

# 运行测试
docker-compose --profile dev run --rm readecho-dev pytest

# 清理开发环境
docker-compose --profile dev down -v
```

## CI/CD集成

### GitHub Actions工作流
项目已配置GitHub Actions工作流 (`.github/workflows/ci.yml`):

**自动触发条件:**
- 推送到main/master分支
- 创建Pull Request

**工作流步骤:**
1. 代码格式化检查 (black)
2. 代码风格检查 (flake8)
3. 类型检查 (mypy)
4. 单元测试 (pytest)
5. 覆盖率报告 (pytest-cov)
6. 包构建验证 (build + twine)

### 本地预提交检查
```bash
# 安装预提交钩子
pip install pre-commit
pre-commit install

# 手动运行所有检查
pre-commit run --all-files
```

## 项目结构

```
ReadEcho/
├── main.py              # 应用入口
├── config.py            # 配置管理 (支持.env)
├── app_services.py      # 服务协调层
├── database_manager.py  # 数据库管理
├── ai_processor.py      # AI处理 (Whisper + Ollama)
├── ui_builder.py        # PyQt6 UI构建
├── event_handler.py     # 事件处理
├── recording_manager.py # 录音管理
├── utils.py             # 工具函数
├── validators.py        # 输入验证
├── model_cache.py       # 模型缓存
├── docs/                # 文档
├── tests/               # 测试
├── .github/workflows/   # CI/CD配置
├── Dockerfile           # 容器化配置
├── docker-compose.yml   # 多容器编排
├── pyproject.toml       # 项目配置
└── README-DEV.md        # 本文档
```

## 依赖管理

### 核心依赖
- `PyQt6>=6.4.0` - GUI框架
- `whisper-openai>=20230314` - 语音识别
- `torch>=2.0.0` - 深度学习框架
- `sounddevice>=0.4.6` - 音频录制

### 开发依赖
- `pytest>=7.0.0` - 测试框架
- `black>=23.0.0` - 代码格式化
- `flake8>=6.0.0` - 代码风格检查
- `mypy>=1.0.0` - 类型检查
- `python-dotenv>=1.0.0` - .env文件支持

## 故障排除

### 常见问题

#### 1. FFmpeg路径问题
```bash
# 设置环境变量
export FFMPEG_PATH=/path/to/ffmpeg/bin  # Linux/macOS
set FFMPEG_PATH=C:\path\to\ffmpeg\bin   # Windows
```

#### 2. 依赖安装失败
```bash
# 使用国内镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -e ".[dev]"

# 或使用阿里云镜像
pip install -i https://mirrors.aliyun.com/pypi/simple -e ".[dev]"
```

#### 3. Docker构建失败
```bash
# 清理缓存重建
docker system prune -a
docker build --no-cache -t readecho-pro:latest .
```

#### 4. 测试失败
```bash
# 运行特定测试并查看详细输出
pytest tests/ -v --tb=long

# 只运行失败的测试
pytest --lf -v
```

## 贡献指南

### 1. 开发流程
1. Fork项目仓库
2. 创建功能分支 (`git checkout -b feature/your-feature`)
3. 进行更改并确保测试通过
4. 提交更改 (`git commit -m "feat: description"`)
5. 推送到分支 (`git push origin feature/your-feature`)
6. 创建Pull Request

### 2. 提交规范
- `feat`: 新功能
- `fix`: bug修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具变动

### 3. 代码审查要求
- 所有新代码必须有测试覆盖
- 通过所有代码质量检查
- 更新相关文档
- 保持向后兼容性

## 性能优化

### 1. 构建优化
```dockerfile
# 使用多阶段构建减少镜像大小
# 使用.dockerignore排除不必要的文件
```

### 2. 运行时优化
- 使用模型缓存减少加载时间
- 异步处理耗时操作
- 定期清理临时文件

### 3. 监控和日志
- 配置适当的日志级别
- 监控内存和CPU使用情况
- 设置健康检查端点

## 安全考虑

### 1. 依赖安全
```bash
# 定期更新依赖
pip list --outdated
pip install -U package-name

# 安全检查
pip-audit
```

### 2. 运行时安全
- 使用非root用户运行容器
- 限制容器资源使用
- 定期更新基础镜像

### 3. 数据安全
- 敏感配置使用环境变量
- 数据库文件加密 (如需要)
- 定期备份用户数据

## 支持与反馈

- **问题报告**: 使用GitHub Issues
- **功能请求**: 使用GitHub Discussions
- **文档改进**: 提交Pull Request
- **紧急问题**: 检查日志文件 (`~/.readecho/logs/`)

---

*最后更新: 2026-04-21*