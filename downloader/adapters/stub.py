# -*- coding: utf-8 -*-
"""
占位适配器
用于尚未实现具体下载逻辑的报纸，提示用户可扩展
"""

from downloader.base import BaseAdapter, DownloadTask, DownloadResult, DownloadStatus


class StubAdapter(BaseAdapter):
    """占位适配器：暂未实现，返回友好提示"""

    def download(
        self,
        task: DownloadTask,
        progress_callback=None,
        is_cancelled=None,
    ) -> DownloadResult:
        return DownloadResult(
            success=False,
            message=f"「{self.newspaper_name}」下载功能正在开发中，敬请期待。您可参考 people_daily.py 自行扩展。",
            status=DownloadStatus.FAILED,
        )
