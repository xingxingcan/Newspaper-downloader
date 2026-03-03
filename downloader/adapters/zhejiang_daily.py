# -*- coding: utf-8 -*-
"""
浙江日报，html/YYYY-MM/DD/node_N.htm，PDF: images/YYYY-MM/DD/zjrbYYYYMMDD000NNv01n.pdf
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


class ZhejiangDailyAdapter(BaseAdapter):
    BASE_URL = "http://zjrb.zjol.com.cn"

    def download(self, task, progress_callback=None, is_cancelled=None):
        date_str = task.date_str
        parts = date_str.split("-")
        if len(parts) != 3:
            return DownloadResult(success=False, message="日期格式无效", status=DownloadStatus.FAILED)
        yyyy, mm, dd = parts[0], parts[1], parts[2]
        yyyymmdd = yyyy + mm + dd
        date_slash = f"{yyyy}-{mm}/{dd}"

        save_dir = task.save_dir
        try:
            Path(save_dir).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return DownloadResult(success=False, message=f"无法创建目录：{e}", status=DownloadStatus.FAILED)
        output_file = Path(save_dir) / f"浙江日报_{date_str}.pdf"
        if output_file.exists():
            return DownloadResult(success=True, file_path=str(output_file), message="已下载过", status=DownloadStatus.COMPLETED)

        part_path = tempfile.mkdtemp(prefix="zjrb_")
        try:
            session = create_session(f"{self.BASE_URL}/")
            random_delay(0.2, 0.6)

            index_url = f"{self.BASE_URL}/html/{date_slash}/zjrbindex.htm"
            resp = session.get(index_url, headers=get_browser_headers(f"{self.BASE_URL}/", include_ua=False), timeout=25)
            if not resp or resp.status_code != 200:
                return DownloadResult(success=False, message="该日期无内容", status=DownloadStatus.FAILED)
            resp.encoding = "utf-8"
            nodes = re.findall(r"node_(\d+)\.htm", resp.text, re.I)
            if not nodes:
                nodes = [str(i) for i in range(1, 17)]
            else:
                nodes = sorted(set(nodes), key=lambda x: int(x))

            ref = f"{self.BASE_URL}/"
            downloaded = 0
            for i, nn in enumerate(nodes):
                if is_cancelled and is_cancelled():
                    return DownloadResult(success=False, message="用户取消", status=DownloadStatus.CANCELLED)
                if progress_callback:
                    progress_callback(i, len(nodes), f"第 {int(nn)} 版")
                if i > 0:
                    random_delay(0.4, 1.0)

                pdf_name = f"zjrb{yyyymmdd}{int(nn):05d}v01n.pdf"
                pdf_url = f"{self.BASE_URL}/images/{date_slash}/{pdf_name}"
                r = None
                for _ in range(3):
                    try:
                        r = session.get(pdf_url, headers=get_browser_headers(ref, include_ua=False), timeout=30)
                        if r and r.status_code == 200 and len(r.content) > 500:
                            break
                    except (requests.RequestException, TimeoutError):
                        pass
                if r and r.status_code == 200 and len(r.content) > 500:
                    with open(os.path.join(part_path, f"zjrb_{nn}.pdf"), "wb") as f:
                        f.write(r.content)
                    downloaded += 1
                else:
                    if downloaded > 0:
                        break

            if downloaded == 0:
                return DownloadResult(success=False, message="未找到该日期报纸", status=DownloadStatus.FAILED)
            if progress_callback:
                progress_callback(len(nodes), len(nodes), "合并 PDF...")
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
        files = sorted([f for f in os.listdir(part_path) if f.endswith(".pdf")],
                      key=lambda x: int(re.search(r"\d+", x).group()) if re.search(r"\d+", x) else 0)
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
