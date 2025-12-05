"""
AI 服务工厂
负责创建和管理 AI 服务实例
"""

from typing import Dict, Type, Optional

from .base import AIServiceBase
from .gemini_service import GeminiService
from .gpt_service import GPTService
from ...core.log_manager import LogManager
from ...core.config_manager import ConfigManager


class AIServiceFactory:
    """AI 服务工厂"""

    # 注册的服务类
    _services: Dict[str, Type[AIServiceBase]] = {
        "Gemini": GeminiService,
        "GPT": GPTService,
    }

    def __init__(self, config_manager: ConfigManager, log_manager: LogManager):
        self.config_manager = config_manager
        self.log_manager = log_manager
        self._instances: Dict[str, AIServiceBase] = {}

    @classmethod
    def register_service(cls, provider_key: str, service_class: Type[AIServiceBase]) -> None:
        """
        注册新的 AI 服务
        Args:
            provider_key: 服务提供商标识符
            service_class: 服务类
        """
        cls._services[provider_key] = service_class

    @classmethod
    def get_available_providers(cls) -> list:
        """获取所有可用的服务提供商"""
        return list(cls._services.keys())

    def get_service(self, provider: Optional[str] = None) -> AIServiceBase:
        """
        获取 AI 服务实例
        Args:
            provider: 服务提供商，如 'Gemini', 'GPT'。如果为空则使用配置中的默认值
        Returns:
            AI 服务实例
        """
        if provider is None:
            provider = self.config_manager.get("provider", "Gemini")

        if provider not in self._services:
            self.log_manager.add_log(
                f"未知的服务提供商: {provider}，使用默认 Gemini",
                "WARNING"
            )
            provider = "Gemini"

        # 缓存实例
        if provider not in self._instances:
            service_class = self._services[provider]
            self._instances[provider] = service_class(self.config_manager, self.log_manager)
            self.log_manager.add_log(f"创建 {provider} 服务实例")

        return self._instances[provider]

    def get_current_service(self) -> AIServiceBase:
        """获取当前配置的 AI 服务"""
        provider = self.config_manager.get("provider", "Gemini")
        return self.get_service(provider)

    def switch_provider(self, provider: str) -> AIServiceBase:
        """
        切换服务提供商
        Args:
            provider: 新的服务提供商
        Returns:
            新的 AI 服务实例
        """
        if provider not in self._services:
            raise ValueError(f"不支持的服务提供商: {provider}")

        self.config_manager.set("provider", provider)
        self.log_manager.add_log(f"切换到 {provider} 服务")
        return self.get_service(provider)

    def validate_current_service(self) -> tuple:
        """
        验证当前服务配置
        Returns:
            (is_valid, error_message)
        """
        service = self.get_current_service()
        return service.validate_config()

    def clear_cache(self) -> None:
        """清除服务实例缓存"""
        self._instances.clear()
        self.log_manager.add_log("已清除 AI 服务缓存")
