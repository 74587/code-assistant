#!/usr/bin/env python
# gemini_overlay_proxy.py
import os, sys, threading, ctypes, io, re, json
from datetime import datetime
from mss import mss, tools
from markdown_it import MarkdownIt
from PyQt6 import QtCore, QtGui, QtWidgets
from pynput import keyboard
from pynput.keyboard import Key, KeyCode, Listener, HotKey
import google.generativeai as genai
import pyperclip
import tempfile
import psutil
import socket
import urllib.request
import urllib.error
import time
from typing import Optional, Tuple

# ────────────────────── 导 入 模 块 ────────────────────── #
import threading

# ────────────────────── 单实例检查 ────────────────────── #
class SingleInstance:
    def __init__(self, app_name="GeminiScreenshotAssistant"):
        self.app_name = app_name
        self.lock_file_path = os.path.join(tempfile.gettempdir(), f"{app_name}.lock")
        self.lock_file = None
        self.is_locked = False
    
    def is_already_running(self):
        """检查是否已有实例在运行"""
        try:
            # 检查锁文件是否存在
            if os.path.exists(self.lock_file_path):
                # 读取锁文件中的PID
                with open(self.lock_file_path, 'r') as f:
                    pid = int(f.read().strip())
                
                # 检查该PID的进程是否还在运行
                if psutil.pid_exists(pid):
                    try:
                        process = psutil.Process(pid)
                        # 检查进程名是否包含python（确保是我们的程序）
                        if 'python' in process.name().lower():
                            return True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # 如果进程不存在，删除过期的锁文件
                os.remove(self.lock_file_path)
            
            return False
        except Exception:
            return False
    
    def acquire_lock(self):
        """获取锁"""
        try:
            # 创建锁文件并写入当前进程PID
            with open(self.lock_file_path, 'w') as f:
                f.write(str(os.getpid()))
            self.is_locked = True
            return True
        except Exception:
            return False
    
    def release_lock(self):
        """释放锁"""
        try:
            if self.is_locked and os.path.exists(self.lock_file_path):
                os.remove(self.lock_file_path)
                self.is_locked = False
        except Exception:
            pass
    
    def __del__(self):
        """析构函数，确保释放锁"""
        self.release_lock()

# ─────────────────────── 配置管理 ─────────────────────── #
class ConfigManager:
    def __init__(self):
        self.config_file = "gemini_config.json"
        self.config = self.load_or_create_config()

    def get_default_config(self):
        return {
            "api_key": os.getenv("GEMINI_KEY", ""),
            "proxy": os.getenv("CLASH_PROXY", ""),
            "background_opacity": 120,
            "prompts": [
                {
                    "name": "代码实现",
                    "content": "请基于图上的问问题给出答案，如果答案是需要通过代码实现，只需要给出完整的代码实现，并在代码里面加解释即可，代码实现需要保证执行效率，时间复杂度尽可能低，不需要添加额外的解释，代码请用 markdown 格式化",
                    "hotkey": "alt+z"
                },
                {
                    "name": "BUG修复",
                    "content": "请找到截图中的代码BUG，并给出正确的写法",
                    "hotkey": "alt+x"
                }
            ],
            "hotkeys": {
                "toggle": "alt+q",
                "screenshot_only": "alt+w",
                "scroll_up": "alt+up",
                "scroll_down": "alt+down"
            }
        }

    def load_or_create_config(self):
        if not os.path.exists(self.config_file):
            print(f"配置文件 '{self.config_file}' 不存在，将创建默认配置。")
            default_config = self.get_default_config()
            try:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=2)
                return default_config
            except Exception as e:
                print(f"创建默认配置文件失败: {e}")
                return default_config # 返回内存中的默认配置

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"读取配置文件 '{self.config_file}' 失败: {e}。将使用默认配置。")
            return self.get_default_config()
    
    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        self.save_config()

# ─────────────────────── 日志管理 ─────────────────────── #
class LogManager(QtCore.QObject):
    log_updated = QtCore.pyqtSignal(str)
    MAX_LOG_ENTRIES = 1000  # 最大日志条数

    def __init__(self):
        super().__init__()
        self.logs = []
        self.log_file = None
        self.setup_log_file()

    def setup_log_file(self):
        """设置日志文件，实现日志轮转"""
        try:
            log_dir = os.path.join(os.path.expanduser("~"), ".gemini_assistant", "logs")
            os.makedirs(log_dir, exist_ok=True)

            # 使用日期作为日志文件名
            log_filename = f"gemini_{datetime.now().strftime('%Y%m%d')}.log"
            log_path = os.path.join(log_dir, log_filename)

            # 清理超过7天的旧日志
            self.cleanup_old_logs(log_dir, days=7)

            self.log_file = log_path
        except Exception as e:
            print(f"设置日志文件失败: {e}")
            self.log_file = None

    def cleanup_old_logs(self, log_dir, days=7):
        """清理旧日志文件"""
        try:
            import time
            current_time = time.time()
            for filename in os.listdir(log_dir):
                if filename.startswith("gemini_") and filename.endswith(".log"):
                    file_path = os.path.join(log_dir, filename)
                    if os.path.getmtime(file_path) < current_time - (days * 24 * 60 * 60):
                        os.remove(file_path)
        except Exception:
            pass

    def add_log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"

        # 内存日志轮转
        if len(self.logs) >= self.MAX_LOG_ENTRIES:
            self.logs = self.logs[-self.MAX_LOG_ENTRIES + 100:]  # 保留最近的900条

        self.logs.append(log_entry)
        self.log_updated.emit(log_entry)
        print(log_entry)

        # 同时写入文件
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    full_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{full_timestamp}] {level}: {message}\n")
            except Exception:
                pass

    def get_logs(self):
        return "\n".join(self.logs)

# ────────────────────── 浮  窗 ────────────────────── #
class Overlay(QtWidgets.QWidget):
    content_ready = QtCore.pyqtSignal(str)

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.background_frame = None
        self._build_ui()
        self.content_ready.connect(self.handle_response, QtCore.Qt.ConnectionType.QueuedConnection)

        flags = (QtCore.Qt.WindowType.FramelessWindowHint |
                 QtCore.Qt.WindowType.Tool |
                 QtCore.Qt.WindowType.WindowStaysOnTopHint |
                 QtCore.Qt.WindowType.WindowTransparentForInput)
        self.setWindowFlags(flags)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        # 录屏排除
        try:
            ctypes.windll.user32.SetWindowDisplayAffinity(
                int(self.winId()), 0x11)  # WDA_EXCLUDEFROMCAPTURE
        except Exception:
            pass

    def _build_ui(self):
        self.resize(960, 360)  # 宽度从640增加50%到960
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
        self.browser.setStyleSheet("""
            QTextBrowser {
                background-color: transparent;
                border: none;
                font-family: Consolas, Segoe UI, monospace;
            }
            QTextBrowser pre, QTextBrowser code {
                background-color: rgba(0, 0, 0, 0.5);
                padding: 10px;
                border-radius: 5px;
                color: white; /* Ensure code block text is also white */
            }
        """)

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

# ────────────────────── 大模型调用 ────────────────────── #
def capture_screen() -> bytes:
    with mss() as sct:
        sct_img = sct.grab(sct.monitors[1])
        return tools.to_png(sct_img.rgb, sct_img.size)

def extract_code_blocks(markdown_text: str) -> str:
    """提取 markdown 文本中的所有代码块"""
    # 匹配代码块的正则表达式
    code_pattern = r'```(?:[a-zA-Z0-9+#-]*\n)?(.*?)```'
    matches = re.findall(code_pattern, markdown_text, re.DOTALL)
    
    if matches:
        # 将所有代码块合并，用换行分隔
        code_content = '\n\n'.join(match.strip() for match in matches)
        return code_content
    return ""

def check_network_connectivity(timeout: int = 5) -> Tuple[bool, str]:
    """检查网络连接状态
    返回: (是否连接, 状态描述)
    """
    test_hosts = [
        ("8.8.8.8", 53, "Google DNS"),
        ("1.1.1.1", 53, "Cloudflare DNS"),
        ("223.5.5.5", 53, "阿里 DNS")
    ]

    for host, port, name in test_hosts:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                return True, f"网络连接正常 (通过 {name})"
        except Exception:
            continue

    return False, "网络连接失败，请检查网络设置"

def check_api_connectivity(api_key: str, proxy: Optional[str] = None) -> Tuple[bool, str]:
    """检查 API 连接状态"""
    try:
        # 配置代理（如果有）
        if proxy:
            os.environ['HTTPS_PROXY'] = proxy
            os.environ['HTTP_PROXY'] = proxy

        genai.configure(api_key=api_key)
        # 尝试列出模型以测试连接
        models = genai.list_models()
        return True, "API 连接正常"
    except Exception as e:
        error_str = str(e)
        if "API key not valid" in error_str:
            return False, "API Key 无效，请检查配置"
        elif "connection" in error_str.lower():
            return False, f"API 连接失败: {error_str}"
        else:
            return False, f"API 测试失败: {error_str}"

def ask_gemini_with_retry(png: bytes, prompt: str, config_manager, log_manager,
                         max_retries: int = 3, retry_delay: int = 2) -> str:
    """带重试机制的 Gemini API 调用"""
    api_key = config_manager.get("api_key")
    if not api_key:
        error_msg = "❌ API Key 未配置，请在设置中配置"
        log_manager.add_log(error_msg, "ERROR")
        return error_msg

    # 首先检查网络连接
    network_ok, network_msg = check_network_connectivity()
    if not network_ok:
        log_manager.add_log(network_msg, "ERROR")
        return f"❌ {network_msg}"

    # 配置代理
    proxy = config_manager.get("proxy", "")
    if proxy:
        os.environ['HTTPS_PROXY'] = proxy
        os.environ['HTTP_PROXY'] = proxy
        log_manager.add_log(f"使用代理: {proxy}")

    # 重试逻辑
    last_error = None
    for attempt in range(max_retries):
        try:
            log_manager.add_log(f"调用 Gemini API (尝试 {attempt + 1}/{max_retries})")

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')

            # 创建图片对象
            import PIL.Image
            import io
            image = PIL.Image.open(io.BytesIO(png))

            # 设置生成配置
            generation_config = genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=4096,
            )

            response = model.generate_content(
                [prompt, image],
                generation_config=generation_config,
                request_options={"timeout": 30}  # 30秒超时
            )

            if response and response.text:
                log_manager.add_log(f"✅ API 调用成功，返回 {len(response.text)} 字符")
                return response.text
            else:
                raise Exception("API 返回空响应")

        except Exception as e:
            last_error = e
            error_str = str(e)

            # 分析错误类型
            if "quota" in error_str.lower():
                error_msg = "❌ API 配额已用完，请稍后再试或更换 API Key"
                log_manager.add_log(error_msg, "ERROR")
                return error_msg
            elif "api key" in error_str.lower():
                error_msg = "❌ API Key 无效或已过期，请检查配置"
                log_manager.add_log(error_msg, "ERROR")
                return error_msg
            elif "timeout" in error_str.lower():
                log_manager.add_log(f"⏱️ 请求超时，{retry_delay}秒后重试...", "WARNING")
            elif "connection" in error_str.lower():
                log_manager.add_log(f"🔌 连接错误: {error_str}，{retry_delay}秒后重试...", "WARNING")
            else:
                log_manager.add_log(f"⚠️ 尝试 {attempt + 1} 失败: {error_str}", "WARNING")

            # 如果不是最后一次尝试，等待后重试
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数退避

    # 所有重试都失败
    error_msg = f"❌ API 调用失败（重试{max_retries}次后）: {last_error}"
    log_manager.add_log(error_msg, "ERROR")
    return error_msg

def ask_gemini(png: bytes, prompt: str, config_manager, log_manager) -> str:
    """保持向后兼容的接口"""
    return ask_gemini_with_retry(png, prompt, config_manager, log_manager)

def ask_gemini_multi_images_with_retry(images: list, prompt: str, config_manager, log_manager,
                                      max_retries: int = 3, retry_delay: int = 2) -> str:
    """带重试机制的多图片 Gemini API 调用"""
    api_key = config_manager.get("api_key")
    if not api_key:
        error_msg = "❌ API Key 未配置，请在设置中配置"
        log_manager.add_log(error_msg, "ERROR")
        return error_msg

    # 检查网络
    network_ok, network_msg = check_network_connectivity()
    if not network_ok:
        log_manager.add_log(network_msg, "ERROR")
        return f"❌ {network_msg}"

    # 配置代理
    proxy = config_manager.get("proxy", "")
    if proxy:
        os.environ['HTTPS_PROXY'] = proxy
        os.environ['HTTP_PROXY'] = proxy
        log_manager.add_log(f"使用代理: {proxy}")

    # 计算总数据大小
    total_size_mb = sum(len(img) for img in images) / (1024 * 1024)
    if total_size_mb > 20:  # 如果总大小超过20MB，给出警告
        log_manager.add_log(f"⚠️ 图片总大小较大 ({total_size_mb:.1f} MB)，可能需要较长时间", "WARNING")

    last_error = None
    for attempt in range(max_retries):
        try:
            log_manager.add_log(f"调用 Gemini API - 多图片模式 (尝试 {attempt + 1}/{max_retries})")

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')

            # 构建内容列表
            import PIL.Image
            import io

            contents = [prompt]
            for i, png_data in enumerate(images):
                try:
                    image = PIL.Image.open(io.BytesIO(png_data))
                    # 如果图片太大，可以考虑压缩
                    if len(png_data) > 5 * 1024 * 1024:  # 5MB
                        log_manager.add_log(f"压缩第 {i+1} 张图片...", "INFO")
                        # 调整图片大小
                        max_size = (1920, 1080)
                        image.thumbnail(max_size, PIL.Image.Resampling.LANCZOS)
                    contents.append(image)
                except Exception as img_error:
                    log_manager.add_log(f"⚠️ 处理第 {i+1} 张图片失败: {img_error}", "WARNING")
                    continue

            if len(contents) == 1:  # 只有提示词，没有有效图片
                raise Exception("没有有效的图片可以处理")

            # 生成配置
            generation_config = genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=4096,
            )

            # 增加超时时间（多图片需要更长时间）
            timeout = 30 + (len(images) * 10)  # 基础30秒 + 每张图片10秒
            response = model.generate_content(
                contents,
                generation_config=generation_config,
                request_options={"timeout": timeout}
            )

            if response and response.text:
                log_manager.add_log(
                    f"✅ API 调用成功，处理了 {len(images)} 张图片，返回 {len(response.text)} 字符"
                )
                return response.text
            else:
                raise Exception("API 返回空响应")

        except Exception as e:
            last_error = e
            error_str = str(e)

            # 错误分析和处理
            if "quota" in error_str.lower():
                error_msg = "❌ API 配额已用完，请稍后再试或更换 API Key"
                log_manager.add_log(error_msg, "ERROR")
                return error_msg
            elif "api key" in error_str.lower():
                error_msg = "❌ API Key 无效或已过期，请检查配置"
                log_manager.add_log(error_msg, "ERROR")
                return error_msg
            elif "timeout" in error_str.lower():
                log_manager.add_log(f"⏱️ 请求超时（图片较多），{retry_delay}秒后重试...", "WARNING")
            else:
                log_manager.add_log(f"⚠️ 尝试 {attempt + 1} 失败: {error_str}", "WARNING")

            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2

    error_msg = f"❌ API 调用失败（重试{max_retries}次后）: {last_error}"
    log_manager.add_log(error_msg, "ERROR")
    return error_msg

def ask_gemini_multi_images(images: list, prompt: str, config_manager, log_manager) -> str:
    """保持向后兼容的接口"""
    return ask_gemini_multi_images_with_retry(images, prompt, config_manager, log_manager)

# ────────────────────── 配置界面 ────────────────────── #
class ConfigWindow(QtWidgets.QMainWindow):
    MAX_SCREENSHOT_HISTORY = 10  # 最大截图历史数量

    def __init__(self, config_manager, log_manager, single_instance):
        super().__init__()
        self.config_manager = config_manager
        self.log_manager = log_manager
        self.single_instance = single_instance  # 单实例管理器

        # 初始化其他属性
        self.overlay = None
        self.hotkey_handlers = []
        self.screenshot_history = []  # 存储历史截图的字节数据
        
        # pynput 相关属性
        self.keyboard_listener = None
        self.hotkeys = {}  # 存储 HotKey 对象
        self.pressed_keys = set()  # 当前按下的键
        
        self.setWindowTitle("Gemini 截图助手 - 配置")
        self.setMinimumSize(400, 650)
        self.resize(450, 700)
        
        self.setup_ui()
        self.setup_tray()
        self.load_settings()
        
        # 初始化状态指示器
        self.update_status("未启动", "#dc3545")
        
    def setup_ui(self):
        """设置用户界面"""
        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                background: white;
                margin-top: 5px;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background: #e9ecef;
                border: 1px solid #dee2e6;
                border-bottom: none;
                border-radius: 4px 4px 0 0;
                padding: 8px 16px;
                margin-right: 1px;
                font-weight: 500;
                color: #495057;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background: white;
                color: #007bff;
                border-color: #007bff;
            }
            QTabBar::tab:hover:!selected {
                background: #f8f9fa;
                color: #007bff;
            }
            QFrame#editFrame {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                background: white;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #495057;
                background: white;
            }
            QLineEdit, QTextEdit, QPlainTextEdit {
                border: 2px solid #e9ecef;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 13px;
                background: white;
                max-height: 32px;
            }
            QPlainTextEdit {
                max-height: none;
            }
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border-color: #007bff;
                outline: none;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #007bff, stop:1 #0056b3);
                border: none;
                border-radius: 4px;
                color: white;
                font-weight: 500;
                padding: 6px 12px;
                font-size: 13px;
                min-height: 24px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0056b3, stop:1 #004085);
            }
            QPushButton:pressed {
                background: #004085;
            }
            QPushButton:disabled {
                background: #6c757d;
                color: #adb5bd;
            }
            QPushButton.success {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #28a745, stop:1 #1e7e34);
            }
            QPushButton.success:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e7e34, stop:1 #155724);
            }
            QPushButton.danger {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #dc3545, stop:1 #c82333);
            }
            QPushButton.danger:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c82333, stop:1 #a71e2a);
            }
            QPushButton.secondary {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6c757d, stop:1 #545b62);
            }
            QPushButton.secondary:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #545b62, stop:1 #3d4142);
            }
            QListWidget {
                border: 2px solid #e9ecef;
                border-radius: 6px;
                background: white;
                alternate-background-color: #f8f9fa;
                selection-background-color: #007bff;
                selection-color: white;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f1f3f4;
                color: #495057;
            }
            QListWidget::item:selected {
                background: #007bff;
                color: white;
            }
            QListWidget::item:hover {
                background: #e3f2fd;
                color: #495057;
            }
            QSlider::groove:horizontal {
                border: 1px solid #dee2e6;
                height: 6px;
                background: #e9ecef;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #007bff;
                border: 2px solid #007bff;
                width: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #0056b3;
                border-color: #0056b3;
            }
            QLabel {
                color: #495057;
                font-size: 14px;
            }
            QLabel.title {
                font-size: 16px;
                font-weight: bold;
                color: #212529;
            }
            QLabel.subtitle {
                color: #6c757d;
                font-size: 12px;
            }
            QPlainTextEdit#promptContentEdit {
                padding-top: 0px;
            }
        """)
        
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # 创建选项卡
        tab_widget = QtWidgets.QTabWidget()
        
        # 基本设置选项卡
        basic_tab = self.create_basic_tab()
        tab_widget.addTab(basic_tab, "⚙️ 基本设置")
        
        # 提示词管理选项卡
        prompts_tab = self.create_prompts_tab()
        tab_widget.addTab(prompts_tab, "💬 提示词管理")
        
        # 运行日志选项卡
        logs_tab = self.create_log_tab()
        tab_widget.addTab(logs_tab, "📋 运行日志")
        
        layout.addWidget(tab_widget)
        
        # 控制按钮区域
        button_frame = QtWidgets.QFrame()
        button_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        button_layout = QtWidgets.QHBoxLayout(button_frame)
        
        # 状态指示器
        self.status_label = QtWidgets.QLabel("● 未启动")
        self.status_label.setStyleSheet("color: #dc3545; font-weight: bold; font-size: 14px;")
        
        self.start_btn = QtWidgets.QPushButton("🚀 启动监听")
        self.start_btn.setProperty("class", "success")
        self.start_btn.clicked.connect(self.start_listening)
        
        self.stop_btn = QtWidgets.QPushButton("⏹️ 停止监听")
        self.stop_btn.setProperty("class", "danger")
        self.stop_btn.clicked.connect(self.stop_listening)
        self.stop_btn.setEnabled(False)
        
        button_layout.addWidget(self.status_label)
        button_layout.addStretch()
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        
        layout.addWidget(button_frame)
    
    def create_basic_tab(self):
        """创建基本设置选项卡"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # API Key 设置
        api_group = QtWidgets.QGroupBox("🔑 API 配置")
        api_layout = QtWidgets.QVBoxLayout(api_group)
        api_layout.setSpacing(6)
        
        api_label = QtWidgets.QLabel("Gemini API Key:")
        api_label.setProperty("class", "title")
        
        self.api_key_edit = QtWidgets.QLineEdit()
        self.api_key_edit.setText(self.config_manager.get("api_key", ""))
        self.api_key_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("请输入您的 Gemini API Key")
        
        # API Key 显示/隐藏按钮
        api_container = QtWidgets.QHBoxLayout()
        self.show_api_btn = QtWidgets.QPushButton("👁️")
        self.show_api_btn.setProperty("class", "secondary")
        self.show_api_btn.setFixedSize(40, 40)
        self.show_api_btn.setToolTip("显示/隐藏 API Key")
        self.show_api_btn.clicked.connect(self.toggle_api_visibility)
        
        api_container.addWidget(self.api_key_edit)
        api_container.addWidget(self.show_api_btn)
        
        api_help = QtWidgets.QLabel("💡 在 Google AI Studio 获取您的 API Key")
        api_help.setProperty("class", "subtitle")
        api_help.setOpenExternalLinks(True)
        
        api_layout.addWidget(api_label)
        api_layout.addLayout(api_container)
        api_layout.addWidget(api_help)
        
        # 代理设置
        proxy_group = QtWidgets.QGroupBox("🌐 网络配置")
        proxy_layout = QtWidgets.QVBoxLayout(proxy_group)
        proxy_layout.setSpacing(6)
        
        proxy_label = QtWidgets.QLabel("代理地址 (可选):")
        proxy_label.setProperty("class", "title")
        
        self.proxy_edit = QtWidgets.QLineEdit()
        self.proxy_edit.setText(self.config_manager.get("proxy", ""))
        self.proxy_edit.setPlaceholderText("例如: http://127.0.0.1:7890")
        
        proxy_help = QtWidgets.QLabel("💡 如果网络访问受限，请配置代理服务器")
        proxy_help.setProperty("class", "subtitle")
        
        proxy_layout.addWidget(proxy_label)
        proxy_layout.addWidget(self.proxy_edit)
        proxy_layout.addWidget(proxy_help)
        
        # 透明度设置
        opacity_group = QtWidgets.QGroupBox("🎨 界面配置")
        opacity_layout = QtWidgets.QVBoxLayout(opacity_group)
        opacity_layout.setSpacing(6)
        
        opacity_label = QtWidgets.QLabel("浮窗背景透明度:")
        opacity_label.setProperty("class", "title")
        
        # 透明度滑块和数值显示
        opacity_container = QtWidgets.QHBoxLayout()
        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(50, 255)
        self.opacity_slider.setValue(self.config_manager.get("background_opacity", 120))
        self.opacity_slider.valueChanged.connect(self.update_opacity_label)
        
        self.opacity_value_label = QtWidgets.QLabel(str(self.opacity_slider.value()))
        self.opacity_value_label.setFixedWidth(30)
        self.opacity_value_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.opacity_value_label.setStyleSheet("font-weight: bold; color: #007bff;")
        
        opacity_container.addWidget(self.opacity_slider)
        opacity_container.addWidget(self.opacity_value_label)
        
        opacity_help = QtWidgets.QLabel("💡 数值越小越透明，越大越不透明")
        opacity_help.setProperty("class", "subtitle")
        
        opacity_layout.addWidget(opacity_label)
        opacity_layout.addLayout(opacity_container)
        opacity_layout.addWidget(opacity_help)
        
        # 保存按钮
        save_btn = QtWidgets.QPushButton("💾 保存设置")
        save_btn.setProperty("class", "success")
        save_btn.clicked.connect(self.save_basic_settings)
        save_btn.setFixedHeight(45)
        
        layout.addWidget(api_group)
        layout.addWidget(proxy_group)
        layout.addWidget(opacity_group)
        layout.addStretch()
        layout.addWidget(save_btn)
        
        return widget
    
    def create_prompts_tab(self):
        """创建提示词管理选项卡"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # 左侧：提示词选择
        left_group = QtWidgets.QGroupBox("📝 选择提示词")
        left_layout = QtWidgets.QVBoxLayout(left_group)
        left_layout.setSpacing(6)
        
        # 可搜索的下拉框
        prompt_select_container = QtWidgets.QHBoxLayout()
        
        self.prompts_combo = QtWidgets.QComboBox()
        self.prompts_combo.setEditable(True)
        self.prompts_combo.setPlaceholderText("🔍 搜索或选择提示词...")
        self.prompts_combo.currentIndexChanged.connect(self.on_prompt_selected)
        self.prompts_combo.setMinimumHeight(35)
        self.prompts_combo.setStyleSheet("""
            QComboBox {
                font-size: 14px;
                font-weight: 500;
                padding: 5px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #dee2e6;
                background: #f8f9fa;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #6c757d;
                width: 0;
                height: 0;
            }
        """)
        
        # 刷新按钮
        refresh_btn = QtWidgets.QPushButton("🔄")
        refresh_btn.setProperty("class", "secondary")
        refresh_btn.setToolTip("刷新列表")
        refresh_btn.setFixedSize(35, 35)
        refresh_btn.clicked.connect(self.load_prompts_list)
        
        prompt_select_container.addWidget(self.prompts_combo)
        prompt_select_container.addWidget(refresh_btn)
        
        left_layout.addLayout(prompt_select_container)
        
        # 右侧：编辑区域
        right_frame = QtWidgets.QFrame()
        right_frame.setObjectName("editFrame")
        right_layout = QtWidgets.QVBoxLayout(right_frame)
        right_layout.setSpacing(0)
        right_layout.setContentsMargins(10, 10, 10, 10)

        edit_label = QtWidgets.QLabel("✏️ 编辑提示词")
        edit_label.setProperty("class", "title")
        right_layout.addWidget(edit_label)
        right_layout.addSpacing(10)

        # 提示词名称行
        name_container = QtWidgets.QWidget()
        name_layout = QtWidgets.QHBoxLayout(name_container)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(8)
        
        name_label = QtWidgets.QLabel("提示词名称:")
        name_label.setMinimumWidth(80)
        name_label.setStyleSheet("font-weight: bold; color: #495057;")
        
        self.prompt_name_edit = QtWidgets.QLineEdit()
        self.prompt_name_edit.setPlaceholderText("例如: 代码实现助手")
        
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.prompt_name_edit)
        
        # 快捷键行
        hotkey_container = QtWidgets.QWidget()
        hotkey_layout = QtWidgets.QHBoxLayout(hotkey_container)
        hotkey_layout.setContentsMargins(0, 0, 0, 0)
        hotkey_layout.setSpacing(8)
        
        hotkey_label = QtWidgets.QLabel("快捷键:")
        hotkey_label.setMinimumWidth(80)
        hotkey_label.setStyleSheet("font-weight: bold; color: #495057;")
        
        self.prompt_hotkey_edit = QtWidgets.QLineEdit()
        self.prompt_hotkey_edit.setPlaceholderText("例如: alt+g")
        self.prompt_hotkey_edit.setMaximumWidth(150)
        self.prompt_hotkey_edit.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        
        hotkey_help_btn = QtWidgets.QPushButton("❓")
        hotkey_help_btn.setFixedSize(40, 40)
        hotkey_help_btn.setToolTip("快捷键格式帮助")
        hotkey_help_btn.clicked.connect(self.show_hotkey_help)
        hotkey_help_btn.setStyleSheet("""
            QPushButton {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 20px;
                font-size: 22px;
                font-weight: bold;
                color: #6c757d;
                padding: 0;
            }
            QPushButton:hover {
                background: #e9ecef;
                color: #495057;
            }
        """)
        
        hotkey_layout.addWidget(hotkey_label)
        hotkey_layout.addWidget(self.prompt_hotkey_edit)
        hotkey_layout.addWidget(hotkey_help_btn)
        hotkey_layout.addStretch()

        # 内容编辑
        content_label = QtWidgets.QLabel("提示词内容:")
        content_label.setProperty("class", "title")
        
        self.prompt_content_edit = QtWidgets.QPlainTextEdit()
        self.prompt_content_edit.setObjectName("promptContentEdit")
        self.prompt_content_edit.setPlaceholderText("请输入详细的提示词内容...")
        self.prompt_content_edit.setMinimumHeight(300)

        
        # 字符计数
        self.char_count_label = QtWidgets.QLabel("字符数: 0")
        self.char_count_label.setProperty("class", "subtitle")
        self.char_count_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.prompt_content_edit.textChanged.connect(self.update_char_count)
        
        # 操作按钮 - 使用网格布局
        button_widget = QtWidgets.QWidget()
        button_layout = QtWidgets.QGridLayout(button_widget)
        button_layout.setSpacing(4)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        add_btn = QtWidgets.QPushButton("➕ 添加")
        add_btn.setProperty("class", "success")
        add_btn.clicked.connect(self.add_prompt)
        
        update_btn = QtWidgets.QPushButton("✏️ 更新")
        update_btn.clicked.connect(self.update_prompt)
        
        button_layout.addWidget(add_btn, 0, 0)
        button_layout.addWidget(update_btn, 0, 1)
        
        delete_btn = QtWidgets.QPushButton("🗑️ 删除")
        delete_btn.setProperty("class", "danger")
        delete_btn.clicked.connect(self.delete_prompt)
        
        clear_btn = QtWidgets.QPushButton("🧹 清空")
        clear_btn.setProperty("class", "secondary")
        clear_btn.clicked.connect(self.clear_prompt_fields)
        
        button_layout.addWidget(delete_btn, 1, 0)
        button_layout.addWidget(clear_btn, 1, 1)
        
        button_layout.setColumnStretch(0, 1)
        button_layout.setColumnStretch(1, 1)

        # 将所有控件直接添加到 right_layout
        right_layout.addWidget(name_container)
        right_layout.addWidget(hotkey_container)
        right_layout.addSpacing(15)

        # 创建一个专门的容器来处理内容区域的布局
        content_area_widget = QtWidgets.QWidget()
        content_area_layout = QtWidgets.QVBoxLayout(content_area_widget)
        content_area_layout.setContentsMargins(0, 0, 0, 0)
        content_area_layout.setSpacing(2)  # 精确控制标签和输入框的间距
        content_area_layout.addWidget(content_label)
        content_area_layout.addWidget(self.prompt_content_edit)

        right_layout.addWidget(content_area_widget)
        right_layout.addSpacing(10)
        right_layout.addWidget(self.char_count_label)
        right_layout.addWidget(button_widget)
        
        layout.addWidget(left_group, 1)  # 左侧占1份
        layout.addWidget(right_frame, 3)  # 右侧占3份，更多空间
        
        # 加载提示词列表
        self.load_prompts_list()
        
        return widget
    
    def create_log_tab(self):
        """创建运行日志选项卡"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # 日志控制区域
        control_frame = QtWidgets.QFrame()
        control_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        control_layout = QtWidgets.QHBoxLayout(control_frame)
        
        # 日志级别过滤
        level_label = QtWidgets.QLabel("📊 日志级别:")
        level_label.setProperty("class", "title")
        
        self.log_level_combo = QtWidgets.QComboBox()
        self.log_level_combo.addItems(["全部", "信息", "警告", "错误"])
        self.log_level_combo.currentTextChanged.connect(self.filter_logs)
        
        # 自动滚动开关
        self.auto_scroll_check = QtWidgets.QCheckBox("📜 自动滚动")
        self.auto_scroll_check.setChecked(True)
        
        # 日志统计
        self.log_stats_label = QtWidgets.QLabel("📈 总计: 0 条")
        self.log_stats_label.setProperty("class", "subtitle")
        
        control_layout.addWidget(level_label)
        control_layout.addWidget(self.log_level_combo)
        control_layout.addWidget(self.auto_scroll_check)
        control_layout.addStretch()
        control_layout.addWidget(self.log_stats_label)
        
        # 日志显示区域
        log_group = QtWidgets.QGroupBox("📋 运行日志")
        log_layout = QtWidgets.QVBoxLayout(log_group)
        
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(200)
        self.log_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                line-height: 1.4;
                background: #f8f9fa;
                border: 1px solid #e9ecef;
            }
        """)
        
        log_layout.addWidget(self.log_text)
        
        # 操作按钮区域
        button_frame = QtWidgets.QFrame()
        button_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        button_layout = QtWidgets.QHBoxLayout(button_frame)
        
        # 日志操作按钮
        clear_btn = QtWidgets.QPushButton("🧹 清空日志")
        clear_btn.setProperty("class", "secondary")
        clear_btn.clicked.connect(self.clear_logs)
        
        export_btn = QtWidgets.QPushButton("💾 导出日志")
        export_btn.clicked.connect(self.export_logs)
        
        refresh_btn = QtWidgets.QPushButton("🔄 刷新")
        refresh_btn.setProperty("class", "secondary")
        refresh_btn.clicked.connect(self.refresh_logs)
        
        # 搜索功能
        search_label = QtWidgets.QLabel("🔍")
        self.log_search_edit = QtWidgets.QLineEdit()
        self.log_search_edit.setPlaceholderText("搜索日志内容...")
        self.log_search_edit.textChanged.connect(self.search_logs)
        
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(export_btn)
        button_layout.addWidget(refresh_btn)
        button_layout.addStretch()
        button_layout.addWidget(search_label)
        button_layout.addWidget(self.log_search_edit)
        
        layout.addWidget(control_frame)
        layout.addWidget(log_group, 1)  # 给日志区域更多空间
        layout.addWidget(button_frame)
        
        # 连接日志更新信号
        self.log_manager.log_updated.connect(self.append_log)
        
        return widget
    
    def load_settings(self):
        """加载配置到界面"""
        # 加载基本设置
        self.api_key_edit.setText(self.config_manager.get("api_key", ""))
        self.proxy_edit.setText(self.config_manager.get("proxy", ""))
        self.opacity_slider.setValue(self.config_manager.get("background_opacity", 120))
        
        # 加载提示词列表
        self.load_prompts_list()
    
    def setup_tray(self):
        """设置系统托盘"""
        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        
        # 创建托盘图标（使用默认图标）
        icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        
        # 创建托盘菜单
        tray_menu = QtWidgets.QMenu()
        
        show_action = tray_menu.addAction("显示配置")
        show_action.triggered.connect(self.show)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self.quit_app)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
    def tray_icon_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
    
    def toggle_api_visibility(self):
        """切换 API Key 显示/隐藏"""
        if self.api_key_edit.echoMode() == QtWidgets.QLineEdit.EchoMode.Password:
            self.api_key_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Normal)
            self.show_api_btn.setText("🙈")
        else:
            self.api_key_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            self.show_api_btn.setText("👁️")
    
    def update_opacity_label(self, value):
        """更新透明度标签"""
        self.opacity_value_label.setText(str(value))
        # 实时预览透明度变化
        if self.overlay:
            self.config_manager.config["background_opacity"] = value
            self.overlay.update_background_opacity()
    
    def validate_proxy_url(self, proxy: str) -> Tuple[bool, str]:
        """验证代理URL格式"""
        if not proxy:
            return True, ""  # 空代理是允许的

        import urllib.parse
        try:
            parsed = urllib.parse.urlparse(proxy)
            if not parsed.scheme in ['http', 'https', 'socks5']:
                return False, "代理协议必须是 http, https 或 socks5"
            if not parsed.netloc:
                return False, "代理地址格式不正确"
            return True, ""
        except Exception as e:
            return False, f"代理地址解析失败: {e}"

    def save_basic_settings(self):
        """保存基本设置"""
        api_key = self.api_key_edit.text().strip()
        proxy = self.proxy_edit.text().strip()

        # 验证 API Key
        if not api_key:
            QtWidgets.QMessageBox.warning(self, "警告", "请输入 API Key")
            return

        if len(api_key) < 20:  # Google API Key 通常很长
            reply = QtWidgets.QMessageBox.question(
                self, "确认",
                "API Key 看起来较短，确定要保存吗？",
                QtWidgets.QMessageBox.StandardButton.Yes |
                QtWidgets.QMessageBox.StandardButton.No
            )
            if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                return

        # 验证代理设置
        proxy_valid, proxy_error = self.validate_proxy_url(proxy)
        if not proxy_valid:
            QtWidgets.QMessageBox.warning(self, "代理设置错误", proxy_error)
            return

        # 测试API连接（可选）
        reply = QtWidgets.QMessageBox.question(
            self, "测试连接",
            "是否要测试 API 连接？",
            QtWidgets.QMessageBox.StandardButton.Yes |
            QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            # 显示进度对话框
            progress = QtWidgets.QProgressDialog("正在测试 API 连接...", "取消", 0, 0, self)
            progress.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
            progress.setAutoClose(True)
            progress.show()
            QtWidgets.QApplication.processEvents()

            # 测试网络
            network_ok, network_msg = check_network_connectivity()
            if not network_ok:
                progress.close()
                QtWidgets.QMessageBox.warning(self, "网络错误", network_msg)
                return

            # 测试API
            api_ok, api_msg = check_api_connectivity(api_key, proxy)
            progress.close()

            if not api_ok:
                QtWidgets.QMessageBox.warning(self, "API 连接失败", api_msg)
                reply = QtWidgets.QMessageBox.question(
                    self, "确认",
                    "API 连接测试失败，是否仍要保存设置？",
                    QtWidgets.QMessageBox.StandardButton.Yes |
                    QtWidgets.QMessageBox.StandardButton.No
                )
                if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                    return
            else:
                QtWidgets.QMessageBox.information(self, "成功", "API 连接测试成功！")

        # 保存设置
        self.config_manager.set("api_key", api_key)
        self.config_manager.set("proxy", proxy)
        self.config_manager.set("background_opacity", self.opacity_slider.value())

        # 更新浮窗透明度
        if self.overlay:
            self.overlay.update_background_opacity()

        self.log_manager.add_log("基本设置已保存")
        QtWidgets.QMessageBox.information(self, "成功", "基本设置已保存")
    
    def load_prompts_list(self):
        """加载提示词列表"""
        self.prompts_combo.clear()
        prompts = self.config_manager.get("prompts", [])
        for prompt in prompts:
            item_text = f"{prompt['name']} ({prompt['hotkey']})"
            self.prompts_combo.addItem(item_text)
    
    def on_prompt_selected(self, index):
        """选择提示词时的处理"""
        if index >= 0:
            prompts = self.config_manager.get("prompts", [])
            if index < len(prompts):
                prompt = prompts[index]
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
    
    def delete_prompt(self):
        """删除选中的提示词"""
        index = self.prompts_combo.currentIndex()
        if index < 0:
            QtWidgets.QMessageBox.warning(self, "警告", "请先选择要删除的提示词")
            return
        
        prompts = self.config_manager.get("prompts", [])
        if index < len(prompts):
            name = prompts[index]['name']
            reply = QtWidgets.QMessageBox.question(self, "确认", f"确定要删除提示词 '{name}' 吗？")
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                prompts.pop(index)
                self.config_manager.set("prompts", prompts)
                self.load_prompts_list()
                self.clear_prompt_fields()
                self.log_manager.add_log(f"删除提示词: {name}")
    
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
• alt+z
• ctrl+shift+a
• f5
• ctrl+space
        """
        QtWidgets.QMessageBox.information(self, "快捷键格式帮助", help_text.strip())
    
    def append_log(self, log_entry):
        """添加日志到界面"""
        self.log_text.append(log_entry)
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_logs(self):
        """清空日志"""
        self.log_text.clear()
        self.log_manager.logs.clear()
        self.update_log_stats()
    
    def filter_logs(self, level):
        """根据级别过滤日志"""
        # 这里可以实现日志级别过滤逻辑
        # 暂时保持简单实现
        pass
    
    def export_logs(self):
        """导出日志到文件"""
        try:
            from datetime import datetime
            filename = f"gemini_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "导出日志", filename, "文本文件 (*.txt)")
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                QtWidgets.QMessageBox.information(self, "成功", f"日志已导出到: {file_path}")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "错误", f"导出失败: {e}")
    
    def refresh_logs(self):
        """刷新日志显示"""
        self.log_text.clear()
        for log_entry in self.log_manager.logs:
            self.log_text.append(log_entry)
        self.update_log_stats()
    
    def search_logs(self, text):
        """搜索日志内容"""
        if not text:
            # 如果搜索框为空，显示所有日志
            self.refresh_logs()
            return
        
        # 高亮搜索结果
        cursor = self.log_text.textCursor()
        format = QtGui.QTextCharFormat()
        format.setBackground(QtGui.QColor("yellow"))
        
        # 清除之前的高亮
        cursor.select(QtGui.QTextCursor.SelectionType.Document)
        cursor.setCharFormat(QtGui.QTextCharFormat())
        
        # 搜索并高亮
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.Start)
        while cursor.position() < len(self.log_text.toPlainText()):
            cursor = self.log_text.document().find(text, cursor)
            if cursor.isNull():
                break
            cursor.setCharFormat(format)
    
    def update_log_stats(self):
        """更新日志统计信息"""
        count = len(self.log_manager.logs)
        self.log_stats_label.setText(f"📈 总计: {count} 条")
    
    def update_status(self, status, color="#dc3545"):
        """更新状态显示"""
        self.status_label.setText(f"● {status}")
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px;")
    
    def parse_hotkey(self, hotkey_str):
        """解析快捷键字符串为pynput格式"""
        parts = hotkey_str.lower().split('+')
        keys = []
        
        for part in parts:
            part = part.strip()
            if part == 'ctrl':
                keys.append(Key.ctrl_l)
            elif part == 'alt':
                keys.append(Key.alt_l)
            elif part == 'shift':
                keys.append(Key.shift_l)
            elif part == 'cmd' or part == 'win':
                keys.append(Key.cmd)
            elif part == 'up':
                keys.append(Key.up)
            elif part == 'down':
                keys.append(Key.down)
            elif part == 'left':
                keys.append(Key.left)
            elif part == 'right':
                keys.append(Key.right)
            elif part == 'space':
                keys.append(Key.space)
            elif part == 'enter':
                keys.append(Key.enter)
            elif part == 'tab':
                keys.append(Key.tab)
            elif part == 'esc':
                keys.append(Key.esc)
            elif len(part) == 1:
                keys.append(KeyCode.from_char(part))
            else:
                # 尝试作为特殊键处理
                try:
                    keys.append(getattr(Key, part))
                except AttributeError:
                    self.log_manager.add_log(f"未知的键: {part}", "WARNING")
                    continue
        
        return keys
    
    def on_key_press(self, key):
        """键盘按下事件处理"""
        try:
            self.pressed_keys.add(key)
            # 通知所有热键有键被按下
            for hotkey in self.hotkeys.values():
                hotkey.press(key)
        except Exception as e:
            pass  # 忽略键盘事件处理错误
    
    def on_key_release(self, key):
        """键盘释放事件处理"""
        try:
            self.pressed_keys.discard(key)
            # 通知所有热键有键被释放
            for hotkey in self.hotkeys.values():
                hotkey.release(key)
        except Exception as e:
            pass  # 忽略键盘事件处理错误
     
    def start_listening(self):
        """启动快捷键监听"""
        try:
            # 设置代理
            proxy = self.config_manager.get("proxy", "")
            if proxy:
                os.environ['HTTPS_PROXY'] = proxy
            
            # 创建浮窗
            if not self.overlay:
                self.overlay = Overlay(self.config_manager)
            
            # 清除旧的快捷键绑定
            self.stop_listening()
            
            # 清空热键字典
            self.hotkeys.clear()
            
            # 绑定提示词快捷键
            prompts = self.config_manager.get("prompts", [])
            for i, prompt in enumerate(prompts):
                hotkey_str = prompt['hotkey']
                try:
                    keys = self.parse_hotkey(hotkey_str)
                    if keys:
                        handler = lambda p=prompt: threading.Thread(target=lambda: self.trigger_prompt(p), daemon=True).start()
                        hotkey = HotKey(keys, handler)
                        self.hotkeys[hotkey_str] = hotkey
                        self.log_manager.add_log(f"绑定快捷键: {hotkey_str} -> {prompt['name']}")
                except Exception as e:
                    self.log_manager.add_log(f"绑定快捷键失败 {hotkey_str}: {e}", "ERROR")
            
            # 绑定控制快捷键
            control_hotkeys = self.config_manager.get("hotkeys", {})
            
            # 浮窗切换快捷键
            toggle_key = control_hotkeys.get("toggle", "alt+q")
            try:
                keys = self.parse_hotkey(toggle_key)
                if keys:
                    hotkey = HotKey(keys, self.overlay.toggle)
                    self.hotkeys[toggle_key] = hotkey
                    self.log_manager.add_log(f"绑定浮窗切换快捷键: {toggle_key}")
            except Exception as e:
                self.log_manager.add_log(f"绑定浮窗切换快捷键失败 {toggle_key}: {e}", "ERROR")
            
            # 绑定纯截图快捷键
            screenshot_only_key = control_hotkeys.get("screenshot_only", "alt+w")
            try:
                keys = self.parse_hotkey(screenshot_only_key)
                if keys:
                    handler = lambda: threading.Thread(target=self.capture_screenshot_only, daemon=True).start()
                    hotkey = HotKey(keys, handler)
                    self.hotkeys[screenshot_only_key] = hotkey
                    self.log_manager.add_log(f"绑定纯截图快捷键: {screenshot_only_key}")
            except Exception as e:
                self.log_manager.add_log(f"绑定纯截图快捷键失败 {screenshot_only_key}: {e}", "ERROR")
            
            # 滚动快捷键
            scroll_up_key = control_hotkeys.get("scroll_up", "alt+up")
            try:
                keys = self.parse_hotkey(scroll_up_key)
                if keys:
                    hotkey = HotKey(keys, self.overlay.scroll_up)
                    self.hotkeys[scroll_up_key] = hotkey
                    self.log_manager.add_log(f"绑定向上滚动快捷键: {scroll_up_key}")
            except Exception as e:
                self.log_manager.add_log(f"绑定向上滚动快捷键失败 {scroll_up_key}: {e}", "ERROR")
            
            scroll_down_key = control_hotkeys.get("scroll_down", "alt+down")
            try:
                keys = self.parse_hotkey(scroll_down_key)
                if keys:
                    hotkey = HotKey(keys, self.overlay.scroll_down)
                    self.hotkeys[scroll_down_key] = hotkey
                    self.log_manager.add_log(f"绑定向下滚动快捷键: {scroll_down_key}")
            except Exception as e:
                self.log_manager.add_log(f"绑定向下滚动快捷键失败 {scroll_down_key}: {e}", "ERROR")
            
            # 启动键盘监听器
            self.keyboard_listener = Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            self.keyboard_listener.start()
            
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            
            # 更新状态指示器
            self.update_status("运行中", "#28a745")
            
            self.log_manager.add_log("快捷键监听已启动 (使用底层键盘钩子)")
            
            # 最小化到托盘
            self.hide()
            self.tray_icon.show()
            self.tray_icon.showMessage("Gemini 截图助手", "已启动并最小化到托盘", QtWidgets.QSystemTrayIcon.MessageIcon.Information, 500)
            
        except Exception as e:
            # 更新状态指示器为错误状态
            self.update_status("启动失败", "#dc3545")
            self.log_manager.add_log(f"启动监听失败: {e}", "ERROR")
            QtWidgets.QMessageBox.critical(self, "错误", f"启动失败: {e}")
    
    def stop_listening(self):
        """停止快捷键监听"""
        try:
            # 停止键盘监听器
            if self.keyboard_listener and self.keyboard_listener.running:
                self.keyboard_listener.stop()
                self.keyboard_listener = None
            
            # 清空热键字典
            self.hotkeys.clear()
            self.pressed_keys.clear()
            
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            
            # 更新状态指示器
            self.update_status("已停止", "#dc3545")
            
            self.log_manager.add_log("快捷键监听已停止")
            
        except Exception as e:
            self.log_manager.add_log(f"停止监听失败: {e}", "ERROR")
    
    def capture_screenshot_only(self):
        """仅截图保存到历史记录"""
        try:
            png = capture_screen()

            # 实施LRU策略，限制历史截图数量
            if len(self.screenshot_history) >= self.MAX_SCREENSHOT_HISTORY:
                # 移除最旧的截图，释放内存
                removed = self.screenshot_history.pop(0)
                del removed  # 显式删除以释放内存
                self.log_manager.add_log(f"已达到最大截图数量限制({self.MAX_SCREENSHOT_HISTORY})，移除最旧的截图")

            self.screenshot_history.append(png)

            # 计算当前内存占用（估算）
            total_size_mb = sum(len(img) for img in self.screenshot_history) / (1024 * 1024)
            self.log_manager.add_log(
                f"截图已保存到历史记录 (共 {len(self.screenshot_history)} 张, "
                f"约 {total_size_mb:.1f} MB)"
            )
        except Exception as e:
            self.log_manager.add_log(f"截图保存失败: {e}", "ERROR")
    
    def trigger_prompt(self, prompt):
        """触发提示词处理"""
        try:
            self.log_manager.add_log(f"触发提示词: {prompt['name']}")

            # 截屏当前画面
            current_png = capture_screen()
            self.log_manager.add_log("当前截屏完成")

            # 准备所有图片（历史截图 + 当前截图）
            all_images = self.screenshot_history + [current_png]
            total_size_mb = sum(len(img) for img in all_images) / (1024 * 1024)
            self.log_manager.add_log(
                f"准备发送 {len(all_images)} 张图片到 Gemini "
                f"(总大小: {total_size_mb:.1f} MB)"
            )

            # 调用 Gemini（支持多图片）
            md = ask_gemini_multi_images(all_images, prompt['content'], self.config_manager, self.log_manager)

            # 清空历史截图，释放内存
            for img in self.screenshot_history:
                del img
            self.screenshot_history.clear()
            import gc
            gc.collect()  # 强制垃圾回收
            self.log_manager.add_log("历史截图已清空，内存已释放")
            
            # 提取代码块并复制到剪贴板
            code_blocks = extract_code_blocks(md)
            if code_blocks:
                try:
                    pyperclip.copy(code_blocks)
                    self.log_manager.add_log(f"代码已复制到剪贴板 ({len(code_blocks)} 字符)")
                except Exception as e:
                    self.log_manager.add_log(f"复制到剪贴板失败: {e}", "ERROR")
            
            # 渲染并显示
            html = MarkdownIt("commonmark", {"html": True}).render(md)
            if self.overlay:
                self.overlay.content_ready.emit(html)
            
        except Exception as e:
            self.log_manager.add_log(f"处理提示词失败: {e}", "ERROR")
    
    def closeEvent(self, event):
        """关闭事件处理"""
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            self.quit_app()
    
    def quit_app(self):
        """退出应用"""
        self.stop_listening()
        
        # 确保键盘监听器完全停止
        if self.keyboard_listener:
            try:
                self.keyboard_listener.stop()
                self.keyboard_listener.join(timeout=1.0)  # 等待最多1秒
            except:
                pass
        
        # 释放单实例锁
        if self.single_instance:
            self.single_instance.release_lock()
        
        if self.overlay:
            self.overlay.close()
        self.tray_icon.hide()
        QtWidgets.QApplication.quit()

# ────────────────────── 主 程 序 ────────────────────── #
if __name__ == "__main__":
    # 创建单实例管理器
    single_instance = SingleInstance()
    
    # 检查是否已有实例在运行
    if single_instance.is_already_running():
        # 创建临时应用程序用于显示消息框
        temp_app = QtWidgets.QApplication(sys.argv)
        QtWidgets.QMessageBox.warning(
            None, 
            "程序已运行", 
            "Gemini 截图助手已经在运行中！\n\n请检查系统托盘或任务管理器。",
            QtWidgets.QMessageBox.StandardButton.Ok
        )
        sys.exit(0)
    
    # 获取单实例锁
    if not single_instance.acquire_lock():
        temp_app = QtWidgets.QApplication(sys.argv)
        QtWidgets.QMessageBox.critical(
            None, 
            "启动失败", 
            "无法获取程序锁，启动失败！",
            QtWidgets.QMessageBox.StandardButton.Ok
        )
        sys.exit(1)
    
    app = QtWidgets.QApplication(sys.argv)
    
    # 检查系统托盘支持
    if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
        QtWidgets.QMessageBox.critical(None, "系统托盘", "系统不支持托盘功能")
        single_instance.release_lock()
        sys.exit(1)
    
    # 创建配置管理器和日志管理器
    config_manager = ConfigManager()
    log_manager = LogManager()
    
    # 创建并显示配置窗口
    config_window = ConfigWindow(config_manager, log_manager, single_instance)
    config_window.show()
    
    try:
        sys.exit(app.exec())
    finally:
        # 确保释放锁
        single_instance.release_lock()
