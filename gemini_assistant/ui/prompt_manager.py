"""
提示词管理组件
提供提示词的增删改查功能
"""

from PyQt6 import QtCore, QtWidgets
from ..core.config_manager import ConfigManager
from ..core.log_manager import LogManager


class PromptManagerWidget(QtWidgets.QWidget):
    """提示词管理界面组件"""

    def __init__(self, config_manager: ConfigManager, log_manager: LogManager):
        super().__init__()
        self.config_manager = config_manager
        self.log_manager = log_manager
        self.setup_ui()
        self.load_prompts_list()



    def setup_ui(self):
        """设置用户界面"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        editor_card = QtWidgets.QFrame()
        editor_card.setProperty("class", "settings-card")
        editor_layout = QtWidgets.QVBoxLayout(editor_card)
        editor_layout.setContentsMargins(14, 12, 14, 12)
        editor_layout.setSpacing(10)

        header_row = QtWidgets.QHBoxLayout()
        editor_header = QtWidgets.QLabel("✏️ 编辑提示词")
        editor_header.setProperty("class", "card-header")
        header_row.addWidget(editor_header)
        header_row.addStretch()

        self.prompts_combo = QtWidgets.QComboBox()
        self.prompts_combo.setEditable(True)
        self.prompts_combo.setPlaceholderText("🔍 搜索或选择提示词...")
        self.prompts_combo.currentIndexChanged.connect(self.on_prompt_selected)
        self.prompts_combo.setMinimumHeight(32)
        self.prompts_combo.setFixedWidth(260)
        header_row.addWidget(self.prompts_combo)

        refresh_btn = QtWidgets.QPushButton("刷新列表")
        refresh_btn.setProperty("class", "secondary")
        refresh_btn.setToolTip("刷新提示词列表")
        refresh_btn.setMinimumWidth(80)
        refresh_btn.setFixedHeight(28)
        refresh_btn.clicked.connect(self.load_prompts_list)
        header_row.addWidget(refresh_btn)

        editor_layout.addLayout(header_row)

        form_layout = QtWidgets.QFormLayout()
        form_layout.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        form_layout.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(8)

        self.prompt_name_edit = QtWidgets.QLineEdit()
        self.prompt_name_edit.setPlaceholderText("例如: 代码实现助手")
        form_layout.addRow("提示词名称", self.prompt_name_edit)

        self.prompt_hotkey_edit = QtWidgets.QLineEdit()
        self.prompt_hotkey_edit.setPlaceholderText("例如: alt+1")

        hotkey_row = QtWidgets.QHBoxLayout()
        hotkey_row.setContentsMargins(0, 0, 0, 0)
        hotkey_row.setSpacing(6)
        hotkey_row.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
        hotkey_row.addWidget(self.prompt_hotkey_edit)

        self.hotkey_help_btn = QtWidgets.QPushButton("快捷键说明")
        self.hotkey_help_btn.setProperty("class", "secondary")
        self.hotkey_help_btn.setMinimumWidth(80)
        self.hotkey_help_btn.setFixedHeight(28)
        self.hotkey_help_btn.setToolTip("快捷键说明")
        self.hotkey_help_btn.clicked.connect(self.show_hotkey_help)
        hotkey_row.addWidget(self.hotkey_help_btn)

        form_layout.addRow("快捷键", hotkey_row)

        self.prompt_content_edit = QtWidgets.QPlainTextEdit()
        self.prompt_content_edit.setPlaceholderText("请输入详细的提示词内容...")
        self.prompt_content_edit.setMinimumHeight(160)
        self.prompt_content_edit.textChanged.connect(self.update_char_count)
        form_layout.addRow("提示词内容", self.prompt_content_edit)

        editor_layout.addLayout(form_layout)

        self.char_count_label = QtWidgets.QLabel("字符数: 0")
        self.char_count_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        editor_layout.addWidget(self.char_count_label)

        button_row = QtWidgets.QHBoxLayout()
        button_row.setSpacing(10)

        self.add_btn = QtWidgets.QPushButton("＋ 添加")
        self.add_btn.setProperty("class", "success")
        self.add_btn.clicked.connect(self.add_prompt)
        button_row.addWidget(self.add_btn)

        self.update_btn = QtWidgets.QPushButton("✏️ 更新")
        self.update_btn.setProperty("class", "secondary")
        self.update_btn.clicked.connect(self.update_prompt)
        button_row.addWidget(self.update_btn)

        self.delete_btn = QtWidgets.QPushButton("🗑️ 删除")
        self.delete_btn.setProperty("class", "danger")
        self.delete_btn.clicked.connect(self.delete_prompt)
        button_row.addWidget(self.delete_btn)

        self.clear_btn = QtWidgets.QPushButton("🧹 清空")
        self.clear_btn.setProperty("class", "secondary")
        self.clear_btn.clicked.connect(self.clear_prompt_fields)
        button_row.addWidget(self.clear_btn)

        button_row.addStretch()
        editor_layout.addLayout(button_row)

        layout.addWidget(editor_card)

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

    def on_prompt_selected(self, index):
        """选择提示词时的处理"""
        if index >= 0:
            prompt = self.prompts_combo.itemData(index)
            if prompt:
                self.prompt_name_edit.setText(prompt['name'])
                self.prompt_hotkey_edit.setText(prompt['hotkey'])
                self.prompt_content_edit.setPlainText(prompt['content'])

    def add_prompt(self):
        """添加新提示词"""
        name = self.prompt_name_edit.text().strip()
        hotkey = self.prompt_hotkey_edit.text().strip()
        content = self.prompt_content_edit.toPlainText().strip()

        if not all([name, hotkey, content]):
            QtWidgets.QMessageBox.warning(self, "警告", "请填写完整信息")
            return

        prompts = self.config_manager.get("prompts", [])

        # 检查快捷键是否重复
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

        # 检查快捷键是否与其他提示词重复
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
        help_text = """
快捷键格式说明：

• 单个键：a, b, c, 1, 2, 3
• 修饰键组合：
  - ctrl+a
  - alt+b
  - shift+c
  - ctrl+shift+d
• 功能键：f1, f2, ..., f12
• 特殊键：space, enter, tab, esc
• 方向键：up, down, left, right

示例：
• alt+1
• ctrl+shift+a
• f5
• ctrl+space
        """
        QtWidgets.QMessageBox.information(self, "快捷键格式帮助", help_text.strip())
