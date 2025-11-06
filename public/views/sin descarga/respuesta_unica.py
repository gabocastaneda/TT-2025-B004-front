import sys
import os
import cv2
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QLabel, QDesktopWidget, QWidget
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon, QColor
from PyQt5.QtCore import QSize, QTimer, Qt, pyqtSignal, QRect, QThread, QMetaObject
import time

class HiloVideo(QThread):
    # Señal para actualizar la imagen (QPixmap)
    senial_cambio_pixmap = pyqtSignal(QPixmap)
    terminado = pyqtSignal()

    def __init__(self, captura):
        super().__init__()
        self._bandera_ejecucion = True
        self.captura = captura
        self.fps = self.captura.get(cv2.CAP_PROP_FPS)

    def run(self):
        while self._bandera_ejecucion:
            tiempo_inicio = time.time()
            ret, frame = self.captura.read()
            
            if not ret:
                break
                
            frame = cv2.flip(frame, 1) # Volteo horizontal (efecto espejo)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            alto, ancho, canales = frame_rgb.shape
            bytes_por_linea = canales * ancho
            
            # Crear QImage y emitir QPixmap
            imagen_qt = QImage(frame_rgb.data, ancho, alto, bytes_por_linea, QImage.Format_RGB888)
            self.senial_cambio_pixmap.emit(QPixmap.fromImage(imagen_qt))
            
            # Control de velocidad (sincronización con el FPS)
            tiempo_transcurrido = time.time() - tiempo_inicio
            tiempo_espera = (1.0 / self.fps) - tiempo_transcurrido if self.fps > 0 else 0
            if tiempo_espera > 0:
                time.sleep(tiempo_espera)
                
        self.terminado.emit()

    def parar(self):
        self._bandera_ejecucion = False
        self.wait()

class VentanaReproductorVideo(QMainWindow):
    redimensionado = pyqtSignal()
    solicitud_transicion = pyqtSignal()

    def __init__(self, ruta_video):
        super().__init__()
        self.setWindowTitle("Ventana de Respuesta Única")
        self.setWindowIcon(QIcon())
        
        self.ruta_video = ruta_video 
        self.captura = None
        self.tiempo_inicio_reproduccion = None 
        
        self.iniciar_IU()
        # Conectamos la señal de redimensionado a la actualización del layout
        self.redimensionado.connect(self.actualizar_disposicion)
        self.actualizar_disposicion()
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

        # Recuadro de Video
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
        self.etiqueta_video.setText("Cargando video...")

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
        ruta_imagen = directorio_base.parent.parent.parent / 'public' / 'images' / 'fondo2.png' 

        try:
            imagen_fondo_original = QPixmap(str(ruta_imagen))
            if not imagen_fondo_original.isNull():
                imagen_fondo_escalada = imagen_fondo_original.scaled(ancho, alto - alto_barra, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                self.etiqueta_fondo.setPixmap(imagen_fondo_escalada)
                self.etiqueta_fondo.setGeometry(0, alto_barra, ancho, alto - alto_barra)
                self.etiqueta_fondo.lower()
        except Exception as e:
            print(f"Error al cargar imagen de fondo: {e}")

        # Centrar el recuadro de video
        margen_izq = int(ancho * 0.05)
        margen_der = int(ancho * 0.05)
        separacion = int(ancho * 0.05)
        area_util_ancho = ancho - margen_izq - margen_der
        
        # El ancho del recuadro se calcula para un layout de 2 videos, pero aquí solo se usa 1,
        # así que simplificamos el tamaño para que se vea centrado y grande.
        ancho_recuadro = int(ancho * 0.70) # Un 70% del ancho
        alto_recuadro = int(ancho_recuadro * 0.5625) # Relación 16:9
        
        pos_y_video = int(alto * 0.20)
        pos_x_video = (ancho - ancho_recuadro) // 2

        self.recuadro_video.setGeometry(pos_x_video, pos_y_video, ancho_recuadro, alto_recuadro)
        self.etiqueta_video.setGeometry(10, 10, ancho_recuadro - 20, alto_recuadro - 20)
        self.widget_central.setGeometry(0, 0, ancho, alto)

    def iniciar_video(self):
        if not self.ruta_video:
            self.etiqueta_video.setText("Error al cargar el video")
            self.solicitud_transicion.emit()
            return

        self.captura = cv2.VideoCapture(self.ruta_video)
        
        if not self.captura.isOpened():
            self.etiqueta_video.setText("Error al abrir el video")
            self.solicitud_transicion.emit()
            return
            
        # --- Medición: Duración Nominal del Video ---
        fps = self.captura.get(cv2.CAP_PROP_FPS)
        total_frames = self.captura.get(cv2.CAP_PROP_FRAME_COUNT)
        
        if fps > 0 and total_frames > 0:
            duracion_seg = total_frames / fps
            minutos = int(duracion_seg // 60)
            segundos = int(duracion_seg % 60)
            print(f"Duración de video de respuesta única: {minutos:02d}:{segundos:02d} ({duracion_seg:.2f} sec)")
            print(f"FPS: {fps}")
        else:
            print("Duración: No disponible (típico en streaming)")
        # ---------------------------------------------

        self.tiempo_inicio_reproduccion = time.time()
        self.hilo_video = HiloVideo(self.captura)
        self.hilo_video.senial_cambio_pixmap.connect(self.actualizar_imagen)
        # Usamos Qt.QueuedConnection para asegurar que la señal se maneje en el hilo principal de PyQt
        self.hilo_video.terminado.connect(self.finalizar_reproduccion, Qt.QueuedConnection) 
        self.hilo_video.start()

    def actualizar_imagen(self, imagen):
        self.etiqueta_video.setPixmap(imagen.scaled(self.etiqueta_video.width(), self.etiqueta_video.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def finalizar_reproduccion(self):
        tiempo_fin = time.time()
        tiempo_total_reproduccion = tiempo_fin - self.tiempo_inicio_reproduccion
        print(f"Tiempo real de reproducción: {tiempo_total_reproduccion:.4f} segundos.")
        
        if hasattr(self, 'hilo_video'):
            self.hilo_video.parar()
            
        self.solicitud_transicion.emit()

    def closeEvent(self, evento):
        print("Cerrando ventana y liberando recursos de video...")
        if hasattr(self, 'hilo_video'):
            self.hilo_video.parar()
        if self.captura:
            self.captura.release()
        evento.accept()