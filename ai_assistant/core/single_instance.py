"""
单实例管理模块
确保程序只能运行一个实例
"""

import os
import tempfile
import psutil
from ..utils.constants import APP_NAME


class SingleInstance:
    def __init__(self, app_name: str = APP_NAME):
        self.app_name = app_name
        self.lock_file_path = os.path.join(tempfile.gettempdir(), f"{app_name}.lock")
        self.lock_file = None
        self.is_locked = False

    def is_already_running(self) -> bool:
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

    def acquire_lock(self) -> bool:
        """获取锁"""
        try:
            # 创建锁文件并写入当前进程PID
            with open(self.lock_file_path, 'w') as f:
                f.write(str(os.getpid()))
            self.is_locked = True
            return True
        except Exception:
            return False

    def release_lock(self) -> None:
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