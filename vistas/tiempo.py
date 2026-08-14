import asyncio
from datetime import datetime

import flet as ft

from core.app_state import state
from logica.calendario_360 import (
    BASE_ANIO,
    calcular_calendario_360,
    cargar_base_calendario,
    fecha_gregoriana_desde_biblica,
    formatear_fecha_real,
    parsear_fecha_consulta,
    texto_calendario_360,
)
from logica.exportar_calendario import (
    exportar_convertidor_calendario_xlsx,
    exportar_almanaque_pdf,
    exportar_almanaque_xlsx,
)
from ui.nombre_guardado import pedir_nombre_y_carpeta_guardado
from ui.dialogos import cerrar_dialogo, mostrar_dialogo
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
from ui.compartir import descargar_archivo
from ui.clipboard import copiar_al_portapapeles


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
        self._anio_almanaque = BASE_ANIO

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
        self.acciones_consulta = ft.Row(
            visible=False,
            controls=[
                ft.IconButton(
                    icon=ft.Icons.CONTENT_COPY,
                    tooltip="Copiar resultado",
                    on_click=lambda e: copiar_al_portapapeles(
                        self.page, self.consulta_resultado.value
                    ),
                ),
            ],
        )
        self.biblica_anio_input = ft.TextField(
            label="Año bíblico",
            value=str(BASE_ANIO),
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_submit=self.calcular_fecha_gregoriana,
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
        )
        self.biblica_mes_input = ft.TextField(
            label="Mes (1-12)",
            value="1",
            width=130,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_submit=self.calcular_fecha_gregoriana,
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
        )
        self.biblica_dia_input = ft.TextField(
            label="Día (1-30)",
            value="1",
            width=130,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_submit=self.calcular_fecha_gregoriana,
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
        )
        self.biblica_resultado = ft.Text(
            "",
            selectable=True,
            color=ft.Colors.BLACK,
        )
        self.biblica_resultado_panel = ft.Container(
            visible=False,
            padding=14,
            bgcolor=SUPERFICIE_PERLADA,
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=16,
            content=self.biblica_resultado,
        )
        self.acciones_biblica = ft.Row(
            visible=False,
            controls=[
                ft.IconButton(
                    icon=ft.Icons.CONTENT_COPY,
                    tooltip="Copiar resultado",
                    on_click=lambda e: copiar_al_portapapeles(
                        self.page, self.biblica_resultado.value
                    ),
                ),
            ],
        )

    def _on_resize(self, e):
        self.router.refrescar()

    def _crear_almanaque(self, es_movil, anio=None, contenedor=None):
        """Construye los doce meses biblicos sin alterar la regla de 360 dias."""
        anio = self._anio_almanaque if anio is None else anio
        contenedor = contenedor or ft.Column(spacing=8)
        contenedor.controls.clear()

        meses = (
            "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre",
            "Octubre", "Noviembre", "Diciembre", "Enero", "Febrero", "Marzo",
        )
        tarjetas = []
        for indice, mes in enumerate(meses, start=1):
            dias = []
            for dia in range(1, 31):
                fecha_gregoriana = fecha_gregoriana_desde_biblica(anio, indice, dia)
                es_hoy = (
                    anio == self.datos_actuales["anio"]
                    and indice == self.datos_actuales["mes_numero"]
                    and dia == self.datos_actuales["dia_mes"]
                )
                dias.append(
                    ft.Container(
                        width=20 if es_movil else 24,
                        height=20 if es_movil else 24,
                        alignment=ft.Alignment(0, 0),
                        border_radius=4,
                        bgcolor=DORADO if es_hoy else "#8B5A44",
                        border=ft.Border.all(
                            1,
                            DORADO if es_hoy else "#B98262",
                        ),
                        tooltip=(
                            "Calendario gregoriano: "
                            f"{formatear_fecha_real(fecha_gregoriana)}"
                        ),
                        content=ft.Text(
                            str(dia),
                            size=9 if es_movil else 10,
                            color=MARRON_RELOJ if es_hoy else COLORES_DIGITOS[str(dia)[-1]],
                            weight=ft.FontWeight.BOLD if es_hoy else ft.FontWeight.W_500,
                        ),
                    )
                )
            tarjetas.append(
                ft.Container(
                    width=154 if es_movil else 190,
                    padding=7,
                    border_radius=12,
                    bgcolor="#6D402F",
                    border=ft.Border.all(1, "#B98262"),
                    content=ft.Column(
                        spacing=5,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(mes, color=DORADO, size=11 if es_movil else 13, weight=ft.FontWeight.BOLD),
                            ft.Row(
                                wrap=True,
                                spacing=3,
                                run_spacing=3,
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=dias,
                            ),
                        ],
                    ),
                )
            )
        columnas = 2 if es_movil else 3
        for inicio in range(0, len(tarjetas), columnas):
            contenedor.controls.append(
                ft.Row(
                    spacing=8,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=tarjetas[inicio:inicio + columnas],
                )
            )
        return contenedor

    def _seccion_almanaque(self, es_movil, anio):
        """Devuelve un año completo con su referencia gregoriana directa."""
        meses = ft.Column(spacing=8)
        self._crear_almanaque(es_movil, anio, meses)
        inicio = formatear_fecha_real(fecha_gregoriana_desde_biblica(anio, 1, 1))
        fin = formatear_fecha_real(fecha_gregoriana_desde_biblica(anio, 12, 30))

        return ft.Container(
            padding=10 if es_movil else 14,
            border_radius=14,
            bgcolor=ft.Colors.with_opacity(0.10, BLANCO),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.28, DORADO)),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        wrap=True,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                f"Año bíblico {anio}",
                                color=DORADO,
                                size=16 if es_movil else 18,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                f"Gregoriano: {inicio} a {fin}",
                                color=ft.Colors.WHITE70,
                                size=10 if es_movil else 11,
                            ),
                        ],
                    ),
                    ft.Divider(height=1, color=ft.Colors.with_opacity(0.28, DORADO)),
                    meses,
                ],
            ),
        )

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
                scroll=ft.ScrollMode.AUTO,
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
                    ft.Divider(color=ft.Colors.with_opacity(0.30, DORADO), height=14),
                    ft.OutlinedButton(
                        "Ver almanaque bíblico",
                        icon=ft.Icons.CALENDAR_MONTH,
                        icon_color=DORADO,
                        on_click=self.abrir_almanaque,
                    ),
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
                self.acciones_consulta,
                ft.Divider(height=10),
                ft.Text(
                    "Consultar fecha bíblica",
                    color=TEXTO_PRINCIPAL,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "Ingresá una fecha del calendario bíblico para conocer su equivalencia gregoriana.",
                    size=12,
                    color=TEXTO_SECUNDARIO,
                ),
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        self.biblica_anio_input,
                        self.biblica_mes_input,
                        self.biblica_dia_input,
                    ],
                ),
                ft.ElevatedButton(
                    "Convertir a gregoriano",
                    icon=ft.Icons.CALENDAR_TODAY,
                    bgcolor=MARRON_RELOJ_MEDIO,
                    color=BLANCO,
                    on_click=self.calcular_fecha_gregoriana,
                ),
                self.biblica_resultado_panel,
                self.acciones_biblica,
                ft.OutlinedButton(
                    "Descargar convertidor Excel",
                    icon=ft.Icons.TABLE_CHART,
                    on_click=self.descargar_convertidor_excel,
                ),
                ft.Divider(height=10),
                ft.Text(
                    "Base fija del calendario",
                    color=TEXTO_PRINCIPAL,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    f"11/04/2029 00:00:00 = Año {BASE_ANIO}, Abril, día 1. Las consultas comparan días reales sin corrección solar.",
                    color=TEXTO_SECUNDARIO,
                    size=12,
                ),
            ],
        )
        return panel_moderno(contenido, padding=18 if es_movil else 20, expand=True)

    def _actualizar_resultado_consulta_visible(self):
        visible = bool((self.consulta_resultado.value or "").strip())
        self.consulta_resultado_panel.visible = visible
        self.acciones_consulta.visible = visible

    def _actualizar_resultado_biblico_visible(self):
        visible = bool((self.biblica_resultado.value or "").strip())
        self.biblica_resultado_panel.visible = visible
        self.acciones_biblica.visible = visible

    def _avisar_conversion(self):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("Conversión realizada correctamente"),
            duration=1800,
            behavior=ft.SnackBarBehavior.FLOATING,
        )
        self.page.snack_bar.open = True

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
        self._avisar_conversion()
        self.page.update()

    def usar_ahora(self):
        self.consulta_input.value = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.consulta_era.value = "DC"
        self.calcular_consulta()

    def calcular_fecha_gregoriana(self, e=None):
        """Convierte directamente una fecha biblica de 360 dias a gregoriana."""
        if not self._puede("tiempo_consultar"):
            return
        if e is not None:
            ocultar_teclado(self.page, e.control)
        try:
            anio = int((self.biblica_anio_input.value or "").strip())
            mes = int((self.biblica_mes_input.value or "").strip())
            dia = int((self.biblica_dia_input.value or "").strip())
            fecha = fecha_gregoriana_desde_biblica(anio, mes, dia)
            self.biblica_resultado.value = (
                f"Fecha gregoriana equivalente: {formatear_fecha_real(fecha)}\n"
                f"Referencia: Año {BASE_ANIO}, mes 1, día 1 = "
                "11/04/2029 00:00:00 DC."
            )
        except ValueError:
            self.biblica_resultado.value = (
                "Ingresá valores numéricos válidos. El mes debe estar entre 1 y 12 "
                "y el día entre 1 y 30."
            )
        self._actualizar_resultado_biblico_visible()
        self._avisar_conversion()
        self.page.update()

    def descargar_convertidor_excel(self, e=None):
        try:
            archivo = exportar_convertidor_calendario_xlsx()
        except OSError:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("No se pudo crear el convertidor Excel."))
            self.page.snack_bar.open = True
            self.page.update()
            return
        descargar_archivo(self.page, archivo, "Guardar convertidor de calendario Excel")

    def abrir_almanaque(self, e=None):
        """Muestra un solo año por vez para conservar legible la equivalencia."""
        es_movil = self.responsive.is_mobile()
        self._anio_almanaque = BASE_ANIO
        meses = ft.Column(spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        titulo = ft.Text(
            f"Almanaque bíblico: año {self._anio_almanaque}",
            size=20,
            color=DORADO,
            weight=ft.FontWeight.BOLD,
        )
        referencia = ft.Text(
            "", size=11 if es_movil else 12, color=ft.Colors.WHITE70, text_align=ft.TextAlign.CENTER
        )
        panel_desplazable = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            controls=[referencia, meses],
        )

        anterior = ft.IconButton(
            icon=ft.Icons.KEYBOARD_ARROW_UP,
            tooltip="Ver año anterior",
        )
        siguiente = ft.IconButton(
            icon=ft.Icons.KEYBOARD_ARROW_DOWN,
            tooltip="Volver al año siguiente",
            disabled=True,
        )

        def texto_rango():
            inicio = formatear_fecha_real(
                fecha_gregoriana_desde_biblica(self._anio_almanaque, 1, 1)
            )
            fin = formatear_fecha_real(
                fecha_gregoriana_desde_biblica(self._anio_almanaque, 12, 30)
            )
            return (
                f"Mes 1, día 1: {inicio}. "
                f"Fin del año: {fin}. Cada mes tiene 30 días."
            )

        def refrescar_anio(ev=None):
            self._crear_almanaque(es_movil, self._anio_almanaque, meses)
            titulo.value = f"Almanaque bíblico: año {self._anio_almanaque}"
            referencia.value = texto_rango()
            siguiente.disabled = self._anio_almanaque >= BASE_ANIO
            self.page.update()
            panel_desplazable.scroll_to(offset=0)

        def ir_anterior(ev=None):
            self._anio_almanaque -= 1
            refrescar_anio()

        def ir_siguiente(ev=None):
            if self._anio_almanaque < BASE_ANIO:
                self._anio_almanaque += 1
                refrescar_anio()

        anterior.on_click = ir_anterior
        siguiente.on_click = ir_siguiente
        self._crear_almanaque(es_movil, self._anio_almanaque, meses)
        referencia.value = texto_rango()

        def cerrar(ev=None):
            cerrar_dialogo(self.page, dialog)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                tight=True,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[anterior, titulo, siguiente],
            ),
            content=ft.Container(
                width=700 if not es_movil else None,
                height=560 if not es_movil else 490,
                bgcolor=MARRON_RELOJ,
                border_radius=14,
                padding=12 if es_movil else 16,
                content=panel_desplazable,
            ),
            actions=[
                ft.OutlinedButton(
                    "Exportar",
                    icon=ft.Icons.DOWNLOAD,
                    on_click=lambda ev: self.abrir_exportacion_almanaque(ev, dialog),
                ),
                ft.TextButton("Cerrar", on_click=cerrar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        # El gestor monta el dialogo antes de abrirlo. Esto evita que Flet
        # intente actualizar un control aun ajeno a la pagina.
        mostrar_dialogo(self.page, dialog)

    def abrir_exportacion_almanaque(self, e=None, dialogo_padre=None):
        anio_actual = str(self._anio_almanaque)
        desde = ft.TextField(
            label="Desde el año bíblico",
            value=anio_actual,
            keyboard_type=ft.KeyboardType.NUMBER,
            width=210,
        )
        hasta = ft.TextField(
            label="Hasta el año bíblico",
            value=anio_actual,
            keyboard_type=ft.KeyboardType.NUMBER,
            width=210,
        )
        aviso = ft.Text("", color=ft.Colors.RED, size=12)

        def cerrar(ev=None):
            cerrar_dialogo(self.page, dialog)

        def exportar(formato):
            try:
                inicio = int((desde.value or "").strip())
                fin = int((hasta.value or "").strip())
                if formato == "xlsx":
                    archivo = exportar_almanaque_xlsx(inicio, fin)
                    titulo = "Guardar almanaque Excel"
                else:
                    archivo = exportar_almanaque_pdf(inicio, fin)
                    titulo = "Guardar almanaque PDF"
            except (ValueError, OSError) as error:
                aviso.value = str(error)
                self.page.update()
                return

            cerrar()
            if dialogo_padre is not None:
                cerrar_dialogo(self.page, dialogo_padre)
            descargar_archivo(self.page, archivo, titulo)

        dialog = ft.AlertDialog(
            title=ft.Text("Exportar almanaque"),
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Text(
                        "Elija un segmento de años. Excel crea una hoja por año y PDF una página por año.",
                        size=13,
                        color=TEXTO_SECUNDARIO,
                    ),
                    ft.Row(wrap=True, spacing=10, controls=[desde, hasta]),
                    aviso,
                ],
            ),
            actions=[
                ft.ElevatedButton(
                    "Excel",
                    icon=ft.Icons.TABLE_CHART,
                    bgcolor=MARRON_RELOJ_MEDIO,
                    color=BLANCO,
                    on_click=lambda ev: exportar("xlsx"),
                ),
                ft.OutlinedButton(
                    "PDF",
                    icon=ft.Icons.PICTURE_AS_PDF,
                    on_click=lambda ev: exportar("pdf"),
                ),
                ft.TextButton("Cancelar", on_click=cerrar),
            ],
        )
        mostrar_dialogo(self.page, dialog)

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
            cerrar_dialogo(self.page, dialog)

        dialog = ft.AlertDialog(
            title=ft.Text("Guardado correctamente"),
            content=ft.Text(mensaje),
            actions=[
                ft.ElevatedButton("Aceptar", on_click=cerrar),
            ],
        )

        mostrar_dialogo(self.page, dialog)
