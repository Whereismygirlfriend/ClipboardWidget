import os
import json
import zipfile
import shutil
from PyQt6.QtGui import QPdfWriter, QPainter, QPageSize, QImage, QTextDocument
from PyQt6.QtCore import QMarginsF, QSizeF, QRectF
from utils import timestamp_to_filename_fragment


class ExportManager:
    def __init__(self):
        pass

    def _image_extension(self, src_path):
        ext = os.path.splitext(str(src_path))[1].strip().lower()
        return ext if ext else ".png"

    def _parse_file_paths(self, content):
        if isinstance(content, list):
            return [str(path).strip() for path in content if str(path).strip()]
        text = str(content or "")
        return [line.strip() for line in text.splitlines() if line.strip()]

    def _iter_existing_images(self, items):
        for idx, item in enumerate(items):
            if item.get("type") != "image":
                continue
            src_path = item.get("content", "")
            if not os.path.exists(src_path):
                continue
            timestamp_str = timestamp_to_filename_fragment(item.get("timestamp", ""))
            yield idx, src_path, timestamp_str, self._image_extension(src_path)

    def export_txt(self, items, output_path):
        written_count = 0
        with open(output_path, "w", encoding="utf-8") as f:
            for item in items:
                timestamp = item.get("timestamp", "")
                c_type = item.get("type", "unknown")
                content = ""
                if c_type == "text":
                    content = str(item.get("content", ""))
                elif c_type == "image":
                    content = f"[이미지 경로]\n{item.get('content', '')}"
                elif c_type == "file":
                    file_paths = self._parse_file_paths(item.get("content", ""))
                    content = "\n".join(file_paths) if file_paths else "(파일 경로 없음)"
                else:
                    content = str(item.get("content", ""))

                f.write(f"[{timestamp}] ({c_type})\n{content}\n\n{'-' * 40}\n\n")
                written_count += 1
        return written_count

    def export_json(self, items, output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=4)
        return len(items)

    def export_markdown(self, items, output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# 클립보드 내보내기\n\n")
            for idx, item in enumerate(items, start=1):
                timestamp = item.get("timestamp", "")
                c_type = item.get("type", "unknown")
                if c_type == "text":
                    f.write(f"## {idx}. 텍스트 ({timestamp})\n\n")
                    f.write(f"{item.get('content', '')}\n\n")
                elif c_type == "image":
                    image_path = item.get("content", "")
                    markdown_path = str(image_path).replace("\\", "/")
                    f.write(f"## {idx}. 이미지 ({timestamp})\n\n")
                    f.write(f"![클립보드 이미지 {idx}]({markdown_path})\n\n")
                    f.write(f"- 원본 경로: `{image_path}`\n\n")
                elif c_type == "file":
                    file_paths = self._parse_file_paths(item.get("content", ""))
                    f.write(f"## {idx}. 파일 ({timestamp})\n\n")
                    if file_paths:
                        for path in file_paths:
                            f.write(f"- `{path}`\n")
                    else:
                        f.write("- (파일 경로 없음)\n")
                    f.write("\n")
                else:
                    f.write(f"## {idx}. 기타 ({timestamp})\n\n")
                    f.write(f"{item.get('content', '')}\n\n")
        return len(items)

    def export_pdf(self, items, output_path):
        if not items:
            return 0
        writer = QPdfWriter(output_path)
        writer.setPageMargins(QMarginsF(10, 10, 10, 10))
        painter = QPainter()
        is_first_page = True
        exported_count = 0

        for item in items:
            if item["type"] == "image":
                img = QImage(item["content"])
                if img.isNull():
                    continue
                page_size = QPageSize(QSizeF(img.width(), img.height()), QPageSize.Unit.Point)
                if is_first_page:
                    writer.setPageSize(page_size)
                    painter.begin(writer)
                    is_first_page = False
                else:
                    writer.setPageSize(page_size)
                    writer.newPage()
                painter.drawImage(0, 0, img)
                exported_count += 1
            elif item["type"] in ("text", "file"):
                page_size = QPageSize(QPageSize.PageSizeId.A4)
                if is_first_page:
                    writer.setPageSize(page_size)
                    painter.begin(writer)
                    is_first_page = False
                else:
                    writer.setPageSize(page_size)
                    writer.newPage()
                doc = QTextDocument()
                if item["type"] == "file":
                    file_text = "\n".join(self._parse_file_paths(item.get("content", "")))
                    content_text = f"[{item['timestamp']}]\n[파일]\n{file_text}"
                else:
                    content_text = f"[{item['timestamp']}]\n{item['content']}"
                doc.setPlainText(content_text)
                paint_rect = writer.pageLayout().paintRectPixels(writer.resolution())
                doc.setTextWidth(paint_rect.width())
                page_height = paint_rect.height()
                current_y = 0.0
                total_height = doc.size().height()
                while current_y < total_height:
                    clip_rect = QRectF(0, current_y, paint_rect.width(), page_height)
                    painter.save()
                    painter.translate(0, -current_y)
                    doc.drawContents(painter, clip_rect)
                    painter.restore()
                    current_y += page_height
                    if current_y < total_height:
                        writer.newPage()
                exported_count += 1
        if painter.isActive():
            painter.end()
        return exported_count

    def export_png(self, items, output_dir_or_zip, as_zip=False):
        images = list(self._iter_existing_images(items))
        if not images:
            return 0
        if as_zip:
            with zipfile.ZipFile(output_dir_or_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
                for idx, src_path, timestamp_str, ext in images:
                    zipf.write(src_path, f"{timestamp_str}_{idx}{ext}")
        else:
            os.makedirs(output_dir_or_zip, exist_ok=True)
            for idx, src_path, timestamp_str, ext in images:
                shutil.copy2(
                    src_path, os.path.join(output_dir_or_zip, f"{timestamp_str}_{idx}{ext}")
                )
        return len(images)
