# -*- coding: utf-8 -*-
"""
优雅日期选择器
青绿配色、输入框风格、简约现代
"""

from PyQt6.QtWidgets import (
    QWidget,
    QPushButton,
    QCalendarWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QTimer
from PyQt6.QtGui import QFont


class ElegantDatePicker(QFrame):
    """优雅日期选择 - 输入框风格 + 青绿配色"""

    dateChanged = pyqtSignal(QDate)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("elegantDatePicker")
        self._date = QDate.currentDate()
        self._min_date = QDate.currentDate().addYears(-1)
        self._max_date = QDate.currentDate()
        self._setup_ui()
        self._update_display()
        self.setStyleSheet(self._get_style())
        self.setMinimumWidth(160)
        self.setMinimumHeight(56)

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 10, 10)
        layout.setSpacing(8)

        self._date_label = QLabel()
        self._date_label.setObjectName("dateLabel")
        font = QFont()
        font.setPointSize(11)
        self._date_label.setFont(font)
        layout.addWidget(self._date_label, 1)

        self._btn = QPushButton("📅 日历")
        self._btn.setObjectName("calendarBtn")
        self._btn.setToolTip("点击选择日期")
        self._btn.setFixedSize(100, 48)
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn.clicked.connect(self._on_btn_clicked)
        layout.addWidget(self._btn)

    def _get_style(self) -> str:
        return """
            ElegantDatePicker#elegantDatePicker {
                background-color: #ffffff;
                border: 1px solid #d1d5db;
                border-radius: 10px;
            }
            ElegantDatePicker#elegantDatePicker:hover {
                border-color: #0d9488;
            }
            ElegantDatePicker#elegantDatePicker QLabel#dateLabel {
                color: #1f2937;
                background: transparent;
            }
            ElegantDatePicker#elegantDatePicker QPushButton#calendarBtn {
                background-color: #f0fdfa;
                color: #0d9488;
                border: 1px solid #99f6e4;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
            }
            ElegantDatePicker#elegantDatePicker QPushButton#calendarBtn:hover {
                background-color: #ccfbf1;
                border-color: #0d9488;
            }
            ElegantDatePicker#elegantDatePicker QPushButton#calendarBtn:pressed {
                background-color: #99f6e4;
            }
        """

    def _get_calendar_style(self) -> str:
        return """
            QCalendarWidget {
                background-color: #ffffff;
                border-radius: 12px;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0d9488, stop:1 #0f766e);
                min-height: 44px;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
            QCalendarWidget QToolButton {
                background: transparent;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QCalendarWidget QToolButton:hover {
                background: rgba(255,255,255,0.25);
            }
            QCalendarWidget QToolButton::menu-indicator { image: none; width: 0; }
            QCalendarWidget QSpinBox {
                background: transparent;
                color: white;
                border: none;
                font-weight: 600;
                font-size: 15px;
            }
            QCalendarWidget QAbstractItemView {
                background-color: #fafafa;
                color: #374151;
                selection-background-color: #0d9488;
                selection-color: white;
                border: none;
                gridline-color: #e5e7eb;
            }
            QCalendarWidget QAbstractItemView::item:hover {
                background-color: #ecfdf5;
            }
            QCalendarWidget QMenu {
                background-color: #ffffff;
                color: #374151;
            }
        """

    def _on_btn_clicked(self) -> None:
        QTimer.singleShot(60, self._show_calendar)

    def _show_calendar(self) -> None:
        popup = QFrame(self.window())
        popup.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        popup.setStyleSheet("QFrame { background: transparent; }")

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
            }
        """)

        cal = QCalendarWidget()
        cal.setSelectedDate(self._date)
        cal.setMinimumDate(self._min_date)
        cal.setMaximumDate(self._max_date)
        cal.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        cal.setStyleSheet(self._get_calendar_style())
        cal.setMinimumWidth(300)
        cal.setMinimumHeight(280)
        cal.setGridVisible(True)
        cal.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        cal.activated.connect(lambda d: self._on_date_selected(d, popup))
        cal.clicked.connect(lambda d: self._on_date_selected(d, popup))

        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(cal)

        main_layout = QVBoxLayout(popup)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

        popup.adjustSize()
        global_pos = self.mapToGlobal(self.rect().bottomLeft())
        popup.move(global_pos.x(), global_pos.y() + 6)
        popup.show()
        QTimer.singleShot(0, cal.setFocus)

    def _on_date_selected(self, date: QDate, popup: QFrame) -> None:
        self._date = date
        self._update_display()
        self.dateChanged.emit(date)
        popup.close()

    def _update_display(self) -> None:
        self._date_label.setText(self._date.toString("yyyy-MM-dd"))

    def setDateRange(self, min_date: QDate, max_date: QDate) -> None:
        self._min_date = min_date
        self._max_date = max_date

    def date(self) -> QDate:
        return self._date

    def setDate(self, date: QDate) -> None:
        self._date = date
        self._update_display()
