from ui.tareas import ejecutar_demorado


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

        ejecutar_demorado(page, 0.12, restaurar)

    try:
        page.window.focused = True
        page.update()
    except Exception:
        pass
