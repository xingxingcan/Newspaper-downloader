# -*- coding: utf-8 -*-
"""
报纸下载器 - 主程序入口
面向 Windows 的报纸电子版批量下载桌面应用
"""

import sys
import os
import logging

# 屏蔽 PyPDF2 合并时的 "Multiple definitions in dictionary" 日志（人民日报 PDF 含非标准结构）
for name in ("PyPDF2", "pypdf"):
    logging.getLogger(name).setLevel(logging.ERROR)

# 确保项目根目录在 Python 路径中，便于打包和开发环境运行
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

from ui.main_window import MainWindow, get_stylesheet


def _icon_path() -> str:
    """获取图标路径，兼容开发环境与 PyInstaller 打包"""
    base = getattr(sys, "_MEIPASS", app_dir)
    return os.path.join(base, "image", "news.ico")


def main() -> None:
    """应用主函数"""
    # 高 DPI 支持（Qt 6.4+）
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except AttributeError:
        pass
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("报纸下载器")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("NewspaperDownloader")

    # 设置默认字体
    font = QFont()
    font.setFamily("Microsoft YaHei")
    font.setPointSize(10)
    app.setFont(font)

    # 应用全局样式（含 QMessageBox 等对话框）
    app.setStyleSheet(get_stylesheet())

    # 设置应用与窗口图标
    icon_path = _icon_path()
    icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    window = MainWindow()
    if not icon.isNull():
        window.setWindowIcon(icon)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
