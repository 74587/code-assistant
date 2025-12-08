"""
快捷键配置模块
集中管理系统保留快捷键，避免与用户自定义快捷键冲突
"""

from typing import Dict, List, Tuple, Optional


class HotkeyConfig:
    """快捷键配置管理"""

    # 系统控制快捷键 - 用于核心功能，用户不可用于提示词
    SYSTEM_CONTROL_HOTKEYS: Dict[str, str] = {
        "alt+z": "发送提示词",
        "alt+q": "显示/隐藏浮窗",
        "alt+w": "截图",
        "alt+v": "清空截图历史",
        "alt+s": "切换AI服务商",
        "alt+up": "向上滚动",
        "alt+down": "向下滚动",
    }

    # 提示词可用快捷键 - alt+1 到 alt+9，用户可以分配给提示词
    PROMPT_HOTKEY_SLOTS: List[str] = [
        "alt+1", "alt+2", "alt+3", "alt+4", "alt+5",
        "alt+6", "alt+7", "alt+8", "alt+9",
    ]

    # 合并的保留快捷键（向后兼容）
    RESERVED_HOTKEYS: Dict[str, str] = {
        **SYSTEM_CONTROL_HOTKEYS,
    }

    # 常见系统快捷键 - 建议避免使用
    SYSTEM_HOTKEYS: Dict[str, str] = {
        "alt+tab": "Windows 切换窗口",
        "alt+f4": "关闭窗口",
        "ctrl+c": "复制",
        "ctrl+v": "粘贴",
        "ctrl+x": "剪切",
        "ctrl+z": "撤销",
        "ctrl+a": "全选",
        "ctrl+s": "保存",
        "win+d": "显示桌面",
        "win+e": "打开资源管理器",
    }

    @classmethod
    def is_reserved(cls, hotkey: str) -> Tuple[bool, str]:
        """
        检查快捷键是否被系统控制功能占用（不包括提示词槽位）

        Returns:
            (是否保留, 保留原因/用途)
        """
        normalized = cls.normalize_hotkey(hotkey)

        if normalized in cls.SYSTEM_CONTROL_HOTKEYS:
            return True, cls.SYSTEM_CONTROL_HOTKEYS[normalized]

        return False, ""

    @classmethod
    def is_prompt_slot(cls, hotkey: str) -> bool:
        """检查是否是提示词槽位快捷键 (alt+1~9)"""
        normalized = cls.normalize_hotkey(hotkey)
        return normalized in cls.PROMPT_HOTKEY_SLOTS

    @classmethod
    def get_available_prompt_slots(cls, used_hotkeys: List[str]) -> List[str]:
        """
        获取未被使用的提示词快捷键槽位

        Args:
            used_hotkeys: 已使用的快捷键列表

        Returns:
            可用的快捷键列表
        """
        used_normalized = {cls.normalize_hotkey(h) for h in used_hotkeys}
        return [slot for slot in cls.PROMPT_HOTKEY_SLOTS if slot not in used_normalized]

    @classmethod
    def is_system_hotkey(cls, hotkey: str) -> Tuple[bool, str]:
        """
        检查是否是常见系统快捷键

        Returns:
            (是否是系统快捷键, 用途说明)
        """
        normalized = cls.normalize_hotkey(hotkey)

        if normalized in cls.SYSTEM_HOTKEYS:
            return True, cls.SYSTEM_HOTKEYS[normalized]

        return False, ""

    @classmethod
    def normalize_hotkey(cls, hotkey: str) -> str:
        """标准化快捷键格式"""
        if not hotkey:
            return ""

        parts = hotkey.lower().split('+')
        modifiers = []
        keys = []
        modifier_order = ['ctrl', 'alt', 'shift', 'cmd', 'win']

        for part in parts:
            part = part.strip()
            if part in modifier_order:
                modifiers.append(part)
            else:
                keys.append(part)

        modifiers.sort(key=lambda x: modifier_order.index(x) if x in modifier_order else 99)
        return '+'.join(modifiers + keys)

    @classmethod
    def get_reserved_hotkeys_display(cls) -> str:
        """获取保留快捷键的显示文本"""
        lines = ["系统控制快捷键（不可用于提示词）：", ""]

        for hotkey, desc in cls.SYSTEM_CONTROL_HOTKEYS.items():
            lines.append(f"  {hotkey}: {desc}")

        lines.append("")
        lines.append("提示词快捷键槽位：")
        lines.append("  alt+1 到 alt+9: 可分配给提示词")
        lines.append("  （从下拉框选择可用槽位）")

        return "\n".join(lines)

    @classmethod
    def get_available_modifiers(cls) -> List[str]:
        """获取可用的修饰键"""
        return ["Alt", "Ctrl", "Shift", "Ctrl+Alt", "Ctrl+Shift", "Alt+Shift"]

    @classmethod
    def get_suggested_hotkeys(cls) -> List[str]:
        """获取建议使用的快捷键格式"""
        return [
            "ctrl+f1", "ctrl+f2", "ctrl+f3",
            "ctrl+alt+a", "ctrl+alt+b", "ctrl+alt+c",
            "ctrl+shift+1", "ctrl+shift+2", "ctrl+shift+3",
        ]
