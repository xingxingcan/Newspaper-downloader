# -*- coding: utf-8 -*-
"""
新华每日电讯电子版下载适配器
来源：http://mrdx.cn
说明：优先下载 PDF（PDF/YYYYMMDD/NN.pdf），无则下载版面图片（IMAGE/YYYYMMDD/NN/PageNN-1500.jpg）合并为 PDF
"""

import os
import re
import shutil
import tempfile
import warnings
from pathlib import Path

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


class XinhuaAdapter(BaseAdapter):
    """新华每日电讯电子版下载器"""

    BASE_URL = "http://mrdx.cn"
    # 首页与 content 路径（优先 content，兼容 h5）
    INDEX_PATHS = [
        "content",
        "h5/mrdx/content",
    ]

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
        output_file = Path(save_dir) / f"新华每日电讯_{date_str}.pdf"
        if output_file.exists():
            return DownloadResult(
                success=True,
                file_path=str(output_file),
                message="该日期已下载过，跳过",
                status=DownloadStatus.COMPLETED,
            )

        part_path = tempfile.mkdtemp(prefix="mrdx_")
        try:
            session = create_session(f"{self.BASE_URL}/")
            random_delay(0.2, 0.6)

            page_count = self._fetch_page_count(session, yyyymmdd)
            if page_count <= 0:
                page_count = 8
            page_count = min(page_count, 24)

            # 1. 优先尝试下载 PDF
            result = self._download_pdfs(
                session, yyyymmdd, page_count, part_path, str(output_file),
                progress_callback, is_cancelled
            )
            if result.success:
                return result

            # 2. 回退：下载版面图片并合并为 PDF
            if HAS_PILLOW:
                return self._download_images_and_merge(
                    session, yyyymmdd, page_count, part_path, str(output_file),
                    progress_callback, is_cancelled
                )
            return DownloadResult(
                success=False,
                message="未能获取 PDF，且需要 Pillow 才能从图片合并，请安装：pip install Pillow",
                status=DownloadStatus.FAILED,
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

    def _fetch_page_count(self, session: requests.Session, yyyymmdd: str) -> int:
        """获取首版页面并解析版面数量。仅匹配 01-24 版，避免误解析日期/ID"""
        for path in self.INDEX_PATHS:
            url = f"{self.BASE_URL}/{path}/{yyyymmdd}/Page01BC.htm"
            try:
                resp = session.get(
                    url,
                    headers=get_browser_headers(f"{self.BASE_URL}/", include_ua=False),
                    timeout=25,
                )
                if resp and resp.status_code == 200 and len(resp.text) > 200:
                    resp.encoding = "gbk" if "gb" in (resp.encoding or "").lower() else "utf-8"
                    # 只匹配 Page01 ~ Page24，避免误匹配日期(20260304)等
                    matches = re.findall(r"Page0?([1-9]|1\d|2[0-4])[A-Z]*\.htm", resp.text, re.I)
                    if matches:
                        return min(max(int(m) for m in matches), 24)
                    return 0
            except (requests.RequestException, TimeoutError):
                continue
        return 0

    def _download_pdfs(
        self,
        session: requests.Session,
        yyyymmdd: str,
        page_count: int,
        part_path: str,
        output_file: str,
        progress_callback,
        is_cancelled,
    ) -> DownloadResult:
        """下载各版 PDF 并合并。URL: PDF/YYYYMMDD/NN.pdf"""
        ref = f"{self.BASE_URL}/"
        downloaded = 0

        for page in range(1, page_count + 1):
            if is_cancelled and is_cancelled():
                return DownloadResult(success=False, message="用户取消下载", status=DownloadStatus.CANCELLED)
            if progress_callback:
                progress_callback(page - 1, page_count, f"正在下载第 {page}/{page_count} 版 PDF")
            if page > 1:
                random_delay(0.4, 1.0)

            nn = f"{page:02d}"
            pdf_url = f"{self.BASE_URL}/PDF/{yyyymmdd}/{nn}.pdf"
            for _ in range(3):
                try:
                    r = session.get(pdf_url, headers=get_browser_headers(ref, include_ua=False), timeout=30)
                    if r and r.status_code == 200 and len(r.content) > 500:
                        with open(os.path.join(part_path, f"mrdx_{nn}.pdf"), "wb") as f:
                            f.write(r.content)
                        downloaded += 1
                        break
                except (requests.RequestException, TimeoutError):
                    pass

        if downloaded == 0:
            return DownloadResult(success=False, message="", status=DownloadStatus.FAILED)
        if progress_callback:
            progress_callback(page_count, page_count, "正在合并 PDF...")
        self._merge_pdfs(part_path, output_file)
        return DownloadResult(
            success=True,
            file_path=output_file,
            message="下载成功",
            status=DownloadStatus.COMPLETED,
        )

    def _download_images_and_merge(
        self,
        session: requests.Session,
        yyyymmdd: str,
        page_count: int,
        part_path: str,
        output_file: str,
        progress_callback,
        is_cancelled,
    ) -> DownloadResult:
        """下载版面图片并合并为 PDF。URL: IMAGE/YYYYMMDD/NN/PageNN-1500.jpg"""
        ref = f"{self.BASE_URL}/"
        downloaded = 0

        for page in range(1, page_count + 1):
            if is_cancelled and is_cancelled():
                return DownloadResult(success=False, message="用户取消下载", status=DownloadStatus.CANCELLED)
            if progress_callback:
                progress_callback(page - 1, page_count, f"正在下载第 {page}/{page_count} 版图片")
            if page > 1:
                random_delay(0.4, 1.0)

            nn = f"{page:02d}"
            img_url = f"{self.BASE_URL}/IMAGE/{yyyymmdd}/{nn}/Page{nn}-1500.jpg"
            for _ in range(3):
                try:
                    r = session.get(img_url, headers=get_browser_headers(ref, include_ua=False), timeout=30)
                    if r and r.status_code == 200 and len(r.content) > 1000:
                        path = os.path.join(part_path, f"mrdx_{nn}.jpg")
                        with open(path, "wb") as f:
                            f.write(r.content)
                        downloaded += 1
                        break
                except (requests.RequestException, TimeoutError):
                    pass

        if downloaded == 0:
            return DownloadResult(
                success=False,
                message="未能下载任何版面，新华每日电讯官网可能未提供该日期内容",
                status=DownloadStatus.FAILED,
            )
        if progress_callback:
            progress_callback(page_count, page_count, "正在将图片合并为 PDF...")
        self._images_to_pdf(part_path, output_file)
        return DownloadResult(
            success=True,
            file_path=output_file,
            message="已从版面图片合并为 PDF",
            status=DownloadStatus.COMPLETED,
        )

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
