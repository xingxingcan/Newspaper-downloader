# -*- coding: utf-8 -*-
"""
主窗口界面
浅色系主题，现代简洁外观
"""

from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QCheckBox,
    QLabel,
    QPushButton,
    QLineEdit,
    QProgressBar,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QFrame,
)
from PyQt6.QtCore import Qt, QDate, QThread, QUrl
from PyQt6.QtGui import QDesktopServices

from config import ConfigManager, NEWSPAPER_SOURCES
from downloader.worker import DownloadWorker
from downloader.base import DownloadResult
from .elegant_date_picker import ElegantDatePicker


# 和谐浅色主题 - 统一色系，柔和对度
THEME = {
    "bg_primary": "#f0f2f5",     # 主背景 - 浅灰（与卡片协调）
    "bg_card": "#ffffff",       # 卡片 - 纯白
    "bg_input": "#ffffff",       # 输入框 - 白，通过边框区分
    "bg_log": "#fafafa",        # 日志区 - 略深于白，区分层次
    "border": "#e1e4e8",        # 边框 - 柔和灰
    "border_light": "#eef0f2",  # 浅边框
    "accent": "#1890ff",        # 主色 - 柔和蓝
    "accent_hover": "#40a9ff",
    "text_primary": "#262626",   # 主文字 - 深灰非纯黑
    "text_secondary": "#595959",
    "text_muted": "#8c8c8c",
    "success": "#52c41a",
    "error": "#ff4d4f",
    "gradient_start": "#1890ff",
    "gradient_end": "#40a9ff",
}


def get_stylesheet() -> str:
    return f"""
        QMainWindow {{
            background-color: {THEME["bg_primary"]};
        }}
        QWidget#centralWidget {{
            background-color: {THEME["bg_primary"]};
            color: {THEME["text_primary"]};
        }}
        QWidget {{
            background: transparent;
            color: {THEME["text_primary"]};
        }}
        QGroupBox {{
            font-weight: 600;
            font-size: 13px;
            color: {THEME["text_primary"]};
            border: 1px solid {THEME["border"]};
            border-radius: 10px;
            margin-top: 18px;
            padding: 18px 14px 14px 14px;
            background-color: {THEME["bg_card"]};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 14px;
            top: 6px;
            padding: 2px 10px;
            color: {THEME["text_primary"]};
            background-color: {THEME["bg_card"]};
            border-radius: 4px;
            border-left: 3px solid {THEME["accent"]};
        }}
        QPushButton {{
            background-color: {THEME["accent"]};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 9px 18px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {THEME["accent_hover"]};
        }}
        QPushButton:pressed {{
            background-color: #096dd9;
        }}
        QPushButton:disabled {{
            background-color: #d9d9d9;
            color: #bfbfbf;
        }}
        QPushButton#secondary {{
            background-color: #fafafa;
            color: {THEME["text_primary"]};
            border: 1px solid {THEME["border"]};
        }}
        QPushButton#secondary:hover {{
            background-color: #f0f0f0;
            border-color: #d9d9d9;
            color: {THEME["accent"]};
        }}
        QPushButton#danger {{
            background-color: #fff1f0;
            color: {THEME["error"]};
            border: 1px solid #ffccc7;
        }}
        QPushButton#danger:hover {{
            background-color: #ffccc7;
            border-color: {THEME["error"]};
        }}
        QLineEdit {{
            background-color: {THEME["bg_input"]};
            color: {THEME["text_primary"]};
            border: 1px solid {THEME["border"]};
            border-radius: 6px;
            padding: 8px 12px;
            selection-background-color: {THEME["accent"]};
        }}
        QDateEdit {{
            background-color: {THEME["bg_input"]};
            color: {THEME["text_primary"]};
            border: 1px solid {THEME["border"]};
            border-radius: 6px;
            padding: 8px 12px 8px 12px;
            padding-right: 36px;
            selection-background-color: {THEME["accent"]};
        }}
        QLineEdit:focus {{
            border-color: {THEME["accent"]};
        }}
        QLineEdit:disabled {{
            color: {THEME["text_secondary"]};
            background-color: #fafafa;
        }}
        QDateEdit::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: center right;
            width: 24px;
            border-left: 1px solid {THEME["border"]};
            border-top-right-radius: 5px;
            border-bottom-right-radius: 5px;
            background-color: #f5f5f5;
        }}
        QDateEdit::drop-down:hover {{
            background-color: #e8e8e8;
        }}
        QCalendarWidget {{
            background-color: #ffffff;
            color: {THEME["text_primary"]};
        }}
        QCalendarWidget QToolButton {{
            background-color: #f5f5f5;
            color: {THEME["text_primary"]};
            border: 1px solid {THEME["border"]};
            border-radius: 4px;
            padding: 4px;
        }}
        QCalendarWidget QToolButton:hover {{
            background-color: #e8e8e8;
        }}
        QCalendarWidget QMenu {{
            background-color: #ffffff;
            color: {THEME["text_primary"]};
        }}
        QCalendarWidget QSpinBox {{
            background-color: #ffffff;
            color: {THEME["text_primary"]};
            border: 1px solid {THEME["border"]};
        }}
        QCalendarWidget QAbstractItemView {{
            background-color: #ffffff;
            color: {THEME["text_primary"]};
            selection-background-color: {THEME["accent"]};
            selection-color: white;
        }}
        QCalendarWidget QAbstractItemView:enabled {{
            color: {THEME["text_primary"]};
        }}
        QCalendarWidget QWidget#qt_calendar_navigationbar {{
            background-color: #fafafa;
            color: {THEME["text_primary"]};
        }}
        QCalendarWidget QLabel {{
            color: {THEME["text_primary"]};
        }}
        QProgressBar {{
            border: 1px solid {THEME["border"]};
            border-radius: 6px;
            text-align: center;
            background-color: #f5f5f5;
            color: {THEME["text_primary"]};
        }}
        QProgressBar::chunk {{
            background-color: {THEME["accent"]};
            border-radius: 5px;
        }}
        QTextEdit {{
            background-color: {THEME["bg_log"]};
            color: {THEME["text_secondary"]};
            border: 1px solid {THEME["border"]};
            border-radius: 6px;
            padding: 10px;
            font-family: 'Consolas', 'JetBrains Mono', monospace;
            font-size: 12px;
            selection-background-color: {THEME["accent"]};
        }}
        QCheckBox {{
            spacing: 10px;
            color: {THEME["text_primary"]};
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border-radius: 3px;
            border: 1px solid {THEME["border"]};
            background-color: {THEME["bg_card"]};
        }}
        QCheckBox::indicator:checked {{
            background-color: {THEME["accent"]};
            border-color: {THEME["accent"]};
        }}
        QCheckBox::indicator:hover {{
            border-color: {THEME["accent"]};
        }}
        QScrollBar:vertical {{
            background: #f5f5f5;
            width: 8px;
            border-radius: 4px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: #bfbfbf;
            border-radius: 4px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {THEME["accent"]};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
    """


class MainWindow(QMainWindow):
    """主窗口 - 科技感界面"""

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
        self.setMinimumSize(880, 680)
        w, h = self.config.window_size
        self.resize(max(w, 880), max(h, 680))
        self.setStyleSheet(get_stylesheet())

        central = QWidget()
        central.setObjectName("centralWidget")
        central.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(28, 28, 28, 28)

        # 顶部标题栏
        header = QLabel("报纸下载器")
        header.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {THEME["text_primary"]};
            letter-spacing: 2px;
        """)
        header_layout = QHBoxLayout()
        header_layout.addWidget(header)
        header_layout.addStretch()
        ver_label = QLabel("v1.0")
        ver_label.setStyleSheet(f"color: {THEME["text_muted"]}; font-size: 12px;")
        header_layout.addWidget(ver_label)
        main_layout.addLayout(header_layout)

        # 装饰线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {THEME['border_light']}; max-height: 1px;")
        main_layout.addWidget(line)

        # 内容区 - 两列布局
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # 左列：报纸选择 + 日期
        left_col = QVBoxLayout()
        left_col.setSpacing(16)

        # 报纸选择卡片
        paper_group = QGroupBox("报纸源")
        paper_layout = QVBoxLayout()
        btn_row = QHBoxLayout()
        for txt, obj, slot in [("全选", "selectAll", self._select_all_papers),
                                ("全不选", "deselectAll", self._deselect_all_papers)]:
            btn = QPushButton(txt)
            btn.setObjectName("secondary")
            btn.clicked.connect(slot)
            btn_row.addWidget(btn)
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
        left_col.addWidget(paper_group)

        # 日期选择卡片
        date_group = QGroupBox("日期")
        date_layout = QVBoxLayout()
        self.date_edit = ElegantDatePicker()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDateRange(
            QDate.currentDate().addYears(-1),
            QDate.currentDate(),
        )
        date_layout.addWidget(self.date_edit)
        date_group.setLayout(date_layout)
        left_col.addWidget(date_group)

        content_layout.addLayout(left_col, 1)

        # 右列：保存路径 + 控制 + 进度
        right_col = QVBoxLayout()
        right_col.setSpacing(16)

        # 保存目录
        save_group = QGroupBox("保存路径")
        save_layout = QVBoxLayout()
        save_row = QHBoxLayout()
        self.save_dir_edit = QLineEdit()
        self.save_dir_edit.setPlaceholderText("点击浏览选择目录...")
        self.save_dir_edit.setReadOnly(True)
        save_row.addWidget(self.save_dir_edit)
        browse_btn = QPushButton("浏览")
        browse_btn.setObjectName("secondary")
        browse_btn.clicked.connect(self._on_browse)
        open_btn = QPushButton("打开")
        open_btn.setObjectName("secondary")
        open_btn.clicked.connect(self._on_open_dir)
        save_row.addWidget(browse_btn)
        save_row.addWidget(open_btn)
        save_layout.addLayout(save_row)
        save_group.setLayout(save_layout)
        right_col.addWidget(save_group)

        # 下载控制
        ctrl_layout = QHBoxLayout()
        self.download_btn = QPushButton("开始下载")
        self.download_btn.setMinimumHeight(44)
        self.download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_btn.clicked.connect(self._on_start_download)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("danger")
        self.cancel_btn.setMinimumHeight(44)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.cancel_btn.setEnabled(False)
        ctrl_layout.addWidget(self.download_btn)
        ctrl_layout.addWidget(self.cancel_btn)
        ctrl_layout.addStretch()
        right_col.addLayout(ctrl_layout)

        # 进度与日志
        progress_group = QGroupBox("状态与日志")
        progress_layout = QVBoxLayout()
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet(f"color: {THEME['text_secondary']}; font-size: 13px;")
        progress_layout.addWidget(self.status_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        progress_layout.addWidget(self.progress_bar)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(200)
        self.log_text.setPlaceholderText("下载日志将在此显示...")
        progress_layout.addWidget(self.log_text)
        progress_group.setLayout(progress_layout)
        right_col.addWidget(progress_group, 1)

        content_layout.addLayout(right_col, 2)
        main_layout.addLayout(content_layout)

    def _load_config(self) -> None:
        self.save_dir_edit.setText(self.config.save_dir)
        self.date_edit.setDate(QDate.currentDate())
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
