# -*- coding: utf-8 -*-
"""
山西日报电子版下载适配器
参考：http://epaper.sxrb.com
说明：下载版面图片 b_page_NN.jpg 合并为 PDF
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


class ShanxiDailyAdapter(BaseAdapter):
    """山西日报电子版下载器"""

    BASE_URL = "http://epaper.sxrb.com"

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
        yyyymmdd = yyyy + mm + dd

        save_dir = task.save_dir
        try:
            Path(save_dir).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return DownloadResult(
                success=False,
                message=f"无法创建保存目录：{e}",
                status=DownloadStatus.FAILED,
            )
        output_file = Path(save_dir) / f"山西日报_{date_str}.pdf"
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

        part_path = tempfile.mkdtemp(prefix="sxrb_")
        try:
            session = create_session(f"{self.BASE_URL}/")
            random_delay(0.2, 0.6)

            ref = f"{self.BASE_URL}/"
            downloaded = 0
            page = 1
            max_pages = 24

            while page <= max_pages:
                if is_cancelled and is_cancelled():
                    return DownloadResult(
                        success=False,
                        message="用户取消下载",
                        status=DownloadStatus.CANCELLED,
                    )
                if progress_callback:
                    progress_callback(page - 1, page, f"正在下载第 {page} 版")
                if page > 1:
                    random_delay(0.4, 1.0)

                nn = f"{page:02d}"
                img_url = f"{self.BASE_URL}/paperdata/sxrb/{yyyymmdd}/b_page_{nn}.jpg"
                for retry in range(3):
                    try:
                        r = session.get(
                            img_url,
                            headers=get_browser_headers(ref, include_ua=False),
                            timeout=30,
                        )
                        if r and r.status_code == 200 and len(r.content) > 1000:
                            path = os.path.join(part_path, f"sxrb_{nn}.jpg")
                            with open(path, "wb") as f:
                                f.write(r.content)
                            downloaded += 1
                            page += 1
                            break
                    except (requests.RequestException, TimeoutError):
                        pass
                else:
                    break

            if downloaded == 0:
                return DownloadResult(
                    success=False,
                    message="未找到该日期的山西日报，请检查日期或网络",
                    status=DownloadStatus.FAILED,
                )
            if progress_callback:
                progress_callback(downloaded, downloaded, "正在合并 PDF...")
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
