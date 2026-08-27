import flet as ft

try:
    from ui.tema import (
        FONDO_APP,
        PERLA_BORDE,
        SUPERFICIE_PERLADA,
        TEXTO_PRINCIPAL,
        TEXTO_SECUNDARIO,
    )
except Exception:
    FONDO_APP = "#F7F4FB"
    PERLA_BORDE = "#E7DCEB"
    SUPERFICIE_PERLADA = "#FFFFFF"
    TEXTO_PRINCIPAL = "#201A23"
    TEXTO_SECUNDARIO = "#6F6476"


class DialogManager:
    """Punto común para las ventanas flotantes de la aplicación."""

    def __init__(self, page: ft.Page):
        self.page = page

    def mostrar(self, dialogo: ft.AlertDialog, cerrar_al_tocar_fuera=True):
        """Abre un diálogo nativo y permite cerrar tocando fuera por defecto."""
        dialogo.modal = not cerrar_al_tocar_fuera
        mostrar_nativo = getattr(self.page, "show_dialog", None)
        if callable(mostrar_nativo):
            try:
                mostrar_nativo(dialogo)
                return dialogo
            except RuntimeError:
                # Si Flet conserva el diálogo en su pila interna, creamos uno
                # nuevo desde el llamador o caemos al overlay de compatibilidad.
                pass
            except Exception:
                pass

        try:
            if dialogo not in self.page.overlay:
                self.page.overlay.append(dialogo)
            dialogo.open = True
            self.page.update()
            return dialogo
        except Exception:
            return dialogo

    def cerrar(self, dialogo: ft.AlertDialog | None = None):
        """Cierra correctamente diálogos nativos y los de compatibilidad."""
        cerrar_nativo = getattr(self.page, "pop_dialog", None)
        if callable(cerrar_nativo):
            try:
                cerrado = cerrar_nativo()
                if cerrado is not None:
                    return
            except Exception:
                pass

        try:
            if dialogo is not None:
                dialogo.open = False
                if dialogo in self.page.overlay:
                    self.page.overlay.remove(dialogo)
        except Exception:
            pass
        try:
            self.page.update()
        except Exception:
            pass

    def informacion(self, titulo, mensaje, on_cerrar=None):
        def cerrar(e=None):
            self.cerrar(dialogo)
            if on_cerrar:
                on_cerrar()

        dialogo = ft.AlertDialog(
            bgcolor=FONDO_APP,
            title=ft.Text(titulo, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
            content=ft.Container(
                width=460,
                padding=14,
                bgcolor=SUPERFICIE_PERLADA,
                border_radius=18,
                border=ft.Border.all(1, PERLA_BORDE),
                content=ft.Text(str(mensaje or ""), color=TEXTO_SECUNDARIO, selectable=True),
            ),
            actions=[ft.ElevatedButton("Aceptar", on_click=cerrar)],
        )
        return self.mostrar(dialogo)

    def confirmar(self, titulo, mensaje, on_aceptar, texto_aceptar="Aceptar", texto_cancelar="Cancelar"):
        def cerrar(e=None):
            self.cerrar(dialogo)

        def aceptar(e=None):
            cerrar()
            if on_aceptar:
                on_aceptar()

        dialogo = ft.AlertDialog(
            bgcolor=FONDO_APP,
            title=ft.Text(titulo, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
            content=ft.Container(
                width=460,
                padding=14,
                bgcolor=SUPERFICIE_PERLADA,
                border_radius=18,
                border=ft.Border.all(1, PERLA_BORDE),
                content=ft.Text(str(mensaje or ""), color=TEXTO_SECUNDARIO, selectable=True),
            ),
            actions=[
                ft.TextButton(texto_cancelar, on_click=cerrar),
                ft.ElevatedButton(texto_aceptar, on_click=aceptar, icon=ft.Icons.CHECK),
            ],
        )
        return self.mostrar(dialogo)


def mostrar_dialogo(page: ft.Page, dialogo: ft.AlertDialog, cerrar_al_tocar_fuera=True):
    return DialogManager(page).mostrar(dialogo, cerrar_al_tocar_fuera)


def cerrar_dialogo(page: ft.Page, dialogo: ft.AlertDialog | None = None):
    DialogManager(page).cerrar(dialogo)
