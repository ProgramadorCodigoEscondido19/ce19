import flet as ft


class RutasService:
    """Fuente única para las rutas de la app.

    Evita repetir el orden, nombres e íconos de las páginas en router.py,
    main.py y servicios de arranque.
    """

    ORDEN_RUTAS = [
        "inicio",
        "pizarra",
        "colores",
        "biblia",
        "tiempo",
        "calculadora",
        "guardados",
    ]

    META_RUTAS = {
        "inicio": {"label": "Inicio", "icon": ft.Icons.HOME},
        "pizarra": {"label": "Pizarra", "icon": ft.Icons.EDIT},
        "colores": {"label": "Colores", "icon": ft.Icons.COLOR_LENS},
        "biblia": {"label": "Biblia", "icon": ft.Icons.BOOK},
        "tiempo": {"label": "Tiempo", "icon": ft.Icons.SCHEDULE},
        "calculadora": {"label": "Calc", "icon": ft.Icons.CALCULATE},
        "guardados": {"label": "Guardados", "icon": ft.Icons.SAVE},
    }

    @classmethod
    def orden(cls):
        return list(cls.ORDEN_RUTAS)

    @classmethod
    def meta(cls, ruta):
        return cls.META_RUTAS.get(
            ruta,
            {"label": str(ruta).title(), "icon": ft.Icons.CIRCLE_OUTLINED},
        )

    @classmethod
    def label(cls, ruta):
        return cls.meta(ruta).get("label", str(ruta).title())

    @classmethod
    def icono(cls, ruta):
        return cls.meta(ruta).get("icon", ft.Icons.CIRCLE_OUTLINED)

    @classmethod
    def indice(cls, ruta):
        try:
            return cls.ORDEN_RUTAS.index(ruta)
        except ValueError:
            return 0

    @classmethod
    def ruta_por_indice(cls, indice):
        if 0 <= indice < len(cls.ORDEN_RUTAS):
            return cls.ORDEN_RUTAS[indice]
        return cls.ORDEN_RUTAS[0]

    @classmethod
    def existe(cls, ruta):
        return ruta in cls.ORDEN_RUTAS

    @classmethod
    def navigation_destinations(cls, icono_inicio=None):
        destinos = []
        for ruta in cls.ORDEN_RUTAS:
            if ruta == "inicio" and icono_inicio is not None:
                destinos.append(
                    ft.NavigationBarDestination(
                        icon=icono_inicio(26),
                        selected_icon=icono_inicio(30),
                        label=cls.label(ruta),
                    )
                )
            else:
                destinos.append(
                    ft.NavigationBarDestination(
                        icon=cls.icono(ruta),
                        label=cls.label(ruta),
                    )
                )
        return destinos
