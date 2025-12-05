"""
浮窗显示模块 v2.0
现代化设计：毛玻璃效果、流畅动画、精致细节
功能保证：防截屏/录屏、低调显示
"""

import ctypes
from PyQt6 import QtCore, QtGui, QtWidgets
from ..utils.constants import OVERLAY_WIDTH, OVERLAY_HEIGHT
from .theme import DesignTokens


class ModernOverlay(QtWidgets.QWidget):
    """
    现代化浮窗组件

    特性：
    - 防截屏/录屏保护 (Windows SetWindowDisplayAffinity)
    - 低调的深色毛玻璃外观，不会在桌面上过于显眼
    - 流畅的淡入淡出动画
    - 流式内容渲染支持
    """

    content_ready = QtCore.pyqtSignal(str)
    content_chunk = QtCore.pyqtSignal(str)

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager

        # UI 组件引用
        self.background_frame = None
        self.title_bar = None
        self.title_label = None
        self.loading_indicator = None
        self.provider_label = None
        self.browser = None

        # 拖动状态
        self._drag_position = None
        self._is_dragging = False

        # 动画组件
        self._opacity_effect = None
        self._fade_animation = None
        self._scale_animation = None

        # 流式渲染状态
        self.streaming_content = ""
        self.is_streaming = False
        self.update_timer = None
        self.pending_chunks = []
        self.last_rendered_length = 0
        self.use_incremental_rendering = True

        # 加载动画
        self.loading_animation = None
        self._loading_dots = 0
        self._pulse_animation = None

        self._build_ui()
        self._setup_animations()
        self._setup_window_flags()

        self.content_ready.connect(self.handle_response, QtCore.Qt.ConnectionType.QueuedConnection)
        self.content_chunk.connect(self.append_chunk, QtCore.Qt.ConnectionType.QueuedConnection)

    def _setup_window_flags(self):
        """设置窗口标志"""
        flags = (
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.Tool |
            QtCore.Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowFlags(flags)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

        # ═══════════════════════════════════════════════════════════
        # 防截屏/录屏保护 (Windows)
        # 使用 SetWindowDisplayAffinity API
        # WDA_EXCLUDEFROMCAPTURE (0x11) - 从截屏和录屏中排除
        # ═══════════════════════════════════════════════════════════
        self._apply_screen_capture_protection()

    def _apply_screen_capture_protection(self):
        """应用截屏保护 - 防止被截屏或录屏工具捕获"""
        try:
            # Windows API: SetWindowDisplayAffinity
            # WDA_EXCLUDEFROMCAPTURE = 0x11
            # 这会使窗口在截图和录屏中显示为黑色
            hwnd = int(self.winId())
            WDA_EXCLUDEFROMCAPTURE = 0x11
            result = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
            if result:
                pass  # 成功应用保护
        except Exception:
            # 非 Windows 平台或 API 调用失败时静默处理
            pass

    def _build_ui(self):
        """构建 UI"""
        self.resize(OVERLAY_WIDTH, OVERLAY_HEIGHT)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 主背景框架 - 极度隐蔽的半透明效果
        self.background_frame = QtWidgets.QFrame(self)
        self._apply_glass_style()

        # 不使用阴影，避免产生明显的边界感
        # 如果需要极轻的阴影可以取消注释
        # shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        # shadow.setBlurRadius(8)
        # shadow.setOffset(0, 2)
        # shadow.setColor(QtGui.QColor(0, 0, 0, 15))
        # self.background_frame.setGraphicsEffect(shadow)

        content_layout = QtWidgets.QVBoxLayout(self.background_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 标题栏 - 极简隐蔽
        self._build_title_bar(content_layout)

        # 内容区域
        self._build_content_area(content_layout)

        main_layout.addWidget(self.background_frame)

        # 加载动画计时器
        self.loading_animation = QtCore.QTimer()
        self.loading_animation.timeout.connect(self._update_loading_animation)

    def _apply_glass_style(self):
        """
        应用隐蔽效果

        设计理念：
        - 背景极度半透明，与任何窗口融合
        - 旁人路过很难注意到有浮窗
        - 使用者自己能清楚阅读内容
        """
        # 透明度：数值越低越透明（范围50-255）
        # 默认120 = 约47%不透明度，非常隐蔽
        opacity = self.config_manager.get("background_opacity", 120)
        radius = DesignTokens.radius.OVERLAY

        # 深色半透明背景，几乎没有边框
        self.background_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(15, 20, 30, {opacity});
                border: 1px solid rgba(60, 70, 90, 0.08);
                border-radius: {radius}px;
            }}
        """)

    def _build_title_bar(self, parent_layout):
        """
        构建标题栏 - 极简隐蔽风格
        只保留必要的拖动区域和关闭按钮
        """
        self.title_bar = QtWidgets.QFrame()
        self.title_bar.setFixedHeight(28)  # 极紧凑
        self.title_bar.setCursor(QtCore.Qt.CursorShape.SizeAllCursor)
        self.title_bar.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: none;
                border-top-left-radius: {DesignTokens.radius.OVERLAY}px;
                border-top-right-radius: {DesignTokens.radius.OVERLAY}px;
            }}
        """)

        title_layout = QtWidgets.QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 8, 0)
        title_layout.setSpacing(6)

        # 极小的拖动指示点（几乎看不见）
        drag_indicator = QtWidgets.QLabel("⋮⋮")
        drag_indicator.setStyleSheet("""
            color: rgba(100, 116, 139, 0.3);
            font-size: 10px;
            background: transparent;
        """)
        title_layout.addWidget(drag_indicator)

        # 隐藏的标题和状态标签（保留引用但不显示文字）
        self.title_label = QtWidgets.QLabel("")
        self.title_label.setStyleSheet("background: transparent;")
        title_layout.addWidget(self.title_label)

        self.provider_label = QtWidgets.QLabel("")
        self.provider_label.setStyleSheet("background: transparent;")
        title_layout.addWidget(self.provider_label)

        title_layout.addStretch()

        # 加载指示器 - 极度隐蔽
        self.loading_indicator = QtWidgets.QLabel("")
        self.loading_indicator.setStyleSheet("""
            color: rgba(100, 180, 200, 0.5);
            font-size: 10px;
            background: transparent;
            padding: 2px 6px;
        """)
        self.loading_indicator.hide()
        title_layout.addWidget(self.loading_indicator)

        # 关闭按钮 - 几乎隐形，悬停时才明显
        close_btn = self._create_window_button("×", "rgba(200, 100, 100, 0.7)")
        close_btn.clicked.connect(self.hide)
        title_layout.addWidget(close_btn)

        parent_layout.addWidget(self.title_bar)

    def _create_window_button(self, text: str, hover_color: str) -> QtWidgets.QPushButton:
        """创建窗口控制按钮 - 默认隐形，悬停显示"""
        btn = QtWidgets.QPushButton(text)
        btn.setFixedSize(18, 18)
        btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: rgba(100, 116, 139, 0.25);
                border: none;
                border-radius: 3px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.05);
                color: {hover_color};
            }}
        """)
        return btn

    def _build_content_area(self, parent_layout):
        """
        构建内容区域

        文字设计理念：
        - 使用柔和的灰色文字，不是刺眼的白色
        - 对于使用者来说足够清晰
        - 对于旁人来说不够显眼，需要靠近才能看清
        """
        content_container = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content_container)
        content_layout.setContentsMargins(12, 6, 12, 12)

        # 文本浏览器 - 柔和灰色文字
        self.browser = QtWidgets.QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: transparent;
                border: none;
                color: rgba(180, 190, 205, 0.85);
                font-family: {DesignTokens.typography.FONT_FAMILY};
                font-size: {DesignTokens.typography.SIZE_BASE}px;
                line-height: 1.55;
                selection-background-color: rgba(100, 120, 180, 0.3);
                selection-color: rgba(220, 230, 245, 0.95);
            }}
            QTextBrowser code, QTextBrowser pre {{
                background-color: rgba(40, 50, 70, 0.3);
                border-radius: 4px;
                padding: 2px 5px;
                font-family: {DesignTokens.typography.FONT_FAMILY_MONO};
                font-size: {DesignTokens.typography.SIZE_SM}px;
                color: rgba(170, 185, 200, 0.85);
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 5px;
                margin: 3px 1px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(100, 116, 139, 0.2);
                border-radius: 2px;
                min-height: 25px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(100, 116, 139, 0.35);
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        content_layout.addWidget(self.browser)
        parent_layout.addWidget(content_container)

    def _setup_animations(self):
        """设置动画效果"""
        self._opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._fade_animation = QtCore.QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_animation.setDuration(250)
        self._fade_animation.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)

    # ─────────────────────────────────────────────────────────────
    # 公共方法
    # ─────────────────────────────────────────────────────────────

    def update_background_opacity(self):
        """更新背景透明度"""
        self._apply_glass_style()

    def set_provider(self, provider: str):
        """设置当前 AI 服务商"""
        if self.provider_label:
            self.provider_label.setText(provider)

    def set_html(self, html_body: str):
        """
        设置 HTML 内容

        文字颜色设计：
        - 主文字：柔和的灰色 rgba(180, 190, 205, 0.85)
        - 标题：稍亮但不刺眼 rgba(195, 205, 220, 0.9)
        - 代码：低调的青灰色
        - 整体效果：使用者能看清，旁人不易注意
        """
        styled_html = f"""
        <style>
            body {{
                margin: 0;
                padding: 0;
                color: rgba(180, 190, 205, 0.85);
                font-family: {DesignTokens.typography.FONT_FAMILY};
                line-height: 1.55;
            }}
            code {{
                background-color: rgba(40, 50, 70, 0.35);
                padding: 2px 5px;
                border-radius: 3px;
                font-family: {DesignTokens.typography.FONT_FAMILY_MONO};
                font-size: 12px;
                color: rgba(165, 180, 195, 0.85);
            }}
            pre {{
                background-color: rgba(35, 45, 65, 0.35);
                padding: 10px 12px;
                border-radius: 5px;
                overflow-x: auto;
                border: 1px solid rgba(70, 85, 105, 0.15);
            }}
            pre code {{
                background: none;
                padding: 0;
            }}
            a {{
                color: rgba(120, 180, 200, 0.75);
                text-decoration: none;
            }}
            a:hover {{
                color: rgba(140, 200, 220, 0.85);
                text-decoration: underline;
            }}
            h1, h2, h3, h4 {{
                color: rgba(195, 205, 220, 0.9);
                margin-top: 12px;
                margin-bottom: 5px;
                font-weight: 500;
            }}
            h1 {{ font-size: 16px; }}
            h2 {{ font-size: 15px; }}
            h3 {{ font-size: 14px; }}
            p {{
                margin: 5px 0;
            }}
            ul, ol {{
                padding-left: 16px;
                margin: 5px 0;
            }}
            li {{
                margin: 3px 0;
            }}
            blockquote {{
                border-left: 2px solid rgba(100, 120, 160, 0.4);
                margin: 8px 0;
                padding-left: 12px;
                color: rgba(160, 175, 190, 0.8);
            }}
            strong {{
                color: rgba(195, 205, 220, 0.9);
                font-weight: 600;
            }}
            em {{
                color: rgba(175, 188, 205, 0.85);
            }}
        </style>
        {html_body}
        """
        self.browser.setHtml(styled_html)
        self.browser.verticalScrollBar().setValue(0)

    @QtCore.pyqtSlot(str)
    def handle_response(self, html: str):
        """处理 API 响应"""
        self.set_html(html)
        if not self.isVisible():
            self.toggle()

    def toggle(self):
        """切换显示/隐藏"""
        if self.isVisible():
            self._fade_out()
        else:
            # 如果内容为空，显示示例内容以便调试
            if not self.browser.toPlainText().strip():
                self._show_sample_content()
            self._fade_in()

    def _show_sample_content(self):
        """显示示例内容用于调试浮窗效果"""
        sample_md = """
## 浮窗效果预览

这是一段**示例文字**，用于测试浮窗的显示效果。

### 特性说明
- 半透明背景，与任何窗口融合
- 低调的文字颜色，不易被旁人注意
- 使用者可以清楚阅读内容

### 代码示例
```python
def hello_world():
    print("Hello, World!")
    return True
```

> 提示：按 `Alt+Q` 可以隐藏此浮窗

正常使用时，这里会显示 AI 的响应内容。
"""
        from markdown_it import MarkdownIt
        html = MarkdownIt("commonmark", {"html": True}).render(sample_md)
        self.set_html(html)

    def show_at_position(self):
        """在指定位置显示"""
        if not self.isVisible():
            self._fade_in()

    # ─────────────────────────────────────────────────────────────
    # 动画方法
    # ─────────────────────────────────────────────────────────────

    def _fade_in(self):
        """淡入显示"""
        scr = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        geo = self.frameGeometry()
        self.move(scr.right() - geo.width() - 24, scr.bottom() - geo.height() - 24)

        if self._opacity_effect:
            self._opacity_effect.setOpacity(0.0)

        self.show()

        if self._fade_animation:
            self._fade_animation.stop()
            self._fade_animation.setStartValue(0.0)
            self._fade_animation.setEndValue(1.0)
            self._fade_animation.start()

    def _fade_out(self):
        """淡出隐藏"""
        if self._fade_animation:
            self._fade_animation.stop()
            self._fade_animation.setStartValue(1.0)
            self._fade_animation.setEndValue(0.0)
            self._fade_animation.finished.connect(self._on_fade_out_finished)
            self._fade_animation.start()
        else:
            self.hide()

    def _on_fade_out_finished(self):
        """淡出完成"""
        self.hide()
        if self._opacity_effect:
            self._opacity_effect.setOpacity(1.0)
        if self._fade_animation:
            try:
                self._fade_animation.finished.disconnect(self._on_fade_out_finished)
            except TypeError:
                pass

    # ─────────────────────────────────────────────────────────────
    # 鼠标事件（拖动）
    # ─────────────────────────────────────────────────────────────

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            if self.title_bar and self.title_bar.geometry().contains(event.pos()):
                self._is_dragging = True
                self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self._is_dragging and self._drag_position is not None:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._is_dragging = False
            self._drag_position = None
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        sb = self.browser.verticalScrollBar()
        if delta > 0:
            sb.setValue(sb.value() - sb.singleStep() * 3)
        elif delta < 0:
            sb.setValue(sb.value() + sb.singleStep() * 3)
        event.accept()

    # ─────────────────────────────────────────────────────────────
    # 滚动方法
    # ─────────────────────────────────────────────────────────────

    def scroll_up(self):
        sb = self.browser.verticalScrollBar()
        sb.setValue(sb.value() - sb.singleStep() * 3)

    def scroll_down(self):
        sb = self.browser.verticalScrollBar()
        sb.setValue(sb.value() + sb.singleStep() * 3)

    def _scroll_to_bottom(self):
        sb = self.browser.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ─────────────────────────────────────────────────────────────
    # 加载动画
    # ─────────────────────────────────────────────────────────────

    def _update_loading_animation(self):
        """更新加载动画 - 极简低调"""
        self._loading_dots = (self._loading_dots + 1) % 4
        dots = "·" * (self._loading_dots + 1)
        self.loading_indicator.setText(dots)

    def _start_loading_animation(self):
        """开始加载动画"""
        if self.loading_indicator:
            self.loading_indicator.setText("·")
            self.loading_indicator.show()
            self._loading_dots = 0
        if self.loading_animation:
            self.loading_animation.start(350)

    def _stop_loading_animation(self):
        """停止加载动画"""
        if self.loading_animation:
            self.loading_animation.stop()
        if self.loading_indicator:
            self.loading_indicator.hide()

    # ─────────────────────────────────────────────────────────────
    # 流式响应
    # ─────────────────────────────────────────────────────────────

    def start_streaming(self):
        """开始流式响应"""
        self.is_streaming = True
        self.streaming_content = ""
        self.pending_chunks.clear()
        self.last_rendered_length = 0
        self.use_incremental_rendering = True

        if hasattr(self, 'last_rendered_content'):
            delattr(self, 'last_rendered_content')

        if self.update_timer:
            self.update_timer.stop()
        self.update_timer = QtCore.QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._process_buffered_chunks)

        self._start_loading_animation()

        # 显示处理中的提示 - 极度低调
        self.set_html("""
            <div style='
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 150px;
                text-align: center;
            '>
                <p style='
                    color: rgba(140, 155, 175, 0.6);
                    font-size: 12px;
                    margin: 0;
                '>...</p>
            </div>
        """)

        if not self.isVisible():
            self.show_at_position()

    @QtCore.pyqtSlot(str)
    def append_chunk(self, chunk: str):
        """追加流式内容"""
        if not self.is_streaming:
            return
        self.pending_chunks.append(chunk)
        if not self.update_timer.isActive():
            self.update_timer.start(80)

    def _process_buffered_chunks(self):
        """处理缓冲的内容"""
        if not self.is_streaming or not self.pending_chunks:
            return

        new_content = ''.join(self.pending_chunks)
        self.streaming_content += new_content
        self.pending_chunks.clear()

        content_length = len(self.streaming_content)
        length_diff = content_length - self.last_rendered_length

        should_render = (
            length_diff >= 80 or
            new_content.endswith(('.', '!', '?', '\n', '```')) or
            content_length < 150
        )

        if should_render:
            self._render_content()
            self.last_rendered_length = content_length

    def finish_streaming(self):
        """完成流式响应"""
        self.is_streaming = False
        self._stop_loading_animation()

        if self.update_timer and self.update_timer.isActive():
            self.update_timer.stop()

        if self.pending_chunks:
            self._process_buffered_chunks()

        self._render_content()

    def _render_content(self):
        """渲染内容"""
        try:
            from markdown_it import MarkdownIt
            html = MarkdownIt("commonmark", {"html": True}).render(self.streaming_content)
            self.set_html(html)
            self.last_rendered_content = self.streaming_content
            QtCore.QTimer.singleShot(30, self._scroll_to_bottom)
        except Exception:
            self.browser.setPlainText(self.streaming_content)
            self.use_incremental_rendering = False


# 保持向后兼容
Overlay = ModernOverlay
