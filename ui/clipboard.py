import flet as ft


async def _copiar_async(page, texto):
    clipboard = getattr(page, "clipboard", None)

    if clipboard and hasattr(clipboard, "set"):
        await clipboard.set(str(texto))
        return True

    return False


def copiar_al_portapapeles(page, texto):
    try:
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Copiado correctamente"),
            duration=1500,
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=ft.Margin(left=18, top=0, right=18, bottom=72),
            show_close_icon=True,
        )
        page.snack_bar.open = True
        page.update()
    except Exception:
        pass

    try:
        if hasattr(page, "run_task"):
            page.run_task(_copiar_async, page, texto)
            return True
    except Exception:
        return False

    return False
