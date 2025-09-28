# Repository Guidelines

## Project Structure & Module Organization
The repository centers on `code_test.py`, a PyQt6 desktop runner that wires together every module. Supporting packages live under `gemini_assistant/`: `core/` owns configuration, logging, and single-instance guards; `services/` houses Gemini and GPT API clients plus shared network helpers; `ui/` renders overlays, prompt management, and screenshot selection; `utils/` contains hotkey handling, screenshot capture, configuration migration, and constants. Top-level artifacts such as `model_config.json` and `*backup.py` files store runtime defaults and fallbacks; keep large assets (for example, `11111.png`) out of version control unless strictly required.

## Build, Test & Development Commands
- `python -m venv .venv; .venv\Scripts\activate`: create and enter an isolated environment.
- `pip install PyQt6 requests markdown-it-py mss pynput psutil pyperclip openai`: install the minimal dependencies surfaced by `check_requirements.py`.
- `python check_requirements.py`: verify that all essential packages are present.
- `python code_test.py`: launch the assistant UI; use when exercising end-to-end flows.

## Coding Style & Naming Conventions
Use Python 3.11+ with four-space indentation, module-level docstrings, and type hints mirroring the existing codebase. Favor `snake_case` for functions and module names, `PascalCase` for classes (see `GeminiAssistantApp`), and SCREAMING_SNAKE_CASE for constants defined in `utils/constants.py`. Route diagnostics through `LogManager` rather than `print`, and colocate feature-specific helpers next to their UI or service counterparts.

## Testing Guidelines
Automated tests are minimal today; prioritize adding `pytest`-style suites under `gemini_assistant/tests/` (create the folder if absent) with files named `test_*.py`. Exercise API integrations via stubbed responses and mock the PyQt event loop for UI behaviors. While tests mature, document manual validation steps alongside pull requests and run `python code_test.py` to validate prompt workflows, screenshot capture, and overlay rendering.

## Commit & Pull Request Guidelines
Git metadata is not bundled with this workspace, so default to Conventional Commits (for example, `feat: add toast notification throttling` or `fix: guard mss capture errors`). Every pull request should summarize behavior changes, list configuration impacts (keys added to `model_config.json`, hotkeys modified, etc.), reference related issues or tickets, and attach screenshots/GIFs when UI changes affect overlays or selectors. Highlight any new dependencies and call out manual test coverage performed.

## Security & Configuration Tips
Keep API credentials in local-only config files (for example, `model_config.json`) and never commit secrets. Validate network connectivity with `services/network_utils.py` helpers instead of ad-hoc requests. When adjusting migration logic, ensure `utils/config_migrator.py` gracefully handles missing keys so upgrades remain backward compatible.
