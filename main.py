#!/usr/bin/env python
"""
AI Screenshot Assistant - 重构版本
使用模块化架构的AI截图分析工具
"""

import sys
import os
import threading
import gc
from PyQt6 import QtCore, QtGui, QtWidgets

# 导入模块化组件
from ai_assistant.core.single_instance import SingleInstance
from ai_assistant.core.config_manager import ConfigManager
from ai_assistant.core.log_manager import LogManager
from ai_assistant.services.ai import AIServiceFactory
from ai_assistant.services.network_utils import NetworkUtils
from ai_assistant.utils.screenshot import capture_screen, extract_code_blocks, copy_to_clipboard
from ai_assistant.utils.hotkey_handler import HotkeyHandler
from ai_assistant.utils.constants import *
from ai_assistant.ui.styles import AppStyles
from ai_assistant.ui.toast import Toast
try:
    from ai_assistant.ui.fluent_theme import (
        FluentThemeManager,
        FluentTopBar,
        FluentStatusBar,
        FluentSettingsCard,
        FluentFormLayout,
        SectionTitle,
        add_form_row,
        FluentCardColumn,
        create_card_scroll_area,
    )
    from qfluentwidgets import CommandBar, FluentIcon
    HAS_FLUENT_THEME = True
except Exception:  # pragma: no cover - Fluent UI is optional
    FluentThemeManager = None
    FluentTopBar = None
    FluentStatusBar = None
    FluentSettingsCard = None
    FluentFormLayout = None
    SectionTitle = None
    add_form_row = None
    FluentCardColumn = None
    create_card_scroll_area = None
    CommandBar = None
    FluentIcon = None
    HAS_FLUENT_THEME = False

# 导入现代化UI组件
from ai_assistant.ui.modern_ui import (
    DesignSystem,
    MainWindowLayout,
    PageContainer,
    Card,
    FormRow,
    ModernLineEdit,
    ModernComboBox,
    ModernCheckBox,
    ModernRadioButton,
    ModernButton,
    IconButton,
)

# ──────────────────────── UI组件 ──────────────────────── #
from ai_assistant.ui.overlay import Overlay
from ai_assistant.ui.prompt_manager import PromptManagerWidget
from ai_assistant.ui.screenshot_selector import ScreenshotSelector
from ai_assistant.ui.log_viewer import LogViewerWidget

# ──────────────────────── 主应用程序 ──────────────────────── #
class AIAssistantApp(QtWidgets.QMainWindow):
    """主应用程序类"""

    # 定义信号，用于在主线程中处理操作
    trigger_screenshot_signal = QtCore.pyqtSignal(bool)  # True为带提示词，False为纯截图
    toggle_overlay_signal = QtCore.pyqtSignal()  # 切换浮窗显示
    toggle_provider_signal = QtCore.pyqtSignal()  # 切换AI服务商
    api_response_signal = QtCore.pyqtSignal(str)  # API响应信号

    def __init__(self, config_manager: ConfigManager, log_manager: LogManager, single_instance: SingleInstance):
        super().__init__()
        self.config_manager = config_manager
        self.log_manager = log_manager
        self.single_instance = single_instance

        # 初始化组件
        self.overlay = None
        self.ai_factory = AIServiceFactory(config_manager, log_manager)
        self.hotkey_handler = HotkeyHandler()
        self.screenshot_history = []
        self.screenshot_selector = None  # 截图选择器实例
        self.pending_prompt = None  # 待处理的提示词
        self.current_prompt_index = self.config_manager.get("current_prompt_index", 0)  # 当前选中的提示词索引

        self.use_fluent_theme = False
        self.fluent_theme_manager = None
        self.main_layout = None  # 现代化UI主布局
        self.top_bar = None
        self.status_bar = None
        self.status_label = None
        self.start_btn = None
        self.stop_btn = None
        self.tab_widget = None
        self.log_viewer = None
        self.provider_field_widgets = {}
        self.setWindowTitle(f"AI 截图助手 v{APP_VERSION} - 配置")
        # 从配置文件读取窗口尺寸
        min_width = self.config_manager.get("window_min_width", CONFIG_WINDOW_MIN_WIDTH)
        min_height = self.config_manager.get("window_min_height", CONFIG_WINDOW_MIN_HEIGHT)
        width = self.config_manager.get("window_width", CONFIG_WINDOW_WIDTH)
        height = self.config_manager.get("window_height", CONFIG_WINDOW_HEIGHT)

        self.setMinimumSize(min_width, min_height)
        self.resize(width, height)

        # 连接信号，确保在主线程中处理操作
        self.trigger_screenshot_signal.connect(self.handle_screenshot_in_main_thread)
        self.toggle_overlay_signal.connect(self.handle_toggle_overlay)
        self.toggle_provider_signal.connect(self.handle_toggle_provider)
        self.api_response_signal.connect(self.handle_api_response)

        self.setup_ui()
        self.setup_tray()
        self.settings_loading = True
        self.setup_settings_autosave()
        self.load_settings()
        self.update_status("未启动", STATUS_COLORS["stopped"])

    def setup_ui(self):
        """设置用户界面"""
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        self.use_fluent_theme = self._init_fluent_theme()

        if self.use_fluent_theme:
            self._setup_ui_fluent(central_widget)
        else:
            self.setStyleSheet(AppStyles.get_main_window_style())
            self._setup_ui_classic(central_widget)

    def _init_fluent_theme(self) -> bool:
        if not (USE_FLUENT_THEME and HAS_FLUENT_THEME):
            return False
        try:
            self.fluent_theme_manager = FluentThemeManager(primary="#5E81F4")
        except Exception as exc:  # pragma: no cover - Fluent UI fallback
            self.fluent_theme_manager = None
            self.log_manager.add_log(f"初始化 Fluent 主题失败: {exc}", level="ERROR")
            return False
        return True

    def _setup_ui_fluent(self, central_widget: QtWidgets.QWidget) -> None:
        """使用现代化UI框架构建界面"""
        self.setStyleSheet(f"background: {DesignSystem.Colors.BG_PRIMARY};")

        # 主布局框架
        self.main_layout = MainWindowLayout()
        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.main_layout)

        # 更新侧边栏版本号
        self.main_layout.sidebar.version_label.setText(f"v{APP_VERSION}")

        # ═══════════════════════════════════════════════════════════════════
        # 页面1: 基本设置
        # ═══════════════════════════════════════════════════════════════════
        settings_page = PageContainer("基本设置", "配置 AI 服务商、网络代理和界面选项")
        self._build_settings_page(settings_page)
        self.main_layout.add_page("⚙️", "基本设置", settings_page)

        # ═══════════════════════════════════════════════════════════════════
        # 页面2: 提示词管理
        # ═══════════════════════════════════════════════════════════════════
        prompts_page = PageContainer("提示词管理", "管理 AI 对话的系统提示词和快捷键")
        prompts_widget = PromptManagerWidget(self.config_manager, self.log_manager)
        prompts_page.add_widget(prompts_widget)
        self.main_layout.add_page("💬", "提示词", prompts_page)

        # ═══════════════════════════════════════════════════════════════════
        # 页面3: 运行日志
        # ═══════════════════════════════════════════════════════════════════
        show_log_tab = self.config_manager.get("show_log_tab", True)
        if show_log_tab:
            logs_page = PageContainer("运行日志", "查看应用程序运行状态和调试信息")
            self.log_viewer = LogViewerWidget(self.log_manager, True)
            logs_page.add_widget(self.log_viewer)
            self.main_layout.add_page("📋", "日志", logs_page)
        else:
            self.log_viewer = None

        # ═══════════════════════════════════════════════════════════════════
        # 底部控制栏按钮
        # ═══════════════════════════════════════════════════════════════════
        self.start_btn = ModernButton("🚀 启动监听", "success")
        self.start_btn.setMinimumWidth(140)
        self.start_btn.clicked.connect(self.start_listening)

        self.stop_btn = ModernButton("⏹️ 停止监听", "danger")
        self.stop_btn.setMinimumWidth(140)
        self.stop_btn.clicked.connect(self.stop_listening)
        self.stop_btn.setEnabled(False)

        self.main_layout.control_bar.add_button(self.start_btn)
        self.main_layout.control_bar.add_button(self.stop_btn)

        # 兼容性设置
        self.status_bar = None
        self.status_label = None
        self.top_bar = None
        self.tab_widget = None

    def _build_settings_page(self, page: PageContainer):
        """构建设置页面内容"""

        # ─────────────────────────────────────────────────────────────
        # AI 服务商卡片
        # ─────────────────────────────────────────────────────────────
        provider_card = Card("AI 服务商", "选择默认服务商并配置认证信息")

        # 服务商选择 - 使用胶囊样式单选按钮
        provider_select = QtWidgets.QWidget()
        provider_layout = QtWidgets.QHBoxLayout(provider_select)
        provider_layout.setContentsMargins(0, 0, 0, 0)
        provider_layout.setSpacing(8)

        current_provider = self.config_manager.get("provider", DEFAULT_PROVIDER)
        self.provider_radio_group = QtWidgets.QButtonGroup()
        self.provider_radios = {}

        for provider in AVAILABLE_PROVIDERS:
            radio = ModernRadioButton(provider)
            self.provider_radios[provider] = radio
            self.provider_radio_group.addButton(radio)
            provider_layout.addWidget(radio)

            if provider == current_provider:
                radio.setChecked(True)

            radio.toggled.connect(self.on_provider_radio_changed)

        provider_layout.addStretch()
        provider_card.add_widget(FormRow("服务商", provider_select))

        # 服务商配置堆栈
        self.provider_stack = QtWidgets.QStackedWidget()
        provider_card.add_widget(self.provider_stack)

        # Gemini 配置面板
        self.gemini_group = self._build_modern_provider_panel("Gemini")
        self.provider_stack.addWidget(self.gemini_group)

        # GPT 配置面板
        self.gpt_group = self._build_modern_provider_panel("GPT")
        self.provider_stack.addWidget(self.gpt_group)

        self.provider_widget_map = {
            "Gemini": self.gemini_group,
            "GPT": self.gpt_group,
        }

        if current_provider in self.provider_widget_map:
            self.provider_stack.setCurrentWidget(self.provider_widget_map[current_provider])

        page.add_widget(provider_card)

        # ─────────────────────────────────────────────────────────────
        # 网络配置卡片
        # ─────────────────────────────────────────────────────────────
        network_card = Card("网络配置", "为 API 请求配置代理服务")

        self.proxy_edit = ModernLineEdit("例如: http://127.0.0.1:7890")
        proxy_url = self.config_manager.get("proxy", "")
        self.proxy_edit.setText(proxy_url)
        network_card.add_widget(FormRow("代理地址", self.proxy_edit, "留空则不使用代理"))

        page.add_widget(network_card)

        # ─────────────────────────────────────────────────────────────
        # 界面配置卡片
        # ─────────────────────────────────────────────────────────────
        ui_card = Card("界面配置", "调整浮窗透明度和显示选项")

        # 透明度滑块
        opacity_widget = QtWidgets.QWidget()
        opacity_layout = QtWidgets.QHBoxLayout(opacity_widget)
        opacity_layout.setContentsMargins(0, 0, 0, 0)
        opacity_layout.setSpacing(16)

        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(50, 255)
        self.opacity_slider.setValue(self.config_manager.get("background_opacity", 120))
        self.opacity_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {DesignSystem.Colors.BG_TERTIARY};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {DesignSystem.Colors.PRIMARY};
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {DesignSystem.Colors.PRIMARY_HOVER};
            }}
            QSlider::sub-page:horizontal {{
                background: {DesignSystem.Colors.PRIMARY};
                border-radius: 3px;
            }}
        """)
        self.opacity_slider.valueChanged.connect(self.update_opacity_label)
        opacity_layout.addWidget(self.opacity_slider, 1)

        self.opacity_value_label = QtWidgets.QLabel(str(self.opacity_slider.value()))
        self.opacity_value_label.setFixedWidth(50)
        self.opacity_value_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.opacity_value_label.setStyleSheet(f"""
            font-size: {DesignSystem.Typography.SIZE_MD}px;
            font-weight: {DesignSystem.Typography.WEIGHT_SEMIBOLD};
            color: {DesignSystem.Colors.PRIMARY_HOVER};
            background: {DesignSystem.Colors.PRIMARY_LIGHT};
            border-radius: {DesignSystem.Radius.MD}px;
            padding: 6px;
        """)
        opacity_layout.addWidget(self.opacity_value_label)

        ui_card.add_widget(FormRow("浮窗透明度", opacity_widget, "数值越低越透明 (50-255)"))

        # 显示日志选项
        self.show_log_checkbox = ModernCheckBox("显示运行日志页面")
        self.show_log_checkbox.setChecked(self.config_manager.get("show_log_tab", True))
        ui_card.add_widget(FormRow("日志面板", self.show_log_checkbox))

        # 防截屏保护开关
        self.capture_protection_checkbox = ModernCheckBox("启用防截屏保护")
        self.capture_protection_checkbox.setChecked(self.config_manager.get("enable_capture_protection", True))
        ui_card.add_widget(FormRow("防截屏", self.capture_protection_checkbox, "关闭后浮窗和截图选择器可被截图工具捕获"))

        page.add_widget(ui_card)

        # ─────────────────────────────────────────────────────────────
        # 当前提示词状态卡片
        # ─────────────────────────────────────────────────────────────
        prompt_card = Card("当前提示词", "查看当前选用的提示词信息")

        self.current_prompt_label = QtWidgets.QLabel()
        self.current_prompt_label.setWordWrap(True)
        self.current_prompt_label.setStyleSheet(f"""
            font-size: {DesignSystem.Typography.SIZE_MD}px;
            color: {DesignSystem.Colors.TEXT_PRIMARY};
            background: {DesignSystem.Colors.BG_TERTIARY};
            padding: 16px;
            border-radius: {DesignSystem.Radius.MD}px;
            border-left: 3px solid {DesignSystem.Colors.PRIMARY};
        """)
        self.update_current_prompt_display()
        prompt_card.add_widget(self.current_prompt_label)

        page.add_widget(prompt_card)
        page.add_stretch()

    def _build_modern_provider_panel(self, provider: str) -> QtWidgets.QWidget:
        """构建现代化的服务商配置面板"""
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        if provider == "Gemini":
            # Gemini API Key
            api_key_row = QtWidgets.QWidget()
            api_key_layout = QtWidgets.QHBoxLayout(api_key_row)
            api_key_layout.setContentsMargins(0, 0, 0, 0)
            api_key_layout.setSpacing(8)

            self.gemini_api_key_edit = ModernLineEdit("请输入您的 Gemini API Key")
            self.gemini_api_key_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            api_key = self.config_manager.get("gemini.api_key", "")
            self.gemini_api_key_edit.setText(api_key)
            api_key_layout.addWidget(self.gemini_api_key_edit, 1)

            self.show_gemini_api_btn = IconButton("👁️", "显示/隐藏 API Key")
            self.show_gemini_api_btn.clicked.connect(self.toggle_gemini_api_visibility)
            api_key_layout.addWidget(self.show_gemini_api_btn)

            layout.addWidget(FormRow("API Key", api_key_row))

            # Gemini Base URL
            self.gemini_base_url_edit = ModernLineEdit("API 基础 URL")
            base_url = self.config_manager.get("gemini_base_url", "")
            self.gemini_base_url_edit.setText(base_url)
            layout.addWidget(FormRow("Base URL", self.gemini_base_url_edit))

            # Gemini 模型选择
            self.gemini_model_combo = ModernComboBox()
            models = self.config_manager.get("available_gemini_models", [])
            self.gemini_model_combo.addItems(models)
            current_model = self.config_manager.get("gemini_model", "")
            if current_model and current_model in models:
                self.gemini_model_combo.setCurrentText(current_model)
            layout.addWidget(FormRow("模型", self.gemini_model_combo))

            # Gemini 代理选项
            self.gemini_use_proxy_check = ModernCheckBox("为 Gemini 使用代理")
            self.gemini_use_proxy_check.setChecked(self.config_manager.get("gemini.use_proxy", False))
            layout.addWidget(FormRow("网络", self.gemini_use_proxy_check))

        else:  # GPT
            # GPT API Key
            api_key_row = QtWidgets.QWidget()
            api_key_layout = QtWidgets.QHBoxLayout(api_key_row)
            api_key_layout.setContentsMargins(0, 0, 0, 0)
            api_key_layout.setSpacing(8)

            self.gpt_api_key_edit = ModernLineEdit("请输入您的 OpenAI API Key")
            self.gpt_api_key_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            api_key = self.config_manager.get("gpt.api_key", "")
            self.gpt_api_key_edit.setText(api_key)
            api_key_layout.addWidget(self.gpt_api_key_edit, 1)

            self.show_gpt_api_btn = IconButton("👁️", "显示/隐藏 API Key")
            self.show_gpt_api_btn.clicked.connect(self.toggle_gpt_api_visibility)
            api_key_layout.addWidget(self.show_gpt_api_btn)

            layout.addWidget(FormRow("API Key", api_key_row))

            # GPT Base URL
            self.gpt_base_url_edit = ModernLineEdit("API 基础 URL")
            base_url = self.config_manager.get("gpt_base_url", "")
            self.gpt_base_url_edit.setText(base_url)
            layout.addWidget(FormRow("Base URL", self.gpt_base_url_edit))

            # GPT 模型选择
            self.gpt_model_combo = ModernComboBox()
            models = self.config_manager.get("available_gpt_models", [])
            self.gpt_model_combo.addItems(models)
            current_model = self.config_manager.get("gpt_model", "")
            if current_model and current_model in models:
                self.gpt_model_combo.setCurrentText(current_model)
            layout.addWidget(FormRow("模型", self.gpt_model_combo))

            # GPT 代理选项
            self.gpt_use_proxy_check = ModernCheckBox("为 GPT 使用代理")
            self.gpt_use_proxy_check.setChecked(self.config_manager.get("gpt.use_proxy", False))
            layout.addWidget(FormRow("网络", self.gpt_use_proxy_check))

        return panel

    def _setup_ui_classic(self, central_widget: QtWidgets.QWidget) -> None:
        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.tab_widget = self._create_tab_widget()
        layout.addWidget(self.tab_widget, 1)

        button_frame = QtWidgets.QFrame()
        button_frame.setStyleSheet(AppStyles.get_button_frame_style())
        button_layout = QtWidgets.QHBoxLayout(button_frame)

        self.status_bar = None
        self.status_label = QtWidgets.QLabel("⚫ 未启动")
        self.status_label.setStyleSheet(
            """
            color: #f56565;
            font-weight: 600;
            font-size: 15px;
            padding: 8px 12px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(245, 101, 101, 0.1), stop:1 rgba(245, 101, 101, 0.05));
            border-radius: 6px;
            border-left: 3px solid #f56565;
            """
        )

        self.start_btn = QtWidgets.QPushButton("🚀 启动监听")
        self.start_btn.setProperty("class", "success")
        self.start_btn.clicked.connect(self.start_listening)
        self.start_btn.setFixedHeight(44)

        self.stop_btn = QtWidgets.QPushButton("⏹️ 停止监听")
        self.stop_btn.setProperty("class", "danger")
        self.stop_btn.clicked.connect(self.stop_listening)
        self.stop_btn.setFixedHeight(44)
        self.stop_btn.setEnabled(False)

        button_layout.addWidget(self.status_label)
        button_layout.addStretch()
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)

        layout.addWidget(button_frame)

    def _create_tab_widget(self) -> QtWidgets.QTabWidget:
        tab_widget = QtWidgets.QTabWidget()
        tab_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        if self.use_fluent_theme:
            tab_widget.setDocumentMode(True)
            tab_widget.setStyleSheet(
                """
                QTabWidget::pane {
                    border: none;
                    background: transparent;
                }
                """
            )

        basic_tab = self.create_basic_tab()
        basic_tab.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        tab_widget.addTab(basic_tab, "⚙️ 基本设置")

        prompts_tab = self.create_prompts_tab()
        prompts_tab.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        tab_widget.addTab(prompts_tab, "💬 提示词管理")

        show_log_tab = self.config_manager.get("show_log_tab", True)
        if show_log_tab:
            logs_tab = self.create_log_tab()
            logs_tab.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
            tab_widget.addTab(logs_tab, "📋 运行日志")
        else:
            self.log_text = None
            self.log_manager.log_updated.connect(self.append_log)

        return tab_widget

    def _apply_button_style(self, button: QtWidgets.QPushButton, variant: str = "secondary", *, compact: bool = False) -> None:
        if not self.use_fluent_theme:
            return

        palettes = {
            "primary": ("rgba(94, 129, 244, 0.26)", "rgba(94, 129, 244, 0.36)", "rgba(94, 129, 244, 0.46)", "#e0e7ff"),
            "danger": ("rgba(248, 113, 113, 0.20)", "rgba(248, 113, 113, 0.30)", "rgba(248, 113, 113, 0.40)", "#fecaca"),
            "success": ("rgba(34, 197, 94, 0.20)", "rgba(34, 197, 94, 0.30)", "rgba(34, 197, 94, 0.40)", "#bbf7d0"),
            "secondary": ("rgba(148, 163, 184, 0.18)", "rgba(148, 163, 184, 0.28)", "rgba(148, 163, 184, 0.40)", "#e2e8f0"),
        }
        base, hover, pressed, text = palettes.get(variant, palettes["secondary"])
        height = 32 if compact else 36
        radius = 14 if compact else 18
        padding = "0 14px" if compact else "0 20px"

        button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        button.setFixedHeight(height)
        button.setStyleSheet(
            f"""
            QPushButton {{
                color: {text};
                background-color: {base};
                border: 1px solid {base};
                border-radius: {radius}px;
                padding: {padding};
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {hover};
                border-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: {pressed};
                border-color: {pressed};
            }}
            QPushButton:disabled {{
                color: rgba(148, 163, 184, 0.55);
                background-color: rgba(71, 85, 105, 0.24);
                border-color: rgba(71, 85, 105, 0.24);
            }}
            """
        )

    def _add_form_row(self, form, label_text: str, widget: QtWidgets.QWidget, helper_text: str | None = None) -> None:
        if form is None:
            return

        if hasattr(form, "add_row"):
            form.add_row(label_text, widget, helper_text=helper_text)
            return

        if helper_text:
            container = QtWidgets.QWidget()
            container_layout = QtWidgets.QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(6)
            container_layout.addWidget(widget)
            helper_label = QtWidgets.QLabel(helper_text)
            helper_label.setProperty("class", "card-helper")
            helper_label.setWordWrap(True)
            container_layout.addWidget(helper_label)
            widget = container

        form.addRow(label_text, widget)

    def _build_card(self, title: str, *, with_form: bool = True, icon=None, description: str = ""):
        if self.use_fluent_theme and FluentSettingsCard:
            card = FluentSettingsCard(title=title, description=description, icon=icon)
            card_layout = card.body_layout
            form = None
            if with_form:
                form = FluentFormLayout()
                card_layout.addLayout(form)
            return card, card_layout, form

        card = QtWidgets.QFrame()
        card.setProperty("class", "settings-card")
        card.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Maximum)
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        header = QtWidgets.QLabel(title)
        header.setProperty("class", "card-header")
        layout.addWidget(header)

        if description:
            helper = QtWidgets.QLabel(description)
            helper.setProperty("class", "card-helper")
            helper.setWordWrap(True)
            layout.addWidget(helper)

        form = None
        if with_form:
            form = QtWidgets.QFormLayout()
            form.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            form.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
            form.setHorizontalSpacing(12)
            form.setVerticalSpacing(12)
            layout.addLayout(form)

        return card, layout, form

    def _build_provider_panel(self, title: str):
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(0, 0 if self.use_fluent_theme else 6, 0, 0)
        layout.setSpacing(12 if self.use_fluent_theme else 8)

        if self.use_fluent_theme and SectionTitle:
            header = SectionTitle(title)
        else:
            header = QtWidgets.QLabel(title)
            header.setProperty("class", "card-subheader")
        layout.addWidget(header)

        if self.use_fluent_theme and FluentFormLayout:
            form = FluentFormLayout()
            layout.addLayout(form)
        else:
            form = QtWidgets.QFormLayout()
            form.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            form.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
            form.setHorizontalSpacing(12)
            form.setVerticalSpacing(12)
            layout.addLayout(form)

        return panel, layout, form

    def _create_provider_card(self):
        icon = getattr(FluentIcon, "ROBOT", None) if self.use_fluent_theme and FluentIcon else None
        description = "选择默认服务商并维护各自的认证信息。"
        card, card_layout, provider_form = self._build_card("🤖 AI 服务商", icon=icon, description=description)

        provider_widget = QtWidgets.QWidget()
        provider_row = QtWidgets.QHBoxLayout(provider_widget)
        provider_row.setContentsMargins(0, 0, 0, 0)
        provider_row.setSpacing(10 if self.use_fluent_theme else 12)

        current_provider = self.config_manager.get("provider", DEFAULT_PROVIDER)
        self.provider_radio_group = QtWidgets.QButtonGroup()
        self.provider_radios = {}

        for provider in AVAILABLE_PROVIDERS:
            radio = QtWidgets.QRadioButton(provider)
            radio.setMinimumHeight(28)
            radio.setProperty("class", "provider-option")
            self.provider_radios[provider] = radio
            self.provider_radio_group.addButton(radio)
            provider_row.addWidget(radio)

            if provider == current_provider:
                radio.setChecked(True)

            radio.toggled.connect(self.on_provider_radio_changed)

        provider_row.addStretch()
        self._add_form_row(provider_form, "服务商", provider_widget)

        self.provider_stack = QtWidgets.QStackedWidget()
        self.provider_stack.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )
        card_layout.addWidget(self.provider_stack)

        provider_specs = self._provider_field_specs()

        self.gemini_group = self._build_provider_panel_from_spec("Gemini", provider_specs["Gemini"])
        self.gpt_group = self._build_provider_panel_from_spec("GPT", provider_specs["GPT"])

        self.provider_stack.addWidget(self.gemini_group)
        self.provider_stack.addWidget(self.gpt_group)

        self.provider_widget_map = {
            "Gemini": self.gemini_group,
            "GPT": self.gpt_group,
        }

        if current_provider in self.provider_widget_map:
            self.provider_stack.setCurrentWidget(self.provider_widget_map[current_provider])

        return card

    def _provider_field_specs(self):
        return {
            "Gemini": {
                "title": "🟢 Gemini 配置",
                "fields": [
                    {
                        "type": "secret",
                        "attr": "gemini_api_key_edit",
                        "button_attr": "show_gemini_api_btn",
                        "label": "API Key",
                        "placeholder": "请输入您的 Gemini API Key",
                        "button_tooltip": "显示/隐藏 Gemini API Key",
                        "toggle_slot": self.toggle_gemini_api_visibility,
                        "value_paths": [
                            "ai_providers.gemini.api_key",
                            "api_key",
                        ],
                        "default": "",
                    },
                    {
                        "type": "line_edit",
                        "attr": "gemini_base_url_edit",
                        "label": "Base URL",
                        "placeholder": "API基础URL",
                        "value_paths": [
                            "ai_providers.gemini.base_url",
                            "gemini_base_url",
                        ],
                        "default": "",
                    },
                    {
                        "type": "checkbox",
                        "attr": "gemini_use_proxy_check",
                        "label": "网络",
                        "text": "为 Gemini 使用代理",
                        "value_paths": [
                            "ai_providers.gemini.use_proxy",
                            "gemini_use_proxy",
                        ],
                        "default": False,
                    },
                    {
                        "type": "combo",
                        "attr": "gemini_model_combo",
                        "label": "模型",
                        "items_paths": [
                            "available_gemini_models",
                        ],
                        "default_items": [],
                        "value_paths": [
                            "gemini_model",
                            "model",
                        ],
                        "default": "",
                    },
                ],
            },
            "GPT": {
                "title": "🔵 GPT 配置",
                "fields": [
                    {
                        "type": "secret",
                        "attr": "gpt_api_key_edit",
                        "button_attr": "show_gpt_api_btn",
                        "label": "API Key",
                        "placeholder": "请输入您的 OpenAI API Key",
                        "button_tooltip": "显示/隐藏 GPT API Key",
                        "toggle_slot": self.toggle_gpt_api_visibility,
                        "value_paths": [
                            "ai_providers.gpt.api_key",
                            "gpt_api_key",
                        ],
                        "default": "",
                    },
                    {
                        "type": "line_edit",
                        "attr": "gpt_base_url_edit",
                        "label": "Base URL",
                        "placeholder": "API基础URL",
                        "value_paths": [
                            "ai_providers.gpt.base_url",
                            "gpt_base_url",
                        ],
                        "default": "",
                    },
                    {
                        "type": "combo",
                        "attr": "gpt_model_combo",
                        "label": "模型",
                        "items_paths": [
                            "available_gpt_models",
                        ],
                        "default_items": [],
                        "value_paths": [
                            "gpt_model",
                        ],
                        "default": "",
                    },
                    {
                        "type": "checkbox",
                        "attr": "gpt_use_proxy_check",
                        "label": "网络",
                        "text": "为 GPT 使用代理",
                        "value_paths": [
                            "ai_providers.gpt.use_proxy",
                            "gpt_use_proxy",
                        ],
                        "default": False,
                    },
                ],
            },
        }

    def _build_provider_panel_from_spec(self, provider_key, spec):
        panel, _, form = self._build_provider_panel(spec["title"])
        field_widgets = {}

        for field in spec["fields"]:
            field_type = field["type"]
            if field_type == "secret":
                widget = self._create_secret_field(form, field)
            elif field_type == "line_edit":
                widget = self._create_line_edit_field(form, field)
            elif field_type == "checkbox":
                widget = self._create_checkbox_field(form, field)
            elif field_type == "combo":
                widget = self._create_combo_field(form, field)
            else:
                continue
            field_widgets[field["attr"]] = widget

        if not hasattr(self, "provider_field_widgets"):
            self.provider_field_widgets = {}
        self.provider_field_widgets[provider_key] = field_widgets
        return panel

    def _resolve_config_value(self, paths, default=None):
        for path in paths:
            value = self.config_manager.get(path, None)
            if value is not None:
                return value
        return default

    def _create_secret_field(self, form, field):
        line_edit = QtWidgets.QLineEdit()
        line_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        line_edit.setPlaceholderText(field.get("placeholder", ""))
        if self.use_fluent_theme:
            line_edit.setMinimumHeight(32)

        value = self._resolve_config_value(field.get("value_paths", []), field.get("default"))
        if value is not None:
            line_edit.setText(value)

        row = QtWidgets.QWidget()
        row_layout = QtWidgets.QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6 if self.use_fluent_theme else 8)
        row_layout.addWidget(line_edit)

        toggle_slot = field.get("toggle_slot")
        button = QtWidgets.QPushButton(field.get("button_text", "👁️"))
        button.setProperty("class", field.get("button_class", "secondary"))
        button.setToolTip(field.get("button_tooltip", ""))
        if toggle_slot:
            button.clicked.connect(toggle_slot)

        if self.use_fluent_theme:
            self._apply_button_style(button, "secondary", compact=True)
            button.setMinimumWidth(44)
        else:
            button.setStyleSheet("padding: 0; margin: 0;")
            button_height = max(line_edit.sizeHint().height(), 32)
            button.setFixedSize(button_height, button_height)

        row_layout.addWidget(button)

        helper_text = field.get("helper")
        self._add_form_row(form, field.get("label", ""), row, helper_text=helper_text)

        setattr(self, field["attr"], line_edit)
        button_attr = field.get("button_attr")
        if button_attr:
            setattr(self, button_attr, button)

        return line_edit

    def _create_line_edit_field(self, form, field):
        line_edit = QtWidgets.QLineEdit()
        line_edit.setPlaceholderText(field.get("placeholder", ""))
        if self.use_fluent_theme:
            line_edit.setMinimumHeight(32)
        value = self._resolve_config_value(field.get("value_paths", []), field.get("default"))
        if value is not None:
            line_edit.setText(value)

        helper_text = field.get("helper")
        self._add_form_row(form, field.get("label", ""), line_edit, helper_text=helper_text)
        setattr(self, field["attr"], line_edit)
        return line_edit

    def _create_checkbox_field(self, form, field):
        checkbox = QtWidgets.QCheckBox(field.get("text", ""))
        if self.use_fluent_theme:
            checkbox.setMinimumHeight(30)
        value = self._resolve_config_value(field.get("value_paths", []), field.get("default", False))
        checkbox.setChecked(bool(value))

        helper_text = field.get("helper")
        self._add_form_row(form, field.get("label", ""), checkbox, helper_text=helper_text)
        setattr(self, field["attr"], checkbox)
        return checkbox

    def _create_combo_field(self, form, field):
        combo = QtWidgets.QComboBox()
        raw_items = self._resolve_config_value(field.get("items_paths", []), field.get("default_items", []))
        if isinstance(raw_items, (list, tuple)):
            items = list(raw_items)
        else:
            items = list(field.get("default_items", []))
        combo.addItems(items)
        minimum_height = field.get("minimum_height", 34 if self.use_fluent_theme else 32)
        combo.setMinimumHeight(minimum_height)

        current_value = self._resolve_config_value(field.get("value_paths", []), field.get("default"))
        if current_value and current_value in items:
            combo.setCurrentText(current_value)

        helper_text = field.get("helper")
        self._add_form_row(form, field.get("label", ""), combo, helper_text=helper_text)
        setattr(self, field["attr"], combo)
        return combo

    def _create_proxy_card(self): 
        icon = getattr(FluentIcon, "GLOBE", None) if self.use_fluent_theme and FluentIcon else None
        description = "为 API 请求配置代理服务，保持网络连通。"
        card, _, form = self._build_card("🌐 网络配置", icon=icon, description=description)
        if form is None:
            return card

        self.proxy_edit = QtWidgets.QLineEdit()
        if self.use_fluent_theme:
            self.proxy_edit.setMinimumHeight(32)
        proxy_url = self.config_manager.get(
            "network.proxy",
            self.config_manager.get("proxy", "http://127.0.0.1:6789")
        )
        self.proxy_edit.setText(proxy_url)
        self.proxy_edit.setPlaceholderText("例如: http://127.0.0.1:6789")

        helper_text = "用于 Gemini/GPT 网络请求，留空则不使用代理。"
        self._add_form_row(form, "代理地址", self.proxy_edit, helper_text=helper_text)
        return card

    def _create_opacity_card(self):
        icon = getattr(FluentIcon, "LAYOUT", None) if self.use_fluent_theme and FluentIcon else None
        description = "调节截图浮窗透明度，平衡信息密度。"
        card, _, form = self._build_card("🎨 界面配置", icon=icon, description=description)
        if form is None:
            return card

        opacity_row = QtWidgets.QWidget()
        opacity_row_layout = QtWidgets.QHBoxLayout(opacity_row)
        opacity_row_layout.setContentsMargins(0, 0, 0, 0)
        opacity_row_layout.setSpacing(8 if self.use_fluent_theme else 10)

        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(50, 255)
        self.opacity_slider.setValue(self.config_manager.get("background_opacity", 120))
        self.opacity_slider.valueChanged.connect(self.update_opacity_label)
        opacity_row_layout.addWidget(self.opacity_slider)

        self.opacity_value_label = QtWidgets.QLabel(str(self.opacity_slider.value()))
        self.opacity_value_label.setFixedWidth(40)
        self.opacity_value_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        if self.use_fluent_theme:
            self.opacity_value_label.setStyleSheet(
                "font-weight: 600; color: #e0f2fe; font-size: 15px; padding: 4px 10px; "
                "background-color: rgba(94, 129, 244, 0.22); border-radius: 10px;"
            )
        else:
            self.opacity_value_label.setStyleSheet(
                "font-weight: 600;"
                " color: #38bdf8;"
                " font-size: 15px;"
                " padding: 4px 8px;"
                " background: rgba(56, 189, 248, 0.12);"
                " border: 1px solid #1f2b44;"
                " border-radius: 6px;"
            )
        opacity_row_layout.addWidget(self.opacity_value_label)

        helper_text = "范围 50-255，数值越低透明度越高。"
        self._add_form_row(form, "浮窗透明度", opacity_row, helper_text=helper_text)
        return card

    def _create_ui_card(self):
        icon = getattr(FluentIcon, "INFO", None) if self.use_fluent_theme and FluentIcon else None
        description = "切换界面中的辅助区域与日志面板显示。"
        card, _, form = self._build_card("🖥️ 界面显示设置", icon=icon, description=description)
        if form is None:
            return card

        self.show_log_checkbox = QtWidgets.QCheckBox("显示运行日志选项卡")
        if self.use_fluent_theme:
            self.show_log_checkbox.setMinimumHeight(30)
        self.show_log_checkbox.setChecked(self.config_manager.get("show_log_tab", True))
        helper_text = "关闭后可在状态栏按钮重新启用日志面板。"
        self._add_form_row(form, "运行日志", self.show_log_checkbox, helper_text=helper_text)

        # 防截屏保护
        self.capture_protection_checkbox = QtWidgets.QCheckBox("启用防截屏保护")
        if self.use_fluent_theme:
            self.capture_protection_checkbox.setMinimumHeight(30)
        
        # 连接信号
        self.capture_protection_checkbox.stateChanged.connect(self.handle_capture_protection_change)
        
        protection_helper = "防止截图软件捕获应用界面（仅Windows有效）。"
        self._add_form_row(form, "隐私保护", self.capture_protection_checkbox, helper_text=protection_helper)
        return card

    def _create_prompt_status_card(self):
        icon = getattr(FluentIcon, "DOCUMENT", None) if self.use_fluent_theme and FluentIcon else None
        description = "查看当前选用的提示词与关联热键。"
        card, layout, _ = self._build_card("📝 提示词状态", with_form=False, icon=icon, description=description)
        layout.setSpacing(12 if self.use_fluent_theme else 8)

        self.current_prompt_label = QtWidgets.QLabel()
        if self.use_fluent_theme:
            self.current_prompt_label.setStyleSheet(
                "font-size: 15px; font-weight: 600; color: #e0f2fe; padding: 10px 14px; "
                "background-color: rgba(94, 129, 244, 0.22); border-radius: 12px;"
            )
        else:
            self.current_prompt_label.setStyleSheet(
                "font-size: 15px; font-weight: 600; color: #38bdf8; padding: 8px 12px; "
                "background: rgba(56, 189, 248, 0.18); border-radius: 6px; border-left: 3px solid #38bdf8;"
            )
        self.update_current_prompt_display()
        layout.addWidget(self.current_prompt_label)

        return card

    def create_basic_tab(self):
        if self.use_fluent_theme:
            return self._create_basic_tab_fluent()
        return self._create_basic_tab_classic()

    def _create_basic_tab_fluent(self):
        if not (FluentCardColumn and create_card_scroll_area):
            return self._create_basic_tab_classic()

        column = FluentCardColumn()
        column.add_widget(self._create_provider_card())
        column.add_widget(self._create_proxy_card())
        column.add_widget(self._create_opacity_card())
        column.add_widget(self._create_ui_card())
        column.add_widget(self._create_prompt_status_card())
        column.add_stretch()

        return create_card_scroll_area(column)

    def _create_basic_tab_classic(self):
        """创建基本设置选项卡"""
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QtWidgets.QWidget()
        container.setMinimumWidth(980)
        root_layout = QtWidgets.QVBoxLayout(container)
        root_layout.setContentsMargins(14, 14, 14, 18)
        root_layout.setSpacing(16)

        provider_card = self._create_provider_card()
        root_layout.addWidget(provider_card)

        grid_container = QtWidgets.QWidget()
        grid_layout = QtWidgets.QGridLayout(grid_container)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setHorizontalSpacing(12)
        grid_layout.setVerticalSpacing(16)

        grid_layout.addWidget(self._create_proxy_card(), 0, 0)
        grid_layout.addWidget(self._create_opacity_card(), 0, 1)
        grid_layout.addWidget(self._create_ui_card(), 1, 0)
        grid_layout.addWidget(self._create_prompt_status_card(), 1, 1)

        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)

        root_layout.addWidget(grid_container)

        scroll_area.setWidget(container)
        return scroll_area
    def create_prompts_tab(self):
        """创建提示词管理选项卡"""
        return PromptManagerWidget(self.config_manager, self.log_manager)

    def create_log_tab(self):
        """创建运行日志选项卡"""
        self.log_viewer = LogViewerWidget(self.log_manager, self.use_fluent_theme)
        return self.log_viewer

    def setup_tray(self):
        """设置系统托盘"""
        self.tray_icon = QtWidgets.QSystemTrayIcon(self)

        # 创建托盘图标
        icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)

        # 创建托盘菜单
        tray_menu = QtWidgets.QMenu()

        show_action = tray_menu.addAction("显示配置")
        show_action.triggered.connect(self.show)

        tray_menu.addSeparator()

        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self.quit_app)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)

    def tray_icon_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()

    def load_settings(self):
        """从配置文件加载设置到UI"""
        self.settings_loading = True
        provider = self.config_manager.get("provider", DEFAULT_PROVIDER)
        if hasattr(self, 'provider_radios') and provider in self.provider_radios:
            self.provider_radios[provider].setChecked(True)
        self._load_provider_settings()
        self._load_additional_settings()
        self.on_provider_changed(provider)
        self.settings_loading = False

    def _load_provider_settings(self):
        provider_specs = self._provider_field_specs()
        for provider_key, spec in provider_specs.items():
            field_widgets = self.provider_field_widgets.get(provider_key, {})
            for field in spec.get("fields", []):
                widget_attr = field.get("attr")
                widget = field_widgets.get(widget_attr) or getattr(self, widget_attr, None)
                if not widget:
                    continue
                field_type = field.get("type")
                value = self._resolve_config_value(field.get("value_paths", []), field.get("default"))
                if field_type == "combo":
                    items = self._resolve_config_value(field.get("items_paths", []), field.get("default_items", []))
                    if isinstance(items, (list, tuple)):
                        widget.blockSignals(True)
                        widget.clear()
                        widget.addItems(list(items))
                        widget.blockSignals(False)
                if field_type in {"secret", "line_edit"}:
                    widget.blockSignals(True)
                    widget.setText(value or "")
                    widget.blockSignals(False)
                elif field_type == "checkbox":
                    widget.blockSignals(True)
                    widget.setChecked(bool(value))
                    widget.blockSignals(False)
                elif field_type == "combo":
                    widget.blockSignals(True)
                    if value:
                        index = widget.findText(value)
                        if index >= 0:
                            widget.setCurrentIndex(index)
                        elif widget.count() > 0:
                            widget.setCurrentIndex(0)
                    elif widget.count() > 0:
                        widget.setCurrentIndex(0)
                    widget.blockSignals(False)

    def _load_additional_settings(self):
        proxy = self.config_manager.get("network.proxy", self.config_manager.get("proxy", ""))
        self.proxy_edit.blockSignals(True)
        self.proxy_edit.setText(proxy)
        self.proxy_edit.blockSignals(False)
        opacity = self.config_manager.get("background_opacity", 120)
        self.opacity_slider.blockSignals(True)
        self.opacity_slider.setValue(opacity)
        self.opacity_slider.blockSignals(False)
        self.update_opacity_label(opacity)
        show_log = self.config_manager.get("show_log_tab", True)
        self.show_log_checkbox.blockSignals(True)
        self.show_log_checkbox.setChecked(show_log)
        self.show_log_checkbox.blockSignals(False)

        enable_protection = self.config_manager.get("enable_capture_protection", True)
        if hasattr(self, 'capture_protection_checkbox'):
            self.capture_protection_checkbox.blockSignals(True)
            self.capture_protection_checkbox.setChecked(enable_protection)
            self.capture_protection_checkbox.blockSignals(False)

    def on_provider_radio_changed(self):
        """处理单选按钮变更"""
        sender = self.sender()
        if sender.isChecked():
            provider = sender.text()
            # 自动保存提供商选择
            self.config_manager.set("provider", provider)
            self.log_manager.add_log(f"✅ AI服务商已切换为: {provider}")
            self.on_provider_changed(provider)
            self.handle_settings_change()

    # 注意：toggle_provider方法已移动到handle_toggle_provider，使用信号机制

    def on_provider_changed(self, provider: str):
        """处理提供商变更"""
        if hasattr(self, "provider_stack"):
            target_widget = self.provider_widget_map.get(provider, self.gemini_group)
            self.provider_stack.setCurrentWidget(target_widget)
    def toggle_gemini_api_visibility(self):
        """切换 Gemini API Key 显示/隐藏"""
        if self.gemini_api_key_edit.echoMode() == QtWidgets.QLineEdit.EchoMode.Password:
            self.gemini_api_key_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Normal)
            self.show_gemini_api_btn.setText("🙈")
        else:
            self.gemini_api_key_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            self.show_gemini_api_btn.setText("👁️")

    def toggle_gpt_api_visibility(self):
        """切换 GPT API Key 显示/隐藏"""
        if self.gpt_api_key_edit.echoMode() == QtWidgets.QLineEdit.EchoMode.Password:
            self.gpt_api_key_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Normal)
            self.show_gpt_api_btn.setText("🙈")
        else:
            self.gpt_api_key_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            self.show_gpt_api_btn.setText("👁️")

    def update_opacity_label(self, value):
        """更新透明度显示标签"""
        self.opacity_value_label.setText(str(value))
        if self.overlay:
            self.config_manager.config["background_opacity"] = value
            self.overlay.update_background_opacity()

    def handle_capture_protection_change(self, state):
        """处理防截屏保护状态变更"""
        enabled = (state == 2) # Qt.CheckState.Checked
        self.config_manager.set("enable_capture_protection", enabled)
        self.log_manager.add_log(f"防截屏保护已{'启用' if enabled else '禁用'}")
        
        if self.overlay:
            # 尝试动态更新保护状态
            if hasattr(self.overlay, 'update_capture_protection'):
                self.overlay.update_capture_protection()
            else:
                # 如果没有update方法，可能需要重新应用保护
                # 这里假设overlay有_apply_screen_capture_protection方法
                if hasattr(self.overlay, '_apply_screen_capture_protection'):
                    self.overlay._apply_screen_capture_protection()

    def _read_basic_settings(self):
        """收集界面上的基础配置值"""
        provider = None
        for provider_name, radio in self.provider_radios.items():
            if radio.isChecked():
                provider = provider_name
                break

        settings = {
            "provider": provider,
            "proxy": self.proxy_edit.text().strip(),
            "background_opacity": self.opacity_slider.value(),
            "show_log_tab": self.show_log_checkbox.isChecked(),
            "enable_capture_protection": self.capture_protection_checkbox.isChecked(),
            "gemini": {
                "api_key": self.gemini_api_key_edit.text().strip(),
                "base_url": self.gemini_base_url_edit.text().strip(),
                "use_proxy": self.gemini_use_proxy_check.isChecked(),
                "model": self.gemini_model_combo.currentText(),
            },
            "gpt": {
                "api_key": self.gpt_api_key_edit.text().strip(),
                "base_url": self.gpt_base_url_edit.text().strip(),
                "use_proxy": self.gpt_use_proxy_check.isChecked(),
                "model": self.gpt_model_combo.currentText(),
            },
        }
        return settings

    def _validate_basic_settings(self, settings):
        """校验基础配置，返回 (是否通过, 提示标题, 提示内容)"""
        provider = settings.get("provider")
        if not provider:
            return False, "选择错误", "请选择一个AI服务商"

        gemini = settings["gemini"]
        gpt = settings["gpt"]

        if provider == "Gemini":
            if not gemini["api_key"]:
                return False, "输入错误", "请输入 Gemini API Key"
            if not gemini["base_url"]:
                return False, "输入错误", "请输入 Gemini Base URL"
        elif provider == "GPT":
            if not gpt["api_key"]:
                return False, "输入错误", "请输入 GPT API Key"
            if not gpt["base_url"]:
                return False, "输入错误", "请输入 GPT Base URL"

        proxy = settings.get("proxy", "")
        if proxy:
            valid, error = NetworkUtils.validate_proxy_url(proxy)
            if not valid:
                return False, "代理设置错误", error

        return True, None, None

    def _apply_basic_settings(self, settings):
        """将配置写入 ConfigManager"""
        self.config_manager.set("provider", settings["provider"])
        self.config_manager.set("proxy", settings["proxy"])
        self.config_manager.set("background_opacity", settings["background_opacity"])
        self.config_manager.set("show_log_tab", settings["show_log_tab"])
        self.config_manager.set("enable_capture_protection", settings["enable_capture_protection"])

        gemini = settings["gemini"]
        self.config_manager.set("api_key", gemini["api_key"])
        self.config_manager.set("ai_providers.gemini.api_key", gemini["api_key"])
        self.config_manager.set("gemini_base_url", gemini["base_url"])
        self.config_manager.set("ai_providers.gemini.base_url", gemini["base_url"])
        self.config_manager.set("gemini_use_proxy", gemini["use_proxy"])
        self.config_manager.set("ai_providers.gemini.use_proxy", gemini["use_proxy"])
        self.config_manager.set("gemini_model", gemini["model"])
        self.config_manager.set("model", gemini["model"])

        gpt = settings["gpt"]
        self.config_manager.set("gpt_api_key", gpt["api_key"])
        self.config_manager.set("ai_providers.gpt.api_key", gpt["api_key"])
        self.config_manager.set("gpt_base_url", gpt["base_url"])
        self.config_manager.set("ai_providers.gpt.base_url", gpt["base_url"])
        self.config_manager.set("gpt_model", gpt["model"])
        self.config_manager.set("ai_providers.gpt.model", gpt["model"])
        self.config_manager.set("gpt_use_proxy", gpt["use_proxy"])
        self.config_manager.set("ai_providers.gpt.use_proxy", gpt["use_proxy"])

        if self.overlay:
            self.overlay.update_background_opacity()

    def setup_settings_autosave(self):
        """绑定自动保存信号"""
        self.gemini_api_key_edit.editingFinished.connect(self.handle_settings_change)
        self.gemini_base_url_edit.editingFinished.connect(self.handle_settings_change)
        self.gemini_use_proxy_check.toggled.connect(lambda _: self.handle_settings_change())
        self.gemini_model_combo.currentIndexChanged.connect(lambda _: self.handle_settings_change())

        self.gpt_api_key_edit.editingFinished.connect(self.handle_settings_change)
        self.gpt_base_url_edit.editingFinished.connect(self.handle_settings_change)
        self.gpt_use_proxy_check.toggled.connect(lambda _: self.handle_settings_change())
        self.gpt_model_combo.currentIndexChanged.connect(lambda _: self.handle_settings_change())

        self.proxy_edit.editingFinished.connect(self.handle_settings_change)
        self.show_log_checkbox.toggled.connect(lambda _: self.handle_settings_change())
        self.opacity_slider.sliderReleased.connect(self.handle_settings_change)
        self.capture_protection_checkbox.toggled.connect(self.handle_capture_protection_change)

    def handle_capture_protection_change(self, checked):
        """处理防截屏保护开关变更"""
        if getattr(self, 'settings_loading', False):
            return
        # 保存设置
        self.config_manager.set("enable_capture_protection", checked)
        # 动态更新浮窗保护状态
        if self.overlay:
            self.overlay.update_capture_protection()
        self.log_manager.add_log(f"防截屏保护已{'启用' if checked else '关闭'}")

    def handle_settings_change(self):
        """字段变更时处理自动保存"""
        if getattr(self, 'settings_loading', False):
            return
        self.save_basic_settings(strict_validation=False, show_message=False)

    def save_basic_settings(self, *, strict_validation: bool = True, show_message: bool = False):
        """保存基本设置"""
        settings = self._read_basic_settings()

        if not settings["provider"]:
            if strict_validation:
                QtWidgets.QMessageBox.warning(self, "选择错误", "请选择一个AI服务商")
            return

        is_valid, title, message = self._validate_basic_settings(settings)
        if not is_valid:
            if strict_validation and title and message:
                QtWidgets.QMessageBox.warning(self, title, message)
            return

        self._apply_basic_settings(settings)

        if show_message:
            provider = settings["provider"]
            self.log_manager.add_log(f"基本设置已保存 (提供商: {provider})")
            QtWidgets.QMessageBox.information(self, "成功", f"基本设置已保存\n当前提供商: {provider}")

    def update_current_prompt_display(self):
        """更新当前提示词显示"""
        try:
            prompts = self.config_manager.get("prompts", [])
            if not prompts:
                if hasattr(self, 'current_prompt_label'):
                    self.current_prompt_label.setText("❌ 未配置提示词")
                return

            if 0 <= self.current_prompt_index < len(prompts):
                prompt = prompts[self.current_prompt_index]
                prompt_name = prompt.get('name', f'提示词{self.current_prompt_index+1}')
                display_text = f"🎯 当前提示词 {self.current_prompt_index+1}: {prompt_name}"
            else:
                # 索引超出范围，重置为第一个
                self.current_prompt_index = 0
                prompt = prompts[0] if prompts else None
                if prompt:
                    prompt_name = prompt.get('name', '提示词1')
                    display_text = f"🎯 当前提示词 1: {prompt_name}"
                else:
                    display_text = "❌ 未配置提示词"

            if hasattr(self, 'current_prompt_label'):
                self.current_prompt_label.setText(display_text)

        except Exception as e:
            self.log_manager.add_log(f"更新提示词显示失败: {e}", "ERROR")
            if hasattr(self, 'current_prompt_label'):
                self.current_prompt_label.setText("❌ 显示错误")

    def update_status(self, status, color=STATUS_COLORS["stopped"]):
        """更新状态显示"""
        # 新版现代化UI
        if self.use_fluent_theme and hasattr(self, 'main_layout') and self.main_layout:
            running = "运行中" in status
            self.main_layout.update_status(status, running)
            return

        # 旧版Fluent UI
        if self.use_fluent_theme and self.status_bar:
            self.status_bar.update_status(status, color=color)

        if not self.status_label:
            return

        if "运行中" in status:
            icon = "🟢"
            bg_color = "rgba(72, 187, 120, 0.1)"
            border_color = "#48bb78"
        elif "错误" in status or "失败" in status:
            icon = "🔴"
            bg_color = "rgba(245, 101, 101, 0.1)"
            border_color = "#f56565"
        else:
            icon = "⚫"
            bg_color = "rgba(113, 128, 150, 0.1)"
            border_color = "#718096"

        css = (
            f"color: {color};"
            " font-weight: 600;"
            " font-size: 15px;"
            " padding: 8px 12px;"
            f" background: {bg_color};"
            " border-radius: 6px;"
            f" border-left: 3px solid {border_color};"
        )
        self.status_label.setText(f"{icon} {status}")
        self.status_label.setStyleSheet(css)

    def open_logs_directory(self) -> None:
        """打开日志目录"""
        log_dir = os.path.join(os.path.expanduser("~"), LOG_DIR_NAME, LOG_SUBDIR)
        try:
            os.makedirs(log_dir, exist_ok=True)
        except OSError:
            pass
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(log_dir))
    def start_listening(self):
        """启动快捷键监听"""
        try:
            # 创建浮窗
            if not self.overlay:
                try:
                    self.overlay = Overlay(self.config_manager)
                except Exception as overlay_error:
                    self.log_manager.add_log(f"浮窗创建失败: {overlay_error}", "ERROR")
                    # 尝试继续运行，但记录警告
                    self.overlay = None

            # 停止旧的监听
            self.stop_listening()

            # 绑定热键
            self.setup_hotkeys()

            # 启动键盘监听
            if self.hotkey_handler.start_listening():
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                self.update_status("运行中", STATUS_COLORS["running"])
                self.log_manager.add_log("快捷键监听已启动")

                # 如果浮窗创建失败，给出警告
                if not self.overlay:
                    self.log_manager.add_log("警告：浮窗未能创建，部分功能可能不可用", "WARNING")

                # 最小化到托盘
                self.hide()
                self.tray_icon.show()
                self.tray_icon.showMessage(
                    "AI 截图助手",
                    "已启动并最小化到托盘",
                    QtWidgets.QSystemTrayIcon.MessageIcon.Information,
                    500
                )
            else:
                raise Exception("启动键盘监听失败")

        except Exception as e:
            self.update_status("启动失败", STATUS_COLORS["error"])
            self.log_manager.add_log(f"启动监听失败: {e}", "ERROR")
            QtWidgets.QMessageBox.critical(self, "错误", f"启动失败: {e}")

    def setup_hotkeys(self):
        """设置热键"""
        control_hotkeys = self.config_manager.get("hotkeys", {})

        # 绑定提示词发送快捷键 (alt+z 发送当前选中的提示词)
        send_prompt_key = control_hotkeys.get("send_prompt", "alt+z")
        send_prompt_handler = lambda: threading.Thread(
            target=self.send_current_prompt, daemon=True
        ).start()

        if self.hotkey_handler.register_hotkey(send_prompt_key, send_prompt_handler):
            self.log_manager.add_log(f"绑定提示词发送快捷键: {send_prompt_key}")

        # 绑定每个提示词的快捷键（按快捷键直接发送对应提示词）
        prompts = self.config_manager.get("prompts", [])
        for i, prompt in enumerate(prompts):
            hotkey_str = prompt.get('hotkey', '')
            if not hotkey_str:
                continue

            # 创建处理函数，直接发送该提示词
            def make_handler(prompt_index):
                return lambda: threading.Thread(
                    target=lambda: self.send_prompt_by_index(prompt_index),
                    daemon=True
                ).start()

            handler = make_handler(i)
            prompt_name = prompt.get('name', f'提示词{i+1}')

            if self.hotkey_handler.register_hotkey(hotkey_str, handler):
                self.log_manager.add_log(f"绑定提示词: {hotkey_str} -> {prompt_name}")

        # 绑定控制快捷键

        # 浮窗切换 - 使用信号确保线程安全
        toggle_key = control_hotkeys.get("toggle", "alt+q")
        toggle_handler = lambda: self.toggle_overlay_signal.emit()

        if self.hotkey_handler.register_hotkey(toggle_key, toggle_handler):
            self.log_manager.add_log(f"绑定浮窗切换快捷键: {toggle_key}")

        # 纯截图
        screenshot_key = control_hotkeys.get("screenshot_only", "alt+w")
        screenshot_handler = lambda: threading.Thread(
            target=self.capture_screenshot_only, daemon=True
        ).start()
        if self.hotkey_handler.register_hotkey(screenshot_key, screenshot_handler):
            self.log_manager.add_log(f"绑定纯截图快捷键: {screenshot_key}")

        # 清空截图历史
        clear_key = control_hotkeys.get("clear_screenshots", "alt+v")
        clear_handler = lambda: threading.Thread(
            target=self.clear_screenshot_history, daemon=True
        ).start()
        if self.hotkey_handler.register_hotkey(clear_key, clear_handler):
            self.log_manager.add_log(f"绑定清空截图快捷键: {clear_key}")

        # 滚动快捷键
        scroll_up_key = control_hotkeys.get("scroll_up", "alt+up")
        scroll_down_key = control_hotkeys.get("scroll_down", "alt+down")

        def safe_scroll_up():
            try:
                if self.overlay:
                    self.overlay.scroll_up()
            except Exception as e:
                self.log_manager.add_log(f"滚动失败: {e}", "WARNING")

        def safe_scroll_down():
            try:
                if self.overlay:
                    self.overlay.scroll_down()
            except Exception as e:
                self.log_manager.add_log(f"滚动失败: {e}", "WARNING")

        if self.hotkey_handler.register_hotkey(scroll_up_key, safe_scroll_up):
            self.log_manager.add_log(f"绑定向上滚动快捷键: {scroll_up_key}")

        if self.hotkey_handler.register_hotkey(scroll_down_key, safe_scroll_down):
            self.log_manager.add_log(f"绑定向下滚动快捷键: {scroll_down_key}")

        # 切换服务商快捷键 - 使用信号确保线程安全
        switch_provider_key = "alt+s"
        switch_provider_handler = lambda: self.toggle_provider_signal.emit()
        if self.hotkey_handler.register_hotkey(switch_provider_key, switch_provider_handler):
            self.log_manager.add_log(f"绑定切换服务商快捷键: {switch_provider_key}")

    def stop_listening(self):
        """停止快捷键监听"""
        try:
            self.hotkey_handler.stop_listening()

            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.update_status("已停止", STATUS_COLORS["stopped"])

            self.log_manager.add_log("快捷键监听已停止")

        except Exception as e:
            self.log_manager.add_log(f"停止监听失败: {e}", "ERROR")

    def capture_screenshot_only(self):
        """仅截图保存到历史记录"""
        try:
            # 使用智能截图选择器
            if SCREENSHOT_MODE.get("use_selector", True):
                self.pending_prompt = None  # 标记为纯截图
                # 发送信号到主线程
                self.trigger_screenshot_signal.emit(False)
                return
            else:
                # 传统截图
                png = capture_screen()
                self.save_screenshot_to_history(png)

        except Exception as e:
            self.log_manager.add_log(f"截图保存失败: {e}", "ERROR")

    def handle_screenshot_in_main_thread(self, with_prompt: bool):
        """在主线程中处理截图（避免线程问题）"""
        if with_prompt:
            self.start_smart_screenshot()
        else:
            self.start_smart_screenshot_only()

    def handle_toggle_overlay(self):
        """在主线程中处理overlay切换"""
        if self.overlay:
            self.overlay.toggle()
        else:
            self.log_manager.add_log("浮窗尚未初始化", "WARNING")

    def handle_toggle_provider(self):
        """在主线程中处理AI服务商切换"""
        try:
            current_provider = self.config_manager.get("provider", "Gemini")

            # 切换到另一个服务商
            if current_provider == "Gemini":
                new_provider = "GPT"
            else:
                new_provider = "Gemini"

            # 保存新的配置
            self.config_manager.set("provider", new_provider)

            # 更新UI（如果有的话）
            if hasattr(self, 'provider_radios') and new_provider in self.provider_radios:
                self.provider_radios[new_provider].setChecked(True)

            # 显示Toast提示
            try:
                Toast.show_message(f"🤖 已切换到 {new_provider}", 1500)
            except Exception as toast_error:
                self.log_manager.add_log(f"Toast显示失败: {toast_error}", "WARNING")

            # 记录日志
            self.log_manager.add_log(f"🔄 通过热键切换到 {new_provider}")

        except Exception as e:
            self.log_manager.add_log(f"切换服务商失败: {e}", "ERROR")

    def switch_prompt(self, index: int):
        """切换到指定索引的提示词"""
        try:
            prompts = self.config_manager.get("prompts", [])
            if 0 <= index < len(prompts):
                self.current_prompt_index = index
                self.config_manager.set("current_prompt_index", index)

                prompt_name = prompts[index].get('name', f'提示词{index+1}')
                self.log_manager.add_log(f"🔄 切换到提示词 {index+1}: {prompt_name}")

                # 更新UI显示
                self.update_current_prompt_display()

                # 显示Toast提示
                try:
                    Toast.show_message(f"📝 提示词 {index+1}: {prompt_name}", 1500)
                except Exception as toast_error:
                    self.log_manager.add_log(f"Toast显示失败: {toast_error}", "WARNING")
            else:
                self.log_manager.add_log(f"⚠️ 提示词索引 {index+1} 超出范围", "WARNING")

        except Exception as e:
            self.log_manager.add_log(f"切换提示词失败: {e}", "ERROR")

    def send_current_prompt(self):
        """发送当前选中的提示词"""
        try:
            prompts = self.config_manager.get("prompts", [])
            if not prompts:
                self.log_manager.add_log("⚠️ 没有配置的提示词", "WARNING")
                return

            if 0 <= self.current_prompt_index < len(prompts):
                current_prompt = prompts[self.current_prompt_index]
                prompt_name = current_prompt.get('name', f'提示词{self.current_prompt_index+1}')

                self.log_manager.add_log(f"📤 发送提示词 {self.current_prompt_index+1}: {prompt_name}")
                self.trigger_prompt(current_prompt)
            else:
                # 索引超出范围，重置为第一个提示词
                self.current_prompt_index = 0
                self.config_manager.set("current_prompt_index", 0)

                current_prompt = prompts[0]
                prompt_name = current_prompt.get('name', '提示词1')

                self.log_manager.add_log(f"⚠️ 提示词索引重置，发送提示词1: {prompt_name}")
                self.trigger_prompt(current_prompt)

        except Exception as e:
            self.log_manager.add_log(f"发送提示词失败: {e}", "ERROR")

    def send_prompt_by_index(self, index: int):
        """通过索引发送指定的提示词（由快捷键直接触发）"""
        try:
            prompts = self.config_manager.get("prompts", [])
            if not prompts:
                self.log_manager.add_log("没有配置的提示词", "WARNING")
                return

            if 0 <= index < len(prompts):
                prompt = prompts[index]
                prompt_name = prompt.get('name', f'提示词{index+1}')
                hotkey = prompt.get('hotkey', '')

                self.log_manager.add_log(f"快捷键 {hotkey} -> 发送提示词: {prompt_name}")
                self.trigger_prompt(prompt)

                # 同时更新当前选中索引
                self.current_prompt_index = index
                self.config_manager.set("current_prompt_index", index)
            else:
                self.log_manager.add_log(f"提示词索引 {index} 超出范围", "WARNING")

        except Exception as e:
            self.log_manager.add_log(f"发送提示词失败: {e}", "ERROR")

    def handle_api_response(self, response: str):
        """在主线程中处理API响应"""
        try:
            # 检查overlay是否存在
            if not self.overlay:
                self.log_manager.add_log("浮窗未初始化，无法显示响应", "WARNING")
                return

            # 检查是否为错误消息
            if response.startswith("错误:"):
                self.log_manager.add_log(response, "ERROR")
                self.overlay.handle_response(f"<p style='color: red;'>{response}</p>")
                return

            self.log_manager.add_log(f"API响应处理开始，内容长度: {len(response)}")

            # 提取代码块并复制到剪贴板
            code_blocks = extract_code_blocks(response)
            if code_blocks:
                # 记录复制前的剪切板内容哈希值（避免重复复制）
                import hashlib
                content_hash = hashlib.md5(code_blocks.encode()).hexdigest()[:8]

                if copy_to_clipboard(code_blocks):
                    self.log_manager.add_log(f"✅ 代码已复制到剪贴板 ({len(code_blocks)} 字符, ID:{content_hash})")
                else:
                    self.log_manager.add_log("❌ 复制到剪贴板失败", "WARNING")
            else:
                self.log_manager.add_log("⚠️ 响应中未找到代码块")
                # 显示响应的前200字符用于调试
                preview = response[:200] + "..." if response and len(response) > 200 else response
                self.log_manager.add_log(f"响应预览: {preview}")

            # 渲染markdown为HTML并显示
            from markdown_it import MarkdownIt
            html = MarkdownIt("commonmark", {"html": True}).render(response)
            self.overlay.handle_response(html)
            self.log_manager.add_log("API 响应已显示在浮窗")

        except Exception as e:
            error_msg = f"处理API响应失败: {str(e)}"
            self.log_manager.add_log(error_msg, "ERROR")
            if self.overlay:
                self.overlay.handle_response(f"<p style='color: red;'>{error_msg}</p>")

    def clear_screenshot_history(self):
        """清空截图历史记录"""
        try:
            if not self.screenshot_history:
                self.log_manager.add_log("截图历史记录为空，无需清理")
                return

            # 计算释放的内存
            total_size_mb = sum(len(img) for img in self.screenshot_history) / (1024 * 1024)
            count = len(self.screenshot_history)

            # 释放内存
            for img in self.screenshot_history:
                del img
            self.screenshot_history.clear()
            gc.collect()

            self.log_manager.add_log(
                f"已清空 {count} 张截图，释放约 {total_size_mb:.1f} MB 内存"
            )

        except Exception as e:
            self.log_manager.add_log(f"清空截图历史失败: {e}", "ERROR")

    def start_smart_screenshot(self):
        """启动智能截图选择器"""
        try:
            # 创建截图选择器（传入配置管理器以支持防截屏开关）
            self.screenshot_selector = ScreenshotSelector(self.config_manager)

            # 连接信号
            self.screenshot_selector.screenshot_taken.connect(self.on_screenshot_taken)
            self.screenshot_selector.screenshot_cancelled.connect(self.on_screenshot_cancelled)

            # 启动截图
            self.screenshot_selector.start_capture()

        except Exception as e:
            self.log_manager.add_log(f"启动智能截图失败: {e}", "ERROR")
            # 回退到传统截图
            if self.pending_prompt:
                self.process_prompt_with_screenshot(capture_screen(), self.pending_prompt)

    def on_screenshot_taken(self, png_data: bytes):
        """截图完成回调"""
        self.log_manager.add_log("智能截图完成")

        # 关闭截图选择器
        if self.screenshot_selector:
            self.screenshot_selector.close()
            self.screenshot_selector = None

        if self.pending_prompt:
            self.process_prompt_with_screenshot(png_data, self.pending_prompt)
            self.pending_prompt = None

    def on_screenshot_cancelled(self):
        """截图取消回调"""
        self.log_manager.add_log("截图已取消")

        # 关闭截图选择器
        if self.screenshot_selector:
            self.screenshot_selector.close()
            self.screenshot_selector = None

        self.pending_prompt = None

    def start_smart_screenshot_only(self):
        """启动智能截图（仅保存）"""
        try:
            self.screenshot_selector = ScreenshotSelector(self.config_manager)
            self.screenshot_selector.screenshot_taken.connect(self.on_screenshot_only_taken)
            self.screenshot_selector.screenshot_cancelled.connect(self.on_screenshot_cancelled)
            self.screenshot_selector.start_capture()
        except Exception as e:
            self.log_manager.add_log(f"启动智能截图失败: {e}", "ERROR")
            # 回退到传统截图
            self.save_screenshot_to_history(capture_screen())

    def on_screenshot_only_taken(self, png_data: bytes):
        """纯截图完成回调"""
        self.log_manager.add_log("智能截图完成（仅保存）")

        # 关闭截图选择器
        if self.screenshot_selector:
            self.screenshot_selector.close()
            self.screenshot_selector = None

        self.save_screenshot_to_history(png_data)

    def save_screenshot_to_history(self, png: bytes):
        """保存截图到历史记录"""
        try:
            # 实施LRU策略，限制历史截图数量
            if len(self.screenshot_history) >= MAX_SCREENSHOT_HISTORY:
                removed = self.screenshot_history.pop(0)
                del removed
                self.log_manager.add_log(
                    f"已达到最大截图数量限制({MAX_SCREENSHOT_HISTORY})，移除最旧的截图"
                )

            self.screenshot_history.append(png)

            # 计算当前内存占用
            total_size_mb = sum(len(img) for img in self.screenshot_history) / (1024 * 1024)
            self.log_manager.add_log(
                f"截图已保存到历史记录 (共 {len(self.screenshot_history)} 张, "
                f"约 {total_size_mb:.1f} MB)"
            )
        except Exception as e:
            self.log_manager.add_log(f"截图保存失败: {e}", "ERROR")

    def process_prompt_with_screenshot(self, current_png: bytes, prompt: dict):
        """使用截图处理提示词 - 异步版本"""
        try:
            # 准备所有图片
            self.log_manager.add_log(f"历史截图数量: {len(self.screenshot_history)}")
            self.log_manager.add_log(f"当前截图大小: {len(current_png)} bytes")

            all_images = self.screenshot_history + [current_png]

            # 根据配置选择API提供商
            provider = self.config_manager.get("provider", "Gemini")
            self.log_manager.add_log(f"🤖 使用提供商: {provider}")

            total_size_mb = sum(len(img) for img in all_images) / (1024 * 1024)
            self.log_manager.add_log(
                f"准备发送 {len(all_images)} 张图片到 {provider} "
                f"(总大小: {total_size_mb:.1f} MB)"
            )

            # 创建异步线程处理API请求
            self._start_async_api_request(all_images, prompt, provider)

        except Exception as e:
            self.log_manager.add_log(f"处理提示词失败: {str(e)}", "ERROR")
            if self.overlay:
                self.overlay.handle_response(f"错误: {str(e)}")

    def _start_async_api_request(self, all_images: list, prompt: dict, provider: str):
        """启动异步API请求"""
        # 在后台线程中执行API调用
        thread = threading.Thread(
            target=self._async_api_worker,
            args=(all_images, prompt, provider),
            daemon=True
        )
        thread.start()

    def _async_api_worker(self, all_images: list, prompt: dict, provider: str):
        """异步API工作线程"""
        try:
            # 使用工厂获取 AI 服务
            service = self.ai_factory.get_service(provider)
            if not service:
                raise Exception(f"无法获取 {provider} 服务")

            # 统一调用接口
            prompt_content = prompt.get('content', '') if isinstance(prompt, dict) else str(prompt)
            if not prompt_content:
                raise Exception("提示词内容为空")

            md = service.analyze_images(all_images, prompt_content)

            # 通过信号发送结果到主线程（确保信号连接有效）
            if md:
                try:
                    self.api_response_signal.emit(md)
                except RuntimeError:
                    # 信号可能在窗口关闭后失效
                    self.log_manager.add_log("窗口已关闭，无法显示响应", "WARNING")
            else:
                try:
                    self.api_response_signal.emit("API调用失败，未获得响应")
                except RuntimeError:
                    pass

        except Exception as e:
            # 发送错误信息到主线程
            error_msg = f"API调用异常: {str(e)}"
            try:
                self.log_manager.add_log(error_msg, "ERROR")
            except Exception:
                pass  # 日志管理器可能也已失效

            try:
                self.api_response_signal.emit(f"错误: {error_msg}")
            except RuntimeError:
                pass  # 信号可能在窗口关闭后失效

        finally:
            # 清理资源（通过信号在主线程中执行）
            try:
                QtCore.QTimer.singleShot(0, self._cleanup_screenshot_history)
            except RuntimeError:
                # 应用可能已退出
                pass

    def _cleanup_screenshot_history(self):
        """清理截图历史记录（在主线程中执行）"""
        try:
            if not self.screenshot_history:
                return

            # 计算释放的内存
            total_size_mb = sum(len(img) for img in self.screenshot_history) / (1024 * 1024)
            count = len(self.screenshot_history)

            # 清空历史截图，释放内存
            for img in self.screenshot_history:
                del img
            self.screenshot_history.clear()
            gc.collect()
            self.log_manager.add_log(f"历史截图已清空({count}张, {total_size_mb:.1f}MB)，内存已释放")

        except Exception as e:
            self.log_manager.add_log(f"清理截图历史失败: {e}", "WARNING")

    def _handle_streaming_response(self, response_stream):
        """处理流式响应"""
        full_response = ""
        try:
            if not self.overlay:
                self.log_manager.add_log("浮窗未初始化，无法处理流式响应", "WARNING")
                return

            # 启动流式渲染
            self.overlay.start_streaming()
            self.log_manager.add_log("开始流式响应处理")

            chunk_count = 0

            for chunk_text, is_complete in response_stream:
                chunk_count += 1
                self.log_manager.add_log(f"收到chunk #{chunk_count}, 完成状态: {is_complete}")

                if is_complete:
                    # 流式响应完成
                    self.log_manager.add_log(f"流式响应完成，总长度: {len(full_response)}字符")
                    if self.overlay:
                        self.overlay.finish_streaming()
                    self._process_complete_response(full_response)
                    break
                else:
                    # 追加内容块
                    full_response += chunk_text
                    self.log_manager.add_log(f"追加内容: {chunk_text[:50]}...")
                    if self.overlay:
                        self.overlay.content_chunk.emit(chunk_text)

        except Exception as e:
            if self.overlay:
                self.overlay.finish_streaming()
            self.log_manager.add_log(f"流式响应处理失败: {e}", "ERROR")
            # 回退到传统渲染
            if full_response and self.overlay:
                try:
                    from markdown_it import MarkdownIt
                    html = MarkdownIt("commonmark", {"html": True}).render(full_response)
                    self.overlay.handle_response(html)
                except Exception:
                    pass

    def _process_complete_response(self, md_content: str):
        """处理完整响应（流式响应专用） - 注意：不再复制代码，避免重复"""
        try:
            self.log_manager.add_log(f"流式响应完成，内容长度: {len(md_content)} 字符")
            # 流式响应的代码复制已在主流程中处理，这里不再重复
        except Exception as e:
            self.log_manager.add_log(f"处理完整响应失败: {e}", "ERROR")

    def trigger_prompt(self, prompt):
        """触发提示词处理"""
        try:
            self.log_manager.add_log(f"触发提示词: {prompt['name']}")

            # 使用智能截图选择器
            if SCREENSHOT_MODE.get("use_selector", True):
                self.pending_prompt = prompt
                # 发送信号到主线程
                self.trigger_screenshot_signal.emit(True)
                return  # 等待截图完成后继续
            else:
                # 使用传统截图方式
                current_png = capture_screen()
                self.log_manager.add_log("当前截屏完成")
                self.process_prompt_with_screenshot(current_png, prompt)

        except Exception as e:
            self.log_manager.add_log(f"处理提示词失败: {e}", "ERROR")

    def closeEvent(self, event):
        """关闭事件处理"""
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            self.quit_app()

    def quit_app(self):
        """退出应用"""
        self.stop_listening()

        # 释放单实例锁
        if self.single_instance:
            self.single_instance.release_lock()

        if self.overlay:
            self.overlay.close()
        self.tray_icon.hide()
        QtWidgets.QApplication.quit()


# ──────────────────────── 主程序入口 ──────────────────────── #
def main():
    """主程序入口"""
    # 启用高DPI支持 (PyQt6自动支持高DPI，但可以设置一些选项)
    try:
        # PyQt6 会自动处理高DPI，这里设置舍入策略
        QtWidgets.QApplication.setHighDpiScaleFactorRoundingPolicy(
            QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except:
        pass  # 某些版本可能不支持

    # 创建单实例管理器
    single_instance = SingleInstance()

    # 检查是否已有实例在运行
    if single_instance.is_already_running():
        temp_app = QtWidgets.QApplication(sys.argv)
        QtWidgets.QMessageBox.warning(
            None,
            "程序已运行",
            "AI 截图助手已经在运行中！\n\n请检查系统托盘或任务管理器。",
            QtWidgets.QMessageBox.StandardButton.Ok
        )
        sys.exit(0)

    # 获取单实例锁
    if not single_instance.acquire_lock():
        temp_app = QtWidgets.QApplication(sys.argv)
        QtWidgets.QMessageBox.critical(
            None,
            "启动失败",
            "无法获取程序锁，启动失败！",
            QtWidgets.QMessageBox.StandardButton.Ok
        )
        sys.exit(1)

    app = QtWidgets.QApplication(sys.argv)

    # 检查系统托盘支持
    if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
        QtWidgets.QMessageBox.critical(None, "系统托盘", "系统不支持托盘功能")
        single_instance.release_lock()
        sys.exit(1)

    # 创建配置管理器和日志管理器
    config_manager = ConfigManager()
    log_manager = LogManager()

    # 创建并显示主窗口
    main_window = AIAssistantApp(config_manager, log_manager, single_instance)
    main_window.show()

    try:
        sys.exit(app.exec())
    finally:
        # 确保释放锁
        single_instance.release_lock()


if __name__ == "__main__":
    main()























