import json
import os
import time
from core.app_state import state
from core.rutas import ruta_datos

CARPETA_TARJETAS = "TARJETAS"
CARPETA_PIZARRAS = "PIZARRAS"
CARPETA_FRAGMENTOS = "FRAGMENTOS BIBLICOS"
CARPETA_COLORES = "COLORES"
CARPETA_TIEMPO = "TIEMPO"
CARPETAS_VALIDAS = {
    CARPETA_TARJETAS,
    CARPETA_PIZARRAS,
    CARPETA_FRAGMENTOS,
    CARPETA_COLORES,
    CARPETA_TIEMPO,
}
CARPETAS_POR_TIPO = {
    "tarjeta": (1, CARPETA_TARJETAS),
    "pizarra": (2, CARPETA_PIZARRAS),
    "fragmento_biblico": (3, CARPETA_FRAGMENTOS),
    "analisis_colores": (4, CARPETA_COLORES),
    "tiempo": (5, CARPETA_TIEMPO),
}


class Guardados:
    # =======================
    # INIT
    # =======================
    def __init__(self):
        self.archivo = ruta_datos("guardados.json")
        self.lista = []
        self.cargar()

    # =======================
    # CARGAR
    # =======================
    def cargar(self):
        if os.path.exists(self.archivo):
            try:
                with open(
                    self.archivo,
                    "r",
                    encoding="utf-8"
                ) as archivo:
                    self.lista = json.load(archivo)
            except (json.JSONDecodeError, OSError):
                self._respaldar_archivo_daniado()
                self.lista = []
                self.guardar_archivo()
                return

            # Compatibilidad con registros antiguos
            for registro in self.lista:
                if "referencia" not in registro:
                    registro["referencia"] = ""
                if "id" not in registro:
                    registro["id"] = self.generar_id()
                self.normalizar_registro(registro)

            self.guardar_archivo()
        else:
            self.guardar_archivo()

    def _respaldar_archivo_daniado(self):
        if not os.path.exists(self.archivo):
            return

        respaldo = f"{self.archivo}.daniado_{int(time.time())}.bak"

        try:
            os.replace(self.archivo, respaldo)
        except OSError:
            pass

    # =======================
    # GENERAL ID
    # =======================    
    def generar_id(self):
        if not self.lista:
            return 1
        return max(
            registro.get("id", 0)
            for registro in self.lista
        ) + 1
    
    # =======================
    # GUARDAR
    # =======================
    def guardar(self, registro):
        registro = registro.copy()

        if "id" not in registro:
            registro["id"] = self.generar_id()

        if "referencia" not in registro:
            registro["referencia"] = ""

        self.normalizar_registro(registro)

        self.lista.insert(
            0,
            registro
        )
        self.guardar_archivo()
        state.notify('update')

    def normalizar_registro(self, registro):
        tipo = registro.get("tipo")

        if tipo not in CARPETAS_POR_TIPO:
            tipo = "tarjeta"

        registro["tipo"] = tipo
        carpeta_id, carpeta_nombre = CARPETAS_POR_TIPO[tipo]

        if not registro.get("carpeta"):
            registro["carpeta"] = carpeta_nombre

        if not registro.get("carpeta_id") and registro["carpeta"] in CARPETAS_VALIDAS:
            registro["carpeta_id"] = carpeta_id
    # =======================
    # ELIMINAR
    # =======================
    def eliminar(self, id_registro):
        self.lista = [
            registro
            for registro in self.lista
            if registro.get("id") != id_registro
        ]
        self.guardar_archivo()

    # =======================
    # ACTUALIZAR REFERENCIA
    # =======================
    def actualizar_referencia(
        self,
        id_registro,
        referencia
    ):
        for registro in self.lista:
            if registro.get("id") == id_registro:
                registro["referencia"] = referencia
                break
        self.guardar_archivo()

    # =======================
    # OBTENER
    # =======================
    def obtener(self):
        return self.lista

    # =======================
    # GUARDAR ARCHIVOS
    # =======================
    def guardar_archivo(self):

        carpeta = os.path.dirname(
            self.archivo
        )
        if not os.path.exists(carpeta):
            os.makedirs(carpeta)
        temporal = f"{self.archivo}.tmp"

        with open(
            temporal,
            "w",
            encoding="utf-8"
        ) as archivo:
            json.dump(
                self.lista,
                archivo,
                indent=4,
                ensure_ascii=False,
                default=str,
            )

        os.replace(temporal, self.archivo)
    # =======================
    # MOVER REGISTRO
    # =======================
    def mover_registro(
        self,
        id_registro,
        nueva_carpeta
    ):
        for registro in self.lista:
            if registro.get("id") == id_registro:
                registro["carpeta"] = nueva_carpeta
                registro.pop("carpeta_id", None)
                self.guardar_archivo()
                return True

        return False

    def mover_registro_a_carpeta(
        self,
        id_registro,
        carpeta
    ):
        for registro in self.lista:
            if registro.get("id") == id_registro:
                registro["carpeta_id"] = carpeta["id"]
                registro["carpeta"] = carpeta["nombre"]
                self.guardar_archivo()
                state.notify("update")
                return True

        return False
