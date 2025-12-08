# AI 截图助手

一款桌面应用程序，通过截图并使用 AI（Google Gemini / OpenAI GPT）进行分析。具有隐蔽式浮窗显示和 **防截屏保护** 功能——非常适合在线笔试/面试时快速获取 AI 辅助。

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.4+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

[English](README.md) | 中文

## 🎯 这是什么？

这个工具可以帮你 **随手截图，立即问 AI**：

- 📚 **日常学习**：遇到问题或代码直接截图，快速获取 AI 解释
- 💼 **在线笔试/面试**：在编程测试时获取隐蔽的 AI 辅助
- 🛡️ **防检测**：浮窗 **对截图工具完全不可见**，不会被录屏或监考软件发现

> **核心特性**：开启防截屏保护后，AI 回复浮窗无法被任何截屏录屏工具捕获（截图工具、ShareX、OBS、视频会议屏幕共享、在线监考软件等全部无效）

## ✨ 功能特性

- **多 AI 支持**：在 Google Gemini 和 OpenAI GPT 之间自由切换
- **智能截图**：十字准星区域选择器
- **隐蔽浮窗**：半透明悬浮窗口，可与任何背景融合
- **🔒 防截屏保护**：浮窗对截屏工具不可见（仅限 Windows）
- **全局热键**：系统级快捷键，随时快速调用
- **多提示词**：配置多个 AI 提示词，每个可绑定独立热键
- **自动代码提取**：自动提取代码块并复制到剪贴板
- **流式响应**：实时显示 AI 响应内容

## 📸 截图预览

### 主界面
![主界面设置](assets/main-settings-1.png)

### 服务商配置
![服务商设置](assets/main-settings-2.png)

### AI 回复浮窗
![浮窗效果](assets/overlay.png)

## 🚀 快速开始

### 环境要求

- Python 3.10 或更高版本
- Windows 10/11（防截屏功能需要）

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/yourusername/ai-screenshot-assistant.git
cd ai-screenshot-assistant

# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 创建配置文件
copy model_config.example.json model_config.json
```

### 配置 API 密钥

编辑 `model_config.json` 并添加你的 API 密钥：
- **Gemini**：从 [Google AI Studio](https://makersuite.google.com/app/apikey) 获取
- **GPT**：从 [OpenAI Platform](https://platform.openai.com/api-keys) 获取

### 运行

```bash
python main.py
```

## ⌨️ 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Alt+Z` | 截图并发送到 AI 分析 |
| `Alt+Q` | 显示/隐藏浮窗 |
| `Alt+W` | 仅截图（添加到历史） |
| `Alt+V` | 清空截图历史 |
| `Alt+1-9` | 切换提示词 |
| `Alt+S` | 切换 AI 服务商 |
| `Alt+↑/↓` | 滚动浮窗内容 |

## 🛡️ 防截屏保护

浮窗使用 Windows `SetWindowDisplayAffinity` API 和 `WDA_EXCLUDEFROMCAPTURE` 标志，使其对以下工具 **完全不可见**：

- ✅ Windows 截图工具
- ✅ ShareX、Greenshot 等截图软件
- ✅ OBS Studio 等录屏软件
- ✅ Zoom、腾讯会议等视频会议屏幕共享
- ✅ 在线监考/防作弊软件

> **注意**：此功能仅在 Windows 10/11 上有效，可在设置中开启或关闭。

### 隐蔽设计

浮窗设计追求低调隐蔽：
- 高透明度（可调节 50-255）
- 柔和的文字颜色，可与任何背景融合
- 无可见边框和阴影
- 极简、几乎不可见的标题栏

## 📁 项目结构

```
ai-screenshot-assistant/
├── main.py                    # 应用入口
├── model_config.example.json  # 配置模板
├── requirements.txt           # Python 依赖
├── ai_assistant/
│   ├── core/                  # 核心功能
│   ├── services/              # AI API 客户端
│   ├── ui/                    # UI 组件
│   └── utils/                 # 工具类
```

## 🤝 参与贡献

欢迎贡献代码！请随时提交 Pull Request。

## 📄 开源许可

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## ⚠️ 免责声明

本工具仅供个人效率提升和学习使用。用户有责任确保遵守：
- 所在组织/公司的相关政策
- 考试/测试的规则和规定
- 所在地区的适用法律法规

开发者对本软件的任何滥用行为不承担责任。
