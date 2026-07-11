import threading
import time
import flet as ft
from ui.clipboard import copiar_al_portapapeles
from vistas.detalle import mostrar_detalle

def tarjeta_resultado(
        page,
        palabra,
        alfabeto,
        suma,
        resultado,
        texto_boton,
        funcion,
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

            time.sleep(1.5)

            boton_copiar.icon = ft.Icons.CONTENT_COPY
            boton_copiar.tooltip = "Copiar"

            page.update()

        threading.Thread(
            target=restaurar,
            daemon=True,
        ).start()

    # ----------------------------------------------------

    boton_copiar = ft.IconButton(

        icon=ft.Icons.CONTENT_COPY,

        tooltip="Copiar",

        on_click=copiar,

    )

    # ----------------------------------------------------

    return ft.Card(
        elevation=4,
        content=ft.Container(
            padding=15,
            content=ft.Column(
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

                    ft.Text(
                        f"Longitud del texto: {len(palabra)} caracteres",
                        color=ft.Colors.GREY_700,
                    ),

                    # -------------------------
                    # Botones
                    # -------------------------

                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.OutlinedButton(
                                "Ver detalle",
                                icon=ft.Icons.VISIBILITY,
                                on_click=ver_detalle,
                            ),

                            ft.ElevatedButton(
                                texto_boton,
                                on_click=funcion,
                            ),

                        ],

                    ),

                ],

            ),

        ),    

    )
