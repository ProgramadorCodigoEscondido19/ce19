from pathlib import Path


class AppPaths:
    """Rutas centrales de Codigo Escondido 19.

    Usar este archivo evita repetir nombres de archivos en distintas vistas/servicios.
    Todas las rutas son relativas al directorio del proyecto.
    """

    ROOT = Path(".")
    DATOS = Path("datos")
    ASSETS = Path("assets")
    BACKUPS = Path("backups")
    LOGS = Path("logs")

    GUARDADOS = DATOS / "guardados.json"
    CARPETAS = DATOS / "carpetas.json"
    RESALTADOS_BIBLIA = DATOS / "resaltados_biblia.json"
    ULTIMA_LECTURA_BIBLIA = DATOS / "ultima_lectura_biblia.json"
    HISTORIAL_REFERENCIAS_BIBLIA = DATOS / "historial_referencias_biblia.json"
    CONFIG_APP = DATOS / "config_app.json"

    ERROR_LOG = LOGS / "error_log.txt"

    @classmethod
    def asegurar_directorios(cls):
        for ruta in (cls.DATOS, cls.ASSETS, cls.BACKUPS, cls.LOGS):
            ruta.mkdir(parents=True, exist_ok=True)

    @classmethod
    def existe_archivo(cls, ruta):
        return Path(ruta).exists() and Path(ruta).is_file()
