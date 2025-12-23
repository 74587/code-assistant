"""
热键处理模块
处理全局热键的解析、绑定和管理
"""

from typing import List, Dict, Set, Callable, Optional, Tuple
from pynput.keyboard import Key, KeyCode, Listener, HotKey


class HotkeyConflictError(Exception):
    """热键冲突异常"""
    def __init__(self, hotkey: str, existing_name: str):
        self.hotkey = hotkey
        self.existing_name = existing_name
        super().__init__(f"热键 '{hotkey}' 已被 '{existing_name}' 使用")


class HotkeyHandler:
    def __init__(self):
        self.keyboard_listener = None
        self.hotkeys: Dict[str, HotKey] = {}
        self.hotkey_names: Dict[str, str] = {}  # hotkey_str -> name 映射
        self.pressed_keys: Set = set()

    def parse_hotkey(self, hotkey_str: str) -> List:
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
            elif part == 'backspace':
                keys.append(Key.backspace)
            elif part == 'delete':
                keys.append(Key.delete)
            elif part == 'home':
                keys.append(Key.home)
            elif part == 'end':
                keys.append(Key.end)
            elif part == 'pageup':
                keys.append(Key.page_up)
            elif part == 'pagedown':
                keys.append(Key.page_down)
            elif part.startswith('f') and part[1:].isdigit():
                # 功能键 F1-F12
                try:
                    keys.append(getattr(Key, part))
                except AttributeError:
                    print(f"未知的功能键: {part}")
            elif len(part) == 1:
                keys.append(KeyCode.from_char(part))
            else:
                # 尝试作为特殊键处理
                try:
                    keys.append(getattr(Key, part))
                except AttributeError:
                    print(f"未知的键: {part}")
                    continue

        return keys

    def normalize_hotkey(self, hotkey_str: str) -> str:
        """标准化热键字符串（用于比较）"""
        parts = hotkey_str.lower().split('+')
        # 分离修饰键和普通键
        modifiers = []
        keys = []
        modifier_order = ['ctrl', 'alt', 'shift', 'cmd', 'win']

        for part in parts:
            part = part.strip()
            if part in modifier_order:
                modifiers.append(part)
            else:
                keys.append(part)

        # 按固定顺序排列修饰键
        modifiers.sort(key=lambda x: modifier_order.index(x) if x in modifier_order else 99)
        return '+'.join(modifiers + keys)

    def check_conflict(self, hotkey_str: str, exclude_name: str = None) -> Optional[str]:
        """
        检查热键是否与已注册的热键冲突
        返回冲突的热键名称，如果没有冲突返回 None
        """
        normalized = self.normalize_hotkey(hotkey_str)

        for registered_hotkey, name in self.hotkey_names.items():
            if exclude_name and name == exclude_name:
                continue
            if self.normalize_hotkey(registered_hotkey) == normalized:
                return name

        return None

    def register_hotkey(self, hotkey_str: str, callback: Callable,
                        name: str = None, check_conflict: bool = True) -> bool:
        """
        注册热键

        Args:
            hotkey_str: 热键字符串，如 "alt+1"
            callback: 热键触发时的回调函数
            name: 热键名称（用于冲突检测和显示）
            check_conflict: 是否检查冲突

        Returns:
            是否注册成功

        Raises:
            HotkeyConflictError: 如果热键已被注册且 check_conflict=True
        """
        try:
            # 检查冲突
            if check_conflict:
                conflict_name = self.check_conflict(hotkey_str, exclude_name=name)
                if conflict_name:
                    raise HotkeyConflictError(hotkey_str, conflict_name)

            keys = self.parse_hotkey(hotkey_str)
            if keys:
                hotkey = HotKey(keys, callback)
                self.hotkeys[hotkey_str] = hotkey
                if name:
                    self.hotkey_names[hotkey_str] = name
                return True
        except HotkeyConflictError:
            raise
        except Exception as e:
            print(f"注册热键失败 {hotkey_str}: {e}")
        return False

    def unregister_hotkey(self, hotkey_str: str) -> None:
        """注销热键"""
        if hotkey_str in self.hotkeys:
            del self.hotkeys[hotkey_str]
        if hotkey_str in self.hotkey_names:
            del self.hotkey_names[hotkey_str]

    def clear_hotkeys(self) -> None:
        """清空所有热键"""
        self.hotkeys.clear()
        self.hotkey_names.clear()
        self.pressed_keys.clear()

    def get_registered_hotkeys(self) -> Dict[str, str]:
        """获取所有已注册的热键及其名称"""
        return self.hotkey_names.copy()

    def validate_hotkey_format(self, hotkey_str: str) -> Tuple[bool, str]:
        """
        验证热键格式是否正确

        Returns:
            (是否有效, 错误信息)
        """
        if not hotkey_str or not isinstance(hotkey_str, str):
            return False, "热键不能为空"

        parts = hotkey_str.lower().split('+')
        if len(parts) < 2:
            return False, "热键必须包含修饰键（如 Alt、Ctrl）和一个按键"

        modifiers = {'ctrl', 'alt', 'shift', 'cmd', 'win'}
        has_modifier = False
        has_key = False

        for part in parts:
            part = part.strip()
            if part in modifiers:
                has_modifier = True
            elif part:
                has_key = True

        if not has_modifier:
            return False, "热键必须包含至少一个修饰键（Alt、Ctrl、Shift）"
        if not has_key:
            return False, "热键必须包含一个触发键"

        return True, ""

    def on_key_press(self, key):
        """键盘按下事件处理"""
        try:
            self.pressed_keys.add(key)
            # 通知所有热键有键被按下
            for hotkey in self.hotkeys.values():
                hotkey.press(key)
        except Exception:
            pass  # 忽略键盘事件处理错误

    def on_key_release(self, key):
        """键盘释放事件处理"""
        try:
            self.pressed_keys.discard(key)
            # 通知所有热键有键被释放
            for hotkey in self.hotkeys.values():
                hotkey.release(key)
        except Exception:
            pass  # 忽略键盘事件处理错误

    def start_listening(self) -> bool:
        """启动键盘监听"""
        try:
            if self.keyboard_listener and self.keyboard_listener.running:
                return True

            self.keyboard_listener = Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            # 设置为守护线程,确保程序退出时线程自动终止
            self.keyboard_listener.daemon = True
            self.keyboard_listener.start()
            return True
        except Exception as e:
            print(f"启动键盘监听失败: {e}")
            return False

    def stop_listening(self) -> None:
        """停止键盘监听"""
        try:
            if self.keyboard_listener and self.keyboard_listener.running:
                self.keyboard_listener.stop()
                self.keyboard_listener = None

            self.clear_hotkeys()
        except Exception as e:
            print(f"停止键盘监听失败: {e}")

    def is_listening(self) -> bool:
        """检查是否正在监听"""
        return (self.keyboard_listener is not None and
                self.keyboard_listener.running)