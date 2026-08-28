import asyncio
from datetime import datetime

import flet as ft

from services.archivo_local_service import ArchivoLocalService
from logica.calendario_360 import (
    BASE_ANIO,
    MESES_360,
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
from ui.dialogos import cerrar_dialogo, mostrar_dialogo
from ui.responsive import Responsive
from ui.tema import (
    BLANCO,
    DORADO,
    MARRON,
    PERLA_BORDE,
    SUPERFICIE_PERLADA,
    TEXTO_PRINCIPAL,
    TEXTO_SECUNDARIO,
    panel_moderno,
)
from ui.teclado import ocultar_teclado
from ui.compartir import descargar_archivo
from ui.clipboard import copiar_al_portapapeles


MARRON_RELOJ = "#5A3023"
MARRON_RELOJ_MEDIO = "#7D4937"
ALMANAQUE_TEXTO_CLARO = "#FFF7E6"
LINEA_TIEMPO_MARRON = "#B97554"
LINEA_TIEMPO_ROJO = "#F01824"
LINEA_TIEMPO_AMARILLO = "#F0E500"
LINEA_TIEMPO_VERDE = "#1EAD4B"
LINEA_TIEMPO_VIOLETA = "#A64CB0"
FECHA_INICIO_APOPHIS = datetime(2004, 6, 19, 0, 0, 0)
FECHA_APOPHIS = datetime(2029, 4, 13, 0, 0, 0)
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


class TarjetaFlip:
    def __init__(self, valor, ancho, alto, tamano_texto, resolver_color):
        self.valor = str(valor)
        self.ancho = ancho
        self.alto = alto
        self.mitad = alto / 2
        self.tamano_texto = tamano_texto
        self.resolver_color = resolver_color
        self.texto_superior_base = self._crear_texto(self.valor)
        self.texto_inferior_base = self._crear_texto(self.valor)
        self.texto_superior_flip = self._crear_texto(self.valor)
        self.texto_inferior_flip = self._crear_texto(self.valor)
        self.superior_base = self._crear_media_cara(
            self.texto_superior_base, superior=True
        )
        self.inferior_base = self._crear_media_cara(
            self.texto_inferior_base, superior=False
        )
        self.superior_flip = self._crear_media_cara(
            self.texto_superior_flip, superior=True, animada=True
        )
        self.inferior_flip = self._crear_media_cara(
            self.texto_inferior_flip, superior=False, animada=True
        )
        self.superior_flip.visible = False
        self.inferior_flip.visible = False
        self.superior_flip.animate = ft.Animation(220, ft.AnimationCurve.EASE_IN)
        self.inferior_flip.animate = ft.Animation(220, ft.AnimationCurve.EASE_OUT)
        self.superior_flip.transform = self._transformacion(0, superior=True)
        self.inferior_flip.transform = self._transformacion(-1.54, superior=False)
        self.control = ft.Stack(
            width=ancho,
            height=alto,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            controls=[
                self.superior_base,
                self.inferior_base,
                self.superior_flip,
                self.inferior_flip,
            ],
        )

    def _crear_texto(self, valor):
        return ft.Text(
            valor,
            size=self.tamano_texto,
            color=self.resolver_color(valor),
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )

    def _crear_media_cara(self, texto, superior, animada=False):
        radio = (
            ft.BorderRadius.only(top_left=6, top_right=6)
            if superior
            else ft.BorderRadius.only(bottom_left=6, bottom_right=6)
        )
        contenido = ft.Container(
            top=0 if superior else -self.mitad,
            width=self.ancho,
            height=self.alto,
            alignment=ft.Alignment(0, 0),
            content=texto,
        )
        return ft.Container(
            top=0 if superior else self.mitad,
            width=self.ancho,
            height=self.mitad,
            bgcolor="#6B3C2E" if animada else "#512E24",
            border=ft.Border.all(1, "#2A1510"),
            border_radius=radio,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            shadow=(
                ft.BoxShadow(
                    blur_radius=7,
                    spread_radius=0,
                    color=ft.Colors.with_opacity(0.42, "#2A1510"),
                    offset=ft.Offset(0, 4),
                )
                if animada
                else None
            ),
            content=ft.Stack(
                width=self.ancho,
                height=self.mitad,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                controls=[
                    contenido,
                    ft.Container(
                        left=0,
                        top=self.mitad - 2 if superior else 0,
                        width=self.ancho,
                        height=2,
                        bgcolor="#2A1510",
                    ),
                ],
            ),
        )

    def _transformacion(self, angulo, superior):
        matriz = ft.Matrix4.identity().set_entry(3, 2, 0.0015).rotate_x(angulo)
        return ft.Transform(
            matrix=matriz,
            alignment=ft.Alignment(0, 1 if superior else -1),
        )

    def _asignar_texto(self, texto, valor):
        texto.value = valor
        texto.color = self.resolver_color(valor)

    def preparar_cambio(self, nuevo_valor):
        nuevo_valor = str(nuevo_valor)
        if nuevo_valor == self.valor:
            return False
        valor_anterior = self.valor
        self._asignar_texto(self.texto_superior_base, nuevo_valor)
        self._asignar_texto(self.texto_inferior_base, valor_anterior)
        self._asignar_texto(self.texto_superior_flip, valor_anterior)
        self._asignar_texto(self.texto_inferior_flip, nuevo_valor)
        self.superior_flip.visible = True
        self.superior_flip.transform = self._transformacion(0, superior=True)
        self.inferior_flip.visible = False
        self.inferior_flip.transform = self._transformacion(-1.54, superior=False)
        self.valor = nuevo_valor
        return True

    def establecer(self, nuevo_valor):
        nuevo_valor = str(nuevo_valor)
        self.valor = nuevo_valor
        self._asignar_texto(self.texto_superior_base, nuevo_valor)
        self._asignar_texto(self.texto_inferior_base, nuevo_valor)
        self.superior_flip.visible = False
        self.inferior_flip.visible = False
        self.superior_flip.transform = self._transformacion(0, superior=True)
        self.inferior_flip.transform = self._transformacion(-1.54, superior=False)

    def iniciar_caida(self):
        self.superior_flip.transform = self._transformacion(1.54, superior=True)

    def preparar_reverso(self):
        self.superior_flip.visible = False
        self.inferior_flip.visible = True
        self.inferior_flip.transform = self._transformacion(-1.54, superior=False)

    def completar_caida(self):
        self.inferior_flip.transform = self._transformacion(0, superior=False)

    def terminar_caida(self):
        self._asignar_texto(self.texto_inferior_base, self.valor)
        self.superior_flip.visible = False
        self.inferior_flip.visible = False
        self.superior_flip.transform = self._transformacion(0, superior=True)
        self.inferior_flip.transform = self._transformacion(-1.54, superior=False)


class TiempoView:
    def __init__(self, page, router):
        self.page = page
        self.router = router
        self.responsive = Responsive(page)
        self._timer_activo = False
        self.base_real = cargar_base_calendario()
        self.datos_actuales = calcular_calendario_360(base_real=self.base_real)
        self.datos_consulta = None
        self._anio_almanaque = BASE_ANIO
        self._ancho_ultimo_resize = None
        self._alto_ultimo_resize = None
        self._ajustar_dialogo_activo = None
        self._tarjetas_flip = {}
        self.reloj_fecha_flip = ft.Container()
        self.reloj_hora_flip = ft.Container()
        self.consulta_input = ft.TextField(
            label="Fecha",
            hint_text="DD-MM-AAAA",
            value=datetime.now().strftime("%d-%m-%Y"),
            keyboard_type=ft.KeyboardType.DATETIME,
            on_submit=self.calcular_consulta,
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
        )
        self.consulta_calendario = ft.SegmentedButton(
            selected=["biblico"],
            show_selected_icon=False,
            segments=[
                ft.Segment(
                    value="biblico",
                    icon=ft.Icons.AUTO_STORIES,
                    label="Bíblico",
                ),
                ft.Segment(
                    value="gregoriano",
                    icon=ft.Icons.CALENDAR_MONTH,
                    label="Gregoriano",
                ),
            ],
            on_change=self._cambiar_tipo_consulta,
        )
        self.consulta_alcance = ft.SegmentedButton(
            selected=["exacta"],
            show_selected_icon=False,
            segments=[
                ft.Segment(value="exacta", label="Fecha exacta"),
                ft.Segment(value="edades", label="Tres edades"),
            ],
        )
        self.consulta_era = ft.SegmentedButton(
            selected=["DC"],
            show_selected_icon=False,
            segments=[
                ft.Segment(
                    value="DC",
                    label="DC",
                    tooltip="Después de Cristo",
                ),
                ft.Segment(
                    value="AC",
                    label="AC",
                    tooltip="Antes de Cristo",
                ),
            ],
        )
        self.consulta_opciones_biblicas = ft.Container(visible=False)
        self.consulta_opciones_gregorianas = ft.Column(
            tight=True,
            visible=False,
            spacing=10,
            controls=[
                ft.Text(
                    "Era",
                    size=12,
                    color=TEXTO_SECUNDARIO,
                    weight=ft.FontWeight.BOLD,
                ),
                self.consulta_era,
                ft.Text(
                    "Resultado bíblico",
                    size=12,
                    color=TEXTO_SECUNDARIO,
                    weight=ft.FontWeight.BOLD,
                ),
                self.consulta_alcance,
            ],
        )
        self.consulta_resultado = ft.Text(
            "",
            selectable=True,
            color=TEXTO_PRINCIPAL,
        )
        self.consulta_resultado_panel = ft.Container(
            visible=False,
            padding=ft.Padding(left=2, top=8, right=2, bottom=2),
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
        ancho = getattr(e, "width", None)
        alto = getattr(e, "height", None)
        if ancho:
            self._ancho_ultimo_resize = float(ancho)
        if alto:
            self._alto_ultimo_resize = float(alto)
        if callable(self._ajustar_dialogo_activo):
            self._ajustar_dialogo_activo(
                self._ancho_ultimo_resize,
                self._alto_ultimo_resize,
            )
        self.router.refrescar()

    def _crear_almanaque(self, es_movil, anio=None, contenedor=None):
        """Construye los doce meses biblicos sin alterar la regla de 360 dias."""
        anio = self._anio_almanaque if anio is None else anio
        contenedor = contenedor or ft.Column(spacing=8)
        contenedor.controls.clear()

        ancho_dialogo = self._ancho_dialogo_almanaque(es_movil)
        ancho_util = max(236, ancho_dialogo - (30 if es_movil else 44))
        espacio_tarjetas = 6 if es_movil else 8
        if es_movil:
            columnas = 1
            ancho_tarjeta = min(190, max(154, ancho_util - 8))
            tamano_dia = max(17, min(20, int((ancho_tarjeta - 31) / 6)))
            tamano_texto_dia = 8 if tamano_dia < 19 else 9
        else:
            columnas = 3 if ancho_util >= 610 else 2
            ancho_tarjeta = min(
                190,
                int((ancho_util - (espacio_tarjetas * (columnas - 1))) / columnas),
            )
            tamano_dia = 24
            tamano_texto_dia = 10

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
                        width=tamano_dia,
                        height=tamano_dia,
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
                            size=tamano_texto_dia,
                            color=MARRON_RELOJ if es_hoy else COLORES_DIGITOS[str(dia)[-1]],
                            weight=ft.FontWeight.BOLD if es_hoy else ft.FontWeight.W_500,
                        ),
                    )
                )
            tarjetas.append(
                ft.Container(
                    width=ancho_tarjeta,
                    padding=7,
                    border_radius=12,
                    bgcolor="#6D402F",
                    border=ft.Border.all(1, "#B98262"),
                    content=ft.Column(
                        spacing=5,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(mes, color=ALMANAQUE_TEXTO_CLARO, size=11 if es_movil else 13, weight=ft.FontWeight.BOLD),
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
        for inicio in range(0, len(tarjetas), columnas):
            contenedor.controls.append(
                ft.Row(
                    spacing=espacio_tarjetas,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=tarjetas[inicio:inicio + columnas],
                )
            )
        return contenedor

    def _ancho_pantalla_actual(self):
        anchos = []
        if self._ancho_ultimo_resize:
            anchos.append(self._ancho_ultimo_resize)
        for origen in (self.page, getattr(self.page, "window", None)):
            ancho = getattr(origen, "width", None) if origen is not None else None
            if ancho:
                anchos.append(ancho)
        return min(anchos) if anchos else self.responsive.width()

    def _ancho_dialogo_almanaque(self, es_movil):
        ancho = self._ancho_pantalla_actual()
        if es_movil:
            return max(230, min(520, ancho - 28))
        return max(560, min(760, ancho - 120))

    def _alto_dialogo_almanaque(self, es_movil):
        alto = getattr(self.page, "height", None)
        if alto is None and hasattr(self.page, "window"):
            alto = getattr(self.page.window, "height", None)
        alto = alto or 720
        if es_movil:
            return max(360, min(520, alto - 190))
        return max(460, min(590, alto - 170))

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

    def _puede(self, capacidad):
        comprobar = getattr(self.router, "tiene_capacidad", None)
        return bool(comprobar(capacidad)) if callable(comprobar) else True

    def _grupo_tarjetas_flip(self, controles, etiqueta, es_movil):
        return ft.Column(
            tight=True,
            spacing=5,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    tight=True,
                    spacing=3 if es_movil else 4,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=controles,
                ),
                ft.Text(
                    etiqueta,
                    size=9 if es_movil else 11,
                    color=ft.Colors.WHITE70,
                    weight=ft.FontWeight.BOLD,
                ),
            ],
        )

    def _configurar_relojes_flip(self, es_movil, bajo=False):
        datos = self.datos_actuales
        muy_estrecho = es_movil and self._ancho_pantalla_actual() < 300
        if muy_estrecho:
            ancho_digito, alto_tarjeta, tamano_digito = 22, 42, 22
            ancho_mes, tamano_mes = 48, 18
        elif es_movil:
            ancho_digito, alto_tarjeta, tamano_digito = 28, 46, 26
            ancho_mes, tamano_mes = 62, 22
        elif bajo:
            ancho_digito, alto_tarjeta, tamano_digito = 40, 60, 36
            ancho_mes, tamano_mes = 86, 28
        else:
            ancho_digito, alto_tarjeta, tamano_digito = 48, 72, 44
            ancho_mes, tamano_mes = 100, 34

        self._tarjetas_flip = {}

        def tarjeta(clave, valor, ancho=None, tamano=None, resolver=None):
            control = TarjetaFlip(
                valor,
                ancho or ancho_digito,
                alto_tarjeta,
                tamano or tamano_digito,
                resolver or (lambda texto: COLORES_DIGITOS.get(texto[-1:], BLANCO)),
            )
            self._tarjetas_flip[clave] = control
            return control.control

        dia = f"{datos['dia_mes']:02d}"
        anio = f"{datos['anio']:04d}"
        hora = f"{datos['hora']:02d}"
        minuto = f"{datos['minuto']:02d}"
        segundo = f"{datos['segundo']:02d}"
        mes = datos["mes"][:3].upper()

        grupo_dia = self._grupo_tarjetas_flip(
            [tarjeta(f"dia_{indice}", valor) for indice, valor in enumerate(dia)],
            "DÍA",
            es_movil,
        )
        grupo_mes = self._grupo_tarjetas_flip(
            [
                tarjeta(
                    "mes",
                    mes,
                    ancho=ancho_mes,
                    tamano=tamano_mes,
                    resolver=lambda texto: DORADO,
                )
            ],
            "MES",
            es_movil,
        )
        grupo_anio = self._grupo_tarjetas_flip(
            [tarjeta(f"anio_{indice}", valor) for indice, valor in enumerate(anio)],
            "AÑO",
            es_movil,
        )
        grupo_hora = self._grupo_tarjetas_flip(
            [tarjeta(f"hora_{indice}", valor) for indice, valor in enumerate(hora)],
            "HORA",
            es_movil,
        )
        grupo_minuto = self._grupo_tarjetas_flip(
            [tarjeta(f"minuto_{indice}", valor) for indice, valor in enumerate(minuto)],
            "MINUTO",
            es_movil,
        )
        grupo_segundo = self._grupo_tarjetas_flip(
            [tarjeta(f"segundo_{indice}", valor) for indice, valor in enumerate(segundo)],
            "SEGUNDO",
            es_movil,
        )
        separador_tiempo = lambda: ft.Container(
            height=alto_tarjeta,
            alignment=ft.Alignment(0, 0),
            content=ft.Text(
                ":",
                size=24 if es_movil else 34,
                color=ft.Colors.WHITE70,
                weight=ft.FontWeight.BOLD,
            ),
        )

        def panel_reloj(titulo, icono, grupos):
            return ft.Container(
                padding=8 if muy_estrecho else (10 if es_movil else 14),
                bgcolor="#43261E",
                border=ft.Border.all(1, "#754638"),
                border_radius=8,
                shadow=ft.BoxShadow(
                    blur_radius=12,
                    spread_radius=0,
                    color=ft.Colors.with_opacity(0.24, "#2A1510"),
                    offset=ft.Offset(0, 4),
                ),
                content=ft.Column(
                    tight=True,
                    spacing=9 if es_movil else 12,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Row(
                            tight=True,
                            spacing=6,
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(icono, size=16 if es_movil else 18, color=DORADO),
                                ft.Text(
                                    titulo,
                                    size=11 if es_movil else 13,
                                    color=ft.Colors.WHITE,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                        ),
                        ft.Row(
                            tight=True,
                            wrap=False,
                            spacing=5 if muy_estrecho else (7 if es_movil else 12),
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            controls=grupos,
                        ),
                    ],
                ),
            )

        self.reloj_fecha_flip = panel_reloj(
            "FECHA BÍBLICA",
            ft.Icons.CALENDAR_MONTH,
            [grupo_dia, grupo_mes, grupo_anio],
        )
        self.reloj_hora_flip = panel_reloj(
            "HORA BÍBLICA",
            ft.Icons.SCHEDULE,
            [
                grupo_hora,
                separador_tiempo(),
                grupo_minuto,
                separador_tiempo(),
                grupo_segundo,
            ],
        )

    def obtener_vista(self):
        self.page.on_resize = self._on_resize
        es_movil = self._ancho_pantalla_actual() < 700
        alto = (
            self._alto_ultimo_resize
            or getattr(self.page, "height", None)
            or getattr(self.page.window, "height", None)
            or 720
        )
        bajo = alto < 680
        self.datos_actuales = calcular_calendario_360(base_real=self.base_real)
        self._configurar_relojes_flip(es_movil, bajo)
        self._actualizar_textos(animar=False)
        self._iniciar_timer()
        contenido = ft.Column(
            expand=True,
            spacing=8 if es_movil else 10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self._herramientas_reloj(es_movil),
                ft.Container(expand=True, content=self._panel_reloj(es_movil)),
            ],
        )

        return ft.Container(
            expand=True,
            bgcolor=ft.Colors.TRANSPARENT,
            padding=ft.Padding(left=4 if es_movil else 6, top=4 if es_movil else 6, right=4 if es_movil else 6, bottom=4),
            content=contenido,
        )

    def _panel_reloj(self, es_movil):
        if es_movil:
            contenido = ft.Column(
                tight=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[self.reloj_fecha_flip, self.reloj_hora_flip],
            )
        else:
            contenido = ft.Row(
                wrap=True,
                spacing=14,
                run_spacing=12,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[self.reloj_fecha_flip, self.reloj_hora_flip],
            )
        return ft.Container(
            expand=not es_movil,
            bgcolor=ft.Colors.TRANSPARENT,
            padding=0,
            alignment=ft.Alignment(0, 0),
            content=contenido,
        )

    def _boton_herramienta_reloj(self, texto, icono, on_click, es_movil):
        return ft.OutlinedButton(
            texto,
            icon=icono,
            icon_color=DORADO,
            width=134 if es_movil else 164,
            height=34 if es_movil else 36,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                side=ft.BorderSide(1, ft.Colors.with_opacity(0.54, DORADO)),
                padding=ft.Padding(8, 0, 8, 0),
                text_style=ft.TextStyle(size=11 if es_movil else 12),
            ),
            on_click=on_click,
        )

    def _herramientas_reloj(self, es_movil):
        botones = [
            self._boton_herramienta_reloj(
                "Almanaque",
                ft.Icons.CALENDAR_MONTH,
                self.abrir_almanaque,
                es_movil,
            ),
            self._boton_herramienta_reloj(
                "Lineas del Tiempo",
                ft.Icons.TIMELINE,
                self.abrir_lineas_tiempo,
                es_movil,
            ),
            self._boton_herramienta_reloj(
                "Apofis",
                ft.Icons.TRACK_CHANGES,
                self.abrir_linea_apofis,
                es_movil,
            ),
        ]
        if self._puede("tiempo_consultar"):
            botones.append(
                self._boton_herramienta_reloj(
                    "Consultas",
                    ft.Icons.DATE_RANGE,
                    self.abrir_consultas,
                    es_movil,
                )
            )
        if es_movil:
            return ft.Container(
                padding=ft.Padding(8, 6, 8, 6),
                border_radius=12,
                bgcolor=ft.Colors.with_opacity(0.78, MARRON_RELOJ),
                content=ft.Row(
                    wrap=True,
                    spacing=6,
                    run_spacing=6,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=botones,
                ),
            )
        return ft.Container(
            padding=ft.Padding(10, 7, 10, 7),
            border_radius=14,
            bgcolor=ft.Colors.with_opacity(0.78, MARRON_RELOJ),
            content=ft.Row(
                wrap=True,
                spacing=8,
                run_spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=botones,
            )
        )

    def abrir_consultas(self, e=None):
        es_movil = self._ancho_pantalla_actual() < 700
        ancho = self._ancho_dialogo_fecha(es_movil)
        ventana = getattr(self.page, "window", None)
        alto_pantalla = (
            getattr(self.page, "height", None)
            or getattr(ventana, "height", None)
            or 720
        )
        alto = max(380, min(560, alto_pantalla - 120))
        panel = self._panel_consulta(es_movil)

        def cerrar(ev=None):
            cerrar_dialogo(self.page, dialog)

        dialog = ft.AlertDialog(
            modal=False,
            title=ft.Text(
                "Consultas",
                color=TEXTO_PRINCIPAL,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Container(
                width=ancho,
                height=alto,
                content=panel,
            ),
            actions=[ft.TextButton("Cerrar", on_click=cerrar)],
            actions_alignment=ft.MainAxisAlignment.END,
            inset_padding=ft.Padding(
                8 if es_movil else 24,
                8 if es_movil else 24,
                8 if es_movil else 24,
                8 if es_movil else 24,
            ),
        )
        mostrar_dialogo(self.page, dialog)

    def _panel_consulta(self, es_movil):
        self._actualizar_resultado_consulta_visible()
        contenido = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(
                            "Conversión de fecha",
                            size=18 if es_movil else 20,
                            color=TEXTO_PRINCIPAL,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.TODAY,
                            tooltip="Usar hoy",
                            on_click=lambda e: self.usar_ahora(),
                        ),
                    ],
                ),
                ft.Text(
                    "Calendario de la fecha ingresada",
                    size=12,
                    color=TEXTO_SECUNDARIO,
                    weight=ft.FontWeight.BOLD,
                ),
                self.consulta_calendario,
                self.consulta_input,
                self.consulta_opciones_biblicas,
                self.consulta_opciones_gregorianas,
                ft.Row(
                    spacing=8,
                    alignment=ft.MainAxisAlignment.START,
                    controls=[
                        ft.ElevatedButton(
                            "Consultar",
                            icon=ft.Icons.SEARCH,
                            bgcolor=MARRON_RELOJ_MEDIO,
                            color=BLANCO,
                            on_click=self.calcular_consulta,
                        ),
                    ],
                ),
                self.consulta_resultado_panel,
                self.acciones_consulta,
            ],
        )
        return panel_moderno(contenido, padding=14 if es_movil else 18, expand=True)

    def _ancho_dialogo_fecha(self, es_movil):
        margen = 28 if es_movil else 120
        return min(620, max(220, self._ancho_pantalla_actual() - margen))

    def abrir_consulta_fecha_real(self, e=None):
        es_movil = self._ancho_pantalla_actual() < 700
        ancho = self._ancho_dialogo_fecha(es_movil)
        self._actualizar_resultado_consulta_visible()

        def cerrar(ev=None):
            cerrar_dialogo(self.page, dialog)

        dialog = ft.AlertDialog(
            modal=False,
            title=ft.Text(
                "Consultar fecha real",
                color=TEXTO_PRINCIPAL,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Container(
                width=ancho,
                padding=12 if es_movil else 16,
                border_radius=8,
                bgcolor=SUPERFICIE_PERLADA,
                border=ft.Border.all(1, PERLA_BORDE),
                content=ft.Column(
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                    spacing=10,
                    controls=[
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
                                ft.IconButton(
                                    icon=ft.Icons.TODAY,
                                    tooltip="Usar fecha actual",
                                    on_click=lambda ev: self.usar_ahora(),
                                ),
                                ft.OutlinedButton(
                                    "Guardar",
                                    icon=ft.Icons.SAVE_ALT,
                                    on_click=lambda ev: self.guardar_tiempo(
                                        self.datos_consulta or self.datos_actuales
                                    ),
                                ),
                            ],
                        ),
                        self.consulta_resultado_panel,
                        self.acciones_consulta,
                    ],
                ),
            ),
            actions=[ft.TextButton("Cerrar", on_click=cerrar)],
            actions_alignment=ft.MainAxisAlignment.END,
            inset_padding=ft.Padding(
                8 if es_movil else 24,
                8 if es_movil else 24,
                8 if es_movil else 24,
                8 if es_movil else 24,
            ),
        )
        mostrar_dialogo(self.page, dialog)

    def abrir_consulta_fecha_biblica(self, e=None):
        es_movil = self._ancho_pantalla_actual() < 700
        ancho = self._ancho_dialogo_fecha(es_movil)
        self._actualizar_resultado_biblico_visible()

        def cerrar(ev=None):
            cerrar_dialogo(self.page, dialog)

        dialog = ft.AlertDialog(
            modal=False,
            title=ft.Text(
                "Consultar fecha bíblica",
                color=TEXTO_PRINCIPAL,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Container(
                width=ancho,
                padding=12 if es_movil else 16,
                border_radius=8,
                bgcolor=SUPERFICIE_PERLADA,
                border=ft.Border.all(1, PERLA_BORDE),
                content=ft.Column(
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                    spacing=10,
                    controls=[
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
                        ft.Row(
                            wrap=True,
                            spacing=8,
                            controls=[
                                ft.ElevatedButton(
                                    "Convertir",
                                    icon=ft.Icons.CALENDAR_TODAY,
                                    bgcolor=MARRON_RELOJ_MEDIO,
                                    color=BLANCO,
                                    on_click=self.calcular_fecha_gregoriana,
                                ),
                                ft.OutlinedButton(
                                    "Excel",
                                    icon=ft.Icons.TABLE_CHART,
                                    on_click=self.descargar_convertidor_excel,
                                ),
                            ],
                        ),
                        self.biblica_resultado_panel,
                        self.acciones_biblica,
                    ],
                ),
            ),
            actions=[ft.TextButton("Cerrar", on_click=cerrar)],
            actions_alignment=ft.MainAxisAlignment.END,
            inset_padding=ft.Padding(
                8 if es_movil else 24,
                8 if es_movil else 24,
                8 if es_movil else 24,
                8 if es_movil else 24,
            ),
        )
        mostrar_dialogo(self.page, dialog)

    def _actualizar_resultado_consulta_visible(self):
        visible = bool((self.consulta_resultado.value or "").strip())
        self.consulta_resultado_panel.visible = visible
        self.acciones_consulta.visible = visible

    def _actualizar_resultado_biblico_visible(self):
        visible = bool((self.biblica_resultado.value or "").strip())
        self.biblica_resultado_panel.visible = visible
        self.acciones_biblica.visible = visible

    def _valor_segmentado(self, control, predeterminado):
        seleccion = getattr(control, "selected", None) or []
        return seleccion[0] if seleccion else predeterminado

    def _cambiar_tipo_consulta(self, e=None):
        es_biblico = (
            self._valor_segmentado(self.consulta_calendario, "biblico")
            == "biblico"
        )
        self.consulta_opciones_biblicas.visible = False
        self.consulta_opciones_gregorianas.visible = not es_biblico
        self.consulta_resultado.value = ""
        self._actualizar_resultado_consulta_visible()
        try:
            self.page.update()
        except (RuntimeError, AssertionError):
            pass

    def _partes_fecha_consulta(self):
        valor = (self.consulta_input.value or "").strip()
        partes = valor.split("-")
        if len(partes) != 3:
            raise ValueError("Use el formato DD-MM-AAAA.")
        try:
            dia, mes, anio = [int(parte) for parte in partes]
        except ValueError as error:
            raise ValueError("Use el formato DD-MM-AAAA.") from error
        if anio <= 0:
            raise ValueError("El año debe ser mayor a 0.")
        return dia, mes, anio

    def _fecha_sin_hora(self, fecha):
        if isinstance(fecha, datetime):
            return fecha.strftime("%d-%m-%Y DC")
        return f"{fecha.dia:02d}-{fecha.mes:02d}-{fecha.anio:04d} {fecha.era}"

    def _texto_fecha_biblica(self, anio, mes, dia):
        return f"{dia:02d}-{mes:02d}-{anio:04d} ({MESES_360[mes - 1]})"

    def _avisar_conversion(self):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("Conversión realizada correctamente"),
            duration=1800,
            behavior=ft.SnackBarBehavior.FLOATING,
        )
        self.page.snack_bar.open = True

    def _actualizar_textos(self, animar=True):
        self.datos_actuales = calcular_calendario_360(base_real=self.base_real)
        datos = self.datos_actuales
        valores = {
            "mes": datos["mes"][:3].upper(),
        }
        for prefijo, valor in (
            ("dia", f"{datos['dia_mes']:02d}"),
            ("anio", f"{datos['anio']:04d}"),
            ("hora", f"{datos['hora']:02d}"),
            ("minuto", f"{datos['minuto']:02d}"),
            ("segundo", f"{datos['segundo']:02d}"),
        ):
            for indice, caracter in enumerate(valor):
                valores[f"{prefijo}_{indice}"] = caracter

        cambiadas = []
        for clave, valor in valores.items():
            tarjeta = self._tarjetas_flip.get(clave)
            if tarjeta is None:
                continue
            if animar:
                if tarjeta.preparar_cambio(valor):
                    cambiadas.append(tarjeta)
            else:
                tarjeta.establecer(valor)
        return cambiadas

    def _iniciar_timer(self):
        if self._timer_activo:
            return
        self._timer_activo = True
        if hasattr(self.page, "run_task"):
            self.page.run_task(self._ciclo_reloj)

    def _refrescar_tarjetas_flip(self, tarjetas):
        controles = [tarjeta.control for tarjeta in tarjetas]
        if controles:
            self.page.update(*controles)

    async def _ciclo_reloj(self):
        while self.router.activo == "tiempo":
            cambiadas = self._actualizar_textos(animar=True)
            if cambiadas:
                try:
                    self._refrescar_tarjetas_flip(cambiadas)
                except (RuntimeError, AssertionError):
                    self._timer_activo = False
                    return
                await asyncio.sleep(0.025)
                for tarjeta in cambiadas:
                    tarjeta.iniciar_caida()
                try:
                    self._refrescar_tarjetas_flip(cambiadas)
                except (RuntimeError, AssertionError):
                    self._timer_activo = False
                    return
                await asyncio.sleep(0.24)
                for tarjeta in cambiadas:
                    tarjeta.preparar_reverso()
                try:
                    self._refrescar_tarjetas_flip(cambiadas)
                except (RuntimeError, AssertionError):
                    self._timer_activo = False
                    return
                await asyncio.sleep(0.025)
                for tarjeta in cambiadas:
                    tarjeta.completar_caida()
                try:
                    self._refrescar_tarjetas_flip(cambiadas)
                except (RuntimeError, AssertionError):
                    self._timer_activo = False
                    return
                await asyncio.sleep(0.24)
                for tarjeta in cambiadas:
                    tarjeta.terminar_caida()
                try:
                    self._refrescar_tarjetas_flip(cambiadas)
                except (RuntimeError, AssertionError):
                    self._timer_activo = False
                    return
            espera = max(0.05, 1 - (datetime.now().microsecond / 1_000_000))
            await asyncio.sleep(espera)
        self._timer_activo = False

    def calcular_consulta(self, e=None):
        if not self._puede("tiempo_consultar"):
            return
        if e is not None:
            ocultar_teclado(self.page, e.control)
        try:
            dia, mes, anio = self._partes_fecha_consulta()
            calendario = self._valor_segmentado(
                self.consulta_calendario, "biblico"
            )
            if calendario == "biblico":
                if mes < 1 or mes > 12 or dia < 1 or dia > 30:
                    raise ValueError(
                        "La fecha bíblica admite meses del 1 al 12 y días del 1 al 30."
                    )
                if anio > BASE_ANIO:
                    raise ValueError(
                        f"El calendario bíblico admite años del 1 al {BASE_ANIO}."
                    )
                fecha_exacta = fecha_gregoriana_desde_biblica(anio, mes, dia)
                self.datos_consulta = calcular_calendario_360(
                    fecha_exacta,
                    base_real=self.base_real,
                )
                self.consulta_resultado.value = (
                    f"Bíblico: {self._texto_fecha_biblica(anio, mes, dia)}\n"
                    f"Gregoriano: {self._fecha_sin_hora(fecha_exacta)}"
                )
            else:
                era = self._valor_segmentado(self.consulta_era, "DC")
                fecha = parsear_fecha_consulta(
                    f"{dia:02d}/{mes:02d}/{anio}",
                    era,
                )
                self.datos_consulta = calcular_calendario_360(
                    fecha,
                    base_real=self.base_real,
                )
                datos = self.datos_consulta
                alcance = self._valor_segmentado(
                    self.consulta_alcance, "exacta"
                )
                if alcance == "edades":
                    posicion = ((datos["anio"] - 1) % 2000) + 1
                    edades = (
                        ("Edad del Caos", posicion),
                        ("Edad de las Arenas", posicion + 2000),
                        ("Edad de las Estrellas", posicion + 4000),
                    )
                    lineas = [f"Posición dentro del período: {posicion}/2000"]
                    for nombre, anio_edad in edades:
                        lineas.append(
                            f"{nombre}: "
                            f"{self._texto_fecha_biblica(anio_edad, datos['mes_numero'], datos['dia_mes'])}"
                        )
                    self.consulta_resultado.value = "\n".join(lineas)
                else:
                    self.consulta_resultado.value = (
                        f"Gregoriano: {dia:02d}-{mes:02d}-{anio:04d} {era}\n"
                        "Bíblico: "
                        f"{self._texto_fecha_biblica(datos['anio'], datos['mes_numero'], datos['dia_mes'])}"
                    )
        except ValueError as error:
            self.datos_consulta = None
            self.consulta_resultado.value = str(error)
            self._actualizar_resultado_consulta_visible()
            self.page.update()
            return
        self._actualizar_resultado_consulta_visible()
        self._avisar_conversion()
        self.page.update()

    def usar_ahora(self):
        self.consulta_input.value = datetime.now().strftime("%d-%m-%Y")
        self.consulta_calendario.selected = ["gregoriano"]
        self.consulta_era.selected = ["DC"]
        self._cambiar_tipo_consulta()
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

    def _posicion_linea_tiempo(self, valor, minimo, maximo, ancho, margen=36):
        if maximo <= minimo:
            return margen
        progreso = (valor - minimo) / (maximo - minimo)
        progreso = max(0, min(1, progreso))
        return margen + progreso * max(1, ancho - (margen * 2))

    def _anio_biblico_decimal(self, datos):
        return datos["anio"] + ((datos["dia_anio"] - 1) / 360)

    def _anio_gregoriano_decimal(self, fecha):
        fecha = self._fecha_como_datetime(fecha) or datetime.now()
        inicio = datetime(fecha.year, 1, 1)
        fin = datetime(fecha.year + 1, 1, 1)
        avance = (fecha - inicio).total_seconds()
        total = max(1, (fin - inicio).total_seconds())
        return fecha.year + (avance / total)

    def _fecha_como_datetime(self, fecha):
        if isinstance(fecha, datetime):
            return fecha
        try:
            if getattr(fecha, "era", "DC") != "DC":
                return None
            return datetime(
                fecha.anio,
                fecha.mes,
                fecha.dia,
                getattr(fecha, "hora", 0),
                getattr(fecha, "minuto", 0),
                getattr(fecha, "segundo", 0),
            )
        except (TypeError, ValueError, AttributeError):
            return None

    def _dias_entre_fechas_visibles(self, origen, destino):
        origen_dt = self._fecha_como_datetime(origen)
        destino_dt = self._fecha_como_datetime(destino)
        if origen_dt is None or destino_dt is None:
            return 0
        return (destino_dt.date() - origen_dt.date()).days

    def _control_linea_tiempo(self, izquierda, arriba, ancho, color, alto=6):
        return ft.Container(
            left=izquierda,
            top=arriba,
            width=max(2, ancho),
            height=alto,
            bgcolor=color,
            border_radius=3,
        )

    def _texto_linea_tiempo(self, texto, izquierda, arriba, color, tamano=13, ancho=None, peso=None):
        return ft.Container(
            left=izquierda,
            top=arriba,
            width=ancho,
            content=ft.Text(
                texto,
                size=tamano,
                color=color,
                weight=peso or ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
        )

    def _marca_linea_tiempo(
        self,
        x,
        y,
        color,
        etiqueta=None,
        arriba=True,
        ancho_etiqueta=84,
        tamano_etiqueta=13,
    ):
        controles = [
            ft.Container(
                left=x - 1.5,
                top=y - 12,
                width=3,
                height=27,
                bgcolor=color,
                border_radius=2,
            )
        ]
        if etiqueta:
            controles.append(
                self._texto_linea_tiempo(
                    etiqueta,
                    max(0, x - (ancho_etiqueta / 2)),
                    y - (42 if arriba else -19),
                    color,
                    tamano_etiqueta,
                    ancho_etiqueta,
                )
            )
        return controles

    def _dibujito_apophis_linea_tiempo(self, x, y):
        barras = []
        colores = tuple(COLORES_DIGITOS[str(indice)] for indice in range(10))
        alturas = (30, 33, 36, 39, 42, 42, 39, 36, 33, 30)
        for indice, (color, altura) in enumerate(zip(colores, alturas)):
            barras.append(
                ft.Container(
                    left=7 + (indice * 4.2),
                    top=43 - altura - (indice * 0.8),
                    width=5,
                    height=altura,
                    bgcolor=color,
                    border=ft.Border.all(
                        0.7,
                        "#8A8A8A" if indice in (8, 9) else color,
                    ),
                    border_radius=3,
                    rotate=ft.Rotate(angle=-0.20),
                )
            )
        base = ft.Container(
            left=0,
            top=38,
            width=28,
            height=15,
            bgcolor="#D6A16F",
            border=ft.Border.all(1, "#B97554"),
            border_radius=10,
        )
        return ft.Container(
            left=x - 28,
            top=y,
            width=58,
            height=54,
            tooltip="Apophis · 13/04/2029",
            content=ft.Stack(width=58, height=54, controls=[*barras, base]),
        )

    def _dias_hasta_texto(self, destino, texto):
        dias = (destino.date() - datetime.now().date()).days
        if dias >= 0:
            return f"Faltan {dias} días {texto}"
        return f"Pasaron {abs(dias)} días {texto}"

    def _panel_dato_linea_tiempo(self, titulo, valor, color, ancho=None):
        return ft.Container(
            width=ancho,
            padding=10,
            border_radius=8,
            bgcolor=ft.Colors.with_opacity(0.08, color),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.55, color)),
            content=ft.Column(
                spacing=2,
                controls=[
                    ft.Text(titulo, color=color, size=12, weight=ft.FontWeight.BOLD),
                    ft.Text(valor, color=TEXTO_PRINCIPAL, size=12, selectable=True),
                ],
            ),
        )

    def _crear_grafico_linea_tiempo_anterior(self, modo, fecha_real, datos, ancho, es_movil):
        alto = 440 if not es_movil else 390
        margen = 28 if es_movil else 42
        izquierda = margen
        derecha = ancho - margen
        ancho_linea = derecha - izquierda
        fecha_base_6000 = fecha_gregoriana_desde_biblica(BASE_ANIO, 1, 1)
        fecha_6000_texto = f"{fecha_base_6000.dia:02d}/{fecha_base_6000.mes:02d}/{fecha_base_6000.anio:04d}"
        controles = [
            ft.Container(
                left=0,
                top=0,
                width=ancho,
                height=alto,
                bgcolor="#FFFFFF",
                border_radius=8,
                border=ft.Border.all(2, LINEA_TIEMPO_MARRON),
            )
        ]

        if modo == "actual":
            y_biblico = 126 if es_movil else 145
            y_violeta = 235 if es_movil else 275
            y_gregoriano = 300 if es_movil else 345
            controles.extend(
                [
                    self._texto_linea_tiempo("EDAD DEL CAOS", izquierda - 6, 26, LINEA_TIEMPO_MARRON, 11 if es_movil else 14, 120),
                    self._texto_linea_tiempo("EDAD DE LAS ARENAS", ancho * 0.30, 26, LINEA_TIEMPO_ROJO, 11 if es_movil else 14, 165),
                    self._texto_linea_tiempo("EDAD DE LAS ESTRELLAS", ancho * 0.63, 26, LINEA_TIEMPO_AMARILLO, 11 if es_movil else 14, 185),
                    self._control_linea_tiempo(izquierda, y_biblico, ancho_linea, LINEA_TIEMPO_MARRON),
                    self._control_linea_tiempo(izquierda, y_violeta, ancho_linea, LINEA_TIEMPO_VIOLETA),
                    self._control_linea_tiempo(izquierda, y_gregoriano, ancho_linea, LINEA_TIEMPO_VERDE),
                ]
            )
            for valor, etiqueta in ((1, "1"), (2000, "2000"), (4000, "4000"), (6000, "6000")):
                x = self._posicion_linea_tiempo(valor, 1, BASE_ANIO, ancho, margen)
                controles.extend(self._marca_linea_tiempo(x, y_biblico, LINEA_TIEMPO_MARRON, etiqueta))

            x_biblico = self._posicion_linea_tiempo(self._anio_biblico_decimal(datos), 1, BASE_ANIO, ancho, margen)
            x_gregoriano = self._posicion_linea_tiempo(self._anio_gregoriano_decimal(fecha_real), 1, FECHA_APOPHIS.year, ancho, margen)
            inicio_violeta = datetime(2024, 1, 1)
            total_violeta = max(1, (FECHA_APOPHIS - inicio_violeta).total_seconds())
            avance_violeta = (fecha_real - inicio_violeta).total_seconds() / total_violeta
            x_violeta = izquierda + max(0, min(1, avance_violeta)) * ancho_linea
            x_llegada = self._posicion_linea_tiempo(BASE_ANIO, 1, BASE_ANIO, ancho, margen)

            controles.extend(
                [
                    self._texto_linea_tiempo("usted se encuentra aquí", max(0, x_biblico - 82), y_biblico - 76, LINEA_TIEMPO_ROJO, 11, 164),
                    ft.Icon(ft.Icons.ARROW_DROP_DOWN, color=LINEA_TIEMPO_ROJO, size=44, left=x_biblico - 22, top=y_biblico - 66),
                    self._texto_linea_tiempo(f"{datos['anio']}", max(0, x_biblico - 38), y_biblico + 22, LINEA_TIEMPO_ROJO, 18, 76),
                    self._texto_linea_tiempo(formatear_fecha_real(fecha_real), max(0, x_biblico - 94), y_biblico - 44, LINEA_TIEMPO_ROJO, 12, 188),
                    *self._marca_linea_tiempo(x_violeta, y_violeta, LINEA_TIEMPO_VIOLETA, "hoy", False),
                    *self._marca_linea_tiempo(x_llegada, y_violeta, ft.Colors.BLACK, "13/04/2029", True),
                    self._texto_linea_tiempo("6000 + 2 días", max(0, x_llegada - 54), y_violeta - 48, ft.Colors.BLACK, 12, 108),
                    ft.Icon(ft.Icons.ARROW_DROP_UP, color=LINEA_TIEMPO_VERDE, size=54, left=x_gregoriano - 27, top=y_gregoriano + 6),
                    self._texto_linea_tiempo(formatear_fecha_real(fecha_real), max(0, x_gregoriano - 88), y_gregoriano + 60, LINEA_TIEMPO_VERDE, 12, 176),
                    self._texto_linea_tiempo("ANTES DE CRISTO", izquierda, y_gregoriano - 28, LINEA_TIEMPO_VERDE, 12, ancho_linea / 2),
                    self._texto_linea_tiempo("DESPUÉS DE CRISTO", izquierda + (ancho_linea / 2), y_gregoriano - 28, LINEA_TIEMPO_VERDE, 12, ancho_linea / 2),
                ]
            )
            x_ano_6000 = self._posicion_linea_tiempo(BASE_ANIO, 1, BASE_ANIO, ancho, margen)
            controles.extend(self._marca_linea_tiempo(x_ano_6000, y_biblico, LINEA_TIEMPO_MARRON, fecha_6000_texto, False))
        else:
            eras = {
                "caos": ("EDAD DEL CAOS", 1, 2000, LINEA_TIEMPO_MARRON),
                "arenas": ("EDAD DE LAS ARENAS", 2000, 4000, LINEA_TIEMPO_ROJO),
                "estrellas": ("EDAD DE LAS ESTRELLAS", 4000, 6000, LINEA_TIEMPO_AMARILLO),
            }
            titulo, inicio, fin, color = eras.get(modo, eras["arenas"])
            y_biblico = 160 if es_movil else 175
            y_gregoriano = 260 if es_movil else 300
            inicio_real = fecha_gregoriana_desde_biblica(inicio, 1, 1)
            fin_real = fecha_gregoriana_desde_biblica(fin, 12, 30)
            x_inicio = self._posicion_linea_tiempo(inicio, inicio, fin, ancho, margen)
            x_fin = self._posicion_linea_tiempo(fin, inicio, fin, ancho, margen)
            x_biblico = self._posicion_linea_tiempo(self._anio_biblico_decimal(datos), inicio, fin, ancho, margen)
            controles.extend(
                [
                    self._texto_linea_tiempo(titulo, ancho * 0.26, 42, color, 14 if es_movil else 17, ancho * 0.48),
                    self._control_linea_tiempo(izquierda, y_biblico, ancho_linea, LINEA_TIEMPO_MARRON),
                    self._control_linea_tiempo(izquierda, y_gregoriano, ancho_linea, LINEA_TIEMPO_VERDE),
                    *self._marca_linea_tiempo(x_inicio, y_biblico, color, str(inicio)),
                    *self._marca_linea_tiempo(x_fin, y_biblico, color, str(fin)),
                    self._texto_linea_tiempo(
                        f"{formatear_fecha_real(inicio_real)}  a  {formatear_fecha_real(fin_real)}",
                        izquierda,
                        y_gregoriano + 34,
                        LINEA_TIEMPO_VERDE,
                        11 if es_movil else 12,
                        ancho_linea,
                    ),
                ]
            )
            if inicio <= datos["anio"] <= fin:
                controles.extend(
                    [
                        ft.Icon(ft.Icons.ARROW_DROP_DOWN, color=color, size=42, left=x_biblico - 21, top=y_biblico - 64),
                        self._texto_linea_tiempo(f"{datos['anio']}", max(0, x_biblico - 38), y_biblico + 24, color, 15, 76),
                    ]
                )
            else:
                controles.append(
                    self._texto_linea_tiempo(
                        "La fecha seleccionada queda fuera de esta era",
                        izquierda,
                        y_biblico + 32,
                        TEXTO_SECUNDARIO,
                        11,
                        ancho_linea,
                    )
                )

        return ft.Container(
            width=ancho,
            height=alto,
            content=ft.Stack(width=ancho, height=alto, controls=controles),
        )

    def _tarjeta_fecha_linea_tiempo(self, x, y, ancho, fecha_real, datos, color):
        ancho_tarjeta = min(176, max(132, ancho * 0.24))
        izquierda = max(10, min(ancho - ancho_tarjeta - 10, x - (ancho_tarjeta / 2)))
        return ft.Container(
            left=izquierda,
            top=y,
            width=ancho_tarjeta,
            padding=ft.Padding(8, 6, 8, 6),
            bgcolor=SUPERFICIE_PERLADA,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.55, color)),
            border_radius=8,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.10, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
            content=ft.Column(
                spacing=1,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        f"Año bíblico {datos['anio']}\n"
                        f"{datos['mes']} · día {datos['dia_mes']} "
                        f"(mes {datos['mes_numero']})",
                        size=10,
                        color=color,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            ),
        )

    def _texto_edad_linea_tiempo(self, texto, izquierda, ancho, color, activo):
        return ft.Container(
            left=izquierda,
            top=18,
            width=ancho,
            padding=ft.Padding(3, 2, 3, 2),
            border_radius=4,
            bgcolor=ft.Colors.with_opacity(0.11 if activo else 0.045, color),
            content=ft.Text(
                texto,
                size=9,
                color=color,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
        )

    def _crear_grafico_linea_tiempo(
        self,
        modo,
        fecha_real,
        datos,
        ancho,
        es_movil,
        al_elegir_edad=None,
        al_mover_fecha=None,
        al_ir_anio_redondo=None,
    ):
        alto = 285 if es_movil else 340
        margen = 16 if es_movil else 30
        izquierda = margen
        derecha = ancho - margen
        ancho_linea = max(1, derecha - izquierda)
        x_6000_visual = derecha - (18 if es_movil else 32)
        ancho_biblico = x_6000_visual + margen if modo == "actual" else ancho
        ancho_marca = 32 if es_movil else 72
        tamano_marca = 9 if es_movil else 11
        eras = {
            "caos": ("EDAD DEL CAOS", 1, 2000, LINEA_TIEMPO_MARRON),
            "arenas": ("EDAD DE LAS ARENAS", 2001, 4000, LINEA_TIEMPO_ROJO),
            "estrellas": ("EDAD DE LAS ESTRELLAS", 4001, BASE_ANIO, LINEA_TIEMPO_AMARILLO),
        }
        inicio, fin = 1, BASE_ANIO
        color_activo = LINEA_TIEMPO_ROJO
        if modo in eras:
            _, inicio, fin, color_activo = eras[modo]

        y_linea = 118 if es_movil else 160
        y_real = y_linea + 84
        ancho_fecha_real = min(188, ancho_linea)
        x_actual = self._posicion_linea_tiempo(
            self._anio_biblico_decimal(datos),
            inicio,
            fin,
            ancho_biblico if modo == "actual" else ancho,
            margen,
        )
        controles = [
            ft.Container(
                left=0,
                top=0,
                width=ancho,
                height=alto,
                bgcolor=SUPERFICIE_PERLADA,
                border_radius=8,
                border=ft.Border.all(1, PERLA_BORDE),
            )
        ]

        if modo == "actual":
            for clave, (titulo, edad_inicio, edad_fin, color) in eras.items():
                x_inicio = self._posicion_linea_tiempo(edad_inicio, 1, BASE_ANIO, ancho_biblico, margen)
                x_fin = self._posicion_linea_tiempo(edad_fin, 1, BASE_ANIO, ancho_biblico, margen)
                controles.append(
                    self._texto_edad_linea_tiempo(
                        titulo,
                        x_inicio,
                        max(50, x_fin - x_inicio),
                        color,
                        False,
                    )
                )
                controles.append(
                    self._control_linea_tiempo(x_inicio, y_linea, max(2, x_fin - x_inicio), color, 3)
                )
                controles.extend(
                    self._marca_linea_tiempo(
                        x_inicio,
                        y_linea,
                        color,
                        str(edad_inicio),
                        False,
                        ancho_marca,
                        tamano_marca,
                    )
                )
            controles.extend(
                [
                    *self._marca_linea_tiempo(
                        x_6000_visual,
                        y_linea,
                        LINEA_TIEMPO_AMARILLO,
                        str(BASE_ANIO),
                        False,
                        ancho_marca,
                        tamano_marca,
                    ),
                ]
            )
            if not es_movil:
                paneles_izquierda = x_actual > derecha - 320
                panel_dias_6000_x = izquierda if paneles_izquierda else max(izquierda, derecha - 272)
                controles.extend(
                    [
                        ft.Container(
                            left=panel_dias_6000_x,
                            top=52,
                            width=242,
                            padding=ft.Padding(10, 7, 10, 7),
                            border=ft.Border.all(1, ft.Colors.with_opacity(0.75, LINEA_TIEMPO_MARRON)),
                            border_radius=6,
                            bgcolor=SUPERFICIE_PERLADA,
                            content=ft.Text(
                                self._dias_hasta_texto(datetime(2029, 4, 11), "para el año 6000 bíblico"),
                                size=11,
                                color=LINEA_TIEMPO_MARRON,
                                weight=ft.FontWeight.BOLD,
                            ),
                        ),
                    ]
                )
        else:
            titulo, _, _, color = eras[modo]
            if not es_movil:
                controles.append(
                    ft.GestureDetector(
                        mouse_cursor=ft.MouseCursor.CLICK,
                        on_tap=lambda ev: al_elegir_edad("actual") if callable(al_elegir_edad) else None,
                        left=izquierda,
                        top=18,
                        content=ft.Container(
                            padding=ft.Padding(5, 3, 5, 3),
                            border_radius=6,
                            bgcolor=ft.Colors.with_opacity(0.07, TEXTO_SECUNDARIO),
                            content=ft.Row(
                                tight=True,
                                spacing=3,
                                controls=[
                                    ft.Icon(ft.Icons.ARROW_BACK, size=14, color=TEXTO_SECUNDARIO),
                                    ft.Text("Todas las edades", size=10, color=TEXTO_SECUNDARIO),
                                ],
                            ),
                        ),
                    )
                )
                controles.append(
                    self._texto_linea_tiempo(
                        titulo,
                        ancho * 0.28,
                        24,
                        color,
                        14,
                        ancho * 0.44,
                    )
                )
            controles.extend(
                [
                    self._control_linea_tiempo(izquierda, y_linea, ancho_linea, color, 3),
                    *self._marca_linea_tiempo(izquierda, y_linea, color, str(inicio), False, ancho_marca, tamano_marca),
                    *self._marca_linea_tiempo(derecha, y_linea, color, str(fin), False, ancho_marca, tamano_marca),
                ]
            )

        tarjeta_fecha = self._tarjeta_fecha_linea_tiempo(
            x_actual,
            40 if es_movil else 72,
            ancho,
            fecha_real,
            datos,
            color_activo,
        )
        flecha_biblica = ft.Icon(
            ft.Icons.ARROW_DROP_DOWN,
            color=color_activo,
            size=30,
            left=x_actual - 15,
            top=y_linea - 32,
        )
        marca_biblica = ft.Container(
            left=x_actual - 1,
            top=y_linea - 8,
            width=2,
            height=20,
            bgcolor=color_activo,
            border_radius=1,
        )
        flecha_gregoriana = ft.Icon(
            ft.Icons.ARROW_DROP_UP,
            color=LINEA_TIEMPO_VERDE,
            size=34,
            left=x_actual - 17,
            top=y_real + 2,
        )
        fecha_gregoriana_texto = self._texto_linea_tiempo(
            formatear_fecha_real(fecha_real),
            max(
                izquierda,
                min(derecha - ancho_fecha_real, x_actual - (ancho_fecha_real / 2)),
            ),
            y_real + 38,
            TEXTO_SECUNDARIO,
            9 if es_movil else 10,
            ancho_fecha_real,
            ft.FontWeight.W_500,
        )
        controles.extend(
            [
                tarjeta_fecha,
                flecha_biblica,
                marca_biblica,
                self._control_linea_tiempo(
                    izquierda,
                    y_real,
                    ancho_linea,
                    LINEA_TIEMPO_VERDE,
                    3,
                ),
                flecha_gregoriana,
                fecha_gregoriana_texto,
                self._texto_linea_tiempo(
                    "Calendario gregoriano",
                    izquierda,
                    y_real + 57,
                    LINEA_TIEMPO_VERDE,
                    10,
                    ancho_linea,
                    ft.FontWeight.W_500,
                ),
            ]
        )

        def actualizar_indicadores(fecha_nueva, datos_nuevos):
            x_nuevo = self._posicion_linea_tiempo(
                self._anio_biblico_decimal(datos_nuevos),
                inicio,
                fin,
                ancho_biblico if modo == "actual" else ancho,
                margen,
            )
            tarjeta_fecha.left = max(
                10,
                min(
                    ancho - tarjeta_fecha.width - 10,
                    x_nuevo - (tarjeta_fecha.width / 2),
                ),
            )
            tarjeta_fecha.content.controls[0].value = (
                f"Año bíblico {datos_nuevos['anio']}\n"
                f"{datos_nuevos['mes']} · día {datos_nuevos['dia_mes']} "
                f"(mes {datos_nuevos['mes_numero']})"
            )
            flecha_biblica.left = x_nuevo - 15
            marca_biblica.left = x_nuevo - 1
            flecha_gregoriana.left = x_nuevo - 17
            fecha_gregoriana_texto.left = max(
                izquierda,
                min(
                    derecha - ancho_fecha_real,
                    x_nuevo - (ancho_fecha_real / 2),
                ),
            )
            fecha_gregoriana_texto.content.value = formatear_fecha_real(fecha_nueva)
            try:
                lienzo.update()
            except RuntimeError:
                pass

        def mover_desde_evento(ev, permitir_accesos_directos=False):
            posicion = getattr(ev, "local_position", None)
            x = getattr(posicion, "x", None)
            y = getattr(posicion, "y", None)
            if x is None:
                x = getattr(ev, "local_x", None)
            if y is None:
                y = getattr(ev, "local_y", None)
            if x is None:
                return
            if permitir_accesos_directos and modo == "actual" and y is not None and 12 <= y <= 66:
                progreso = max(0, min(1, (float(x) - margen) / ancho_linea))
                for clave, (_, edad_inicio, edad_fin, _) in eras.items():
                    if edad_inicio <= 1 + ((BASE_ANIO - 1) * progreso) <= edad_fin:
                        if callable(al_elegir_edad):
                            al_elegir_edad(clave)
                        return
            if permitir_accesos_directos and modo == "actual" and y is not None and y_linea - 56 <= y <= y_linea + 72:
                for anio_redondo in (1, 2000, 4000, BASE_ANIO):
                    x_redondo = self._posicion_linea_tiempo(
                        anio_redondo,
                        1,
                        BASE_ANIO,
                        ancho_biblico,
                        margen,
                    )
                    if abs(float(x) - x_redondo) <= (18 if es_movil else 24):
                        if callable(al_ir_anio_redondo):
                            al_ir_anio_redondo(anio_redondo)
                        return
            if callable(al_mover_fecha):
                resultado = al_mover_fecha(
                    x,
                    inicio,
                    fin,
                    margen,
                    ancho_biblico if modo == "actual" else ancho,
                )
                if resultado:
                    actualizar_indicadores(*resultado)

        def mover_al_tocar(ev):
            cambiar_cursor(ft.MouseCursor.CLICK)
            mover_desde_evento(ev, permitir_accesos_directos=True)

        def iniciar_arrastre(ev):
            cambiar_cursor(ft.MouseCursor.GRABBING)
            mover_desde_evento(ev, permitir_accesos_directos=False)

        def continuar_arrastre(ev):
            cambiar_cursor(ft.MouseCursor.GRABBING)
            mover_desde_evento(ev, permitir_accesos_directos=False)

        def finalizar_arrastre(ev=None):
            cambiar_cursor(ft.MouseCursor.GRAB)

        def cambiar_cursor(cursor):
            if detector.mouse_cursor == cursor:
                return
            detector.mouse_cursor = cursor
            try:
                detector.update()
            except RuntimeError:
                pass

        lienzo = ft.Container(
            width=ancho,
            height=alto,
            content=ft.Stack(width=ancho, height=alto, controls=controles),
        )
        detector = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.GRAB,
            drag_interval=20,
            on_tap=mover_al_tocar,
            on_tap_move=iniciar_arrastre,
            on_double_tap_down=mover_al_tocar,
            on_tap_cancel=finalizar_arrastre,
            on_pan_down=iniciar_arrastre,
            on_pan_start=iniciar_arrastre,
            on_pan_update=continuar_arrastre,
            on_pan_end=finalizar_arrastre,
            on_pan_cancel=finalizar_arrastre,
            on_exit=finalizar_arrastre,
            width=ancho,
            height=alto,
            content=lienzo,
        )
        return detector

    def abrir_lineas_tiempo_anterior(self, e=None):
        es_movil = self._ancho_pantalla_actual() < 700
        ancho = max(300, min(980, self._ancho_pantalla_actual() - (24 if es_movil else 120)))
        alto = 650 if es_movil else 690
        fecha_estado = {"valor": datetime.now().replace(microsecond=0)}
        modo_estado = {"valor": "actual"}

        grafico = ft.Container()
        resumen = ft.Row(wrap=True, spacing=8, run_spacing=8)
        fecha_texto = ft.Text("", color=DORADO, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
        modo_selector = ft.Dropdown(
            label="Vista",
            value="actual",
            width=220 if es_movil else 260,
            dense=True,
            options=[
                ft.dropdown.Option("actual", "Actual"),
                ft.dropdown.Option("caos", "Edad del Caos"),
                ft.dropdown.Option("arenas", "Edad de las Arenas"),
                ft.dropdown.Option("estrellas", "Edad de las Estrellas"),
            ],
        )

        def renderizar(actualizar=True):
            datos = calcular_calendario_360(fecha_estado["valor"], base_real=self.base_real)
            grafico.content = self._crear_grafico_linea_tiempo(
                modo_estado["valor"],
                fecha_estado["valor"],
                datos,
                ancho,
                es_movil,
            )
            fecha_texto.value = (
                f"{formatear_fecha_real(fecha_estado['valor'])}  |  "
                f"Año bíblico {datos['anio']}, {datos['mes']} {datos['dia_mes']}/30"
            )
            ancho_panel = ancho if es_movil else (ancho - 24) / 3
            resumen.controls = [
                self._panel_dato_linea_tiempo(
                    "Calendario gregoriano",
                    formatear_fecha_real(fecha_estado["valor"]),
                    LINEA_TIEMPO_VERDE,
                    ancho_panel,
                ),
                self._panel_dato_linea_tiempo(
                    "Calendario bíblico",
                    f"Año {datos['anio']} · mes {datos['mes_numero']} · día {datos['dia_mes']} · día del año {datos['dia_anio']}/360",
                    LINEA_TIEMPO_MARRON,
                    ancho_panel,
                ),
                self._panel_dato_linea_tiempo(
                    "Llegadas",
                    (
                        f"{self._dias_hasta_texto(datetime(2029, 4, 11), 'para el año 6000')} · "
                        f"{self._dias_hasta_texto(FECHA_APOPHIS, 'para Apophis')}"
                    ),
                    LINEA_TIEMPO_VIOLETA,
                    ancho_panel,
                ),
            ]
            if actualizar:
                self.page.update()

        def volver_hoy(ev=None):
            fecha_estado["valor"] = datetime.now().replace(microsecond=0)
            renderizar()

        def cambiar_modo(ev=None):
            modo_estado["valor"] = modo_selector.value or "actual"
            renderizar()

        modo_selector.on_select = cambiar_modo
        renderizar(False)

        def cerrar(ev=None):
            cerrar_dialogo(self.page, dialog)

        dialog = ft.AlertDialog(
            modal=False,
            title=ft.Row(
                wrap=True,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("Líneas de tiempo", color=DORADO, weight=ft.FontWeight.BOLD),
                    modo_selector,
                ],
            ),
            content=ft.Container(
                width=ancho,
                height=alto,
                padding=10 if es_movil else 14,
                bgcolor=SUPERFICIE_PERLADA,
                border_radius=8,
                border=ft.Border.all(1, PERLA_BORDE),
                content=ft.Column(
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Row(
                            wrap=True,
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=4,
                            controls=[
                                ft.Container(width=min(ancho - 96, 560), content=fecha_texto),
                                ft.IconButton(
                                    icon=ft.Icons.TODAY,
                                    tooltip="Volver a hoy",
                                    icon_color=LINEA_TIEMPO_VERDE,
                                    on_click=volver_hoy,
                                ),
                            ],
                        ),
                        grafico,
                        resumen,
                    ],
                ),
            ),
            actions=[ft.TextButton("Cerrar", on_click=cerrar)],
            actions_alignment=ft.MainAxisAlignment.END,
            inset_padding=ft.Padding(8 if es_movil else 24, 8 if es_movil else 24, 8 if es_movil else 24, 8 if es_movil else 24),
        )
        mostrar_dialogo(self.page, dialog)

    def _crear_grafico_apofis(
        self,
        fecha_real,
        datos,
        ancho,
        es_movil,
        al_mover_fecha=None,
    ):
        alto = 260 if es_movil else 280
        margen = 18 if es_movil else 30
        izquierda = margen
        derecha = ancho - margen
        ancho_linea = max(1, derecha - izquierda)
        y_linea = 154 if es_movil else 164
        total_segundos = max(
            1,
            (FECHA_APOPHIS - FECHA_INICIO_APOPHIS).total_seconds(),
        )

        def posicion_fecha(fecha):
            progreso = (
                (fecha - FECHA_INICIO_APOPHIS).total_seconds() / total_segundos
            )
            progreso = max(0, min(1, progreso))
            return izquierda + (progreso * ancho_linea)

        x_actual = posicion_fecha(fecha_real)
        ancho_tarjeta = min(210, max(146, ancho * 0.48))
        tarjeta_fecha_real = ft.Text(
            formatear_fecha_real(fecha_real),
            size=10 if es_movil else 11,
            color=TEXTO_PRINCIPAL,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )
        tarjeta_fecha_biblica = ft.Text(
            f"Año bíblico {datos['anio']} · {datos['mes_numero']}/{datos['dia_mes']}",
            size=9 if es_movil else 10,
            color=LINEA_TIEMPO_VIOLETA,
            text_align=ft.TextAlign.CENTER,
        )
        tarjeta = ft.Container(
            left=max(
                8,
                min(ancho - ancho_tarjeta - 8, x_actual - (ancho_tarjeta / 2)),
            ),
            top=48,
            width=ancho_tarjeta,
            padding=ft.Padding(8, 6, 8, 6),
            bgcolor=SUPERFICIE_PERLADA,
            border=ft.Border.all(
                1,
                ft.Colors.with_opacity(0.60, LINEA_TIEMPO_VIOLETA),
            ),
            border_radius=6,
            content=ft.Column(
                spacing=1,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[tarjeta_fecha_real, tarjeta_fecha_biblica],
            ),
        )
        progreso_linea = self._control_linea_tiempo(
            izquierda,
            y_linea,
            max(2, x_actual - izquierda),
            LINEA_TIEMPO_VIOLETA,
            3,
        )
        icono_apofis = self._dibujito_apophis_linea_tiempo(
            max(28, min(ancho - 30, x_actual)),
            y_linea - 57,
        )
        marca_actual = ft.Container(
            left=x_actual - 1.5,
            top=y_linea - 8,
            width=3,
            height=18,
            bgcolor=LINEA_TIEMPO_VIOLETA,
            border_radius=2,
        )
        datos_inicio = calcular_calendario_360(
            FECHA_INICIO_APOPHIS,
            base_real=self.base_real,
        )
        datos_fin = calcular_calendario_360(
            FECHA_APOPHIS,
            base_real=self.base_real,
        )
        ancho_extremo = ancho_linea / 2
        controles = [
            ft.Container(
                left=0,
                top=0,
                width=ancho,
                height=alto,
                bgcolor=SUPERFICIE_PERLADA,
                border=ft.Border.all(1, PERLA_BORDE),
                border_radius=8,
            ),
            self._texto_linea_tiempo(
                "TRAYECTO DE APOFIS",
                izquierda,
                18,
                LINEA_TIEMPO_VIOLETA,
                10 if es_movil else 12,
                ancho_linea,
            ),
            tarjeta,
            self._control_linea_tiempo(
                izquierda,
                y_linea,
                ancho_linea,
                ft.Colors.with_opacity(0.22, LINEA_TIEMPO_VIOLETA),
                3,
            ),
            progreso_linea,
            ft.Container(
                left=izquierda - 1.5,
                top=y_linea - 8,
                width=3,
                height=18,
                bgcolor=LINEA_TIEMPO_MARRON,
                border_radius=2,
            ),
            ft.Container(
                left=derecha - 1.5,
                top=y_linea - 8,
                width=3,
                height=18,
                bgcolor=LINEA_TIEMPO_VIOLETA,
                border_radius=2,
            ),
            icono_apofis,
            marca_actual,
            self._texto_linea_tiempo(
                "19/06/2004\n"
                f"Año {datos_inicio['anio']} · {datos_inicio['mes_numero']}/{datos_inicio['dia_mes']}",
                izquierda,
                y_linea + 18,
                LINEA_TIEMPO_MARRON,
                8 if es_movil else 9,
                ancho_extremo,
                ft.FontWeight.W_500,
            ),
            self._texto_linea_tiempo(
                "13/04/2029\n"
                f"Año {datos_fin['anio']} · {datos_fin['mes_numero']}/{datos_fin['dia_mes']}",
                izquierda + ancho_extremo,
                y_linea + 18,
                LINEA_TIEMPO_VIOLETA,
                8 if es_movil else 9,
                ancho_extremo,
                ft.FontWeight.W_500,
            ),
            self._texto_linea_tiempo(
                "Dos días después del inicio del año bíblico 6000",
                izquierda,
                y_linea + 68,
                TEXTO_SECUNDARIO,
                8 if es_movil else 9,
                ancho_linea,
                ft.FontWeight.W_500,
            ),
        ]

        def actualizar_indicador(fecha_nueva, datos_nuevos):
            x_nuevo = posicion_fecha(fecha_nueva)
            progreso_linea.width = max(2, x_nuevo - izquierda)
            marca_actual.left = x_nuevo - 1.5
            icono_apofis.left = max(0, min(ancho - icono_apofis.width, x_nuevo - 28))
            tarjeta.left = max(
                8,
                min(
                    ancho - ancho_tarjeta - 8,
                    x_nuevo - (ancho_tarjeta / 2),
                ),
            )
            tarjeta_fecha_real.value = formatear_fecha_real(fecha_nueva)
            tarjeta_fecha_biblica.value = (
                f"Año bíblico {datos_nuevos['anio']} · "
                f"{datos_nuevos['mes_numero']}/{datos_nuevos['dia_mes']}"
            )
            try:
                lienzo.update()
            except RuntimeError:
                pass

        def mover_desde_evento(ev):
            posicion = getattr(ev, "local_position", None)
            x = getattr(posicion, "x", None)
            if x is None:
                x = getattr(ev, "local_x", None)
            if x is None or not callable(al_mover_fecha):
                return
            resultado = al_mover_fecha(
                max(izquierda, min(derecha, float(x))),
                izquierda,
                derecha,
            )
            if resultado:
                actualizar_indicador(*resultado)

        def mover_al_tocar(ev):
            cambiar_cursor(ft.MouseCursor.CLICK)
            mover_desde_evento(ev)

        def iniciar_arrastre(ev):
            cambiar_cursor(ft.MouseCursor.GRABBING)
            mover_desde_evento(ev)

        def continuar_arrastre(ev):
            cambiar_cursor(ft.MouseCursor.GRABBING)
            mover_desde_evento(ev)

        def finalizar_arrastre(ev=None):
            cambiar_cursor(ft.MouseCursor.GRAB)

        def cambiar_cursor(cursor):
            if detector.mouse_cursor == cursor:
                return
            detector.mouse_cursor = cursor
            try:
                detector.update()
            except RuntimeError:
                pass

        lienzo = ft.Container(
            width=ancho,
            height=alto,
            content=ft.Stack(width=ancho, height=alto, controls=controles),
        )
        detector = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.GRAB,
            drag_interval=20,
            on_tap=mover_al_tocar,
            on_tap_move=iniciar_arrastre,
            on_tap_cancel=finalizar_arrastre,
            on_pan_down=iniciar_arrastre,
            on_pan_start=iniciar_arrastre,
            on_pan_update=continuar_arrastre,
            on_pan_end=finalizar_arrastre,
            on_pan_cancel=finalizar_arrastre,
            on_exit=finalizar_arrastre,
            width=ancho,
            height=alto,
            content=lienzo,
        )
        return detector

    def abrir_lineas_tiempo(self, e=None):
        def calcular_dimensiones(ancho_pantalla, alto_pantalla=None):
            movil = ancho_pantalla < 700
            disponible = ancho_pantalla - (16 if movil else 60)
            ancho_dialogo_local = max(
                190 if movil else 560,
                min(1040, disponible),
            )
            ancho_carril_local = max(
                170 if movil else 520,
                ancho_dialogo_local - (20 if movil else 28),
            )
            ancho_grafico_local = ancho_carril_local
            alto_base = 460 if movil else 420
            alto_dialogo_local = (
                max(300, min(alto_base, alto_pantalla - 150))
                if alto_pantalla
                else alto_base
            )
            return (
                movil,
                ancho_dialogo_local,
                ancho_carril_local,
                ancho_grafico_local,
                alto_dialogo_local,
            )

        alto_pantalla = self._alto_ultimo_resize or getattr(self.page, "height", None)
        es_movil, ancho_dialogo, ancho_carril, ancho, alto = calcular_dimensiones(
            self._ancho_pantalla_actual(),
            alto_pantalla,
        )
        fecha_estado = {"valor": datetime.now().replace(microsecond=0)}
        edades_orden = ("caos", "arenas", "estrellas")
        edades_datos = {
            "caos": ("Edad del Caos", "1-2000", LINEA_TIEMPO_MARRON),
            "arenas": ("Edad de las Arenas", "2001-4000", LINEA_TIEMPO_ROJO),
            "estrellas": ("Edad de las Estrellas", "4001-6000", LINEA_TIEMPO_AMARILLO),
        }

        def edad_de_anio(anio):
            if anio <= 2000:
                return "caos"
            if anio <= 4000:
                return "arenas"
            return "estrellas"

        datos_iniciales = calcular_calendario_360(
            fecha_estado["valor"], base_real=self.base_real
        )
        modo_estado = {
            "valor": edad_de_anio(datos_iniciales["anio"]) if es_movil else "actual"
        }
        grafico = ft.Container(width=ancho)
        carril = ft.Row(
            width=ancho_carril,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[grafico],
        )
        edad_etiqueta = ft.Text(
            "",
            size=12,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )
        edad_anterior = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            tooltip="Edad anterior",
        )
        edad_siguiente = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT,
            tooltip="Edad siguiente",
        )
        navegador_edades = ft.Container(
            visible=es_movil,
            width=ancho_carril,
            padding=ft.Padding(4, 2, 4, 2),
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=8,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    edad_anterior,
                    ft.Container(expand=True, alignment=ft.Alignment(0, 0), content=edad_etiqueta),
                    edad_siguiente,
                ],
            ),
        )

        def mover_a_posicion(x, inicio, fin, margen, ancho_grafico):
            ancho_util = max(1, ancho_grafico - (margen * 2))
            progreso = max(0, min(1, (float(x) - margen) / ancho_util))
            dias = int(round((fin - inicio) * 360 * progreso))
            anio = min(fin, inicio + (dias // 360))
            dia_anio = (dias % 360) + 1
            mes = ((dia_anio - 1) // 30) + 1
            dia = ((dia_anio - 1) % 30) + 1
            nueva_fecha = fecha_gregoriana_desde_biblica(anio, mes, dia)
            if formatear_fecha_real(nueva_fecha) == formatear_fecha_real(fecha_estado["valor"]):
                return
            fecha_estado["valor"] = nueva_fecha
            datos_nuevos = calcular_calendario_360(
                nueva_fecha,
                base_real=self.base_real,
            )
            return nueva_fecha, datos_nuevos

        def refrescar_navegador(actualizar=False):
            modo = modo_estado["valor"]
            if modo not in edades_orden:
                datos = calcular_calendario_360(
                    fecha_estado["valor"], base_real=self.base_real
                )
                modo = edad_de_anio(datos["anio"])
            indice = edades_orden.index(modo)
            titulo, rango, color = edades_datos[modo]
            edad_etiqueta.value = f"{titulo}\n{rango}"
            edad_etiqueta.color = color
            edad_anterior.disabled = indice == 0
            edad_siguiente.disabled = indice == len(edades_orden) - 1
            if actualizar:
                try:
                    navegador_edades.update()
                except (RuntimeError, AssertionError):
                    pass

        def elegir_edad(modo):
            rangos = {
                "caos": (1, 2000),
                "arenas": (2001, 4000),
                "estrellas": (4001, BASE_ANIO),
            }
            if modo in rangos:
                datos_actuales = calcular_calendario_360(
                    fecha_estado["valor"], base_real=self.base_real
                )
                inicio, fin = rangos[modo]
                if not inicio <= datos_actuales["anio"] <= fin:
                    posicion_periodo = (datos_actuales["anio"] - 1) % 2000
                    anio_equivalente = min(fin, inicio + posicion_periodo)
                    fecha_estado["valor"] = fecha_gregoriana_desde_biblica(
                        anio_equivalente,
                        datos_actuales["mes_numero"],
                        datos_actuales["dia_mes"],
                    )
            modo_estado["valor"] = modo
            refrescar_navegador(actualizar=True)
            renderizar()

        def mover_edad(pasos):
            modo = modo_estado["valor"]
            if modo not in edades_orden:
                datos = calcular_calendario_360(
                    fecha_estado["valor"], base_real=self.base_real
                )
                modo = edad_de_anio(datos["anio"])
            indice = max(
                0,
                min(len(edades_orden) - 1, edades_orden.index(modo) + pasos),
            )
            elegir_edad(edades_orden[indice])

        edad_anterior.on_click = lambda ev: mover_edad(-1)
        edad_siguiente.on_click = lambda ev: mover_edad(1)

        def volver_hoy(ev=None):
            fecha_estado["valor"] = datetime.now().replace(microsecond=0)
            datos_hoy = calcular_calendario_360(
                fecha_estado["valor"], base_real=self.base_real
            )
            modo_estado["valor"] = (
                edad_de_anio(datos_hoy["anio"]) if es_movil else "actual"
            )
            refrescar_navegador(actualizar=True)
            renderizar()

        def ir_a_anio_redondo(anio):
            fecha_estado["valor"] = fecha_gregoriana_desde_biblica(anio, 1, 1)
            modo_estado["valor"] = edad_de_anio(anio) if es_movil else "actual"
            refrescar_navegador(actualizar=True)
            renderizar()

        def renderizar(actualizar=True):
            datos = calcular_calendario_360(fecha_estado["valor"], base_real=self.base_real)
            grafico.content = self._crear_grafico_linea_tiempo(
                modo_estado["valor"],
                fecha_estado["valor"],
                datos,
                ancho,
                es_movil,
                elegir_edad,
                mover_a_posicion,
                ir_a_anio_redondo,
            )
            if actualizar:
                try:
                    grafico.update()
                except RuntimeError:
                    self.page.update()

        refrescar_navegador()
        renderizar(False)

        def cerrar(ev=None):
            if self._ajustar_dialogo_activo is ajustar_dialogo:
                self._ajustar_dialogo_activo = None
            cerrar_dialogo(self.page, dialog)

        dialog = ft.AlertDialog(
            modal=False,
            content_padding=0,
            content=ft.Container(
                width=ancho_dialogo,
                height=alto,
                padding=10 if es_movil else 14,
                bgcolor=SUPERFICIE_PERLADA,
                border_radius=8,
                border=ft.Border.all(1, PERLA_BORDE),
                content=ft.Column(
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.END,
                            spacing=2,
                            controls=[
                                ft.OutlinedButton(
                                    "Hoy",
                                    icon=ft.Icons.TODAY,
                                    icon_color=LINEA_TIEMPO_VERDE,
                                    tooltip="Volver a la fecha actual",
                                    on_click=volver_hoy,
                                ),
                            ],
                        ),
                        navegador_edades,
                        carril,
                    ],
                ),
            ),
            actions=[ft.TextButton("Cerrar", on_click=cerrar)],
            actions_alignment=ft.MainAxisAlignment.END,
            inset_padding=ft.Padding(
                8 if es_movil else 24,
                8 if es_movil else 24,
                8 if es_movil else 24,
                8 if es_movil else 24,
            ),
        )
        def ajustar_dialogo(ancho_nuevo, alto_nuevo=None):
            nonlocal es_movil, ancho_dialogo, ancho_carril, ancho, alto
            if not ancho_nuevo:
                return
            era_movil = es_movil
            (
                es_movil,
                ancho_dialogo,
                ancho_carril,
                ancho,
                alto,
            ) = calcular_dimensiones(ancho_nuevo, alto_nuevo)
            if es_movil != era_movil:
                datos_visibles = calcular_calendario_360(
                    fecha_estado["valor"], base_real=self.base_real
                )
                modo_estado["valor"] = (
                    edad_de_anio(datos_visibles["anio"])
                    if es_movil
                    else "actual"
                )
            dialog.content.width = ancho_dialogo
            dialog.content.height = alto
            dialog.content.padding = 10 if es_movil else 14
            dialog.inset_padding = ft.Padding(
                8 if es_movil else 24,
                8 if es_movil else 24,
                8 if es_movil else 24,
                8 if es_movil else 24,
            )
            navegador_edades.visible = es_movil
            navegador_edades.width = ancho_carril
            carril.width = ancho_carril
            grafico.width = ancho
            refrescar_navegador()
            renderizar(False)
            try:
                self.page.update()
            except RuntimeError:
                pass

        self._ajustar_dialogo_activo = ajustar_dialogo
        mostrar_dialogo(self.page, dialog)

    def abrir_linea_apofis(self, e=None):
        def calcular_dimensiones(ancho_pantalla, alto_pantalla=None):
            movil = ancho_pantalla < 700
            disponible = ancho_pantalla - (24 if movil else 60)
            ancho_dialogo_local = max(
                230 if movil else 560,
                min(860, disponible),
            )
            ancho_grafico_local = max(
                210,
                ancho_dialogo_local - (20 if movil else 28),
            )
            alto_base = 370 if movil else 400
            alto_dialogo_local = (
                max(300, min(alto_base, alto_pantalla - 150))
                if alto_pantalla
                else alto_base
            )
            return movil, ancho_dialogo_local, ancho_grafico_local, alto_dialogo_local

        def limitar_fecha(fecha):
            return max(FECHA_INICIO_APOPHIS, min(FECHA_APOPHIS, fecha))

        alto_pantalla = self._alto_ultimo_resize or getattr(self.page, "height", None)
        es_movil, ancho_dialogo, ancho, alto = calcular_dimensiones(
            self._ancho_pantalla_actual(),
            alto_pantalla,
        )
        fecha_estado = {
            "valor": limitar_fecha(datetime.now().replace(microsecond=0))
        }
        grafico = ft.Container(width=ancho)
        carril = ft.Row(
            width=ancho,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[grafico],
        )

        def mover_a_posicion(x, izquierda, derecha):
            ancho_util = max(1, derecha - izquierda)
            progreso = max(0, min(1, (float(x) - izquierda) / ancho_util))
            nueva_fecha = (
                FECHA_INICIO_APOPHIS
                + ((FECHA_APOPHIS - FECHA_INICIO_APOPHIS) * progreso)
            ).replace(microsecond=0)
            if nueva_fecha == fecha_estado["valor"]:
                return
            fecha_estado["valor"] = nueva_fecha
            datos_nuevos = calcular_calendario_360(
                nueva_fecha,
                base_real=self.base_real,
            )
            return nueva_fecha, datos_nuevos

        def renderizar(actualizar=True):
            datos = calcular_calendario_360(
                fecha_estado["valor"],
                base_real=self.base_real,
            )
            grafico.content = self._crear_grafico_apofis(
                fecha_estado["valor"],
                datos,
                ancho,
                es_movil,
                mover_a_posicion,
            )
            if actualizar:
                try:
                    grafico.update()
                except RuntimeError:
                    self.page.update()

        def elegir_fecha(fecha):
            fecha_estado["valor"] = limitar_fecha(fecha)
            renderizar()

        renderizar(False)

        def cerrar(ev=None):
            if self._ajustar_dialogo_activo is ajustar_dialogo:
                self._ajustar_dialogo_activo = None
            cerrar_dialogo(self.page, dialog)

        botones_fecha = ft.Row(
            wrap=True,
            spacing=6,
            run_spacing=6,
            alignment=ft.MainAxisAlignment.END,
            controls=[
                ft.OutlinedButton(
                    "Inicio",
                    icon=ft.Icons.FIRST_PAGE,
                    on_click=lambda ev: elegir_fecha(FECHA_INICIO_APOPHIS),
                ),
                ft.OutlinedButton(
                    "Hoy",
                    icon=ft.Icons.TODAY,
                    icon_color=LINEA_TIEMPO_VERDE,
                    on_click=lambda ev: elegir_fecha(datetime.now().replace(microsecond=0)),
                ),
                ft.OutlinedButton(
                    "Llegada",
                    icon=ft.Icons.LAST_PAGE,
                    icon_color=LINEA_TIEMPO_VIOLETA,
                    on_click=lambda ev: elegir_fecha(FECHA_APOPHIS),
                ),
            ],
        )
        dialog = ft.AlertDialog(
            modal=False,
            content=ft.Container(
                width=ancho_dialogo,
                height=alto,
                padding=10 if es_movil else 14,
                bgcolor=SUPERFICIE_PERLADA,
                border=ft.Border.all(1, PERLA_BORDE),
                border_radius=8,
                content=ft.Column(
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[botones_fecha, carril],
                ),
            ),
            actions=[ft.TextButton("Cerrar", on_click=cerrar)],
            actions_alignment=ft.MainAxisAlignment.END,
            inset_padding=ft.Padding(
                8 if es_movil else 24,
                8 if es_movil else 24,
                8 if es_movil else 24,
                8 if es_movil else 24,
            ),
        )

        def ajustar_dialogo(ancho_nuevo, alto_nuevo=None):
            nonlocal es_movil, ancho_dialogo, ancho, alto
            if not ancho_nuevo:
                return
            es_movil, ancho_dialogo, ancho, alto = calcular_dimensiones(
                ancho_nuevo,
                alto_nuevo,
            )
            dialog.content.width = ancho_dialogo
            dialog.content.height = alto
            dialog.content.padding = 10 if es_movil else 14
            dialog.inset_padding = ft.Padding(
                8 if es_movil else 24,
                8 if es_movil else 24,
                8 if es_movil else 24,
                8 if es_movil else 24,
            )
            carril.width = ancho
            grafico.width = ancho
            renderizar(False)
            try:
                self.page.update()
            except RuntimeError:
                pass

        self._ajustar_dialogo_activo = ajustar_dialogo
        mostrar_dialogo(self.page, dialog)

    def abrir_almanaque(self, e=None):
        """Muestra un solo año por vez para conservar legible la equivalencia."""
        es_movil = self._ancho_pantalla_actual() < 700
        self._anio_almanaque = BASE_ANIO
        ancho_dialogo = self._ancho_dialogo_almanaque(es_movil)
        alto_dialogo = self._alto_dialogo_almanaque(es_movil)
        meses = ft.Column(spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        titulo = ft.Text(
            f"Año bíblico {self._anio_almanaque}",
            size=18 if es_movil else 20,
            color=ALMANAQUE_TEXTO_CLARO,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )
        aviso_busqueda = ft.Text(
            "",
            visible=False,
            size=11,
            color="#FFD4D4",
            text_align=ft.TextAlign.CENTER,
        )
        buscar_anio_input = ft.TextField(
            label="Buscar año",
            value=str(self._anio_almanaque),
            keyboard_type=ft.KeyboardType.NUMBER,
            width=150 if es_movil else 170,
            dense=True,
            text_align=ft.TextAlign.CENTER,
            color=ALMANAQUE_TEXTO_CLARO,
            text_style=ft.TextStyle(color=ALMANAQUE_TEXTO_CLARO, size=14),
            label_style=ft.TextStyle(color=ALMANAQUE_TEXTO_CLARO, weight=ft.FontWeight.BOLD),
            cursor_color=ALMANAQUE_TEXTO_CLARO,
            border_color=ALMANAQUE_TEXTO_CLARO,
            focused_border_color=ALMANAQUE_TEXTO_CLARO,
            bgcolor=ft.Colors.with_opacity(0.08, BLANCO),
            on_tap_outside=lambda ev: ocultar_teclado(self.page, ev.control),
        )
        buscar_boton = ft.IconButton(
            icon=ft.Icons.SEARCH,
            icon_color=ALMANAQUE_TEXTO_CLARO,
            tooltip="Buscar año bíblico",
        )
        panel_desplazable = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Row(
                    wrap=True,
                    spacing=6,
                    run_spacing=6,
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        buscar_anio_input,
                        buscar_boton,
                    ],
                ),
                aviso_busqueda,
                meses,
            ],
        )

        anterior = ft.IconButton(
            icon=ft.Icons.KEYBOARD_ARROW_UP,
            tooltip="Ver año anterior",
        )
        siguiente = ft.IconButton(
            icon=ft.Icons.KEYBOARD_ARROW_DOWN,
            tooltip="Ver año siguiente",
        )

        def refrescar_anio(ev=None):
            self._crear_almanaque(es_movil, self._anio_almanaque, meses)
            titulo.value = f"Año bíblico {self._anio_almanaque}"
            buscar_anio_input.value = str(self._anio_almanaque)
            aviso_busqueda.visible = False
            anterior.disabled = self._anio_almanaque <= 1
            self.page.update()
            if hasattr(self.page, "run_task"):
                self.page.run_task(panel_desplazable.scroll_to, offset=0)
            else:
                try:
                    asyncio.get_running_loop().create_task(
                        panel_desplazable.scroll_to(offset=0)
                    )
                except RuntimeError:
                    pass

        def ir_anterior(ev=None):
            if self._anio_almanaque > 1:
                self._anio_almanaque -= 1
                refrescar_anio()

        def ir_siguiente(ev=None):
            self._anio_almanaque += 1
            refrescar_anio()

        def buscar_anio(ev=None):
            try:
                nuevo_anio = int((buscar_anio_input.value or "").strip())
                if nuevo_anio <= 0:
                    raise ValueError
            except ValueError:
                aviso_busqueda.value = "Ingresá un número de año válido."
                aviso_busqueda.visible = True
                self.page.update()
                return
            self._anio_almanaque = nuevo_anio
            refrescar_anio()

        anterior.on_click = ir_anterior
        siguiente.on_click = ir_siguiente
        buscar_anio_input.on_submit = buscar_anio
        buscar_boton.on_click = buscar_anio
        self._crear_almanaque(es_movil, self._anio_almanaque, meses)
        anterior.disabled = self._anio_almanaque <= 1
        anterior.icon_color = ALMANAQUE_TEXTO_CLARO
        siguiente.icon_color = ALMANAQUE_TEXTO_CLARO

        def cerrar(ev=None):
            cerrar_dialogo(self.page, dialog)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Column(
                tight=True,
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        "Almanaque bíblico",
                        color=ALMANAQUE_TEXTO_CLARO,
                        size=16 if es_movil else 18,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Row(
                        tight=True,
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[anterior, titulo, siguiente],
                    ),
                ],
            ),
            title_padding=ft.Padding(
                left=8 if es_movil else 16,
                top=10 if es_movil else 14,
                right=8 if es_movil else 16,
                bottom=4,
            ),
            content_padding=0,
            actions_padding=ft.Padding(
                left=8 if es_movil else 16,
                top=6,
                right=8 if es_movil else 16,
                bottom=8 if es_movil else 12,
            ),
            inset_padding=ft.Padding(
                left=8 if es_movil else 24,
                top=8 if es_movil else 24,
                right=8 if es_movil else 24,
                bottom=8 if es_movil else 24,
            ),
            content=ft.Container(
                width=ancho_dialogo,
                height=alto_dialogo,
                bgcolor=MARRON_RELOJ,
                border_radius=14,
                padding=10 if es_movil else 16,
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
            actions_alignment=(
                ft.MainAxisAlignment.CENTER if es_movil else ft.MainAxisAlignment.END
            ),
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
        contenido = {
            clave: valor
            for clave, valor in datos.items()
            if clave not in {"fecha_real", "base_real"}
        }
        contenido["fecha_real_iso"] = datos["fecha_real"].isoformat()
        contenido["base_real_iso"] = datos["base_real"].isoformat()
        contenido["resumen"] = texto_calendario_360(datos)
        ArchivoLocalService.guardar_json(
            self.page,
            contenido,
            nombre_sugerido,
            "Guardar tiempo en el dispositivo",
        )
