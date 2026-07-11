from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path


ARCHIVOS_DATOS = [
    "guardados.json",
    "carpetas.json",
    "config_tiempo.json",
    "analisis_colores_historial.json",
    "biblia_ultima_lectura.json",
    "ultima_lectura_biblia.json",
    "resaltados_biblia.json",
    "biblia_resaltados.json",
    "datos/guardados.json",
    "datos/carpetas.json",
    "datos/config_tiempo.json",
    "datos/analisis_colores_historial.json",
    "datos/biblia_ultima_lectura.json",
    "datos/ultima_lectura_biblia.json",
    "datos/resaltados_biblia.json",
    "datos/biblia_resaltados.json",
]


def _raiz_proyecto() -> Path:
    return Path.cwd()


def _asegurar_json_valido(ruta: Path) -> bool:
    if not ruta.exists() or not ruta.is_file():
        return False

    if ruta.suffix.lower() != ".json":
        return True

    try:
        with ruta.open("r", encoding="utf-8") as archivo:
            json.load(archivo)
        return True
    except Exception:
        # Si el JSON está dañado, igual lo copiamos para no perderlo.
        return True


def archivos_existentes() -> list[Path]:
    raiz = _raiz_proyecto()
    encontrados = []

    for relativo in ARCHIVOS_DATOS:
        ruta = raiz / relativo
        if _asegurar_json_valido(ruta):
            encontrados.append(ruta)

    return encontrados


def crear_backup_datos(motivo: str = "manual") -> dict:
    raiz = _raiz_proyecto()
    archivos = archivos_existentes()
    ahora = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre = f"backup_{motivo}_{ahora}"
    carpeta_destino = raiz / "backups" / nombre
    carpeta_destino.mkdir(parents=True, exist_ok=True)

    copiados = []

    for origen in archivos:
        relativo = origen.relative_to(raiz)
        destino = carpeta_destino / relativo
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origen, destino)
        copiados.append(str(relativo))

    manifiesto = {
        "motivo": motivo,
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "carpeta": str(carpeta_destino),
        "archivos": copiados,
        "total": len(copiados),
    }

    with (carpeta_destino / "manifest.json").open("w", encoding="utf-8") as archivo:
        json.dump(manifiesto, archivo, ensure_ascii=False, indent=2)

    return manifiesto


def crear_backup_inicio() -> dict | None:
    raiz = _raiz_proyecto()
    hoy = datetime.now().strftime("%Y%m%d")
    carpeta_backups = raiz / "backups"

    if carpeta_backups.exists():
        for carpeta in carpeta_backups.iterdir():
            if carpeta.is_dir() and carpeta.name.startswith(f"backup_inicio_{hoy}"):
                return None

    if not archivos_existentes():
        return None

    return crear_backup_datos("inicio")



def listar_backups(limite: int = 20) -> list[dict]:
    """Devuelve los backups disponibles, del más reciente al más antiguo."""
    raiz = _raiz_proyecto()
    carpeta_backups = raiz / "backups"

    if not carpeta_backups.exists():
        return []

    resultados = []

    for carpeta in carpeta_backups.iterdir():
        if not carpeta.is_dir() or not carpeta.name.startswith("backup_"):
            continue

        manifiesto_path = carpeta / "manifest.json"
        datos = {
            "nombre": carpeta.name,
            "carpeta": str(carpeta),
            "fecha": "",
            "motivo": "",
            "total": 0,
            "archivos": [],
        }

        if manifiesto_path.exists():
            try:
                with manifiesto_path.open("r", encoding="utf-8") as archivo:
                    manifiesto = json.load(archivo)
                datos.update({
                    "fecha": manifiesto.get("fecha", ""),
                    "motivo": manifiesto.get("motivo", ""),
                    "total": manifiesto.get("total", 0),
                    "archivos": manifiesto.get("archivos", []),
                })
            except Exception:
                pass

        try:
            datos["timestamp"] = carpeta.stat().st_mtime
        except Exception:
            datos["timestamp"] = 0

        resultados.append(datos)

    resultados.sort(key=lambda item: item.get("timestamp", 0), reverse=True)
    return resultados[:limite]


def restaurar_backup(carpeta_backup: str | Path, crear_respaldo_actual: bool = True) -> dict:
    """Restaura los archivos de datos desde una carpeta de backup."""
    raiz = _raiz_proyecto()
    carpeta = Path(carpeta_backup)

    if not carpeta.is_absolute():
        carpeta = raiz / carpeta

    if not carpeta.exists() or not carpeta.is_dir():
        raise FileNotFoundError(f"No existe la carpeta de backup: {carpeta}")

    if crear_respaldo_actual:
        crear_backup_datos("antes_restaurar")

    manifiesto_path = carpeta / "manifest.json"
    archivos: list[str] = []

    if manifiesto_path.exists():
        try:
            with manifiesto_path.open("r", encoding="utf-8") as archivo:
                manifiesto = json.load(archivo)
            archivos = [str(item) for item in manifiesto.get("archivos", [])]
        except Exception:
            archivos = []

    if not archivos:
        archivos = [
            str(ruta.relative_to(carpeta))
            for ruta in carpeta.rglob("*.json")
            if ruta.name != "manifest.json"
        ]

    restaurados = []

    for relativo in archivos:
        origen = carpeta / relativo
        destino = raiz / relativo

        if not origen.exists() or not origen.is_file():
            continue

        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origen, destino)
        restaurados.append(relativo)

    return {
        "backup": str(carpeta),
        "total": len(restaurados),
        "archivos": restaurados,
    }
