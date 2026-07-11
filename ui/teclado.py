import threading


def ocultar_teclado(page, *controles):
    controles = [control for control in controles if control is not None]

    for control in controles:
        if not hasattr(control, "can_request_focus"):
            continue

        try:
            control.can_request_focus = False
            control.update()
        except Exception:
            pass

        def restaurar(c=control):
            try:
                c.can_request_focus = True
                c.update()
            except Exception:
                pass

        threading.Timer(0.12, restaurar).start()

    try:
        page.window.focused = True
        page.update()
    except Exception:
        pass
