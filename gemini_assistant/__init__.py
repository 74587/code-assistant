"""
Gemini Screenshot Assistant
一个基于PyQt6的截图AI分析工具
"""

__version__ = "2.0.0"
__author__ = "Gemini Assistant Team"
__description__ = "AI-powered screenshot analysis tool"

# 导出主要类
from .core.config_manager import ConfigManager
from .core.log_manager import LogManager
from .core.single_instance import SingleInstance
from .services.network_utils import NetworkUtils

__all__ = [
    "ConfigManager",
    "LogManager",
    "SingleInstance",
    "NetworkUtils"
]