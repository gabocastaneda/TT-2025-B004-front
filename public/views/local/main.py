import sys
import os
from pathlib import Path
import atexit
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
import time

dir_actual = Path(__file__).resolve().parent
if str(dir_actual) not in sys.path:
    sys.path.insert(0, str(dir_actual))

from bienvenida import VentanaBienvenida
from respuesta_unica import VentanaReproductorVideo
from interaccion import VentanaInteraccion

class HiloEntrada(QThread):
    senal_comando_recibido = pyqtSignal(int)
    senal_palabra_clave_recibida = pyqtSignal(str) 
    
    senal_salida_solicitada = pyqtSignal() 

    def run(self):
        print("\n----------------------------------------------------")
        print("1: Regresar a Ventana de Bienvenida")
        print("2: Regresar a Ventana de Respuesta Única")
        print("3: Salir de la aplicación")
        print("Palabras clave:")
        print("hola")
        print("adios")
        print("precio")
        print("----------------------------------------------------")
        
        while True:
            comando_str = input("Ingrese un comando (1, 2, 3) o palabra clave: ")
            
            try:
                comando_int = int(comando_str)
                
                if comando_int in [1, 2]:
                    self.senal_comando_recibido.emit(comando_int)
                elif comando_int == 3:
                    self.senal_comando_recibido.emit(3)
                    break
                else:
                    print(f"Comando numérico '{comando_int}' no reconocido. Intente 1, 2, 3")
            
            except ValueError:
                if comando_str:
                    self.senal_palabra_clave_recibida.emit(comando_str)

        self.senal_salida_solicitada.emit()
        
        
class GestorAplicacion:
    def __init__(self, app):
        self.app = app
        self.ventana_actual = None
        self.inicio_ultima_transicion = None
        
        dir_base = Path(__file__).resolve().parent
        
        self.rutas_video = {
            'bienvenida': str(dir_base / 'videos' / '30fps1.mp4'), 
            'respuesta_unica': str(dir_base / 'videos' / '30fps2.mp4'), 
            'interaccion_1': str(dir_base / 'videos' / '30fps1.mp4'),
            'interaccion_2': str(dir_base / 'videos' / '30fps2.mp4'),
        }
        
        self.mapa_videos_interaccion = {
            'hola': 'https://drive.google.com/file/d/1I8XnaGQ-RpHd9rJxd5NtwJ3ArWHk2gnD/view?usp=drive_link',
            'adios': 'https://drive.google.com/file/d/1I7YNzTj1JmRLYtG9bHTPA3TDWKh46ndy/view?usp=drive_link',
            'precio': 'https://drive.google.com/file/d/1I4PnfDA_6MyiSdXjheIdLvxJdanYyXzT/view?usp=drive_link',

            'local_dos': self.rutas_video.get('interaccion_2')
        }
        # ------------------------------------

        self.hilo_entrada = HiloEntrada()
        self.hilo_entrada.senal_comando_recibido.connect(self.manejar_comando_entrada)
        self.hilo_entrada.senal_palabra_clave_recibida.connect(self.manejar_palabra_clave)
        self.hilo_entrada.senal_salida_solicitada.connect(self.app.quit)
        self.hilo_entrada.start()

    def manejar_palabra_clave(self, palabra_clave):
        if not isinstance(self.ventana_actual, VentanaInteraccion):
            print(f"Palabra clave '{palabra_clave}' ignorada (espere a la ventana de interacción).")
            return

        palabra_norm = palabra_clave.lower().strip()
        ruta_o_url = self.mapa_videos_interaccion.get(palabra_norm)
        
        if ruta_o_url:
            print(f"Palabra: '{palabra_norm}'. Iniciando video")
            self.ventana_actual.cambiar_video_unidad(ruta_o_url)
        else:
            print(f"Palabra '{palabra_norm}' no reconocida.")
            print("Videos disponibles:", list(self.mapa_videos_interaccion.keys()))


    def manejar_comando_entrada(self, comando):
        
        if comando == 1:
            self.mostrar_pantalla_bienvenida() 
            return
        elif comando == 2:
            self.mostrar_pantalla_reproductor_video()
            return
        elif comando == 3:
            QTimer.singleShot(100, self.app.quit)
            return


    def mostrar_pantalla_bienvenida(self):
        if self.inicio_ultima_transicion:
            tiempo_transicion = time.time() - self.inicio_ultima_transicion    
            print(f"Transición a bienvenida: {tiempo_transicion:.4f} segundos.")

        ruta_video = self.rutas_video.get('bienvenida')
        
        if not Path(ruta_video).is_file():
            print(f"ERROR: No se encontró el video de bienvenida en {ruta_video}.")
            self.app.quit()
            return
            
        nueva_ventana = VentanaBienvenida(ruta_video)
        nueva_ventana.video_terminado.connect(self.solicitar_pantalla_reproductor_video) 
        
        self._gestionar_cambio_ventana(nueva_ventana)

    def solicitar_pantalla_reproductor_video(self):
        self.mostrar_pantalla_reproductor_video()
        
    def mostrar_pantalla_reproductor_video(self):
        if self.inicio_ultima_transicion:
            tiempo_transicion = time.time() - self.inicio_ultima_transicion
            print(f"Transición a respuesta única: {tiempo_transicion:.4f} segundos.")

        ruta_video = self.rutas_video.get('respuesta_unica')
        
        if not Path(ruta_video).is_file():
            print(f"ERROR: No se encontró el video de respuesta única en {ruta_video}.")
            nueva_ventana = VentanaReproductorVideo(None)
        else:
            nueva_ventana = VentanaReproductorVideo(ruta_video)
            
        if not isinstance(self.ventana_actual, VentanaInteraccion):
            nueva_ventana.transicion_solicitada.connect(self.solicitar_pantalla_interaccion)

        self._gestionar_cambio_ventana(nueva_ventana)


    def solicitar_pantalla_interaccion(self):
        self.mostrar_pantalla_interaccion()

    def mostrar_pantalla_interaccion(self):
        if self.inicio_ultima_transicion:
            tiempo_transicion = time.time() - self.inicio_ultima_transicion
            print(f"Transición a interacción: {tiempo_transicion:.4f} segundos.")

        video_inicial = self.rutas_video.get('interaccion_1')
        
        if not Path(video_inicial).is_file():
            print(f"ERROR: No se encontró el video inicial de interacción en {video_inicial}.")
            nueva_ventana = VentanaInteraccion(None)
        else:
            nueva_ventana = VentanaInteraccion(video_inicial)
            
        self._gestionar_cambio_ventana(nueva_ventana)


    def _gestionar_cambio_ventana(self, nueva_ventana):
        nueva_ventana.show()

        if self.ventana_actual:
            ventana_antigua = self.ventana_actual
            self.ventana_actual = nueva_ventana
            QTimer.singleShot(100, ventana_antigua.close)
        else:
            self.ventana_actual = nueva_ventana
            
        self.inicio_ultima_transicion = time.time()

    def run(self):
        self.mostrar_pantalla_bienvenida()
        sys.exit(self.app.exec_())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gestor = GestorAplicacion(app)
    gestor.run()