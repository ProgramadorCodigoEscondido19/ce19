from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from core.backup_datos import crear_backup_datos
except Exception:  # pragma: no cover
    crear_backup_datos = None


POSIBLES_GUARDADOS = ["guardados.json", "datos/guardados.json"]
POSIBLES_CARPETAS = ["carpetas.json", "datos/carpetas.json"]


def _raiz() -> Path:
    return Path.cwd()


def _buscar_archivo(candidatos: list[str]) -> Path | None:
    raiz = _raiz()
    for relativo in candidatos:
        ruta = raiz / relativo
        if ruta.exists() and ruta.is_file():
            return ruta
    return None


def _leer_json(ruta: Path | None, defecto: Any) -> Any:
    if ruta is None or not ruta.exists():
        return defecto
    with ruta.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


def _guardar_json(ruta: Path, datos: Any) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)


def _normalizar_lista(datos: Any) -> list[dict]:
    if isinstance(datos, list):
        return [x for x in datos if isinstance(x, dict)]
    if isinstance(datos, dict):
        for clave in ("items", "registros", "guardados", "carpetas"):
            valor = datos.get(clave)
            if isinstance(valor, list):
                return [x for x in valor if isinstance(x, dict)]
    return []


def _extraer_ids_carpetas(carpetas: list[dict]) -> set[int]:
    ids: set[int] = set()
    for carpeta in carpetas:
        try:
            ids.add(int(carpeta.get("id")))
        except Exception:
            pass
    return ids


def _root_carpeta(carpetas: list[dict]) -> tuple[int, str]:
    for carpeta in carpetas:
        if carpeta.get("id") == 1 or str(carpeta.get("nombre", "")).upper() == "TARJETAS":
            try:
                return int(carpeta.get("id", 1)), str(carpeta.get("nombre") or "TARJETAS")
            except Exception:
                return 1, "TARJETAS"
    return 1, "TARJETAS"


def _siguiente_id_guardado(guardados: list[dict]) -> int:
    mayor = 0
    for registro in guardados:
        try:
            mayor = max(mayor, int(registro.get("id", 0)))
        except Exception:
            pass
    return mayor + 1


def _firma_registro(registro: dict) -> str:
    partes = [
        str(registro.get("tipo", "")),
        str(registro.get("palabra", "")),
        str(registro.get("nombre", "")),
        str(registro.get("referencia", "")),
        str(registro.get("resultado", "")),
        str(registro.get("suma", ""))[:200],
    ]
    return "|".join(partes).strip().lower()


def analizar_datos() -> dict:
    ruta_guardados = _buscar_archivo(POSIBLES_GUARDADOS)
    ruta_carpetas = _buscar_archivo(POSIBLES_CARPETAS)

    datos_guardados = _leer_json(ruta_guardados, [])
    datos_carpetas = _leer_json(ruta_carpetas, [])

    guardados = _normalizar_lista(datos_guardados)
    carpetas = _normalizar_lista(datos_carpetas)

    ids_carpetas = _extraer_ids_carpetas(carpetas)
    ids_guardados = set()
    ids_repetidos = []
    faltan_id = 0
    huérfanos = 0
    firmas = {}
    posibles_duplicados = []

    for registro in guardados:
        rid = registro.get("id")
        if rid is None:
            faltan_id += 1
        else:
            try:
                rid_int = int(rid)
                if rid_int in ids_guardados:
                    ids_repetidos.append(rid_int)
                ids_guardados.add(rid_int)
            except Exception:
                faltan_id += 1

        cid = registro.get("carpeta_id")
        if cid is not None:
            try:
                if int(cid) not in ids_carpetas:
                    huérfanos += 1
            except Exception:
                huérfanos += 1

        firma = _firma_registro(registro)
        if firma:
            firmas[firma] = firmas.get(firma, 0) + 1

    for firma, total in firmas.items():
        if total > 1:
            posibles_duplicados.append({"firma": firma[:120], "total": total})

    problemas = []
    if ruta_guardados is None:
        problemas.append("No se encontró guardados.json.")
    if ruta_carpetas is None:
        problemas.append("No se encontró carpetas.json.")
    if faltan_id:
        problemas.append(f"Hay {faltan_id} guardados sin ID válido.")
    if ids_repetidos:
        problemas.append(f"Hay IDs repetidos en guardados: {sorted(set(ids_repetidos))[:20]}.")
    if huérfanos:
        problemas.append(f"Hay {huérfanos} guardados apuntando a carpetas inexistentes.")
    if posibles_duplicados:
        problemas.append(f"Hay {len(posibles_duplicados)} grupos de posibles duplicados.")

    return {
        "ruta_guardados": str(ruta_guardados) if ruta_guardados else "",
        "ruta_carpetas": str(ruta_carpetas) if ruta_carpetas else "",
        "total_guardados": len(guardados),
        "total_carpetas": len(carpetas),
        "faltan_id": faltan_id,
        "ids_repetidos": sorted(set(ids_repetidos)),
        "huerfanos": huérfanos,
        "posibles_duplicados": posibles_duplicados[:30],
        "problemas": problemas,
        "reparable": bool(faltan_id or huérfanos),
    }


def reparar_datos(aplicar: bool = False) -> dict:
    ruta_guardados = _buscar_archivo(POSIBLES_GUARDADOS)
    ruta_carpetas = _buscar_archivo(POSIBLES_CARPETAS)

    if ruta_guardados is None:
        raise FileNotFoundError("No se encontró guardados.json")

    datos_guardados = _leer_json(ruta_guardados, [])
    datos_carpetas = _leer_json(ruta_carpetas, [])
    guardados = _normalizar_lista(datos_guardados)
    carpetas = _normalizar_lista(datos_carpetas)

    ids_carpetas = _extraer_ids_carpetas(carpetas)
    root_id, root_nombre = _root_carpeta(carpetas)
    siguiente_id = _siguiente_id_guardado(guardados)

    asignados = 0
    movidos_a_raiz = 0

    for registro in guardados:
        necesita_id = False
        try:
            int(registro.get("id"))
        except Exception:
            necesita_id = True

        if registro.get("id") is None or necesita_id:
            registro["id"] = siguiente_id
            siguiente_id += 1
            asignados += 1

        cid = registro.get("carpeta_id")
        if cid is not None:
            try:
                carpeta_ok = int(cid) in ids_carpetas
            except Exception:
                carpeta_ok = False
            if not carpeta_ok:
                registro["carpeta_id"] = root_id
                registro["carpeta"] = root_nombre
                movidos_a_raiz += 1

    backup = None
    if aplicar:
        if crear_backup_datos is not None:
            try:
                backup = crear_backup_datos("antes_reparar")
            except Exception:
                backup = None
        _guardar_json(ruta_guardados, guardados)

    return {
        "aplicado": aplicar,
        "ruta_guardados": str(ruta_guardados),
        "ids_asignados": asignados,
        "movidos_a_raiz": movidos_a_raiz,
        "backup": backup,
    }


def reporte_reparacion_como_texto(reporte: dict) -> str:
    lineas = [
        "MANTENIMIENTO / REPARACIÓN DE DATOS",
        "",
        f"Guardados: {reporte.get('total_guardados', '-')}",
        f"Carpetas: {reporte.get('total_carpetas', '-')}",
        f"Guardados sin ID válido: {reporte.get('faltan_id', 0)}",
        f"Guardados con carpeta inexistente: {reporte.get('huerfanos', 0)}",
        f"IDs repetidos: {reporte.get('ids_repetidos', [])}",
        f"Posibles grupos duplicados: {len(reporte.get('posibles_duplicados') or [])}",
        "",
        "Problemas detectados:",
    ]
    problemas = reporte.get("problemas") or []
    if not problemas:
        lineas.append("- No se detectaron problemas reparables.")
    else:
        for problema in problemas:
            lineas.append(f"- {problema}")
    return "\n".join(lineas)
