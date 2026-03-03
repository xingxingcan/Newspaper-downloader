# -*- coding: utf-8 -*-
"""
下载器基类定义
所有报纸适配器需继承 BaseAdapter 并实现 download 方法
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Callable


class DownloadStatus(Enum):
    """下载状态枚举"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadResult:
    """单次下载结果"""
    success: bool
    file_path: str = ""
    message: str = ""
    status: DownloadStatus = DownloadStatus.COMPLETED


@dataclass
class DownloadTask:
    """下载任务描述"""
    newspaper_id: str
    newspaper_name: str
    date_str: str  # YYYY-MM-DD
    save_dir: str


class BaseAdapter(ABC):
    """报纸下载适配器基类"""

    def __init__(self, newspaper_id: str, newspaper_name: str):
        self.newspaper_id = newspaper_id
        self.newspaper_name = newspaper_name

    @abstractmethod
    def download(
        self,
        task: DownloadTask,
        progress_callback: Callable[[int, int, str], None] | None = None,
        is_cancelled: Callable[[], bool] | None = None,
    ) -> DownloadResult:
        """
        执行下载
        :param task: 下载任务
        :param progress_callback: 进度回调 (current, total, message)
        :param is_cancelled: 检查是否已取消的回调
        :return: 下载结果
        """
        pass

    def validate_date(self, date_str: str) -> tuple[bool, str]:
        """
        验证日期是否对该报纸有效
        :return: (是否有效, 错误信息)
        """
        # 默认实现：近 30 天有效
        from datetime import datetime, timedelta
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
            today = datetime.now().date()
            if d > today:
                return False, "不能选择未来日期"
            if (today - d).days > 365:
                return False, "仅支持近一年内的报纸"
            return True, ""
        except ValueError:
            return False, "日期格式无效"
