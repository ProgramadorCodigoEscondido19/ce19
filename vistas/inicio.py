from ui.responsive import Responsive
from ui.responsive_layout import ResponsiveLayout
import flet as ft
from services.codificador_service import CodificadorService
from services.alfabetos_service import AlfabetosService
from services.notificacion_service import NotificacionService
from vistas.componentes import tarjeta_resultado
from vistas.detalle import mostrar_detalle_comparacion
from ui.sidebar import AppSidebar
from ui.compartir import compartir_texto
from ui.tema import (
    PERLA_BORDE,
    PERLA_PANEL,
    PERLA_PURPURA,
    SUPERFICIE_PERLADA,
    TEXTO_PRINCIPAL,
    TEXTO_SECUNDARIO,
    PURPURA_IOS,
    sombra_suave,
)
from ui.teclado import ocultar_teclado
from ui.tareas import ejecutar_demorado
from ui.dialogos import cerrar_dialogo, mostrar_dialogo
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
        self.icono_referencia_colores = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            on_tap=self.abrir_referencia_colores,
            content=ft.Container(
                width=28,
                height=28,
                border=ft.Border.all(1, PERLA_BORDE),
                border_radius=4,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                content=ft.Image(
                    src="referencia_colores.png",
                    width=28,
                    height=28,
                    fit=ft.BoxFit.FILL,
                ),
            ),
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
            hint_text="Ej: Hola",
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

        self.modo_codificacion = ft.Dropdown(
            label="Tipo de codificación",
            value="texto_a_numeros",
            options=[
                ft.dropdown.Option("texto_a_numeros", text="Texto a números"),
                ft.dropdown.Option("numeros_a_texto", text="Números a texto"),
            ],
            border_radius=18,
            filled=True,
            bgcolor="#FCFAFF",
            border_color="#E7DCEB",
            focused_border_color="#A44BA8",
            on_select=self._actualizar_modo_codificacion,
        )

        self.alfabeto_selector = ft.Dropdown(
            label="Alfabeto",
            border_radius=18,
            filled=True,
            bgcolor="#FCFAFF",
            border_color="#E7DCEB",
            focused_border_color="#A44BA8",
            on_select=self._seleccionar_alfabeto,
        )
        self.actualizar_alfabeto(actualizar_pantalla=False)

        self.ayuda_modo = ft.Text(
            "Texto normal: Hola → 9 + 18 + 13 + 1",
            size=12,
            color=TEXTO_SECUNDARIO,
        )

        self.boton = ft.ElevatedButton(
            "DECODIFICAR",
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

        self.boton_comparar = ft.OutlinedButton(
            "Comparar",
            height=45,
            icon=ft.Icons.COMPARE_ARROWS,
            on_click=self.abrir_comparacion,
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
        solo_texto_a_numeros = getattr(self.router, "nivel", 4) == 1
        puede_elegir_alfabeto = self.router.tiene_capacidad("inicio_diccionarios")
        puede_comparar = self.router.tiene_capacidad("inicio_comparar")

        self.titulo.size = 22 if es_movil else 26 if es_tablet else 30
        self.boton.width = None if es_movil else 220 if es_tablet else 250
        self.palabra_input.max_lines = 4 if es_movil else 2
        self.alfabeto_selector.visible = puede_elegir_alfabeto
        self.modo_codificacion.visible = not solo_texto_a_numeros
        if not puede_elegir_alfabeto:
            self.alfabeto_selector.value = AlfabetosService.ID_BASE
            self.codificador_service.usar_alfabeto_temporal(AlfabetosService.ID_BASE)
            self.motor = self.codificador_service.motor
        if solo_texto_a_numeros:
            self.modo_codificacion.value = "texto_a_numeros"
            self.palabra_input.label = "Ingrese texto"
            self.palabra_input.hint_text = "Ej: Hola"
            self.boton.text = "CODIFICAR"
        self.boton_comparar.visible = (
            puede_comparar and self.modo_codificacion.value == "texto_a_numeros"
        )

        acciones = ft.Row(
            wrap=True,
            spacing=10,
            run_spacing=8,
            controls=[
                self.boton,
                self.boton_comparar,
                self.boton_limpiar,
            ],
        )

        panel_formulario = self._tarjeta_visual(
            ft.Column(
                spacing=14,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                "Entrada",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=TEXTO_PRINCIPAL,
                            ),
                            self.icono_referencia_colores,
                        ],
                    ),
                    self.palabra_input,
                    self.alfabeto_selector,
                    self.modo_codificacion,
                    self.ayuda_modo,
                    ft.Container(
                        padding=ft.Padding(left=12, top=6, right=12, bottom=6),
                        bgcolor=PERLA_PURPURA,
                        border=ft.Border.all(1, PERLA_BORDE),
                        border_radius=16,
                        content=ft.Text(
                            "Código 19",
                            size=13,
                            color=PURPURA_IOS,
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
                            ft.Icon(ft.Icons.INSIGHTS, color=PURPURA_IOS, size=22),
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

    def abrir_referencia_colores(self, e=None):
        ventana = getattr(self.page, "window", None)
        ancho_pantalla = min(
            valor
            for valor in (
                getattr(self.page, "width", None),
                getattr(ventana, "width", None),
                1200,
            )
            if valor
        )
        alto_pantalla = (
            getattr(self.page, "height", None)
            or getattr(ventana, "height", None)
            or 720
        )
        es_movil = ancho_pantalla < 700
        proporcion = 1180 / 1333
        ancho_maximo = max(190, min(720, ancho_pantalla - (24 if es_movil else 72)))
        alto_maximo = max(240, alto_pantalla - (48 if es_movil else 80))
        ancho_imagen = min(ancho_maximo, alto_maximo * proporcion)
        alto_imagen = ancho_imagen / proporcion

        def cerrar(ev=None):
            cerrar_dialogo(self.page, dialog)

        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=ft.Colors.BLACK,
            content_padding=0,
            inset_padding=ft.Padding(
                8 if es_movil else 24,
                8 if es_movil else 24,
                8 if es_movil else 24,
                8 if es_movil else 24,
            ),
            content=ft.Stack(
                width=ancho_imagen,
                height=alto_imagen,
                controls=[
                    ft.Container(
                        width=ancho_imagen,
                        height=alto_imagen,
                        border_radius=8,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                        content=ft.Image(
                            src="referencia_colores.png",
                            width=ancho_imagen,
                            height=alto_imagen,
                            fit=ft.BoxFit.CONTAIN,
                        ),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.with_opacity(0.68, ft.Colors.BLACK),
                        right=6,
                        top=6,
                        on_click=cerrar,
                    ),
                ],
            ),
        )
        mostrar_dialogo(self.page, dialog)

    def limpiar_codificador(self, e=None):
        self.palabra_input.value = ""
        self.resultado_actual.controls.clear()
        self.ultimo_registro = None
        self.mensaje_error.visible = False
        self.mensaje_exito.visible = False
        self.page.update()

    def _actualizar_modo_codificacion(self, e=None):
        if self.modo_codificacion.value == "numeros_a_texto":
            self.palabra_input.label = "Ingrese números codificados"
            self.palabra_input.hint_text = "Ej: 9_18_13_1__9_18_13_1"
            self.ayuda_modo.value = (
                "1-29. Use _ entre letras y __ entre palabras. "
                "Ej: 29 = z, 9_18_13_1 = Hola."
            )
            self.boton.text = "DECODIFICAR"
            self.boton_comparar.visible = False
        else:
            self.palabra_input.label = "Ingrese texto"
            self.palabra_input.hint_text = "Ej: Hola"
            self.ayuda_modo.value = "Texto normal: Hola → 9 + 18 + 13 + 1"
            self.boton.text = "CODIFICAR"
            self.boton_comparar.visible = self.router.tiene_capacidad("inicio_comparar")

        self.page.update()

    def actualizar_alfabeto(self, actualizar_pantalla=True):
        alfabetos = AlfabetosService.listar()
        activo = AlfabetosService.activo_id()
        self.alfabeto_selector.options = [
            ft.dropdown.Option(alfabeto["id"], text=alfabeto["nombre"])
            for alfabeto in alfabetos
        ]
        self.alfabeto_selector.value = activo
        self.codificador_service.seleccionar_alfabeto(activo)
        self.motor = self.codificador_service.motor
        if actualizar_pantalla:
            self.page.update()

    def _seleccionar_alfabeto(self, e=None):
        self.codificador_service.seleccionar_alfabeto(self.alfabeto_selector.value)
        self.motor = self.codificador_service.motor
        self.page.update()

    def abrir_comparacion(self, e=None):
        if not self.router.tiene_capacidad("inicio_comparar"):
            self.mensaje_error.value = "La comparacion de diccionarios requiere el Nivel 4."
            self.mensaje_error.visible = True
            self.page.update()
            return

        texto = (self.palabra_input.value or "").strip()
        if not texto:
            self.mensaje_error.value = "Ingrese primero el texto que desea comparar."
            self.mensaje_error.visible = True
            self.page.update()
            return

        alfabetos = AlfabetosService.listar()
        seleccionados = {alfabeto["id"] for alfabeto in alfabetos}
        lista = ft.Column(spacing=4)

        def actualizar_estado(identificador, marcado):
            if marcado:
                seleccionados.add(identificador)
            else:
                seleccionados.discard(identificador)

        for alfabeto in alfabetos:
            lista.controls.append(
                ft.Checkbox(
                    label=alfabeto["nombre"],
                    value=True,
                    on_change=lambda ev, ident=alfabeto["id"]: actualizar_estado(
                        ident, bool(ev.control.value)
                    ),
                )
            )

        def cerrar(ev=None):
            cerrar_dialogo(self.page, dialog)

        def comparar(ev=None):
            if len(seleccionados) < 2:
                self.mensaje_error.value = "Seleccione al menos dos diccionarios para comparar."
                self.mensaje_error.visible = True
                cerrar()
                return
            resultados = self.codificador_service.comparar_diccionarios(texto, seleccionados)
            cerrar()
            self.mostrar_comparacion(resultados)

        dialog = ft.AlertDialog(
            modal=False,
            title=ft.Text("Comparar diccionarios"),
            content=ft.Container(
                width=360,
                content=ft.Column(tight=True, spacing=10, controls=[
                    ft.Text("Seleccione los diccionarios para calcular el mismo texto.", size=12),
                    lista,
                ]),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar),
                ft.ElevatedButton(
                    "Comparar",
                    icon=ft.Icons.COMPARE_ARROWS,
                    on_click=comparar,
                ),
            ],
        )
        mostrar_dialogo(self.page, dialog)

    def mostrar_comparacion(self, resultados):
        if not resultados:
            self.mensaje_error.value = "No se pudieron comparar los diccionarios seleccionados."
            self.mensaje_error.visible = True
            self.page.update()
            return

        texto = resultados[0].get("palabra", self.palabra_input.value or "")
        filas_guardadas = [
            {
                "alfabeto": resultado.get("alfabeto", "Diccionario"),
                "suma": resultado.get("suma", ""),
                "resultado": resultado.get("resultado", ""),
                "detalle_palabras": resultado.get("detalle_palabras", []),
            }
            for resultado in resultados
        ]
        registro = {
            "palabra": texto,
            "alfabeto": "Comparacion de diccionarios",
            "suma": "\n".join(
                f"{fila['alfabeto']}: {fila['suma']}" for fila in filas_guardadas
            ),
            "resultado": " | ".join(
                f"{fila['alfabeto']}: {fila['resultado']}" for fila in filas_guardadas
            ),
            "modo_codificacion": "Comparacion de diccionarios",
            "comparacion": filas_guardadas,
        }
        self.ultimo_registro = registro
        resumen = " | ".join(
            f"{fila['alfabeto']}: {fila['resultado']}" for fila in filas_guardadas
        )
        self.resultado_actual.controls.clear()
        self.resultado_actual.controls.append(
            tarjeta_resultado(
                page=self.page,
                palabra=texto,
                alfabeto="Comparacion",
                suma=registro["suma"],
                resultado=resumen,
                texto_boton="Guardar",
                funcion=lambda e, r=registro: self.confirmar_guardado(r),
                funcion_compartir=lambda e, r=registro: self.compartir_tarjeta(r),
                modo_codificacion="Comparacion de diccionarios",
                mostrar_guardar=getattr(self.router, "nivel", 4) >= 2,
                funcion_detalle=lambda e, r=registro: mostrar_detalle_comparacion(self.page, r),
            )
        )
        self.page.update()

    # =====================================================
    # CODIFICAR
    # =====================================================
    def codificar(self, e):
        if self.responsive.is_mobile():
            ocultar_teclado(self.page)
        if getattr(self.router, "nivel", 4) == 1:
            self.modo_codificacion.value = "texto_a_numeros"
        if not self.router.tiene_capacidad("inicio_diccionarios"):
            self.codificador_service.usar_alfabeto_temporal(AlfabetosService.ID_BASE)
            self.motor = self.codificador_service.motor
        texto = self.palabra_input.value.strip()

        if not texto:
            self.mensaje_error.value = "Debe ingresar texto o números para codificar."
            self.mensaje_error.visible = True
            self.page.update()
            return

        self.mensaje_error.visible = False

        try:
            if self.modo_codificacion.value == "numeros_a_texto":
                datos = self.codificador_service.decodificar_numeros(
                    self.palabra_input.value
                )
            else:
                datos = self.codificador_service.codificar(
                    self.palabra_input.value,
                    usar_ch=True,
                    usar_ll=True,
                    usar_ñ=True,
                )
                datos["modo_codificacion"] = "Texto a números"
        except ValueError as error:
            self.mensaje_error.value = str(error)
            self.mensaje_error.visible = True
            self.page.update()
            return

        self.mostrar_resultado(datos)

        def guardar_historial():
            self.historial.agregar(datos, notificar=False)

        ejecutar_demorado(self.page, 0.01, guardar_historial)

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
            modo_codificacion=registro.get("subtipo") or registro.get("modo_codificacion"),
            mostrar_guardar=getattr(self.router, "nivel", 4) >= 2,
        )

        self.resultado_actual.controls.append(tarjeta)
        self.page.update()

    def compartir_tarjeta(self, registro):
        compartir_texto(
            self.page,
            (
                "CODIGO ESCONDIDO 19\n\n"
                f"Modo: {registro.get('modo_codificacion', 'Texto a números')}\n"
                f"Entrada: {registro.get('palabra', '')}\n"
                f"Abecedario: {registro.get('alfabeto', '')}\n"
                f"Detalle: {registro.get('suma', '')}\n"
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
        guardando = {"valor": False}

        def abrir_selector():
            arbol = self.crear_selector_arbol()
            self.dialog_selector.content = ft.Container(
                width=320 if self.responsive.is_mobile() else 350,
                height=280 if self.responsive.is_mobile() else 450,
                content=arbol,
            )
            self.dialog_selector.open = True
            self.page.update()

        def cerrar(e):
            dialog.open = False
            self.page.update()

        def guardar(e):
            if guardando["valor"]:
                return

            guardando["valor"] = True
            nuevo_registro = registro.copy()
            nuevo_registro["nombre"] = nombre.value
            nuevo_registro["tipo"] = "tarjeta"
            if registro.get("subtipo"):
                nuevo_registro["subtipo"] = registro.get("subtipo")
            carpeta_destino = self.carpetas.obtener_por_id(self.carpeta_selector_id) or destino

            try:
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
                self.resultado_actual.controls.clear()
                self.page.update()
                NotificacionService.exito(self.page, "Guardado correctamente.")
            except Exception as error:
                guardando["valor"] = False
                NotificacionService.error(self.page, f"No se pudo guardar: {error}")

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
