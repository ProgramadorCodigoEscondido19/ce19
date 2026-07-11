import flet as ft


class DialogManager:

    def __init__(self, page: ft.Page):
        self.page = page

    def mostrar(self, dialogo: ft.AlertDialog):

        self.page.dialog = dialogo

        dialogo.open = True

        self.page.update()

    def cerrar(self, dialogo: ft.AlertDialog):

        dialogo.open = False

        self.page.update()