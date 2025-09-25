import sys
import os
import requests
import tempfile
import atexit
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
import time

from bienvenida import WelcomeWindow
from respuesta_unica_4 import VideoPlayerWindow
from interaccion import InteractionWindow

class VideoDownloader(QThread):
    finished = pyqtSignal(dict)  

    def __init__(self, video_urls):
        super().__init__()
        self.video_urls = video_urls
        self.video_paths = {}

    def run(self):
        print("Starting silent download of videos...")
        for name, url in self.video_urls.items():
            try:
                print(f"Attempting to download video '{name}' from: {url}")
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                response = requests.get(url, stream=True)
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                self.video_paths[name] = temp_file.name
                temp_file.close()
                print(f"Video '{name}' downloaded to: {self.video_paths[name]}")
                atexit.register(os.unlink, self.video_paths[name])
            except requests.exceptions.HTTPError as err:
                print(f"HTTP Error for '{name}': {err}")
                self.video_paths[name] = None
            except Exception as e:
                print(f"Other Error for '{name}': {e}")
                self.video_paths[name] = None
        print("All downloads complete. Emitting finished signal.")
        self.finished.emit(self.video_paths)

class ApplicationManager:

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.video_paths = {}
        self.current_window = None
        self.video_urls = {
            'welcome': 'https://www.googleapis.com/drive/v3/files/1wPu1sCICiGd0vlSgCpNiYffaM_yEtx4K?alt=media&key=AIzaSyAWW-xLcA9ZMiFZLUyHODYT9KMKTUf7RiU',
            'player': 'https://www.googleapis.com/drive/v3/files/1X913T6IvBezORm7lXkyMVDfygKHh2aty?alt=media&key=AIzaSyAWW-xLcA9ZMiFZLUyHODYT9KMKTUf7RiU',
            'interaction': 'https://www.googleapis.com/drive/v3/files/1WetNlQgjLCpBz6ATuazyi8QkJNufReub?alt=media&key=AIzaSyAWW-xLcA9ZMiFZLUyHODYT9KMKTUf7RiU'
        }
        self.start_download()

    def start_download(self):
        self.downloader_thread = VideoDownloader(self.video_urls)
        self.downloader_thread.finished.connect(self.on_download_finished)
        self.downloader_thread.start()

    def on_download_finished(self, video_paths):
        self.video_paths = video_paths
        self.show_welcome_screen()

    def show_welcome_screen(self):
        video_path = self.video_paths.get('welcome')
        self.current_window = WelcomeWindow(video_path)
        self.current_window.video_finished.connect(self.show_video_player_screen)
        self.current_window.show()

    def show_video_player_screen(self):
        print("Transición a la pantalla del video.")
        video_path = self.video_paths.get('player')
        new_window = VideoPlayerWindow(video_path)
        new_window.transition_requested.connect(self.show_interaction_screen)
        new_window.show()

        if self.current_window:
            old_window = self.current_window
            self.current_window = new_window
            QTimer.singleShot(0, old_window.close)
        else:
            self.current_window = new_window

    def show_interaction_screen(self):
        print("Transición a la pantalla de interacción.")
        video_path = self.video_paths.get('interaction')
        new_window = InteractionWindow(video_path)
        new_window.show()

        if self.current_window:
            old_window = self.current_window
            self.current_window = new_window
            QTimer.singleShot(0, old_window.close)
        else:
            self.current_window = new_window

    def run(self):
        sys.exit(self.app.exec_())

if __name__ == '__main__':
    manager = ApplicationManager()
    manager.run()
