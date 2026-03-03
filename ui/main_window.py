# -*- coding: utf-8 -*-
"""
主窗口界面
采用 PyQt6 实现，蓝白/浅灰主题，响应式布局
"""

import os
from datetime import datetime, timedelta
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QCheckBox,
    QLabel,
    QPushButton,
    QLineEdit,
    QDateEdit,
    QProgressBar,
    QTextEdit,
    QScrollArea,
    QFrame,
    QSizePolicy,
    QFileDialog,
    QMessageBox,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt, QDate, QThread
from PyQt6.QtGui import QFont, QDesktopServices, QUrl

from config import ConfigManager, NEWSPAPER_SOURCES
from downloader.worker import DownloadWorker
from downloader.base import DownloadResult


# 主题配色
COLORS = {
    "bg_primary": "#F5F7FA",
    "bg_card": "#FFFFFF",
    "accent": "#2563EB",
    "accent_hover": "#1D4ED8",
    "text_primary": "#1E293B",
    "text_secondary": "#64748B",
    "border": "#E2E8F0",
    "success": "#22C55E",
    "error": "#EF4444",
}


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self._worker: DownloadWorker | None = None
        self._thread: QThread | None = None
        self._completed_count = 0
        self._setup_ui()
        self._load_config()
        self._connect_signals()

    def _setup_ui(self) -> None:
        self.setWindowTitle("报纸下载器")
        self.setMinimumSize(800, 600)
        w, h = self.config.window_size
        self.resize(w, h)

        # 使用样式表实现现代蓝白主题
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS["bg_primary"]};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {COLORS["border"]};
                border-radius: 8px;
                margin-top: 12px;
                padding: 16px 12px 12px 12px;
                background-color: {COLORS["bg_card"]};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 0 8px;
                color: {COLORS["text_primary"]};
                background-color: {COLORS["bg_card"]};
            }}
            QPushButton {{
                background-color: {COLORS["accent"]};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS["accent_hover"]};
            }}
            QPushButton:disabled {{
                background-color: #94A3B8;
                color: #CBD5E1;
            }}
            QPushButton#secondary {{
                background-color: #E2E8F0;
                color: {COLORS["text_primary"]};
            }}
            QPushButton#secondary:hover {{
                background-color: #CBD5E1;
            }}
            QPushButton#danger {{
                background-color: {COLORS["error"]};
            }}
            QPushButton#danger:hover {{
                background-color: #DC2626;
            }}
            QLineEdit, QDateEdit {{
                border: 1px solid {COLORS["border"]};
                border-radius: 6px;
                padding: 8px 12px;
                background: white;
                min-height: 20px;
            }}
            QLineEdit:focus, QDateEdit:focus {{
                border-color: {COLORS["accent"]};
            }}
            QProgressBar {{
                border: 1px solid {COLORS["border"]};
                border-radius: 6px;
                text-align: center;
                background: white;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS["accent"]};
                border-radius: 5px;
            }}
            QTextEdit {{
                border: 1px solid {COLORS["border"]};
                border-radius: 6px;
                padding: 8px;
                background: white;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 12px;
            }}
            QCheckBox {{
                spacing: 8px;
            }}
            QScrollArea {{
                border: none;
                background: transparent;
            }}
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # 1. 报纸选择区
        paper_group = QGroupBox("报纸选择")
        paper_layout = QVBoxLayout()
        btn_row = QHBoxLayout()
        select_all_btn = QPushButton("全选")
        select_all_btn.setObjectName("secondary")
        select_all_btn.clicked.connect(self._select_all_papers)
        deselect_btn = QPushButton("全不选")
        deselect_btn.setObjectName("secondary")
        deselect_btn.clicked.connect(self._deselect_all_papers)
        btn_row.addWidget(select_all_btn)
        btn_row.addWidget(deselect_btn)
        btn_row.addStretch()
        paper_layout.addLayout(btn_row)
        self.paper_checkboxes = []
        for src in NEWSPAPER_SOURCES:
            if not src.get("enabled", True):
                continue
            cb = QCheckBox(src["name"])
            cb.setProperty("newspaper_id", src["id"])
            cb.setToolTip(src.get("description", ""))
            self.paper_checkboxes.append(cb)
            paper_layout.addWidget(cb)
        paper_group.setLayout(paper_layout)
        layout.addWidget(paper_group)

        # 2. 日期与保存区（同一行）
        row1 = QHBoxLayout()
        # 日期选择
        date_group = QGroupBox("日期选择")
        date_layout = QVBoxLayout()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDateRange(
            QDate.currentDate().addYears(-1),
            QDate.currentDate(),
        )
        date_layout.addWidget(self.date_edit)
        date_group.setLayout(date_layout)
        row1.addWidget(date_group, 1)

        # 保存目录
        save_group = QGroupBox("保存目录")
        save_layout = QVBoxLayout()
        save_row = QHBoxLayout()
        self.save_dir_edit = QLineEdit()
        self.save_dir_edit.setPlaceholderText("选择保存位置...")
        self.save_dir_edit.setReadOnly(True)
        save_row.addWidget(self.save_dir_edit)
        browse_btn = QPushButton("浏览")
        browse_btn.setObjectName("secondary")
        browse_btn.clicked.connect(self._on_browse)
        save_row.addWidget(browse_btn)
        open_btn = QPushButton("打开目录")
        open_btn.setObjectName("secondary")
        open_btn.clicked.connect(self._on_open_dir)
        save_row.addWidget(open_btn)
        save_layout.addLayout(save_row)
        save_group.setLayout(save_layout)
        row1.addWidget(save_group, 2)
        layout.addLayout(row1)

        # 3. 下载控制区
        ctrl_group = QGroupBox("下载控制")
        ctrl_layout = QHBoxLayout()
        self.download_btn = QPushButton("开始下载")
        self.download_btn.setMinimumHeight(40)
        self.download_btn.clicked.connect(self._on_start_download)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("danger")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.cancel_btn.setEnabled(False)
        ctrl_layout.addWidget(self.download_btn)
        ctrl_layout.addWidget(self.cancel_btn)
        ctrl_layout.addStretch()
        ctrl_group.setLayout(ctrl_layout)
        layout.addWidget(ctrl_group)

        # 4. 进度显示区
        progress_group = QGroupBox("进度与状态")
        progress_layout = QVBoxLayout()
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        progress_layout.addWidget(self.status_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(150)
        progress_layout.addWidget(self.log_text)
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group, 1)

    def _load_config(self) -> None:
        self.save_dir_edit.setText(self.config.save_dir)
        if self.config.last_date:
            try:
                d = datetime.strptime(self.config.last_date, "%Y-%m-%d")
                self.date_edit.setDate(QDate(d.year, d.month, d.day))
            except ValueError:
                pass
        for nid in self.config.last_newspapers:
            for cb in self.paper_checkboxes:
                if cb.property("newspaper_id") == nid:
                    cb.setChecked(True)
                    break

    def _connect_signals(self) -> None:
        pass

    def _on_browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择保存目录", self.save_dir_edit.text())
        if path:
            self.save_dir_edit.setText(path)
            self.config.save_dir = path

    def _on_open_dir(self) -> None:
        path = self.save_dir_edit.text()
        if path and Path(path).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            QMessageBox.information(self, "提示", "请先选择有效的保存目录。")

    def _select_all_papers(self) -> None:
        for cb in self.paper_checkboxes:
            cb.setChecked(True)

    def _deselect_all_papers(self) -> None:
        for cb in self.paper_checkboxes:
            cb.setChecked(False)

    def _get_selected_newspapers(self) -> list[str]:
        return [
            cb.property("newspaper_id")
            for cb in self.paper_checkboxes
            if cb.isChecked()
        ]

    def _on_start_download(self) -> None:
        newspapers = self._get_selected_newspapers()
        if not newspapers:
            QMessageBox.warning(self, "提示", "请至少选择一份报纸。")
            return
        save_dir = self.save_dir_edit.text().strip()
        if not save_dir:
            QMessageBox.warning(self, "提示", "请选择保存目录。")
            return
        try:
            Path(save_dir).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            QMessageBox.critical(self, "错误", f"无法创建保存目录：{e}")
            return

        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        self.config.last_date = date_str
        self.config.last_newspapers = newspapers

        self.download_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(newspapers) * 100)
        self._completed_count = 0
        self.log_text.clear()
        self._log(f"开始下载 {len(newspapers)} 份报纸，日期：{date_str}")

        self._worker = DownloadWorker(newspapers, date_str, save_dir)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_download_progress)
        self._worker.task_done.connect(self._on_task_done)
        self._worker.all_done.connect(self._on_all_done)
        self._thread.start()

    def _on_download_progress(self, name: str, current: int, total: int, msg: str) -> None:
        """由 worker 信号触发，在主线程执行"""
        self.status_label.setText(f"{name} - {msg}")
        if total > 0:
            pct = int(100 * current / total)
            base = self._completed_count * 100
            self.progress_bar.setValue(min(base + pct, self.progress_bar.maximum()))

    def _on_task_done(self, newspaper_id: str, result: DownloadResult) -> None:
        self._completed_count += 1
        if result.success:
            self._log(f"✓ {result.file_path} - {result.message}")
        else:
            self._log(f"✗ {result.message}")
        self.progress_bar.setValue(
            min(self._completed_count * 100, self.progress_bar.maximum())
        )

    def _on_all_done(self) -> None:
        self.download_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("全部完成")
        self._log("下载任务已结束。")
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(3000)

    def _on_cancel(self) -> None:
        if self._worker:
            self._worker.cancel()
        self._log("用户取消下载")

    def _log(self, msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{ts}] {msg}")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.config.window_size = (self.width(), self.height())
