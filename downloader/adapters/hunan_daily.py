# -*- coding: utf-8 -*-
"""
湖南日报，epaper.voc.com.cn/hnrb/html/YYYY-MM/DD/node_NNN.htm
日期格式为 YYYY-MM/DD
"""
import os
import re
import shutil
import tempfile
import warnings
from pathlib import Path
from urllib.parse import urljoin

import requests
import PyPDF2

warnings.filterwarnings("ignore", message="Multiple definitions in dictionary")

from downloader.base import BaseAdapter, DownloadTask, DownloadResult, DownloadStatus
from downloader.http_client import get_browser_headers, random_delay, create_session


class HunanDailyAdapter(BaseAdapter):
    BASE_URL = "https://epaper.voc.com.cn"
    LAYOUT_BASE = "https://epaper.voc.com.cn/hnrb/html"

    def download(self, task, progress_callback=None, is_cancelled=None):
        date_str = task.date_str
        parts = date_str.split("-")
        if len(parts) != 3:
            return DownloadResult(success=False, message="日期格式无效", status=DownloadStatus.FAILED)
        yyyy, mm, dd = parts[0], parts[1], parts[2]
        date_path = f"{yyyy}-{mm}/{dd}"

        save_dir = task.save_dir
        try:
            Path(save_dir).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return DownloadResult(success=False, message=f"无法创建目录：{e}", status=DownloadStatus.FAILED)
        output_file = Path(save_dir) / f"湖南日报_{date_str}.pdf"
        if output_file.exists():
            return DownloadResult(success=True, file_path=str(output_file), message="已下载过", status=DownloadStatus.COMPLETED)

        part_path = tempfile.mkdtemp(prefix="hnrb_")
        try:
            session = create_session(f"{self.BASE_URL}/")
            random_delay(0.2, 0.6)

            layout_url = f"{self.LAYOUT_BASE}/{date_path}/"
            resp = session.get(layout_url, headers=get_browser_headers(f"{self.BASE_URL}/", include_ua=False), timeout=25)
            if not resp or resp.status_code != 200 or len(resp.text) < 100:
                return DownloadResult(success=False, message="该日期无内容", status=DownloadStatus.FAILED)
            resp.encoding = "utf-8"

            links = re.findall(r'href=["\']([^"\']*?node[^"\']*?\.htm)["\']', resp.text, re.I)
            if not links:
                return DownloadResult(success=False, message="未找到版面", status=DownloadStatus.FAILED)

            seen = set()
            unique = []
            for x in links:
                if x not in seen:
                    seen.add(x)
                    unique.append(x)

            def node_num(s):
                m = re.search(r"node[_-]?(\d+)", s, re.I)
                return int(m.group(1)) if m else 999
            unique.sort(key=node_num)

            ref = f"{self.BASE_URL}/"
            downloaded = 0
            for i, node_rel in enumerate(unique):
                if is_cancelled and is_cancelled():
                    return DownloadResult(success=False, message="用户取消", status=DownloadStatus.CANCELLED)
                if progress_callback:
                    progress_callback(i, len(unique), f"第 {i+1} 版")
                if i > 0:
                    random_delay(0.4, 1.0)

                node_url = node_rel if node_rel.startswith("http") else urljoin(layout_url, node_rel)
                r = None
                for _ in range(3):
                    try:
                        r = session.get(node_url, headers=get_browser_headers(ref, include_ua=False), timeout=25)
                        if r and r.status_code == 200:
                            break
                    except (requests.RequestException, TimeoutError):
                        pass
                if not r or r.status_code != 200:
                    continue
                r.encoding = "utf-8"
                pdfs = re.findall(r'["\']([^"\']+\.pdf)["\']', r.text, re.I)
                if not pdfs:
                    continue
                pdf_url = urljoin(node_url, pdfs[0])
                random_delay(0.2, 0.6)
                r2 = None
                for _ in range(3):
                    try:
                        r2 = session.get(pdf_url, headers=get_browser_headers(node_url, include_ua=False), timeout=45)
                        if r2 and r2.status_code == 200 and len(r2.content) > 500:
                            break
                    except (requests.RequestException, TimeoutError):
                        pass
                if r2 and r2.status_code == 200 and len(r2.content) > 500:
                    with open(os.path.join(part_path, f"p_{i+1:02d}.pdf"), "wb") as f:
                        f.write(r2.content)
                    downloaded += 1

            if downloaded == 0:
                return DownloadResult(success=False, message="未能下载任何版面", status=DownloadStatus.FAILED)
            if progress_callback:
                progress_callback(len(unique), len(unique), "合并 PDF...")
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
