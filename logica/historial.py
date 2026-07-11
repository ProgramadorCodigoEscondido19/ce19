import json
import os
from core.app_state import state
from core.rutas import ruta_datos

class Historial:

    def __init__(self):
        self.archivo = ruta_datos("historial.json")
        self.lista = []
        self.cargar()
    # ---------------------------------------------

    def cargar(self):
        if os.path.exists(self.archivo):
            with open(
                self.archivo,
                "r",
                encoding="utf-8"
            ) as archivo:

                self.lista = json.load(archivo)
        else:
            self.guardar_archivo()
    # ---------------------------------------------
    def agregar(self, registro):

        self.lista.insert(
            0,
            registro
        )

        self.guardar_archivo()
        state.notify('update')



    # ---------------------------------------------

    def obtener(self):

        return self.lista



    # ---------------------------------------------

    def guardar_archivo(self):

        carpeta = os.path.dirname(
            self.archivo
        )

        if not os.path.exists(carpeta):

            os.makedirs(carpeta)


        with open(
            self.archivo,
            "w",
            encoding="utf-8"
        ) as archivo:

            json.dump(
                self.lista,
                archivo,
                indent=4,
                ensure_ascii=False
            )
