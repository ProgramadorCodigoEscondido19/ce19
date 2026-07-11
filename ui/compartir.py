from urllib.parse import quote
import base64
from pathlib import Path

import flet as ft
from flet.controls.services.url_launcher import LaunchMode


def _obtener_url_launcher(page):
    launcher = getattr(page, "_codigo19_url_launcher", None)

    if launcher is not None:
        return launcher

    launcher = ft.UrlLauncher()
    setattr(page, "_codigo19_url_launcher", launcher)

    try:
        page.services.append(launcher)
        page.update()
    except Exception:
        pass

    return launcher


def _programar(page, tarea, *args):
    try:
        if hasattr(page, "run_task"):
            page.run_task(tarea, *args)
            return True
    except Exception:
        return False

    return False


def _snack(page, mensaje):
    try:
        page.snack_bar = ft.SnackBar(ft.Text(mensaje))
        page.snack_bar.open = True
        page.update()
    except Exception:
        pass


async def _abrir_url_async(page, url, modo=LaunchMode.EXTERNAL_APPLICATION):
    launcher = _obtener_url_launcher(page)

    try:
        await launcher.launch_url(url, mode=modo)
        return True
    except Exception:
        try:
            await launcher.launch_url(url, mode=LaunchMode.EXTERNAL_APPLICATION)
            return True
        except Exception:
            pass

    try:
        await page.launch_url(url, web_popup_window=True)
        return True
    except Exception:
        _snack(page, "No se pudo abrir el enlace para compartir.")
        return False


def _abrir_url(page, url, modo=LaunchMode.EXTERNAL_APPLICATION):
    return _programar(page, _abrir_url_async, page, url, modo)


async def _copiar_texto_async(page, texto):
    try:
        clipboard = getattr(page, "clipboard", None)

        if clipboard and hasattr(clipboard, "set"):
            await clipboard.set(str(texto))
            _snack(page, "Contenido copiado.")
            return True
    except Exception:
        pass

    _snack(page, "No se pudo copiar el contenido.")
    return False


def _copiar_texto(page, texto):
    return _programar(page, _copiar_texto_async, page, texto)


async def _servicio_compartir_texto_async(page, texto, titulo):
    try:
        servicio = ft.Share()
        page.services.append(servicio)
        page.update()
        await servicio.share_text(texto, title=titulo)
        return True
    except Exception:
        _snack(page, "No se pudo abrir el panel de compartir.")
        return False


def _servicio_compartir_texto(page, texto, titulo):
    return _programar(page, _servicio_compartir_texto_async, page, texto, titulo)


def _mostrar_dialogo_compartir_texto(page, texto, titulo, urls):
    def cerrar(e=None):
        dialog.open = False
        page.update()

    def abrir(url, modo):
        cerrar()
        _abrir_url(page, url, modo=modo)

    def compartir_sistema(e=None):
        cerrar()
        _servicio_compartir_texto(page, texto, titulo)

    def copiar_enlace(e=None):
        _copiar_texto(page, urls[-1])

    def copiar_texto(e=None):
        _copiar_texto(page, texto)

    dialog = ft.AlertDialog(
        title=ft.Text("Compartir"),
        content=ft.Text("Elija como quiere compartir este contenido."),
        actions=[
            ft.ElevatedButton(
                "WhatsApp",
                icon=ft.Icons.CHAT,
                on_click=lambda e: abrir(
                    urls[0],
                    LaunchMode.EXTERNAL_NON_BROWSER_APPLICATION,
                ),
            ),
            ft.OutlinedButton(
                "WhatsApp Web",
                on_click=lambda e: abrir(
                    urls[1],
                    LaunchMode.EXTERNAL_APPLICATION,
                ),
            ),
            ft.OutlinedButton(
                "Compartir",
                icon=ft.Icons.SHARE,
                on_click=compartir_sistema,
            ),
            ft.OutlinedButton(
                "Copiar enlace",
                on_click=copiar_enlace,
            ),
            ft.TextButton(
                "Copiar texto",
                on_click=copiar_texto,
            ),
            ft.TextButton("Cerrar", on_click=cerrar),
        ],
    )

    page.overlay.append(dialog)
    dialog.open = True
    page.update()
    return True


def compartir_texto(page, texto, titulo="Compartir"):
    texto = str(texto)
    texto_url = quote(texto, safe="")
    urls_whatsapp = [
        f"whatsapp://send?text={texto_url}",
        f"https://api.whatsapp.com/send?text={texto_url}",
        f"https://wa.me/?text={texto_url}",
    ]

    return _mostrar_dialogo_compartir_texto(
        page,
        texto,
        titulo,
        urls_whatsapp,
    )


async def _compartir_imagen_base64_async(
    page,
    imagen_base64,
    nombre,
    titulo,
    mime_type,
):
    try:
        datos = base64.b64decode(imagen_base64)
        archivo = ft.ShareFile(
            data=datos,
            mime_type=mime_type,
            name=nombre,
        )
        servicio = ft.Share()
        page.services.append(servicio)
        page.update()
        await servicio.share_files(
            [archivo],
            title=titulo,
            text=titulo,
            preview_thumbnail=archivo,
        )
        return True
    except Exception:
        _snack(page, "No se pudo abrir el panel de compartir imagen.")
        return await _abrir_url_async(
            page,
            "https://wa.me/",
            modo=LaunchMode.EXTERNAL_APPLICATION,
        )


def _mostrar_dialogo_compartir_archivo(page, titulo, ejecutar_compartir, ayuda):
    def cerrar(e=None):
        dialog.open = False
        page.update()

    def compartir(e=None):
        cerrar()
        ejecutar_compartir()

    def abrir_whatsapp(e=None):
        cerrar()
        _abrir_url(
            page,
            "whatsapp://send",
            modo=LaunchMode.EXTERNAL_NON_BROWSER_APPLICATION,
        )

    dialog = ft.AlertDialog(
        title=ft.Text("Compartir"),
        content=ft.Text(ayuda),
        actions=[
            ft.ElevatedButton(
                "WhatsApp / Apps",
                icon=ft.Icons.CHAT,
                on_click=compartir,
            ),
            ft.OutlinedButton(
                "Compartir",
                icon=ft.Icons.SHARE,
                on_click=compartir,
            ),
            ft.TextButton(
                "Abrir WhatsApp",
                on_click=abrir_whatsapp,
            ),
            ft.TextButton("Cerrar", on_click=cerrar),
        ],
    )

    page.overlay.append(dialog)
    dialog.open = True
    page.update()
    return True


def compartir_imagen_base64(
    page,
    imagen_base64,
    nombre="pizarra.jpg",
    titulo="Compartir",
    mime_type="image/jpeg",
):
    def ejecutar():
        _programar(
            page,
            _compartir_imagen_base64_async,
            page,
            imagen_base64,
            nombre,
            titulo,
            mime_type,
        )

    return _mostrar_dialogo_compartir_archivo(
        page,
        titulo,
        ejecutar,
        "Se abrira el panel para compartir. Elija WhatsApp para enviar la imagen.",
    )


async def _compartir_archivo_async(page, archivo, titulo, mime_type):
    try:
        ruta = Path(archivo)
        servicio = ft.Share()
        page.services.append(servicio)
        page.update()
        await servicio.share_files(
            [
                ft.ShareFile(
                    path=str(ruta),
                    name=ruta.name,
                    mime_type=mime_type,
                )
            ],
            title=titulo,
            subject=titulo,
        )
        return True
    except Exception:
        _snack(page, "No se pudo abrir el panel para exportar el archivo.")
        return False


def compartir_archivo(
    page,
    archivo,
    titulo="Exportar archivo",
    mime_type="application/octet-stream",
):
    def ejecutar():
        _programar(
            page,
            _compartir_archivo_async,
            page,
            archivo,
            titulo,
            mime_type,
        )

    return _mostrar_dialogo_compartir_archivo(
        page,
        titulo,
        ejecutar,
        "Se abrira el panel para compartir. Elija WhatsApp para enviar el archivo.",
    )

