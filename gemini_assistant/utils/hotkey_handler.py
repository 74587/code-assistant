"""
热键处理模块
处理全局热键的解析、绑定和管理
"""

from typing import List, Dict, Set, Callable
from pynput.keyboard import Key, KeyCode, Listener, HotKey


class HotkeyHandler:
    def __init__(self):
        self.keyboard_listener = None
        self.hotkeys: Dict[str, HotKey] = {}
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

    def register_hotkey(self, hotkey_str: str, callback: Callable) -> bool:
        """注册热键"""
        try:
            keys = self.parse_hotkey(hotkey_str)
            if keys:
                hotkey = HotKey(keys, callback)
                self.hotkeys[hotkey_str] = hotkey
                return True
        except Exception as e:
            print(f"注册热键失败 {hotkey_str}: {e}")
        return False

    def unregister_hotkey(self, hotkey_str: str) -> None:
        """注销热键"""
        if hotkey_str in self.hotkeys:
            del self.hotkeys[hotkey_str]

    def clear_hotkeys(self) -> None:
        """清空所有热键"""
        self.hotkeys.clear()
        self.pressed_keys.clear()

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