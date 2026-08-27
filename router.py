# Router visual unificado - Camino 2
import flet as ft

from core.error_logger import registrar_error, ruta_log
from services.app_config_service import AppConfigService
from services.app_paths import AppPaths
from services.rutas_service import RutasService

from ui.tema import (
    AZUL,
    BLANCO,
    FONDO_APP,
    FONDO_APP_IMAGEN,
    NARANJA,
    PERLA_BORDE,
    PERLA_PURPURA,
    ROJO,
    SUPERFICIE,
    TEXTO,
    TEXTO_MUTED,
    VERDE,
    PURPURA,
    PURPURA_IOS,
    PURPURA_SUAVE,
    APP_VERSION,
    icono_estrella,
    opacidad,
    sombra_color,
    sombra_suave,
)


class Router:
    RUTAS_POR_NIVEL = {
        1: {"inicio", "biblia", "ajustes"},
        2: {"inicio", "biblia", "guardados", "calculadora", "tiempo", "ajustes"},
        3: {"inicio", "pizarra", "colores", "biblia", "tiempo", "calculadora", "guardados", "ajustes"},
        4: {"inicio", "pizarra", "colores", "biblia", "tiempo", "calculadora", "guardados", "ajustes"},
    }

    # Las vistas consultan estas capacidades para proteger sus acciones, no solo
    # para ocultar botones del menú.
    CAPACIDADES_POR_NIVEL = {
        "inicio_diccionarios": 4,
        "inicio_comparar": 4,
        "biblia_buscar": 2,
        "biblia_editar": 3,
        "biblia_color": 3,
        "biblia_marcas": 3,
        "biblia_cordero": 3,
        "biblia_diccionario_hebreo": 4,
        "biblia_aleatorio": 3,
        "tiempo_consultar": 3,
        "tiempo_guardar": 3,
        "calculadora_suma_biblia": 3,
    }

    def __init__(self, page, nivel=4):
        self.page = page
        self.nivel = max(1, min(4, int(nivel or 4)))
        self.vistas = {}
        self.fabricas_vistas = {}
        self.root = None
        self.on_cambiar_nivel = None
        self.ruta_actual = None
        self._refrescando = False
        self.menu_lateral_abierto = True
        self.orden_rutas = RutasService.orden()
        self.orden_navegacion = RutasService.orden_navegacion()
        self.meta_rutas = {ruta: (RutasService.label(ruta), RutasService.icono(ruta)) for ruta in self.orden_rutas}
        self.meta_rutas["ajustes"] = ("Ajustes", ft.Icons.SETTINGS)

    def puede_acceder(self, ruta):
        return ruta in self.RUTAS_POR_NIVEL.get(self.nivel, self.RUTAS_POR_NIVEL[4])

    def tiene_capacidad(self, capacidad):
        nivel_requerido = self.CAPACIDADES_POR_NIVEL.get(capacidad, 4)
        return self.nivel >= nivel_requerido

    def rutas_bloqueadas(self):
        return [ruta for ruta in self.orden_rutas if not self.puede_acceder(ruta)]

    def cambiar_nivel(self, e=None):
        if callable(self.on_cambiar_nivel):
            self.on_cambiar_nivel()

    def _avisar_bloqueo(self, ruta):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"{RutasService.label(ruta)} requiere un nivel superior."),
            behavior=ft.SnackBarBehavior.FLOATING,
            show_close_icon=True,
        )
        self.page.snack_bar.open = True
        try:
            self.page.update()
        except (RuntimeError, AssertionError):
            pass

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
        if not self.puede_acceder(ruta):
            if self.page.navigation_bar and self.ruta_actual in self.orden_navegacion:
                self.page.navigation_bar.selected_index = self.orden_navegacion.index(self.ruta_actual)
            self._avisar_bloqueo(ruta)
            return

        ruta_anterior = self.ruta_actual
        if ruta != ruta_anterior:
            vista_anterior = self.vistas.get(ruta_anterior)
            salir = getattr(vista_anterior, "on_leave", None)
            if callable(salir):
                try:
                    salir()
                except Exception as error:
                    registrar_error("Router.navegar.on_leave", error, f"ruta={ruta_anterior}")
        self.ruta_actual = ruta

        if self.page.navigation_bar and ruta in self.orden_navegacion:
            self.page.navigation_bar.selected_index = self.orden_navegacion.index(ruta)

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
                        ft.ElevatedButton("Volver a Inicio", icon=ft.Icons.HOME, bgcolor=PURPURA_IOS, color=BLANCO, on_click=lambda e: self.navegar("inicio")),
                    ],
                ),
            ),
        )

    def _ancho(self):
        ancho = getattr(self.page, "width", None)
        ancho_ventana = None
        if hasattr(self.page, "window"):
            ancho_ventana = getattr(self.page.window, "width", None)
        anchos = [
            valor
            for valor in (ancho, ancho_ventana)
            if isinstance(valor, (int, float)) and valor > 0
        ]
        return min(anchos) if anchos else 1200

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
                ft.Container(right=-190, top=40, width=470, height=470, bgcolor=opacidad(0.13, PURPURA), border_radius=470),
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
        preferencias = AppConfigService.leer_json(AppPaths.CONFIG_APP, {})
        mostrar_fondo = preferencias.get("fondo_decorativo", True) if isinstance(preferencias, dict) else True
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
                                ft.Container(expand=True, content=contenido),
                            ],
                        ),
                    ),
                ],
            )

        acciones_contextuales = []
        if callable(self.on_cambiar_nivel):
            acciones_contextuales.append(
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    tooltip="Cambiar de nivel",
                    icon_color=PURPURA_IOS,
                    on_click=self.cambiar_nivel,
                )
            )
        if self.puede_acceder("ajustes"):
            if acciones_contextuales:
                acciones_contextuales.append(
                    ft.Container(width=1, height=22, bgcolor=opacidad(0.7, PERLA_BORDE))
                )
            acciones_contextuales.append(
                ft.IconButton(
                    icon=ft.Icons.SETTINGS,
                    tooltip="Ajustes",
                    icon_color=PURPURA_IOS,
                    on_click=lambda e: self.navegar("ajustes"),
                )
            )

        controles_flotantes = []
        if acciones_contextuales:
            controles_flotantes.append(
                ft.Container(
                    bottom=74 if es_movil else 16,
                    right=12,
                    bgcolor=opacidad(0.94, BLANCO),
                    border=ft.Border.all(1, opacidad(0.72, PERLA_BORDE)),
                    border_radius=14,
                    shadow=sombra_suave(0.07, 12, 0, 3),
                    content=ft.Row(tight=True, spacing=2, controls=acciones_contextuales),
                )
            )

        return ft.Container(
            expand=True,
            content=ft.Stack(
                expand=True,
                controls=[
                    ft.Container(
                        expand=True,
                        on_click=self._deseleccionar_vista_actual,
                        image=(
                            ft.DecorationImage(src=FONDO_APP_IMAGEN, fit=ft.BoxFit.COVER)
                            if mostrar_fondo
                            else None
                        ),
                        bgcolor=FONDO_APP,
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
                    *controles_flotantes,
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
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(width=34, height=34, border_radius=13, bgcolor=PURPURA_SUAVE, alignment=ft.Alignment(0, 0), content=ft.Icon(icono, size=19, color=PURPURA_IOS)),
                            ft.Text(label, size=17, weight=ft.FontWeight.BOLD, color=TEXTO),
                        ],
                    ),
                ],
            ),
        )

    def _menu_lateral(self):
        compacto = not self.menu_lateral_abierto
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
                        ft.Text(
                            f"Nivel {self.nivel}",
                            size=11,
                            color=PURPURA_IOS,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Divider(height=8, color=opacidad(0.65, PERLA_BORDE)),
                        ft.Column(spacing=4, controls=[self._item_menu(ruta, compacto) for ruta in self.orden_navegacion]),
                        ft.Container(expand=True),
                        ft.Text(f"v{APP_VERSION}", size=10, color=TEXTO_MUTED, text_align=ft.TextAlign.CENTER),
                    ],
                ),
            ),
        )

    def _encabezado_menu(self, compacto):
        boton_toggle = ft.IconButton(
            icon=ft.Icons.MENU_OPEN if compacto else ft.Icons.CHEVRON_LEFT,
            tooltip="Abrir menú" if compacto else "Cerrar menú",
            icon_color=TEXTO_MUTED,
            on_click=self._alternar_menu_lateral,
        )

        if compacto:
            return ft.Column(
                tight=True,
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    boton_toggle,
                    icono_estrella(42),
                ],
            )

        return ft.Column(
            tight=True,
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(alignment=ft.MainAxisAlignment.END, controls=[boton_toggle]),
                icono_estrella(42),
                ft.Text("Código Escondido", size=16, weight=ft.FontWeight.BOLD, color=TEXTO, text_align=ft.TextAlign.CENTER),
                ft.Text(f"Versión {APP_VERSION}", size=10, color=TEXTO_MUTED, text_align=ft.TextAlign.CENTER),
            ],
        )

    def _item_menu(self, ruta, compacto=False):
        label, icono = self.meta_rutas[ruta]
        bloqueado = not self.puede_acceder(ruta)
        seleccionado = ruta == self.ruta_actual
        fondo = PERLA_PURPURA if seleccionado else ft.Colors.TRANSPARENT
        borde = opacidad(0.95, PERLA_BORDE) if seleccionado else ft.Colors.TRANSPARENT

        return ft.Container(
            height=42,
            padding=ft.Padding(left=10, top=0, right=10, bottom=0),
            bgcolor=fondo,
            border=ft.Border.all(1, borde),
            border_radius=8,
            shadow=sombra_color(PURPURA, 0.08, 12, 3) if seleccionado else None,
            on_click=lambda e, r=ruta: self.navegar(r),
            content=ft.Row(
                spacing=10,
                alignment=ft.MainAxisAlignment.CENTER if compacto else ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(
                        ft.Icons.BLOCK if bloqueado else icono,
                        size=20,
                        color=ROJO if bloqueado else (PURPURA_IOS if seleccionado else TEXTO_MUTED),
                    ),
                    ft.Text(
                        label,
                        visible=not compacto,
                        size=13,
                        weight=ft.FontWeight.BOLD if seleccionado else ft.FontWeight.NORMAL,
                        color=ROJO if bloqueado else (PURPURA_IOS if seleccionado else TEXTO),
                    ),
                ],
            ),
        )

    def _alternar_menu_lateral(self, e=None):
        self.menu_lateral_abierto = not self.menu_lateral_abierto
        self.refrescar()

    def _cambiar_desde_menu_lateral(self, e):
        indice = e.control.selected_index
        if 0 <= indice < len(self.orden_navegacion):
            self.navegar(self.orden_navegacion[indice])

    def _actualizar_barra_inferior(self):
        # En escritorio/web se usa menú lateral; en celular queda la barra inferior.
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
