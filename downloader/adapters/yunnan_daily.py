# -*- coding: utf-8 -*-
"""
云南日报电子版下载适配器
来源：yndaily.yunnan.cn
说明：从 pad 版 node 页解析 pic/YYYYMM/DD/xxx.jpg.1 版面图，合并为 PDF
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

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

warnings.filterwarnings("ignore", message="Multiple definitions in dictionary")

from downloader.base import BaseAdapter, DownloadTask, DownloadResult, DownloadStatus
from downloader.http_client import get_browser_headers, random_delay, create_session


class YunnanDailyAdapter(BaseAdapter):
    """云南日报电子版下载器"""

    BASE_URL = "https://yndaily.yunnan.cn"

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
        output_file = Path(save_dir) / f"云南日报_{date_str}.pdf"
        if output_file.exists():
            return DownloadResult(
                success=True,
                file_path=str(output_file),
                message="该日期已下载过，跳过",
                status=DownloadStatus.COMPLETED,
            )

        if not HAS_PILLOW:
            return DownloadResult(
                success=False,
                message="需要安装 Pillow，请运行：pip install Pillow",
                status=DownloadStatus.FAILED,
            )

        part_path = tempfile.mkdtemp(prefix="ynrb_")
        try:
            session = create_session(f"{self.BASE_URL}/")
            random_delay(0.2, 0.6)

            # 从 pad 索引页获取 node 列表
            pad_index = f"{self.BASE_URL}/pad/{yyyymm}/{dd}/"
            resp = None
            for retry in range(3):
                try:
                    resp = session.get(
                        pad_index,
                        headers=get_browser_headers(f"{self.BASE_URL}/", include_ua=False),
                        timeout=25,
                    )
                    if resp and resp.status_code == 200:
                        break
                except (requests.RequestException, TimeoutError):
                    resp = None
            if not resp or resp.status_code != 200:
                return DownloadResult(
                    success=False,
                    message="云南日报网站连接超时或该日期无内容，请检查网络",
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

            pad_base = f"{self.BASE_URL}/pad/{yyyymm}/{dd}/"
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

                node_url = urljoin(pad_base, node_rel)
                r = None
                for _ in range(3):
                    try:
                        r = session.get(
                            node_url,
                            headers=get_browser_headers(ref, include_ua=False),
                            timeout=25,
                        )
                        if r and r.status_code == 200:
                            break
                    except (requests.RequestException, TimeoutError):
                        r = None
                if not r or r.status_code != 200:
                    continue
                r.encoding = r.encoding or "utf-8"
                img_src = self._parse_layout_image(r.text, yyyymm, dd)
                if not img_src:
                    continue
                img_url = urljoin(node_url, img_src)
                rr = None
                for try_url in [img_url, img_url.rstrip(".1")]:
                    for _ in range(3):
                        try:
                            rr = session.get(
                                try_url,
                                headers=get_browser_headers(ref, include_ua=False),
                                timeout=30,
                            )
                            if rr and rr.status_code == 200 and len(rr.content) > 1000:
                                break
                        except (requests.RequestException, TimeoutError):
                            rr = None
                    if rr and rr.status_code == 200 and len(rr.content) > 1000:
                        break
                if rr and rr.status_code == 200 and len(rr.content) > 1000:
                    path = os.path.join(part_path, f"ynrb_{i+1:02d}.jpg")
                    with open(path, "wb") as f:
                        f.write(rr.content)
                    downloaded += 1

            if downloaded == 0:
                return DownloadResult(
                    success=False,
                    message="未能下载任何版面，请检查日期或网络",
                    status=DownloadStatus.FAILED,
                )
            if progress_callback:
                progress_callback(len(node_links), len(node_links), "正在合并 PDF...")
            self._images_to_pdf(part_path, str(output_file))
            return DownloadResult(
                success=True,
                file_path=str(output_file),
                message="下载成功",
                status=DownloadStatus.COMPLETED,
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
        """从 pad 索引页解析 node 链接，按版号排序"""
        links = re.findall(r'href=["\']([^"\']*?node_(\d{2})\.html)["\']', html, re.I)
        if links:
            seen = set()
            ordered = []
            for href, num in sorted(links, key=lambda x: int(x[1])):
                if num not in seen:
                    seen.add(num)
                    ordered.append(href)
            return ordered
        return [f"node_{i:02d}.html" for i in range(1, 17)]

    def _parse_layout_image(self, html: str, yyyymm: str, dd: str) -> str | None:
        """从 node 页解析版面图，pic/YYYYMM/DD/xxx.jpg.1"""
        m = re.search(r'<img[^>]+src=["\']([^"\']*?/pic/\d{6}/\d{2}/[^"\']+\.jpg(?:\.1)?)["\']', html, re.I)
        if m:
            return m.group(1)
        m = re.search(r'src=["\'](\.\./\.\./pic/\d{6}/\d{2}/[^"\']+\.jpg(?:\.1)?)["\']', html, re.I)
        if m:
            return m.group(1)
        return None

    def _images_to_pdf(self, part_path: str, output_file: str) -> None:
        """将图片合并为 PDF"""
        exts = (".jpg", ".jpeg", ".png")
        files = sorted(
            [f for f in os.listdir(part_path) if f.lower().endswith(exts)],
            key=lambda x: int(re.search(r"\d+", x).group()) if re.search(r"\d+", x) else 0,
        )
        if not files:
            return
        try:
            merger = PyPDF2.PdfMerger(strict=False)
        except TypeError:
            merger = PyPDF2.PdfMerger()
        for f in files:
            full_path = os.path.join(part_path, f)
            try:
                img = Image.open(full_path)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                pdf_path = full_path.rsplit(".", 1)[0] + "_tmp.pdf"
                img.save(pdf_path, "PDF")
                img.close()
                if os.path.getsize(pdf_path) >= 10:
                    merger.append(pdf_path)
                try:
                    os.remove(pdf_path)
                except OSError:
                    pass
            except Exception:
                pass
        merger.write(output_file)
        merger.close()
