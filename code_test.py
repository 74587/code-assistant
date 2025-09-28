#!/usr/bin/env python
"""
Gemini Screenshot Assistant - 重构版本
使用模块化架构的AI截图分析工具
"""

import sys
import os
import threading
import gc
from PyQt6 import QtCore, QtGui, QtWidgets

# 导入模块化组件
from gemini_assistant.core.single_instance import SingleInstance
from gemini_assistant.core.config_manager import ConfigManager
from gemini_assistant.core.log_manager import LogManager
from gemini_assistant.services.gemini_api import GeminiAPI
from gemini_assistant.services.gpt_api import GPTAPI
from gemini_assistant.services.network_utils import NetworkUtils
from gemini_assistant.utils.screenshot import capture_screen, extract_code_blocks, copy_to_clipboard
from gemini_assistant.utils.hotkey_handler import HotkeyHandler
from gemini_assistant.utils.constants import *
from gemini_assistant.ui.styles import AppStyles
from gemini_assistant.ui.toast import Toast

# ──────────────────────── UI组件 ──────────────────────── #
from gemini_assistant.ui.overlay import Overlay
from gemini_assistant.ui.prompt_manager import PromptManagerWidget
from gemini_assistant.ui.screenshot_selector import ScreenshotSelector

# ──────────────────────── 主应用程序 ──────────────────────── #
class GeminiAssistantApp(QtWidgets.QMainWindow):
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
        self.gemini_api = GeminiAPI(config_manager, log_manager)
        self.gpt_api = GPTAPI(config_manager, log_manager)
        self.hotkey_handler = HotkeyHandler()
        self.screenshot_history = []
        self.screenshot_selector = None  # 截图选择器实例
        self.pending_prompt = None  # 待处理的提示词
        self.current_prompt_index = self.config_manager.get("current_prompt_index", 0)  # 当前选中的提示词索引

        self.setWindowTitle(f"Gemini 截图助手 v{APP_VERSION} - 配置")
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
        self.setStyleSheet(AppStyles.get_main_window_style())

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 创建选项卡
        tab_widget = QtWidgets.QTabWidget()
        tab_widget.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

        # 基本设置选项卡
        basic_tab = self.create_basic_tab()
        basic_tab.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        tab_widget.addTab(basic_tab, "⚙️ 基本设置")

        # 提示词管理选项卡
        prompts_tab = self.create_prompts_tab()
        prompts_tab.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        tab_widget.addTab(prompts_tab, "💬 提示词管理")

        # 运行日志选项卡（根据配置决定是否显示）
        show_log_tab = self.config_manager.get("show_log_tab", True)
        if show_log_tab:
            logs_tab = self.create_log_tab()
            # 确保日志选项卡内容能够正确扩展
            logs_tab.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
            tab_widget.addTab(logs_tab, "📋 运行日志")
        else:
            # 即使不显示日志选项卡，也要初始化log_text为None并连接信号
            self.log_text = None
            self.log_manager.log_updated.connect(self.append_log)

        # 添加tab_widget到布局，设置拉伸因子为1确保它占据主要空间
        layout.addWidget(tab_widget, 1)

        # 控制按钮区域
        button_frame = QtWidgets.QFrame()
        button_frame.setStyleSheet(AppStyles.get_button_frame_style())
        button_layout = QtWidgets.QHBoxLayout(button_frame)

        # 状态指示器 - 现代化设计
        self.status_label = QtWidgets.QLabel("⚫ 未启动")
        self.status_label.setStyleSheet("""
            color: #f56565;
            font-weight: 600;
            font-size: 15px;
            padding: 8px 12px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(245, 101, 101, 0.1), stop:1 rgba(245, 101, 101, 0.05));
            border-radius: 6px;
            border-left: 3px solid #f56565;
        """)

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



    def _build_card(self, title: str, *, with_form: bool = True):
        card = QtWidgets.QFrame()
        card.setProperty("class", "settings-card")
        card.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Maximum)
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        header = QtWidgets.QLabel(title)
        header.setProperty("class", "card-header")
        layout.addWidget(header)

        form = None
        if with_form:
            form = QtWidgets.QFormLayout()
            form.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            form.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
            form.setHorizontalSpacing(12)
            form.setVerticalSpacing(8)
            layout.addLayout(form)

        return card, layout, form

    def _build_provider_panel(self, title: str):
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(0, 6, 0, 0)
        layout.setSpacing(8)

        header = QtWidgets.QLabel(title)
        header.setProperty("class", "card-subheader")
        layout.addWidget(header)

        form = QtWidgets.QFormLayout()
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        layout.addLayout(form)

        return panel, layout, form

    def _create_provider_card(self):
        card, card_layout, provider_form = self._build_card("🤖 AI 服务商")

        provider_widget = QtWidgets.QWidget()
        provider_row = QtWidgets.QHBoxLayout(provider_widget)
        provider_row.setContentsMargins(0, 0, 0, 0)
        provider_row.setSpacing(12)

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
        provider_form.addRow("服务商", provider_widget)

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
        default_gpt_key = "sk-FbfcCVp4Qzh5WIXX8kMNI8gLUoBSH4c6ZzdwEbM2tiz0obDj"
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
                        "default": "AIzaSyBxrlBuilfstZRgoLUQghukDSVq0Helc6E",
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
                        "default": DEFAULT_GEMINI_BASE_URL,
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
                            "ai_providers.gemini.available_models",
                            "available_gemini_models",
                        ],
                        "default_items": AVAILABLE_GEMINI_MODELS,
                        "value_paths": [
                            "ai_providers.gemini.model",
                            "gemini_model",
                        ],
                        "default": DEFAULT_GEMINI_MODEL,
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
                        "default": default_gpt_key,
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
                        "default": DEFAULT_GPT_BASE_URL,
                    },
                    {
                        "type": "combo",
                        "attr": "gpt_model_combo",
                        "label": "模型",
                        "items_paths": [
                            "ai_providers.gpt.available_models",
                            "available_gpt_models",
                        ],
                        "default_items": AVAILABLE_GPT_MODELS,
                        "value_paths": [
                            "ai_providers.gpt.model",
                            "gpt_model",
                        ],
                        "default": DEFAULT_GPT_MODEL,
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

        value = self._resolve_config_value(field.get("value_paths", []), field.get("default"))
        if value is not None:
            line_edit.setText(value)

        row = QtWidgets.QWidget()
        row_layout = QtWidgets.QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)
        row_layout.addWidget(line_edit)

        toggle_slot = field.get("toggle_slot")
        button = QtWidgets.QPushButton(field.get("button_text", "👁️"))
        button.setProperty("class", field.get("button_class", "secondary"))
        button.setToolTip(field.get("button_tooltip", ""))
        button.setStyleSheet("padding: 0; margin: 0;")
        if toggle_slot:
            button.clicked.connect(toggle_slot)
        row_layout.addWidget(button)

        form.addRow(field.get("label", ""), row)

        button_height = max(line_edit.sizeHint().height(), 32)
        button.setFixedSize(button_height, button_height)

        setattr(self, field["attr"], line_edit)
        button_attr = field.get("button_attr")
        if button_attr:
            setattr(self, button_attr, button)

        return line_edit

    def _create_line_edit_field(self, form, field):
        line_edit = QtWidgets.QLineEdit()
        line_edit.setPlaceholderText(field.get("placeholder", ""))
        value = self._resolve_config_value(field.get("value_paths", []), field.get("default"))
        if value is not None:
            line_edit.setText(value)

        form.addRow(field.get("label", ""), line_edit)
        setattr(self, field["attr"], line_edit)
        return line_edit

    def _create_checkbox_field(self, form, field):
        checkbox = QtWidgets.QCheckBox(field.get("text", ""))
        value = self._resolve_config_value(field.get("value_paths", []), field.get("default", False))
        checkbox.setChecked(bool(value))

        form.addRow(field.get("label", ""), checkbox)
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
        combo.setMinimumHeight(field.get("minimum_height", 32))

        current_value = self._resolve_config_value(field.get("value_paths", []), field.get("default"))
        if current_value and current_value in items:
            combo.setCurrentText(current_value)

        form.addRow(field.get("label", ""), combo)
        setattr(self, field["attr"], combo)
        return combo

    def _create_proxy_card(self): 
        card, _, form = self._build_card("🌐 网络配置")
        self.proxy_edit = QtWidgets.QLineEdit()
        proxy_url = self.config_manager.get(
            "network.proxy",
            self.config_manager.get("proxy", "http://127.0.0.1:6789")
        )
        self.proxy_edit.setText(proxy_url)
        self.proxy_edit.setPlaceholderText("例如: http://127.0.0.1:6789")
        form.addRow("代理地址", self.proxy_edit)
        return card

    def _create_opacity_card(self):
        card, _, form = self._build_card("🎨 界面配置")
        opacity_row = QtWidgets.QWidget()
        opacity_row_layout = QtWidgets.QHBoxLayout(opacity_row)
        opacity_row_layout.setContentsMargins(0, 0, 0, 0)
        opacity_row_layout.setSpacing(10)

        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(50, 255)
        self.opacity_slider.setValue(self.config_manager.get("background_opacity", 120))
        self.opacity_slider.valueChanged.connect(self.update_opacity_label)
        opacity_row_layout.addWidget(self.opacity_slider)

        self.opacity_value_label = QtWidgets.QLabel(str(self.opacity_slider.value()))
        self.opacity_value_label.setFixedWidth(38)
        self.opacity_value_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.opacity_value_label.setStyleSheet("""
            font-weight: 600;
            color: #38bdf8;
            font-size: 15px;
            padding: 4px 8px;
            background: rgba(56, 189, 248, 0.12);
            border: 1px solid #1f2b44;
            border-radius: 6px;
        """)
        opacity_row_layout.addWidget(self.opacity_value_label)

        form.addRow("浮窗透明度", opacity_row)
        return card

    def _create_ui_card(self):
        card, _, form = self._build_card("🖥️ 界面显示设置")
        self.show_log_checkbox = QtWidgets.QCheckBox("显示运行日志选项卡")
        self.show_log_checkbox.setChecked(self.config_manager.get("show_log_tab", True))
        form.addRow("运行日志", self.show_log_checkbox)
        return card

    def _create_prompt_status_card(self):
        card, layout, _ = self._build_card("📝 提示词状态", with_form=False)
        layout.setSpacing(8)

        self.current_prompt_label = QtWidgets.QLabel()
        self.current_prompt_label.setStyleSheet("""
            font-size: 15px;
            font-weight: 600;
            color: #38bdf8;
            padding: 8px 12px;
            background: rgba(56, 189, 248, 0.18);
            border-radius: 6px;
            border-left: 3px solid #38bdf8;
        """)
        self.update_current_prompt_display()
        layout.addWidget(self.current_prompt_label)

        return card

    def create_basic_tab(self):
        """创建基本设置选项卡"""
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QtWidgets.QWidget()
        container.setMinimumWidth(960)
        root_layout = QtWidgets.QVBoxLayout(container)
        root_layout.setContentsMargins(14, 14, 14, 18)
        root_layout.setSpacing(12)

        provider_card = self._create_provider_card()
        root_layout.addWidget(provider_card)

        grid_container = QtWidgets.QWidget()
        grid_layout = QtWidgets.QGridLayout(grid_container)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setHorizontalSpacing(12)
        grid_layout.setVerticalSpacing(12)

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
        container = QtWidgets.QWidget()
        container.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(12)

        header_label = QtWidgets.QLabel("运行日志")
        header_label.setProperty("class", "section-header")
        layout.addWidget(header_label)

        helper_label = QtWidgets.QLabel("实时查看应用输出，排查问题时可复制日志分享。")
        helper_label.setProperty("class", "section-helper")
        helper_label.setWordWrap(True)
        layout.addWidget(helper_label)

        log_card = QtWidgets.QFrame()
        log_card.setObjectName("logCard")
        card_layout = QtWidgets.QVBoxLayout(log_card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(12)

        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setObjectName("logViewer")
        self.log_text.setReadOnly(True)
        self.log_text.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.log_text.setMinimumHeight(320)
        self.log_text.setStyleSheet("""
            QTextEdit {
                font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                background: #0f172a;
                color: #e2e8f0;
                border: 1px solid #1e293b;
                border-radius: 12px;
                padding: 16px;
                selection-background-color: #38bdf8;
            }
            QTextEdit:focus {
                border-color: #38bdf8;
                background: #0b1628;
            }
        """)

        card_layout.addWidget(self.log_text)
        layout.addWidget(log_card, 1)

        self.log_manager.log_updated.connect(self.append_log)

        self.log_text.append("🚀 日志系统已就绪")
        self.log_text.append("----------------------------------------")
        self.log_text.append("等待系统启动...")

        return container

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
        """????"""
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
        """???????"""
        self.opacity_value_label.setText(str(value))
        if self.overlay:
            self.config_manager.config["background_opacity"] = value
            self.overlay.update_background_opacity()

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

    def append_log(self, log_entry):
        """添加日志到界面"""
        # 只有在日志选项卡存在时才更新UI
        if hasattr(self, 'log_text') and self.log_text:
            self.log_text.append(log_entry)
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def update_status(self, status, color=STATUS_COLORS["stopped"]):
        """更新状态显示"""
        # 根据状态选择不同的图标
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

        self.status_label.setText(f"{icon} {status}")
        self.status_label.setStyleSheet(f"""
            color: {color};
            font-weight: 600;
            font-size: 15px;
            padding: 8px 12px;
            background: {bg_color};
            border-radius: 6px;
            border-left: 3px solid {border_color};
        """)

    def start_listening(self):
        """启动快捷键监听"""
        try:
            # 创建浮窗
            if not self.overlay:
                self.overlay = Overlay(self.config_manager)

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

                # 最小化到托盘
                self.hide()
                self.tray_icon.show()
                self.tray_icon.showMessage(
                    "Gemini 截图助手",
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
        # 绑定提示词发送快捷键 (统一使用alt+z)
        control_hotkeys = self.config_manager.get("hotkeys", {})
        send_prompt_key = control_hotkeys.get("send_prompt", "alt+z")
        send_prompt_handler = lambda: threading.Thread(
            target=self.send_current_prompt, daemon=True
        ).start()

        if self.hotkey_handler.register_hotkey(send_prompt_key, send_prompt_handler):
            self.log_manager.add_log(f"绑定提示词发送快捷键: {send_prompt_key}")

        # 绑定提示词切换快捷键 (alt+1-9)
        prompts = self.config_manager.get("prompts", [])
        max_prompts = min(len(prompts), 9)  # 最多9个提示词

        for i in range(max_prompts):
            hotkey_str = f"alt+{i+1}"
            handler = lambda idx=i: self.switch_prompt(idx)

            if self.hotkey_handler.register_hotkey(hotkey_str, handler):
                prompt_name = prompts[i].get('name', f'提示词{i+1}')
                self.log_manager.add_log(f"绑定提示词切换: {hotkey_str} -> {prompt_name}")

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

        scroll_up_handler = lambda: self.overlay.scroll_up()
        if self.hotkey_handler.register_hotkey(scroll_up_key, scroll_up_handler):
            self.log_manager.add_log(f"绑定向上滚动快捷键: {scroll_up_key}")

        scroll_down_handler = lambda: self.overlay.scroll_down()
        if self.hotkey_handler.register_hotkey(scroll_down_key, scroll_down_handler):
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

    def handle_api_response(self, response: str):
        """在主线程中处理API响应"""
        try:
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
            # 创建截图选择器
            self.screenshot_selector = ScreenshotSelector()

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
            self.screenshot_selector = ScreenshotSelector()
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
            # 执行实际的API调用
            md = None
            if provider == "GPT":
                # 使用GPT API
                if len(all_images) == 1:
                    md = self.gpt_api.call_api_single_image(all_images[0], prompt['content'])
                else:
                    md = self.gpt_api.call_api_multi_images(all_images, prompt['content'])
            else:
                # 默认使用Gemini API
                if len(all_images) == 1:
                    md = self.gemini_api.call_api_single_image(all_images[0], prompt['content'])
                else:
                    md = self.gemini_api.call_api_multi_images(all_images, prompt['content'])

            # 通过信号发送结果到主线程
            if md:
                self.api_response_signal.emit(md)
            else:
                self.api_response_signal.emit("API调用失败，未获得响应")

        except Exception as e:
            # 发送错误信息到主线程
            error_msg = f"API调用异常: {str(e)}"
            self.log_manager.add_log(error_msg, "ERROR")
            self.api_response_signal.emit(f"错误: {error_msg}")

        finally:
            # 清理资源（通过信号在主线程中执行）
            QtCore.QTimer.singleShot(0, self._cleanup_screenshot_history)

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
        try:
            # 启动流式渲染
            self.overlay.start_streaming()
            self.log_manager.add_log("开始流式响应处理")

            full_response = ""
            chunk_count = 0

            for chunk_text, is_complete in response_stream:
                chunk_count += 1
                self.log_manager.add_log(f"收到chunk #{chunk_count}, 完成状态: {is_complete}")

                if is_complete:
                    # 流式响应完成
                    self.log_manager.add_log(f"流式响应完成，总长度: {len(full_response)}字符")
                    self.overlay.finish_streaming()
                    self._process_complete_response(full_response)
                    break
                else:
                    # 追加内容块
                    full_response += chunk_text
                    self.log_manager.add_log(f"追加内容: {chunk_text[:50]}...")
                    self.overlay.content_chunk.emit(chunk_text)

        except Exception as e:
            self.overlay.finish_streaming()
            self.log_manager.add_log(f"流式响应处理失败: {e}", "ERROR")
            # 回退到传统渲染
            if 'full_response' in locals() and full_response:
                from markdown_it import MarkdownIt
                html = MarkdownIt("commonmark", {"html": True}).render(full_response)
                self.overlay.handle_response(html)

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
            "Gemini 截图助手已经在运行中！\n\n请检查系统托盘或任务管理器。",
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
    main_window = GeminiAssistantApp(config_manager, log_manager, single_instance)
    main_window.show()

    try:
        sys.exit(app.exec())
    finally:
        # 确保释放锁
        single_instance.release_lock()


if __name__ == "__main__":
    main()








