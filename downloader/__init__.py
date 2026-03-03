# -*- coding: utf-8 -*-
"""
下载模块
提供各类报纸的下载适配器及统一的下载任务管理
"""

from .base import BaseAdapter, DownloadTask, DownloadResult
from .adapters import get_adapter
from .task_manager import DownloadTaskManager

__all__ = [
    "BaseAdapter",
    "DownloadTask",
    "DownloadResult",
    "get_adapter",
    "DownloadTaskManager",
]
