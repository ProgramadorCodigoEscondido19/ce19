from ui.responsive import Responsive
from ui.responsive_layout import ResponsiveLayout
import flet as ft
from services.codificador_service import CodificadorService
from services.alfabetos_service import AlfabetosService
from services.archivo_local_service import ArchivoLocalService
from vistas.componentes import tarjeta_resultado
from vistas.detalle import mostrar_detalle_comparacion
from ui.compartir import compartir_texto, descargar_archivo
from ui.tema import (
    PERLA_BORDE,
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

REFERENCIAS_INICIO = {
    "colores": {
        "src": "referencia_colores.png",
        "archivo": "assets/referencia_colores.png",
        "titulo": "Referencia de colores",
        "proporcion": 1180 / 1333,
    },
    "texto_parrafo": {
        "src": "referencia_texto_parrafo.jpg",
        "archivo": "assets/referencia_texto_parrafo.jpg",
        "titulo": "Texto del parrafo",
        "proporcion": 1,
    },
}


class InicioView:
    # =======================================
    # F (INIT)
    # =======================================
    def __init__(self, page, router):
        self.page = page
        self.router = router
        self.historial = state.historial
        self.responsive = Responsive(self.page)
        self.layout = ResponsiveLayout(self.page, self.responsive)
        self.page.on_resize = self._on_resize

        self.codificador_service = CodificadorService()
        self.motor = self.codificador_service.motor
        self.crear_controles()
        state.bind(self._on_state_change)
        bus.subscribe("historial_updated", self._on_historial_update)

    # =======================================
    # F (ON RESIZE)
    # =======================================
    def _on_resize(self, e):
        self.router.refrescar()

    def get_page(self):
        return self.page

    # =====================================================
    # CREAR CONTROLES
    # =====================================================
    def crear_controles(self):
        self.referencias_inicio = ft.Row(
            tight=True,
            spacing=8,
            controls=[
                self._crear_boton_referencia("colores"),
                self._crear_boton_referencia("texto_parrafo"),
            ],
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
                            self.referencias_inicio,
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

    def _crear_boton_referencia(self, clave):
        referencia = REFERENCIAS_INICIO[clave]
        return ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            on_tap=lambda e, clave_ref=clave: self.abrir_referencia_imagen(clave_ref),
            content=ft.Container(
                width=32,
                height=32,
                border=ft.Border.all(1, PERLA_BORDE),
                border_radius=4,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                content=ft.Image(
                    src=referencia["src"],
                    width=32,
                    height=32,
                    fit=ft.BoxFit.COVER,
                ),
            ),
        )

    def descargar_referencia(self, clave):
        referencia = REFERENCIAS_INICIO[clave]
        descargar_archivo(
            self.page,
            referencia["archivo"],
            f"Guardar {referencia['titulo']}",
        )

    def abrir_referencia_colores(self, e=None):
        self.abrir_referencia_imagen("colores")

    def abrir_referencia_imagen(self, clave):
        referencia = REFERENCIAS_INICIO[clave]
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
        proporcion = referencia["proporcion"]
        ancho_maximo = max(190, min(720, ancho_pantalla - (24 if es_movil else 72)))
        alto_maximo = max(240, alto_pantalla - (48 if es_movil else 80))
        ancho_imagen = min(ancho_maximo, alto_maximo * proporcion)
        alto_imagen = ancho_imagen / proporcion

        def cerrar(ev=None):
            cerrar_dialogo(self.page, dialog)

        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=ft.Colors.TRANSPARENT,
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
                        content=ft.Image(
                            src=referencia["src"],
                            width=ancho_imagen,
                            height=alto_imagen,
                            fit=ft.BoxFit.FILL,
                        ),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DOWNLOAD,
                        tooltip="Descargar",
                        icon_color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.with_opacity(0.68, ft.Colors.BLACK),
                        right=50,
                        top=6,
                        on_click=lambda ev, clave_ref=clave: self.descargar_referencia(clave_ref),
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
        texto = "\n".join(
            [
                "CODIGO ESCONDIDO 19",
                "",
                f"Modo: {registro.get('modo_codificacion', 'Texto a numeros')}",
                f"Entrada: {registro.get('palabra', '')}",
                f"Alfabeto: {registro.get('alfabeto', '')}",
                f"Detalle: {registro.get('suma', '')}",
                f"Resultado: {registro.get('resultado', '')}",
            ]
        )
        nombre = registro.get("palabra") or "codigo-escondido-19"
        ArchivoLocalService.guardar_texto(
            self.page,
            texto,
            nombre,
            "Guardar codificacion en el dispositivo",
        )

    # ======================================================
    # OCULTAR MENSAJE
    # ======================================================
    def ocultar_mensaje_exito(self):
        try:
            self.mensaje_exito.visible = False
            self.page.update()
        except RuntimeError:
            pass

    def _on_state_change(self, event=None):
        if event == "update":
            if hasattr(self, "resultado_actual"):
                self.resultado_actual.update()
                self.page.update()
            return
        self.page.update()

    def _on_historial_update(self, data):
        self.page.update()
