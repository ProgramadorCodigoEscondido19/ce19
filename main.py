import flet as ft

from router import Router
from services.app_startup_service import AppStartupService
from ui.intro import construir_intro
from ui.tema import APP_NAME, PURPURA_INICIAL


def main(page: ft.Page):
    AppStartupService.configurar_page(page)
    page.bgcolor = PURPURA_INICIAL

    root = ft.Container(expand=True)
    page.add(root)

    app_iniciada = {"valor": False}

    def iniciar_app(e=None):
        if app_iniciada["valor"]:
            return

        app_iniciada["valor"] = True

        try:
            AppStartupService.preparar_estructura_base()
            AppStartupService.intentar_backup_auto()
            AppStartupService.inicializar_estado()

            router = Router(page)
            router.root = root

            AppStartupService.registrar_vistas(router, page)
            AppStartupService.crear_navigation_bar(page, router)
            router.iniciar("inicio")

        except Exception as error:
            AppStartupService.pantalla_error(
                root,
                "No se pudo iniciar la app",
                error,
            )

        page.update()

    try:
        intro, iniciar_animacion = construir_intro(page, iniciar_app)
        root.content = intro
        page.update()
        iniciar_animacion()
    except Exception:
        iniciar_app()


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets", name=APP_NAME)
