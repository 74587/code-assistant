"""
浮窗显示模块
"""

import ctypes
from PyQt6 import QtCore, QtGui, QtWidgets
from ..utils.constants import OVERLAY_WIDTH, OVERLAY_HEIGHT
from .styles import AppStyles


class Overlay(QtWidgets.QWidget):
    content_ready = QtCore.pyqtSignal(str)
    content_chunk = QtCore.pyqtSignal(str)  # 流式内容块信号

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.background_frame = None
        self._build_ui()
        self.content_ready.connect(self.handle_response, QtCore.Qt.ConnectionType.QueuedConnection)
        self.content_chunk.connect(self.append_chunk, QtCore.Qt.ConnectionType.QueuedConnection)

        # 流式渲染相关变量
        self.streaming_content = ""  # 累积的markdown内容
        self.is_streaming = False
        self.update_timer = None  # 节流更新计时器
        self.pending_chunks = []  # 待处理的chunk缓冲区
        self.last_rendered_length = 0  # 上次渲染的内容长度
        self.use_incremental_rendering = True  # 是否使用增量渲染

        flags = (QtCore.Qt.WindowType.FramelessWindowHint |
                 QtCore.Qt.WindowType.Tool |
                 QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlags(flags)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        # Remove NoFocus and WindowTransparentForInput to enable mouse interaction
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

        # 录屏排除
        try:
            ctypes.windll.user32.SetWindowDisplayAffinity(
                int(self.winId()), 0x11)  # WDA_EXCLUDEFROMCAPTURE
        except Exception:
            pass

    def _build_ui(self):
        self.resize(OVERLAY_WIDTH, OVERLAY_HEIGHT)
        # Main layout for the transparent window
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # A QFrame to act as the visible, styled background
        self.background_frame = QtWidgets.QFrame(self)
        self.update_background_opacity()

        # Layout for the content inside the background frame
        content_layout = QtWidgets.QVBoxLayout(self.background_frame)
        content_layout.setContentsMargins(15, 15, 15, 15)

        self.browser = QtWidgets.QTextBrowser(self.background_frame)
        self.browser.setStyleSheet(AppStyles.get_overlay_style())

        content_layout.addWidget(self.browser)
        main_layout.addWidget(self.background_frame)

    def update_background_opacity(self):
        if self.background_frame:
            opacity = self.config_manager.get("background_opacity", 120)
            self.background_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(30, 30, 30, {opacity});
                    border: none;
                    border-radius: 15px;
                    color: white;
                }}
            """)

    def set_html(self, html_body: str):
        self.browser.setHtml(html_body)
        self.browser.verticalScrollBar().setValue(0)

    @QtCore.pyqtSlot(str)
    def handle_response(self, html: str):
        self.set_html(html)
        if not self.isVisible():
            self.toggle()

    def toggle(self):
        if self.isVisible():
            self.hide()
        else:
            scr = QtGui.QGuiApplication.primaryScreen().availableGeometry()
            geo = self.frameGeometry()
            self.move(scr.right() - geo.width() - 20,
                      scr.bottom() - geo.height() - 20)
            self.show()

    def scroll_up(self):
        sb = self.browser.verticalScrollBar()
        sb.setValue(sb.value() - sb.singleStep()*3)

    def scroll_down(self):
        sb = self.browser.verticalScrollBar()
        sb.setValue(sb.value() + sb.singleStep()*3)

    def wheelEvent(self, event):
        """处理鼠标滚轮事件"""
        # 获取滚轮滚动方向
        delta = event.angleDelta().y()

        if delta > 0:
            # 向上滚动
            self.scroll_up()
        elif delta < 0:
            # 向下滚动
            self.scroll_down()

        # 接受事件，防止传递给父窗口
        event.accept()

    def start_streaming(self):
        """开始流式响应"""
        self.is_streaming = True
        self.streaming_content = ""
        self.pending_chunks.clear()
        self.last_rendered_length = 0

        # 重置增量渲染状态
        self.use_incremental_rendering = True
        if hasattr(self, 'last_rendered_content'):
            delattr(self, 'last_rendered_content')

        # 初始化节流计时器
        if self.update_timer:
            self.update_timer.stop()
        self.update_timer = QtCore.QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._process_buffered_chunks)

        # 显示等待提示
        self.set_html("<p style='color: #999; text-align: center;'>正在生成回复...</p>")
        if not self.isVisible():
            self.show_at_position()

    @QtCore.pyqtSlot(str)
    def append_chunk(self, chunk: str):
        """追加流式内容块 - 优化版本"""
        print(f"[DEBUG] 收到chunk: '{chunk[:50]}...', streaming状态: {self.is_streaming}")

        if not self.is_streaming:
            print("[DEBUG] 不在流式模式，忽略chunk")
            return

        # 添加到缓冲区而不是立即处理
        self.pending_chunks.append(chunk)
        print(f"[DEBUG] 缓冲区大小: {len(self.pending_chunks)}")

        # 节流更新：每100ms最多更新一次
        if not self.update_timer.isActive():
            print("[DEBUG] 启动更新计时器")
            self.update_timer.start(100)

    def _process_buffered_chunks(self):
        """批量处理缓冲的chunk"""
        print(f"[DEBUG] 处理缓冲chunk, streaming: {self.is_streaming}, chunks数量: {len(self.pending_chunks)}")

        if not self.is_streaming or not self.pending_chunks:
            return

        # 合并所有待处理的chunk
        new_content = ''.join(self.pending_chunks)
        self.streaming_content += new_content
        self.pending_chunks.clear()

        # 智能渲染：只有内容长度显著变化时才重新渲染
        content_length = len(self.streaming_content)
        length_diff = content_length - self.last_rendered_length

        # 渲染策略：内容增长超过100字符或包含完整句子时才更新
        should_render = (
            length_diff >= 100 or  # 内容增长足够多
            new_content.endswith(('.', '!', '?', '\n', '```')) or  # 完整句子或代码块
            content_length < 200  # 初始内容较少时保持响应性
        )

        if should_render:
            self._render_content()
            self.last_rendered_length = content_length

    def finish_streaming(self):
        """结束流式响应"""
        self.is_streaming = False

        # 停止计时器
        if self.update_timer and self.update_timer.isActive():
            self.update_timer.stop()

        # 处理剩余的chunk并做最终渲染
        if self.pending_chunks:
            self._process_buffered_chunks()

        # 确保最终内容完整渲染
        self._render_content()

    def _render_content(self):
        """渲染内容到界面 - 高性能版本"""
        try:
            if self.use_incremental_rendering and hasattr(self, 'last_rendered_content'):
                # 增量渲染：只渲染新内容
                new_content = self.streaming_content[len(self.last_rendered_content):]
                if new_content:
                    self._append_rendered_content(new_content)
                    self.last_rendered_content = self.streaming_content
            else:
                # 全量渲染（首次或出错时的回退）
                from markdown_it import MarkdownIt
                html = MarkdownIt("commonmark", {"html": True}).render(self.streaming_content)
                self.set_html(html)
                self.last_rendered_content = self.streaming_content

            # 延迟滚动，确保内容已渲染
            QtCore.QTimer.singleShot(50, self._scroll_to_bottom)

        except Exception as e:
            # 如果渲染失败，回退到纯文本显示
            self.browser.setPlainText(self.streaming_content)
            self.use_incremental_rendering = False  # 禁用增量渲染

    def _append_rendered_content(self, new_content: str):
        """增量追加内容（实验性功能）"""
        try:
            from markdown_it import MarkdownIt
            # 只渲染新内容
            new_html = MarkdownIt("commonmark", {"html": True}).render(new_content)

            # 使用QTextCursor在文档末尾追加内容
            cursor = self.browser.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            cursor.insertHtml(new_html)

        except Exception as e:
            # 增量渲染失败，回退到全量渲染
            self.use_incremental_rendering = False
            self._render_content()

    def _scroll_to_bottom(self):
        """滚动到底部"""
        sb = self.browser.verticalScrollBar()
        sb.setValue(sb.maximum())

    def show_at_position(self):
        """在指定位置显示浮窗"""
        scr = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        geo = self.frameGeometry()
        self.move(scr.right() - geo.width() - 20,
                  scr.bottom() - geo.height() - 20)
        self.show()