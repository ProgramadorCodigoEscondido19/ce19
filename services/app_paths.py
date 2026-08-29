from pathlib import Path

from core.rutas import RAIZ_PROYECTO, carpeta_datos_usuario, ruta_datos


class AppPaths:
    """Rutas centrales de Codigo Escondido 19.

    Usar este archivo evita repetir nombres de archivos en distintas vistas/servicios.
    Los datos modificables viven fuera del directorio del programa para que
    permanezcan separados de los archivos de la aplicacion.
    """

    ROOT = RAIZ_PROYECTO
    DATOS = carpeta_datos_usuario()
    ASSETS = RAIZ_PROYECTO / "assets"
    BACKUPS = DATOS / "backups"
    LOGS = DATOS / "logs"

    RESALTADOS_BIBLIA = Path(ruta_datos("resaltados_biblia.json"))
    ULTIMA_LECTURA_BIBLIA = Path(ruta_datos("ultima_lectura_biblia.json"))
    HISTORIAL_REFERENCIAS_BIBLIA = Path(ruta_datos("historial_referencias_biblia.json"))
    CONFIG_APP = Path(ruta_datos("config_app.json"))

    ERROR_LOG = LOGS / "error_log.txt"

    @classmethod
    def asegurar_directorios(cls):
        for ruta in (cls.DATOS, cls.ASSETS, cls.BACKUPS, cls.LOGS):
            ruta.mkdir(parents=True, exist_ok=True)

    @classmethod
    def existe_archivo(cls, ruta):
        return Path(ruta).exists() and Path(ruta).is_file()
