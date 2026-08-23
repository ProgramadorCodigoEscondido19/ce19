import flet as ft
import base64
import json
import math
import os
import time
from pathlib import Path
from vistas.detalle import mostrar_detalle, mostrar_detalle_comparacion
from core.app_state import state
from core.rutas import ruta_exportacion
from services.mantenimiento_service import MantenimientoService

from logica.exportar_excel import exportar_guardados_xlsx
from logica.exportar_documentos import exportar_guardados_docx, exportar_guardados_pdf
from logica.pizarra_imagen import renderizar_lienzo_exportable_base64
from logica.tarjeta_biblica import datos_tarjeta_versiculo
from ui.clipboard import copiar_al_portapapeles
from ui.compartir import compartir_archivo, compartir_texto
from ui.tareas import ejecutar_demorado
from ui.tema import (
    BLANCO,
    MARRON,
    NEGRO,
    PERLA_BORDE,
    PERLA_PANEL,
    PERLA_PURPURA,
    SUPERFICIE_PERLADA,
    TEXTO_PRINCIPAL,
    TEXTO_SECUNDARIO,
    PURPURA_IOS,
    sombra_suave,
)
from ui.teclado import ocultar_teclado
from services.guardados_service import GuardadosService
from services.estadisticas_service import EstadisticasService
from services.exportacion_service import ExportacionService
from services.busqueda_global_service import BusquedaGlobalService


COLOR_ICONOS = {
    "NEGRO": "\u2B1B",
    "MARRON": "\U0001F7EB",
    "ROJO": "\U0001F7E5",
    "NARANJA": "\U0001F7E7",
    "AMARILLO": "\U0001F7E8",
    "VERDE": "\U0001F7E9",
    "AZUL": "\U0001F7E6",
    "PURPURA": "\U0001F7EA",
    "GRIS": "\u25FD\uFE0F",
    "BLANCO": "\u2B1C",
}


def _nombre_color_publico(nombre):
    nombre = str(nombre or "").upper().strip()
    if nombre in ("VIOLETA", "PÚRPURA"):
        return "PURPURA"
    return nombre


def _icono_color(nombre):
    return COLOR_ICONOS.get(_nombre_color_publico(nombre), "▫")


# Identidad visual de las carpetas principales. Las subcarpetas heredan una
# apariencia neutra para que la jerarquía siga siendo fácil de leer.
ESTILOS_CARPETAS = {
    "TARJETAS": ("#7C3AED", "#F1EBFF", ft.Icons.STYLE),
    "PIZARRAS": ("#D97706", "#FFF2E0", ft.Icons.EDIT),
    "FRAGMENTOS BIBLICOS": ("#E11D70", "#FDEAF2", ft.Icons.MENU_BOOK),
    "COLORES": ("#2563EB", "#EAF2FF", ft.Icons.COLOR_LENS),
    "TIEMPO": ("#16A34A", "#EAF8EF", ft.Icons.SCHEDULE),
    "CALCULADORA": ("#7C3AED", "#F1EBFF", ft.Icons.CALCULATE),
}


class GuardadosView:
    # ======================================
    # INIT
    # ======================================
    def __init__(self, page, router):
        self.tarjeta_seleccionada = None
        self.ids_seleccionados = set()
        self.page = page
        self.ancho = page.window.width
        self.guardados = state.guardados
        self.historial = state.historial
        self.carpetas = state.carpetas
        self.guardados_service = GuardadosService(self.guardados, self.carpetas)
        self.estadisticas_service = EstadisticasService(self.guardados, self.carpetas)
        self.busqueda_global_service = BusquedaGlobalService(self.guardados, self.carpetas)
        self.mantenimiento_service = MantenimientoService()
        # La lista es la vista inicial porque permite escanear carpetas y
        # fechas como en el explorador de referencia. El icono ofrece pasar
        # a cuadrícula cuando el usuario lo necesite.
        self.modo_cuadricula = False
        self.modo_seleccion_multiple = False
        self.file_picker_excel = None
        self.file_picker_tarjeta = None
        
        # Guardados abre en el nivel general, como el explorador de Windows.
        # Desde allí se entra a cada carpeta con doble clic.
        self.carpeta_actual_id = None
        self.carpeta_actual_nombre = None
        self.carpeta_seleccionada_id = None
        self.carpeta_seleccionada_nombre = None
        
        self.ruta_carpetas = []
        
        self.carpetas_expandidas = set()
        self.carpetas_colapsadas = True
        self.modo_vista = 'tarjetas'
        self.filtro_tipo = 'Todos'
        self.orden_guardados = 'Antiguos'
        self.campo_busqueda = ft.TextField(
            hint_text="Buscar carpetas",
            prefix_icon=ft.Icons.SEARCH,
            dense=True,
            width=280,
            filled=True,
            bgcolor=BLANCO,
            border_color=PERLA_BORDE,
            focused_border_color=PURPURA_IOS,
            border_radius=14,
            on_change=self.buscar_registros,
            on_submit=lambda e: ocultar_teclado(self.page, e.control),
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
        )
        self.boton_limpiar_busqueda = ft.IconButton(
            icon=ft.Icons.CLOSE,
            visible=False,
            tooltip="Limpiar búsqueda",
            on_click=self.limpiar_busqueda,
        )

        self.arbol_carpetas = ft.ListView(
            expand=True,
            spacing=2,
            padding=ft.Padding(left=0,top=0,right=12, bottom=0),
        )
        self.boton_nueva = ft.IconButton(
            icon=ft.Icons.CREATE_NEW_FOLDER,
            tooltip="Nueva carpeta",
            visible=True,
            on_click=lambda e: self.dialog_crear_carpeta(),
        )
        self.boton_renombrar = ft.IconButton(
            icon=ft.Icons.DRIVE_FILE_RENAME_OUTLINE,
            tooltip="Renombrar carpeta",
            disabled=True,
            visible=True,
            on_click=self.renombrar_carpeta,
        )
        self.boton_eliminar = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            tooltip="Eliminar carpeta",
            disabled=True,
            visible=True,
            on_click=self.eliminar_carpeta,
        )
        self.boton_vista = ft.IconButton(
            icon=ft.Icons.GRID_VIEW,
            tooltip='Ver como cuadrícula',
            on_click=self.cambiar_vista
        )
        self.boton_seleccion_multiple = ft.IconButton(
            icon=ft.Icons.SELECT_ALL,
            tooltip="Seleccion multiple",
            on_click=self.toggle_modo_seleccion_multiple,
        )
        # Esta accion es intencionalmente textual: exportar no debe quedar
        # escondido como un icono mas dentro de Guardados.
        self.boton_exportar_excel = ft.OutlinedButton(
            "Exportar",
            icon=ft.Icons.FILE_DOWNLOAD,
            tooltip="Exportar Excel, Word o PDF",
            on_click=self.dialog_exportar_excel,
        )
        self.boton_compartir_txt_filtrado = ft.IconButton(
            icon=ft.Icons.DESCRIPTION,
            tooltip="Compartir TXT filtrado",
            on_click=self.compartir_txt_filtrado,
        )
        self.boton_estadisticas = ft.IconButton(
            icon=ft.Icons.INFO_OUTLINE,
            tooltip="Estadísticas",
            on_click=self.dialog_estadisticas,
        )
        self.boton_busqueda_global = ft.IconButton(
            icon=ft.Icons.SEARCH,
            tooltip="Búsqueda global",
            on_click=self.dialog_busqueda_global,
        )
        self.boton_backup_datos = ft.IconButton(
            icon=ft.Icons.BACKUP,
            tooltip="Crear backup de datos",
            on_click=self.crear_backup_manual,
        )
        self.boton_restaurar_backup = ft.IconButton(
            icon=ft.Icons.RESTORE,
            tooltip="Restaurar backup",
            on_click=self.dialog_restaurar_backup,
        )
        self.boton_diagnostico = ft.IconButton(
            icon=ft.Icons.INFO_OUTLINE,
            tooltip="Diagnóstico de datos",
            on_click=self.dialog_diagnostico_datos,
        )
        self.boton_reparar_datos = ft.IconButton(
            icon=ft.Icons.HEALING,
            tooltip="Reparar datos",
            on_click=self.dialog_reparar_datos,
        )
        self.boton_log_errores = ft.IconButton(
            icon=ft.Icons.BUG_REPORT,
            tooltip="Ver errores registrados",
            on_click=self.dialog_log_errores,
        )
        self.boton_limpieza_app = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            tooltip="Limpieza segura",
            on_click=self.dialog_limpieza_app,
        )
        self.barra_explorador = ft.Row(
            tight=True,
            spacing=2,
            controls=[
                self.boton_vista,
                self.boton_seleccion_multiple,
            ]
        )
        self.barra_filtros_tipo = self._crear_barra_filtros_tipo()
        self.barra_orden_guardados = self._crear_barra_orden_guardados()
        self.barra_ruta = ft.Row(
            spacing=5,
            scroll=ft.ScrollMode.AUTO
        ) 
        # Un único panel con desplazamiento automático evita conflictos de
        # tamaño al volver a entrar a Guardados en escritorio o en la web.
        self.panel_contenido = ft.Column(
            expand=True,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )
        self.panel_izquierdo = ft.Container(
            width=250,
            padding=10,
            bgcolor=SUPERFICIE_PERLADA,
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=8,
            content=ft.Column(
                expand=True,
                spacing=8,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                "Carpetas",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                            ),
                        ],
                    ),
                    ft.Divider(height=1),
                    self.arbol_carpetas,
                ],
            ),
        )
        self.drawer = ft.NavigationDrawer(
            controls=[

                ft.Container(

                    padding=15,

                    content=ft.Text(

                        "Carpetas",

                        size=22,

                        weight=ft.FontWeight.BOLD,

                    )

                ),

                ft.Divider(),
                ft.Text("Use el panel de carpetas de la vista."),

            ]

        )
        self.lista_guardados = ft.Column(
            expand=True,
            spacing=10
        )
        self.texto_contador = ft.Text(
            "",
            color=ft.Colors.GREY_700
        )
        self.texto_seleccion = ft.Text(
            "",
            color=PURPURA_IOS,
            weight=ft.FontWeight.BOLD,
        )
        self.boton_copiar = ft.IconButton(
            icon=ft.Icons.CONTENT_COPY,
            tooltip="Copiar",
            on_click=self.copiar_seleccionado,
        )
        self.barra_acciones = ft.Container(
            visible=False,
            padding=ft.Padding(left=12, top=8, right=12, bottom=8),
            bgcolor=PERLA_PURPURA,
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=16,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                wrap=True,
                controls=[
                    self.texto_seleccion,
                    ft.Row(
                        tight=True,
                        spacing=2,
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.VISIBILITY,
                                tooltip="Ver detalle",
                                on_click=self.ver_detalle_seleccionado
                            ),
                            ft.IconButton(
                                icon=ft.Icons.EDIT,
                                tooltip="Editar",
                                on_click=self.editar_seleccionado,
                            ),
                            self.boton_copiar,
                            ft.IconButton(
                                icon=ft.Icons.SHARE,
                                tooltip="Enviar / compartir",
                                on_click=self.compartir_seleccionado,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DRIVE_FILE_MOVE,
                                tooltip="Mover",
                                visible=True,
                                on_click=self.mover_seleccionado,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                tooltip="Eliminar",
                                on_click=self.eliminar_seleccionado
                            ),
                        ],
                    ),
                ],
            ),
        )
        self.panel_derecho = ft.Container(
            expand=True,
            padding=14,
            bgcolor=PERLA_PANEL,
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=20,
            content=self._crear_panel_derecho_content(),
        )
        
        self.router = router
        self.menu_abierto = True
        state.bind(self._on_state_change)

    def crear_backup_manual(self, e=None):
        try:
            resultado = self.mantenimiento_service.crear_backup_manual()
            mensaje = f"Backup creado: {resultado.get('total', 0)} archivos"
        except Exception as error:
            mensaje = f"No se pudo crear el backup: {error}"

        self.page.snack_bar = ft.SnackBar(content=ft.Text(mensaje))
        self.page.snack_bar.open = True
        self.page.update()

    def dialog_restaurar_backup(self, e=None):
        try:
            backups = self.mantenimiento_service.listar_backups(30)
        except Exception as error:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"No se pudieron listar backups: {error}")
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        if not backups:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("No hay backups disponibles todavía.")
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        lista = ft.ListView(
            height=360,
            spacing=8,
            padding=ft.Padding(left=0, top=0, right=8, bottom=0),
        )

        def cerrar(ev=None):
            dialog.open = False
            self.page.update()

        def confirmar_restore(backup):
            def cancelar(ev=None):
                confirm.open = False
                self.page.update()

            def restaurar(ev=None):
                try:
                    resultado = self.mantenimiento_service.restaurar_backup(backup.get("carpeta"), crear_respaldo_actual=True)
                    mensaje = (
                        f"Backup restaurado: {resultado.get('total', 0)} archivos. "
                        "Cierre y vuelva a abrir la app para recargar todo."
                    )
                    confirm.open = False
                    dialog.open = False
                except Exception as error:
                    mensaje = f"No se pudo restaurar: {error}"
                    confirm.open = False

                self.page.snack_bar = ft.SnackBar(content=ft.Text(mensaje))
                self.page.snack_bar.open = True
                self.page.update()

            confirm = ft.AlertDialog(
                title=ft.Text("Restaurar backup"),
                content=ft.Text(
                    "Esto reemplazará los datos actuales por los del backup seleccionado. "
                    "Antes de restaurar se creará un backup de seguridad del estado actual."
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=cancelar),
                    ft.ElevatedButton("Restaurar", icon=ft.Icons.RESTORE, on_click=restaurar),
                ],
            )
            self.page.overlay.append(confirm)
            confirm.open = True
            self.page.update()

        for backup in backups:
            nombre = backup.get("nombre", "Backup")
            fecha = backup.get("fecha") or "sin fecha"
            motivo = backup.get("motivo") or "backup"
            total = backup.get("total", 0)

            lista.controls.append(
                ft.Container(
                    padding=12,
                    border=ft.Border.all(1, ft.Colors.GREY_300),
                    border_radius=12,
                    bgcolor=ft.Colors.WHITE,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Column(
                                tight=True,
                                spacing=3,
                                controls=[
                                    ft.Text(nombre, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{fecha} | {motivo} | {total} archivos", size=12, color=ft.Colors.GREY_700),
                                ],
                            ),
                            ft.ElevatedButton(
                                "Restaurar",
                                icon=ft.Icons.RESTORE,
                                on_click=lambda ev, b=backup: confirmar_restore(b),
                            ),
                        ],
                    ),
                )
            )

        dialog = ft.AlertDialog(
            title=ft.Text("Restaurar backup de datos"),
            content=ft.Container(
                width=560,
                content=ft.Column(
                    tight=True,
                    spacing=10,
                    controls=[
                        ft.Text(
                            "Elegí un backup para volver a un estado anterior de Guardados, Carpetas, Biblia y configuraciones.",
                            size=13,
                            color=ft.Colors.GREY_700,
                        ),
                        lista,
                    ],
                ),
            ),
            actions=[ft.TextButton("Cerrar", on_click=cerrar)],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()


    def dialog_diagnostico_datos(self, e=None):
        try:
            reporte, texto_reporte = self.mantenimiento_service.crear_diagnostico()
        except Exception as error:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"No se pudo crear el diagnóstico: {error}")
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        advertencias = reporte.get("advertencias") or []
        resumen = ft.Column(
            tight=True,
            spacing=8,
            controls=[
                ft.Text("Diagnóstico de datos", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Revisa archivos JSON, backups y posibles problemas antes de seguir modificando la app.",
                    size=13,
                    color=ft.Colors.GREY_700,
                ),
                ft.Container(
                    padding=10,
                    border_radius=10,
                    bgcolor="#F7F7FA",
                    content=ft.Text(
                        f"Backups detectados: {reporte.get('total_backups', 0)}\n"
                        f"Advertencias: {len(advertencias)}",
                        size=13,
                    ),
                ),
                ft.Container(
                    height=330,
                    padding=12,
                    border=ft.Border.all(1, ft.Colors.GREY_300),
                    border_radius=12,
                    bgcolor=ft.Colors.WHITE,
                    content=ft.Text(
                        texto_reporte,
                        selectable=True,
                        size=12,
                    ),
                ),
            ],
        )

        def cerrar(ev=None):
            dialog.open = False
            self.page.update()

        def copiar(ev=None):
            copiar_al_portapapeles(self.page, texto_reporte)

        dialog = ft.AlertDialog(
            title=ft.Text("Mantenimiento"),
            content=ft.Container(width=680, content=resumen),
            actions=[
                ft.TextButton("Copiar reporte", on_click=copiar),
                ft.TextButton("Cerrar", on_click=cerrar),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()


    def dialog_reparar_datos(self, e=None):
        try:
            reporte, texto_reporte = self.mantenimiento_service.analizar_reparacion()
        except Exception as error:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"No se pudo analizar la reparación: {error}")
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        estado = ft.Text(
            "Listo para revisar.",
            size=13,
            color=ft.Colors.GREY_700,
        )

        contenido = ft.Column(
            tight=True,
            spacing=10,
            controls=[
                ft.Text("Reparación segura de datos", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Esta herramienta no borra tarjetas. Solo corrige IDs faltantes y mueve guardados que apuntan a carpetas inexistentes hacia TARJETAS. Antes de aplicar crea un backup.",
                    size=13,
                    color=ft.Colors.GREY_700,
                ),
                ft.Container(
                    height=310,
                    padding=12,
                    border=ft.Border.all(1, ft.Colors.GREY_300),
                    border_radius=12,
                    bgcolor=ft.Colors.WHITE,
                    content=ft.Text(texto_reporte, selectable=True, size=12),
                ),
                estado,
            ],
        )

        def cerrar(ev=None):
            dialog.open = False
            self.page.update()

        def copiar(ev=None):
            copiar_al_portapapeles(self.page, texto_reporte)

        def aplicar(ev=None):
            try:
                resultado = self.mantenimiento_service.reparar_datos(aplicar=True)
                estado.value = (
                    f"Reparación aplicada. IDs asignados: {resultado.get('ids_asignados', 0)}. "
                    f"Movidos a TARJETAS: {resultado.get('movidos_a_raiz', 0)}. "
                    "Cerrá y abrí la app si no ves los cambios inmediatamente."
                )
                estado.color = PURPURA_IOS
                try:
                    self.cargar_vista_carpetas()
                    self.buscar_registros()
                except Exception:
                    pass
                self.page.update()
            except Exception as error:
                estado.value = f"No se pudo reparar: {error}"
                estado.color = ft.Colors.RED_700
                self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Reparar datos"),
            content=ft.Container(width=680, content=contenido),
            actions=[
                ft.TextButton("Copiar reporte", on_click=copiar),
                ft.ElevatedButton("Aplicar reparación", icon=ft.Icons.HEALING, on_click=aplicar),
                ft.TextButton("Cerrar", on_click=cerrar),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def dialog_log_errores(self, e=None):
        texto_log, ruta = self.mantenimiento_service.leer_log_errores()

        contenido_log = ft.Text(
            texto_log,
            selectable=True,
            size=12,
        )

        def cerrar(ev=None):
            dialog.open = False
            self.page.update()

        def copiar(ev=None):
            copiar_al_portapapeles(self.page, texto_log)

        def limpiar(ev=None):
            if self.mantenimiento_service.limpiar_log_errores():
                contenido_log.value = "Log limpiado. Todavía no hay errores registrados."
            else:
                contenido_log.value = "No se pudo limpiar el log."
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Errores registrados"),
            content=ft.Container(
                width=760,
                content=ft.Column(
                    tight=True,
                    spacing=10,
                    controls=[
                        ft.Text(
                            f"Archivo: {ruta}",
                            size=12,
                            color=ft.Colors.GREY_700,
                            selectable=True,
                        ),
                        ft.Container(
                            height=420,
                            padding=12,
                            border=ft.Border.all(1, ft.Colors.GREY_300),
                            border_radius=12,
                            bgcolor=ft.Colors.WHITE,
                            content=contenido_log,
                        ),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Copiar", on_click=copiar),
                ft.TextButton("Limpiar log", on_click=limpiar),
                ft.TextButton("Cerrar", on_click=cerrar),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _on_resize(self, e):
        modo_actual = self._modo_responsivo()
        if modo_actual == getattr(self, "_modo_responsivo_anterior", None):
            return
        self._modo_responsivo_anterior = modo_actual
        self.router.refrescar()


    def dialog_limpieza_app(self, e=None):
        try:
            reporte, texto = self.mantenimiento_service.crear_reporte_limpieza()
        except Exception as error:
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"No se pudo generar reporte de limpieza: {error}"))
            self.page.snack_bar.open = True
            self.page.update()
            return

        contenido = ft.TextField(
            value=texto,
            multiline=True,
            read_only=True,
            min_lines=12,
            max_lines=18,
            expand=True,
        )
        estado = ft.Text("La limpieza no borra tarjetas ni carpetas de trabajo. Solo backups antiguos y logs pesados.", size=12, color=ft.Colors.GREY_700)

        def cerrar(ev=None):
            dialog.open = False
            self.page.update()

        def copiar(ev=None):
            copiar_al_portapapeles(self.page, contenido.value or "")

        def refrescar(ev=None):
            try:
                nuevo, texto_nuevo = self.mantenimiento_service.crear_reporte_limpieza()
                contenido.value = texto_nuevo
                estado.value = "Reporte actualizado."
            except Exception as error:
                estado.value = f"No se pudo actualizar: {error}"
            self.page.update()

        def ejecutar(ev=None):
            try:
                resultado = self.mantenimiento_service.ejecutar_limpieza_segura(mantener_backups=10, max_log_kb=512)
                backups = resultado.get("backups", {})
                log = resultado.get("log", {})
                contenido.value = self.mantenimiento_service.texto_limpieza(resultado.get("reporte_final", {}))
                estado.value = (
                    f"Limpieza realizada. Backups eliminados: {backups.get('eliminados_total', 0)}. "
                    f"Log: {log.get('motivo', '')}"
                )
            except Exception as error:
                estado.value = f"No se pudo ejecutar limpieza: {error}"
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Limpieza segura"),
            content=ft.Container(
                width=620,
                height=520,
                content=ft.Column(
                    expand=True,
                    spacing=10,
                    controls=[
                        ft.Text(
                            "Mantiene los últimos 10 backups, archiva el log si pesa demasiado y no toca tus tarjetas guardadas.",
                            size=13,
                        ),
                        contenido,
                        estado,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Copiar reporte", on_click=copiar),
                ft.TextButton("Refrescar", on_click=refrescar),
                ft.ElevatedButton("Ejecutar limpieza", icon=ft.Icons.DELETE_OUTLINE, on_click=ejecutar),
                ft.TextButton("Cerrar", on_click=cerrar),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _crear_panel_derecho_content(self):
        buscador = ft.Row(
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(expand=True, content=self.campo_busqueda),
                self.boton_limpiar_busqueda,
            ],
        )

        # En el nivel general el buscador sirve para localizar carpetas. Las
        # acciones del explorador solo aparecen una vez que el usuario entra
        # en una carpeta.
        self.acciones_explorador = ft.Container(
            visible=not self._esta_en_inicio_guardados(),
            padding=ft.Padding(left=3, top=2, right=3, bottom=2),
            bgcolor=PERLA_PURPURA,
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=12,
            content=self.barra_explorador,
        )

        if self.es_movil():
            herramientas = ft.Column(
                tight=True,
                spacing=6,
                controls=[
                    buscador,
                    self.acciones_explorador,
                    self.boton_exportar_excel,
                ],
            )
        else:
            herramientas = ft.Row(
                wrap=True,
                spacing=8,
                run_spacing=6,
                controls=[
                    ft.Container(width=420, content=buscador),
                    self.acciones_explorador,
                    self.boton_exportar_excel,
                ],
            )

        self.herramientas_guardados = ft.Container(
            padding=0,
            bgcolor=ft.Colors.TRANSPARENT,
            content=herramientas,
        )

        return ft.Column(
            expand=True,
            spacing=10,
            controls=[
                self.herramientas_guardados,
                self.barra_ruta,
                self.barra_acciones,
                self.panel_contenido
            ],
        )

    def _esta_en_inicio_guardados(self):
        return self.carpeta_actual_id is None

    def _categoria_registro(self, registro):
        tipo = registro.get("tipo", "tarjeta")
        contenido = registro.get("contenido") or {}

        if tipo == "fragmento_biblico":
            return "Biblia"

        if isinstance(contenido, dict) and contenido.get("tipo") == "biblia_codificada":
            return "Biblia"

        if tipo == "pizarra":
            return "Pizarra"

        if tipo == "analisis_colores":
            return "Colores"

        if tipo == "tiempo":
            return "Tiempo"

        if tipo == "calculo_biblico":
            return "Calculadora"

        return "Codificador"

    def _registro_pasa_filtro_tipo(self, registro):
        if self.filtro_tipo == "Todos":
            return True
        return self._categoria_registro(registro) == self.filtro_tipo

    def _aplicar_filtro_tipo(self, registros):
        # Camino 1: el filtrado queda centralizado en services/guardados_service.py
        return self.guardados_service.filtrar_por_tipo(registros, self.filtro_tipo)

    def _crear_barra_filtros_tipo(self):
        filtros = [
            "Todos",
            "Codificador",
            "Biblia",
            "Pizarra",
            "Colores",
            "Tiempo",
            "Calculadora",
        ]

        return ft.Row(
            scroll=ft.ScrollMode.AUTO,
            spacing=6,
            controls=[
                self._chip_filtro_tipo(nombre)
                for nombre in filtros
            ],
        )

    def _chip_filtro_tipo(self, nombre):
        activo = self.filtro_tipo == nombre
        return ft.Container(
            padding=ft.Padding(left=12, top=7, right=12, bottom=7),
            bgcolor=SUPERFICIE_PERLADA if activo else PERLA_PURPURA,
            border=ft.Border.all(
                1.4 if activo else 1,
                PURPURA_IOS if activo else PERLA_BORDE,
            ),
            border_radius=20,
            content=ft.Text(
                nombre,
                size=12,
                weight=ft.FontWeight.BOLD if activo else None,
                color=PURPURA_IOS if activo else TEXTO_SECUNDARIO,
            ),
            on_click=lambda e, n=nombre: self._cambiar_filtro_tipo(n),
        )

    def _refrescar_barra_filtros_tipo(self):
        if not hasattr(self, "barra_filtros_tipo"):
            return
        self.barra_filtros_tipo.controls.clear()
        for nombre in ["Todos", "Codificador", "Biblia", "Pizarra", "Colores", "Tiempo", "Calculadora"]:
            self.barra_filtros_tipo.controls.append(self._chip_filtro_tipo(nombre))

    def _cambiar_filtro_tipo(self, nombre):
        self.filtro_tipo = nombre
        self._refrescar_barra_filtros_tipo()
        self.actualizar_tabla()
        self.page.update()

    def _crear_barra_orden_guardados(self):
        return ft.Row(
            scroll=ft.ScrollMode.AUTO,
            spacing=6,
            controls=[
                ft.Text(
                    "Orden:",
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_700,
                ),
                self._chip_orden_guardados("Antiguos"),
                self._chip_orden_guardados("A-Z"),
                self._chip_orden_guardados("Resultado"),
            ],
        )

    def _chip_orden_guardados(self, nombre):
        activo = self.orden_guardados == nombre
        return ft.Container(
            padding=ft.Padding(left=10, top=5, right=10, bottom=5),
            bgcolor=SUPERFICIE_PERLADA if activo else PERLA_PURPURA,
            border=ft.Border.all(
                1.2 if activo else 1,
                PURPURA_IOS if activo else PERLA_BORDE,
            ),
            border_radius=16,
            content=ft.Text(
                nombre,
                size=11,
                weight=ft.FontWeight.BOLD if activo else None,
                color=PURPURA_IOS if activo else TEXTO_SECUNDARIO,
            ),
            on_click=lambda e, n=nombre: self._cambiar_orden_guardados(n),
        )

    def _refrescar_barra_orden_guardados(self):
        if not hasattr(self, "barra_orden_guardados"):
            return
        self.barra_orden_guardados.controls.clear()
        self.barra_orden_guardados.controls.append(
            ft.Text(
                "Orden:",
                size=12,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.GREY_700,
            )
        )
        for nombre in ["Antiguos", "A-Z", "Resultado"]:
            self.barra_orden_guardados.controls.append(self._chip_orden_guardados(nombre))

    def _cambiar_orden_guardados(self, nombre):
        self.orden_guardados = nombre
        self._refrescar_barra_orden_guardados()
        self.actualizar_tabla()
        self.page.update()

    def _ordenar_registros(self, registros):
        if self.orden_guardados == "Antiguos":
            return list(registros)

        if self.orden_guardados == "A-Z":
            return sorted(
                registros,
                key=lambda r: self.titulo_registro(r).lower(),
            )

        if self.orden_guardados == "Resultado":
            def clave_resultado(registro):
                try:
                    return int(str(self.resultado_registro(registro)).strip())
                except Exception:
                    return 0

            return sorted(registros, key=clave_resultado, reverse=True)

        return list(reversed(registros))

    def limpiar_busqueda(self, e=None):
        self.campo_busqueda.value = ""
        self.boton_limpiar_busqueda.visible = False
        self.actualizar_tabla()
        self.page.update()

    def _ids_con_descendientes(self, ids_carpetas):
        ids = {
            id_carpeta
            for id_carpeta in ids_carpetas
            if id_carpeta is not None
        }

        for id_carpeta in list(ids):
            ids.update(self.carpetas.obtener_descendientes(id_carpeta))

        return ids

    def _registros_para_exportar(self, ids_carpetas):
        ids = self._ids_con_descendientes(ids_carpetas)
        nombres = {
            carpeta["nombre"]
            for carpeta in self.carpetas.obtener()
            if carpeta.get("id") in ids
        }

        return [
            registro
            for registro in self.guardados.obtener()
            if (
                registro.get("carpeta_id") in ids
                or (
                    registro.get("carpeta_id") is None
                    and registro.get("carpeta") in nombres
                )
            )
        ]

    def dialog_exportar_excel(self, e=None):
        seleccion_inicial = (
            {self.carpeta_actual_id}
            if self.carpeta_actual_id is not None
            else {1, 2, 3, 4, 5}
        )
        seleccionadas = set(seleccion_inicial)
        expandidas = {
            carpeta["id"]
            for carpeta in self.carpetas.obtener()
            if carpeta.get("padre") is None
        }
        lista = ft.ListView(
            scroll=ft.ScrollMode.AUTO,
            spacing=2,
        )
        formato = ft.Dropdown(
            label="Formato",
            value="xlsx",
            options=[
                ft.dropdown.Option("xlsx", text="Excel (.xlsx)"),
                ft.dropdown.Option("docx", text="Word (.docx)"),
                ft.dropdown.Option("pdf", text="PDF (.pdf)"),
            ],
        )

        def cerrar(e=None):
            dialog.open = False
            try:
                if dialog in self.page.overlay:
                    self.page.overlay.remove(dialog)
            except Exception:
                pass
            self.page.update()

        def actualizar_check(e):
            id_carpeta = e.control.data

            if e.control.value:
                seleccionadas.add(id_carpeta)
            else:
                seleccionadas.discard(id_carpeta)

        def alternar(carpeta):
            if carpeta["id"] in expandidas:
                expandidas.remove(carpeta["id"])
            else:
                expandidas.add(carpeta["id"])
            renderizar_arbol()

        def item_carpeta(carpeta, nivel):
            hijos = self.carpetas.obtener_hijos(carpeta["id"])
            return ft.Container(
                padding=ft.Padding(left=4 + nivel * 18, top=1, right=4, bottom=1),
                content=ft.Row(
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.IconButton(
                            icon=(
                                ft.Icons.EXPAND_MORE
                                if carpeta["id"] in expandidas
                                else ft.Icons.CHEVRON_RIGHT
                            )
                            if hijos
                            else ft.Icons.FOLDER_OUTLINED,
                            icon_size=18,
                            width=32,
                            height=32,
                            on_click=(
                                lambda e, c=carpeta: alternar(c)
                                if hijos
                                else None
                            ),
                        ),
                        ft.Checkbox(
                            value=carpeta["id"] in seleccionadas,
                            data=carpeta["id"],
                            on_change=actualizar_check,
                        ),
                        ft.Text(
                            carpeta["nombre"],
                            expand=True,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                ),
            )

        def agregar_rama(carpeta, nivel):
            lista.controls.append(item_carpeta(carpeta, nivel))

            if carpeta["id"] not in expandidas:
                return

            for hija in self.carpetas.obtener_hijos(carpeta["id"]):
                agregar_rama(hija, nivel + 1)

        def renderizar_arbol():
            lista.controls.clear()

            for carpeta in self.carpetas.obtener_hijos(None):
                agregar_rama(carpeta, 0)

            try:
                lista.update()
            except (RuntimeError, AssertionError):
                pass

        def marcar_todas(e=None):
            seleccionadas.clear()
            seleccionadas.update(
                carpeta["id"]
                for carpeta in self.carpetas.obtener()
            )
            renderizar_arbol()
            self.page.update()

        def exportar(e=None):
            ids = list(seleccionadas)

            if not ids:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Seleccione al menos una carpeta.")
                )
                self.page.snack_bar.open = True
                self.page.update()
                return

            registros = self._registros_para_exportar(ids)

            if not registros:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("No hay registros en esas carpetas.")
                )
                self.page.snack_bar.open = True
                self.page.update()
                return

            if formato.value == "docx":
                archivo = exportar_guardados_docx(registros)
            elif formato.value == "pdf":
                archivo = exportar_guardados_pdf(registros)
            else:
                nombres_carpetas = [
                    carpeta["nombre"]
                    for carpeta in self.carpetas.obtener()
                    if carpeta["id"] in seleccionadas
                ]
                archivo = exportar_guardados_xlsx(registros, carpetas=nombres_carpetas)
            cerrar()
            self.descargar_documento(archivo, formato.value)

        dialog = ft.AlertDialog(
            title=ft.Text("Exportar registros"),
            content=ft.Container(
                width=420,
                height=420,
                content=ft.Column(controls=[formato, ft.Container(expand=True, content=lista)]),
            ),
            actions=[
                ft.TextButton("Todas", on_click=marcar_todas),
                ft.TextButton("Cancelar", on_click=cerrar),
                ft.ElevatedButton(
                    "Exportar",
                    icon=ft.Icons.FILE_DOWNLOAD,
                    on_click=exportar,
                ),
            ],
        )

        self.page.overlay.append(dialog)
        renderizar_arbol()
        dialog.open = True
        self.page.update()


    def _registros_visibles_para_accion(self):
        """Devuelve los registros visibles según carpeta, búsqueda, filtro y orden actuales."""
        if self.carpeta_actual_nombre is None:
            registros = []
        else:
            registros = [
                r
                for r in self.guardados.obtener()
                if (
                    r.get("carpeta_id") == self.carpeta_actual_id
                    or (
                        r.get("carpeta_id") is None
                        and r.get("carpeta") == self.carpeta_actual_nombre
                    )
                )
            ]

        texto = str(getattr(self.campo_busqueda, "value", "") or "").lower().strip()
        if texto:
            registros = [
                r
                for r in registros
                if (
                    texto in self.titulo_registro(r).lower()
                    or texto in self.subtitulo_registro(r).lower()
                    or texto in self.resultado_registro(r).lower()
                    or texto in self.texto_registro(r).lower()
                )
            ]

        registros = self._aplicar_filtro_tipo(registros)
        registros = self._ordenar_registros(registros)
        return registros

    def compartir_txt_filtrado(self, e=None):
        registros = self._registros_visibles_para_accion()

        if not registros:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("No hay registros visibles para compartir."),
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        titulo = (
            f"CODIGO ESCONDIDO 19 - {self.carpeta_actual_nombre or 'Guardados'}\n"
            f"Filtro: {self.filtro_tipo} | Orden: {self.orden_guardados} | Registros: {len(registros)}"
        )
        texto = ExportacionService.registros_a_texto(registros, titulo=titulo)
        compartir_texto(
            self.page,
            texto,
            f"Guardados - {self.carpeta_actual_nombre or 'Registros'}",
        )

    def dialog_estadisticas(self, e=None):
        resumen = self.estadisticas_service.resumen_guardados()
        texto = self.estadisticas_service.resumen_texto()

        tipos = resumen.get("por_tipo", {})
        carpetas = resumen.get("por_carpeta", {})

        def fila(nombre, valor):
            return ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(str(nombre), expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(str(valor), weight=ft.FontWeight.BOLD),
                ],
            )

        contenido = ft.Column(
            tight=True,
            spacing=10,
            controls=[
                ft.Text("Resumen general", size=18, weight=ft.FontWeight.BOLD),
                fila("Guardados totales", resumen.get("total", 0)),
                fila("Carpetas totales", resumen.get("carpetas_total", 0)),
                ft.Divider(height=1),
                ft.Text("Por tipo", weight=ft.FontWeight.BOLD),
            ]
            + [fila(tipo, cantidad) for tipo, cantidad in sorted(tipos.items())]
            + [
                ft.Divider(height=1),
                ft.Text("Por carpeta", weight=ft.FontWeight.BOLD),
            ]
            + [fila(carpeta, cantidad) for carpeta, cantidad in sorted(carpetas.items())[:12]]
        )

        def copiar(e=None):
            copiar_al_portapapeles(self.page, texto)

        dialog = ft.AlertDialog(
            title=ft.Text("Estadísticas de Guardados"),
            content=ft.Container(width=460, content=contenido),
            actions=[
                ft.TextButton("Copiar", on_click=copiar),
                ft.TextButton("Cerrar", on_click=lambda ev: cerrar()),
            ],
        )

        def cerrar():
            dialog.open = False
            self.page.update()

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def dialog_busqueda_global(self, e=None):
        campo = ft.TextField(
            label="Buscar en toda la app",
            hint_text="Palabra, referencia, carpeta, resultado...",
            prefix_icon=ft.Icons.SEARCH,
            autofocus=True,
        )
        resultados = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)

        def renderizar(items):
            resultados.controls.clear()
            if not items:
                resultados.controls.append(ft.Text("Sin resultados."))
                return
            for registro in items[:40]:
                resultados.controls.append(
                    ft.Container(
                        padding=10,
                        border=ft.Border.all(1, ft.Colors.GREY_300),
                        border_radius=10,
                        content=ft.Column(
                            tight=True,
                            spacing=3,
                            controls=[
                                ft.Text(self.titulo_registro(registro), weight=ft.FontWeight.BOLD),
                                ft.Text(self.subtitulo_registro(registro), size=12, color=ft.Colors.GREY_700, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(f"Carpeta: {registro.get('carpeta', 'TARJETAS')}", size=11, color=ft.Colors.GREY_600),
                            ],
                        ),
                    )
                )

        def buscar(e=None):
            items = self.busqueda_global_service.buscar_guardados(campo.value, limite=40)
            renderizar(items)
            resultados.update()

        campo.on_submit = buscar

        dialog = ft.AlertDialog(
            title=ft.Text("Búsqueda global"),
            content=ft.Container(
                width=560,
                height=500,
                content=ft.Column(
                    expand=True,
                    spacing=10,
                    controls=[
                        campo,
                        ft.ElevatedButton("Buscar", icon=ft.Icons.SEARCH, on_click=buscar),
                        ft.Divider(height=1),
                        ft.Container(expand=True, content=resultados),
                    ],
                ),
            ),
            actions=[ft.TextButton("Cerrar", on_click=lambda ev: cerrar())],
        )

        def cerrar():
            dialog.open = False
            self.page.update()

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _obtener_file_picker_excel(self):
        if self.file_picker_excel is not None:
            return self.file_picker_excel

        self.file_picker_excel = ft.FilePicker()

        try:
            self.page.services.append(self.file_picker_excel)
            self.page.update()
        except Exception:
            pass

        return self.file_picker_excel

    def descargar_excel(self, archivo):
        self.descargar_documento(archivo, "xlsx")

    def descargar_documento(self, archivo, formato):
        if hasattr(self.page, "run_task"):
            self.page.run_task(self._descargar_documento_async, archivo, formato)
            return

        compartir_archivo(
            self.page,
            archivo,
            "Guardados exportados",
            "application/octet-stream",
        )

    async def _descargar_documento_async(self, archivo, formato):
        ruta = Path(archivo)
        datos = ruta.read_bytes()
        picker = self._obtener_file_picker_excel()
        extensiones = {"xlsx": ["xlsx"], "docx": ["docx"], "pdf": ["pdf"]}
        nombres = {"xlsx": "Excel", "docx": "Word", "pdf": "PDF"}

        try:
            destino = await picker.save_file(
                dialog_title=f"Descargar {nombres.get(formato, 'archivo')}",
                file_name=ruta.name,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=extensiones.get(formato, [formato]),
                src_bytes=datos,
            )
        except Exception:
            destino = None

        if destino:
            plataforma = getattr(self.page, "platform", None)
            es_movil = plataforma in (ft.PagePlatform.ANDROID, ft.PagePlatform.IOS)

            if not es_movil:
                destino_path = Path(destino)

                extension = "." + formato
                if destino_path.suffix.lower() != extension:
                    destino_path = destino_path.with_suffix(extension)

                try:
                    destino_path.write_bytes(datos)
                    destino = str(destino_path)
                except Exception:
                    destino = None

            if destino:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"{nombres.get(formato, 'Archivo')} descargado: {destino}")
                )
                self.page.snack_bar.open = True
                self.page.update()
                return

        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("No se pudo descargar. Puede compartirlo o guardarlo desde el panel.")
        )
        self.page.snack_bar.open = True
        self.page.update()
        compartir_archivo(
            self.page,
            archivo,
            "Guardados exportados",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    
    # ======================================
    # F() CARGAR VISTA CARPETAS
    # ======================================
    def cargar_vista_carpetas(self):
        self._expandir_carpetas_con_registros()
        self.arbol_carpetas.controls.clear()
        self.construir_rama()
        self.arbol_carpetas.controls.append(
            ft.Container(
                height=500,
                on_click=self.deseleccionar_carpeta,
            )
        )
        self.page.update()

    def _expandir_carpetas_con_registros(self):
        for registro in self.guardados.obtener():
            nombre_carpeta = registro.get("carpeta", "TARJETAS")
            carpeta = self.carpetas.obtener_por_nombre(nombre_carpeta)

            while carpeta and carpeta.get("padre") is not None:
                padre_id = carpeta.get("padre")
                self.carpetas_expandidas.add(padre_id)
                carpeta = self.carpetas.obtener_por_id(padre_id)
        
    # ======================================
    # F() CONSTRUIR RAMA
    # ======================================
    def construir_rama(self, padre=None, nivel=0):
        hijos = self.carpetas.obtener_hijos(padre)
        
        for carpeta in hijos:
            self.arbol_carpetas.controls.append(
                self.crear_item_arbol(
                    carpeta,
                    nivel
                )
            )

            if carpeta["id"] in self.carpetas_expandidas:
                self.construir_rama(
                    carpeta["id"],
                    nivel + 1
                )
    
        # ======================================
    # CONTAR REGISTROS DE UNA CARPETA
    # ======================================
    def contar_registros_carpeta(self, nombre_carpeta):

        contador = 0
        carpeta = self.carpetas.obtener_por_nombre(nombre_carpeta)

        for registro in self.guardados.obtener():

            if (
                carpeta
                and registro.get("carpeta_id") == carpeta.get("id")
            ) or registro.get("carpeta", "TARJETAS") == nombre_carpeta:
                contador += 1

        return contador

    def titulo_registro(self, registro):
        tipo = registro.get("tipo", "tarjeta")

        if tipo == "fragmento_biblico":
            return registro.get("referencia") or registro.get("nombre") or "Fragmento biblico"

        if tipo == "pizarra":
            return registro.get("nombre") or registro.get("palabra") or "Pizarra"

        if tipo == "analisis_colores":
            return registro.get("nombre") or "Analisis de colores"

        if tipo == "tiempo":
            return registro.get("nombre") or "Tiempo"

        if tipo == "calculo_biblico":
            return registro.get("nombre") or "Suma biblica"

        return registro.get("nombre") or registro.get("palabra") or "Tarjeta"

    def subtitulo_registro(self, registro):
        tipo = registro.get("tipo", "tarjeta")

        if tipo == "fragmento_biblico":
            return registro.get("contenido") or registro.get("suma") or ""

        if tipo == "pizarra":
            extension = registro.get("imagen_extension", "jpg").upper()
            return f"Imagen de pizarra ({extension})"

        if tipo == "analisis_colores":
            contenido = registro.get("contenido") or {}
            total = contenido.get("total_letras") if isinstance(contenido, dict) else None
            return f"{total or 0} letras analizadas"

        if tipo == "tiempo":
            return registro.get("referencia") or "Tiempo"

        if tipo == "calculo_biblico":
            contenido = registro.get("contenido") or {}
            letras = contenido.get("cantidad_letras") if isinstance(contenido, dict) else ""
            referencia = registro.get("referencia") or "Biblia"
            return f"{referencia} | {letras} letras sumadas"

        contenido = registro.get("contenido") or {}
        if isinstance(contenido, dict) and contenido.get("tipo") == "biblia_codificada":
            alcance = contenido.get("alcance") or registro.get("alcance") or "Biblia"
            alfabeto = registro.get("alfabeto", "")
            return f"{alcance} biblico codificado | Alfabeto: {alfabeto}"

        return f"Alfabeto: {registro.get('alfabeto', '')}"

    def resultado_registro(self, registro):
        tipo = registro.get("tipo", "tarjeta")

        if tipo == "fragmento_biblico":
            return "Biblia"

        if tipo == "pizarra":
            return "Pizarra"

        if tipo == "analisis_colores":
            return registro.get("resultado") or "Colores"

        if tipo == "tiempo":
            return "Tiempo"

        if tipo == "calculo_biblico":
            return str(registro.get("resultado") or "")

        return str(registro.get("resultado", ""))

    def etiqueta_tipo_registro(self, registro):
        tipo = registro.get("tipo", "tarjeta")

        if registro.get("subtipo") == "tarjeta_versiculo":
            return "Tarjeta biblica"

        etiquetas = {
            "fragmento_biblico": "Fragmento biblico",
            "pizarra": "Pizarra",
            "analisis_colores": "Analisis de colores",
            "tiempo": "Consulta de tiempo",
            "calculo_biblico": "Calculo biblico",
            "tarjeta": "Tarjeta",
        }
        return etiquetas.get(tipo, "Archivo guardado")

    def fecha_corta_registro(self, registro):
        fecha = str(registro.get("fecha") or "").strip()

        if not fecha:
            return "Sin fecha"

        return fecha.replace("T", " ")[:16]

    def _vista_previa_cuadricula(self, registro):
        tipo = registro.get("tipo", "tarjeta")

        if (
            tipo == "pizarra"
            or registro.get("subtipo") == "tarjeta_versiculo"
            or registro.get("subtipo") == "tarjeta_colores"
            or registro.get("imagen_base64")
            or registro.get("imagen_archivo")
        ):
            return self.preview_registro(registro)

        return ft.Container(
            height=90,
            alignment=ft.Alignment(0, 0),
            bgcolor=ft.Colors.with_opacity(0.05, PURPURA_IOS),
            border_radius=10,
            content=self.icono_registro(registro, grande=True),
        )

    def _selector_orden_guardados(self):
        etiquetas = {
            "Antiguos": "Ordenar por: Más reciente",
            "A-Z": "Ordenar por: A-Z",
            "Resultado": "Ordenar por: Resultado",
        }
        return ft.Dropdown(
            width=210 if not self.es_movil() else 190,
            dense=True,
            value=self.orden_guardados,
            options=[
                ft.dropdown.Option(valor, text=texto)
                for valor, texto in etiquetas.items()
            ],
            on_select=lambda e: self._cambiar_orden_guardados(e.control.value),
        )

    def dialog_filtros_tipo(self):
        def seleccionar(nombre):
            self._cambiar_filtro_tipo(nombre)
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Filtrar guardados"),
            content=ft.Column(
                tight=True,
                spacing=8,
                controls=[
                    ft.OutlinedButton(
                        nombre,
                        icon=ft.Icons.CHECK if nombre == self.filtro_tipo else None,
                        on_click=lambda e, n=nombre: seleccionar(n),
                    )
                    for nombre in ["Todos", "Codificador", "Biblia", "Pizarra", "Colores", "Tiempo", "Calculadora"]
                ],
            ),
            actions=[ft.TextButton("Cancelar", on_click=lambda e: self._cerrar_dialogo(dialog))],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self._refrescar_pagina()

    def _cerrar_dialogo(self, dialogo):
        dialogo.open = False
        self._refrescar_pagina()

    def texto_previsualizacion(self, registro, size=13, max_lines=2, color=None):
        return ft.Text(
            self.subtitulo_registro(registro),
            size=size,
            color=color,
            max_lines=max_lines,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

    def icono_registro(self, registro, grande=False):
        tipo = registro.get("tipo", "tarjeta")

        if tipo == "pizarra":
            ancho = 42 if grande else 30
            alto = 30 if grande else 22
            return ft.Container(
                width=ancho,
                height=alto,
                bgcolor=ft.Colors.WHITE,
                border=ft.Border.all(2, ft.Colors.BLACK),
                border_radius=2,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Stack(
                    controls=[
                        ft.Container(
                            left=5 if grande else 4,
                            top=alto - (8 if grande else 6),
                            width=ancho - (11 if grande else 8),
                            height=2,
                            bgcolor=ft.Colors.BLACK,
                        ),
                        ft.Icon(
                            ft.Icons.EDIT,
                            color=ft.Colors.BLACK,
                            size=22 if grande else 16,
                            left=ancho - (23 if grande else 17),
                            top=1,
                        ),
                    ],
                ),
            )

        if tipo == "fragmento_biblico" and registro.get("subtipo") == "tarjeta_versiculo":
            ancho = 52 if grande else 42
            alto = 34 if grande else 28
            return ft.Container(
                width=ancho,
                height=alto,
                border_radius=5,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                border=ft.Border.all(1, "#D7A934"),
                content=ft.Image(
                    src="tarjeta_versiculo_base.png",
                    width=ancho,
                    height=alto,
                    fit=ft.BoxFit.COVER,
                ),
            )

        if tipo == "fragmento_biblico":
            return ft.Container(
                width=48 if grande else 38,
                height=32 if grande else 26,
                bgcolor="#8B5A2B",
                border=ft.Border.all(1, "#5A3518"),
                border_radius=4,
                alignment=ft.Alignment(0, 0),
                content=ft.Text(
                    "BIBLIA",
                    size=8 if not grande else 10,
                    color=ft.Colors.WHITE,
                    weight=ft.FontWeight.BOLD,
                ),
            )

        if tipo == "analisis_colores":
            return ft.Icon(
                ft.Icons.COLOR_LENS,
                color=ft.Colors.PURPLE_700,
                size=34 if grande else 28,
            )

        if tipo == "tiempo":
            return ft.Icon(
                ft.Icons.HOURGLASS_BOTTOM,
                color="#8B5A2B",
                size=34 if grande else 28,
            )

        if tipo == "calculo_biblico":
            return ft.Icon(
                ft.Icons.FUNCTIONS,
                color=PURPURA_IOS,
                size=34 if grande else 28,
            )

        return ft.Icon(
            ft.Icons.DESCRIPTION,
            color=PURPURA_IOS,
            size=34 if grande else 28,
        )

    def imagen_pizarra_base64(self, registro):
        contenido = registro.get("contenido") or {}
        objetos = contenido.get("objetos", []) if isinstance(contenido, dict) else []

        if objetos:
            return renderizar_lienzo_exportable_base64(contenido)["base64"]

        return registro.get("imagen_base64")

    def datos_imagen_pizarra(self, registro):
        contenido = registro.get("contenido") or {}
        objetos = contenido.get("objetos", []) if isinstance(contenido, dict) else []

        if objetos:
            return renderizar_lienzo_exportable_base64(contenido)

        return {
            "base64": registro.get("imagen_base64"),
            "mime": registro.get("imagen_mime", "image/jpeg"),
            "extension": registro.get("imagen_extension", "jpg"),
        }

    def datos_imagen_registro(self, registro):
        if registro.get("tipo") == "pizarra":
            return self.datos_imagen_pizarra(registro)

        if registro.get("subtipo") == "tarjeta_versiculo":
            archivo_actual = Path(registro.get("imagen_archivo") or "")

            if archivo_actual.exists() and archivo_actual.suffix.lower() in (".jpg", ".jpeg"):
                return {
                    "archivo": str(archivo_actual),
                    "mime": "image/jpeg",
                    "extension": "jpg",
                }

            referencia = registro.get("referencia") or registro.get("nombre") or "Versiculo"
            texto = registro.get("contenido") or registro.get("suma") or ""

            if texto:
                try:
                    imagen = datos_tarjeta_versiculo(referencia, texto)
                    registro["imagen_archivo"] = imagen["archivo"]
                    registro["imagen_mime"] = imagen["mime"]
                    registro["imagen_extension"] = imagen["extension"]
                    return imagen
                except Exception:
                    pass

        archivo = registro.get("imagen_archivo")

        if archivo and Path(archivo).exists():
            return {
                "archivo": str(archivo),
                "mime": registro.get("imagen_mime", "image/jpeg"),
                "extension": registro.get("imagen_extension", "jpg"),
            }

        if registro.get("imagen_base64"):
            return {
                "base64": registro.get("imagen_base64"),
                "mime": registro.get("imagen_mime", "image/jpeg"),
                "extension": registro.get("imagen_extension", "jpg"),
            }

        return None

    def _nombre_archivo_imagen(self, registro, extension):
        base = self.titulo_registro(registro)
        limpio = "".join(
            caracter if caracter.isalnum() else "_"
            for caracter in str(base)
        ).strip("_")
        return f"{limpio or 'imagen_guardada'}.{extension or 'jpg'}"

    def archivo_imagen_registro(self, registro):
        imagen = self.datos_imagen_registro(registro)

        if not imagen:
            return None

        archivo_existente = imagen.get("archivo")

        if archivo_existente and Path(archivo_existente).exists():
            return {
                "archivo": str(archivo_existente),
                "mime": imagen.get("mime", "image/jpeg"),
            }

        if not imagen.get("base64"):
            return None

        extension = (imagen.get("extension") or "jpg").lstrip(".")
        nombre = self._nombre_archivo_imagen(registro, extension)
        archivo = Path(ruta_exportacion(nombre))
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_bytes(base64.b64decode(imagen["base64"]))

        return {
            "archivo": str(archivo),
            "mime": imagen.get("mime", "image/jpeg"),
        }

    def src_imagen_registro(self, imagen):
        if not imagen:
            return None

        mime = imagen.get("mime", "image/png")
        archivo = imagen.get("archivo")

        if archivo:
            try:
                datos = base64.b64encode(Path(archivo).read_bytes()).decode("ascii")
                return f"data:{mime};base64,{datos}"
            except Exception:
                pass

        base64_imagen = imagen.get("base64")

        if base64_imagen:
            base64_imagen = str(base64_imagen).strip()

            if base64_imagen.startswith("data:"):
                return base64_imagen

            return f"data:{mime};base64,{base64_imagen}"

        return None

    def _texto_dorado_tarjeta_guardada(self, texto, size, max_lines=None):
        return ft.Text(
            texto,
            text_align=ft.TextAlign.CENTER,
            max_lines=max_lines,
            overflow=ft.TextOverflow.ELLIPSIS,
            style=ft.TextStyle(
                size=size,
                weight=ft.FontWeight.BOLD,
                color="#FFE47A",
                shadow=[
                    ft.BoxShadow(
                        blur_radius=12,
                        color=ft.Colors.with_opacity(0.70, "#E8AA23"),
                        offset=ft.Offset(0, 0),
                    ),
                    ft.BoxShadow(
                        blur_radius=3,
                        color=ft.Colors.with_opacity(0.55, "#4A2100"),
                        offset=ft.Offset(1.5, 2),
                    ),
                ],
            ),
        )

    def _control_tarjeta_versiculo_guardada(self, registro, ancho=560, compacto=False):
        ancho = max(170, min(float(ancho or 560), 760))
        alto = ancho * 2 / 3
        referencia = registro.get("referencia") or registro.get("nombre") or "Versiculo"
        texto = registro.get("contenido") or registro.get("suma") or ""
        largo_texto = len(texto)
        ref_size = max(12, min(42, ancho * (0.057 if not compacto else 0.070)))
        texto_size = max(
            8,
            min(
                32,
                ancho * (
                    0.050
                    if largo_texto < 130
                    else 0.041
                    if largo_texto < 230
                    else 0.034
                ),
            ),
        )

        if compacto:
            ref_size = min(ref_size, 15)
            texto_size = min(texto_size, 10)

        return ft.Container(
            width=ancho,
            height=alto,
            border_radius=8 if compacto else 18,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            shadow=None if compacto else sombra_suave(),
            content=ft.Stack(
                controls=[
                    ft.Image(
                        src="tarjeta_versiculo_base.png",
                        width=ancho,
                        height=alto,
                        fit=ft.BoxFit.COVER,
                    ),
                    ft.Container(
                        left=ancho * 0.10,
                        right=ancho * 0.10,
                        top=alto * 0.11,
                        content=self._texto_dorado_tarjeta_guardada(
                            referencia,
                            ref_size,
                            max_lines=1,
                        ),
                    ),
                    ft.Container(
                        left=ancho * 0.12,
                        right=ancho * 0.12,
                        top=alto * 0.23,
                        height=1 if compacto else 2,
                        bgcolor=ft.Colors.with_opacity(0.82, "#FFE47A"),
                    ),
                    ft.Container(
                        left=ancho * 0.09,
                        right=ancho * 0.09,
                        top=alto * 0.34,
                        content=self._texto_dorado_tarjeta_guardada(
                            texto,
                            texto_size,
                            max_lines=4 if compacto else 6,
                        ),
                    ),
                ],
            ),
        )

    def _aviso_guardados(self, mensaje):
        self.page.snack_bar = ft.SnackBar(content=ft.Text(mensaje))
        self.page.snack_bar.open = True
        self.page.update()

    def _texto_contraste_color(self, hex_color):
        color = str(hex_color or "").strip().lstrip("#")
        if len(color) == 6:
            try:
                rojo, verde, azul = (int(color[indice:indice + 2], 16) for indice in (0, 2, 4))
                luminancia = (rojo * 299 + verde * 587 + azul * 114) / 1000
                return NEGRO if luminancia >= 155 else BLANCO
            except ValueError:
                pass
        return NEGRO

    def _bloque_color_guardado(self, item, compacto=False):
        color_hex = item.get("hex", "#FFFFFF")
        reducido = item.get("reducido", "")
        digitos = item.get("digitos_colores", [])
        tiene_reduccion = len(digitos) > 1
        ancho = 58 if compacto else 82

        return ft.Container(
            width=ancho,
            padding=4 if compacto else 5,
            bgcolor="#FCFAFF",
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=10,
            content=ft.Column(
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2 if compacto else 3,
                controls=[
                    ft.Container(
                        width=42 if compacto else 50,
                        height=28 if compacto else 34,
                        alignment=ft.Alignment(0, 0),
                        bgcolor=color_hex,
                        border=ft.Border.all(1.5, MARRON) if reducido == 9 else ft.Border.all(1, ft.Colors.WHITE),
                        border_radius=6,
                        content=ft.Text(
                            item.get("letra", ""),
                            size=12 if compacto else 15,
                            weight=ft.FontWeight.BOLD,
                            color=self._texto_contraste_color(color_hex),
                        ),
                    ),
                    ft.Text(str(item.get("valor", "")), size=10 if compacto else 12, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=2,
                        controls=[
                            ft.Text(str(d.get("digito", "")), size=9 if compacto else 11, weight=ft.FontWeight.BOLD)
                            for d in digitos
                        ],
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=2,
                        controls=[
                            ft.Container(
                                width=15 if compacto else 19,
                                height=15 if compacto else 19,
                                bgcolor=d.get("hex", "#FFFFFF"),
                                border=ft.Border.all(1.4, MARRON) if d.get("digito") == 9 else ft.Border.all(1, ft.Colors.GREY_400),
                            )
                            for d in digitos
                        ],
                    ),
                    ft.Container(
                        width=24 if compacto else 28,
                        height=20 if compacto else 24,
                        visible=tiene_reduccion,
                        alignment=ft.Alignment(0, 0),
                        bgcolor=color_hex,
                        border=ft.Border.all(1.4, MARRON) if reducido == 9 else ft.Border.all(1, ft.Colors.GREY_400),
                        content=ft.Text(
                            str(reducido),
                            size=10 if compacto else 12,
                            weight=ft.FontWeight.BOLD,
                            color=self._texto_contraste_color(color_hex),
                        ),
                    ),
                ],
            ),
        )

    def _cuadro_numero_color_guardado(self, valor, color):
        return ft.Container(
            width=max(48, len(str(valor)) * 16 + 20),
            height=40,
            alignment=ft.Alignment(0, 0),
            bgcolor=color,
            border=ft.Border.all(1.5, MARRON) if str(color).upper() == "#FFFFFF" else ft.Border.all(1, PERLA_BORDE),
            border_radius=6,
            content=ft.Text(
                str(valor),
                size=16,
                weight=ft.FontWeight.BOLD,
                color=self._texto_contraste_color(color),
            ),
        )

    def _control_tarjeta_colores_guardada(self, registro, compacto=False):
        contenido = registro.get("contenido") or {}
        if not isinstance(contenido, dict):
            return ft.Text(self.texto_registro(registro), selectable=True)

        detalle = contenido.get("detalle_visual") or []
        limite = 24 if compacto else 120
        visibles = detalle[:limite]
        texto = contenido.get("texto_limpio") or registro.get("referencia") or self.titulo_registro(registro)
        vista_texto = texto if len(texto) <= 70 else texto[:67] + "..."
        pasos = contenido.get("pasos_reduccion") or []
        final = contenido.get("resultado_final") or registro.get("resultado") or ""
        final_hex = contenido.get("hex_final") or "#FFFFFF"

        bloques = [self._bloque_color_guardado(item, compacto=compacto) for item in visibles]
        if len(detalle) > limite:
            bloques.append(
                ft.Container(
                    padding=10,
                    border_radius=10,
                    bgcolor=PERLA_PURPURA,
                    content=ft.Text(f"+ {len(detalle) - limite} caracteres", size=11, color=TEXTO_SECUNDARIO),
                )
            )

        pasos_controles = []
        if pasos:
            pasos_controles.append(self._cuadro_numero_color_guardado(pasos[0], "#F7F0E8"))
            for paso in pasos[1:]:
                pasos_controles.append(ft.Text("=", size=18, weight=ft.FontWeight.BOLD))
                color_paso = final_hex if paso == final else "#FFFFFF"
                pasos_controles.append(self._cuadro_numero_color_guardado(paso, color_paso))

        return ft.Container(
            padding=12 if not compacto else 8,
            bgcolor=PERLA_PANEL,
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=18,
            content=ft.Column(
                tight=True,
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(
                        padding=10,
                        border=ft.Border.all(1, PERLA_BORDE),
                        border_radius=12,
                        content=ft.Column(
                            tight=True,
                            spacing=4,
                            controls=[
                                ft.Text("Texto", size=12, weight=ft.FontWeight.BOLD, color=TEXTO_SECUNDARIO),
                                ft.Text(vista_texto, size=16 if not compacto else 12, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                            ],
                        ),
                    ),
                    ft.Container(
                        padding=10,
                        border=ft.Border.all(1, PERLA_BORDE),
                        border_radius=14,
                        content=ft.Row(
                            wrap=True,
                            spacing=8 if not compacto else 5,
                            run_spacing=10 if not compacto else 6,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            controls=bloques,
                        ),
                    ),
                    ft.Container(
                        padding=12,
                        border=ft.Border.all(1, PERLA_BORDE),
                        border_radius=14,
                        content=ft.Column(
                            tight=True,
                            spacing=8,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text(f"TOTAL DE CODIGOS: {contenido.get('total_codigo', '')}", size=16, weight=ft.FontWeight.BOLD),
                                ft.Text("PROCESO DE REDUCCION", size=12, weight=ft.FontWeight.BOLD, color=TEXTO_SECUNDARIO),
                                ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=8, controls=pasos_controles),
                                ft.Text("RESULTADO FINAL", size=12, weight=ft.FontWeight.BOLD, color=TEXTO_SECUNDARIO),
                                ft.Container(
                                    width=88,
                                    height=58,
                                    alignment=ft.Alignment(0, 0),
                                    bgcolor=final_hex,
                                    border=ft.Border.all(2, MARRON),
                                    border_radius=8,
                                    content=ft.Text(
                                        str(final),
                                        size=28,
                                        weight=ft.FontWeight.BOLD,
                                        color=self._texto_contraste_color(final_hex),
                                    ),
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )

    def preview_registro(self, registro):
        contenido = registro.get("contenido") or {}

        if (
            registro.get("tipo", "tarjeta") == "tarjeta"
            and isinstance(contenido, dict)
            and contenido.get("tipo") == "biblia_codificada"
        ):
            return self.preview_biblia_codificada(registro)

        if registro.get("subtipo") == "tarjeta_versiculo":
            return ft.Container(
                height=120,
                alignment=ft.Alignment(0, 0),
                content=self._control_tarjeta_versiculo_guardada(
                    registro,
                    ancho=180,
                    compacto=True,
                ),
            )

        if registro.get("subtipo") == "tarjeta_colores":
            return ft.Container(
                height=150,
                alignment=ft.Alignment(0, 0),
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=self._control_tarjeta_colores_guardada(registro, compacto=True),
            )

        objetos = contenido.get("objetos", []) if isinstance(contenido, dict) else []
        imagen = self.datos_imagen_registro(registro)
        src_imagen = self.src_imagen_registro(imagen)

        if src_imagen:
            return ft.Container(
                height=110,
                bgcolor=ft.Colors.WHITE,
                border=ft.Border.all(1, ft.Colors.BLACK),
                border_radius=4,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Image(
                    src=src_imagen,
                    fit=ft.BoxFit.CONTAIN,
                ),
            )

        if registro.get("tipo") != "pizarra":
            return ft.Container(height=0)

        ancho = 180
        alto = 86

        if not objetos:
            return ft.Container(
                height=alto,
                bgcolor=ft.Colors.WHITE,
                border=ft.Border.all(1, ft.Colors.BLACK),
                border_radius=4,
            )

        xs = []
        ys = []

        for objeto in objetos:
            if objeto.get("tipo") == "trazo":
                puntos = objeto.get("puntos", [])
                xs.extend(punto[0] for punto in puntos)
                ys.extend(punto[1] for punto in puntos)
            elif "desde" in objeto:
                xs.extend([objeto["desde"][0], objeto["hasta"][0]])
                ys.extend([objeto["desde"][1], objeto["hasta"][1]])
            elif "x" in objeto:
                xs.append(objeto["x"])
                ys.append(objeto["y"])

        min_x = min(xs or [0])
        min_y = min(ys or [0])
        max_x = max(xs or [ancho])
        max_y = max(ys or [alto])
        escala = min(
            ancho / max(max_x - min_x + 20, 1),
            alto / max(max_y - min_y + 20, 1),
        )

        def punto(p):
            return (
                (p[0] - min_x + 10) * escala,
                (p[1] - min_y + 10) * escala,
            )

        controles = []

        for objeto in objetos[:80]:
            tipo = objeto.get("tipo")
            color = objeto.get("color", "#111111")
            grosor = max(objeto.get("grosor", 2) * escala, 1)

            if tipo == "linea":
                x1, y1 = punto(objeto["desde"])
                x2, y2 = punto(objeto["hasta"])
                largo = max(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5, 1)
                angulo = math.atan2(y2 - y1, x2 - x1)
                controles.append(
                    ft.Container(
                        left=x1,
                        top=y1,
                        width=largo,
                        height=grosor,
                        bgcolor=color,
                        rotate=ft.Rotate(angle=angulo, alignment=ft.Alignment(-1, 0)),
                    )
                )
            elif tipo == "trazo":
                puntos = objeto.get("puntos", [])

                for indice in range(max(len(puntos) - 1, 0)):
                    x1, y1 = punto(puntos[indice])
                    x2, y2 = punto(puntos[indice + 1])
                    largo = max(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5, 1)
                    angulo = math.atan2(y2 - y1, x2 - x1)
                    controles.append(
                        ft.Container(
                            left=x1,
                            top=y1,
                            width=largo,
                            height=grosor,
                            bgcolor=color,
                            rotate=ft.Rotate(angle=angulo, alignment=ft.Alignment(-1, 0)),
                        )
                    )
            elif tipo in ("rectangulo", "circulo"):
                x1, y1 = punto(objeto["desde"])
                x2, y2 = punto(objeto["hasta"])
                controles.append(
                    ft.Container(
                        left=min(x1, x2),
                        top=min(y1, y2),
                        width=max(abs(x2 - x1), 4),
                        height=max(abs(y2 - y1), 4),
                        shape=ft.BoxShape.CIRCLE if tipo == "circulo" else ft.BoxShape.RECTANGLE,
                        border=ft.Border.all(grosor, color),
                    )
                )
            elif tipo == "texto":
                x, y = punto((objeto.get("x", 0), objeto.get("y", 0)))
                controles.append(
                    ft.Text(
                        objeto.get("texto", ""),
                        left=x,
                        top=y,
                        size=10,
                        color=color,
                    )
                )

        return ft.Container(
            height=alto,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, ft.Colors.BLACK),
            border_radius=4,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Stack(
                expand=True,
                controls=controles,
            ),
        )

    def texto_biblia_codificada(self, registro):
        contenido = registro.get("contenido") or {}
        if not isinstance(contenido, dict):
            return ""

        return (
            contenido.get("texto_original")
            or contenido.get("texto")
            or registro.get("texto_original")
            or ""
        )

    def preview_biblia_codificada(self, registro):
        contenido = registro.get("contenido") or {}
        referencia = (
            contenido.get("referencia")
            if isinstance(contenido, dict)
            else None
        ) or registro.get("referencia") or self.titulo_registro(registro)
        alcance = (
            contenido.get("alcance")
            if isinstance(contenido, dict)
            else None
        ) or registro.get("alcance") or "Biblia"
        texto = self.texto_biblia_codificada(registro).strip()

        if not texto:
            return ft.Container(height=0)

        texto_previo = texto
        if len(texto_previo) > 1400:
            texto_previo = texto_previo[:1400].rstrip() + "..."

        return ft.Container(
            padding=10,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            content=ft.Column(
                tight=True,
                spacing=6,
                controls=[
                    ft.Text(
                        f"Texto biblico ({alcance})",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        referencia,
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=PURPURA_IOS,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(
                        texto_previo,
                        size=13,
                        max_lines=8,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        selectable=True,
                    ),
                ],
            ),
        )

    def texto_registro(self, registro):
        tipo = registro.get("tipo", "tarjeta")

        if tipo == "fragmento_biblico":
            return (
                f"{registro.get('referencia', '')}\n\n"
                f"{registro.get('contenido') or registro.get('suma') or ''}"
            )

        if tipo == "pizarra":
            contenido = registro.get("contenido") or {}
            objetos = contenido.get("objetos", []) if isinstance(contenido, dict) else []
            return (
                f"{self.titulo_registro(registro)}\n"
                f"Elementos: {len(objetos)}"
            )

        if tipo == "analisis_colores":
            return self.texto_analisis_colores(registro)

        if tipo == "tiempo":
            return (
                f"{self.titulo_registro(registro)}\n"
                f"{registro.get('suma') or registro.get('referencia', '')}"
            )

        if tipo == "calculo_biblico":
            contenido = registro.get("contenido") or {}
            letras = contenido.get("cantidad_letras") if isinstance(contenido, dict) else ""
            alcance = contenido.get("alcance") if isinstance(contenido, dict) else ""
            return (
                f"{self.titulo_registro(registro)}\n"
                f"Referencia: {registro.get('referencia', '')}\n"
                f"Alcance: {alcance}\n"
                f"Letras sumadas: {letras}\n"
                f"Suma total: {registro.get('resultado', '')}"
            )

        contenido = registro.get("contenido") or {}
        if isinstance(contenido, dict) and contenido.get("tipo") == "biblia_codificada":
            texto_biblia = self.texto_biblia_codificada(registro)
            return (
                f"Referencia: {registro.get('referencia', '')}\n"
                f"Alcance: {contenido.get('alcance') or registro.get('alcance', '')}\n"
                f"Alfabeto: {registro.get('alfabeto', '')}\n"
                f"Resultado: {registro.get('resultado', '')}\n\n"
                f"Texto biblico:\n{texto_biblia}\n\n"
                f"Calculo:\n{registro.get('suma', '')}"
            )

        return (
            f"Palabra: {registro.get('palabra', '')}\n"
            f"Alfabeto: {registro.get('alfabeto', '')}\n"
            f"Calculo: {registro.get('suma', '')}\n"
            f"Resultado: {registro.get('resultado', '')}\n"
            f"Referencia: {registro.get('referencia', '')}"
        )

    def texto_analisis_colores(self, registro):
        contenido = registro.get("contenido") or {}

        if not isinstance(contenido, dict):
            return str(registro.get("suma") or contenido or "")

        pasos = " -> ".join(str(p) for p in contenido.get("pasos_reduccion", []))
        detalle = contenido.get("detalle_visual") or []
        partes = []

        for item in detalle[:80]:
            digitos = item.get("digitos_colores", [])
            iconos_digitos = "".join(_icono_color(d.get("color", "")) for d in digitos)
            icono_final = _icono_color(item.get("color", ""))
            if len(digitos) > 1:
                partes.append(f"{item.get('letra', '')} {iconos_digitos} = {icono_final} {item.get('reducido', '')}")
            else:
                partes.append(f"{item.get('letra', '')} {icono_final} {item.get('reducido', '')}")

        total_detalle = contenido.get("detalle_visual_total") or len(detalle)
        if total_detalle > len(detalle):
            partes.append(f"... {total_detalle - len(detalle)} caracteres mas")

        caracteres = " | ".join(partes)
        color_final = contenido.get("color_final", "")
        return (
            "CODIGO ESCONDIDO 19 - COLORES\n\n"
            f"Texto: {registro.get('referencia') or self.titulo_registro(registro)}\n"
            f"Caracteres: {caracteres}\n"
            f"Total de codigos: {contenido.get('total_codigo', registro.get('resultado', ''))}\n"
            f"Proceso de reduccion: {pasos}\n"
            f"Resultado final: {contenido.get('resultado_final', registro.get('resultado', ''))} "
            f"{_icono_color(color_final)} ({_nombre_color_publico(color_final)})"
        )

    def _linea_color_compartir(self, item):
        letra = item.get("letra", "")
        valor = item.get("valor", "")
        reducido = item.get("reducido", "")
        digitos = item.get("digitos_colores", [])
        color_final = _nombre_color_publico(item.get("color", ""))
        icono_final = _icono_color(color_final)

        if len(digitos) > 1:
            partes = [
                f"{d.get('digito')} {_icono_color(d.get('color', ''))} {_nombre_color_publico(d.get('color', ''))}"
                for d in digitos
            ]
            return f"{letra}: {valor} = {' + '.join(partes)} -> {reducido} {icono_final} {color_final}"

        return f"{letra}: {valor} {icono_final} {color_final}"

    def texto_analisis_colores(self, registro):
        contenido = registro.get("contenido") or {}

        if not isinstance(contenido, dict):
            return str(registro.get("suma") or contenido or "")

        pasos = " -> ".join(str(p) for p in contenido.get("pasos_reduccion", []))
        detalle = contenido.get("detalle_visual") or []
        partes = [self._linea_color_compartir(item) for item in detalle]

        referencia = registro.get("referencia") or self.titulo_registro(registro)
        texto_limpio = contenido.get("texto_limpio", "")
        texto = texto_limpio if referencia == "Analisis de colores" else f"{referencia}\n{texto_limpio}"
        color_final = contenido.get("color_final", "")
        return (
            "CODIGO ESCONDIDO 19 - COLORES\n\n"
            f"Texto analizado:\n{texto}\n\n"
            f"Detalle:\n" + "\n".join(partes) + "\n\n"
            f"Total de codigo: {contenido.get('total_codigo', registro.get('resultado', ''))}\n"
            f"Reduccion final: {pasos}\n"
            f"Resultado final: {contenido.get('resultado_final', registro.get('resultado', ''))} "
            f"{_icono_color(color_final)} {_nombre_color_publico(color_final)}"
        )

    def esta_seleccionado(self, registro):
        return registro.get("id") in self.ids_seleccionados

    def toggle_modo_seleccion_multiple(self, e=None):
        self.modo_seleccion_multiple = not self.modo_seleccion_multiple
        self.ids_seleccionados.clear()
        self.tarjeta_seleccionada = None
        self.boton_seleccion_multiple.bgcolor = (
            PERLA_PURPURA
            if self.modo_seleccion_multiple
            else None
        )
        self._actualizar_barra_acciones()
        self.actualizar_tabla()
        self.page.update()

    def tocar_registro(self, registro):
        if self.modo_seleccion_multiple:
            self.toggle_seleccion_multiple(registro)
            return

        self.seleccionar_tarjeta(registro)

    def registros_seleccionados(self):
        ids = set(self.ids_seleccionados)

        if not ids and self.tarjeta_seleccionada:
            ids.add(self.tarjeta_seleccionada.get("id"))

        return [
            registro
            for registro in self.guardados.obtener()
            if registro.get("id") in ids
        ]

    def _actualizar_barra_acciones(self):
        cantidad = len(self.registros_seleccionados())
        # El inicio solo muestra carpetas. Nunca debe conservar acciones de
        # un archivo seleccionado al regresar desde una carpeta.
        self.barra_acciones.visible = cantidad > 0 and not self._esta_en_inicio_guardados()
        self.texto_seleccion.value = (
            f"{cantidad} seleccionado"
            if cantidad == 1
            else f"{cantidad} seleccionados"
        ) if cantidad else ""

    def deseleccionar_actual(self, e=None):
        if (
            not self.tarjeta_seleccionada
            and not self.ids_seleccionados
            and self.carpeta_seleccionada_id is None
        ):
            return

        self.tarjeta_seleccionada = None
        self.ids_seleccionados.clear()
        self.carpeta_seleccionada_id = None
        self.carpeta_seleccionada_nombre = None
        self._actualizar_barra_acciones()
        self.actualizar_tabla()
        self._refrescar_pagina()

    def _zona_vacia_deseleccion(self):
        """Area neutra para quitar una seleccion sin buscar un boton."""
        return ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.BASIC,
            on_tap=self.deseleccionar_actual,
            content=ft.Container(height=300 if self.es_movil() else 180),
        )

    def toggle_seleccion_multiple(self, registro):
        id_registro = registro.get("id")

        if id_registro in self.ids_seleccionados:
            self.ids_seleccionados.remove(id_registro)
        else:
            self.ids_seleccionados.add(id_registro)

        seleccionados = self.registros_seleccionados()
        self.tarjeta_seleccionada = seleccionados[-1] if seleccionados else None
        self._actualizar_barra_acciones()
        self.actualizar_tabla()
        self.page.update()

    def menu_contextual_registro(self, registro):
        self.seleccionar_tarjeta(registro)

        def cerrar(e=None):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text(self.titulo_registro(registro)),
            content=ft.Text("Seleccione una accion para este elemento."),
            actions=[
                ft.TextButton(
                    "Ver",
                    on_click=lambda e: (cerrar(), self.abrir_detalle(registro)),
                ),
                ft.TextButton(
                    "Editar / cambiar nombre",
                    on_click=lambda e: (cerrar(), self.editar_registro(registro)),
                ),
                ft.TextButton(
                    "Copiar",
                    on_click=lambda e: (cerrar(), self.copiar_seleccionado(e)),
                ),
                ft.TextButton(
                    "Enviar / compartir",
                    on_click=lambda e: (cerrar(), self.compartir_seleccionado(e)),
                ),
                ft.TextButton(
                    "Mover",
                    on_click=lambda e: (cerrar(), self._mover_registro_directo(registro)),
                ),
                ft.TextButton(
                    "Eliminar",
                    on_click=lambda e: (cerrar(), self.confirmar_eliminar(registro["id"])),
                ),
                ft.TextButton("Cancelar", on_click=cerrar),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _seleccionar_para_accion_directa(self, registro):
        self.tarjeta_seleccionada = registro
        self.ids_seleccionados = {registro.get("id")}
        self._actualizar_barra_acciones()

    def _mover_registro_directo(self, registro):
        self._seleccionar_para_accion_directa(registro)
        self.mover_seleccionado(None)

    def _compartir_registro_directo_desde_icono(self, registro):
        self._seleccionar_para_accion_directa(registro)
        self.compartir_registro_directo(registro)

    def _area_click_registro(self, registro, content, expand=False):
        return ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            on_tap=lambda e, r=registro: self.tocar_registro(r),
            on_double_tap=lambda e, r=registro: self.abrir_detalle(r),
            on_secondary_tap=lambda e, r=registro: self.menu_contextual_registro(r),
            content=ft.Container(
                expand=expand,
                content=content,
            ),
        )

    def _boton_accion_inline(self, icono, tooltip, accion, ancho, tamano):
        return ft.Container(
            width=ancho,
            height=ancho,
            border_radius=10,
            alignment=ft.Alignment(0, 0),
            ink=True,
            tooltip=tooltip,
            on_click=lambda e: accion(),
            content=ft.Icon(
                icono,
                size=tamano,
                color=TEXTO_SECUNDARIO,
            ),
        )

    def _acciones_registro_inline(self, registro, compacto=False):
        return ft.Container(width=0, height=0)
    # ======================================
    # f() BARRA SUPERIOR
    # ======================================
    def crear_barra_superior(self):
        controles = []

        controles.append(
            ft.Text(
                "Guardados",
                size=24 if self.es_movil() else 28,
                weight=ft.FontWeight.BOLD,
            )
        )

        return ft.Container(
            padding=10,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.START,
                controls=controles,
            )
        )
    
    # ======================================
    # FUNCIO BARRA INFERIOR
    # ======================================
    def crear_barra_estado(self):

        return ft.Container(
            padding=10,
            bgcolor=PERLA_PANEL,

            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    self.texto_contador,
                ]
            )
        )

    # ======================================
    # F() AREA CENTRAL
    # ======================================
    def crear_area_trabajo(self):
        # Una fila expandible, incluso con un único panel, proporciona al
        # contenido el ancho y alto acotados que Flet necesita para dibujarlo.
        return ft.Row(
            expand=True,
            spacing=0,
            controls=[self.panel_derecho],
        )

    def _modo_responsivo(self):
        if self.es_movil():
            return "movil"
        if self.es_tablet():
            return "tablet"
        return "pc"

    def _aplicar_responsive(self):
        if self.es_movil():
            self.panel_izquierdo.width = None
            self.panel_izquierdo.height = 68 if self.carpetas_colapsadas else 168
            self.panel_izquierdo.padding = 8
            self.panel_izquierdo.content = self.crear_barra_carpetas_movil()
            self.panel_derecho.padding = 10
            self.campo_busqueda.width = None
            self.barra_explorador.spacing = 0
            return

        if self.es_tablet():
            self.panel_izquierdo.width = 210
            self.panel_izquierdo.height = None
            self.panel_izquierdo.padding = 10
            self.panel_izquierdo.content = self._contenido_panel_carpetas()
            self.panel_derecho.padding = 8
            self.campo_busqueda.width = 240
            return

        self.panel_izquierdo.width = 250
        self.panel_izquierdo.height = None
        self.panel_izquierdo.padding = 10
        self.panel_izquierdo.content = self._contenido_panel_carpetas()
        self.panel_derecho.padding = 8
        self.campo_busqueda.width = 320

    def _contenido_panel_carpetas(self):
        return ft.Column(
            expand=True,
            spacing=10,
            controls=[
                ft.Container(
                    padding=ft.Padding(left=12, top=8, right=8, bottom=8),
                    bgcolor=PERLA_PURPURA,
                    border=ft.Border.all(1, PERLA_BORDE),
                    border_radius=16,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                "Carpetas",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=TEXTO_PRINCIPAL,
                            ),
                            ft.Row(
                                tight=True,
                                spacing=0,
                                controls=[
                                    self.boton_nueva,
                                    self.boton_renombrar,
                                    self.boton_eliminar,
                                ],
                            ),
                        ],
                    ),
                ),
                self.arbol_carpetas,
            ],
        )

    def crear_barra_carpetas_movil(self):
        controles = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        expand=True,
                        content=ft.Text(
                            self.carpeta_actual_nombre or "Carpetas",
                            weight=ft.FontWeight.BOLD,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ),
                    ft.IconButton(
                        icon=(
                            ft.Icons.KEYBOARD_ARROW_DOWN
                            if self.carpetas_colapsadas
                            else ft.Icons.KEYBOARD_ARROW_UP
                        ),
                        tooltip="Mostrar carpetas",
                        on_click=lambda e: self.toggle_carpetas_movil(),
                    ),
                    self.boton_nueva,
                ],
            )
        ]

        if not self.carpetas_colapsadas:
            controles.append(
                ft.Row(
                    scroll=ft.ScrollMode.AUTO,
                    spacing=8,
                    controls=[
                        self._chip_carpeta(carpeta)
                        for carpeta in self.carpetas.obtener()
                    ],
                )
            )

        return ft.Column(
            tight=True,
            spacing=6,
            controls=controles,
        )

    def _chip_carpeta(self, carpeta):
        seleccionada = self.carpeta_actual_id == carpeta["id"]
        ruta = self.carpetas.obtener_ruta(carpeta["id"])
        texto = " / ".join(c["nombre"] for c in ruta)

        return ft.Container(
            width=180,
            padding=ft.Padding(left=12, top=9, right=12, bottom=9),
            bgcolor=PERLA_PURPURA if seleccionada else SUPERFICIE_PERLADA,
            border=ft.Border.all(1.4 if seleccionada else 1, PURPURA_IOS if seleccionada else PERLA_BORDE),
            border_radius=18,
            shadow=sombra_suave(0.035, 12, 0, 4) if seleccionada else None,
            on_click=lambda e, c=carpeta: self.seleccionar_carpeta_arbol(c),
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.FOLDER, size=18, color=PURPURA_IOS if seleccionada else "#B97852"),
                    ft.Text(
                        texto,
                        expand=True,
                        size=12,
                        weight=ft.FontWeight.BOLD if seleccionada else None,
                        color=PURPURA_IOS if seleccionada else TEXTO_SECUNDARIO,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
            ),
        )

    def toggle_carpetas_movil(self):
        self.carpetas_colapsadas = not self.carpetas_colapsadas
        self.router.refrescar()

    def _tarjeta_visual(self, content, padding=18, expand=False):
        return ft.Container(
            expand=expand,
            padding=padding,
            bgcolor=SUPERFICIE_PERLADA,
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=8,
            shadow=sombra_suave(0.055, 18, 0, 6),
            content=content,
        )

    def _estilo_carpeta(self, carpeta):
        return ESTILOS_CARPETAS.get(
            carpeta.get("nombre", "").upper(),
            ("#B97852", "#FFF1E8", ft.Icons.FOLDER),
        )

    def _cantidad_registros_carpeta(self, carpeta):
        carpeta_id = carpeta.get("id")
        nombre = carpeta.get("nombre")
        return sum(
            1
            for registro in self.guardados.obtener()
            if (
                registro.get("carpeta_id") == carpeta_id
                or (
                    registro.get("carpeta_id") is None
                    and registro.get("carpeta", "TARJETAS") == nombre
                )
            )
        )

    def _abrir_o_seleccionar_carpeta(self, carpeta):
        if self.es_movil():
            self._entrar_carpeta_explorador(carpeta)
        else:
            self._seleccionar_carpeta_explorador(carpeta)

    def _tarjeta_carpeta_resumen(self, carpeta, cuadricula=False):
        color, fondo, icono = self._estilo_carpeta(carpeta)
        cantidad = self._cantidad_registros_carpeta(carpeta)
        seleccionada = carpeta.get("id") == self.carpeta_seleccionada_id

        if cuadricula:
            ancho = (
                max(86, min(108, int((self.ancho_actual() - 54) / 3)))
                if self.es_movil()
                else 190
            )
            alto = 138 if self.es_movil() else 164
            return ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK,
                on_tap=lambda e, c=carpeta: self._abrir_o_seleccionar_carpeta(c),
                on_double_tap=lambda e, c=carpeta: self._entrar_carpeta_explorador(c),
                on_secondary_tap=lambda e, c=carpeta: self.menu_contextual_carpeta(c),
                content=ft.Container(
                    width=ancho,
                    height=alto,
                    padding=10,
                    bgcolor=PERLA_PURPURA if seleccionada else BLANCO,
                    border=ft.Border.all(1.5 if seleccionada else 1, color if seleccionada else PERLA_BORDE),
                    border_radius=18,
                    shadow=sombra_suave(0.035, 12, 0, 4),
                    content=ft.Column(
                        tight=True,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=7,
                        controls=[
                            ft.Container(
                                width=48 if self.es_movil() else 58,
                                height=48 if self.es_movil() else 58,
                                alignment=ft.Alignment(0, 0),
                                bgcolor=fondo,
                                border_radius=16,
                                content=ft.Icon(icono, color=color, size=27 if self.es_movil() else 31),
                            ),
                            ft.Text(
                                carpeta.get("nombre", "Carpeta"),
                                size=11 if self.es_movil() else 13,
                                weight=ft.FontWeight.BOLD,
                                color=TEXTO_PRINCIPAL,
                                text_align=ft.TextAlign.CENTER,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Row(
                                tight=True,
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Icon(ft.Icons.FOLDER_OUTLINED, size=14, color=color),
                                    ft.Text(
                                        str(cantidad),
                                        size=11,
                                        color=TEXTO_SECUNDARIO,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ),
            )

        return ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            on_tap=lambda e, c=carpeta: self._seleccionar_carpeta_explorador(c),
            on_double_tap=lambda e, c=carpeta: self._entrar_carpeta_explorador(c),
            on_secondary_tap=lambda e, c=carpeta: self.menu_contextual_carpeta(c),
            content=ft.Container(
                height=78 if self.es_movil() else 82,
                padding=ft.Padding(left=13, top=10, right=8, bottom=10),
                bgcolor=PERLA_PURPURA if seleccionada else BLANCO,
                border=ft.Border.all(1.5 if seleccionada else 1, color if seleccionada else PERLA_BORDE),
                border_radius=8,
                content=ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=42,
                            height=42,
                            alignment=ft.Alignment(0, 0),
                            bgcolor=fondo,
                            border_radius=8,
                            content=ft.Icon(icono, color=color, size=22),
                        ),
                        ft.Container(
                            expand=True,
                            content=ft.Column(
                                tight=True,
                                spacing=3,
                                controls=[
                                    ft.Text(
                                        carpeta.get("nombre", "Carpeta"),
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                        color=TEXTO_PRINCIPAL,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Text(
                                        f"{cantidad} elemento{'s' if cantidad != 1 else ''}",
                                        size=11,
                                        color=TEXTO_SECUNDARIO,
                                        max_lines=1,
                                    ),
                                ],
                            ),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.MORE_VERT,
                            tooltip="Acciones de carpeta",
                            icon_color=TEXTO_SECUNDARIO,
                            on_click=lambda e, c=carpeta: self.menu_contextual_carpeta(c),
                        ),
                    ],
                ),
            ),
        )

    def _seccion_carpetas_principales(self, carpetas=None):
        carpetas = carpetas if carpetas is not None else self.carpetas.obtener_hijos(None)
        if not carpetas:
            return ft.Container(
                padding=30,
                alignment=ft.Alignment(0, 0),
                content=ft.Text("No se encontraron carpetas", color=TEXTO_SECUNDARIO),
            )

        filas = [carpetas[indice:indice + 3] for indice in range(0, len(carpetas), 3)]
        return ft.Column(
            tight=True,
            spacing=10 if self.es_movil() else 16,
            controls=[
                ft.Row(
                    spacing=10 if self.es_movil() else 16,
                    controls=[
                        self._tarjeta_carpeta_resumen(carpeta, cuadricula=True)
                        for carpeta in fila
                    ],
                )
                for fila in filas
            ],
        )

    def _hero_guardados_visual(self):
        return ft.Container(
            padding=ft.Padding(left=16, top=8, right=10, bottom=8),
            bgcolor=PERLA_PANEL,
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=14,
            shadow=sombra_suave(0.03, 10, 0, 3),
            content=ft.Row(
                tight=True,
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        "Guardados",
                        size=21 if self.es_movil() else 24,
                        weight=ft.FontWeight.BOLD,
                        color=TEXTO_PRINCIPAL,
                    ),
                    ft.Container(
                        width=34,
                        height=34,
                        alignment=ft.Alignment(0, 0),
                        bgcolor=PERLA_PURPURA,
                        border=ft.Border.all(1, PERLA_BORDE),
                        border_radius=10,
                        ink=True,
                        tooltip="Crear carpeta",
                        on_click=lambda e: self.dialog_crear_carpeta(),
                        content=ft.Icon(
                            ft.Icons.CREATE_NEW_FOLDER,
                            size=18,
                            color=PURPURA_IOS,
                        ),
                    ),
                ],
            ),
        )

    # ======================================
    # OBTENER VISTA
    # ======================================
    def on_enter(self):
        if not self.es_movil():
            self.router.menu_lateral_abierto = False
        self._aplicar_carpeta_preferida()

    def _aplicar_carpeta_preferida(self):
        id_carpeta = getattr(state, "carpeta_guardados_preferida", None)

        if not id_carpeta:
            return

        carpeta = self.carpetas.obtener_por_id(id_carpeta)

        if not carpeta:
            state.carpeta_guardados_preferida = None
            return

        self.carpeta_actual_id = carpeta["id"]
        self.carpeta_actual_nombre = carpeta["nombre"]
        self.carpeta_seleccionada_id = carpeta["id"]
        self.carpeta_seleccionada_nombre = carpeta["nombre"]
        self.ruta_carpetas = self.carpetas.obtener_ruta(carpeta["id"])
        self.carpetas_expandidas.update(
            item["id"]
            for item in self.ruta_carpetas
        )
        state.carpeta_guardados_preferida = None

    def obtener_vista(self):
        self.page.on_resize = self._on_resize

        self._aplicar_responsive()
        self._modo_responsivo_anterior = self._modo_responsivo()
        self._aplicar_carpeta_preferida()
        # La navegación principal ya no muestra el árbol secundario. Evitar
        # actualizar la página antes de que el panel sea incorporado al árbol
        # visual previene que Flet renderice un contenedor vacío.
        self.actualizar_barra_ruta(actualizar=False)
        self.actualizar_tabla()

        contenido_guardados = ft.Column(
            expand=True,
            spacing=10,
            controls=[
                self._hero_guardados_visual(),
                self.crear_area_trabajo(),
            ],
        )

        return ft.Container(
            expand=True,
            padding=8 if not self.es_movil() else 6,
            content=contenido_guardados,
        )
    # ======================================
    # EXPLORADOR DE CARPETAS (LÓGICA)
    # ======================================
    def cargar_arbol_carpetas(self):
        self.arbol_carpetas.controls.clear()

        carpetas= self.carpetas.obtener()

        for carpeta in carpetas:
            self.arbol_carpetas.controls.append(
                self.crear_item_arbol(carpeta)
            )
        self.page.update()

    # ======================================
    # F() CREAR ITEM ARBOL
    # ======================================
    def crear_item_arbol(self, carpeta, nivel=0):
        seleccionado = (
            self.carpeta_seleccionada_id == carpeta["id"]
        )
        abierta = carpeta["id"] in self.carpetas_expandidas
        hijos = self.carpetas.obtener_hijos(carpeta["id"])
        tiene_hijos = bool(hijos)
        cantidad = self.contar_registros_carpeta(carpeta["nombre"])

        flecha = (
            ft.Icons.KEYBOARD_ARROW_DOWN
            if abierta
            else ft.Icons.KEYBOARD_ARROW_RIGHT
        )

        fondo = PERLA_PURPURA if seleccionado else SUPERFICIE_PERLADA
        borde = PURPURA_IOS if seleccionado else PERLA_BORDE
        texto_color = PURPURA_IOS if seleccionado else TEXTO_PRINCIPAL
        detalle_color = PURPURA_IOS if seleccionado else TEXTO_SECUNDARIO

        return ft.Container(
            padding=ft.Padding(left=nivel * 14, top=4, bottom=4, right=4),
            content=ft.Container(
                padding=ft.Padding(left=8, top=8, bottom=8, right=10),
                bgcolor=fondo,
                border=ft.Border.all(1.3 if seleccionado else 1, borde),
                border_radius=16,
                shadow=sombra_suave(0.04, 12, 0, 4) if seleccionado else None,
                content=ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.GestureDetector(
                            mouse_cursor=ft.MouseCursor.CLICK,
                            on_tap=lambda e: self.expandir_colapsar(carpeta["id"]),
                            content=ft.Container(
                                width=26,
                                height=32,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(
                                    flecha if tiene_hijos else ft.Icons.CIRCLE,
                                    size=18 if tiene_hijos else 6,
                                    color=PURPURA_IOS if tiene_hijos else PERLA_BORDE,
                                ),
                            ),
                        ),
                        ft.Container(
                            width=34,
                            height=34,
                            border_radius=13,
                            bgcolor=ft.Colors.with_opacity(
                                0.16 if seleccionado else 0.10,
                                PURPURA_IOS if seleccionado else "#B97852",
                            ),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(
                                ft.Icons.FOLDER_OPEN if abierta else ft.Icons.FOLDER,
                                color=PURPURA_IOS if seleccionado else "#B97852",
                                size=19,
                            ),
                        ),
                        ft.Container(
                            expand=True,
                            content=ft.GestureDetector(
                                mouse_cursor=ft.MouseCursor.CLICK,
                                on_tap=lambda e: self.seleccionar_carpeta_arbol(carpeta),
                                on_double_tap=lambda e: self.entrar_carpeta(carpeta["nombre"]),
                                on_secondary_tap=lambda e, c=carpeta: self.menu_contextual_carpeta(c),
                                content=ft.Column(
                                    tight=True,
                                    spacing=1,
                                    controls=[
                                        ft.Text(
                                            carpeta["nombre"],
                                            size=13,
                                            weight=ft.FontWeight.BOLD if seleccionado else ft.FontWeight.NORMAL,
                                            color=texto_color,
                                            max_lines=1,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                        ),
                                        ft.Text(
                                            f"{cantidad} elemento{'s' if cantidad != 1 else ''}",
                                            size=10,
                                            color=detalle_color,
                                        ),
                                    ],
                                ),
                            ),
                        ),
                    ],
                ),
            ),
        )
    # ======================================
    # F() ALTERNAR CARPETA
    # ======================================
    def alternar_carpeta(self, nombre):
        carpeta = self.carpetas.obtener_por_nombre(nombre)

        if carpeta is None:
            return

        self.expandir_colapsar(carpeta["id"])

    # ======================================
    # F() EXPANDIR COLAPSAR
    # ======================================
    def expandir_colapsar(self, id_carpeta):

        if id_carpeta in self.carpetas_expandidas:
            self.carpetas_expandidas.remove(
                id_carpeta
            )
        else:
            self.carpetas_expandidas.add(
                id_carpeta
            )
        self.cargar_vista_carpetas()
        self.page.update()

    # ======================================
    # F() SELECCION CARPETA ARBOL
    # ======================================
    def seleccionar_carpeta_arbol(self, carpeta):

        self.carpeta_actual_id = carpeta["id"]
        self.carpeta_actual_nombre = carpeta["nombre"]

        self.tarjeta_seleccionada = None
        self.ids_seleccionados.clear()
        self.modo_seleccion_multiple = False
        self.boton_seleccion_multiple.bgcolor = None


        self.carpeta_seleccionada_id = carpeta["id"]
        self.carpeta_seleccionada_nombre = carpeta["nombre"]

        self.ruta_carpetas = self.carpetas.obtener_ruta(
            carpeta["id"]
        )

        es_raiz = self.carpetas.es_raiz_fija(carpeta["id"])
        self.boton_renombrar.disabled = es_raiz
        self.boton_eliminar.disabled = es_raiz

        self.actualizar_barra_ruta()
        self.actualizar_tabla()
        self.cargar_vista_carpetas()
        self._refrescar_pagina()
    # ======================================
    # F() SELECCIONAR CARPETA
    # ======================================
    def seleccionar_carpeta(self, nombre):
        self.carpeta_seleccionada_nombre = nombre
        self.cargar_vista_carpetas()
        self.page.update()
    
    # ======================================
    # FUNCION CREAR ICIONO CARPETA
    # ======================================

    def crear_icono_carpeta(self, nombre):
        es_seleccionada = (self.carpeta_seleccionada_nombre == nombre)
        es_actual = (self.carpeta_actual_nombre == nombre)
        
        bg_color = PERLA_PURPURA if es_seleccionada else None
        border_color = ft.Colors.BLUE if es_actual else ft.Colors.TRANSPARENT

        return ft.GestureDetector(
            on_tap=lambda e: self.seleccionar_carpeta(nombre),
            on_double_tap=lambda e: self.entrar_carpeta(nombre),
            on_secondary_tap=lambda e: self.menu_contextual_carpeta(nombre),
            content=ft.Container(
                width=100,
                padding=10,
                border=ft.Border.all(2, border_color),
                border_radius=8,
                bgcolor=bg_color,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.FOLDER, size=50, color=ft.Colors.YELLOW_700),
                        ft.Text(
                            nombre, 
                            text_align=ft.TextAlign.CENTER, 
                            max_lines=2, 
                            overflow=ft.TextOverflow.ELLIPSIS, 
                            size=12
                        )
                    ]
                )
            )
        )

    # =========================================
    # F() ENTRAR CARPETA
    # =========================================
    def entrar_carpeta(self, nombre):
        carpeta = self.carpetas.obtener_por_nombre(nombre)

        if carpeta is None:
            return

        self.carpeta_actual_id = carpeta["id"]
        self.carpeta_actual_nombre = carpeta["nombre"]

        self.tarjeta_seleccionada = None
        self.ids_seleccionados.clear()
        self.modo_seleccion_multiple = False
        self.boton_seleccion_multiple.bgcolor = None

        self.carpeta_seleccionada_id = carpeta["id"]
        self.carpeta_seleccionada_nombre = carpeta["nombre"]

        self.ruta_carpetas = self.carpetas.obtener_ruta(
            carpeta["id"]
        )

        self.actualizar_barra_ruta()
        self.actualizar_tabla()
        self.cargar_vista_carpetas()
        self._refrescar_pagina()
    # ======================================
    # ACTUALIZAR BARRA DE RUTA
    # ======================================
    def actualizar_barra_ruta(self, actualizar=True):
        self.barra_ruta.controls.clear()

        # En el nivel general no hay ruta que mostrar. Dentro de carpetas se
        # usa una sola flecha: el explorador queda claro incluso en celular.
        if self.carpeta_actual_id is None:
            self.barra_ruta.visible = False
        else:
            self.barra_ruta.visible = True
            ruta = self.ruta_carpetas or []
            carpeta_anterior = ruta[-2] if len(ruta) > 1 else None

            if carpeta_anterior:
                volver = lambda e, c=carpeta_anterior: self.volver_a_carpeta(c)
                ayuda = f"Volver a {carpeta_anterior['nombre']}"
            else:
                volver = lambda e: self.volver_inicio()
                ayuda = "Volver a Guardados"

            self.barra_ruta.controls.extend([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    tooltip=ayuda,
                    icon_color=PURPURA_IOS,
                    on_click=volver,
                ),
                ft.Text(
                    self.carpeta_actual_nombre or "Guardados",
                    size=16,
                    color=TEXTO_PRINCIPAL,
                    weight=ft.FontWeight.BOLD,
                ),
            ])

        if actualizar:
            self._refrescar_pagina()
    
    # F(VOLVER INICIO)=======================================
    def volver_inicio(self):

        general = self.carpetas.obtener_por_nombre("TARJETAS")

        self.carpeta_actual_id = None
        self.carpeta_actual_nombre = None

        self.carpeta_seleccionada_id = None
        self.carpeta_seleccionada_nombre = None 

        self.tarjeta_seleccionada = None
        self.ids_seleccionados.clear()
        self.modo_seleccion_multiple = False
        self.boton_seleccion_multiple.bgcolor = None

        self.ruta_carpetas = []

        self.actualizar_barra_ruta()
        self.actualizar_tabla()
        self.cargar_vista_carpetas()
        self._refrescar_pagina()
    
    # F(CARGAR A CARPETA)====================================
    def volver_a_carpeta(self, carpeta):
        self.carpeta_actual_id = carpeta["id"]
        self.carpeta_actual_nombre = carpeta["nombre"]

        self.carpeta_seleccionada_id = carpeta["id"]
        self.carpeta_seleccionada_nombre = carpeta["nombre"]

        self.tarjeta_seleccionada = None
        self.ids_seleccionados.clear()
        self.modo_seleccion_multiple = False
        self.boton_seleccion_multiple.bgcolor = None

        self.ruta_carpetas = self.carpetas.obtener_ruta(
            carpeta["id"]
        )

        self.actualizar_barra_ruta()
        self.actualizar_tabla()
        self.cargar_vista_carpetas()
        self._refrescar_pagina()
   
    #F(OBTENER REGISTROS ACTUALES)===========================
    def obtener_registros_actuales(self):
        carpeta = self.carpeta_actual_nombre or "TARJETAS"
        return [
            r for r in self.guardados.obtener()
            if r.get("carpeta", "TARJETAS") == carpeta
        ]

    def _subcarpetas_actuales(self):
        if self.carpeta_actual_id is None:
            return []

        return self.carpetas.obtener_hijos(self.carpeta_actual_id)

    def _seleccionar_carpeta_explorador(self, carpeta):
        """Marca una carpeta sin abrirla, igual que un clic en Windows."""
        self.carpeta_seleccionada_id = carpeta["id"]
        self.carpeta_seleccionada_nombre = carpeta["nombre"]
        self.actualizar_tabla()
        self._refrescar_pagina()

    def _entrar_carpeta_explorador(self, carpeta):
        """Abre una carpeta con doble clic."""
        self.seleccionar_carpeta_arbol(carpeta)

    def _abrir_subcarpeta(self, carpeta):
        self._entrar_carpeta_explorador(carpeta)

    def _tarjeta_subcarpeta(self, carpeta):
        cantidad = self.contar_registros_carpeta(carpeta["nombre"])
        hijos = self.carpetas.obtener_hijos(carpeta["id"])
        seleccionada = carpeta["id"] == self.carpeta_seleccionada_id

        return ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            on_tap=lambda e, c=carpeta: self._seleccionar_carpeta_explorador(c),
            on_double_tap=lambda e, c=carpeta: self._abrir_subcarpeta(c),
            on_secondary_tap=lambda e, c=carpeta: self.menu_contextual_carpeta(c),
            content=ft.Container(
                width=210,
                padding=ft.Padding(left=12, top=10, right=12, bottom=10),
                bgcolor=PERLA_PURPURA if seleccionada else SUPERFICIE_PERLADA,
                border=ft.Border.all(1.4 if seleccionada else 1, PURPURA_IOS if seleccionada else PERLA_BORDE),
                border_radius=18,
                shadow=sombra_suave(0.035, 12, 0, 4),
                content=ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=38,
                            height=38,
                            border_radius=14,
                            bgcolor=ft.Colors.with_opacity(0.11, "#B97852"),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(
                                ft.Icons.FOLDER,
                                color="#B97852",
                                size=22,
                            ),
                        ),
                        ft.Container(
                            expand=True,
                            content=ft.Column(
                                tight=True,
                                spacing=2,
                                controls=[
                                    ft.Text(
                                        carpeta["nombre"],
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                        color=TEXTO_PRINCIPAL,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Text(
                                        f"{cantidad} elemento{'s' if cantidad != 1 else ''}"
                                        + (f" - {len(hijos)} carpeta{'s' if len(hijos) != 1 else ''}" if hijos else ""),
                                        size=10,
                                        color=TEXTO_SECUNDARIO,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                ],
                            ),
                        ),
                        ft.Icon(
                            ft.Icons.CHEVRON_RIGHT,
                            size=18,
                            color=PURPURA_IOS,
                        ),
                    ],
                ),
            ),
        )

    def _seccion_subcarpetas(self, carpetas):
        return ft.Column(
            tight=True,
            spacing=8,
            controls=[
                ft.Text(
                    "Carpetas",
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=TEXTO_SECUNDARIO,
                ),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        self._tarjeta_subcarpeta(carpeta)
                        for carpeta in carpetas
                    ],
                ),
            ],
        )
     
    # =========================================
    # F() CARGAR CONTENIDO CARPETA
    # =========================================
    def cargar_contenido_carpeta(self):
        self.panel_contenido.controls.clear()
        self.panel_contenido.horizontal_alignment = (
            ft.CrossAxisAlignment.START
        )
        self.panel_contenido.controls.append(
            ft.Text(
                f"📁 {self.carpeta_actual_nombre}",
                size=22,
                weight=ft.FontWeight.BOLD
            )
        )

        registros = [
            r
            for r in self.guardados.obtener()
            if r.get("carpeta","TARJETAS") == self.carpeta_actual_nombre
        ]

        if not registros:
            self.panel_contenido.controls.append(
                ft.Text(
                    "Carpeta vacía",
                    color=ft.Colors.GREY_600
                )
            )

        else:
            for registro in registros:
                self.panel_contenido.controls.append(
                    self.crear_tarjeta(registro)
                )

        self.page.update()

    # =========================================
    # F() MENU
    # =========================================   
    def menu_contextual_carpeta(self, carpeta_o_nombre):
        carpeta = (
            carpeta_o_nombre
            if isinstance(carpeta_o_nombre, dict)
            else self.carpetas.obtener_por_nombre(carpeta_o_nombre)
        )

        if carpeta is None:
            return

        nombre = carpeta["nombre"]

        def preparar_carpeta():
            self.carpeta_seleccionada_id = carpeta["id"]
            self.carpeta_seleccionada_nombre = carpeta["nombre"]

        def cerrar(e=None):
            dialog.open = False
            self.page.update()
            def eliminar_dialogo():
                if dialog in self.page.overlay:
                    self.page.overlay.remove(dialog)
            ejecutar_demorado(self.page, 0.1, eliminar_dialogo)

        dialog = ft.AlertDialog(
            title=ft.Text(f"Carpeta: {nombre}"),
            content=ft.Text("Seleccione una acción:"),
            actions=[
                ft.TextButton("Abrir", on_click=lambda e, c=carpeta: (cerrar(), self._abrir_subcarpeta(c))),
                ft.TextButton("Cambiar nombre", on_click=lambda e: (preparar_carpeta(), cerrar(), self.renombrar_carpeta(None))),
                ft.TextButton("Eliminar", on_click=lambda e: (preparar_carpeta(), cerrar(), self.confirmar_eliminar_carpeta(nombre))),
                ft.TextButton("Cancelar", on_click=cerrar),
            ]
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def menu_contextual_fondo(self, e):
        def cerrar(e=None):
            dialog.open = False
            self.page.update()
            def eliminar_dialogo():
                if dialog in self.page.overlay:
                    self.page.overlay.remove(dialog)
            ejecutar_demorado(self.page, 0.1, eliminar_dialogo)

        dialog = ft.AlertDialog(
            title=ft.Text("Lienzo de carpetas"),
            content=ft.Text("¿Qué desea hacer?"),
            actions=[
                ft.TextButton("Nueva carpeta", on_click=lambda e: (cerrar(), self.dialog_crear_carpeta())),
                ft.TextButton("Cancelar", on_click=cerrar),
            ]
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    # =============================================
    # F() CREAR CARPETA
    # =============================================
    def dialog_crear_carpeta(self):
        if self.carpeta_seleccionada_id is None:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Seleccione primero una carpeta principal.")
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        campo = ft.TextField(
            label="Nombre de la nueva carpeta",
            autofocus=True,
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
        )
        
        def cerrar(e=None):
            dialog.open = False
            self.page.update()
            
            def eliminar_dialogo():
                if dialog in self.page.overlay:
                    self.page.overlay.remove(dialog)
            ejecutar_demorado(self.page, 0.1, eliminar_dialogo)

        def aceptar(e):
            ocultar_teclado(self.page, campo)
            nombre = campo.value.strip()
            
            if nombre:
                self.carpetas.crear(
                    nombre,
                    padre=self.carpeta_seleccionada_id
                )
                if self.carpeta_seleccionada_id:
                    self.carpetas_expandidas.add(
                        self.carpeta_seleccionada_id
                    )
                self.cargar_vista_carpetas()
            cerrar()

        campo.on_submit = aceptar

        dialog = ft.AlertDialog(title=ft.Text("Nueva Carpeta"), content=campo, actions=[
            ft.TextButton("Cancelar", on_click=cerrar),
            ft.ElevatedButton("Crear", on_click=aceptar),
        ])
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def dialog_renombrar_carpeta(self, nombre_viejo):
        carpeta = self.carpetas.obtener_por_nombre(nombre_viejo)

        if carpeta is None:
            return

        campo = ft.TextField(
            label="Nuevo nombre",
            value=nombre_viejo,
            autofocus=True,
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
        )
        def cerrar(e=None):
            dialog.open = False
            self.page.update()
            def eliminar_dialogo():
                if dialog in self.page.overlay:
                    self.page.overlay.remove(dialog)
            ejecutar_demorado(self.page, 0.1, eliminar_dialogo)

        def aceptar(e):
            ocultar_teclado(self.page, campo)
            nombre_nuevo = campo.value.strip()
            if nombre_nuevo and nombre_nuevo != nombre_viejo:
                self.carpetas.renombrar(carpeta["id"], nombre_nuevo)
                if self.carpeta_actual_nombre == nombre_viejo:
                    self.carpeta_actual_nombre = nombre_nuevo
                if self.carpeta_seleccionada_nombre == nombre_viejo:
                    self.carpeta_seleccionada_nombre = nombre_nuevo
                self.cargar_vista_carpetas()
                self.actualizar_barra_ruta()
                self.actualizar_tabla()
            cerrar()

        campo.on_submit = aceptar

        dialog = ft.AlertDialog(title=ft.Text("Renombrar Carpeta"), content=campo, actions=[
            ft.TextButton("Cancelar", on_click=cerrar),
            ft.ElevatedButton("Guardar", on_click=aceptar),
        ])
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def confirmar_eliminar_carpeta(self, nombre):
        carpeta = None

        if self.carpeta_seleccionada_nombre == nombre:
            carpeta = self.carpetas.obtener_por_id(self.carpeta_seleccionada_id)

        if carpeta is None:
            carpeta = self.carpetas.obtener_por_nombre(nombre)

        if carpeta is None:
            return

        def cerrar(e=None):
            dialog.open = False
            self.page.update()
            def eliminar_dialogo():
                if dialog in self.page.overlay:
                    self.page.overlay.remove(dialog)
            ejecutar_demorado(self.page, 0.1, eliminar_dialogo)

        def aceptar(e):
            self.carpetas.eliminar(carpeta["id"])
            if self.carpeta_actual_nombre == nombre:
                self.carpeta_actual_nombre = "TARJETAS"
                self.carpeta_actual_id = 1
                self.carpeta_seleccionada_nombre = "TARJETAS"
                self.carpeta_seleccionada_id = 1
                self.ruta_carpetas = [{"id": 1, "nombre": "TARJETAS"}]
            self.cargar_vista_carpetas()
            self.actualizar_barra_ruta()
            self.actualizar_tabla()
            cerrar()

        dialog = ft.AlertDialog(
            title=ft.Text("Eliminar Carpeta"),
            content=ft.Text(f"¿Seguro que quieres eliminar la carpeta '{nombre}' y todo su contenido?"),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar),
                ft.ElevatedButton("Eliminar", color=ft.Colors.WHITE, bgcolor=ft.Colors.RED, on_click=aceptar),
            ]
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    # ======================================
    # CREAR TARJETA
    # ======================================
    def crear_tarjeta(self, registro):

        seleccionada = self.esta_seleccionado(registro)

        referencia = ft.TextField(
            value=registro.get("referencia", ""),

            label="Referencia",

            expand=True,

            max_lines=1,
            on_submit=lambda e: ocultar_teclado(self.page, e.control),
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),

            on_change=lambda e:
                self.cambiar_referencia(
                    registro["id"],
                    e.control.value
                ),
        )


        return ft.Card(

                elevation=1,

                content=ft.Container(

                    padding=15,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,

                    bgcolor=(

                        PERLA_PURPURA
                        if seleccionada
                        else "#FFFFFF"

                    ),


                    border=ft.Border.all(

                        2
                        if seleccionada
                        else 1,

                        ft.Colors.BLUE
                        if seleccionada
                        else "#E8E0EC"

                    ),


                    border_radius=20,


                    content=ft.Column(

                        spacing=10,


                        controls=[


                            ft.Row(

                                alignment=
                                ft.MainAxisAlignment.SPACE_BETWEEN,


                                controls=[


                                    ft.Row(
                                        spacing=8,
                                        expand=True,
                                        controls=[
                                            ft.Checkbox(
                                                visible=self.modo_seleccion_multiple,
                                                value=seleccionada,
                                                on_change=lambda e, r=registro:
                                                    self.toggle_seleccion_multiple(r),
                                            ),
                                            self._area_click_registro(
                                                registro,
                                                ft.Row(
                                                    spacing=8,
                                                    expand=True,
                                                    controls=[
                                                        ft.Container(
                                                            width=46,
                                                            alignment=ft.Alignment(0, 0),
                                                            content=self.icono_registro(registro),
                                                        ),
                                                        ft.Container(
                                                            expand=True,
                                                            content=ft.Text(
                                                                self.titulo_registro(registro),
                                                                size=20,
                                                                weight=ft.FontWeight.BOLD,
                                                                max_lines=1,
                                                                overflow=ft.TextOverflow.ELLIPSIS,
                                                            ),
                                                        ),
                                                    ],
                                                ),
                                                expand=True,
                                            ),
                                        ],
                                    ),


                                    self._acciones_registro_inline(registro)

                                ]

                            ),


                            self._area_click_registro(
                                registro,
                                ft.Column(
                                    spacing=10,
                                    controls=[
                                        self.preview_registro(registro),
                                        self.texto_previsualizacion(
                                            registro,
                                            size=14,
                                            max_lines=4,
                                        ),
                                        ft.Text(
                                            f'Resultado: {self.resultado_registro(registro)}',
                                            size=18,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                    ],
                                ),
                            ),



                            referencia

                        ]

                    )

                )

            )

    # ======================================
    # CREAR TARJETA CUADRADA
    # ======================================                            
    def crear_tarjeta_cuadrada(self, registro):
        seleccionada = self.esta_seleccionado(registro)

        return ft.Container(
            height=224 if self.es_movil() else 242,
            padding=12,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            bgcolor=PERLA_PURPURA if seleccionada else SUPERFICIE_PERLADA,
            border=ft.Border.all(
                1,
                PURPURA_IOS if seleccionada else PERLA_BORDE,
            ),
            border_radius=8,
            shadow=sombra_suave(0.05, 14, 0, 4),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Checkbox(
                                visible=self.modo_seleccion_multiple,
                                value=seleccionada,
                                on_change=lambda e, r=registro: self.toggle_seleccion_multiple(r),
                            ),
                            self.icono_registro(registro),
                            ft.Text(
                                self.etiqueta_tipo_registro(registro),
                                expand=True,
                                size=12,
                                color=TEXTO_SECUNDARIO,
                                weight=ft.FontWeight.BOLD,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                    ),
                    self._area_click_registro(
                        registro,
                        self._vista_previa_cuadricula(registro),
                    ),
                    self._area_click_registro(
                        registro,
                        ft.Column(
                            tight=True,
                            spacing=3,
                            controls=[
                                ft.Text(
                                    self.titulo_registro(registro),
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Text(
                                    self.fecha_corta_registro(registro),
                                    size=11,
                                    color=TEXTO_SECUNDARIO,
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )
    # ======================================
    # CREAR CUADRICULA
    # ======================================
    def crear_cuadricula(self, registros):
        ancho_tarjeta = 172 if self.es_movil() else 248
        return ft.Row(
            wrap=True,
            spacing=10,
            run_spacing=10,
            controls=[
                ft.Container(
                    width=ancho_tarjeta,
                    content=self.crear_tarjeta_cuadrada(registro),
                )
                for registro in registros
            ]
        )

    # ======================================
    # f() CREAR LISTA
    # ======================================
    def crear_lista(self, registros):
        return ft.Column(
            tight=True,
            spacing=10,
            controls=[
                ft.Container(
                    padding=ft.Padding(left=12, top=11, right=10, bottom=11),
                    border_radius=14,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    bgcolor=(PERLA_PURPURA if self.esta_seleccionado(registro) else SUPERFICIE_PERLADA),
                    border=ft.Border.all(
                        1,
                        PURPURA_IOS if self.esta_seleccionado(registro) else PERLA_BORDE,
                    ),
                    content=ft.Row(
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Checkbox(
                                visible=self.modo_seleccion_multiple,
                                value=self.esta_seleccionado(registro),
                                on_change=lambda e, r=registro: self.toggle_seleccion_multiple(r),
                            ),
                            self._area_click_registro(
                                registro,
                                ft.Row(
                                    spacing=12,
                                    expand=True,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Container(
                                            width=46,
                                            height=46,
                                            alignment=ft.Alignment(0, 0),
                                            border_radius=12,
                                            bgcolor=ft.Colors.with_opacity(0.05, PURPURA_IOS),
                                            content=self.icono_registro(registro),
                                        ),
                                        ft.Container(
                                            expand=True,
                                            content=ft.Column(
                                                tight=True,
                                                spacing=3,
                                                controls=[
                                                    ft.Text(
                                                        self.titulo_registro(registro),
                                                        weight=ft.FontWeight.BOLD,
                                                        size=15,
                                                        max_lines=1,
                                                        overflow=ft.TextOverflow.ELLIPSIS,
                                                    ),
                                                    self.texto_previsualizacion(
                                                        registro,
                                                        size=12,
                                                        max_lines=1,
                                                        color=TEXTO_SECUNDARIO,
                                                    ),
                                                    ft.Text(
                                                        self.etiqueta_tipo_registro(registro),
                                                        size=11,
                                                        color=TEXTO_SECUNDARIO,
                                                        max_lines=1,
                                                        overflow=ft.TextOverflow.ELLIPSIS,
                                                    ),
                                                ],
                                            ),
                                        ),
                                    ],
                                ),
                                expand=True,
                            ),
                        ],
                    ),
                )
                for registro in registros
            ],
        )
                 
    # -------------------------------------------------
    # CAMBIAR VISTA
    # -------------------------------------------------
    def cambiar_vista(self, e):
        self.modo_cuadricula = not self.modo_cuadricula

        if self.modo_cuadricula:
            self.boton_vista.icon = ft.Icons.VIEW_LIST
            self.boton_vista.tooltip = "Ver como lista"
        else:
            self.boton_vista.icon = ft.Icons.GRID_VIEW
            self.boton_vista.tooltip = "Ver como cuadrícula"

        self.actualizar_tabla()
        self._refrescar_pagina()

    # =================================================
    # F() ACTUALIZAR TABLA
    # =================================================
    def actualizar_tabla(self, registros=None):
        
        self.panel_contenido.controls.clear()
        self._actualizar_barra_acciones()
        busqueda_activa = bool(str(getattr(self.campo_busqueda, "value", "") or "").strip())
        es_inicio = self._esta_en_inicio_guardados()

        if hasattr(self, "acciones_explorador"):
            self.acciones_explorador.visible = not es_inicio
        if hasattr(self, "herramientas_guardados"):
            self.herramientas_guardados.padding = 0
        self.barra_ruta.visible = not es_inicio
        self.boton_limpiar_busqueda.visible = busqueda_activa
        self.campo_busqueda.hint_text = (
            "Buscar carpetas" if es_inicio else f"Buscar en {self.carpeta_actual_nombre or 'carpeta'}"
        )

        # El nivel general es un tablero de carpetas: no mezcla archivos ni
        # cronologÃ­as. El buscador de este nivel filtra exclusivamente carpetas.
        if es_inicio:
            texto_busqueda = str(getattr(self.campo_busqueda, "value", "") or "").strip().lower()
            carpetas = self.carpetas.obtener_hijos(None)
            if texto_busqueda:
                carpetas = [
                    carpeta for carpeta in carpetas
                    if texto_busqueda in str(carpeta.get("nombre", "")).lower()
                ]
            self.panel_contenido.controls.append(
                self._seccion_carpetas_principales(carpetas)
            )
            self.panel_contenido.controls.append(self._zona_vacia_deseleccion())
            return
        
        if registros is None:        
            if self.carpeta_actual_nombre is None:
                registros = []
            else:
                registros = [
                    r
                    for r in self.guardados.obtener()
                    if (
                        r.get("carpeta_id") == self.carpeta_actual_id
                        or (
                            r.get("carpeta_id") is None
                            and r.get("carpeta") == self.carpeta_actual_nombre
                        )
                    )
                ]

        registros = self._aplicar_filtro_tipo(registros)
        registros = self._ordenar_registros(registros)
        subcarpetas = [] if busqueda_activa else self._subcarpetas_actuales()
        if subcarpetas:
            self.panel_contenido.controls.append(
                self._seccion_subcarpetas(subcarpetas)
            )

        if len(registros) == 0 and not subcarpetas and not es_inicio:
            self.panel_contenido.controls.append(
                ft.Container(
                    height= 400,
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True,
                        controls=[
                            ft.Icon(
                                ft.Icons.SEARCH_OFF,
                                size=70,
                                color=ft.Colors.GREY_500,
                            ),
                            ft.Text(
                                "No se encontraron registros",
                                size=20,
                                color=ft.Colors.GREY_700,
                            )


                        ]
                    )
                )
            )
            self.panel_contenido.controls.append(self._zona_vacia_deseleccion())
            return

        if not registros:
            self.panel_contenido.controls.append(self._zona_vacia_deseleccion())
            return

        if self.modo_cuadricula:
            self.panel_contenido.controls.append(
                self.crear_cuadricula(registros)
            )

        else:
            self.panel_contenido.controls.append(
                self.crear_lista(registros)
            )

        self.panel_contenido.controls.append(self._zona_vacia_deseleccion())
        
                    
    # -------------------------------------------------
    # CAMBIAR REFERENCIA
    # -------------------------------------------------
    def cambiar_referencia(self, id_registro, texto):
        self.guardados.actualizar_referencia( id_registro, texto)
    
    # -------------------------------------------------
    # FILTRAR
    # -------------------------------------------------
    def filtrar(self, e):
        texto = str(self.busqueda.value).lower()

        resultados = []
        for registro in self.guardados.obtener():
            if (
                texto in self.titulo_registro(registro).lower()
                or
                texto in self.subtitulo_registro(registro).lower()
            ):
                resultados.append(registro)
        self.actualizar_tabla(
            resultados
        )
        self.page.update()
    
    # -------------------------------------------------
    # CONFIRMAR ELIMINAR
    # -------------------------------------------------
    def confirmar_eliminar(self, id_registro):
        self.confirmar_eliminar_varios([id_registro])
        return

    def confirmar_eliminar_varios(self, ids_registros):
        ids_registros = [
            id_registro
            for id_registro in ids_registros
            if id_registro is not None
        ]

        if not ids_registros:
            return

        def cerrar(e=None):
            dialog.open = False
            self.page.update()

            def eliminar_dialogo():
                if dialog in self.page.overlay:
                    self.page.overlay.remove(dialog)

            ejecutar_demorado(self.page, 0.1, eliminar_dialogo)

        def aceptar(e):
            for id_registro in ids_registros:
                self.guardados.eliminar(id_registro)

            self.ids_seleccionados.difference_update(ids_registros)
            self.tarjeta_seleccionada = None
            self._actualizar_barra_acciones()
            cerrar()
            self.actualizar_tabla()
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(
                    "Registro eliminado"
                    if len(ids_registros) == 1
                    else "Registros eliminados"
                )
            )

            self.page.snack_bar.open = True
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Eliminar registro" if len(ids_registros) == 1 else "Eliminar registros"),
            content=ft.Text(
                "¿Seguro que desea eliminar este registro?"
            ),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=cerrar
                ),
                ft.ElevatedButton(
                    "Eliminar",
                    on_click=aceptar
                )
            ]
        )
        dialog.content = ft.Text(
            "Seguro que desea eliminar este registro?"
            if len(ids_registros) == 1
            else f"Seguro que desea eliminar {len(ids_registros)} registros?"
        )

        if dialog not in self.page.overlay:
            self.page.overlay.append(dialog)

        dialog.open = True
        self.page.update()

    # -------------------------------------------------
    # ELIMINAR TODOS
    # -------------------------------------------------
    def eliminar_todos(self, e):
        def cerrar(ev=None):
            dialog.open = False
            self.page.update()
            def eliminar_dialogo():
                if dialog in self.page.overlay:
                    self.page.overlay.remove(dialog)

            ejecutar_demorado(self.page, 0.1, eliminar_dialogo)

        def aceptar(ev):
            self.guardados.lista = [
                registro
                for registro in self.guardados.lista
                if registro.get("carpeta", "TARJETAS") != self.carpeta_actual_nombre
            ]
            self.guardados.guardar_archivo()

            cerrar()

            self.actualizar_tabla()

            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(
                    "Todos los registros fueron eliminados."
                )
            )
            self.page.snack_bar.open = True
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Eliminar todos los registros"),
            content=ft.Column(
                tight=True,
                controls=[
                    ft.Text(
                        "Esta acción eliminará TODOS los registros guardados."
                    ),
                    ft.Text(
                        "No podrán recuperarse.",
                        color=ft.Colors.RED,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "¿Desea continuar?"
                    ),
                ],
            ),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=cerrar,
                ),
                ft.ElevatedButton(
                    "Eliminar todo",
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.RED,
                    on_click=aceptar,
                ),
            ],
        )

        if dialog not in self.page.overlay:
            self.page.overlay.append(dialog)

        dialog.open = True
        self.page.update()
    
    # -------------------------------------------------
    # ACCION DE TARJETA
    # -------------------------------------------------
    def ver_detalle_seleccionado(self, e):

        seleccionados = self.registros_seleccionados()

        if len(seleccionados) != 1:
            return
        registro = seleccionados[0]
        self.abrir_detalle(registro)

    def editar_seleccionado(self, e=None):
        seleccionados = self.registros_seleccionados()

        if len(seleccionados) != 1:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Seleccione un solo documento para editar.")
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        self.editar_registro(seleccionados[0])

    def editar_registro(self, registro):
        nombre = ft.TextField(
            label="Nombre",
            value=self.titulo_registro(registro),
            autofocus=True,
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
        )
        referencia = ft.TextField(
            label="Referencia",
            value=registro.get("referencia", ""),
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
        )

        def cerrar(e=None):
            dialog.open = False
            self.page.update()

        def guardar(e=None):
            ocultar_teclado(self.page, nombre)
            ocultar_teclado(self.page, referencia)
            nuevo_nombre = (nombre.value or "").strip()
            nueva_referencia = (referencia.value or "").strip()

            for item in self.guardados.obtener():
                if item.get("id") == registro.get("id"):
                    item["nombre"] = nuevo_nombre
                    item["referencia"] = nueva_referencia
                    break

            self.guardados.guardar_archivo()
            state.notify("update")
            cerrar()
            self.actualizar_tabla()
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Documento actualizado.")
            )
            self.page.snack_bar.open = True
            self.page.update()

        nombre.on_submit = guardar
        referencia.on_submit = guardar

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar documento"),
            content=ft.Container(
                width=420,
                content=ft.Column(
                    tight=True,
                    spacing=10,
                    controls=[
                        nombre,
                        referencia,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar),
                ft.ElevatedButton("Guardar", icon=ft.Icons.SAVE, on_click=guardar),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    # ======================================
    # COPIAR SELECCIONADO
    # ======================================
    def copiar_seleccionado(self, e):

        seleccionados = self.registros_seleccionados()

        if not seleccionados:
            self._aviso_guardados("Seleccione un archivo para compartir.")
            return
        texto = "\n\n---\n\n".join(
            self.texto_registro(registro)
            for registro in seleccionados
        )
        copiar_al_portapapeles(self.page, texto)
        self.boton_copiar.icon = ft.Icons.CHECK
        self.boton_copiar.tooltip = "Copiado"

        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("Copiado correctamente"),
            duration=1500,
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=ft.Margin(left=18, top=0, right=18, bottom=72),
            show_close_icon=True,
        )
        self.page.snack_bar.open = True
        def restaurar():
            self.boton_copiar.icon = ft.Icons.CONTENT_COPY
            self.boton_copiar.tooltip = "Copiar"
            self.page.update()
        ejecutar_demorado(self.page, 1.5, restaurar)

        self.page.update()

    def compartir_seleccionado(self, e):
        seleccionados = self.registros_seleccionados()

        if not seleccionados:
            self._aviso_guardados("Seleccione un archivo para compartir.")
            return

        if len(seleccionados) == 1 and seleccionados[0].get("subtipo") == "tarjeta_colores":
            compartir_texto(
                self.page,
                self.texto_registro(seleccionados[0]),
                self.titulo_registro(seleccionados[0]),
            )
            return

        if len(seleccionados) == 1 and seleccionados[0].get("subtipo") == "tarjeta_versiculo":
            self.descargar_tarjeta_versiculo(seleccionados[0])
            return

        if len(seleccionados) == 1:
            imagen = self.archivo_imagen_registro(seleccionados[0])

            if imagen:
                compartir_archivo(
                    self.page,
                    imagen["archivo"],
                    self.titulo_registro(seleccionados[0]),
                    imagen["mime"],
                )
                return

        texto = "\n\n---\n\n".join(
            self.texto_registro(registro)
            for registro in seleccionados
        )

        titulo = (
            self.titulo_registro(seleccionados[0])
            if len(seleccionados) == 1
            else "Elementos guardados"
        )

        compartir_texto(
            self.page,
            texto,
            titulo,
        )

    def _obtener_file_picker_tarjeta(self):
        if self.file_picker_tarjeta is not None:
            return self.file_picker_tarjeta

        self.file_picker_tarjeta = ft.FilePicker()

        try:
            self.page.services.append(self.file_picker_tarjeta)
            self.page.update()
        except Exception:
            try:
                self.page.overlay.append(self.file_picker_tarjeta)
                self.page.update()
            except Exception:
                pass

        return self.file_picker_tarjeta

    def _nombre_archivo_tarjeta_jpg(self, referencia):
        limpio = "".join(
            caracter if caracter.isalnum() else "_"
            for caracter in str(referencia or "tarjeta")
        ).strip("_")
        return f"tarjeta_{limpio or 'versiculo'}_{int(time.time() * 1000)}.jpg"

    def _cerrar_flotante_guardados(self, control):
        if control is None:
            return

        try:
            control.open = False
        except Exception:
            pass

        try:
            if hasattr(self.page, "close"):
                self.page.close(control)
        except Exception:
            pass

        try:
            while control in self.page.overlay:
                self.page.overlay.remove(control)
        except Exception:
            pass

        try:
            self.page.update()
        except Exception:
            pass

    def _crear_flotante_guardados(self, titulo, contenido, acciones, ancho=460, alto=360):
        ancho_page = getattr(self.page, "width", None) or 760
        alto_page = getattr(self.page, "height", None) or 720
        return ft.Container(
            width=ancho_page,
            height=alto_page,
            bgcolor=ft.Colors.with_opacity(0.55, ft.Colors.BLACK),
            alignment=ft.Alignment(0, 0),
            content=ft.Container(
                width=min(ancho, max(300, ancho_page - 32)),
                height=min(alto, max(300, alto_page - 40)),
                padding=ft.Padding(24, 22, 24, 18),
                border_radius=24,
                bgcolor=PERLA_PANEL,
                shadow=sombra_suave(),
                content=ft.Column(
                    spacing=14,
                    controls=[
                        ft.Text(
                            titulo,
                            size=22,
                            weight=ft.FontWeight.W_500,
                            color=TEXTO_PRINCIPAL,
                        ),
                        ft.Container(
                            expand=True,
                            content=contenido,
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.END,
                            spacing=10,
                            controls=acciones,
                        ),
                    ],
                ),
            ),
        )

    def _confirmar_descarga_tarjeta_jpg(self, destino):
        destino = Path(destino)

        def cerrar(e=None):
            self._cerrar_flotante_guardados(dialog)

        def copiar(e=None):
            copiar_al_portapapeles(self.page, str(destino))

        def abrir_carpeta(e=None):
            try:
                if os.name == "nt":
                    os.startfile(str(destino.parent))
                else:
                    self.page.launch_url(destino.parent.as_uri())
            except Exception:
                self._aviso_guardados("No se pudo abrir la carpeta.")

        dialog = self._crear_flotante_guardados(
            "JPG descargado",
            ft.Column(
                spacing=8,
                controls=[
                    ft.Text("La tarjeta se guardo correctamente en:"),
                    ft.Text(str(destino), selectable=True, color=TEXTO_SECUNDARIO),
                ],
            ),
            [
                ft.OutlinedButton(
                    "Abrir carpeta",
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=abrir_carpeta,
                ),
                ft.OutlinedButton(
                    "Copiar ruta",
                    icon=ft.Icons.CONTENT_COPY,
                    on_click=copiar,
                ),
                ft.ElevatedButton("Aceptar", on_click=cerrar),
            ],
            ancho=560,
            alto=300,
        )

        self.page.overlay.append(dialog)
        self.page.update()

    def descargar_tarjeta_versiculo(self, registro):
        archivo = self._preparar_archivo_tarjeta_versiculo(registro)

        if not archivo:
            self._aviso_guardados("No se pudo preparar la tarjeta JPG.")
            return

        if self._es_descarga_tarjeta_escritorio():
            self._mostrar_selector_carpeta_descarga_tarjeta(archivo)
            return

        # En web y móvil el sistema entrega la descarga al navegador.
        if hasattr(self.page, "run_task"):
            self.page.run_task(self._descargar_tarjeta_versiculo_async, registro, str(archivo))
        else:
            self._aviso_guardados("No se pudo iniciar la descarga.")

    def descargar_imagen_registro(self, registro):
        imagen = self.archivo_imagen_registro(registro)

        if not imagen or not imagen.get("archivo"):
            self._aviso_guardados("No se pudo preparar la imagen.")
            return

        archivo = Path(imagen["archivo"])

        if not archivo.exists():
            self._aviso_guardados("No se encontro la imagen para descargar.")
            return

        if self._es_descarga_tarjeta_escritorio():
            self._mostrar_selector_carpeta_descarga_tarjeta(archivo)
            return

        if hasattr(self.page, "run_task"):
            self.page.run_task(self._descargar_tarjeta_versiculo_async, registro, str(archivo))
        else:
            self._aviso_guardados("No se pudo iniciar la descarga.")

    def _preparar_archivo_tarjeta_versiculo(self, registro):
        referencia = registro.get("referencia") or registro.get("nombre") or "Versiculo"
        texto = registro.get("contenido") or registro.get("suma") or ""

        imagen = None

        if texto:
            try:
                imagen = datos_tarjeta_versiculo(
                    referencia,
                    texto,
                    nombre_archivo=self._nombre_archivo_tarjeta_jpg(referencia),
                )
                registro["imagen_archivo"] = imagen["archivo"]
                registro["imagen_mime"] = "image/jpeg"
                registro["imagen_extension"] = "jpg"
            except Exception:
                imagen = None

        if not imagen:
            imagen = self.archivo_imagen_registro(registro)

        if not imagen:
            return None

        archivo = Path(imagen["archivo"])

        if not archivo.exists():
            return None

        if archivo.suffix.lower() in (".jpg", ".jpeg"):
            return archivo

        if not texto:
            return None

        try:
            imagen = datos_tarjeta_versiculo(
                referencia,
                texto,
                nombre_archivo=self._nombre_archivo_tarjeta_jpg(referencia),
            )
            registro["imagen_archivo"] = imagen["archivo"]
            registro["imagen_mime"] = "image/jpeg"
            registro["imagen_extension"] = "jpg"
            archivo = Path(imagen["archivo"])
            return archivo if archivo.exists() else None
        except Exception:
            return None

    async def _descargar_tarjeta_versiculo_async(self, registro, archivo=None):
        archivo = Path(archivo) if archivo else self._preparar_archivo_tarjeta_versiculo(registro)

        if not archivo:
            self._aviso_guardados("No se pudo preparar la tarjeta JPG.")
            return

        try:
            datos = Path(archivo).read_bytes()
        except Exception:
            self._aviso_guardados("No se pudo leer la tarjeta JPG.")
            return

        picker = self._obtener_file_picker_tarjeta()
        destino = None

        try:
            destino = await picker.save_file(
                dialog_title="Guardar tarjeta JPG",
                file_name=Path(archivo).name,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["jpg"],
                src_bytes=datos,
            )
        except Exception as error:
            self._aviso_guardados(f"No se pudo abrir el selector de guardado: {error}")
            return

        if destino:
            self._confirmar_descarga_tarjeta_jpg(destino)
            return

        self._aviso_guardados("La descarga JPG se inició en el dispositivo.")

    def _carpeta_descargas_local(self):
        candidatos = []
        userprofile = os.environ.get("USERPROFILE")

        if userprofile:
            candidatos.extend(
                [
                    Path(userprofile) / "Downloads",
                    Path(userprofile) / "Descargas",
                ]
            )

        candidatos.extend(
            [
                Path.home() / "Downloads",
                Path.home() / "Descargas",
                Path.home(),
            ]
        )

        for carpeta in candidatos:
            try:
                carpeta.mkdir(parents=True, exist_ok=True)
                return carpeta
            except Exception:
                continue

        return Path(ruta_exportacion("")).parent

    def _es_descarga_tarjeta_escritorio(self):
        if bool(getattr(self.page, "web", False)):
            return False

        plataforma = getattr(self.page, "platform", None)
        return plataforma not in (ft.PagePlatform.ANDROID, ft.PagePlatform.IOS)

    def _unidades_locales(self):
        if os.name != "nt":
            return [Path.home().anchor or Path("/")]

        unidades = []

        for letra in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            unidad = Path(f"{letra}:/")

            try:
                if unidad.exists():
                    unidades.append(unidad)
            except OSError:
                pass

        return unidades or [Path.home().anchor or Path("/")]

    def _mostrar_selector_carpeta_descarga_tarjeta(self, archivo):
        archivo = Path(archivo)

        if not archivo.exists():
            self._aviso_guardados("No se encontro la tarjeta JPG para descargar.")
            return

        estado = {"ruta": self._carpeta_descargas_local()}
        ruta_texto = ft.Text(
            str(estado["ruta"]),
            size=12,
            color=TEXTO_SECUNDARIO,
            selectable=True,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        nombre = ft.TextField(
            label="Nombre del archivo",
            value=archivo.name,
            dense=True,
            height=54,
        )
        lista = ft.ListView(expand=True, spacing=4, padding=4)
        subir = ft.IconButton(
            icon=ft.Icons.ARROW_UPWARD,
            tooltip="Subir una carpeta",
        )
        dialog_ref = {"control": None}

        def cerrar(e=None):
            self._cerrar_flotante_guardados(dialog_ref["control"])

        def ir_a(ruta):
            try:
                ruta = Path(ruta)

                if not ruta.exists() or not ruta.is_dir():
                    self._aviso_guardados("No se pudo abrir esa carpeta.")
                    return

                estado["ruta"] = ruta
                renderizar()
            except OSError:
                self._aviso_guardados("No se pudo abrir esa carpeta.")

        def subir_un_nivel(e=None):
            actual = estado["ruta"]
            padre = actual.parent

            if padre != actual:
                ir_a(padre)

        def crear_item_carpeta(carpeta):
            return ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK,
                on_tap=lambda e, ruta=carpeta: ir_a(ruta),
                content=ft.Container(
                    padding=ft.Padding(10, 8, 10, 8),
                    border_radius=9,
                    bgcolor=ft.Colors.with_opacity(0.04, PURPURA_IOS),
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Icon(ft.Icons.FOLDER, color=ft.Colors.AMBER_800),
                            ft.Text(
                                carpeta.name or str(carpeta),
                                expand=True,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, color=TEXTO_SECUNDARIO),
                        ],
                    ),
                ),
            )

        def renderizar():
            actual = estado["ruta"]
            ruta_texto.value = str(actual)
            subir.disabled = actual.parent == actual
            lista.controls.clear()

            try:
                carpetas = sorted(
                    (
                        item
                        for item in actual.iterdir()
                        if item.is_dir() and not item.name.startswith("$")
                    ),
                    key=lambda item: item.name.casefold(),
                )
            except (OSError, PermissionError):
                carpetas = []

            if carpetas:
                lista.controls.extend(crear_item_carpeta(carpeta) for carpeta in carpetas)
            else:
                lista.controls.append(
                    ft.Container(
                        padding=20,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text("No hay carpetas disponibles aquí.", color=TEXTO_SECUNDARIO),
                    )
                )

            for control in (ruta_texto, subir, lista):
                try:
                    control.update()
                except (RuntimeError, AssertionError):
                    pass

        def guardar_aqui(e=None):
            nombre_archivo = Path(str(nombre.value or archivo.name).strip()).name

            if not nombre_archivo:
                self._aviso_guardados("Ingresá un nombre para el archivo.")
                return

            if Path(nombre_archivo).suffix.lower() not in (".jpg", ".jpeg"):
                nombre_archivo = f"{nombre_archivo}.jpg"

            destino = self._guardar_tarjeta_jpg_en_destino(
                archivo,
                estado["ruta"] / nombre_archivo,
            )

            if not destino:
                self._aviso_guardados("No se pudo guardar el JPG en esa carpeta.")
                return

            cerrar()
            self._confirmar_descarga_tarjeta_jpg(destino)

        unidades = [
            ft.OutlinedButton(
                str(unidad),
                icon=ft.Icons.DRIVE_FOLDER_UPLOAD,
                on_click=lambda e, ruta=unidad: ir_a(ruta),
            )
            for unidad in self._unidades_locales()
        ]
        acciones_ruta = ft.Row(
            spacing=4,
            controls=[
                subir,
                ft.OutlinedButton(
                    "Descargas",
                    icon=ft.Icons.DOWNLOAD,
                    on_click=lambda e: ir_a(self._carpeta_descargas_local()),
                ),
                *unidades,
            ],
            scroll=ft.ScrollMode.AUTO,
        )
        contenido = ft.Column(
            expand=True,
            spacing=10,
            controls=[
                ft.Text("Elegí la carpeta donde querés guardar la tarjeta JPG."),
                acciones_ruta,
                ruta_texto,
                ft.Container(
                    expand=True,
                    border=ft.Border.all(1, PERLA_BORDE),
                    border_radius=12,
                    content=lista,
                ),
                nombre,
            ],
        )
        dialog = self._crear_flotante_guardados(
            "Guardar tarjeta JPG",
            contenido,
            [
                ft.TextButton("Cancelar", on_click=cerrar),
                ft.ElevatedButton(
                    "Guardar aquí",
                    icon=ft.Icons.SAVE_ALT,
                    on_click=guardar_aqui,
                ),
            ],
            ancho=720,
            alto=650,
        )
        dialog_ref["control"] = dialog
        self.page.overlay.append(dialog)
        renderizar()
        self.page.update()

    def _guardar_tarjeta_jpg_en_destino(self, archivo, destino):
        archivo = Path(archivo)
        destino = Path(destino)

        if not archivo.exists():
            return None

        if destino.suffix.lower() not in (".jpg", ".jpeg"):
            destino = destino.with_suffix(".jpg")

        try:
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(archivo.read_bytes())
        except Exception:
            return None

        return destino if destino.exists() and destino.stat().st_size > 0 else None
    # ======================================
    # ELIMINAR SELECIONADO
    # ======================================
    def eliminar_seleccionado(self, e):

        seleccionados = self.registros_seleccionados()

        if not seleccionados:
            return

        self.confirmar_eliminar_varios(
            [
                registro.get("id")
                for registro in seleccionados
            ]
        )
    
    # ======================================
    # F() ABRIR DETALLE
    # ======================================
    def abrir_detalle(self, registro):
        if registro.get("subtipo") == "tarjeta_versiculo":
            self._abrir_detalle_tarjeta_versiculo(registro)
            return

        if registro.get("comparacion"):
            mostrar_detalle_comparacion(self.page, registro)
            return

        if registro.get("tipo", "tarjeta") == "tarjeta":
            contenido = registro.get("contenido") or {}
            palabra = registro.get("palabra", "")

            if isinstance(contenido, dict) and contenido.get("tipo") == "biblia_codificada":
                texto_biblia = self.texto_biblia_codificada(registro)
                palabra = (
                    f"{registro.get('referencia', palabra)}\n\n"
                    f"Texto biblico:\n{texto_biblia}"
                )

            mostrar_detalle(
                page=self.page,
                palabra=palabra,
                alfabeto=registro.get("alfabeto", ""),
                suma=registro.get("suma", ""),
                resultado=registro.get("resultado", ""),
            )
            return

        if registro.get("tipo") == "pizarra":
            self.abrir_detalle_pizarra(registro)
            return

        def cerrar(e=None):
            dialog.open = False
            try:
                if hasattr(self.page, "close"):
                    self.page.close(dialog)
            except Exception:
                pass
            try:
                if dialog in self.page.overlay:
                    self.page.overlay.remove(dialog)
            except Exception:
                pass
            self.page.update()

        contenido_dialogo = []
        es_tarjeta_versiculo = registro.get("subtipo") == "tarjeta_versiculo"
        es_tarjeta_colores = registro.get("subtipo") == "tarjeta_colores"

        if es_tarjeta_versiculo:
            contenido_dialogo.append(
                self._control_tarjeta_versiculo_guardada(
                    registro,
                    ancho=560,
                    compacto=False,
                )
            )
            src_imagen = True
        elif es_tarjeta_colores:
            contenido_dialogo.append(self._control_tarjeta_colores_guardada(registro, compacto=False))
            src_imagen = False
        else:
            imagen = self.datos_imagen_registro(registro)
            src_imagen = self.src_imagen_registro(imagen)

        if src_imagen and registro.get("subtipo") != "tarjeta_versiculo":
            contenido_dialogo.append(
                ft.Image(
                    src=src_imagen,
                    fit=ft.BoxFit.CONTAIN,
                    width=560,
                    height=300,
                )
            )

        if not es_tarjeta_versiculo and not es_tarjeta_colores:
            contenido_dialogo.append(
                ft.Text(
                    self.texto_registro(registro),
                    selectable=True,
                )
            )

        acciones = [ft.TextButton("Cerrar", on_click=cerrar)]

        if es_tarjeta_versiculo:
            acciones.append(
                ft.ElevatedButton(
                    "Descargar JPG",
                    icon=ft.Icons.DOWNLOAD,
                    on_click=lambda e: self.descargar_tarjeta_versiculo(registro),
                )
            )
        elif es_tarjeta_colores:
            acciones.extend(
                [
                    ft.OutlinedButton(
                        "Copiar",
                        icon=ft.Icons.CONTENT_COPY,
                        on_click=lambda e: copiar_al_portapapeles(self.page, self.texto_registro(registro)),
                    ),
                    ft.OutlinedButton(
                        "Compartir",
                        icon=ft.Icons.SHARE,
                        on_click=lambda e: self.compartir_registro_directo(registro),
                    ),
                ]
            )
        else:
            acciones.append(
                ft.ElevatedButton(
                    "Compartir",
                    icon=ft.Icons.SHARE,
                    visible=bool(src_imagen),
                    on_click=lambda e: self.compartir_registro_directo(registro),
                )
            )

        dialog = ft.AlertDialog(
            title=ft.Text(self.titulo_registro(registro)),
            content=ft.Container(
                width=600,
                height=360,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    controls=contenido_dialogo,
                ),
            ),
            actions=acciones,
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _abrir_detalle_tarjeta_versiculo(self, registro):
        dialog_ref = {"control": None}

        def cerrar(e=None):
            self._cerrar_flotante_guardados(dialog_ref["control"])

        def descargar(e=None):
            self.descargar_tarjeta_versiculo(registro)

        contenido = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            controls=[
                self._control_tarjeta_versiculo_guardada(
                    registro,
                    ancho=560,
                    compacto=False,
                )
            ],
        )

        dialog = self._crear_flotante_guardados(
            self.titulo_registro(registro),
            contenido,
            [
                ft.TextButton("Cerrar", on_click=cerrar),
                ft.ElevatedButton("Descargar JPG", icon=ft.Icons.DOWNLOAD, on_click=descargar),
            ],
            ancho=680,
            alto=540,
        )
        dialog_ref["control"] = dialog
        self.page.overlay.append(dialog)
        self.page.update()

    def abrir_detalle_pizarra(self, registro):
        def cerrar(e=None):
            dialog.open = False
            self.page.update()

        contenido = []

        imagen = self.imagen_pizarra_base64(registro)

        if imagen:
            contenido.append(
                ft.Image(
                    src=base64.b64decode(imagen),
                    fit=ft.BoxFit.CONTAIN,
                    width=760,
                    height=420,
                )
            )
        else:
            contenido.append(
                ft.Container(
                    width=760,
                    height=420,
                    content=self.preview_registro(registro),
                )
            )

        contenido.append(
            ft.Text(
                self.texto_registro(registro),
                selectable=True,
            )
        )

        dialog = ft.AlertDialog(
            title=ft.Text(self.titulo_registro(registro)),
            content=ft.Container(
                width=780,
                height=500,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    controls=contenido,
                ),
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=cerrar),
                ft.ElevatedButton(
                    "Compartir",
                    icon=ft.Icons.SHARE,
                    on_click=lambda e: self.compartir_registro_directo(registro),
                ),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def compartir_registro_directo(self, registro):
        if registro.get("subtipo") == "tarjeta_colores":
            compartir_texto(
                self.page,
                self.texto_registro(registro),
                self.titulo_registro(registro),
            )
            return

        if registro.get("subtipo") == "tarjeta_versiculo":
            self.descargar_tarjeta_versiculo(registro)
            return

        imagen = self.archivo_imagen_registro(registro)

        if imagen:
            compartir_archivo(
                self.page,
                imagen["archivo"],
                self.titulo_registro(registro),
                imagen["mime"],
            )
            return

        compartir_texto(
            self.page,
            self.texto_registro(registro),
            self.titulo_registro(registro),
        )
    # ======================================
    # SELECCION TARJETA
    # ======================================
    def seleccionar_tarjeta(self, registro):
        self.tarjeta_seleccionada = registro
        self.ids_seleccionados = {registro.get("id")}
        self._actualizar_barra_acciones()

        self.actualizar_tabla()
        self.page.update()
 
    # ======================================
    # RENOMBRAR CARPETA
    # ======================================
    def renombrar_carpeta(self,e):

        if self.carpeta_seleccionada_id is None:
            return

        carpeta = self.carpetas.obtener_por_id(
            self.carpeta_seleccionada_id
        )

        if carpeta is None:
            return

        campo = ft.TextField(
            label="Nuevo nombre",
            value=carpeta["nombre"],
            autofocus=True,
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
        )

        def cerrar(e=None):
            dialog.open = False
            self.page.update()

        def aceptar(e):
            ocultar_teclado(self.page, campo)

            nuevo_nombre = campo.value.strip()

            if nuevo_nombre:

                cambiado = self.carpetas.renombrar(
                    self.carpeta_seleccionada_id,
                    nuevo_nombre
                )

                if cambiado:

                    self.carpeta_actual_nombre = nuevo_nombre

                    self.cargar_vista_carpetas()
                    self.actualizar_tabla()

            cerrar()

        campo.on_submit = aceptar

        dialog = ft.AlertDialog(
            title=ft.Text("Renombrar carpeta"),
            content=campo,
            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=cerrar
                ),

                ft.ElevatedButton(
                    "Guardar",
                    on_click=aceptar
                )
            ]
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def eliminar_carpeta(self, e):
        if self.carpeta_seleccionada_id is None:
            return

        eliminado = self.carpetas.eliminar(
            self.carpeta_seleccionada_id
        )

        if eliminado:

            self.carpeta_seleccionada_id = 1
            self.carpeta_seleccionada_nombre = "TARJETAS"

            self.carpeta_actual_nombre = "TARJETAS"
            self.carpeta_actual_id = 1
            self.ruta_carpetas = [{"id": 1, "nombre": "TARJETAS"}]

            self.cargar_vista_carpetas()

            self.actualizar_barra_ruta()
            self.actualizar_tabla()

            self.page.update()

    # ======================================
    # DESELECCIONAR CARPETA
    # ======================================
    def deseleccionar_carpeta(self, e):

        self.carpeta_seleccionada_id = None
        self.carpeta_seleccionada_nombre = None

        self.ruta_carpetas = []

        self.boton_renombrar.disabled = True
        self.boton_eliminar.disabled = True

        self.actualizar_barra_ruta()
        self.actualizar_tabla()
        self.cargar_vista_carpetas()

        self.page.update()
    # ======================================
    # BUSCAR REGISTROS
    # ======================================
    def buscar_registros(self, e):
        texto = str(self.campo_busqueda.value).lower().strip()

        if texto == "":
            self.actualizar_tabla()
            return

        registros_base = [
            r
            for r in self.guardados.obtener()
            if (
                r.get("carpeta_id") == self.carpeta_actual_id
                or (
                    r.get("carpeta_id") is None
                    and r.get("carpeta") == self.carpeta_actual_nombre
                )
            )
        ]

        registros = [
            r
            for r in registros_base
            if (
                texto in self.titulo_registro(r).lower()
                or
                texto in self.subtitulo_registro(r).lower()
                or
                texto in self.resultado_registro(r).lower()
                or
                texto in self.texto_registro(r).lower()
            )
        ]

        self.actualizar_tabla(registros)
    # =========================================
    # F() OBTENER POR NOMBRE
    # =========================================
    def obtener_por_nombre(self, nombre):
        for carpeta in self.obtener():
            if carpeta["nombre"] == nombre:
                return carpeta
        return None
    
    # ======================================
    # MOVER SELECCIONADO
    # ======================================
    def mover_seleccionado(self, e):

        seleccionados = self.registros_seleccionados()

        if not seleccionados:
            return

        destino = {"carpeta": None}
        expandidas = {
            carpeta["id"]
            for carpeta in self.carpetas.obtener()
            if carpeta.get("padre") is None
        }
        destino_texto = ft.Text(
            "Seleccione una carpeta destino.",
            size=12,
            color=ft.Colors.GREY_700,
        )
        arbol = ft.ListView(
            height=330,
            spacing=2,
            auto_scroll=False,
        )

        def cancelar(ev):
            dialog.open = False
            self.page.update()

        def actualizar_destino():
            carpeta = destino["carpeta"]

            if carpeta:
                destino_texto.value = (
                    "Destino: "
                    + self.carpetas.obtener_ruta_texto(carpeta["id"])
                )
            else:
                destino_texto.value = "Seleccione una carpeta destino."

        def seleccionar(carpeta):
            destino["carpeta"] = carpeta
            renderizar_arbol()

        def alternar(carpeta):
            if carpeta["id"] in expandidas:
                expandidas.remove(carpeta["id"])
            else:
                expandidas.add(carpeta["id"])
            renderizar_arbol()

        def item_carpeta(carpeta, nivel):
            hijos = self.carpetas.obtener_hijos(carpeta["id"])
            seleccionada = (
                destino["carpeta"]
                and destino["carpeta"]["id"] == carpeta["id"]
            )

            return ft.Container(
                padding=ft.Padding(left=4 + nivel * 18, top=2, right=4, bottom=2),
                bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.DEEP_PURPLE)
                if seleccionada
                else None,
                border_radius=6,
                content=ft.Row(
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.IconButton(
                            icon=(
                                ft.Icons.EXPAND_MORE
                                if carpeta["id"] in expandidas
                                else ft.Icons.CHEVRON_RIGHT
                            )
                            if hijos
                            else ft.Icons.FOLDER_OUTLINED,
                            icon_size=18,
                            width=32,
                            height=32,
                            on_click=(
                                lambda e, c=carpeta: alternar(c)
                                if hijos
                                else seleccionar(c)
                            ),
                        ),
                        ft.GestureDetector(
                            expand=True,
                            on_tap=lambda e, c=carpeta: seleccionar(c),
                            on_double_tap=lambda e, c=carpeta: (
                                seleccionar(c),
                                aceptar(e),
                            ),
                            content=ft.Container(
                                height=34,
                                alignment=ft.Alignment(-1, 0),
                                content=ft.Text(
                                    carpeta["nombre"],
                                    weight=(
                                        ft.FontWeight.BOLD
                                        if seleccionada
                                        else ft.FontWeight.NORMAL
                                    ),
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ),
                        ),
                    ],
                ),
            )

        def agregar_rama(carpeta, nivel):
            arbol.controls.append(item_carpeta(carpeta, nivel))

            if carpeta["id"] not in expandidas:
                return

            for hija in self.carpetas.obtener_hijos(carpeta["id"]):
                agregar_rama(hija, nivel + 1)

        def renderizar_arbol():
            arbol.controls.clear()

            for carpeta in self.carpetas.obtener_hijos(None):
                agregar_rama(carpeta, 0)

            actualizar_destino()

            try:
                arbol.update()
                destino_texto.update()
            except (RuntimeError, AssertionError):
                pass

        def aceptar(ev):

            if destino["carpeta"]:

                for registro in seleccionados:
                    self.guardados.mover_registro_a_carpeta(
                        registro["id"],
                        destino["carpeta"],
                    )

                dialog.open = False

                self.ids_seleccionados.clear()
                self.tarjeta_seleccionada = None
                self._actualizar_barra_acciones()
                self.actualizar_tabla()

                self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text(
                "Mover registro"
                if len(seleccionados) == 1
                else "Mover registros"
            ),
            content=ft.Container(
                width=420,
                content=ft.Column(
                    tight=True,
                    spacing=10,
                    controls=[
                        destino_texto,
                        ft.Container(
                            border=ft.Border.all(1, ft.Colors.GREY_300),
                            border_radius=8,
                            padding=6,
                            content=arbol,
                        ),
                    ],
                ),
            ),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=cancelar,
                ),
                ft.ElevatedButton(
                    "Mover",
                    on_click=aceptar,
                ),
            ],
        )

        self.page.overlay.append(dialog)
        renderizar_arbol()

        dialog.open = True

        self.page.update()

    def _on_state_change(self, event=None):
        # Esta vista queda registrada aunque el usuario esté en otra página.
        # No se deben actualizar controles desmontados desde ese aviso global.
        if event == "update" and getattr(self.router, "ruta_actual", None) == "guardados":
            self.actualizar_tabla()
            self.cargar_vista_carpetas()
            self._refrescar_pagina()

    def _refrescar_pagina(self):
        """Actualiza solo cuando la vista ya fue montada por Flet."""
        try:
            self.page.update()
        except (RuntimeError, AssertionError):
            pass

    def obtener_carpeta_actual(self):

        if self.carpeta_actual_nombre is None:
            return {"id": 1, "nombre": "TARJETAS"}

        return {
            "id": self.carpeta_actual_id,
            "nombre": self.carpeta_actual_nombre
        }
    
    def es_movil(self):
        return self.ancho_actual() < 700

    def es_tablet(self):
        return 700 <= self.ancho_actual() < 1100

    def es_pc(self):
        return self.ancho_actual() >= 1100

    def ancho_actual(self):
        ancho = getattr(self.page, "width", None)

        if ancho is None and hasattr(self.page, "window"):
            ancho = getattr(self.page.window, "width", None)

        return ancho or 1200
    
    def abrir_menu(self):

        self.page.drawer = self.drawer

        self.drawer.open = True

        self.page.update()

    def ancho_panel_izquierdo(self):

        if self.es_pc():
            return 320

        if self.es_tablet():
            return 250

        return 0
