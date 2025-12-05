"""日志查看器组件 - 使用现代化UI"""

from PyQt6 import QtCore, QtGui, QtWidgets

from ..core.log_manager import LogManager
from .modern_ui import (
    DesignSystem,
    Card,
    FormRow,
    ModernLineEdit,
    ModernButton,
)


class ModernLogTextEdit(QtWidgets.QTextEdit):
    """现代化日志文本框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QTextEdit {{
                font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                background: {DesignSystem.Colors.BG_TERTIARY};
                color: {DesignSystem.Colors.TEXT_PRIMARY};
                border: 1px solid {DesignSystem.Colors.BORDER_DEFAULT};
                border-radius: {DesignSystem.Radius.SM}px;
                padding: 16px;
                selection-background-color: {DesignSystem.Colors.PRIMARY};
            }}
            QTextEdit:focus {{
                border-color: {DesignSystem.Colors.PRIMARY};
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.15);
                border-radius: 4px;
                min-height: 40px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(255, 255, 255, 0.25);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
        """)


class LogViewerWidget(QtWidgets.QWidget):
    """日志查看器组件 - 现代化UI"""

    def __init__(self, log_manager: LogManager, use_fluent_theme: bool = False):
        super().__init__()
        self.log_manager = log_manager
        self._log_filter_text = ""
        self._setup_ui()

        # 连接信号
        self.log_manager.log_updated.connect(self.append_log)

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # ═══════════════════════════════════════════════════════════════════
        # 日志卡片
        # ═══════════════════════════════════════════════════════════════════
        log_card = Card("运行日志", "实时查看应用输出，排查问题时可复制日志分享")

        # 过滤器
        filter_container = QtWidgets.QWidget()
        filter_layout = QtWidgets.QHBoxLayout(filter_container)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(12)

        self.log_filter_edit = ModernLineEdit("输入关键字过滤日志...")
        self.log_filter_edit.textChanged.connect(self._apply_log_filter)
        filter_layout.addWidget(self.log_filter_edit, 1)

        log_card.add_widget(FormRow("筛选", filter_container))

        # 日志文本框
        self.log_text = ModernLogTextEdit()
        self.log_text.setMinimumHeight(350)
        self.log_text.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding
        )
        log_card.add_widget(self.log_text)

        layout.addWidget(log_card, 1)

        # ═══════════════════════════════════════════════════════════════════
        # 操作按钮
        # ═══════════════════════════════════════════════════════════════════
        button_container = QtWidgets.QWidget()
        button_layout = QtWidgets.QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(12)

        button_layout.addStretch()

        self.copy_btn = ModernButton("复制日志", "secondary")
        self.copy_btn.setMinimumWidth(100)
        self.copy_btn.clicked.connect(self._copy_logs_to_clipboard)
        button_layout.addWidget(self.copy_btn)

        self.clear_btn = ModernButton("清空日志", "ghost")
        self.clear_btn.setMinimumWidth(100)
        self.clear_btn.clicked.connect(self._clear_logs_via_ui)
        button_layout.addWidget(self.clear_btn)

        layout.addWidget(button_container)

        # 初始日志
        self._render_logs()

    def _apply_log_filter(self) -> None:
        """应用日志过滤"""
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
                    "────────────────────────────────",
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
