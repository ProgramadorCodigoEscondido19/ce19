from pathlib import Path
import importlib
import traceback

import flet as ft

from core.app_state import state
from logica.carpetas import Carpetas
from logica.guardados import Guardados
from logica.historial import Historial
from ui.tema import APP_NAME, FONDO_APP, PERLA_PANEL, PERLA_VIOLETA, VIOLETA_IOS, icono_estrella
from services.rutas_service import RutasService
from services.vistas_registry_service import VistasRegistryService

try:
    from services.app_paths import AppPaths
except Exception:
    AppPaths = None


class AppStartupService:
    """Centraliza el arranque de la app.

    Version final del Camino 1:
    - usa AppPaths si existe
    - registra vistas desde VistasRegistryService
    - mantiene backup automatico tolerante
    - mantiene pantalla de error clara
    """

    RUTAS_BASE = ("datos", "backups", "logs")

    @staticmethod
    def preparar_estructura_base():
        if AppPaths is not None:
            AppPaths.asegurar_directorios()
            return
        for ruta in AppStartupService.RUTAS_BASE:
            Path(ruta).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def intentar_backup_auto():
        try:
            modulo = importlib.import_module("core.backup_datos")
        except Exception:
            return False, "Módulo de backup no disponible"

        for nombre_funcion in (
            "crear_backup_automatico_diario",
            "crear_backup_automatico",
            "backup_automatico_diario",
            "backup_automatico",
        ):
            funcion = getattr(modulo, nombre_funcion, None)
            if callable(funcion):
                try:
                    funcion()
                    return True, nombre_funcion
                except Exception as error:
                    return False, str(error)

        return False, "No se encontró una función de backup automático compatible"

    @staticmethod
    def inicializar_estado():
        state.historial = Historial()
        state.guardados = Guardados()
        state.carpetas = Carpetas(state.guardados)
        return state

    @staticmethod
    def registrar_vistas(router, page):
        return VistasRegistryService.registrar_todas(router, page)

    @staticmethod
    def crear_navigation_bar(page, router):
        def cambiar_pagina(e):
            indice = getattr(e.control, "selected_index", 0)
            router.navegar(RutasService.ruta_por_indice(indice))

        page.navigation_bar = ft.NavigationBar(
            selected_index=0,
            on_change=cambiar_pagina,
            bgcolor=PERLA_PANEL,
            indicator_color=PERLA_VIOLETA,
            elevation=0,
            destinations=RutasService.navigation_destinations(icono_inicio=icono_estrella),
        )

    @staticmethod
    def configurar_page(page):
        page.title = APP_NAME
        page.bgcolor = FONDO_APP
        page.theme_mode = ft.ThemeMode.LIGHT
        page.theme = ft.Theme(color_scheme_seed=VIOLETA_IOS)
        page.padding = 0
        page.spacing = 0

        ventana = getattr(page, "window", None)
        if ventana is not None:
            ventana.min_width = 360
            ventana.min_height = 600
            ventana.title = APP_NAME
            try:
                ventana.icon = "assets/icon.ico"
            except Exception:
                pass

    @staticmethod
    def pantalla_error(root, titulo, error, detalle=None):
        detalle_texto = detalle or traceback.format_exc()
        root.content = ft.Container(
            expand=True,
            alignment=ft.Alignment(0, 0),
            padding=24,
            bgcolor=FONDO_APP,
            content=ft.Container(
                width=680,
                padding=24,
                bgcolor="#FFFFFF",
                border_radius=24,
                border=ft.Border.all(1, "#E6E6EA"),
                content=ft.Column(
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                    controls=[
                        ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=52, color=VIOLETA_IOS),
                        ft.Text(titulo, size=24, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                        ft.Text(str(error), selectable=True, text_align=ft.TextAlign.CENTER),
                        ft.Container(
                            padding=12,
                            bgcolor="#F7F7FA",
                            border_radius=12,
                            content=ft.Text(detalle_texto, selectable=True, size=12),
                        ),
                    ],
                ),
            ),
        )
