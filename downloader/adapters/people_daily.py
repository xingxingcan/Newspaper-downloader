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
import warnings
from pathlib import Path

import requests
import PyPDF2

# 抑制 PyPDF2 对部分 PDF 的字典重复键警告
warnings.filterwarnings("ignore", message="Multiple definitions in dictionary")

from downloader.base import BaseAdapter, DownloadTask, DownloadResult, DownloadStatus
from downloader.http_client import get_browser_headers, random_delay, create_session


class PeopleDailyAdapter(BaseAdapter):
    """人民日报电子版下载器"""

    BASE_URL = "http://paper.people.com.cn/rmrb/pc"

    def download(
        self,
        task: DownloadTask,
        progress_callback=None,
        is_cancelled=None,
    ) -> DownloadResult:
        date_str = task.date_str
        # 解析日期：2026-03-03 -> YYYYMM=202603, DD=03
        parts = date_str.split("-")
        if len(parts) != 3:
            return DownloadResult(
                success=False,
                message="日期格式无效，应为 YYYY-MM-DD",
                status=DownloadStatus.FAILED,
            )
        yyyymm = parts[0] + parts[1]
        dd = parts[2]
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

            session = create_session(f"{self.BASE_URL}/")
            random_delay(0.2, 0.6)  # 模拟用户进入页面后的短暂停顿
            # 新格式：layout/YYYYMM/DD/node_XX.html
            cover_url_new = f"{self.BASE_URL}/layout/{yyyymm}/{dd}/node_01.html"
            resp = session.get(cover_url_new, headers=get_browser_headers(self.BASE_URL + "/", include_ua=False), timeout=20)
            if resp.status_code == 200:
                page_count = self._parse_page_count(resp.text, yyyymm, dd)
                if page_count > 0:
                    return self._download_new_format(
                        session, yyyymm, dd, part_path, str(output_file),
                        page_count, progress_callback, is_cancelled
                    )

            # 旧格式（兼容历史日期）
            session = create_session("http://paper.people.com.cn/")
            random_delay(0.2, 0.6)
            cover_url_old = f"http://paper.people.com.cn/rmrb/html/{today1}/nbs.D110000renmrb_01.htm"
            resp = session.get(cover_url_old, headers=get_browser_headers("http://paper.people.com.cn/", include_ua=False), timeout=20)
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
                session, today1, today2, part_path, str(output_file),
                page_count, progress_callback, is_cancelled
            )
        finally:
            if os.path.exists(part_path):
                try:
                    shutil.rmtree(part_path)
                except OSError:
                    pass

    def _parse_page_count(self, html: str, yyyymm: str, dd: str) -> int:
        """从 layout 页面解析版面数量（node_01, node_02, ...）"""
        matches = re.findall(r"node_(\d+)", html)
        if matches:
            return max(int(m) for m in matches)
        return 0

    def _download_new_format(
        self,
        session: requests.Session,
        yyyymm: str,
        dd: str,
        part_path: str,
        output_file: str,
        page_count: int,
        progress_callback,
        is_cancelled,
    ) -> DownloadResult:
        """新格式：从 layout/YYYYMM/DD/node_XX.html 爬取每页 PDF 并合并"""
        layout_base = f"{self.BASE_URL}/layout/{yyyymm}/{dd}/"
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
                random_delay(0.4, 1.2)

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
            if not resp:
                continue
            matches = re.findall(r"(?:https?://[^\"]*)?(attachement/[^\s\"'<>]+\.pdf)", resp.text)
            if not matches:
                matches = re.findall(r"attachement[^\s\"']*?\.pdf", resp.text)
            if matches:
                pdf_path = matches[0].strip()
                if pdf_path.startswith("http"):
                    download_url = pdf_path
                else:
                    download_url = self.BASE_URL + "/" + pdf_path
                random_delay(0.2, 0.6)
                r = None
                for retry in range(3):
                    try:
                        r = session.get(
                            download_url,
                            headers=get_browser_headers(page_url, include_ua=False),
                            timeout=35,
                        )
                        if r and len(r.content) > 1000:
                            break
                    except (requests.RequestException, TimeoutError):
                        r = None
                if r and len(r.content) > 1000:
                    filename = f"rmrb{yyyymm}{dd}{page:02d}.pdf"
                    with open(os.path.join(part_path, filename), "wb") as f:
                        f.write(r.content)

        if progress_callback:
            progress_callback(page_count, page_count, "正在合并 PDF...")
        self._merge_pdfs(part_path, output_file, f"{yyyymm}{dd}")
        return DownloadResult(
            success=True,
            file_path=output_file,
            message="下载成功",
            status=DownloadStatus.COMPLETED,
        )

    def _download_old_format(
        self,
        session: requests.Session,
        today1: str,
        today2: str,
        part_path: str,
        output_file: str,
        page_count: int,
        progress_callback,
        is_cancelled,
    ) -> DownloadResult:
        """旧格式：直接拼接 URL 下载"""
        ref = f"http://paper.people.com.cn/rmrb/html/{today1}/"
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
                random_delay(0.4, 1.2)

            format_page = f"{page:02d}"
            down_url = f"http://paper.people.com.cn/rmrb/images/{today1}/{format_page}/rmrb{today2}{format_page}.pdf"
            for retry in range(5):
                try:
                    r = session.get(down_url, headers=get_browser_headers(ref, include_ua=False), timeout=30)
                    if r and len(r.content) > 1000:
                        filename = f"rmrb{today2}{format_page}.pdf"
                        with open(os.path.join(part_path, filename), "wb") as f:
                            f.write(r.content)
                        break
                except (requests.RequestException, TimeoutError):
                    if retry == 4:
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
