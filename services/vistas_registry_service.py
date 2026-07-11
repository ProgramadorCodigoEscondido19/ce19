"""Registro central de vistas.

Mantiene AppStartupService mas limpio y deja en un solo lugar las clases de vistas
que se registran en el router.
"""


class VistasRegistryService:
    @staticmethod
    def registrar_todas(router, page):
        # Imports internos para no cargar vistas hasta que la app ya este iniciando.
        from vistas.analizador_colores import AnalizadorColoresView
        from vistas.biblia import BibliaView
        from vistas.calculadora import CalculadoraView
        from vistas.guardados import GuardadosView
        from vistas.inicio import InicioView
        from vistas.pizarra import PizarraView
        from vistas.tiempo import TiempoView

        vistas = {
            "inicio": InicioView(page, router),
            "pizarra": PizarraView(page, router),
            "colores": AnalizadorColoresView(page, router),
            "biblia": BibliaView(page, router),
            "tiempo": TiempoView(page, router),
            "calculadora": CalculadoraView(page, router),
            "guardados": GuardadosView(page, router),
        }

        for ruta, vista in vistas.items():
            router.registrar(ruta, vista)

        return vistas
