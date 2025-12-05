"""
GPT AI 服务实现
"""

import os
import time
import base64
from typing import List, Tuple, Generator

from .base import AIServiceBase, AIServiceConfig
from ...core.log_manager import LogManager
from ...core.config_manager import ConfigManager
from ...utils.constants import (
    DEFAULT_GPT_MODEL, AVAILABLE_GPT_MODELS, DEFAULT_GPT_BASE_URL,
    API_TIMEOUT, MAX_RETRIES, INITIAL_RETRY_DELAY,
    MAX_TOTAL_SIZE_MB
)


class GPTService(AIServiceBase):
    """GPT AI 服务"""

    def __init__(self, config_manager: ConfigManager, log_manager: LogManager):
        super().__init__(config_manager, log_manager)

    @property
    def name(self) -> str:
        return "GPT"

    @property
    def provider_key(self) -> str:
        return "GPT"

    def get_service_config(self) -> AIServiceConfig:
        """获取 GPT 服务配置"""
        return AIServiceConfig(
            api_key=self.config_manager.get("gpt_api_key", ""),
            base_url=self.config_manager.get("gpt_base_url", DEFAULT_GPT_BASE_URL),
            model=self._get_model(),
            use_proxy=self.config_manager.get("gpt_use_proxy", False),
            proxy_url=self.config_manager.get("proxy", ""),
            timeout=API_TIMEOUT,
            max_retries=MAX_RETRIES,
            retry_delay=INITIAL_RETRY_DELAY,
        )

    def _get_model(self) -> str:
        """获取配置的 GPT 模型"""
        model = self.config_manager.get("gpt_model", DEFAULT_GPT_MODEL)
        if model not in AVAILABLE_GPT_MODELS:
            self.log_manager.add_log(
                f"配置的GPT模型 {model} 不在支持列表中，使用默认模型 {DEFAULT_GPT_MODEL}",
                "WARNING"
            )
            return DEFAULT_GPT_MODEL
        return model

    def validate_config(self) -> Tuple[bool, str]:
        """验证配置"""
        config = self.get_service_config()
        if not config.api_key:
            return False, "GPT API Key 未配置，请在设置中配置"
        return True, ""

    def _setup_proxy(self) -> None:
        """设置代理"""
        config = self.get_service_config()
        if config.use_proxy and config.proxy_url:
            os.environ['HTTPS_PROXY'] = config.proxy_url
            os.environ['HTTP_PROXY'] = config.proxy_url
            self.log_manager.add_log(f"GPT已设置代理: {config.proxy_url}")
        else:
            os.environ.pop('HTTPS_PROXY', None)
            os.environ.pop('HTTP_PROXY', None)
            self.log_manager.add_log("GPT使用直连（无代理）")

    def _encode_image(self, png_data: bytes) -> str:
        """将PNG数据编码为base64"""
        return base64.b64encode(png_data).decode('utf-8')

    def _create_image_message(self, png_data: bytes) -> dict:
        """创建图片消息"""
        base64_image = self._encode_image(png_data)
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64_image}"
            }
        }

    def _get_openai_client(self):
        """获取 OpenAI 客户端"""
        try:
            import openai
        except ImportError:
            raise Exception("需要安装openai库: pip install openai")

        config = self.get_service_config()
        return openai.OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )

    def analyze_single_image(self, image_data: bytes, prompt: str) -> str:
        """分析单张图片"""
        is_valid, error_msg = self.validate_config()
        if not is_valid:
            return f"错误: {error_msg}"

        config = self.get_service_config()
        self._setup_proxy()

        self.log_manager.add_log(f"使用GPT模型: {config.model}")
        self.log_manager.add_log(f"Base URL: {config.base_url}")

        last_error = None
        retry_delay = config.retry_delay

        for attempt in range(config.max_retries):
            try:
                self.log_manager.add_log(f"调用 GPT API (尝试 {attempt + 1}/{config.max_retries})")

                client = self._get_openai_client()

                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            self._create_image_message(image_data)
                        ]
                    }
                ]

                response = client.chat.completions.create(
                    model=config.model,
                    messages=messages,
                    max_tokens=16384
                )

                if response and response.choices:
                    result = response.choices[0].message.content
                    self.log_manager.add_log(f"GPT API 调用成功，返回 {len(result)} 字符")
                    return result
                else:
                    raise Exception("GPT API 返回空响应")

            except Exception as e:
                last_error = e
                error_str = str(e)

                if any(kw in error_str.lower() for kw in ["quota", "billing", "api key", "unauthorized"]):
                    error_msg = self._analyze_error(error_str)
                    self.log_manager.add_log(error_msg, "ERROR")
                    return f"错误: {error_msg}"

                self.log_manager.add_log(f"尝试 {attempt + 1} 失败: {error_str}", "WARNING")

                if attempt < config.max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2

        error_msg = f"GPT API 调用失败（重试{config.max_retries}次后）: {last_error}"
        self.log_manager.add_log(error_msg, "ERROR")
        return f"错误: {error_msg}"

    def analyze_multi_images(self, images: List[bytes], prompt: str) -> str:
        """分析多张图片"""
        is_valid, error_msg = self.validate_config()
        if not is_valid:
            return f"错误: {error_msg}"

        config = self.get_service_config()
        self._setup_proxy()

        self.log_manager.add_log(f"使用GPT模型: {config.model}")
        self.log_manager.add_log(f"Base URL: {config.base_url}")

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
                    f"调用 GPT API - 多图片模式 (尝试 {attempt + 1}/{config.max_retries})"
                )

                client = self._get_openai_client()

                # 构建内容
                content = [{"type": "text", "text": prompt}]
                self.log_manager.add_log(f"开始处理 {len(images)} 张图片")

                for i, png_data in enumerate(images):
                    try:
                        content.append(self._create_image_message(png_data))
                    except Exception as img_error:
                        self.log_manager.add_log(f"跳过第 {i+1} 张图片: {img_error}", "WARNING")
                        continue

                if len(content) == 1:
                    raise Exception("没有有效的图片可以处理")

                messages = [{"role": "user", "content": content}]

                response = client.chat.completions.create(
                    model=config.model,
                    messages=messages,
                    max_tokens=16384
                )

                if response and response.choices:
                    result = response.choices[0].message.content
                    self.log_manager.add_log(
                        f"GPT API 调用成功，处理了 {len(images)} 张图片，返回 {len(result)} 字符"
                    )
                    return result
                else:
                    raise Exception("GPT API 返回空响应")

            except Exception as e:
                last_error = e
                error_str = str(e)

                if any(kw in error_str.lower() for kw in ["quota", "billing", "api key", "unauthorized"]):
                    error_msg = self._analyze_error(error_str)
                    self.log_manager.add_log(error_msg, "ERROR")
                    return f"错误: {error_msg}"

                self.log_manager.add_log(f"尝试 {attempt + 1} 失败: {error_str}", "WARNING")

                if attempt < config.max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2

        error_msg = f"GPT API 调用失败（重试{config.max_retries}次后）: {last_error}"
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
            self.log_manager.add_log(f"调用 GPT API 流式版本")
            self.log_manager.add_log(f"使用模型: {config.model}")

            client = self._get_openai_client()

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        self._create_image_message(image_data)
                    ]
                }
            ]

            response_stream = client.chat.completions.create(
                model=config.model,
                messages=messages,
                max_tokens=16384,
                stream=True
            )

            full_text = ""
            for chunk in response_stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_text += content
                    yield (content, False)

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
            self.log_manager.add_log(f"调用 GPT API 流式版本 - 多图片模式")

            client = self._get_openai_client()

            content = [{"type": "text", "text": prompt}]
            for i, png_data in enumerate(images):
                try:
                    content.append(self._create_image_message(png_data))
                except Exception as img_error:
                    self.log_manager.add_log(f"跳过第 {i+1} 张图片: {img_error}", "WARNING")

            if len(content) == 1:
                yield ("错误: 没有有效的图片可以处理", True)
                return

            messages = [{"role": "user", "content": content}]
            self.log_manager.add_log(f"使用模型: {config.model}")

            response_stream = client.chat.completions.create(
                model=config.model,
                messages=messages,
                max_tokens=16384,
                stream=True
            )

            full_text = ""
            for chunk in response_stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content_text = chunk.choices[0].delta.content
                    full_text += content_text
                    yield (content_text, False)

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
