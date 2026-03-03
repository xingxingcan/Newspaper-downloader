# -*- coding: utf-8 -*-
"""
黑龙江日报电子版下载适配器
参考：http://epaper.hljnews.cn/hljrb/pc/layout
说明：从 layout 页解析 node 链接，逐页提取 PDF 并合并
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


class HeilongjiangDailyAdapter(BaseAdapter):
    """黑龙江日报电子版下载器"""

    BASE_URL = "http://epaper.hljnews.cn/hljrb"
    LAYOUT_BASE = "http://epaper.hljnews.cn/hljrb/pc/layout"

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
        yyyy, mm, dd = parts[0], parts[1], parts[2]
        yyyymm = yyyy + mm

        save_dir = task.save_dir
        try:
            Path(save_dir).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return DownloadResult(
                success=False,
                message=f"无法创建保存目录：{e}",
                status=DownloadStatus.FAILED,
            )
        output_file = Path(save_dir) / f"黑龙江日报_{date_str}.pdf"
        if output_file.exists():
            return DownloadResult(
                success=True,
                file_path=str(output_file),
                message="该日期已下载过，跳过",
                status=DownloadStatus.COMPLETED,
            )

        part_path = tempfile.mkdtemp(prefix="hljrb_")
        try:
            session = create_session(f"{self.BASE_URL}/")
            random_delay(0.2, 0.6)

            layout_date_url = f"{self.LAYOUT_BASE}/{yyyymm}/{dd}/"
            resp = None
            for url in [f"{layout_date_url}index.html", layout_date_url]:
                try:
                    resp = session.get(
                        url,
                        headers=get_browser_headers(f"{self.BASE_URL}/", include_ua=False),
                        timeout=25,
                    )
                    if resp and resp.status_code == 200 and len(resp.text) > 100:
                        break
                except (requests.RequestException, TimeoutError):
                    resp = None
            if not resp or resp.status_code != 200:
                return DownloadResult(
                    success=False,
                    message="黑龙江日报网站连接超时或该日期无内容，请检查网络",
                    status=DownloadStatus.FAILED,
                )

            resp.encoding = resp.encoding or "utf-8"
            node_links = self._parse_node_links(resp.text, yyyymm, dd)
            if not node_links:
                return DownloadResult(
                    success=False,
                    message="未找到该日期的报纸版面",
                    status=DownloadStatus.FAILED,
                )

            base_for_nodes = resp.url.rsplit("/", 1)[0] + "/"
            return self._download_pdfs(
                session, node_links, base_for_nodes, part_path, str(output_file),
                progress_callback, is_cancelled
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

    def _parse_node_links(self, html: str, yyyymm: str, dd: str) -> list[str]:
        """解析 node 页面链接，按版号排序"""
        links = re.findall(r'href=["\']([^"\']*?node[^"\']*?\.html)["\']', html, re.I)
        if links:
            seen = set()
            unique = []
            for x in links:
                if x not in seen:
                    seen.add(x)
                    unique.append(x)
            # 按 node_01, node_02... 排序
            def node_num(s: str) -> int:
                m = re.search(r"node_?(\d+)", s, re.I)
                return int(m.group(1)) if m else 99
            unique.sort(key=node_num)
            return unique
        return [f"{yyyymm}/{dd}/node_{i:02d}.html" for i in range(1, 17)]

    def _download_pdfs(
        self,
        session: requests.Session,
        node_links: list[str],
        layout_base: str,
        part_path: str,
        output_file: str,
        progress_callback,
        is_cancelled,
    ) -> DownloadResult:
        """逐 node 下载 PDF 并合并"""
        ref = f"{self.BASE_URL}/"
        downloaded = 0

        for i, node_rel in enumerate(node_links):
            if is_cancelled and is_cancelled():
                return DownloadResult(
                    success=False,
                    message="用户取消下载",
                    status=DownloadStatus.CANCELLED,
                )
            if progress_callback:
                progress_callback(i, len(node_links), f"正在下载第 {i+1}/{len(node_links)} 版")
            if i > 0:
                random_delay(0.4, 1.0)

            node_url = node_rel if node_rel.startswith("http") else urljoin(layout_base, node_rel)
            resp = None
            for _ in range(3):
                try:
                    resp = session.get(
                        node_url,
                        headers=get_browser_headers(ref, include_ua=False),
                        timeout=25,
                    )
                    if resp and resp.status_code == 200:
                        break
                except (requests.RequestException, TimeoutError):
                    resp = None
            if not resp or resp.status_code != 200:
                continue
            resp.encoding = resp.encoding or "utf-8"
            pdfs = re.findall(r'["\']([^"\']+\.pdf)["\']', resp.text, re.I)
            if not pdfs:
                continue
            pdf_url = urljoin(node_url, pdfs[0])
            random_delay(0.2, 0.6)
            r = None
            for _ in range(3):
                try:
                    r = session.get(
                        pdf_url,
                        headers=get_browser_headers(node_url, include_ua=False),
                        timeout=45,
                    )
                    if r and r.status_code == 200 and len(r.content) > 500:
                        break
                except (requests.RequestException, TimeoutError):
                    r = None
            if r and r.status_code == 200 and len(r.content) > 500:
                fn = f"hljrb_{i+1:02d}.pdf"
                with open(os.path.join(part_path, fn), "wb") as f:
                    f.write(r.content)
                downloaded += 1

        if downloaded == 0:
            return DownloadResult(
                success=False,
                message="未能下载任何版面，请检查日期或网络",
                status=DownloadStatus.FAILED,
            )
        if progress_callback:
            progress_callback(len(node_links), len(node_links), "正在合并 PDF...")
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
