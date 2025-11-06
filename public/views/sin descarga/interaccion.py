import sys
import os
import cv2
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QLabel, QDesktopWidget, QWidget
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon
from PyQt5.QtCore import QSize, QTimer, Qt, pyqtSignal, QRect, QThread
import time

class HiloVideo(QThread):
    # Señal para actualizar la imagen (QPixmap)
    senial_cambio_pixmap = pyqtSignal(QPixmap)
    terminado = pyqtSignal()
    
    def __init__(self, captura, bucle=False):
        super().__init__()
        self._bandera_ejecucion = True
        self.captura = captura
        self.bucle = bucle
        # La obtención de FPS puede fallar con streaming, pero se mantiene la lógica de reproducción
        self.fps = self.captura.get(cv2.CAP_PROP_FPS) 

    def run(self):
        while self._bandera_ejecucion:
            tiempo_inicio = time.time()
            ret, frame = self.captura.read()
            if ret:
                # Procesamiento del frame
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
            elif self.bucle:
                # Si el video terminó y 'bucle' es True, reinicia al frame 0
                self.captura.set(cv2.CAP_PROP_POS_FRAMES, 0)
            else:
                # Si el video terminó y no debe repetirse
                self._bandera_ejecucion = False
        self.terminado.emit()

    def parar(self):
        self._bandera_ejecucion = False
        self.wait()

class VentanaInteraccion(QMainWindow):
    redimensionado = pyqtSignal()
    
    def __init__(self, ruta_video):
        super().__init__()
        self.setWindowTitle("Ventana de Interacción")
        self.setWindowIcon(QIcon())
        
        # Captura de la cámara web (índice 0)
        self.captura_camara = cv2.VideoCapture(0)
        
        self.ruta_video = ruta_video 
        self.captura_video_drive = None
        self.hilo_video_drive = None
        
        self.iniciar_IU()
        
        # Temporizador para la cámara web (ejecución periódica en el hilo principal)
        self.temporizador_camara = QTimer(self)
        self.temporizador_camara.timeout.connect(self.actualizar_frame_camara)
        self.temporizador_camara.start(10)
        
        self.iniciar_video_drive()

    def iniciar_IU(self):
        geometria_pantalla = QDesktopWidget().screenGeometry()
        self.ancho_pantalla = geometria_pantalla.width()
        self.alto_pantalla = geometria_pantalla.height()
        self.alto_barra = int(self.alto_pantalla * 0.1)
        self.setGeometry(0, 0, self.ancho_pantalla, self.alto_pantalla)
        
        self.widget_central = QWidget(self)
        self.setCentralWidget(self.widget_central)
        
        # Elementos de la interfaz (traducción de nombres)
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
        
        # Primer recuadro de video (Cámara)
        self.recuadro_video1 = QFrame(self.widget_central)
        self.recuadro_video1.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 10px solid #F3D05C;
                border-radius: 10px;
            }
        """)
        self.etiqueta_video1 = QLabel(self.recuadro_video1)
        self.etiqueta_video1.setAlignment(Qt.AlignCenter)
        
        # Segundo recuadro de video (Drive/Cloud)
        self.recuadro_video2 = QFrame(self.widget_central)
        self.recuadro_video2.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 10px solid #F3D05C;
                border-radius: 10px;
            }
        """)
        self.etiqueta_video2 = QLabel(self.recuadro_video2)
        self.etiqueta_video2.setAlignment(Qt.AlignCenter)
        
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
        
        # Cálculo de las posiciones y tamaños de los dos recuadros de video
        margen_izq = int(ancho * 0.05)
        margen_der = int(ancho * 0.05)
        separacion = int(ancho * 0.05)
        area_util_ancho = ancho - margen_izq - margen_der
        
        ancho_recuadro = (area_util_ancho - separacion) // 2
        alto_recuadro = int(ancho_recuadro * 0.75)
        
        pos_y_video = int(alto * 0.25)
        pos_x_video1 = margen_izq
        pos_x_video2 = margen_izq + ancho_recuadro + separacion
        
        self.recuadro_video1.setGeometry(pos_x_video1, pos_y_video, ancho_recuadro, alto_recuadro)
        self.recuadro_video2.setGeometry(pos_x_video2, pos_y_video, ancho_recuadro, alto_recuadro)
        self.etiqueta_video1.setGeometry(10, 10, ancho_recuadro - 20, alto_recuadro - 20)
        self.etiqueta_video2.setGeometry(10, 10, ancho_recuadro - 20, alto_recuadro - 20)

    def actualizar_frame_camara(self):
        if not self.captura_camara.isOpened():
            return
            
        ret, frame = self.captura_camara.read()
        if ret:
            # Voltear el frame para una vista de "espejo"
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            alto, ancho, canales = frame_rgb.shape
            bytes_por_linea = canales * ancho
            imagen_qt = QImage(frame_rgb.data, ancho, alto, bytes_por_linea, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(imagen_qt)
            
            # Escalar y mostrar en la etiqueta 1 (cámara)
            pixmap_escalado = pixmap.scaled(self.etiqueta_video1.width(), self.etiqueta_video1.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.etiqueta_video1.setPixmap(pixmap_escalado)

    def iniciar_video_drive(self):
        if not self.ruta_video:
            self.etiqueta_video2.setText("Error al cargar el video de Drive")
            return
            
        self.captura_video_drive = cv2.VideoCapture(self.ruta_video)
        
        if not self.captura_video_drive.isOpened():
            self.etiqueta_video2.setText("Error al abrir el video de Drive")
            return

        # --- Medición: Duración Nominal del Video ---
        fps = self.captura_video_drive.get(cv2.CAP_PROP_FPS)
        total_frames = self.captura_video_drive.get(cv2.CAP_PROP_FRAME_COUNT)
        if fps > 0 and total_frames > 0:
            duracion_seg = total_frames / fps
            minutos = int(duracion_seg // 60)
            segundos = int(duracion_seg % 60)
            print(f"Duración de video de interaccion: {minutos:02d}:{segundos:02d} ({duracion_seg:.2f} sec)")
            print(f"FPS: {fps}")
        else:
            print("Duración: No disponible (típico en streaming)")
        # ---------------------------------------------

        # Iniciar el hilo para el video de Drive (con bucle=True)
        self.hilo_video_drive = HiloVideo(self.captura_video_drive, bucle=True)
        self.hilo_video_drive.senial_cambio_pixmap.connect(self.actualizar_imagen_video_drive)
        self.hilo_video_drive.start()


    def actualizar_imagen_video_drive(self, imagen):
        # Escalar y mostrar en la etiqueta 2 (video de Drive)
        self.etiqueta_video2.setPixmap(imagen.scaled(self.etiqueta_video2.width(), self.etiqueta_video2.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def closeEvent(self, evento):
        # Liberar recursos y detener procesos al cerrar la ventana
        if self.captura_camara:
            self.captura_camara.release()
        if self.hilo_video_drive:
            self.hilo_video_drive.parar()
        if self.captura_video_drive:
            self.captura_video_drive.release()
        self.temporizador_camara.stop()
        evento.accept()