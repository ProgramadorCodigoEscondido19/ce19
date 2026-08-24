from pathlib import Path

import flet as ft

from core.app_state import state
from logica.analizador_colores import (
    DIGITO_COLORES,
    analizar_codigo_visual,
    exportar_pdf_colores,
    guardar_historial,
    reducir_numero,
    tokenizar,
    valores_secundarios_colores,
)
from services.biblia_service import BibliaService
from ui.clipboard import copiar_al_portapapeles
from ui.compartir import compartir_archivo, compartir_texto
from ui.dialogos import cerrar_dialogo, mostrar_dialogo
from ui.nombre_guardado import pedir_nombre_y_carpeta_guardado
from ui.responsive import Responsive
from ui.teclado import ocultar_teclado
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


CARD_BLANCO = SUPERFICIE_PERLADA
BORDE_SUAVE = PERLA_BORDE
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

COLOR_ORDEN = ["NEGRO", "MARRON", "ROJO", "NARANJA", "AMARILLO", "VERDE", "AZUL", "PURPURA", "GRIS", "BLANCO"]
COLOR_INICIALES = {
    "NEGRO": "N",
    "MARRON": "M",
    "ROJO": "R",
    "NARANJA": "N",
    "AMARILLO": "Am",
    "VERDE": "V",
    "AZUL": "Az",
    "PURPURA": "P",
    "GRIS": "G",
    "BLANCO": "B",
}


def _nombre_color_publico(nombre):
    nombre = str(nombre or "").upper().strip()
    if nombre in ("VIOLETA", "PÚRPURA"):
        return "PURPURA"
    return nombre


def _icono_color(nombre):
    return COLOR_ICONOS.get(_nombre_color_publico(nombre), "▫")


def _inicial_color(nombre):
    return COLOR_INICIALES.get(_nombre_color_publico(nombre), "")


class AnalizadorColoresView:
    def __init__(self, page, router):
        self.page = page
        self.router = router
        self.responsive = Responsive(page)
        self.resultado = None
        self.ultimo_archivo_tarjeta = None
        self.escala_vista = 0.86
        self.dialogo_importar = None
        self.file_picker_pdf = None

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
            focused_border_color=PURPURA_IOS,
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

        self.panel_resultado = ft.Column(
            expand=True,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
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
                spacing=6,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[entrada, salida],
            )

        if self.responsive.is_desktop():
            return ft.Column(
                expand=True,
                spacing=6,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    entrada,
                    ft.Container(expand=True, content=salida),
                ],
            )

        return ft.Column(
            expand=True,
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                entrada,
                ft.Container(expand=True, content=salida),
            ],
        )

    def _panel_entrada(self):
        controles = ft.Row(
            wrap=True,
            spacing=8,
            run_spacing=8,
            alignment=ft.MainAxisAlignment.END,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.ElevatedButton("Texto", icon=ft.Icons.TEXT_FIELDS, on_click=self.abrir_texto),
                ft.OutlinedButton("Importar", icon=ft.Icons.DOWNLOAD, on_click=self.abrir_importar),
                ft.ElevatedButton("Analizar", icon=ft.Icons.PLAY_ARROW, on_click=self.analizar),
                ft.IconButton(icon=ft.Icons.CLEAR, tooltip="Limpiar analisis", on_click=self.limpiar),
                ft.IconButton(icon=ft.Icons.ZOOM_OUT, tooltip="Achicar vista", on_click=lambda e: self._cambiar_escala(-0.08)),
                ft.Text(f"{int(self.escala_vista * 100)}%", size=12, weight=ft.FontWeight.BOLD, color=TEXTO_SECUNDARIO),
                ft.IconButton(icon=ft.Icons.ZOOM_IN, tooltip="Agrandar vista", on_click=lambda e: self._cambiar_escala(0.08)),
            ],
        )

        return self._card(
            ft.Row(
                wrap=True,
                spacing=12,
                run_spacing=8,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        tight=True,
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=40,
                                height=40,
                                border_radius=14,
                                bgcolor=PERLA_PURPURA,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(ft.Icons.COLOR_LENS, color=PURPURA_IOS, size=22),
                            ),
                            ft.Text("Resaltado", size=24, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                        ],
                    ),
                    controles,
                ],
            ),
            padding=10,
            expand=False,
        )

    def abrir_texto(self, e=None):
        ancho = min(760, max(320, int((self.responsive.width() or 760) * 0.72)))
        alto = 360 if self.responsive.is_mobile() else 420
        entrada = ft.TextField(
            label="Texto",
            value=self.texto.value or "",
            multiline=True,
            min_lines=10,
            max_lines=18,
            border_radius=14,
            filled=True,
            autofocus=True,
            bgcolor="#FCFAFF",
            border_color=PERLA_BORDE,
            focused_border_color=PURPURA_IOS,
        )

        def cerrar(ev=None):
            cerrar_dialogo(self.page, dialog)

        def aceptar(ev=None):
            self.texto.value = entrada.value or ""
            self.texto.label = "Texto"
            cerrar()
            self.analizar()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Texto a analizar"),
            content=ft.Container(width=ancho, height=alto, content=entrada),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar),
                ft.ElevatedButton("Aceptar", icon=ft.Icons.CHECK, on_click=aceptar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        mostrar_dialogo(self.page, dialog, cerrar_al_tocar_fuera=False)

    def abrir_importar(self, e=None):
        ancho = min(860, max(330, int((self.responsive.width() or 860) * 0.78)))

        def cerrar(ev=None):
            self.dialogo_importar = None
            cerrar_dialogo(self.page, dialog)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Importar segmentos de Biblia"),
            content=ft.Container(width=ancho, content=self._panel_importar_biblia()),
            actions=[ft.TextButton("Cerrar", on_click=cerrar)],
            actions_alignment=ft.MainAxisAlignment.END,
            scrollable=True,
        )
        self.dialogo_importar = dialog
        mostrar_dialogo(self.page, dialog, cerrar_al_tocar_fuera=False)

    def _cambiar_escala(self, delta):
        self.escala_vista = max(0.42, min(1.18, self.escala_vista + delta))
        if self.resultado:
            self._render_resultado()
        else:
            self.router.refrescar()

    def _tam(self, valor, minimo=None):
        ajustado = int(round(valor * self.escala_vista))
        if minimo is not None:
            return max(minimo, ajustado)
        return ajustado

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
                            ft.Icon(ft.Icons.AUTO_AWESOME, size=40, color=PURPURA_IOS),
                            ft.Text("Ingrese texto o importe Biblia y presione Analizar.", text_align=ft.TextAlign.CENTER, color=TEXTO_SECUNDARIO),
                        ],
                    ),
                    expand=False,
                )
            ]

        return ft.Container(
            expand=True,
            padding=4,
            bgcolor=ft.Colors.with_opacity(0.93, BLANCO),
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=10,
            content=self.panel_resultado,
        )

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
        color = str(hex_color or "").strip().lstrip("#")
        if len(color) == 6:
            try:
                rojo, verde, azul = (int(color[indice:indice + 2], 16) for indice in (0, 2, 4))
                luminancia = (rojo * 299 + verde * 587 + azul * 114) / 1000
                return NEGRO if luminancia >= 155 else BLANCO
            except ValueError:
                pass
        return NEGRO

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
        if self.dialogo_importar:
            dialogo = self.dialogo_importar
            self.dialogo_importar = None
            cerrar_dialogo(self.page, dialogo)
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
        self.panel_resultado.spacing = self._tam(10, 5)
        self.panel_resultado.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
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
            padding=self._tam(12, 7),
            bgcolor=PERLA_PANEL,
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=12,
            content=ft.Column(
                tight=True,
                spacing=self._tam(6, 3),
                controls=[
                    ft.Text("Texto", size=self._tam(13, 10), weight=ft.FontWeight.BOLD, color=TEXTO_SECUNDARIO),
                    ft.Text(vista or "Sin texto", size=self._tam(18, 12), weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL, selectable=True),
                ],
            ),
        )

    def _bloques_caracteres(self):
        detalle = self.resultado.get("detalle_visual", [])
        limite_base = 90 if self.responsive.is_mobile() else 220 if self.responsive.is_tablet() else 420
        limite = int(limite_base / max(0.62, self.escala_vista))
        grupos, cantidad_visible = self._grupos_palabras_visibles(detalle, limite)
        controles = [self._bloque_palabra(palabra, items) for palabra, items in grupos]

        if cantidad_visible < len(detalle):
            controles.append(
                ft.Container(
                    padding=self._tam(12, 7),
                    border_radius=12,
                    bgcolor=PERLA_PURPURA,
                    content=ft.Text(
                        f"Vista resumida: se muestran {cantidad_visible} de {len(detalle)} caracteres. El total se calcula completo.",
                        size=self._tam(12, 9),
                        color=TEXTO_SECUNDARIO,
                    ),
                )
            )

        return ft.Container(
            padding=self._tam(10, 6),
            bgcolor="#FFFFFF",
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=10,
            content=ft.Row(
                wrap=True,
                spacing=self._tam(8, 4),
                run_spacing=self._tam(10, 5),
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=controles,
            ),
        )

    def _grupos_palabras_visibles(self, detalle, limite):
        texto = self.resultado.get("texto_limpio", "")
        grupos = []
        indice = 0
        cantidad_visible = 0

        for palabra in texto.split():
            cantidad = len(tokenizar(palabra))
            if not cantidad:
                continue

            items = detalle[indice:indice + cantidad]
            indice += cantidad
            if not items:
                continue

            if grupos and cantidad_visible + len(items) > limite:
                break

            grupos.append((palabra, items))
            cantidad_visible += len(items)

            if cantidad_visible >= limite:
                break

        if not grupos and detalle:
            grupos.append((texto or "Texto", detalle[:limite]))
            cantidad_visible = len(grupos[0][1])

        return grupos, cantidad_visible

    def _bloque_palabra(self, palabra, items):
        es_movil = self.responsive.is_mobile()
        ancho_caracter = self._tam(74 if es_movil else 84, 48)
        separacion = self._tam(8, 4)
        ancho_maximo_base = 310 if es_movil else 620 if self.responsive.is_tablet() else 980
        ancho_maximo = ancho_maximo_base
        ancho_contenido = len(items) * ancho_caracter + max(0, len(items) - 1) * separacion + 18
        ancho_grupo = min(ancho_maximo, max(self._tam(112, 84), ancho_contenido))

        return ft.Container(
            width=ancho_grupo,
            padding=self._tam(8, 5),
            bgcolor="#FCFAFF",
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=10,
            content=ft.Column(
                tight=True,
                spacing=self._tam(7, 3),
                controls=[
                    ft.Text(
                        palabra,
                        size=self._tam(13, 9),
                        weight=ft.FontWeight.BOLD,
                        color=PURPURA_IOS,
                        no_wrap=True,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        tooltip=palabra,
                    ),
                    ft.Container(
                        height=self._tam(142, 92),
                        content=ft.Row(
                            tight=True,
                            scroll=ft.ScrollMode.AUTO,
                            spacing=separacion,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            controls=[self._bloque_caracter(item) for item in items],
                        ),
                    ),
                ],
            ),
        )

    def _bloque_caracter(self, item):
        color_hex = item.get("hex", "#FFFFFF")
        reducido = item.get("reducido", "")
        digitos = item.get("digitos_colores", [])
        tiene_reduccion = len(digitos) > 1
        ancho = self._tam(74 if self.responsive.is_mobile() else 84, 48)

        return ft.Container(
            width=ancho,
            padding=self._tam(5, 3),
            bgcolor="#FCFAFF",
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=8,
            content=ft.Column(
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=self._tam(3, 1),
                controls=[
                    ft.Container(
                        width=self._tam(50, 32),
                        height=self._tam(34, 23),
                        alignment=ft.Alignment(0, 0),
                        bgcolor=color_hex,
                        border=ft.Border.all(1.5, MARRON) if reducido == 9 else ft.Border.all(1, ft.Colors.WHITE),
                        border_radius=5,
                        content=ft.Text(item.get("letra", ""), size=self._tam(15, 10), weight=ft.FontWeight.BOLD, color=self._texto_contraste(color_hex)),
                    ),
                    ft.Text(str(item.get("valor", "")), size=self._tam(12, 8), weight=ft.FontWeight.BOLD),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=2,
                        controls=[
                            ft.Text(str(d["digito"]), size=self._tam(11, 8), weight=ft.FontWeight.BOLD)
                            for d in digitos
                        ],
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=2,
                        controls=[
                            ft.Container(
                                width=self._tam(19, 12),
                                height=self._tam(19, 12),
                                bgcolor=d["hex"],
                                border=ft.Border.all(1.4, MARRON) if d["digito"] == 9 else ft.Border.all(1, ft.Colors.GREY_400),
                            )
                            for d in digitos
                        ],
                    ),
                    ft.Container(
                        width=self._tam(28, 18),
                        height=self._tam(24, 16),
                        visible=tiene_reduccion,
                        alignment=ft.Alignment(0, 0),
                        bgcolor=color_hex,
                        border=ft.Border.all(1.4, MARRON) if reducido == 9 else ft.Border.all(1, ft.Colors.GREY_400),
                        content=ft.Text(str(reducido), size=self._tam(12, 8), weight=ft.FontWeight.BOLD, color=self._texto_contraste(color_hex)),
                    ),
                ],
            ),
        )

    def _resumen_codigo(self):
        controles = [
            self._panel_analisis_primario(),
            self._panel_analisis_secundario(),
        ]

        if self.responsive.is_mobile():
            return ft.Column(
                spacing=self._tam(10, 5),
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=controles,
            )

        return ft.Row(
            spacing=self._tam(12, 6),
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Container(expand=True, content=controles[0]),
                ft.Container(expand=True, content=controles[1]),
            ],
        )

    def _panel_analisis(self, titulo, controles):
        return ft.Container(
            padding=self._tam(12, 7),
            bgcolor=PERLA_PANEL,
            border=ft.Border.all(1.4, NEGRO),
            border_radius=12,
            content=ft.Column(
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=self._tam(11, 5),
                controls=[
                    ft.Text(titulo, size=self._tam(14, 10), weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                    *controles,
                ],
            ),
        )

    def _panel_analisis_primario(self):
        total = self.resultado.get("total_codigo", 0)
        pasos = self.resultado.get("pasos_reduccion", [])
        final = self.resultado.get("resultado_final", 0)
        final_hex = self.resultado.get("hex_final", "#FFFFFF")
        bloque_final = ft.Container(
            width=self._tam(96 if self.responsive.is_mobile() else 118, 68),
            height=self._tam(70 if self.responsive.is_mobile() else 84, 52),
            alignment=ft.Alignment(0, 0),
            bgcolor=final_hex,
            border=ft.Border.all(2, MARRON),
            border_radius=8,
            content=ft.Text(str(final), size=self._tam(34 if self.responsive.is_mobile() else 40, 24), weight=ft.FontWeight.BOLD, color=self._texto_contraste(final_hex)),
        )

        return self._panel_analisis(
            "ANALISIS PRIMARIO",
            [
                ft.Text("TOTAL DE CODIGOS:", size=self._tam(17, 11), weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                self._digitos_en_fila(total, alineacion=ft.MainAxisAlignment.CENTER, separacion=self._tam(18, 7)),
                ft.Text("PROCESO DE REDUCCION", size=self._tam(13, 9), weight=ft.FontWeight.BOLD, color=TEXTO_SECUNDARIO),
                ft.Column(
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=self._tam(10, 5),
                    controls=self._filas_proceso_reduccion(pasos),
                ),
                ft.Text("RESULTADO FINAL", size=self._tam(13, 9), weight=ft.FontWeight.BOLD, color=TEXTO_SECUNDARIO),
                bloque_final,
            ],
        )

    def _panel_analisis_secundario(self):
        valores = valores_secundarios_colores(self.resultado)
        total = sum(valores)
        limite_base = 46 if self.responsive.is_mobile() else 82
        limite = max(24, int(limite_base / max(0.62, self.escala_vista)))
        visibles = valores[:limite]
        faltantes = len(valores) - len(visibles)

        controles_suma = [self._fila_valores_secundarios(visibles)]
        if faltantes > 0:
            controles_suma.append(
                ft.Text(
                    f"+ {faltantes} valores mas incluidos en el total",
                    size=self._tam(11, 8),
                    color=TEXTO_SECUNDARIO,
                    text_align=ft.TextAlign.CENTER,
                )
            )

        return self._panel_analisis(
            "ANALISIS SECUNDARIO",
            [
                ft.Text("SUMA DE RESULTADOS EN 1 DIGITO:", size=self._tam(13, 9), weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL, text_align=ft.TextAlign.CENTER),
                ft.Column(
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=self._tam(6, 3),
                    controls=controles_suma,
                ),
                ft.Text("RESULTADO SIN REDUCIR:", size=self._tam(13, 9), weight=ft.FontWeight.BOLD, color=TEXTO_SECUNDARIO),
                self._digitos_en_fila(total, alineacion=ft.MainAxisAlignment.CENTER, separacion=self._tam(8, 4)),
            ],
        )

    def _fila_valores_secundarios(self, valores):
        controles = []
        for indice, valor in enumerate(valores):
            if indice:
                controles.append(self._signo_operacion("+", tamano=15))
            controles.append(self._cuadro_digito(valor, compacto=True))

        if not controles:
            controles.append(self._cuadro_digito(0, compacto=True))

        return ft.Row(
            wrap=True,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=self._tam(4, 2),
            run_spacing=self._tam(7, 3),
            controls=controles,
        )

    def _filas_proceso_reduccion(self, pasos):
        if not pasos:
            return []

        if len(pasos) == 1:
            return [self._digitos_en_fila(pasos[0], alineacion=ft.MainAxisAlignment.CENTER)]

        filas = []
        for indice in range(len(pasos) - 1):
            filas.append(self._fila_suma(pasos[indice], pasos[indice + 1]))
        return filas

    def _fila_suma(self, origen, resultado):
        controles = []
        digitos_origen = self._digitos_numero(origen)
        for indice, digito in enumerate(digitos_origen):
            if indice:
                controles.append(self._signo_operacion("+"))
            controles.append(self._cuadro_digito(digito))

        controles.append(self._signo_operacion("="))
        controles.extend(self._cuadro_digito(digito) for digito in self._digitos_numero(resultado))

        return ft.Row(
            wrap=True,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=self._tam(6, 3),
            run_spacing=self._tam(8, 4),
            controls=controles,
        )

    def _bloque_suma_de_sumas(self, total_suma_de_sumas, resultado_suma_de_sumas):
        if int(total_suma_de_sumas or 0) <= 9:
            return self._cuadro_digito(resultado_suma_de_sumas)

        return ft.Column(
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            controls=[
                self._fila_suma_sin_resultado(total_suma_de_sumas),
                ft.Text("=", size=self._tam(14, 10), weight=ft.FontWeight.BOLD, color=NEGRO),
                self._cuadro_digito(resultado_suma_de_sumas),
            ],
        )

    def _fila_suma_sin_resultado(self, valor):
        controles = []
        for indice, digito in enumerate(self._digitos_numero(valor)):
            if indice:
                controles.append(self._signo_operacion("+", tamano=15))
            controles.append(self._cuadro_digito(digito, compacto=True))

        return ft.Row(
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=self._tam(4, 2),
            controls=controles,
        )

    def _digitos_en_fila(self, valor, alineacion=ft.MainAxisAlignment.START, separacion=8):
        return ft.Row(
            wrap=True,
            alignment=alineacion,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=separacion,
            run_spacing=self._tam(8, 4),
            controls=[self._cuadro_digito(digito) for digito in self._digitos_numero(valor)],
        )

    @staticmethod
    def _digitos_numero(valor):
        texto = str(abs(int(valor or 0)))
        return [int(digito) for digito in texto] or [0]

    def _cuadro_digito(self, digito, compacto=False):
        color = DIGITO_COLORES.get(int(digito or 0), DIGITO_COLORES[0])["hex"]
        ancho = self._tam(42 if compacto else 54, 28 if compacto else 34)
        alto = self._tam(36 if compacto else 44, 24 if compacto else 30)
        return ft.Container(
            width=ancho,
            height=alto,
            alignment=ft.Alignment(0, 0),
            bgcolor=color,
            border=ft.Border.all(1.5, MARRON) if int(digito or 0) == 9 else ft.Border.all(1, PERLA_BORDE),
            border_radius=5,
            content=ft.Text(str(digito), size=self._tam(16 if compacto else 18, 10 if compacto else 12), weight=ft.FontWeight.BOLD, color=self._texto_contraste(color)),
        )

    def _signo_operacion(self, signo, tamano=20):
        return ft.Text(signo, size=self._tam(tamano, 10), weight=ft.FontWeight.BOLD, color=NEGRO)

    @staticmethod
    def _color_reduccion(valor):
        """Colorea cada paso por el resultado de sumar sus digitos."""
        try:
            reducido = reducir_numero(int(valor))
        except (TypeError, ValueError):
            reducido = 0
        return DIGITO_COLORES.get(reducido, DIGITO_COLORES[0])["hex"]

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
                ft.OutlinedButton("PDF", icon=ft.Icons.PICTURE_AS_PDF, on_click=self.descargar_pdf_resultado),
                ft.OutlinedButton("Compartir", icon=ft.Icons.SHARE, on_click=self.compartir_resultado),
                ft.OutlinedButton("Copiar", icon=ft.Icons.CONTENT_COPY, on_click=self.abrir_opciones_copiado),
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
            iconos_digitos = "".join(_icono_color(d.get("color", "")) for d in digitos)
            icono_final = _icono_color(item.get("color", ""))
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
            f"{_icono_color(self.resultado.get('color_final', ''))} "
            f"({_nombre_color_publico(self.resultado.get('color_final', ''))})"
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
                "alfabeto": "Resaltado",
                "suma": resumen,
                "resultado": self.resultado.get("resultado_final", ""),
                "contenido": contenido,
            }
        )
        self._confirmacion("Guardado correctamente.")

    def _obtener_file_picker_pdf(self):
        if self.file_picker_pdf is not None:
            return self.file_picker_pdf

        self.file_picker_pdf = ft.FilePicker()

        try:
            self.page.services.append(self.file_picker_pdf)
            self.page.update()
        except Exception:
            try:
                self.page.overlay.append(self.file_picker_pdf)
                self.page.update()
            except Exception:
                pass

        return self.file_picker_pdf

    def descargar_pdf_resultado(self, e=None):
        if not self.resultado:
            self._snack("Primero realice un analisis.")
            return

        try:
            archivo = exportar_pdf_colores(self.resultado, self._titulo_resultado())
        except Exception:
            self._snack("No se pudo generar el PDF.")
            return

        if hasattr(self.page, "run_task"):
            self.page.run_task(self._descargar_pdf_resultado_async, archivo)
            return

        compartir_archivo(
            self.page,
            archivo,
            "Analisis de colores PDF",
            "application/pdf",
        )

    async def _descargar_pdf_resultado_async(self, archivo):
        ruta = Path(archivo)
        try:
            datos = ruta.read_bytes()
        except Exception:
            self._snack("No se pudo leer el PDF.")
            return

        picker = self._obtener_file_picker_pdf()
        try:
            destino = await picker.save_file(
                dialog_title="Guardar analisis de colores PDF",
                file_name=ruta.name,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["pdf"],
                src_bytes=datos,
            )
        except Exception:
            self._snack("No se pudo abrir el selector de guardado.")
            return

        if not destino:
            self._snack("Guardado PDF cancelado.")
            return

        plataforma = getattr(self.page, "platform", None)
        es_movil_o_web = bool(getattr(self.page, "web", False)) or plataforma in (
            ft.PagePlatform.ANDROID,
            ft.PagePlatform.IOS,
        )

        if not es_movil_o_web:
            destino_path = Path(destino)
            if destino_path.suffix.lower() != ".pdf":
                destino_path = destino_path.with_suffix(".pdf")

            try:
                destino_path.write_bytes(datos)
                destino = str(destino_path)
            except Exception:
                self._snack("No se pudo guardar el PDF en esa ubicacion.")
                return

        self._snack(f"PDF guardado: {destino}")

    def _opciones_copiado_base(self):
        return {
            "letras_numeros": False,
            "resultados": True,
            "sumas": True,
            "cuadritos": False,
            "solo_palabras": False,
            "todo": False,
        }

    def _opciones_copiado_todo(self):
        return {
            "letras_numeros": True,
            "resultados": True,
            "sumas": True,
            "cuadritos": True,
            "solo_palabras": True,
            "todo": True,
        }

    def _marca_color_copiado(self, color, incluir_cuadrito):
        if not incluir_cuadrito:
            return ""
        color = _nombre_color_publico(color)
        if color == "GRIS":
            return "[G]"
        if color == "BLANCO":
            return "[B]"
        return _icono_color(color)

    def _numero_con_color(self, valor, color, incluir_letra, incluir_cuadrito=False):
        texto = str(valor)
        if incluir_letra:
            texto += _inicial_color(color)
        marca = self._marca_color_copiado(color, incluir_cuadrito)
        if marca:
            texto += marca
        return texto

    def _leyenda_colores_copiado(self, opciones):
        incluir_letra = bool(opciones.get("letras_numeros"))
        incluir_cuadrito = bool(opciones.get("cuadritos"))
        if not incluir_letra and not incluir_cuadrito:
            return ""

        partes = []
        for color in COLOR_ORDEN:
            etiqueta = _inicial_color(color) if incluir_letra else ""
            marca = self._marca_color_copiado(color, incluir_cuadrito)
            partes.append(f"{etiqueta}{marca}" or color)
        return "-".join(partes)

    def _token_item_copiado(self, item, opciones, detallado=False):
        letras_numeros = bool(opciones.get("letras_numeros"))
        incluir_sumas = bool(opciones.get("sumas"))
        incluir_cuadrito = bool(opciones.get("cuadritos"))
        reducido = item.get("reducido", "")
        digitos = item.get("digitos_colores", [])
        color_final = _nombre_color_publico(item.get("color", ""))
        final_texto = self._numero_con_color(reducido, color_final, letras_numeros, incluir_cuadrito)

        if detallado and incluir_sumas and len(digitos) > 1:
            partes = [
                self._numero_con_color(
                    d.get("digito", ""),
                    d.get("color", ""),
                    letras_numeros,
                    incluir_cuadrito,
                )
                for d in digitos
            ]
            return f"({''.join(partes)}={final_texto})"

        return final_texto

    def _linea_color_compartir(self, item, opciones=None):
        opciones = opciones or {}
        letras_numeros = bool(opciones.get("letras_numeros"))
        incluir_sumas = bool(opciones.get("sumas"))
        incluir_cuadrito = bool(opciones.get("cuadritos"))
        letra = item.get("letra", "")
        valor = item.get("valor", "")
        reducido = item.get("reducido", "")
        digitos = item.get("digitos_colores", [])
        color_final = _nombre_color_publico(item.get("color", ""))
        marca_final = self._marca_color_copiado(color_final, incluir_cuadrito)
        final_texto = self._numero_con_color(reducido, color_final, letras_numeros, False)

        if len(digitos) > 1 and (letras_numeros or incluir_sumas):
            partes = [
                self._numero_con_color(
                    d.get("digito", ""),
                    d.get("color", ""),
                    letras_numeros,
                    incluir_cuadrito,
                )
                for d in digitos
            ]
            operador = "=" if incluir_sumas else "->"
            marca = f" {marca_final}" if marca_final else ""
            return f"{letra}: {valor} ({''.join(partes)}{operador}{final_texto}){marca} {color_final}"

        valor_texto = self._numero_con_color(valor, color_final, letras_numeros, incluir_cuadrito)
        return f"{letra}: {valor_texto} {color_final}"

    def _color_digito_copiado(self, digito):
        try:
            return _nombre_color_publico(DIGITO_COLORES[int(digito)]["nombre"])
        except (KeyError, TypeError, ValueError):
            return "NEGRO"

    def _digito_con_color_copiado(self, digito, opciones):
        color = self._color_digito_copiado(digito)
        return self._numero_con_color(
            digito,
            color,
            bool(opciones.get("letras_numeros")),
            bool(opciones.get("cuadritos")),
        )

    def _digitos_numero_copiado(self, valor, opciones, separador=""):
        return separador.join(
            self._digito_con_color_copiado(digito, opciones)
            for digito in self._digitos_numero(valor)
        )

    def _suma_digitos_numero_copiado(self, valor, opciones):
        return self._digitos_numero_copiado(valor, opciones, " + ")

    def _fila_reduccion_copiado(self, origen, resultado, opciones):
        return (
            f"{self._suma_digitos_numero_copiado(origen, opciones)} = "
            f"{self._digitos_numero_copiado(resultado, opciones)}"
        )

    def _texto_resultados_copiado(self, opciones):
        valores_secundarios = valores_secundarios_colores(self.resultado)
        total_secundario = sum(valores_secundarios)
        pasos = self.resultado.get("pasos_reduccion", [])
        total = self.resultado.get("total_codigo", 0)
        final = pasos[-1] if pasos else self.resultado.get("resultado_final", 0)
        proceso = [
            self._fila_reduccion_copiado(pasos[indice], pasos[indice + 1], opciones)
            for indice in range(len(pasos) - 1)
        ]
        suma_secundaria = " + ".join(
            self._digito_con_color_copiado(valor, opciones)
            for valor in valores_secundarios
        )
        if not suma_secundaria:
            suma_secundaria = self._digito_con_color_copiado(0, opciones)

        lineas = [
            "Analisis primario:",
            f"Total de codigos: {self._suma_digitos_numero_copiado(total, opciones)}",
            "Proceso de reduccion:",
        ]
        lineas.extend(proceso or [self._digitos_numero_copiado(final, opciones)])
        lineas.extend(
            [
                f"Resultado primario: {self._digitos_numero_copiado(final, opciones)}",
                "",
                "Analisis secundario:",
                f"Suma de resultados en 1 digito: {suma_secundaria}",
                f"Resultado secundario: {self._digitos_numero_copiado(total_secundario, opciones)}",
            ]
        )
        return "\n".join(lineas)

    def _texto_palabras_copiado(self, opciones):
        texto_limpio = self.resultado.get("texto_limpio", "")
        palabras = [p for p in texto_limpio.split() if p.strip()]
        lineas = []
        detallado = bool(opciones.get("todo")) or bool(opciones.get("sumas"))
        for palabra in palabras:
            analisis = analizar_codigo_visual(palabra)
            final = analisis.get("resultado_final", 0)
            color = _nombre_color_publico(analisis.get("color_final", ""))
            final_texto = self._numero_con_color(
                final,
                color,
                bool(opciones.get("letras_numeros")),
                bool(opciones.get("cuadritos")),
            )
            if detallado:
                partes = [
                    self._token_item_copiado(item, opciones, detallado=True)
                    for item in analisis.get("detalle_visual", [])
                ]
                formula = " + ".join(partes)
                if formula:
                    lineas.append(f"{palabra}= {formula}={final_texto}")
                    continue
            lineas.append(f"{palabra}={final_texto}")

        if not lineas:
            return "Resultado por palabra:\nSin palabras para copiar."

        if detallado:
            return "\n".join(lineas)
        return " | ".join(lineas)

    def _texto_resumen(self, opciones=None):
        if not self.resultado:
            return ""

        incluir_encabezado = opciones is None
        opciones = opciones or self._opciones_copiado_base()
        solo_palabras = bool(opciones.get("solo_palabras")) and not bool(opciones.get("todo"))
        mostrar_detalle = not solo_palabras and bool(opciones.get("todo"))
        secciones = []

        referencia = self._titulo_resultado()
        texto_limpio = self.resultado.get("texto_limpio", "")
        texto = texto_limpio if referencia == "Analisis de colores" else f"{referencia}\n{texto_limpio}"
        leyenda = self._leyenda_colores_copiado(opciones)
        if leyenda:
            secciones.append(leyenda)
        if mostrar_detalle or solo_palabras or opciones.get("resultados"):
            secciones.append(f"Texto analizado:\n{texto}")

        if mostrar_detalle or solo_palabras:
            secciones.append(self._texto_palabras_copiado(opciones))

        if opciones.get("resultados"):
            secciones.append(self._texto_resultados_copiado(opciones))

        if not secciones:
            secciones.append(f"Texto analizado:\n{texto}")

        contenido = "\n\n".join(secciones)
        if incluir_encabezado:
            return "CODIGO ESCONDIDO 19 - COLORES\n\n" + contenido
        return contenido

    def compartir_resultado(self, e=None):
        if not self.resultado:
            self._snack("Primero realice un analisis.")
            return
        compartir_texto(self.page, self._texto_resumen(), self._titulo_resultado())

    def abrir_opciones_copiado(self, e=None):
        if not self.resultado:
            self._snack("Primero realice un analisis.")
            return

        opciones_iniciales = self._opciones_copiado_base()
        check_letras = ft.Checkbox(
            label="Letras junto a numeros",
            value=opciones_iniciales["letras_numeros"],
        )
        check_resultados = ft.Checkbox(
            label="Incluir analisis primario y secundario",
            value=opciones_iniciales["resultados"],
        )
        check_sumas = ft.Checkbox(
            label="Incluir suma de numeros",
            value=opciones_iniciales["sumas"],
        )
        check_cuadritos = ft.Checkbox(
            label="Cuadritos de colores",
            value=opciones_iniciales["cuadritos"],
        )
        check_palabras = ft.Checkbox(
            label="Solo resultado palabra por palabra",
            value=opciones_iniciales["solo_palabras"],
        )
        check_todo = ft.Checkbox(label="Todo", value=opciones_iniciales["todo"])
        preview = ft.Text(
            self._texto_resumen(opciones_iniciales),
            size=12,
            color=TEXTO_SECUNDARIO,
            selectable=True,
        )

        def leer_opciones():
            return {
                "letras_numeros": bool(check_letras.value),
                "resultados": bool(check_resultados.value),
                "sumas": bool(check_sumas.value),
                "cuadritos": bool(check_cuadritos.value),
                "solo_palabras": bool(check_palabras.value),
                "todo": bool(check_todo.value),
            }

        def refrescar(e=None):
            opciones = leer_opciones()
            preview.value = self._texto_resumen(opciones)
            try:
                self.page.update()
            except Exception:
                pass

        def cambiar_todo(e=None):
            activar = bool(check_todo.value)
            check_letras.value = activar
            check_resultados.value = activar
            check_sumas.value = activar
            check_cuadritos.value = activar
            check_palabras.value = activar
            refrescar()

        def cambiar_opcion(e=None):
            check_todo.value = all(
                bool(c.value)
                for c in (check_letras, check_resultados, check_sumas, check_cuadritos, check_palabras)
            )
            refrescar()

        for check in (check_letras, check_resultados, check_sumas, check_cuadritos, check_palabras):
            check.on_change = cambiar_opcion
        check_todo.on_change = cambiar_todo

        def cerrar(e=None):
            cerrar_dialogo(self.page, dialog)

        def copiar(e=None):
            texto = self._texto_resumen(leer_opciones())
            cerrar_dialogo(self.page, dialog)
            copiar_al_portapapeles(self.page, texto)

        dialog = ft.AlertDialog(
            title=ft.Text("Forma de copiado"),
            content=ft.Container(
                width=520,
                content=ft.Column(
                    tight=True,
                    spacing=10,
                    controls=[
                        ft.Column(
                            tight=True,
                            spacing=0,
                            controls=[
                                check_letras,
                                check_resultados,
                                check_sumas,
                                check_cuadritos,
                                check_palabras,
                                check_todo,
                            ],
                        ),
                        ft.Container(
                            height=220,
                            padding=10,
                            border=ft.Border.all(1, PERLA_BORDE),
                            border_radius=8,
                            bgcolor=SUPERFICIE_PERLADA,
                            content=ft.Column(
                                scroll=ft.ScrollMode.AUTO,
                                controls=[preview],
                            ),
                        ),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar),
                ft.ElevatedButton("Copiar", icon=ft.Icons.CONTENT_COPY, on_click=copiar),
            ],
        )
        mostrar_dialogo(self.page, dialog)

    def copiar_resultado(self):
        self.abrir_opciones_copiado()

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
            cerrar_dialogo(self.page, dialog)

        dialog = ft.AlertDialog(
            title=ft.Text("Guardado correctamente"),
            content=ft.Text(mensaje),
            actions=[ft.ElevatedButton("Aceptar", on_click=cerrar)],
        )
        mostrar_dialogo(self.page, dialog)
