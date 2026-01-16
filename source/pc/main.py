"""
PC Server Node - PyQt6 Video Viewer (UDP MPEG-TS, H.264)

This module displays the annotated video stream from the Raspberry Pi using PyQt6

Expected incoming stream: UDP MPEG-TS containing H.264 video.
Example sender (RPi) pipeline sketch:
  ... ! h264parse ! mpegtsmux ! udpsink host=<PC_IP> port=<PORT>
"""

import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSpinBox,
    QToolBar,
    QTimer
)

from feed_widget import FeedWidget

# Configuration
PORT = 5000

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RPi Gimbal Tracker")
        self.setMinimumSize(1920, 1080)

        self.feed = FeedWidget(parent=self)
        self.setCentralWidget(self.feed)

        # Toolbar controls
        tb = QToolBar("Controls", self)
        tb.setMovable(False)
        self.addToolBar(tb)

        self.port_spin = QSpinBox(self)
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(PORT)
        self.port_spin.setToolTip("UDP listen port (MPEG-TS)")
        tb.addWidget(self.port_spin)

        start_action = tb.addAction("Start")
        stop_action = tb.addAction("Stop")

        start_action.triggered.connect(self._on_start)
        stop_action.triggered.connect(self._on_stop)

        # Status bar
        self.statusBar().showMessage(f"Ready (port {PORT})")

        # Feed signals
        self.feed.status_text.connect(self.statusBar().showMessage)

        # Autostart
        QTimer.singleShot(0.1, self._on_start)

    def _on_start(self):
        self.feed.start(port=PORT)

    def _on_stop(self):
        self.feed.stop()

    def closeEvent(self, event):
        try:
            self.feed.stop()
        finally:
            event.accept()

def main():
    # Qt app
    app = QApplication(sys.argv)
    app.setApplicationName("RPi Gimbal Tracker")
    app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, True)

    win = MainWindow()
    win.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())