import sys
import os
import cv2
from pathlib import Path
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import pyqtSignal, QThread
import time

class HiloVideo(QThread):
    senal_cambio_pixmap = pyqtSignal(QPixmap)
    terminado = pyqtSignal()
    
    def __init__(self, cap, bucle=False):
        super().__init__()
        self._bandera_ejecucion = True
        self.cap = cap
        self.bucle = bucle
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) if self.cap.isOpened() else 30

    def run(self):
        while self._bandera_ejecucion:
            tiempo_inicio = time.time()
            
            if not self._bandera_ejecucion or not self.cap.isOpened():
                break

            ret, marco = self.cap.read()
            if ret:
                if not self._bandera_ejecucion:
                    break

                marco = cv2.flip(marco, 1) 
                marco_rgb = cv2.cvtColor(marco, cv2.COLOR_BGR2RGB)
                h, w, ch = marco_rgb.shape
                bytes_por_linea = ch * w
                imagen_qt = QImage(marco_rgb.data, w, h, bytes_por_linea, QImage.Format_RGB888)
                
                if not self._bandera_ejecucion:
                    break
                self.senal_cambio_pixmap.emit(QPixmap.fromImage(imagen_qt))

                tiempo_transcurrido = time.time() - tiempo_inicio
                tiempo_espera = (1.0 / self.fps) - tiempo_transcurrido if self.fps > 0 else 0
                if tiempo_espera > 0:
                    time.sleep(tiempo_espera)
            elif self.bucle:
                if not self._bandera_ejecucion:
                    break
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            else:
                self._bandera_ejecucion = False
        self.terminado.emit()

    def stop(self):
        self._bandera_ejecucion = False
        self.wait()