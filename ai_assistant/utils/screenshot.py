"""
截图工具模块
处理屏幕截图相关功能
"""

import re
from mss import mss, tools
import pyperclip


class ScreenshotError(Exception):
    """截图相关错误"""
    pass


def capture_screen() -> bytes:
    """
    捕获当前屏幕截图

    Returns:
        PNG格式的截图字节数据

    Raises:
        ScreenshotError: 截图失败时抛出
    """
    try:
        with mss() as sct:
            # 安全获取显示器 - monitors[0]是所有显示器的组合，monitors[1]是主显示器
            if len(sct.monitors) < 2:
                # 只有一个显示器或没有检测到，使用第一个可用的
                monitor = sct.monitors[0]
            else:
                # 使用主显示器
                monitor = sct.monitors[1]

            sct_img = sct.grab(monitor)

            if sct_img is None or sct_img.rgb is None:
                raise ScreenshotError("截图数据无效")

            return tools.to_png(sct_img.rgb, sct_img.size)

    except ScreenshotError:
        raise
    except Exception as e:
        raise ScreenshotError(f"截图失败: {e}")


def extract_code_blocks(markdown_text: str) -> str:
    """提取 markdown 文本中的所有代码块"""
    if not markdown_text:
        return ""

    # 匹配代码块的正则表达式 - 避免重复匹配
    # 按优先级排序：先匹配长的，再匹配短的，避免冲突
    patterns = [
        r'```[a-zA-Z0-9+#-]*\n?(.*?)```',  # 标准三个反引号（包含语言标识）
        r'~~~[a-zA-Z0-9+#-]*\n?(.*?)~~~',  # 波浪线代码块
        r'(?<!`)``([^`\n]+?)``(?!`)',       # 双反引号（前后不能有反引号）
        r'(?<!`)`([^`\n]{20,})`(?!`)',      # 长内联代码（至少20字符，前后不能有反引号）
    ]

    all_matches = []
    for pattern in patterns:
        matches = re.findall(pattern, markdown_text, re.DOTALL)
        all_matches.extend(matches)

    if all_matches:
        # 将所有代码块合并，用换行分隔，过滤空的匹配和重复内容
        valid_matches = []
        seen_hashes = set()

        for match in all_matches:
            match_text = match.strip()
            if not match_text:
                continue

            # 使用哈希值去重
            import hashlib
            match_hash = hashlib.md5(match_text.encode()).hexdigest()
            if match_hash not in seen_hashes:
                valid_matches.append(match_text)
                seen_hashes.add(match_hash)

        if valid_matches:
            code_content = '\n\n'.join(valid_matches)
            return code_content

    # 如果没有找到标准代码块，检查整个文本是否像代码
    if _looks_like_code(markdown_text):
        return markdown_text.strip()

    return ""


def _looks_like_code(text: str) -> bool:
    """判断文本是否看起来像代码"""
    if not text or len(text.strip()) < 10:
        return False

    text = text.strip()

    # 代码特征检测
    code_indicators = [
        # Java特征
        r'\bpublic\s+class\b', r'\bprivate\s+\w+\b', r'\bimport\s+java\b',
        r'\bpublic\s+static\s+void\s+main\b', r'\bSystem\.out\.print\b',

        # Python特征
        r'\bdef\s+\w+\s*\(', r'\bimport\s+\w+', r'\bfrom\s+\w+\s+import\b',
        r'\bif\s+__name__\s*==\s*["\']__main__["\']', r'\bprint\s*\(',

        # JavaScript特征
        r'\bfunction\s+\w+\s*\(', r'\bconst\s+\w+\s*=', r'\blet\s+\w+\s*=',
        r'\bconsole\.log\s*\(', r'\b=>\s*\{',

        # C/C++特征
        r'#include\s*<', r'\bint\s+main\s*\(', r'\bprintf\s*\(',

        # 通用代码特征
        r'\{[\s\S]*\}',  # 代码块
        r'\bfor\s*\(', r'\bwhile\s*\(', r'\bif\s*\(',  # 控制流
        r'[=+\-*/]\s*[=+\-*/]',  # 运算符
    ]

    # 计算匹配的代码特征数量
    matches = 0
    for pattern in code_indicators:
        if re.search(pattern, text, re.IGNORECASE):
            matches += 1

    # 如果匹配到足够多的代码特征，认为是代码
    return matches >= 2


def copy_to_clipboard(text: str) -> bool:
    """复制文本到剪贴板"""
    try:
        pyperclip.copy(text)
        return True
    except Exception:
        return False