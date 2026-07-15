import threading
import time


def ejecutar_demorado(page, segundos, funcion):
    """Ejecuta una tarea corta luego de una pausa sin romper la version web."""

    def ejecutar_seguro():
        try:
            funcion()
        except Exception:
            pass

    if bool(getattr(page, "web", False)):
        ejecutar_seguro()
        return

    def ejecutar():
        if segundos > 0:
            time.sleep(segundos)
        ejecutar_seguro()

    try:
        threading.Thread(target=ejecutar, daemon=True).start()
    except Exception:
        ejecutar_seguro()
