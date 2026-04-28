"""
ReadEcho Pro 配置文件
包含应用程序的配置参数、样式表和常量
支持环境变量配置：从环境变量读取，回退到默认值
使用 .env 文件：在项目根目录创建 .env 文件（参考 .env.template）
"""

# flake8: noqa E501
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Union

# 尝试加载 python-dotenv（可选）
try:
    from dotenv import load_dotenv

    # 从项目根目录加载 .env 文件
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"已加载环境变量文件: {env_path}")
    else:
        print("未找到 .env 文件，使用默认配置和环境变量")
except ImportError:
    # python-dotenv 未安装，仅使用系统环境变量
    print("python-dotenv 未安装，仅使用系统环境变量")
    pass


def get_env_var(name: str, default: Union[str, int, bool, None] = None) -> Optional[str]:
    """从环境变量获取值，支持类型转换"""
    value = os.environ.get(name)
    if value is None:
        return default
    return value


def get_env_int(name: str, default: int) -> int:
    """从环境变量获取整数值"""
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def get_env_bool(name: str, default: bool) -> bool:
    """从环境变量获取布尔值"""
    value = os.environ.get(name)
    if value is None:
        return default
    value_lower = value.lower()
    if value_lower in ("true", "1", "yes", "on"):
        return True
    elif value_lower in ("false", "0", "no", "off"):
        return False
    return default


def get_env_log_level(name: str, default: str) -> int:
    """从环境变量获取日志级别"""
    value = os.environ.get(name, default).upper()
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(value, logging.INFO)


# --- 日志系统配置 ---
def setup_logging():
    """配置应用程序日志系统，支持环境变量配置"""
    # 从环境变量获取日志目录，回退到默认值
    log_dir_env = get_env_var("LOG_DIR", ".readecho/logs")
    if log_dir_env.startswith(".") or not os.path.isabs(log_dir_env):
        # 相对路径，相对于用户主目录
        log_dir = Path.home() / Path(log_dir_env)
    else:
        # 绝对路径
        log_dir = Path(log_dir_env)

    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("readecho")
    logger.setLevel(get_env_log_level("LOG_LEVEL", "DEBUG"))

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(get_env_log_level("LOG_LEVEL", "INFO"))

    # 文件处理器（轮转日志）
    max_bytes = get_env_int("LOG_MAX_BYTES", 5 * 1024 * 1024)  # 默认 5MB
    backup_count = get_env_int("LOG_BACKUP_COUNT", 5)

    file_handler = RotatingFileHandler(
        log_dir / "readecho.log", maxBytes=max_bytes, backupCount=backup_count
    )
    file_handler.setLevel(get_env_log_level("LOG_LEVEL", "DEBUG"))

    # 日志格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.info(f"日志系统初始化完成，日志目录: {log_dir}")
    logger.info(f"日志级别: {logging.getLevelName(logger.level)}")
    return logger


LOGGER = setup_logging()

# --- FFMPEG 配置 ---
# 从环境变量 FFMPEG_PATH 读取，自动检测或回退到默认值
import shutil


def _find_ffmpeg() -> Optional[str]:
    """自动发现ffmpeg：环境变量 → PATH → 常见安装位置"""
    # 1. 检查环境变量
    env_path = get_env_var("FFMPEG_PATH", "")
    if env_path:
        candidate = Path(env_path) / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
        if candidate.exists():
            return str(candidate.parent)
        # 也检查路径本身是否就是目录
        if Path(env_path).is_dir():
            ffmpeg_in_dir = Path(env_path) / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
            if ffmpeg_in_dir.exists():
                return str(Path(env_path))

    # 2. 检查系统PATH中是否已有ffmpeg
    if shutil.which("ffmpeg"):
        return None  # 已在PATH中，无需额外处理

    # 3. 常见安装位置
    common_paths = [
        Path.home() / "ffmpeg" / "bin",
        Path("/usr/local/bin"),
        Path("/opt/ffmpeg/bin"),
    ]
    for p in common_paths:
        ffmpeg_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        if (p / ffmpeg_name).exists():
            return str(p)

    LOGGER.warning("FFmpeg未找到，请设置FFMPEG_PATH环境变量")
    return None


FFMPEG_PATH = _find_ffmpeg()

# 将ffmpeg路径添加到系统PATH（如果路径存在且不在PATH中）
if FFMPEG_PATH and os.path.exists(FFMPEG_PATH):
    if FFMPEG_PATH not in os.environ.get("PATH", ""):
        os.environ["PATH"] += os.pathsep + FFMPEG_PATH
        LOGGER.info(f"已将FFMPEG路径添加到系统PATH: {FFMPEG_PATH}")
elif FFMPEG_PATH:
    LOGGER.warning(f"FFMPEG路径不存在: {FFMPEG_PATH}")

# --- 应用程序常量 ---
# 从环境变量读取，回退到默认值
SAMPLE_RATE = get_env_int("SAMPLE_RATE", 44100)  # 音频采样率
RECORDING_DURATION = get_env_int("RECORDING_DURATION", 30)  # 录音时长（秒）
DATABASE_FILE = get_env_var("DATABASE_FILE", "readecho_v1.db")
TEMP_AUDIO_FILE = get_env_var("TEMP_AUDIO_FILE", "temp_note.wav")

# 记录配置值
LOGGER.info(f"音频采样率: {SAMPLE_RATE} Hz")
LOGGER.info(f"录音时长: {RECORDING_DURATION} 秒")
LOGGER.info(f"数据库文件: {DATABASE_FILE}")
LOGGER.info(f"临时音频文件: {TEMP_AUDIO_FILE}")

# --- 样式表 ---
# 米黄色温暖主题样式（默认）
WARM_STYLESHEET = """
    QWidget {
        background-color: #F5F0E8;
        color: #3D3229;
        font-family: 'Segoe UI';
    }
    QTextEdit {
        background-color: #FFFBF5;
        border: 1px solid #D4C5A9;
        border-radius: 5px;
        padding: 10px;
        color: #3D3229;
    }
    QLineEdit {
        background-color: #FFFBF5;
        border: 1px solid #D4C5A9;
        padding: 5px;
        border-radius: 3px;
        color: #3D3229;
    }
    QPushButton {
        background-color: #C9A96E;
        border-radius: 5px;
        padding: 8px;
        font-weight: bold;
        color: #FFFFFF;
    }
    QPushButton:hover {
        background-color: #B8944D;
    }
    QPushButton:disabled {
        background-color: #D4C5A9;
        color: #8B7D6B;
    }
    QPushButton.danger {
        background-color: #C75050;
        color: #ffffff;
    }
    QPushButton.danger:hover {
        background-color: #A84040;
    }
    QListWidget {
        background-color: #FFFBF5;
        border: 1px solid #D4C5A9;
        border-radius: 5px;
        color: #3D3229;
    }
    QListWidget::item:selected {
        background-color: #E8DCC8;
        color: #3D3229;
    }
    QListWidget::item:hover {
        background-color: #F0E8D8;
    }
    QGroupBox {
        font-weight: bold;
        border: 2px solid #D4C5A9;
        border-radius: 5px;
        margin-top: 10px;
        color: #5C4A32;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px 0 5px;
    }
    QSplitter::handle {
        background-color: #D4C5A9;
    }
"""

# 暗色主题样式（可选）
DARK_STYLESHEET = """
    QWidget {
        background-color: #2b2b2b;
        color: #ffffff;
        font-family: 'Segoe UI';
    }
    QTextEdit {
        background-color: #2b2b2b;
        border: 1px solid #3c3c3c;
        border-radius: 5px;
        padding: 10px;
    }
    QLineEdit {
        background-color: #3c3c3c;
        border: 1px solid #555555;
        padding: 5px;
        border-radius: 3px;
        color: #ffffff;
    }
    QPushButton {
        background-color: #0d6efd;
        border-radius: 5px;
        padding: 8px;
        font-weight: bold;
        color: #ffffff;
    }
    QPushButton:hover {
        background-color: #0b5ed7;
    }
    QPushButton:disabled {
        background-color: #444444;
        color: #888888;
    }
    QPushButton.danger {
        background-color: #dc3545;
        color: #ffffff;
    }
    QPushButton.danger:hover {
        background-color: #c82333;
    }
    QListWidget {
        background-color: #3c3c3c;
        border: 1px solid #555555;
        border-radius: 5px;
    }
    QListWidget::item:selected {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    QListWidget::item:hover {
        background-color: #2a2a2a;
    }
    QGroupBox {
        font-weight: bold;
        border: 2px solid #555555;
        border-radius: 5px;
        margin-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px 0 5px;
    }
    QSplitter::handle {
        background-color: #555555;
    }
"""

# 默认使用米黄色主题
STYLESHEET = WARM_STYLESHEET

# --- AI 配置 ---
# 从环境变量读取，回退到默认值
WHISPER_MODEL = get_env_var(
    "WHISPER_MODEL", "tiny"
)  # Whisper模型大小 (tiny, base, small, medium, large)

# AI 提供商选择：ollama 或 deepseek
AI_PROVIDER = get_env_var("AI_PROVIDER", "deepseek")

# DeepSeek 配置（首选）
DEEPSEEK_API_KEY = get_env_var("DEEPSEEK_API_KEY", "your_api_key_here")
DEEPSEEK_BASE_URL = get_env_var("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = get_env_var("DEEPSEEK_MODEL", "deepseek-v4-pro")

# Ollama 配置（备用）
OLLAMA_MODEL = get_env_var("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_BASE_URL = get_env_var("OLLAMA_BASE_URL", "http://localhost:11434")

# --- 模型选择持久化 ---
_MODEL_CONFIG_FILE = Path.home() / ".readecho" / "model_config.txt"

def get_selected_model() -> str:
    """获取上次选择的模型"""
    try:
        if _MODEL_CONFIG_FILE.exists():
            return _MODEL_CONFIG_FILE.read_text().strip()
    except Exception:
        pass
    return DEEPSEEK_MODEL

def save_selected_model(model: str) -> None:
    """保存选择的模型"""
    try:
        _MODEL_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        _MODEL_CONFIG_FILE.write_text(model)
    except Exception as e:
        LOGGER.warning(f"保存模型配置失败: {e}")

# 记录AI配置
LOGGER.info(f"Whisper模型: {WHISPER_MODEL}")
LOGGER.info(f"AI提供商: {AI_PROVIDER}")
if AI_PROVIDER == "deepseek":
    LOGGER.info(f"DeepSeek模型: {DEEPSEEK_MODEL}")
else:
    LOGGER.info(f"Ollama模型: {OLLAMA_MODEL}")

# --- 在线搜索配置 ---
# 从环境变量读取，回退到默认值
DOUBAN_API_KEY = get_env_var("DOUBAN_API_KEY", "")  # 豆瓣API密钥
GOOGLE_BOOKS_API_KEY = get_env_var("GOOGLE_BOOKS_API_KEY", "")  # Google Books API密钥
SEARCH_CACHE_ENABLED = get_env_bool("SEARCH_CACHE_ENABLED", True)  # 启用搜索缓存
SEARCH_CACHE_TTL = get_env_int("SEARCH_CACHE_TTL", 604800)  # 缓存过期时间（秒），默认7天
SEARCH_TIMEOUT = get_env_int("SEARCH_TIMEOUT", 10)  # 搜索超时时间（秒）

# 网络搜索配置
WEB_SEARCH_ENABLED = get_env_bool("WEB_SEARCH_ENABLED", True)  # 启用网络搜索
WEB_SEARCH_TIMEOUT = get_env_int("WEB_SEARCH_TIMEOUT", 15)  # 网络搜索超时时间（秒）
WEB_SEARCH_MAX_RESULTS = get_env_int("WEB_SEARCH_MAX_RESULTS", 50)  # 网络搜索最大结果数
WEB_SEARCH_RETRY_ATTEMPTS = get_env_int("WEB_SEARCH_RETRY_ATTEMPTS", 3)  # 网络搜索重试次数
WEB_SEARCH_RETRY_DELAY = get_env_int("WEB_SEARCH_RETRY_DELAY", 2)  # 网络搜索重试延迟（秒）

# 记录搜索配置
if DOUBAN_API_KEY:
    LOGGER.info("豆瓣API密钥已配置")
else:
    LOGGER.info("豆瓣API密钥未配置，豆瓣搜索将不可用")
if GOOGLE_BOOKS_API_KEY:
    LOGGER.info("Google Books API密钥已配置")
else:
    LOGGER.info("Google Books API密钥未配置，Google Books搜索将不可用")
LOGGER.info(f"搜索缓存: {'启用' if SEARCH_CACHE_ENABLED else '禁用'}")
LOGGER.info(f"缓存TTL: {SEARCH_CACHE_TTL}秒")

# --- 窗口配置 ---
# 从环境变量读取，回退到默认值
WINDOW_TITLE = get_env_var("WINDOW_TITLE", "ReadEcho Pro - GPU Accelerated")
WINDOW_WIDTH = get_env_int("WINDOW_WIDTH", 900)
WINDOW_HEIGHT = get_env_int("WINDOW_HEIGHT", 700)
WINDOW_X = get_env_int("WINDOW_X", 300)
WINDOW_Y = get_env_int("WINDOW_Y", 300)

# 主题配置
DEFAULT_THEME = get_env_var("DEFAULT_THEME", "dark")  # dark 或 light

# 记录窗口配置
LOGGER.info(f"窗口标题: {WINDOW_TITLE}")
LOGGER.info(f"窗口尺寸: {WINDOW_WIDTH}x{WINDOW_HEIGHT}")
LOGGER.info(f"窗口位置: ({WINDOW_X}, {WINDOW_Y})")
LOGGER.info(f"默认主题: {DEFAULT_THEME}")

# --- 高级配置 ---
DEBUG = get_env_bool("DEBUG", False)
PRELOAD_MODELS = get_env_bool("PRELOAD_MODELS", True)
PRELOAD_DELAY = get_env_int("PRELOAD_DELAY", 500)

if DEBUG:
    LOGGER.info("调试模式已启用")
    LOGGER.info(f"模型预加载: {PRELOAD_MODELS}, 延迟: {PRELOAD_DELAY}ms")
