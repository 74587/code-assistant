"""
GPT API 服务模块
处理与 OpenAI GPT API 的交互
"""

import os
import time
import base64
from typing import List, Optional, Generator, Tuple
from ..core.log_manager import LogManager
from ..core.config_manager import ConfigManager
from ..utils.constants import (
    API_TIMEOUT, MAX_RETRIES, INITIAL_RETRY_DELAY,
    MAX_IMAGE_SIZE_MB, MAX_TOTAL_SIZE_MB, MAX_THUMBNAIL_SIZE
)


class GPTAPI:
    def __init__(self, config_manager: ConfigManager, log_manager: LogManager):
        self.config_manager = config_manager
        self.log_manager = log_manager

    def _setup_proxy(self) -> None:
        """设置代理（如果启用）"""
        use_proxy_for_gpt = self.config_manager.get("gpt_use_proxy", False)
        if use_proxy_for_gpt:
            proxy = self.config_manager.get("proxy", "")
            if proxy:
                os.environ['HTTPS_PROXY'] = proxy
                os.environ['HTTP_PROXY'] = proxy
                self.log_manager.add_log(f"✅ GPT已设置代理: {proxy}")
            else:
                self.log_manager.add_log("⚠️ GPT启用代理但未配置代理地址", "WARNING")
        else:
            # 清除代理环境变量，确保GPT不使用代理
            os.environ.pop('HTTPS_PROXY', None)
            os.environ.pop('HTTP_PROXY', None)
            self.log_manager.add_log("⚪ GPT使用直连（无代理）")

    def _get_model(self) -> str:
        """获取配置的GPT模型"""
        # 不再验证模型是否在支持列表中，因为用户可能使用自定义API端点
        return self.config_manager.get("gpt_model", "")

    def _get_base_url(self) -> str:
        """获取配置的Base URL"""
        return self.config_manager.get("gpt_base_url", "")

    def _validate_api_key(self) -> str:
        """验证GPT API Key"""
        api_key = self.config_manager.get("gpt_api_key")
        if not api_key:
            raise Exception("GPT API Key 未配置，请在设置中配置")
        return api_key

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

    def _analyze_error(self, error_str: str) -> str:
        """分析错误类型并返回用户友好的错误信息"""
        if "quota" in error_str.lower() or "billing" in error_str.lower():
            return "❌ API 配额已用完或计费问题，请检查账户余额"
        elif "api key" in error_str.lower() or "unauthorized" in error_str.lower():
            return "❌ API Key 无效或已过期，请检查配置"
        elif "timeout" in error_str.lower():
            return "⏱️ 请求超时，网络可能较慢"
        elif "connection" in error_str.lower():
            return f"🔌 连接错误: {error_str}"
        else:
            return f"⚠️ GPT API 调用失败: {error_str}"

    def call_api_single_image(self, png: bytes, prompt: str,
                             max_retries: int = MAX_RETRIES,
                             retry_delay: int = INITIAL_RETRY_DELAY) -> str:
        """单图片API调用"""
        api_key = self._validate_api_key()
        self._setup_proxy()

        model = self._get_model()
        base_url = self._get_base_url()
        self.log_manager.add_log(f"🤖 使用GPT模型: {model}")
        self.log_manager.add_log(f"🌐 Base URL: {base_url}")

        last_error = None
        for attempt in range(max_retries):
            try:
                self.log_manager.add_log(f"调用 GPT API (尝试 {attempt + 1}/{max_retries})")

                # 检查当前代理环境变量状态
                current_https = os.environ.get('HTTPS_PROXY')
                current_http = os.environ.get('HTTP_PROXY')
                if current_https or current_http:
                    self.log_manager.add_log(f"🌐 当前使用代理: {current_https or current_http}")
                else:
                    self.log_manager.add_log("🌐 当前使用直连（无代理）")

                # 使用openai库
                try:
                    import openai
                except ImportError:
                    raise Exception("需要安装openai库: pip install openai")

                client = openai.OpenAI(
                    api_key=api_key,
                    base_url=base_url
                )

                # 创建消息
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            self._create_image_message(png)
                        ]
                    }
                ]

                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=16384
                )

                if response and response.choices:
                    result = response.choices[0].message.content
                    self.log_manager.add_log(f"✅ GPT API 调用成功，返回 {len(result)} 字符")
                    return result
                else:
                    raise Exception("GPT API 返回空响应")

            except Exception as e:
                last_error = e
                error_str = str(e)

                # 对于致命错误，直接返回
                if any(keyword in error_str.lower() for keyword in ["quota", "billing", "api key", "unauthorized"]):
                    error_msg = self._analyze_error(error_str)
                    self.log_manager.add_log(error_msg, "ERROR")
                    return error_msg

                self.log_manager.add_log(f"⚠️ 尝试 {attempt + 1} 失败: {error_str}", "WARNING")

                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避

        # 所有重试都失败
        error_msg = f"❌ GPT API 调用失败（重试{max_retries}次后）: {last_error}"
        self.log_manager.add_log(error_msg, "ERROR")
        return error_msg

    def call_api_multi_images(self, images: List[bytes], prompt: str,
                             max_retries: int = MAX_RETRIES,
                             retry_delay: int = INITIAL_RETRY_DELAY) -> str:
        """多图片API调用"""
        api_key = self._validate_api_key()
        self._setup_proxy()

        model = self._get_model()
        base_url = self._get_base_url()
        self.log_manager.add_log(f"🤖 使用GPT模型: {model}")
        self.log_manager.add_log(f"🌐 Base URL: {base_url}")

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
                    f"调用 GPT API - 多图片模式 (尝试 {attempt + 1}/{max_retries})"
                )

                # 检查当前代理环境变量状态
                current_https = os.environ.get('HTTPS_PROXY')
                current_http = os.environ.get('HTTP_PROXY')
                if current_https or current_http:
                    self.log_manager.add_log(f"🌐 当前使用代理: {current_https or current_http}")
                else:
                    self.log_manager.add_log("🌐 当前使用直连（无代理）")

                # 使用openai库
                try:
                    import openai
                except ImportError:
                    raise Exception("需要安装openai库: pip install openai")

                client = openai.OpenAI(
                    api_key=api_key,
                    base_url=base_url
                )

                # 创建消息内容
                content = [{"type": "text", "text": prompt}]

                self.log_manager.add_log(f"开始处理 {len(images)} 张图片")
                for i, png_data in enumerate(images):
                    try:
                        self.log_manager.add_log(f"处理第 {i+1} 张图片，大小: {len(png_data)} bytes")
                        content.append(self._create_image_message(png_data))
                        self.log_manager.add_log(f"第 {i+1} 张图片处理成功")
                    except Exception as img_error:
                        self.log_manager.add_log(f"⚠️ 跳过第 {i+1} 张图片: {img_error}", "WARNING")
                        continue

                if len(content) == 1:  # 只有提示词，没有有效图片
                    raise Exception("没有有效的图片可以处理")

                messages = [{"role": "user", "content": content}]

                self.log_manager.add_log(f"准备发送给API，内容数量: {len(content)}")
                self.log_manager.add_log("开始调用 API...")

                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=16384
                )

                self.log_manager.add_log("API 调用完成，检查响应...")

                if response and response.choices:
                    result = response.choices[0].message.content
                    self.log_manager.add_log(
                        f"✅ GPT API 调用成功，处理了 {len(images)} 张图片，返回 {len(result)} 字符"
                    )
                    return result
                else:
                    raise Exception("GPT API 返回空响应")

            except Exception as e:
                last_error = e
                error_str = str(e)

                # 对于致命错误，直接返回
                if any(keyword in error_str.lower() for keyword in ["quota", "billing", "api key", "unauthorized"]):
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

        error_msg = f"❌ GPT API 调用失败（重试{max_retries}次后）: {last_error}"
        self.log_manager.add_log(error_msg, "ERROR")
        return error_msg