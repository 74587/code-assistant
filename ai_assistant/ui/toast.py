"""
Toast 提示窗口
防录屏的临时提示窗口
"""

import sys
from PyQt6 import QtWidgets, QtCore, QtGui


class Toast(QtWidgets.QWidget):
    def __init__(self, message: str, duration: int = 2000):
        super().__init__()
        self.message = message
        self.duration = duration
        self.setup_ui()
        self.setup_window()

    def setup_ui(self):
        """设置UI"""
        self.setFixedSize(300, 80)

        # 创建布局
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)

        # 创建标签
        self.label = QtWidgets.QLabel(self.message)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # 设置样式
        self.label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }
        """)

        layout.addWidget(self.label)

        # 设置窗口样式
        self.setStyleSheet("""
            Toast {
                background-color: rgba(0, 0, 0, 180);
                border-radius: 10px;
                border: 2px solid rgba(255, 255, 255, 100);
            }
        """)

    def setup_window(self):
        """设置窗口属性"""
        # 无边框、置顶、工具窗口
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.WindowStaysOnTopHint |
            QtCore.Qt.WindowType.Tool
        )

        # 设置窗口属性，防止被录屏
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Windows 下防录屏设置
        if sys.platform == "win32":
            try:
                import ctypes
                from ctypes import wintypes

                # 获取窗口句柄
                hwnd = int(self.winId())

                # 设置 WDA_EXCLUDEFROMCAPTURE，防止被录屏
                WDA_EXCLUDEFROMCAPTURE = 0x00000011
                ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
            except Exception:
                pass  # 忽略错误，继续显示

        # 居中显示
        self.center_on_screen()

    def center_on_screen(self):
        """窗口居中显示"""
        screen = QtGui.QGuiApplication.primaryScreen()
        screen_rect = screen.availableGeometry()

        x = (screen_rect.width() - self.width()) // 2
        y = screen_rect.height() // 4  # 显示在屏幕上方1/4处

        self.move(x, y)

    def show_toast(self):
        """显示Toast并自动隐藏"""
        self.show()

        # 设置定时器自动隐藏
        QtCore.QTimer.singleShot(self.duration, self.close)

    @staticmethod
    def show_message(message: str, duration: int = 2000):
        """静态方法，显示Toast消息"""
        toast = Toast(message, duration)
        toast.show_toast()
        return toast