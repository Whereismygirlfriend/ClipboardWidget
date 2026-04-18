import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMessageBox
from database import DatabaseManager
from export import ExportManager
from monitor import ClipboardMonitor
from instance_guard import SingleInstanceGuard
from settings import SettingsManager
from ui import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("클립보드 위젯")
    app.setQuitOnLastWindowClosed(True)

    # 세션 시간 및 기본 경로 초기화
    session_start_time = datetime.now()
    base_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "ClipboardManager")
    os.makedirs(base_dir, exist_ok=True)

    db_path = os.path.join(base_dir, "clipboard_history.db")
    sound_path = os.path.join(base_dir, "sounds", "notify.wav")
    instance_name = "ClipboardWidgetSingleton_v2"

    guard = SingleInstanceGuard(instance_name)
    if not guard.is_primary:
        QMessageBox.information(
            None,
            "이미 실행 중",
            "클립보드 위젯이 이미 백그라운드에서 실행 중입니다.\n기존 창을 활성화합니다.",
        )
        sys.exit(0)

    # 코어 모듈 인스턴스화
    db_manager = DatabaseManager(db_path)
    export_manager = ExportManager()
    settings_manager = SettingsManager(base_dir)

    # 백그라운드 모니터 실행
    monitor = ClipboardMonitor(db_manager, base_dir, sound_path, session_start_time)

    # UI 렌더링
    window = MainWindow(db_manager, export_manager, monitor, settings_manager)
    guard.message_received.connect(window.handle_instance_message)
    window.show()

    def cleanup():
        guard.close()
        monitor.stop()
        db_manager.close()

    app.aboutToQuit.connect(cleanup)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
