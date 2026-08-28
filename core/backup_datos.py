from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from core.rutas import carpeta_datos_usuario

CARPETAS_EXCLUIDAS = {"backups", "updates"}


def _raiz_datos() -> Path:
    return carpeta_datos_usuario()


def archivos_existentes() -> list[Path]:
    raiz = _raiz_datos()
    if not raiz.exists():
        return []

    return sorted(
        ruta
        for ruta in raiz.rglob("*")
        if ruta.is_file()
        and not any(
            parte.lower() in CARPETAS_EXCLUIDAS
            for parte in ruta.relative_to(raiz).parts[:-1]
        )
    )


def crear_backup_datos(motivo: str = "manual") -> dict:
    raiz = _raiz_datos()
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
    raiz = _raiz_datos()
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
    raiz = _raiz_datos()
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
    raiz = _raiz_datos()
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
