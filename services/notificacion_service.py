import flet as ft


class NotificacionService:
    """Mensajes visuales simples y seguros para Flet."""

    @staticmethod
    def mostrar(page, mensaje, color=None, duracion_ms=2500):
        try:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(str(mensaje)),
                bgcolor=color,
                duration=duracion_ms,
                behavior=ft.SnackBarBehavior.FLOATING,
                margin=ft.Margin(left=18, top=0, right=18, bottom=72),
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
