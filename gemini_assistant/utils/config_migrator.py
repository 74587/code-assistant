"""
配置迁移工具
用于将旧版本配置自动升级到新的配置结构
"""

import json
import os
import shutil
from typing import Dict, Any
from datetime import datetime

class ConfigMigrator:
    """配置迁移器"""

    def __init__(self, config_file_path: str):
        self.config_file_path = config_file_path
        self.backup_dir = os.path.join(os.path.dirname(config_file_path), "config_backups")

    def migrate_if_needed(self) -> Dict[str, Any]:
        """
        检查并迁移配置文件（如果需要）
        返回: 迁移后的配置字典
        """
        if not os.path.exists(self.config_file_path):
            print("配置文件不存在，将使用默认配置")
            return self._get_default_config()

        with open(self.config_file_path, 'r', encoding='utf-8') as f:
            old_config = json.load(f)

        # 检查配置版本
        config_version = old_config.get("config_version", "1.0.0")
        app_config_version = old_config.get("app", {}).get("config_version", "1.0.0")

        if config_version == "2.0.0" or app_config_version == "2.0.0":
            print("配置文件已是最新版本")
            return old_config

        print("检测到旧版本配置，开始迁移...")

        # 备份旧配置
        self._backup_old_config(old_config)

        # 执行迁移
        new_config = self._migrate_from_v1_to_v2(old_config)

        # 保存新配置
        self._save_new_config(new_config)

        print("✅ 配置迁移完成！")
        return new_config

    def _backup_old_config(self, old_config: Dict[str, Any]):
        """备份旧配置"""
        os.makedirs(self.backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"model_config_backup_{timestamp}.json")

        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(old_config, f, indent=2, ensure_ascii=False)

        print(f"✅ 旧配置已备份到: {backup_file}")

    def _migrate_from_v1_to_v2(self, old_config: Dict[str, Any]) -> Dict[str, Any]:
        """从v1.x迁移到v2.0"""
        new_config = {
            "app": {
                "name": "GeminiScreenshotAssistant",
                "version": "2.0.0",
                "config_version": "2.0.0"
            },
            "ai_providers": {
                "current_provider": old_config.get("provider", "Gemini"),
                "default_provider": "Gemini",
                "available_providers": ["Gemini", "GPT"],
                "gemini": {
                    "api_key": old_config.get("api_key", ""),
                    "model": old_config.get("gemini_model", old_config.get("model", "gemini-2.5-flash")),
                    "default_model": "gemini-2.5-flash",
                    "available_models": old_config.get("available_gemini_models", [
                        "gemini-2.5-flash", "gemini-2.5-pro"
                    ])
                },
                "gpt": {
                    "api_key": old_config.get("gpt_api_key", ""),
                    "model": old_config.get("gpt_model", "gpt-5-2025-08-07"),
                    "default_model": "gpt-5-2025-08-07",
                    "base_url": old_config.get("gpt_base_url", "https://zzzzapi.com/v1"),
                    "use_proxy": old_config.get("gpt_use_proxy", False),
                    "available_models": old_config.get("available_gpt_models", [
                        "gpt-5-2025-08-07", "gpt-5-chat-latest"
                    ])
                },
                "common": {
                    "timeout": 30,
                    "max_retries": 3,
                    "initial_retry_delay": 2,
                    "min_api_key_length": 20
                }
            },
            "network": {
                "proxy": old_config.get("proxy", ""),
                "timeout": 5,
                "supported_proxy_schemes": ["http", "https", "socks5"]
            },
            "ui": {
                "window": {
                    "width": old_config.get("window_width", 550),
                    "height": old_config.get("window_height", 800),
                    "min_width": old_config.get("window_min_width", 500),
                    "min_height": old_config.get("window_min_height", 700)
                },
                "overlay": {
                    "width": 960,
                    "height": 360,
                    "background_opacity": old_config.get("background_opacity", 120)
                },
                "display": {
                    "show_log_tab": old_config.get("show_log_tab", True)
                },
                "theme": {
                    "colors": {
                        "primary": "#007bff",
                        "success": "#28a745",
                        "danger": "#dc3545",
                        "warning": "#ffc107",
                        "secondary": "#6c757d",
                        "light": "#f8f9fa",
                        "dark": "#343a40"
                    },
                    "status_colors": {
                        "running": "#28a745",
                        "stopped": "#dc3545",
                        "error": "#dc3545"
                    }
                }
            },
            "features": {
                "screenshot": {
                    "max_history": old_config.get("max_screenshot_history", 10),
                    "mode": {
                        "use_selector": True,
                        "wait_time": 3000,
                        "confirm_time": 2000,
                        "minimize_focus_impact": True,
                        "backup_mode": "traditional"
                    },
                    "image_processing": {
                        "max_image_size_mb": 5,
                        "max_total_size_mb": 20,
                        "max_thumbnail_size": [1920, 1080]
                    }
                },
                "logging": {
                    "max_entries": 1000,
                    "retention_days": 7,
                    "log_dir_name": ".gemini_assistant",
                    "log_subdir": "logs"
                },
                "prompts": old_config.get("prompts", []),
                "hotkeys": old_config.get("hotkeys", {
                    "toggle": "alt+q",
                    "screenshot_only": "alt+w",
                    "clear_screenshots": "alt+v",
                    "scroll_up": "alt+up",
                    "scroll_down": "alt+down"
                })
            },
            "_compatibility": old_config  # 保留完整的旧配置用于兼容性
        }

        return new_config

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "app": {
                "name": "GeminiScreenshotAssistant",
                "version": "2.0.0",
                "config_version": "2.0.0"
            },
            "ai_providers": {
                "current_provider": "Gemini",
                "default_provider": "Gemini",
                "available_providers": ["Gemini", "GPT"],
                "gemini": {
                    "api_key": "",
                    "model": "gemini-2.5-flash",
                    "default_model": "gemini-2.5-flash",
                    "available_models": ["gemini-2.5-flash", "gemini-2.5-pro"]
                },
                "gpt": {
                    "api_key": "",
                    "model": "gpt-5-2025-08-07",
                    "default_model": "gpt-5-2025-08-07",
                    "base_url": "https://zzzzapi.com/v1",
                    "use_proxy": False,
                    "available_models": ["gpt-5-2025-08-07", "gpt-5-chat-latest"]
                },
                "common": {
                    "timeout": 30,
                    "max_retries": 3,
                    "initial_retry_delay": 2,
                    "min_api_key_length": 20
                }
            },
            "network": {
                "proxy": "",
                "timeout": 5,
                "supported_proxy_schemes": ["http", "https", "socks5"]
            },
            "ui": {
                "window": {
                    "width": 550,
                    "height": 800,
                    "min_width": 500,
                    "min_height": 700
                },
                "overlay": {
                    "width": 960,
                    "height": 360,
                    "background_opacity": 120
                },
                "display": {
                    "show_log_tab": True
                },
                "theme": {
                    "colors": {
                        "primary": "#007bff",
                        "success": "#28a745",
                        "danger": "#dc3545",
                        "warning": "#ffc107",
                        "secondary": "#6c757d",
                        "light": "#f8f9fa",
                        "dark": "#343a40"
                    },
                    "status_colors": {
                        "running": "#28a745",
                        "stopped": "#dc3545",
                        "error": "#dc3545"
                    }
                }
            },
            "features": {
                "screenshot": {
                    "max_history": 10,
                    "mode": {
                        "use_selector": True,
                        "wait_time": 3000,
                        "confirm_time": 2000,
                        "minimize_focus_impact": True,
                        "backup_mode": "traditional"
                    },
                    "image_processing": {
                        "max_image_size_mb": 5,
                        "max_total_size_mb": 20,
                        "max_thumbnail_size": [1920, 1080]
                    }
                },
                "logging": {
                    "max_entries": 1000,
                    "retention_days": 7,
                    "log_dir_name": ".gemini_assistant",
                    "log_subdir": "logs"
                },
                "prompts": [],
                "hotkeys": {
                    "toggle": "alt+q",
                    "screenshot_only": "alt+w",
                    "clear_screenshots": "alt+v",
                    "scroll_up": "alt+up",
                    "scroll_down": "alt+down"
                }
            },
            "_compatibility": {}
        }

    def _save_new_config(self, new_config: Dict[str, Any]):
        """保存新配置"""
        with open(self.config_file_path, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, indent=2, ensure_ascii=False)

        print(f"✅ 新配置已保存到: {self.config_file_path}")