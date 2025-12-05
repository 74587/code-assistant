"""
配置数据模型
使用 Pydantic 进行配置验证和类型安全
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import os


@dataclass
class PromptConfig:
    """提示词配置"""
    name: str
    hotkey: str
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"name": self.name, "hotkey": self.hotkey, "content": self.content}

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "PromptConfig":
        return cls(
            name=data.get("name", ""),
            hotkey=data.get("hotkey", ""),
            content=data.get("content", "")
        )


@dataclass
class HotkeyConfig:
    """热键配置"""
    toggle: str = "alt+q"
    screenshot_only: str = "alt+w"
    clear_screenshots: str = "alt+v"
    scroll_up: str = "alt+up"
    scroll_down: str = "alt+down"

    def to_dict(self) -> Dict[str, str]:
        return {
            "toggle": self.toggle,
            "screenshot_only": self.screenshot_only,
            "clear_screenshots": self.clear_screenshots,
            "scroll_up": self.scroll_up,
            "scroll_down": self.scroll_down
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "HotkeyConfig":
        return cls(
            toggle=data.get("toggle", "alt+q"),
            screenshot_only=data.get("screenshot_only", "alt+w"),
            clear_screenshots=data.get("clear_screenshots", "alt+v"),
            scroll_up=data.get("scroll_up", "alt+up"),
            scroll_down=data.get("scroll_down", "alt+down")
        )


@dataclass
class GeminiProviderConfig:
    """Gemini 服务商配置"""
    api_key: str = ""
    model: str = "gemini-2.5-flash"
    base_url: str = "https://generativelanguage.googleapis.com"
    use_proxy: bool = False
    available_models: List[str] = field(default_factory=lambda: [
        "gemini-2.5-flash",
        "gemini-2.5-pro"
    ])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_key": self.api_key,
            "model": self.model,
            "base_url": self.base_url,
            "use_proxy": self.use_proxy,
            "available_models": self.available_models
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GeminiProviderConfig":
        return cls(
            api_key=data.get("api_key", os.getenv("GEMINI_KEY", "")),
            model=data.get("model", "gemini-2.5-flash"),
            base_url=data.get("base_url", "https://generativelanguage.googleapis.com"),
            use_proxy=data.get("use_proxy", False),
            available_models=data.get("available_models", ["gemini-2.5-flash", "gemini-2.5-pro"])
        )


@dataclass
class GPTProviderConfig:
    """GPT 服务商配置"""
    api_key: str = ""
    model: str = "gpt-4o"
    base_url: str = "https://api.openai.com/v1"
    use_proxy: bool = False
    available_models: List[str] = field(default_factory=lambda: [
        "gpt-4o",
        "gpt-4o-mini"
    ])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_key": self.api_key,
            "model": self.model,
            "base_url": self.base_url,
            "use_proxy": self.use_proxy,
            "available_models": self.available_models
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GPTProviderConfig":
        return cls(
            api_key=data.get("api_key", ""),
            model=data.get("model", "gpt-4o"),
            base_url=data.get("base_url", "https://api.openai.com/v1"),
            use_proxy=data.get("use_proxy", False),
            available_models=data.get("available_models", ["gpt-4o", "gpt-4o-mini"])
        )


@dataclass
class UIConfig:
    """界面配置"""
    window_width: int = 550
    window_height: int = 800
    window_min_width: int = 500
    window_min_height: int = 700
    background_opacity: int = 120

    def __post_init__(self):
        # 验证范围
        self.window_width = max(self.window_min_width, self.window_width)
        self.window_height = max(self.window_min_height, self.window_height)
        self.background_opacity = max(0, min(255, self.background_opacity))

    def to_dict(self) -> Dict[str, int]:
        return {
            "window_width": self.window_width,
            "window_height": self.window_height,
            "window_min_width": self.window_min_width,
            "window_min_height": self.window_min_height,
            "background_opacity": self.background_opacity
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UIConfig":
        return cls(
            window_width=data.get("window_width", 550),
            window_height=data.get("window_height", 800),
            window_min_width=data.get("window_min_width", 500),
            window_min_height=data.get("window_min_height", 700),
            background_opacity=data.get("background_opacity", 120)
        )


@dataclass
class AppConfig:
    """应用程序完整配置"""
    # 版本信息
    config_version: str = "2.1.0"

    # AI 服务商
    provider: str = "Gemini"
    gemini: GeminiProviderConfig = field(default_factory=GeminiProviderConfig)
    gpt: GPTProviderConfig = field(default_factory=GPTProviderConfig)

    # 网络
    proxy: str = ""

    # 界面
    ui: UIConfig = field(default_factory=UIConfig)

    # 功能
    max_screenshot_history: int = 10
    prompts: List[PromptConfig] = field(default_factory=list)
    hotkeys: HotkeyConfig = field(default_factory=HotkeyConfig)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于保存到 JSON）"""
        return {
            "config_version": self.config_version,
            "provider": self.provider,
            "gemini": self.gemini.to_dict(),
            "gpt": self.gpt.to_dict(),
            "proxy": self.proxy,
            "ui": self.ui.to_dict(),
            "max_screenshot_history": self.max_screenshot_history,
            "prompts": [p.to_dict() for p in self.prompts],
            "hotkeys": self.hotkeys.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        """从字典创建配置对象"""
        prompts_data = data.get("prompts", [])
        prompts = [PromptConfig.from_dict(p) if isinstance(p, dict) else p for p in prompts_data]

        return cls(
            config_version=data.get("config_version", "2.1.0"),
            provider=data.get("provider", "Gemini"),
            gemini=GeminiProviderConfig.from_dict(data.get("gemini", {})),
            gpt=GPTProviderConfig.from_dict(data.get("gpt", {})),
            proxy=data.get("proxy", os.getenv("CLASH_PROXY", "")),
            ui=UIConfig.from_dict(data.get("ui", {})),
            max_screenshot_history=data.get("max_screenshot_history", 10),
            prompts=prompts,
            hotkeys=HotkeyConfig.from_dict(data.get("hotkeys", {}))
        )

    @classmethod
    def get_default(cls) -> "AppConfig":
        """获取默认配置"""
        return cls(
            prompts=[
                PromptConfig(
                    name="代码实现助手",
                    hotkey="alt+1",
                    content="你是一个专业的代码实现助手。请分析这张截图中的内容，并提供相应的代码实现。\n要求：\n1. 提供可运行的代码，解释通过代码注释提供\n2. 代码实现逻辑尽量简洁高效"
                ),
                PromptConfig(
                    name="详细分析专家",
                    hotkey="alt+2",
                    content="你是一个技术分析专家。请仔细分析这张截图中的内容，提供：\n1. 详细的技术分析\n2. 可能的实现方案\n3. 最佳实践建议"
                ),
                PromptConfig(
                    name="问题回答助手",
                    hotkey="alt+3",
                    content="你是一个问题回答助手，识别截图中的问题和代码信息，帮助补全未完成的代码"
                )
            ]
        )


class ConfigValidator:
    """配置验证器"""

    @staticmethod
    def validate_api_key(api_key: str, min_length: int = 10) -> bool:
        """验证 API Key"""
        if not api_key or not isinstance(api_key, str):
            return False
        return len(api_key.strip()) >= min_length

    @staticmethod
    def validate_hotkey(hotkey: str) -> bool:
        """验证热键格式"""
        if not hotkey or not isinstance(hotkey, str):
            return False
        # 简单验证：应该包含修饰键 + 实际按键
        parts = hotkey.lower().split("+")
        if len(parts) < 2:
            return False
        modifiers = {"alt", "ctrl", "shift", "cmd", "win"}
        return any(p in modifiers for p in parts[:-1])

    @staticmethod
    def validate_opacity(opacity: int) -> int:
        """验证并修正透明度值"""
        return max(0, min(255, int(opacity)))

    @staticmethod
    def validate_prompt(prompt: Dict[str, str]) -> bool:
        """验证提示词配置"""
        required_keys = ["name", "hotkey", "content"]
        return all(key in prompt and prompt[key] for key in required_keys)
