# -*- coding: utf-8 -*-
"""
下载工作线程
使用 QThread + 信号实现线程安全的 UI 更新
"""

from PyQt6.QtCore import QObject, pyqtSignal, QThread

from downloader.adapters import get_adapter
from downloader.base import DownloadTask, DownloadResult, DownloadStatus
from config.newspaper_sources import NEWSPAPER_SOURCES


class DownloadWorker(QObject):
    """下载工作对象，在 QThread 中运行"""

    progress = pyqtSignal(str, int, int, str)  # name, current, total, msg
    task_done = pyqtSignal(str, object)  # newspaper_id, DownloadResult
    all_done = pyqtSignal()

    def __init__(self, newspaper_ids: list[str], date_str: str, save_dir: str):
        super().__init__()
        self.newspaper_ids = newspaper_ids
        self.date_str = date_str
        self.save_dir = save_dir
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        source_map = {s["id"]: s for s in NEWSPAPER_SOURCES if s.get("enabled", True)}
        for nid in self.newspaper_ids:
            if self._cancelled:
                self.task_done.emit(
                    nid,
                    DownloadResult(
                        success=False,
                        message="已取消",
                        status=DownloadStatus.CANCELLED,
                    ),
                )
                continue

            info = source_map.get(nid)
            if not info:
                continue
            name = info["name"]
            adapter = get_adapter(nid, name, info["adapter"])

            def progress_cb(cur: int, total_pages: int, msg: str):
                self.progress.emit(name, cur, total_pages, msg)

            def is_cancelled() -> bool:
                return self._cancelled

            task = DownloadTask(
                newspaper_id=nid,
                newspaper_name=name,
                date_str=self.date_str,
                save_dir=self.save_dir,
            )
            result = adapter.download(
                task,
                progress_callback=progress_cb,
                is_cancelled=is_cancelled,
            )
            self.task_done.emit(nid, result)

        self.all_done.emit()
