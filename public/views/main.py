import sys
import os
import requests
import tempfile
import atexit
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer

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
        total_download_start_time = time.time()
        
        for name, url in self.video_urls.items():
            start_time = time.time()
            try:
                print(f"Attempting to download video '{name}'...")
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                response = requests.get(url, stream=True)
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                self.video_paths[name] = temp_file.name
                temp_file.close()
                end_time = time.time()
                download_time = end_time - start_time
                print(f"Video '{name}' downloaded successfully to: {self.video_paths[name]}")
                print(f"Time to download '{name}': {download_time:.4f} seconds.")
                atexit.register(os.unlink, self.video_paths[name])
            except requests.exceptions.HTTPError as err:
                print(f"HTTP Error for '{name}': {err}")
                self.video_paths[name] = None
            except Exception as e:
                print(f"Other Error for '{name}': {e}")
                self.video_paths[name] = None
                
        total_download_end_time = time.time()
        total_download_time = total_download_end_time - total_download_start_time
        print(f"\n--- Tiempo total de descarga: {total_download_time:.4f} seconds. ---\n")
        self.finished.emit(self.video_paths)

class ApplicationManager:

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app_start_time = time.time()  # Start time of the application
        self.video_paths = {}
        self.current_window = None
        self.last_transition_start = None
        self.video_urls = {
            'welcome': 'https://www.googleapis.com/drive/v3/files/1X913T6IvBezORm7lXkyMVDfygKHh2aty?alt=media&key=AIzaSyCPQezDLouT6Lwc0JHG6QpxWPrukz_2Jac',
            'player': 'https://www.googleapis.com/drive/v3/files/1X913T6IvBezORm7lXkyMVDfygKHh2aty?alt=media&key=AIzaSyCPQezDLouT6Lwc0JHG6QpxWPrukz_2Jac',
            'interaction': 'https://www.googleapis.com/drive/v3/files/1X913T6IvBezORm7lXkyMVDfygKHh2aty?alt=media&key=AIzaSyCPQezDLouT6Lwc0JHG6QpxWPrukz_2Jac'
        }
        self.start_download()

    def start_download(self):
        self.downloader_thread = VideoDownloader(self.video_urls)
        self.downloader_thread.finished.connect(self.on_download_finished)
        self.downloader_thread.start()

    def on_download_finished(self, video_paths):
        self.video_paths = video_paths
        total_startup_time = time.time() - self.app_start_time
        print(f"--- Tiempo total de descarga de videos e inicio de la aplicación: {total_startup_time:.4f} seconds. ---\n")
        
        # Inicia la primera transición y mide el tiempo
        self.last_transition_start = time.time() 
        self.show_welcome_screen()

    def show_welcome_screen(self):

        video_path = self.video_paths.get('welcome')
        self.current_window = WelcomeWindow(video_path)
        self.current_window.video_finished.connect(self.request_video_player_screen)
        self.current_window.show()

    def request_video_player_screen(self):
        self.show_video_player_screen()

    def show_video_player_screen(self):

        video_path = self.video_paths.get('player')
        new_window = VideoPlayerWindow(video_path)
        new_window.transition_requested.connect(self.request_interaction_screen)
        new_window.show()

        if self.current_window:
            old_window = self.current_window
            self.current_window = new_window
            QTimer.singleShot(0, old_window.close)
        else:
            self.current_window = new_window

    def request_interaction_screen(self):
        self.show_interaction_screen()

    def show_interaction_screen(self):
        print("Showing Interaction Screen (Final State).")
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