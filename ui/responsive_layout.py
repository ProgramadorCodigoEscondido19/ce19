import flet as ft

class ResponsiveLayout:
    def __init__(self, page, responsive):
        self.page = page
        self.responsive = responsive

    def build(self, sidebar, content):

        mode = self.responsive.mode()

        # MOBILE
        if mode == "mobile":
            return ft.Column(
                expand=True,
                controls=[
                    ft.Container(
                        content=sidebar,
                        visible=True
                    ),
                    ft.Container(
                        expand=True,
                        content=content,
                    ),
                ]
            )

        # TABLET
        if mode == "tablet":
            return ft.Row(
                expand=True,
                controls=[
                    ft.Container(
                        width=80,
                        content=sidebar
                    ),
                    ft.Container(
                        expand=True,
                        content=content
                    ),
                ]
            )

        # DESKTOP
        return ft.Row(
            expand=True,
            controls=[
                ft.Container(
                    width=300,
                    content=sidebar
                ),
                ft.Container(
                    expand=True,
                    content=content
                ),
            ]
        )