# -*- coding: utf-8 -*-
"""
中国文化报电子版下载适配器
参考：https://npaper.ccmapp.cn/
PDF：https://zyk.ccmapp.cn/apis/file/dl/source/{id}.pdf
"""

import os
import re
import shutil
import tempfile
import warnings
from pathlib import Path

import requests
import PyPDF2

warnings.filterwarnings("ignore", message="Multiple definitions in dictionary")

from downloader.base import BaseAdapter, DownloadTask, DownloadResult, DownloadStatus
from downloader.http_client import get_browser_headers, random_delay, create_session


class CCMAppAdapter(BaseAdapter):
    """中国文化报电子版下载器"""

    NPAPER_URL = "https://npaper.ccmapp.cn"
    PDF_BASE = "https://zyk.ccmapp.cn/apis/file/dl/source"

    def download(
        self,
        task: DownloadTask,
        progress_callback=None,
        is_cancelled=None,
    ) -> DownloadResult:
        date_str = task.date_str
        parts = date_str.split("-")
        if len(parts) != 3:
            return DownloadResult(
                success=False,
                message="日期格式无效，应为 YYYY-MM-DD",
                status=DownloadStatus.FAILED,
            )

        save_dir = task.save_dir
        try:
            Path(save_dir).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return DownloadResult(
                success=False,
                message=f"无法创建保存目录：{e}",
                status=DownloadStatus.FAILED,
            )
        output_file = Path(save_dir) / f"中国文化报_{date_str}.pdf"
        if output_file.exists():
            return DownloadResult(
                success=True,
                file_path=str(output_file),
                message="该日期已下载过，跳过",
                status=DownloadStatus.COMPLETED,
            )
        part_path = tempfile.mkdtemp(prefix="ccmapp_")
        try:
            session = create_session(self.NPAPER_URL + "/")
            random_delay(0.2, 0.6)

            pdf_ids = self._fetch_pdf_ids(date_str)
            if not pdf_ids:
                return DownloadResult(
                    success=False,
                    message="未找到该日期的报纸，或该日期无电子版",
                    status=DownloadStatus.FAILED,
                )

            return self._download_pages(
                session, part_path, str(output_file),
                pdf_ids, progress_callback, is_cancelled
            )
        except (requests.RequestException, TimeoutError) as e:
            return DownloadResult(
                success=False,
                message=f"网络错误：{str(e)[:80]}",
                status=DownloadStatus.FAILED,
            )
        finally:
            if os.path.exists(part_path):
                try:
                    shutil.rmtree(part_path)
                except OSError:
                    pass

    def _fetch_pdf_ids(self, date_str: str) -> list[str]:
        """
        从页面 HTML 提取 PDF ID 列表。首页含当期报纸的 PDF ID。
        该站点对 Sec-Fetch 等完整头返回精简版，故用简头请求。
        """
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}
        urls_to_try = [f"{self.NPAPER_URL}/", f"{self.NPAPER_URL}/zh-CN/"]
        for url in urls_to_try:
            try:
                resp = requests.get(url, headers=headers, timeout=25)
                if resp and resp.status_code == 200:
                    resp.encoding = "utf-8"
                    text = resp.text
                    ids = re.findall(r"([a-f0-9]{24})\.pdf", text)
                    if ids:
                        return ids
            except (requests.RequestException, TimeoutError):
                continue
        return []

    def _download_pages(
        self,
        session: requests.Session,
        part_path: str,
        output_file: str,
        pdf_ids: list[str],
        progress_callback,
        is_cancelled,
    ) -> DownloadResult:
        """下载各版 PDF 并合并"""
        ref = f"{self.NPAPER_URL}/zh-CN/"
        for idx, pid in enumerate(pdf_ids):
            if is_cancelled and is_cancelled():
                return DownloadResult(
                    success=False,
                    message="用户取消下载",
                    status=DownloadStatus.CANCELLED,
                )
            if progress_callback:
                progress_callback(idx, len(pdf_ids), f"正在下载第 {idx + 1}/{len(pdf_ids)} 版")
            if idx > 0:
                random_delay(0.4, 1.0)

            pdf_url = f"{self.PDF_BASE}/{pid}.pdf"
            r = None
            for retry in range(3):
                try:
                    r = session.get(
                        pdf_url,
                        headers=get_browser_headers(ref, include_ua=False),
                        timeout=45,
                    )
                    if r and r.status_code == 200 and len(r.content) > 1000:
                        break
                except (requests.RequestException, TimeoutError):
                    r = None
            if r and r.status_code == 200 and len(r.content) > 1000:
                filename = f"ccmapp_{idx + 1:02d}.pdf"
                with open(os.path.join(part_path, filename), "wb") as f:
                    f.write(r.content)

        downloaded = len([f for f in os.listdir(part_path) if f.endswith(".pdf")])
        if downloaded == 0:
            return DownloadResult(
                success=False,
                message="未能下载任何版面，请检查网络或该日期是否有电子版",
                status=DownloadStatus.FAILED,
            )
        if progress_callback:
            progress_callback(len(pdf_ids), len(pdf_ids), "正在合并 PDF...")
        self._merge_pdfs(part_path, output_file)
        return DownloadResult(
            success=True,
            file_path=output_file,
            message="下载成功",
            status=DownloadStatus.COMPLETED,
        )

    def _merge_pdfs(self, part_path: str, output_file: str) -> None:
        """合并分页 PDF"""
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
