"""
设计令牌系统 v2.0
现代化商业级视觉设计变量
灵感来源：Linear, Raycast, Arc Browser
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Colors:
    """颜色令牌 - 现代深色主题"""

    # 品牌主色 - 渐变蓝紫色系
    PRIMARY = "#6366F1"           # Indigo-500
    PRIMARY_LIGHT = "#818CF8"     # Indigo-400
    PRIMARY_DARK = "#4F46E5"      # Indigo-600
    PRIMARY_GLOW = "rgba(99, 102, 241, 0.15)"

    # 强调色 - 科技感青色
    ACCENT = "#06B6D4"            # Cyan-500
    ACCENT_LIGHT = "#22D3EE"      # Cyan-400
    ACCENT_DARK = "#0891B2"       # Cyan-600
    ACCENT_GLOW = "rgba(6, 182, 212, 0.12)"

    # 渐变色
    GRADIENT_PRIMARY = "linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)"
    GRADIENT_ACCENT = "linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%)"
    GRADIENT_SURFACE = "linear-gradient(180deg, rgba(15, 23, 42, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%)"

    # 语义色
    SUCCESS = "#10B981"           # Emerald-500
    SUCCESS_LIGHT = "#34D399"
    SUCCESS_BG = "rgba(16, 185, 129, 0.12)"

    WARNING = "#F59E0B"           # Amber-500
    WARNING_LIGHT = "#FBBF24"
    WARNING_BG = "rgba(245, 158, 11, 0.12)"

    DANGER = "#EF4444"            # Red-500
    DANGER_LIGHT = "#F87171"
    DANGER_BG = "rgba(239, 68, 68, 0.12)"

    INFO = "#3B82F6"              # Blue-500
    INFO_LIGHT = "#60A5FA"
    INFO_BG = "rgba(59, 130, 246, 0.12)"

    # 背景层级 - 深色玻璃质感
    BG_BASE = "#030712"           # 最深底色
    BG_PRIMARY = "#0F172A"        # 主背景
    BG_SECONDARY = "#1E293B"      # 次级背景
    BG_TERTIARY = "#334155"       # 三级背景
    BG_ELEVATED = "rgba(30, 41, 59, 0.8)"  # 浮起元素
    BG_GLASS = "rgba(15, 23, 42, 0.75)"    # 玻璃效果
    BG_CARD = "rgba(30, 41, 59, 0.5)"      # 卡片背景
    BG_OVERLAY = "rgba(15, 23, 42, 0.92)"  # 浮窗背景

    # 边框
    BORDER_DEFAULT = "rgba(71, 85, 105, 0.4)"
    BORDER_SUBTLE = "rgba(71, 85, 105, 0.2)"
    BORDER_HOVER = "rgba(99, 102, 241, 0.5)"
    BORDER_FOCUS = "#6366F1"
    BORDER_GLOW = "rgba(99, 102, 241, 0.25)"

    # 文字层级
    TEXT_PRIMARY = "#F8FAFC"      # 主要文字
    TEXT_SECONDARY = "#CBD5E1"    # 次要文字
    TEXT_TERTIARY = "#94A3B8"     # 辅助文字
    TEXT_MUTED = "#64748B"        # 弱化文字
    TEXT_DISABLED = "#475569"     # 禁用文字
    TEXT_INVERSE = "#0F172A"      # 反色文字

    # 状态指示
    STATUS_ONLINE = "#10B981"
    STATUS_OFFLINE = "#6B7280"
    STATUS_BUSY = "#EF4444"
    STATUS_AWAY = "#F59E0B"

    # 特效色
    GLOW_PRIMARY = "rgba(99, 102, 241, 0.4)"
    GLOW_ACCENT = "rgba(6, 182, 212, 0.4)"
    SHIMMER = "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.05) 50%, transparent 100%)"


@dataclass(frozen=True)
class Spacing:
    """间距令牌 - 8px 基础网格"""
    NONE = 0
    XXS = 2
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 20
    XXL = 24
    XXXL = 32
    XXXXL = 48

    # 组件特定间距
    CARD_PADDING = 20
    CARD_PADDING_LG = 24
    CARD_GAP = 16
    SECTION_GAP = 32
    FORM_GAP = 16
    BUTTON_PADDING_H = 20
    BUTTON_PADDING_V = 10
    INPUT_PADDING_H = 14
    INPUT_PADDING_V = 10


@dataclass(frozen=True)
class Radius:
    """圆角令牌 - 现代圆润风格"""
    NONE = 0
    XS = 4
    SM = 6
    MD = 8
    LG = 12
    XL = 16
    XXL = 20
    XXXL = 24
    FULL = 9999

    # 组件特定圆角
    BUTTON = 10
    BUTTON_SM = 8
    BUTTON_LG = 12
    CARD = 16
    CARD_LG = 20
    INPUT = 10
    OVERLAY = 20
    TAG = 6
    AVATAR = 9999
    TOOLTIP = 8


@dataclass(frozen=True)
class Typography:
    """字体令牌 - 现代无衬线"""

    # 字体族
    FONT_FAMILY = '"Inter", "SF Pro Display", "Segoe UI", -apple-system, sans-serif'
    FONT_FAMILY_CN = '"PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif'
    FONT_FAMILY_MONO = '"JetBrains Mono", "SF Mono", "Fira Code", "Consolas", monospace'

    # 字号
    SIZE_XS = 11
    SIZE_SM = 12
    SIZE_MD = 13
    SIZE_BASE = 14
    SIZE_LG = 15
    SIZE_XL = 16
    SIZE_2XL = 18
    SIZE_3XL = 20
    SIZE_4XL = 24
    SIZE_5XL = 30
    SIZE_DISPLAY = 36

    # 行高
    LINE_HEIGHT_TIGHT = 1.25
    LINE_HEIGHT_NORMAL = 1.5
    LINE_HEIGHT_RELAXED = 1.75

    # 字重
    WEIGHT_LIGHT = 300
    WEIGHT_NORMAL = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700

    # 字间距
    TRACKING_TIGHT = "-0.02em"
    TRACKING_NORMAL = "0"
    TRACKING_WIDE = "0.02em"


@dataclass(frozen=True)
class Shadows:
    """阴影令牌 - 柔和深度感"""

    # 基础阴影
    XS = "0 1px 2px rgba(0, 0, 0, 0.05)"
    SM = "0 2px 4px rgba(0, 0, 0, 0.1)"
    MD = "0 4px 8px rgba(0, 0, 0, 0.12)"
    LG = "0 8px 16px rgba(0, 0, 0, 0.15)"
    XL = "0 12px 24px rgba(0, 0, 0, 0.18)"
    XXL = "0 20px 40px rgba(0, 0, 0, 0.22)"

    # 组件阴影
    CARD = "0 4px 24px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.08)"
    CARD_HOVER = "0 8px 32px rgba(0, 0, 0, 0.16), 0 2px 4px rgba(0, 0, 0, 0.1)"
    OVERLAY = "0 16px 48px rgba(0, 0, 0, 0.24), 0 4px 12px rgba(0, 0, 0, 0.12)"
    DROPDOWN = "0 8px 24px rgba(0, 0, 0, 0.2), 0 2px 8px rgba(0, 0, 0, 0.1)"
    BUTTON = "0 2px 8px rgba(0, 0, 0, 0.08)"
    BUTTON_HOVER = "0 4px 12px rgba(0, 0, 0, 0.12)"
    INPUT_FOCUS = "0 0 0 3px rgba(99, 102, 241, 0.2)"

    # 发光效果
    GLOW_PRIMARY = "0 0 20px rgba(99, 102, 241, 0.3)"
    GLOW_ACCENT = "0 0 20px rgba(6, 182, 212, 0.3)"
    GLOW_SUCCESS = "0 0 20px rgba(16, 185, 129, 0.3)"


@dataclass(frozen=True)
class Transitions:
    """过渡动画令牌"""

    # 时长
    DURATION_INSTANT = "50ms"
    DURATION_FAST = "100ms"
    DURATION_NORMAL = "200ms"
    DURATION_SLOW = "300ms"
    DURATION_SLOWER = "400ms"

    # 缓动函数
    EASE_DEFAULT = "cubic-bezier(0.4, 0, 0.2, 1)"
    EASE_IN = "cubic-bezier(0.4, 0, 1, 1)"
    EASE_OUT = "cubic-bezier(0, 0, 0.2, 1)"
    EASE_IN_OUT = "cubic-bezier(0.4, 0, 0.2, 1)"
    EASE_BOUNCE = "cubic-bezier(0.68, -0.55, 0.265, 1.55)"
    EASE_SMOOTH = "cubic-bezier(0.25, 0.1, 0.25, 1)"

    # 组合
    DEFAULT = "all 200ms cubic-bezier(0.4, 0, 0.2, 1)"
    FAST = "all 100ms cubic-bezier(0.4, 0, 0.2, 1)"
    COLORS = "color 200ms, background-color 200ms, border-color 200ms"
    TRANSFORM = "transform 200ms cubic-bezier(0.4, 0, 0.2, 1)"
    OPACITY = "opacity 200ms cubic-bezier(0.4, 0, 0.2, 1)"


@dataclass(frozen=True)
class Blur:
    """模糊效果令牌"""
    NONE = "0"
    SM = "4px"
    MD = "8px"
    LG = "12px"
    XL = "16px"
    XXL = "24px"
    GLASS = "12px"  # 毛玻璃效果


class DesignTokens:
    """设计令牌聚合类"""
    colors = Colors()
    spacing = Spacing()
    radius = Radius()
    typography = Typography()
    shadows = Shadows()
    transitions = Transitions()
    blur = Blur()

    @classmethod
    def get_status_color(cls, status: str) -> str:
        """根据状态获取颜色"""
        status_lower = status.lower()
        if "运行" in status_lower or "running" in status_lower or "online" in status_lower:
            return cls.colors.STATUS_ONLINE
        elif "停止" in status_lower or "offline" in status_lower:
            return cls.colors.STATUS_OFFLINE
        elif "错误" in status_lower or "失败" in status_lower or "error" in status_lower:
            return cls.colors.STATUS_BUSY
        elif "警告" in status_lower or "warning" in status_lower:
            return cls.colors.STATUS_AWAY
        return cls.colors.STATUS_OFFLINE

    @classmethod
    def get_glass_style(cls, opacity: float = 0.75) -> str:
        """获取毛玻璃效果样式"""
        return f"""
            background-color: rgba(15, 23, 42, {opacity});
            backdrop-filter: blur({cls.blur.GLASS});
            -webkit-backdrop-filter: blur({cls.blur.GLASS});
        """
