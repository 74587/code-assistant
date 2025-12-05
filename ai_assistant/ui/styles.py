"""
应用程序样式定义 v2.0
现代化商业级视觉设计
"""

from pathlib import Path

try:
    from .theme import DesignTokens
except ImportError:  # pragma: no cover
    from ai_assistant.ui.theme import DesignTokens


class AppStyles:
    """应用程序样式类，支持从外部QSS资源加载样式。"""

    _RESOURCE_DIR = Path(__file__).resolve().parent / "resources"

    # 使用设计令牌构建现代化样式
    _MAIN_WINDOW_FALLBACK = f"""
        /* ═══════════════════════════════════════════════════════════
           主窗口 - 现代深色渐变背景
           ═══════════════════════════════════════════════════════════ */
        QMainWindow {{
            background: qlineargradient(x1:0, y1:0, x2:0.5, y2:1,
                stop:0 {DesignTokens.colors.BG_BASE},
                stop:0.5 {DesignTokens.colors.BG_PRIMARY},
                stop:1 #0c1222);
            color: {DesignTokens.colors.TEXT_PRIMARY};
        }}

        QWidget {{
            background: transparent;
            color: {DesignTokens.colors.TEXT_PRIMARY};
            font-family: {DesignTokens.typography.FONT_FAMILY};
        }}

        /* ═══════════════════════════════════════════════════════════
           标签样式
           ═══════════════════════════════════════════════════════════ */
        QLabel {{
            color: {DesignTokens.colors.TEXT_PRIMARY};
            background: transparent;
        }}

        QLabel[class="title"] {{
            font-weight: {DesignTokens.typography.WEIGHT_SEMIBOLD};
            color: {DesignTokens.colors.TEXT_PRIMARY};
            font-size: {DesignTokens.typography.SIZE_LG}px;
        }}

        QLabel[class="subtitle"] {{
            color: {DesignTokens.colors.TEXT_MUTED};
            font-size: {DesignTokens.typography.SIZE_SM}px;
        }}

        QLabel[class="section-header"] {{
            font-weight: {DesignTokens.typography.WEIGHT_BOLD};
            font-size: {DesignTokens.typography.SIZE_XL}px;
            color: {DesignTokens.colors.TEXT_PRIMARY};
        }}

        QLabel[class="section-helper"] {{
            color: {DesignTokens.colors.TEXT_MUTED};
            font-size: {DesignTokens.typography.SIZE_SM}px;
        }}

        /* ═══════════════════════════════════════════════════════════
           选项卡 - 现代化胶囊风格
           ═══════════════════════════════════════════════════════════ */
        QTabWidget::pane {{
            border: 1px solid {DesignTokens.colors.BORDER_SUBTLE};
            border-radius: {DesignTokens.radius.CARD_LG}px;
            background: rgba(15, 23, 42, 0.6);
            margin: 8px 12px 0 12px;
            padding: 20px 24px 24px 24px;
        }}

        QTabWidget > QWidget > QWidget {{
            background: transparent;
        }}

        QTabWidget::tab-bar {{
            alignment: center;
        }}

        QTabBar::tab {{
            background: {DesignTokens.colors.BG_SECONDARY};
            border: 1px solid transparent;
            border-bottom: none;
            border-top-left-radius: {DesignTokens.radius.LG}px;
            border-top-right-radius: {DesignTokens.radius.LG}px;
            padding: 12px 24px;
            margin-right: 8px;
            font-weight: {DesignTokens.typography.WEIGHT_SEMIBOLD};
            color: {DesignTokens.colors.TEXT_TERTIARY};
            font-size: {DesignTokens.typography.SIZE_BASE}px;
            min-width: 130px;
        }}

        QTabBar::tab:selected {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(99, 102, 241, 0.15),
                stop:1 rgba(6, 182, 212, 0.1));
            color: {DesignTokens.colors.PRIMARY_LIGHT};
            border-color: {DesignTokens.colors.BORDER_HOVER};
        }}

        QTabBar::tab:hover:!selected {{
            color: {DesignTokens.colors.ACCENT_LIGHT};
            background: rgba(30, 41, 59, 0.8);
        }}

        /* ═══════════════════════════════════════════════════════════
           分组框
           ═══════════════════════════════════════════════════════════ */
        QGroupBox {{
            font-weight: {DesignTokens.typography.WEIGHT_SEMIBOLD};
            border: 1px solid {DesignTokens.colors.BORDER_SUBTLE};
            border-radius: {DesignTokens.radius.CARD}px;
            margin-top: 14px;
            padding: 22px 18px 18px 18px;
            background: {DesignTokens.colors.BG_CARD};
        }}

        QGroupBox::title {{
            subcontrol-origin: padding;
            subcontrol-position: top left;
            padding: 0 12px;
            margin-top: 6px;
            margin-left: 10px;
            color: {DesignTokens.colors.PRIMARY_LIGHT};
            background: transparent;
            font-weight: {DesignTokens.typography.WEIGHT_SEMIBOLD};
        }}

        QGroupBox[class="settings-card"] {{
            margin-top: 0;
            padding: 18px 18px 16px 18px;
        }}

        /* ═══════════════════════════════════════════════════════════
           设置卡片 - 玻璃质感
           ═══════════════════════════════════════════════════════════ */
        QFrame[class="settings-card"] {{
            border: 1px solid {DesignTokens.colors.BORDER_SUBTLE};
            border-radius: {DesignTokens.radius.CARD}px;
            background: {DesignTokens.colors.BG_CARD};
            padding: 0;
        }}

        QLabel[class="card-header"] {{
            font-size: {DesignTokens.typography.SIZE_LG}px;
            font-weight: {DesignTokens.typography.WEIGHT_SEMIBOLD};
            color: {DesignTokens.colors.PRIMARY_LIGHT};
        }}

        QLabel[class="card-subheader"] {{
            font-size: {DesignTokens.typography.SIZE_BASE}px;
            font-weight: {DesignTokens.typography.WEIGHT_SEMIBOLD};
            color: {DesignTokens.colors.ACCENT_LIGHT};
        }}

        QLabel[class="card-helper"] {{
            color: {DesignTokens.colors.TEXT_MUTED};
            font-size: {DesignTokens.typography.SIZE_SM}px;
        }}

        QRadioButton[class="provider-option"] {{
            font-size: {DesignTokens.typography.SIZE_BASE}px;
        }}

        /* ═══════════════════════════════════════════════════════════
           输入控件 - 精致边框与焦点效果
           ═══════════════════════════════════════════════════════════ */
        QPlainTextEdit,
        QTextEdit,
        QLineEdit {{
            background: {DesignTokens.colors.BG_PRIMARY};
            border: 1px solid {DesignTokens.colors.BORDER_DEFAULT};
            border-radius: {DesignTokens.radius.INPUT}px;
            color: {DesignTokens.colors.TEXT_PRIMARY};
            padding: 10px 14px;
            selection-background-color: {DesignTokens.colors.PRIMARY};
            font-size: {DesignTokens.typography.SIZE_BASE}px;
        }}

        QLineEdit[echoMode="2"] {{
            letter-spacing: 3px;
        }}

        QLineEdit:focus,
        QPlainTextEdit:focus,
        QTextEdit:focus {{
            border-color: {DesignTokens.colors.PRIMARY};
            background: rgba(15, 23, 42, 0.9);
        }}

        QLineEdit:hover,
        QPlainTextEdit:hover,
        QTextEdit:hover {{
            border-color: {DesignTokens.colors.BORDER_HOVER};
        }}

        /* ═══════════════════════════════════════════════════════════
           下拉框 - 现代化设计
           ═══════════════════════════════════════════════════════════ */
        QComboBox {{
            background: {DesignTokens.colors.BG_PRIMARY};
            border: 1px solid {DesignTokens.colors.BORDER_DEFAULT};
            border-radius: {DesignTokens.radius.INPUT}px;
            padding: 10px 14px;
            color: {DesignTokens.colors.TEXT_PRIMARY};
            font-size: {DesignTokens.typography.SIZE_BASE}px;
        }}

        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 32px;
            border-left: 1px solid {DesignTokens.colors.BORDER_SUBTLE};
            background: {DesignTokens.colors.BG_SECONDARY};
            border-top-right-radius: {DesignTokens.radius.INPUT}px;
            border-bottom-right-radius: {DesignTokens.radius.INPUT}px;
        }}

        QComboBox::down-arrow {{
            width: 12px;
            height: 6px;
            border-style: solid;
            border-width: 6px 5px 0 5px;
            border-color: {DesignTokens.colors.PRIMARY_LIGHT} transparent transparent transparent;
            background: transparent;
            margin: 0 10px 0 0;
        }}

        QComboBox::down-arrow:on,
        QComboBox::down-arrow:hover {{
            border-top-color: {DesignTokens.colors.ACCENT};
        }}

        QComboBox:hover {{
            border-color: {DesignTokens.colors.BORDER_HOVER};
        }}

        QComboBox:focus {{
            border-color: {DesignTokens.colors.PRIMARY};
        }}

        QComboBox QAbstractItemView {{
            background: {DesignTokens.colors.BG_PRIMARY};
            border: 1px solid {DesignTokens.colors.BORDER_DEFAULT};
            selection-background-color: {DesignTokens.colors.PRIMARY_DARK};
            selection-color: {DesignTokens.colors.TEXT_PRIMARY};
            border-radius: {DesignTokens.radius.INPUT}px;
            padding: 4px;
        }}

        /* ═══════════════════════════════════════════════════════════
           按钮 - 渐变与微交互
           ═══════════════════════════════════════════════════════════ */
        QPushButton {{
            border-radius: {DesignTokens.radius.BUTTON}px;
            padding: 10px 18px;
            font-weight: {DesignTokens.typography.WEIGHT_SEMIBOLD};
            border: 1px solid transparent;
            background: {DesignTokens.colors.BG_SECONDARY};
            color: {DesignTokens.colors.TEXT_PRIMARY};
            font-size: {DesignTokens.typography.SIZE_BASE}px;
        }}

        QPushButton:hover {{
            background: {DesignTokens.colors.BG_TERTIARY};
            color: {DesignTokens.colors.TEXT_PRIMARY};
        }}

        QPushButton:pressed {{
            background: rgba(51, 65, 85, 0.8);
        }}

        QPushButton[class="primary"] {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {DesignTokens.colors.PRIMARY},
                stop:1 {DesignTokens.colors.PRIMARY_DARK});
            color: {DesignTokens.colors.TEXT_PRIMARY};
            border: 1px solid {DesignTokens.colors.PRIMARY};
        }}

        QPushButton[class="primary"]:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {DesignTokens.colors.PRIMARY_LIGHT},
                stop:1 {DesignTokens.colors.PRIMARY});
        }}

        QPushButton[class="secondary"] {{
            background: {DesignTokens.colors.BG_SECONDARY};
            border: 1px solid {DesignTokens.colors.BORDER_DEFAULT};
        }}

        QPushButton[class="secondary"]:hover {{
            background: {DesignTokens.colors.BG_TERTIARY};
            border-color: {DesignTokens.colors.BORDER_HOVER};
        }}

        QPushButton[class="success"] {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {DesignTokens.colors.SUCCESS},
                stop:1 #059669);
            border: 1px solid {DesignTokens.colors.SUCCESS};
        }}

        QPushButton[class="success"]:hover {{
            background: {DesignTokens.colors.SUCCESS_LIGHT};
        }}

        QPushButton[class="danger"] {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {DesignTokens.colors.DANGER},
                stop:1 #dc2626);
            border: 1px solid {DesignTokens.colors.DANGER};
        }}

        QPushButton[class="danger"]:hover {{
            background: {DesignTokens.colors.DANGER_LIGHT};
        }}

        /* ═══════════════════════════════════════════════════════════
           列表与表格
           ═══════════════════════════════════════════════════════════ */
        QListWidget,
        QTreeWidget,
        QTableWidget {{
            border: 1px solid {DesignTokens.colors.BORDER_DEFAULT};
            border-radius: {DesignTokens.radius.LG}px;
            background: {DesignTokens.colors.BG_PRIMARY};
            selection-background-color: {DesignTokens.colors.PRIMARY_DARK};
            selection-color: {DesignTokens.colors.TEXT_PRIMARY};
            alternate-background-color: rgba(30, 41, 59, 0.3);
        }}

        QListWidget::item,
        QTreeWidget::item {{
            padding: 8px 12px;
            border-radius: {DesignTokens.radius.SM}px;
        }}

        QListWidget::item:hover,
        QTreeWidget::item:hover {{
            background: rgba(99, 102, 241, 0.1);
        }}

        /* ═══════════════════════════════════════════════════════════
           滑块 - 现代化轨道与手柄
           ═══════════════════════════════════════════════════════════ */
        QSlider::groove:horizontal {{
            border: none;
            height: 6px;
            background: {DesignTokens.colors.BG_TERTIARY};
            border-radius: 3px;
        }}

        QSlider::sub-page:horizontal {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {DesignTokens.colors.PRIMARY},
                stop:1 {DesignTokens.colors.ACCENT});
            border-radius: 3px;
        }}

        QSlider::handle:horizontal {{
            background: {DesignTokens.colors.TEXT_PRIMARY};
            border: 3px solid {DesignTokens.colors.PRIMARY};
            width: 16px;
            height: 16px;
            margin: -6px 0;
            border-radius: 10px;
        }}

        QSlider::handle:horizontal:hover {{
            background: {DesignTokens.colors.PRIMARY_LIGHT};
            border-color: {DesignTokens.colors.ACCENT};
        }}

        /* ═══════════════════════════════════════════════════════════
           滚动区域与滚动条
           ═══════════════════════════════════════════════════════════ */
        QScrollArea {{
            border: none;
            background: transparent;
        }}

        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 4px 2px;
        }}

        QScrollBar::handle:vertical {{
            background: {DesignTokens.colors.BORDER_DEFAULT};
            border-radius: 4px;
            min-height: 40px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {DesignTokens.colors.TEXT_MUTED};
        }}

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            background: none;
            height: 0;
        }}

        QScrollBar:horizontal {{
            background: transparent;
            height: 8px;
            margin: 2px 4px;
        }}

        QScrollBar::handle:horizontal {{
            background: {DesignTokens.colors.BORDER_DEFAULT};
            border-radius: 4px;
            min-width: 40px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background: {DesignTokens.colors.TEXT_MUTED};
        }}

        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            background: none;
            width: 0;
        }}

        /* ═══════════════════════════════════════════════════════════
           文本浏览器
           ═══════════════════════════════════════════════════════════ */
        QTextBrowser {{
            border: 1px solid {DesignTokens.colors.BORDER_DEFAULT};
            border-radius: {DesignTokens.radius.LG}px;
            background: {DesignTokens.colors.BG_PRIMARY};
            color: {DesignTokens.colors.TEXT_PRIMARY};
            font-size: {DesignTokens.typography.SIZE_BASE}px;
            padding: 12px;
        }}

        /* ═══════════════════════════════════════════════════════════
           复选框与单选按钮
           ═══════════════════════════════════════════════════════════ */
        QCheckBox,
        QRadioButton {{
            color: {DesignTokens.colors.TEXT_PRIMARY};
            font-size: {DesignTokens.typography.SIZE_BASE}px;
            spacing: 8px;
        }}

        QCheckBox::indicator,
        QRadioButton::indicator {{
            width: 20px;
            height: 20px;
            border: 2px solid {DesignTokens.colors.BORDER_DEFAULT};
            border-radius: 5px;
            background: {DesignTokens.colors.BG_PRIMARY};
        }}

        QRadioButton::indicator {{
            border-radius: 11px;
        }}

        QCheckBox::indicator:hover,
        QRadioButton::indicator:hover {{
            border-color: {DesignTokens.colors.PRIMARY};
        }}

        QCheckBox::indicator:checked {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {DesignTokens.colors.PRIMARY},
                stop:1 {DesignTokens.colors.ACCENT});
            border-color: {DesignTokens.colors.PRIMARY};
        }}

        QRadioButton::indicator:checked {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {DesignTokens.colors.PRIMARY},
                stop:1 {DesignTokens.colors.ACCENT});
            border-color: {DesignTokens.colors.PRIMARY};
        }}

        /* ═══════════════════════════════════════════════════════════
           工具提示
           ═══════════════════════════════════════════════════════════ */
        QToolTip {{
            background: {DesignTokens.colors.BG_ELEVATED};
            color: {DesignTokens.colors.TEXT_PRIMARY};
            border: 1px solid {DesignTokens.colors.BORDER_DEFAULT};
            border-radius: {DesignTokens.radius.TOOLTIP}px;
            padding: 8px 12px;
            font-size: {DesignTokens.typography.SIZE_SM}px;
        }}

        /* ═══════════════════════════════════════════════════════════
           菜单
           ═══════════════════════════════════════════════════════════ */
        QMenu {{
            background: {DesignTokens.colors.BG_ELEVATED};
            border: 1px solid {DesignTokens.colors.BORDER_DEFAULT};
            border-radius: {DesignTokens.radius.MD}px;
            padding: 6px;
        }}

        QMenu::item {{
            padding: 8px 24px 8px 16px;
            border-radius: {DesignTokens.radius.SM}px;
            color: {DesignTokens.colors.TEXT_PRIMARY};
        }}

        QMenu::item:selected {{
            background: rgba(99, 102, 241, 0.15);
            color: {DesignTokens.colors.PRIMARY_LIGHT};
        }}

        QMenu::separator {{
            height: 1px;
            background: {DesignTokens.colors.BORDER_SUBTLE};
            margin: 6px 8px;
        }}
    """

    # 浮窗样式 - 使用设计令牌
    _OVERLAY_FALLBACK = f"""
        QTextBrowser {{
            background-color: transparent;
            border: none;
            font-family: {DesignTokens.typography.FONT_FAMILY};
            color: {DesignTokens.colors.TEXT_PRIMARY};
            line-height: 1.6;
        }}
        QTextBrowser code, QTextBrowser pre {{
            background-color: {DesignTokens.colors.BG_SECONDARY};
            padding: 12px 16px;
            border-radius: {DesignTokens.radius.MD}px;
            font-family: {DesignTokens.typography.FONT_FAMILY_MONO};
            border: 1px solid {DesignTokens.colors.BORDER_SUBTLE};
        }}
    """

    # 按钮框架样式 - 现代化卡片效果
    _BUTTON_FRAME_FALLBACK = f"""
        QFrame {{
            background: {DesignTokens.colors.BG_CARD};
            border: 1px solid {DesignTokens.colors.BORDER_SUBTLE};
            border-radius: {DesignTokens.radius.CARD}px;
            padding: 14px 20px;
        }}
    """

    @classmethod
    def _load_stylesheet(cls, filename: str, fallback: str) -> str:
        """从文件加载样式表，失败时返回内置样式"""
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

    @classmethod
    def get_toast_style(cls) -> str:
        """获取Toast提示样式"""
        return f"""
            QLabel {{
                background: {DesignTokens.colors.BG_OVERLAY};
                color: {DesignTokens.colors.TEXT_PRIMARY};
                border: 1px solid {DesignTokens.colors.BORDER_DEFAULT};
                border-radius: {DesignTokens.radius.LG}px;
                padding: 12px 20px;
                font-size: {DesignTokens.typography.SIZE_BASE}px;
                font-weight: {DesignTokens.typography.WEIGHT_MEDIUM};
            }}
        """

