import sys
import os
import cv2
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QLabel, QDesktopWidget, QWidget
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon, QColor
from PyQt5.QtCore import QSize, QTimer, Qt, pyqtSignal, QRect, QThread, QMetaObject
import time

from hilo_video import HiloVideo

class VentanaReproductorVideo(QMainWindow):
    redimensionada = pyqtSignal()
    transicion_solicitada = pyqtSignal()

    def __init__(self, ruta_video):
        super().__init__()
        self.setWindowTitle("Ventana de Interacción")
        self.setWindowIcon(QIcon())
        self.ruta_video = ruta_video
        self.cap = None
        self.tiempo_inicio_reproduccion = None
        self.inicializar_ui()
        self.iniciar_video()

    def inicializar_ui(self):
        geometria_pantalla = QDesktopWidget().screenGeometry()
        self.ancho_pantalla = geometria_pantalla.width()
        self.alto_pantalla = geometria_pantalla.height()
        self.alto_barra = int(self.alto_pantalla * 0.1)
        self.setGeometry(0, 0, self.ancho_pantalla, self.alto_pantalla)
        self.widget_central = QWidget(self)
        self.setCentralWidget(self.widget_central)
        self.barra_superior = QFrame(self.widget_central)
        self.barra_superior.setStyleSheet("background-color: #1881d7;")
        self.etiqueta_titulo = QLabel("TT 2025-B004", self.barra_superior)
        self.etiqueta_titulo.setAlignment(Qt.AlignCenter)
        self.etiqueta_titulo.setStyleSheet("color: white;")
        fuente = QFont("Arial", 20, QFont.Bold, italic=True)
        self.etiqueta_titulo.setFont(fuente)
        self.etiqueta_fondo = QLabel(self.widget_central)
        self.etiqueta_fondo.setScaledContents(True)
        self.etiqueta_fondo.lower()
        self.recuadro_video = QFrame(self.widget_central)
        self.recuadro_video.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 10px solid #F3D05C;
                border-radius: 10px;
            }
        """)

        self.etiqueta_video = QLabel(self.recuadro_video)
        self.etiqueta_video.setAlignment(Qt.AlignCenter)
        self.etiqueta_video.setStyleSheet("color: black; font-size: 20px; font-weight: bold;")
        self.etiqueta_video.setText("Cargando video")
        self.redimensionada.connect(self.actualizar_disposicion)


    def resizeEvent(self, evento):
        self.redimensionada.emit()
        super().resizeEvent(evento)

    def actualizar_disposicion(self):
        w = self.width()
        h = self.height()
        alto_barra = int(h * 0.1)

        self.barra_superior.setGeometry(0, 0, w, alto_barra)
        self.etiqueta_titulo.setGeometry(0, 0, w, alto_barra)

        dir_base = Path(__file__).parent if '__file__' in globals() else Path.cwd()
        ruta_imagen = dir_base.parent.parent.parent / 'public' / 'images' / 'fondo2.png'

        try:
            imagen_fondo_original = QPixmap(str(ruta_imagen))
            if not imagen_fondo_original.isNull():
                imagen_fondo_escalada = imagen_fondo_original.scaled(w, h - alto_barra, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                self.etiqueta_fondo.setPixmap(imagen_fondo_escalada)
                self.etiqueta_fondo.setGeometry(0, alto_barra, w, h - alto_barra)
                self.etiqueta_fondo.lower()
        except Exception as e:
            print(f"Error cargando imagen de fondo: {e}")

        margen_izquierdo = int(w * 0.05)
        margen_derecho = int(w * 0.05)
        separacion = int(w * 0.05)
        ancho_area_util = w - margen_izquierdo - margen_derecho
        ancho_recuadro = (ancho_area_util - separacion) // 2
        alto_recuadro = int(ancho_recuadro * 0.75)
        y_video = int(h * 0.25)
        x_video = (w - ancho_recuadro) // 2

        self.recuadro_video.setGeometry(x_video, y_video, ancho_recuadro, alto_recuadro)
        self.etiqueta_video.setGeometry(10, 10, ancho_recuadro - 20, alto_recuadro - 20)
        self.widget_central.setGeometry(0, 0, w, h)

    def iniciar_video(self):
        if not self.ruta_video:
            self.etiqueta_video.setText("Error: Ruta de video no especificada.")
            self.transicion_solicitada.emit()
            return

        self.cap = cv2.VideoCapture(self.ruta_video)
        
        if not self.cap.isOpened():
            self.etiqueta_video.setText("Error al abrir el video.")
            self.transicion_solicitada.emit()
            return
            
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        ancho = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        alto = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fotogramas_totales = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        
        print("Respuesta única")
        if fps > 0 and fotogramas_totales > 0:
            duracion_seg = fotogramas_totales / fps
            minutos = int(duracion_seg // 60)
            segundos = int(duracion_seg % 60)
            print(f"Duración nominal: {minutos:02d}:{segundos:02d} ({duracion_seg:.2f} seg)")
            print(f"FPS: {fps:.2f}")
            print(f"Calidad: {ancho}x{alto}")
        else:
            print("Propiedades: No disponibles")
        # --------------------------------------------------

        self.tiempo_inicio_reproduccion = time.time()
        self.hilo_video = HiloVideo(self.cap)
        self.hilo_video.senal_cambio_pixmap.connect(self.actualizar_imagen)
        self.hilo_video.terminado.connect(self.finalizar_reproduccion, Qt.QueuedConnection)
        self.hilo_video.start()

    def actualizar_imagen(self, imagen):
        self.etiqueta_video.setPixmap(imagen.scaled(self.etiqueta_video.width(), self.etiqueta_video.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def finalizar_reproduccion(self):
        tiempo_fin = time.time()
        if hasattr(self, 'hilo_video'):
            self.hilo_video.stop()
            
        if self.tiempo_inicio_reproduccion:
            tiempo_total_reproduccion = tiempo_fin - self.tiempo_inicio_reproduccion
            print(f"Tiempo de reproducción real: {tiempo_total_reproduccion:.2f} segundos.")

        self.transicion_solicitada.emit()

    def closeEvent(self, evento):
        if hasattr(self, 'hilo_video'):
            self.hilo_video.stop()
        if self.cap:
            self.cap.release()
        evento.accept()