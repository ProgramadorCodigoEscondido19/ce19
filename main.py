import flet as ft

from router import Router
from services.app_startup_service import AppStartupService
from services.permisos_service import PermisosService
from ui.intro import construir_intro
from ui.tema import APP_NAME, PERLA_PANEL, PURPURA_INICIAL, VIOLETA_IOS, icono_estrella


def main(page: ft.Page):
    AppStartupService.configurar_page(page)
    page.bgcolor = PURPURA_INICIAL

    root = ft.Container(expand=True)
    page.add(root)

    app_iniciada = {"valor": False}
    selector_niveles_activo = {"valor": False}
    router_actual = {"valor": None}

    def iniciar_app(nivel=4):
        if app_iniciada["valor"]:
            router = router_actual["valor"]
            if router is not None:
                selector_niveles_activo["valor"] = False
                router.nivel = nivel
                AppStartupService.crear_navigation_bar(page, router)
                router.navegar("inicio")
            return

        app_iniciada["valor"] = True

        try:
            AppStartupService.preparar_estructura_base()
            AppStartupService.intentar_backup_auto()
            AppStartupService.inicializar_estado(page)

            router = Router(page, nivel=nivel)
            router.root = root
            router.on_cambiar_nivel = mostrar_selector_niveles
            router_actual["valor"] = router
            selector_niveles_activo["valor"] = False

            AppStartupService.registrar_vistas(router, page)
            AppStartupService.crear_navigation_bar(page, router)
            router.iniciar("inicio")

            ultimo_modo = {"movil": router._es_movil()}

            def adaptar_al_tamano(e=None):
                if selector_niveles_activo["valor"]:
                    return
                modo_movil = router._es_movil()
                if modo_movil != ultimo_modo["movil"]:
                    ultimo_modo["movil"] = modo_movil
                    router.refrescar()
                else:
                    router._actualizar_barra_inferior()

            page.on_resize = adaptar_al_tamano

        except Exception as error:
            AppStartupService.pantalla_error(
                root,
                "No se pudo iniciar la app",
                error,
            )

        page.update()

    def mostrar_selector_niveles(e=None):
        """Permite escoger un nivel antes de montar las vistas de la app."""
        selector_niveles_activo["valor"] = True
        if page.navigation_bar:
            page.navigation_bar.visible = False
        ancho = getattr(page, "width", None) or 900
        es_movil = ancho < 700

        def tarjeta_nivel(nivel):
            autorizado = PermisosService.esta_autorizado(nivel)

            casilla = ft.Container(
                width=16,
                height=16,
                border_radius=4,
                border=ft.Border.all(1.5, VIOLETA_IOS if autorizado else "#8B778F"),
                bgcolor=VIOLETA_IOS if autorizado else ft.Colors.TRANSPARENT,
                alignment=ft.Alignment(0, 0),
                content=ft.Icon(ft.Icons.CHECK, size=12, color=ft.Colors.WHITE) if autorizado else None,
            )

            estado_acceso = ft.Text(
                "Ingreso habilitado" if autorizado else "Solicita clave la primera vez",
                size=9 if es_movil else 10,
                color="#6E6374",
                text_align=ft.TextAlign.CENTER,
            )

            def alternar_guardar_acceso(ev=None):
                if PermisosService.esta_autorizado(nivel):
                    PermisosService.revocar(nivel)
                    casilla.bgcolor = ft.Colors.TRANSPARENT
                    casilla.border = ft.Border.all(1.5, "#8B778F")
                    casilla.content = None
                    estado_acceso.value = "Solicitara clave al ingresar"
                else:
                    pedir_clave(nivel)
                    return
                page.update()

            return ft.Container(
                expand=True,
                height=126 if es_movil else 146,
                padding=10,
                border_radius=16,
                bgcolor=PERLA_PANEL,
                border=ft.Border.all(1, "#E5D7EB"),
                content=ft.Column(
                    expand=True,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    spacing=3,
                    controls=[
                        ft.Container(
                            expand=True,
                            ink=True,
                            border_radius=12,
                            on_click=lambda ev, n=nivel: elegir_nivel(n),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Column(
                                tight=True,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=4,
                                controls=[
                                    ft.Container(
                                        width=40,
                                        height=40,
                                        border_radius=14,
                                        bgcolor="#F0E3F7",
                                        alignment=ft.Alignment(0, 0),
                                        content=ft.Text(str(nivel), size=21, weight=ft.FontWeight.BOLD, color=VIOLETA_IOS),
                                    ),
                                    ft.Text(f"Nivel {nivel}", size=15, weight=ft.FontWeight.BOLD),
                                    estado_acceso,
                                ],
                            ),
                        ),
                        ft.Container(
                            height=22,
                            ink=True,
                            border_radius=6,
                            on_click=alternar_guardar_acceso,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Row(
                                tight=True,
                                spacing=6,
                                alignment=ft.MainAxisAlignment.CENTER,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    casilla,
                                    ft.Text("Guardar acceso", size=10, color="#5F5365"),
                                ],
                            ),
                        ),
                    ],
                ),
            )

        def volver_niveles(ev=None):
            mostrar_selector_niveles()

        def pedir_clave(nivel):
            clave = ft.TextField(
                label=f"Clave del Nivel {nivel}",
                password=True,
                can_reveal_password=True,
                autofocus=True,
                on_submit=lambda ev: confirmar_clave(),
            )
            guardar_clave = ft.Checkbox(
                label="Guardar contraseña en este dispositivo",
                value=False,
            )
            error = ft.Text("", color=ft.Colors.RED, size=12, visible=False)

            def confirmar_clave(ev=None):
                if PermisosService.validar_clave(nivel, clave.value or ""):
                    PermisosService.autorizar(nivel, guardar=bool(guardar_clave.value))
                    iniciar_app(nivel)
                    return
                error.value = "La clave no es correcta."
                error.visible = True
                page.update()

            root.content = ft.Container(
                expand=True,
                alignment=ft.Alignment(0, 0),
                bgcolor=PURPURA_INICIAL,
                padding=20,
                content=ft.Container(
                    width=390,
                    padding=26,
                    bgcolor=PERLA_PANEL,
                    border_radius=24,
                    content=ft.Column(
                        tight=True,
                        spacing=14,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            icono_estrella(56),
                            ft.Text(f"Nivel {nivel}", size=24, weight=ft.FontWeight.BOLD),
                            ft.Text("Ingrese la clave para habilitar este nivel en el dispositivo.", size=12, text_align=ft.TextAlign.CENTER),
                            clave,
                            guardar_clave,
                            error,
                            ft.Row(
                                alignment=ft.MainAxisAlignment.END,
                                controls=[
                                    ft.TextButton("Volver", on_click=volver_niveles),
                                    ft.ElevatedButton("Ingresar", icon=ft.Icons.LOCK_OPEN, bgcolor=VIOLETA_IOS, color=ft.Colors.WHITE, on_click=confirmar_clave),
                                ],
                            ),
                        ],
                    ),
                ),
            )
            page.update()

        def elegir_nivel(nivel):
            if PermisosService.esta_autorizado(nivel):
                iniciar_app(nivel)
            else:
                pedir_clave(nivel)

        root.content = ft.Container(
            expand=True,
            alignment=ft.Alignment(0, 0),
            bgcolor=PURPURA_INICIAL,
            padding=10 if es_movil else 20,
            content=ft.Container(
                width=None if es_movil else 640,
                padding=18 if es_movil else 28,
                bgcolor=PERLA_PANEL,
                border_radius=26,
                content=ft.Column(
                    tight=True,
                    spacing=12 if es_movil else 18,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        icono_estrella(52 if es_movil else 64),
                        ft.Text("Seleccione un nivel", size=23 if es_movil else 27, weight=ft.FontWeight.BOLD),
                        ft.Text("Elija el nivel con el que desea ingresar.", size=12 if es_movil else 13, color="#6E6374"),
                        ft.Row(
                            spacing=10,
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[tarjeta_nivel(1), tarjeta_nivel(2)],
                        ),
                        ft.Row(
                            spacing=10,
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[tarjeta_nivel(3), tarjeta_nivel(4)],
                        ),
                    ],
                ),
            ),
        )
        page.update()

    try:
        intro, iniciar_animacion = construir_intro(page, mostrar_selector_niveles)
        root.content = intro
        page.update()
        iniciar_animacion()
    except Exception:
        mostrar_selector_niveles()


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets", name=APP_NAME)
