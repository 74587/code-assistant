"""
应用程序常量定义
"""

# 应用程序信息
APP_NAME = "AIScreenshotAssistant"
APP_VERSION = "2.0.0"

# 文件和目录
CONFIG_FILE = "model_config.json"
LOG_DIR_NAME = ".ai_assistant"
LOG_SUBDIR = "logs"

# 窗口尺寸
OVERLAY_WIDTH = 960
OVERLAY_HEIGHT = 360
CONFIG_WINDOW_MIN_WIDTH = 900
CONFIG_WINDOW_MIN_HEIGHT = 700
CONFIG_WINDOW_WIDTH = 1100
CONFIG_WINDOW_HEIGHT = 800

# 内存限制


MAX_SCREENSHOT_HISTORY = 10
MAX_LOG_ENTRIES = 1000

# 日志配置
LOG_RETENTION_DAYS = 7
SHOW_LOG_TAB = True  # 是否显示日志选项卡

# API提供商配置
AVAILABLE_PROVIDERS = ["Gemini", "GPT"]
DEFAULT_PROVIDER = "Gemini"

# 通用API配置（这些是程序运行参数，非模型配置）
API_TIMEOUT = 30
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 2

# 网络配置
NETWORK_TIMEOUT = 5

# 图片处理
MAX_IMAGE_SIZE_MB = 5
MAX_TOTAL_SIZE_MB = 20
MAX_THUMBNAIL_SIZE = (1920, 1080)

# 热键相关
SUPPORTED_PROXY_SCHEMES = ["http", "https", "socks5"]
MIN_API_KEY_LENGTH = 20

# 默认热键
DEFAULT_HOTKEYS = {
    "toggle": "alt+q",
    "screenshot_only": "alt+w",
    "clear_screenshots": "alt+v",
    "scroll_up": "alt+up",
    "scroll_down": "alt+down"
}

# 默认提示词（将从配置文件读取，这里留空）
DEFAULT_PROMPTS = []

USE_FLUENT_THEME = True

# UI样式颜色
COLORS = {
    "primary": "#007bff",
    "success": "#28a745",
    "danger": "#dc3545",
    "warning": "#ffc107",
    "secondary": "#6c757d",
    "light": "#f8f9fa",
    "dark": "#343a40"
}

# 状态指示器颜色
STATUS_COLORS = {
    "running": "#28a745",
    "stopped": "#dc3545",
    "error": "#dc3545"
}

# 截图模式配置
SCREENSHOT_MODE = {
    "use_selector": True,  # 是否使用智能选择器
    "wait_time": 3000,     # 等待时间（毫秒）
    "confirm_time": 2000,  # 确认时间（毫秒）
    "minimize_focus_impact": True,  # 是否最小化焦点影响
    "backup_mode": "traditional"    # 备选模式: "traditional" 或 "instant"
}

# 防截屏保护配置
# 启用后，浮窗和截图选择器将无法被截图工具捕获
ENABLE_CAPTURE_PROTECTION = True

