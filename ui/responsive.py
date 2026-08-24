class Responsive:
    
    #F() INIT================================
    def __init__(self, page):
        self.page = page

    def width(self):
        ancho_pagina = getattr(self.page, "width", None)
        ancho_ventana = (
            getattr(getattr(self.page, "window", None), "width", None)
            if hasattr(self.page, "window")
            else None
        )
        anchos = [
            ancho
            for ancho in (ancho_pagina, ancho_ventana)
            if isinstance(ancho, (int, float)) and ancho > 0
        ]
        return min(anchos) if anchos else 1200

    #F() IS MOBILE===========================
    def is_mobile(self):
        return self.width() < 700

    #F() IS TABLET===========================
    def is_tablet(self):
        return 700 <= self.width() < 1100

    #F() IS TABLET===========================
    def is_desktop(self):
        return self.width() >= 1100

    #F() MODE================================
    def mode(self):
        if self.is_mobile():
            return "mobile"
        elif self.is_tablet():
            return "tablet"
        return "desktop"
