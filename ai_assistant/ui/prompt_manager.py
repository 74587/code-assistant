"""提示词管理组件 - 使用现代化UI"""

from __future__ import annotations

from PyQt6 import QtCore, QtWidgets, QtGui

from ..core.config_manager import ConfigManager
from ..core.log_manager import LogManager
from ..core.hotkey_config import HotkeyConfig
from .modern_ui import (
    DesignSystem,
    Card,
    FormRow,
    ModernLineEdit,
    ModernComboBox,
    ModernButton,
    ProtectedMessageBox,
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
        bg = DesignSystem.Colors.BG_ELEVATED if self._focused else DesignSystem.Colors.BG_INPUT

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
        self._current_edit_index = -1  # 当前编辑的提示词索引，-1表示新建模式
        self._setup_ui()
        self.load_prompts_list()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # ═══════════════════════════════════════════════════════════════════
        # 提示词选择卡片
        # ═══════════════════════════════════════════════════════════════════
        select_card = Card("选择提示词", "从已保存的提示词中选择编辑，或创建新的提示词")

        self.prompts_combo = ModernComboBox()
        self.prompts_combo.setPlaceholderText("选择提示词进行编辑...")
        self.prompts_combo.currentIndexChanged.connect(self.on_prompt_selected)
        select_card.add_widget(FormRow("提示词列表", self.prompts_combo))

        layout.addWidget(select_card)

        # ═══════════════════════════════════════════════════════════════════
        # 编辑提示词卡片
        # ═══════════════════════════════════════════════════════════════════
        edit_card = Card("编辑提示词", "设置提示词名称、快捷键和内容")

        # 编辑模式指示
        self.mode_label = QtWidgets.QLabel("新建模式")
        self.mode_label.setStyleSheet(f"""
            font-size: {DesignSystem.Typography.SIZE_SM}px;
            color: {DesignSystem.Colors.PRIMARY};
            font-weight: {DesignSystem.Typography.WEIGHT_MEDIUM};
            padding: 4px 8px;
            background: {DesignSystem.Colors.PRIMARY_LIGHT};
            border-radius: 4px;
        """)
        edit_card.add_widget(self.mode_label)

        # 名称
        self.prompt_name_edit = ModernLineEdit("例如：代码实现助手")
        edit_card.add_widget(FormRow("提示词名称", self.prompt_name_edit))

        # 快捷键 - 改为下拉选择
        hotkey_container = QtWidgets.QWidget()
        hotkey_layout = QtWidgets.QVBoxLayout(hotkey_container)
        hotkey_layout.setContentsMargins(0, 0, 0, 0)
        hotkey_layout.setSpacing(4)

        hotkey_input_row = QtWidgets.QHBoxLayout()
        hotkey_input_row.setSpacing(8)

        self.hotkey_combo = ModernComboBox()
        self.hotkey_combo.setPlaceholderText("选择快捷键...")
        hotkey_input_row.addWidget(self.hotkey_combo, 1)

        self.hotkey_help_btn = ModernButton("说明", "ghost")
        self.hotkey_help_btn.setFixedWidth(60)
        self.hotkey_help_btn.clicked.connect(self.show_hotkey_help)
        hotkey_input_row.addWidget(self.hotkey_help_btn)

        hotkey_layout.addLayout(hotkey_input_row)

        # 快捷键提示
        self.hotkey_hint_label = QtWidgets.QLabel("选择 Alt+数字 作为快捷键，启动后按该快捷键即可发送提示词")
        self.hotkey_hint_label.setWordWrap(True)
        self.hotkey_hint_label.setStyleSheet(f"""
            font-size: {DesignSystem.Typography.SIZE_XS}px;
            color: {DesignSystem.Colors.TEXT_TERTIARY};
        """)
        hotkey_layout.addWidget(self.hotkey_hint_label)

        edit_card.add_widget(FormRow("快捷键", hotkey_container))

        # 内容
        self.prompt_content_edit = ModernTextEdit("请输入详细的提示词内容...")
        self.prompt_content_edit.setMinimumHeight(140)
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

        # 保存按钮（根据模式自动切换为添加/更新）
        self.save_btn = ModernButton("保存新建", "success")
        self.save_btn.setMinimumWidth(90)
        self.save_btn.clicked.connect(self.save_prompt)
        button_layout.addWidget(self.save_btn)

        self.delete_btn = ModernButton("删除", "danger")
        self.delete_btn.setMinimumWidth(70)
        self.delete_btn.setEnabled(False)  # 新建模式下禁用
        self.delete_btn.clicked.connect(self.delete_prompt)
        button_layout.addWidget(self.delete_btn)

        self.new_btn = ModernButton("新建", "secondary")
        self.new_btn.setMinimumWidth(70)
        self.new_btn.clicked.connect(self.start_new_prompt)
        button_layout.addWidget(self.new_btn)

        button_layout.addStretch()

        self.refresh_btn = ModernButton("刷新列表", "ghost")
        self.refresh_btn.clicked.connect(self.load_prompts_list)
        button_layout.addWidget(self.refresh_btn)

        layout.addWidget(button_container)
        layout.addStretch()

    def _get_used_hotkeys(self, exclude_index: int = -1) -> list:
        """获取已使用的快捷键列表"""
        prompts = self.config_manager.get("prompts", [])
        used = []
        for i, prompt in enumerate(prompts):
            if i != exclude_index:
                used.append(prompt.get('hotkey', ''))
        return used

    def _update_hotkey_combo(self, current_hotkey: str = ""):
        """更新快捷键下拉框选项"""
        self.hotkey_combo.blockSignals(True)
        self.hotkey_combo.clear()

        # 获取已使用的快捷键（排除当前编辑的）
        used_hotkeys = self._get_used_hotkeys(self._current_edit_index)
        available_slots = HotkeyConfig.get_available_prompt_slots(used_hotkeys)

        # 如果当前有值，确保它在列表中
        if current_hotkey:
            normalized = HotkeyConfig.normalize_hotkey(current_hotkey)
            if normalized not in available_slots:
                available_slots.insert(0, normalized)

        # 添加可用选项
        for slot in available_slots:
            display_text = slot.upper().replace("+", " + ")
            self.hotkey_combo.addItem(display_text, slot)

        # 设置当前值
        if current_hotkey:
            normalized = HotkeyConfig.normalize_hotkey(current_hotkey)
            for i in range(self.hotkey_combo.count()):
                if self.hotkey_combo.itemData(i) == normalized:
                    self.hotkey_combo.setCurrentIndex(i)
                    break

        self.hotkey_combo.blockSignals(False)

        # 更新提示文本
        if not available_slots:
            self.hotkey_hint_label.setText("所有快捷键槽位已用完（最多9个提示词）")
            self.hotkey_hint_label.setStyleSheet(f"""
                font-size: {DesignSystem.Typography.SIZE_XS}px;
                color: {DesignSystem.Colors.WARNING};
            """)
        else:
            remaining = len(available_slots)
            self.hotkey_hint_label.setText(f"还可创建 {remaining} 个提示词")
            self.hotkey_hint_label.setStyleSheet(f"""
                font-size: {DesignSystem.Typography.SIZE_XS}px;
                color: {DesignSystem.Colors.TEXT_TERTIARY};
            """)

    def load_prompts_list(self):
        """加载提示词列表"""
        self.prompts_combo.blockSignals(True)
        self.prompts_combo.clear()

        # 添加"新建"选项
        self.prompts_combo.addItem("➕ 新建提示词...", None)

        prompts = self.config_manager.get("prompts", [])
        for i, prompt in enumerate(prompts):
            hotkey_display = prompt['hotkey'].upper().replace("+", "+")
            item_text = f"{prompt['name']} ({hotkey_display})"
            self.prompts_combo.addItem(item_text, {"index": i, "prompt": prompt})

        self.prompts_combo.blockSignals(False)
        self.prompts_combo.setCurrentIndex(0)
        self.start_new_prompt()

    def on_prompt_selected(self, index):
        """选择提示词时的处理"""
        if index <= 0:
            # 选择了"新建"
            self.start_new_prompt()
            return

        data = self.prompts_combo.itemData(index)
        if data and "prompt" in data:
            prompt = data["prompt"]
            self._current_edit_index = data["index"]

            self.prompt_name_edit.setText(prompt['name'])
            self._update_hotkey_combo(prompt['hotkey'])
            self.prompt_content_edit.setPlainText(prompt['content'])
            self.update_char_count()

            self._set_edit_mode()

    def start_new_prompt(self):
        """开始新建提示词"""
        self._current_edit_index = -1
        self.prompt_name_edit.clear()
        self._update_hotkey_combo("")  # 刷新可用快捷键
        self.prompt_content_edit.clear()
        self.update_char_count()
        self._set_new_mode()

        # 重置下拉框到"新建"选项
        self.prompts_combo.blockSignals(True)
        self.prompts_combo.setCurrentIndex(0)
        self.prompts_combo.blockSignals(False)

    def _set_new_mode(self):
        """设置为新建模式"""
        self.mode_label.setText("新建模式")
        self.mode_label.setStyleSheet(f"""
            font-size: {DesignSystem.Typography.SIZE_SM}px;
            color: {DesignSystem.Colors.PRIMARY};
            font-weight: {DesignSystem.Typography.WEIGHT_MEDIUM};
            padding: 4px 8px;
            background: {DesignSystem.Colors.PRIMARY_LIGHT};
            border-radius: 4px;
        """)
        self.save_btn.setText("保存新建")
        self.delete_btn.setEnabled(False)

    def _set_edit_mode(self):
        """设置为编辑模式"""
        self.mode_label.setText("编辑模式")
        self.mode_label.setStyleSheet(f"""
            font-size: {DesignSystem.Typography.SIZE_SM}px;
            color: {DesignSystem.Colors.ACCENT};
            font-weight: {DesignSystem.Typography.WEIGHT_MEDIUM};
            padding: 4px 8px;
            background: {DesignSystem.Colors.ACCENT_LIGHT};
            border-radius: 4px;
        """)
        self.save_btn.setText("保存修改")
        self.delete_btn.setEnabled(True)

    def save_prompt(self):
        """保存提示词（根据模式自动判断是新建还是更新）"""
        name = self.prompt_name_edit.text().strip()
        hotkey = self.hotkey_combo.currentData()
        content = self.prompt_content_edit.toPlainText().strip()

        # 验证必填字段
        if not name:
            ProtectedMessageBox.warning(self, "提示", "请输入提示词名称")
            self.prompt_name_edit.setFocus()
            return

        if not hotkey:
            ProtectedMessageBox.warning(self, "提示", "请选择快捷键")
            return

        if not content:
            ProtectedMessageBox.warning(self, "提示", "请输入提示词内容")
            self.prompt_content_edit.setFocus()
            return

        prompts = self.config_manager.get("prompts", [])

        new_prompt = {
            "name": name,
            "hotkey": hotkey,
            "content": content
        }

        if self._current_edit_index == -1:
            # 新建模式
            prompts.append(new_prompt)
            self.config_manager.set("prompts", prompts)
            self.log_manager.add_log(f"添加提示词: {name} ({hotkey})")
            ProtectedMessageBox.information(
                self, "成功",
                f"已添加提示词「{name}」\n\n"
                f"快捷键：{hotkey.upper()}\n"
                f"启动监听后，按 {hotkey.upper()} 即可发送此提示词"
            )
        else:
            # 编辑模式
            prompts[self._current_edit_index] = new_prompt
            self.config_manager.set("prompts", prompts)
            self.log_manager.add_log(f"更新提示词: {name} ({hotkey})")
            ProtectedMessageBox.information(self, "成功", f"已更新提示词「{name}」")

        self.load_prompts_list()

    def delete_prompt(self):
        """删除选中的提示词"""
        if self._current_edit_index < 0:
            ProtectedMessageBox.warning(self, "提示", "请先选择要删除的提示词")
            return

        prompts = self.config_manager.get("prompts", [])
        if self._current_edit_index < len(prompts):
            name = prompts[self._current_edit_index]['name']
            hotkey = prompts[self._current_edit_index]['hotkey']

            if ProtectedMessageBox.question(
                self, "确认删除",
                f"确定要删除提示词「{name}」吗？\n\n"
                f"快捷键 {hotkey.upper()} 将被释放，可用于新提示词。"
            ):
                prompts.pop(self._current_edit_index)
                self.config_manager.set("prompts", prompts)
                self.log_manager.add_log(f"删除提示词: {name}")
                ProtectedMessageBox.information(self, "成功", f"已删除提示词「{name}」")
                self.load_prompts_list()

    def update_char_count(self):
        """更新字符计数"""
        count = len(self.prompt_content_edit.toPlainText())
        self.char_count_label.setText(f"字符数: {count}")

    def show_hotkey_help(self):
        """显示快捷键说明"""
        prompts = self.config_manager.get("prompts", [])
        used_count = len(prompts)
        available_count = 9 - used_count

        help_text = f"""快捷键说明：

• 提示词快捷键固定为 Alt+1 到 Alt+9
• 每个提示词绑定一个快捷键，最多9个
• 当前已使用 {used_count} 个，剩余 {available_count} 个可用

使用方法：
1. 点击"启动"开始监听
2. 按 Alt+数字 直接发送对应提示词
3. 按 Alt+Z 发送当前选中的提示词

系统控制快捷键（不可更改）：
• Alt+Z: 发送当前提示词
• Alt+Q: 显示/隐藏浮窗
• Alt+W: 截图
• Alt+V: 清空截图历史
• Alt+S: 切换AI服务商
• Alt+↑/↓: 滚动浮窗"""

        ProtectedMessageBox.information(self, "快捷键说明", help_text)
