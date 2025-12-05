"""提示词管理组件 - 使用现代化UI"""

from __future__ import annotations

from PyQt6 import QtCore, QtWidgets, QtGui

from ..core.config_manager import ConfigManager
from ..core.log_manager import LogManager
from .modern_ui import (
    DesignSystem,
    Card,
    FormRow,
    ModernLineEdit,
    ModernComboBox,
    ModernButton,
)


class ModernTextEdit(QtWidgets.QPlainTextEdit):
    """现代化多行文本框"""

    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self._focused = False
        self._apply_style()

    def focusInEvent(self, event):
        self._focused = True
        self._apply_style()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self._focused = False
        self._apply_style()
        super().focusOutEvent(event)

    def _apply_style(self):
        border_color = DesignSystem.Colors.PRIMARY if self._focused else DesignSystem.Colors.BORDER_DEFAULT
        bg = DesignSystem.Colors.BG_ELEVATED if self._focused else DesignSystem.Colors.BG_TERTIARY

        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {bg};
                border: 1px solid {border_color};
                border-radius: {DesignSystem.Radius.SM}px;
                padding: 12px;
                font-size: {DesignSystem.Typography.SIZE_MD}px;
                color: {DesignSystem.Colors.TEXT_PRIMARY};
                selection-background-color: {DesignSystem.Colors.PRIMARY};
            }}
            QPlainTextEdit::placeholder {{
                color: {DesignSystem.Colors.TEXT_DISABLED};
            }}
        """)


class PromptManagerWidget(QtWidgets.QWidget):
    """提示词管理界面组件 - 现代化UI"""

    def __init__(self, config_manager: ConfigManager, log_manager: LogManager):
        super().__init__()
        self.config_manager = config_manager
        self.log_manager = log_manager
        self._setup_ui()
        self.load_prompts_list()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # ═══════════════════════════════════════════════════════════════════
        # 提示词选择卡片
        # ═══════════════════════════════════════════════════════════════════
        select_card = Card("选择提示词", "从已保存的提示词中选择，或创建新的提示词")

        self.prompts_combo = ModernComboBox()
        self.prompts_combo.setEditable(True)
        self.prompts_combo.setPlaceholderText("搜索或选择提示词...")
        self.prompts_combo.currentIndexChanged.connect(self.on_prompt_selected)
        select_card.add_widget(FormRow("提示词列表", self.prompts_combo))

        layout.addWidget(select_card)

        # ═══════════════════════════════════════════════════════════════════
        # 编辑提示词卡片
        # ═══════════════════════════════════════════════════════════════════
        edit_card = Card("编辑提示词", "设置提示词名称、快捷键和内容")

        # 名称
        self.prompt_name_edit = ModernLineEdit("例如：代码实现助手")
        edit_card.add_widget(FormRow("提示词名称", self.prompt_name_edit))

        # 快捷键
        hotkey_container = QtWidgets.QWidget()
        hotkey_layout = QtWidgets.QHBoxLayout(hotkey_container)
        hotkey_layout.setContentsMargins(0, 0, 0, 0)
        hotkey_layout.setSpacing(8)

        self.prompt_hotkey_edit = ModernLineEdit("例如：alt+1")
        hotkey_layout.addWidget(self.prompt_hotkey_edit, 1)

        self.hotkey_help_btn = ModernButton("说明", "ghost")
        self.hotkey_help_btn.setFixedWidth(60)
        self.hotkey_help_btn.clicked.connect(self.show_hotkey_help)
        hotkey_layout.addWidget(self.hotkey_help_btn)

        edit_card.add_widget(FormRow("快捷键", hotkey_container))

        # 内容
        self.prompt_content_edit = ModernTextEdit("请输入详细的提示词内容...")
        self.prompt_content_edit.setMinimumHeight(180)
        self.prompt_content_edit.textChanged.connect(self.update_char_count)
        edit_card.add_widget(FormRow("提示词内容", self.prompt_content_edit))

        # 字符计数
        self.char_count_label = QtWidgets.QLabel("字符数: 0")
        self.char_count_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.char_count_label.setStyleSheet(f"""
            font-size: {DesignSystem.Typography.SIZE_XS}px;
            color: {DesignSystem.Colors.TEXT_TERTIARY};
            padding-right: 8px;
        """)
        edit_card.add_widget(self.char_count_label)

        layout.addWidget(edit_card)

        # ═══════════════════════════════════════════════════════════════════
        # 操作按钮
        # ═══════════════════════════════════════════════════════════════════
        button_container = QtWidgets.QWidget()
        button_layout = QtWidgets.QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(12)

        self.add_btn = ModernButton("添加", "success")
        self.add_btn.setMinimumWidth(80)
        self.add_btn.clicked.connect(self.add_prompt)
        button_layout.addWidget(self.add_btn)

        self.update_btn = ModernButton("更新", "primary")
        self.update_btn.setMinimumWidth(80)
        self.update_btn.clicked.connect(self.update_prompt)
        button_layout.addWidget(self.update_btn)

        self.delete_btn = ModernButton("删除", "danger")
        self.delete_btn.setMinimumWidth(80)
        self.delete_btn.clicked.connect(self.delete_prompt)
        button_layout.addWidget(self.delete_btn)

        self.clear_btn = ModernButton("清空", "secondary")
        self.clear_btn.setMinimumWidth(80)
        self.clear_btn.clicked.connect(self.clear_prompt_fields)
        button_layout.addWidget(self.clear_btn)

        button_layout.addStretch()

        self.refresh_btn = ModernButton("刷新列表", "ghost")
        self.refresh_btn.clicked.connect(self.load_prompts_list)
        button_layout.addWidget(self.refresh_btn)

        layout.addWidget(button_container)
        layout.addStretch()

    def load_prompts_list(self):
        """加载提示词列表"""
        self.prompts_combo.clear()
        prompts = self.config_manager.get("prompts", [])
        for prompt in prompts:
            item_text = f"{prompt['name']} ({prompt['hotkey']})"
            self.prompts_combo.addItem(item_text, prompt)

        if prompts:
            self.prompts_combo.setCurrentIndex(0)
            self.on_prompt_selected(0)
        else:
            self.clear_prompt_fields()

    def on_prompt_selected(self, index):
        """选择提示词时的处理"""
        if index >= 0:
            prompt = self.prompts_combo.itemData(index)
            if prompt:
                self.prompt_name_edit.setText(prompt['name'])
                self.prompt_hotkey_edit.setText(prompt['hotkey'])
                self.prompt_content_edit.setPlainText(prompt['content'])
                self.update_char_count()

    def add_prompt(self):
        """添加新提示词"""
        name = self.prompt_name_edit.text().strip()
        hotkey = self.prompt_hotkey_edit.text().strip()
        content = self.prompt_content_edit.toPlainText().strip()

        if not all([name, hotkey, content]):
            QtWidgets.QMessageBox.warning(self, "警告", "请填写完整信息")
            return

        prompts = self.config_manager.get("prompts", [])

        for prompt in prompts:
            if prompt['hotkey'] == hotkey:
                QtWidgets.QMessageBox.warning(self, "警告", "快捷键已存在")
                return

        new_prompt = {
            "name": name,
            "hotkey": hotkey,
            "content": content
        }

        prompts.append(new_prompt)
        self.config_manager.set("prompts", prompts)
        self.load_prompts_list()
        self.clear_prompt_fields()
        self.log_manager.add_log(f"添加提示词: {name}")

        QtWidgets.QMessageBox.information(self, "成功", f"已添加提示词: {name}")

    def update_prompt(self):
        """更新选中的提示词"""
        index = self.prompts_combo.currentIndex()
        if index < 0:
            QtWidgets.QMessageBox.warning(self, "警告", "请先选择要更新的提示词")
            return

        name = self.prompt_name_edit.text().strip()
        hotkey = self.prompt_hotkey_edit.text().strip()
        content = self.prompt_content_edit.toPlainText().strip()

        if not all([name, hotkey, content]):
            QtWidgets.QMessageBox.warning(self, "警告", "请填写完整信息")
            return

        prompts = self.config_manager.get("prompts", [])

        for i, prompt in enumerate(prompts):
            if i != index and prompt['hotkey'] == hotkey:
                QtWidgets.QMessageBox.warning(self, "警告", "快捷键已存在")
                return

        prompts[index] = {
            "name": name,
            "hotkey": hotkey,
            "content": content
        }

        self.config_manager.set("prompts", prompts)
        self.load_prompts_list()
        self.log_manager.add_log(f"更新提示词: {name}")

        QtWidgets.QMessageBox.information(self, "成功", f"已更新提示词: {name}")

    def delete_prompt(self):
        """删除选中的提示词"""
        index = self.prompts_combo.currentIndex()
        if index < 0:
            QtWidgets.QMessageBox.warning(self, "警告", "请先选择要删除的提示词")
            return

        prompts = self.config_manager.get("prompts", [])
        if index < len(prompts):
            name = prompts[index]['name']
            reply = QtWidgets.QMessageBox.question(
                self, "确认",
                f"确定要删除提示词 '{name}' 吗？"
            )
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                prompts.pop(index)
                self.config_manager.set("prompts", prompts)
                self.load_prompts_list()
                self.clear_prompt_fields()
                self.log_manager.add_log(f"删除提示词: {name}")

                QtWidgets.QMessageBox.information(self, "成功", f"已删除提示词: {name}")

    def clear_prompt_fields(self):
        """清空提示词编辑字段"""
        self.prompt_name_edit.clear()
        self.prompt_hotkey_edit.clear()
        self.prompt_content_edit.clear()
        self.update_char_count()

    def update_char_count(self):
        """更新字符计数"""
        count = len(self.prompt_content_edit.toPlainText())
        self.char_count_label.setText(f"字符数: {count}")

    def show_hotkey_help(self):
        """显示快捷键格式帮助"""
        help_text = """快捷键格式说明：

• 单个键：a, b, c, 1, 2, 3
• 修饰键组合：
  - ctrl+a
  - alt+b
  - shift+c
  - ctrl+shift+d

请使用英文加号 + 连接按键，按键名称不区分大小写。"""
        QtWidgets.QMessageBox.information(self, "快捷键说明", help_text)
