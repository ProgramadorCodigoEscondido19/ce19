"""Leyenda reutilizable de la relacion numerologica de colores."""

import flet as ft

from logica.analizador_colores import DIGITO_COLORES
from logica.circulo_biblico import COLOR_CONTORNO, color_texto_para_digito


def leyenda_nueve_colores():
    controles = []
    for numero in range(1, 10):
        color = DIGITO_COLORES[numero]["hex"]
        controles.append(
            ft.Container(
                width=58,
                height=34,
                alignment=ft.Alignment(0, 0),
                bgcolor=color,
                border=ft.Border.all(1.2, COLOR_CONTORNO),
                border_radius=10,
                content=ft.Text(
                    str(numero),
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=color_texto_para_digito(numero),
                ),
            )
        )
    return ft.Row(wrap=True, spacing=7, run_spacing=7, controls=controles)
