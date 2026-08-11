import asyncio
from datetime import datetime

import flet as ft

from core.app_state import state
from logica.calendario_360 import (
    ANIOS_BIBLICOS_PREVIOS,
    BASE_ANIO,
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
    MARRON,
    PERLA_BORDE,
    PERLA_PANEL,
    SUPERFICIE_PERLADA,
    TEXTO_PRINCIPAL,
    TEXTO_SECUNDARIO,
    panel_moderno,
    swatches_colores,
)
from ui.teclado import ocultar_teclado


MARRON_RELOJ = "#5A3023"
MARRON_RELOJ_MEDIO = "#7D4937"
COLORES_DIGITOS = {
    "0": "#171717",
    "1": "#B97852",
    "2": "#F01824",
    "3": "#FF7A24",
    "4": "#FFF300",
    "5": "#24AE52",
    "6": "#4448C8",
    "7": "#A44BA8",
    "8": "#C9C9C9",
    "9": "#FFFFFF",
}


class TiempoView:
    def __init__(self, page, router):
        self.page = page
        self.router = router
        self.responsive = Responsive(page)
        self._timer_activo = False
        self.base_real = cargar_base_calendario()
        self.datos_actuales = calcular_calendario_360(base_real=self.base_real)
        self.datos_consulta = None
        self._pulso_reloj = False
        self._tamano_anio = 48
        self._tamano_hora = 104
        self._tamano_fecha = 20

        self.anio = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=7,
        )
        self.mes_dia = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            wrap=True,
        )
        self.hora = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5,
        )
        self.dia_anio = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=3,
            wrap=True,
        )
        self.fecha_real = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=2,
            wrap=True,
        )
        self.reloj_icono = ft.Container(
            width=66,
            height=66,
            border_radius=20,
            bgcolor=ft.Colors.with_opacity(0.18, DORADO),
            alignment=ft.Alignment(0, 0),
            animate_scale=ft.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
            content=ft.Icon(ft.Icons.HOURGLASS_BOTTOM, color=DORADO, size=42),
        )
        self.base_input = ft.TextField(
            label=f"Día base del año {BASE_ANIO + ANIOS_BIBLICOS_PREVIOS}",
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

    def _digito(self, valor, tamano, destacado=True):
        color = COLORES_DIGITOS.get(str(valor), BLANCO)
        borde = ft.Border.all(1, MARRON) if str(valor) == "9" else None
        return ft.Container(
            padding=ft.Padding(left=2, top=0, right=2, bottom=0),
            border=borde,
            border_radius=4,
            content=ft.Text(
                str(valor),
                size=tamano,
                color=color,
                weight=ft.FontWeight.BOLD if destacado else ft.FontWeight.W_500,
            ),
        )

    def _texto_numerico(self, texto, tamano, color_texto=ft.Colors.WHITE, destacado=True):
        controles = []
        for caracter in str(texto):
            if caracter.isdigit():
                controles.append(self._digito(caracter, tamano, destacado))
            else:
                controles.append(
                    ft.Text(
                        caracter,
                        size=tamano,
                        color=color_texto,
                        weight=ft.FontWeight.BOLD if destacado else ft.FontWeight.W_500,
                    )
                )
        return controles

    def _texto_y_numero(self, etiqueta, numero, tamano_texto, tamano_numero):
        return [
            ft.Text(etiqueta, size=tamano_texto, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            *self._texto_numerico(numero, tamano_numero),
        ]

    def _puede(self, capacidad):
        comprobar = getattr(self.router, "tiene_capacidad", None)
        return bool(comprobar(capacidad)) if callable(comprobar) else True

    def obtener_vista(self):
        self.page.on_resize = self._on_resize
        self._actualizar_textos()
        self._iniciar_timer()

        es_movil = self.responsive.is_mobile()
        es_tablet = self.responsive.is_tablet()
        alto = self.page.window.height or 720
        bajo = alto < 680

        self._tamano_anio = 28 if es_movil else 34 if bajo else 42 if es_tablet else 48
        self._tamano_hora = 50 if es_movil else 66 if bajo else 86 if es_tablet else 104
        self._tamano_fecha = 14 if es_movil else 16
        self._actualizar_textos()
        puede_consultar = self._puede("tiempo_consultar")

        if es_movil:
            contenido = ft.Column(
                expand=True,
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
                controls=[self._panel_reloj(es_movil)] + ([self._panel_consulta(es_movil)] if puede_consultar else []),
            )
        else:
            contenido = ft.Row(
                expand=True,
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(
                        expand=3 if puede_consultar else True,
                        content=self._panel_reloj(es_movil),
                    ),
                ] + ([
                    ft.Container(expand=2, content=self._panel_consulta(es_movil)),
                ] if puede_consultar else []),
            )

        return ft.Container(
            expand=True,
            bgcolor=ft.Colors.TRANSPARENT,
            padding=ft.Padding(left=4 if es_movil else 6, top=4 if es_movil else 6, right=4 if es_movil else 6, bottom=4),
            content=contenido,
        )

    def _panel_reloj(self, es_movil):
        tamano_icono = 58 if es_movil else 66
        self.reloj_icono.width = tamano_icono
        self.reloj_icono.height = tamano_icono
        self.reloj_icono.content.size = 34 if es_movil else 42
        return ft.Container(
            expand=not es_movil,
            border_radius=20,
            bgcolor=MARRON_RELOJ,
            padding=16 if es_movil else 20,
            shadow=ft.BoxShadow(
                blur_radius=26,
                spread_radius=0,
                color=ft.Colors.with_opacity(0.24, MARRON_RELOJ_MEDIO),
                offset=ft.Offset(0, 10),
            ),
            content=ft.Column(
                expand=not es_movil,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8 if es_movil else 10,
                controls=[
                    swatches_colores(14 if es_movil else 18),
                    self.reloj_icono,
                    self.anio,
                    self.mes_dia,
                    self.hora,
                    self.dia_anio,
                    ft.Divider(color=ft.Colors.with_opacity(0.30, DORADO), height=18),
                    ft.Text(
                        "Fecha real de referencia",
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.BOLD,
                    ),
                    self.fecha_real,
                    *([
                        ft.ElevatedButton(
                            "Guardar tiempo actual",
                            icon=ft.Icons.SAVE_ALT,
                            bgcolor=DORADO,
                            color=MARRON_RELOJ,
                            on_click=lambda e: self.guardar_tiempo(self.datos_actuales),
                        ),
                    ] if self._puede("tiempo_guardar") else []),
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
                            bgcolor=MARRON_RELOJ_MEDIO,
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
                    f"La fecha elegida será Año {BASE_ANIO + ANIOS_BIBLICOS_PREVIOS}, Mes 1, Día 1, 00:00:00.",
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
                            bgcolor=MARRON_RELOJ_MEDIO,
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
        self.anio.controls = self._texto_y_numero(
            "AÑO",
            datos["anio"],
            max(18, self._tamano_anio - 8),
            self._tamano_anio,
        )
        self.mes_dia.controls = [
            ft.Text(datos["mes"], size=self._tamano_fecha + 4, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            ft.Text("- día", size=self._tamano_fecha + 4, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            *self._texto_numerico(f"{datos['dia_mes']}/30", self._tamano_fecha + 4),
            ft.Text("(mes", size=self._tamano_fecha + 4, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            *self._texto_numerico(f"{datos['mes_numero']}/12)", self._tamano_fecha + 4),
        ]
        self.hora.controls = self._texto_numerico(datos["hora_texto"], self._tamano_hora)
        self.dia_anio.controls = [
            ft.Text("Día del año", size=self._tamano_fecha, color=ft.Colors.WHITE70),
            *self._texto_numerico(f"{datos['dia_anio']}/360", self._tamano_fecha, ft.Colors.WHITE70, False),
        ]
        self.fecha_real.controls = self._texto_numerico(
            datos["fecha_real_texto"],
            max(11, self._tamano_fecha - 2),
            ft.Colors.WHITE70,
            False,
        )

    def _iniciar_timer(self):
        if self._timer_activo:
            return
        self._timer_activo = True
        if hasattr(self.page, "run_task"):
            self.page.run_task(self._ciclo_reloj)

    async def _ciclo_reloj(self):
        while self.router.activo == "tiempo":
            self._actualizar_textos()
            self._pulso_reloj = not self._pulso_reloj
            self.reloj_icono.scale = ft.Scale(1.08 if self._pulso_reloj else 1.0)
            try:
                self.anio.update()
                self.mes_dia.update()
                self.hora.update()
                self.dia_anio.update()
                self.fecha_real.update()
                self.reloj_icono.update()
            except (RuntimeError, AssertionError):
                self._timer_activo = False
                return
            await asyncio.sleep(1)
        self._timer_activo = False

    def calcular_consulta(self, e=None):
        if not self._puede("tiempo_consultar"):
            return
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
        if not self._puede("tiempo_consultar"):
            return
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
        if not self._puede("tiempo_consultar"):
            return
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
        if not self._puede("tiempo_guardar"):
            return
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
