from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import QCoreApplication
from qfluentwidgets import setTheme, setThemeColor, Theme, qconfig, FluentTranslator

DEFAULT_FONT = QtGui.QFont("Segoe UI", 10)


class FluentThemeManager:
    """Apply Fluent theme (dark) across the app."""

    def __init__(self, primary: str = "#5E81F4", dark: bool = True) -> None:
        app = QtWidgets.QApplication.instance()
        if app is None:
            raise RuntimeError("QApplication must exist before FluentThemeManager is created")

        self._app = app
        self._primary = QtGui.QColor(primary)
        self._is_dark = dark

        qconfig.load()
        translator = FluentTranslator()
        QCoreApplication.installTranslator(translator)

        self.apply_global_palette()
        self._app.setFont(DEFAULT_FONT)

    def apply_global_palette(self) -> None:
        theme = Theme.DARK if self._is_dark else Theme.LIGHT
        setTheme(theme)
        setThemeColor(self._primary)

    def update_primary_color(self, color: str) -> None:
        self._primary = QtGui.QColor(color)
        setThemeColor(self._primary)

    def toggle_mode(self, dark: bool) -> None:
        if self._is_dark == dark:
            return
        self._is_dark = dark
        self.apply_global_palette()
