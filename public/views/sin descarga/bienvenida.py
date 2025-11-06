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

class HiloVideo(QThread):
    # Señal para actualizar la imagen (QPixmap)
    senial_cambio_pixmap = pyqtSignal(QPixmap)
    terminado = pyqtSignal()
    
    def __init__(self, cap):
        super().__init__()
        self._bandera_ejecucion = True
        self.captura = cap
        # Obtener el FPS (Frames Por Segundo) del video
        self.fps = self.captura.get(cv2.CAP_PROP_FPS)

    def run(self):
        while self._bandera_ejecucion:
            tiempo_inicio = time.time()
            # Leer el siguiente frame
            ret, frame = self.captura.read()
            if ret:
                # Procesamiento del frame (volteo, conversión de color)
                frame = cv2.flip(frame, 1)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                alto, ancho, canales = frame_rgb.shape
                bytes_por_linea = canales * ancho
                # Crear QImage y emitir QPixmap
                imagen_qt = QImage(frame_rgb.data, ancho, alto, bytes_por_linea, QImage.Format_RGB888)
                self.senial_cambio_pixmap.emit(QPixmap.fromImage(imagen_qt))

                # Control de velocidad de reproducción (sincronización con el FPS)
                tiempo_transcurrido = time.time() - tiempo_inicio
                tiempo_espera = (1.0 / self.fps) - tiempo_transcurrido if self.fps > 0 else 0
                if tiempo_espera > 0:
                    time.sleep(tiempo_espera)
            else:
                # El video terminó
                self._bandera_ejecucion = False
        self.terminado.emit()

    def parar(self):
        self._bandera_ejecucion = False
        self.wait()


class VentanaBienvenida(QMainWindow):
    redimensionado = pyqtSignal()
    video_terminado = pyqtSignal()

    def __init__(self, ruta_video):
        super().__init__()
        self.setWindowTitle("Ventana de Bienvenida")
        self.setWindowIcon(QIcon())
        
        self.ruta_video = ruta_video
        self.captura = None
        self.tiempo_inicio_reproduccion = None
        
        self.iniciar_IU()
        self.iniciar_video()
    
    def iniciar_IU(self):
        geometria_pantalla = QDesktopWidget().screenGeometry()
        self.ancho_pantalla = geometria_pantalla.width()
        self.alto_pantalla = geometria_pantalla.height()
        self.alto_barra = int(self.alto_pantalla * 0.1)
        self.setGeometry(0, 0, self.ancho_pantalla, self.alto_pantalla)
        
        self.widget_central = QWidget(self)
        self.setCentralWidget(self.widget_central)
        
        # Barra Superior
        self.barra_superior = QFrame(self.widget_central)
        self.barra_superior.setStyleSheet("background-color: #1881d7;")
        self.etiqueta_titulo = QLabel("TT 2025-B004", self.barra_superior)
        self.etiqueta_titulo.setAlignment(Qt.AlignCenter)
        self.etiqueta_titulo.setStyleSheet("color: white;")
        fuente = QFont("Arial", 20, QFont.Bold, italic=True)
        self.etiqueta_titulo.setFont(fuente)
        
        # Fondo
        self.etiqueta_fondo = QLabel(self.widget_central)
        self.etiqueta_fondo.setScaledContents(True)
        self.etiqueta_fondo.lower()
        
        # Recuadro del Video
        self.recuadro_video = QFrame(self.widget_central)
        self.recuadro_video.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 10px solid #F3D05C;
                border-radius: 20px;
            }
        """)
        self.etiqueta_video = QLabel(self.recuadro_video)
        self.etiqueta_video.setAlignment(Qt.AlignCenter)

        # Contenedor de Texto
        self.contenedor_texto = QWidget(self.widget_central)
        self.disposicion_texto = QVBoxLayout(self.contenedor_texto)
        self.disposicion_texto.setAlignment(Qt.AlignCenter)

        self.texto_titulo = QLabel("¡HOLA, BIENVENIDO!", self.contenedor_texto)
        self.texto_titulo.setWordWrap(True)
        self.texto_titulo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.texto_hola = QLabel("SOMOS UN SISTEMA DE APOYO PARA PERSONAS SORDAS.", self.contenedor_texto)
        self.texto_hola.setWordWrap(True)
        self.texto_hola.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.texto_bienvenida = QLabel("POR FAVOR, COLOCATE EN EL ÁREA DESIGNADA.", self.contenedor_texto)
        self.texto_bienvenida.setWordWrap(True)
        self.texto_bienvenida.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        for etiqueta in [self.texto_titulo, self.texto_hola, self.texto_bienvenida]:
            etiqueta.setStyleSheet("color: black;")
            etiqueta.setAlignment(Qt.AlignCenter)
            etiqueta.setFont(QFont("Segoe UI", 30, QFont.Bold))
            self.disposicion_texto.addWidget(etiqueta)

        self.contenedor_texto.setMinimumWidth(int(self.ancho_pantalla * 0.40))
        self.contenedor_texto.setMinimumHeight(int(self.alto_pantalla * 0.45))

        self.redimensionado.connect(self.actualizar_disposicion)
        self.actualizar_disposicion()

    def resizeEvent(self, evento):
        self.redimensionado.emit()
        super().resizeEvent(evento)
    
    def actualizar_disposicion(self):
        ancho = self.width()
        alto = self.height()
        alto_barra = int(alto * 0.1)
        
        self.barra_superior.setGeometry(0, 0, ancho, alto_barra)
        self.etiqueta_titulo.setGeometry(0, 0, ancho, alto_barra)
        
        directorio_base = Path(__file__).parent if '__file__' in globals() else Path.cwd()
        # Asegura que la ruta a 'fondo2.png' sea correcta según tu estructura de archivos
        ruta_imagen = directorio_base.parent.parent.parent / 'public' / 'images' / 'fondo2.png' 
        try:
            imagen_fondo_original = QPixmap(str(ruta_imagen))
            if not imagen_fondo_original.isNull():
                imagen_fondo_escalada = imagen_fondo_original.scaled(ancho, alto - alto_barra, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                self.etiqueta_fondo.setPixmap(imagen_fondo_escalada)
                self.etiqueta_fondo.setGeometry(0, alto_barra, ancho, alto - alto_barra)
                self.etiqueta_fondo.lower()
            else:
                 print("Error: QPixmap es nula (imagen no cargada).")
        except Exception as e:
            print(f"Error al cargar imagen de fondo: {e}")
        
        ancho_video = int(ancho * 0.3)
        alto_video = int(alto * 0.7)
        pos_x_video = int(ancho * 0.15)
        pos_y_video = int(alto * 0.20)
        self.recuadro_video.setGeometry(pos_x_video, pos_y_video, ancho_video, alto_video)
        self.etiqueta_video.setGeometry(10, 10, ancho_video - 20, alto_video - 20)

        ancho_texto = int(ancho * 0.40)
        pos_x_texto = int(ancho * 0.55)
        pos_y_texto = pos_y_video
        
        self.contenedor_texto.setGeometry(pos_x_texto, pos_y_texto, ancho_texto, int(alto * 0.5))

    def iniciar_video(self):
        if not self.ruta_video:
            self.etiqueta_video.setText("Error al cargar el video")
            self.video_terminado.emit()
            return
            
        self.captura = cv2.VideoCapture(self.ruta_video)
        
        if not self.captura.isOpened():
            self.etiqueta_video.setText("Error al abrir el video")
            self.video_terminado.emit()
            return
        
        # --- Medición: Duración Nominal del Video ---
        fps = self.captura.get(cv2.CAP_PROP_FPS)
        total_frames = self.captura.get(cv2.CAP_PROP_FRAME_COUNT)
        if fps > 0 and total_frames > 0:
            duracion_seg = total_frames / fps
            minutos = int(duracion_seg // 60)
            segundos = int(duracion_seg % 60)
            print(f"Duración de video de bienvenida: {minutos:02d}:{segundos:02d} ({duracion_seg:.2f} sec)")
            print(f"FPS: {fps}")
        else:
            print("Duración: No disponible (típico en streaming)")
        # ---------------------------------------------

        self.tiempo_inicio_reproduccion = time.time()
        self.hilo_video = HiloVideo(self.captura)
        self.hilo_video.senial_cambio_pixmap.connect(self.actualizar_imagen)
        self.hilo_video.terminado.connect(self.finalizar_reproduccion)
        self.hilo_video.start()

    def actualizar_imagen(self, imagen):
        self.etiqueta_video.setPixmap(imagen.scaled(self.etiqueta_video.width(), self.etiqueta_video.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def finalizar_reproduccion(self):
        # --- Medición: Tiempo Real de Reproducción ---
        tiempo_total_reproduccion = time.time() - self.tiempo_inicio_reproduccion
        print(f"Tiempo real de reproducción: {tiempo_total_reproduccion:.4f} segundos.")
        # ----------------------------------------------
        self.video_terminado.emit()

    def closeEvent(self, evento):
        if hasattr(self, 'hilo_video'):
            self.hilo_video.parar()
        if self.captura:
            self.captura.release()
        evento.accept()