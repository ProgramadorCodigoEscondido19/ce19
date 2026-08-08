import flet as ft

from ui.clipboard import copiar_al_portapapeles
from ui.tareas import ejecutar_demorado
from vistas.detalle import mostrar_detalle


def tarjeta_resultado(
    page,
    palabra,
    alfabeto,
    suma,
    resultado,
    texto_boton,
    funcion,
    funcion_compartir=None,
    modo_codificacion=None,
    mostrar_guardar=True,
    funcion_detalle=None,
):
    """Muestra una sola tarjeta compacta con las acciones del codificador."""

    def ver_detalle(e):
        if callable(funcion_detalle):
            funcion_detalle(e)
            return
        mostrar_detalle(
            page=page,
            palabra=palabra,
            alfabeto=alfabeto,
            suma=suma,
            resultado=resultado,
            modo_codificacion=modo_codificacion,
        )

    def copiar(e):
        texto = (
            f"Palabra: {palabra}\n"
            f"Alfabeto: {alfabeto}\n\n"
            f"{suma}\n\n"
            f"Resultado: {resultado}"
        )
        copiar_al_portapapeles(page, texto)
        boton_copiar.icon = ft.Icons.CHECK
        boton_copiar.tooltip = "Copiado"
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Copiado correctamente"),
            duration=1500,
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=ft.Margin(left=18, top=0, right=18, bottom=72),
            show_close_icon=True,
        )
        page.snack_bar.open = True
        page.update()

        def restaurar():
            boton_copiar.icon = ft.Icons.CONTENT_COPY
            boton_copiar.tooltip = "Copiar"
            page.update()

        ejecutar_demorado(page, 1.5, restaurar)

    ancho = getattr(page, "width", None)
    if ancho is None and hasattr(page, "window"):
        ancho = getattr(page.window, "width", None)
    es_movil = (ancho or 1200) < 560

    boton_copiar = ft.IconButton(
        icon=ft.Icons.CONTENT_COPY,
        tooltip="Copiar",
        on_click=copiar,
    )

    def accion(texto, icono, on_click, principal=False):
        return ft.Container(
            expand=True,
            height=42,
            padding=ft.Padding(left=8, top=0, right=8, bottom=0),
            alignment=ft.Alignment(0, 0),
            bgcolor="#6E2A8A" if principal else "#F7EDF9",
            border=ft.Border.all(1, "#6E2A8A" if principal else "#DCC8E4"),
            border_radius=14,
            ink=True,
            on_click=on_click,
            content=ft.Row(
                tight=True,
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Icon(
                        icono,
                        size=18,
                        color="#FFFFFF" if principal else "#6E2A8A",
                    ),
                    ft.Text(
                        texto,
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color="#FFFFFF" if principal else "#6E2A8A",
                    ),
                ],
            ),
        )

    acciones = [accion("Detalle", ft.Icons.VISIBILITY, ver_detalle)]
    if funcion_compartir:
        acciones.append(accion("Compartir", ft.Icons.SHARE, funcion_compartir))
    if mostrar_guardar and callable(funcion):
        acciones.append(accion(texto_boton, ft.Icons.SAVE, funcion, principal=True))

    if es_movil and len(acciones) == 3:
        acciones_control = ft.Column(
            tight=True,
            spacing=8,
            controls=[
                ft.Row(spacing=8, controls=acciones[:2]),
                ft.Row(spacing=8, controls=acciones[2:]),
            ],
        )
    else:
        acciones_control = ft.Row(spacing=8, controls=acciones)

    titulo = (palabra[:60] + "..." if len(palabra) > 60 else palabra)
    # El resultado puede ser un texto extenso al decodificar numeros. Se le da
    # un area desplazable propia para mantener las acciones siempre accesibles.
    altura_tarjeta = 292 if es_movil else 244

    return ft.Container(
        height=altura_tarjeta,
        padding=15,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        bgcolor="#FFF7FE",
        border=ft.Border.all(1, "#E8D9ED"),
        border_radius=16,
        shadow=ft.BoxShadow(
            blur_radius=10,
            color=ft.Colors.with_opacity(0.10, ft.Colors.BLACK),
            offset=ft.Offset(0, 3),
        ),
        content=ft.Column(
            expand=True,
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Container(
                            expand=True,
                            content=ft.Text(
                                f"{titulo}({alfabeto})",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ),
                        boton_copiar,
                    ],
                ),
                ft.Container(
                    expand=True,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    content=ft.Column(
                        scroll=ft.ScrollMode.AUTO,
                        tight=True,
                        controls=[
                            ft.Text(
                                f"Resultado: {resultado}",
                                size=22,
                                weight=ft.FontWeight.BOLD,
                                selectable=True,
                            ),
                        ],
                    ),
                ),
                acciones_control,
            ],
        ),
    )
