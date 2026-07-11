import copy
import base64
import math

import flet as ft
import flet.canvas as cv

from core.app_state import state
from logica.pizarra_imagen import renderizar_lienzo_exportable_base64
from ui.clipboard import copiar_al_portapapeles
from ui.nombre_guardado import pedir_nombre_y_carpeta_guardado
from ui.responsive import Responsive
from ui.tema import (
    AZUL,
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


COLOR_MARRON_PIZARRA = "#795548"
COLOR_BLANCO_BORDE = "#FFFFFF"

COLORES_PIZARRA = [
    "#111111",
    COLOR_MARRON_PIZARRA,
    "#E53935",
    "#FB8C00",
    "#FDD835",
    "#43A047",
    "#1E88E5",
    "#8E24AA",
    "#FFFFFF",
]

ANCHO_LIENZO = 900
ALTO_LIENZO = 520


# Estilo moderno local para no depender de cambios grandes en ui.tema
FONDO_SUAVE = ft.Colors.TRANSPARENT
CARD_BLANCO = SUPERFICIE_PERLADA
BORDE_SUAVE = PERLA_BORDE
ACENTO_AZUL = AZUL
ACENTO_VIOLETA = "#8E24AA"

def _sombra_card():
    return sombra_suave(0.055, 18, 0, 6)


class PizarraView:
    def __init__(self, page, router):
        self.page = page
        self.router = router
        self.responsive = Responsive(page)

        self.lienzos = [
            {
                "nombre": "Lienzo 1",
                "fondo": "#FFFFFF",
                "objetos": [],
            }
        ]
        self.lienzo_actual = 0
        self.herramienta = "lapiz"
        self.color = "#111111"
        self.grosor = 4
        self.borrador = 24
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.viewport_ancho = ANCHO_LIENZO
        self.viewport_alto = ALTO_LIENZO
        self.texto = "Texto"
        self.portapapeles = None
        self.objeto_seleccionado = None
        self.objetos_seleccionados = []
        self.herramientas_abiertas = False
        self._moviendo_objeto = False
        self._cuadro_seleccion = None
        self._inicio = None
        self._ultimo = None
        self._trazo_actual = None
        self._cursor_activo = False
        self._cursor_punto = None
        self._modo_mover_gesto = False
        self._ultimo_offset_largo = None
        self.canvas_stack = None
        self.canvas = None
        self.overlay_stack = None
        self.screenshot_ref = ft.Ref[ft.Screenshot]()

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
                    self._selector_lienzos(),
                    self._contenido(),
                ],
            ),
        )

    def _padding(self):
        if self.responsive.is_mobile():
            return 4
        if self.responsive.is_tablet():
            return 6
        return 6

    def _barra_superior(self):
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
                                "Pizarra",
                                size=24 if self.responsive.is_mobile() else 32,
                                weight=ft.FontWeight.BOLD,
                                color=TEXTO_PRINCIPAL,
                            ),
                            ft.Text(
                                "Dibujo, formas, textos y lienzos múltiples",
                                size=12 if self.responsive.is_mobile() else 14,
                                color=TEXTO_SECUNDARIO,
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=6,
                        controls=[
                            ft.IconButton(
                                icon_size=18,
                                width=34,
                                height=34,
                                icon=ft.Icons.ARROW_BACK,
                                tooltip="Nuevo a la izquierda",
                                bgcolor="#F0F3FF",
                                on_click=lambda e: self.crear_lienzo("izquierda"),
                            ),
                            ft.IconButton(
                                icon_size=18,
                                width=34,
                                height=34,
                                icon=ft.Icons.ARROW_FORWARD,
                                tooltip="Nuevo a la derecha",
                                bgcolor="#F0F3FF",
                                on_click=lambda e: self.crear_lienzo("derecha"),
                            ),
                            ft.ElevatedButton(
                                "Guardar",
                                icon=ft.Icons.SAVE_ALT,
                                on_click=lambda e: self.guardar_pizarra(),
                            ),
                        ],
                    ),
                ],
            ),
        )

    def _selector_lienzos(self):
        return ft.Row(
            scroll=ft.ScrollMode.AUTO,
            spacing=6,
            controls=[
                ft.ElevatedButton(
                    lienzo["nombre"],
                    bgcolor=("#EEF2FF" if indice == self.lienzo_actual else CARD_BLANCO),
                    color=(ACENTO_AZUL if indice == self.lienzo_actual else TEXTO_PRINCIPAL),
                    on_click=lambda e, i=indice: self.seleccionar_lienzo(i),
                )
                for indice, lienzo in enumerate(self.lienzos)
            ],
        )

    def _contenido(self):
        herramientas = self._panel_herramientas()
        lienzo = self._lienzo_control()

        if self.responsive.is_mobile():
            return ft.Column(
                expand=True,
                spacing=10,
                controls=[
                    herramientas,
                    lienzo,
                ],
            )

        return ft.Row(
            expand=True,
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Container(
                    width=168 if self.responsive.is_tablet() else 180,
                    content=herramientas,
                ),
                lienzo,
            ],
        )

    def _panel_herramientas(self):
        if self.responsive.is_mobile() and not self.herramientas_abiertas:
            return ft.Container(
                padding=10,
                bgcolor=CARD_BLANCO,
                border=ft.Border.all(1, BORDE_SUAVE),
                border_radius=18,
                shadow=_sombra_card(),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.ElevatedButton(
                            "Herramientas",
                            icon=ft.Icons.BUILD,
                            on_click=lambda e: self.toggle_herramientas(),
                        ),
                        ft.Text(
                            self.herramienta.upper(),
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                ),
            )

        herramientas = [
            ("lapiz", ft.Icons.EDIT, "Dibujar"),
            ("seleccionar", ft.Icons.SELECT_ALL, "Seleccionar y mover"),
            ("mano", ft.Icons.PAN_TOOL, "Desplazar lienzo"),
            ("borrador", ft.Icons.AUTO_FIX_HIGH, "Borrador"),
            ("texto", ft.Icons.TITLE, "Texto"),
            ("linea", ft.Icons.HORIZONTAL_RULE, "Linea recta"),
            ("rectangulo", ft.Icons.CROP_SQUARE, "Rectangulo"),
            ("circulo", ft.Icons.CIRCLE_OUTLINED, "Circulo"),
            ("pintar", ft.Icons.FORMAT_COLOR_FILL, "Pintar fondo"),
        ]

        botones = ft.Row(
            wrap=True,
            spacing=4,
            controls=[
                ft.IconButton(
                    icon=icono,
                    icon_size=16,
                    width=30,
                    height=30,
                    tooltip=tooltip,
                    bgcolor=(
                        PERLA_VIOLETA
                        if self.herramienta == valor
                        else None
                    ),
                    on_click=lambda e, v=valor: self.cambiar_herramienta(v),
                )
                for valor, icono, tooltip in herramientas
            ],
        )

        colores = ft.Row(
            wrap=True,
            spacing=6,
            controls=[
                ft.Container(
                    width=18,
                    height=18,
                    bgcolor=color,
                    border=ft.Border.all(
                        3 if color == self.color else 2 if self._es_blanco_borde(color) else 1,
                        COLOR_MARRON_PIZARRA if self._es_blanco_borde(color) else ft.Colors.BLACK,
                    ),
                    border_radius=4,
                    tooltip="Blanco con borde marron" if self._es_blanco_borde(color) else color,
                    on_click=lambda e, c=color: self.cambiar_color(c),
                )
                for color in COLORES_PIZARRA
            ],
        )

        return ft.Container(
            padding=8,
            bgcolor=CARD_BLANCO,
            border=ft.Border.all(1, BORDE_SUAVE),
            border_radius=18,
            shadow=_sombra_card(),
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Row(
                        visible=self.responsive.is_mobile(),
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                "Herramientas",
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.IconButton(
                                icon_size=18,
                                width=34,
                                height=34,
                                icon=ft.Icons.CLOSE,
                                tooltip="Cerrar",
                                on_click=lambda e: self.toggle_herramientas(),
                            ),
                        ],
                    ),
                    ft.Text("Herramientas", size=12, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                    botones,
                    ft.Text("Color", size=12, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                    colores,
                    ft.Text("Texto", size=12, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                    ft.TextField(
                        label="Texto",
                        dense=True,
                        value=self.texto,
                        on_change=lambda e: self.actualizar_texto(e.control.value),
                        on_submit=lambda e: ocultar_teclado(self.page, e.control),
                        on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
                    ),
                    ft.Row(
                        spacing=4,
                        controls=[
                            ft.IconButton(
                                icon_size=18,
                                width=34,
                                height=34,
                                icon=ft.Icons.ZOOM_OUT,
                                tooltip="Contraer",
                                on_click=lambda e: self.cambiar_zoom(-0.1),
                            ),
                            ft.Container(
                                width=84,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Text(f"{int(self.zoom * 100)}%"),
                            ),
                            ft.IconButton(
                                icon_size=18,
                                width=34,
                                height=34,
                                icon=ft.Icons.ZOOM_IN,
                                tooltip="Expandir",
                                on_click=lambda e: self.cambiar_zoom(0.1),
                            ),
                        ],
                    ),
                    ft.Slider(
                        min=1,
                        max=18,
                        divisions=17,
                        value=self.grosor,
                        label="{value}",
                        on_change=lambda e: self.actualizar_grosor(e.control.value),
                    ),
                    ft.Slider(
                        min=8,
                        max=80,
                        divisions=18,
                        value=self.borrador,
                        label="Borrador {value}",
                        on_change=lambda e: self.actualizar_borrador(e.control.value),
                    ),
                    ft.Row(
                        wrap=True,
                        spacing=4,
                        controls=[
                            ft.IconButton(
                                icon_size=18,
                                width=34,
                                height=34,
                                icon=ft.Icons.UNDO,
                                tooltip="Deshacer",
                                on_click=lambda e: self.deshacer(),
                            ),
                            ft.IconButton(
                                icon_size=18,
                                width=34,
                                height=34,
                                icon=ft.Icons.CONTENT_COPY,
                                tooltip="Copiar ultimo",
                                on_click=lambda e: self.copiar_ultimo(),
                            ),
                            ft.IconButton(
                                icon_size=18,
                                width=34,
                                height=34,
                                icon=ft.Icons.CONTENT_PASTE,
                                tooltip="Pegar",
                                on_click=lambda e: self.pegar(),
                            ),
                            ft.IconButton(
                                icon_size=18,
                                width=34,
                                height=34,
                                icon=ft.Icons.DELETE,
                                tooltip="Limpiar lienzo",
                                on_click=lambda e: self.limpiar_lienzo(),
                            ),
                        ],
                    ),
                ],
            ),
        )

    def _lienzo_control(self):
        lienzo = self.lienzos[self.lienzo_actual]
        alto = 520

        if self.responsive.is_mobile():
            alto = 460
        elif self.responsive.is_tablet():
            alto = 500

        self.viewport_alto = alto
        self.viewport_ancho = self._ancho_area_lienzo()
        self._limitar_pan()

        self.canvas = cv.Canvas(
            expand=True,
            shapes=self._formas_lienzo(),
        )
        self.overlay_stack = ft.Stack(
            expand=True,
            controls=self._overlays_lienzo(),
        )
        self.canvas_stack = ft.Stack(
            expand=True,
            controls=[
                self.canvas,
                self.overlay_stack,
            ],
        )

        area = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            drag_interval=8,
            on_pan_start=self._pan_start,
            on_pan_update=self._pan_update,
            on_pan_end=self._pan_end,
            on_tap_down=self._tap_down,
            on_double_tap_down=self._doble_tap_down,
            on_long_press_start=self._long_press_start,
            on_long_press_end=self._long_press_end,
            content=ft.Container(
                expand=True,
                bgcolor=lienzo["fondo"],
                border=ft.Border.all(1, BORDE_SUAVE),
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=self.canvas_stack,
            ),
        )

        return ft.Container(
            expand=True,
            height=alto,
            padding=8,
            bgcolor=CARD_BLANCO,
            border=ft.Border.all(1, BORDE_SUAVE),
            border_radius=18,
            shadow=_sombra_card(),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Column(
                expand=True,
                spacing=8,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(self.lienzos[self.lienzo_actual]["nombre"], weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                            ft.Text(f"{self.herramienta.upper()} · {int(self.zoom * 100)}%", size=12, color=TEXTO_SECUNDARIO),
                        ],
                    ),
                    ft.Container(
                        expand=True,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        border_radius=12,
                        content=ft.Screenshot(
                            ref=self.screenshot_ref,
                            content=area,
                        ),
                    ),
                ],
            ),
        )

    def _ancho_area_lienzo(self):
        ancho = getattr(self.page, "width", None)

        if ancho is None and hasattr(self.page, "window"):
            ancho = getattr(self.page.window, "width", None)

        ancho = ancho or ANCHO_LIENZO

        if self.responsive.is_mobile():
            return max(280, ancho - 16)

        panel = 250 if self.responsive.is_tablet() else 280
        return max(360, ancho - panel - 64)

    def _control_objeto(self, objeto):
        tipo = objeto["tipo"]

        if tipo == "linea":
            x1, y1 = objeto["desde"]
            x2, y2 = objeto["hasta"]
            sx1, sy1 = self._pantalla((x1, y1))
            sx2, sy2 = self._pantalla((x2, y2))
            largo = max(math.hypot(sx2 - sx1, sy2 - sy1), 1)
            angulo = math.atan2(y2 - y1, x2 - x1)

            return ft.Container(
                left=sx1,
                top=sy1 - objeto["grosor"] * self.zoom / 2,
                width=largo,
                height=max(objeto["grosor"] * self.zoom, 1),
                bgcolor=objeto["color"],
                border_radius=max(objeto["grosor"] * self.zoom / 2, 1),
                rotate=ft.Rotate(
                    angle=angulo,
                    alignment=ft.Alignment(-1, 0),
                ),
            )

        if tipo == "trazo":
            return ft.Container()

        if tipo == "rectangulo":
            x1, y1 = objeto["desde"]
            x2, y2 = objeto["hasta"]
            sx1, sy1 = self._pantalla((x1, y1))
            sx2, sy2 = self._pantalla((x2, y2))

            return ft.Container(
                left=min(sx1, sx2),
                top=min(sy1, sy2),
                width=max(abs(sx2 - sx1), 4),
                height=max(abs(sy2 - sy1), 4),
                border=ft.Border.all(max(objeto["grosor"] * self.zoom, 1), objeto["color"]),
            )

        if tipo == "circulo":
            x1, y1 = objeto["desde"]
            x2, y2 = objeto["hasta"]
            sx1, sy1 = self._pantalla((x1, y1))
            sx2, sy2 = self._pantalla((x2, y2))
            medida = max(abs(sx2 - sx1), abs(sy2 - sy1), 6)

            return ft.Container(
                left=min(sx1, sx2),
                top=min(sy1, sy2),
                width=medida,
                height=medida,
                shape=ft.BoxShape.CIRCLE,
                border=ft.Border.all(max(objeto["grosor"] * self.zoom, 1), objeto["color"]),
            )

        if tipo == "texto":
            sx, sy = self._pantalla((objeto["x"], objeto["y"]))
            texto = objeto.get("texto", "")
            size = max(14, objeto["grosor"] * 5 * self.zoom)
            ancho = max(len(texto) * size * 0.68 + 24, 72)
            alto = max(size * 1.55 + 16, 42)
            indice = self._indice_objeto(objeto)
            seleccionado = indice in self._indices_seleccionados()

            return ft.GestureDetector(
                left=sx - 8,
                top=sy - 8,
                mouse_cursor=ft.MouseCursor.MOVE,
                on_tap=lambda e, obj=objeto: self._seleccionar_objeto_directo(obj),
                on_double_tap_down=lambda e, obj=objeto: self._activar_movimiento_objeto_directo(obj),
                on_long_press_start=lambda e, obj=objeto: self._activar_movimiento_objeto_directo(obj),
                on_long_press_end=lambda e: self._finalizar_movimiento_gesto(),
                on_pan_update=lambda e, obj=objeto: self._mover_objeto_directo(obj, e),
                content=ft.Container(
                    width=ancho,
                    height=alto,
                    padding=ft.Padding(left=8, top=6, right=8, bottom=6),
                    border=(
                        ft.Border.all(1.5, VIOLETA_IOS)
                        if seleccionado
                        else None
                    ),
                    border_radius=6,
                    content=ft.Text(
                        texto,
                        color=objeto["color"],
                        size=size,
                        weight=ft.FontWeight.BOLD,
                    ),
                ),
            )

        return ft.Container()

    def _pan_start(self, e):
        punto = self._punto(e.local_position)
        self._inicio = punto
        self._ultimo = punto
        self._moviendo_objeto = False

        if self.herramienta == "seleccionar":
            indice = self._objeto_en_punto(punto)

            if indice is not None:
                self.objeto_seleccionado = indice
                self.objetos_seleccionados = [indice]
                self._moviendo_objeto = True
                self._modo_mover_gesto = True
                self._cuadro_seleccion = None
            else:
                self.objeto_seleccionado = None
                self.objetos_seleccionados = []
                self._moviendo_objeto = False
                self._cuadro_seleccion = (punto, punto)
                self._redibujar_lienzo()
            return

        if self.herramienta == "borrador":
            self._cursor_activo = True
            self._cursor_punto = punto
            self.borrar_en_punto(punto)

        if self.herramienta == "lapiz":
            self._cursor_activo = True
            self._cursor_punto = punto
            self._trazo_actual = {
                "tipo": "trazo",
                "puntos": [punto],
                "color": self.color,
                "grosor": self.grosor,
            }
            self.lienzos[self.lienzo_actual]["objetos"].append(self._trazo_actual)
            self._redibujar_lienzo()

    def _pan_update(self, e):
        punto = self._punto(e.local_position)
        anterior = self._ultimo
        self._ultimo = punto

        if self.herramienta == "mano" and e.local_delta:
            velocidad = 10.0
            self.pan_x += (e.local_delta.x / self.zoom) * velocidad
            self.pan_y += (e.local_delta.y / self.zoom) * velocidad
            self._limitar_pan()
            self._redibujar_lienzo()
            return

        if self.herramienta == "seleccionar":
            seleccion = self._indices_seleccionados()

            if self._moviendo_objeto and seleccion:
                if e.local_delta:
                    dx = e.local_delta.x / max(self.zoom, 0.3)
                    dy = e.local_delta.y / max(self.zoom, 0.3)
                elif anterior:
                    dx = punto[0] - anterior[0]
                    dy = punto[1] - anterior[1]
                else:
                    dx = dy = 0

                self.mover_objetos(
                    seleccion,
                    dx,
                    dy,
                )
            elif self._cuadro_seleccion:
                self._cuadro_seleccion = (self._cuadro_seleccion[0], punto)
                self._redibujar_lienzo()
            return

        if self.herramienta == "borrador":
            self._cursor_activo = True
            self._cursor_punto = punto
            self.borrar_en_punto(punto)
            return

        if self.herramienta in ("linea", "rectangulo", "circulo") and self._inicio:
            self._redibujar_lienzo()
            return

        if self.herramienta != "lapiz" or anterior is None:
            return

        self._cursor_activo = True
        self._cursor_punto = punto

        if self._trazo_actual is None:
            self._trazo_actual = {
                "tipo": "trazo",
                "puntos": [anterior],
                "color": self.color,
                "grosor": self.grosor,
            }
            self.lienzos[self.lienzo_actual]["objetos"].append(self._trazo_actual)

        puntos = self._trazo_actual["puntos"]
        ultimo = puntos[-1]
        umbral = max(7.0, self.grosor * 1.35 / max(self.zoom, 0.3))

        if math.hypot(punto[0] - ultimo[0], punto[1] - ultimo[1]) >= umbral:
            puntos.append(punto)
            self._redibujar_lienzo()

    def _pan_end(self, e):
        if self.herramienta in ("lapiz", "borrador"):
            self._cursor_activo = False
            self._cursor_punto = None
            self._trazo_actual = None
            self._redibujar_lienzo()
            return

        if self.herramienta == "seleccionar":
            if self._cuadro_seleccion:
                seleccion = self._objetos_en_rectangulo(self._cuadro_seleccion)
                self.objetos_seleccionados = seleccion
                self.objeto_seleccionado = seleccion[0] if seleccion else None
                self._cuadro_seleccion = None
                self._redibujar_lienzo()
            self._finalizar_movimiento_gesto(redibujar=False)
            return

        if self.herramienta not in ("linea", "rectangulo", "circulo") or self._inicio is None:
            return

        fin = self._ultimo or self._inicio
        objeto = {
            "tipo": self.herramienta,
            "desde": self._inicio,
            "hasta": fin,
            "color": self.color,
            "grosor": self.grosor,
        }
        self._inicio = None
        self._ultimo = None
        self._agregar_objeto(objeto)

    def _tap_down(self, e):
        punto = self._punto(e.local_position)

        if self.herramienta == "seleccionar":
            self.objeto_seleccionado = self._objeto_en_punto(punto)
            self.objetos_seleccionados = (
                [self.objeto_seleccionado]
                if self.objeto_seleccionado is not None
                else []
            )
            self._redibujar_lienzo()
        elif self.herramienta == "borrador":
            self.borrar_en_punto(punto)
        elif self.herramienta == "texto":
            self.dialog_agregar_texto(punto)
        elif self.herramienta == "pintar":
            self.lienzos[self.lienzo_actual]["fondo"] = self.color
            self.router.refrescar()

    def _doble_tap_down(self, e):
        if self.herramienta != "seleccionar" or not e.local_position:
            return

        self._iniciar_movimiento_gesto(self._punto(e.local_position))

    def _long_press_start(self, e):
        if self.herramienta != "seleccionar" or not e.local_position:
            return

        self._ultimo_offset_largo = None
        self._iniciar_movimiento_gesto(self._punto(e.local_position))

    def _long_press_end(self, e):
        self._finalizar_movimiento_gesto()

    def _iniciar_movimiento_gesto(self, punto):
        indice = self._objeto_en_punto(punto)

        if indice is None and self._punto_en_seleccion(punto):
            seleccion = self._indices_seleccionados()
            indice = seleccion[0] if seleccion else None

        if indice is None:
            return

        self.objeto_seleccionado = indice
        self.objetos_seleccionados = [indice]
        self._modo_mover_gesto = True
        self._moviendo_objeto = True
        self._cuadro_seleccion = None
        self._ultimo = punto
        self._redibujar_lienzo()

    def _mover_seleccion_por_delta(self, dx, dy):
        seleccion = self._indices_seleccionados()

        if not seleccion:
            return

        self.mover_objetos(seleccion, dx, dy)

    def _finalizar_movimiento_gesto(self, redibujar=True):
        self._modo_mover_gesto = False
        self._moviendo_objeto = False
        self._ultimo_offset_largo = None

        if redibujar:
            self._redibujar_lienzo()

    def dialog_agregar_texto(self, punto):
        campo = ft.TextField(
            label="Texto",
            value="" if self.texto == "Texto" else self.texto,
            autofocus=True,
            min_lines=1,
            max_lines=3,
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
        )

        def cerrar(e=None):
            dialog.open = False
            self.page.update()

        def aceptar(e=None):
            ocultar_teclado(self.page, campo)
            texto = (campo.value or "").strip()

            if texto:
                self.texto = texto
                self._agregar_objeto(
                    {
                        "tipo": "texto",
                        "x": punto[0],
                        "y": punto[1],
                        "texto": texto,
                        "color": self.color,
                        "grosor": self.grosor,
                    }
                )

            cerrar()

        campo.on_submit = aceptar

        dialog = ft.AlertDialog(
            title=ft.Text("Escribir en el lienzo"),
            content=campo,
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar),
                ft.ElevatedButton("Agregar", on_click=aceptar),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _punto(self, offset):
        return (
            self._limitar(offset.x / self.zoom - self.pan_x, 0, ANCHO_LIENZO),
            self._limitar(offset.y / self.zoom - self.pan_y, 0, ALTO_LIENZO),
        )

    def _pantalla(self, punto):
        return (
            (punto[0] + self.pan_x) * self.zoom,
            (punto[1] + self.pan_y) * self.zoom,
        )

    def _es_blanco_borde(self, color):
        return (color or "").upper() == COLOR_BLANCO_BORDE

    def _color_borde_para(self, color):
        return COLOR_MARRON_PIZARRA if self._es_blanco_borde(color) else None

    def _color_visible_icono(self, color):
        return COLOR_MARRON_PIZARRA if self._es_blanco_borde(color) else color

    def _pintura_trazo(self, color, grosor, extra=0):
        return ft.Paint(
            color=color,
            stroke_width=max((grosor + extra) * self.zoom, 1),
            style=ft.PaintingStyle.STROKE,
            stroke_cap=ft.StrokeCap.ROUND,
            stroke_join=ft.StrokeJoin.ROUND,
            anti_alias=True,
        )

    def _pintura_relleno(self, color):
        return ft.Paint(
            color=color,
            style=ft.PaintingStyle.FILL,
            anti_alias=True,
        )

    def _formas_con_borde_blanco(self, creador, color, grosor):
        borde = self._color_borde_para(color)

        if not borde:
            return [creador(color, grosor, 0)]

        return [
            creador(borde, grosor, 4),
            creador(color, grosor, 0),
        ]

    def _limitar(self, valor, minimo, maximo):
        return max(minimo, min(maximo, valor))

    def _limitar_pan(self):
        min_x = min(0, self.viewport_ancho / max(self.zoom, 0.3) - ANCHO_LIENZO)
        min_y = min(0, self.viewport_alto / max(self.zoom, 0.3) - ALTO_LIENZO)
        self.pan_x = self._limitar(self.pan_x, min_x, 0)
        self.pan_y = self._limitar(self.pan_y, min_y, 0)

    def _formas_lienzo(self):
        formas = []
        lienzo = self.lienzos[self.lienzo_actual]

        for objeto in lienzo["objetos"]:
            formas.extend(self._formas_objeto(objeto))

        preview = self._objeto_previsualizacion()

        if preview:
            formas.extend(self._formas_objeto(preview))

        return formas

    def _objeto_previsualizacion(self):
        if self.herramienta not in ("linea", "rectangulo", "circulo"):
            return None

        if self._inicio is None or self._ultimo is None:
            return None

        return {
            "tipo": self.herramienta,
            "desde": self._inicio,
            "hasta": self._ultimo,
            "color": self.color,
            "grosor": self.grosor,
        }

    def _formas_objeto(self, objeto):
        tipo = objeto.get("tipo")

        if tipo == "trazo":
            return self._formas_trazo(objeto)

        color = objeto.get("color", self.color)
        grosor = objeto.get("grosor", self.grosor)

        if tipo == "linea":
            sx1, sy1 = self._pantalla(objeto["desde"])
            sx2, sy2 = self._pantalla(objeto["hasta"])

            def linea(color_actual, grosor_actual, extra):
                return cv.Line(
                    sx1,
                    sy1,
                    sx2,
                    sy2,
                    paint=self._pintura_trazo(color_actual, grosor_actual, extra),
                )

            return self._formas_con_borde_blanco(linea, color, grosor)

        if tipo == "rectangulo":
            sx1, sy1 = self._pantalla(objeto["desde"])
            sx2, sy2 = self._pantalla(objeto["hasta"])

            def rectangulo(color_actual, grosor_actual, extra):
                return cv.Rect(
                    min(sx1, sx2),
                    min(sy1, sy2),
                    max(abs(sx2 - sx1), 4),
                    max(abs(sy2 - sy1), 4),
                    paint=self._pintura_trazo(color_actual, grosor_actual, extra),
                )

            return self._formas_con_borde_blanco(rectangulo, color, grosor)

        if tipo == "circulo":
            sx1, sy1 = self._pantalla(objeto["desde"])
            sx2, sy2 = self._pantalla(objeto["hasta"])
            medida = max(abs(sx2 - sx1), abs(sy2 - sy1), 6)

            def circulo(color_actual, grosor_actual, extra):
                return cv.Oval(
                    min(sx1, sx2),
                    min(sy1, sy2),
                    medida,
                    medida,
                    paint=self._pintura_trazo(color_actual, grosor_actual, extra),
                )

            return self._formas_con_borde_blanco(circulo, color, grosor)

        if tipo == "texto":
            sx, sy = self._pantalla((objeto["x"], objeto["y"]))
            valor = objeto.get("texto", "")
            size = max(14, grosor * 5 * self.zoom)

            def texto_canvas(color_actual, dx=0, dy=0):
                return cv.Text(
                    sx + dx,
                    sy + dy,
                    value=valor,
                    style=ft.TextStyle(
                        color=color_actual,
                        size=size,
                        weight=ft.FontWeight.BOLD,
                    ),
                )

            if self._es_blanco_borde(color):
                borde = max(1.2, self.zoom * 1.4)
                return [
                    texto_canvas(COLOR_MARRON_PIZARRA, -borde, 0),
                    texto_canvas(COLOR_MARRON_PIZARRA, borde, 0),
                    texto_canvas(COLOR_MARRON_PIZARRA, 0, -borde),
                    texto_canvas(COLOR_MARRON_PIZARRA, 0, borde),
                    texto_canvas(color),
                ]

            return [texto_canvas(color)]

        return []

    def _formas_trazo(self, objeto):
        puntos = objeto.get("puntos", [])

        if not puntos:
            return []

        color = objeto.get("color", self.color)
        grosor = objeto.get("grosor", self.grosor)

        if len(puntos) == 1:
            sx, sy = self._pantalla(puntos[0])

            if self._es_blanco_borde(color):
                return [
                    cv.Circle(
                        sx,
                        sy,
                        max((grosor + 4) * self.zoom / 2, 1),
                        paint=self._pintura_relleno(COLOR_MARRON_PIZARRA),
                    ),
                    cv.Circle(
                        sx,
                        sy,
                        max(grosor * self.zoom / 2, 1),
                        paint=self._pintura_relleno(color),
                    ),
                ]

            return [
                cv.Circle(
                    sx,
                    sy,
                    max(grosor * self.zoom / 2, 1),
                    paint=self._pintura_relleno(color),
                )
            ]

        elementos = []

        sx, sy = self._pantalla(puntos[0])
        elementos.append(cv.Path.MoveTo(sx, sy))

        for punto in puntos[1:]:
            sx, sy = self._pantalla(punto)
            elementos.append(cv.Path.LineTo(sx, sy))

        def path(color_actual, grosor_actual, extra):
            return cv.Path(
                elementos,
                paint=self._pintura_trazo(color_actual, grosor_actual, extra),
            )

        return self._formas_con_borde_blanco(path, color, grosor)

    def _controles_lienzo(self):
        lienzo = self.lienzos[self.lienzo_actual]
        controles = []

        for objeto in lienzo["objetos"]:
            controles.extend(self._controles_objeto(objeto))

        controles.extend(self._overlays_lienzo())
        return controles

    def _controles_objeto(self, objeto):
        if objeto.get("tipo") == "trazo":
            return self._controles_trazo(objeto)

        return [self._control_objeto(objeto)]

    def _controles_trazo(self, objeto):
        puntos = objeto.get("puntos", [])
        grosor = objeto.get("grosor", self.grosor)
        color = objeto.get("color", self.color)

        if len(puntos) < 2:
            if not puntos:
                return []

            sx, sy = self._pantalla(puntos[0])
            medida = max(grosor * self.zoom, 2)
            return [
                ft.Container(
                    left=sx - medida / 2,
                    top=sy - medida / 2,
                    width=medida,
                    height=medida,
                    bgcolor=color,
                    shape=ft.BoxShape.CIRCLE,
                )
            ]

        return [
            self._control_objeto(
                {
                    "tipo": "linea",
                    "desde": puntos[indice],
                    "hasta": puntos[indice + 1],
                    "color": color,
                    "grosor": grosor,
                }
            )
            for indice in range(len(puntos) - 1)
        ]

    def _redibujar_lienzo(self):
        if not self.canvas or not self.overlay_stack:
            self.router.refrescar()
            return

        self.canvas.shapes.clear()
        self.canvas.shapes.extend(self._formas_lienzo())
        self.overlay_stack.controls.clear()
        self.overlay_stack.controls.extend(self._overlays_lienzo())

        try:
            self.canvas.update()
            self.overlay_stack.update()
        except (RuntimeError, AssertionError):
            self.router.refrescar()

    def _overlays_lienzo(self):
        controles = []
        objetos = self.lienzos[self.lienzo_actual]["objetos"]

        seleccion = self._indices_seleccionados()

        if self.herramienta == "seleccionar":
            for indice in range(len(objetos) - 1, -1, -1):
                controles.append(self._hitbox_objeto(indice, objetos[indice]))

        if seleccion:
            bounds = [
                self._bounds(objetos[indice])
                for indice in seleccion
                if 0 <= indice < len(objetos)
            ]

            if bounds:
                x1 = min(b[0] for b in bounds)
                y1 = min(b[1] for b in bounds)
                x2 = max(b[2] for b in bounds)
                y2 = max(b[3] for b in bounds)
                sx1, sy1 = self._pantalla((x1, y1))
                sx2, sy2 = self._pantalla((x2, y2))
                controles.append(
                    ft.Container(
                        left=min(sx1, sx2),
                        top=min(sy1, sy2),
                        width=max(abs(sx2 - sx1), 8),
                        height=max(abs(sy2 - sy1), 8),
                        border=ft.Border.all(2, ft.Colors.BLUE),
                        ignore_interactions=True,
                    )
                )

        if self._cuadro_seleccion:
            inicio, fin = self._cuadro_seleccion
            sx1, sy1 = self._pantalla(inicio)
            sx2, sy2 = self._pantalla(fin)
            controles.append(
                ft.Container(
                    left=min(sx1, sx2),
                    top=min(sy1, sy2),
                    width=max(abs(sx2 - sx1), 4),
                    height=max(abs(sy2 - sy1), 4),
                    border=ft.Border.all(1, VIOLETA_IOS),
                    bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.BLUE),
                    ignore_interactions=True,
                )
            )

        if (
            self._cursor_activo
            and self._cursor_punto
            and self.herramienta in ("lapiz", "borrador")
        ):
            sx, sy = self._pantalla(self._cursor_punto)

            if self.herramienta == "borrador":
                medida = max(self.borrador * self.zoom, 18)
                controles.append(
                    ft.Container(
                        left=sx - medida / 2,
                        top=sy - medida / 2,
                        width=medida,
                        height=medida,
                        shape=ft.BoxShape.CIRCLE,
                        border=ft.Border.all(2, ft.Colors.RED_400),
                        bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.RED),
                    )
                )
                controles.append(
                    ft.Icon(
                        ft.Icons.AUTO_FIX_HIGH,
                        left=sx + medida / 2,
                        top=sy - medida / 2,
                        size=22,
                        color=ft.Colors.RED_700,
                    )
                )
            else:
                controles.append(
                    ft.Icon(
                        ft.Icons.EDIT,
                        left=sx + 8,
                        top=sy - 28,
                        size=24,
                        color=self._color_visible_icono(self.color),
                    )
                )

        return controles

    def _hitbox_objeto(self, indice, objeto):
        x1, y1, x2, y2 = self._bounds(objeto)
        sx1, sy1 = self._pantalla((x1, y1))
        sx2, sy2 = self._pantalla((x2, y2))
        izquierda = min(sx1, sx2)
        arriba = min(sy1, sy2)
        ancho = max(abs(sx2 - sx1), 1)
        alto = max(abs(sy2 - sy1), 1)

        minimo = 36

        if ancho < minimo:
            izquierda -= (minimo - ancho) / 2
            ancho = minimo

        if alto < minimo:
            arriba -= (minimo - alto) / 2
            alto = minimo

        seleccionado = indice in self._indices_seleccionados()

        return ft.GestureDetector(
            left=izquierda,
            top=arriba,
            mouse_cursor=ft.MouseCursor.MOVE,
            drag_interval=4,
            on_tap=lambda e, i=indice: self._seleccionar_indice_directo(i),
            on_double_tap_down=lambda e, i=indice: self._iniciar_arrastre_indice(i),
            on_long_press_start=lambda e, i=indice: self._iniciar_arrastre_indice(i),
            on_pan_start=lambda e, i=indice: self._iniciar_arrastre_indice(i),
            on_pan_update=lambda e, i=indice: self._mover_indice_directo(i, e),
            on_pan_end=lambda e: self._finalizar_movimiento_gesto(),
            on_long_press_end=lambda e: self._finalizar_movimiento_gesto(),
            content=ft.Container(
                width=ancho,
                height=alto,
                bgcolor=ft.Colors.with_opacity(
                    0.03 if seleccionado else 0.01,
                    ft.Colors.BLUE,
                ),
            ),
        )

    def _indices_seleccionados(self):
        objetos = self.lienzos[self.lienzo_actual]["objetos"]
        indices = [
            indice
            for indice in self.objetos_seleccionados
            if indice is not None and 0 <= indice < len(objetos)
        ]

        if indices:
            return sorted(set(indices))

        if (
            self.objeto_seleccionado is not None
            and 0 <= self.objeto_seleccionado < len(objetos)
        ):
            return [self.objeto_seleccionado]

        return []

    def _indice_objeto(self, objeto):
        objetos = self.lienzos[self.lienzo_actual]["objetos"]

        for indice, actual in enumerate(objetos):
            if actual is objeto:
                return indice

        return None

    def _seleccionar_indice_directo(self, indice):
        objetos = self.lienzos[self.lienzo_actual]["objetos"]

        if indice is None or indice < 0 or indice >= len(objetos):
            return

        self.objeto_seleccionado = indice
        self.objetos_seleccionados = [indice]
        self._moviendo_objeto = False
        self._cuadro_seleccion = None
        self._redibujar_lienzo()

    def _iniciar_arrastre_indice(self, indice):
        objetos = self.lienzos[self.lienzo_actual]["objetos"]

        if indice is None or indice < 0 or indice >= len(objetos):
            return

        if indice not in self._indices_seleccionados():
            self.objeto_seleccionado = indice
            self.objetos_seleccionados = [indice]

        self._moviendo_objeto = True
        self._modo_mover_gesto = True
        self._cuadro_seleccion = None

    def _mover_indice_directo(self, indice, e):
        if not e.local_delta:
            return

        objetos = self.lienzos[self.lienzo_actual]["objetos"]

        if indice is None or indice < 0 or indice >= len(objetos):
            return

        if indice not in self._indices_seleccionados():
            self.objeto_seleccionado = indice
            self.objetos_seleccionados = [indice]

        self.mover_objetos(
            self._indices_seleccionados(),
            e.local_delta.x / max(self.zoom, 0.3),
            e.local_delta.y / max(self.zoom, 0.3),
        )

    def _seleccionar_objeto_directo(self, objeto):
        if self.herramienta != "seleccionar":
            return

        indice = self._indice_objeto(objeto)

        if indice is None:
            return

        self.objeto_seleccionado = indice
        self.objetos_seleccionados = [indice]
        self._moviendo_objeto = True
        self._cuadro_seleccion = None
        self._redibujar_lienzo()

    def _activar_movimiento_objeto_directo(self, objeto):
        if self.herramienta != "seleccionar":
            return

        indice = self._indice_objeto(objeto)

        if indice is None:
            return

        self.objeto_seleccionado = indice
        self.objetos_seleccionados = [indice]
        self._modo_mover_gesto = True
        self._moviendo_objeto = True
        self._cuadro_seleccion = None
        self._ultimo_offset_largo = None
        self._redibujar_lienzo()

    def _mover_objeto_directo(self, objeto, e):
        if (
            self.herramienta != "seleccionar"
            or not self._modo_mover_gesto
            or not e.local_delta
        ):
            return

        indice = self._indice_objeto(objeto)

        if indice is None:
            return

        self.objeto_seleccionado = indice
        self.objetos_seleccionados = [indice]
        self.mover_objetos(
            [indice],
            e.local_delta.x / max(self.zoom, 0.3),
            e.local_delta.y / max(self.zoom, 0.3),
        )

    def _punto_en_seleccion(self, punto):
        seleccion = self._indices_seleccionados()

        if not seleccion:
            return False

        objetos = self.lienzos[self.lienzo_actual]["objetos"]
        bounds = [
            self._bounds(objetos[indice])
            for indice in seleccion
            if 0 <= indice < len(objetos)
        ]

        if not bounds:
            return False

        x1 = min(b[0] for b in bounds)
        y1 = min(b[1] for b in bounds)
        x2 = max(b[2] for b in bounds)
        y2 = max(b[3] for b in bounds)

        return x1 <= punto[0] <= x2 and y1 <= punto[1] <= y2

    def _bounds(self, objeto):
        tipo = objeto["tipo"]
        margen = objeto.get("grosor", 1) + 4

        if tipo in ("linea", "rectangulo", "circulo"):
            x1, y1 = objeto["desde"]
            x2, y2 = objeto["hasta"]
            return (
                min(x1, x2) - margen,
                min(y1, y2) - margen,
                max(x1, x2) + margen,
                max(y1, y2) + margen,
            )

        if tipo == "trazo":
            puntos = objeto.get("puntos", [])

            if not puntos:
                return (0, 0, 0, 0)

            xs = [punto[0] for punto in puntos]
            ys = [punto[1] for punto in puntos]
            return (
                min(xs) - margen,
                min(ys) - margen,
                max(xs) + margen,
                max(ys) + margen,
            )

        if tipo == "texto":
            size = max(14, objeto.get("grosor", 4) * 5)
            ancho = max(len(objeto.get("texto", "")) * size * 0.72 + 28, 80)
            alto = max(size * 1.8 + 18, 46)
            return (
                objeto["x"] - 12,
                objeto["y"] - 12,
                objeto["x"] + ancho,
                objeto["y"] + alto,
            )

        return (0, 0, 0, 0)

    def _bounds_movimiento(self, objeto):
        tipo = objeto["tipo"]

        if tipo in ("linea", "rectangulo", "circulo"):
            x1, y1 = objeto["desde"]
            x2, y2 = objeto["hasta"]
            return (
                min(x1, x2),
                min(y1, y2),
                max(x1, x2),
                max(y1, y2),
            )

        if tipo == "trazo":
            puntos = objeto.get("puntos", [])

            if not puntos:
                return (0, 0, 0, 0)

            xs = [punto[0] for punto in puntos]
            ys = [punto[1] for punto in puntos]
            return (min(xs), min(ys), max(xs), max(ys))

        if tipo == "texto":
            size = max(14, objeto.get("grosor", 4) * 5)
            ancho = max(len(objeto.get("texto", "")) * size * 0.72 + 28, 80)
            alto = max(size * 1.8 + 18, 46)
            return (
                objeto["x"],
                objeto["y"],
                objeto["x"] + ancho,
                objeto["y"] + alto,
            )

        return self._bounds(objeto)

    def _objeto_en_punto(self, punto):
        objetos = self.lienzos[self.lienzo_actual]["objetos"]

        for indice in range(len(objetos) - 1, -1, -1):
            objeto = objetos[indice]

            if self._punto_toca_objeto(punto, objeto):
                return indice

        return None

    def _punto_toca_objeto(self, punto, objeto):
        tipo = objeto["tipo"]
        radio = max(self.borrador / 2, objeto.get("grosor", 4) + 6)

        if tipo == "linea":
            return self._distancia_segmento(
                punto,
                objeto["desde"],
                objeto["hasta"],
            ) <= radio

        if tipo == "trazo":
            puntos = objeto.get("puntos", [])

            if len(puntos) < 2:
                return bool(puntos) and math.hypot(
                    punto[0] - puntos[0][0],
                    punto[1] - puntos[0][1],
                ) <= radio

            return any(
                self._distancia_segmento(
                    punto,
                    puntos[indice],
                    puntos[indice + 1],
                ) <= radio
                for indice in range(len(puntos) - 1)
            )

        x1, y1, x2, y2 = self._bounds(objeto)
        return x1 <= punto[0] <= x2 and y1 <= punto[1] <= y2

    def _objetos_en_rectangulo(self, rectangulo):
        inicio, fin = rectangulo
        rx1, rx2 = sorted((inicio[0], fin[0]))
        ry1, ry2 = sorted((inicio[1], fin[1]))
        objetos = self.lienzos[self.lienzo_actual]["objetos"]
        seleccion = []

        for indice in range(len(objetos) - 1, -1, -1):
            x1, y1, x2, y2 = self._bounds(objetos[indice])

            if x1 <= rx2 and x2 >= rx1 and y1 <= ry2 and y2 >= ry1:
                seleccion.append(indice)

        return seleccion

    def _distancia_segmento(self, punto, desde, hasta):
        px, py = punto
        x1, y1 = desde
        x2, y2 = hasta
        dx = x2 - x1
        dy = y2 - y1

        if dx == 0 and dy == 0:
            return math.hypot(px - x1, py - y1)

        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        cx = x1 + t * dx
        cy = y1 + t * dy
        return math.hypot(px - cx, py - cy)

    def mover_objetos(self, indices, dx, dy):
        dx, dy = self._delta_limitado_objetos(indices, dx, dy)

        for indice in indices:
            self.mover_objeto(indice, dx, dy, refrescar=False)

        self._redibujar_lienzo()

    def _delta_limitado_objetos(self, indices, dx, dy):
        objetos = self.lienzos[self.lienzo_actual]["objetos"]
        bounds = [
            self._bounds_movimiento(objetos[indice])
            for indice in indices
            if indice is not None and 0 <= indice < len(objetos)
        ]

        if not bounds:
            return dx, dy

        x1 = min(b[0] for b in bounds)
        y1 = min(b[1] for b in bounds)
        x2 = max(b[2] for b in bounds)
        y2 = max(b[3] for b in bounds)

        if x1 + dx < 0:
            dx = -x1

        if y1 + dy < 0:
            dy = -y1

        if x2 + dx > ANCHO_LIENZO:
            dx = ANCHO_LIENZO - x2

        if y2 + dy > ALTO_LIENZO:
            dy = ALTO_LIENZO - y2

        return dx, dy

    def mover_objeto(self, indice, dx, dy, refrescar=True):
        objetos = self.lienzos[self.lienzo_actual]["objetos"]

        if indice is None or indice < 0 or indice >= len(objetos):
            return

        objeto = objetos[indice]

        if "puntos" in objeto:
            objeto["puntos"] = [
                (punto[0] + dx, punto[1] + dy)
                for punto in objeto["puntos"]
            ]
        elif "desde" in objeto:
            objeto["desde"] = (objeto["desde"][0] + dx, objeto["desde"][1] + dy)
            objeto["hasta"] = (objeto["hasta"][0] + dx, objeto["hasta"][1] + dy)
        else:
            objeto["x"] += dx
            objeto["y"] += dy

        if refrescar:
            self.router.refrescar()

    def borrar_en_punto(self, punto):
        objetos = self.lienzos[self.lienzo_actual]["objetos"]
        restantes = []
        cambio = False

        for objeto in objetos:
            if objeto.get("tipo") == "trazo":
                partes = self._trazo_sin_borrado(objeto, punto)
                restantes.extend(partes)
                cambio = cambio or len(partes) != 1 or partes[0] is not objeto
            elif self._punto_toca_objeto(punto, objeto):
                cambio = True
            else:
                restantes.append(objeto)

        if cambio:
            self.lienzos[self.lienzo_actual]["objetos"] = restantes
            self.objeto_seleccionado = None
            self.objetos_seleccionados = []
            self._redibujar_lienzo()

    def _trazo_sin_borrado(self, objeto, punto):
        puntos = objeto.get("puntos", [])
        radio = max(self.borrador / 2, objeto.get("grosor", 4) + 4)

        if len(puntos) < 2:
            if self._punto_toca_objeto(punto, objeto):
                return []
            return [objeto]

        partes = []
        actual = []
        hubo_borrado = False

        for indice in range(len(puntos) - 1):
            desde = puntos[indice]
            hasta = puntos[indice + 1]
            toca = self._distancia_segmento(punto, desde, hasta) <= radio

            if toca:
                hubo_borrado = True

                if len(actual) >= 2:
                    nuevo = copy.deepcopy(objeto)
                    nuevo["puntos"] = actual
                    partes.append(nuevo)

                actual = []
                continue

            if not actual:
                actual = [desde, hasta]
            else:
                if actual[-1] != desde:
                    actual.append(desde)
                actual.append(hasta)

        if len(actual) >= 2:
            nuevo = copy.deepcopy(objeto)
            nuevo["puntos"] = actual
            partes.append(nuevo)

        return partes if hubo_borrado else [objeto]

    def _agregar_objeto(self, objeto):
        self.lienzos[self.lienzo_actual]["objetos"].append(objeto)
        self._redibujar_lienzo()

    def crear_lienzo(self, lado):
        nuevo = {
            "nombre": f"Lienzo {len(self.lienzos) + 1}",
            "fondo": "#FFFFFF",
            "objetos": [],
        }

        if lado == "izquierda":
            self.lienzos.insert(self.lienzo_actual, nuevo)
        else:
            self.lienzos.insert(self.lienzo_actual + 1, nuevo)
            self.lienzo_actual += 1

        self.router.refrescar()

    def seleccionar_lienzo(self, indice):
        self.lienzo_actual = indice
        self.router.refrescar()

    def cambiar_herramienta(self, herramienta):
        self.herramienta = herramienta
        self._cursor_activo = False
        self._cursor_punto = None
        self._inicio = None
        self._ultimo = None
        self._trazo_actual = None
        if self.responsive.is_mobile():
            self.herramientas_abiertas = False
        self.router.refrescar()

    def toggle_herramientas(self):
        self.herramientas_abiertas = not self.herramientas_abiertas
        self.router.refrescar()

    def cambiar_color(self, color):
        self.color = color

        if self.herramienta == "seleccionar":
            objetos = self.lienzos[self.lienzo_actual]["objetos"]

            for indice in self._indices_seleccionados():
                if 0 <= indice < len(objetos):
                    objetos[indice]["color"] = color

        self.router.refrescar()

    def actualizar_texto(self, texto):
        self.texto = texto

    def actualizar_grosor(self, valor):
        self.grosor = int(float(valor))
        objetos = self.lienzos[self.lienzo_actual]["objetos"]
        seleccion = self._indices_seleccionados()

        for indice in seleccion:
            if 0 <= indice < len(objetos):
                objetos[indice]["grosor"] = self.grosor

        if self._trazo_actual is not None:
            self._trazo_actual["grosor"] = self.grosor

        if seleccion or self._trazo_actual is not None:
            self._redibujar_lienzo()

    def actualizar_borrador(self, valor):
        self.borrador = int(float(valor))

    def cambiar_zoom(self, delta):
        self.zoom = max(0.3, min(2.5, self.zoom + delta))
        self._limitar_pan()
        self.router.refrescar()

    def deshacer(self):
        objetos = self.lienzos[self.lienzo_actual]["objetos"]

        if objetos:
            objetos.pop()
            self.router.refrescar()

    def limpiar_lienzo(self):
        self.lienzos[self.lienzo_actual]["objetos"].clear()
        self.router.refrescar()

    def copiar_ultimo(self):
        objetos = self.lienzos[self.lienzo_actual]["objetos"]

        if objetos:
            self.portapapeles = copy.deepcopy(objetos[-1])
            copiar_al_portapapeles(self.page, str(self.portapapeles))

    def pegar(self):
        if not self.portapapeles:
            return

        objeto = copy.deepcopy(self.portapapeles)

        if "puntos" in objeto:
            objeto["puntos"] = [
                (punto[0] + 20, punto[1] + 20)
                for punto in objeto["puntos"]
            ]
        elif "desde" in objeto:
            objeto["desde"] = (objeto["desde"][0] + 20, objeto["desde"][1] + 20)
            objeto["hasta"] = (objeto["hasta"][0] + 20, objeto["hasta"][1] + 20)
        else:
            objeto["x"] += 20
            objeto["y"] += 20

        self._agregar_objeto(objeto)

    def guardar_pizarra(self):
        if not hasattr(self.router, "page"):
            return

        nombre_sugerido = self.lienzos[self.lienzo_actual].get("nombre", "Pizarra")
        pedir_nombre_y_carpeta_guardado(
            self.page,
            "Guardar pizarra",
            nombre_sugerido,
            state.carpetas,
            "PIZARRAS",
            self._guardar_pizarra_con_nombre,
            "La pizarra se guardara como imagen en PIZARRAS.",
        )

    def _guardar_pizarra_con_nombre(self, nombre, carpeta=None):
        lienzo = self._lienzo_compacto_para_guardar(
            self.lienzos[self.lienzo_actual]
        )
        lienzo["nombre"] = nombre
        self.lienzos[self.lienzo_actual]["nombre"] = nombre
        imagen = renderizar_lienzo_exportable_base64(lienzo)
        imagen_base64 = imagen.get("base64")
        destino = carpeta or state.carpetas.obtener_por_nombre("PIZARRAS")
        registro = {
            "tipo": "pizarra",
            "carpeta": destino["nombre"] if destino else "PIZARRAS",
            "carpeta_id": destino["id"] if destino else 2,
            "nombre": nombre,
            "palabra": nombre,
            "referencia": "Pizarra guardada",
            "alfabeto": "",
            "suma": "",
            "resultado": len(lienzo["objetos"]),
            "contenido": lienzo,
        }

        if imagen_base64:
            registro["imagen_base64"] = imagen_base64
            registro["imagen_mime"] = imagen.get("mime", "image/jpeg")
            registro["imagen_extension"] = imagen.get("extension", "jpg")
        else:
            captura = self._capturar_lienzo_base64()

            if captura:
                registro["imagen_base64"] = captura

        state.guardados.guardar(registro)
        ruta = (
            state.carpetas.obtener_ruta_texto(destino["id"])
            if destino
            else "PIZARRAS"
        )
        self._confirmar_guardado(f"Pizarra guardada correctamente en {ruta}.")

    def _lienzo_compacto_para_guardar(self, lienzo):
        compacto = copy.deepcopy(lienzo)
        objetos = []

        for objeto in compacto.get("objetos", []):
            if objeto.get("tipo") != "trazo":
                objetos.append(objeto)
                continue

            puntos = objeto.get("puntos", [])

            if len(puntos) <= 2:
                objetos.append(objeto)
                continue

            filtrados = [puntos[0]]
            distancia_minima = max(4.0, objeto.get("grosor", 3) * 0.9)

            for punto in puntos[1:-1]:
                ultimo = filtrados[-1]

                if math.hypot(punto[0] - ultimo[0], punto[1] - ultimo[1]) >= distancia_minima:
                    filtrados.append(punto)

            if filtrados[-1] != puntos[-1]:
                filtrados.append(puntos[-1])

            objeto["puntos"] = filtrados
            objetos.append(objeto)

        compacto["objetos"] = objetos
        return compacto

    def _capturar_lienzo_base64(self):
        try:
            screenshot = self.screenshot_ref.current

            if screenshot is None:
                return None

            captura = screenshot.capture(pixel_ratio=2, delay=50)

            if not captura:
                return None

            if isinstance(captura, str):
                return captura

            return base64.b64encode(captura).decode("ascii")
        except Exception:
            return None

    def _confirmar_guardado(self, mensaje):
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
