import sys
import os
import requests
import tempfile
import atexit
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
import time

from bienvenida import VentanaBienvenida
from respuesta_unica import VentanaReproductorVideo
from interaccion import VentanaInteraccion


class GestorAplicacion:
    def __init__(self):
        self.tiempo_inicio_app = time.time()
        
        self.app = QApplication(sys.argv)
        self.rutas_videos = {} 
        self.ventana_actual = None
        self.inicio_ultima_transicion = time.time()

        self.urls_videos = {
            'bienvenida': 'https://www.googleapis.com/drive/v3/files/1X913T6IvBezORm7lXkyMVDfygKHh2aty?alt=media&key=AIzaSyCPQezDLouT6Lwc0JHG6QpxWPrukz_2Jac',
            'respuesta': 'https://www.googleapis.com/drive/v3/files/1X913T6IvBezORm7lXkyMVDfygKHh2aty?alt=media&key=AIzaSyCPQezDLouT6Lwc0JHG6QpxWPrukz_2Jac',
            'interaccion': 'https://www.googleapis.com/drive/v3/files/1X913T6IvBezORm7lXkyMVDfygKHh2aty?alt=media&key=AIzaSyCPQezDLouT6Lwc0JHG6QpxWPrukz_2Jac'
        }
        
        self.rutas_videos = self.urls_videos

        self.mostrar_pantalla_bienvenida() 

    def mostrar_pantalla_bienvenida(self):
        if self.inicio_ultima_transicion is not None:
            tiempo_transicion = time.time() - self.inicio_ultima_transicion
            print(f"Tiempo de inicio de la aplicación: {tiempo_transicion:.4f} segundos.\n")
            self.inicio_ultima_transicion = None

        ruta_video = self.rutas_videos.get('bienvenida')
        self.ventana_actual = VentanaBienvenida(ruta_video)
        self.ventana_actual.video_terminado.connect(self.solicitar_pantalla_reproductor_video)
        self.ventana_actual.show()

    def solicitar_pantalla_reproductor_video(self):
        self.mostrar_pantalla_reproductor_video()

    def mostrar_pantalla_reproductor_video(self):
        ruta_video = self.rutas_videos.get('respuesta')
        nueva_ventana = VentanaReproductorVideo(ruta_video)
        nueva_ventana.solicitud_transicion.connect(self.solicitar_pantalla_interaccion)
        nueva_ventana.show()

        if self.ventana_actual:
            ventana_antigua = self.ventana_actual
            self.ventana_actual = nueva_ventana
            QTimer.singleShot(0, ventana_antigua.close)
        else:
            self.ventana_actual = nueva_ventana

    def solicitar_pantalla_interaccion(self):
        self.mostrar_pantalla_interaccion()

    def mostrar_pantalla_interaccion(self):
        ruta_video = self.rutas_videos.get('interaccion')
        nueva_ventana = VentanaInteraccion(ruta_video)
        nueva_ventana.show()

        if self.ventana_actual:
            ventana_antigua = self.ventana_actual
            self.ventana_actual = nueva_ventana
            QTimer.singleShot(0, ventana_antigua.close)
        else:
            self.ventana_actual = nueva_ventana

    def ejecutar(self):
        sys.exit(self.app.exec_())

if __name__ == '__main__':
    gestor = GestorAplicacion()
    gestor.ejecutar()