#!/usr/bin/env python3
"""
调试代码块提取功能
"""

import re
import hashlib

def debug_extract_code_blocks(markdown_text: str):
    """调试版本的代码块提取"""
    if not markdown_text:
        return ""

    print("=== 调试代码块提取 ===")
    print(f"输入文本长度: {len(markdown_text)}")
    print(f"输入文本前200字符: {repr(markdown_text[:200])}")

    # 匹配代码块的正则表达式 - 避免重复匹配
    # 按优先级排序：先匹配长的，再匹配短的，避免冲突
    patterns = [
        (r'```[a-zA-Z0-9+#-]*\n?(.*?)```', "标准三反引号"),
        (r'~~~[a-zA-Z0-9+#-]*\n?(.*?)~~~', "波浪线代码块"),
        (r'(?<!`)``([^`\n]+?)``(?!`)', "双反引号（前后不能有反引号）"),
        (r'(?<!`)`([^`\n]{20,})`(?!`)', "长内联代码（前后不能有反引号）"),
    ]

    all_matches = []
    for pattern, name in patterns:
        matches = re.findall(pattern, markdown_text, re.DOTALL)
        print(f"\n{name} 匹配到 {len(matches)} 个:")
        for i, match in enumerate(matches):
            print(f"  匹配 {i+1}: {repr(match[:50])}{'...' if len(match) > 50 else ''}")
        all_matches.extend(matches)

    print(f"\n总共匹配到 {len(all_matches)} 个代码块")

    if all_matches:
        # 将所有代码块合并，用换行分隔，过滤空的匹配和重复内容
        valid_matches = []
        seen_hashes = set()

        for i, match in enumerate(all_matches):
            match_text = match.strip()
            if not match_text:
                print(f"跳过空匹配 {i+1}")
                continue

            # 使用哈希值去重
            match_hash = hashlib.md5(match_text.encode()).hexdigest()
            print(f"匹配 {i+1} 哈希: {match_hash[:8]} 内容: {repr(match_text[:30])}{'...' if len(match_text) > 30 else ''}")

            if match_hash not in seen_hashes:
                valid_matches.append(match_text)
                seen_hashes.add(match_hash)
                print(f"  -> 添加到结果")
            else:
                print(f"  -> 跳过重复内容")

        if valid_matches:
            code_content = '\n\n'.join(valid_matches)
            print(f"\n最终结果长度: {len(code_content)}")
            print(f"最终结果: {repr(code_content[:100])}{'...' if len(code_content) > 100 else ''}")
            return code_content

    print("\n未找到标准代码块，检查整体是否为代码...")
    return ""


if __name__ == "__main__":
    # 测试用例 - 模拟可能出现的问题
    test_cases = [
        # 带语言标识的代码块
        """```java
public class Test {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}
```""",

        # 可能导致重复的复杂情况
        """这里是一些说明文字 `System.out.println("test")` 然后是代码块：

```java
public class Example {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}
```

还有一些说明 `public static void main` 之类的。
""",
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*50}")
        print(f"测试用例 {i}:")
        result = debug_extract_code_blocks(test)
        print(f"结果: {repr(result)}")
        print('='*50)