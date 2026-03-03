# -*- coding: utf-8 -*-
"""
新华每日电讯电子版下载适配器
参考：http://mrdx.cn/content/YYYYMMDD/Page01BC.htm
说明：优先下载 PDF；无 PDF 时下载版面图片（PageNN-1500.jpg）合并为 PDF
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
    # 两种常见 URL 格式
    CONTENT_PATHS = [
        "content",           # http://mrdx.cn/content/YYYYMMDD/Page01BC.htm
        "h5/mrdx/content",    # http://mrdx.cn/h5/mrdx/content/YYYYMMDD/Page01BC.htm
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

            html, content_base = self._fetch_index(session, yyyymmdd)
            if not html:
                return DownloadResult(
                    success=False,
                    message="新华每日电讯网站连接超时或该日期无内容，请检查网络后重试",
                    status=DownloadStatus.FAILED,
                )

            page_count = self._parse_page_count(html)
            if page_count == 0:
                # 默认尝试 8 版（常见版数）
                page_count = 8

            pdf_urls = self._extract_pdf_urls(html, content_base, yyyymmdd)
            if not pdf_urls:
                pdf_urls = self._guess_pdf_urls(content_base, yyyymmdd, page_count)

            result = self._download_pages(
                session, yyyymmdd, part_path, str(output_file),
                html, content_base, pdf_urls, page_count,
                progress_callback, is_cancelled
            )
            if result.success:
                return result
            # PDF 失败时回退：尝试下载版面图片并合并为 PDF
            return self._download_images_and_merge(
                session, yyyymmdd, part_path, str(output_file),
                html, content_base, page_count,
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

    def _fetch_index(self, session: requests.Session, yyyymmdd: str) -> tuple[str | None, str | None]:
        """获取首版页面，返回 (html, content_base_url)"""
        for path in self.CONTENT_PATHS:
            url = f"{self.BASE_URL}/{path}/{yyyymmdd}/Page01BC.htm"
            try:
                resp = session.get(
                    url,
                    headers=get_browser_headers(f"{self.BASE_URL}/", include_ua=False),
                    timeout=20,
                )
                if resp and resp.status_code == 200:
                    resp.encoding = resp.encoding or "utf-8"
                    if "gb" in (resp.encoding or "").lower() or "gbk" in (resp.encoding or "").lower():
                        resp.encoding = "gbk"
                    else:
                        resp.encoding = "utf-8"
                    base = f"{self.BASE_URL}/{path}/{yyyymmdd}"
                    return resp.text, base
            except (requests.RequestException, TimeoutError):
                continue
        return None, None

    def _parse_page_count(self, html: str) -> int:
        """从页面解析版面数量（Page01BC, Page02BC, ...）"""
        matches = re.findall(r"Page(\d+)[A-Z]*\.htm", html, re.I)
        return max(int(m) for m in matches) if matches else 0

    def _extract_pdf_urls(self, html: str, content_base: str, yyyymmdd: str) -> list[str]:
        """从 HTML 中提取 PDF 链接"""
        urls = []
        # 直接 href 到 .pdf
        for m in re.finditer(r'href\s*=\s*["\']([^"\']*?\.pdf)["\']', html, re.I):
            u = m.group(1)
            if not u.startswith("http"):
                u = content_base.rstrip("/") + "/" + u.lstrip("./")
            if u not in urls:
                urls.append(u)
        # 路径中带 pdf 或 attachment
        for m in re.finditer(r'["\']([^"\']*?(?:pdf|attachment)[^"\']*?\.pdf)["\']', html, re.I):
            u = m.group(1)
            if not u.startswith("http"):
                u = content_base.rstrip("/") + "/" + u.lstrip("./")
            if u not in urls:
                urls.append(u)
        return urls

    def _guess_pdf_urls(self, content_base: str, yyyymmdd: str, page_count: int) -> list[str]:
        """根据常见规则猜测 PDF URL"""
        urls = []
        base = content_base.rstrip("/")
        for page in range(1, page_count + 1):
            nn = f"{page:02d}"
            candidates = [
                f"{base}/Page{nn}BC.pdf",
                f"{base}/Page{nn}.pdf",
                f"{base}/pdf/Page{nn}.pdf",
                f"{self.BASE_URL}/pdf/{yyyymmdd}/Page{nn}.pdf",
                f"{self.BASE_URL}/images/{yyyymmdd}/Page{nn}.pdf",
            ]
            urls.extend(candidates)
        return urls

    def _download_pages(
        self,
        session: requests.Session,
        yyyymmdd: str,
        part_path: str,
        output_file: str,
        html: str,
        content_base: str,
        pdf_urls: list[str],
        page_count: int,
        progress_callback,
        is_cancelled,
    ) -> DownloadResult:
        """下载各版 PDF 并合并"""
        ref = f"{self.BASE_URL}/"
        downloaded = 0

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

            nn = f"{page:02d}"
            candidates = []
            if pdf_urls:
                candidates = [u for u in pdf_urls if f"Page{nn}" in u or re.search(rf"Page0?{page}\D", u)]
            if not candidates:
                candidates = [
                    f"{self.BASE_URL}/content/{yyyymmdd}/Page{nn}BC.pdf",
                    f"{self.BASE_URL}/content/{yyyymmdd}/Page{nn}.pdf",
                    f"{self.BASE_URL}/h5/mrdx/content/{yyyymmdd}/Page{nn}BC.pdf",
                ]
            saved = False
            for pdf_url in candidates:
                for retry in range(3):
                    try:
                        r = session.get(
                            pdf_url,
                            headers=get_browser_headers(ref, include_ua=False),
                            timeout=30,
                        )
                        if r and r.status_code == 200 and len(r.content) > 500:
                            filename = f"mrdx_{page:02d}.pdf"
                            with open(os.path.join(part_path, filename), "wb") as f:
                                f.write(r.content)
                            downloaded += 1
                            saved = True
                            break
                    except (requests.RequestException, TimeoutError):
                        pass
                if saved:
                    break

        if downloaded == 0:
            return DownloadResult(
                success=False,
                message="",
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

    def _extract_image_urls(self, html: str, content_base: str) -> list[str]:
        """从 HTML 提取版面图片链接（PageNN-1500.jpg 等）"""
        urls = []
        for m in re.finditer(r'["\']([^"\']*?Page\d+-?\d*\.(?:jpg|jpeg|png))["\']', html, re.I):
            u = m.group(1)
            if "IMAGE" in u or "Page" in u:
                if not u.startswith("http"):
                    u = self._resolve_url(u, content_base)
                if u not in urls:
                    urls.append(u)
        for m in re.finditer(r'["\']([^"\']*?/IMAGE/[^"\']+\.(?:jpg|jpeg|png))["\']', html, re.I):
            u = m.group(1)
            if not u.startswith("http"):
                u = self._resolve_url(u, content_base)
            if u not in urls:
                urls.append(u)
        return urls

    def _resolve_url(self, rel: str, content_base: str) -> str:
        """相对路径转绝对 URL，支持 ../"""
        from urllib.parse import urljoin
        base_slash = content_base.rstrip("/") + "/"
        return urljoin(base_slash, rel)

    def _guess_image_urls(self, yyyymmdd: str, page_count: int) -> list[str]:
        """猜测版面图片 URL，格式 IMAGE/YYYYMMDD/NN/PageNN-1500.jpg"""
        urls = []
        for page in range(1, page_count + 1):
            nn = f"{page:02d}"
            urls.extend([
                f"{self.BASE_URL}/IMAGE/{yyyymmdd}/{nn}/Page{nn}-1500.jpg",
                f"{self.BASE_URL}/h5/mrdx/IMAGE/{yyyymmdd}/{nn}/Page{nn}-1500.jpg",
                f"{self.BASE_URL}/content/{yyyymmdd}/IMAGE/{nn}/Page{nn}-1500.jpg",
                f"{self.BASE_URL}/content/{yyyymmdd}/Page{nn}-1500.jpg",
                f"{self.BASE_URL}/content/{yyyymmdd}/images/Page{nn}-1500.jpg",
            ])
        return urls

    def _download_images_and_merge(
        self,
        session: requests.Session,
        yyyymmdd: str,
        part_path: str,
        output_file: str,
        html: str,
        content_base: str,
        page_count: int,
        progress_callback,
        is_cancelled,
    ) -> DownloadResult:
        """下载版面图片并合并为 PDF"""
        if not HAS_PILLOW:
            return DownloadResult(
                success=False,
                message="需要安装 Pillow 才能将图片合并为 PDF，请运行：pip install Pillow",
                status=DownloadStatus.FAILED,
            )
        ref = f"{self.BASE_URL}/"
        img_urls = self._extract_image_urls(html, content_base)
        if not img_urls:
            img_urls = self._guess_image_urls(yyyymmdd, page_count)

        downloaded = 0
        for page in range(1, page_count + 1):
            if is_cancelled and is_cancelled():
                return DownloadResult(
                    success=False,
                    message="用户取消下载",
                    status=DownloadStatus.CANCELLED,
                )
            if progress_callback:
                progress_callback(page - 1, page_count, f"正在下载第 {page}/{page_count} 版图片")
            if page > 1:
                random_delay(0.4, 1.0)
            nn = f"{page:02d}"
            candidates = [u for u in img_urls if f"Page{nn}" in u or re.search(rf"/{nn}/", u)]
            if not candidates:
                candidates = [
                    f"{self.BASE_URL}/IMAGE/{yyyymmdd}/{nn}/Page{nn}-1500.jpg",
                    f"{self.BASE_URL}/h5/mrdx/IMAGE/{yyyymmdd}/{nn}/Page{nn}-1500.jpg",
                    f"{self.BASE_URL}/content/{yyyymmdd}/Page{nn}-1500.jpg",
                ]
            saved = False
            for img_url in candidates:
                for retry in range(3):
                    try:
                        r = session.get(
                            img_url,
                            headers=get_browser_headers(ref, include_ua=False),
                            timeout=30,
                        )
                        if r and r.status_code == 200 and len(r.content) > 1000:
                            ext = "jpg" if "jpg" in img_url.lower() or "jpeg" in img_url.lower() else "png"
                            path = os.path.join(part_path, f"mrdx_{page:02d}.{ext}")
                            with open(path, "wb") as f:
                                f.write(r.content)
                            downloaded += 1
                            saved = True
                            break
                    except (requests.RequestException, TimeoutError):
                        pass
                if saved:
                    break

        if downloaded == 0:
            return DownloadResult(
                success=False,
                message="未能下载任何版面。新华每日电讯官网可能未提供该日期的 PDF 或版面图片。",
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
        """将图片文件合并为单个 PDF"""
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
