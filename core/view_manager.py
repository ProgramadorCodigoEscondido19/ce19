import flet as ft


class ViewManager:

    def __init__(self, page):

        self.page = page

        self.contenedor = ft.Container(
            expand=True
        )


    def mostrar(self, vista):

        self.contenedor.content = vista

        self.contenedor.update()