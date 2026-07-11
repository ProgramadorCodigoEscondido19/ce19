import flet as ft

from ui.tema import PERLA_PANEL, VIOLETA_IOS

class AppSidebar:
    def __init__(
        self,
        page,
        responsive,
        sidebar_content,
        router,
    ):
        self.page = page
        self.responsive = responsive
        self.content_builder = sidebar_content
        self.router = router

        self.visible = True
        self.collapsed = False

    def toggle(self, e=None):
        self.visible = not self.visible
        self.page.update()

    def toggle_collapse(self, e=None):
        self.collapsed = not self.collapsed
        self.page.update()

    def build(self):

        mode = self.responsive.mode()

        sidebar_content = self.content_builder()

        menu = ft.Column(
            spacing=5,
            controls=[
                ft.ListTile(
                    leading=ft.Icon(
                        ft.Icons.SAVE,
                        color=VIOLETA_IOS if self.es_activo("guardados") else None,
                    ),
                    title=ft.Text(
                        "Guardados",
                        weight=ft.FontWeight.BOLD if self.es_activo("guardados") else None,
                    ),
                    on_click=lambda e: self.router.navegar("guardados"),
                )
                
            ],
        )

        # 📱 MOBILE → DRAWER
        if mode == "mobile":
            return ft.Container(
                width=280,
                bgcolor=PERLA_PANEL,
                animate=ft.Animation(duration=200, curve=ft.AnimationCurve.EASE_IN_OUT,),
                visible=self.visible,
                content=ft.Column(
                    expand=True,
                    controls=[
                        menu,
                        ft.Divider(),
                        sidebar_content,
                    ],
                ),
            )

        # 📟 TABLET → ICON BAR
        if mode == "tablet":
            return ft.Container(
                width=80 if self.collapsed else 280,
                bgcolor=PERLA_PANEL,
                animate=ft.Animation(duration=200, curve=ft.AnimationCurve.EASE_IN_OUT,),
                content=ft.Column(
                    expand=True,
                    controls=[
                        menu,
                        ft.Divider(),
                        sidebar_content,
                    ],
                ),
            )

        # 🖥 DESKTOP → FULL
        return ft.Container(
            width=300,
            bgcolor=PERLA_PANEL,
            animate=ft.Animation(duration=200, curve=ft.AnimationCurve.EASE_IN_OUT,),
            content=ft.Column(
                expand=True,
                controls=[
                    menu,
                    ft.Divider(),
                    sidebar_content,
                ],
            ),
        )
    def es_activo(self, nombre):
        return self.router.activo == nombre
