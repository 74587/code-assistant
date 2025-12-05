"""
日志查看器组件
"""

from PyQt6 import QtCore, QtGui, QtWidgets

from ..core.log_manager import LogManager
from ..utils.constants import USE_FLUENT_THEME

try:
    from .fluent_theme import (
        FluentSettingsCard,
        FluentCardColumn,
        create_card_scroll_area,
    )
    from qfluentwidgets import CommandBar, FluentIcon
    HAS_FLUENT_THEME = True
except Exception:
    FluentSettingsCard = None
    FluentCardColumn = None
    create_card_scroll_area = None
    CommandBar = None
    FluentIcon = None
    HAS_FLUENT_THEME = False


class LogViewerWidget(QtWidgets.QWidget):
    """日志查看器组件"""

    def __init__(self, log_manager: LogManager, use_fluent_theme: bool = False):
        super().__init__()
        self.log_manager = log_manager
        self.use_fluent_theme = use_fluent_theme and USE_FLUENT_THEME and HAS_FLUENT_THEME

        self.log_text: QtWidgets.QTextEdit = None
        self.log_command_bar = None
        self.log_filter_edit: QtWidgets.QLineEdit = None
        self._log_filter_text = ""

        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if self.use_fluent_theme:
            content = self._create_fluent_ui()
        else:
            content = self._create_classic_ui()

        layout.addWidget(content)

        # 连接信号
        self.log_manager.log_updated.connect(self.append_log)

    def _create_fluent_ui(self) -> QtWidgets.QWidget:
        """创建 Fluent 风格 UI"""
        if not (FluentCardColumn and create_card_scroll_area and CommandBar):
            return self._create_classic_ui()

        column = FluentCardColumn()
        scroll_area = create_card_scroll_area(column)

        icon = getattr(FluentIcon, "INFO", None) if FluentIcon else None
        card = FluentSettingsCard(
            title="运行日志",
            description="实时查看应用输出，可按关键字过滤并快速复制。",
            icon=icon,
        )
        column.add_widget(card)

        # 命令栏
        self.log_command_bar = CommandBar(self)
        self.log_command_bar.setButtonTight(True)
        self.log_command_bar.setIconSize(QtCore.QSize(18, 18))
        card.body_layout.addWidget(self.log_command_bar)
        self._init_log_actions()

        # 过滤器
        filter_widget = QtWidgets.QWidget()
        filter_layout = QtWidgets.QHBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(8)

        filter_label = QtWidgets.QLabel("关键字筛选")
        filter_label.setStyleSheet("color: rgba(226, 232, 240, 0.78); font-weight: 600;")
        filter_layout.addWidget(filter_label)

        self.log_filter_edit = QtWidgets.QLineEdit()
        self.log_filter_edit.setPlaceholderText("输入关键字过滤日志…")
        self.log_filter_edit.textChanged.connect(self._apply_log_filter)
        filter_layout.addWidget(self.log_filter_edit)

        card.body_layout.addWidget(filter_widget)

        # 日志文本框
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setObjectName("logViewer")
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(320)
        self.log_text.setStyleSheet(
            "QTextEdit {"
            " font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', 'Monaco', monospace;"
            " font-size: 12px;"
            " background: rgba(15, 23, 42, 0.72);"
            " color: #e2e8f0;"
            " border: 1px solid rgba(71, 85, 105, 0.38);"
            " border-radius: 12px;"
            " padding: 16px;"
            "}"
            "QTextEdit:focus {"
            " border-color: rgba(94, 129, 244, 0.6);"
            "}"
        )
        card.body_layout.addWidget(self.log_text)

        self._render_logs()
        return scroll_area

    def _create_classic_ui(self) -> QtWidgets.QWidget:
        """创建经典风格 UI"""
        container = QtWidgets.QWidget()
        container.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding
        )

        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(12)

        # 标题
        header_label = QtWidgets.QLabel("运行日志")
        header_label.setProperty("class", "section-header")
        layout.addWidget(header_label)

        helper_label = QtWidgets.QLabel("实时查看应用输出，排查问题时可复制日志分享。")
        helper_label.setProperty("class", "section-helper")
        helper_label.setWordWrap(True)
        layout.addWidget(helper_label)

        # 日志卡片
        log_card = QtWidgets.QFrame()
        log_card.setObjectName("logCard")
        card_layout = QtWidgets.QVBoxLayout(log_card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(16)

        # 日志文本框
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setObjectName("logViewer")
        self.log_text.setReadOnly(True)
        self.log_text.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding
        )
        self.log_text.setMinimumHeight(320)
        self.log_text.setStyleSheet(
            "QTextEdit {"
            " font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', 'Monaco', monospace;"
            " font-size: 12px;"
            " background: #0f172a;"
            " color: #e2e8f0;"
            " border: 1px solid #1e293b;"
            " border-radius: 12px;"
            " padding: 16px;"
            " selection-background-color: #38bdf8;"
            "}"
            "QTextEdit:focus {"
            " border-color: #38bdf8;"
            " background: #0b1628;"
            "}"
        )

        card_layout.addWidget(self.log_text)
        layout.addWidget(log_card, 1)

        # 初始日志
        self.log_text.append("日志系统已就绪")
        self.log_text.append("----------------------------------------")
        self.log_text.append("等待系统启动...")

        return container

    def _init_log_actions(self) -> None:
        """初始化日志操作按钮"""
        if not self.log_command_bar:
            return

        def build_action(text: str, slot, icon_name: str | None) -> None:
            action = QtGui.QAction(text, self)
            if icon_name and FluentIcon:
                icon_obj = getattr(FluentIcon, icon_name, None)
                if icon_obj:
                    action.setIcon(icon_obj.icon())
            action.triggered.connect(slot)
            self.log_command_bar.addAction(action)

        build_action("复制日志", self._copy_logs_to_clipboard, "COPY")
        build_action("清空日志", self._clear_logs_via_ui, "CLEAR_SELECTION")

    def _apply_log_filter(self) -> None:
        """应用日志过滤"""
        if not self.log_filter_edit:
            return
        self._log_filter_text = self.log_filter_edit.text().strip()
        self._render_logs()

    def _render_logs(self) -> None:
        """渲染日志"""
        if not self.log_text:
            return

        logs = getattr(self.log_manager, "logs", [])
        if self._log_filter_text:
            lower_filter = self._log_filter_text.lower()
            filtered = [log for log in logs if lower_filter in log.lower()]
        else:
            filtered = list(logs)

        if not filtered:
            if logs:
                display_lines = ["当前过滤条件未匹配任何日志。"]
            else:
                display_lines = [
                    "日志系统已就绪",
                    "----------------------------------------",
                    "等待系统启动...",
                ]
        else:
            display_lines = filtered

        self.log_text.setPlainText("\n".join(display_lines))
        self.log_text.moveCursor(QtGui.QTextCursor.MoveOperation.End)

    def _copy_logs_to_clipboard(self) -> None:
        """复制日志到剪贴板"""
        if not self.log_text:
            return
        QtWidgets.QApplication.clipboard().setText(self.log_text.toPlainText())

    def _clear_logs_via_ui(self) -> None:
        """清空日志"""
        self.log_manager.clear_logs()
        self._render_logs()

    @QtCore.pyqtSlot(str)
    def append_log(self, message: str):
        """追加日志消息"""
        if self._log_filter_text:
            # 如果有过滤条件，重新渲染
            self._render_logs()
        elif self.log_text:
            self.log_text.append(message)
            self.log_text.moveCursor(QtGui.QTextCursor.MoveOperation.End)
