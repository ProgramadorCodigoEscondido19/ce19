import flet as ft

from core.app_state import state
from logica.analizador_colores import (
    DIGITO_COLORES,
    analizar_codigo_visual,
    guardar_historial,
)
from services.biblia_service import BibliaService
from ui.clipboard import copiar_al_portapapeles
from ui.compartir import compartir_texto
from ui.nombre_guardado import pedir_nombre_y_carpeta_guardado
from ui.responsive import Responsive
from ui.teclado import ocultar_teclado
from ui.tema import (
    BLANCO,
    MARRON,
    NEGRO,
    PERLA_BORDE,
    PERLA_PANEL,
    PERLA_VIOLETA,
    SUPERFICIE_PERLADA,
    TEXTO_PRINCIPAL,
    TEXTO_SECUNDARIO,
    VIOLETA_IOS,
    sombra_suave,
)


CARD_BLANCO = SUPERFICIE_PERLADA
BORDE_SUAVE = PERLA_BORDE
COLOR_ICONOS = {
    "NEGRO": "⬛",
    "MARRON": "🟫",
    "ROJO": "🟥",
    "NARANJA": "🟧",
    "AMARILLO": "🟨",
    "VERDE": "🟩",
    "AZUL": "🟦",
    "VIOLETA": "🟪",
    "GRIS": "🔲",
    "BLANCO": "⬜",
}


COLOR_ICONOS = {
    "NEGRO": "\u2B1B",
    "MARRON": "\U0001F7EB",
    "ROJO": "\U0001F7E5",
    "NARANJA": "\U0001F7E7",
    "AMARILLO": "\U0001F7E8",
    "VERDE": "\U0001F7E9",
    "AZUL": "\U0001F7E6",
    "VIOLETA": "\U0001F7EA",
    "GRIS": "\U0001F532",
    "BLANCO": "\u2B1C",
}


class AnalizadorColoresView:
    def __init__(self, page, router):
        self.page = page
        self.router = router
        self.responsive = Responsive(page)
        self.resultado = None
        self.ultimo_archivo_tarjeta = None

        self.libros = BibliaService.nombres_libros()
        libro_inicial = self.libros[0] if self.libros else ""

        self.texto = ft.TextField(
            label="Texto",
            multiline=True,
            min_lines=4,
            max_lines=8,
            border_radius=18,
            filled=True,
            bgcolor="#FCFAFF",
            border_color=PERLA_BORDE,
            focused_border_color=VIOLETA_IOS,
            on_focus=lambda e: self._preparar_entrada_texto(e.control),
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
        )

        self.origen_biblia = ft.Dropdown(
            label="Importar",
            value="Texto escrito",
            dense=True,
            options=[
                ft.dropdown.Option("Texto escrito"),
                ft.dropdown.Option("Biblia completa"),
                ft.dropdown.Option("Libro"),
                ft.dropdown.Option("Capitulo"),
                ft.dropdown.Option("Versiculos"),
            ],
            on_select=self._actualizar_importador,
        )
        self.libro_biblia = ft.Dropdown(
            label="Libro desde",
            value=libro_inicial,
            dense=True,
            options=[ft.dropdown.Option(nombre) for nombre in self.libros],
            on_select=self._actualizar_importador,
        )
        self.libro_hasta_biblia = ft.Dropdown(
            label="Libro hasta",
            value=libro_inicial,
            dense=True,
            options=[ft.dropdown.Option(nombre) for nombre in self.libros],
            on_select=self._actualizar_importador,
        )
        self.capitulo_biblia = ft.Dropdown(
            label="Capitulo desde",
            value="1",
            dense=True,
            options=[],
            on_select=self._actualizar_importador,
        )
        self.capitulo_hasta_biblia = ft.Dropdown(
            label="Capitulo hasta",
            value="1",
            dense=True,
            options=[],
            on_select=self._actualizar_importador,
        )
        self.versiculo_desde = ft.Dropdown(
            label="Desde",
            value="1",
            dense=True,
            options=[],
            on_select=self._actualizar_importador,
        )
        self.versiculo_hasta = ft.Dropdown(
            label="Hasta",
            value="1",
            dense=True,
            options=[],
        )

        self.panel_resultado = ft.Column(expand=True, spacing=10, scroll=ft.ScrollMode.AUTO)
        self._actualizar_importador()

    def _on_resize(self, e):
        self.router.refrescar()

    def obtener_vista(self):
        self.page.on_resize = self._on_resize
        return ft.Container(
            expand=True,
            padding=self._padding(),
            content=self._contenido(),
        )

    def _padding(self):
        if self.responsive.is_mobile():
            return 4
        if self.responsive.is_tablet():
            return 6
        return 6

    def _card(self, content, padding=14, expand=False):
        return ft.Container(
            expand=expand,
            padding=padding,
            bgcolor=CARD_BLANCO,
            border=ft.Border.all(1, BORDE_SUAVE),
            border_radius=20,
            shadow=sombra_suave(0.055, 18, 0, 6),
            content=content,
        )

    def _panel_suave(self, content, padding=12):
        return ft.Container(
            padding=padding,
            bgcolor=ft.Colors.with_opacity(0.90, BLANCO),
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=18,
            shadow=sombra_suave(0.035, 12, 0, 4),
            content=content,
        )

    def _contenido(self):
        entrada = self._panel_entrada()
        salida = self._panel_salida()

        if self.responsive.is_mobile():
            return ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=10,
                controls=[entrada, salida],
            )

        return ft.Row(
            expand=True,
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Container(width=430 if not self.responsive.is_tablet() else 360, content=entrada),
                ft.Container(expand=True, content=salida),
            ],
        )

    def _panel_entrada(self):
        return self._card(
            ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=46,
                                height=46,
                                border_radius=16,
                                bgcolor=PERLA_VIOLETA,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(ft.Icons.COLOR_LENS, color=VIOLETA_IOS, size=26),
                            ),
                            ft.Column(
                                tight=True,
                                spacing=2,
                                controls=[
                                    ft.Text("Colores", size=26, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                                    ft.Text("Codigo visual por caracter", size=12, color=TEXTO_SECUNDARIO),
                                ],
                            ),
                        ],
                    ),
                    self._panel_suave(
                        ft.Column(
                            tight=True,
                            spacing=8,
                            controls=[
                                ft.Row(
                                    spacing=8,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Icon(ft.Icons.TEXT_FIELDS, size=18, color=VIOLETA_IOS),
                                        ft.Text("Texto a analizar", size=13, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                                    ],
                                ),
                                self.texto,
                            ],
                        )
                    ),
                    self._panel_importar_biblia(),
                    ft.Row(
                        wrap=True,
                        spacing=8,
                        run_spacing=8,
                        controls=[
                            ft.ElevatedButton("Analizar", icon=ft.Icons.PLAY_ARROW, on_click=self.analizar),
                            ft.OutlinedButton("Limpiar", icon=ft.Icons.CLEAR, on_click=self.limpiar),
                        ],
                    ),
                    self._leyenda_colores(),
                ],
            ),
            expand=not self.responsive.is_mobile(),
        )

    def _panel_importar_biblia(self):
        controles = [
            ft.Text("Importar segmentos de Biblia", size=13, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
            ft.Row(
                wrap=True,
                spacing=8,
                run_spacing=8,
                controls=[
                    ft.Container(width=150, content=self.origen_biblia),
                    ft.Container(width=170, content=self.libro_biblia),
                    ft.Container(width=170, content=self.libro_hasta_biblia),
                    ft.Container(width=112, content=self.capitulo_biblia),
                    ft.Container(width=112, content=self.capitulo_hasta_biblia),
                    ft.Container(width=96, content=self.versiculo_desde),
                    ft.Container(width=96, content=self.versiculo_hasta),
                    ft.ElevatedButton("Importar", icon=ft.Icons.DOWNLOAD, on_click=self.importar_biblia),
                ],
            ),
        ]
        return ft.Container(
            padding=10,
            bgcolor=ft.Colors.with_opacity(0.90, BLANCO),
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=18,
            shadow=sombra_suave(0.035, 12, 0, 4),
            content=ft.Column(tight=True, spacing=8, controls=controles),
        )

    def _panel_salida(self):
        if not self.resultado:
            self.panel_resultado.controls = [
                self._card(
                    ft.Column(
                        tight=True,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                        controls=[
                            ft.Icon(ft.Icons.AUTO_AWESOME, size=40, color=VIOLETA_IOS),
                            ft.Text("Ingrese texto o importe Biblia y presione Analizar.", text_align=ft.TextAlign.CENTER, color=TEXTO_SECUNDARIO),
                        ],
                    ),
                    expand=False,
                )
            ]

        return self._card(self.panel_resultado, expand=True)

    def _leyenda_colores(self):
        return ft.Row(
            wrap=True,
            spacing=5,
            run_spacing=5,
            controls=[
                self._chip_color(numero, color["nombre"], color["hex"], compacto=True)
                for numero, color in DIGITO_COLORES.items()
            ],
        )

    def _chip_color(self, numero, nombre, hex_color, compacto=False):
        borde = ft.Border.all(1.4, MARRON) if numero == 9 else ft.Border.all(1, ft.Colors.GREY_400)
        return ft.Container(
            padding=ft.Padding(left=7, top=4, right=7, bottom=4),
            bgcolor=hex_color,
            border=borde,
            border_radius=7,
            content=ft.Text(
                f"{numero} {nombre}" if not compacto else str(numero),
                size=11,
                weight=ft.FontWeight.BOLD,
                color=self._texto_contraste(hex_color),
            ),
            tooltip=f"{numero} {nombre}",
        )

    def _texto_contraste(self, hex_color):
        if str(hex_color).upper() == "#FFFFFF":
            return NEGRO
        if str(hex_color).upper() == "#000000":
            return BLANCO
        return ft.Colors.BLACK if hex_color in ("#FDD835", "#FFF300") else ft.Colors.WHITE

    def _actualizar_importador(self, e=None):
        libro = self.libro_biblia.value or (self.libros[0] if self.libros else "")
        if not self.libro_hasta_biblia.value:
            self.libro_hasta_biblia.value = libro
        cantidad_capitulos = BibliaService.cantidad_capitulos(libro) or 1
        self.capitulo_biblia.options = [ft.dropdown.Option(str(i)) for i in range(1, cantidad_capitulos + 1)]
        self.capitulo_hasta_biblia.options = [ft.dropdown.Option(str(i)) for i in range(1, cantidad_capitulos + 1)]
        if not self.capitulo_biblia.value or int(self.capitulo_biblia.value) > cantidad_capitulos:
            self.capitulo_biblia.value = "1"
        if not self.capitulo_hasta_biblia.value or int(self.capitulo_hasta_biblia.value) > cantidad_capitulos:
            self.capitulo_hasta_biblia.value = self.capitulo_biblia.value

        capitulo = int(self.capitulo_biblia.value or 1)
        cantidad_versiculos = len(BibliaService.obtener_capitulo(libro, capitulo)) or 1
        opciones_versiculos = [ft.dropdown.Option(str(i)) for i in range(1, cantidad_versiculos + 1)]
        self.versiculo_desde.options = opciones_versiculos
        self.versiculo_hasta.options = [ft.dropdown.Option(str(i)) for i in range(1, cantidad_versiculos + 1)]
        if not self.versiculo_desde.value or int(self.versiculo_desde.value) > cantidad_versiculos:
            self.versiculo_desde.value = "1"
        if not self.versiculo_hasta.value or int(self.versiculo_hasta.value) > cantidad_versiculos:
            self.versiculo_hasta.value = self.versiculo_desde.value

        modo = self.origen_biblia.value
        self.libro_biblia.visible = modo in ("Libro", "Capitulo", "Versiculos")
        self.libro_hasta_biblia.visible = modo == "Libro"
        self.capitulo_biblia.visible = modo in ("Capitulo", "Versiculos")
        self.capitulo_hasta_biblia.visible = modo == "Capitulo"
        self.versiculo_desde.visible = modo == "Versiculos"
        self.versiculo_hasta.visible = modo == "Versiculos"

        try:
            for control in (
                self.libro_biblia,
                self.libro_hasta_biblia,
                self.capitulo_biblia,
                self.capitulo_hasta_biblia,
                self.versiculo_desde,
                self.versiculo_hasta,
            ):
                control.update()
        except (RuntimeError, AssertionError):
            pass

    def importar_biblia(self, e=None):
        modo = self.origen_biblia.value
        libro = self.libro_biblia.value or (self.libros[0] if self.libros else "")
        libro_hasta = self.libro_hasta_biblia.value or libro
        capitulo = int(self.capitulo_biblia.value or 1)
        capitulo_hasta = int(self.capitulo_hasta_biblia.value or capitulo)

        if modo == "Texto escrito":
            self._snack("Seleccione Biblia completa, Libro, Capitulo o Versiculos.")
            return

        if modo == "Biblia completa":
            partes = []
            for item_libro in BibliaService.libros():
                for cap in item_libro.get("capitulos", []):
                    partes.extend(str(v) for v in cap)
            referencia = "Biblia completa"
            texto = " ".join(partes)
        elif modo == "Libro":
            nombres = self._rango_libros(libro, libro_hasta)
            partes = []
            for nombre_libro in nombres:
                item = BibliaService.libro_por_nombre(nombre_libro)
                for cap in (item or {}).get("capitulos", []):
                    partes.extend(str(v) for v in cap)
            referencia = libro if libro == libro_hasta else f"{libro} - {libro_hasta}"
            texto = " ".join(partes)
        elif modo == "Capitulo":
            if capitulo_hasta < capitulo:
                capitulo, capitulo_hasta = capitulo_hasta, capitulo
            partes = []
            for numero_capitulo in range(capitulo, capitulo_hasta + 1):
                partes.extend(str(v) for v in BibliaService.obtener_capitulo(libro, numero_capitulo))
            referencia = f"{libro} {capitulo}" if capitulo == capitulo_hasta else f"{libro} {capitulo}-{capitulo_hasta}"
            texto = " ".join(partes)
        else:
            desde = int(self.versiculo_desde.value or 1)
            hasta = int(self.versiculo_hasta.value or desde)
            if hasta < desde:
                desde, hasta = hasta, desde
            cap = BibliaService.obtener_capitulo(libro, capitulo)
            textos = [str(cap[i - 1]) for i in range(desde, min(hasta, len(cap)) + 1)]
            referencia = f"{libro} {capitulo}:{desde}" if desde == hasta else f"{libro} {capitulo}:{desde}-{hasta}"
            texto = " ".join(textos)

        self.texto.value = texto
        self.texto.label = referencia
        self.page.update()
        self.analizar()

    def _rango_libros(self, desde, hasta):
        if not self.libros:
            return []
        try:
            inicio = self.libros.index(desde)
        except ValueError:
            inicio = 0
        try:
            fin = self.libros.index(hasta)
        except ValueError:
            fin = inicio
        if fin < inicio:
            inicio, fin = fin, inicio
        return self.libros[inicio:fin + 1]

    def limpiar(self, e=None):
        self.texto.value = ""
        self.texto.label = "Texto"
        self.resultado = None
        self.ultimo_archivo_tarjeta = None
        self.panel_resultado.controls.clear()
        self.page.update()

    def analizar(self, e=None):
        if self.responsive.is_mobile():
            ocultar_teclado(self.page, self.texto)
        texto = self.texto.value or ""

        if not texto.strip():
            self._snack("Ingrese un texto para analizar.")
            return

        self.resultado = analizar_codigo_visual(texto)
        guardar_historial(self._resultado_para_guardar())
        self._render_resultado()
        self._preparar_entrada_texto(self.texto)

    def _preparar_entrada_texto(self, control=None):
        control = control or self.texto
        control.disabled = False
        control.read_only = False
        control.can_request_focus = True
        try:
            control.update()
        except (RuntimeError, AssertionError):
            pass

    def _render_resultado(self):
        self.panel_resultado.controls.clear()
        if not self.resultado:
            self.page.update()
            return

        self.panel_resultado.controls.extend(
            [
                self._encabezado_resultado(),
                self._bloques_caracteres(),
                self._resumen_codigo(),
                self._acciones_resultado(),
            ]
        )
        self.page.update()

    def _encabezado_resultado(self):
        texto_limpio = self.resultado.get("texto_limpio", "")
        vista = texto_limpio if len(texto_limpio) <= 220 else texto_limpio[:217] + "..."
        return ft.Container(
            padding=12,
            bgcolor=PERLA_PANEL,
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=16,
            content=ft.Column(
                tight=True,
                spacing=6,
                controls=[
                    ft.Text("Texto", size=13, weight=ft.FontWeight.BOLD, color=TEXTO_SECUNDARIO),
                    ft.Text(vista or "Sin texto", size=18, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL, selectable=True),
                ],
            ),
        )

    def _bloques_caracteres(self):
        detalle = self.resultado.get("detalle_visual", [])
        limite = 90 if self.responsive.is_mobile() else 180
        visibles = detalle[:limite]
        controles = [self._bloque_caracter(item) for item in visibles]

        if len(detalle) > limite:
            controles.append(
                ft.Container(
                    padding=12,
                    border_radius=12,
                    bgcolor=PERLA_VIOLETA,
                    content=ft.Text(
                        f"Vista resumida: se muestran {limite} de {len(detalle)} caracteres. El total se calcula completo.",
                        size=12,
                        color=TEXTO_SECUNDARIO,
                    ),
                )
            )

        return ft.Container(
            padding=10,
            bgcolor="#FFFFFF",
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=16,
            content=ft.Row(
                wrap=True,
                spacing=8,
                run_spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=controles,
            ),
        )

    def _bloque_caracter(self, item):
        color_hex = item.get("hex", "#FFFFFF")
        reducido = item.get("reducido", "")
        digitos = item.get("digitos_colores", [])
        tiene_reduccion = len(digitos) > 1

        return ft.Container(
            width=74 if self.responsive.is_mobile() else 84,
            padding=5,
            bgcolor="#FCFAFF",
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=10,
            content=ft.Column(
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=3,
                controls=[
                    ft.Container(
                        width=50,
                        height=34,
                        alignment=ft.Alignment(0, 0),
                        bgcolor=color_hex,
                        border=ft.Border.all(1.5, MARRON) if reducido == 9 else ft.Border.all(1, ft.Colors.WHITE),
                        border_radius=6,
                        content=ft.Text(item.get("letra", ""), size=15, weight=ft.FontWeight.BOLD, color=self._texto_contraste(color_hex)),
                    ),
                    ft.Text(str(item.get("valor", "")), size=12, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=2,
                        controls=[
                            ft.Text(str(d["digito"]), size=11, weight=ft.FontWeight.BOLD)
                            for d in digitos
                        ],
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=2,
                        controls=[
                            ft.Container(
                                width=19,
                                height=19,
                                bgcolor=d["hex"],
                                border=ft.Border.all(1.4, MARRON) if d["digito"] == 9 else ft.Border.all(1, ft.Colors.GREY_400),
                            )
                            for d in digitos
                        ],
                    ),
                    ft.Container(
                        width=28,
                        height=24,
                        visible=tiene_reduccion,
                        alignment=ft.Alignment(0, 0),
                        bgcolor=color_hex,
                        border=ft.Border.all(1.4, MARRON) if reducido == 9 else ft.Border.all(1, ft.Colors.GREY_400),
                        content=ft.Text(str(reducido), size=12, weight=ft.FontWeight.BOLD, color=self._texto_contraste(color_hex)),
                    ),
                ],
            ),
        )

    def _resumen_codigo(self):
        total = self.resultado.get("total_codigo", 0)
        pasos = self.resultado.get("pasos_reduccion", [])
        final = self.resultado.get("resultado_final", 0)
        final_hex = self.resultado.get("hex_final", "#FFFFFF")
        partes = []

        if pasos:
            partes.append(self._cuadro_numero(pasos[0], "#F7F0E8"))
            for paso in pasos[1:]:
                partes.append(ft.Text("=", size=20, weight=ft.FontWeight.BOLD))
                partes.append(self._cuadro_numero(paso, DIGITO_COLORES.get(paso, DIGITO_COLORES[0])["hex"]))

        return ft.Container(
            padding=12,
            bgcolor=PERLA_PANEL,
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=16,
            content=ft.Column(
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    ft.Text(f"TOTAL DE CODIGOS: {total}", size=18, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                    ft.Text("PROCESO DE REDUCCION", size=13, weight=ft.FontWeight.BOLD, color=TEXTO_SECUNDARIO),
                    ft.Row(wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=8, run_spacing=8, controls=partes),
                    ft.Text("RESULTADO FINAL", size=13, weight=ft.FontWeight.BOLD, color=TEXTO_SECUNDARIO),
                    ft.Container(
                        width=96,
                        height=70,
                        alignment=ft.Alignment(0, 0),
                        bgcolor=final_hex,
                        border=ft.Border.all(2, MARRON),
                        border_radius=8,
                        content=ft.Text(str(final), size=34, weight=ft.FontWeight.BOLD, color=self._texto_contraste(final_hex)),
                    ),
                ],
            ),
        )

    def _cuadro_numero(self, valor, color):
        return ft.Container(
            width=max(54, len(str(valor)) * 18 + 22),
            height=44,
            alignment=ft.Alignment(0, 0),
            padding=ft.Padding(left=10, top=0, right=10, bottom=0),
            bgcolor=color,
            border=ft.Border.all(1.5, MARRON) if color == "#FFFFFF" else ft.Border.all(1, PERLA_BORDE),
            border_radius=6,
            content=ft.Text(str(valor), size=18, weight=ft.FontWeight.BOLD, color=self._texto_contraste(color)),
        )

    def _acciones_resultado(self):
        return ft.Row(
            wrap=True,
            spacing=8,
            run_spacing=8,
            controls=[
                ft.ElevatedButton("Guardar", icon=ft.Icons.SAVE_ALT, on_click=self.guardar_resultado),
                ft.OutlinedButton("Compartir", icon=ft.Icons.SHARE, on_click=self.compartir_resultado),
                ft.OutlinedButton("Copiar", icon=ft.Icons.CONTENT_COPY, on_click=lambda e: self.copiar_resultado()),
            ],
        )

    def _resultado_para_guardar(self):
        if not self.resultado:
            return {}
        datos = dict(self.resultado)
        detalle_base = datos.get("detalle", [])
        secuencia = datos.get("secuencia", [])
        detalle = datos.get("detalle_visual", [])
        datos["detalle"] = detalle_base[:300]
        datos["detalle_total"] = len(detalle_base)
        datos["secuencia"] = secuencia[:300]
        datos["secuencia_total"] = len(secuencia)
        datos["detalle_visual"] = detalle[:300]
        datos["detalle_visual_total"] = len(detalle)
        return datos

    def _titulo_resultado(self):
        etiqueta = self.texto.label if self.texto.label and self.texto.label != "Texto" else "Analisis de colores"
        return etiqueta or "Analisis de colores"

    def _texto_resumen(self):
        if not self.resultado:
            return ""
        pasos = " -> ".join(str(p) for p in self.resultado.get("pasos_reduccion", []))
        detalle = self.resultado.get("detalle_visual", [])
        partes = []

        for item in detalle:
            digitos = item.get("digitos_colores", [])
            iconos_digitos = "".join(COLOR_ICONOS.get(d.get("color", ""), "▫") for d in digitos)
            icono_final = COLOR_ICONOS.get(item.get("color", ""), "▫")
            if len(digitos) > 1:
                partes.append(f"{item.get('letra', '')} {iconos_digitos} = {icono_final} {item.get('reducido', '')}")
            else:
                partes.append(f"{item.get('letra', '')} {icono_final} {item.get('reducido', '')}")

        caracteres = " | ".join(partes)
        return (
            "CODIGO ESCONDIDO 19 - COLORES\n\n"
            f"Texto: {self._titulo_resultado()}\n"
            f"Caracteres: {caracteres}\n"
            f"Total de codigos: {self.resultado.get('total_codigo', 0)}\n"
            f"Proceso de reduccion: {pasos}\n"
            f"Resultado final: {self.resultado.get('resultado_final', 0)} "
            f"{COLOR_ICONOS.get(self.resultado.get('color_final', ''), '')} "
            f"({self.resultado.get('color_final', '')})"
        )

    def guardar_resultado(self, e=None):
        if not self.resultado:
            self._snack("Primero realice un analisis.")
            return
        pedir_nombre_y_carpeta_guardado(
            self.page,
            "Guardar tarjeta de colores",
            self._titulo_resultado(),
            state.carpetas,
            "COLORES",
            self._guardar_resultado_con_nombre,
            "Se guardara como tarjeta visual dentro de COLORES.",
        )

    def _guardar_resultado_con_nombre(self, nombre, carpeta=None):
        destino = carpeta or state.carpetas.obtener_por_nombre("COLORES")
        resumen = self._texto_resumen()
        contenido = self._resultado_para_guardar()
        contenido["texto_compartir"] = resumen
        state.guardados.guardar(
            {
                "tipo": "analisis_colores",
                "subtipo": "tarjeta_colores",
                "carpeta": destino["nombre"] if destino else "COLORES",
                "carpeta_id": destino["id"] if destino else 4,
                "nombre": nombre,
                "palabra": nombre or self._titulo_resultado(),
                "referencia": self._titulo_resultado(),
                "alfabeto": "Colores",
                "suma": resumen,
                "resultado": self.resultado.get("resultado_final", ""),
                "contenido": contenido,
            }
        )
        self._confirmacion("Guardado correctamente.")

    def _linea_color_compartir(self, item):
        letra = item.get("letra", "")
        valor = item.get("valor", "")
        reducido = item.get("reducido", "")
        digitos = item.get("digitos_colores", [])
        icono_final = COLOR_ICONOS.get(item.get("color", ""), "[]")

        if len(digitos) > 1:
            partes = [
                f"{d.get('digito')} {COLOR_ICONOS.get(d.get('color', ''), '[]')} {d.get('color', '')}"
                for d in digitos
            ]
            return f"{letra}: {valor} = {' + '.join(partes)} -> {reducido} {icono_final} {item.get('color', '')}"

        return f"{letra}: {valor} {icono_final} {item.get('color', '')}"

    def _texto_resumen(self):
        if not self.resultado:
            return ""

        pasos = " -> ".join(str(p) for p in self.resultado.get("pasos_reduccion", []))
        detalle = self.resultado.get("detalle_visual", [])
        partes = [self._linea_color_compartir(item) for item in detalle]

        referencia = self._titulo_resultado()
        texto_limpio = self.resultado.get("texto_limpio", "")
        texto = texto_limpio if referencia == "Analisis de colores" else f"{referencia}\n{texto_limpio}"
        return (
            "CODIGO ESCONDIDO 19 - COLORES\n\n"
            f"Texto analizado:\n{texto}\n\n"
            f"Detalle:\n" + "\n".join(partes) + "\n\n"
            f"Total de codigo: {self.resultado.get('total_codigo', 0)}\n"
            f"Reduccion final: {pasos}\n"
            f"Resultado final: {self.resultado.get('resultado_final', 0)} "
            f"{COLOR_ICONOS.get(self.resultado.get('color_final', ''), '')} "
            f"{self.resultado.get('color_final', '')}"
        )

    def compartir_resultado(self, e=None):
        if not self.resultado:
            self._snack("Primero realice un analisis.")
            return
        compartir_texto(self.page, self._texto_resumen(), self._titulo_resultado())

    def copiar_resultado(self):
        if not self.resultado:
            self._snack("Primero realice un analisis.")
            return
        copiar_al_portapapeles(self.page, self._texto_resumen())

    def _snack(self, mensaje):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje),
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=ft.Margin(left=18, top=0, right=18, bottom=72),
            show_close_icon=True,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _confirmacion(self, mensaje):
        def cerrar(e=None):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Guardado correctamente"),
            content=ft.Text(mensaje),
            actions=[ft.ElevatedButton("Aceptar", on_click=cerrar)],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
