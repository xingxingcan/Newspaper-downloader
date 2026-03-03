# -*- coding: utf-8 -*-
"""
炫酷日期选择器
渐变配色 + 圆角 + 现代风格的日历弹窗
"""

from PyQt6.QtWidgets import (
    QPushButton,
    QCalendarWidget,
    QVBoxLayout,
    QFrame,
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QTimer


class CoolDatePicker(QPushButton):
    """炫酷日期选择按钮，点击弹出日历"""

    dateChanged = pyqtSignal(QDate)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("coolDatePicker")
        self._date = QDate.currentDate()
        self._min_date = QDate.currentDate().addYears(-1)
        self._max_date = QDate.currentDate()
        self._update_text()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(160)
        self.setMinimumHeight(38)
        self.setStyleSheet(self._get_button_style())
        self.clicked.connect(self._show_calendar)

    def setDateRange(self, min_date: QDate, max_date: QDate) -> None:
        self._min_date = min_date
        self._max_date = max_date

    def _update_text(self) -> None:
        self.setText("📅  " + self._date.toString("yyyy-MM-dd"))

    def _get_button_style(self) -> str:
        return """
            QPushButton#coolDatePicker {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton#coolDatePicker:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a67d8, stop:1 #6b46c1);
            }}
            QPushButton#coolDatePicker:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4c51bf, stop:1 #553c9a);
            }}
        """

    def _get_calendar_style(self) -> str:
        return """
            QCalendarWidget {
                background-color: #ffffff;
                border-radius: 12px;
                font-family: "Microsoft YaHei", sans-serif;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                min-height: 40px;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
            QCalendarWidget QToolButton {
                background: transparent;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px;
                font-size: 14px;
            }
            QCalendarWidget QToolButton:hover {
                background: rgba(255,255,255,0.2);
            }
            QCalendarWidget QToolButton::menu-indicator {
                image: none;
                width: 0;
            }
            QCalendarWidget QSpinBox {
                background: transparent;
                color: white;
                border: none;
                font-weight: 600;
                font-size: 14px;
            }
            QCalendarWidget QWidget {
                alternate-background-color: #f8f9fa;
            }
            QCalendarWidget QAbstractItemView {
                background-color: #ffffff;
                color: #2d3748;
                selection-background-color: #667eea;
                selection-color: white;
                border: none;
                outline: none;
                gridline-color: #e2e8f0;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #2d3748;
            }
            QCalendarWidget QAbstractItemView::item:hover {
                background-color: #edf2f7;
            }
            QCalendarWidget QMenu {
                background-color: #ffffff;
                color: #2d3748;
            }
        """

    def _show_calendar(self) -> None:
        popup = QFrame(self.window())
        popup.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        popup.setStyleSheet("""
            QFrame { background: transparent; }
        """)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
            }
        """)

        cal = QCalendarWidget()
        cal.setSelectedDate(self._date)
        cal.setMinimumDate(self._min_date)
        cal.setMaximumDate(self._max_date)
        cal.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        cal.setStyleSheet(self._get_calendar_style())
        cal.setMinimumWidth(320)
        cal.setMinimumHeight(300)
        cal.setGridVisible(True)
        cal.activated.connect(lambda d: self._on_date_selected(d, popup))
        cal.clicked.connect(lambda d: self._on_date_selected(d, popup))

        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(cal)

        main_layout = QVBoxLayout(popup)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.addWidget(container)

        popup.adjustSize()
        global_pos = self.mapToGlobal(self.rect().bottomLeft())
        popup.move(global_pos.x(), global_pos.y() + 4)
        popup.show()

    def _on_date_selected(self, date: QDate, popup: QFrame) -> None:
        self._date = date
        self._update_text()
        self.dateChanged.emit(date)
        popup.close()

    def date(self) -> QDate:
        return self._date

    def setDate(self, date: QDate) -> None:
        self._date = date
        self._update_text()
