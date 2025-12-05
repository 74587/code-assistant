"""
AI 服务抽象基类
定义所有 AI 服务的统一接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Generator, Tuple

from ...core.log_manager import LogManager
from ...core.config_manager import ConfigManager


@dataclass
class AIServiceConfig:
    """AI 服务配置"""
    api_key: str
    base_url: str
    model: str
    use_proxy: bool = False
    proxy_url: str = ""
    timeout: int = 120
    max_retries: int = 3
    retry_delay: int = 2


class AIServiceBase(ABC):
    """AI 服务抽象基类"""

    def __init__(self, config_manager: ConfigManager, log_manager: LogManager):
        self.config_manager = config_manager
        self.log_manager = log_manager

    @property
    @abstractmethod
    def name(self) -> str:
        """服务名称"""
        pass

    @property
    @abstractmethod
    def provider_key(self) -> str:
        """配置中的 provider 标识符，如 'Gemini', 'GPT'"""
        pass

    @abstractmethod
    def get_service_config(self) -> AIServiceConfig:
        """获取当前服务配置"""
        pass

    @abstractmethod
    def validate_config(self) -> Tuple[bool, str]:
        """
        验证服务配置是否有效
        Returns: (is_valid, error_message)
        """
        pass

    @abstractmethod
    def analyze_single_image(self, image_data: bytes, prompt: str) -> str:
        """
        分析单张图片
        Args:
            image_data: PNG 格式的图片字节数据
            prompt: 用户提示词
        Returns:
            AI 响应文本
        """
        pass

    @abstractmethod
    def analyze_multi_images(self, images: List[bytes], prompt: str) -> str:
        """
        分析多张图片
        Args:
            images: PNG 格式的图片字节数据列表
            prompt: 用户提示词
        Returns:
            AI 响应文本
        """
        pass

    def analyze_images(self, images: List[bytes], prompt: str) -> str:
        """
        统一的图片分析入口（自动选择单图/多图模式）
        """
        if len(images) == 1:
            return self.analyze_single_image(images[0], prompt)
        return self.analyze_multi_images(images, prompt)

    # 可选：流式响应接口
    def stream_single_image(
        self, image_data: bytes, prompt: str
    ) -> Generator[Tuple[str, bool], None, None]:
        """
        流式分析单张图片（可选实现）
        Yields: (chunk_text, is_complete)
        """
        # 默认实现：不支持流式，直接返回完整结果
        result = self.analyze_single_image(image_data, prompt)
        yield (result, True)

    def stream_multi_images(
        self, images: List[bytes], prompt: str
    ) -> Generator[Tuple[str, bool], None, None]:
        """
        流式分析多张图片（可选实现）
        Yields: (chunk_text, is_complete)
        """
        # 默认实现：不支持流式，直接返回完整结果
        result = self.analyze_multi_images(images, prompt)
        yield (result, True)

    def _setup_proxy(self) -> None:
        """设置代理（子类可重写）"""
        config = self.get_service_config()
        if config.use_proxy and config.proxy_url:
            import os
            os.environ['HTTPS_PROXY'] = config.proxy_url
            os.environ['HTTP_PROXY'] = config.proxy_url
            self.log_manager.add_log(f"已设置代理: {config.proxy_url}")
        else:
            import os
            os.environ.pop('HTTPS_PROXY', None)
            os.environ.pop('HTTP_PROXY', None)

    def _analyze_error(self, error_str: str) -> str:
        """分析错误并返回用户友好的信息（子类可重写）"""
        error_lower = error_str.lower()
        if "quota" in error_lower or "billing" in error_lower:
            return "API 配额已用完，请检查账户余额"
        elif "api key" in error_lower or "unauthorized" in error_lower:
            return "API Key 无效或已过期，请检查配置"
        elif "timeout" in error_lower:
            return "请求超时，网络可能较慢"
        elif "connection" in error_lower:
            return f"连接错误: {error_str}"
        return f"API 调用失败: {error_str}"
