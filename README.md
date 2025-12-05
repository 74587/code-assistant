# AI Screenshot Assistant

A desktop application that captures screenshots and analyzes them using AI (Google Gemini / OpenAI GPT). Features a stealth overlay display with anti-screenshot protection.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.4+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

## Features

- **Multi-AI Support**: Switch between Google Gemini and OpenAI GPT
- **Smart Screenshot**: Select screen regions or capture full screen
- **Stealth Overlay**: Semi-transparent floating window that blends with any background
- **Anti-Screenshot Protection**: Overlay is invisible to screen capture tools (Windows)
- **Global Hotkeys**: System-wide keyboard shortcuts for quick access
- **Multiple Prompts**: Configure multiple AI prompts and switch between them
- **Code Extraction**: Automatically extracts and copies code blocks to clipboard
- **Streaming Response**: Real-time display of AI responses

## Screenshots

> Screenshots coming soon

## Installation

### Prerequisites

- Python 3.10 or higher
- Windows 10/11 (for anti-screenshot feature)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-screenshot-assistant.git
cd ai-screenshot-assistant
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the application:
```bash
copy model_config.example.json model_config.json
```

5. Edit `model_config.json` and add your API keys:
   - For Gemini: Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - For GPT: Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)

## Usage

### Start the Application

```bash
python main.py
```

### Default Hotkeys

| Hotkey | Action |
|--------|--------|
| `Alt+Z` | Capture screenshot and send to AI |
| `Alt+Q` | Toggle overlay visibility |
| `Alt+W` | Capture screenshot only (add to history) |
| `Alt+V` | Clear screenshot history |
| `Alt+1-9` | Switch between prompts |
| `Alt+S` | Switch AI provider |
| `Alt+Up/Down` | Scroll overlay content |

### Configuration

The application uses `model_config.json` for all settings. You can configure:

- AI provider settings (API keys, models, base URLs)
- Network proxy settings
- UI preferences (overlay opacity, window size)
- Custom prompts
- Hotkey bindings

## Project Structure

```
ai-screenshot-assistant/
├── main.py                    # Application entry point
├── model_config.example.json  # Configuration template
├── requirements.txt           # Python dependencies
├── ai_assistant/
│   ├── core/
│   │   ├── config_manager.py  # Configuration management
│   │   ├── log_manager.py     # Logging system
│   │   └── single_instance.py # Single instance lock
│   ├── services/
│   │   ├── ai/                # AI service abstraction
│   │   ├── gemini_api.py      # Gemini API client
│   │   ├── gpt_api.py         # GPT API client
│   │   └── network_utils.py   # Network utilities
│   ├── ui/
│   │   ├── overlay.py         # Stealth overlay window
│   │   ├── styles.py          # Application styles
│   │   ├── theme/             # Design tokens system
│   │   └── ...                # Other UI components
│   └── utils/
│       ├── constants.py       # Application constants
│       ├── hotkey_handler.py  # Global hotkey management
│       └── screenshot.py      # Screenshot utilities
```

## Security Features

### Anti-Screenshot Protection

The overlay window uses Windows `SetWindowDisplayAffinity` API with `WDA_EXCLUDEFROMCAPTURE` flag, making it invisible to:
- Screenshot tools (Snipping Tool, ShareX, etc.)
- Screen recording software
- Video conferencing screen share

> **Note**: This feature only works on Windows 10/11.

### Stealth Design

The overlay is designed to be inconspicuous:
- High transparency (adjustable 50-255)
- Muted text colors
- No visible borders or shadows
- Minimal title bar

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Style

This project follows PEP 8 guidelines. Use a linter like flake8 or black for code formatting.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [Google Generative AI](https://ai.google.dev/) - Gemini API
- [OpenAI](https://openai.com/) - GPT API
- [pynput](https://pynput.readthedocs.io/) - Keyboard monitoring
- [mss](https://python-mss.readthedocs.io/) - Screen capture

## Disclaimer

This tool is intended for personal productivity use. Please ensure compliance with your organization's policies and applicable laws when using AI services and screen capture functionality.
