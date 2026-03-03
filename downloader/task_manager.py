# -*- coding: utf-8 -*-
"""
下载任务管理器
在后台线程中执行下载，支持暂停、取消，并通过信号与 UI 通信
"""

import threading
from typing import Callable

from downloader.adapters import get_adapter
from downloader.base import DownloadTask, DownloadResult, DownloadStatus
from config.newspaper_sources import NEWSPAPER_SOURCES


class DownloadTaskManager:
    """管理多个报纸的下载任务，支持取消"""

    def __init__(
        self,
        on_progress: Callable[[str, int, int, str], None] | None = None,
        on_task_done: Callable[[str, DownloadResult], None] | None = None,
        on_all_done: Callable[[], None] | None = None,
    ):
        self._on_progress = on_progress
        self._on_task_done = on_task_done
        self._on_all_done = on_all_done
        self._cancelled = False
        self._paused = False
        self._thread: threading.Thread | None = None

    def start(
        self,
        newspaper_ids: list[str],
        date_str: str,
        save_dir: str,
    ) -> None:
        """
        在后台线程中开始下载
        :param newspaper_ids: 要下载的报纸 ID 列表
        :param date_str: 日期 YYYY-MM-DD
        :param save_dir: 保存目录
        """
        self._cancelled = False
        self._paused = False
        self._thread = threading.Thread(
            target=self._run_tasks,
            args=(newspaper_ids, date_str, save_dir),
        )
        self._thread.start()

    def cancel(self) -> None:
        """取消所有任务"""
        self._cancelled = True

    def pause(self) -> None:
        """暂停（当前实现中取消即停止，暂停可扩展）"""
        self._paused = True

    def resume(self) -> None:
        """恢复"""
        self._paused = False

    def _run_tasks(
        self,
        newspaper_ids: list[str],
        date_str: str,
        save_dir: str,
    ) -> None:
        source_map = {s["id"]: s for s in NEWSPAPER_SOURCES if s.get("enabled", True)}
        total = len(newspaper_ids)
        for i, nid in enumerate(newspaper_ids):
            if self._cancelled:
                if self._on_task_done:
                    self._on_task_done(
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
                if self._on_progress:
                    self._on_progress(name, cur, total_pages, msg)

            def is_cancelled() -> bool:
                return self._cancelled

            task = DownloadTask(
                newspaper_id=nid,
                newspaper_name=name,
                date_str=date_str,
                save_dir=save_dir,
            )
            result = adapter.download(
                task,
                progress_callback=progress_cb,
                is_cancelled=is_cancelled,
            )
            if self._on_task_done:
                self._on_task_done(nid, result)

        if self._on_all_done:
            self._on_all_done()
