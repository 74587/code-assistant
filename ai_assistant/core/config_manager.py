"""
配置管理模块
处理应用程序配置的加载、保存和验证
"""

import os
import json
from typing import Any, Dict, Optional
from ..utils.constants import CONFIG_FILE
from .config_models import (
    AppConfig, PromptConfig, HotkeyConfig,
    GeminiProviderConfig, GPTProviderConfig, UIConfig,
    ConfigValidator
)


class ConfigManager:
    """配置管理器 - 简化版"""

    def __init__(self):
        self.config_file = CONFIG_FILE
        self._app_config: Optional[AppConfig] = None
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 检查是否需要迁移旧配置
                if self._is_legacy_config(data):
                    data = self._migrate_legacy_config(data)
                    self._save_to_file(data)

                self._app_config = AppConfig.from_dict(data)
            else:
                # 配置文件不存在，尝试从示例文件复制
                self._create_config_from_example()

        except json.JSONDecodeError as e:
            # JSON 解析错误 - 配置文件格式损坏
            self._handle_config_error(f"配置文件格式错误: {e}")
        except Exception as e:
            # 其他错误
            self._handle_config_error(f"配置加载失败: {e}")

    def _handle_config_error(self, error_msg: str):
        """处理配置错误"""
        print(f"⚠️ {error_msg}")
        print("正在使用默认配置...")

        # 备份损坏的配置文件
        if os.path.exists(self.config_file):
            try:
                backup_name = f"{self.config_file}.corrupted"
                os.rename(self.config_file, backup_name)
                print(f"已将损坏的配置备份到: {backup_name}")
            except Exception:
                pass

        self._app_config = AppConfig.get_default()
        self.save_config()
        print("已创建新的默认配置文件")

    def _create_config_from_example(self):
        """从示例配置文件创建配置"""
        example_file = "model_config.example.json"

        if os.path.exists(example_file):
            # 复制示例文件
            import shutil
            shutil.copy2(example_file, self.config_file)
            print(f"已从 {example_file} 创建配置文件")
            print("请编辑 model_config.json 填入您的 API Key")

            # 加载复制的配置
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._app_config = AppConfig.from_dict(data)
        else:
            # 示例文件也不存在，使用默认配置
            print("未找到配置文件，使用默认配置")
            self._app_config = AppConfig.get_default()
            self.save_config()

    def _is_legacy_config(self, data: Dict[str, Any]) -> bool:
        """检查是否是旧版配置格式"""
        # 旧版配置有这些扁平化的键
        legacy_keys = ["api_key", "gemini_model", "gpt_api_key", "window_width"]
        # 新版配置有 gemini/gpt 作为嵌套对象
        new_keys = ["gemini", "gpt", "ui"]

        has_legacy = any(key in data for key in legacy_keys)
        has_new = all(key in data and isinstance(data[key], dict) for key in new_keys)

        return has_legacy and not has_new

    def _migrate_legacy_config(self, old: Dict[str, Any]) -> Dict[str, Any]:
        """从旧版配置迁移到新版"""
        print("检测到旧版配置，正在迁移...")

        # 创建备份
        self._backup_config(old)

        new_config = {
            "config_version": "2.1.0",
            "provider": old.get("provider", "Gemini"),
            "gemini": {
                "api_key": old.get("api_key", ""),
                "model": old.get("gemini_model", old.get("model", "gemini-2.5-flash")),
                "base_url": old.get("gemini_base_url", "https://generativelanguage.googleapis.com"),
                "use_proxy": old.get("gemini_use_proxy", False),
                "available_models": old.get("available_gemini_models", ["gemini-2.5-flash", "gemini-2.5-pro"])
            },
            "gpt": {
                "api_key": old.get("gpt_api_key", ""),
                "model": old.get("gpt_model", "gpt-4o"),
                "base_url": old.get("gpt_base_url", "https://api.openai.com/v1"),
                "use_proxy": old.get("gpt_use_proxy", False),
                "available_models": old.get("available_gpt_models", ["gpt-4o", "gpt-4o-mini"])
            },
            "proxy": old.get("proxy", ""),
            "ui": {
                "window_width": old.get("window_width", 550),
                "window_height": old.get("window_height", 800),
                "window_min_width": old.get("window_min_width", 500),
                "window_min_height": old.get("window_min_height", 700),
                "background_opacity": old.get("background_opacity", 120)
            },
            "max_screenshot_history": old.get("max_screenshot_history", 10),
            "prompts": old.get("prompts", []),
            "hotkeys": old.get("hotkeys", {})
        }

        print("配置迁移完成！")
        return new_config

    def _backup_config(self, config: Dict[str, Any]):
        """备份配置文件"""
        backup_dir = os.path.join(os.path.dirname(self.config_file), "config_backups")
        os.makedirs(backup_dir, exist_ok=True)

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"config_backup_{timestamp}.json")

        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"旧配置已备份到: {backup_file}")

    def _save_to_file(self, data: Dict[str, Any]) -> bool:
        """保存字典数据到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    @property
    def config(self) -> Dict[str, Any]:
        """获取配置字典（向后兼容）"""
        return self._to_flat_dict()

    def _to_flat_dict(self) -> Dict[str, Any]:
        """转换为扁平化字典（向后兼容旧代码）"""
        cfg = self._app_config
        return {
            # API 配置
            "api_key": cfg.gemini.api_key,
            "proxy": cfg.proxy,

            # 服务商
            "provider": cfg.provider,

            # Gemini
            "model": cfg.gemini.model,  # 别名，用于兼容旧代码
            "gemini_model": cfg.gemini.model,
            "gemini_base_url": cfg.gemini.base_url,
            "gemini_use_proxy": cfg.gemini.use_proxy,
            "available_gemini_models": cfg.gemini.available_models,

            # GPT
            "gpt_api_key": cfg.gpt.api_key,
            "gpt_model": cfg.gpt.model,
            "gpt_base_url": cfg.gpt.base_url,
            "gpt_use_proxy": cfg.gpt.use_proxy,
            "available_gpt_models": cfg.gpt.available_models,

            # UI
            "background_opacity": cfg.ui.background_opacity,
            "window_width": cfg.ui.window_width,
            "window_height": cfg.ui.window_height,
            "window_min_width": cfg.ui.window_min_width,
            "window_min_height": cfg.ui.window_min_height,

            # 功能
            "max_screenshot_history": cfg.max_screenshot_history,
            "prompts": [p.to_dict() for p in cfg.prompts],
            "hotkeys": cfg.hotkeys.to_dict(),
            "enable_capture_protection": cfg.ui.enable_capture_protection if hasattr(cfg.ui, 'enable_capture_protection') else True,
        }

    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            # 创建备份
            if os.path.exists(self.config_file):
                backup_file = f"{self.config_file}.backup"
                try:
                    import shutil
                    shutil.copy2(self.config_file, backup_file)
                except Exception:
                    pass

            # 保存新配置
            data = self._app_config.to_dict()
            return self._save_to_file(data)

        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（向后兼容）"""
        flat = self._to_flat_dict()
        return flat.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """设置配置值（向后兼容）"""
        cfg = self._app_config

        # 映射扁平化键到新结构
        key_mapping = {
            "api_key": ("gemini", "api_key"),
            "proxy": ("proxy", None),
            "provider": ("provider", None),
            "gemini_model": ("gemini", "model"),
            "gemini_base_url": ("gemini", "base_url"),
            "gemini_use_proxy": ("gemini", "use_proxy"),
            "available_gemini_models": ("gemini", "available_models"),
            "gpt_api_key": ("gpt", "api_key"),
            "gpt_model": ("gpt", "model"),
            "gpt_base_url": ("gpt", "base_url"),
            "gpt_use_proxy": ("gpt", "use_proxy"),
            "available_gpt_models": ("gpt", "available_models"),
            "background_opacity": ("ui", "background_opacity"),
            "window_width": ("ui", "window_width"),
            "window_height": ("ui", "window_height"),
            "max_screenshot_history": ("max_screenshot_history", None),
            "prompts": ("prompts", None),
            "hotkeys": ("hotkeys", None),
            "enable_capture_protection": ("ui", "enable_capture_protection"),
        }

        if key in key_mapping:
            section, attr = key_mapping[key]

            if attr is None:
                # 顶级属性
                if key == "prompts":
                    cfg.prompts = [
                        PromptConfig.from_dict(p) if isinstance(p, dict) else p
                        for p in value
                    ]
                elif key == "hotkeys":
                    cfg.hotkeys = HotkeyConfig.from_dict(value) if isinstance(value, dict) else value
                else:
                    setattr(cfg, section, value)
            else:
                # 嵌套属性
                nested_obj = getattr(cfg, section)
                setattr(nested_obj, attr, value)

        return self.save_config()

    def update(self, updates: Dict[str, Any]) -> bool:
        """批量更新配置"""
        for key, value in updates.items():
            self.set(key, value)
        return self.save_config()

    def reset_to_default(self) -> bool:
        """重置为默认配置"""
        self._app_config = AppConfig.get_default()
        return self.save_config()

    def get_app_config(self) -> AppConfig:
        """获取类型安全的配置对象"""
        return self._app_config

    def validate_api_key(self, provider: str = None) -> bool:
        """验证当前服务商的 API Key"""
        provider = provider or self._app_config.provider
        if provider == "Gemini":
            return ConfigValidator.validate_api_key(self._app_config.gemini.api_key)
        elif provider == "GPT":
            return ConfigValidator.validate_api_key(self._app_config.gpt.api_key)
        return False

    def get_current_provider_config(self) -> Dict[str, Any]:
        """获取当前服务商的配置"""
        provider = self._app_config.provider
        if provider == "Gemini":
            return {
                "api_key": self._app_config.gemini.api_key,
                "model": self._app_config.gemini.model,
                "base_url": self._app_config.gemini.base_url,
                "use_proxy": self._app_config.gemini.use_proxy,
                "proxy": self._app_config.proxy if self._app_config.gemini.use_proxy else ""
            }
        elif provider == "GPT":
            return {
                "api_key": self._app_config.gpt.api_key,
                "model": self._app_config.gpt.model,
                "base_url": self._app_config.gpt.base_url,
                "use_proxy": self._app_config.gpt.use_proxy,
                "proxy": self._app_config.proxy if self._app_config.gpt.use_proxy else ""
            }
        return {}
