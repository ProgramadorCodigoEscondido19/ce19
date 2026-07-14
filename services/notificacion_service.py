import flet as ft


class NotificacionService:
    """Mensajes visuales simples y seguros para Flet."""

    @staticmethod
    def mostrar(page, mensaje, color=None, duracion_ms=2500):
        try:
            margen_inferior = 92
            ancho = getattr(page, "width", None)
            if ancho is None and hasattr(page, "window"):
                ancho = getattr(page.window, "width", None)

            page.snack_bar = ft.SnackBar(
                content=ft.Text(str(mensaje)),
                bgcolor=color,
                duration=duracion_ms,
                behavior=ft.SnackBarBehavior.FLOATING,
                margin=ft.Margin(12, 0, 12, margen_inferior),
                width=min(420, max(280, int((ancho or 420) - 24))),
                show_close_icon=True,
            )
            page.snack_bar.open = True
            page.update()
        except Exception:
            pass

    @staticmethod
    def exito(page, mensaje="Listo"):
        NotificacionService.mostrar(page, mensaje, ft.Colors.GREEN_700)

    @staticmethod
    def error(page, mensaje="Ocurrió un error"):
        NotificacionService.mostrar(page, mensaje, ft.Colors.RED_700)

    @staticmethod
    def info(page, mensaje):
        NotificacionService.mostrar(page, mensaje, ft.Colors.BLUE_700)
