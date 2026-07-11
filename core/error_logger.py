from __future__ import annotations

from datetime import datetime
from pathlib import Path
import traceback


PROYECTO_RAIZ = Path(__file__).resolve().parents[1]
CARPETA_LOGS = PROYECTO_RAIZ / "logs"
ARCHIVO_ERRORES = CARPETA_LOGS / "error_log.txt"


def _asegurar_logs():
    CARPETA_LOGS.mkdir(parents=True, exist_ok=True)


def ruta_log() -> str:
    _asegurar_logs()
    return str(ARCHIVO_ERRORES)


def registrar_error(origen: str, error=None, contexto: str | None = None):
    """Guarda un error sin romper la app si el registro falla."""
    try:
        _asegurar_logs()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        partes = [
            "=" * 80,
            f"FECHA: {fecha}",
            f"ORIGEN: {origen}",
        ]

        if contexto:
            partes.append(f"CONTEXTO: {contexto}")

        if error is not None:
            partes.append(f"ERROR: {repr(error)}")

        traza = traceback.format_exc()
        if traza and traza.strip() != "NoneType: None":
            partes.append("TRACEBACK:")
            partes.append(traza)

        partes.append("")
        with ARCHIVO_ERRORES.open("a", encoding="utf-8") as archivo:
            archivo.write("\n".join(partes))
    except Exception:
        pass


def leer_ultimos_errores(max_chars: int = 12000) -> str:
    try:
        _asegurar_logs()
        if not ARCHIVO_ERRORES.exists():
            return "Todavía no hay errores registrados."

        texto = ARCHIVO_ERRORES.read_text(encoding="utf-8", errors="replace")
        if not texto.strip():
            return "Todavía no hay errores registrados."

        if len(texto) > max_chars:
            return "... LOG RECORTADO, MOSTRANDO EL FINAL ...\n\n" + texto[-max_chars:]
        return texto
    except Exception as error:
        return f"No se pudo leer el log de errores: {error}"


def limpiar_log_errores():
    try:
        _asegurar_logs()
        ARCHIVO_ERRORES.write_text("", encoding="utf-8")
        return True
    except Exception:
        return False
