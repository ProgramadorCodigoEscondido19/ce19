"""Alfabetos configurables y sus tablas visuales para el codificador."""

import hashlib

from services.app_config_service import AppConfigService
from services.app_paths import AppPaths


class AlfabetosService:
    CLAVE_LISTA = "alfabetos_personalizados"
    CLAVE_ACTIVO = "alfabeto_activo"
    ID_BASE = "abc_biblico"
    IDS_PREDEFINIDOS = {"abc_biblico", "abc_hebreo", "abc_griego"}

    @classmethod
    def _valores_secuenciales(cls, caracteres):
        return {caracter: indice for indice, caracter in enumerate(caracteres, start=1)}

    @staticmethod
    def _valores_validos(valores):
        """Conserva solo los caracteres que realmente tienen un valor usable."""
        resultado = {}
        for caracter, valor in (valores or {}).items():
            try:
                numero = int(valor)
            except (TypeError, ValueError):
                continue
            if numero > 0:
                resultado[str(caracter).strip().upper()] = numero
        return resultado

    @classmethod
    def _predefinidos(cls):
        biblico = [
            "A", "B", "C", "CH", "D", "E", "F", "G", "H", "I", "J", "K", "L",
            "LL", "M", "N", chr(0x00D1), "O", "P", "Q", "R", "S", "T", "U", "V", "W",
            "X", "Y", "Z",
        ]
        hebreo = [
            chr(codigo) for codigo in (
                0x05D0, 0x05D1, 0x05D2, 0x05D3, 0x05D4, 0x05D5, 0x05D6, 0x05D7,
                0x05D8, 0x05D9, 0x05DB, 0x05DC, 0x05DE, 0x05E0, 0x05E1, 0x05E2,
                0x05E4, 0x05E6, 0x05E7, 0x05E8, 0x05E9, 0x05EA,
            )
        ]
        griego = [
            chr(codigo) for codigo in (
                0x0391, 0x0392, 0x0393, 0x0394, 0x0395, 0x0396, 0x0397, 0x0398,
                0x0399, 0x039A, 0x039B, 0x039C, 0x039D, 0x039E, 0x039F, 0x03A0,
                0x03A1, 0x03A3, 0x03A4, 0x03A5, 0x03A6, 0x03A7, 0x03A8, 0x03A9,
            )
        ]
        return [
            {
                "id": "abc_biblico",
                "nombre": "ABC Biblico",
                "valores": cls._valores_secuenciales(biblico),
                "predefinido": True,
            },
            {
                "id": "abc_hebreo",
                "nombre": "ABC Hebreo",
                "valores": cls._valores_secuenciales(hebreo),
                "predefinido": True,
            },
            {
                "id": "abc_griego",
                "nombre": "ABC Griego",
                "valores": cls._valores_secuenciales(griego),
                "predefinido": True,
            },
        ]

    @classmethod
    def listar(cls):
        datos = AppConfigService.leer_json(AppPaths.CONFIG_APP, {})
        personalizados = datos.get(cls.CLAVE_LISTA, []) if isinstance(datos, dict) else []
        resultado = cls._predefinidos()

        for item in personalizados:
            if not isinstance(item, dict) or not item.get("id") or not item.get("nombre"):
                continue
            valores = item.get("valores", {})
            if not isinstance(valores, dict) or not valores:
                continue
            valores_limpios = cls._valores_validos(valores)
            if not valores_limpios:
                continue
            resultado.append(
                {
                    "id": str(item["id"]),
                    "nombre": str(item["nombre"]),
                    "valores": valores_limpios,
                    "predefinido": False,
                }
            )
        return resultado

    @classmethod
    def activo_id(cls):
        datos = AppConfigService.leer_json(AppPaths.CONFIG_APP, {})
        activo = datos.get(cls.CLAVE_ACTIVO, cls.ID_BASE) if isinstance(datos, dict) else cls.ID_BASE
        # Compatibilidad con la primera version de alfabetos configurables.
        if str(activo) == "espanol_29":
            return cls.ID_BASE
        return str(activo)

    @classmethod
    def obtener(cls, identificador=None):
        identificador = str(identificador or cls.activo_id())
        for alfabeto in cls.listar():
            if alfabeto["id"] == identificador:
                return alfabeto
        return cls._predefinidos()[0]

    @classmethod
    def seleccionar(cls, identificador):
        alfabeto = cls.obtener(identificador)
        datos = AppConfigService.leer_json(AppPaths.CONFIG_APP, {})
        if not isinstance(datos, dict):
            datos = {}
        datos[cls.CLAVE_ACTIVO] = alfabeto["id"]
        AppConfigService.guardar_json(AppPaths.CONFIG_APP, datos)
        return alfabeto

    @classmethod
    def guardar(cls, nombre, valores, identificador=None):
        nombre = str(nombre or "").strip()
        if not nombre:
            raise ValueError("Ingrese un nombre para el alfabeto.")
        if not isinstance(valores, dict) or not valores:
            raise ValueError("Seleccione al menos un caracter y asigne sus valores.")

        valores_limpios = cls._valores_validos(valores)
        if not valores_limpios:
            raise ValueError("Seleccione al menos un caracter y asigne sus valores.")

        if identificador in cls.IDS_PREDEFINIDOS:
            identificador = None
        if not identificador:
            semilla = f"{nombre}|{'|'.join(valores_limpios)}".encode("utf-8")
            identificador = f"personalizado_{hashlib.sha1(semilla).hexdigest()[:12]}"

        datos = AppConfigService.leer_json(AppPaths.CONFIG_APP, {})
        if not isinstance(datos, dict):
            datos = {}
        lista = [item for item in datos.get(cls.CLAVE_LISTA, []) if item.get("id") != identificador]
        lista.append({"id": identificador, "nombre": nombre, "valores": valores_limpios})
        datos[cls.CLAVE_LISTA] = lista
        datos[cls.CLAVE_ACTIVO] = identificador
        AppConfigService.guardar_json(AppPaths.CONFIG_APP, datos)
        return cls.obtener(identificador)

    @classmethod
    def eliminar(cls, identificador):
        if identificador in cls.IDS_PREDEFINIDOS:
            return False
        datos = AppConfigService.leer_json(AppPaths.CONFIG_APP, {})
        if not isinstance(datos, dict):
            datos = {}
        datos[cls.CLAVE_LISTA] = [
            item for item in datos.get(cls.CLAVE_LISTA, []) if item.get("id") != identificador
        ]
        if datos.get(cls.CLAVE_ACTIVO) == identificador:
            datos[cls.CLAVE_ACTIVO] = cls.ID_BASE
        AppConfigService.guardar_json(AppPaths.CONFIG_APP, datos)
        return True
