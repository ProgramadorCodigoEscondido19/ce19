import asyncio

import flet as ft

from services.actualizador_service import ActualizadorService
from services.alfabetos_service import AlfabetosService
from services.app_config_service import AppConfigService
from services.app_paths import AppPaths
from ui.compartir import _abrir_url
from ui.tema import APP_UPDATE_DATE, APP_VERSION, PERLA_BORDE, PERLA_PANEL, PURPURA_IOS
from ui.dialogos import cerrar_dialogo, mostrar_dialogo

GITHUB_RELEASES = "https://github.com/ProgramadorCodigoEscondido19/ce19/releases"
GITHUB_LATEST = f"{GITHUB_RELEASES}/latest"
RELEASE_TAG = f"v{APP_VERSION}"
DESCARGAS_APP = {
    "android": {
        "label": "Android",
        "icono": ft.Icons.ANDROID,
        "url": GITHUB_LATEST,
        "detalle": "Abre la ultima actualizacion publicada para Android.",
    },
    "windows": {
        "label": "Windows",
        "icono": ft.Icons.DESKTOP_WINDOWS,
        "url": GITHUB_LATEST,
        "detalle": "Abre la ultima actualizacion publicada para Windows.",
    },
    "iphone": {
        "label": "iPhone",
        "icono": ft.Icons.PHONE_IPHONE,
        "url": GITHUB_LATEST,
        "detalle": "Todavía no disponible: iPhone requiere firma y un perfil de distribución de Apple.",
    },
    "mac": {
        "label": "Mac",
        "icono": ft.Icons.LAPTOP_MAC,
        "url": f"{GITHUB_RELEASES}/download/{RELEASE_TAG}/CODIGO-ESCONDIDO-19-Mac-{RELEASE_TAG}.zip",
        "detalle": "Descarga el ZIP para macOS. Al no estar firmado, el sistema puede pedir autorización para abrirlo.",
    },
}


class AjustesView:
    """Preferencias de la app y descargas locales por nivel."""

    def __init__(self, page, router):
        self.page = page
        self.router = router
        self.sistema_descarga = self._sistema_sugerido()
        self.selector_sistema = ft.Dropdown(
            label="Sistema operativo",
            value=self.sistema_descarga,
            options=[
                ft.dropdown.Option("android", text="Android"),
                ft.dropdown.Option("windows", text="Windows"),
                ft.dropdown.Option("iphone", text="iPhone"),
                ft.dropdown.Option("mac", text="Mac"),
            ],
            border_radius=12,
            on_select=self._cambiar_sistema_descarga,
        )
        self.info_descarga = ft.Text(
            DESCARGAS_APP[self.sistema_descarga]["detalle"],
            size=12,
            color="#6E6374",
        )
        self.actualizador = ActualizadorService(self.sistema_descarga)
        self.estado_actualizacion = ft.Text(
            f"Version final {APP_VERSION}. Actualizacion instalada: "
            f"{ActualizadorService.formatear_fecha(APP_UPDATE_DATE)}.",
            size=12,
            color="#6E6374",
        )
        self.progreso_actualizacion = ft.ProgressBar(value=0, visible=False)
        self.boton_actualizar = ft.OutlinedButton(
            "Buscar actualizaciones",
            icon=ft.Icons.SYSTEM_UPDATE_ALT,
            on_click=self._buscar_actualizaciones,
        )
        self.selector = ft.Dropdown(
            label="Alfabeto activo",
            expand=True,
            on_select=self.cambiar_alfabeto,
        )
        self.lista_alfabetos = ft.Column(spacing=8)
        self._recargar()

    def _config(self):
        datos = AppConfigService.leer_json(AppPaths.CONFIG_APP, {})
        return datos if isinstance(datos, dict) else {}

    def _guardar_config(self, clave, valor):
        datos = self._config()
        datos[clave] = valor
        AppConfigService.guardar_json(AppPaths.CONFIG_APP, datos)

    def _sistema_sugerido(self):
        plataforma = getattr(self.page, "platform", None)
        if plataforma == ft.PagePlatform.ANDROID:
            return "android"
        if plataforma == ft.PagePlatform.IOS:
            return "iphone"
        if plataforma == ft.PagePlatform.MACOS:
            return "mac"
        return "windows"

    def _cambiar_sistema_descarga(self, e=None):
        self.sistema_descarga = self.selector_sistema.value or self.sistema_descarga
        self.actualizador = ActualizadorService(self.sistema_descarga)
        self.info_descarga.value = DESCARGAS_APP[self.sistema_descarga]["detalle"]
        self.page.update()

    def _abrir_descarga(self, actualizar=False):
        sistema = self.selector_sistema.value or self.sistema_descarga
        url = GITHUB_LATEST if actualizar else DESCARGAS_APP[sistema]["url"]
        _abrir_url(self.page, url)

    def _buscar_actualizaciones(self, e=None):
        try:
            self.page.run_task(self._buscar_actualizaciones_async)
        except (RuntimeError, AssertionError, AttributeError):
            self._snack("No se pudo iniciar la busqueda de actualizaciones.")

    async def _buscar_actualizaciones_async(self):
        self.boton_actualizar.disabled = True
        self.progreso_actualizacion.visible = True
        self.progreso_actualizacion.value = 0
        self.estado_actualizacion.value = "Consultando GitHub..."
        self.page.update()

        try:
            actualizacion = await asyncio.to_thread(self.actualizador.buscar_actualizacion)
        except Exception as error:
            self.estado_actualizacion.value = f"No se pudo buscar actualizaciones: {error}"
            self.boton_actualizar.disabled = False
            self.progreso_actualizacion.visible = False
            self.page.update()
            return

        if actualizacion is None:
            self.estado_actualizacion.value = (
                f"La version final {APP_VERSION} ya esta actualizada al "
                f"{ActualizadorService.formatear_fecha(APP_UPDATE_DATE)}."
            )
            self.boton_actualizar.disabled = False
            self.progreso_actualizacion.visible = False
            self.page.update()
            return

        self.estado_actualizacion.value = (
            "Nueva actualizacion del "
            f"{ActualizadorService.formatear_fecha(actualizacion.fecha_remota)}. "
            f"Descargando {actualizacion.archivo}..."
        )
        self.page.update()

        def progreso(descargado, total):
            if total:
                self.progreso_actualizacion.value = min(1, descargado / total)
                self.estado_actualizacion.value = (
                    f"Descargando {int(self.progreso_actualizacion.value * 100)}%..."
                )
            else:
                self.progreso_actualizacion.value = None
                self.estado_actualizacion.value = f"Descargados {descargado // 1024} KB..."
            try:
                self.page.update()
            except Exception:
                pass

        try:
            paquete = await asyncio.to_thread(self.actualizador.descargar, actualizacion, progreso)
            preparacion = await asyncio.to_thread(self.actualizador.preparar_instalacion, paquete, actualizacion)
        except Exception as error:
            self.estado_actualizacion.value = f"La actualizacion fallo antes de instalar: {error}"
            self.boton_actualizar.disabled = False
            self.progreso_actualizacion.visible = False
            self.page.update()
            return

        self.progreso_actualizacion.value = 1
        self.estado_actualizacion.value = preparacion.get("mensaje", "Actualizacion lista.")
        self.page.update()

        if preparacion.get("accion") == "windows_script":
            self._confirmar_reinicio_windows(preparacion)
        elif preparacion.get("accion") == "abrir_instalador":
            self._confirmar_instalar_android(preparacion)
        else:
            self.boton_actualizar.disabled = False

    def _confirmar_reinicio_windows(self, preparacion):
        def cancelar(ev=None):
            cerrar_dialogo(self.page, dialog)
            self.boton_actualizar.disabled = False
            self.page.update()

        def aplicar(ev=None):
            cerrar_dialogo(self.page, dialog)
            try:
                self.actualizador.ejecutar_instalacion_preparada(preparacion)
                ventana = getattr(self.page, "window", None)
                if ventana is not None and hasattr(ventana, "close"):
                    ventana.close()
                elif hasattr(self.page, "window_destroy"):
                    self.page.window_destroy()
            except Exception as error:
                self.estado_actualizacion.value = f"No se pudo iniciar el instalador: {error}"
                self.boton_actualizar.disabled = False
                self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Aplicar actualizacion"),
            content=ft.Text("Se hizo backup de tus datos. La app se cerrara, reemplazara solo archivos del programa y volvera a iniciar."),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton("Actualizar ahora", icon=ft.Icons.RESTART_ALT, bgcolor=PURPURA_IOS, color=ft.Colors.WHITE, on_click=aplicar),
            ],
        )
        mostrar_dialogo(self.page, dialog)

    def _confirmar_instalar_android(self, preparacion):
        def cerrar(ev=None):
            cerrar_dialogo(self.page, dialog)
            self.boton_actualizar.disabled = False
            self.page.update()

        def abrir(ev=None):
            try:
                self.actualizador.ejecutar_instalacion_preparada(preparacion)
            except Exception as error:
                self.estado_actualizacion.value = f"No se pudo abrir el APK: {error}"
            cerrar()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Instalar actualizacion"),
            content=ft.Text("Se hizo backup de tus datos. Android pedira confirmar la instalacion del APK descargado."),
            actions=[
                ft.TextButton("Luego", on_click=cerrar),
                ft.ElevatedButton("Abrir APK", icon=ft.Icons.ANDROID, bgcolor=PURPURA_IOS, color=ft.Colors.WHITE, on_click=abrir),
            ],
        )
        mostrar_dialogo(self.page, dialog)

    def _cambiar_fondo(self, e):
        self._guardar_config("fondo_decorativo", bool(e.control.value))
        self.router.refrescar()

    def _cambiar_audio(self, e):
        self._guardar_config("intro_audio_muted", not bool(e.control.value))
        self._snack("La preferencia de sonido se aplicara en la proxima introduccion.")

    def _recargar(self):
        alfabetos = AlfabetosService.listar()
        activo = AlfabetosService.activo_id()
        self.selector.options = [
            ft.dropdown.Option(alfabeto["id"], text=alfabeto["nombre"])
            for alfabeto in alfabetos
        ]
        self.selector.value = activo
        self.lista_alfabetos.controls = [self._fila_alfabeto(alfabeto) for alfabeto in alfabetos]

    def _fila_alfabeto(self, alfabeto):
        valores = alfabeto["valores"]
        return ft.Container(
            padding=12,
            border_radius=12,
            bgcolor="#FFFFFF",
            border=ft.Border.all(1, PERLA_BORDE),
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.ABC, color=PURPURA_IOS),
                    ft.Column(
                        expand=True,
                        tight=True,
                        spacing=2,
                        controls=[
                            ft.Text(alfabeto["nombre"], weight=ft.FontWeight.BOLD),
                            ft.Text(f"{len(valores)} caracteres configurados", size=11, color="#6E6374"),
                        ],
                    ),
                    ft.IconButton(
                        icon=ft.Icons.EDIT_OUTLINED,
                        tooltip="Editar alfabeto",
                        disabled=alfabeto.get("predefinido", False),
                        on_click=lambda e, a=alfabeto: self.dialog_alfabeto(a),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        tooltip="Eliminar alfabeto",
                        disabled=alfabeto.get("predefinido", False),
                        on_click=lambda e, a=alfabeto: self.eliminar_alfabeto(a),
                    ),
                ],
            ),
        )

    def cambiar_alfabeto(self, e=None):
        AlfabetosService.seleccionar(self.selector.value)
        inicio = self.router.vistas.get("inicio")
        if inicio is not None and hasattr(inicio, "actualizar_alfabeto"):
            inicio.actualizar_alfabeto()
        self._snack("Alfabeto activo actualizado.")

    def _snack(self, texto):
        self.page.snack_bar = ft.SnackBar(content=ft.Text(texto))
        self.page.snack_bar.open = True
        self.page.update()

    def dialog_alfabeto(self, alfabeto=None, e=None):
        if not isinstance(alfabeto, dict):
            alfabeto = {}
        alfabeto = alfabeto or {}
        valores = dict(alfabeto.get("valores", {}))
        seleccionados = set()
        nombre = ft.TextField(
            label="Nombre del diccionario",
            value=alfabeto.get("nombre", ""),
            autofocus=not bool(alfabeto),
        )
        plantilla = ft.Dropdown(
            label="Tabla base",
            value="abc_biblico",
            options=[
                ft.dropdown.Option(item["id"], text=item["nombre"])
                for item in AlfabetosService.listar()
                if item.get("predefinido")
            ],
        )
        valor = ft.TextField(label="Valor", width=112, input_filter=ft.NumbersOnlyInputFilter())
        estado = ft.Text("Selecciona uno o varios cuadros.", size=12, color="#6E6374")
        error = ft.Text("", color=ft.Colors.RED, size=12, visible=False)
        grilla = ft.Row(wrap=True, spacing=7, run_spacing=7)

        def caracteres_ordenados():
            return list(valores.keys())

        def actualizar_grilla():
            grilla.controls = []
            for caracter in caracteres_ordenados():
                seleccionado = caracter in seleccionados
                grilla.controls.append(
                    ft.Container(
                        width=68,
                        height=62,
                        ink=True,
                        border_radius=11,
                        bgcolor="#F2E8F7" if seleccionado else "#FFFFFF",
                        border=ft.Border.all(2 if seleccionado else 1, PURPURA_IOS if seleccionado else PERLA_BORDE),
                        on_click=lambda e, c=caracter: alternar(c),
                        content=ft.Column(
                            tight=True,
                            spacing=2,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text(caracter, size=17, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                                ft.Text(
                                    str(valores[caracter]) if valores.get(caracter) else "-",
                                    size=12,
                                    color=PURPURA_IOS if valores.get(caracter) else "#8C8194",
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                        ),
                    )
                )
            estado.value = (
                f"{len(seleccionados)} caracteres seleccionados."
                if seleccionados
                else "Selecciona uno o varios cuadros."
            )
            self.page.update()

        def alternar(caracter):
            if caracter in seleccionados:
                seleccionados.remove(caracter)
            else:
                seleccionados.add(caracter)
            actualizar_grilla()

        def cargar_plantilla(ev=None):
            base = AlfabetosService.obtener(plantilla.value)
            valores.clear()
            # Solo los cuadros valorados quedan incluidos al guardar.
            valores.update({caracter: None for caracter in base["valores"]})
            seleccionados.clear()
            if not nombre.value.strip() or nombre.value == alfabeto.get("nombre", ""):
                nombre.value = f"Mi {base['nombre']}"
            actualizar_grilla()

        def valor_ingresado():
            try:
                numero = int(valor.value or "")
            except ValueError as problema:
                raise ValueError("Ingresa un valor numérico mayor que cero.") from problema
            if numero <= 0:
                raise ValueError("Ingresa un valor numérico mayor que cero.")
            return numero

        def aplicar_valor(ev=None, consecutivos=False):
            try:
                inicio = valor_ingresado()
                if not seleccionados:
                    raise ValueError("Selecciona al menos un carácter de la tabla.")
            except ValueError as problema:
                error.value = str(problema)
                error.visible = True
                self.page.update()
                return
            orden = [caracter for caracter in caracteres_ordenados() if caracter in seleccionados]
            for indice, caracter in enumerate(orden):
                valores[caracter] = inicio + indice if consecutivos else inicio
            error.visible = False
            actualizar_grilla()

        def quitar_valor(ev=None):
            if not seleccionados:
                error.value = "Selecciona los caracteres que quieres dejar sin valor."
                error.visible = True
                self.page.update()
                return
            for caracter in seleccionados:
                valores[caracter] = None
            error.visible = False
            actualizar_grilla()

        def cerrar(ev=None):
            cerrar_dialogo(self.page, dialog)

        def guardar(ev=None):
            try:
                AlfabetosService.guardar(nombre.value, valores, alfabeto.get("id"))
            except ValueError as problema:
                error.value = str(problema)
                error.visible = True
                self.page.update()
                return
            cerrar()
            self._recargar()
            inicio = self.router.vistas.get("inicio")
            if inicio is not None and hasattr(inicio, "actualizar_alfabeto"):
                inicio.actualizar_alfabeto()
            self._snack("Alfabeto guardado y seleccionado.")

        dialog = ft.AlertDialog(
            modal=False,
            title=ft.Text("Editar alfabeto" if alfabeto else "Nuevo alfabeto"),
            content=ft.Container(
                width=640,
                content=ft.Column(tight=True, spacing=12, controls=[
                    ft.Text("Marca uno o varios caracteres, indica un valor y aplica el cambio.", size=12),
                    nombre,
                    ft.Row(wrap=True, spacing=10, controls=[
                        plantilla,
                        ft.OutlinedButton("Cargar tabla", icon=ft.Icons.TABLE_CHART, on_click=cargar_plantilla),
                    ]),
                    ft.Container(
                        height=250,
                        padding=10,
                        border_radius=12,
                        bgcolor="#FCFAFF",
                        border=ft.Border.all(1, PERLA_BORDE),
                        content=ft.Column(scroll=ft.ScrollMode.AUTO, controls=[grilla]),
                    ),
                    estado,
                    ft.Row(wrap=True, spacing=8, controls=[
                        valor,
                        ft.ElevatedButton("Asignar valor", on_click=aplicar_valor),
                        ft.OutlinedButton("Asignar consecutivos", on_click=lambda e: aplicar_valor(e, True)),
                        ft.OutlinedButton("Quitar valor", icon=ft.Icons.REMOVE_CIRCLE_OUTLINE, on_click=quitar_valor),
                    ]),
                    error,
                ]),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar),
                ft.ElevatedButton("Guardar", icon=ft.Icons.SAVE, bgcolor=PURPURA_IOS, color=ft.Colors.WHITE, on_click=guardar),
            ],
        )
        mostrar_dialogo(self.page, dialog)
        if not valores:
            cargar_plantilla()
        else:
            actualizar_grilla()

    def eliminar_alfabeto(self, alfabeto, e=None):
        AlfabetosService.eliminar(alfabeto["id"])
        self._recargar()
        self._snack("Alfabeto eliminado.")

    def _preferencias(self):
        datos = self._config()
        fondo = ft.Switch(
            label="Mostrar fondo decorativo",
            value=datos.get("fondo_decorativo", True),
            on_change=self._cambiar_fondo,
        )
        audio = ft.Switch(
            label="Sonido en la introduccion",
            value=not datos.get("intro_audio_muted", False),
            on_change=self._cambiar_audio,
        )
        return ft.Container(
            padding=16,
            border_radius=16,
            bgcolor=PERLA_PANEL,
            border=ft.Border.all(1, PERLA_BORDE),
            content=ft.Column(spacing=6, controls=[
                ft.Text("Preferencias", size=18, weight=ft.FontWeight.BOLD),
                fondo,
                audio,
                ft.Text("Los cambios visuales se aplican al volver a abrir la pantalla.", size=11, color="#6E6374"),
            ]),
        )

    def _descargas_app(self):
        return ft.Container(
            padding=16,
            border_radius=16,
            bgcolor=PERLA_PANEL,
            border=ft.Border.all(1, PERLA_BORDE),
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.INSTALL_MOBILE, color=PURPURA_IOS),
                            ft.Text("Descarga local de la app", size=18, weight=ft.FontWeight.BOLD, expand=True),
                        ],
                    ),
                    ft.Text(
                        "Elige el sistema operativo para instalar o actualizar Código Escondido 19 en el dispositivo.",
                        size=12,
                        color="#6E6374",
                    ),
                    self.selector_sistema,
                    self.info_descarga,
                    ft.Row(
                        wrap=True,
                        spacing=10,
                        run_spacing=8,
                        controls=[
                            ft.ElevatedButton(
                                "Descargar",
                                icon=ft.Icons.DOWNLOAD,
                                bgcolor=PURPURA_IOS,
                                color=ft.Colors.WHITE,
                                on_click=lambda e: self._abrir_descarga(False),
                            ),
                            ft.OutlinedButton(
                                "Ver ultima version",
                                icon=ft.Icons.OPEN_IN_NEW,
                                on_click=lambda e: self._abrir_descarga(True),
                            ),
                            self.boton_actualizar,
                        ],
                    ),
                    self.progreso_actualizacion,
                    self.estado_actualizacion,
                ],
            ),
        )

    def obtener_vista(self):
        nivel = getattr(self.router, "nivel", 4)
        if nivel >= 4:
            self._recargar()

        controles = [
            ft.Container(
                padding=ft.Padding(left=18, top=16, right=18, bottom=16),
                border_radius=18,
                bgcolor=PERLA_PANEL,
                border=ft.Border.all(1, PERLA_BORDE),
                content=ft.Column(
                    tight=True,
                    spacing=4,
                    controls=[
                        ft.Text("Ajustes", size=27, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "Descargas, actualizaciones y configuracion del codificador.",
                            color="#6E6374",
                        ),
                    ],
                ),
            ),
            self._descargas_app(),
        ]

        if nivel >= 4:
            controles.extend([
                self._preferencias(),
                ft.Container(
                    padding=16,
                    border_radius=16,
                    bgcolor=PERLA_PANEL,
                    border=ft.Border.all(1, PERLA_BORDE),
                    content=ft.Column(spacing=12, controls=[
                        ft.Row(controls=[
                            ft.Text("Alfabetos", size=18, weight=ft.FontWeight.BOLD, expand=True),
                            ft.ElevatedButton(
                                "Nuevo",
                                icon=ft.Icons.ADD,
                                bgcolor=PURPURA_IOS,
                                color=ft.Colors.WHITE,
                                on_click=lambda e: self.dialog_alfabeto(),
                            ),
                        ]),
                        self.selector,
                        ft.Text("El alfabeto activo se usa al codificar y decodificar desde Inicio.", size=12, color="#6E6374"),
                        self.lista_alfabetos,
                    ]),
                ),
            ])

        return ft.Container(
            expand=True,
            padding=16,
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=14,
                controls=controles,
            ),
        )
