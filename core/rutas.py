import os
import shutil
import sys
from pathlib import Path


APP_CARPETA_DATOS = "CODIGO ESCONDIDO 19"
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent


def _base_datos_usuario():
    variable = os.environ.get("FLET_APP_STORAGE_DATA")

    if variable:
        return Path(variable) / APP_CARPETA_DATOS

    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming"
        return Path(base) / APP_CARPETA_DATOS

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_CARPETA_DATOS

    return Path.home() / ".local" / "share" / APP_CARPETA_DATOS


DATOS_USUARIO = _base_datos_usuario()


def carpeta_datos_usuario():
    candidatos = [
        DATOS_USUARIO,
        Path.home() / APP_CARPETA_DATOS,
        RAIZ_PROYECTO / "datos_usuario",
    ]

    for carpeta in candidatos:
        try:
            carpeta.mkdir(parents=True, exist_ok=True)
            return carpeta
        except OSError:
            continue

    return RAIZ_PROYECTO / "datos"


def ruta_recurso(ruta_relativa):
    return str(RAIZ_PROYECTO / ruta_relativa)


def ruta_datos(nombre_archivo, copiar_desde_datos=True):
    destino = carpeta_datos_usuario() / nombre_archivo

    if not destino.exists() and copiar_desde_datos:
        origen = RAIZ_PROYECTO / "datos" / nombre_archivo

        if origen.exists():
            try:
                destino.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(origen, destino)
            except OSError:
                return str(origen)

    return str(destino)


def ruta_exportacion(nombre_archivo):
    carpeta = carpeta_datos_usuario() / "exportaciones"
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
    except OSError:
        carpeta = RAIZ_PROYECTO / "datos" / "exportaciones"
    return str(carpeta / nombre_archivo)
