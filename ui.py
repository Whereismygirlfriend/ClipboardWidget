import os
import shutil
import json
import uuid
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLayout,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListView,
    QDialog,
    QLabel,
    QScrollArea,
    QStyledItemDelegate,
    QStyle,
    QStyleOptionButton,
    QFileDialog,
    QMessageBox,
    QFrame,
    QSizePolicy,
    QComboBox,
    QLineEdit,
    QPlainTextEdit,
    QMenu,
    QSystemTrayIcon,
    QColorDialog,
    QDialogButtonBox,
    QFormLayout,
    QKeySequenceEdit,
)
from PyQt6.QtCore import (
    Qt,
    QAbstractListModel,
    QModelIndex,
    QSize,
    QRect,
    QEvent,
    QPoint,
    QUrl,
    QTimer,
)
from PyQt6.QtGui import (
    QPixmap,
    QColor,
    QCloseEvent,
    QShortcut,
    QKeySequence,
    QDesktopServices,
    QAction,
)
from settings import SettingsManager, DEFAULT_CUSTOM_THEME, DEFAULT_SHORTCUTS
from utils import timestamp_to_filename_fragment


DARK_STYLESHEET = """
QWidget {
    background-color: #161a20;
    color: #e7edf5;
    font-family: "Segoe UI", "Malgun Gothic";
    font-size: 12px;
}
QFrame#TopHeader {
    background: qlineargradient(
        x1:0,
        y1:0,
        x2:1,
        y2:1,
        stop:0 #242b36,
        stop:1 #1b2028
    );
    border: 1px solid #394252;
    border-radius: 12px;
}
QFrame#ControlPanel {
    background-color: #1a2029;
    border: 1px solid #313b4d;
    border-radius: 12px;
}
QFrame#SectionCard {
    background-color: #202836;
    border: 1px solid #354158;
    border-radius: 10px;
}
QLabel#HeaderTitle {
    font-size: 14px;
    font-weight: 700;
    color: #f5f8fc;
    background-color: transparent;
}
QLabel#HeaderSubTitle {
    font-size: 10px;
    color: #8f98a8;
    background-color: transparent;
}
QLabel#SectionTitle {
    color: #b6c3d8;
    font-size: 11px;
    font-weight: 600;
    background-color: transparent;
}
QLabel#PathLabel {
    color: #a8b3c2;
    background-color: transparent;
}
QPushButton {
    background-color: #2a3448;
    border: 1px solid #4c5c79;
    border-radius: 9px;
    padding: 6px 11px;
    color: #e7edf5;
}
QPushButton:hover {
    background-color: #354663;
}
QPushButton:pressed {
    background-color: #28374f;
}
QPushButton:checked {
    background-color: #2f7de1;
    border-color: #2f7de1;
    color: #ffffff;
}
QPushButton#PrimaryAction {
    background-color: #2f7de1;
    border-color: #2f7de1;
    color: #ffffff;
}
QPushButton#PrimaryAction:hover {
    background-color: #3a89eb;
}
QComboBox,
QLineEdit {
    background-color: #121821;
    border: 1px solid #43506a;
    border-radius: 8px;
    padding: 6px 10px;
    color: #e7edf5;
}
QComboBox {
    padding-right: 28px;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border: none;
}
QComboBox::down-arrow {
    image: none;
    width: 0px;
    height: 0px;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #9fb3cf;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #111823;
    color: #e7edf5;
    border: 1px solid #41516e;
    selection-background-color: #2b4468;
}
QListView {
    background-color: #11151b;
    border: 1px solid #323b4a;
    border-radius: 12px;
    padding: 8px;
    outline: none;
}
QScrollBar:vertical {
    background: #1b2027;
    width: 11px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #56657b;
    min-height: 24px;
    border-radius: 5px;
}
QStatusBar {
    background-color: #11151b;
    border-top: 1px solid #2b3442;
    color: #aeb9c7;
}
"""

LIGHT_STYLESHEET = """
QWidget {
    background-color: #f1f4f9;
    color: #1d2633;
    font-family: "Segoe UI", "Malgun Gothic";
    font-size: 12px;
}
QFrame#TopHeader {
    background: qlineargradient(
        x1:0,
        y1:0,
        x2:1,
        y2:1,
        stop:0 #f9fbff,
        stop:1 #e8edf6
    );
    border: 1px solid #c9d4e3;
    border-radius: 12px;
}
QFrame#ControlPanel {
    background-color: #f7faff;
    border: 1px solid #d6e0ee;
    border-radius: 12px;
}
QFrame#SectionCard {
    background-color: #ffffff;
    border: 1px solid #d8e2ef;
    border-radius: 10px;
}
QLabel#HeaderTitle {
    font-size: 14px;
    font-weight: 700;
    color: #1f2a3a;
    background-color: transparent;
}
QLabel#HeaderSubTitle {
    font-size: 10px;
    color: #8f98a8;
    background-color: transparent;
}
QLabel#SectionTitle {
    color: #607086;
    font-size: 11px;
    font-weight: 600;
    background-color: transparent;
}
QLabel#PathLabel {
    color: #5e6f84;
    background-color: transparent;
}
QPushButton {
    background-color: #ffffff;
    border: 1px solid #d0d9e7;
    border-radius: 9px;
    padding: 6px 11px;
    color: #213044;
}
QPushButton:hover {
    background-color: #f0f6ff;
}
QPushButton:pressed {
    background-color: #e7f0ff;
}
QPushButton:checked {
    background-color: #1371de;
    border-color: #1371de;
    color: #ffffff;
}
QPushButton#PrimaryAction {
    background-color: #1371de;
    border-color: #1371de;
    color: #ffffff;
}
QPushButton#PrimaryAction:hover {
    background-color: #1b7cf0;
}
QComboBox,
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #cfdae9;
    border-radius: 8px;
    padding: 6px 10px;
    color: #1d2633;
}
QComboBox {
    padding-right: 28px;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border: none;
}
QComboBox::down-arrow {
    image: none;
    width: 0px;
    height: 0px;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #4e627b;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #1d2633;
    border: 1px solid #cfdae9;
    selection-background-color: #d9e8ff;
}
QListView {
    background-color: #ffffff;
    border: 1px solid #c9d4e3;
    border-radius: 12px;
    padding: 8px;
    outline: none;
}
QScrollBar:vertical {
    background: #e9eef6;
    width: 11px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #b8c7da;
    min-height: 24px;
    border-radius: 5px;
}
QStatusBar {
    background-color: #f8fbff;
    border-top: 1px solid #d5dfed;
    color: #5e6f84;
}
"""


def build_custom_stylesheet(palette):
    p = dict(DEFAULT_CUSTOM_THEME)
    p.update(palette or {})
    return f"""
QWidget {{
    background-color: {p['window_bg']};
    color: {p['text']};
    font-family: "Segoe UI", "Malgun Gothic";
    font-size: 12px;
}}
QFrame#TopHeader {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 {p['card_bg']}, stop:1 {p['surface_bg']}
    );
    border: 1px solid {p['border']};
    border-radius: 12px;
}}
QFrame#ControlPanel {{
    background-color: {p['surface_bg']};
    border: 1px solid {p['border']};
    border-radius: 12px;
}}
QFrame#SectionCard {{
    background-color: {p['card_bg']};
    border: 1px solid {p['border']};
    border-radius: 10px;
}}
QLabel#HeaderTitle {{
    font-size: 14px;
    font-weight: 700;
    color: {p['text']};
    background-color: transparent;
}}
QLabel#HeaderSubTitle {{
    font-size: 10px;
    color: #8f98a8;
    background-color: transparent;
}}
QLabel#SectionTitle {{
    color: {p['muted_text']};
    font-size: 11px;
    font-weight: 600;
    background-color: transparent;
}}
QLabel#PathLabel {{
    color: {p['muted_text']};
    background-color: transparent;
}}
QPushButton {{
    background-color: {p['button_bg']};
    border: 1px solid {p['border']};
    border-radius: 9px;
    padding: 6px 11px;
    color: {p['text']};
}}
QPushButton:hover {{
    background-color: {p['button_hover']};
}}
QPushButton:checked {{
    background-color: {p['accent']};
    border-color: {p['accent']};
    color: #ffffff;
}}
QPushButton#PrimaryAction {{
    background-color: {p['accent']};
    border-color: {p['accent']};
    color: #ffffff;
}}
QPushButton#PrimaryAction:hover {{
    background-color: {p['accent_hover']};
}}
QComboBox,
QLineEdit,
QPlainTextEdit {{
    background-color: {p['input_bg']};
    border: 1px solid {p['border']};
    border-radius: 8px;
    padding: 6px 10px;
    color: {p['text']};
}}
QComboBox {{
    padding-right: 28px;
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border: none;
}}
QComboBox::down-arrow {{
    image: none;
    width: 0px;
    height: 0px;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {p['arrow']};
    margin-right: 6px;
}}
QComboBox QAbstractItemView {{
    background-color: {p['input_bg']};
    color: {p['text']};
    border: 1px solid {p['border']};
    selection-background-color: {p['selection_bg']};
}}
QListView {{
    background-color: {p['list_bg']};
    border: 1px solid {p['border']};
    border-radius: 12px;
    padding: 8px;
    outline: none;
}}
QStatusBar {{
    background-color: {p['list_bg']};
    border-top: 1px solid {p['border']};
    color: {p['muted_text']};
}}
"""


class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, h_spacing=6, v_spacing=6):
        super().__init__(parent)
        self._items = []
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect, test_only):
        margins = self.contentsMargins()
        effective = rect.adjusted(
            margins.left(),
            margins.top(),
            -margins.right(),
            -margins.bottom(),
        )
        x = effective.x()
        y = effective.y()
        line_height = 0

        for item in self._items:
            item_size = item.sizeHint()
            next_x = x + item_size.width() + self._h_spacing
            if line_height > 0 and next_x - self._h_spacing > effective.right() + 1:
                x = effective.x()
                y = y + line_height + self._v_spacing
                next_x = x + item_size.width() + self._h_spacing
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item_size))

            x = next_x
            line_height = max(line_height, item_size.height())

        return (y + line_height) - rect.y() + margins.bottom()


class ThumbnailCache:
    def __init__(self, max_size=100, thumb_size=(80, 80)):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.thumb_size = QSize(*thumb_size)

    def get_thumbnail(self, path):
        if path in self.cache:
            self.cache.move_to_end(path)
            return self.cache[path]
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            thumbnail = pixmap.scaled(
                self.thumb_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.cache[path] = thumbnail
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)
            return thumbnail
        return None

    def invalidate_path(self, path):
        self.cache.pop(path, None)


class ClipboardDataModel(QAbstractListModel):
    IdRole, TypeRole, ContentRole, TimestampRole, DuplicateRole, CheckedRole = range(
        Qt.ItemDataRole.UserRole + 1, Qt.ItemDataRole.UserRole + 7
    )

    def __init__(self, db_manager, page_size=200, max_cached_rows=1000, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.page_size = page_size
        self.max_cached_rows = max_cached_rows
        self.type_filter = "all"
        self.duplicate_filter = "all"
        self.search_keyword = ""
        self.items = []
        self.checked_items = set()
        self.total_count = 0
        self.reload()

    def reload(self):
        self.beginResetModel()
        self.total_count = self.db.count_clips(
            type_filter=self.type_filter,
            duplicate_filter=self.duplicate_filter,
            search_keyword=self.search_keyword,
        )
        self.items = self.db.get_clips(
            self.page_size,
            0,
            type_filter=self.type_filter,
            duplicate_filter=self.duplicate_filter,
            search_keyword=self.search_keyword,
        )
        self.checked_items.clear()
        self.endResetModel()

    def set_filters(self, type_filter="all", duplicate_filter="all", search_keyword=""):
        self.type_filter = type_filter
        self.duplicate_filter = duplicate_filter
        self.search_keyword = str(search_keyword or "").strip()
        self.reload()

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self.items)

    def canFetchMore(self, parent=QModelIndex()):
        if parent.isValid():
            return False
        return len(self.items) < self.total_count

    def fetchMore(self, parent=QModelIndex()):
        if parent.isValid():
            return
        current_count = len(self.items)
        remaining = self.total_count - current_count
        fetch_count = min(self.page_size, remaining)
        if fetch_count <= 0:
            return
        new_items = self.db.get_clips(
            fetch_count,
            current_count,
            type_filter=self.type_filter,
            duplicate_filter=self.duplicate_filter,
            search_keyword=self.search_keyword,
        )
        if not new_items:
            return
        self.beginInsertRows(
            QModelIndex(),
            current_count,
            current_count + len(new_items) - 1,
        )
        self.items.extend(new_items)
        self.endInsertRows()
        self._trim_cached_tail()

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None
        item = self.items[index.row()]
        if role == self.IdRole:
            return item["id"]
        if role == self.TypeRole:
            return item["type"]
        if role == self.ContentRole:
            return item["content"]
        if role == self.TimestampRole:
            return item["timestamp"]
        if role == self.DuplicateRole:
            return item["is_duplicate"]
        if role == self.CheckedRole:
            return item["id"] in self.checked_items
        if role == Qt.ItemDataRole.DisplayRole:
            dup_mark = "[중복] " if item["is_duplicate"] else ""
            if item["type"] == "text":
                return f"{dup_mark}{item['content'][:50].replace(chr(10), ' ')}"
            if item["type"] == "image":
                return f"{dup_mark}[이미지] {item['timestamp']}"
            if item["type"] == "file":
                paths = [line.strip() for line in str(item["content"]).splitlines() if line.strip()]
                if not paths:
                    return f"{dup_mark}[파일] 경로 없음"
                first_name = os.path.basename(paths[0]) or paths[0]
                extra_count = len(paths) - 1
                suffix = f" 외 {extra_count}개" if extra_count > 0 else ""
                return f"{dup_mark}[파일] {first_name}{suffix}"
            return f"{dup_mark}[기타] {item['timestamp']}"
        if role == Qt.ItemDataRole.CheckStateRole:
            if item["id"] in self.checked_items:
                return Qt.CheckState.Checked
            return Qt.CheckState.Unchecked
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return False
        if role != Qt.ItemDataRole.CheckStateRole:
            return False
        item_id = self.items[index.row()]["id"]
        is_checked = value in (Qt.CheckState.Checked, Qt.CheckState.Checked.value, 2)
        if is_checked:
            self.checked_items.add(item_id)
        else:
            self.checked_items.discard(item_id)
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.CheckStateRole])
        return True

    def flags(self, index):
        flags = super().flags(index)
        if index.isValid():
            return flags | Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def prepend_item(self, item):
        if not item or "id" not in item:
            return
        if not self.item_matches_filters(item):
            return
        if self.items and self.items[0]["id"] == item["id"]:
            return
        self.total_count += 1
        self.beginInsertRows(QModelIndex(), 0, 0)
        self.items.insert(0, item)
        self.endInsertRows()
        self._trim_cached_tail()

    def _trim_cached_tail(self):
        if self.max_cached_rows <= 0:
            return
        excess = len(self.items) - self.max_cached_rows
        if excess <= 0:
            return
        first_remove = len(self.items) - excess
        last_remove = len(self.items) - 1
        removed_ids = [item["id"] for item in self.items[first_remove:]]
        self.beginRemoveRows(QModelIndex(), first_remove, last_remove)
        del self.items[first_remove:]
        self.endRemoveRows()
        for item_id in removed_ids:
            self.checked_items.discard(item_id)

    def get_checked_ids(self):
        return list(self.checked_items)

    def set_all_checked(self, checked=True, include_unloaded=True):
        if include_unloaded:
            target_ids = set(
                self.db.get_clip_ids(
                    type_filter=self.type_filter,
                    duplicate_filter=self.duplicate_filter,
                    search_keyword=self.search_keyword,
                )
            )
        else:
            target_ids = {item["id"] for item in self.items}

        if not target_ids:
            return 0

        if checked:
            self.checked_items.update(target_ids)
        else:
            self.checked_items.difference_update(target_ids)

        if self.items:
            top_left = self.index(0, 0)
            bottom_right = self.index(len(self.items) - 1, 0)
            self.dataChanged.emit(
                top_left,
                bottom_right,
                [Qt.ItemDataRole.CheckStateRole, self.CheckedRole],
            )
        return len(self.checked_items)

    def checked_count(self):
        return len(self.checked_items)

    def item_matches_filters(self, item):
        if self.type_filter in ("text", "image", "file") and item.get("type") != self.type_filter:
            return False

        if self.duplicate_filter == "only" and int(item.get("is_duplicate", 0)) != 1:
            return False
        if self.duplicate_filter == "exclude" and int(item.get("is_duplicate", 0)) == 1:
            return False

        keyword = self.search_keyword
        if keyword and keyword.lower() not in str(item.get("content", "")).lower():
            return False
        return True


class ClipboardDelegate(QStyledItemDelegate):
    def __init__(self, cache_manager, parent=None):
        super().__init__(parent)
        self.cache = cache_manager
        self.row_height = 100
        self.selected_bg_color = QColor("#2f3d57")
        self.selected_text_color = QColor("#f1f3f5")

    def set_selection_colors(self, background_hex, text_hex):
        self.selected_bg_color = QColor(background_hex)
        self.selected_text_color = QColor(text_hex)

    def _checkbox_rect(self, row_rect):
        return QRect(row_rect.left() + 12, row_rect.center().y() - 8, 16, 16)

    def paint(self, painter, option, index):
        painter.save()
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, self.selected_bg_color)
        rect = option.rect
        c_type = index.data(Qt.ItemDataRole.UserRole + 2)
        content = index.data(Qt.ItemDataRole.UserRole + 3)
        thumb_rect = QRect(rect.left() + 42, rect.top() + 10, 80, 80)

        checkbox_option = QStyleOptionButton()
        checkbox_option.rect = self._checkbox_rect(rect)
        checkbox_option.state = QStyle.StateFlag.State_Enabled
        check_state = index.data(Qt.ItemDataRole.CheckStateRole)
        if check_state == Qt.CheckState.Checked:
            checkbox_option.state |= QStyle.StateFlag.State_On
        else:
            checkbox_option.state |= QStyle.StateFlag.State_Off
        style = option.widget.style() if option.widget else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_CheckBox, checkbox_option, painter)

        if c_type == "image":
            pixmap = self.cache.get_thumbnail(content)
            if pixmap:
                target_rect = QStyle.alignedRect(
                    Qt.LayoutDirection.LeftToRight,
                    Qt.AlignmentFlag.AlignCenter,
                    pixmap.size(),
                    thumb_rect,
                )
                painter.drawPixmap(target_rect, pixmap)
        elif c_type == "file":
            painter.setPen(QColor("#6b7f99"))
            painter.drawRect(thumb_rect)
            painter.drawText(thumb_rect, Qt.AlignmentFlag.AlignCenter, "FILE")
        else:
            painter.setPen(QColor("#888888"))
            painter.drawRect(thumb_rect)
            painter.drawText(thumb_rect, Qt.AlignmentFlag.AlignCenter, "텍스트")

        text_rect = QRect(
            thumb_rect.right() + 20,
            rect.top(),
            rect.width() - 150,
            rect.height(),
        )
        if option.state & QStyle.StateFlag.State_Selected:
            painter.setPen(self.selected_text_color)
        else:
            painter.setPen(option.palette.text().color())
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignVCenter,
            index.data(Qt.ItemDataRole.DisplayRole),
        )
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), self.row_height)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonRelease:
            if self._checkbox_rect(option.rect).contains(event.pos()):
                current_state = index.data(Qt.ItemDataRole.CheckStateRole)
                next_state = (
                    Qt.CheckState.Unchecked
                    if current_state == Qt.CheckState.Checked
                    else Qt.CheckState.Checked
                )
                return model.setData(index, next_state, Qt.ItemDataRole.CheckStateRole)
        return super().editorEvent(event, model, option, index)


class ImageViewerDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("원본 이미지 보기")
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            image_label.setPixmap(pixmap)
            image_label.resize(pixmap.width(), pixmap.height())
        else:
            image_label.setText("이미지를 불러오지 못했습니다.")
        scroll_area.setWidget(image_label)
        layout.addWidget(scroll_area)


class TextViewerDialog(QDialog):
    def __init__(self, text_content, timestamp="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("텍스트 상세 보기")
        self.resize(700, 480)
        layout = QVBoxLayout(self)
        if timestamp:
            header = QLabel(f"복사 시각: {timestamp}")
            header.setObjectName("PathLabel")
            layout.addWidget(header)
        editor = QPlainTextEdit()
        editor.setReadOnly(True)
        editor.setPlainText(str(text_content or ""))
        layout.addWidget(editor)


class FileViewerDialog(QDialog):
    def __init__(self, file_text, timestamp="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("파일 상세 보기")
        self.resize(720, 460)
        self.file_paths = [line.strip() for line in str(file_text or "").splitlines() if line.strip()]
        layout = QVBoxLayout(self)
        if timestamp:
            header = QLabel(f"복사 시각: {timestamp}")
            header.setObjectName("PathLabel")
            layout.addWidget(header)
        editor = QPlainTextEdit()
        editor.setReadOnly(True)
        editor.setPlainText("\n".join(self.file_paths) if self.file_paths else "(파일 경로 없음)")
        layout.addWidget(editor)

        action_row = QHBoxLayout()
        btn_open = QPushButton("📂 위치 열기")
        btn_copy = QPushButton("📋 경로 복사")
        btn_close = QPushButton("닫기")
        action_row.addWidget(btn_open)
        action_row.addWidget(btn_copy)
        action_row.addStretch(1)
        action_row.addWidget(btn_close)
        layout.addLayout(action_row)

        btn_open.clicked.connect(self.open_in_explorer)
        btn_copy.clicked.connect(self.copy_paths)
        btn_close.clicked.connect(self.accept)

    def open_in_explorer(self):
        if not self.file_paths:
            return
        target = self.file_paths[0]
        open_target = target if os.path.isdir(target) else os.path.dirname(target)
        if open_target:
            QDesktopServices.openUrl(QUrl.fromLocalFile(open_target))

    def copy_paths(self):
        QApplication.clipboard().setText("\n".join(self.file_paths))


class CustomThemeDialog(QDialog):
    COLOR_FIELDS = [
        ("window_bg", "배경"),
        ("surface_bg", "패널"),
        ("card_bg", "카드"),
        ("border", "테두리"),
        ("text", "기본 텍스트"),
        ("muted_text", "보조 텍스트"),
        ("button_bg", "버튼 배경"),
        ("button_hover", "버튼 Hover"),
        ("input_bg", "입력 영역"),
        ("list_bg", "리스트 배경"),
        ("accent", "강조 색상"),
        ("accent_hover", "강조 Hover"),
        ("arrow", "콤보 화살표"),
        ("selection_bg", "선택 배경"),
    ]

    def __init__(self, initial_palette, parent=None):
        super().__init__(parent)
        self.setWindowTitle("사용자 테마 편집")
        self.resize(420, 560)
        self.palette_values = dict(DEFAULT_CUSTOM_THEME)
        self.palette_values.update(initial_palette or {})
        self.color_buttons = {}

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        for key, label in self.COLOR_FIELDS:
            btn = QPushButton("")
            btn.clicked.connect(lambda _, k=key: self.pick_color(k))
            self.color_buttons[key] = btn
            self._apply_color_button(key)
            form.addRow(label, btn)

        layout.addLayout(form)
        footer_row = QHBoxLayout()
        btn_reset = QPushButton("기본값 복원")
        footer_row.addWidget(btn_reset)
        footer_row.addStretch(1)
        layout.addLayout(footer_row)
        btn_reset.clicked.connect(self.reset_palette)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _apply_color_button(self, key):
        color = self.palette_values[key]
        btn = self.color_buttons[key]
        btn.setText(color)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {color}; color: #ffffff; border: 1px solid #667085; }}"
        )

    def pick_color(self, key):
        current = QColor(self.palette_values[key])
        selected = QColorDialog.getColor(current, self, "색상 선택")
        if not selected.isValid():
            return
        self.palette_values[key] = selected.name()
        self._apply_color_button(key)

    def reset_palette(self):
        self.palette_values = dict(DEFAULT_CUSTOM_THEME)
        for key in self.color_buttons:
            self._apply_color_button(key)

    def get_palette(self):
        return dict(self.palette_values)


class ShortcutDialog(QDialog):
    FIELD_META = [
        ("toggle_panel", "도구 패널 열기/닫기"),
        ("refresh", "새로고침"),
        ("select_all", "전체 선택/해제"),
        ("delete_checked", "체크 삭제"),
        ("toggle_theme", "테마 순환"),
        ("export_markdown", "MD 내보내기"),
    ]

    def __init__(self, current_mapping, parent=None):
        super().__init__(parent)
        self.setWindowTitle("단축키 설정")
        self.resize(420, 320)
        self.mapping = dict(DEFAULT_SHORTCUTS)
        self.mapping.update(current_mapping or {})
        self.editors = {}

        layout = QVBoxLayout(self)
        form = QFormLayout()
        for key, label in self.FIELD_META:
            editor = QKeySequenceEdit(QKeySequence(self.mapping.get(key, "")))
            self.editors[key] = editor
            form.addRow(label, editor)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        values = self.get_mapping()
        normalized = [seq for seq in values.values() if seq]
        if len(normalized) != len(set(normalized)):
            QMessageBox.warning(self, "중복 단축키", "동일한 단축키가 중복 지정되어 있습니다.")
            return
        self.accept()

    def get_mapping(self):
        data = {}
        for key, _ in self.FIELD_META:
            data[key] = self.editors[key].keySequence().toString()
        return data


class MainWindow(QMainWindow):
    TYPE_FILTER_MAP = {
        "전체": "all",
        "텍스트": "text",
        "이미지": "image",
        "파일": "file",
    }
    DUPLICATE_FILTER_MAP = {
        "전체": "all",
        "중복만": "only",
        "중복 제외": "exclude",
    }

    def __init__(self, db_manager, export_manager, monitor, settings_manager=None):
        super().__init__()
        self.setWindowTitle("클립보드 위젯")
        self.resize(520, 640)
        self.setMinimumSize(340, 420)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, True)
        self.db = db_manager
        self.export_manager = export_manager
        self.monitor = monitor
        self.settings = settings_manager or SettingsManager(self.monitor.base_dir)
        self.theme_mode = self.settings.get_theme_mode()
        self.custom_theme_palette = self.settings.get_custom_theme()
        self.shortcut_mapping = self.settings.get_shortcuts()
        self.background_mode_enabled = self.settings.get_background_mode()
        self.force_quit = False
        self._cleanup_done = False
        self._tray_notified_hidden = False
        self.tray_icon = None
        self.shortcuts = {}
        self.realtime_save_enabled = self.settings.get_realtime_save_enabled()
        self.realtime_save_dir = self.settings.get_realtime_save_dir()
        self._sync_timer = QTimer(self)
        self._sync_timer.setInterval(1500)
        self._sync_timer.timeout.connect(self._sync_model_count_with_db)
        self._auto_sync_running = False
        self.realtime_save_executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="realtime_save",
        )

        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(12, 12, 12, 8)
        layout.setSpacing(10)
        self._build_toolbar(layout)
        self._setup_system_tray()
        if self.background_mode_enabled and self.tray_icon is None:
            self.background_mode_enabled = False
            self.settings.set_background_mode(False)
        self._sync_realtime_controls_from_settings()

        self.list_view = QListView()
        self.list_view.setUniformItemSizes(True)
        self.list_view.setSpacing(6)
        self.cache_manager = ThumbnailCache()
        self.model = ClipboardDataModel(self.db)
        self.delegate = ClipboardDelegate(self.cache_manager)
        self.list_view.setModel(self.model)
        self.list_view.setItemDelegate(self.delegate)
        self.list_view.doubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.list_view, 1)
        self.setCentralWidget(main_widget)

        self.btn_widget_mode.toggled.connect(self.set_widget_mode)
        self.btn_toolbar_toggle.clicked.connect(lambda: self.toggle_toolbar_visibility())
        self.btn_theme_mode.clicked.connect(self.toggle_theme)
        self.btn_theme_custom.clicked.connect(self.open_custom_theme_dialog)
        self.btn_shortcuts.clicked.connect(self.open_shortcut_dialog)
        self.btn_background_mode.toggled.connect(self.set_background_mode)
        self.btn_realtime_mode.toggled.connect(self.toggle_realtime_save)
        self.btn_realtime_folder.clicked.connect(self.choose_realtime_folder)
        self.btn_refresh.clicked.connect(self.model.reload)
        self.btn_select_all.clicked.connect(self.toggle_select_all)
        self.btn_delete.clicked.connect(self.delete_checked_items)
        self.btn_import_json.clicked.connect(self.import_json_file)
        self.btn_filter_apply.clicked.connect(self.apply_filters)
        self.btn_filter_clear.clicked.connect(self.clear_filters)
        self.input_search.returnPressed.connect(self.apply_filters)
        self.btn_export_txt.clicked.connect(self.export_txt)
        self.btn_export_md.clicked.connect(self.export_md)
        self.btn_export_pdf.clicked.connect(self.export_pdf)
        self.btn_export_png_zip.clicked.connect(self.export_png_zip)
        self.btn_export_png_dir.clicked.connect(self.export_png_dir)
        self.monitor.clip_saved.connect(
            self.on_clip_saved,
            Qt.ConnectionType.QueuedConnection,
        )
        self.model.modelReset.connect(self.update_select_all_button)
        self.model.rowsInserted.connect(lambda *_: self.update_select_all_button())
        self.model.rowsRemoved.connect(lambda *_: self.update_select_all_button())
        self.model.dataChanged.connect(lambda *_: self.update_select_all_button())

        self.statusBar().showMessage("도구 패널은 버튼 또는 단축키로 열고 닫을 수 있습니다.")
        self.statusBar().addPermanentWidget(self.lbl_realtime_folder_status, 1)

        self._setup_shortcuts(self.shortcut_mapping)
        self.set_widget_mode(True)
        self.apply_theme(self.theme_mode)
        self.update_background_mode_button()
        self.update_select_all_button()
        self.toggle_toolbar_visibility(show=True)
        self._sync_timer.start()

    def _create_section(self, title):
        section = QFrame()
        section.setObjectName("SectionCard")
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(10, 8, 10, 10)
        section_layout.setSpacing(6)
        label = QLabel(title)
        label.setObjectName("SectionTitle")
        section_layout.addWidget(label)
        flow = FlowLayout(h_spacing=6, v_spacing=6)
        section_layout.addLayout(flow)
        return section, section_layout, flow

    def _build_toolbar(self, parent_layout):
        self.header_frame = QFrame()
        self.header_frame.setObjectName("TopHeader")
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(12, 10, 12, 10)
        header_layout.setSpacing(8)
        self.lbl_header_title = QLabel("클립보드 위젯")
        self.lbl_header_title.setObjectName("HeaderTitle")
        self.lbl_header_credit = QLabel("@made by 어디있니내여친")
        self.lbl_header_credit.setObjectName("HeaderSubTitle")
        self.lbl_header_credit.setToolTip("@made by 어디있니내여친")
        self.btn_toolbar_toggle = QPushButton("🧰 도구 패널 닫기")
        self.btn_toolbar_toggle.setObjectName("PrimaryAction")
        header_layout.addWidget(self.lbl_header_title)
        header_layout.addWidget(self.lbl_header_credit)
        header_layout.addStretch(1)
        header_layout.addWidget(self.btn_toolbar_toggle)
        parent_layout.addWidget(self.header_frame)

        self.toolbar_panel = QFrame()
        self.toolbar_panel.setObjectName("ControlPanel")
        panel_layout = QVBoxLayout(self.toolbar_panel)
        panel_layout.setContentsMargins(10, 10, 10, 10)
        panel_layout.setSpacing(8)

        self.btn_widget_mode = QPushButton("📌 위젯 모드: 켜짐")
        self.btn_widget_mode.setCheckable(True)
        self.btn_widget_mode.setChecked(True)
        self.btn_theme_mode = QPushButton("🎨 테마: 다크")
        self.btn_theme_custom = QPushButton("🧩 사용자 테마")
        self.btn_shortcuts = QPushButton("⌨️ 단축키")
        self.btn_background_mode = QPushButton("🛰️ 백그라운드: 꺼짐")
        self.btn_background_mode.setCheckable(True)
        self.btn_background_mode.setChecked(self.background_mode_enabled)
        self.btn_refresh = QPushButton("🔄 새로고침")
        self.btn_select_all = QPushButton("☑️ 전체 선택")
        self.btn_delete = QPushButton("🗑️ 체크 삭제")
        self.btn_import_json = QPushButton("📥 JSON 불러오기")

        self.btn_realtime_mode = QPushButton("💾 실시간 저장: 꺼짐")
        self.btn_realtime_mode.setCheckable(True)
        self.btn_realtime_folder = QPushButton("📁 실시간 저장 폴더")
        self.lbl_realtime_folder = QLabel("📍 저장 위치: 미설정")
        self.lbl_realtime_folder.setObjectName("PathLabel")
        self.lbl_realtime_folder.setWordWrap(True)
        self.lbl_realtime_folder.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self.lbl_realtime_folder.setToolTip("실시간 저장 폴더가 선택되지 않았습니다.")
        self.lbl_realtime_folder_status = QLabel("저장 위치: 미설정")
        self.lbl_realtime_folder_status.setObjectName("PathLabel")
        self.lbl_realtime_folder_status.setToolTip("실시간 저장 폴더가 선택되지 않았습니다.")

        self.cmb_type_filter = QComboBox()
        self.cmb_type_filter.addItems(["전체", "텍스트", "이미지", "파일"])
        self.cmb_duplicate_filter = QComboBox()
        self.cmb_duplicate_filter.addItems(["전체", "중복만", "중복 제외"])
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("🔎 텍스트/경로 검색")
        self.input_search.setMinimumWidth(120)
        self.btn_filter_apply = QPushButton("✅ 필터 적용")
        self.btn_filter_apply.setObjectName("PrimaryAction")
        self.btn_filter_clear = QPushButton("↺ 필터 초기화")

        self.btn_export_txt = QPushButton("📝 TXT 내보내기")
        self.btn_export_md = QPushButton("🧾 Markdown 내보내기")
        self.btn_export_pdf = QPushButton("📄 PDF 내보내기")
        self.btn_export_png_zip = QPushButton("🗜️ PNG ZIP 내보내기")
        self.btn_export_png_dir = QPushButton("🖼️ PNG 폴더 내보내기")

        quick_section, _, quick_flow = self._create_section("빠른 작업")
        for widget in [
            self.btn_widget_mode,
            self.btn_theme_mode,
            self.btn_theme_custom,
            self.btn_shortcuts,
            self.btn_background_mode,
            self.btn_refresh,
            self.btn_select_all,
            self.btn_delete,
            self.btn_import_json,
        ]:
            quick_flow.addWidget(widget)
        panel_layout.addWidget(quick_section)

        realtime_section, realtime_layout, realtime_flow = self._create_section("실시간 저장")
        for widget in [self.btn_realtime_mode, self.btn_realtime_folder]:
            realtime_flow.addWidget(widget)
        realtime_layout.addWidget(self.lbl_realtime_folder)
        panel_layout.addWidget(realtime_section)

        filter_section, _, filter_flow = self._create_section("필터")
        filter_flow.addWidget(QLabel("🏷️ 타입"))
        filter_flow.addWidget(self.cmb_type_filter)
        filter_flow.addWidget(QLabel("♻️ 중복"))
        filter_flow.addWidget(self.cmb_duplicate_filter)
        filter_flow.addWidget(self.input_search)
        filter_flow.addWidget(self.btn_filter_apply)
        filter_flow.addWidget(self.btn_filter_clear)
        panel_layout.addWidget(filter_section)

        export_section, _, export_flow = self._create_section("내보내기")
        for widget in [
            self.btn_export_txt,
            self.btn_export_md,
            self.btn_export_pdf,
            self.btn_export_png_zip,
            self.btn_export_png_dir,
        ]:
            export_flow.addWidget(widget)
        panel_layout.addWidget(export_section)
        parent_layout.addWidget(self.toolbar_panel)

    def _setup_system_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = None
            return

        tray_icon = self.windowIcon()
        if tray_icon.isNull():
            tray_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogInfoView)
            self.setWindowIcon(tray_icon)

        self.tray_icon = QSystemTrayIcon(tray_icon, self)
        self.tray_icon.setToolTip("클립보드 위젯")

        tray_menu = QMenu(self)
        action_show = QAction("창 열기", self)
        action_hide = QAction("창 숨기기", self)
        action_quit = QAction("완전 종료", self)
        action_show.triggered.connect(self.show_from_tray)
        action_hide.triggered.connect(self.hide_to_tray)
        action_quit.triggered.connect(self.quit_from_tray)
        tray_menu.addAction(action_show)
        tray_menu.addAction(action_hide)
        tray_menu.addSeparator()
        tray_menu.addAction(action_quit)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._on_app_about_to_quit)

    def on_tray_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            if self.isVisible():
                self.hide_to_tray()
            else:
                self.show_from_tray()

    def show_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self._tray_notified_hidden = False

    def hide_to_tray(self):
        self.hide()

    def handle_instance_message(self, message):
        if str(message).strip().upper() == "ACTIVATE":
            self.show_from_tray()
            self.statusBar().showMessage("이미 실행 중인 창을 활성화했습니다.", 2000)

    def quit_from_tray(self):
        self.force_quit = True
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def update_background_mode_button(self):
        self.btn_background_mode.blockSignals(True)
        self.btn_background_mode.setChecked(self.background_mode_enabled)
        self.btn_background_mode.blockSignals(False)
        self.btn_background_mode.setText(
            "🛰️ 백그라운드: 켜짐" if self.background_mode_enabled else "🛰️ 백그라운드: 꺼짐"
        )

    def _update_realtime_folder_labels(self):
        if self.realtime_save_dir:
            folder = self.realtime_save_dir
            self.lbl_realtime_folder.setText(f"📍 저장 위치: {folder}")
            self.lbl_realtime_folder.setToolTip(folder)
            self.lbl_realtime_folder_status.setText(f"저장 위치: {folder}")
            self.lbl_realtime_folder_status.setToolTip(folder)
        else:
            self.lbl_realtime_folder.setText("📍 저장 위치: 미설정")
            self.lbl_realtime_folder.setToolTip("실시간 저장 폴더가 선택되지 않았습니다.")
            self.lbl_realtime_folder_status.setText("저장 위치: 미설정")
            self.lbl_realtime_folder_status.setToolTip("실시간 저장 폴더가 선택되지 않았습니다.")

    def _sync_realtime_controls_from_settings(self):
        if self.realtime_save_enabled and not self.realtime_save_dir:
            self.realtime_save_enabled = False
            self.settings.set_realtime_save_enabled(False)
        self._update_realtime_folder_labels()
        self.btn_realtime_mode.blockSignals(True)
        self.btn_realtime_mode.setChecked(self.realtime_save_enabled)
        self.btn_realtime_mode.blockSignals(False)
        self.btn_realtime_mode.setText(
            "💾 실시간 저장: 켜짐" if self.realtime_save_enabled else "💾 실시간 저장: 꺼짐"
        )

    def _sync_model_count_with_db(self):
        if self._cleanup_done or self._auto_sync_running:
            return
        if self.model.get_checked_ids():
            # 체크 상태를 유지하기 위해 사용자가 선택 중일 때 자동 리로드를 피한다.
            return
        try:
            db_count = self.db.count_clips(
                type_filter=self.model.type_filter,
                duplicate_filter=self.model.duplicate_filter,
                search_keyword=self.model.search_keyword,
            )
        except Exception:
            return
        if db_count == self.model.total_count:
            return
        self._auto_sync_running = True
        try:
            self.model.reload()
        finally:
            self._auto_sync_running = False

    def set_background_mode(self, enabled):
        enabled = bool(enabled)
        if enabled and self.tray_icon is None:
            QMessageBox.warning(
                self,
                "백그라운드 모드 사용 불가",
                "이 시스템에서는 트레이 아이콘을 사용할 수 없어 백그라운드 모드를 켤 수 없습니다.",
            )
            self.background_mode_enabled = False
            self.settings.set_background_mode(False)
            self.update_background_mode_button()
            return

        self.background_mode_enabled = enabled
        self.settings.set_background_mode(self.background_mode_enabled)
        self.update_background_mode_button()
        if self.background_mode_enabled and self.tray_icon is not None:
            self.tray_icon.show()
        self.statusBar().showMessage(
            "백그라운드 모드가 켜졌습니다. 창을 닫아도 트레이에서 계속 동작합니다."
            if self.background_mode_enabled
            else "백그라운드 모드가 꺼졌습니다. 창을 닫으면 앱이 종료됩니다.",
            2500,
        )

    def _on_app_about_to_quit(self):
        if self._cleanup_done:
            return
        self._cleanup_done = True
        try:
            self.monitor.clip_saved.disconnect(self.on_clip_saved)
        except TypeError:
            pass
        if self.tray_icon is not None:
            self.tray_icon.hide()
        self._sync_timer.stop()
        self.realtime_save_executor.shutdown(wait=True, cancel_futures=False)

    def _shortcut_text(self, action_key):
        return self.shortcut_mapping.get(action_key, "").strip() or "미지정"

    def _setup_shortcuts(self, mapping):
        self.shortcut_mapping = dict(DEFAULT_SHORTCUTS)
        self.shortcut_mapping.update(mapping or {})
        for shortcut in self.shortcuts.values():
            shortcut.setParent(None)
            shortcut.deleteLater()
        self.shortcuts.clear()

        action_map = {
            "toggle_panel": lambda: self.toggle_toolbar_visibility(),
            "refresh": self.model.reload,
            "select_all": self.toggle_select_all,
            "delete_checked": self.delete_checked_items,
            "toggle_theme": self.toggle_theme,
            "export_markdown": self.export_md,
        }
        for action_key, callback in action_map.items():
            sequence = self.shortcut_mapping.get(action_key, "").strip()
            if not sequence:
                continue
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(callback)
            self.shortcuts[action_key] = shortcut

    def open_shortcut_dialog(self):
        dialog = ShortcutDialog(self.shortcut_mapping, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        mapping = dialog.get_mapping()
        self._setup_shortcuts(mapping)
        self.settings.set_shortcuts(self.shortcut_mapping)
        self.statusBar().showMessage("단축키 설정이 저장되었습니다.", 2000)

    def open_custom_theme_dialog(self):
        dialog = CustomThemeDialog(self.custom_theme_palette, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.custom_theme_palette = dialog.get_palette()
        self.settings.set_custom_theme(self.custom_theme_palette)
        self.apply_theme("custom")
        self.statusBar().showMessage("사용자 테마가 적용되었습니다.", 2000)

    def toggle_toolbar_visibility(self, show=None):
        if show is None:
            show = not self.toolbar_panel.isVisible()
        self.toolbar_panel.setVisible(bool(show))
        self.btn_toolbar_toggle.setText(
            "🧰 도구 패널 닫기" if self.toolbar_panel.isVisible() else "🧰 도구 패널 열기"
        )
        shortcut_hint = self._shortcut_text("toggle_panel")
        self.statusBar().showMessage(
            (
                f"도구 패널 표시됨 (버튼/{shortcut_hint}로 닫기)"
                if self.toolbar_panel.isVisible()
                else f"도구 패널 숨김 (버튼/{shortcut_hint}로 열기)"
            ),
            2000,
        )

    def set_widget_mode(self, enabled):
        self.btn_widget_mode.setText("📌 위젯 모드: 켜짐" if enabled else "📌 위젯 모드: 꺼짐")
        previous_pos = self.pos()
        self.hide()
        self.setWindowFlag(Qt.WindowType.Tool, enabled)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        self.show()
        self.move(previous_pos)

    def toggle_theme(self):
        order = ["dark", "light", "custom"]
        if self.theme_mode not in order:
            self.apply_theme("dark")
            return
        next_mode = order[(order.index(self.theme_mode) + 1) % len(order)]
        self.apply_theme(next_mode)

    def apply_theme(self, mode):
        if mode not in ("dark", "light", "custom"):
            mode = "dark"
        self.theme_mode = mode
        if mode == "dark":
            self.setStyleSheet(DARK_STYLESHEET)
            self.delegate.set_selection_colors("#3a4150", "#f8fafc")
            self.btn_theme_mode.setText("🎨 테마: 다크")
        elif mode == "light":
            self.setStyleSheet(LIGHT_STYLESHEET)
            self.delegate.set_selection_colors("#dbeafe", "#0f172a")
            self.btn_theme_mode.setText("🎨 테마: 라이트")
        else:
            self.setStyleSheet(build_custom_stylesheet(self.custom_theme_palette))
            selection_color = self.custom_theme_palette.get("selection_bg", "#2b4468")
            text_color = self.custom_theme_palette.get("text", "#e7edf5")
            self.delegate.set_selection_colors(selection_color, text_color)
            self.btn_theme_mode.setText("🎨 테마: 사용자")
        self.settings.set_theme_mode(mode)
        self.list_view.viewport().update()

    def apply_filters(self):
        type_filter = self.TYPE_FILTER_MAP.get(self.cmb_type_filter.currentText(), "all")
        duplicate_filter = self.DUPLICATE_FILTER_MAP.get(
            self.cmb_duplicate_filter.currentText(),
            "all",
        )
        keyword = self.input_search.text().strip()
        self.model.set_filters(
            type_filter=type_filter,
            duplicate_filter=duplicate_filter,
            search_keyword=keyword,
        )

    def clear_filters(self):
        self.cmb_type_filter.setCurrentText("전체")
        self.cmb_duplicate_filter.setCurrentText("전체")
        self.input_search.clear()
        self.apply_filters()

    def update_select_all_button(self):
        total_rows = self.model.total_count
        checked_rows = self.model.checked_count()
        if total_rows <= 0:
            self.btn_select_all.setEnabled(False)
            self.btn_select_all.setText("☑️ 전체 선택")
            return
        self.btn_select_all.setEnabled(True)
        if checked_rows >= total_rows:
            self.btn_select_all.setText("🔳 전체 해제")
        else:
            self.btn_select_all.setText("☑️ 전체 선택")

    def toggle_select_all(self):
        if self.model.total_count <= 0:
            return
        should_select_all = self.model.checked_count() < self.model.total_count
        self.model.set_all_checked(checked=should_select_all, include_unloaded=True)
        self.update_select_all_button()

    def choose_realtime_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "실시간 저장 폴더 선택")
        if not folder:
            return
        self.realtime_save_dir = folder
        self.settings.set_realtime_save_dir(folder)
        self._update_realtime_folder_labels()
        if self.btn_realtime_mode.isChecked():
            self.realtime_save_enabled = True
            self.settings.set_realtime_save_enabled(True)
            self.btn_realtime_mode.setText("💾 실시간 저장: 켜짐")

    def toggle_realtime_save(self, enabled):
        enabled = bool(enabled)
        if enabled and not self.realtime_save_dir:
            self.choose_realtime_folder()
            if not self.realtime_save_dir:
                self.btn_realtime_mode.blockSignals(True)
                self.btn_realtime_mode.setChecked(False)
                self.btn_realtime_mode.blockSignals(False)
                self.realtime_save_enabled = False
                self.settings.set_realtime_save_enabled(False)
                self.btn_realtime_mode.setText("💾 실시간 저장: 꺼짐")
                return
        self.realtime_save_enabled = enabled
        self.settings.set_realtime_save_enabled(enabled)
        self.btn_realtime_mode.setText(
            "💾 실시간 저장: 켜짐" if enabled else "💾 실시간 저장: 꺼짐"
        )

    def import_json_file(self):
        json_path, _ = QFileDialog.getOpenFileName(
            self,
            "JSON 불러오기",
            "",
            "JSON 파일 (*.json)",
        )
        if not json_path:
            return

        try:
            with open(json_path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
        except (OSError, json.JSONDecodeError) as exc:
            QMessageBox.warning(self, "불러오기 실패", f"JSON 파싱에 실패했습니다.\n{exc}")
            return

        if isinstance(data, dict):
            data = data.get("items", [])
        if not isinstance(data, list):
            QMessageBox.warning(self, "불러오기 실패", "JSON 루트는 배열이어야 합니다.")
            return

        result = self._import_json_records(data)
        self.apply_filters()
        QMessageBox.information(
            self,
            "JSON 불러오기 완료",
            (
                f"추가됨: {result['imported']}개\n"
                f"형식 오류로 건너뜀: {result['skipped_invalid']}개\n"
                f"이미지 파일 누락으로 건너뜀: {result['skipped_missing']}개"
            ),
        )

    def _normalize_timestamp(self, value):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if value is None:
            return now_str

        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M:%S")
            except (OverflowError, OSError, ValueError):
                return now_str

        text = str(value).strip()
        if not text:
            return now_str

        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(text, fmt)
                if fmt == "%Y-%m-%d":
                    dt = dt.replace(hour=0, minute=0, second=0)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass

        try:
            iso = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if iso.tzinfo is not None:
                iso = iso.astimezone().replace(tzinfo=None)
            return iso.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return now_str

    def _hash_file(self, file_path):
        digest = hashlib.md5()
        with open(file_path, "rb") as fp:
            for chunk in iter(lambda: fp.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _import_json_records(self, items):
        records = []
        record_hashes = []
        skipped_invalid = 0
        skipped_missing = 0
        import_dir = None

        for item in items:
            if not isinstance(item, dict):
                skipped_invalid += 1
                continue

            c_type = item.get("type")
            if c_type not in ("text", "image", "file"):
                skipped_invalid += 1
                continue

            record_id = str(uuid.uuid4())
            timestamp = self._normalize_timestamp(item.get("timestamp"))

            if c_type == "text":
                content = str(item.get("content", ""))
                if not content:
                    skipped_invalid += 1
                    continue
                c_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
                records.append([record_id, "text", content, c_hash, 0, timestamp])
                record_hashes.append(c_hash)
                continue

            if c_type == "file":
                raw_content = item.get("content", "")
                if isinstance(raw_content, list):
                    file_paths = [str(path).strip() for path in raw_content if str(path).strip()]
                else:
                    file_paths = [
                        line.strip()
                        for line in str(raw_content).splitlines()
                        if line.strip()
                    ]
                if not file_paths:
                    skipped_invalid += 1
                    continue
                content = "\n".join(file_paths)
                normalized = "\n".join(sorted(os.path.normcase(path) for path in file_paths))
                c_hash = hashlib.md5(normalized.encode("utf-8")).hexdigest()
                records.append([record_id, "file", content, c_hash, 0, timestamp])
                record_hashes.append(c_hash)
                continue

            source_path = str(item.get("content", ""))
            if not source_path or not os.path.exists(source_path):
                skipped_missing += 1
                continue

            if import_dir is None:
                now = datetime.now()
                import_dir = os.path.join(
                    self.monitor.base_dir,
                    "imports",
                    now.strftime("%Y-%m-%d"),
                    now.strftime("%H%M%S"),
                )
                os.makedirs(import_dir, exist_ok=True)

            ext = os.path.splitext(source_path)[1] or ".png"
            filename = f"import_{timestamp_to_filename_fragment(timestamp)}_{record_id[:8]}{ext}"
            copied_path = os.path.join(import_dir, filename)
            try:
                shutil.copy2(source_path, copied_path)
                c_hash = self._hash_file(copied_path)
            except OSError:
                skipped_missing += 1
                continue

            records.append([record_id, "image", copied_path, c_hash, 0, timestamp])
            record_hashes.append(c_hash)

        existing_hashes = self.db.get_existing_hashes_since(
            record_hashes,
            "1970-01-01 00:00:00",
        )
        if existing_hashes:
            for record in records:
                record[4] = 1 if record[3] in existing_hashes else 0

        imported = self.db.insert_clips_bulk([tuple(record) for record in records])
        return {
            "imported": imported,
            "skipped_invalid": skipped_invalid,
            "skipped_missing": skipped_missing,
        }

    def save_realtime_item(self, item):
        if not self.realtime_save_enabled or not self.realtime_save_dir:
            return
        item_copy = dict(item)
        target_dir = self.realtime_save_dir
        try:
            self.realtime_save_executor.submit(self._write_realtime_item, target_dir, item_copy)
        except RuntimeError:
            return

    def _write_realtime_item(self, target_dir, item):
        try:
            os.makedirs(target_dir, exist_ok=True)
            timestamp_str = timestamp_to_filename_fragment(item.get("timestamp", ""))
            suffix = item.get("id", "")[:8]

            if item.get("type") == "image":
                source_path = item.get("content", "")
                if os.path.exists(source_path):
                    ext = os.path.splitext(source_path)[1].lower() or ".png"
                    target_path = os.path.join(
                        target_dir,
                        f"{timestamp_str}_{suffix}{ext}",
                    )
                    shutil.copy2(source_path, target_path)
            elif item.get("type") == "text":
                target_path = os.path.join(
                    target_dir,
                    f"{timestamp_str}_{suffix}.txt",
                )
                with open(target_path, "w", encoding="utf-8") as fp:
                    fp.write(item.get("content", ""))
            elif item.get("type") == "file":
                target_path = os.path.join(
                    target_dir,
                    f"{timestamp_str}_{suffix}_files.txt",
                )
                with open(target_path, "w", encoding="utf-8") as fp:
                    fp.write(item.get("content", ""))
        except OSError:
            return

    def _get_items_for_export(self):
        checked_ids = self.model.get_checked_ids()
        if checked_ids:
            return self.db.get_clips_by_ids(checked_ids)

        dialog = QMessageBox(self)
        dialog.setWindowTitle("선택 없음")
        dialog.setText("체크한 항목이 없습니다. 어떤 범위를 내보낼까요?")
        btn_filtered = dialog.addButton("현재 필터 결과", QMessageBox.ButtonRole.AcceptRole)
        btn_all = dialog.addButton("전체 히스토리", QMessageBox.ButtonRole.ActionRole)
        dialog.addButton(QMessageBox.StandardButton.Cancel)
        dialog.exec()

        clicked = dialog.clickedButton()
        if clicked == btn_filtered:
            return self.db.get_all_clips(
                type_filter=self.model.type_filter,
                duplicate_filter=self.model.duplicate_filter,
                search_keyword=self.model.search_keyword,
            )
        if clicked == btn_all:
            return self.db.get_all_clips()
        return []

    def _show_export_done(self, output_path, exported_count=None):
        extra = ""
        if isinstance(exported_count, int):
            extra = f"\n내보낸 항목: {exported_count}개"
        QMessageBox.information(
            self,
            "내보내기 완료",
            f"내보내기가 완료되었습니다.\n{output_path}{extra}",
        )

    def _show_export_empty_warning(self):
        QMessageBox.warning(
            self,
            "내보내기 없음",
            "내보낼 수 있는 항목이 없어 파일이 생성되지 않았습니다.",
        )

    def _export_with_save_dialog(
        self,
        dialog_title,
        default_filename,
        file_filter,
        export_callback,
    ):
        items = self._get_items_for_export()
        if not items:
            return
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            dialog_title,
            default_filename,
            file_filter,
        )
        if not output_path:
            return
        exported_count = export_callback(items, output_path)
        if isinstance(exported_count, int) and exported_count <= 0:
            self._show_export_empty_warning()
            return
        self._show_export_done(
            output_path,
            exported_count if isinstance(exported_count, int) else None,
        )

    def export_txt(self):
        self._export_with_save_dialog(
            dialog_title="TXT 내보내기",
            default_filename="클립보드_내보내기.txt",
            file_filter="텍스트 파일 (*.txt)",
            export_callback=self.export_manager.export_txt,
        )

    def export_md(self):
        self._export_with_save_dialog(
            dialog_title="Markdown 내보내기",
            default_filename="클립보드_내보내기.md",
            file_filter="마크다운 파일 (*.md)",
            export_callback=self.export_manager.export_markdown,
        )

    def export_pdf(self):
        self._export_with_save_dialog(
            dialog_title="PDF 내보내기",
            default_filename="클립보드_내보내기.pdf",
            file_filter="PDF 파일 (*.pdf)",
            export_callback=self.export_manager.export_pdf,
        )

    def export_png_zip(self):
        self._export_with_save_dialog(
            dialog_title="PNG ZIP 내보내기",
            default_filename="클립보드_이미지.zip",
            file_filter="ZIP 파일 (*.zip)",
            export_callback=lambda items, path: self.export_manager.export_png(
                items, path, as_zip=True
            ),
        )

    def export_png_dir(self):
        items = self._get_items_for_export()
        if not items:
            return
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "PNG 저장 폴더 선택",
        )
        if not output_dir:
            return
        exported_count = self.export_manager.export_png(items, output_dir, as_zip=False)
        if exported_count <= 0:
            self._show_export_empty_warning()
            return
        self._show_export_done(output_dir, exported_count)

    def delete_checked_items(self):
        checked_ids = self.model.get_checked_ids()
        if not checked_ids:
            QMessageBox.warning(self, "삭제", "삭제할 체크 항목이 없습니다.")
            return
        answer = QMessageBox.question(
            self,
            "삭제 확인",
            f"{len(checked_ids)}개 항목을 삭제할까요?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        removed_items = self.db.delete_clips(checked_ids)
        for item in removed_items:
            if item.get("type") == "image":
                image_path = item.get("content", "")
                self.cache_manager.invalidate_path(image_path)
                if os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                    except OSError:
                        pass
        self.apply_filters()

    def on_clip_saved(self, item):
        self.model.prepend_item(item)
        self.save_realtime_item(item)

    def on_item_double_clicked(self, index):
        c_type = index.data(self.model.TypeRole)
        content = index.data(self.model.ContentRole)
        timestamp = index.data(self.model.TimestampRole)
        if c_type == "image":
            viewer = ImageViewerDialog(content, self)
            viewer.exec()
        elif c_type == "text":
            viewer = TextViewerDialog(content, timestamp, self)
            viewer.exec()
        elif c_type == "file":
            viewer = FileViewerDialog(content, timestamp, self)
            viewer.exec()

    def closeEvent(self, event: QCloseEvent):
        if self.background_mode_enabled and not self.force_quit and self.tray_icon is not None:
            dialog = QMessageBox(self)
            dialog.setWindowTitle("종료 방식 선택")
            dialog.setIcon(QMessageBox.Icon.Question)
            dialog.setText("앱을 완전히 종료할까요, 백그라운드에서 계속 실행할까요?")
            btn_background = dialog.addButton("백그라운드에서 계속 실행", QMessageBox.ButtonRole.AcceptRole)
            btn_quit = dialog.addButton("완전 종료", QMessageBox.ButtonRole.DestructiveRole)
            dialog.addButton("취소", QMessageBox.ButtonRole.RejectRole)
            dialog.exec()

            clicked = dialog.clickedButton()
            if clicked == btn_background:
                self.hide_to_tray()
                if not self._tray_notified_hidden:
                    self.tray_icon.showMessage(
                        "클립보드 위젯",
                        "백그라운드 모드로 전환되었습니다. 트레이 아이콘에서 다시 열 수 있습니다.",
                        QSystemTrayIcon.MessageIcon.Information,
                        2500,
                    )
                    self._tray_notified_hidden = True
                event.ignore()
                return
            if clicked == btn_quit:
                self.force_quit = True
            else:
                event.ignore()
                return
        self._on_app_about_to_quit()
        event.accept()
        # Qt.Tool 창은 "lastWindowClosed" 종료 경로가 누락될 수 있어 명시적으로 종료를 요청한다.
        app = QApplication.instance()
        if app is not None and (self.force_quit or not self.background_mode_enabled):
            app.quit()
