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
# 从环境变量 FFMPEG_PATH 读取，回退到默认值
# 注意：路径里用的是双反斜杠 \\ 或者单斜杠 /
FFMPEG_PATH = get_env_var(
    "FFMPEG_PATH", r"E:\ffmpeg-8.1-essentials_build\ffmpeg-8.1-essentials_build\bin"
)

# 将ffmpeg路径添加到系统PATH（如果路径存在且不在PATH中）
if FFMPEG_PATH and os.path.exists(FFMPEG_PATH):
    if FFMPEG_PATH not in os.environ.get("PATH", ""):
        os.environ["PATH"] += os.pathsep + FFMPEG_PATH
        LOGGER.info(f"已将FFMPEG路径添加到系统PATH: {FFMPEG_PATH}")
else:
    LOGGER.warning(f"FFMPEG路径不存在或未配置: {FFMPEG_PATH}")

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
# 深色模式样式
DARK_STYLESHEET = """
    QWidget {
        background-color: #2b2b2b;
        color: #ffffff;
        font-family: 'Segoe UI';
    }
    QTextEdit {
        background-color: #1e1e1e;
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
"""

# 浅色模式样式
LIGHT_STYLESHEET = """
    QWidget { background-color: #f3f4f6; color: #111111; font-family: 'Segoe UI'; }
    QTextEdit { background-color: #ffffff; border: 1px solid #d1d5db; border-radius: 5px; padding: 10px; color: #111111; }
    QLineEdit { background-color: #ffffff; border: 1px solid #9ca3af; padding: 5px; border-radius: 3px; color: #111111; }
    QPushButton { background-color: #2563eb; border-radius: 5px; padding: 8px; font-weight: bold; color: #ffffff; }
    QPushButton:hover { background-color: #1d4ed8; }
    QPushButton:disabled { background-color: #d1d5db; color: #6b7280; }
    QPushButton.danger { background-color: #dc3545; color: #ffffff; }
    QPushButton.danger:hover { background-color: #c82333; }
    QListWidget { background-color: #ffffff; border: 1px solid #d1d5db; border-radius: 5px; }
    QGroupBox { font-weight: bold; border: 2px solid #d1d5db; border-radius: 5px; margin-top: 10px; }
    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }
"""

# --- AI 配置 ---
# 从环境变量读取，回退到默认值
WHISPER_MODEL = get_env_var(
    "WHISPER_MODEL", "tiny"
)  # Whisper模型大小 (tiny, base, small, medium, large)
OLLAMA_MODEL = get_env_var("OLLAMA_MODEL", "qwen2.5:7b")  # Ollama模型名称

# 记录AI配置
LOGGER.info(f"Whisper模型: {WHISPER_MODEL}")
LOGGER.info(f"Ollama模型: {OLLAMA_MODEL}")

# --- 在线搜索配置 ---
# 从环境变量读取，回退到默认值
DOUBAN_API_KEY = get_env_var("DOUBAN_API_KEY", "")  # 豆瓣API密钥
GOOGLE_BOOKS_API_KEY = get_env_var("GOOGLE_BOOKS_API_KEY", "")  # Google Books API密钥
SEARCH_CACHE_ENABLED = get_env_bool("SEARCH_CACHE_ENABLED", True)  # 启用搜索缓存
SEARCH_CACHE_TTL = get_env_int("SEARCH_CACHE_TTL", 604800)  # 缓存过期时间（秒），默认7天
SEARCH_TIMEOUT = get_env_int("SEARCH_TIMEOUT", 10)  # 搜索超时时间（秒）

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
