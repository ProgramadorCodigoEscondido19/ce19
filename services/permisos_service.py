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
        1: "bb56598ddb6157cec3a4b92ef4462b26ceb905b027520319f1ec787fcf321373",
        2: "b17a5425faa5bf4c70e72184569e2b6ee046e45434db760e87b2529f112b70eb",
        3: "35842d344a99a71b6d0e8c0df27f134a2307cbe06eeba752044f121b50eb6ace",
        4: "d19104c01263800c8b238e9500514839fba4868eb0cd36101880183f7e1fa7fa",
    }

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
        datos = AppConfigService.leer_json(AppPaths.CONFIG_APP, {})
        if not isinstance(datos, dict) or datos.get(cls.CLAVE_VERSION_CONFIG) != cls.VERSION_CREDENCIALES:
            return set()
        niveles = datos.get(cls.CLAVE_CONFIG, []) if isinstance(datos, dict) else []
        return {int(nivel) for nivel in niveles if str(nivel).isdigit() and 1 <= int(nivel) <= 4}

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
        datos[cls.CLAVE_CONFIG] = sorted(niveles)
        datos[cls.CLAVE_VERSION_CONFIG] = cls.VERSION_CREDENCIALES
        AppConfigService.guardar_json(AppPaths.CONFIG_APP, datos)
