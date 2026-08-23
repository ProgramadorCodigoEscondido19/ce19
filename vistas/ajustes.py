import flet as ft

from services.alfabetos_service import AlfabetosService
from services.app_config_service import AppConfigService
from services.app_paths import AppPaths
from ui.tema import PERLA_BORDE, PERLA_PANEL, PURPURA_IOS
from ui.dialogos import cerrar_dialogo, mostrar_dialogo


class AjustesView:
    """Preferencias disponibles solo para el Nivel 4."""

    def __init__(self, page, router):
        self.page = page
        self.router = router
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
        estado = ft.Text("Seleccione uno o varios cuadros.", size=12, color="#6E6374")
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
                else "Seleccione uno o varios cuadros."
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
                raise ValueError("Ingrese un valor numerico mayor que cero.") from problema
            if numero <= 0:
                raise ValueError("Ingrese un valor numerico mayor que cero.")
            return numero

        def aplicar_valor(ev=None, consecutivos=False):
            try:
                inicio = valor_ingresado()
                if not seleccionados:
                    raise ValueError("Seleccione al menos un caracter de la tabla.")
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
                error.value = "Seleccione los caracteres a dejar sin valor."
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
                    ft.Text("Marque uno o varios caracteres, indique un valor y aplique el cambio.", size=12),
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

    def obtener_vista(self):
        self._recargar()
        return ft.Container(
            expand=True,
            padding=16,
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=14,
                controls=[
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
                                    "Configure la experiencia y los alfabetos disponibles en el codificador.",
                                    color="#6E6374",
                                ),
                            ],
                        ),
                    ),
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
                ],
            ),
        )
