"""Registro central de vistas.

Mantiene AppStartupService mas limpio y deja en un solo lugar las clases de vistas
que se registran en el router.
"""


class VistasRegistryService:
    @staticmethod
    def registrar_todas(router, page):
        # Cada vista se importa y se crea solo cuando el usuario la abre.
        # Esto evita que Biblia y Pizarra hagan pesado el arranque.
        def crear_inicio():
            from vistas.inicio import InicioView
            return InicioView(page, router)

        def crear_pizarra():
            from vistas.pizarra import PizarraView
            return PizarraView(page, router)

        def crear_colores():
            from vistas.analizador_colores import AnalizadorColoresView
            return AnalizadorColoresView(page, router)

        def crear_biblia():
            from vistas.biblia import BibliaView
            return BibliaView(page, router)

        def crear_tiempo():
            from vistas.tiempo import TiempoView
            return TiempoView(page, router)

        def crear_calculadora():
            from vistas.calculadora import CalculadoraView
            return CalculadoraView(page, router)

        def crear_ajustes():
            from vistas.ajustes import AjustesView
            return AjustesView(page, router)

        fabricas = {
            "inicio": crear_inicio,
            "pizarra": crear_pizarra,
            "colores": crear_colores,
            "biblia": crear_biblia,
            "tiempo": crear_tiempo,
            "calculadora": crear_calculadora,
            "ajustes": crear_ajustes,
        }

        for ruta, fabrica in fabricas.items():
            router.registrar_lazy(ruta, fabrica)

        return fabricas
