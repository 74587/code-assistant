"""
日志管理模块
提供日志记录、轮转、持久化等功能
"""

import os
import time
from datetime import datetime
from PyQt6 import QtCore
from ..utils.constants import (
    MAX_LOG_ENTRIES, LOG_DIR_NAME, LOG_SUBDIR, LOG_RETENTION_DAYS
)


class LogManager(QtCore.QObject):
    log_updated = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.logs = []
        self.log_file = None
        self.setup_log_file()

    def setup_log_file(self) -> None:
        """设置日志文件，实现日志轮转"""
        try:
            log_dir = os.path.join(os.path.expanduser("~"), LOG_DIR_NAME, LOG_SUBDIR)
            os.makedirs(log_dir, exist_ok=True)

            # 使用日期作为日志文件名
            log_filename = f"gemini_{datetime.now().strftime('%Y%m%d')}.log"
            log_path = os.path.join(log_dir, log_filename)

            # 清理超过指定天数的旧日志
            self.cleanup_old_logs(log_dir, days=LOG_RETENTION_DAYS)

            self.log_file = log_path
        except Exception as e:
            print(f"设置日志文件失败: {e}")
            self.log_file = None

    def cleanup_old_logs(self, log_dir: str, days: int = LOG_RETENTION_DAYS) -> None:
        """清理旧日志文件"""
        try:
            current_time = time.time()
            for filename in os.listdir(log_dir):
                if filename.startswith("gemini_") and filename.endswith(".log"):
                    file_path = os.path.join(log_dir, filename)
                    if os.path.getmtime(file_path) < current_time - (days * 24 * 60 * 60):
                        os.remove(file_path)
        except Exception:
            pass

    def add_log(self, message: str, level: str = "INFO") -> None:
        """添加日志条目"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"

        # 内存日志轮转
        if len(self.logs) >= MAX_LOG_ENTRIES:
            self.logs = self.logs[-MAX_LOG_ENTRIES + 100:]  # 保留最近的900条

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

    def get_logs(self) -> str:
        """获取所有日志"""
        return "\n".join(self.logs)

    def clear_logs(self) -> None:
        """清空内存日志"""
        self.logs.clear()

    def get_log_count(self) -> int:
        """获取日志条数"""
        return len(self.logs)