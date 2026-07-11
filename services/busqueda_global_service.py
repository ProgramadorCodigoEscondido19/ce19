from core.app_state import state


class BusquedaGlobalService:
    """Búsqueda global preparada para una futura pantalla de búsqueda.

    Por ahora trabaja sobre guardados y carpetas. No depende de Flet.
    """

    def __init__(self, guardados=None, carpetas=None):
        self.guardados = guardados or state.guardados
        self.carpetas = carpetas or state.carpetas

    def buscar_guardados(self, texto, limite=50):
        q = str(texto or "").strip().lower()
        if not q:
            return []

        resultados = []
        for registro in self.guardados.obtener():
            if self._registro_contiene(registro, q):
                resultados.append(registro)
                if len(resultados) >= limite:
                    break
        return resultados

    def buscar_carpetas(self, texto, limite=30):
        q = str(texto or "").strip().lower()
        if not q:
            return []

        resultados = []
        for carpeta in self.carpetas.obtener():
            nombre = str(carpeta.get("nombre", "")).lower()
            if q in nombre:
                resultados.append(carpeta)
                if len(resultados) >= limite:
                    break
        return resultados

    def buscar_todo(self, texto, limite_guardados=50, limite_carpetas=30):
        return {
            "guardados": self.buscar_guardados(texto, limite_guardados),
            "carpetas": self.buscar_carpetas(texto, limite_carpetas),
        }

    def _registro_contiene(self, registro, q):
        campos = [
            "id",
            "nombre",
            "palabra",
            "referencia",
            "alfabeto",
            "resultado",
            "suma",
            "carpeta",
            "tipo",
            "fecha",
        ]
        valores = [str(registro.get(campo, "")) for campo in campos]
        contenido = registro.get("contenido", "")
        if isinstance(contenido, dict):
            valores.extend(str(v) for v in contenido.values())
        else:
            valores.append(str(contenido))
        return q in " ".join(valores).lower()
