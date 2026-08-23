import re

import flet as ft

from ui.clipboard import copiar_al_portapapeles
from ui.tareas import ejecutar_demorado
from ui.dialogos import cerrar_dialogo, mostrar_dialogo

try:
    from ui.tema import (
        BLANCO,
        FONDO_APP,
        PERLA_BORDE,
        SUPERFICIE_PERLADA,
        PURPURA_IOS,
        DORADO_IOS,
        TEXTO_PRINCIPAL,
        TEXTO_SECUNDARIO,
        sombra_suave,
    )
except Exception:
    BLANCO = "#FFFFFF"
    FONDO_APP = "#F7F4FB"
    PERLA_BORDE = "#E7DCEB"
    PURPURA_IOS = "#A64B57"
    DORADO_IOS = "#D8B45A"
    TEXTO_PRINCIPAL = "#201A23"
    TEXTO_SECUNDARIO = "#6F6476"
    SUPERFICIE_PERLADA = BLANCO

    def sombra_suave(opacidad=0.10, blur=24, spread=0, desplazamiento_y=8):
        return ft.BoxShadow(
            blur_radius=blur,
            spread_radius=spread,
            offset=ft.Offset(0, desplazamiento_y),
            color=ft.Colors.with_opacity(opacidad, ft.Colors.BLACK),
        )


def _seccion(titulo, contenido, selectable=False, mono=False):
    texto = str(contenido or "")
    if not texto.strip():
        texto = "—"

    return ft.Container(
        padding=ft.Padding(left=14, top=12, right=14, bottom=12),
        bgcolor=SUPERFICIE_PERLADA,
        border=ft.Border.all(1, PERLA_BORDE),
        border_radius=18,
        content=ft.Column(
            tight=True,
            spacing=8,
            controls=[
                ft.Text(
                    titulo,
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=PURPURA_IOS,
                ),
                ft.Text(
                    texto,
                    selectable=selectable,
                    size=14,
                    color=TEXTO_PRINCIPAL,
                    font_family="Consolas" if mono else None,
                ),
            ],
        ),
    )


def _tokens_palabra(texto):
    palabra = str(texto or "").upper()
    tokens = []
    i = 0
    while i < len(palabra):
        par = palabra[i:i + 2]
        if par in ("CH", "LL"):
            tokens.append(par)
            i += 2
            continue
        if palabra[i].isalpha() or palabra[i].isdigit():
            tokens.append(palabra[i])
        i += 1
    return tokens


def _detalle_por_palabra(palabra, suma):
    palabras = str(palabra or "").split()
    valores = [int(numero) for numero in re.findall(r"\d+", str(suma or ""))]
    if not palabras or not valores:
        return str(suma or palabra or "")

    partes = []
    indice = 0
    for texto_palabra in palabras:
        cantidad = len(_tokens_palabra(texto_palabra))
        valores_palabra = valores[indice:indice + cantidad]
        indice += cantidad

        if not valores_palabra:
            partes.append(texto_palabra)
            continue

        calculo = "+".join(str(valor) for valor in valores_palabra)
        subtotal = sum(valores_palabra)
        partes.append(f"{texto_palabra} ({calculo} ={subtotal})")

    if indice < len(valores):
        resto = valores[indice:]
        calculo = "+".join(str(valor) for valor in resto)
        partes.append(f"({calculo} ={sum(resto)})")

    return " ".join(partes)


def _es_decodificacion(modo_codificacion):
    modo = str(modo_codificacion or "").lower()
    return "numeros_a_texto" in modo or "números a texto" in modo or "numeros a texto" in modo


def _seccion_resultado(resultado, es_movil):
    texto_resultado = str(resultado or "")
    es_largo = len(texto_resultado) > 70 or "\n" in texto_resultado

    valor = ft.Text(
        texto_resultado,
        size=22 if es_largo else 34,
        weight=ft.FontWeight.BOLD,
        color=PURPURA_IOS,
        selectable=True,
        text_align=ft.TextAlign.CENTER if not es_largo else ft.TextAlign.LEFT,
    )

    if es_largo:
        valor_control = ft.Container(
            height=116 if es_movil else 150,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Column(
                scroll=ft.ScrollMode.AUTO,
                tight=True,
                controls=[valor],
            ),
        )
    else:
        valor_control = ft.Container(
            alignment=ft.Alignment(0, 0),
            content=valor,
        )

    return ft.Container(
        padding=18,
        bgcolor=SUPERFICIE_PERLADA,
        border=ft.Border.all(1, PERLA_BORDE),
        border_radius=18,
        shadow=sombra_suave(0.055, 18, 0, 6),
        content=ft.Column(
            tight=True,
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    "Resultado final",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=TEXTO_PRINCIPAL,
                ),
                valor_control,
            ],
        ),
    )


def mostrar_detalle(
        page: ft.Page,
        palabra: str,
        alfabeto: str,
        suma: str,
        resultado,
        modo_codificacion=None,
):
    """Muestra el detalle de una tarjeta sin cambiar la lógica original."""
    ancho_page = getattr(page, "width", None)
    if ancho_page is None and hasattr(page, "window"):
        ancho_page = getattr(page.window, "width", None)
    es_movil = (ancho_page or 1200) < 700
    ancho_detalle = min(760, max(280, (ancho_page or 760) - 44))
    es_decodificacion = _es_decodificacion(modo_codificacion)
    # Al decodificar, el detalle se construye desde el texto obtenido y los
    # valores originales. Asi conserva la misma lectura por palabras y sumas
    # que se muestra en el modo Texto a numeros.
    texto_para_detalle = resultado if es_decodificacion else palabra
    detalle_palabras = _detalle_por_palabra(texto_para_detalle, suma)

    def copiar(e=None):
        texto = (
            f"Detalle:\n{detalle_palabras}\n\n"
            f"Alfabeto: {alfabeto}\n\n"
            f"Resultado: {resultado}"
        )

        copiar_al_portapapeles(page, texto)
        boton_copiar.icon = ft.Icons.CHECK
        boton_copiar.tooltip = "Copiado"
        page.update()

        def restaurar():
            boton_copiar.icon = ft.Icons.CONTENT_COPY
            boton_copiar.tooltip = "Copiar todo"
            try:
                page.update()
            except Exception:
                pass

        ejecutar_demorado(page, 1.4, restaurar)

    def cerrar(e=None):
        cerrar_dialogo(page, dialog)

    boton_copiar = ft.IconButton(
        icon=ft.Icons.CONTENT_COPY,
        tooltip="Copiar todo",
        on_click=copiar,
        icon_color=PURPURA_IOS,
    )

    dialog = ft.AlertDialog(
        modal=False,
        bgcolor=FONDO_APP,
        title=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    "Detalle",
                    size=22,
                    weight=ft.FontWeight.BOLD,
                    color=TEXTO_PRINCIPAL,
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    tooltip="Cerrar",
                    icon_color=PURPURA_IOS,
                    on_click=cerrar,
                ),
            ],
        ),
        content=ft.Container(
            width=ancho_detalle,
            height=360 if es_movil else 500,
            padding=ft.Padding(left=4, top=4, right=4, bottom=4),
            content=ft.Column(
                scroll=ft.ScrollMode.AUTO,
                spacing=12,
                controls=[
                    _seccion("Detalle", detalle_palabras, selectable=True),
                    _seccion("Alfabeto", alfabeto, selectable=True),
                    _seccion_resultado(resultado, es_movil),
                ],
            ),
        ),
        actions=[
            ft.TextButton(
                "Cerrar",
                on_click=cerrar,
            ),
            ft.ElevatedButton(
                "Copiar todo",
                icon=ft.Icons.CONTENT_COPY,
                on_click=copiar,
            ),
        ],
    )

    mostrar_dialogo(page, dialog)


def mostrar_detalle_comparacion(page: ft.Page, registro: dict):
    """Muestra una tarjeta guardada con una sola fila por diccionario."""
    comparacion = registro.get("comparacion") or []
    ancho_page = getattr(page, "width", None)
    if ancho_page is None and hasattr(page, "window"):
        ancho_page = getattr(page.window, "width", None)
    es_movil = (ancho_page or 1200) < 700

    def cerrar(e=None):
        cerrar_dialogo(page, dialog)

    filas = ft.Column(spacing=7, scroll=ft.ScrollMode.AUTO)
    for fila in comparacion:
        detalle_texto = []
        for detalle in fila.get("detalle_palabras", []):
            valores = " + ".join(str(valor) for valor in detalle.get("valores", []))
            detalle_texto.append(
                f"{detalle.get('palabra', '')} ({valores} = {detalle.get('subtotal', 0)})"
            )
        filas.controls.append(
            ft.Container(
                padding=10,
                border_radius=10,
                bgcolor="#FFFFFF",
                border=ft.Border.all(1, "#E4D8E8"),
                content=ft.Column(
                    tight=True,
                    spacing=3,
                    controls=[
                        ft.Text(
                            str(fila.get("alfabeto", "Diccionario")),
                            weight=ft.FontWeight.BOLD,
                            color=PURPURA_IOS,
                        ),
                        ft.Text(
                            "  ".join(detalle_texto) or "Sin caracteres compatibles.",
                            selectable=True,
                        ),
                        ft.Text(
                            f"Resultado: {fila.get('resultado', '')}",
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                ),
            )
        )

    dialog = ft.AlertDialog(
        modal=False,
        title=ft.Text("Comparacion de diccionarios"),
        content=ft.Container(
            width=min(680, max(280, (ancho_page or 680) - 44)),
            height=340 if es_movil else 430,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Text(f"Texto: {registro.get('palabra', '')}", selectable=True),
                    ft.Container(expand=True, content=filas),
                ],
            ),
        ),
        actions=[ft.TextButton("Cerrar", on_click=cerrar)],
    )
    mostrar_dialogo(page, dialog)
