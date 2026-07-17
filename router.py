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
        self.fabricas_vistas = {}
        self.root = None
        self.ruta_actual = None
        self._refrescando = False
        self.orden_rutas = RutasService.orden()
        self.meta_rutas = {ruta: (RutasService.label(ruta), RutasService.icono(ruta)) for ruta in self.orden_rutas}

    def registrar(self, nombre, vista):
        self.vistas[nombre] = vista
        self.fabricas_vistas.pop(nombre, None)

    def registrar_lazy(self, nombre, fabrica):
        self.vistas[nombre] = None
        self.fabricas_vistas[nombre] = fabrica

    def _obtener_vista_registrada(self, ruta):
        if ruta not in self.vistas:
            return None

        vista = self.vistas.get(ruta)
        if vista is None and ruta in self.fabricas_vistas:
            vista = self.fabricas_vistas[ruta]()
            self.vistas[ruta] = vista

        return vista

    @property
    def activo(self):
        return self.ruta_actual

    def iniciar(self, ruta):
        self.ruta_actual = ruta
        vista = None
        try:
            vista = self._obtener_vista_registrada(ruta)
        except Exception as error:
            registrar_error("Router.iniciar.crear_vista", error, f"ruta={ruta}")

        if vista is not None and hasattr(vista, "on_enter"):
            try:
                vista.on_enter()
            except Exception as error:
                registrar_error("Router.iniciar", error, f"ruta={ruta}")
        self.cargar_vista(ruta)

    def navegar(self, ruta):
        ruta_anterior = self.ruta_actual
        self.ruta_actual = ruta

        if self.page.navigation_bar and ruta in self.orden_rutas:
            self.page.navigation_bar.selected_index = self.orden_rutas.index(ruta)

        vista = None
        try:
            vista = self._obtener_vista_registrada(ruta)
        except Exception as error:
            registrar_error("Router.navegar.crear_vista", error, f"ruta={ruta}")

        if ruta != ruta_anterior and vista is not None and hasattr(vista, "on_enter"):
            try:
                vista.on_enter()
            except Exception as error:
                registrar_error("Router.navegar.on_enter", error, f"ruta={ruta}")

        self.cargar_vista(ruta)

    def cargar_vista(self, ruta):
        if ruta not in self.vistas:
            self.root.content = self._envolver_en_marco(self._vista_error("Vista no encontrada", f"No existe una vista registrada con el nombre: {ruta}"))
            self._actualizar_root()
            return

        try:
            vista = self._obtener_vista_registrada(ruta)
            if vista is None:
                raise RuntimeError(f"No existe una vista registrada con el nombre: {ruta}")
            contenido = vista.obtener_vista()
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

    def _deseleccionar_vista_actual(self, e=None):
        vista = self.vistas.get(self.ruta_actual)
        metodo = getattr(vista, "deseleccionar_actual", None)

        if not callable(metodo):
            return

        try:
            metodo(e)
        except Exception as error:
            registrar_error("Router.deseleccionar_vista_actual", error, f"ruta={self.ruta_actual}")

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

        es_movil = self._es_movil()
        padding = 4 if es_movil else 10
        bottom_padding = 6 if es_movil else 10
        contenido_responsivo = contenido

        if not es_movil:
            contenido_responsivo = ft.Row(
                expand=True,
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    self._menu_lateral(),
                    ft.Container(
                        expand=True,
                        padding=ft.Padding(left=10, top=10, right=12, bottom=10),
                        content=ft.Column(
                            expand=True,
                            spacing=10,
                            controls=[
                                self._barra_superior_contextual(),
                                ft.Container(expand=True, content=contenido),
                            ],
                        ),
                    ),
                ],
            )

        return ft.Container(
            expand=True,
            content=ft.Stack(
                expand=True,
                controls=[
                    ft.Container(
                        expand=True,
                        on_click=self._deseleccionar_vista_actual,
                        image=ft.DecorationImage(
                            src=FONDO_APP_IMAGEN,
                            fit=ft.BoxFit.COVER,
                        ),
                    ),

                    # Capa mínima para que el fondo sea fuerte,
                    # pero el contenido blanco no se mezcle.
                    ft.Container(
                        expand=True,
                        on_click=self._deseleccionar_vista_actual,
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
                            content=contenido_responsivo,
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
            width=86 if compacto else 236,
            padding=ft.Padding(left=10, top=10, right=0, bottom=10),
            content=ft.Container(
                expand=True,
                padding=ft.Padding(left=10, top=12, right=10, bottom=10),
                bgcolor=opacidad(0.96, BLANCO),
                border=ft.Border.all(1, opacidad(0.72, PERLA_BORDE)),
                border_radius=12,
                shadow=sombra_suave(0.055, 18, 0, 4),
                content=ft.Column(
                    expand=True,
                    spacing=8,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self._encabezado_menu(compacto),
                        ft.Divider(height=12, color=opacidad(0.65, PERLA_BORDE)),
                        ft.Column(spacing=4, controls=[self._item_menu(ruta, compacto) for ruta in self.orden_rutas]),
                        ft.Container(expand=True),
                        self._firma_menu(compacto),
                    ],
                ),
            ),
        )

    def _encabezado_menu(self, compacto):
        if compacto:
            return ft.Column(tight=True, spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[icono_estrella(42), swatches_colores(7, suave=True)])

        return ft.Column(
            tight=True,
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            controls=[
                icono_estrella(42),
                ft.Text("Código Escondido", size=16, weight=ft.FontWeight.BOLD, color=TEXTO, text_align=ft.TextAlign.CENTER),
                ft.Container(
                    padding=ft.Padding(left=12, top=4, right=12, bottom=4),
                    bgcolor=NARANJA_SUAVE,
                    border_radius=99,
                    content=ft.Text("19", size=15, weight=ft.FontWeight.BOLD, color=NARANJA),
                ),
                swatches_colores(9, suave=True),
            ],
        )

    def _firma_menu(self, compacto):
        return ft.Container(
            padding=ft.Padding(left=8, top=7, right=8, bottom=7),
            bgcolor=opacidad(0.72, GRIS_SUAVE),
            border=ft.Border.all(1, opacidad(0.65, PERLA_BORDE)),
            border_radius=8,
            content=ft.Text("CE19" if compacto else "Listo", size=11, color=TEXTO_MUTED, text_align=ft.TextAlign.CENTER),
        )

    def _item_menu(self, ruta, compacto=False):
        label, icono = self.meta_rutas[ruta]
        seleccionado = ruta == self.ruta_actual
        fondo = PERLA_VIOLETA if seleccionado else ft.Colors.TRANSPARENT
        borde = opacidad(0.95, PERLA_BORDE) if seleccionado else ft.Colors.TRANSPARENT

        return ft.Container(
            height=42,
            padding=ft.Padding(left=10, top=0, right=10, bottom=0),
            bgcolor=fondo,
            border=ft.Border.all(1, borde),
            border_radius=8,
            shadow=sombra_color(VIOLETA, 0.08, 12, 3) if seleccionado else None,
            on_click=lambda e, r=ruta: self.navegar(r),
            content=ft.Row(
                spacing=10,
                alignment=ft.MainAxisAlignment.CENTER if compacto else ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icono, size=20, color=VIOLETA_IOS if seleccionado else TEXTO_MUTED),
                    ft.Text(label, visible=not compacto, size=13, weight=ft.FontWeight.BOLD if seleccionado else ft.FontWeight.NORMAL, color=VIOLETA_IOS if seleccionado else TEXTO),
                ],
            ),
        )

    def _cambiar_desde_menu_lateral(self, e):
        indice = e.control.selected_index
        if 0 <= indice < len(self.orden_rutas):
            self.navegar(self.orden_rutas[indice])

    def _actualizar_barra_inferior(self):
        # En escritorio/web se usa menu lateral; en celular queda la barra inferior.
        if not self.page.navigation_bar:
            return
        visible = self._es_movil()
        if self.page.navigation_bar.visible != visible:
            self.page.navigation_bar.visible = visible
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
