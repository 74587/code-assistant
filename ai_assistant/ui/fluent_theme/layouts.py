"""Fluent UI helper components for the configuration window."""

from __future__ import annotations

from typing import Callable, Optional, Union

from PyQt6 import QtCore, QtGui, QtWidgets
from qfluentwidgets import BodyLabel, FluentIcon, IconWidget, SimpleCardWidget

IconArg = Union[FluentIcon, QtGui.QIcon, str, None]
ColorArg = Union[str, QtGui.QColor]

PRIMARY_COLOR = QtGui.QColor("#5E81F4")
ACCENT_COLOR = QtGui.QColor("#38BDF8")

CARD_MIN_WIDTH = 640
CARD_MAX_WIDTH = 880
CARD_SPACING = 28

FORM_LABEL_WIDTH = 180
FORM_HORIZONTAL_SPACING = 18
FORM_VERTICAL_SPACING = 18

TOP_BAR_MIN_HEIGHT = 72
STATUS_BAR_HEIGHT = 56

HELPER_LABEL_STYLE = (
    "color: rgba(226, 232, 240, 0.72);"
    "font-size: 12px;"
    "line-height: 1.35;"
)


def _as_qcolor(value: ColorArg) -> QtGui.QColor:
    if isinstance(value, QtGui.QColor):
        return QtGui.QColor(value)
    color = QtGui.QColor(value)
    if not color.isValid():
        raise ValueError(f"Invalid color value: {value}")
    return color


def _color_to_rgba(color: QtGui.QColor) -> str:
    return f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})"


def _coerce_qicon(icon: IconArg) -> Optional[QtGui.QIcon]:
    if icon is None:
        return None
    if isinstance(icon, QtGui.QIcon):
        return icon
    if isinstance(icon, FluentIcon):
        # qfluentwidgets exposes a helper to access the underlying QIcon
        icon_accessor = getattr(icon, "icon", None)
        if callable(icon_accessor):
            qicon = icon_accessor()
        else:
            qicon = getattr(icon, "value", None)
        if isinstance(qicon, QtGui.QIcon):
            return qicon
    if isinstance(icon, str):
        return QtGui.QIcon(icon)
    return None


def _create_icon_widget(icon: IconArg, *, size: int = 24, background_alpha: int = 68) -> Optional[IconWidget]:
    if icon is None:
        return None
    if isinstance(icon, FluentIcon):
        widget = IconWidget(icon)
    else:
        widget = IconWidget()
        qicon = _coerce_qicon(icon)
        if qicon is None:
            return None
        widget.setIcon(qicon)
    diameter = size + 12
    widget.setFixedSize(diameter, diameter)
    if hasattr(widget, 'setIconSize'):
        widget.setIconSize(QtCore.QSize(size, size))
    if hasattr(widget, 'setBorderRadius'):
        widget.setBorderRadius(diameter // 2)
    background = QtGui.QColor(PRIMARY_COLOR)
    background.setAlpha(background_alpha)
    if hasattr(widget, 'setBackgroundColor'):
        widget.setBackgroundColor(background)
    else:
        alpha = background.alphaF()
        widget.setStyleSheet(f"""background-color: rgba({background.red()}, {background.green()}, {background.blue()}, {alpha:.3f});
        border-radius: {diameter // 2}px;""")
    if hasattr(widget, 'setToolTipDuration'):
        widget.setToolTipDuration(0)
    return widget


def _clear_layout(layout: QtWidgets.QLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        child_layout = item.layout()
        if widget is not None:
            widget.deleteLater()
        if child_layout is not None:
            _clear_layout(child_layout)


class FluentTopBar(QtWidgets.QFrame):
    """Fluent style top shell with title, version and quick actions."""

    def __init__(
        self,
        title: str,
        *,
        subtitle: str = "",
        version: str = "",
        icon: IconArg = FluentIcon.ROBOT,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("fluentTopBar")
        self.setMinimumHeight(TOP_BAR_MIN_HEIGHT)
        self.setStyleSheet(
            """
            #fluentTopBar {
                background-color: rgba(15, 23, 42, 0.78);
                border: 1px solid rgba(148, 163, 184, 0.22);
                border-radius: 20px;
            }
            #fluentTopBar QLabel#titleLabel {
                color: #f8fafc;
                font-size: 18px;
                font-weight: 600;
            }
            #fluentTopBar QLabel#subtitleLabel {
                color: rgba(226, 232, 240, 0.82);
                font-size: 12px;
            }
            """
        )

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(16)

        icon_widget = _create_icon_widget(icon, size=24, background_alpha=64)
        if icon_widget:
            icon_widget.setFixedSize(48, 48)
            if hasattr(icon_widget, 'setIconSize'):
                icon_widget.setIconSize(QtCore.QSize(28, 28))
            layout.addWidget(icon_widget)

        text_container = QtWidgets.QWidget()
        text_layout = QtWidgets.QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)

        title_label = QtWidgets.QLabel(title)
        title_label.setObjectName("titleLabel")
        title_label.setFont(QtGui.QFont("Segoe UI", 18, QtGui.QFont.Weight.DemiBold))
        text_layout.addWidget(title_label)

        subtitle_parts = [part for part in (subtitle, version) if part]
        if subtitle_parts:
            subtitle_label = QtWidgets.QLabel(" · ".join(subtitle_parts))
            subtitle_label.setObjectName("subtitleLabel")
            subtitle_label.setFont(QtGui.QFont("Segoe UI", 11))
            subtitle_label.setWordWrap(True)
            text_layout.addWidget(subtitle_label)

        layout.addWidget(text_container, 1)

        self._actions_widget = QtWidgets.QWidget()
        self._actions_layout = QtWidgets.QHBoxLayout(self._actions_widget)
        self._actions_layout.setContentsMargins(0, 0, 0, 0)
        self._actions_layout.setSpacing(10)
        layout.addWidget(self._actions_widget, 0, QtCore.Qt.AlignmentFlag.AlignRight)

    def add_quick_action(
        self,
        text: str,
        slot: Callable[[], None],
        *,
        icon: IconArg = None,
    ) -> QtWidgets.QPushButton:
        button = QtWidgets.QPushButton(text)
        button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        button.setFixedHeight(34)
        button.setStyleSheet(
            """
            QPushButton {
                color: #e0e7ff;
                background-color: rgba(94, 129, 244, 0.18);
                border: 1px solid rgba(94, 129, 244, 0.32);
                border-radius: 17px;
                padding: 0 18px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(94, 129, 244, 0.28);
            }
            QPushButton:pressed {
                background-color: rgba(94, 129, 244, 0.38);
            }
            """
        )
        qicon = _coerce_qicon(icon)
        if qicon:
            button.setIcon(qicon)
            if hasattr(button, 'setIconSize'):
                button.setIconSize(QtCore.QSize(18, 18))
        button.clicked.connect(slot)
        self._actions_layout.addWidget(button)
        return button

    def clear_actions(self) -> None:
        _clear_layout(self._actions_layout)


class FluentStatusBar(QtWidgets.QFrame):
    """Bottom capsule-style status bar."""

    def __init__(
        self,
        text: str = "",
        *,
        color: ColorArg = "#f97316",
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("fluentStatusBar")
        self.setFixedHeight(STATUS_BAR_HEIGHT)
        self.setStyleSheet(
            """
            #fluentStatusBar {
                border-radius: 24px;
                border: 1px solid rgba(71, 85, 105, 0.55);
                background-color: rgba(15, 23, 42, 0.82);
            }
            #fluentStatusBar QLabel {
                color: #e2e8f0;
                font-weight: 600;
            }
            """
        )

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(12)

        self._indicator = QtWidgets.QFrame()
        self._indicator.setObjectName("statusIndicator")
        self._indicator.setFixedSize(12, 12)
        self._indicator.setStyleSheet(
            f"background-color: {_color_to_rgba(_as_qcolor(color))}; border-radius: 6px;"
        )
        layout.addWidget(self._indicator)

        self._label = QtWidgets.QLabel(text)
        layout.addWidget(self._label)

        layout.addStretch()

        self._trailing_widget = QtWidgets.QWidget()
        self._trailing_layout = QtWidgets.QHBoxLayout(self._trailing_widget)
        self._trailing_layout.setContentsMargins(0, 0, 0, 0)
        self._trailing_layout.setSpacing(10)
        layout.addWidget(self._trailing_widget)

    def update_status(self, text: str, *, color: ColorArg | None = None) -> None:
        self._label.setText(text)
        if color is not None:
            rgba = _color_to_rgba(_as_qcolor(color))
            self._indicator.setStyleSheet(f"background-color: {rgba}; border-radius: 6px;")

    def add_widget(self, widget: QtWidgets.QWidget) -> None:
        self._trailing_layout.addWidget(widget)

    def clear_trailing(self) -> None:
        _clear_layout(self._trailing_layout)


class SectionTitle(QtWidgets.QWidget):
    """Reusable title + description block used within cards."""

    def __init__(
        self,
        title: str,
        *,
        description: str = "",
        icon: IconArg = None,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("fluentSectionTitle")
        self.setStyleSheet(
            """
            #fluentSectionTitle QLabel#titleLabel {
                color: #f8fafc;
                font-size: 14px;
                font-weight: 600;
            }
            #fluentSectionTitle QLabel#descriptionLabel {
                color: rgba(226, 232, 240, 0.75);
                font-size: 12px;
            }
            """
        )

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        icon_widget = _create_icon_widget(icon, size=18, background_alpha=58)
        if icon_widget:
            icon_widget.setFixedSize(40, 40)
            if hasattr(icon_widget, 'setBorderRadius'):
                icon_widget.setBorderRadius(20)
            layout.addWidget(icon_widget)

        text_container = QtWidgets.QWidget()
        text_layout = QtWidgets.QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        title_label = BodyLabel(title)
        title_label.setObjectName("titleLabel")
        title_label.setFont(QtGui.QFont("Segoe UI", 13, QtGui.QFont.Weight.DemiBold))
        text_layout.addWidget(title_label)

        if description:
            description_label = QtWidgets.QLabel(description)
            description_label.setObjectName("descriptionLabel")
            description_label.setWordWrap(True)
            description_label.setStyleSheet(HELPER_LABEL_STYLE)
            text_layout.addWidget(description_label)

        layout.addWidget(text_container, 1)


class FluentSettingsCard(SimpleCardWidget):
    """Card with Fluent styling, title area and body layout."""

    def __init__(
        self,
        title: str = "",
        *,
        description: str = "",
        icon: IconArg = None,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("fluentSettingsCard")
        self.setMinimumWidth(CARD_MIN_WIDTH)
        self.setMaximumWidth(CARD_MAX_WIDTH)
        self.setStyleSheet(
            """
            #fluentSettingsCard {
                background-color: rgba(15, 23, 42, 0.86);
                border: 1px solid rgba(71, 85, 105, 0.38);
            }
            #fluentSettingsCard QWidget {
                background-color: transparent;
            }
            """
        )

        effect = QtWidgets.QGraphicsDropShadowEffect(self)
        effect.setBlurRadius(32)
        effect.setOffset(0, 12)
        effect.setColor(QtGui.QColor(15, 23, 42, 160))
        self.setGraphicsEffect(effect)

        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(24, 24, 24, 24)
        self._layout.setSpacing(22)

        self._header: Optional[SectionTitle] = None
        if title or description or icon is not None:
            self._header = SectionTitle(title, description=description, icon=icon)
            self._header.setProperty("variant", "card")
            self._layout.addWidget(self._header)

        self.content_widget = QtWidgets.QWidget()
        self.body_layout = QtWidgets.QVBoxLayout(self.content_widget)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(20)
        self._layout.addWidget(self.content_widget)

    def header(self) -> Optional[SectionTitle]:
        return self._header

    def add_section(
        self,
        title: str,
        *,
        description: str = "",
        icon: IconArg = None,
    ) -> QtWidgets.QVBoxLayout:
        section = QtWidgets.QWidget()
        section_layout = QtWidgets.QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(16)

        header = SectionTitle(title, description=description, icon=icon)
        section_layout.addWidget(header)

        self.body_layout.addWidget(section)
        return section_layout

    def add_stretch(self, stretch: int = 1) -> None:
        self.body_layout.addStretch(stretch)


class FluentFormLayout(QtWidgets.QGridLayout):
    """Grid form layout with consistent label sizing."""

    def __init__(self, *, label_width: int = FORM_LABEL_WIDTH) -> None:
        super().__init__()
        self.label_width = label_width
        self.setColumnStretch(0, 0)
        self.setColumnStretch(1, 1)
        self.setHorizontalSpacing(FORM_HORIZONTAL_SPACING)
        self.setVerticalSpacing(FORM_VERTICAL_SPACING)

    def add_row(
        self,
        label: str,
        field: QtWidgets.QWidget,
        *,
        helper_text: str | None = None,
    ) -> tuple[QtWidgets.QLabel, QtWidgets.QWidget]:
        return add_form_row(self, label, field, helper_text=helper_text, label_width=self.label_width)


def add_form_row(
    form_layout: QtWidgets.QGridLayout,
    label_text: str,
    field: QtWidgets.QWidget,
    *,
    helper_text: str | None = None,
    label_width: int = FORM_LABEL_WIDTH,
) -> tuple[QtWidgets.QLabel, QtWidgets.QWidget]:
    row_index = form_layout.rowCount()

    label = QtWidgets.QLabel(label_text)
    label.setMinimumWidth(label_width)
    label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
    label.setStyleSheet("color: rgba(226, 232, 240, 0.86); font-weight: 600;")
    form_layout.addWidget(label, row_index, 0, 1, 1)

    container = QtWidgets.QWidget()
    container_layout = QtWidgets.QVBoxLayout(container)
    container_layout.setContentsMargins(0, 0, 0, 0)
    container_layout.setSpacing(6)
    container_layout.addWidget(field)

    if helper_text:
        helper_label = QtWidgets.QLabel(helper_text)
        helper_label.setStyleSheet(HELPER_LABEL_STYLE)
        helper_label.setWordWrap(True)
        container_layout.addWidget(helper_label)

    form_layout.addWidget(container, row_index, 1, 1, 1)
    return label, container


class FluentCardColumn(QtWidgets.QWidget):
    """Centered column that constrains card width across tabs."""

    def __init__(self, *, max_width: int = CARD_MAX_WIDTH, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("fluentCardColumn")

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._column = QtWidgets.QWidget()
        self._column.setMinimumWidth(CARD_MIN_WIDTH)
        self._column.setMaximumWidth(max_width)
        self._column.setMinimumWidth(min(max_width, CARD_MIN_WIDTH))
        self.column_layout = QtWidgets.QVBoxLayout(self._column)
        self.column_layout.setContentsMargins(0, 0, 0, 0)
        self.column_layout.setSpacing(CARD_SPACING)

        layout.addStretch(1)
        layout.addWidget(self._column)
        layout.addStretch(1)

    def add_widget(self, widget: QtWidgets.QWidget) -> None:
        self.column_layout.addWidget(widget)

    def add_layout(self, layout: QtWidgets.QLayout) -> None:
        container = QtWidgets.QWidget()
        container.setLayout(layout)
        self.column_layout.addWidget(container)

    def add_stretch(self, stretch: int = 1) -> None:
        self.column_layout.addStretch(stretch)


def create_card_scroll_area(
    content: QtWidgets.QWidget,
    *,
    top_padding: int = 24,
    bottom_padding: int = 32,
) -> QtWidgets.QScrollArea:
    scroll_area = QtWidgets.QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
    scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    wrapper = QtWidgets.QWidget()
    wrapper_layout = QtWidgets.QVBoxLayout(wrapper)
    wrapper_layout.setContentsMargins(0, top_padding, 0, bottom_padding)
    wrapper_layout.setSpacing(0)
    wrapper_layout.addStretch(1)
    wrapper_layout.addWidget(content, 0, QtCore.Qt.AlignmentFlag.AlignHCenter)
    wrapper_layout.addStretch(1)

    scroll_area.setWidget(wrapper)
    return scroll_area


def wrap_card(card: QtWidgets.QWidget, *, max_width: int = CARD_MAX_WIDTH) -> QtWidgets.QWidget:
    column = FluentCardColumn(max_width=max_width)
    column.add_widget(card)
    return column


FluentHeader = FluentTopBar

__all__ = [
    "FluentTopBar",
    "FluentHeader",
    "FluentStatusBar",
    "SectionTitle",
    "FluentSettingsCard",
    "FluentFormLayout",
    "add_form_row",
    "FluentCardColumn",
    "create_card_scroll_area",
    "wrap_card",
]




