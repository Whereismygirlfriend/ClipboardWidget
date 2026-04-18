import os
import uuid
import hashlib
import time
import struct
import logging
from datetime import datetime
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import (
    QByteArray,
    QBuffer,
    QIODevice,
    QObject,
    QThread,
    Qt,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import QImage
from plyer import notification
import playsound
try:
    import winsound
except ImportError:
    winsound = None

logger = logging.getLogger(__name__)


class ClipboardWorker(QObject):
    clip_saved = pyqtSignal(dict)
    alert_requested = pyqtSignal(str, str)

    def __init__(self, db_manager, session_folder, session_start_time, ttl_seconds):
        super().__init__()
        self.db = db_manager
        self.session_folder = session_folder
        self.session_start_time = session_start_time
        self.ttl_seconds = ttl_seconds
        self.last_hash = None
        self.last_event_time = 0

    @pyqtSlot(dict)
    def process_payload(self, payload):
        current_time = time.time()
        c_type = payload.get("type")
        c_hash = None
        content = None
        image_ext = ".png"

        if c_type == "image":
            image_bytes = payload.get("image_bytes")
            if not image_bytes:
                return
            c_hash = hashlib.md5(image_bytes).hexdigest()
            content = image_bytes
            raw_ext = str(payload.get("image_ext", ".png")).strip().lower()
            image_ext = raw_ext if raw_ext.startswith(".") else f".{raw_ext}"
            if not image_ext or image_ext == ".":
                image_ext = ".png"
        elif c_type == "file":
            files = payload.get("files", [])
            if not files:
                return
            file_paths = [
                os.path.normpath(str(path))
                for path in files
                if str(path).strip()
            ]
            if not file_paths:
                return
            normalized = sorted(os.path.normcase(path) for path in file_paths)
            c_hash = hashlib.md5("\n".join(normalized).encode("utf-8")).hexdigest()
            content = "\n".join(file_paths)
        elif c_type == "text":
            text = payload.get("text", "")
            if not text:
                return
            c_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
            content = text
        else:
            return

        time_passed = current_time - self.last_event_time
        if c_hash == self.last_hash and time_passed < self.ttl_seconds:
            return

        is_existing = self.db.check_exists_by_hash(
            c_hash, self.session_start_time.strftime("%Y-%m-%d %H:%M:%S")
        )
        is_duplicate = 1 if is_existing else 0

        record_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.last_hash = c_hash
        self.last_event_time = current_time

        if c_type == "image":
            filename = f"clip_{datetime.now().strftime('%H%M%S')}_{record_id[:8]}{image_ext}"
            filepath = os.path.join(self.session_folder, filename)
            with open(filepath, "wb") as fp:
                fp.write(content)
            db_content = filepath
        else:
            db_content = content

        self.db.insert_clip(
            record_id,
            c_type,
            db_content,
            c_hash,
            is_duplicate,
            timestamp=timestamp,
        )

        self.clip_saved.emit(
            {
                "id": record_id,
                "type": c_type,
                "content": db_content,
                "timestamp": timestamp,
                "is_duplicate": is_duplicate,
            }
        )
        status_msg = "[중복] " if is_duplicate else ""
        if c_type == "image":
            type_label = "이미지"
        elif c_type == "file":
            type_label = "파일"
        else:
            type_label = "텍스트"
        self.alert_requested.emit(
            f"{status_msg}{type_label} 복사 감지",
            "히스토리가 업데이트되었습니다.",
        )


class ClipboardMonitor(QObject):
    payload_received = pyqtSignal(dict)
    clip_saved = pyqtSignal(dict)

    def __init__(self, db_manager, base_dir, sound_path, session_start_time, ttl_seconds=3):
        super().__init__()
        self.db = db_manager
        self.base_dir = base_dir
        self.sound_path = sound_path
        self.session_start_time = session_start_time
        self.ttl_seconds = ttl_seconds
        self._stopped = False

        self.clipboard = QApplication.clipboard()
        self.clipboard.dataChanged.connect(self.on_clipboard_changed)

        self.session_folder = os.path.join(
            self.base_dir,
            "images",
            self.session_start_time.strftime("%Y-%m-%d"),
            self.session_start_time.strftime("%H%M%S"),
        )
        os.makedirs(self.session_folder, exist_ok=True)

        self.worker_thread = QThread(self)
        self.worker = ClipboardWorker(
            db_manager=self.db,
            session_folder=self.session_folder,
            session_start_time=self.session_start_time,
            ttl_seconds=self.ttl_seconds,
        )
        self.worker.moveToThread(self.worker_thread)
        self.payload_received.connect(
            self.worker.process_payload,
            Qt.ConnectionType.QueuedConnection,
        )
        self.worker.clip_saved.connect(
            self._relay_clip_saved,
            Qt.ConnectionType.QueuedConnection,
        )
        self.worker.alert_requested.connect(
            self.trigger_alert,
            Qt.ConnectionType.QueuedConnection,
        )
        self.worker_thread.finished.connect(self.worker.deleteLater)
        self.worker_thread.start()

    @pyqtSlot(dict)
    def _relay_clip_saved(self, item):
        self.clip_saved.emit(item)

    @staticmethod
    def _guess_image_ext(mime_format):
        normalized = str(mime_format or "").strip().lower()
        if "gif" in normalized:
            return ".gif"
        if "png" in normalized:
            return ".png"
        if "jpg" in normalized or "jpeg" in normalized or "jfif" in normalized:
            return ".jpg"
        if "bmp" in normalized or "dib" in normalized:
            return ".bmp"
        if "webp" in normalized:
            return ".webp"
        if "tif" in normalized:
            return ".tiff"
        return ""

    def _extract_raw_image_payload(self, mime_data):
        preferred_formats = (
            "image/png",
            "image/jpeg",
            "image/jpg",
            "image/bmp",
            "image/x-ms-bmp",
            "image/webp",
            "image/tiff",
            "PNG",
            "JFIF",
            "DIB",
        )

        for fmt in preferred_formats:
            if not mime_data.hasFormat(fmt):
                continue
            raw = bytes(mime_data.data(fmt))
            if not raw:
                continue
            ext = self._guess_image_ext(fmt) or ".png"
            if ext == ".bmp" and "dib" in str(fmt).lower():
                converted = self._dib_to_bmp(raw)
                if converted and not QImage.fromData(converted).isNull():
                    return converted, ".bmp"
            if not QImage.fromData(raw).isNull():
                return raw, ext

        for fmt in mime_data.formats():
            ext = self._guess_image_ext(fmt)
            if not ext:
                continue
            raw = bytes(mime_data.data(fmt))
            if not raw:
                continue
            if ext == ".bmp" and "dib" in str(fmt).lower():
                converted = self._dib_to_bmp(raw)
                if converted and not QImage.fromData(converted).isNull():
                    return converted, ".bmp"
            if not QImage.fromData(raw).isNull():
                return raw, ext

        return None

    @staticmethod
    def _dib_to_bmp(dib_bytes):
        if not dib_bytes or len(dib_bytes) < 40:
            return None
        try:
            header_size = int.from_bytes(dib_bytes[0:4], "little", signed=False)
            if header_size < 40 or header_size > len(dib_bytes):
                return None

            bit_count = int.from_bytes(dib_bytes[14:16], "little", signed=False)
            compression = int.from_bytes(dib_bytes[16:20], "little", signed=False)
            colors_used = int.from_bytes(dib_bytes[32:36], "little", signed=False)

            pixel_offset = 14 + header_size
            if bit_count <= 8:
                color_count = colors_used if colors_used else (1 << bit_count)
                pixel_offset += color_count * 4
            if compression == 3 and header_size == 40:
                pixel_offset += 12
            elif compression == 6 and header_size == 40:
                pixel_offset += 16

            if pixel_offset < 14 or pixel_offset > (14 + len(dib_bytes)):
                return None

            file_size = 14 + len(dib_bytes)
            file_header = struct.pack("<2sIHHI", b"BM", file_size, 0, 0, pixel_offset)
            return file_header + dib_bytes
        except (ValueError, struct.error, OverflowError):
            return None

    def on_clipboard_changed(self):
        if self._stopped:
            return
        mime_data = self.clipboard.mimeData()
        if mime_data.hasFormat("image/gif"):
            gif_data = bytes(mime_data.data("image/gif"))
            if gif_data:
                self.payload_received.emit(
                    {"type": "image", "image_bytes": gif_data, "image_ext": ".gif"}
                )
                return
        if mime_data.hasImage():
            raw_payload = self._extract_raw_image_payload(mime_data)
            if raw_payload is not None:
                image_bytes, image_ext = raw_payload
                self.payload_received.emit(
                    {"type": "image", "image_bytes": image_bytes, "image_ext": image_ext}
                )
                return
            image = self.clipboard.image()
            if image.isNull():
                return
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            image.save(buffer, "PNG")
            self.payload_received.emit(
                {"type": "image", "image_bytes": bytes(byte_array), "image_ext": ".png"}
            )
            return
        if mime_data.hasUrls():
            files = [
                url.toLocalFile()
                for url in mime_data.urls()
                if url.isLocalFile() and url.toLocalFile()
            ]
            if not files:
                return
            self.payload_received.emit({"type": "file", "files": files})
        elif mime_data.hasText():
            text = self.clipboard.text()
            if not text:
                return
            self.payload_received.emit({"type": "text", "text": text})

    @pyqtSlot(str, str)
    def trigger_alert(self, title, message):
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="클립보드 위젯",
                timeout=2,
            )
            if os.path.exists(self.sound_path):
                self._play_sound()
        except Exception:
            logger.debug("Desktop notification failed.", exc_info=True)

    def _play_sound(self):
        try:
            if winsound is not None:
                winsound.PlaySound(
                    self.sound_path,
                    winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
                )
            else:
                playsound.playsound(self.sound_path, block=False)
        except Exception:
            logger.debug("Sound playback failed.", exc_info=True)

    def stop(self):
        if self._stopped:
            return
        self._stopped = True
        try:
            self.clipboard.dataChanged.disconnect(self.on_clipboard_changed)
        except TypeError:
            logger.debug("Clipboard signal already disconnected.")
        try:
            self.payload_received.disconnect(self.worker.process_payload)
        except TypeError:
            logger.debug("Payload signal already disconnected.")
        try:
            self.worker.clip_saved.disconnect(self._relay_clip_saved)
        except TypeError:
            logger.debug("clip_saved signal already disconnected.")
        try:
            self.worker.alert_requested.disconnect(self.trigger_alert)
        except TypeError:
            logger.debug("alert_requested signal already disconnected.")
        self.worker_thread.quit()
        if not self.worker_thread.wait(5000):
            logger.warning("Worker thread did not stop in 5s, retrying graceful shutdown.")
            self.worker_thread.requestInterruption()
            self.worker_thread.quit()
            if not self.worker_thread.wait(5000):
                logger.error("Worker thread force terminated after graceful retries.")
                self.worker_thread.terminate()
                self.worker_thread.wait(2000)
        if winsound is not None:
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except RuntimeError:
                logger.debug("winsound purge failed.")
