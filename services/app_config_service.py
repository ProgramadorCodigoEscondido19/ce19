import json
import tempfile
import threading
from pathlib import Path


class AppConfigService:
    """Lectura/escritura segura de configuraciones simples en JSON."""

    _bloqueo_archivos = threading.RLock()

    @staticmethod
    def leer_json(ruta, defecto=None):
        path = Path(ruta)
        try:
            with AppConfigService._bloqueo_archivos:
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {} if defecto is None else defecto

    @staticmethod
    def guardar_json(ruta, datos):
        with AppConfigService._bloqueo_archivos:
            return AppConfigService._guardar_json(ruta, datos)

    @staticmethod
    def _guardar_json(ruta, datos):
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        texto = json.dumps(datos, ensure_ascii=False, indent=2)
        # Cada guardado usa su propio temporal: dos eventos de la interfaz
        # pueden escribir simultaneamente sin pisarse el archivo intermedio.
        temporal = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=path.parent,
                prefix=f".{path.name}.", suffix=".tmp", delete=False,
            ) as archivo:
                temporal = Path(archivo.name)
                archivo.write(texto)
            temporal.replace(path)
        finally:
            if temporal is not None:
                temporal.unlink(missing_ok=True)
        return datos
