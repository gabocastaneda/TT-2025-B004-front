import sys
import os
import cv2
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFrame, QLabel, QDesktopWidget, QWidget,
    QVBoxLayout, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon
from PyQt5.QtCore import QSize, QTimer, Qt, pyqtSignal, QRect, QThread
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
            if ret:
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
            else:
                self._run_flag = False
        self.finished.emit()

    def stop(self):
        self._run_flag = False
        self.wait()


class WelcomeWindow(QMainWindow):
    resized = pyqtSignal()
    video_finished = pyqtSignal()

    def __init__(self, video_path):
        super().__init__()
        self.setWindowTitle("Ventana de Bienvenida")
        self.setWindowIcon(QIcon())
        
        self.video_path = video_path
        self.cap = None
        
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
        
        # Top Bar
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
                border-radius: 20px;
            }
        """)
        self.video_label = QLabel(self.recuadro_video)
        self.video_label.setAlignment(Qt.AlignCenter)

        self.texto_container = QWidget(self.central_widget)
        self.texto_layout = QVBoxLayout(self.texto_container)
        self.texto_layout.setAlignment(Qt.AlignCenter)

        self.titulo_texto = QLabel("¡HOLA, BIENVENIDO!", self.texto_container)
        self.titulo_texto.setWordWrap(True)
        self.titulo_texto.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.hola_texto = QLabel("SOMOS UN SISTEMA DE APOYO PARA PERSONAS SORDAS.", self.texto_container)
        self.hola_texto.setWordWrap(True)
        self.hola_texto.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.bienvenida_texto = QLabel("POR FAVOR, COLOCATE EN EL ÁREA DESIGNADA.", self.texto_container)
        self.bienvenida_texto.setWordWrap(True)
        self.bienvenida_texto.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        for label in [self.titulo_texto, self.hola_texto, self.bienvenida_texto]:
            label.setStyleSheet("color: black;")
            label.setAlignment(Qt.AlignCenter)
            label.setFont(QFont("Segoe UI", 30, QFont.Bold))
            self.texto_layout.addWidget(label)

        self.texto_container.setMinimumWidth(int(self.screen_width * 0.40))
        self.texto_container.setMinimumHeight(int(self.screen_height * 0.45))

        self.resized.connect(self.update_layout)
        self.update_layout()

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
        
        video_width = int(w * 0.3)
        video_height = int(h * 0.7)
        video_x = int(w * 0.15)
        video_y = int(h * 0.20)
        self.recuadro_video.setGeometry(video_x, video_y, video_width, video_height)
        self.video_label.setGeometry(10, 10, video_width - 20, video_height - 20)

        texto_width = int(w * 0.40)
        texto_x = int(w * 0.55)
        texto_y = video_y
        
        self.texto_container.setGeometry(texto_x, texto_y, texto_width, int(h * 0.5))

    def start_video(self):
        if not self.video_path:
            self.video_label.setText("Error al cargar el video")
            self.video_finished.emit()
            return
            
        self.cap = cv2.VideoCapture(self.video_path)
        
        if not self.cap.isOpened():
            self.video_label.setText("Error al abrir el video")
            self.video_finished.emit()
            return
        
        # --- Cálculo e impresión de la duración del video ---
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        total_frames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        if fps > 0 and total_frames > 0:
            duration_sec = total_frames / fps
            minutes = int(duration_sec // 60)
            seconds = int(duration_sec % 60)
            print(f"Video 'welcome' duration: {minutes:02d}:{seconds:02d} ({duration_sec:.2f} sec)")
        else:
            print("Video 'welcome' duration: Not available (FPS or Frame Count is zero).")
        # ----------------------------------------------------

        self.video_thread = VideoThread(self.cap)
        self.video_thread.change_pixmap_signal.connect(self.update_image)
        self.video_thread.finished.connect(self.end_playback)
        self.video_thread.start()

    def update_image(self, image):
        self.video_label.setPixmap(image.scaled(self.video_label.width(), self.video_label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def end_playback(self):
        print("Video playback finished for Welcome Screen.")
        self.video_finished.emit()

    def closeEvent(self, event):
        if hasattr(self, 'video_thread'):
            self.video_thread.stop()
        if self.cap:
            self.cap.release()
        event.accept()