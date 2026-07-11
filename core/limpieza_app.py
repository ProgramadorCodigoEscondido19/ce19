from __future__ import annotations

import os
import shutil
from pathlib import Path
from datetime import datetime

BASE_DIR = Path.cwd()
BACKUPS_DIR = BASE_DIR / "backups"
LOGS_DIR = BASE_DIR / "logs"
ERROR_LOG = LOGS_DIR / "error_log.txt"


def _fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


def _fecha_archivo(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def listar_backups_locales():
    if not BACKUPS_DIR.exists():
        return []

    backups = []
    for item in BACKUPS_DIR.iterdir():
        if not item.is_dir():
            continue
        total = 0
        archivos = 0
        for archivo in item.rglob("*"):
            if archivo.is_file():
                archivos += 1
                try:
                    total += archivo.stat().st_size
                except OSError:
                    pass
        backups.append({
            "nombre": item.name,
            "ruta": str(item),
            "fecha_ts": _fecha_archivo(item),
            "fecha": datetime.fromtimestamp(_fecha_archivo(item)).strftime("%Y-%m-%d %H:%M:%S"),
            "archivos": archivos,
            "bytes": total,
            "tamano": _fmt_bytes(total),
        })

    backups.sort(key=lambda x: x.get("fecha_ts", 0), reverse=True)
    return backups


def reporte_limpieza():
    backups = listar_backups_locales()
    total_backups_bytes = sum(b.get("bytes", 0) for b in backups)
    log_size = ERROR_LOG.stat().st_size if ERROR_LOG.exists() else 0

    return {
        "backups_total": len(backups),
        "backups_tamano": _fmt_bytes(total_backups_bytes),
        "backups": backups[:20],
        "log_existe": ERROR_LOG.exists(),
        "log_tamano": _fmt_bytes(log_size),
        "log_bytes": log_size,
        "backups_dir": str(BACKUPS_DIR),
        "logs_dir": str(LOGS_DIR),
    }


def reporte_limpieza_texto(reporte: dict | None = None) -> str:
    reporte = reporte or reporte_limpieza()
    lineas = [
        "REPORTE DE LIMPIEZA",
        "====================",
        f"Backups detectados: {reporte.get('backups_total', 0)}",
        f"Tamaño total de backups: {reporte.get('backups_tamano', '0 B')}",
        f"Log de errores: {reporte.get('log_tamano', '0 B')}",
        "",
        "Últimos backups:",
    ]
    for backup in reporte.get("backups", []):
        lineas.append(f"- {backup.get('nombre')} | {backup.get('fecha')} | {backup.get('tamano')}")
    return "\n".join(lineas)


def limpiar_backups_antiguos(mantener: int = 10):
    backups = listar_backups_locales()
    borrar = backups[mantener:]
    eliminados = []
    errores = []

    for backup in borrar:
        ruta = Path(backup.get("ruta", ""))
        try:
            if ruta.exists() and ruta.is_dir():
                shutil.rmtree(ruta)
                eliminados.append(backup)
        except Exception as error:
            errores.append({"backup": backup.get("nombre"), "error": str(error)})

    return {
        "mantener": mantener,
        "eliminados_total": len(eliminados),
        "errores_total": len(errores),
        "eliminados": eliminados,
        "errores": errores,
    }


def limpiar_log_errores_si_pesa(max_kb: int = 512):
    LOGS_DIR.mkdir(exist_ok=True)
    if not ERROR_LOG.exists():
        return {"limpiado": False, "motivo": "No existe log de errores.", "bytes_antes": 0}

    size = ERROR_LOG.stat().st_size
    limite = max_kb * 1024
    if size <= limite:
        return {
            "limpiado": False,
            "motivo": f"El log pesa {_fmt_bytes(size)}, no supera el límite de {_fmt_bytes(limite)}.",
            "bytes_antes": size,
        }

    archivo_historico = LOGS_DIR / f"error_log_archivado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    ERROR_LOG.replace(archivo_historico)
    ERROR_LOG.write_text("", encoding="utf-8")
    return {
        "limpiado": True,
        "motivo": f"Log archivado como {archivo_historico.name}.",
        "bytes_antes": size,
        "archivo_historico": str(archivo_historico),
    }


def ejecutar_limpieza_segura(mantener_backups: int = 10, max_log_kb: int = 512):
    return {
        "backups": limpiar_backups_antiguos(mantener_backups),
        "log": limpiar_log_errores_si_pesa(max_log_kb),
        "reporte_final": reporte_limpieza(),
    }
