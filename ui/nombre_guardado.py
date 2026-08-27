import flet as ft

from ui.teclado import ocultar_teclado
from ui.dialogos import cerrar_dialogo, mostrar_dialogo


def _ancho_disponible(page):
    ancho = getattr(page, "width", None)
    if ancho is None and hasattr(page, "window"):
        ancho = getattr(page.window, "width", None)
    return ancho or 420


def _es_movil(page):
    return _ancho_disponible(page) < 560


def _ancho_dialogo(page):
    return min(420, max(280, _ancho_disponible(page) - 44))


def _mostrar_error(page, mensaje):
    try:
        page.snack_bar = ft.SnackBar(
            content=ft.Text(str(mensaje)),
            bgcolor=ft.Colors.RED_700,
            duration=2500,
        )
        page.snack_bar.open = True
        page.update()
    except Exception:
        pass


def pedir_nombre_guardado(
    page,
    titulo,
    valor_sugerido,
    on_guardar,
    descripcion=None,
):
    campo = ft.TextField(
        label="Nombre",
        value=valor_sugerido or "",
        autofocus=False,
        on_tap_outside=lambda e: ocultar_teclado(page, e.control),
    )
    guardando = {"valor": False}

    def cerrar(e=None):
        cerrar_dialogo(page, dialog)

    def confirmar(e=None):
        if guardando["valor"]:
            return

        guardando["valor"] = True
        nombre = (campo.value or valor_sugerido or "Guardado").strip()
        try:
            on_guardar(nombre)
            cerrar()
        except Exception as error:
            guardando["valor"] = False
            _mostrar_error(page, f"No se pudo guardar: {error}")

    campo.on_submit = confirmar

    controles = []

    if descripcion:
        controles.append(ft.Text(descripcion))

    controles.append(campo)

    dialog = ft.AlertDialog(
        title=ft.Text(titulo),
        content=ft.Container(
            width=_ancho_dialogo(page),
            content=ft.Column(
                tight=True,
                spacing=10,
                controls=controles,
            ),
        ),
        actions_alignment=ft.MainAxisAlignment.END,
        actions=[
            ft.TextButton("Cancelar", on_click=cerrar),
            ft.ElevatedButton("Guardar", on_click=confirmar),
        ],
    )

    mostrar_dialogo(page, dialog)


def pedir_nombre_y_carpeta_guardado(
    page,
    titulo,
    valor_sugerido,
    carpetas,
    raiz_nombre,
    on_guardar,
    descripcion=None,
):
    raiz = carpetas.obtener_por_nombre(raiz_nombre) if carpetas else None
    carpeta_seleccionada = {"valor": raiz}
    expandidas = {raiz["id"]} if raiz else set()

    campo = ft.TextField(
        label="Nombre",
        value=valor_sugerido or "",
        autofocus=False,
        on_tap_outside=lambda e: ocultar_teclado(page, e.control),
    )
    destino = ft.Text(
        "",
        size=12,
        color=ft.Colors.GREY_700,
    )
    lista = ft.ListView(
        height=130 if _es_movil(page) else 240,
        spacing=2,
        auto_scroll=False,
    )
    guardando = {"valor": False}

    def ruta_destino():
        carpeta = carpeta_seleccionada["valor"]
        if not carpeta:
            return raiz_nombre
        return carpetas.obtener_ruta_texto(carpeta["id"])

    def actualizar_destino():
        destino.value = f"Destino: {ruta_destino()}"

    def seleccionar(carpeta):
        carpeta_seleccionada["valor"] = carpeta
        renderizar_arbol()

    def alternar(carpeta):
        if carpeta["id"] in expandidas:
            expandidas.remove(carpeta["id"])
        else:
            expandidas.add(carpeta["id"])
        renderizar_arbol()

    def item_carpeta(carpeta, nivel):
        hijos = carpetas.obtener_hijos(carpeta["id"])
        seleccionada = (
            carpeta_seleccionada["valor"]
            and carpeta_seleccionada["valor"]["id"] == carpeta["id"]
        )

        icono = (
            ft.Icons.EXPAND_MORE
            if carpeta["id"] in expandidas
            else ft.Icons.CHEVRON_RIGHT
        )

        return ft.Container(
            bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.DEEP_PURPLE)
            if seleccionada
            else None,
            border_radius=6,
            padding=ft.Padding(left=4 + nivel * 18, top=2, right=4, bottom=2),
            content=ft.Row(
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(
                        icon=icono if hijos else ft.Icons.FOLDER_OUTLINED,
                        icon_size=18,
                        width=32,
                        height=32,
                        tooltip="Desplegar" if hijos else "Carpeta",
                        on_click=(
                            lambda e, c=carpeta: alternar(c)
                            if hijos
                            else seleccionar(c)
                        ),
                    ),
                    ft.GestureDetector(
                        expand=True,
                        on_tap=lambda e, c=carpeta: seleccionar(c),
                        content=ft.Container(
                            height=34,
                            alignment=ft.Alignment(-1, 0),
                            content=ft.Text(
                                carpeta["nombre"],
                                weight=(
                                    ft.FontWeight.BOLD
                                    if seleccionada
                                    else ft.FontWeight.NORMAL
                                ),
                            ),
                        ),
                    ),
                ],
            ),
        )

    def agregar_rama(carpeta, nivel):
        lista.controls.append(item_carpeta(carpeta, nivel))

        if carpeta["id"] not in expandidas:
            return

        for hija in carpetas.obtener_hijos(carpeta["id"]):
            agregar_rama(hija, nivel + 1)

    def renderizar_arbol():
        lista.controls.clear()

        if raiz:
            agregar_rama(raiz, 0)
        else:
            lista.controls.append(ft.Text("No se encontró la carpeta destino."))

        actualizar_destino()
        try:
            lista.update()
            destino.update()
        except (RuntimeError, AssertionError):
            pass

    def cerrar(e=None):
        cerrar_dialogo(page, dialog)

    def confirmar(e=None):
        if guardando["valor"]:
            return

        guardando["valor"] = True
        nombre = (campo.value or valor_sugerido or "Guardado").strip()
        carpeta = carpeta_seleccionada["valor"] or raiz
        try:
            on_guardar(nombre, carpeta)
            cerrar()
        except Exception as error:
            guardando["valor"] = False
            _mostrar_error(page, f"No se pudo guardar: {error}")

    campo.on_submit = confirmar
    controles = []

    if descripcion:
        controles.append(ft.Text(descripcion))

    controles.extend(
        [
            campo,
            destino,
            ft.Container(
                border=ft.Border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                padding=6,
                content=lista,
            ),
        ]
    )

    dialog = ft.AlertDialog(
        title=ft.Text(titulo),
        content=ft.Container(
            width=_ancho_dialogo(page),
            content=ft.Column(
                tight=True,
                spacing=10,
                controls=controles,
            ),
        ),
        actions_alignment=ft.MainAxisAlignment.END,
        actions=[
            ft.TextButton("Cancelar", on_click=cerrar),
            ft.ElevatedButton("Guardar", on_click=confirmar),
        ],
    )

    renderizar_arbol()
    mostrar_dialogo(page, dialog)
