from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket


class SingleInstanceGuard(QObject):
    message_received = pyqtSignal(str)

    def __init__(self, server_name):
        super().__init__()
        self.server_name = server_name
        self.server = None
        self.is_primary = False

        if self._notify_existing():
            self.is_primary = False
            return

        QLocalServer.removeServer(self.server_name)
        self.server = QLocalServer(self)
        if not self.server.listen(self.server_name):
            self.is_primary = False
            return

        self.server.newConnection.connect(self._on_new_connection)
        self.is_primary = True

    def _notify_existing(self):
        socket = QLocalSocket()
        socket.connectToServer(self.server_name)
        if not socket.waitForConnected(150):
            return False
        socket.write(b"ACTIVATE")
        socket.flush()
        socket.waitForBytesWritten(150)
        socket.disconnectFromServer()
        return True

    def _on_new_connection(self):
        if self.server is None:
            return
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            if socket is None:
                continue
            self.message_received.emit("ACTIVATE")
            socket.disconnectFromServer()
            socket.deleteLater()

    def close(self):
        if self.server is not None:
            self.server.close()
            QLocalServer.removeServer(self.server_name)
