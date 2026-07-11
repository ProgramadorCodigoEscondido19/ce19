# Router visual unificado - Camino 2
import flet as ft

from core.error_logger import registrar_error, ruta_log
from services.rutas_service import RutasService

from ui.tema import (
    AZUL,
    AZUL_SUAVE,
    BLANCO,
    DORADO_IOS,
    FONDO_APP,
    FONDO_APP_IMAGEN,
    GRIS_SUAVE,
    NARANJA,
    NARANJA_SUAVE,
    PERLA_BORDE,
    PERLA_PANEL,
    PERLA_VIOLETA,
    SUPERFICIE,
    TEXTO,
    TEXTO_MUTED,
    VERDE,
    VIOLETA,
    VIOLETA_IOS,
    VIOLETA_SUAVE,
    banda_colores,
    icono_estrella,
    opacidad,
    sombra_color,
    sombra_suave,
    swatches_colores,
)


class Router:
    def __init__(self, page):
        self.page = page
        self.vistas = {}
        self.root = None
        self.ruta_actual = None
        self._refrescando = False
        self.orden_rutas = RutasService.orden()
        self.meta_rutas = {ruta: (RutasService.label(ruta), RutasService.icono(ruta)) for ruta in self.orden_rutas}

    def registrar(self, nombre, vista):
        self.vistas[nombre] = vista

    @property
    def activo(self):
        return self.ruta_actual

    def iniciar(self, ruta):
        self.ruta_actual = ruta
        if ruta in self.vistas and hasattr(self.vistas[ruta], "on_enter"):
            try:
                self.vistas[ruta].on_enter()
            except Exception as error:
                registrar_error("Router.iniciar", error, f"ruta={ruta}")
        self.cargar_vista(ruta)

    def navegar(self, ruta):
        ruta_anterior = self.ruta_actual
        self.ruta_actual = ruta

        if self.page.navigation_bar and ruta in self.orden_rutas:
            self.page.navigation_bar.selected_index = self.orden_rutas.index(ruta)

        if ruta != ruta_anterior and ruta in self.vistas and hasattr(self.vistas[ruta], "on_enter"):
            try:
                self.vistas[ruta].on_enter()
            except Exception as error:
                registrar_error("Router.navegar.on_enter", error, f"ruta={ruta}")

        self.cargar_vista(ruta)

    def cargar_vista(self, ruta):
        if ruta not in self.vistas:
            self.root.content = self._envolver_en_marco(self._vista_error("Vista no encontrada", f"No existe una vista registrada con el nombre: {ruta}"))
            self._actualizar_root()
            return

        try:
            contenido = self.vistas[ruta].obtener_vista()
        except Exception as error:
            registrar_error("Router.cargar_vista", error, f"ruta={ruta}")
            contenido = self._vista_error("La vista no pudo cargarse", f"{error}\n\nSe guardó el detalle en: {ruta_log()}")

        self.root.content = self._envolver_en_marco(contenido)
        self._actualizar_root()

    def _actualizar_root(self):
        try:
            self.root.update()
        except (RuntimeError, AssertionError):
            try:
                self.page.update()
            except Exception:
                pass

    def _vista_error(self, titulo, detalle):
        return ft.Container(
            expand=True,
            alignment=ft.Alignment(0, 0),
            padding=24,
            content=ft.Container(
                width=650,
                padding=26,
                bgcolor=SUPERFICIE,
                border=ft.Border.all(1, PERLA_BORDE),
                border_radius=28,
                shadow=sombra_suave(0.10, 30, 1, 10),
                content=ft.Column(
                    tight=True,
                    spacing=14,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=46, color=NARANJA),
                        ft.Text(titulo, size=24, weight=ft.FontWeight.BOLD, color=TEXTO, text_align=ft.TextAlign.CENTER),
                        ft.Text(detalle, size=13, color=TEXTO_MUTED, text_align=ft.TextAlign.CENTER, selectable=True),
                        ft.ElevatedButton("Volver a Inicio", icon=ft.Icons.HOME, bgcolor=VIOLETA_IOS, color=BLANCO, on_click=lambda e: self.navegar("inicio")),
                    ],
                ),
            ),
        )

    def _ancho(self):
        ancho = getattr(self.page, "width", None)
        if ancho is None and hasattr(self.page, "window"):
            ancho = getattr(self.page.window, "width", None)
        return ancho or 1200

    def _es_movil(self):
        return self._ancho() < 700

    def _fondo_luminoso(self, contenido):
        return ft.Stack(
            expand=True,
            controls=[
                ft.Container(left=-210, top=-180, width=520, height=520, bgcolor=opacidad(0.12, AZUL), border_radius=520),
                ft.Container(right=-190, top=40, width=470, height=470, bgcolor=opacidad(0.13, VIOLETA), border_radius=470),
                ft.Container(left=220, bottom=-260, width=620, height=620, bgcolor=opacidad(0.12, NARANJA), border_radius=620),
                ft.Container(right=260, bottom=-190, width=390, height=390, bgcolor=opacidad(0.10, VERDE), border_radius=390),
                contenido,
            ],
        )

    def _envolver_en_marco(self, contenido):
        # Panel lateral eliminado: la app usa solo la barra inferior en PC, notebook y celular.
        # No reservamos 90 px abajo porque la NavigationBar de Flet ya ocupa su propio espacio;
        # reservarlo recortaba las páginas.
        # El fondo global se aplica acá para TODAS las páginas normales.
        # La intro no pasa por este marco, por eso no se modifica.
        self._actualizar_barra_inferior()

        padding = 4 if self._es_movil() else 8
        bottom_padding = 6 if self._es_movil() else 8

        return ft.Container(
            expand=True,
            content=ft.Stack(
                expand=True,
                controls=[
                    ft.Container(
                        expand=True,
                        image=ft.DecorationImage(
                            src=FONDO_APP_IMAGEN,
                            fit=ft.BoxFit.COVER,
                        ),
                    ),

                    # Capa mínima para que el fondo sea fuerte,
                    # pero el contenido blanco no se mezcle.
                    ft.Container(
                        expand=True,
                        bgcolor=opacidad(0.06, FONDO_APP),
                    ),

                    ft.SafeArea(
                        expand=True,
                        minimum_padding=0,
                        content=ft.Container(
                            expand=True,
                            padding=ft.Padding(
                                left=padding,
                                top=padding,
                                right=padding,
                                bottom=bottom_padding,
                            ),
                            content=contenido,
                        ),
                    ),
                ],
            ),
        )
    def _barra_superior_contextual(self):
        label, icono = self.meta_rutas.get(self.ruta_actual, ("Inicio", ft.Icons.HOME))
        return ft.Container(
            height=54,
            padding=ft.Padding(left=16, top=0, right=16, bottom=0),
            bgcolor=opacidad(0.82, BLANCO),
            border=ft.Border.all(1, opacidad(0.75, PERLA_BORDE)),
            border_radius=24,
            shadow=sombra_suave(0.055, 18, 0, 5),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(width=34, height=34, border_radius=13, bgcolor=VIOLETA_SUAVE, alignment=ft.Alignment(0, 0), content=ft.Icon(icono, size=19, color=VIOLETA_IOS)),
                            ft.Text(label, size=17, weight=ft.FontWeight.BOLD, color=TEXTO),
                        ],
                    ),
                    swatches_colores(9, suave=True),
                ],
            ),
        )

    def _menu_lateral(self):
        compacto = self._ancho() < 1100
        return ft.Container(
            width=96 if compacto else 250,
            padding=ft.Padding(left=16, top=18, right=0, bottom=18),
            content=ft.Container(
                expand=True,
                padding=ft.Padding(left=12, top=18, right=12, bottom=14),
                bgcolor=opacidad(0.90, BLANCO),
                border=ft.Border.all(1, opacidad(0.80, PERLA_BORDE)),
                border_radius=32,
                shadow=sombra_suave(0.11, 34, 1, 12),
                content=ft.Column(
                    expand=True,
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self._encabezado_menu(compacto),
                        ft.Container(height=8),
                        ft.Column(spacing=7, controls=[self._item_menu(ruta, compacto) for ruta in self.orden_rutas]),
                        ft.Container(expand=True),
                        self._firma_menu(compacto),
                    ],
                ),
            ),
        )

    def _encabezado_menu(self, compacto):
        if compacto:
            return ft.Column(tight=True, spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[icono_estrella(46), swatches_colores(8, suave=True)])

        return ft.Column(
            tight=True,
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                icono_estrella(62),
                ft.Text("Código Escondido", size=16, weight=ft.FontWeight.BOLD, color=TEXTO, text_align=ft.TextAlign.CENTER),
                ft.Container(
                    padding=ft.Padding(left=12, top=4, right=12, bottom=4),
                    bgcolor=NARANJA_SUAVE,
                    border_radius=99,
                    content=ft.Text("19", size=15, weight=ft.FontWeight.BOLD, color=NARANJA),
                ),
                swatches_colores(11, suave=True),
            ],
        )

    def _firma_menu(self, compacto):
        return ft.Container(
            padding=ft.Padding(left=10, top=9, right=10, bottom=9),
            bgcolor=GRIS_SUAVE,
            border_radius=18,
            content=ft.Text("CE19" if compacto else "Sistema de estudio", size=11, color=TEXTO_MUTED, text_align=ft.TextAlign.CENTER),
        )

    def _item_menu(self, ruta, compacto=False):
        label, icono = self.meta_rutas[ruta]
        seleccionado = ruta == self.ruta_actual
        fondo = PERLA_VIOLETA if seleccionado else ft.Colors.TRANSPARENT
        borde = opacidad(0.95, PERLA_BORDE) if seleccionado else ft.Colors.TRANSPARENT

        return ft.Container(
            height=46,
            padding=ft.Padding(left=12, top=0, right=12, bottom=0),
            bgcolor=fondo,
            border=ft.Border.all(1, borde),
            border_radius=19,
            shadow=sombra_color(VIOLETA, 0.12, 18, 5) if seleccionado else None,
            on_click=lambda e, r=ruta: self.navegar(r),
            content=ft.Row(
                spacing=12,
                alignment=ft.MainAxisAlignment.CENTER if compacto else ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icono, size=22, color=VIOLETA_IOS if seleccionado else TEXTO_MUTED),
                    ft.Text(label, visible=not compacto, size=14, weight=ft.FontWeight.BOLD if seleccionado else ft.FontWeight.NORMAL, color=VIOLETA_IOS if seleccionado else TEXTO),
                ],
            ),
        )

    def _cambiar_desde_menu_lateral(self, e):
        indice = e.control.selected_index
        if 0 <= indice < len(self.orden_rutas):
            self.navegar(self.orden_rutas[indice])

    def _actualizar_barra_inferior(self):
        # La barra inferior queda activa en todos los tamaños de pantalla.
        if not self.page.navigation_bar:
            return
        if self.page.navigation_bar.visible is not True:
            self.page.navigation_bar.visible = True
            try:
                self.page.update()
            except (RuntimeError, AssertionError):
                pass

    def refrescar(self):
        if self._refrescando or self.root is None or self.ruta_actual is None:
            return
        self._refrescando = True
        try:
            self.cargar_vista(self.ruta_actual)
        finally:
            self._refrescando = False
