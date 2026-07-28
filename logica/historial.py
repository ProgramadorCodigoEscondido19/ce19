import json
import os
import flet as ft
from core.app_state import state
from core.rutas import ruta_datos

class Historial:
    CLAVE_WEB = "ce19.historial.v1"

    def __init__(self, page=None):
        self.archivo = ruta_datos("historial.json")
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
            contenido = await self.preferencias_web.get(self.CLAVE_WEB)
            if not contenido:
                await self._guardar_web()
                return

            datos = json.loads(contenido)
            if isinstance(datos, list):
                self.lista = datos
                state.notify("update")
        except Exception:
            pass

    async def _guardar_web(self):
        try:
            contenido = json.dumps(
                self.lista,
                ensure_ascii=False,
                default=str,
            )
            await self.preferencias_web.set(self.CLAVE_WEB, contenido)
        except Exception:
            pass
    # ---------------------------------------------

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
                self.lista = []
        else:
            self.guardar_archivo()
    # ---------------------------------------------
    def agregar(self, registro, notificar=True):

        self.lista.insert(
            0,
            registro
        )

        self.guardar_archivo()
        if notificar:
            state.notify('update')



    # ---------------------------------------------

    def obtener(self):

        return self.lista



    # ---------------------------------------------

    def guardar_archivo(self):
        try:
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
        except OSError:
            pass

        self._programar_web(self._guardar_web)
