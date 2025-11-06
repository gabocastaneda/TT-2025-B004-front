import sys
import os
import cv2
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QLabel, QDesktopWidget, QWidget, QMessageBox
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon
from PyQt5.QtCore import QSize, QTimer, Qt, pyqtSignal, QRect, QThread
import time
import shutil
import re 
from hilo_video import HiloVideo
from hilo_descarga import HiloDescarga

class VentanaInteraccion(QMainWindow):
    redimensionada = pyqtSignal()
    
    def __init__(self, ruta_video_inicial):
        super().__init__()
        self.setWindowTitle("Ventana de Interacción")
        self.setWindowIcon(QIcon())
        self.cap_camara = cv2.VideoCapture(0)
        
        self.cap_video_unidad = None
        self.hilo_video_unidad = None
        self.hilo_descarga = None 
        self.ruta_actual_video_unidad = None 
        self.inicializar_ui()
        self.temporizador_camara = QTimer(self)
        self.temporizador_camara.timeout.connect(self.actualizar_marco_camara)
        self.temporizador_camara.start(10)
        
        self.etiqueta_video2.setText("Esperando comando")
        
        if ruta_video_inicial:
            self.cambiar_video_unidad(ruta_video_inicial) 

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
        self.redimensionada.connect(self.actualizar_disposicion)
        self.actualizar_disposicion()

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
        x_video1 = margen_izquierdo
        x_video2 = margen_izquierdo + ancho_recuadro + separacion
        
        self.recuadro_video1.setGeometry(x_video1, y_video, ancho_recuadro, alto_recuadro)
        self.recuadro_video2.setGeometry(x_video2, y_video, ancho_recuadro, alto_recuadro)
        self.etiqueta_video1.setGeometry(10, 10, ancho_recuadro - 20, alto_recuadro - 20)
        self.etiqueta_video2.setGeometry(10, 10, ancho_recuadro - 20, alto_recuadro - 20)

    def actualizar_marco_camara(self):
        if not self.cap_camara.isOpened():
            return
            
        ret, marco = self.cap_camara.read()
        if ret:
            marco = cv2.flip(marco, 1)
            marco_rgb = cv2.cvtColor(marco, cv2.COLOR_BGR2RGB)
            h, w, ch = marco_rgb.shape
            bytes_por_linea = ch * w
            imagen_qt = QImage(marco_rgb.data, w, h, bytes_por_linea, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(imagen_qt)
            pixmap_escalado = pixmap.scaled(self.etiqueta_video1.width(), self.etiqueta_video1.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.etiqueta_video1.setPixmap(pixmap_escalado)


    def cambiar_video_unidad(self, nueva_ruta_o_url): 
        if self.hilo_descarga and self.hilo_descarga.isRunning():
             self.hilo_descarga.terminate() 
             print(f"Descarga cancelada.")
             self.hilo_descarga = None

        if self.hilo_video_unidad:
            if hasattr(self.hilo_video_unidad, 'tiempo_inicio'):
                nombre_video_anterior = Path(self.ruta_actual_video_unidad).name if self.ruta_actual_video_unidad else 'N/A'
                tiempo_total_reproduccion = time.time() - self.hilo_video_unidad.tiempo_inicio
                
                print(f"Finalizado video anterior: {nombre_video_anterior}")
                print(f"Tiempo de reproducción real: {tiempo_total_reproduccion:.2f} segundos.")

            self.hilo_video_unidad.stop()
            self.hilo_video_unidad = None
        if self.cap_video_unidad:
            self.cap_video_unidad.release()
            self.cap_video_unidad = None
            
        if nueva_ruta_o_url.startswith("http"):
            dir_guardado = Path(__file__).resolve().parent / 'videos'
            match = re.search(r'/d/([a-zA-Z0-9_-]+)', nueva_ruta_o_url)
            
            if match:
                 file_id = match.group(1)
                 nombre_base = f"descargado_{file_id[:8]}.mp4"
                 ruta_guardada = dir_guardado / nombre_base
                 
                 if ruta_guardada.is_file():
                     print(f"Video ya descargado ({nombre_base}). Iniciando reproducción local.")
                     self.iniciar_video_unidad(str(ruta_guardada))
                     return
            self.etiqueta_video2.setText(f"Descargando video de Drive")
            
            self.hilo_descarga = HiloDescarga(nueva_ruta_o_url)
            self.hilo_descarga.senal_descarga_terminada.connect(self._manejar_descarga_terminada)
            self.hilo_descarga.start()
        
        elif Path(nueva_ruta_o_url).is_file():
            self.iniciar_video_unidad(nueva_ruta_o_url)
        else:
             self.etiqueta_video2.setText("Error: Ruta no válida o video no encontrado.")
             print(f"Error: La ruta '{nueva_ruta_o_url}' no es válida.")

    def _manejar_descarga_terminada(self, nombre_archivo, ruta_local_permanente):
        if ruta_local_permanente:
            print(f"Descarga exitosa. Iniciando reproducción {nombre_archivo}")
            self.iniciar_video_unidad(ruta_local_permanente)
        else:
            self.etiqueta_video2.setText(f"Error al descargar {nombre_archivo}.")
            QMessageBox.critical(self, "Error de Descarga", f"No se pudo descargar el video: {nombre_archivo}.")
        
        self.hilo_descarga = None

    def iniciar_video_unidad(self, ruta_video):
        if not ruta_video:
            self.etiqueta_video2.setText("Error al cargar el video")
            return
            
        self.cap_video_unidad = cv2.VideoCapture(ruta_video)
        self.ruta_actual_video_unidad = ruta_video 
        
        if not self.cap_video_unidad.isOpened():
            self.etiqueta_video2.setText("Error al abrir el video: " + Path(ruta_video).name)
            return
        
        fps = self.cap_video_unidad.get(cv2.CAP_PROP_FPS)
        ancho = int(self.cap_video_unidad.get(cv2.CAP_PROP_FRAME_WIDTH))
        alto = int(self.cap_video_unidad.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fotogramas_totales = self.cap_video_unidad.get(cv2.CAP_PROP_FRAME_COUNT)

        print(f"Video: {Path(ruta_video).name}")
        if fps > 0 and fotogramas_totales > 0:
            duracion_seg = fotogramas_totales / fps
            minutos = int(duracion_seg // 60)
            segundos = int(duracion_seg % 60)
            print(f"Duración Nominal: {minutos:02d}:{segundos:02d} ({duracion_seg:.2f} seg)")
            print(f"FPS: {fps:.2f}")
            print(f"Calidad: {ancho}x{alto}")
        else:
            print("   Propiedades: No disponibles")

        self.etiqueta_video2.setText("Reproduciendo")
        self.hilo_video_unidad = HiloVideo(self.cap_video_unidad, bucle=True)
        self.hilo_video_unidad.senal_cambio_pixmap.connect(self.actualizar_imagen_video_unidad)
        
        self.hilo_video_unidad.tiempo_inicio = time.time() 
        self.hilo_video_unidad.start()


    def actualizar_imagen_video_unidad(self, imagen):
        self.etiqueta_video2.setPixmap(imagen.scaled(self.etiqueta_video2.width(), self.etiqueta_video2.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def closeEvent(self, evento):
        if self.hilo_descarga and self.hilo_descarga.isRunning():
            self.hilo_descarga.terminate()
        if self.cap_camara:
            self.cap_camara.release()
        if self.hilo_video_unidad:
            if hasattr(self.hilo_video_unidad, 'tiempo_inicio'):
                tiempo_total_reproduccion = time.time() - self.hilo_video_unidad.tiempo_inicio
                nombre_video_final = Path(self.ruta_actual_video_unidad).name if hasattr(self, 'ruta_actual_video_unidad') else 'N/A'
                print(f"Tiempo de reproducción real: {tiempo_total_reproduccion:.2f} segundos.")
            self.hilo_video_unidad.stop()
        if self.cap_video_unidad:
            self.cap_video_unidad.release()
        self.temporizador_camara.stop()
        print("-" * 50)
        evento.accept()