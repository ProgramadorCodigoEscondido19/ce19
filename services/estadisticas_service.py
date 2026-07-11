from collections import Counter
from core.app_state import state


class EstadisticasService:
    """Cálculos de conteos y resumen general de la app."""

    def __init__(self, guardados=None, carpetas=None):
        self.guardados = guardados or state.guardados
        self.carpetas = carpetas or state.carpetas

    def resumen_guardados(self):
        registros = list(self.guardados.obtener())
        por_tipo = Counter(r.get("tipo", "tarjeta") for r in registros)
        por_carpeta = Counter(r.get("carpeta", "TARJETAS") for r in registros)

        return {
            "total": len(registros),
            "por_tipo": dict(por_tipo),
            "por_carpeta": dict(por_carpeta),
            "carpetas_total": len(list(self.carpetas.obtener())),
        }

    def resumen_texto(self):
        resumen = self.resumen_guardados()
        lineas = [
            "RESUMEN DE CODIGO ESCONDIDO 19",
            "",
            f"Guardados totales: {resumen['total']}",
            f"Carpetas totales: {resumen['carpetas_total']}",
            "",
            "Por tipo:",
        ]
        for tipo, cantidad in sorted(resumen["por_tipo"].items()):
            lineas.append(f"- {tipo}: {cantidad}")

        lineas.append("")
        lineas.append("Por carpeta:")
        for carpeta, cantidad in sorted(resumen["por_carpeta"].items()):
            lineas.append(f"- {carpeta}: {cantidad}")

        return "\n".join(lineas)
