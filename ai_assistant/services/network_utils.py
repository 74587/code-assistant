"""
网络工具模块
提供网络连接检查、代理验证等功能
"""

import os
import socket
import urllib.parse
from typing import Tuple, Optional
import google.generativeai as genai
from ..utils.constants import NETWORK_TIMEOUT, SUPPORTED_PROXY_SCHEMES


class NetworkUtils:
    @staticmethod
    def check_network_connectivity(timeout: int = NETWORK_TIMEOUT) -> Tuple[bool, str]:
        """检查网络连接状态
        返回: (是否连接, 状态描述)
        """
        try:
            # 简单的网络连接测试
            import urllib.request
            urllib.request.urlopen('https://www.google.com', timeout=timeout)
            return True, "网络连接正常"
        except Exception:
            return False, "网络连接失败，请检查网络设置"

    @staticmethod
    def validate_proxy_url(proxy: str) -> Tuple[bool, str]:
        """验证代理URL格式"""
        if not proxy:
            return True, ""  # 空代理是允许的

        try:
            parsed = urllib.parse.urlparse(proxy)
            if parsed.scheme not in SUPPORTED_PROXY_SCHEMES:
                return False, f"代理协议必须是 {', '.join(SUPPORTED_PROXY_SCHEMES)}"
            if not parsed.netloc:
                return False, "代理地址格式不正确"
            return True, ""
        except Exception as e:
            return False, f"代理地址解析失败: {e}"

    @staticmethod
    def check_api_connectivity(api_key: str, proxy: Optional[str] = None) -> Tuple[bool, str]:
        """检查 API 连接状态"""
        try:
            # 配置代理（如果有）
            if proxy:
                os.environ['HTTPS_PROXY'] = proxy
                os.environ['HTTP_PROXY'] = proxy

            genai.configure(api_key=api_key)
            # 尝试列出模型以测试连接
            list(genai.list_models())
            return True, "API 连接正常"
        except Exception as e:
            error_str = str(e)
            if "API key not valid" in error_str:
                return False, "API Key 无效，请检查配置"
            elif "connection" in error_str.lower():
                return False, f"API 连接失败: {error_str}"
            else:
                return False, f"API 测试失败: {error_str}"
        finally:
            # 清理环境变量
            if proxy:
                os.environ.pop('HTTPS_PROXY', None)
                os.environ.pop('HTTP_PROXY', None)

    @staticmethod
    def setup_proxy(proxy: str) -> None:
        """设置代理环境变量"""
        if proxy:
            os.environ['HTTPS_PROXY'] = proxy
            os.environ['HTTP_PROXY'] = proxy

    @staticmethod
    def clear_proxy() -> None:
        """清除代理环境变量"""
        os.environ.pop('HTTPS_PROXY', None)
        os.environ.pop('HTTP_PROXY', None)