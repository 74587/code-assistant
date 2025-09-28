"""
配置管理模块
处理应用程序配置的加载、保存和验证
"""

import os
import json
from typing import Any, Dict
from ..utils.constants import (
    CONFIG_FILE, DEFAULT_HOTKEYS,
    CONFIG_WINDOW_WIDTH, CONFIG_WINDOW_HEIGHT, CONFIG_WINDOW_MIN_WIDTH, CONFIG_WINDOW_MIN_HEIGHT,
    DEFAULT_GEMINI_MODEL, AVAILABLE_GEMINI_MODELS, DEFAULT_GEMINI_BASE_URL,
    DEFAULT_GPT_MODEL, AVAILABLE_GPT_MODELS, DEFAULT_GPT_BASE_URL, MAX_SCREENSHOT_HISTORY
)
from ..utils.config_migrator import ConfigMigrator


class ConfigManager:
    def __init__(self):
        self.config_file = CONFIG_FILE
        self.migrator = ConfigMigrator(self.config_file)
        self._config_modified = False
        self._config_modified = False
        self.config = self.load_or_create_config()

    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            # API配置
            "api_key": os.getenv("GEMINI_KEY", ""),
            "proxy": os.getenv("CLASH_PROXY", ""),

            # AI服务商配置
            "provider": "Gemini",

            # Gemini配置
            "gemini_model": DEFAULT_GEMINI_MODEL,
            "available_gemini_models": AVAILABLE_GEMINI_MODELS.copy(),
            "gemini_base_url": DEFAULT_GEMINI_BASE_URL,
            "gemini_use_proxy": False,
            # GPT配置
            "gpt_api_key": "sk-FbfcCVp4Qzh5WIXX8kMNI8gLUoBSH4c6ZzdwEbM2tiz0obDj",
            "gpt_model": DEFAULT_GPT_MODEL,
            "gpt_base_url": DEFAULT_GPT_BASE_URL,
            "gpt_use_proxy": False,
            "available_gpt_models": AVAILABLE_GPT_MODELS.copy(),

            # 界面配置
            "background_opacity": 120,
            "window_width": CONFIG_WINDOW_WIDTH,
            "window_height": CONFIG_WINDOW_HEIGHT,
            "window_min_width": CONFIG_WINDOW_MIN_WIDTH,
            "window_min_height": CONFIG_WINDOW_MIN_HEIGHT,

            # 功能配置
            "max_screenshot_history": MAX_SCREENSHOT_HISTORY,

            # 用户自定义
            "prompts": [
                {
                    "name": "代码实现助手",
                    "hotkey": "alt+1",
                    "content": "你是一个专业的java代码实现助手。请分析这张截图中的内容，并提供相应的代码实现。\n要求：\n1.  提供可运行的代码即可，所有的解释通过代码注释提供，注释尽量口语化，避免使用太书面和生涩的词汇\n2. 代码实现逻辑尽量以最佳性能实现，在此基础上实现逻辑尽量简介"
                },
                {
                    "name": "详细分析专家",
                    "hotkey": "alt+2",
                    "content": "你是一个详细的java技术分析专家。请仔细分析这张截图中的内容，并提找到接入图中的问题：\n1. 详细的技术分析\n2. 可能的实现方案\n3. 最佳实践建议\n4. 潜在的问题和解决方案\n5. 相关的代码示例"
                },
                {
                    "name": "问题回答助手",
                    "hotkey": "alt+3",
                    "content": "你是一个java问题回答助手，你需要识别截图中的问题，代码结构和一些其他代码信息，来代码补全对应的未完成的代码"
                }
            ],
            "hotkeys": DEFAULT_HOTKEYS.copy()
        }

    def load_or_create_config(self) -> Dict[str, Any]:
        """加载或创建配置文件，自动迁移旧配置"""
        try:
            # 使用迁移器处理配置（包括创建默认配置和迁移旧配置）
            config = self.migrator.migrate_if_needed()

            # 验证和修复配置（向后兼容性检查）
            config = self.validate_and_fix_config(config)
            if getattr(self, '_config_modified', False):
                self.config = config
                self.save_config()
                self._config_modified = False
            return config

        except Exception as e:
            print(f"配置加载/迁移失败: {e}。将使用默认配置。")
            return self.migrator._get_default_config()

    def validate_and_fix_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证并修复配置"""
        default_config = self.get_default_config()
        modified = False

        # 确保必要的键存在
        for key, default_value in default_config.items():
            if key not in config:
                config[key] = default_value
                print(f"配置中缺少 '{key}'，已使用默认值")
                modified = True

        # 验证数据类型
        if not isinstance(config.get("background_opacity"), int):
            config["background_opacity"] = 120
            print("背景透明度配置无效，已重置为默认值")
            modified = True

        if config.get("window_min_width", 0) < CONFIG_WINDOW_MIN_WIDTH:
            config["window_min_width"] = CONFIG_WINDOW_MIN_WIDTH
            modified = True
        if config.get("window_width", 0) < CONFIG_WINDOW_WIDTH:
            config["window_width"] = CONFIG_WINDOW_WIDTH
            modified = True

        if not isinstance(config.get("prompts"), list):
            config["prompts"] = default_config["prompts"]
            modified = True

        migration_map = {
            "代码实现助手": "alt+1",
            "详细分析专家": "alt+2",
            "问题回答助手": "alt+3",
        }
        for prompt in config.get("prompts", []):
            name = prompt.get("name")
            hotkey = prompt.get("hotkey", "").lower()
            if name in migration_map and hotkey in {"alt+z", "alt+x", "alt+c"}:
                prompt["hotkey"] = migration_map[name]
                modified = True

        if modified:
            self._config_modified = True
        return config
    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            # 创建备份
            if os.path.exists(self.config_file):
                backup_file = f"{self.config_file}.backup"
                try:
                    os.rename(self.config_file, backup_file)
                except Exception:
                    pass

            # 保存新配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            # 如果保存失败，尝试恢复备份
            backup_file = f"{self.config_file}.backup"
            if os.path.exists(backup_file):
                try:
                    os.rename(backup_file, self.config_file)
                    print("已恢复配置文件备份")
                except Exception:
                    pass
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持嵌套路径访问（如 'ai_providers.gemini.api_key'）"""
        # 首先尝试直接访问（向后兼容）
        if key in self.config:
            return self.config[key]

        # 检查兼容性配置
        if "_compatibility" in self.config and key in self.config["_compatibility"]:
            return self.config["_compatibility"][key]

        # 支持嵌套路径访问
        if "." in key:
            keys = key.split(".")
            value = self.config
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value

        return default

    def set(self, key: str, value: Any) -> bool:
        """设置配置值并保存，支持嵌套路径和兼容性更新"""
        # 如果是嵌套路径
        if "." in key:
            keys = key.split(".")
            config = self.config

            # 导航到最后一级的父对象
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]

            # 设置最终值
            config[keys[-1]] = value
        else:
            # 直接设置
            self.config[key] = value

        # 同时更新兼容性配置以保持向后兼容
        self._update_compatibility_config(key, value)

        return self.save_config()

    def _update_compatibility_config(self, key: str, value: Any):
        """更新兼容性配置映射"""
        if "_compatibility" not in self.config:
            self.config["_compatibility"] = {}

        # 映射新配置路径到旧的扁平化键名
        compatibility_mappings = {
            "ai_providers.current_provider": "provider",
            "ai_providers.gemini.api_key": "api_key",
            "ai_providers.gemini.base_url": "gemini_base_url",
            "ai_providers.gemini.use_proxy": "gemini_use_proxy",
            "ai_providers.gemini.model": ["gemini_model", "model"],
            "ai_providers.gpt.api_key": "gpt_api_key",
            "ai_providers.gpt.model": "gpt_model",
            "ai_providers.gpt.base_url": "gpt_base_url",
            "ai_providers.gpt.use_proxy": "gpt_use_proxy",
            "network.proxy": "proxy",
            "ui.window.width": "window_width",
            "ui.window.height": "window_height",
            "ui.window.min_width": "window_min_width",
            "ui.window.min_height": "window_min_height",
            "ui.overlay.background_opacity": "background_opacity",
            "ui.display.show_log_tab": "show_log_tab",
            "features.screenshot.max_history": "max_screenshot_history",
            "features.prompts": "prompts",
            "features.hotkeys": "hotkeys"
        }

        # 如果key是新路径，同时更新对应的旧键名
        if key in compatibility_mappings:
            old_keys = compatibility_mappings[key]
            if isinstance(old_keys, list):
                for old_key in old_keys:
                    self.config["_compatibility"][old_key] = value
            else:
                self.config["_compatibility"][old_keys] = value

        # 如果key是旧的键名，直接更新兼容性配置
        if not "." in key:
            self.config["_compatibility"][key] = value

    def update(self, updates: Dict[str, Any]) -> bool:
        """批量更新配置"""
        self.config.update(updates)
        return self.save_config()

    def reset_to_default(self) -> bool:
        """重置为默认配置"""
        self.config = self.get_default_config()
        return self.save_config()

    def get_config_backup_path(self) -> str:
        """获取配置备份文件路径"""
        return f"{self.config_file}.backup"