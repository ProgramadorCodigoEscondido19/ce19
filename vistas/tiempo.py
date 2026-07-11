import asyncio
from datetime import datetime

import flet as ft

from core.app_state import state
from logica.calendario_360 import (
    calcular_calendario_360,
    cargar_base_calendario,
    fecha_extendida_desde_datetime,
    formatear_fecha_real,
    guardar_base_calendario,
    parsear_fecha_consulta,
    texto_calendario_360,
)
from ui.nombre_guardado import pedir_nombre_y_carpeta_guardado
from ui.responsive import Responsive
from ui.tema import (
    BLANCO,
    DORADO,
    PERLA_BORDE,
    PERLA_PANEL,
    PURPURA_INICIAL,
    SUPERFICIE_PERLADA,
    TEXTO_PRINCIPAL,
    TEXTO_SECUNDARIO,
    VIOLETA_IOS,
    panel_moderno,
    sombra_suave,
    swatches_colores,
)
from ui.teclado import ocultar_teclado


class TiempoView:
    def __init__(self, page, router):
        self.page = page
        self.router = router
        self.responsive = Responsive(page)
        self._timer_activo = False
        self.base_real = cargar_base_calendario()
        self.datos_actuales = calcular_calendario_360(base_real=self.base_real)
        self.datos_consulta = None

        self.anio = ft.Text(
            "",
            color=ft.Colors.WHITE,
            text_align=ft.TextAlign.CENTER,
            weight=ft.FontWeight.BOLD,
        )
        self.mes_dia = ft.Text(
            "",
            color=ft.Colors.WHITE,
            text_align=ft.TextAlign.CENTER,
            weight=ft.FontWeight.BOLD,
        )
        self.hora = ft.Text(
            "",
            color=DORADO,
            text_align=ft.TextAlign.CENTER,
            weight=ft.FontWeight.BOLD,
        )
        self.dia_anio = ft.Text(
            "",
            color=ft.Colors.WHITE70,
            text_align=ft.TextAlign.CENTER,
        )
        self.fecha_real = ft.Text(
            "",
            color=ft.Colors.WHITE70,
            text_align=ft.TextAlign.CENTER,
        )
        self.base_input = ft.TextField(
            label="Día base del año 2000",
            hint_text="DD/MM/AAAA HH:MM:SS",
            value=self._texto_input_fecha(self.base_real),
            on_submit=self.aplicar_base,
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
        )
        self.base_era = ft.Dropdown(
            label="Era",
            value=self.base_real.era,
            width=96,
            options=[
                ft.dropdown.Option("DC"),
                ft.dropdown.Option("AC"),
            ],
        )
        self.consulta_input = ft.TextField(
            label="Consultar fecha real",
            hint_text="DD/MM/AAAA HH:MM:SS",
            value=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            on_submit=self.calcular_consulta,
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
        )
        self.consulta_era = ft.Dropdown(
            label="Era",
            value="DC",
            width=96,
            options=[
                ft.dropdown.Option("DC"),
                ft.dropdown.Option("AC"),
            ],
        )
        self.consulta_resultado = ft.Text(
            "",
            selectable=True,
            color=ft.Colors.BLACK,
        )
        self.consulta_resultado_panel = ft.Container(
            visible=False,
            padding=14,
            bgcolor=SUPERFICIE_PERLADA,
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=16,
            content=self.consulta_resultado,
        )

    def _texto_input_fecha(self, fecha):
        if isinstance(fecha, datetime):
            fecha = fecha_extendida_desde_datetime(fecha)

        return (
            f"{fecha.dia:02d}/{fecha.mes:02d}/{fecha.anio:04d} "
            f"{fecha.hora:02d}:{fecha.minuto:02d}:{fecha.segundo:02d}"
        )

    def _on_resize(self, e):
        self.router.refrescar()

    def obtener_vista(self):
        self.page.on_resize = self._on_resize
        self._actualizar_textos()
        self._iniciar_timer()

        es_movil = self.responsive.is_mobile()
        es_tablet = self.responsive.is_tablet()
        alto = self.page.window.height or 720
        bajo = alto < 680

        self.anio.size = 28 if es_movil else 34 if bajo else 42 if es_tablet else 48
        self.mes_dia.size = 16 if es_movil else 20 if bajo else 24
        self.hora.size = 50 if es_movil else 66 if bajo else 86 if es_tablet else 104
        self.dia_anio.size = 14 if es_movil else 16
        self.fecha_real.size = 12 if es_movil else 14

        if es_movil:
            contenido = ft.Column(
                expand=True,
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    self._panel_reloj(es_movil),
                    self._panel_consulta(es_movil),
                ],
            )
        else:
            contenido = ft.Row(
                expand=True,
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(
                        expand=3,
                        content=self._panel_reloj(es_movil),
                    ),
                    ft.Container(
                        expand=2,
                        content=self._panel_consulta(es_movil),
                    ),
                ],
            )

        return ft.Container(
            expand=True,
            bgcolor=ft.Colors.TRANSPARENT,
            padding=ft.Padding(left=4 if es_movil else 6, top=4 if es_movil else 6, right=4 if es_movil else 6, bottom=4),
            content=contenido,
        )

    def _panel_reloj(self, es_movil):
        return ft.Container(
            expand=not es_movil,
            border_radius=20,
            bgcolor=PURPURA_INICIAL,
            padding=16 if es_movil else 20,
            shadow=sombra_suave(0.075, 20, 0, 7),
            content=ft.Column(
                expand=not es_movil,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8 if es_movil else 10,
                controls=[
                    swatches_colores(14 if es_movil else 18),
                    ft.Container(
                        width=58 if es_movil else 66,
                        height=58 if es_movil else 66,
                        border_radius=20,
                        bgcolor=ft.Colors.with_opacity(0.14, ft.Colors.WHITE),
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(
                            ft.Icons.HOURGLASS_BOTTOM,
                            color=DORADO,
                            size=34 if es_movil else 42,
                        ),
                    ),
                    self.anio,
                    self.mes_dia,
                    self.hora,
                    self.dia_anio,
                    ft.Divider(color=ft.Colors.WHITE24, height=18),
                    ft.Text(
                        "Fecha real de referencia",
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.BOLD,
                    ),
                    self.fecha_real,
                    ft.ElevatedButton(
                        "Guardar tiempo actual",
                        icon=ft.Icons.SAVE_ALT,
                        bgcolor=DORADO,
                        color=ft.Colors.BLACK,
                        on_click=lambda e: self.guardar_tiempo(self.datos_actuales),
                    ),
                ],
            ),
        )

    def _panel_consulta(self, es_movil):
        self._actualizar_resultado_consulta_visible()
        contenido = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=12,
            controls=[
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(
                            "Consultar otra fecha",
                            size=18 if es_movil else 22,
                            color=TEXTO_PRINCIPAL,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CALENDAR_MONTH,
                            tooltip="Usar fecha actual",
                            on_click=lambda e: self.usar_ahora(),
                        ),
                    ],
                ),
                ft.Text(
                    "Ingresá una fecha real y convertí su equivalente dentro del calendario 360.",
                    size=12,
                    color=TEXTO_SECUNDARIO,
                ),
                self.consulta_input,
                self.consulta_era,
                ft.Row(
                    wrap=True,
                    spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            "Calcular",
                            icon=ft.Icons.SCHEDULE,
                            bgcolor=VIOLETA_IOS,
                            color=BLANCO,
                            on_click=self.calcular_consulta,
                        ),
                        ft.OutlinedButton(
                            "Guardar consulta",
                            icon=ft.Icons.SAVE_ALT,
                            on_click=lambda e: self.guardar_tiempo(
                                self.datos_consulta or self.datos_actuales
                            ),
                        ),
                    ],
                ),
                self.consulta_resultado_panel,
                ft.Divider(height=10),
                ft.Text(
                    "Base del calendario",
                    color=TEXTO_PRINCIPAL,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "La fecha elegida será Año 2000, Mes 1, Día 1, 00:00:00.",
                    color=TEXTO_SECUNDARIO,
                    size=12,
                ),
                self.base_input,
                self.base_era,
                ft.Row(
                    wrap=True,
                    spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            "Aplicar base",
                            icon=ft.Icons.CHECK,
                            bgcolor=VIOLETA_IOS,
                            color=BLANCO,
                            on_click=self.aplicar_base,
                        ),
                        ft.OutlinedButton(
                            "Base original",
                            icon=ft.Icons.RESTART_ALT,
                            on_click=self.restaurar_base,
                        ),
                    ],
                ),
            ],
        )
        return panel_moderno(contenido, padding=18 if es_movil else 20, expand=True)

    def _actualizar_resultado_consulta_visible(self):
        self.consulta_resultado_panel.visible = bool(
            (self.consulta_resultado.value or "").strip()
        )

    def _actualizar_textos(self):
        self.datos_actuales = calcular_calendario_360(base_real=self.base_real)
        datos = self.datos_actuales
        self.anio.value = f"AÑO {datos['anio']}"
        self.mes_dia.value = (
            f"{datos['mes']} - día {datos['dia_mes']}/30 "
            f"(mes {datos['mes_numero']}/12)"
        )
        self.hora.value = datos["hora_texto"]
        self.dia_anio.value = f"Día del año {datos['dia_anio']}/360"
        self.fecha_real.value = datos["fecha_real_texto"]

    def _iniciar_timer(self):
        if self._timer_activo:
            return
        self._timer_activo = True
        if hasattr(self.page, "run_task"):
            self.page.run_task(self._ciclo_reloj)

    async def _ciclo_reloj(self):
        while self.router.activo == "tiempo":
            self._actualizar_textos()
            try:
                self.anio.update()
                self.mes_dia.update()
                self.hora.update()
                self.dia_anio.update()
                self.fecha_real.update()
            except (RuntimeError, AssertionError):
                self._timer_activo = False
                return
            await asyncio.sleep(1)
        self._timer_activo = False

    def calcular_consulta(self, e=None):
        if e is not None:
            ocultar_teclado(self.page, e.control)
        try:
            fecha = parsear_fecha_consulta(
                self.consulta_input.value,
                self.consulta_era.value,
            )
            self.datos_consulta = calcular_calendario_360(
                fecha,
                base_real=self.base_real,
            )
            self.consulta_resultado.value = texto_calendario_360(self.datos_consulta)
        except ValueError as error:
            self.datos_consulta = None
            self.consulta_resultado.value = str(error)
        self._actualizar_resultado_consulta_visible()
        self.page.update()

    def usar_ahora(self):
        self.consulta_input.value = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.consulta_era.value = "DC"
        self.calcular_consulta()

    def aplicar_base(self, e=None):
        if e is not None:
            ocultar_teclado(self.page, e.control)
        try:
            self.base_real = parsear_fecha_consulta(
                self.base_input.value,
                self.base_era.value,
            )
            guardar_base_calendario(self.base_real)
            self.datos_consulta = None
            self.consulta_resultado.value = (
                f"Base actualizada: {formatear_fecha_real(self.base_real)}"
            )
            self._actualizar_textos()
        except ValueError as error:
            self.consulta_resultado.value = str(error)
        self._actualizar_resultado_consulta_visible()
        self.page.update()

    def restaurar_base(self, e=None):
        self.base_real = fecha_extendida_desde_datetime(datetime(2029, 4, 13, 0, 0, 0))
        guardar_base_calendario(self.base_real)
        self.base_input.value = self._texto_input_fecha(self.base_real)
        self.base_era.value = "DC"
        self.datos_consulta = None
        self.consulta_resultado.value = (
            f"Base restaurada: {formatear_fecha_real(self.base_real)}"
        )
        self._actualizar_textos()
        self._actualizar_resultado_consulta_visible()
        self.page.update()

    def guardar_tiempo(self, datos):
        if not datos:
            datos = calcular_calendario_360(base_real=self.base_real)

        nombre_sugerido = (
            f"Tiempo {datos['anio']} {datos['mes']} "
            f"{datos['dia_mes']:02d} {datos['hora_texto']}"
        )
        pedir_nombre_y_carpeta_guardado(
            self.page,
            "Guardar tiempo",
            nombre_sugerido,
            state.carpetas,
            "TIEMPO",
            lambda nombre, carpeta: self._guardar_tiempo_con_nombre(
                nombre,
                datos,
                carpeta,
            ),
            "Se guardara en la carpeta TIEMPO.",
        )

    def _guardar_tiempo_con_nombre(self, nombre, datos, carpeta=None):
        contenido = {
            clave: valor
            for clave, valor in datos.items()
            if clave not in {"fecha_real", "base_real"}
        }
        contenido["fecha_real_iso"] = datos["fecha_real"].isoformat()
        contenido["base_real_iso"] = datos["base_real"].isoformat()
        texto = texto_calendario_360(datos)
        destino = carpeta or state.carpetas.obtener_por_nombre("TIEMPO")

        state.guardados.guardar(
            {
                "tipo": "tiempo",
                "carpeta": destino["nombre"] if destino else "TIEMPO",
                "carpeta_id": destino["id"] if destino else 5,
                "nombre": nombre,
                "palabra": nombre,
                "referencia": datos["fecha_real_texto"],
                "alfabeto": "",
                "suma": texto,
                "resultado": str(datos["anio"]),
                "contenido": contenido,
            }
        )
        ruta = (
            state.carpetas.obtener_ruta_texto(destino["id"])
            if destino
            else "TIEMPO"
        )
        self._confirmacion(f"Tiempo guardado correctamente en {ruta}.")

    def _confirmacion(self, mensaje):
        def cerrar(e=None):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Guardado correctamente"),
            content=ft.Text(mensaje),
            actions=[
                ft.ElevatedButton("Aceptar", on_click=cerrar),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
