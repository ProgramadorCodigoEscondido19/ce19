import flet as ft

try:
    from ui.tema import BLANCO, FONDO_APP, PERLA_BORDE, SUPERFICIE_PERLADA, VIOLETA_IOS, TEXTO_PRINCIPAL, TEXTO_SECUNDARIO
except Exception:
    BLANCO = "#FFFFFF"
    FONDO_APP = "#F7F4FB"
    PERLA_BORDE = "#E7DCEB"
    SUPERFICIE_PERLADA = BLANCO
    VIOLETA_IOS = "#6E2A8A"
    TEXTO_PRINCIPAL = "#201A23"
    TEXTO_SECUNDARIO = "#6F6476"


class DialogManager:
    """Administrador simple de diálogos, compatible con el código existente."""

    def __init__(self, page: ft.Page):
        self.page = page

    def mostrar(self, dialogo: ft.AlertDialog):
        if dialogo not in self.page.overlay:
            self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()

    def cerrar(self, dialogo: ft.AlertDialog):
        dialogo.open = False
        self.page.update()

    def informacion(self, titulo, mensaje, on_cerrar=None):
        def cerrar(e=None):
            dialogo.open = False
            self.page.update()
            if on_cerrar:
                on_cerrar()

        dialogo = ft.AlertDialog(
            modal=True,
            bgcolor=FONDO_APP,
            title=ft.Text(titulo, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
            content=ft.Container(
                width=460,
                padding=14,
                bgcolor=SUPERFICIE_PERLADA,
                border_radius=18,
                border=ft.Border.all(1, PERLA_BORDE),
                content=ft.Text(str(mensaje or ""), color=TEXTO_SECUNDARIO, selectable=True),
            ),
            actions=[ft.ElevatedButton("Aceptar", on_click=cerrar)],
        )
        self.mostrar(dialogo)
        return dialogo

    def confirmar(self, titulo, mensaje, on_aceptar, texto_aceptar="Aceptar", texto_cancelar="Cancelar"):
        def cerrar(e=None):
            dialogo.open = False
            self.page.update()

        def aceptar(e=None):
            cerrar()
            if on_aceptar:
                on_aceptar()

        dialogo = ft.AlertDialog(
            modal=True,
            bgcolor=FONDO_APP,
            title=ft.Text(titulo, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
            content=ft.Container(
                width=460,
                padding=14,
                bgcolor=SUPERFICIE_PERLADA,
                border_radius=18,
                border=ft.Border.all(1, PERLA_BORDE),
                content=ft.Text(str(mensaje or ""), color=TEXTO_SECUNDARIO, selectable=True),
            ),
            actions=[
                ft.TextButton(texto_cancelar, on_click=cerrar),
                ft.ElevatedButton(texto_aceptar, on_click=aceptar, icon=ft.Icons.CHECK),
            ],
        )
        self.mostrar(dialogo)
        return dialogo
