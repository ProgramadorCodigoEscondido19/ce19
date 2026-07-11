import json
from datetime import datetime
from pathlib import Path


class ExportacionService:
    """Exportaciones simples sin depender de Flet."""

    SALIDA_DIR = Path("exportaciones")

    @classmethod
    def _asegurar_salida(cls):
        cls.SALIDA_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def registros_a_texto(cls, registros, titulo="Guardados exportados"):
        lineas = [titulo, "=" * len(titulo), ""]
        for i, registro in enumerate(registros, start=1):
            lineas.append(f"{i}. {registro.get('nombre') or registro.get('palabra') or registro.get('referencia') or 'Sin titulo'}")
            lineas.append(f"Tipo: {registro.get('tipo', 'tarjeta')}")
            if registro.get("carpeta"):
                lineas.append(f"Carpeta: {registro.get('carpeta')}")
            if registro.get("referencia"):
                lineas.append(f"Referencia: {registro.get('referencia')}")
            contenido = registro.get("contenido", "")
            if isinstance(contenido, dict):
                texto = contenido.get("texto") or contenido.get("texto_original") or str(contenido)
            else:
                texto = str(contenido or "")
            if texto:
                lineas.append("Contenido:")
                lineas.append(texto)
            if registro.get("resultado"):
                lineas.append(f"Resultado: {registro.get('resultado')}")
            lineas.append("-" * 48)
        return "\n".join(lineas)

    @classmethod
    def exportar_txt(cls, registros, nombre_base="guardados_exportados"):
        cls._asegurar_salida()
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta = cls.SALIDA_DIR / f"{nombre_base}_{fecha}.txt"
        ruta.write_text(cls.registros_a_texto(registros), encoding="utf-8")
        return str(ruta)

    @classmethod
    def exportar_json(cls, registros, nombre_base="guardados_exportados"):
        cls._asegurar_salida()
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta = cls.SALIDA_DIR / f"{nombre_base}_{fecha}.json"
        ruta.write_text(json.dumps(list(registros), ensure_ascii=False, indent=2), encoding="utf-8")
        return str(ruta)
