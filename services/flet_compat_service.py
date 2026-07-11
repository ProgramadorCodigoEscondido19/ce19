"""Compatibilidad pequeña para distintas versiones de Flet.

Este archivo evita repetir parches por toda la app cuando una version de Flet
no trae exactamente el mismo nombre de atributo o control.
"""

import flet as ft


class FletCompatService:
    """Helpers seguros para diferencias menores entre versiones de Flet."""

    @staticmethod
    def box_fit_cover():
        return getattr(getattr(ft, "BoxFit", None), "COVER", None)

    @staticmethod
    def box_fit_contain():
        return getattr(getattr(ft, "BoxFit", None), "CONTAIN", None)

    @staticmethod
    def color_con_opacidad(opacidad, color):
        try:
            return ft.Colors.with_opacity(opacidad, color)
        except Exception:
            return color

    @staticmethod
    def icono(nombre, fallback=None):
        iconos = getattr(ft, "Icons", None)
        if iconos is None:
            return fallback
        return getattr(iconos, nombre, fallback)

    @staticmethod
    def texto(valor, **kwargs):
        """Crea ft.Text eliminando kwargs problemáticos en versiones viejas.

        Ejemplo: algunas versiones no aceptan shadow= en Text.
        """
        kwargs.pop("shadow", None)
        try:
            return ft.Text(valor, **kwargs)
        except TypeError:
            # Segundo intento quitando opciones modernas no críticas.
            for clave in ("selectable", "max_lines", "overflow"):
                kwargs.pop(clave, None)
            return ft.Text(valor, **kwargs)

    @staticmethod
    def dropdown(**kwargs):
        """Crea Dropdown tolerando on_select/on_change segun version."""
        try:
            return ft.Dropdown(**kwargs)
        except TypeError as error:
            mensaje = str(error)
            if "on_change" in mensaje and "on_change" in kwargs:
                kwargs["on_select"] = kwargs.pop("on_change")
                return ft.Dropdown(**kwargs)
            if "on_select" in mensaje and "on_select" in kwargs:
                kwargs["on_change"] = kwargs.pop("on_select")
                return ft.Dropdown(**kwargs)
            raise
