class Responsive:
    
    #F() INIT================================
    def __init__(self, page):
        self.page = page

    def width(self):
        ancho = getattr(self.page, "width", None)

        if ancho is None and hasattr(self.page, "window"):
            ancho = getattr(self.page.window, "width", None)

        return ancho or 1200

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
