"""Registro estadistico opcional de una sola vez por dispositivo.

El envio remoto es compatible con un endpoint de Google Apps Script. Si el
equipo esta sin conexion o el endpoint aun no se configuro, el registro queda
en espera localmente y no se vuelve a pedir al usuario.
"""

from __future__ import annotations

import json
import os
import platform
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from services.app_config_service import AppConfigService
from services.app_paths import AppPaths


class RegistroUsuariosService:
    CLAVE_ESTADO = "registro_estadistico"
    CLAVE_ENDPOINT = "registro_estadistico_url"
    CLAVE_PENDIENTES = "registros_estadisticos_pendientes"
    CLAVE_RESUMEN = "registro_estadistico_resumen"
    _registro_finalizado_sesion = None

    @classmethod
    def establecer_estado_sesion(cls, finalizado):
        """Recuerda el registro en la plataforma que esta usando la app."""
        cls._registro_finalizado_sesion = bool(finalizado)

    @classmethod
    def _config(cls):
        datos = AppConfigService.leer_json(AppPaths.CONFIG_APP, {})
        return datos if isinstance(datos, dict) else {}

    @classmethod
    def _guardar(cls, datos):
        AppConfigService.guardar_json(AppPaths.CONFIG_APP, datos)

    @staticmethod
    def _limpiar(valor, maximo=80):
        return " ".join(str(valor or "").strip().split())[:maximo]

    @classmethod
    def esta_finalizado(cls):
        if cls._registro_finalizado_sesion is not None:
            return cls._registro_finalizado_sesion
        estado = cls._config().get(cls.CLAVE_ESTADO, {})
        return bool(isinstance(estado, dict) and estado.get("finalizado"))

    @classmethod
    def ya_registrado(cls):
        datos = cls._config()
        datos[cls.CLAVE_ESTADO] = {
            "finalizado": True,
            "estado": "omitido",
            "fecha": cls._fecha(),
        }
        cls._guardar(datos)
        cls._registro_finalizado_sesion = True

    @staticmethod
    def _fecha():
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    @classmethod
    def _endpoint(cls, datos):
        return cls._limpiar(
            os.getenv("CE19_REGISTRO_URL") or datos.get(cls.CLAVE_ENDPOINT),
            maximo=500,
        )

    @classmethod
    def endpoint_configurado(cls):
        return bool(cls._endpoint(cls._config()))

    @classmethod
    def _enviar(cls, endpoint, registro):
        cuerpo = json.dumps(registro, ensure_ascii=False).encode("utf-8")
        solicitud = Request(
            endpoint,
            data=cuerpo,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            with urlopen(solicitud, timeout=6) as respuesta:
                return 200 <= getattr(respuesta, "status", 200) < 300
        except Exception:
            # En la version web o sin red, se conserva el registro pendiente.
            return False

    @classmethod
    def registrar(cls, nombre, pais, version=""):
        nombre = cls._limpiar(nombre)
        pais = cls._limpiar(pais)
        if not nombre:
            raise ValueError("Ingrese su nombre.")
        if not pais:
            raise ValueError("Seleccione su pais.")

        registro = {
            "nombre": nombre,
            "pais": pais,
            "fecha_utc": cls._fecha(),
            "version": cls._limpiar(version, maximo=30),
            "plataforma": platform.system() or "desconocida",
        }
        datos = cls._config()
        endpoint = cls._endpoint(datos)
        enviado = bool(endpoint and cls._enviar(endpoint, registro))

        datos[cls.CLAVE_ESTADO] = {
            "finalizado": True,
            "estado": "enviado" if enviado else "pendiente",
            "fecha": registro["fecha_utc"],
        }
        if not enviado:
            pendientes = datos.get(cls.CLAVE_PENDIENTES, [])
            if not isinstance(pendientes, list):
                pendientes = []
            pendientes.append(registro)
            datos[cls.CLAVE_PENDIENTES] = pendientes[-20:]
        cls._guardar(datos)
        cls._registro_finalizado_sesion = True
        return {
            "enviado": enviado,
            "pendiente": not enviado,
            "endpoint_configurado": bool(endpoint),
        }

    @classmethod
    def guardar_endpoint(cls, endpoint):
        datos = cls._config()
        endpoint = cls._limpiar(endpoint, maximo=500)
        if endpoint:
            datos[cls.CLAVE_ENDPOINT] = endpoint
        else:
            datos.pop(cls.CLAVE_ENDPOINT, None)
        cls._guardar(datos)
        if endpoint:
            cls.sincronizar_pendientes()

    @classmethod
    def sincronizar_pendientes(cls):
        """Intenta enviar los registros acumulados sin volver a pedir datos."""
        datos = cls._config()
        endpoint = cls._endpoint(datos)
        pendientes = datos.get(cls.CLAVE_PENDIENTES, [])
        if not endpoint or not isinstance(pendientes, list):
            return 0
        restantes = []
        enviados = 0
        for registro in pendientes:
            if isinstance(registro, dict) and cls._enviar(endpoint, registro):
                enviados += 1
            else:
                restantes.append(registro)
        datos[cls.CLAVE_PENDIENTES] = restantes
        cls._guardar(datos)
        return enviados

    @classmethod
    def obtener_resumen(cls, actualizar=False):
        """Devuelve el total y los registros agrupados por pais.

        Se usa una copia local para que el mapa siga siendo inmediato. El
        parametro ``actualizar`` consulta la tabla remota cuando existe una
        direccion configurada.
        """
        datos = cls._config()
        resumen = datos.get(cls.CLAVE_RESUMEN, {})
        if not isinstance(resumen, dict):
            resumen = {}
        respuesta = {
            "total": int(resumen.get("total", 0) or 0),
            "paises": resumen.get("paises", {}) if isinstance(resumen.get("paises"), dict) else {},
        }
        endpoint = cls._endpoint(datos)
        if not actualizar or not endpoint:
            return respuesta

        separador = "&" if "?" in endpoint else "?"
        try:
            with urlopen(f"{endpoint}{separador}{urlencode({'accion': 'resumen'})}", timeout=6) as solicitud:
                remoto = json.loads(solicitud.read().decode("utf-8"))
            paises = remoto.get("paises", {})
            if not isinstance(paises, dict):
                paises = {}
            respuesta = {
                "total": int(remoto.get("total", 0) or 0),
                "paises": {cls._limpiar(pais): int(cantidad or 0) for pais, cantidad in paises.items()},
            }
            datos[cls.CLAVE_RESUMEN] = {
                **respuesta,
                "actualizado": cls._fecha(),
            }
            cls._guardar(datos)
        except Exception:
            pass
        return respuesta
