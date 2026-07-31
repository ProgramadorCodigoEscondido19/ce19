import asyncio
import json
import os
import time
import flet as ft
from core.app_state import state
from core.rutas import ruta_datos

CARPETA_TARJETAS = "TARJETAS"
CARPETA_PIZARRAS = "PIZARRAS"
CARPETA_FRAGMENTOS = "FRAGMENTOS BIBLICOS"
CARPETA_COLORES = "COLORES"
CARPETA_TIEMPO = "TIEMPO"
CARPETA_CALCULADORA = "CALCULADORA"
CARPETAS_VALIDAS = {
    CARPETA_TARJETAS,
    CARPETA_PIZARRAS,
    CARPETA_FRAGMENTOS,
    CARPETA_COLORES,
    CARPETA_TIEMPO,
    CARPETA_CALCULADORA,
}
CARPETAS_POR_TIPO = {
    "tarjeta": (1, CARPETA_TARJETAS),
    "pizarra": (2, CARPETA_PIZARRAS),
    "fragmento_biblico": (3, CARPETA_FRAGMENTOS),
    "analisis_colores": (4, CARPETA_COLORES),
    "tiempo": (5, CARPETA_TIEMPO),
    "calculo_biblico": (6, CARPETA_CALCULADORA),
}


class Guardados:
    CLAVE_WEB = "ce19.guardados.v1"

    # =======================
    # INIT
    # =======================
    def __init__(self, page=None):
        self.archivo = ruta_datos("guardados.json")
        self.lista = []
        self.page = page
        self.preferencias_web = self._crear_preferencias_web(page)
        self.cargar()
        self._cargar_web_si_corresponde()

    def _crear_preferencias_web(self, page):
        if page is None or not getattr(page, "web", False):
            return None

        try:
            preferencias = ft.SharedPreferences()
            if hasattr(page, "services"):
                page.services.append(preferencias)
            else:
                page.overlay.append(preferencias)
            return preferencias
        except Exception:
            return None

    def _programar_web(self, funcion, *args):
        if self.page is None or self.preferencias_web is None:
            return

        try:
            self.page.run_task(funcion, *args)
        except Exception:
            pass

    def _cargar_web_si_corresponde(self):
        self._programar_web(self._cargar_web)

    async def _cargar_web(self):
        try:
            contenido = await self._leer_preferencia_web()
            if not contenido:
                await self._guardar_web()
                return

            datos = json.loads(contenido)
            if not isinstance(datos, list):
                return

            self.lista = [
                registro
                for registro in datos
                if isinstance(registro, dict)
            ]
            hubo_cambios = False
            siguiente_id = self.generar_id()

            for registro in self.lista:
                if not isinstance(registro, dict):
                    continue
                if "id" not in registro:
                    registro["id"] = siguiente_id
                    siguiente_id += 1
                    hubo_cambios = True
                if "referencia" not in registro:
                    registro["referencia"] = ""
                    hubo_cambios = True
                hubo_cambios = self.normalizar_registro(registro) or hubo_cambios

            if hubo_cambios:
                await self._guardar_web()

            state.notify("update")
        except Exception:
            pass

    async def _leer_preferencia_web(self):
        ultimo_error = None

        # El servicio se monta junto con la primera actualizacion de la pagina.
        # En web puede necesitar un instante antes de aceptar lecturas.
        for intento in range(3):
            try:
                return await self.preferencias_web.get(self.CLAVE_WEB)
            except Exception as error:
                ultimo_error = error
                await asyncio.sleep(0.08 * (intento + 1))

        raise ultimo_error

    async def _guardar_web(self):
        contenido = json.dumps(
            self.lista,
            ensure_ascii=False,
            default=str,
        )

        for intento in range(3):
            try:
                await self.preferencias_web.set(self.CLAVE_WEB, contenido)
                return
            except Exception:
                if intento < 2:
                    await asyncio.sleep(0.08 * (intento + 1))

    # =======================
    # CARGAR
    # =======================
    def cargar(self):
        # En web la fuente persistente es SharedPreferences. No se debe escribir
        # una lista vacia antes de que termine la lectura asincrona.
        if self.preferencias_web is not None:
            self.lista = []
            return

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

            hubo_cambios = False
            siguiente_id = self.generar_id()

            # Compatibilidad con registros antiguos
            for registro in self.lista:
                if "referencia" not in registro:
                    registro["referencia"] = ""
                    hubo_cambios = True
                if "id" not in registro:
                    registro["id"] = siguiente_id
                    siguiente_id += 1
                    hubo_cambios = True
                hubo_cambios = self.normalizar_registro(registro) or hubo_cambios

            if hubo_cambios:
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
        tipo_original = registro.get("tipo")
        carpeta_original = registro.get("carpeta")
        carpeta_id_original = registro.get("carpeta_id")

        tipo = registro.get("tipo")

        if tipo not in CARPETAS_POR_TIPO:
            tipo = "tarjeta"

        registro["tipo"] = tipo
        carpeta_id, carpeta_nombre = CARPETAS_POR_TIPO[tipo]

        if not registro.get("carpeta"):
            registro["carpeta"] = carpeta_nombre

        if not registro.get("carpeta_id") and registro["carpeta"] in CARPETAS_VALIDAS:
            registro["carpeta_id"] = carpeta_id

        return (
            tipo_original != registro.get("tipo")
            or carpeta_original != registro.get("carpeta")
            or carpeta_id_original != registro.get("carpeta_id")
        )
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
        try:
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
        except OSError:
            pass

        self._programar_web(self._guardar_web)
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
