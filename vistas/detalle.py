import flet as ft

from ui.clipboard import copiar_al_portapapeles
from ui.tareas import ejecutar_demorado

try:
    from ui.tema import (
        BLANCO,
        FONDO_APP,
        PERLA_BORDE,
        SUPERFICIE_PERLADA,
        VIOLETA_IOS,
        DORADO_IOS,
        TEXTO_PRINCIPAL,
        TEXTO_SECUNDARIO,
        sombra_suave,
    )
except Exception:
    BLANCO = "#FFFFFF"
    FONDO_APP = "#F7F4FB"
    PERLA_BORDE = "#E7DCEB"
    VIOLETA_IOS = "#6E2A8A"
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
                    color=VIOLETA_IOS,
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


def mostrar_detalle(
        page: ft.Page,
        palabra: str,
        alfabeto: str,
        suma: str,
        resultado,
):
    """Muestra el detalle de una tarjeta sin cambiar la lógica original."""
    ancho_page = getattr(page, "width", None)
    if ancho_page is None and hasattr(page, "window"):
        ancho_page = getattr(page.window, "width", None)
    es_movil = (ancho_page or 1200) < 700
    ancho_detalle = min(760, max(280, (ancho_page or 760) - 44))

    def copiar(e=None):
        texto = (
            f"Texto:\n{palabra}\n\n"
            f"Alfabeto: {alfabeto}\n\n"
            f"Cálculo:\n{suma}\n\n"
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
        # Flet 0.85 administra los diálogos en una pila propia. Usar la API
        # nativa evita que Android conserve la capa modal tras tocar Cerrar.
        try:
            page.pop_dialog()
            return
        except Exception:
            pass

        try:
            dialog.open = False
        except Exception:
            pass

        try:
            page.update()
        except Exception:
            pass

    boton_copiar = ft.IconButton(
        icon=ft.Icons.CONTENT_COPY,
        tooltip="Copiar todo",
        on_click=copiar,
        icon_color=VIOLETA_IOS,
    )

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor=FONDO_APP,
        title=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(
                    tight=True,
                    spacing=2,
                    controls=[
                        ft.Text(
                            "Detalle",
                            size=22,
                            weight=ft.FontWeight.BOLD,
                            color=TEXTO_PRINCIPAL,
                        ),
                        ft.Text(
                            "Vista completa de la tarjeta seleccionada",
                            size=12,
                            color=TEXTO_SECUNDARIO,
                        ),
                    ],
                ),
                ft.Container(
                    padding=ft.Padding(left=10, top=5, right=10, bottom=5),
                    bgcolor=ft.Colors.with_opacity(0.12, DORADO_IOS),
                    border_radius=999,
                    content=ft.Text(
                        str(resultado),
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=VIOLETA_IOS,
                    ),
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    tooltip="Cerrar",
                    icon_color=VIOLETA_IOS,
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
                    _seccion("Texto", palabra, selectable=True),
                    _seccion("Alfabeto", alfabeto, selectable=True),
                    _seccion("Cálculo", suma, selectable=True, mono=True),
                    ft.Container(
                        padding=18,
                        bgcolor=SUPERFICIE_PERLADA,
                        border=ft.Border.all(1, PERLA_BORDE),
                        border_radius=18,
                        shadow=sombra_suave(0.055, 18, 0, 6),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text(
                                    "Resultado final",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=TEXTO_PRINCIPAL,
                                ),
                                ft.Text(
                                    str(resultado),
                                    size=34,
                                    weight=ft.FontWeight.BOLD,
                                    color=VIOLETA_IOS,
                                    selectable=True,
                                ),
                            ],
                        ),
                    ),
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

    try:
        page.show_dialog(dialog)
    except Exception:
        # Compatibilidad con instalaciones de Flet anteriores.
        page.overlay.append(dialog)
        dialog.open = True
        page.update()
