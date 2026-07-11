import flet as ft

APP_NAME = "CODIGO ESCONDIDO 19"
ESTRELLA_ICONO = "icon.png"

# Paleta obligatoria del proyecto
NEGRO = "#171717"
MARRON = "#B97852"
ROJO = "#F01824"
NARANJA = "#FF7A24"
AMARILLO = "#FFF300"
VERDE = "#24AE52"
AZUL = "#4448C8"
VIOLETA = "#A44BA8"
GRIS = "#C9C9C9"
BLANCO = "#FFFFFF"

# Matices modernos para usar la misma paleta sin ensuciar la UI
MARRON_SUAVE = "#F4E7DF"
ROJO_SUAVE = "#FFECEF"
NARANJA_SUAVE = "#FFF0E5"
AMARILLO_SUAVE = "#FFFAD1"
VERDE_SUAVE = "#EAF8EF"
AZUL_SUAVE = "#EEF2FF"
VIOLETA_SUAVE = "#F6ECFA"
GRIS_SUAVE = "#F4F4F6"
NEGRO_SUAVE = "#242128"

PURPURA_INICIAL = "#71106F"
DORADO = "#F4C95D"
VIOLETA_IOS = "#6E2A8A"
DORADO_IOS = "#D8B45A"
PERLA = "#FCFAFF"
PERLA_PANEL = "#FFFEFC"
PERLA_VIOLETA = "#F5EDF8"
PERLA_BORDE = "#E9DFEE"
FONDO_APP = "#FCFAFF"

# =====================================================
# FONDO GLOBAL DE TODA LA APP (NO AFECTA LA INTRO)
# =====================================================
FONDO_APP_IMAGEN = "fondo_app.png"
FONDO_IMAGEN_APP = FONDO_APP_IMAGEN
SUPERFICIE_BLANCA = "#FFFFFF"
SUPERFICIE_PERLADA = "#FFFEFC"
SUPERFICIE_GLASS = "#FFFFFFE8"
CAPA_CLARA_FONDO = "#FFFFFF1F"

SUPERFICIE = SUPERFICIE_PERLADA
SUPERFICIE_2 = "#FFFDF8"
TEXTO_PRINCIPAL = "#17131D"
TEXTO_SECUNDARIO = "#6F6677"
TEXTO_MUTED = TEXTO_SECUNDARIO
TEXTO = TEXTO_PRINCIPAL
BORDE_SUAVE = "#ECE3F0"
BORDE_COLORIDO = "#EADAF2"

PALETA_ARCOIRIS = [NEGRO, MARRON, ROJO, NARANJA, AMARILLO, VERDE, AZUL, VIOLETA, GRIS, BLANCO]
PALETA_SUAVE = [NEGRO_SUAVE, MARRON_SUAVE, ROJO_SUAVE, NARANJA_SUAVE, AMARILLO_SUAVE, VERDE_SUAVE, AZUL_SUAVE, VIOLETA_SUAVE, GRIS_SUAVE, BLANCO]


def opacidad(valor, color):
    try:
        return ft.Colors.with_opacity(valor, color)
    except Exception:
        return color


def sombra_suave(opacity=0.065, blur=22, spread=0, y=7):
    return ft.BoxShadow(
        blur_radius=blur,
        spread_radius=spread,
        color=opacidad(opacity, ft.Colors.BLACK),
        offset=ft.Offset(0, y),
    )


def sombra_color(color=VIOLETA, opacity=0.16, blur=34, y=12):
    return ft.BoxShadow(
        blur_radius=blur,
        spread_radius=0,
        color=opacidad(opacity, color),
        offset=ft.Offset(0, y),
    )


def borde_suave(width=1, color=BORDE_SUAVE):
    return ft.Border.all(width, color)


def banda_colores(altura=8, suave=False):
    colores = PALETA_SUAVE if suave else PALETA_ARCOIRIS
    return ft.Row(
        spacing=0,
        controls=[
            ft.Container(
                expand=True,
                height=altura,
                bgcolor=color,
                border=ft.Border.all(1, MARRON) if color == BLANCO else None,
            )
            for color in colores
        ],
    )


def swatches_colores(tamano=14, suave=False):
    colores = PALETA_SUAVE if suave else PALETA_ARCOIRIS
    return ft.Row(
        wrap=True,
        spacing=4,
        run_spacing=4,
        controls=[
            ft.Container(
                width=tamano,
                height=tamano,
                bgcolor=color,
                border=ft.Border.all(1.3, MARRON) if color == BLANCO else None,
                border_radius=tamano / 2,
            )
            for color in colores
        ],
    )


def icono_estrella(tamano=42):
    return ft.Container(
        width=tamano,
        height=tamano,
        border_radius=tamano / 2,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        border=ft.Border.all(2, DORADO),
        shadow=sombra_color(DORADO, 0.20, 20, 6),
        content=ft.Image(src=ESTRELLA_ICONO, fit=ft.BoxFit.COVER, width=tamano, height=tamano),
    )


def panel_ios(content, padding=14, expand=False):
    return panel_moderno(content, padding=padding, expand=expand, radius=20)


def panel_moderno(content, padding=18, expand=False, bgcolor=PERLA_PANEL, radius=20, shadow=True):
    return ft.Container(
        expand=expand,
        padding=padding,
        bgcolor=bgcolor,
        border=ft.Border.all(1, PERLA_BORDE),
        border_radius=radius,
        shadow=sombra_suave(0.055, 18, 0, 6) if shadow else None,
        content=content,
    )


def panel_cristal(content, padding=18, expand=False, radius=22):
    return ft.Container(
        expand=expand,
        padding=padding,
        bgcolor=opacidad(0.82, SUPERFICIE_PERLADA),
        border=ft.Border.all(1, opacidad(0.82, BORDE_COLORIDO)),
        border_radius=radius,
        shadow=sombra_suave(0.055, 20, 0, 7),
        content=content,
    )


def panel_plano(content, padding=16, expand=False, bgcolor=PERLA_PANEL, radius=16):
    return ft.Container(
        expand=expand,
        padding=padding,
        bgcolor=bgcolor,
        border=ft.Border.all(1, BORDE_SUAVE),
        border_radius=radius,
        content=content,
    )


def titulo_pagina(titulo, subtitulo=None, icono=None):
    controles = []
    if icono:
        controles.append(
            ft.Container(
                width=48,
                height=48,
                border_radius=18,
                bgcolor=VIOLETA_SUAVE,
                alignment=ft.Alignment(0, 0),
                content=ft.Icon(icono, color=VIOLETA_IOS, size=26),
            )
        )
    textos = [ft.Text(titulo, size=30, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL)]
    if subtitulo:
        textos.append(ft.Text(subtitulo, size=13, color=TEXTO_SECUNDARIO))
    controles.append(ft.Column(tight=True, spacing=2, controls=textos))
    return ft.Row(spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=controles)


def boton_principal(texto, icono=None, on_click=None):
    return ft.ElevatedButton(texto, icon=icono, height=44, bgcolor=VIOLETA_IOS, color=BLANCO, on_click=on_click)


def boton_secundario(texto, icono=None, on_click=None):
    return ft.OutlinedButton(texto, icon=icono, height=44, on_click=on_click)


def chip_suave(texto, color=VIOLETA_IOS, fondo=VIOLETA_SUAVE, icono=None):
    controles = []
    if icono:
        controles.append(ft.Icon(icono, size=16, color=color))
    controles.append(ft.Text(texto, size=12, weight=ft.FontWeight.BOLD, color=color))
    return ft.Container(
        padding=ft.Padding(left=10, top=6, right=10, bottom=6),
        bgcolor=fondo,
        border=ft.Border.all(1, opacidad(0.55, color)),
        border_radius=99,
        content=ft.Row(tight=True, spacing=5, controls=controles),
    )


def campo_moderno(label=None, hint_text=None, value=None, prefix_icon=None, on_change=None, on_submit=None, expand=False, width=None, multiline=False):
    return ft.TextField(
        label=label,
        hint_text=hint_text,
        value=value,
        prefix_icon=prefix_icon,
        on_change=on_change,
        on_submit=on_submit,
        expand=expand,
        width=width,
        multiline=multiline,
        border_radius=16,
        filled=True,
        bgcolor=BLANCO,
        border_color=BORDE_SUAVE,
        focused_border_color=VIOLETA_IOS,
    )

# ==========================================================
# Camino 2 - tokens de pulido final
# ==========================================================
RADIO_CHICO = 12
RADIO_MEDIO = 18
RADIO_GRANDE = 26
ESPACIADO_CHICO = 6
ESPACIADO_MEDIO = 12
ESPACIADO_GRANDE = 20
ALTURA_BOTON = 44
ALTURA_CAMPO = 48

COLOR_EXITO = VERDE
COLOR_INFO = AZUL
COLOR_ALERTA = NARANJA
COLOR_ERROR = ROJO

FONDO_EXITO = VERDE_SUAVE
FONDO_INFO = AZUL_SUAVE
FONDO_ALERTA = NARANJA_SUAVE
FONDO_ERROR = ROJO_SUAVE


def degradado_suave():
    return ft.LinearGradient(
        begin=ft.Alignment(-1, -1),
        end=ft.Alignment(1, 1),
        colors=[
            PERLA,
            "#F9F2FC",
            "#F8F5FB",
            "#FFF8EE",
            PERLA,
        ],
        stops=[0, 0.30, 0.58, 0.82, 1],
    )


def fondo_moderno(content):
    return ft.Container(
        expand=True,
        gradient=degradado_suave(),
        content=content,
    )
