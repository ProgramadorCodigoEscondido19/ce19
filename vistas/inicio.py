from ui.responsive import Responsive
from ui.responsive_layout import ResponsiveLayout
import flet as ft
from services.codificador_service import CodificadorService
from services.notificacion_service import NotificacionService
from vistas.componentes import tarjeta_resultado
from ui.sidebar import AppSidebar
from ui.compartir import compartir_texto
from ui.tema import (
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
from core.app_state import state
from core.event_bus import bus


class InicioView:
    # =======================================
    # F (INIT)
    # =======================================
    def __init__(self, page, router):
        self.page = page
        self.router = router
        self.historial = state.historial
        self.guardados = state.guardados
        self.carpetas = state.carpetas
        self.responsive = Responsive(self.page)
        self.layout = ResponsiveLayout(self.page, self.responsive)
        self.page.on_resize = self._on_resize

        self.carpeta_selector_id = 1
        self.carpeta_selector_nombre = "TARJETAS"
        self.carpeta_selector_ruta = "TARJETAS"
        self.selector_raiz_id = None

        self.selector_expandidas = set()
        self.selector_arbol = None
        self.dialog_selector = None

        self.codificador_service = CodificadorService()
        self.motor = self.codificador_service.motor
        self.crear_controles()
        state.bind(self._on_state_change)
        self.sidebar = AppSidebar(
            self.page,
            self.responsive,
            self.build_sidebar_content,
            self.router,
        )
        self.selector_carpeta = ft.TextField(
            label="Destino",
            value="TARJETAS",
            expand=True,
            read_only=True,
        )
        bus.subscribe("guardados_updated", self._on_guardados_update)
        bus.subscribe("historial_updated", self._on_historial_update)

    # =======================================
    # F (ON RESIZE)
    # =======================================
    def _on_resize(self, e):
        self.router.refrescar()

    def toggle_sidebar(self, e=None):
        self.sidebar_visible = not self.sidebar_visible
        self.page.update()

    def get_page(self):
        return self.page

    # ======================================
    # F() CONSTRUIR RAMA SELECTOR
    # ======================================
    def _construir_selector_rama(self, lista, padre=None, nivel=0):
        hijos = self.carpetas.obtener_hijos(padre)
        for carpeta in hijos:
            lista.controls.append(self.crear_item_selector(carpeta, nivel))
            if carpeta["id"] in self.selector_expandidas:
                self._construir_selector_rama(lista, carpeta["id"], nivel + 1)

    # ======================================
    # F() CREAR SELECTOR ARBOL
    # ======================================
    def crear_selector_arbol(self):
        lista = ft.ListView(
            expand=True,
            spacing=2,
            padding=ft.Padding(left=0, top=0, right=12, bottom=0),
        )

        raiz_id = getattr(self, "selector_raiz_id", None)

        if raiz_id:
            raiz = self.carpetas.obtener_por_id(raiz_id)
            if raiz:
                lista.controls.append(self.crear_item_selector(raiz, 0))
                if raiz["id"] in self.selector_expandidas:
                    self._construir_selector_rama(lista, raiz["id"], 1)
        else:
            self._construir_selector_rama(lista)

        return lista

    # ======================================
    # F() CREAR ITEM SELECTOR
    # ======================================
    def crear_item_selector(self, carpeta, nivel=0):
        seleccionado = (
            self.carpeta_selector_id is not None
            and self.carpeta_selector_id == carpeta["id"]
        )

        flecha = (
            ft.Icons.KEYBOARD_ARROW_DOWN
            if carpeta["id"] in self.selector_expandidas
            else ft.Icons.KEYBOARD_ARROW_RIGHT
        )

        return ft.Container(
            content=ft.Container(
                padding=ft.Padding(
                    left=10 + (nivel * 20),
                    top=4,
                    bottom=4,
                    right=5,
                ),
                bgcolor=(
                    ft.Colors.with_opacity(0.15, ft.Colors.BLUE)
                    if seleccionado
                    else None
                ),
                border_radius=6,
                content=ft.Row(
                    spacing=5,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.GestureDetector(
                            mouse_cursor=ft.MouseCursor.CLICK,
                            on_tap=lambda e: self.expandir_selector(carpeta["id"]),
                            content=ft.Icon(flecha, size=18),
                        ),
                        ft.GestureDetector(
                            mouse_cursor=ft.MouseCursor.CLICK,
                            on_tap=lambda e: self.seleccionar_selector(carpeta),
                            on_double_tap=lambda e: (
                                self.seleccionar_selector(carpeta),
                                self.expandir_selector(carpeta["id"]),
                            ),
                            content=ft.Row(
                                tight=True,
                                spacing=5,
                                controls=[
                                    ft.Icon(
                                        ft.Icons.FOLDER,
                                        color=ft.Colors.YELLOW_700,
                                        size=20,
                                    ),
                                    ft.Text(
                                        carpeta["nombre"],
                                        weight=(
                                            ft.FontWeight.BOLD if seleccionado else None
                                        ),
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            ),
        )

    # ======================================
    # F() EXPANDIR SELECTOR
    # ======================================
    def expandir_selector(self, id_carpeta):
        if id_carpeta in self.selector_expandidas:
            self.selector_expandidas.remove(id_carpeta)
        else:
            self.selector_expandidas.add(id_carpeta)

        if self.dialog_selector and self.dialog_selector.open:
            self.dialog_selector.content = ft.Container(
                width=350,
                height=450,
                content=self.crear_selector_arbol(),
            )

        self.page.update()

    # ======================================
    # F() SELECCIONAR SELECTOR
    # ======================================
    def seleccionar_selector(self, carpeta):
        ruta = self.carpetas.obtener_ruta(carpeta["id"])
        self.carpeta_selector_id = carpeta["id"]
        self.carpeta_selector_nombre = carpeta["nombre"]
        self.carpeta_selector_ruta = " > ".join(c["nombre"] for c in ruta)
        self.selector_carpeta.value = self.carpeta_selector_ruta

        if self.dialog_selector and self.dialog_selector.open:
            self.dialog_selector.content = ft.Container(
                width=350,
                height=450,
                content=self.crear_selector_arbol(),
            )

        self.page.update()

    # =====================================================
    # CREAR CONTROLES
    # =====================================================
    def crear_controles(self):
        self.btn_menu = ft.IconButton(
            icon=ft.Icons.MENU,
            on_click=lambda e: self.sidebar.toggle(),
        )

        self.resultado_actual = ft.Column()
        self.ultimo_registro = None

        self.titulo = ft.Text(
            "CODIFICADOR ALFABÉTICO",
            size=30,
            weight=ft.FontWeight.BOLD,
        )

        self.palabra_input = ft.TextField(
            label="Ingrese texto",
            multiline=True,
            min_lines=1,
            max_lines=2,
            expand=False,
            text_size=18,
            border_radius=18,
            filled=True,
            bgcolor="#FCFAFF",
            border_color="#E7DCEB",
            focused_border_color="#A44BA8",
            on_submit=self.codificar,
            on_click=lambda e: self._activar_campo_texto(e.control),
        )

        self.boton = ft.ElevatedButton(
            "CODIFICAR",
            width=250,
            height=45,
            icon=ft.Icons.PLAY_ARROW,
            on_click=self.codificar,
        )

        self.boton_limpiar = ft.OutlinedButton(
            "Limpiar",
            height=45,
            icon=ft.Icons.CLEAR,
            on_click=self.limpiar_codificador,
        )

        self.mensaje_exito = ft.Text(
            "",
            visible=False,
            color="green",
            size=16,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )

        self.mensaje_error = ft.Text(
            "",
            visible=False,
            color=ft.Colors.RED,
            size=16,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )

        panel_arbol = self.crear_selector_arbol()
        self.panel_izquierdo = ft.Container(
            width=300,
            padding=10,
            bgcolor=PERLA_PANEL,
            content=ft.Column(
                expand=True,
                spacing=0,
                controls=[panel_arbol],
            ),
        )

        self.selector_arbol = ft.ListView(
            expand=True,
            spacing=2,
            padding=ft.Padding(left=0, top=0, right=12, bottom=0),
        )

    def _tarjeta_visual(self, content, padding=20, expand=False):
        return ft.Container(
            expand=expand,
            padding=padding,
            bgcolor=SUPERFICIE_PERLADA,
            border=ft.Border.all(1, PERLA_BORDE),
            border_radius=20,
            shadow=sombra_suave(0.055, 18, 0, 6),
            content=content,
        )

    # =====================================================
    # OBTENER VISTA
    # =====================================================
    def obtener_vista(self):
        self.page.on_resize = self._on_resize
        return ft.Container(
            expand=True,
            padding=self._padding_responsive(),
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                controls=[self._contenido_principal()],
            ),
        )

    # =====================================================
    # CONTENIDO PRINCIPAL
    # =====================================================
    def _contenido_principal(self):
        es_movil = self.responsive.is_mobile()
        es_tablet = self.responsive.is_tablet()

        self.titulo.size = 22 if es_movil else 26 if es_tablet else 30
        self.boton.width = None if es_movil else 220 if es_tablet else 250
        self.palabra_input.max_lines = 4 if es_movil else 2

        acciones = ft.Row(
            wrap=True,
            spacing=10,
            run_spacing=8,
            controls=[
                self.boton,
                self.boton_limpiar,
            ],
        )

        panel_formulario = self._tarjeta_visual(
            ft.Column(
                spacing=14,
                controls=[
                    ft.Text(
                        "Entrada",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=TEXTO_PRINCIPAL,
                    ),
                    self.palabra_input,
                    ft.Text(
                        "Modo fijo de codificación",
                        size=13,
                        color=TEXTO_SECUNDARIO,
                    ),
                    ft.Container(
                        padding=ft.Padding(left=12, top=6, right=12, bottom=6),
                        bgcolor=PERLA_VIOLETA,
                        border=ft.Border.all(1, PERLA_BORDE),
                        border_radius=16,
                        content=ft.Text(
                            "Código 19",
                            size=13,
                            color=VIOLETA_IOS,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ),
                    acciones,
                    self.mensaje_exito,
                    self.mensaje_error,
                ],
            ),
            expand=not es_movil,
        )

        panel_resultado = self._tarjeta_visual(
            ft.Column(
                expand=not es_movil,
                spacing=12,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                "Resultado",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=TEXTO_PRINCIPAL,
                            ),
                            ft.Icon(ft.Icons.INSIGHTS, color=VIOLETA_IOS, size=22),
                        ],
                    ),
                    ft.Container(expand=not es_movil, content=self.resultado_actual),
                ],
            ),
            expand=not es_movil,
        )

        if es_movil:
            return ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=10,
                controls=[
                    panel_formulario,
                    panel_resultado,
                ],
            )

        return ft.Row(
            expand=True,
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Container(expand=1, content=panel_formulario),
                ft.Container(expand=1, content=panel_resultado),
            ],
        )

    def _padding_responsive(self):
        if self.responsive.is_mobile():
            return 4
        if self.responsive.is_tablet():
            return 6
        return 8

    def limpiar_codificador(self, e=None):
        self.palabra_input.value = ""
        self.resultado_actual.controls.clear()
        self.ultimo_registro = None
        self.mensaje_error.visible = False
        self.mensaje_exito.visible = False
        self.page.update()

    # =====================================================
    # CODIFICAR
    # =====================================================
    def codificar(self, e):
        ocultar_teclado(self.page)
        texto = self.palabra_input.value.strip()

        if not texto:
            self.mensaje_error.value = "Debe ingresar una palabra o texto para codificar."
            self.mensaje_error.visible = True
            self.page.update()
            return

        self.mensaje_error.visible = False

        # Modo único visible en interfaz.
        # Internamente queda fijo en una sola configuración.
        datos = self.codificador_service.codificar(
            self.palabra_input.value,
            usar_ch=True,
            usar_ll=True,
            usar_ñ=True,
        )

        self.historial.agregar(datos)
        self.mostrar_resultado(datos)
        self.page.update()

    def _activar_campo_texto(self, campo):
        campo.can_request_focus = True
        try:
            campo.update()
        except (RuntimeError, AssertionError):
            pass

    # =====================================================
    # MOSTRAR RESULTADO
    # =====================================================
    def mostrar_resultado(self, registro):
        self.ultimo_registro = registro
        self.resultado_actual.controls.clear()

        tarjeta = tarjeta_resultado(
            page=self.page,
            palabra=registro["palabra"],
            alfabeto=registro["alfabeto"],
            suma=registro["suma"],
            resultado=registro["resultado"],
            texto_boton="Guardar",
            funcion=lambda e, r=registro: self.confirmar_guardado(r),
            funcion_compartir=lambda e, r=registro: self.compartir_tarjeta(r),
        )

        self.resultado_actual.controls.append(tarjeta)
        self.page.update()

    def compartir_tarjeta(self, registro):
        compartir_texto(
            self.page,
            (
                "CODIGO ESCONDIDO 19\n\n"
                f"Texto: {registro.get('palabra', '')}\n"
                f"Abecedario: {registro.get('alfabeto', '')}\n"
                f"Suma: {registro.get('suma', '')}\n"
                f"Resultado: {registro.get('resultado', '')}"
            ),
            "Tarjeta CODIGO ESCONDIDO 19",
        )

    # =====================================================
    # CONFIRMAR GUARDADO
    # =====================================================
    def confirmar_guardado(self, registro):
        es_movil = self.responsive.is_mobile()
        destino = self.carpetas.obtener_por_nombre("TARJETAS")
        self.carpeta_selector_id = destino["id"] if destino else 1
        self.carpeta_selector_nombre = "TARJETAS"
        self.carpeta_selector_ruta = "TARJETAS"
        self.selector_raiz_id = destino["id"] if destino else 1

        self.selector_expandidas.clear()
        self.selector_expandidas.add(self.selector_raiz_id)
        self.selector_carpeta = ft.TextField(
            label="Destino",
            value=self.carpeta_selector_ruta,
            expand=True,
            read_only=True,
        )

        nombre = ft.TextField(
            label="Nombre",
            hint_text="Ej: Apocalipsis 13:18",
            autofocus=False,
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
        )

        def abrir_selector():
            arbol = self.crear_selector_arbol()
            self.dialog_selector.content = ft.Container(
                width=320 if self.responsive.is_mobile() else 350,
                height=420 if self.responsive.is_mobile() else 450,
                content=arbol,
            )
            self.dialog_selector.open = True
            self.page.update()

        def cerrar(e):
            dialog.open = False
            self.page.update()

        def guardar(e):
            ocultar_teclado(self.page, nombre)
            nuevo_registro = registro.copy()
            nuevo_registro["nombre"] = nombre.value
            nuevo_registro["tipo"] = "tarjeta"
            carpeta_destino = self.carpetas.obtener_por_id(self.carpeta_selector_id) or destino

            if carpeta_destino:
                nuevo_registro["carpeta"] = carpeta_destino["nombre"]
                nuevo_registro["carpeta_id"] = carpeta_destino["id"]
            else:
                nuevo_registro["carpeta"] = "TARJETAS"
                nuevo_registro["carpeta_id"] = 1

            self.guardados.guardar(nuevo_registro)
            self.carpeta_selector_id = destino["id"] if destino else 1
            self.carpeta_selector_nombre = "TARJETAS"
            self.carpeta_selector_ruta = "TARJETAS"
            self.selector_carpeta.value = "TARJETAS"
            self.selector_raiz_id = destino["id"] if destino else 1
            self.selector_expandidas.clear()

            dialog.open = False
            self.page.update()
            NotificacionService.exito(self.page, "Guardado correctamente.")

            self.resultado_actual.controls.clear()
            self.page.update()

        nombre.on_submit = guardar

        def cerrar_selector():
            self.dialog_selector.open = False
            self.page.update()

        def confirmar_selector():
            if self.carpeta_selector_ruta:
                self.selector_carpeta.value = self.carpeta_selector_ruta
            self.dialog_selector.open = False
            self.page.update()

        self.dialog_selector = ft.AlertDialog(
            title=ft.Text("Seleccionar carpeta"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: cerrar_selector()),
                ft.ElevatedButton("Seleccionar", on_click=lambda e: confirmar_selector()),
            ],
        )

        dialog = ft.AlertDialog(
            title=ft.Text("Guardar resultado"),
            content=ft.Container(
                width=320 if es_movil else 420,
                content=ft.Column(
                    tight=True,
                    spacing=10,
                    controls=[
                        ft.Text(registro["palabra"], no_wrap=False),
                        nombre,
                        ft.Row(
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                self.selector_carpeta,
                                ft.IconButton(
                                    icon=ft.Icons.FOLDER_OPEN,
                                    tooltip="Elegir carpeta",
                                    on_click=lambda e: abrir_selector(),
                                ),
                            ],
                        ),
                    ],
                ),
            ),
            inset_padding=ft.Padding(14, 18, 14, 18) if es_movil else None,
            actions_alignment=ft.MainAxisAlignment.END,
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar),
                ft.ElevatedButton("Guardar", on_click=guardar),
            ],
        )

        if dialog not in self.page.overlay:
            self.page.overlay.append(dialog)
        if self.dialog_selector not in self.page.overlay:
            self.page.overlay.append(self.dialog_selector)
        dialog.open = True
        self.page.update()

    # ======================================================
    # OCULTAR MENSAJE
    # ======================================================
    def ocultar_mensaje_exito(self):
        try:
            self.mensaje_exito.visible = False
            self.page.update()
        except RuntimeError:
            pass

    def build_sidebar_content(self):
        return ft.Column(
            expand=True,
            controls=[
                ft.Container(
                    padding=10,
                    content=ft.Text("CARPETAS", weight=ft.FontWeight.BOLD),
                ),
                ft.Container(expand=True, content=self.crear_selector_arbol()),
            ],
        )

    def _on_state_change(self, event=None):
        if event == "update":
            if hasattr(self, "resultado_actual"):
                self.resultado_actual.update()
                self.page.update()
            return
        self.page.update()

    def _on_guardados_update(self, data):
        self.resultado_actual.update()

    def _on_historial_update(self, data):
        self.page.update()
