import json
from pathlib import Path
from datetime import datetime


class NotasBibliaService:
    """Guarda notas personales por versiculo biblico.

    El archivo se guarda en datos/notas_biblia.json.
    La clave usada es la misma clave interna del versiculo: Libro|Capitulo|Versiculo.
    """

    def __init__(self, ruta=None):
        self.ruta = Path(ruta or "datos/notas_biblia.json")
        self.ruta.parent.mkdir(parents=True, exist_ok=True)

    def cargar(self):
        if not self.ruta.exists():
            return {}

        try:
            data = json.loads(self.ruta.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def guardar_todo(self, data):
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.ruta.write_text(
            json.dumps(data or {}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def obtener(self, clave):
        if not clave:
            return ""
        item = self.cargar().get(str(clave), {})
        if isinstance(item, dict):
            return item.get("nota", "") or ""
        if isinstance(item, str):
            return item
        return ""

    def guardar(self, clave, referencia, texto_biblico, nota):
        clave = str(clave or "").strip()
        nota = str(nota or "").strip()
        if not clave:
            return False

        data = self.cargar()

        if not nota:
            if clave in data:
                del data[clave]
                self.guardar_todo(data)
            return True

        data[clave] = {
            "referencia": str(referencia or clave),
            "texto_biblico": str(texto_biblico or ""),
            "nota": nota,
            "actualizado": datetime.now().isoformat(timespec="seconds"),
        }
        self.guardar_todo(data)
        return True

    def eliminar(self, clave):
        clave = str(clave or "").strip()
        if not clave:
            return False
        data = self.cargar()
        if clave in data:
            del data[clave]
            self.guardar_todo(data)
        return True

    def listar(self):
        data = self.cargar()
        items = []
        for clave, item in data.items():
            if isinstance(item, dict):
                items.append({"clave": clave, **item})
            else:
                items.append({"clave": clave, "referencia": clave, "nota": str(item)})
        return sorted(items, key=lambda x: x.get("actualizado", ""), reverse=True)
