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
from PyQt6.QtGui import QFont

from ui.main_window import MainWindow, get_stylesheet


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

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
