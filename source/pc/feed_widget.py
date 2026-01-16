"""
FeedWidget - QtMultimedia-based UDP MPEG-TS viewer
"""

from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import QVBoxLayout, QWidget

class FeedWidget(QWidget):
    status_text = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._port = None

        self.video_widget = QVideoWidget(self)
        self.player = QMediaPlayer(self)

        self.audio = QAudioOutput(self)
        self.audio.setVolume(0.0)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.video_widget)
        self.setLayout(layout)

        # Signals
        self.player.errorOccurred.connect(self._on_error)
        self.player.playbackStateChanged.connect(self._on_state)

    def start(self, port: int):
        self._port = int(port)

        url = QUrl(f"udp://@0.0.0.0:{self._port}")
        self.player.setSource(url)
        self.player.play()
        self.status_text.emit(f"Playing UDP MPEG-TS on port {self._port}")

    def stop(self):
        self.player.stop()
        if self._port is not None:
            self.status_text.emit(f"Stopped (port {self._port})")
        else:
            self.status_text.emit("Stopped")

    def _on_state(self, state: QMediaPlayer.PlaybackState):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            if self._port is not None:
                self.status_text.emit(f"Receiving (port {self._port})")
            else:
                self.status_text.emit("Receiving")
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.status_text.emit("Paused")
        else:
            if self._port is not None:
                self.status_text.emit(f"Stopped (port {self._port})")
            else:
                self.status_text.emit("Stopped")

    def _on_error(self, err: QMediaPlayer.Error, err_str: str):
        msg = f"Playback error ({int(err)}): {err_str}".strip()
        self.status_text.emit(msg)