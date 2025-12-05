"""
截图选择器组件
提供全屏覆盖和区域选择功能
"""

import sys
import ctypes
from PyQt6 import QtCore, QtGui, QtWidgets
from mss import mss
from mss import tools
from typing import Optional, Tuple


class ScreenshotSelector(QtWidgets.QWidget):
    """截图区域选择器"""

    # 信号定义
    screenshot_taken = QtCore.pyqtSignal(bytes)  # 截图完成信号
    screenshot_cancelled = QtCore.pyqtSignal()  # 取消截图信号

    def __init__(self):
        super().__init__()
        self.start_pos = None  # 鼠标按下位置
        self.end_pos = None    # 鼠标当前位置
        self.is_selecting = False  # 是否正在选择
        self.wait_timer = None  # 等待计时器
        self.confirm_timer = None  # 确认计时器
        self.screenshot_buffer = None  # 全屏截图缓存
        self.selection_confirmed = False  # 是否已确认选择
        self.scale_factor = 1.0  # DPI缩放比例

        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        # 设置为全屏、无边框、置顶，尽量不干扰其他窗口焦点
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.WindowStaysOnTopHint |
            QtCore.Qt.WindowType.Tool |
            QtCore.Qt.WindowType.WindowDoesNotAcceptFocus |
            QtCore.Qt.WindowType.X11BypassWindowManagerHint
        )

        # 设置透明背景
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

        # 设置鼠标追踪
        self.setMouseTracking(True)

        # 设置光标为十字线
        self.setCursor(QtCore.Qt.CursorShape.CrossCursor)


    def start_capture(self):
        """开始截图流程"""
        # 获取整个屏幕
        screen = QtWidgets.QApplication.primaryScreen()
        geometry = screen.geometry()

        # 获取设备像素比例（DPI缩放）
        self.scale_factor = screen.devicePixelRatio()

        # 截取当前全屏内容作为背景
        with mss() as sct:
            monitor = sct.monitors[1]  # 主显示器
            screenshot = sct.grab(monitor)
            # 转换为Qt格式
            img_bytes = QtCore.QByteArray(screenshot.rgb)
            qimg = QtGui.QImage(
                img_bytes,
                screenshot.width,
                screenshot.height,
                QtGui.QImage.Format.Format_RGB888
            )
            # 创建pixmap并缩放到逻辑尺寸
            pixmap = QtGui.QPixmap.fromImage(qimg)

            # 如果有DPI缩放，调整显示大小
            if self.scale_factor != 1.0:
                logical_width = int(screenshot.width / self.scale_factor)
                logical_height = int(screenshot.height / self.scale_factor)
                self.screenshot_buffer = pixmap.scaled(
                    logical_width, logical_height,
                    QtCore.Qt.AspectRatioMode.IgnoreAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation
                )
            else:
                self.screenshot_buffer = pixmap

        # 设置窗口大小为全屏
        self.setGeometry(geometry)
        self.showFullScreen()

        # 录屏排除 - 防止截图选择器出现在屏幕录制中
        try:
            ctypes.windll.user32.SetWindowDisplayAffinity(
                int(self.winId()), 0x11)  # WDA_EXCLUDEFROMCAPTURE
        except Exception:
            pass

        # 启动3秒等待计时器
        self.wait_timer = QtCore.QTimer()
        self.wait_timer.setSingleShot(True)
        self.wait_timer.timeout.connect(self.on_wait_timeout)
        self.wait_timer.start(3000)  # 3秒

        # 重置状态
        self.start_pos = None
        self.end_pos = None
        self.is_selecting = False
        self.selection_confirmed = False

    def on_wait_timeout(self):
        """等待超时 - 全屏截图"""
        if not self.is_selecting and not self.selection_confirmed:
            # 3秒内未按下鼠标，进行全屏截图
            self.capture_fullscreen()

    def capture_fullscreen(self):
        """全屏截图"""
        with mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            png_data = tools.to_png(screenshot.rgb, screenshot.size)

        self.screenshot_taken.emit(png_data)
        self.close()

    def capture_region(self, x1: int, y1: int, x2: int, y2: int):
        """截取指定区域"""
        # 将逻辑坐标转换为物理坐标（考虑DPI缩放）
        scale = self.scale_factor
        x1_scaled = int(x1 * scale)
        y1_scaled = int(y1 * scale)
        x2_scaled = int(x2 * scale)
        y2_scaled = int(y2 * scale)

        # 确保坐标正确
        left = min(x1_scaled, x2_scaled)
        top = min(y1_scaled, y2_scaled)
        width = abs(x2_scaled - x1_scaled)
        height = abs(y2_scaled - y1_scaled)

        if width < 1 or height < 1:
            self.screenshot_cancelled.emit()
            self.close()
            return

        with mss() as sct:
            monitor = {
                "left": left,
                "top": top,
                "width": width,
                "height": height
            }
            screenshot = sct.grab(monitor)
            png_data = tools.to_png(screenshot.rgb, screenshot.size)

        self.screenshot_taken.emit(png_data)
        self.close()

    def paintEvent(self, event):
        """绘制事件"""
        painter = QtGui.QPainter(self)

        # 绘制半透明背景
        if self.screenshot_buffer:
            painter.drawPixmap(0, 0, self.screenshot_buffer)

            # 添加半透明遮罩
            painter.fillRect(self.rect(), QtGui.QColor(0, 0, 0, 100))

        # 如果正在选择，绘制选择框
        if self.is_selecting and self.start_pos and self.end_pos:
            # 计算选择区域
            x = min(self.start_pos.x(), self.end_pos.x())
            y = min(self.start_pos.y(), self.end_pos.y())
            w = abs(self.end_pos.x() - self.start_pos.x())
            h = abs(self.end_pos.y() - self.start_pos.y())

            selection_rect = QtCore.QRect(x, y, w, h)

            # 清除选择区域的遮罩（显示原始截图）
            if self.screenshot_buffer:
                painter.setCompositionMode(QtGui.QPainter.CompositionMode.CompositionMode_SourceOver)
                painter.drawPixmap(selection_rect, self.screenshot_buffer, selection_rect)

            # 绘制选择框边框
            pen = QtGui.QPen(QtGui.QColor(0, 120, 215), 2, QtCore.Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(selection_rect)

            # 绘制角标
            corner_size = 5
            painter.fillRect(x - corner_size//2, y - corner_size//2, corner_size, corner_size, QtGui.QColor(0, 120, 215))
            painter.fillRect(x + w - corner_size//2, y - corner_size//2, corner_size, corner_size, QtGui.QColor(0, 120, 215))
            painter.fillRect(x - corner_size//2, y + h - corner_size//2, corner_size, corner_size, QtGui.QColor(0, 120, 215))
            painter.fillRect(x + w - corner_size//2, y + h - corner_size//2, corner_size, corner_size, QtGui.QColor(0, 120, 215))

            # 显示尺寸信息
            if w > 50 and h > 30:
                size_text = f"{w} × {h}"
                font = QtGui.QFont("Arial", 10)
                painter.setFont(font)
                painter.setPen(QtGui.QPen(QtCore.Qt.GlobalColor.white))

                # 文字背景
                text_rect = painter.fontMetrics().boundingRect(size_text)
                text_rect.moveTopLeft(QtCore.QPoint(x + 5, y + 5))
                painter.fillRect(text_rect.adjusted(-3, -2, 3, 2), QtGui.QColor(0, 0, 0, 150))

                # 文字
                painter.drawText(x + 5, y + 15, size_text)

        # 显示提示信息
        if not self.is_selecting and not self.selection_confirmed:
            hint_text = "点击并拖动选择区域 / 3秒后自动全屏截图 / ESC取消"
            font = QtGui.QFont("Microsoft YaHei", 12)
            painter.setFont(font)
            painter.setPen(QtGui.QPen(QtCore.Qt.GlobalColor.white))

            text_rect = painter.fontMetrics().boundingRect(hint_text)
            x = (self.width() - text_rect.width()) // 2
            y = 50

            # 文字背景
            painter.fillRect(x - 10, y - text_rect.height() - 5, text_rect.width() + 20, text_rect.height() + 10, QtGui.QColor(0, 0, 0, 180))

            # 文字
            painter.drawText(x, y, hint_text)

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            # 停止等待计时器
            if self.wait_timer and self.wait_timer.isActive():
                self.wait_timer.stop()

            self.start_pos = event.pos()
            self.end_pos = event.pos()
            self.is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.is_selecting:
            self.end_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.selection_confirmed = True

            # 启动2秒确认计时器
            self.confirm_timer = QtCore.QTimer()
            self.confirm_timer.setSingleShot(True)
            self.confirm_timer.timeout.connect(self.confirm_selection)
            self.confirm_timer.start(2000)  # 2秒

            self.update()

    def confirm_selection(self):
        """确认选择并截图"""
        if self.start_pos and self.end_pos:
            self.capture_region(
                self.start_pos.x(), self.start_pos.y(),
                self.end_pos.x(), self.end_pos.y()
            )

    def keyPressEvent(self, event):
        """按键事件"""
        if event.key() == QtCore.Qt.Key.Key_Escape:
            # 取消截图
            if self.wait_timer and self.wait_timer.isActive():
                self.wait_timer.stop()
            if self.confirm_timer and self.confirm_timer.isActive():
                self.confirm_timer.stop()

            self.screenshot_cancelled.emit()
            self.close()

        elif event.key() == QtCore.Qt.Key.Key_Return or event.key() == QtCore.Qt.Key.Key_Enter:
            # 立即确认当前选择
            if self.selection_confirmed and self.start_pos and self.end_pos:
                if self.confirm_timer and self.confirm_timer.isActive():
                    self.confirm_timer.stop()
                self.confirm_selection()

    def closeEvent(self, event):
        """关闭事件"""
        # 清理计时器
        if self.wait_timer and self.wait_timer.isActive():
            self.wait_timer.stop()
        if self.confirm_timer and self.confirm_timer.isActive():
            self.confirm_timer.stop()

        event.accept()