import flet as ft

from ui.tema import (
    BLANCO,
    BORDE_SUAVE,
    DORADO_IOS,
    FONDO_APP,
    GRIS_SUAVE,
    NARANJA,
    PERLA_PANEL,
    TEXTO_PRINCIPAL,
    TEXTO_SECUNDARIO,
    VIOLETA_IOS,
    VIOLETA_SUAVE,
    AZUL_SUAVE,
    VERDE_SUAVE,
    ROJO_SUAVE,
    panel_moderno,
    panel_cristal,
    sombra_suave,
    opacidad,
)


def panel(content, padding=18, expand=False):
    return panel_moderno(content, padding=padding, expand=expand)


def panel_glass(content, padding=18, expand=False):
    return panel_cristal(content, padding=padding, expand=expand)


def encabezado_pagina(titulo, subtitulo=None, icono=None, accion=None):
    izquierda = []
    if icono:
        izquierda.append(
            ft.Container(
                width=54,
                height=54,
                border_radius=20,
                bgcolor=VIOLETA_SUAVE,
                alignment=ft.Alignment(0, 0),
                content=ft.Icon(icono, color=VIOLETA_IOS, size=28),
            )
        )
    textos = [ft.Text(titulo, size=32, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL)]
    if subtitulo:
        textos.append(ft.Text(subtitulo, size=14, color=TEXTO_SECUNDARIO))
    izquierda.append(ft.Column(tight=True, spacing=2, controls=textos))
    controles = [ft.Row(spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=izquierda)]
    if accion:
        controles.append(accion)
    return ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=controles,
    )


def tarjeta_info(titulo, valor, icono=None, fondo=AZUL_SUAVE, color=VIOLETA_IOS):
    return ft.Container(
        padding=16,
        bgcolor=PERLA_PANEL,
        border=ft.Border.all(1, BORDE_SUAVE),
        border_radius=18,
        shadow=sombra_suave(0.055, 18, 0, 6),
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=42,
                    height=42,
                    border_radius=16,
                    bgcolor=fondo,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(icono or ft.Icons.INSIGHTS, color=color, size=22),
                ),
                ft.Column(
                    tight=True,
                    spacing=2,
                    controls=[
                        ft.Text(str(titulo), size=12, color=TEXTO_SECUNDARIO),
                        ft.Text(str(valor), size=20, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                    ],
                ),
            ],
        ),
    )


def boton_principal(texto, icono=None, on_click=None):
    return ft.ElevatedButton(texto, icon=icono, height=44, bgcolor=VIOLETA_IOS, color=BLANCO, on_click=on_click)


def boton_suave(texto, icono=None, on_click=None, color=VIOLETA_IOS, fondo=VIOLETA_SUAVE):
    return ft.Container(
        height=42,
        padding=ft.Padding(left=14, top=0, right=14, bottom=0),
        bgcolor=fondo,
        border=ft.Border.all(1, opacidad(0.45, color)),
        border_radius=16,
        on_click=on_click,
        content=ft.Row(
            tight=True,
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(icono, size=18, color=color) if icono else ft.Container(width=0, height=0),
                ft.Text(texto, size=13, weight=ft.FontWeight.BOLD, color=color),
            ],
        ),
    )


def chip(texto, seleccionado=False, on_click=None, icono=None):
    return ft.Container(
        padding=ft.Padding(left=12, top=8, right=12, bottom=8),
        bgcolor=VIOLETA_SUAVE if seleccionado else BLANCO,
        border=ft.Border.all(1, VIOLETA_IOS if seleccionado else BORDE_SUAVE),
        border_radius=99,
        on_click=on_click,
        content=ft.Row(
            tight=True,
            spacing=6,
            controls=[
                ft.Icon(icono, size=16, color=VIOLETA_IOS) if icono else ft.Container(width=0, height=0),
                ft.Text(texto, size=12, weight=ft.FontWeight.BOLD if seleccionado else ft.FontWeight.NORMAL, color=VIOLETA_IOS if seleccionado else TEXTO_PRINCIPAL),
            ],
        ),
    )


def chip_color(color, seleccionado=False, on_click=None, tamano=28, borde=None):
    return ft.Container(
        width=tamano,
        height=tamano,
        bgcolor=color,
        border=ft.Border.all(3 if seleccionado else 1, borde or (VIOLETA_IOS if seleccionado else BORDE_SUAVE)),
        border_radius=tamano / 2,
        on_click=on_click,
    )


def separador():
    return ft.Container(height=1, bgcolor=BORDE_SUAVE, border_radius=1)


def fondo_pagina(content):
    return ft.Container(expand=True, bgcolor=FONDO_APP, content=content)


# ==========================================================
# Camino 2 - Pulido visual final
# Componentes seguros y reutilizables para vistas nuevas
# ==========================================================


def seccion(titulo, subtitulo=None, accion=None):
    controles = [
        ft.Column(
            tight=True,
            spacing=2,
            controls=[
                ft.Text(titulo, size=16, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                ft.Text(subtitulo, size=12, color=TEXTO_SECUNDARIO) if subtitulo else ft.Container(width=0, height=0),
            ],
        )
    ]
    if accion:
        controles.append(accion)
    return ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=controles,
    )


def estado_vacio(titulo="Sin datos", subtitulo="Todavía no hay elementos para mostrar.", icono=ft.Icons.INBOX_OUTLINED, accion=None):
    controles = [
        ft.Container(
            width=64,
            height=64,
            border_radius=18,
            bgcolor=GRIS_SUAVE,
            alignment=ft.Alignment(0, 0),
            content=ft.Icon(icono, size=32, color=TEXTO_SECUNDARIO),
        ),
        ft.Text(titulo, size=18, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL, text_align=ft.TextAlign.CENTER),
        ft.Text(subtitulo, size=13, color=TEXTO_SECUNDARIO, text_align=ft.TextAlign.CENTER),
    ]
    if accion:
        controles.append(ft.Container(height=4))
        controles.append(accion)
    return ft.Container(
        expand=True,
        alignment=ft.Alignment(0, 0),
        content=ft.Column(
            tight=True,
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=controles,
        ),
    )


def barra_herramientas(controles, wrap=True):
    return ft.Container(
        padding=ft.Padding(left=10, top=8, right=10, bottom=8),
        bgcolor=PERLA_PANEL,
        border=ft.Border.all(1, BORDE_SUAVE),
        border_radius=16,
        content=ft.Row(
            wrap=wrap,
            spacing=8,
            run_spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=controles,
        ),
    )


def boton_icono(icono, tooltip=None, on_click=None, color=VIOLETA_IOS, fondo=VIOLETA_SUAVE):
    return ft.Container(
        width=42,
        height=42,
        bgcolor=fondo,
        border=ft.Border.all(1, opacidad(0.50, color)),
        border_radius=16,
        tooltip=tooltip,
        on_click=on_click,
        alignment=ft.Alignment(0, 0),
        content=ft.Icon(icono, size=20, color=color),
    )


def indicador_estado(texto, color=VIOLETA_IOS, fondo=VIOLETA_SUAVE, icono=ft.Icons.CHECK_CIRCLE_OUTLINE):
    return ft.Container(
        padding=ft.Padding(left=10, top=6, right=10, bottom=6),
        bgcolor=fondo,
        border=ft.Border.all(1, opacidad(0.45, color)),
        border_radius=99,
        content=ft.Row(
            tight=True,
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(icono, size=15, color=color),
                ft.Text(texto, size=12, weight=ft.FontWeight.BOLD, color=color),
            ],
        ),
    )


def tarjeta_click(titulo, subtitulo=None, icono=None, on_click=None, trailing=None):
    controles = []
    if icono:
        controles.append(
            ft.Container(
                width=44,
                height=44,
                border_radius=16,
                bgcolor=AZUL_SUAVE,
                alignment=ft.Alignment(0, 0),
                content=ft.Icon(icono, color=VIOLETA_IOS, size=22),
            )
        )
    controles.append(
        ft.Column(
            expand=True,
            tight=True,
            spacing=3,
            controls=[
                ft.Text(titulo, size=14, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(subtitulo or "", size=12, color=TEXTO_SECUNDARIO, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
            ],
        )
    )
    if trailing:
        controles.append(trailing)
    return ft.Container(
        padding=14,
        bgcolor=PERLA_PANEL,
        border=ft.Border.all(1, BORDE_SUAVE),
        border_radius=18,
        shadow=sombra_suave(0.055, 18, 0, 6),
        on_click=on_click,
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=controles,
        ),
    )


def bloque_alerta(titulo, texto, icono=ft.Icons.INFO_OUTLINE, color=VIOLETA_IOS, fondo=VIOLETA_SUAVE):
    return ft.Container(
        padding=14,
        bgcolor=fondo,
        border=ft.Border.all(1, opacidad(0.40, color)),
        border_radius=20,
        content=ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Icon(icono, size=22, color=color),
                ft.Column(
                    expand=True,
                    tight=True,
                    spacing=4,
                    controls=[
                        ft.Text(titulo, size=14, weight=ft.FontWeight.BOLD, color=color),
                        ft.Text(texto, size=12, color=TEXTO_PRINCIPAL),
                    ],
                ),
            ],
        ),
    )
