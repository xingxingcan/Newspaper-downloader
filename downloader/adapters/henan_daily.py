# -*- coding: utf-8 -*-
"""河南日报，resfile/YYYY-MM-DD/NN/hnrbYYYYMMDDNN.pdf"""
import os
import shutil
import tempfile
import warnings
from pathlib import Path

import requests
import PyPDF2

warnings.filterwarnings("ignore", message="Multiple definitions in dictionary")

from downloader.base import BaseAdapter, DownloadTask, DownloadResult, DownloadStatus
from downloader.http_client import get_browser_headers, random_delay, create_session


class HenanDailyAdapter(BaseAdapter):
    BASE_URL = "http://newpaper.dahe.cn/hnrb"

    def download(self, task, progress_callback=None, is_cancelled=None):
        date_str = task.date_str
        parts = date_str.split("-")
        if len(parts) != 3:
            return DownloadResult(success=False, message="日期格式无效", status=DownloadStatus.FAILED)
        yyyy, mm, dd = parts[0], parts[1], parts[2]
        yyyymmdd = yyyy + mm + dd

        save_dir = task.save_dir
        try:
            Path(save_dir).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return DownloadResult(success=False, message=f"无法创建目录：{e}", status=DownloadStatus.FAILED)
        output_file = Path(save_dir) / f"河南日报_{date_str}.pdf"
        if output_file.exists():
            return DownloadResult(success=True, file_path=str(output_file), message="已下载过", status=DownloadStatus.COMPLETED)

        part_path = tempfile.mkdtemp(prefix="hnrb_")
        try:
            session = create_session(f"{self.BASE_URL}/")
            random_delay(0.2, 0.6)
            ref = f"{self.BASE_URL}/"
            downloaded = 0
            page = 1
            while page <= 24:
                if is_cancelled and is_cancelled():
                    return DownloadResult(success=False, message="用户取消", status=DownloadStatus.CANCELLED)
                if progress_callback:
                    progress_callback(page - 1, page, f"第 {page} 版")
                if page > 1:
                    random_delay(0.4, 1.0)
                nn = f"{page:02d}"
                pdf_url = f"{self.BASE_URL}/resfile/{date_str}/{nn}/hnrb{yyyymmdd}{nn}.pdf"
                r = None
                for _ in range(3):
                    try:
                        r = session.get(pdf_url, headers=get_browser_headers(ref, include_ua=False), timeout=30)
                        if r and r.status_code == 200 and len(r.content) > 500:
                            break
                    except (requests.RequestException, TimeoutError):
                        pass
                if r and r.status_code == 200 and len(r.content) > 500:
                    with open(os.path.join(part_path, f"hnrb_{nn}.pdf"), "wb") as f:
                        f.write(r.content)
                    downloaded += 1
                    page += 1
                else:
                    break
            if downloaded == 0:
                return DownloadResult(success=False, message="未找到该日期报纸", status=DownloadStatus.FAILED)
            if progress_callback:
                progress_callback(downloaded, downloaded, "合并 PDF...")
            self._merge_pdfs(part_path, str(output_file))
            return DownloadResult(success=True, file_path=str(output_file), message="下载成功", status=DownloadStatus.COMPLETED)
        except (requests.RequestException, TimeoutError) as e:
            return DownloadResult(success=False, message=f"网络错误：{str(e)[:60]}", status=DownloadStatus.FAILED)
        finally:
            if os.path.exists(part_path):
                try:
                    shutil.rmtree(part_path)
                except OSError:
                    pass

    def _merge_pdfs(self, part_path, output_file):
        files = sorted([f for f in os.listdir(part_path) if f.endswith(".pdf")])
        try:
            merger = PyPDF2.PdfMerger(strict=False)
        except TypeError:
            merger = PyPDF2.PdfMerger()
        for f in files:
            p = os.path.join(part_path, f)
            if os.path.getsize(p) >= 10:
                merger.append(p)
        merger.write(output_file)
        merger.close()
