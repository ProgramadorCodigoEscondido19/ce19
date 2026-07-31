import asyncio
import json
import os
import flet as ft

from core.app_state import state
from core.rutas import ruta_datos

CARPETAS_FIJAS = [
    {
        "id": 1,
        "nombre": "TARJETAS",
        "padre": None,
    },
    {
        "id": 2,
        "nombre": "PIZARRAS",
        "padre": None,
    },
    {
        "id": 3,
        "nombre": "FRAGMENTOS BIBLICOS",
        "padre": None,
    },
    {
        "id": 4,
        "nombre": "COLORES",
        "padre": None,
    },
    {
        "id": 5,
        "nombre": "TIEMPO",
        "padre": None,
    },
    {
        "id": 6,
        "nombre": "CALCULADORA",
        "padre": None,
    },
]


class Carpetas:
    CLAVE_WEB = "ce19.carpetas.v1"

    # ======================================
    # INIT
    # ======================================
    def __init__(self, guardados, page=None):
        self.guardado = guardados
        self.archivo = ruta_datos("carpetas.json")
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
                carpeta
                for carpeta in datos
                if isinstance(carpeta, dict)
            ]
            hubo_cambios = self._asegurar_carpetas_fijas()

            if hubo_cambios:
                await self._guardar_web()

            state.notify("update")
        except Exception:
            pass

    async def _leer_preferencia_web(self):
        ultimo_error = None

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
        )

        for intento in range(3):
            try:
                await self.preferencias_web.set(self.CLAVE_WEB, contenido)
                return
            except Exception:
                if intento < 2:
                    await asyncio.sleep(0.08 * (intento + 1))

    # ======================================
    # CARGAR
    #=======================================
    def cargar(self):
        # En web se mantienen las carpetas guardadas por el navegador. Guardar
        # aqui la estructura inicial reemplazaria las subcarpetas existentes.
        if self.preferencias_web is not None:
            self.lista = []
            self._asegurar_carpetas_fijas()
            return

        if os.path.exists(self.archivo):
            try:
                with open(
                    self.archivo,
                    "r",
                    encoding="utf-8",
                ) as archivo:
                    self.lista = json.load(archivo)
            except (json.JSONDecodeError, OSError):
                self.lista = []
        else:
            self.lista = []

        if self._asegurar_carpetas_fijas():
            self.guardar()

    def _asegurar_carpetas_fijas(self):
        hubo_cambios = False
        orden_original = [carpeta.get("id") for carpeta in self.lista]
        por_id = {
            carpeta.get("id"): carpeta
            for carpeta in self.lista
        }

        for fija in CARPETAS_FIJAS:
            if fija["id"] in por_id:
                carpeta = por_id[fija["id"]]
                if carpeta.get("nombre") != fija["nombre"]:
                    carpeta["nombre"] = fija["nombre"]
                    hubo_cambios = True
                if carpeta.get("padre") is not None:
                    carpeta["padre"] = None
                    hubo_cambios = True
            else:
                self.lista.append(fija.copy())
                hubo_cambios = True

        self.lista.sort(key=lambda carpeta: carpeta.get("id", 0))
        if orden_original != [carpeta.get("id") for carpeta in self.lista]:
            hubo_cambios = True

        return hubo_cambios

    # -----------------------------------------
    def guardar(self):
        try:
            carpeta = os.path.dirname(self.archivo)

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
                    ensure_ascii=False,
                )
        except OSError:
            pass

        self._programar_web(self._guardar_web)

    # -----------------------------------------
    def generar_id(self):

        if not self.lista:

            return 1

        return max(
            carpeta["id"]
            for carpeta in self.lista
        ) + 1

    # ==========================================
    # F() OBTENER
    # ==========================================
    def obtener(self):
        return self.lista

    # ==========================================
    # F()OBTENER HIJOS
    # ==========================================
    def obtener_hijos(self, padre=None):
        return [
            carpeta
            for carpeta in self.lista
            if carpeta.get("padre") == padre
        ]

    # ==============================================
    # F() OBTENER NOMBRES
    #===============================================
    def obtener_nombres(self):
        return sorted(
            carpeta["nombre"]
            for carpeta in self.lista
        )
            
    # -----------------------------------------
    def crear(self,nombre,padre=None,):
        nombre = (nombre or "").strip()

        if not nombre or padre is None:
            return None

        if self.obtener_por_id(padre) is None:
            return None

        existe = any(
            carpeta["nombre"].lower() == nombre.lower()
            and carpeta.get("padre") == padre
            for carpeta in self.lista
        )

        if existe:
            return None

        carpeta = {
            "id": self.generar_id(),
            "nombre": nombre,
            "padre": padre,
        }
        self.lista.append(carpeta)
        self.guardar()
        return carpeta

    # ==============================================
    # FUNCION ELIMINAR
    #===============================================
    def eliminar(self, id_carpeta):
        if self.es_raiz_fija(id_carpeta):
            return False

        ids = {id_carpeta}
        ids.update(self.obtener_descendientes(id_carpeta))
        carpeta = self.obtener_por_id(id_carpeta)
        destino = carpeta.get("padre") if carpeta else None

        for registro in self.guardado.obtener():
            if registro.get("carpeta_id") in ids:
                padre = self.obtener_por_id(destino)
                registro["carpeta_id"] = destino
                registro["carpeta"] = padre["nombre"] if padre else "TARJETAS"

        self.lista = [
            carpeta
            for carpeta in self.lista
            if carpeta["id"] not in ids
        ]
        self.guardar()
        self.guardado.guardar_archivo()
        return True
    
    # ==============================================
    # FUNCION RENOMBRAR
    # ==============================================
    def renombrar(self, id_carpeta, nuevo_nombre,):
        if self.es_raiz_fija(id_carpeta):
            return False

        carpeta = self.obtener_por_id(id_carpeta)

        if carpeta is None:
            return False

        nuevo_nombre = (nuevo_nombre or "").strip()

        if not nuevo_nombre:
            return False

        padre = carpeta.get("padre")
        existe = any(
            otra["id"] != id_carpeta
            and otra.get("padre") == padre
            and otra["nombre"].lower() == nuevo_nombre.lower()
            for otra in self.lista
        )

        if existe:
            return False

        nombre_anterior = carpeta["nombre"]
        carpeta["nombre"] = nuevo_nombre

        for registro in self.guardado.obtener():
            if (
                registro.get("carpeta_id") == id_carpeta
                or registro.get("carpeta") == nombre_anterior
            ):
                registro["carpeta"] = nuevo_nombre
                registro["carpeta_id"] = id_carpeta

        self.guardar()
        self.guardado.guardar_archivo()
        return True

    # ==============================================
    # F() OBTENER POR ID
    #===============================================
    def obtener_por_id(self, id_carpeta):
        for carpeta in self.lista:
            if carpeta["id"] == id_carpeta:
                return carpeta

        return None

    # ==============================================
    # F() OBTENER DESCENDIENTES
    #===============================================
    def obtener_descendientes(self, id_carpeta):
        pendientes = [id_carpeta]
        descendientes = set()

        while pendientes:
            padre = pendientes.pop()
            hijos = [
                carpeta["id"]
                for carpeta in self.lista
                if carpeta.get("padre") == padre
            ]
            for hijo in hijos:
                if hijo not in descendientes:
                    descendientes.add(hijo)
                    pendientes.append(hijo)

        return descendientes
    
    # ==========================================
    # F() OBTENER RUTA
    # ==========================================
    def obtener_ruta(self, id_carpeta):

        ruta = []

        actual = self.obtener_por_id(id_carpeta)

        while actual is not None:
            ruta.append(actual)
        
            actual = self.obtener_por_id(
                actual.get("padre")
            )

        ruta.reverse()

        return ruta
    
    # ==========================================
    # F() RUTA COMO TEXTO
    # ==========================================
    def obtener_ruta_texto(self, id_carpeta):

        ruta = self.obtener_ruta(id_carpeta)

        return " > ".join(
            carpeta["nombre"]
            for carpeta in ruta
        )
    # ==========================================
    # F() OBTENER POR NOMBRE
    # ==========================================
    def obtener_por_nombre(self, nombre):

        for carpeta in self.lista:

            if carpeta["nombre"] == nombre:

                return carpeta

        return None

    def es_raiz_fija(self, id_carpeta):
        return id_carpeta in {
            carpeta["id"]
            for carpeta in CARPETAS_FIJAS
        }

    def raiz_de(self, id_carpeta):
        ruta = self.obtener_ruta(id_carpeta)
        return ruta[0] if ruta else None
