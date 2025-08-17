import sys
import os
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QProgressBar, QScrollArea, QFrame, QHBoxLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class SongWidget(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setLineWidth(1)
        self.setStyleSheet("background-color: #f0f0f0;")
        
        layout = QVBoxLayout()
        self.title_label = QLabel(title)
        self.status_label = QLabel("Waiting...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.title_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

    def set_progress(self, value):
        self.progress_bar.setValue(value)

    def set_status(self, status):
        self.status_label.setText(status)

class DownloadThread(QThread):
    song_started = pyqtSignal(str)
    song_progress = pyqtSignal(str, int)
    song_finished = pyqtSignal(str, str)  # title, status
    overall_progress = pyqtSignal(int)

    def __init__(self, urls, output_folder):
        super().__init__()
        self.urls = urls
        self.output_folder = output_folder
        self._is_running = True
        self._is_paused = False

    def run(self):
        total = len(self.urls)
        for i, url in enumerate(self.urls):
            if not self._is_running:
                break

            while self._is_paused:
                self.msleep(500)
                if not self._is_running:
                    return

            # Extract song title for display
            title = url.split("/")[-1][:30]
            self.song_started.emit(title)

            # Build spotdl command
            command = [
                "spotdl", "download", url,
                "--output", os.path.join(self.output_folder, "{artist}/{album}/{title}.mp3"),
                "--format", "mp3",
                "--bitrate", "320k"
            ]

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            for line in process.stdout:
                line = line.strip()
                if not line or "AZLyrics" in line:
                    continue  # skip repetitive warnings

                if "%" in line:
                    try:
                        percent = int(line.split("%")[0].split()[-1])
                        self.song_progress.emit(title, percent)
                    except:
                        pass

            process.wait()
            status = "Finished" if process.returncode == 0 else "Error"
            self.song_progress.emit(title, 100)
            self.song_finished.emit(title, status)
            self.overall_progress.emit(int((i+1)/total*100))

    def stop(self):
        self._is_running = False
        self._is_paused = False

    def pause(self):
        self._is_paused = True

    def resume(self):
        self._is_paused = False

class SpotDLGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SpotDL GUI Downloader")
        self.setGeometry(300, 150, 800, 600)
        self.song_widgets = {}
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # URL List
        self.url_label = QLabel("Spotify URL List (.txt)")
        self.url_entry = QLineEdit()
        self.url_browse = QPushButton("Browse")
        self.url_browse.clicked.connect(self.browse_file)
        layout.addWidget(self.url_label)
        layout.addWidget(self.url_entry)
        layout.addWidget(self.url_browse)

        # Output Folder
        self.folder_label = QLabel("Output Folder")
        self.folder_entry = QLineEdit()
        self.folder_browse = QPushButton("Browse")
        self.folder_browse.clicked.connect(self.browse_folder)
        layout.addWidget(self.folder_label)
        layout.addWidget(self.folder_entry)
        layout.addWidget(self.folder_browse)

        # Buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_download)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_download)
        self.resume_btn = QPushButton("Resume")
        self.resume_btn.clicked.connect(self.resume_download)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_download)

        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.resume_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # Overall progress bar
        self.overall_progress = QProgressBar()
        self.overall_progress.setValue(0)
        layout.addWidget(QLabel("Overall Progress"))
        layout.addWidget(self.overall_progress)

        # Scrollable song list
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.song_container = QWidget()
        self.song_layout = QVBoxLayout()
        self.song_container.setLayout(self.song_layout)
        self.scroll.setWidget(self.song_container)
        layout.addWidget(self.scroll)

        self.setLayout(layout)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select URL List", "", "Text Files (*.txt)")
        if file_path:
            self.url_entry.setText(file_path)

    def browse_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder_path:
            self.folder_entry.setText(folder_path)

    def start_download(self):
        txt_file = self.url_entry.text()
        output_folder = self.folder_entry.text()
        if not txt_file or not output_folder:
            QMessageBox.critical(self, "Error", "Please select both a URL list and output folder.")
            return

        with open(txt_file, "r") as f:
            urls = [line.strip() for line in f if line.strip()]

        if not urls:
            QMessageBox.warning(self, "Warning", "No URLs found in the file.")
            return

        # Clear previous song widgets
        for i in reversed(range(self.song_layout.count())):
            widget = self.song_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
        self.song_widgets = {}

        # Create widgets for each song
        for url in urls:
            title = url.split("/")[-1][:30]
            song_widget = SongWidget(title)
            self.song_layout.addWidget(song_widget)
            self.song_widgets[title] = song_widget

        self.thread = DownloadThread(urls, output_folder)
        self.thread.song_started.connect(lambda title: self.song_widgets[title].set_status("Downloading..."))
        self.thread.song_progress.connect(lambda title, p: self.song_widgets[title].set_progress(p))
        self.thread.song_finished.connect(lambda title, s: self.song_widgets[title].set_status(s))
        self.thread.overall_progress.connect(self.overall_progress.setValue)
        self.thread.start()

        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)

    def pause_download(self):
        if hasattr(self, "thread"):
            self.thread.pause()
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)

    def resume_download(self):
        if hasattr(self, "thread"):
            self.thread.resume()
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)

    def stop_download(self):
        if hasattr(self, "thread"):
            self.thread.stop()
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            QMessageBox.information(self, "Stopped", "Downloads have been stopped!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpotDLGUI()
    window.show()
    sys.exit(app.exec())
