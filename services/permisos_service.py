"""Permisos locales por nivel para Codigo Escondido 19."""

import hashlib
import hmac

from services.app_config_service import AppConfigService
from services.app_paths import AppPaths


class PermisosService:
    """Valida niveles y recuerda los que ya fueron autorizados en este equipo."""

    CLAVE_CONFIG = "niveles_autorizados"
    CLAVE_VERSION_CONFIG = "niveles_autorizados_version"
    VERSION_CREDENCIALES = "2026-08-seguras"
    _SAL = b"CE19.niveles.2026"
    _ITERACIONES = 120000
    _HASHES_INICIALES = {
        1: "ac5e44d3c3ee18c708b8e1fc938c21da67de956f535ced32dbcb7863b2c8b2ea",
        2: "57e4d16b9aab99543e0abaf9dd6ec63adb05b1ab5946bbda41f62ced6f2f4f01",
        3: "6b6529203278e69562053327be7e8e543769ef17f7833866522e283befcf6f38",
        4: "bdb02814b484f9152ecf92c45dc2f010381e5a39492f3ec90259e0c444dcd5d9",
    }
    _niveles_sesion = None

    @classmethod
    def establecer_niveles_sesion(cls, niveles):
        """Sincroniza los niveles recordados por la plataforma actual.

        En escritorio se conserva el archivo local y en la web este valor se
        carga desde las preferencias persistentes del navegador.
        """
        if not isinstance(niveles, (list, tuple, set)):
            niveles = []
        cls._niveles_sesion = {
            int(nivel)
            for nivel in niveles
            if str(nivel).isdigit() and 1 <= int(nivel) <= 4
        }

    @classmethod
    def _niveles_archivo(cls):
        datos = AppConfigService.leer_json(AppPaths.CONFIG_APP, {})
        if not isinstance(datos, dict) or datos.get(cls.CLAVE_VERSION_CONFIG) != cls.VERSION_CREDENCIALES:
            return set()
        niveles = datos.get(cls.CLAVE_CONFIG, [])
        return {int(nivel) for nivel in niveles if str(nivel).isdigit() and 1 <= int(nivel) <= 4}

    @classmethod
    def _hash_clave(cls, clave):
        contraseña = str(clave).encode("utf-8")
        funcion_nativa = getattr(hashlib, "pbkdf2_hmac", None)
        if callable(funcion_nativa):
            return funcion_nativa(
                "sha256",
                contraseña,
                cls._SAL,
                cls._ITERACIONES,
            ).hex()
        return cls._pbkdf2_compatible_web(contraseña).hex()

    @classmethod
    def _pbkdf2_compatible_web(cls, contraseña):
        """Alternativa para la version web, donde hashlib no incluye PBKDF2."""
        bloque = hmac.new(contraseña, cls._SAL + b"\x00\x00\x00\x01", hashlib.sha256).digest()
        resultado = bytearray(bloque)
        anterior = bloque
        for _ in range(1, cls._ITERACIONES):
            anterior = hmac.new(contraseña, anterior, hashlib.sha256).digest()
            for indice, valor in enumerate(anterior):
                resultado[indice] ^= valor
        return bytes(resultado)

    @classmethod
    def validar_clave(cls, nivel, clave):
        try:
            esperado = cls._HASHES_INICIALES[int(nivel)]
        except (KeyError, TypeError, ValueError):
            return False
        return hmac.compare_digest(cls._hash_clave(clave), esperado)

    @classmethod
    def niveles_autorizados(cls):
        if cls._niveles_sesion is not None:
            return set(cls._niveles_sesion)
        return cls._niveles_archivo()

    @classmethod
    def esta_autorizado(cls, nivel):
        return int(nivel) in cls.niveles_autorizados()

    @classmethod
    def autorizar(cls, nivel, guardar=True):
        nivel = int(nivel)
        if not guardar:
            return nivel
        datos = AppConfigService.leer_json(AppPaths.CONFIG_APP, {})
        if not isinstance(datos, dict):
            datos = {}
        niveles = cls.niveles_autorizados()
        niveles.add(nivel)
        cls._niveles_sesion = set(niveles)
        datos[cls.CLAVE_CONFIG] = sorted(niveles)
        datos[cls.CLAVE_VERSION_CONFIG] = cls.VERSION_CREDENCIALES
        AppConfigService.guardar_json(AppPaths.CONFIG_APP, datos)
        return nivel

    @classmethod
    def revocar(cls, nivel):
        """Quita el acceso recordado para que el nivel vuelva a pedir clave."""
        nivel = int(nivel)
        datos = AppConfigService.leer_json(AppPaths.CONFIG_APP, {})
        if not isinstance(datos, dict):
            datos = {}
        niveles = cls.niveles_autorizados()
        niveles.discard(nivel)
        cls._niveles_sesion = set(niveles)
        datos[cls.CLAVE_CONFIG] = sorted(niveles)
        datos[cls.CLAVE_VERSION_CONFIG] = cls.VERSION_CREDENCIALES
        AppConfigService.guardar_json(AppPaths.CONFIG_APP, datos)
