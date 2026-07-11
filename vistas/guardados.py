import flet as ft
import base64
import json
import time
import threading
import math
from pathlib import Path
from vistas.detalle import mostrar_detalle
from core.app_state import state
from services.mantenimiento_service import MantenimientoService

from logica.exportar_excel import exportar_guardados_xlsx
from logica.pizarra_imagen import renderizar_lienzo_exportable_base64
from ui.clipboard import copiar_al_portapapeles
from ui.compartir import compartir_archivo, compartir_imagen_base64, compartir_texto
from ui.tema import (
    PERLA_BORDE,
    PERLA_PANEL,
    PERLA_VIOLETA,
    SUPERFICIE_PERLADA,
    TEXTO_PRINCIPAL,
    TEXTO_SECUNDARIO,
    VIOLETA_IOS,
    sombra_suave,
)
from ui.teclado import ocultar_teclado
from services.guardados_service import GuardadosService
from services.estadisticas_service import EstadisticasService
from services.exportacion_service import ExportacionService
from services.busqueda_global_service import BusquedaGlobalService

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
        self.modo_cuadricula = False
        self.modo_seleccion_multiple = False
        self.file_picker_excel = None
        
        self.carpeta_actual_id = 1
        self.carpeta_actual_nombre = "TARJETAS"
        self.carpeta_seleccionada_id = 1
        self.carpeta_seleccionada_nombre = "TARJETAS"
        
        self.ruta_carpetas = [{"id":1,"nombre": "TARJETAS"}]
        
        self.carpetas_expandidas = set()
        self.carpetas_colapsadas = True
        self.modo_vista = 'tarjetas'
        self.filtro_tipo = 'Todos'
        self.orden_guardados = 'Antiguos'
        self.boton_vista = ft.IconButton(
            icon=ft.Icons.GRID_VIEW,
            tooltip='cambiar vista',
            on_click=self.cambiar_vista
        )
        self.campo_busqueda = ft.TextField(
            hint_text="Buscar...",
            prefix_icon=ft.Icons.SEARCH,
            dense=True,
            width=280,
            on_change=self.buscar_registros,
            on_submit=lambda e: ocultar_teclado(self.page, e.control),
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
        )
        self.boton_limpiar_busqueda = ft.IconButton(
            icon=ft.Icons.CLOSE,
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
            tooltip='Cambiar vista',
            on_click=self.cambiar_vista
        )
        self.boton_seleccion_multiple = ft.IconButton(
            icon=ft.Icons.SELECT_ALL,
            tooltip="Seleccion multiple",
            on_click=self.toggle_modo_seleccion_multiple,
        )
        self.boton_exportar_excel = ft.IconButton(
            icon=ft.Icons.TABLE_CHART,
            tooltip="Exportar Excel",
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
            spacing=0,
            controls=[
                self.boton_nueva,
                ft.VerticalDivider(width=1),
                self.boton_renombrar,
                ft.VerticalDivider(width=1),
                self.boton_eliminar,
                ft.VerticalDivider(width=1),
                self.boton_vista,
                ft.VerticalDivider(width=1),
                self.boton_seleccion_multiple,
            ]
        )
        self.barra_filtros_tipo = self._crear_barra_filtros_tipo()
        self.barra_orden_guardados = self._crear_barra_orden_guardados()
        self.barra_ruta = ft.Row(
            spacing=5,
            scroll=ft.ScrollMode.AUTO
        ) 
        self.panel_contenido = ft.Column(
            expand=True,
            spacing=10,
            scroll=ft.ScrollMode.AUTO 
        )
        self.panel_izquierdo = ft.Container(
            width=250,
            padding=10,
            bgcolor=SUPERFICIE_PERLADA,
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=18,
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
            color=VIOLETA_IOS,
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
            bgcolor=PERLA_VIOLETA,
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
            padding=15,
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
                estado.color = VIOLETA_IOS
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
        if self.es_movil():
            herramientas = ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        spacing=4,
                        controls=[self.campo_busqueda, self.boton_limpiar_busqueda],
                    ),
                    self.barra_explorador,
                ],
            )
        else:
            herramientas = ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                wrap=True,
                controls=[
                    ft.Row(
                        spacing=4,
                        controls=[self.campo_busqueda, self.boton_limpiar_busqueda],
                    ),
                    self.barra_explorador,
                ],
            )

        return ft.Column(
            expand=True,
            spacing=7,
            controls=[
                herramientas,
                self.barra_ruta,
                self.barra_acciones,
                ft.Divider(height=1),
                self.panel_contenido
            ],
        )

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
            bgcolor=SUPERFICIE_PERLADA if activo else PERLA_VIOLETA,
            border=ft.Border.all(
                1.4 if activo else 1,
                VIOLETA_IOS if activo else PERLA_BORDE,
            ),
            border_radius=20,
            content=ft.Text(
                nombre,
                size=12,
                weight=ft.FontWeight.BOLD if activo else None,
                color=VIOLETA_IOS if activo else TEXTO_SECUNDARIO,
            ),
            on_click=lambda e, n=nombre: self._cambiar_filtro_tipo(n),
        )

    def _refrescar_barra_filtros_tipo(self):
        if not hasattr(self, "barra_filtros_tipo"):
            return
        self.barra_filtros_tipo.controls.clear()
        for nombre in ["Todos", "Codificador", "Biblia", "Pizarra", "Colores", "Tiempo"]:
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
            bgcolor=SUPERFICIE_PERLADA if activo else PERLA_VIOLETA,
            border=ft.Border.all(
                1.2 if activo else 1,
                VIOLETA_IOS if activo else PERLA_BORDE,
            ),
            border_radius=16,
            content=ft.Text(
                nombre,
                size=11,
                weight=ft.FontWeight.BOLD if activo else None,
                color=VIOLETA_IOS if activo else TEXTO_SECUNDARIO,
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

        def cerrar(e=None):
            dialog.open = False
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

            archivo = exportar_guardados_xlsx(registros)
            cerrar()
            self.descargar_excel(archivo)

        dialog = ft.AlertDialog(
            title=ft.Text("Exportar Excel"),
            content=ft.Container(
                width=420,
                height=420,
                content=lista,
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
        if hasattr(self.page, "run_task"):
            self.page.run_task(self._descargar_excel_async, archivo)
            return

        compartir_archivo(
            self.page,
            archivo,
            "Guardados exportados",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    async def _descargar_excel_async(self, archivo):
        ruta = Path(archivo)
        datos = ruta.read_bytes()
        picker = self._obtener_file_picker_excel()

        try:
            destino = await picker.save_file(
                dialog_title="Descargar Excel",
                file_name=ruta.name,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["xlsx"],
                src_bytes=datos,
            )
        except Exception:
            destino = None

        if destino:
            plataforma = getattr(self.page, "platform", None)
            es_movil = plataforma in (ft.PagePlatform.ANDROID, ft.PagePlatform.IOS)

            if not es_movil:
                destino_path = Path(destino)

                if destino_path.suffix.lower() != ".xlsx":
                    destino_path = destino_path.with_suffix(".xlsx")

                try:
                    destino_path.write_bytes(datos)
                    destino = str(destino_path)
                except Exception:
                    destino = None

            if destino:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Excel descargado: {destino}")
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

        return registro.get("palabra") or registro.get("nombre") or "Tarjeta"

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

        return str(registro.get("resultado", ""))

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

        return ft.Icon(
            ft.Icons.DESCRIPTION,
            color=VIOLETA_IOS,
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

    def preview_registro(self, registro):
        contenido = registro.get("contenido") or {}

        if (
            registro.get("tipo", "tarjeta") == "tarjeta"
            and isinstance(contenido, dict)
            and contenido.get("tipo") == "biblia_codificada"
        ):
            return self.preview_biblia_codificada(registro)

        if registro.get("tipo") != "pizarra":
            return ft.Container(height=0)

        objetos = contenido.get("objetos", []) if isinstance(contenido, dict) else []
        imagen = self.imagen_pizarra_base64(registro)

        if imagen:
            return ft.Container(
                height=110,
                bgcolor=ft.Colors.WHITE,
                border=ft.Border.all(1, ft.Colors.BLACK),
                border_radius=4,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Image(
                    src=base64.b64decode(imagen),
                    fit=ft.BoxFit.CONTAIN,
                ),
            )

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
                        color=VIOLETA_IOS,
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
            contenido = registro.get("contenido") or registro.get("suma") or {}

            if isinstance(contenido, str):
                return contenido

            return json.dumps(contenido, ensure_ascii=False, indent=2)

        if tipo == "tiempo":
            return (
                f"{self.titulo_registro(registro)}\n"
                f"{registro.get('suma') or registro.get('referencia', '')}"
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

    def esta_seleccionado(self, registro):
        return registro.get("id") in self.ids_seleccionados

    def toggle_modo_seleccion_multiple(self, e=None):
        self.modo_seleccion_multiple = not self.modo_seleccion_multiple
        self.ids_seleccionados.clear()
        self.tarjeta_seleccionada = None
        self.boton_seleccion_multiple.bgcolor = (
            PERLA_VIOLETA
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
        self.barra_acciones.visible = cantidad > 0
        self.texto_seleccion.value = (
            f"{cantidad} seleccionado"
            if cantidad == 1
            else f"{cantidad} seleccionados"
        ) if cantidad else ""

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

    def _acciones_registro_inline(self, registro, compacto=False):
        ancho = 30 if compacto else 34
        tamano = 16 if compacto else 18

        return ft.Row(
            tight=True,
            spacing=0,
            controls=[
                ft.IconButton(
                    icon=ft.Icons.VISIBILITY,
                    tooltip="Ver",
                    icon_size=tamano,
                    width=ancho,
                    height=ancho,
                    on_click=lambda e, r=registro: self.abrir_detalle(r),
                ),
                ft.IconButton(
                    icon=ft.Icons.EDIT,
                    tooltip="Editar",
                    icon_size=tamano,
                    width=ancho,
                    height=ancho,
                    on_click=lambda e, r=registro: self.editar_registro(r),
                ),
                ft.IconButton(
                    icon=ft.Icons.SHARE,
                    tooltip="Enviar / compartir",
                    icon_size=tamano,
                    width=ancho,
                    height=ancho,
                    on_click=lambda e, r=registro: self.compartir_registro_directo(r),
                ),
                ft.IconButton(
                    icon=ft.Icons.DRIVE_FILE_MOVE,
                    tooltip="Mover",
                    icon_size=tamano,
                    width=ancho,
                    height=ancho,
                    on_click=lambda e, r=registro: self._mover_registro_directo(r),
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    tooltip="Eliminar",
                    icon_size=tamano,
                    width=ancho,
                    height=ancho,
                    on_click=lambda e, r=registro: self.confirmar_eliminar(r["id"]),
                ),
            ],
        )
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
        self._aplicar_responsive()

        if self.es_movil():
            return ft.Column(
                expand=True,
                spacing=0,
                controls=[
                    self.panel_izquierdo,
                    ft.Divider(height=1),
                    self.panel_derecho,
                ],
            )

        return ft.Row(
            expand=True,
            spacing=0,
            controls=[
                self.panel_izquierdo,
                self.panel_derecho,
            ],
        )

    def _aplicar_responsive(self):
        if self.es_movil():
            self.panel_izquierdo.width = None
            self.panel_izquierdo.height = 64 if self.carpetas_colapsadas else 170
            self.panel_izquierdo.padding = 8
            self.panel_izquierdo.content = self.crear_barra_carpetas_movil()
            self.panel_derecho.padding = 10
            self.campo_busqueda.width = None
            self.barra_explorador.spacing = 0
            if hasattr(self, "panel_derecho"):
                self.panel_derecho.content = self._crear_panel_derecho_content()
            return

        if self.es_tablet():
            self.panel_izquierdo.width = 210
            self.panel_izquierdo.height = None
            self.panel_izquierdo.padding = 10
            self.panel_izquierdo.content = self._contenido_panel_carpetas()
            self.panel_derecho.padding = 8
            self.campo_busqueda.width = 240
            if hasattr(self, "panel_derecho"):
                self.panel_derecho.content = self._crear_panel_derecho_content()
            return

        self.panel_izquierdo.width = 250
        self.panel_izquierdo.height = None
        self.panel_izquierdo.padding = 10
        self.panel_izquierdo.content = self._contenido_panel_carpetas()
        self.panel_derecho.padding = 8
        self.campo_busqueda.width = 320
        if hasattr(self, "panel_derecho"):
            self.panel_derecho.content = self._crear_panel_derecho_content()

    def _contenido_panel_carpetas(self):
        return ft.Column(
            expand=True,
            spacing=10,
            controls=[
                ft.Container(
                    padding=ft.Padding(left=12, top=8, right=8, bottom=8),
                    bgcolor=PERLA_VIOLETA,
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
            expand=True,
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
            bgcolor=PERLA_VIOLETA if seleccionada else SUPERFICIE_PERLADA,
            border=ft.Border.all(1.4 if seleccionada else 1, VIOLETA_IOS if seleccionada else PERLA_BORDE),
            border_radius=18,
            shadow=sombra_suave(0.035, 12, 0, 4) if seleccionada else None,
            on_click=lambda e, c=carpeta: self.seleccionar_carpeta_arbol(c),
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.FOLDER, size=18, color=VIOLETA_IOS if seleccionada else "#B97852"),
                    ft.Text(
                        texto,
                        expand=True,
                        size=12,
                        weight=ft.FontWeight.BOLD if seleccionada else None,
                        color=VIOLETA_IOS if seleccionada else TEXTO_SECUNDARIO,
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
            border_radius=18,
            shadow=sombra_suave(0.055, 18, 0, 6),
            content=content,
        )

    def _hero_guardados_visual(self):
        total = len(self.guardados.obtener()) if hasattr(self.guardados, "obtener") else 0
        carpeta = self.carpeta_actual_nombre or "TARJETAS"
        return ft.Container(
            padding=ft.Padding(left=22, top=16, right=22, bottom=16),
            border_radius=20,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=[SUPERFICIE_PERLADA, "#F8F3FB", "#FFF8EE", "#F6ECFF"],
            ),
            border=ft.Border.all(1, PERLA_BORDE),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        tight=True,
                        spacing=4,
                        controls=[
                            ft.Text("Biblioteca personal", size=14, color=TEXTO_SECUNDARIO, weight=ft.FontWeight.BOLD),
                            ft.Text("Guardados", size=30 if not self.es_movil() else 24, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                            ft.Text(f"Carpeta actual: {carpeta}", size=13, color=TEXTO_SECUNDARIO),
                        ],
                    ),
                    ft.Container(
                        visible=not self.es_movil(),
                        padding=ft.Padding(left=16, top=10, right=16, bottom=10),
                        bgcolor=SUPERFICIE_PERLADA,
                        border=ft.Border.all(1, PERLA_BORDE),
                        border_radius=18,
                        content=ft.Column(
                            tight=True,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text(str(total), size=24, weight=ft.FontWeight.BOLD, color=VIOLETA_IOS),
                                ft.Text("registros", size=12, color=TEXTO_SECUNDARIO),
                            ],
                        ),
                    ),
                ],
            ),
        )

    # ======================================
    # OBTENER VISTA
    # ======================================
    def obtener_vista(self):
        self.page.on_resize = self._on_resize

        self.cargar_vista_carpetas()
        self.actualizar_barra_ruta()
        self.actualizar_tabla()

        contenido_guardados = ft.Column(
            expand=True,
            spacing=6,
            controls=[
                self._tarjeta_visual(self.crear_area_trabajo(), padding=0, expand=True),
            ],
        )

        return ft.Container(
            expand=True,
            padding=6 if not self.es_movil() else 4,
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

        fondo = PERLA_VIOLETA if seleccionado else SUPERFICIE_PERLADA
        borde = VIOLETA_IOS if seleccionado else PERLA_BORDE
        texto_color = VIOLETA_IOS if seleccionado else TEXTO_PRINCIPAL
        detalle_color = VIOLETA_IOS if seleccionado else TEXTO_SECUNDARIO

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
                                    color=VIOLETA_IOS if tiene_hijos else PERLA_BORDE,
                                ),
                            ),
                        ),
                        ft.Container(
                            width=34,
                            height=34,
                            border_radius=13,
                            bgcolor=ft.Colors.with_opacity(
                                0.16 if seleccionado else 0.10,
                                VIOLETA_IOS if seleccionado else "#B97852",
                            ),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(
                                ft.Icons.FOLDER_OPEN if abierta else ft.Icons.FOLDER,
                                color=VIOLETA_IOS if seleccionado else "#B97852",
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

        self.panel_izquierdo.update()
        self.panel_derecho.update()
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
        
        bg_color = PERLA_VIOLETA if es_seleccionada else None
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

        self.carpeta_seleccionada_id = carpeta["id"]
        self.carpeta_seleccionada_nombre = carpeta["nombre"]

        self.ruta_carpetas = self.carpetas.obtener_ruta(
            carpeta["id"]
        )

        self.actualizar_barra_ruta()
        self.actualizar_tabla()
        self.cargar_vista_carpetas()

        self.panel_derecho.update()
    # ======================================
    # ACTUALIZAR BARRA DE RUTA
    # ======================================
    def actualizar_barra_ruta(self):
        self.barra_ruta.controls.clear()

        # INICIO
        self.barra_ruta.controls.append(
            ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK,
                on_tap=lambda e: self.volver_inicio(),
                content=ft.Text(
                    "Inicio",
                    color=VIOLETA_IOS,
                    weight=ft.FontWeight.BOLD,
                ),
            )
        )

        # RUTA
        for carpeta in self.ruta_carpetas:
            self.barra_ruta.controls.append(
                ft.Text(">")
            )
            
            self.barra_ruta.controls.append(
                ft.GestureDetector(
                    mouse_cursor=ft.MouseCursor.CLICK,
                    on_tap=lambda e, c=carpeta: self.volver_a_carpeta(c),
                    content=ft.Text(
                        carpeta["nombre"],
                        color=VIOLETA_IOS,
                        weight=ft.FontWeight.BOLD,
                    ),
                )
            )

        self.page.update()
    
    # F(VOLVER INICIO)=======================================
    def volver_inicio(self):

        general = self.carpetas.obtener_por_nombre("TARJETAS")

        self.carpeta_actual_id = None
        self.carpeta_actual_nombre = None

        self.carpeta_seleccionada_id = None
        self.carpeta_seleccionada_nombre = None 

        self.ruta_carpetas = []

        self.actualizar_barra_ruta()
        self.actualizar_tabla()
        self.cargar_vista_carpetas()

        self.panel_izquierdo.update()
        self.panel_derecho.update()
    
    # F(CARGAR A CARPETA)====================================
    def volver_a_carpeta(self, carpeta):
        self.carpeta_actual_id = carpeta["id"]
        self.carpeta_actual_nombre = carpeta["nombre"]

        self.carpeta_seleccionada_id = carpeta["id"]
        self.carpeta_seleccionada_nombre = carpeta["nombre"]

        self.ruta_carpetas = self.carpetas.obtener_ruta(
            carpeta["id"]
        )

        self.actualizar_barra_ruta()
        self.actualizar_tabla()
        self.cargar_vista_carpetas()

        self.panel_izquierdo.update()
        self.panel_derecho.update()
   
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

    def _abrir_subcarpeta(self, carpeta):
        self.seleccionar_carpeta_arbol(carpeta)

    def _tarjeta_subcarpeta(self, carpeta):
        cantidad = self.contar_registros_carpeta(carpeta["nombre"])
        hijos = self.carpetas.obtener_hijos(carpeta["id"])

        return ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            on_tap=lambda e, c=carpeta: self._abrir_subcarpeta(c),
            on_double_tap=lambda e, c=carpeta: self._abrir_subcarpeta(c),
            on_secondary_tap=lambda e, c=carpeta: self.menu_contextual_carpeta(c),
            content=ft.Container(
                width=210,
                padding=ft.Padding(left=12, top=10, right=12, bottom=10),
                bgcolor=SUPERFICIE_PERLADA,
                border=ft.Border.all(1, PERLA_BORDE),
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
                            color=VIOLETA_IOS,
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
                time.sleep(0.1)
                if dialog in self.page.overlay:
                    self.page.overlay.remove(dialog)
            threading.Thread(target=eliminar_dialogo, daemon=True).start()

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
                time.sleep(0.1)
                if dialog in self.page.overlay:
                    self.page.overlay.remove(dialog)
            threading.Thread(target=eliminar_dialogo, daemon=True).start()

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
                time.sleep(0.1)
                if dialog in self.page.overlay:
                    self.page.overlay.remove(dialog)
            threading.Thread(target=eliminar_dialogo, daemon=True).start()

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
                time.sleep(0.1)
                if dialog in self.page.overlay:
                    self.page.overlay.remove(dialog)
            threading.Thread(target=eliminar_dialogo, daemon=True).start()

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
                time.sleep(0.1)
                if dialog in self.page.overlay:
                    self.page.overlay.remove(dialog)
            threading.Thread(target=eliminar_dialogo, daemon=True).start()

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


        return ft.GestureDetector(

            on_tap=lambda e:
                self.tocar_registro(registro),

            on_double_tap=lambda e:
                self.abrir_detalle(registro),

            on_secondary_tap=lambda e:
                self.menu_contextual_registro(registro),


            content=ft.Card(

                elevation=1,

                content=ft.Container(

                    padding=15,

                    bgcolor=(

                        PERLA_VIOLETA
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

                                        controls=[

                                            ft.Checkbox(
                                                visible=self.modo_seleccion_multiple,
                                                value=seleccionada,
                                                on_change=lambda e, r=registro:
                                                    self.toggle_seleccion_multiple(r),
                                            ),

                                            self.icono_registro(registro),


                                            ft.Text(

                                                self.titulo_registro(registro),

                                                size=20,

                                                weight=
                                                ft.FontWeight.BOLD,

                                                max_lines=1,

                                                overflow=
                                                ft.TextOverflow.ELLIPSIS

                                            )

                                        ]

                                    ),


                                    self._acciones_registro_inline(registro)

                                ]

                            ),


                            self.preview_registro(registro),


                            ft.Text(

                                self.subtitulo_registro(registro),

                                size=14

                            ),


                            ft.Text(

                                f'Resultado: {self.resultado_registro(registro)}',

                                size=18,

                                weight=
                                ft.FontWeight.BOLD

                            ),



                            referencia

                        ]

                    )

                )

            )

        )
    # ======================================
    # CREAR TARJETA CUADRADA
    # ======================================                            
    def crear_tarjeta_cuadrada(self, registro):

        seleccionada = self.esta_seleccionado(registro)

        return ft.GestureDetector(

            on_tap=lambda e:
                self.tocar_registro(registro),

            on_double_tap=lambda e:
                self.abrir_detalle(registro),

            on_secondary_tap=lambda e:
                self.menu_contextual_registro(registro),

            content=ft.Card(

                elevation=4,

                content=ft.Container(

                    width=220,
                    height=220,

                    padding=15,

                    bgcolor=(
                        PERLA_VIOLETA
                        if seleccionada
                        else "#FFFFFF"
                    ),

                    border=ft.Border.all(
                        2 if seleccionada else 1,
                        ft.Colors.BLUE
                        if seleccionada
                        else "#E8E0EC"
                    ),

                    border_radius=12,

                    content=ft.Column(

                        spacing=8,

                        controls=[

                            ft.Row(
                                alignment=
                                ft.MainAxisAlignment.SPACE_BETWEEN,

                                controls=[

                                    ft.Checkbox(
                                        visible=self.modo_seleccion_multiple,
                                        value=seleccionada,
                                        on_change=lambda e, r=registro:
                                            self.toggle_seleccion_multiple(r),
                                    ),

                                    self.icono_registro(registro, grande=True),

                                    self._acciones_registro_inline(registro, compacto=True)
                                ]
                            ),

                            ft.Text(
                                self.titulo_registro(registro),

                                size=18,

                                weight=ft.FontWeight.BOLD,

                                max_lines=2,

                                overflow=
                                ft.TextOverflow.ELLIPSIS
                            ),

                            ft.Text(
                                self.subtitulo_registro(registro),

                                size=13
                            ),

                            ft.Text(
                                f'Resultado: {self.resultado_registro(registro)}',

                                size=16,

                                weight=ft.FontWeight.BOLD,

                                max_lines=2,

                                overflow=
                                ft.TextOverflow.ELLIPSIS
                            ),

                            ft.Text(
                                registro.get(
                                    "referencia",
                                    ""
                                ),

                                size=12,

                                color=ft.Colors.GREY_700,

                                max_lines=2,

                                overflow=
                                ft.TextOverflow.ELLIPSIS
                            )

                        ]
                    )
                )
            )
        )
    # ======================================
    # CREAR CUADRICULA
    # ======================================
    def crear_cuadricula(self, registros):
        return ft.GridView(
            expand=True,
            max_extent=240,
            spacing=10,
            run_spacing=10,
            controls=[
                self.crear_tarjeta_cuadrada(registro)
                for registro in registros
            ]
        )

    # ======================================
    # f() CREAR LISTA
    # ======================================
    def crear_lista(self, registros):
        return ft.ListView(
            expand=True,
            spacing=2,

            controls=[
                ft.Container(
                    padding=8,
                    border_radius=6,
                    bgcolor=(
                        PERLA_VIOLETA
                        if (
                            self.esta_seleccionado(registro)
                        )
                        else "#FFFFFF"
                    ),

                    content=ft.GestureDetector(
                        on_tap=lambda e, r=registro:
                            self.tocar_registro(r),
                        on_double_tap=lambda e, r=registro:
                            self.abrir_detalle(r),
                        on_secondary_tap=lambda e, r=registro:
                            self.menu_contextual_registro(r),
                        
                        content=ft.Row(
                            spacing=15,
                            vertical_alignment=
                            ft.CrossAxisAlignment.CENTER,

                            controls=[
                                ft.Checkbox(
                                    visible=self.modo_seleccion_multiple,
                                    value=self.esta_seleccionado(registro),
                                    on_change=lambda e, r=registro:
                                        self.toggle_seleccion_multiple(r),
                                ),
                                self.icono_registro(registro),
                                ft.Container(
                                    expand=True,
                                    content=ft.Column(
                                        spacing=2,
                                        controls=[
                                            ft.Text(
                                                self.titulo_registro(registro),
                                                weight=
                                                ft.FontWeight.BOLD,
                                                size=16,
                                                max_lines=1,
                                                overflow=
                                                ft.TextOverflow.ELLIPSIS
                                            ),

                                            ft.Text(
                                                self.subtitulo_registro(registro),

                                                size=13,

                                                color=
                                                ft.Colors.GREY_700

                                            )
                                        ]
                                    )

                                ),
                                ft.Text(
                                    self.resultado_registro(registro),
                                    size=16,
                                    weight=
                                    ft.FontWeight.BOLD
                                ),
                                self._acciones_registro_inline(registro, compacto=True)
                            ]
                        )
                    )
                )
                for registro in registros
            ]
        )                    
                 
    # -------------------------------------------------
    # CAMBIAR VISTA
    # -------------------------------------------------
    def cambiar_vista(self, e):
        self.modo_cuadricula = not self.modo_cuadricula

        if self.modo_cuadricula:
            self.boton_vista.icon = ft.Icons.VIEW_LIST
        else:
            self.boton_vista.icon = ft.Icons.GRID_VIEW

        self.actualizar_tabla()
        self.page.update()

    # =================================================
    # F() ACTUALIZAR TABLA
    # =================================================
    def actualizar_tabla(self, registros=None):
        
        self.panel_contenido.controls.clear()
        self._actualizar_barra_acciones()
        busqueda_activa = bool(str(getattr(self.campo_busqueda, "value", "") or "").strip())
        
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

        if len(registros) == 0 and not subcarpetas:
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
            return

        if not registros:
            return

        if self.modo_cuadricula:
            self.panel_contenido.controls.append(
                self.crear_cuadricula(registros)
            )

        else:
            self.panel_contenido.controls.append(
                self.crear_lista(registros)
            )
        
                    
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
                time.sleep(0.1)

                if dialog in self.page.overlay:
                    self.page.overlay.remove(dialog)

            threading.Thread(
                target=eliminar_dialogo,
                daemon=True
            ).start()

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
                time.sleep(0.1)
                if dialog in self.page.overlay:
                    self.page.overlay.remove(dialog)

            threading.Thread(
                target=eliminar_dialogo,
                daemon=True,
            ).start()

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
            return
        texto = "\n\n---\n\n".join(
            self.texto_registro(registro)
            for registro in seleccionados
        )
        copiar_al_portapapeles(self.page, texto)
        self.boton_copiar.icon = ft.Icons.CHECK
        self.boton_copiar.tooltip = "Copiado"

        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(
                "Copiado al portapapeles"
                if len(seleccionados) == 1
                else "Elementos copiados al portapapeles"
            )
        )
        self.page.snack_bar.open = True
        def restaurar():
            time.sleep(1.5)

            self.boton_copiar.icon = ft.Icons.CONTENT_COPY
            self.boton_copiar.tooltip = "Copiar"
            self.page.update()
        threading.Thread(
            target=restaurar,
            daemon=True
        ).start()

        self.page.update()

    def compartir_seleccionado(self, e):
        seleccionados = self.registros_seleccionados()

        if not seleccionados:
            return

        datos_imagen = (
            self.datos_imagen_pizarra(seleccionados[0])
            if len(seleccionados) == 1
            and seleccionados[0].get("tipo") == "pizarra"
            else None
        )

        if datos_imagen and datos_imagen.get("base64"):
            compartir_imagen_base64(
                self.page,
                datos_imagen["base64"],
                (
                    f"{self.titulo_registro(seleccionados[0])}."
                    f"{datos_imagen.get('extension', 'jpg')}"
                ),
                self.titulo_registro(seleccionados[0]),
                mime_type=datos_imagen.get("mime", "image/jpeg"),
            )
            return

        compartir_texto(
            self.page,
            "\n\n---\n\n".join(
                self.texto_registro(registro)
                for registro in seleccionados
            ),
            (
                self.titulo_registro(seleccionados[0])
                if len(seleccionados) == 1
                else "Elementos guardados"
            ),
        )

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
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text(self.titulo_registro(registro)),
            content=ft.Container(
                width=600,
                height=360,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        ft.Text(
                            self.texto_registro(registro),
                            selectable=True,
                        )
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=cerrar),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
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
        datos_imagen = (
            self.datos_imagen_pizarra(registro)
            if registro.get("tipo") == "pizarra"
            else None
        )

        if datos_imagen and datos_imagen.get("base64"):
            compartir_imagen_base64(
                self.page,
                datos_imagen["base64"],
                (
                    f"{self.titulo_registro(registro)}."
                    f"{datos_imagen.get('extension', 'jpg')}"
                ),
                self.titulo_registro(registro),
                mime_type=datos_imagen.get("mime", "image/jpeg"),
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

        if event == "update":
            self.actualizar_tabla()
            self.cargar_vista_carpetas()

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
