import sys
import os
import cv2
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QLabel, QDesktopWidget, QWidget
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon, QColor
from PyQt5.QtCore import QSize, QTimer, Qt, pyqtSignal, QRect, QThread, QMetaObject
import time

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QPixmap)
    finished = pyqtSignal()

    def __init__(self, cap):
        super().__init__()
        self._run_flag = True
        self.cap = cap
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

    def run(self):
        while self._run_flag:
            start_time = time.time()
            ret, frame = self.cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.change_pixmap_signal.emit(QPixmap.fromImage(qt_image))
            elapsed_time = time.time() - start_time
            sleep_time = (1.0 / self.fps) - elapsed_time
            if sleep_time > 0:
                time.sleep(sleep_time)
        self.finished.emit()

    def stop(self):
        self._run_flag = False
        self.wait()

class VideoPlayerWindow(QMainWindow):
    resized = pyqtSignal()
    transition_requested = pyqtSignal()

    def __init__(self, video_path):
        super().__init__()
        self.setWindowTitle("Ventana de Interacción")
        self.setWindowIcon(QIcon())
        self.video_path = video_path
        self.cap = None
        self.start_time = None
        self.initUI()
        self.start_video()

    def initUI(self):
        screen_geo = QDesktopWidget().screenGeometry()
        self.screen_width = screen_geo.width()
        self.screen_height = screen_geo.height()
        self.barra_alto = int(self.screen_height * 0.1)
        self.setGeometry(0, 0, self.screen_width, self.screen_height)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.barra_superior = QFrame(self.central_widget)
        self.barra_superior.setStyleSheet("background-color: #1881d7;")

        self.titulo_label = QLabel("TT 2025-B004", self.barra_superior)
        self.titulo_label.setAlignment(Qt.AlignCenter)
        self.titulo_label.setStyleSheet("color: white;")
        font = QFont("Arial", 20, QFont.Bold, italic=True)
        self.titulo_label.setFont(font)

        self.fondo_label = QLabel(self.central_widget)
        self.fondo_label.setScaledContents(True)
        self.fondo_label.lower()

        self.recuadro_video = QFrame(self.central_widget)
        self.recuadro_video.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 10px solid #F3D05C;
                border-radius: 10px;
            }
        """)

        self.video_label = QLabel(self.recuadro_video)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("color: black; font-size: 20px; font-weight: bold;")
        self.video_label.setText("Cargando video...")

        self.resized.connect(self.update_layout)

    def resizeEvent(self, event):
        self.resized.emit()
        super().resizeEvent(event)

    def update_layout(self):
        w = self.width()
        h = self.height()
        barra_h = int(h * 0.1)

        self.barra_superior.setGeometry(0, 0, w, barra_h)
        self.titulo_label.setGeometry(0, 0, w, barra_h)

        base_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
        image_path = base_dir.parent / 'images' / 'fondo2.png'

        try:
            bg_image_original = QPixmap(str(image_path))
            if not bg_image_original.isNull():
                bg_img_scaled = bg_image_original.scaled(w, h - barra_h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                self.fondo_label.setPixmap(bg_img_scaled)
                self.fondo_label.setGeometry(0, barra_h, w, h - barra_h)
                self.fondo_label.lower()
        except Exception as e:
            print(f"Error loading background image: {e}")

        margen_izq = int(w * 0.05)
        margen_der = int(w * 0.05)
        separacion = int(w * 0.05)
        area_util_ancho = w - margen_izq - margen_der
        recuadro_width = (area_util_ancho - separacion) // 2
        recuadro_height = int(recuadro_width * 0.75)
        video_y = int(h * 0.25)
        video_x = (w - recuadro_width) // 2

        self.recuadro_video.setGeometry(video_x, video_y, recuadro_width, recuadro_height)
        self.video_label.setGeometry(10, 10, recuadro_width - 20, recuadro_height - 20)
        self.central_widget.setGeometry(0, 0, w, h)

        if hasattr(self, 'video_thread'):
            self.video_thread.video_size = (self.video_label.width(), self.video_label.height())

    def start_video(self):
        if not self.video_path:
            self.video_label.setText("Error al cargar el video")
            self.transition_requested.emit()
            return

        self.cap = cv2.VideoCapture(self.video_path)
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        total_frames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        if fps > 0:
            duration_sec = total_frames / fps
            minutes = int(duration_sec // 60)
            seconds = int(duration_sec % 60)
            print(f"Duración del video: {minutes:02d}:{seconds:02d}")
        else:
            print("Duración del video: No disponible")
        print(f"Detected FPS: {fps}")

        self.start_time = time.time()
        self.video_thread = VideoThread(self.cap)
        self.video_thread.change_pixmap_signal.connect(self.update_image)
        self.video_thread.finished.connect(self.end_playback, Qt.QueuedConnection)
        self.video_thread.start()

    def update_image(self, image):
        self.video_label.setPixmap(image.scaled(self.video_label.width(), self.video_label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def end_playback(self):
        end_time = time.time()
        total_playback_time = end_time - self.start_time
        print(f"Tiempo total de reproducción: {total_playback_time:.2f} segundos. Iniciando transición...")

        if hasattr(self, 'video_thread'):
            self.video_thread.stop()
        self.transition_requested.emit()

    def closeEvent(self, event):
        print("Cerrando ventana y liberando recursos de video...")
        if hasattr(self, 'video_thread'):
            self.video_thread.stop()
        if self.cap:
            self.cap.release()
        event.accept()
