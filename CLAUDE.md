# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Gemini Screenshot Assistant application written in Python using PyQt6. It provides an overlay interface for capturing screenshots and getting AI-powered analysis through Google's Gemini API.

## Core Components

### Main Application (`code_test.py`)
- **SingleInstance**: Ensures only one instance of the application runs at a time using PID-based file locking
- **ConfigManager**: Handles JSON configuration file management (`gemini_config.json`)
- **LogManager**: Manages application logging with Qt signals
- **Overlay**: PyQt6 transparent overlay window for displaying AI responses
- **ConfigWindow**: Main configuration GUI with tabbed interface

### Key Architecture Patterns
- **Threading**: Uses threading for non-blocking AI API calls and hotkey handlers
- **Qt Signals/Slots**: Asynchronous communication between components
- **Global Hotkeys**: Uses `pynput` library for system-wide keyboard monitoring
- **Screen Capture**: Uses `mss` library for cross-platform screenshot functionality

## Configuration

### Runtime Configuration (`gemini_config.json`)
```json
{
  "api_key": "YOUR_GEMINI_API_KEY",
  "proxy": "http://127.0.0.1:6789",
  "background_opacity": 120,
  "prompts": [...],
  "hotkeys": {...}
}
```

## Dependencies

The application requires these key Python packages:
- `PyQt6` - GUI framework
- `google-genai` - Gemini API client
- `pynput` - Global hotkey monitoring
- `mss` - Screen capture
- `markdown-it-py` - Markdown rendering
- `pyperclip` - Clipboard operations
- `psutil` - Process management

## Running the Application

### Start the Application
```bash
python code_test.py
```

### Key Features
- **Screenshot + AI Analysis**: Capture screen and get Gemini analysis
- **Multi-image Support**: Accumulates screenshots for context-aware analysis
- **Global Hotkeys**: System-wide keyboard shortcuts for different prompts
- **Overlay Display**: Transparent floating window for results
- **Code Extraction**: Automatically extracts and copies code blocks to clipboard

## Development Notes

### Hotkey Management
- Hotkeys are parsed from string format (e.g., "alt+z") to `pynput` key combinations
- The application maintains a registry of active hotkeys and handlers
- Each prompt can have its own custom hotkey binding

### Screen Capture Workflow
1. Capture current screen with `mss`
2. Optionally combine with previous screenshots for context
3. Send to Gemini API with prompt
4. Extract code blocks and copy to clipboard
5. Display formatted response in overlay

### Single Instance Protection
The application uses a PID-based lock file system to prevent multiple instances, with proper cleanup on exit.

### Proxy Support
Network requests can be routed through a proxy server specified in the configuration.