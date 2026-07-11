from datetime import datetime

from core.app_state import state


TIPOS_FILTRO_GUARDADOS = {
    "Todos": None,
    "Codificador": "tarjeta",
    "Biblia": "fragmento_biblico",
    "Pizarra": "pizarra",
    "Colores": "analisis_colores",
    "Tiempo": "tiempo",
}


class GuardadosService:
    """Servicio para filtrar, ordenar y preparar registros guardados."""

    def __init__(self, guardados=None, carpetas=None):
        self.guardados = guardados or state.guardados
        self.carpetas = carpetas or state.carpetas

    def todos(self):
        return list(self.guardados.obtener())

    def filtrar_por_tipo(self, registros, filtro="Todos"):
        tipo = TIPOS_FILTRO_GUARDADOS.get(filtro)
        if not tipo:
            return list(registros)
        return [r for r in registros if r.get("tipo", "tarjeta") == tipo]

    def buscar(self, registros, texto):
        q = str(texto or "").strip().lower()
        if not q:
            return list(registros)

        claves = ["nombre", "palabra", "referencia", "alfabeto", "resultado", "suma", "carpeta"]
        filtrados = []
        for registro in registros:
            valores = []
            for clave in claves:
                valores.append(str(registro.get(clave, "")))
            contenido = registro.get("contenido", "")
            if isinstance(contenido, dict):
                valores.extend(str(v) for v in contenido.values())
            else:
                valores.append(str(contenido))
            if q in " ".join(valores).lower():
                filtrados.append(registro)
        return filtrados

    def ordenar(self, registros, modo="Recientes"):
        registros = list(registros)
        if modo == "Antiguos":
            return sorted(registros, key=lambda r: str(r.get("fecha", "")))
        if modo == "A-Z":
            return sorted(registros, key=lambda r: str(r.get("nombre") or r.get("palabra") or r.get("referencia") or "").lower())
        if modo == "Resultado":
            def resultado_num(r):
                try:
                    return int(r.get("resultado", 0))
                except Exception:
                    return 0
            return sorted(registros, key=resultado_num, reverse=True)
        return sorted(registros, key=lambda r: str(r.get("fecha", "")), reverse=True)

    def aplicar_vista(self, carpeta_id=None, filtro="Todos", busqueda="", orden="Recientes"):
        registros = self.todos()
        if carpeta_id is not None:
            registros = [r for r in registros if r.get("carpeta_id") == carpeta_id]
        registros = self.filtrar_por_tipo(registros, filtro)
        registros = self.buscar(registros, busqueda)
        registros = self.ordenar(registros, orden)
        return registros

    @staticmethod
    def crear_registro_base(tipo="tarjeta", nombre="", carpeta="TARJETAS", carpeta_id=1):
        return {
            "id": int(datetime.now().timestamp() * 1000),
            "tipo": tipo,
            "nombre": nombre,
            "carpeta": carpeta,
            "carpeta_id": carpeta_id,
            "fecha": datetime.now().isoformat(timespec="seconds"),
        }
