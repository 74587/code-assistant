"""
应用程序样式定义
"""

from pathlib import Path

try:
    from ..utils.constants import COLORS
except ImportError:  # pragma: no cover
    from gemini_assistant.utils.constants import COLORS


class AppStyles:
    """应用程序样式类，支持从外部QSS资源加载样式。"""

    _RESOURCE_DIR = Path(__file__).resolve().parent / "resources"

    _MAIN_WINDOW_FALLBACK = """
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0f172a, stop:1 #111827);
            color: #e2e8f0;
        }
        QWidget {
            background: transparent;
            color: #e2e8f0;
            font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
        }
        QLabel {
            color: #e2e8f0;
            background: transparent;
        }
        QLabel[class="title"] {
            font-weight: 600;
            color: #f8fafc;
            font-size: 14px;
        }
        QLabel[class="subtitle"] {
            color: #94a3b8;
            font-size: 12px;
        }
        QLabel[class="section-header"] {
            font-weight: 600;
            font-size: 16px;
            color: #f8fafc;
        }
        QLabel[class="section-helper"] {
            color: #94a3b8;
            font-size: 12px;
        }
        QTabWidget::pane {
            border: 1px solid #18263a;
            border-radius: 20px;
            background: #0f1829;
            margin: 8px 12px 0 12px;
            padding: 18px 20px 22px 20px;
        }
        QTabWidget > QWidget > QWidget {
            background: transparent;
        }
        QTabWidget::tab-bar {
            alignment: center;
        }
        QTabBar::tab {
            background: #1b253b;
            border: 1px solid transparent;
            border-bottom: none;
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
            padding: 10px 20px;
            margin-right: 6px;
            font-weight: 600;
            color: #94a3b8;
            font-size: 13px;
            min-width: 120px;
        }
        QTabBar::tab:selected {
            background: #111d33;
            color: #38bdf8;
            border-color: #1f2937;
        }
        QTabBar::tab:hover:!selected {
            color: #60a5fa;
        }
        QGroupBox {
            font-weight: 600;
            border: 1px solid #1b2b40;
            border-radius: 14px;
            margin-top: 12px;
            padding: 20px 16px 16px 16px;
            background: #101b2d;
        }
        QFrame[class="settings-card"] {
            border: 1px solid #1b2b40;
            border-radius: 14px;
            background: #101b2d;
            padding: 0;
        }
        QLabel[class="card-header"] {
            font-size: 15px;
            font-weight: 600;
            color: #7dd3fc;
        }
        QLabel[class="card-subheader"] {
            font-size: 14px;
            font-weight: 600;
            color: #7dd3fc;
        }
        QLabel[class="card-helper"] {
            color: #94a3b8;
            font-size: 12px;
        }
        QRadioButton[class="provider-option"] {
            font-size: 13px;
        }
        QGroupBox::title {
            subcontrol-origin: padding;
            subcontrol-position: top left;
            padding: 0 10px;
            margin-top: 6px;
            margin-left: 8px;
            color: #7dd3fc;
            background: transparent;
            font-weight: 600;
        }
        QGroupBox[class="settings-card"] {
            margin-top: 0;
            padding: 16px 16px 14px 16px;
        }
        QPlainTextEdit,
        QTextEdit,
        QLineEdit {
            background: #0f172a;
            border: 1px solid #1f2b44;
            border-radius: 10px;
            color: #f8fafc;
            padding: 8px 12px;
            selection-background-color: #38bdf8;
        }
        QLineEdit[echoMode="2"] {
            letter-spacing: 3px;
        }
        QLineEdit:focus,
        QPlainTextEdit:focus,
        QTextEdit:focus {
            border-color: #38bdf8;
            box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.25);
        }
        QComboBox {
            background: #0f172a;
            border: 1px solid #1f2b44;
            border-radius: 10px;
            padding: 8px 12px;
            color: #f8fafc;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 30px;
            border-left: 1px solid #1f2b44;
            background: #18263a;
        }
        QComboBox::down-arrow {
            width: 12px;
            height: 6px;
            border-style: solid;
            border-width: 6px 5px 0 5px;
            border-color: #93c5fd transparent transparent transparent;
            background: transparent;
            margin: 0 12px 0 0;
        }
        QComboBox::down-arrow:on,
        QComboBox::down-arrow:hover {
            border-top-color: #38bdf8;
        }
        QComboBox:hover {
            border-color: #38bdf8;
        }
        QComboBox QAbstractItemView {
            background: #0f172a;
            border: 1px solid #1f2b44;
            selection-background-color: #1e3a8a;
            selection-color: #f8fafc;
            border-radius: 10px;
        }
        QPushButton {
            border-radius: 10px;
            padding: 9px 16px;
            font-weight: 600;
            border: 1px solid transparent;
            background: #1b253b;
            color: #e2e8f0;
        }
        QPushButton:hover {
            background: #24324d;
            color: #f8fafc;
        }
        QPushButton[class="primary"] {
            background: #2563eb;
            color: #f8fafc;
        }
        QPushButton[class="primary"]:hover {
            background: #1d4ed8;
        }
        QPushButton[class="secondary"] {
            background: #1b253b;
        }
        QPushButton[class="secondary"]:hover {
            background: #24324d;
        }
        QPushButton[class="success"] {
            background: #16a34a;
        }
        QPushButton[class="success"]:hover {
            background: #15803d;
        }
        QPushButton[class="danger"] {
            background: #dc2626;
        }
        QPushButton[class="danger"]:hover {
            background: #b91c1c;
        }
        QListWidget,
        QTreeWidget,
        QTableWidget {
            border: 1px solid #1f2b44;
            border-radius: 12px;
            background: #0f172a;
            selection-background-color: #2563eb;
            selection-color: #f8fafc;
        }
        QSlider::groove:horizontal {
            border: none;
            height: 6px;
            background: #1f2b44;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #38bdf8;
            border: 2px solid #0f172a;
            width: 18px;
            height: 18px;
            margin: -7px 0;
            border-radius: 9px;
        }
        QSlider::handle:horizontal:hover {
            background: #60a5fa;
        }
        QScrollArea {
            border: none;
            background: transparent;
        }
        QScrollBar:vertical {
            background: transparent;
            width: 10px;
            margin: 2px;
        }
        QScrollBar::handle:vertical {
            background: #1f2b44;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical:hover {
            background: #2d3e5e;
        }
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            background: none;
            height: 0;
        }
        QTextBrowser {
            border: 1px solid #1f2b44;
            border-radius: 12px;
            background: #0f172a;
            color: #f8fafc;
            font-size: 13px;
        }
        QCheckBox,
        QRadioButton {
            color: #e2e8f0;
            font-size: 13px;
        }
        QCheckBox::indicator,
        QRadioButton::indicator {
            width: 18px;
            height: 18px;
            border: 1px solid #27364d;
            border-radius: 4px;
            background: #0d1524;
        }
        QRadioButton::indicator {
            border-radius: 9px;
        }
        QCheckBox::indicator:checked,
        QRadioButton::indicator:checked {
            background: #38bdf8;
            border: 1px solid #38bdf8;
        }
        QToolTip {
            background: #1b253b;
            color: #f8fafc;
            border: 1px solid #27364d;
            border-radius: 6px;
            padding: 6px 8px;
        }
    """

    _OVERLAY_FALLBACK = """
        QTextBrowser {
            background-color: transparent;
            border: none;
            font-family: Consolas, Segoe UI, monospace;
        }
        QTextBrowser pre, QTextBrowser code {
            background-color: rgba(0, 0, 0, 0.5);
            padding: 10px;
            border-radius: 5px;
            color: white;
        }
    """

    _BUTTON_FRAME_FALLBACK = """
        QFrame {
            background: #101b2d;
            border: 1px solid #18263a;
            border-radius: 16px;
            padding: 12px 18px;
        }
    """

    @classmethod
    def _load_stylesheet(cls, filename: str, fallback: str) -> str:
        path = cls._RESOURCE_DIR / filename
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return fallback

    @classmethod
    def get_main_window_style(cls) -> str:
        """获取主窗口样式"""
        return cls._load_stylesheet("main_window.qss", cls._MAIN_WINDOW_FALLBACK)

    @classmethod
    def get_overlay_style(cls) -> str:
        """获取浮窗样式"""
        return cls._load_stylesheet("overlay.qss", cls._OVERLAY_FALLBACK)

    @classmethod
    def get_button_frame_style(cls) -> str:
        """获取按钮框架样式"""
        return cls._load_stylesheet("button_frame.qss", cls._BUTTON_FRAME_FALLBACK)

