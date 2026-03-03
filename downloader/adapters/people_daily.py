# -*- coding: utf-8 -*-
"""
人民日报电子版下载适配器
参考：https://github.com/raddyfiy/The-Peoples-Daily-download
支持新旧两种官网 URL 格式（2024 年 12 月更新后）
"""

import os
import re
import shutil
import tempfile
from pathlib import Path

import requests
import PyPDF2

from downloader.base import BaseAdapter, DownloadTask, DownloadResult, DownloadStatus


class PeopleDailyAdapter(BaseAdapter):
    """人民日报电子版下载器"""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def download(
        self,
        task: DownloadTask,
        progress_callback=None,
        is_cancelled=None,
    ) -> DownloadResult:
        date_str = task.date_str
        today1 = date_str.replace("-", "/")
        today2 = date_str.replace("-", "")
        save_dir = task.save_dir
        part_path = tempfile.mkdtemp(prefix="rmrb_")
        try:
            Path(save_dir).mkdir(parents=True, exist_ok=True)
            output_file = Path(save_dir) / f"人民日报_{date_str}.pdf"
            if output_file.exists():
                return DownloadResult(
                    success=True,
                    file_path=str(output_file),
                    message="该日期已下载过，跳过",
                    status=DownloadStatus.COMPLETED,
                )

            # 尝试新格式 (2024.12 后)
            cover_url_new = f"http://paper.people.com.cn/rmrb/pc/layout/{today2}/node_01.html"
            resp = requests.get(cover_url_new, headers=self.HEADERS, timeout=15)
            if resp.status_code == 200 and "pageLink" in resp.text:
                page_count = len(re.findall("pageLink", resp.text))
                if page_count > 0:
                    return self._download_new_format(
                        today2, part_path, str(output_file),
                        page_count, progress_callback, is_cancelled
                    )

            # 旧格式
            cover_url_old = f"http://paper.people.com.cn/rmrb/html/{today1}/nbs.D110000renmrb_01.htm"
            resp = requests.get(cover_url_old, headers=self.HEADERS, timeout=15)
            if resp.status_code == 403:
                return DownloadResult(
                    success=False,
                    message="该日期过于久远，网站不提供下载（仅支持两年内）",
                    status=DownloadStatus.FAILED,
                )
            page_count = len(re.findall("nbs", resp.text))
            if page_count == 0:
                return DownloadResult(
                    success=False,
                    message="未找到该日期的报纸版面",
                    status=DownloadStatus.FAILED,
                )

            return self._download_old_format(
                today1, today2, part_path, str(output_file),
                page_count, progress_callback, is_cancelled
            )
        finally:
            if os.path.exists(part_path):
                try:
                    shutil.rmtree(part_path)
                except OSError:
                    pass

    def _download_new_format(
        self,
        today2: str,
        part_path: str,
        output_file: str,
        page_count: int,
        progress_callback,
        is_cancelled,
    ) -> DownloadResult:
        """新格式：从 layout 页面解析 PDF 链接"""
        for page in range(1, page_count + 1):
            if is_cancelled and is_cancelled():
                return DownloadResult(
                    success=False,
                    message="用户取消下载",
                    status=DownloadStatus.CANCELLED,
                )
            if progress_callback:
                progress_callback(page - 1, page_count, f"正在下载第 {page}/{page_count} 页")

            page_url = f"http://paper.people.com.cn/rmrb/pc/layout/{today2}/node_{page:02d}.html"
            resp = requests.get(page_url, headers=self.HEADERS, timeout=15)
            matches = re.findall(r"attachement.*?\.pdf", resp.text)
            if not matches:
                continue
            download_url = "http://paper.people.com.cn/rmrb/pc/" + matches[0]
            r = requests.get(download_url, headers=self.HEADERS, timeout=30)
            if len(r.content) > 1000:
                filename = f"rmrb{today2}{page:02d}.pdf"
                with open(os.path.join(part_path, filename), "wb") as f:
                    f.write(r.content)

        if progress_callback:
            progress_callback(page_count, page_count, "正在合并 PDF...")
        self._merge_pdfs(part_path, output_file, today2)
        return DownloadResult(
            success=True,
            file_path=output_file,
            message="下载成功",
            status=DownloadStatus.COMPLETED,
        )

    def _download_old_format(
        self,
        today1: str,
        today2: str,
        part_path: str,
        output_file: str,
        page_count: int,
        progress_callback,
        is_cancelled,
    ) -> DownloadResult:
        """旧格式：直接拼接 URL 下载"""
        for page in range(1, page_count + 1):
            if is_cancelled and is_cancelled():
                return DownloadResult(
                    success=False,
                    message="用户取消下载",
                    status=DownloadStatus.CANCELLED,
                )
            if progress_callback:
                progress_callback(page - 1, page_count, f"正在下载第 {page}/{page_count} 页")

            format_page = f"{page:02d}"
            down_url = f"http://paper.people.com.cn/rmrb/images/{today1}/{format_page}/rmrb{today2}{format_page}.pdf"
            for retry in range(5):
                r = requests.get(down_url, headers=self.HEADERS, timeout=30)
                if len(r.content) > 1000:
                    filename = f"rmrb{today2}{format_page}.pdf"
                    with open(os.path.join(part_path, filename), "wb") as f:
                        f.write(r.content)
                    break

        if progress_callback:
            progress_callback(page_count, page_count, "正在合并 PDF...")
        self._merge_pdfs(part_path, output_file, today2)
        return DownloadResult(
            success=True,
            file_path=output_file,
            message="下载成功",
            status=DownloadStatus.COMPLETED,
        )

    def _merge_pdfs(self, part_path: str, output_file: str, today2: str) -> None:
        """合并分页 PDF 为单个文件"""
        files = sorted([f for f in os.listdir(part_path) if f.endswith(".pdf")])
        try:
            merger = PyPDF2.PdfMerger(strict=False)
        except TypeError:
            merger = PyPDF2.PdfMerger()
        for f in files:
            full_path = os.path.join(part_path, f)
            if os.path.getsize(full_path) >= 10:
                merger.append(full_path)
        merger.write(output_file)
        merger.close()
