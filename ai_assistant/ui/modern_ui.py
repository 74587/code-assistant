"""
Modern UI Components - 专业级现代化界面组件
提供商业级应用的视觉体验（参考QQ/微信客户端风格）
"""

from __future__ import annotations
from typing import Optional, Callable, List, Dict, Any
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, pyqtProperty

# ═══════════════════════════════════════════════════════════════════════════════
# 设计系统常量
# ═══════════════════════════════════════════════════════════════════════════════

class DesignSystem:
    """设计系统 - 统一的视觉语言"""

    # 颜色系统 - 更加柔和、专业
    class Colors:
        # 背景色 - 深色主题，类似QQ/微信深色模式
        BG_PRIMARY = "#1e1e1e"       # 主背景（内容区域）
        BG_SECONDARY = "#252525"     # 侧边栏背景
        BG_TERTIARY = "#2f2f2f"      # 输入框背景
        BG_CARD = "#282828"          # 卡片背景
        BG_ELEVATED = "#353535"      # 悬浮/hover背景
        BG_HOVER = "#3d3d3d"         # hover状态
        BG_INPUT = "#232323"         # 输入框背景 - 稍深于卡片，提供视觉区分

        # 边框色 - 增加可见度
        BORDER_DEFAULT = "rgba(255, 255, 255, 0.12)"   # 稍亮的边框
        BORDER_HOVER = "rgba(255, 255, 255, 0.20)"
        BORDER_FOCUS = "rgba(7, 193, 96, 0.7)"

        # 品牌色 - 微信绿色风格
        PRIMARY = "#07c160"          # 主色调 - 微信绿
        PRIMARY_HOVER = "#06ad56"
        PRIMARY_LIGHT = "rgba(7, 193, 96, 0.12)"
        PRIMARY_DARK = "#059048"

        ACCENT = "#1890ff"           # 强调色 - 蓝色
        ACCENT_LIGHT = "rgba(24, 144, 255, 0.12)"

        SUCCESS = "#07c160"          # 成功
        SUCCESS_LIGHT = "rgba(7, 193, 96, 0.12)"

        WARNING = "#faad14"          # 警告
        WARNING_LIGHT = "rgba(250, 173, 20, 0.12)"

        DANGER = "#ff4d4f"           # 危险
        DANGER_LIGHT = "rgba(255, 77, 79, 0.12)"

        # 文字色
        TEXT_PRIMARY = "#e8e8e8"
        TEXT_SECONDARY = "rgba(232, 232, 232, 0.65)"
        TEXT_TERTIARY = "rgba(232, 232, 232, 0.45)"
        TEXT_DISABLED = "rgba(232, 232, 232, 0.25)"

    # 间距系统
    class Spacing:
        XS = 4
        SM = 8
        MD = 12
        LG = 16
        XL = 24
        XXL = 32
        XXXL = 48

    # 圆角系统
    class Radius:
        XS = 4
        SM = 6
        MD = 8
        LG = 12
        XL = 16
        FULL = 9999

    # 字体系统
    class Typography:
        FONT_FAMILY = "Microsoft YaHei UI, Segoe UI, SF Pro Display, -apple-system, sans-serif"

        # 字号
        SIZE_XS = 11
        SIZE_SM = 12
        SIZE_MD = 13
        SIZE_LG = 14
        SIZE_XL = 16
        SIZE_XXL = 18
        SIZE_XXXL = 24

        # 字重
        WEIGHT_NORMAL = 400
        WEIGHT_MEDIUM = 500
        WEIGHT_SEMIBOLD = 600
        WEIGHT_BOLD = 700

    # 动画时长
    class Animation:
        FAST = 150
        NORMAL = 200
        SLOW = 300


# ═══════════════════════════════════════════════════════════════════════════════
# 侧边栏导航
# ═══════════════════════════════════════════════════════════════════════════════

class SidebarItem(QtWidgets.QPushButton):
    """侧边栏导航项 - 带动画效果"""

    def __init__(self, icon: str, text: str, parent=None):
        super().__init__(parent)
        self._icon = icon
        self._text = text
        self.setText(f" {icon}  {text}")
        self.setCheckable(True)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(40)  # 减少高度

        # 动画
        self._bg_opacity = 0.0
        self._animation = QPropertyAnimation(self, b"bgOpacity")
        self._animation.setDuration(DesignSystem.Animation.FAST)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._update_style()

    def get_bg_opacity(self):
        return self._bg_opacity

    def set_bg_opacity(self, value):
        self._bg_opacity = value
        self._update_style()

    bgOpacity = pyqtProperty(float, get_bg_opacity, set_bg_opacity)

    def enterEvent(self, event):
        if not self.isChecked():
            self._animation.stop()
            self._animation.setStartValue(self._bg_opacity)
            self._animation.setEndValue(1.0)
            self._animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.isChecked():
            self._animation.stop()
            self._animation.setStartValue(self._bg_opacity)
            self._animation.setEndValue(0.0)
            self._animation.start()
        super().leaveEvent(event)

    def _update_style(self):
        if self.isChecked():
            bg = DesignSystem.Colors.PRIMARY_LIGHT
            text_color = DesignSystem.Colors.PRIMARY
            font_weight = DesignSystem.Typography.WEIGHT_SEMIBOLD
            border_left = f"3px solid {DesignSystem.Colors.PRIMARY}"
        else:
            # 根据动画值计算背景透明度
            alpha = int(self._bg_opacity * 255 * 0.08)
            bg = f"rgba(255, 255, 255, {alpha/255:.3f})"
            text_color = DesignSystem.Colors.TEXT_SECONDARY if self._bg_opacity < 0.5 else DesignSystem.Colors.TEXT_PRIMARY
            font_weight = DesignSystem.Typography.WEIGHT_MEDIUM
            border_left = "3px solid transparent"

        self.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                border: none;
                border-left: {border_left};
                border-radius: 0;
                color: {text_color};
                font-size: {DesignSystem.Typography.SIZE_MD}px;
                font-weight: {font_weight};
                text-align: left;
                padding-left: 20px;
            }}
        """)

    def setChecked(self, checked):
        super().setChecked(checked)
        self._bg_opacity = 1.0 if checked else 0.0
        self._update_style()


class Sidebar(QtWidgets.QFrame):
    """现代化侧边栏 - 类似QQ/微信风格"""

    page_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(180)  # 减少侧边栏宽度
        self.setObjectName("sidebar")
        self._items: List[SidebarItem] = []
        self._button_group = QtWidgets.QButtonGroup(self)
        self._button_group.setExclusive(True)

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo 区域
        self.logo_container = QtWidgets.QWidget()
        self.logo_container.setFixedHeight(56)  # 减少高度
        logo_layout = QtWidgets.QHBoxLayout(self.logo_container)
        logo_layout.setContentsMargins(16, 0, 16, 0)
        logo_layout.setSpacing(10)

        # Logo 图标
        logo_icon = QtWidgets.QLabel("🤖")
        logo_icon.setStyleSheet(f"font-size: 20px;")
        logo_layout.addWidget(logo_icon)

        # 标题
        title_container = QtWidgets.QWidget()
        title_layout = QtWidgets.QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)

        self.logo_label = QtWidgets.QLabel("AI Assistant")
        self.logo_label.setStyleSheet(f"""
            font-size: {DesignSystem.Typography.SIZE_MD}px;
            font-weight: {DesignSystem.Typography.WEIGHT_BOLD};
            color: {DesignSystem.Colors.TEXT_PRIMARY};
        """)

        self.version_label = QtWidgets.QLabel("v2.0.0")
        self.version_label.setStyleSheet(f"""
            font-size: 10px;
            color: {DesignSystem.Colors.TEXT_TERTIARY};
        """)

        title_layout.addWidget(self.logo_label)
        title_layout.addWidget(self.version_label)
        logo_layout.addWidget(title_container)
        logo_layout.addStretch()

        layout.addWidget(self.logo_container)

        # 分隔线
        separator = QtWidgets.QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background: {DesignSystem.Colors.BORDER_DEFAULT};")
        layout.addWidget(separator)

        # 导航项容器
        self.nav_container = QtWidgets.QWidget()
        self.nav_layout = QtWidgets.QVBoxLayout(self.nav_container)
        self.nav_layout.setContentsMargins(0, 8, 0, 8)
        self.nav_layout.setSpacing(2)
        layout.addWidget(self.nav_container)

        layout.addStretch()

    def _apply_style(self):
        self.setStyleSheet(f"""
            #sidebar {{
                background: {DesignSystem.Colors.BG_SECONDARY};
                border-right: 1px solid {DesignSystem.Colors.BORDER_DEFAULT};
            }}
        """)

    def add_item(self, icon: str, text: str) -> SidebarItem:
        item = SidebarItem(icon, text, self)
        self._button_group.addButton(item, len(self._items))
        self._items.append(item)
        self.nav_layout.addWidget(item)

        item.clicked.connect(lambda: self._on_item_clicked(self._items.index(item)))

        if len(self._items) == 1:
            item.setChecked(True)

        return item

    def _on_item_clicked(self, index: int):
        for i, item in enumerate(self._items):
            item.setChecked(i == index)
        self.page_changed.emit(index)

    def set_current_index(self, index: int):
        if 0 <= index < len(self._items):
            self._on_item_clicked(index)



# ═══════════════════════════════════════════════════════════════════════════════
# 页面容器
# ═══════════════════════════════════════════════════════════════════════════════

class PageContainer(QtWidgets.QWidget):
    """页面容器 - 带标题和滚动"""

    def __init__(self, title: str = "", subtitle: str = "", parent=None):
        super().__init__(parent)
        self._setup_ui(title, subtitle)

    def _setup_ui(self, title: str, subtitle: str):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)  # 减少边距
        layout.setSpacing(0)

        # 页面标题区域
        if title:
            header = QtWidgets.QWidget()
            header_layout = QtWidgets.QVBoxLayout(header)
            header_layout.setContentsMargins(0, 0, 0, 12)  # 减少标题底部间距
            header_layout.setSpacing(2)

            title_label = QtWidgets.QLabel(title)
            title_label.setStyleSheet(f"""
                font-size: {DesignSystem.Typography.SIZE_XL}px;
                font-weight: {DesignSystem.Typography.WEIGHT_BOLD};
                color: {DesignSystem.Colors.TEXT_PRIMARY};
            """)
            header_layout.addWidget(title_label)

            if subtitle:
                subtitle_label = QtWidgets.QLabel(subtitle)
                subtitle_label.setStyleSheet(f"""
                    font-size: {DesignSystem.Typography.SIZE_XS}px;
                    color: {DesignSystem.Colors.TEXT_TERTIARY};
                """)
                header_layout.addWidget(subtitle_label)

            layout.addWidget(header)

        # 滚动区域
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 4px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.25);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)

        self.content_widget = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 8, 0)
        self.content_layout.setSpacing(12)  # 减少卡片间距

        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll, 1)

    def add_widget(self, widget: QtWidgets.QWidget):
        self.content_layout.addWidget(widget)

    def add_stretch(self):
        self.content_layout.addStretch()


# ═══════════════════════════════════════════════════════════════════════════════
# 卡片组件
# ═══════════════════════════════════════════════════════════════════════════════

class Card(QtWidgets.QFrame):
    """现代化卡片组件 - 带阴影和hover效果"""

    def __init__(self, title: str = "", description: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._hover = False
        self._setup_ui(title, description)
        self._apply_style()
        self._setup_shadow()

    def _setup_ui(self, title: str, description: str):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)  # 减少卡片内边距
        layout.setSpacing(10)  # 减少卡片内部间距

        # 标题区域
        if title:
            header = QtWidgets.QWidget()
            header_layout = QtWidgets.QVBoxLayout(header)
            header_layout.setContentsMargins(0, 0, 0, 0)
            header_layout.setSpacing(2)

            title_label = QtWidgets.QLabel(title)
            title_label.setStyleSheet(f"""
                font-size: {DesignSystem.Typography.SIZE_MD}px;
                font-weight: {DesignSystem.Typography.WEIGHT_SEMIBOLD};
                color: {DesignSystem.Colors.TEXT_PRIMARY};
            """)
            header_layout.addWidget(title_label)

            if description:
                desc_label = QtWidgets.QLabel(description)
                desc_label.setWordWrap(True)
                desc_label.setStyleSheet(f"""
                    font-size: {DesignSystem.Typography.SIZE_XS}px;
                    color: {DesignSystem.Colors.TEXT_TERTIARY};
                """)
                header_layout.addWidget(desc_label)

            layout.addWidget(header)

        # 内容区域
        self.content_widget = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)  # 减少内容间距
        layout.addWidget(self.content_widget)

    def _setup_shadow(self):
        """添加微妙的阴影效果"""
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QtGui.QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)
        self._shadow = shadow

    def _apply_style(self):
        # 使用更微妙的边框，减少对比度
        border_color = "rgba(255, 255, 255, 0.06)" if not self._hover else "rgba(255, 255, 255, 0.1)"
        bg = DesignSystem.Colors.BG_ELEVATED if self._hover else DesignSystem.Colors.BG_CARD
        self.setStyleSheet(f"""
            #card {{
                background: {bg};
                border: 1px solid {border_color};
                border-radius: {DesignSystem.Radius.LG}px;
            }}
        """)
        # 更新阴影强度
        if hasattr(self, '_shadow'):
            self._shadow.setColor(QtGui.QColor(0, 0, 0, 60 if self._hover else 40))

    def enterEvent(self, event):
        self._hover = True
        self._apply_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self._apply_style()
        super().leaveEvent(event)

    def add_widget(self, widget: QtWidgets.QWidget):
        self.content_layout.addWidget(widget)


# ═══════════════════════════════════════════════════════════════════════════════
# 表单组件
# ═══════════════════════════════════════════════════════════════════════════════

class FormRow(QtWidgets.QWidget):
    """表单行 - 标签 + 输入框"""

    def __init__(self, label: str, widget: QtWidgets.QWidget, helper: str = "", parent=None):
        super().__init__(parent)
        self._setup_ui(label, widget, helper)

    def _setup_ui(self, label: str, widget: QtWidgets.QWidget, helper: str):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)  # 减少标签和内容间距

        # 标签 - 宽度增加到100以适应中文
        label_widget = QtWidgets.QLabel(label)
        label_widget.setFixedWidth(90)  # 减小标签宽度
        label_widget.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignTop)
        label_widget.setStyleSheet(f"""
            font-size: {DesignSystem.Typography.SIZE_SM}px;
            color: {DesignSystem.Colors.TEXT_SECONDARY};
            padding-top: 6px;
        """)
        layout.addWidget(label_widget)

        # 输入区域
        field_container = QtWidgets.QWidget()
        field_layout = QtWidgets.QVBoxLayout(field_container)
        field_layout.setContentsMargins(0, 0, 0, 0)
        field_layout.setSpacing(4)
        field_layout.addWidget(widget)

        if helper:
            helper_label = QtWidgets.QLabel(helper)
            helper_label.setWordWrap(True)
            helper_label.setStyleSheet(f"""
                font-size: {DesignSystem.Typography.SIZE_XS}px;
                color: {DesignSystem.Colors.TEXT_TERTIARY};
            """)
            field_layout.addWidget(helper_label)

        layout.addWidget(field_container, 1)


class ModernLineEdit(QtWidgets.QLineEdit):
    """现代化输入框 - 带焦点动画"""

    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(32)  # 减少高度
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
            QLineEdit {{
                background: {bg};
                border: 1px solid {border_color};
                border-radius: {DesignSystem.Radius.SM}px;
                padding: 0 12px;
                font-size: {DesignSystem.Typography.SIZE_MD}px;
                color: {DesignSystem.Colors.TEXT_PRIMARY};
                selection-background-color: {DesignSystem.Colors.PRIMARY};
            }}
            QLineEdit::placeholder {{
                color: {DesignSystem.Colors.TEXT_DISABLED};
            }}
        """)


class ModernComboBox(QtWidgets.QComboBox):
    """现代化下拉框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(32)
        self._apply_style()

    def _apply_style(self):
        # 使用unicode字符作为下拉箭头，避免CSS border三角形在Windows上的问题
        self.setStyleSheet(f"""
            QComboBox {{
                background: {DesignSystem.Colors.BG_INPUT};
                border: 1px solid {DesignSystem.Colors.BORDER_DEFAULT};
                border-radius: {DesignSystem.Radius.SM}px;
                padding: 0 28px 0 12px;
                font-size: {DesignSystem.Typography.SIZE_MD}px;
                color: {DesignSystem.Colors.TEXT_PRIMARY};
            }}
            QComboBox:hover {{
                border-color: {DesignSystem.Colors.BORDER_HOVER};
                background: {DesignSystem.Colors.BG_ELEVATED};
            }}
            QComboBox:focus {{
                border-color: {DesignSystem.Colors.PRIMARY};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 28px;
                border: none;
                background: transparent;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
                width: 8px;
                height: 8px;
            }}
            QComboBox QAbstractItemView {{
                background: {DesignSystem.Colors.BG_ELEVATED};
                border: 1px solid {DesignSystem.Colors.BORDER_HOVER};
                border-radius: {DesignSystem.Radius.SM}px;
                padding: 4px;
                selection-background-color: {DesignSystem.Colors.PRIMARY_LIGHT};
                selection-color: {DesignSystem.Colors.TEXT_PRIMARY};
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                height: 32px;
                padding-left: 12px;
                border-radius: {DesignSystem.Radius.XS}px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background: {DesignSystem.Colors.BG_HOVER};
            }}
        """)

    def paintEvent(self, event):
        """自定义绘制下拉箭头"""
        super().paintEvent(event)
        # 绘制下拉箭头 ▼
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # 箭头位置
        arrow_x = self.width() - 18
        arrow_y = self.height() // 2

        # 绘制三角形箭头
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor(DesignSystem.Colors.TEXT_SECONDARY))

        # 三角形顶点
        points = [
            QtCore.QPointF(arrow_x - 4, arrow_y - 2),
            QtCore.QPointF(arrow_x + 4, arrow_y - 2),
            QtCore.QPointF(arrow_x, arrow_y + 3),
        ]
        painter.drawPolygon(points)
        painter.end()


class ModernCheckBox(QtWidgets.QCheckBox):
    """现代化复选框"""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QCheckBox {{
                font-size: {DesignSystem.Typography.SIZE_MD}px;
                color: {DesignSystem.Colors.TEXT_PRIMARY};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid {DesignSystem.Colors.BORDER_HOVER};
                background: transparent;
            }}
            QCheckBox::indicator:hover {{
                border-color: {DesignSystem.Colors.PRIMARY};
                background: {DesignSystem.Colors.PRIMARY_LIGHT};
            }}
            QCheckBox::indicator:checked {{
                background: {DesignSystem.Colors.PRIMARY};
                border-color: {DesignSystem.Colors.PRIMARY};
            }}
            QCheckBox::indicator:checked:hover {{
                background: {DesignSystem.Colors.PRIMARY_HOVER};
                border-color: {DesignSystem.Colors.PRIMARY_HOVER};
            }}
        """)


class ModernRadioButton(QtWidgets.QRadioButton):
    """现代化单选按钮 - 胶囊样式（完全自绘，无原生indicator）"""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(28)
        self.setMinimumWidth(70)
        self._apply_style()
        # 连接状态变化信号以更新样式
        self.toggled.connect(self._apply_style)

    def _apply_style(self):
        # 根据选中状态设置不同样式
        if self.isChecked():
            self.setStyleSheet(f"""
                QRadioButton {{
                    font-size: {DesignSystem.Typography.SIZE_SM}px;
                    color: #ffffff;
                    padding: 4px 14px;
                    background: {DesignSystem.Colors.PRIMARY};
                    border: 1px solid {DesignSystem.Colors.PRIMARY};
                    border-radius: 14px;
                    font-weight: {DesignSystem.Typography.WEIGHT_MEDIUM};
                }}
                QRadioButton::indicator {{
                    width: 0;
                    height: 0;
                    border: none;
                    background: none;
                    image: none;
                }}
                QRadioButton:hover {{
                    background: {DesignSystem.Colors.PRIMARY_HOVER};
                    border-color: {DesignSystem.Colors.PRIMARY_HOVER};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QRadioButton {{
                    font-size: {DesignSystem.Typography.SIZE_SM}px;
                    color: {DesignSystem.Colors.TEXT_SECONDARY};
                    padding: 4px 14px;
                    background: transparent;
                    border: 1px solid {DesignSystem.Colors.BORDER_DEFAULT};
                    border-radius: 14px;
                }}
                QRadioButton::indicator {{
                    width: 0;
                    height: 0;
                    border: none;
                    background: none;
                    image: none;
                }}
                QRadioButton:hover {{
                    background: {DesignSystem.Colors.BG_TERTIARY};
                    border-color: {DesignSystem.Colors.BORDER_HOVER};
                    color: {DesignSystem.Colors.TEXT_PRIMARY};
                }}
            """)


# ═══════════════════════════════════════════════════════════════════════════════
# 按钮组件
# ═══════════════════════════════════════════════════════════════════════════════

class ModernButton(QtWidgets.QPushButton):
    """现代化按钮 - 带按压效果"""

    def __init__(self, text: str, variant: str = "primary", parent=None):
        super().__init__(text, parent)
        self.variant = variant
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(32)  # 减少高度
        self._pressed = False
        self._apply_style()

    def mousePressEvent(self, event):
        self._pressed = True
        self._apply_style()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._pressed = False
        self._apply_style()
        super().mouseReleaseEvent(event)

    def _apply_style(self):
        variants = {
            "primary": {
                "bg": DesignSystem.Colors.PRIMARY,
                "bg_hover": DesignSystem.Colors.PRIMARY_HOVER,
                "bg_pressed": DesignSystem.Colors.PRIMARY_DARK,
                "text": "#ffffff",
            },
            "success": {
                "bg": DesignSystem.Colors.SUCCESS,
                "bg_hover": "#06ad56",
                "bg_pressed": "#059048",
                "text": "#ffffff",
            },
            "danger": {
                "bg": DesignSystem.Colors.DANGER,
                "bg_hover": "#ff7875",
                "bg_pressed": "#d9363e",
                "text": "#ffffff",
            },
            "secondary": {
                "bg": DesignSystem.Colors.BG_TERTIARY,
                "bg_hover": DesignSystem.Colors.BG_HOVER,
                "bg_pressed": DesignSystem.Colors.BG_ELEVATED,
                "text": DesignSystem.Colors.TEXT_PRIMARY,
            },
            "ghost": {
                "bg": "transparent",
                "bg_hover": DesignSystem.Colors.BG_TERTIARY,
                "bg_pressed": DesignSystem.Colors.BG_ELEVATED,
                "text": DesignSystem.Colors.TEXT_SECONDARY,
            },
        }

        v = variants.get(self.variant, variants["primary"])
        bg = v["bg_pressed"] if self._pressed else v["bg"]

        self.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                border: none;
                border-radius: {DesignSystem.Radius.SM}px;
                padding: 0 16px;
                font-size: {DesignSystem.Typography.SIZE_SM}px;
                font-weight: {DesignSystem.Typography.WEIGHT_MEDIUM};
                color: {v["text"]};
            }}
            QPushButton:hover {{
                background: {v["bg_hover"]};
            }}
            QPushButton:disabled {{
                background: {DesignSystem.Colors.BG_TERTIARY};
                color: {DesignSystem.Colors.TEXT_DISABLED};
            }}
        """)


class IconButton(QtWidgets.QPushButton):
    """图标按钮"""

    def __init__(self, icon: str, tooltip: str = "", parent=None):
        super().__init__(icon, parent)
        self.setToolTip(tooltip)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(36, 36)
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background: {DesignSystem.Colors.BG_TERTIARY};
                border: 1px solid {DesignSystem.Colors.BORDER_DEFAULT};
                border-radius: {DesignSystem.Radius.SM}px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background: {DesignSystem.Colors.BG_HOVER};
                border-color: {DesignSystem.Colors.BORDER_HOVER};
            }}
            QPushButton:pressed {{
                background: {DesignSystem.Colors.BG_ELEVATED};
            }}
        """)


# ═══════════════════════════════════════════════════════════════════════════════
# 控制栏组件
# ═══════════════════════════════════════════════════════════════════════════════

class ControlBar(QtWidgets.QFrame):
    """底部控制栏 - 简洁风格"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(52)  # 减少高度
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(12)

        # 左侧状态
        self.status_container = QtWidgets.QWidget()
        status_layout = QtWidgets.QHBoxLayout(self.status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)

        self.status_indicator = QtWidgets.QFrame()
        self.status_indicator.setFixedSize(8, 8)
        self.status_indicator.setStyleSheet(f"""
            background: {DesignSystem.Colors.DANGER};
            border-radius: 4px;
        """)

        self.status_label = QtWidgets.QLabel("未启动")
        self.status_label.setStyleSheet(f"""
            font-size: {DesignSystem.Typography.SIZE_SM}px;
            color: {DesignSystem.Colors.TEXT_SECONDARY};
        """)

        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(self.status_label)
        layout.addWidget(self.status_container)

        layout.addStretch()

        # 右侧按钮
        self.button_container = QtWidgets.QWidget()
        self.button_layout = QtWidgets.QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(12)
        layout.addWidget(self.button_container)

    def _apply_style(self):
        self.setStyleSheet(f"""
            ControlBar {{
                background: {DesignSystem.Colors.BG_SECONDARY};
                border-top: 1px solid {DesignSystem.Colors.BORDER_DEFAULT};
            }}
        """)

    def update_status(self, text: str, running: bool = False):
        self.status_label.setText(text)
        color = DesignSystem.Colors.SUCCESS if running else DesignSystem.Colors.TEXT_SECONDARY
        dot_color = DesignSystem.Colors.SUCCESS if running else DesignSystem.Colors.DANGER
        self.status_label.setStyleSheet(f"""
            font-size: {DesignSystem.Typography.SIZE_MD}px;
            color: {color};
        """)
        self.status_indicator.setStyleSheet(f"""
            background: {dot_color};
            border-radius: 4px;
        """)

    def add_button(self, button: QtWidgets.QPushButton):
        self.button_layout.addWidget(button)


# ═══════════════════════════════════════════════════════════════════════════════
# 主窗口布局
# ═══════════════════════════════════════════════════════════════════════════════

class MainWindowLayout(QtWidgets.QWidget):
    """主窗口布局 - 侧边栏 + 内容区 + 控制栏"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 主体区域 (侧边栏 + 内容)
        body = QtWidgets.QWidget()
        body_layout = QtWidgets.QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # 侧边栏
        self.sidebar = Sidebar()
        body_layout.addWidget(self.sidebar)

        # 内容区域
        self.content_area = QtWidgets.QWidget()
        self.content_area.setStyleSheet(f"background: {DesignSystem.Colors.BG_PRIMARY};")
        self.content_layout = QtWidgets.QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # 页面堆栈
        self.page_stack = QtWidgets.QStackedWidget()
        self.content_layout.addWidget(self.page_stack)

        body_layout.addWidget(self.content_area, 1)
        layout.addWidget(body, 1)

        # 底部控制栏
        self.control_bar = ControlBar()
        layout.addWidget(self.control_bar)

        # 连接信号
        self.sidebar.page_changed.connect(self.page_stack.setCurrentIndex)

    def add_page(self, icon: str, title: str, page: QtWidgets.QWidget) -> int:
        self.sidebar.add_item(icon, title)
        self.page_stack.addWidget(page)
        return self.page_stack.count() - 1

    def update_status(self, text: str, running: bool = False):
        # 只在底部控制栏显示状态（移除了侧边栏状态以避免重复）
        self.control_bar.update_status(text, running)


# ═══════════════════════════════════════════════════════════════════════════════
# 受保护的消息对话框 - 防截屏
# ═══════════════════════════════════════════════════════════════════════════════

class ProtectedMessageBox(QtWidgets.QDialog):
    """
    受保护的消息对话框 - 防止被截屏/录屏捕获
    用于替代 QMessageBox，确保敏感信息不会泄露
    """

    # 消息类型
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    QUESTION = "question"

    def __init__(self, parent=None, msg_type: str = INFO):
        super().__init__(parent)
        self.msg_type = msg_type
        self._result = False
        self._setup_window()
        self._setup_ui()

    def _setup_window(self):
        """设置窗口属性"""
        self.setWindowFlags(
            QtCore.Qt.WindowType.Dialog |
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setMinimumWidth(360)
        self.setMaximumWidth(480)

        # 应用截屏保护
        self._apply_capture_protection()

    def _apply_capture_protection(self):
        """应用防截屏保护"""
        try:
            import ctypes
            hwnd = int(self.winId())
            WDA_EXCLUDEFROMCAPTURE = 0x11
            ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
        except Exception:
            pass  # 非Windows平台静默处理

    def _setup_ui(self):
        """构建UI"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 主容器 - 带圆角和阴影
        container = QtWidgets.QFrame()
        container.setObjectName("msgContainer")
        container.setStyleSheet(f"""
            #msgContainer {{
                background: {DesignSystem.Colors.BG_CARD};
                border: 1px solid {DesignSystem.Colors.BORDER_DEFAULT};
                border-radius: {DesignSystem.Radius.LG}px;
            }}
        """)

        # 添加阴影
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QtGui.QColor(0, 0, 0, 80))
        container.setGraphicsEffect(shadow)

        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setContentsMargins(24, 20, 24, 20)
        container_layout.setSpacing(16)

        # 图标和标题行
        header = QtWidgets.QHBoxLayout()
        header.setSpacing(12)

        # 图标
        icon_label = QtWidgets.QLabel()
        icon_label.setFixedSize(24, 24)
        icon_colors = {
            self.INFO: DesignSystem.Colors.ACCENT,
            self.WARNING: DesignSystem.Colors.WARNING,
            self.ERROR: DesignSystem.Colors.DANGER,
            self.QUESTION: DesignSystem.Colors.PRIMARY,
        }
        icon_texts = {
            self.INFO: "ℹ",
            self.WARNING: "⚠",
            self.ERROR: "✕",
            self.QUESTION: "?",
        }
        icon_label.setText(icon_texts.get(self.msg_type, "ℹ"))
        icon_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"""
            font-size: 18px;
            color: {icon_colors.get(self.msg_type, DesignSystem.Colors.ACCENT)};
        """)
        header.addWidget(icon_label)

        # 标题
        self.title_label = QtWidgets.QLabel()
        self.title_label.setStyleSheet(f"""
            font-size: {DesignSystem.Typography.SIZE_LG}px;
            font-weight: {DesignSystem.Typography.WEIGHT_SEMIBOLD};
            color: {DesignSystem.Colors.TEXT_PRIMARY};
        """)
        header.addWidget(self.title_label, 1)

        container_layout.addLayout(header)

        # 消息内容
        self.message_label = QtWidgets.QLabel()
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet(f"""
            font-size: {DesignSystem.Typography.SIZE_MD}px;
            color: {DesignSystem.Colors.TEXT_SECONDARY};
            line-height: 1.5;
        """)
        container_layout.addWidget(self.message_label)

        # 按钮区域
        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.setSpacing(12)
        self.button_layout.addStretch()
        container_layout.addLayout(self.button_layout)

        layout.addWidget(container)

    def setWindowTitle(self, title: str):
        """设置标题"""
        self.title_label.setText(title)

    def setText(self, text: str):
        """设置消息内容"""
        self.message_label.setText(text)

    def addButton(self, text: str, variant: str = "secondary", is_accept: bool = False):
        """添加按钮"""
        btn = ModernButton(text, variant)
        btn.setMinimumWidth(80)
        if is_accept:
            btn.clicked.connect(self.accept)
        else:
            btn.clicked.connect(self.reject)
        self.button_layout.addWidget(btn)
        return btn

    def showEvent(self, event):
        """显示时应用保护并居中"""
        super().showEvent(event)
        # 再次应用保护（确保生效）
        self._apply_capture_protection()
        # 居中显示
        if self.parent():
            parent_geo = self.parent().geometry()
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - self.height()) // 2
            self.move(x, y)

    @classmethod
    def information(cls, parent, title: str, message: str) -> bool:
        """显示信息对话框"""
        dialog = cls(parent, cls.INFO)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        dialog.addButton("确定", "primary", is_accept=True)
        return dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted

    @classmethod
    def warning(cls, parent, title: str, message: str) -> bool:
        """显示警告对话框"""
        dialog = cls(parent, cls.WARNING)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        dialog.addButton("确定", "primary", is_accept=True)
        return dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted

    @classmethod
    def critical(cls, parent, title: str, message: str) -> bool:
        """显示错误对话框"""
        dialog = cls(parent, cls.ERROR)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        dialog.addButton("确定", "danger", is_accept=True)
        return dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted

    @classmethod
    def question(cls, parent, title: str, message: str) -> bool:
        """显示询问对话框"""
        dialog = cls(parent, cls.QUESTION)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        dialog.addButton("取消", "secondary", is_accept=False)
        dialog.addButton("确定", "primary", is_accept=True)
        return dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted


# ═══════════════════════════════════════════════════════════════════════════════
# 导出
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    "DesignSystem",
    "Sidebar",
    "SidebarItem",
    "PageContainer",
    "Card",
    "FormRow",
    "ModernLineEdit",
    "ModernComboBox",
    "ModernCheckBox",
    "ModernRadioButton",
    "ModernButton",
    "IconButton",
    "ControlBar",
    "MainWindowLayout",
    "ProtectedMessageBox",
]
