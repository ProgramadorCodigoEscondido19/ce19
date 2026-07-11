async def _copiar_async(page, texto):
    clipboard = getattr(page, "clipboard", None)

    if clipboard and hasattr(clipboard, "set"):
        await clipboard.set(str(texto))
        return True

    return False


def copiar_al_portapapeles(page, texto):
    try:
        if hasattr(page, "run_task"):
            page.run_task(_copiar_async, page, texto)
            return True
    except Exception:
        return False

    return False
