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
    ):

    def ver_detalle(e):
        mostrar_detalle(
            page=page,
            palabra=palabra,
            alfabeto=alfabeto,
            suma=suma,
            resultado=resultado,
        )
    # ----------------------------------------------------
    # Copiar
    # ----------------------------------------------------

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
            content=ft.Text("Copiado al portapapeles"),
            duration=1500,
        )

        page.snack_bar.open = True
        page.update()

        def restaurar():
            boton_copiar.icon = ft.Icons.CONTENT_COPY
            boton_copiar.tooltip = "Copiar"

            page.update()

        ejecutar_demorado(page, 1.5, restaurar)

    # ----------------------------------------------------

    boton_copiar = ft.IconButton(

        icon=ft.Icons.CONTENT_COPY,

        tooltip="Copiar",

        on_click=copiar,

    )

    # ----------------------------------------------------

    ancho = getattr(page, "width", None)
    if ancho is None and hasattr(page, "window"):
        ancho = getattr(page.window, "width", None)
    es_movil = (ancho or 1200) < 560

    boton_detalle = ft.OutlinedButton(
        "Ver detalle",
        icon=ft.Icons.VISIBILITY,
        on_click=ver_detalle,
        expand=es_movil,
    )
    boton_compartir = (
        ft.OutlinedButton(
            "Compartir",
            icon=ft.Icons.SHARE,
            on_click=funcion_compartir,
            expand=es_movil,
        )
        if funcion_compartir
        else None
    )
    boton_guardar = ft.ElevatedButton(
        texto_boton,
        icon=ft.Icons.SAVE,
        on_click=funcion,
        expand=es_movil,
    )

    if es_movil:
        fila_primaria = [boton_detalle]
        if boton_compartir:
            fila_primaria.append(boton_compartir)
        botones_accion = ft.Column(
            tight=True,
            spacing=8,
            controls=[
                ft.Row(spacing=8, controls=fila_primaria),
                ft.Row(controls=[boton_guardar]),
            ],
        )
    else:
        botones = [boton_detalle]
        if boton_compartir:
            botones.append(boton_compartir)
        botones.append(boton_guardar)
        botones_accion = ft.Row(
            spacing=8,
            wrap=True,
            run_spacing=8,
            alignment=ft.MainAxisAlignment.START,
            controls=botones,
        )

    return ft.Card(
        elevation=4,
        content=ft.Container(
            padding=15,
            content=ft.Column(
                tight=True,
                spacing=10,
                controls=[
                    # -------------------------
                    # Encabezado
                    # -------------------------

                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            ft.Container(
                                expand=True,
                                content=ft.Text(
                                    (
                                        palabra[:60]+"..."
                                        if len(palabra) > 60
                                        else palabra
                                    )
                                    +
                                    f"({alfabeto})",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS,

                                ),

                            ),

                            boton_copiar,

                        ],

                    ),

                    # -------------------------
                    # Desarrollo
                    # -------------------------
                    # -------------------------
                    # Información resumida
                    # -------------------------

                    ft.Text(
                        f"Resultado: {resultado}",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                    ),


                    # -------------------------
                    # Botones
                    # -------------------------

                    botones_accion,

                ],

            ),

        ),    

    )
