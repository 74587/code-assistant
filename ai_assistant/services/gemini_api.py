"""
Gemini API 服务模块
处理与 Gemini API 的交互
"""

import os
import time
from google import genai
from google.genai import types
import PIL.Image
import io
from typing import List, Optional, Generator, Tuple
from ..core.log_manager import LogManager
from ..core.config_manager import ConfigManager
from .network_utils import NetworkUtils
from ..utils.constants import (
    API_TIMEOUT, MAX_RETRIES, INITIAL_RETRY_DELAY,
    MAX_IMAGE_SIZE_MB, MAX_TOTAL_SIZE_MB, MAX_THUMBNAIL_SIZE
)


class GeminiAPI:
    def __init__(self, config_manager: ConfigManager, log_manager: LogManager):
        self.config_manager = config_manager
        self.log_manager = log_manager

    def _setup_proxy(self) -> None:
        """设置代理"""
        proxy = self.config_manager.get("proxy", "")
        if proxy:
            NetworkUtils.setup_proxy(proxy)
            self.log_manager.add_log(f"✅ 已设置代理: {proxy}")

            # 验证环境变量是否设置成功
            import os
            https_proxy = os.environ.get('HTTPS_PROXY')
            http_proxy = os.environ.get('HTTP_PROXY')
            self.log_manager.add_log(f"环境变量验证 - HTTPS_PROXY: {https_proxy}")
            self.log_manager.add_log(f"环境变量验证 - HTTP_PROXY: {http_proxy}")
        else:
            self.log_manager.add_log("⚪ 未配置代理，使用直连")

    def _get_model(self) -> str:
        """获取配置的模型"""
        # 不验证模型列表，因为用户可能使用自定义API端点
        return self.config_manager.get("model", "")

    def _validate_api_key(self) -> str:
        """验证API Key"""
        api_key = self.config_manager.get("api_key")
        if not api_key:
            raise Exception("API Key 未配置，请在设置中配置")
        return api_key

    def _check_connectivity(self) -> None:
        """检查网络连接"""
        network_ok, network_msg = NetworkUtils.check_network_connectivity()
        if not network_ok:
            self.log_manager.add_log(network_msg, "ERROR")
            raise Exception(network_msg)

    def _process_image(self, png_data: bytes, index: int = 0) -> PIL.Image.Image:
        """处理单个图片"""
        try:
            image = PIL.Image.open(io.BytesIO(png_data))

            # 如果图片太大，进行压缩
            if len(png_data) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
                self.log_manager.add_log(f"压缩第 {index+1} 张图片...", "INFO")
                image.thumbnail(MAX_THUMBNAIL_SIZE, PIL.Image.Resampling.LANCZOS)

            return image
        except Exception as e:
            raise Exception(f"处理第 {index+1} 张图片失败: {e}")

    def _create_generation_config(self) -> genai.types.GenerationConfig:
        """创建生成配置"""
        return genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=4096,
        )

    def _analyze_error(self, error_str: str) -> str:
        """分析错误类型并返回用户友好的错误信息"""
        if "quota" in error_str.lower():
            return "❌ API 配额已用完，请稍后再试或更换 API Key"
        elif "api key" in error_str.lower():
            return "❌ API Key 无效或已过期，请检查配置"
        elif "timeout" in error_str.lower():
            return "⏱️ 请求超时，网络可能较慢"
        elif "connection" in error_str.lower():
            return f"🔌 连接错误: {error_str}"
        else:
            return f"⚠️ API 调用失败: {error_str}"

    def call_api_single_image(self, png: bytes, prompt: str,
                             max_retries: int = MAX_RETRIES,
                             retry_delay: int = INITIAL_RETRY_DELAY) -> str:
        """单图片API调用"""
        api_key = self._validate_api_key()
        self._setup_proxy()

        last_error = None
        for attempt in range(max_retries):
            try:
                self.log_manager.add_log(f"调用 Gemini API (尝试 {attempt + 1}/{max_retries})")

                # 检查当前代理环境变量状态
                import os
                current_https = os.environ.get('HTTPS_PROXY')
                current_http = os.environ.get('HTTP_PROXY')
                if current_https or current_http:
                    self.log_manager.add_log(f"🌐 当前使用代理: {current_https or current_http}")
                else:
                    self.log_manager.add_log("🌐 当前使用直连（无代理）")

                model = self._get_model()
                self.log_manager.add_log(f"🤖 使用模型: {model}")

                image_part = types.Part.from_bytes(data=png, mime_type="image/png")
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(model=model, contents=[prompt, image_part])
                # response = model.generate_content(
                #     [prompt, image],
                #     generation_config=generation_config,
                #     request_options={"timeout": API_TIMEOUT}
                # )

                if response and response.text:
                    self.log_manager.add_log(f"✅ API 调用成功，返回 {len(response.text)} 字符")
                    return response.text
                else:
                    raise Exception("API 返回空响应")

            except Exception as e:
                last_error = e
                error_str = str(e)

                # 对于致命错误，直接返回
                if any(keyword in error_str.lower() for keyword in ["quota", "api key"]):
                    error_msg = self._analyze_error(error_str)
                    self.log_manager.add_log(error_msg, "ERROR")
                    return error_msg

                self.log_manager.add_log(f"⚠️ 尝试 {attempt + 1} 失败: {error_str}", "WARNING")

                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避

        # 所有重试都失败
        error_msg = f"❌ API 调用失败（重试{max_retries}次后）: {last_error}"
        self.log_manager.add_log(error_msg, "ERROR")
        return error_msg

    def call_api_single_image_stream(self, png: bytes, prompt: str,
                                   max_retries: int = MAX_RETRIES,
                                   retry_delay: int = INITIAL_RETRY_DELAY) -> Generator[Tuple[str, bool], None, None]:
        """单图片API调用 - 流式响应版本
        Returns: Generator[(chunk_text, is_complete), None, None]
        """
        api_key = self._validate_api_key()
        self._setup_proxy()

        last_error = None
        for attempt in range(max_retries):
            try:
                self.log_manager.add_log(f"调用 Gemini API 流式版本 (尝试 {attempt + 1}/{max_retries})")

                model = self._get_model()
                self.log_manager.add_log(f"🤖 使用模型: {model}")

                image_part = types.Part.from_bytes(data=png, mime_type="image/png")
                client = genai.Client(api_key=api_key)

                # 使用流式API获取响应
                response_stream = client.models.generate_content_stream(
                    model=model,
                    contents=[prompt, image_part]
                )

                full_text = ""
                for chunk in response_stream:
                    if chunk.text:
                        full_text += chunk.text
                        yield (chunk.text, False)  # 返回增量内容

                if full_text:
                    self.log_manager.add_log(f"✅ 流式API调用成功，返回 {len(full_text)} 字符")
                    yield ("", True)  # 标记完成
                    return
                else:
                    raise Exception("API 返回空响应")

            except Exception as e:
                last_error = e
                error_str = str(e)

                # 对于致命错误，直接返回错误
                if any(keyword in error_str.lower() for keyword in ["quota", "api key"]):
                    error_msg = self._analyze_error(error_str)
                    self.log_manager.add_log(error_msg, "ERROR")
                    yield (error_msg, True)
                    return

                self.log_manager.add_log(f"⚠️ 尝试 {attempt + 1} 失败: {error_str}", "WARNING")

                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避

        # 所有重试都失败
        error_msg = f"❌ API 调用失败（重试{max_retries}次后）: {last_error}"
        self.log_manager.add_log(error_msg, "ERROR")
        yield (error_msg, True)

    def call_api_multi_images_stream(self, images: List[bytes], prompt: str,
                                   max_retries: int = MAX_RETRIES,
                                   retry_delay: int = INITIAL_RETRY_DELAY) -> Generator[Tuple[str, bool], None, None]:
        """多图片API调用 - 流式响应版本"""
        api_key = self._validate_api_key()
        self._setup_proxy()

        # 检查总大小
        total_size_mb = sum(len(img) for img in images) / (1024 * 1024)
        if total_size_mb > MAX_TOTAL_SIZE_MB:
            self.log_manager.add_log(
                f"⚠️ 图片总大小较大 ({total_size_mb:.1f} MB)，可能需要较长时间",
                "WARNING"
            )

        last_error = None
        for attempt in range(max_retries):
            try:
                self.log_manager.add_log(
                    f"调用 Gemini API 流式版本 - 多图片模式 (尝试 {attempt + 1}/{max_retries})"
                )

                # 处理所有图片
                contents = [prompt]
                for i, png_data in enumerate(images):
                    try:
                        image = types.Part.from_bytes(data=png_data, mime_type="image/png")
                        contents.append(image)
                    except Exception as img_error:
                        self.log_manager.add_log(f"⚠️ 跳过第 {i+1} 张图片: {img_error}", "WARNING")
                        continue

                if len(contents) == 1:  # 只有提示词，没有有效图片
                    raise Exception("没有有效的图片可以处理")

                model = self._get_model()
                self.log_manager.add_log(f"🤖 使用模型: {model}")

                client = genai.Client(api_key=api_key)
                response_stream = client.models.generate_content_stream(
                    model=model,
                    contents=contents
                )

                full_text = ""
                for chunk in response_stream:
                    if chunk.text:
                        full_text += chunk.text
                        yield (chunk.text, False)  # 返回增量内容

                if full_text:
                    self.log_manager.add_log(
                        f"✅ 流式API调用成功，处理了 {len(images)} 张图片，返回 {len(full_text)} 字符"
                    )
                    yield ("", True)  # 标记完成
                    return
                else:
                    raise Exception("API 返回空响应")

            except Exception as e:
                last_error = e
                error_str = str(e)

                # 对于致命错误，直接返回
                if any(keyword in error_str.lower() for keyword in ["quota", "api key"]):
                    error_msg = self._analyze_error(error_str)
                    self.log_manager.add_log(error_msg, "ERROR")
                    yield (error_msg, True)
                    return

                if "timeout" in error_str.lower():
                    self.log_manager.add_log(f"⏱️ 请求超时（图片较多），{retry_delay}秒后重试...", "WARNING")
                else:
                    self.log_manager.add_log(f"⚠️ 尝试 {attempt + 1} 失败: {error_str}", "WARNING")

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2

        error_msg = f"❌ API 调用失败（重试{max_retries}次后）: {last_error}"
        self.log_manager.add_log(error_msg, "ERROR")
        yield (error_msg, True)

    def call_api_multi_images(self, images: List[bytes], prompt: str,
                             max_retries: int = MAX_RETRIES,
                             retry_delay: int = INITIAL_RETRY_DELAY) -> str:
        """多图片API调用"""
        api_key = self._validate_api_key()
        self._setup_proxy()

        # 检查总大小
        total_size_mb = sum(len(img) for img in images) / (1024 * 1024)
        if total_size_mb > MAX_TOTAL_SIZE_MB:
            self.log_manager.add_log(
                f"⚠️ 图片总大小较大 ({total_size_mb:.1f} MB)，可能需要较长时间",
                "WARNING"
            )

        last_error = None
        for attempt in range(max_retries):
            try:
                self.log_manager.add_log(
                    f"调用 Gemini API - 多图片模式 (尝试 {attempt + 1}/{max_retries})"
                )

                # 处理所有图片
                contents = [prompt]
                self.log_manager.add_log(f"开始处理 {len(images)} 张图片")

                for i, png_data in enumerate(images):
                    try:
                        self.log_manager.add_log(f"处理第 {i+1} 张图片，大小: {len(png_data)} bytes")
                        image = types.Part.from_bytes(data=png_data, mime_type="image/png")
                        contents.append(image)
                        self.log_manager.add_log(f"第 {i+1} 张图片处理成功")
                    except Exception as img_error:
                        self.log_manager.add_log(f"⚠️ 跳过第 {i+1} 张图片: {img_error}", "WARNING")
                        continue

                if len(contents) == 1:  # 只有提示词，没有有效图片
                    raise Exception("没有有效的图片可以处理")

                self.log_manager.add_log(f"准备发送给API，内容数量: {len(contents)}")
                client = genai.Client(api_key=api_key)
                self.log_manager.add_log("开始调用 API...")

                # 检查当前代理环境变量状态
                import os
                current_https = os.environ.get('HTTPS_PROXY')
                current_http = os.environ.get('HTTP_PROXY')
                if current_https or current_http:
                    self.log_manager.add_log(f"🌐 当前使用代理: {current_https or current_http}")
                else:
                    self.log_manager.add_log("🌐 当前使用直连（无代理）")

                # 添加超时保护（Windows兼容版本）
                import threading
                import concurrent.futures

                model = self._get_model()
                self.log_manager.add_log(f"🤖 使用模型: {model}")

                def api_call():
                    return client.models.generate_content(model=model, contents=contents)

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(api_call)
                    try:
                        response = future.result(timeout=120)  # 120秒超时
                        self.log_manager.add_log("API 调用完成，检查响应...")
                    except concurrent.futures.TimeoutError:
                        raise Exception("API 调用超时 (120秒)")
                if response and response.text:
                    self.log_manager.add_log(
                        f"✅ API 调用成功，处理了 {len(images)} 张图片，返回 {len(response.text)} 字符"
                    )
                    return response.text
                else:
                    raise Exception("API 返回空响应")

            except Exception as e:
                last_error = e
                error_str = str(e)

                # 对于致命错误，直接返回
                if any(keyword in error_str.lower() for keyword in ["quota", "api key"]):
                    error_msg = self._analyze_error(error_str)
                    self.log_manager.add_log(error_msg, "ERROR")
                    return error_msg

                if "timeout" in error_str.lower():
                    self.log_manager.add_log(f"⏱️ 请求超时（图片较多），{retry_delay}秒后重试...", "WARNING")
                else:
                    self.log_manager.add_log(f"⚠️ 尝试 {attempt + 1} 失败: {error_str}", "WARNING")

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2

        error_msg = f"❌ API 调用失败（重试{max_retries}次后）: {last_error}"
        self.log_manager.add_log(error_msg, "ERROR")
        return error_msg