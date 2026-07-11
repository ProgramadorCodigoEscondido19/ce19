class AppState:
    def __init__(self):
        self._listeners = []

        self.historial = None
        self.guardados = None
        self.carpetas = None

    def bind(self, callback):
        if callback not in self._listeners:
            self._listeners.append(callback)

    def notify(self, event=None):
        for fn in list(self._listeners):
            try:
                fn(event)
            except (RuntimeError, AssertionError):
                pass

state = AppState()
