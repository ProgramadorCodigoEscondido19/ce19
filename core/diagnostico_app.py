from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime


ARCHIVOS_IMPORTANTES = [
    "guardados.json",
    "carpetas.json",
    "resaltados_biblia.json",
    "ultima_lectura_biblia.json",
    "biblia_ultima_lectura.json",
    "tiempo.json",
    "colores.json",
]


def _leer_json(ruta: Path):
    try:
        if not ruta.exists():
            return False, "no existe", None
        texto = ruta.read_text(encoding="utf-8")
        if not texto.strip():
            return False, "vacío", None
        return True, "ok", json.loads(texto)
    except Exception as error:
        return False, str(error), None


def _contar_datos(nombre: str, datos):
    if isinstance(datos, list):
        return len(datos)
    if isinstance(datos, dict):
        for clave in ("guardados", "carpetas", "resaltados", "items", "datos"):
            valor = datos.get(clave)
            if isinstance(valor, list):
                return len(valor)
            if isinstance(valor, dict):
                return len(valor)
        return len(datos)
    return 0


def _buscar_archivo(base: Path, nombre: str) -> Path | None:
    candidatos = [
        base / nombre,
        base / "datos" / nombre,
        base / "data" / nombre,
        base / "assets" / nombre,
    ]
    for ruta in candidatos:
        if ruta.exists():
            return ruta
    return None


def crear_reporte_diagnostico(base_dir: str | Path | None = None) -> dict:
    """Crea un diagnóstico liviano de datos y estructura del proyecto.

    No modifica archivos. Sirve para detectar JSON dañados, faltantes,
    backups existentes y conteos generales antes de seguir editando la app.
    """
    base = Path(base_dir or ".").resolve()
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    archivos = []
    advertencias = []
    totales = {}

    for nombre in ARCHIVOS_IMPORTANTES:
        ruta = _buscar_archivo(base, nombre)
        if ruta is None:
            archivos.append({"archivo": nombre, "estado": "no encontrado", "ruta": ""})
            continue

        ok, estado, datos = _leer_json(ruta)
        item = {
            "archivo": nombre,
            "estado": estado,
            "ruta": str(ruta.relative_to(base)) if str(ruta).startswith(str(base)) else str(ruta),
            "tamano_bytes": ruta.stat().st_size if ruta.exists() else 0,
        }
        if ok:
            cantidad = _contar_datos(nombre, datos)
            item["cantidad"] = cantidad
            totales[nombre] = cantidad
        else:
            advertencias.append(f"{nombre}: {estado}")
        archivos.append(item)

    backups_dir = base / "backups"
    backups = []
    if backups_dir.exists():
        for carpeta in sorted(backups_dir.iterdir(), reverse=True):
            if carpeta.is_dir():
                backups.append(carpeta.name)

    carpetas_total = totales.get("carpetas.json", 0)
    guardados_total = totales.get("guardados.json", 0)

    if guardados_total == 0:
        advertencias.append("No se detectaron guardados en guardados.json o el archivo no fue encontrado.")
    if carpetas_total == 0:
        advertencias.append("No se detectaron carpetas en carpetas.json o el archivo no fue encontrado.")

    return {
        "fecha": ahora,
        "base": str(base),
        "archivos": archivos,
        "backups": backups[:20],
        "total_backups": len(backups),
        "totales": totales,
        "advertencias": advertencias,
    }


def reporte_como_texto(reporte: dict) -> str:
    lineas = []
    lineas.append("DIAGNÓSTICO DE CÓDIGO ESCONDIDO 19")
    lineas.append(f"Fecha: {reporte.get('fecha')}")
    lineas.append(f"Proyecto: {reporte.get('base')}")
    lineas.append("")
    lineas.append("ARCHIVOS")

    for item in reporte.get("archivos", []):
        cantidad = item.get("cantidad")
        cantidad_txt = f" | registros: {cantidad}" if cantidad is not None else ""
        tamano = item.get("tamano_bytes")
        tamano_txt = f" | {tamano} bytes" if tamano is not None else ""
        ruta = item.get("ruta") or "sin ruta"
        lineas.append(f"- {item.get('archivo')}: {item.get('estado')} | {ruta}{cantidad_txt}{tamano_txt}")

    lineas.append("")
    lineas.append(f"BACKUPS: {reporte.get('total_backups', 0)}")
    for nombre in reporte.get("backups", [])[:10]:
        lineas.append(f"- {nombre}")

    advertencias = reporte.get("advertencias") or []
    lineas.append("")
    lineas.append("ADVERTENCIAS")
    if advertencias:
        for aviso in advertencias:
            lineas.append(f"- {aviso}")
    else:
        lineas.append("- Sin advertencias importantes.")

    return "\n".join(lineas)
