import sys
import os
import cv2
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QLabel, QDesktopWidget, QWidget
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon
from PyQt5.QtCore import QSize, QTimer, Qt, pyqtSignal, QRect, QThread
import time

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QPixmap)
    finished = pyqtSignal()
    
    def __init__(self, cap, loop=False):
        super().__init__()
        self._run_flag = True
        self.cap = cap
        self.loop = loop
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

    def run(self):
        while self._run_flag:
            start_time = time.time()
            ret, frame = self.cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame_rgb.shape
                bytes_per_line = ch * w
                qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.change_pixmap_signal.emit(QPixmap.fromImage(qt_image))
                elapsed_time = time.time() - start_time
                sleep_time = (1.0 / self.fps) - elapsed_time
                if sleep_time > 0:
                    time.sleep(sleep_time)
            elif self.loop:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Loop video
            else:
                self._run_flag = False
        self.finished.emit()

    def stop(self):
        self._run_flag = False
        self.wait()

class InteractionWindow(QMainWindow):
    resized = pyqtSignal()
    
    def __init__(self, video_path):
        super().__init__()
        self.setWindowTitle("Ventana de Interacción")
        self.setWindowIcon(QIcon())
        
        self.cap_camera = cv2.VideoCapture(0)
        
        self.video_path = video_path
        self.cap_drive_video = None
        self.drive_video_thread = None
        self.initUI()
        self.timer_camera = QTimer(self)
        self.timer_camera.timeout.connect(self.update_camera_frame)
        self.timer_camera.start(10)
        self.start_drive_video()

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
        self.recuadro_video1 = QFrame(self.central_widget)
        self.recuadro_video1.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 10px solid #F3D05C;
                border-radius: 10px;
            }
        """)
        self.video_label1 = QLabel(self.recuadro_video1)
        self.video_label1.setAlignment(Qt.AlignCenter)
        self.recuadro_video2 = QFrame(self.central_widget)
        self.recuadro_video2.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 10px solid #F3D05C;
                border-radius: 10px;
            }
        """)
        self.video_label2 = QLabel(self.recuadro_video2)
        self.video_label2.setAlignment(Qt.AlignCenter)
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
        
        margen_izq = int(w * 0.05)
        margen_der = int(w * 0.05)
        separacion = int(w * 0.05)
        area_util_ancho = w - margen_izq - margen_der
        
        recuadro_width = (area_util_ancho - separacion) // 2
        recuadro_height = int(recuadro_width * 0.75)
        
        video_y = int(h * 0.25)
        video1_x = margen_izq
        video2_x = margen_izq + recuadro_width + separacion
        
        self.recuadro_video1.setGeometry(video1_x, video_y, recuadro_width, recuadro_height)
        self.recuadro_video2.setGeometry(video2_x, video_y, recuadro_width, recuadro_height)
        self.video_label1.setGeometry(10, 10, recuadro_width - 20, recuadro_height - 20)
        self.video_label2.setGeometry(10, 10, recuadro_width - 20, recuadro_height - 20)

    def update_camera_frame(self):
        if not self.cap_camera.isOpened():
            return
            
        ret, frame = self.cap_camera.read()
        if ret:
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(self.video_label1.width(), self.video_label1.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.video_label1.setPixmap(scaled_pixmap)

    def start_drive_video(self):
        if not self.video_path:
            self.video_label2.setText("Error al cargar el video")
            return
            
        self.cap_drive_video = cv2.VideoCapture(self.video_path)
        
        if not self.cap_drive_video.isOpened():
            self.video_label2.setText("Error al abrir el video")
            return

        # --- Cálculo e impresión de la duración del video ---
        fps = self.cap_drive_video.get(cv2.CAP_PROP_FPS)
        total_frames = self.cap_drive_video.get(cv2.CAP_PROP_FRAME_COUNT)
        if fps > 0 and total_frames > 0:
            duration_sec = total_frames / fps
            minutes = int(duration_sec // 60)
            seconds = int(duration_sec % 60)
            print(f"Video 'interaction' (loop) duration: {minutes:02d}:{seconds:02d} ({duration_sec:.2f} sec)")
        else:
            print("Video 'interaction' (loop) duration: Not available (FPS or Frame Count is zero).")
        # ----------------------------------------------------

        self.drive_video_thread = VideoThread(self.cap_drive_video, loop=True)
        self.drive_video_thread.change_pixmap_signal.connect(self.update_drive_video_image)
        self.drive_video_thread.start()

    def update_drive_video_image(self, image):
        self.video_label2.setPixmap(image.scaled(self.video_label2.width(), self.video_label2.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def closeEvent(self, event):
        if self.cap_camera:
            self.cap_camera.release()
        if self.drive_video_thread:
            self.drive_video_thread.stop()
        if self.cap_drive_video:
            self.cap_drive_video.release()
        self.timer_camera.stop()
        event.accept()