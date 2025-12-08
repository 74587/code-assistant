# AI Screenshot Assistant

A desktop application that captures screenshots and analyzes them using AI (Google Gemini / OpenAI GPT). Features a stealth overlay display with **anti-screenshot protection** - perfect for quick AI-assisted problem-solving during online assessments.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.4+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

[中文文档](README_CN.md) | English

## 🎯 What is this?

This tool helps you **instantly ask AI about anything on your screen**:

- 📚 **Daily Learning**: Quickly screenshot any problem or code and get AI explanations
- 💼 **Online Interviews/Assessments**: Get discreet AI assistance during coding tests
- 🛡️ **Anti-Detection**: The overlay window is **invisible to screenshot tools** and screen recording software

> **Key Feature**: When anti-screenshot protection is enabled, the AI response overlay cannot be captured by any screen recording or screenshot tool (Snipping Tool, ShareX, OBS, video conferencing screen share, etc.)

## ✨ Features

- **Multi-AI Support**: Switch between Google Gemini and OpenAI GPT
- **Smart Screenshot**: Select screen regions with crosshair selector
- **Stealth Overlay**: Semi-transparent floating window that blends with any background
- **🔒 Anti-Screenshot Protection**: Overlay is invisible to screen capture tools (Windows)
- **Global Hotkeys**: System-wide keyboard shortcuts for quick access
- **Multiple Prompts**: Configure multiple AI prompts with dedicated hotkeys
- **Auto Code Extraction**: Automatically extracts and copies code blocks to clipboard
- **Streaming Response**: Real-time display of AI responses

## 📸 Screenshots

### Main Interface
![Main Settings](assets/main-settings-1.png)

### Provider Settings
![Provider Settings](assets/main-settings-2.png)

### AI Response Overlay
![Overlay Window](assets/overlay.png)

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Windows 10/11 (for anti-screenshot feature)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-screenshot-assistant.git
cd ai-screenshot-assistant

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Create configuration file
copy model_config.example.json model_config.json
```

### Configure API Keys

Edit `model_config.json` and add your API keys:
- **Gemini**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **GPT**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)

### Run

```bash
python main.py
```

## ⌨️ Hotkeys

| Hotkey | Action |
|--------|--------|
| `Alt+Z` | Capture screenshot and send to AI |
| `Alt+Q` | Toggle overlay visibility |
| `Alt+W` | Capture screenshot only (add to history) |
| `Alt+V` | Clear screenshot history |
| `Alt+1-9` | Switch between prompts |
| `Alt+S` | Switch AI provider |
| `Alt+Up/Down` | Scroll overlay content |

## 🛡️ Anti-Screenshot Protection

The overlay window uses Windows `SetWindowDisplayAffinity` API with `WDA_EXCLUDEFROMCAPTURE` flag, making it **invisible** to:

- ✅ Windows Snipping Tool
- ✅ ShareX, Greenshot, and other screenshot tools
- ✅ OBS Studio and screen recording software
- ✅ Zoom, Teams, and video conferencing screen share
- ✅ Online proctoring software

> **Note**: This feature only works on Windows 10/11 and can be toggled on/off in settings.

### Stealth Design

The overlay is designed to be inconspicuous:
- High transparency (adjustable 50-255)
- Muted text colors that blend with any background
- No visible borders or shadows
- Minimal, almost invisible title bar

## 📁 Project Structure

```
ai-screenshot-assistant/
├── main.py                    # Application entry point
├── model_config.example.json  # Configuration template
├── requirements.txt           # Python dependencies
├── ai_assistant/
│   ├── core/                  # Core functionality
│   ├── services/              # AI API clients
│   ├── ui/                    # UI components
│   └── utils/                 # Utilities
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is intended for personal productivity and learning purposes. Users are responsible for ensuring compliance with:
- Your organization's policies
- Exam/assessment rules and regulations
- Applicable laws in your jurisdiction

The developers are not responsible for any misuse of this software.
