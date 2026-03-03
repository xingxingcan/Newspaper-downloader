# -*- coding: utf-8 -*-
"""
中国经济时报电子版下载适配器
参考：https://jjsb.cet.com.cn/szb_14380.html
PDF 路径：https://jjsb.cet.com.cn/zgjjsb/YYYYMMDD/A01.pdf
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


class CETimesAdapter(BaseAdapter):
    """中国经济时报电子版下载器"""

    BASE_URL = "https://jjsb.cet.com.cn"
    PDF_BASE = "https://jjsb.cet.com.cn/zgjjsb"

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
        yyyymmdd = parts[0] + parts[1] + parts[2]

        save_dir = task.save_dir
        try:
            Path(save_dir).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return DownloadResult(
                success=False,
                message=f"无法创建保存目录：{e}",
                status=DownloadStatus.FAILED,
            )
        output_file = Path(save_dir) / f"中国经济时报_{date_str}.pdf"
        if output_file.exists():
            return DownloadResult(
                success=True,
                file_path=str(output_file),
                message="该日期已下载过，跳过",
                status=DownloadStatus.COMPLETED,
            )
        part_path = tempfile.mkdtemp(prefix="cet_times_")
        try:
            session = create_session(f"{self.BASE_URL}/")
            random_delay(0.2, 0.6)

            # 通过 DigitaNewspaper.aspx 获取该期页面，解析版面列表
            page_list = self._fetch_page_list(session, date_str, yyyymmdd)
            if not page_list:
                return DownloadResult(
                    success=False,
                    message="未找到该日期的报纸，或该日期无电子版",
                    status=DownloadStatus.FAILED,
                )

            return self._download_pages(
                session, date_str, yyyymmdd, part_path, str(output_file),
                page_list, progress_callback, is_cancelled
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

    def _fetch_page_list(self, session: requests.Session, date_str: str, yyyymmdd: str) -> list[str]:
        """
        获取版面列表。先请求 DigitaNewspaper.aspx，解析 A01/A02...；
        若解析不到则尝试 A01..A16 直至 404。
        """
        index_url = f"{self.BASE_URL}/DigitaNewspaper.aspx"
        resp = None
        for retry in range(3):
            try:
                resp = session.get(
                    index_url,
                    params={"date": date_str},
                    headers=get_browser_headers(f"{self.BASE_URL}/", include_ua=False),
                    timeout=20,
                )
                if resp and resp.status_code == 200:
                    break
            except (requests.RequestException, TimeoutError):
                resp = None
        if not resp or resp.status_code != 200:
            return []

        # 从 HTML 解析 szb_xxx_A01.html 或 /zgjjsb/YYYYMMDD/A01.pdf
        pages = [f"A{m}" for m in re.findall(r"szb_\d+_A(\d{2})\.html", resp.text, re.I)]
        if not pages:
            pages = re.findall(r"/zgjjsb/\d+/(A\d{2})\.pdf", resp.text, re.I)
        if pages:
            return sorted(set(pages))

        # 回退：按序尝试 A01..A16
        result = []
        for i in range(1, 17):
            page_id = f"A{i:02d}"
            pdf_url = f"{self.PDF_BASE}/{yyyymmdd}/{page_id}.pdf"
            try:
                r = session.head(
                    pdf_url,
                    headers=get_browser_headers(f"{self.BASE_URL}/", include_ua=False),
                    timeout=10,
                    allow_redirects=False,
                )
                if r.status_code == 200:
                    result.append(page_id)
                else:
                    break  # 连续不存在则停止
            except (requests.RequestException, TimeoutError):
                break
        return result

    def _download_pages(
        self,
        session: requests.Session,
        date_str: str,
        yyyymmdd: str,
        part_path: str,
        output_file: str,
        page_list: list[str],
        progress_callback,
        is_cancelled,
    ) -> DownloadResult:
        """下载各版 PDF 并合并"""
        ref = f"{self.BASE_URL}/"
        for idx, page_id in enumerate(page_list):
            if is_cancelled and is_cancelled():
                return DownloadResult(
                    success=False,
                    message="用户取消下载",
                    status=DownloadStatus.CANCELLED,
                )
            if progress_callback:
                progress_callback(idx, len(page_list), f"正在下载第 {page_id} 版")
            if idx > 0:
                random_delay(0.4, 1.0)

            pdf_url = f"{self.PDF_BASE}/{yyyymmdd}/{page_id}.pdf"
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
                filename = f"cet_{yyyymmdd}_{page_id}.pdf"
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
            progress_callback(len(page_list), len(page_list), "正在合并 PDF...")
        self._merge_pdfs(part_path, output_file, yyyymmdd, page_list)
        return DownloadResult(
            success=True,
            file_path=output_file,
            message="下载成功",
            status=DownloadStatus.COMPLETED,
        )

    def _merge_pdfs(self, part_path: str, output_file: str, yyyymmdd: str, page_list: list[str]) -> None:
        """按版面顺序合并 PDF。文件名格式: cet_YYYYMMDD_A01.pdf"""
        ordered = []
        for p in page_list:
            fn = f"cet_{yyyymmdd}_{p}.pdf"
            fp = os.path.join(part_path, fn)
            if os.path.exists(fp):
                ordered.append(fp)
        if not ordered:
            ordered = [os.path.join(part_path, f) for f in sorted(os.listdir(part_path)) if f.endswith(".pdf")]
        try:
            merger = PyPDF2.PdfMerger(strict=False)
        except TypeError:
            merger = PyPDF2.PdfMerger()
        for fp in ordered:
            if os.path.getsize(fp) >= 10:
                merger.append(fp)
        merger.write(output_file)
        merger.close()
