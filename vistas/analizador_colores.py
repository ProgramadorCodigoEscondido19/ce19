import colorsys
import json
import math

import flet as ft

from core.app_state import state
from logica.analizador_colores import (
    COLORES,
    analizar_colores,
    color_base_mezcla,
    exportar_csv,
    exportar_json,
    guardar_historial,
    hex_color_puro,
)
from ui.clipboard import copiar_al_portapapeles
from ui.nombre_guardado import pedir_nombre_y_carpeta_guardado
from ui.responsive import Responsive
from ui.tema import (
    PERLA_BORDE,
    PERLA_PANEL,
    SUPERFICIE_PERLADA,
    TEXTO_PRINCIPAL,
    TEXTO_SECUNDARIO,
    sombra_suave,
)
from ui.teclado import ocultar_teclado




# Estilo moderno local para Colores
FONDO_SUAVE = ft.Colors.TRANSPARENT
CARD_BLANCO = SUPERFICIE_PERLADA
BORDE_SUAVE = PERLA_BORDE

def _sombra_card():
    return sombra_suave(0.055, 18, 0, 6)

TEXTO_PRUEBA = (
    "que si confesares con tu boca que Jesus es el Senor, y creyeres en tu "
    "corazon que Dios le levanto de los muertos, seras salvo. Porque con el "
    "corazon se cree para justicia, pero con la boca se confiesa para salvacion."
)


class AnalizadorColoresView:
    def __init__(self, page, router):
        self.page = page
        self.router = router
        self.responsive = Responsive(page)
        self.resultado = None

        self.texto = ft.TextField(
            label="Texto",
            multiline=True,
            min_lines=3,
            max_lines=5,
            on_change=lambda e: None,
            on_focus=lambda e: self._preparar_entrada_texto(e.control),
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
        )
        self.panel_resultado = ft.Column(
            expand=True,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )
        opciones_colores = [
            ft.dropdown.Option(color["nombre"])
            for color in COLORES.values()
        ]
        self.mezcla_color_a = ft.Dropdown(
            label="Color 1",
            value=COLORES[2]["nombre"],
            dense=True,
            options=opciones_colores,
            on_select=self.actualizar_mezcla_colores,
        )
        self.mezcla_color_b = ft.Dropdown(
            label="Color 2",
            value=COLORES[6]["nombre"],
            dense=True,
            options=[
                ft.dropdown.Option(color["nombre"])
                for color in COLORES.values()
            ],
            on_select=self.actualizar_mezcla_colores,
        )
        self.mezcla_modo = ft.Dropdown(
            label="Mezcla",
            value="Pigmentos",
            dense=True,
            options=[
                ft.dropdown.Option("Pigmentos"),
                ft.dropdown.Option("Luz"),
            ],
            on_select=self.actualizar_mezcla_colores,
        )
        self.mezcla_muestra = ft.Container(
            width=42,
            height=42,
            border=ft.Border.all(1, ft.Colors.GREY_500),
            border_radius=6,
        )
        self.mezcla_texto = ft.Text(
            "",
            weight=ft.FontWeight.BOLD,
        )
        self.actualizar_mezcla_colores()

    def _on_resize(self, e):
        self.router.refrescar()

    def obtener_vista(self):
        self.page.on_resize = self._on_resize

        return ft.Container(
            expand=True,
            bgcolor=FONDO_SUAVE,
            padding=self._padding(),
            content=ft.Column(
                expand=True,
                spacing=6,
                controls=[
                    self._contenido(),
                ],
            ),
        )

    def _encabezado(self):
        return ft.Container(
            padding=ft.Padding(left=18, top=16, right=18, bottom=16),
            bgcolor=CARD_BLANCO,
            border=ft.Border.all(1, BORDE_SUAVE),
            border_radius=20,
            shadow=_sombra_card(),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        tight=True,
                        spacing=2,
                        controls=[
                            ft.Text(
                                "Colores",
                                size=24 if self.responsive.is_mobile() else 32,
                                weight=ft.FontWeight.BOLD,
                                color=TEXTO_PRINCIPAL,
                            ),
                            ft.Text(
                                "Analisis de letras, mezclas y predominancia cromatica",
                                size=12 if self.responsive.is_mobile() else 14,
                                color=TEXTO_SECUNDARIO,
                            ),
                        ],
                    ),
                    ft.ElevatedButton(
                        "Analizar",
                        icon=ft.Icons.COLOR_LENS,
                        on_click=self.analizar,
                    ),
                ],
            ),
        )

    def _padding(self):
        if self.responsive.is_mobile():
            return 4
        if self.responsive.is_tablet():
            return 6
        return 6

    def _contenido(self):
        entrada = self._panel_entrada()
        salida = ft.Container(
            expand=True,
            content=self.panel_resultado,
        )

        if self.responsive.is_mobile():
            return ft.Column(
                expand=True,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    entrada,
                    salida,
                ],
            )

        return ft.Row(
            expand=True,
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Container(
                    expand=1,
                    content=ft.Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        spacing=8,
                        controls=[entrada],
                    ),
                ),
                ft.Container(
                    expand=1,
                    content=salida,
                ),
            ],
        )

    def _panel_entrada(self):
        return ft.Container(
            padding=8,
            bgcolor=CARD_BLANCO,
            border=ft.Border.all(1, BORDE_SUAVE),
            border_radius=18,
            shadow=_sombra_card(),
            content=ft.Column(
                spacing=6,
                controls=[
                    self.texto,
                    ft.Row(
                        wrap=True,
                        spacing=8,
                        controls=[
                            ft.ElevatedButton(
                                "Analizar",
                                icon=ft.Icons.COLOR_LENS,
                                on_click=self.analizar,
                            ),
                            ft.ElevatedButton(
                                "Guardar",
                                icon=ft.Icons.SAVE_ALT,
                                on_click=self.guardar_resultado,
                            ),
                            ft.OutlinedButton(
                                "Limpiar",
                                icon=ft.Icons.CLEAR,
                                on_click=self.limpiar,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.SAVE_ALT,
                                tooltip="Exportar JSON",
                                on_click=lambda e: self.exportar("json"),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CONTENT_COPY,
                                tooltip="Copiar",
                                on_click=lambda e: self.copiar_resultado(),
                            ),
                        ],
                    ),
                    self._mezclador_colores(),
                ],
            ),
        )

    def _mezclador_colores(self):
        controles = [
            ft.Text(
                "Mezclar colores",
                size=13,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Row(
                wrap=True,
                spacing=8,
                run_spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(width=112, content=self.mezcla_color_a),
                    ft.Container(width=112, content=self.mezcla_color_b),
                    ft.Container(width=112, content=self.mezcla_modo),
                    self.mezcla_muestra,
                    ft.Container(
                        width=150,
                        content=self.mezcla_texto,
                    ),
                ],
            ),
        ]

        return ft.Container(
            padding=8,
            bgcolor=CARD_BLANCO,
            border=ft.Border.all(1, BORDE_SUAVE),
            border_radius=16,
            content=ft.Column(
                tight=True,
                spacing=8,
                controls=controles,
            ),
        )

    def _leyenda_colores(self):
        return ft.Row(
            wrap=True,
            spacing=6,
            controls=[
                ft.Container(
                    padding=ft.Padding(left=8, top=4, right=8, bottom=4),
                    bgcolor=color["hex"],
                    border=ft.Border.all(1, ft.Colors.GREY_400),
                    border_radius=4,
                    content=ft.Text(
                        f"{numero} {color['nombre']}",
                        size=11,
                        color=ft.Colors.BLACK if numero in (4, 9) else ft.Colors.WHITE,
                    ),
                )
                for numero, color in COLORES.items()
            ],
        )

    def _hex_por_nombre(self, nombre):
        for color in COLORES.values():
            if color["nombre"] == nombre:
                return color["hex"]

        return "#000000"

    def _rgb_desde_hex(self, valor):
        valor = valor.lstrip("#")
        return tuple(
            int(valor[indice:indice + 2], 16)
            for indice in (0, 2, 4)
        )

    def _hex_desde_rgb(self, rgb):
        return "#{:02X}{:02X}{:02X}".format(
            *[
                max(0, min(255, int(round(canal))))
                for canal in rgb
            ]
        )

    def actualizar_mezcla_colores(self, e=None):
        color_a = self._rgb_desde_hex(
            self._hex_por_nombre(self.mezcla_color_a.value)
        )
        color_b = self._rgb_desde_hex(
            self._hex_por_nombre(self.mezcla_color_b.value)
        )

        if self.mezcla_modo.value == "Luz":
            resultado = tuple(
                255 - ((255 - color_a[indice]) * (255 - color_b[indice]) / 255)
                for indice in range(3)
            )
            modo = "luz"
        else:
            resultado = self._mezcla_pigmentos(color_a, color_b)
            modo = "pigmento"

        nombre_resultado = color_base_mezcla(
            tuple(
                max(0, min(255, int(round(canal))))
                for canal in resultado
            )
        )
        hex_resultado = hex_color_puro(nombre_resultado)
        self.mezcla_muestra.bgcolor = hex_resultado
        self.mezcla_texto.value = f"{nombre_resultado} ({modo})"

        try:
            self.mezcla_muestra.update()
            self.mezcla_texto.update()
        except (RuntimeError, AssertionError):
            pass

    def _mezcla_pigmentos(self, color_a, color_b):
        hsv_a = colorsys.rgb_to_hsv(
            color_a[0] / 255,
            color_a[1] / 255,
            color_a[2] / 255,
        )
        hsv_b = colorsys.rgb_to_hsv(
            color_b[0] / 255,
            color_b[1] / 255,
            color_b[2] / 255,
        )
        peso_a = max(hsv_a[1], 0.08)
        peso_b = max(hsv_b[1], 0.08)
        x = (
            math.cos(hsv_a[0] * math.tau) * peso_a
            + math.cos(hsv_b[0] * math.tau) * peso_b
        )
        y = (
            math.sin(hsv_a[0] * math.tau) * peso_a
            + math.sin(hsv_b[0] * math.tau) * peso_b
        )

        if abs(x) < 0.0001 and abs(y) < 0.0001:
            h = (hsv_a[0] + hsv_b[0]) / 2
        else:
            h = (math.atan2(y, x) / math.tau) % 1

        s = min(1, (hsv_a[1] + hsv_b[1]) / 2 * 1.08)
        v = min(1, (hsv_a[2] + hsv_b[2]) / 2 * 0.94 + 0.05)
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return (r * 255, g * 255, b * 255)

    def limpiar(self, e=None):
        self.texto.value = ""
        self.resultado = None
        self.panel_resultado.controls.clear()
        self.page.update()

    def analizar(self, e=None):
        ocultar_teclado(self.page, self.texto)
        texto = self.texto.value or ""

        if not texto.strip():
            self._snack("Ingrese un texto para analizar.")
            return

        self.resultado = analizar_colores(texto)
        guardar_historial(self.resultado)
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

    def cargar_prueba(self):
        self.texto.value = TEXTO_PRUEBA
        self.page.update()
        self.analizar()

    def _render_resultado(self):
        resultado = self.resultado
        self.panel_resultado.controls.clear()

        if not resultado:
            self.page.update()
            return

        self.panel_resultado.controls.append(self._tarjeta_resultado(resultado))
        self.page.update()

    def _tarjeta_resultado(self, resultado):
        mezcla = resultado["mezcla"]
        texto = self.texto.value or ""

        def ver_detalle(e=None):
            self._mostrar_detalle_resultado(resultado)

        return ft.Card(
            elevation=4,
            content=ft.Container(
                padding=15,
                bgcolor=CARD_BLANCO,
                border=ft.Border.all(1, BORDE_SUAVE),
                border_radius=18,
                content=ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            controls=[
                                ft.Container(
                                    expand=True,
                                    content=ft.Text(
                                        (
                                            texto[:60] + "..."
                                            if len(texto) > 60
                                            else texto or "Analisis de colores"
                                        ),
                                        size=20,
                                        weight=ft.FontWeight.BOLD,
                                        color=TEXTO_PRINCIPAL,
                                        max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.CONTENT_COPY,
                                    tooltip="Copiar",
                                    on_click=lambda e: self.copiar_resultado(),
                                ),
                            ],
                        ),
                        ft.Row(
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(
                                    width=34,
                                    height=34,
                                    bgcolor=mezcla["hex"],
                                    border=ft.Border.all(1, ft.Colors.GREY_500),
                                    border_radius=7,
                                ),
                                ft.Text(
                                    f"Resultado: {mezcla['nombre']}",
                                    size=22,
                                    weight=ft.FontWeight.BOLD,
                                    color=TEXTO_PRINCIPAL,
                                ),
                            ],
                        ),
                        ft.Text(
                            f"Total de letras: {resultado['total_letras']}",
                            color=TEXTO_SECUNDARIO,
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.OutlinedButton(
                                    "Ver detalle",
                                    icon=ft.Icons.VISIBILITY,
                                    on_click=ver_detalle,
                                ),
                                ft.ElevatedButton(
                                    "Guardar",
                                    icon=ft.Icons.SAVE_ALT,
                                    on_click=self.guardar_resultado,
                                ),
                            ],
                        ),
                    ],
                ),
            ),
        )

    def _mostrar_detalle_resultado(self, resultado):
        mezcla = resultado["mezcla"]
        conteo = "\n".join(
            f"{nombre}: {cantidad}"
            for nombre, cantidad in resultado["conteo"].items()
            if cantidad > 0
        )

        def cerrar(e=None):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Detalle del analisis"),
            content=ft.Container(
                width=520,
                content=ft.Column(
                    tight=True,
                    spacing=8,
                    controls=[
                        ft.Text(f"Total de letras: {resultado['total_letras']}", weight=ft.FontWeight.BOLD),
                        ft.Text(f"Mezcla total: {mezcla['nombre']}"),
                        ft.Text("Conteo:", weight=ft.FontWeight.BOLD),
                        ft.Text(conteo or "Sin datos", selectable=True),
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

    def _ranking(self, ranking):
        return ft.Column(
            spacing=4,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(color, weight=ft.FontWeight.BOLD),
                        ft.Text(str(cantidad)),
                    ],
                )
                for color, cantidad in ranking
            ],
        )

    def _barras(self, resultado):
        maximo = max(resultado["conteo"].values(), default=1) or 1
        controles = []

        for numero, color in COLORES.items():
            cantidad = resultado["conteo"].get(color["nombre"], 0)
            controles.append(
                ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=78,
                            content=ft.Text(color["nombre"], size=12),
                        ),
                        ft.Container(
                            height=18,
                            width=max(8, 220 * cantidad / maximo),
                            bgcolor=color["hex"],
                            border=ft.Border.all(1, ft.Colors.GREY_400),
                        ),
                        ft.Text(str(cantidad), size=12),
                    ],
                )
            )

        return ft.Column(spacing=5, controls=controles)

    def _secuencia(self, resultado):
        detalle = resultado["detalle"][:240]

        return ft.Container(
            padding=10,
            bgcolor=PERLA_PANEL,
            border_radius=8,
            content=ft.Row(
                wrap=True,
                spacing=4,
                run_spacing=4,
                controls=[
                    ft.Container(
                        width=16,
                        height=16,
                        bgcolor=item["hex"],
                        border=ft.Border.all(1, ft.Colors.GREY_500),
                        tooltip=f"{item['letra']} {item['color']}",
                    )
                    for item in detalle
                ],
            ),
        )

    def exportar(self, tipo):
        if not self.resultado:
            self._snack("Primero realice un analisis.")
            return

        if tipo == "csv":
            archivo = exportar_csv(self.resultado)
        else:
            archivo = exportar_json(self.resultado)

        self._snack(f"Exportado en {archivo}")

    def copiar_resultado(self):
        if not self.resultado:
            self._snack("Primero realice un analisis.")
            return

        copiar_al_portapapeles(
            self.page,
            json.dumps(
                self.resultado,
                indent=2,
                ensure_ascii=False,
            )
        )
        self._snack("Resultado copiado.")

    def guardar_resultado(self, e=None):
        if not self.resultado:
            self._snack("Primero realice un analisis.")
            return

        pedir_nombre_y_carpeta_guardado(
            self.page,
            "Guardar analisis",
            "Analisis de colores",
            state.carpetas,
            "COLORES",
            self._guardar_resultado_con_nombre,
            "Se guardara en la carpeta COLORES.",
        )

    def _guardar_resultado_con_nombre(self, nombre, carpeta=None):
        texto = self.texto.value or ""
        predominantes = ", ".join(self.resultado.get("predominantes", [])) or "Sin datos"
        destino = carpeta or state.carpetas.obtener_por_nombre("COLORES")

        state.guardados.guardar(
            {
                "tipo": "analisis_colores",
                "carpeta": destino["nombre"] if destino else "COLORES",
                "carpeta_id": destino["id"] if destino else 4,
                "nombre": nombre,
                "palabra": nombre or texto[:80] or "Analisis de colores",
                "referencia": "Colores",
                "alfabeto": "",
                "suma": json.dumps(self.resultado, ensure_ascii=False),
                "resultado": predominantes,
                "contenido": self.resultado,
            }
        )
        ruta = (
            state.carpetas.obtener_ruta_texto(destino["id"])
            if destino
            else "COLORES"
        )
        self._confirmacion(f"Guardado correctamente en {ruta}.")

    def _snack(self, mensaje):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje),
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
            actions=[
                ft.ElevatedButton("Aceptar", on_click=cerrar),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
