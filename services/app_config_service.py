import json
from pathlib import Path


class AppConfigService:
    """Lectura/escritura segura de configuraciones simples en JSON."""

    @staticmethod
    def leer_json(ruta, defecto=None):
        path = Path(ruta)
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {} if defecto is None else defecto

    @staticmethod
    def guardar_json(ruta, datos):
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        texto = json.dumps(datos, ensure_ascii=False, indent=2)
        temporal = path.with_name(f".{path.name}.tmp")
        temporal.write_text(texto, encoding="utf-8")
        temporal.replace(path)
        return datos
