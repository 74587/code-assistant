#!/usr/bin/env python
"""
检查GPT API所需依赖
"""

def check_requirements():
    """检查所有必需的依赖"""
    print("🔍 检查GPT API依赖")
    print("=" * 50)

    requirements = []

    # 检查openai库
    try:
        import openai
        print(f"✅ openai: {openai.__version__}")
    except ImportError:
        print("❌ openai: 未安装")
        requirements.append("openai")

    # 检查其他依赖
    dependencies = [
        ("PyQt6", "PyQt6"),
        ("requests", "requests"),
        ("markdown_it", "markdown-it-py"),
        ("mss", "mss"),
        ("pynput", "pynput"),
        ("psutil", "psutil"),
        ("pyperclip", "pyperclip")
    ]

    for import_name, package_name in dependencies:
        try:
            module = __import__(import_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"✅ {package_name}: {version}")
        except ImportError:
            print(f"❌ {package_name}: 未安装")
            requirements.append(package_name)

    print("\n📊 检查结果:")
    if requirements:
        print(f"❌ 需要安装以下依赖:")
        for req in requirements:
            print(f"   pip install {req}")
        print(f"\n一键安装:")
        print(f"pip install {' '.join(requirements)}")
    else:
        print("✅ 所有依赖都已安装，可以正常使用GPT API功能")

    return len(requirements) == 0

if __name__ == "__main__":
    all_good = check_requirements()
    if not all_good:
        print("\n💡 提示: 安装缺失依赖后重新启动程序")