"""
Gemini AI 服务实现
"""

import os
import time
from typing import List, Tuple, Generator

from google import genai
from google.genai import types

from .base import AIServiceBase, AIServiceConfig
from ...core.log_manager import LogManager
from ...core.config_manager import ConfigManager
from ...utils.constants import (
    API_TIMEOUT, MAX_RETRIES, INITIAL_RETRY_DELAY,
    MAX_IMAGE_SIZE_MB, MAX_TOTAL_SIZE_MB
)


class GeminiService(AIServiceBase):
    """Gemini AI 服务"""

    def __init__(self, config_manager: ConfigManager, log_manager: LogManager):
        super().__init__(config_manager, log_manager)

    @property
    def name(self) -> str:
        return "Gemini"

    @property
    def provider_key(self) -> str:
        return "Gemini"

    def get_service_config(self) -> AIServiceConfig:
        """获取 Gemini 服务配置"""
        return AIServiceConfig(
            api_key=self.config_manager.get("api_key", ""),
            base_url=self.config_manager.get("gemini_base_url", ""),
            model=self._get_model(),
            use_proxy=self.config_manager.get("gemini_use_proxy", False),
            proxy_url=self.config_manager.get("proxy", ""),
            timeout=API_TIMEOUT,
            max_retries=MAX_RETRIES,
            retry_delay=INITIAL_RETRY_DELAY,
        )

    def _get_model(self) -> str:
        """获取配置的模型"""
        return self.config_manager.get("model", "")

    def validate_config(self) -> Tuple[bool, str]:
        """验证配置"""
        config = self.get_service_config()
        if not config.api_key:
            return False, "Gemini API Key 未配置，请在设置中配置"
        return True, ""

    def _setup_proxy(self) -> None:
        """设置代理"""
        config = self.get_service_config()
        if config.use_proxy and config.proxy_url:
            os.environ['HTTPS_PROXY'] = config.proxy_url
            os.environ['HTTP_PROXY'] = config.proxy_url
            self.log_manager.add_log(f"已设置代理: {config.proxy_url}")
        else:
            os.environ.pop('HTTPS_PROXY', None)
            os.environ.pop('HTTP_PROXY', None)
            self.log_manager.add_log("使用直连（无代理）")

    def analyze_single_image(self, image_data: bytes, prompt: str) -> str:
        """分析单张图片"""
        # 验证配置
        is_valid, error_msg = self.validate_config()
        if not is_valid:
            return f"错误: {error_msg}"

        config = self.get_service_config()
        self._setup_proxy()

        last_error = None
        retry_delay = config.retry_delay

        for attempt in range(config.max_retries):
            try:
                self.log_manager.add_log(f"调用 Gemini API (尝试 {attempt + 1}/{config.max_retries})")
                self.log_manager.add_log(f"使用模型: {config.model}")

                image_part = types.Part.from_bytes(data=image_data, mime_type="image/png")
                client = genai.Client(api_key=config.api_key)
                response = client.models.generate_content(
                    model=config.model,
                    contents=[prompt, image_part]
                )

                if response and response.text:
                    self.log_manager.add_log(f"API 调用成功，返回 {len(response.text)} 字符")
                    return response.text
                else:
                    raise Exception("API 返回空响应")

            except Exception as e:
                last_error = e
                error_str = str(e)

                # 致命错误直接返回
                if any(kw in error_str.lower() for kw in ["quota", "api key"]):
                    error_msg = self._analyze_error(error_str)
                    self.log_manager.add_log(error_msg, "ERROR")
                    return f"错误: {error_msg}"

                self.log_manager.add_log(f"尝试 {attempt + 1} 失败: {error_str}", "WARNING")

                if attempt < config.max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2

        error_msg = f"API 调用失败（重试{config.max_retries}次后）: {last_error}"
        self.log_manager.add_log(error_msg, "ERROR")
        return f"错误: {error_msg}"

    def analyze_multi_images(self, images: List[bytes], prompt: str) -> str:
        """分析多张图片"""
        # 验证配置
        is_valid, error_msg = self.validate_config()
        if not is_valid:
            return f"错误: {error_msg}"

        config = self.get_service_config()
        self._setup_proxy()

        # 检查总大小
        total_size_mb = sum(len(img) for img in images) / (1024 * 1024)
        if total_size_mb > MAX_TOTAL_SIZE_MB:
            self.log_manager.add_log(
                f"图片总大小较大 ({total_size_mb:.1f} MB)，可能需要较长时间",
                "WARNING"
            )

        last_error = None
        retry_delay = config.retry_delay

        for attempt in range(config.max_retries):
            try:
                self.log_manager.add_log(
                    f"调用 Gemini API - 多图片模式 (尝试 {attempt + 1}/{config.max_retries})"
                )

                # 构建内容
                contents = [prompt]
                for i, png_data in enumerate(images):
                    try:
                        image_part = types.Part.from_bytes(data=png_data, mime_type="image/png")
                        contents.append(image_part)
                    except Exception as img_error:
                        self.log_manager.add_log(f"跳过第 {i+1} 张图片: {img_error}", "WARNING")
                        continue

                if len(contents) == 1:
                    raise Exception("没有有效的图片可以处理")

                self.log_manager.add_log(f"使用模型: {config.model}")

                client = genai.Client(api_key=config.api_key)

                # 使用线程池实现超时
                import concurrent.futures
                def api_call():
                    return client.models.generate_content(model=config.model, contents=contents)

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(api_call)
                    response = future.result(timeout=config.timeout)

                if response and response.text:
                    self.log_manager.add_log(
                        f"API 调用成功，处理了 {len(images)} 张图片，返回 {len(response.text)} 字符"
                    )
                    return response.text
                else:
                    raise Exception("API 返回空响应")

            except Exception as e:
                last_error = e
                error_str = str(e)

                if any(kw in error_str.lower() for kw in ["quota", "api key"]):
                    error_msg = self._analyze_error(error_str)
                    self.log_manager.add_log(error_msg, "ERROR")
                    return f"错误: {error_msg}"

                self.log_manager.add_log(f"尝试 {attempt + 1} 失败: {error_str}", "WARNING")

                if attempt < config.max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2

        error_msg = f"API 调用失败（重试{config.max_retries}次后）: {last_error}"
        self.log_manager.add_log(error_msg, "ERROR")
        return f"错误: {error_msg}"

    def stream_single_image(
        self, image_data: bytes, prompt: str
    ) -> Generator[Tuple[str, bool], None, None]:
        """流式分析单张图片"""
        is_valid, error_msg = self.validate_config()
        if not is_valid:
            yield (f"错误: {error_msg}", True)
            return

        config = self.get_service_config()
        self._setup_proxy()

        try:
            self.log_manager.add_log(f"调用 Gemini API 流式版本")
            self.log_manager.add_log(f"使用模型: {config.model}")

            image_part = types.Part.from_bytes(data=image_data, mime_type="image/png")
            client = genai.Client(api_key=config.api_key)

            response_stream = client.models.generate_content_stream(
                model=config.model,
                contents=[prompt, image_part]
            )

            full_text = ""
            for chunk in response_stream:
                if chunk.text:
                    full_text += chunk.text
                    yield (chunk.text, False)

            if full_text:
                self.log_manager.add_log(f"流式API调用成功，返回 {len(full_text)} 字符")
                yield ("", True)
            else:
                yield ("API 返回空响应", True)

        except Exception as e:
            error_msg = self._analyze_error(str(e))
            self.log_manager.add_log(error_msg, "ERROR")
            yield (f"错误: {error_msg}", True)

    def stream_multi_images(
        self, images: List[bytes], prompt: str
    ) -> Generator[Tuple[str, bool], None, None]:
        """流式分析多张图片"""
        is_valid, error_msg = self.validate_config()
        if not is_valid:
            yield (f"错误: {error_msg}", True)
            return

        config = self.get_service_config()
        self._setup_proxy()

        try:
            self.log_manager.add_log(f"调用 Gemini API 流式版本 - 多图片模式")

            contents = [prompt]
            for i, png_data in enumerate(images):
                try:
                    image_part = types.Part.from_bytes(data=png_data, mime_type="image/png")
                    contents.append(image_part)
                except Exception as img_error:
                    self.log_manager.add_log(f"跳过第 {i+1} 张图片: {img_error}", "WARNING")

            if len(contents) == 1:
                yield ("错误: 没有有效的图片可以处理", True)
                return

            self.log_manager.add_log(f"使用模型: {config.model}")

            client = genai.Client(api_key=config.api_key)
            response_stream = client.models.generate_content_stream(
                model=config.model,
                contents=contents
            )

            full_text = ""
            for chunk in response_stream:
                if chunk.text:
                    full_text += chunk.text
                    yield (chunk.text, False)

            if full_text:
                self.log_manager.add_log(
                    f"流式API调用成功，处理了 {len(images)} 张图片，返回 {len(full_text)} 字符"
                )
                yield ("", True)
            else:
                yield ("API 返回空响应", True)

        except Exception as e:
            error_msg = self._analyze_error(str(e))
            self.log_manager.add_log(error_msg, "ERROR")
            yield (f"错误: {error_msg}", True)
