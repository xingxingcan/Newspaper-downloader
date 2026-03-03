# -*- coding: utf-8 -*-
"""
中国旅游报电子版下载适配器
参考：http://www.ctnews.com.cn/paper
URL 结构：paper/YYYYMM/DD/node_XX.html，PDF: paper/att/YYYYMM/DD/uuid.pdf
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


class CTNewsAdapter(BaseAdapter):
    """中国旅游报电子版下载器"""

    BASE_URL = "http://www.ctnews.com.cn"

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
        yyyymm = parts[0] + parts[1]
        dd = parts[2]
        layout_base = f"{self.BASE_URL}/paper/{yyyymm}/{dd}/"

        save_dir = task.save_dir
        try:
            Path(save_dir).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return DownloadResult(
                success=False,
                message=f"无法创建保存目录：{e}",
                status=DownloadStatus.FAILED,
            )
        output_file = Path(save_dir) / f"中国旅游报_{date_str}.pdf"
        if output_file.exists():
            return DownloadResult(
                success=True,
                file_path=str(output_file),
                message="该日期已下载过，跳过",
                status=DownloadStatus.COMPLETED,
            )
        part_path = tempfile.mkdtemp(prefix="ctnews_")
        try:
            session = create_session(f"{self.BASE_URL}/")
            random_delay(0.2, 0.6)

            cover_url = f"{layout_base}node_01.html"
            resp = None
            for retry in range(3):
                try:
                    resp = session.get(
                        cover_url,
                        headers=get_browser_headers(f"{self.BASE_URL}/paper", include_ua=False),
                        timeout=20,
                    )
                    if resp and resp.status_code == 200:
                        break
                except (requests.RequestException, TimeoutError):
                    resp = None
            if not resp or resp.status_code != 200:
                return DownloadResult(
                    success=False,
                    message="未找到该日期的报纸，或网站连接超时",
                    status=DownloadStatus.FAILED,
                )

            page_count = self._parse_page_count(resp.text)
            if page_count == 0:
                return DownloadResult(
                    success=False,
                    message="未找到该日期的报纸版面",
                    status=DownloadStatus.FAILED,
                )

            return self._download_pages(
                session, layout_base, yyyymm, dd,
                part_path, str(output_file),
                page_count, progress_callback, is_cancelled
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

    def _parse_page_count(self, html: str) -> int:
        """从页面解析版面数量"""
        matches = re.findall(r"node_(\d+)\.html", html)
        return max(int(m) for m in matches) if matches else 0

    def _extract_pdf_url(self, html: str) -> str | None:
        """
        从页面提取 PDF 链接。相对路径 ../../att/YYYYMM/DD/uuid.pdf
        实际完整 URL: BASE_URL/paper/att/YYYYMM/DD/uuid.pdf
        """
        m = re.search(r"att/\d{6}/\d{2}/[a-f0-9\-]+\.pdf", html)
        if m:
            return f"{self.BASE_URL}/paper/{m.group(0)}"
        return None

    def _download_pages(
        self,
        session: requests.Session,
        layout_base: str,
        yyyymm: str,
        dd: str,
        part_path: str,
        output_file: str,
        page_count: int,
        progress_callback,
        is_cancelled,
    ) -> DownloadResult:
        """下载各版 PDF 并合并"""
        for page in range(1, page_count + 1):
            if is_cancelled and is_cancelled():
                return DownloadResult(
                    success=False,
                    message="用户取消下载",
                    status=DownloadStatus.CANCELLED,
                )
            if progress_callback:
                progress_callback(page - 1, page_count, f"正在下载第 {page}/{page_count} 页")
            if page > 1:
                random_delay(0.4, 1.0)

            page_url = f"{layout_base}node_{page:02d}.html"
            resp = None
            for retry in range(3):
                try:
                    resp = session.get(
                        page_url,
                        headers=get_browser_headers(layout_base, include_ua=False),
                        timeout=20,
                    )
                    if resp and resp.status_code == 200:
                        break
                except (requests.RequestException, TimeoutError):
                    resp = None
            if not resp or resp.status_code != 200:
                continue

            resp.encoding = resp.apparent_encoding or "utf-8"
            pdf_url = self._extract_pdf_url(resp.text)
            if not pdf_url:
                continue
            random_delay(0.2, 0.6)

            r = None
            for retry in range(3):
                try:
                    r = session.get(
                        pdf_url,
                        headers=get_browser_headers(page_url, include_ua=False),
                        timeout=45,
                    )
                    if r and r.status_code == 200 and len(r.content) > 1000:
                        break
                except (requests.RequestException, TimeoutError):
                    r = None
            if r and r.status_code == 200 and len(r.content) > 1000:
                filename = f"ctnews_{yyyymm}{dd}_{page:02d}.pdf"
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
            progress_callback(page_count, page_count, "正在合并 PDF...")
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
