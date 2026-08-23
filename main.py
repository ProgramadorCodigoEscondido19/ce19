import flet as ft

from router import Router
from services.app_config_service import AppConfigService
from services.app_paths import AppPaths
from services.app_startup_service import AppStartupService
from services.permisos_service import PermisosService
from ui.intro import construir_intro
from ui.tema import APP_NAME, APP_VERSION, DORADO, PERLA_PANEL, PURPURA_INICIAL, PURPURA_IOS, icono_estrella


FONDO_REGION_MARRON = "#5F3A2C"
MARRON_ACENTO = "#87543D"
MARRON_CLARO = "#F4E4D8"
MARRON_BORDE = "#E6CCBC"


PAISES_HISPANOS = [
    ("Argentina", 0.322, 0.821),
    ("Bolivia", 0.322, 0.703),
    ("Chile", 0.303, 0.828),
    ("Colombia", 0.294, 0.559),
    ("Costa Rica", 0.267, 0.517),
    ("Cuba", 0.281, 0.434),
    ("Ecuador", 0.283, 0.597),
    ("El Salvador", 0.253, 0.490),
    ("España", 0.489, 0.310),
    ("Guatemala", 0.250, 0.479),
    ("Guinea Ecuatorial", 0.528, 0.576),
    ("Honduras", 0.261, 0.483),
    ("Mexico", 0.217, 0.428),
    ("Nicaragua", 0.264, 0.497),
    ("Panama", 0.278, 0.528),
    ("Paraguay", 0.339, 0.745),
    ("Peru", 0.292, 0.655),
    ("Republica Dominicana", 0.306, 0.455),
    ("Uruguay", 0.344, 0.814),
    ("Venezuela", 0.317, 0.538),
]

MARCAS_BLOQUEADAS = [
    ("Canada", 0.208, 0.193),
    ("Estados Unidos", 0.228, 0.317),
    ("Brasil", 0.358, 0.655),
    ("Francia", 0.506, 0.269),
    ("Italia", 0.533, 0.297),
    ("Reino Unido", 0.494, 0.214),
    ("Marruecos", 0.483, 0.366),
    ("Egipto", 0.583, 0.400),
    ("Sudafrica", 0.569, 0.793),
    ("India", 0.719, 0.434),
    ("China", 0.789, 0.345),
    ("Japon", 0.883, 0.338),
    ("Australia", 0.872, 0.759),
]

COLORES_BANDERAS = {
    "Argentina": ("#75AADB", "#FFFFFF", "#75AADB"),
    "Bolivia": ("#D52B1E", "#F9E300", "#007A33"),
    "Chile": ("#0039A6", "#FFFFFF", "#D52B1E"),
    "Colombia": ("#FCD116", "#003893", "#CE1126"),
    "Costa Rica": ("#002B7F", "#FFFFFF", "#CE1126", "#FFFFFF", "#002B7F"),
    "Cuba": ("#002A8F", "#FFFFFF", "#CE1126"),
    "Ecuador": ("#FCD116", "#003893", "#CE1126"),
    "El Salvador": ("#0F47AF", "#FFFFFF", "#0F47AF"),
    "Guatemala": ("#4AB3E7", "#FFFFFF", "#4AB3E7"),
    "Guinea Ecuatorial": ("#FFFFFF", "#009B3A", "#E32118"),
    "Honduras": ("#0073CF", "#FFFFFF", "#0073CF"),
    "Mexico": ("#006847", "#FFFFFF", "#CE1126"),
    "Nicaragua": ("#0067C6", "#FFFFFF", "#0067C6"),
    "Panama": ("#FFFFFF", "#D21034", "#005293"),
    "Paraguay": ("#D52B1E", "#FFFFFF", "#0038A8"),
    "Peru": ("#D91023", "#FFFFFF", "#D91023"),
    "Republica Dominicana": ("#002D62", "#FFFFFF", "#CE1126"),
    "Uruguay": ("#FFFFFF", "#0F47AF", "#FFFFFF"),
    "Venezuela": ("#FCD116", "#003893", "#CE1126"),
}

COLORES_BANDERAS["Espa\u00f1a"] = ("#AA151B", "#F1BF00", "#AA151B")

CONTINENTES_DISPONIBLES = {
    "Am\u00e9rica": {
        "icono": ft.Icons.PUBLIC,
        "paises": {
            "Argentina", "Bolivia", "Chile", "Colombia", "Costa Rica", "Cuba", "Ecuador",
            "El Salvador", "Guatemala", "Honduras", "Mexico", "Nicaragua", "Panama",
            "Paraguay", "Peru", "Republica Dominicana", "Uruguay", "Venezuela",
        },
    },
    "Europa": {"icono": ft.Icons.LANGUAGE, "paises": {"Espa\u00f1a"}},
    "\u00c1frica": {"icono": ft.Icons.LANGUAGE, "paises": {"Guinea Ecuatorial"}},
}

CONTINENTES_BLOQUEADOS = ("Asia", "Ocean\u00eda")

# Cada grupo representa una version de idioma. Las banderas se agrupan para
# que elegir una version no dependa de un pais puntual.
IDIOMAS_CONTINENTE = {
    "Am\u00e9rica": [
        {
            "codigo": "es",
            "nombre": "Espa\u00f1ol",
            "paises": (
                "Argentina", "Bolivia", "Chile", "Colombia", "Costa Rica", "Cuba", "Ecuador",
                "El Salvador", "Guatemala", "Honduras", "Mexico", "Nicaragua", "Panama",
                "Paraguay", "Peru", "Republica Dominicana", "Uruguay", "Venezuela",
            ),
            "disponible": True,
        },
    ],
    "Europa": [
        {"codigo": "es", "nombre": "Espa\u00f1ol", "paises": ("Espa\u00f1a",), "disponible": True},
    ],
    "\u00c1frica": [
        {"codigo": "es", "nombre": "Espa\u00f1ol", "paises": ("Guinea Ecuatorial",), "disponible": True},
    ],
}

# Cada vista usa un recorte propio del mapa mundial. Asi el continente ocupa
# el espacio de lectura y los marcadores no compiten con el resto del mundo.
VISTAS_MAPA_CONTINENTE = {
    "Am\u00e9rica": {"src": "mapa_america.png", "marco": (0.028, 0.431, 0.069, 1.000), "proporcion": 1.2},
    "Europa": {"src": "mapa_europa.png", "marco": (0.431, 0.625, 0.069, 0.379), "proporcion": 1.54},
    "\u00c1frica": {"src": "mapa_africa.png", "marco": (0.417, 0.681, 0.324, 0.848), "proporcion": 1.25},
}

# Ajustes solo para paises muy cercanos geograficamente. Conservan la zona
# real, pero evitan que sus pines se monten unos sobre otros.
AJUSTES_PINES_AMERICA = {
    "Guatemala": (-42, -28),
    "El Salvador": (-34, 20),
    "Honduras": (-7, -30),
    "Nicaragua": (25, -2),
    "Costa Rica": (38, 22),
    "Panama": (60, 30),
}

BANDERAS_IMAGEN = {
    "Cuba": "banderas/cuba.png",
    "Chile": "banderas/chile.png",
    "Republica Dominicana": "banderas/republica_dominicana.png",
}

BANDEJAS_PAISES = {
    "Argentina": "🇦🇷", "Bolivia": "🇧🇴", "Chile": "🇨🇱", "Colombia": "🇨🇴",
    "Costa Rica": "🇨🇷", "Cuba": "🇨🇺", "Ecuador": "🇪🇨", "El Salvador": "🇸🇻",
    "España": "🇪🇸", "Guatemala": "🇬🇹", "Guinea Ecuatorial": "🇬🇶", "Honduras": "🇭🇳",
    "México": "🇲🇽", "Nicaragua": "🇳🇮", "Panamá": "🇵🇦", "Paraguay": "🇵🇾",
    "Perú": "🇵🇪", "República Dominicana": "🇩🇴", "Uruguay": "🇺🇾", "Venezuela": "🇻🇪",
}

NOMBRES_PAISES = {
    "Espana": "Espa\u00f1a",
    "Mexico": "M\u00e9xico",
    "Panama": "Panam\u00e1",
    "Peru": "Per\u00fa",
    "Republica Dominicana": "Rep\u00fablica Dominicana",
}

BANDEJAS_PAISES.update({
    "Espana": "\U0001F1EA\U0001F1F8",
    "Mexico": "\U0001F1F2\U0001F1FD",
    "Panama": "\U0001F1F5\U0001F1E6",
    "Peru": "\U0001F1F5\U0001F1EA",
    "Republica Dominicana": "\U0001F1E9\U0001F1F4",
})


def main(page: ft.Page):
    AppStartupService.configurar_page(page)
    page.bgcolor = PURPURA_INICIAL

    root = ft.Container(expand=True)
    page.add(root)

    # Los archivos locales no sobreviven a una recarga de GitHub Pages. Estas
    # preferencias mantienen el acceso por nivel recordado en el navegador.
    preferencias_web = ft.SharedPreferences()
    page.services.append(preferencias_web)
    CLAVE_WEB_NIVELES = "ce19.niveles_autorizados.v1"

    app_iniciada = {"valor": False}
    selector_niveles_activo = {"valor": False}
    router_actual = {"valor": None}
    configuracion_region = AppConfigService.leer_json(AppPaths.CONFIG_APP, {}) or {}
    region_guardada = configuracion_region.get("region", {})
    idioma_seleccionado = {"valor": region_guardada.get("idioma", "")}
    continente_seleccionado = {"valor": None}

    PermisosService.establecer_niveles_sesion(PermisosService.niveles_autorizados())

    async def cargar_preferencias_web():
        """Carga los datos persistentes del navegador al iniciar la app web."""
        try:
            niveles = await preferencias_web.get(CLAVE_WEB_NIVELES)
            if isinstance(niveles, list):
                PermisosService.establecer_niveles_sesion(niveles)

        except Exception:
            # La app sigue funcionando con el respaldo local en plataformas
            # que no ofrezcan preferencias persistentes.
            return

        if selector_niveles_activo["valor"]:
            mostrar_selector_niveles()

    async def guardar_niveles_web():
        try:
            niveles = [str(nivel) for nivel in sorted(PermisosService.niveles_autorizados())]
            await preferencias_web.set(CLAVE_WEB_NIVELES, niveles)
        except Exception:
            pass

    def iniciar_app(nivel=4):
        if app_iniciada["valor"]:
            router = router_actual["valor"]
            if router is not None:
                selector_niveles_activo["valor"] = False
                router.nivel = nivel
                AppStartupService.crear_navigation_bar(page, router)
                router.navegar("inicio")
            return

        app_iniciada["valor"] = True

        try:
            AppStartupService.preparar_estructura_base()
            AppStartupService.intentar_backup_auto()
            AppStartupService.inicializar_estado(page)

            router = Router(page, nivel=nivel)
            router.root = root
            router.on_cambiar_nivel = mostrar_selector_niveles
            router_actual["valor"] = router
            selector_niveles_activo["valor"] = False

            AppStartupService.registrar_vistas(router, page)
            AppStartupService.crear_navigation_bar(page, router)
            router.iniciar("inicio")

            ultimo_modo = {"movil": router._es_movil()}

            def adaptar_al_tamano(e=None):
                if selector_niveles_activo["valor"]:
                    return
                modo_movil = router._es_movil()
                if modo_movil != ultimo_modo["movil"]:
                    ultimo_modo["movil"] = modo_movil
                    router.refrescar()
                else:
                    router._actualizar_barra_inferior()

            page.on_resize = adaptar_al_tamano

        except Exception as error:
            AppStartupService.pantalla_error(
                root,
                "No se pudo iniciar la app",
                error,
            )

        page.update()

    def mostrar_selector_pais(e=None):
        """Configura la region inicial sin cambiar la Biblia ni los datos locales."""
        selector_niveles_activo["valor"] = True
        if page.navigation_bar:
            page.navigation_bar.visible = False

        ancho_pantalla = getattr(page, "width", None) or 1000
        es_movil = ancho_pantalla < 700
        continente_actual = continente_seleccionado["valor"]
        # En la segunda etapa el mapa funciona como referencia del continente:
        # debe verse entero y dejar espacio inmediato para elegir el idioma.
        ancho_mapa = (
            max(250, int(ancho_pantalla) - 48)
            if es_movil
            else (500 if continente_actual else 720)
        )
        # Los mapas generados tienen una proporcion 2:1. Se conserva siempre
        # para que no se estiren al mostrar un continente ampliado.
        proporcion_mapa = VISTAS_MAPA_CONTINENTE.get(continente_actual, {}).get("proporcion", 2)
        alto_mapa = max(125, int(ancho_mapa / proporcion_mapa))
        # El selector debe dejar siempre a la vista la accion final. Si la
        # ventana es baja, reducimos el mapa sin alterar su proporcion.
        alto_pantalla = getattr(page, "height", None) or 720
        alto_maximo_mapa = max(180 if es_movil else 250, int(alto_pantalla) - (390 if es_movil else 360))
        if alto_mapa > alto_maximo_mapa:
            alto_mapa = alto_maximo_mapa
            ancho_mapa = int(alto_mapa * proporcion_mapa)

        def cantidad_pais(nombre):
            return 0
            paises = {}
            alternativas = {
                nombre,
                NOMBRES_PAISES.get(nombre, nombre),
                nombre.replace("Espana", "España"),
                nombre.replace("Mexico", "México"),
                nombre.replace("Panama", "Panamá"),
                nombre.replace("Peru", "Perú"),
                nombre.replace("Republica", "República"),
            }
            for alternativa in alternativas:
                if alternativa in paises:
                    return int(paises.get(alternativa, 0) or 0)
            return 0

        def marcador_registro(nombre, posicion_x, posicion_y, vista):
            return None
            cantidad = cantidad_pais(nombre)
            if cantidad <= 0:
                return None
            marco = vista.get("marco") if vista else None
            if marco:
                x1, x2, y1, y2 = marco
                proporcion_x = (posicion_x - x1) / (x2 - x1)
                proporcion_y = (posicion_y - y1) / (y2 - y1)
            else:
                proporcion_x, proporcion_y = posicion_x, posicion_y
            if not (0 <= proporcion_x <= 1 and 0 <= proporcion_y <= 1):
                return None
            return ft.Container(
                left=max(3, min(ancho_mapa - 48, int(proporcion_x * ancho_mapa) - 18)),
                top=max(3, min(alto_mapa - 29, int(proporcion_y * alto_mapa) - 14)),
                padding=ft.Padding(left=5, top=3, right=5, bottom=3),
                border_radius=10,
                bgcolor="#5F3A2C",
                border=ft.Border.all(1, "#FFF9EF"),
                tooltip=f"{NOMBRES_PAISES.get(nombre, nombre)}: {cantidad} registro(s)",
                content=ft.Row(
                    tight=True,
                    spacing=3,
                    controls=[
                        bandera_pais(nombre, ancho=15, alto=10),
                        ft.Text(str(cantidad), size=10, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                    ],
                ),
            )

        def adaptar_selector_pais(evento=None):
            if selector_niveles_activo["valor"]:
                mostrar_selector_pais()

        page.on_resize = adaptar_selector_pais

        def seleccionar_idioma(codigo):
            idioma_seleccionado["valor"] = codigo
            construir_pantalla()

        def seleccionar_continente(nombre):
            continente_seleccionado["valor"] = nombre
            idioma_seleccionado["valor"] = ""
            # Reconstruye la etapa con medidas nuevas para que el continente
            # seleccionado use toda la superficie disponible.
            mostrar_selector_pais()

        def volver_a_continentes(evento=None):
            continente_seleccionado["valor"] = None
            idioma_seleccionado["valor"] = ""
            mostrar_selector_pais()

        def bandera_pais(nombre, ancho=24, alto=15):
            imagen_bandera = BANDERAS_IMAGEN.get(nombre)
            if imagen_bandera:
                return ft.Container(
                    width=ancho,
                    height=alto,
                    border_radius=3,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    border=ft.Border.all(1, "#D8CBDD"),
                    content=ft.Image(src=imagen_bandera, fit=ft.BoxFit.FILL),
                )
            colores = COLORES_BANDERAS.get(nombre, ("#AA151B", "#F1BF00", "#AA151B"))
            verticales = {"Mexico", "Peru", "Guatemala"}
            if nombre in verticales:
                contenido = ft.Row(
                    spacing=0,
                    controls=[ft.Container(expand=True, bgcolor=color) for color in colores],
                )
            elif nombre == "Panama":
                contenido = ft.Column(
                    spacing=0,
                    controls=[
                        ft.Row(spacing=0, expand=True, controls=[ft.Container(expand=True, bgcolor="#FFFFFF"), ft.Container(expand=True, bgcolor="#D21034")]),
                        ft.Row(spacing=0, expand=True, controls=[ft.Container(expand=True, bgcolor="#005293"), ft.Container(expand=True, bgcolor="#FFFFFF")]),
                    ],
                )
            elif nombre == "Republica Dominicana":
                contenido = ft.Column(
                    spacing=0,
                    controls=[
                        ft.Row(spacing=0, expand=True, controls=[ft.Container(expand=True, bgcolor="#002D62"), ft.Container(expand=True, bgcolor="#CE1126")]),
                        ft.Row(spacing=0, expand=True, controls=[ft.Container(expand=True, bgcolor="#CE1126"), ft.Container(expand=True, bgcolor="#002D62")]),
                    ],
                )
            else:
                alto_franja = max(2, alto // len(colores))
                contenido = ft.Column(
                    spacing=0,
                    controls=[ft.Container(height=alto_franja, bgcolor=color) for color in colores],
                )
            return ft.Container(
                width=ancho,
                height=alto,
                border_radius=3,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                border=ft.Border.all(1, "#D8CBDD"),
                content=contenido,
            )

        def continuar(e=None):
            idioma = idioma_seleccionado["valor"]
            if not idioma:
                return
            datos = AppConfigService.leer_json(AppPaths.CONFIG_APP, {}) or {}
            datos["region"] = {
                "pais": "",
                "continente": continente_seleccionado["valor"],
                "idioma": idioma,
                "biblia": "Reina Valera 1960",
            }
            AppConfigService.guardar_json(AppPaths.CONFIG_APP, datos)
            mostrar_selector_niveles()

        def ficha_continente(nombre, disponible=True):
            datos = CONTINENTES_DISPONIBLES.get(nombre, {})
            seleccionado = continente_seleccionado["valor"] == nombre
            return ft.Container(
                width=150 if not es_movil else 128,
                height=82 if es_movil else 92,
                padding=10,
                border_radius=14,
                border=ft.Border.all(1.5, DORADO if seleccionado else "#E6D8EA"),
                bgcolor="#FFF7DE" if seleccionado else "#FFFFFFB8",
                ink=disponible,
                on_click=(lambda ev, n=nombre: seleccionar_continente(n)) if disponible else None,
                alignment=ft.Alignment(0, 0),
                content=ft.Column(
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=5,
                    controls=[
                        ft.Icon(datos.get("icono", ft.Icons.LOCK), size=22, color=PURPURA_IOS if disponible else "#9A8F9E"),
                        ft.Text(nombre, size=12 if es_movil else 13, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            f"{len(datos.get('paises', []))} pa\u00edses disponibles" if disponible else "Pr\u00f3ximamente",
                            size=9 if es_movil else 10,
                            color="#746879",
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                ),
            )

        def grupo_idioma(datos):
            codigo = datos["codigo"]
            disponible = datos.get("disponible", False)
            seleccionado = idioma_seleccionado["valor"] == codigo
            color_borde = DORADO if seleccionado else (PURPURA_IOS if disponible else "#D8CDD9")
            return ft.Container(
                width=None if es_movil else 340,
                padding=12,
                border_radius=14,
                bgcolor="#FFF9E9" if seleccionado else "#FFFFFF",
                border=ft.Border.all(1.5, color_borde),
                ink=disponible,
                on_click=(lambda ev, c=codigo: seleccionar_idioma(c)) if disponible else None,
                content=ft.Column(
                    tight=True,
                    spacing=8,
                    controls=[
                        ft.Row(
                            tight=True,
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.LANGUAGE if disponible else ft.Icons.LOCK, color=PURPURA_IOS if disponible else "#8D8393", size=19),
                                ft.Text(datos["nombre"], weight=ft.FontWeight.BOLD, size=14),
                                ft.Text("Disponible" if disponible else "Pr\u00f3ximamente", size=11, color="#746879"),
                            ],
                        ),
                        ft.Row(
                            wrap=True,
                            spacing=5,
                            run_spacing=5,
                            controls=[bandera_pais(nombre, ancho=22, alto=14) for nombre in datos.get("paises", ())],
                        ),
                    ],
                ),
            )

        def construir_pantalla():
            idioma = idioma_seleccionado["valor"]
            continente = continente_seleccionado["valor"]
            vista_mapa = VISTAS_MAPA_CONTINENTE.get(continente)
            src_mapa = vista_mapa["src"] if vista_mapa else "mapa_mundo_hispano.png"
            mapa_base = ft.Image(
                src=src_mapa,
                width=ancho_mapa,
                height=alto_mapa,
                fit=ft.BoxFit.FILL,
            )
            # InteractiveViewer deja el mapa en gris en algunos equipos. El
            # mapa se muestra a su tamano natural y el ListView principal
            # permite recorrerlo completo sin deformarlo.
            mapa = ft.Container(
                width=ancho_mapa,
                height=alto_mapa,
                bgcolor="#FCFAFD",
                border_radius=12,
                border=ft.Border.all(1, "#E5DAE9"),
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=mapa_base,
            )

            encabezado = ft.Column(
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Row(
                        tight=True,
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.PUBLIC, color=PURPURA_IOS, size=27),
                            ft.Text(
                                "Elige una versi\u00f3n" if continente else "Elige tu continente",
                                size=23 if es_movil else 28,
                                weight=ft.FontWeight.BOLD,
                            ),
                        ],
                    ),
                    ft.Text(
                        "Selecciona un idioma para configurar tu experiencia." if continente else "Primero elige el continente desde donde deseas continuar.",
                        size=11 if es_movil else 13,
                        color="#6E6374",
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            )

            seleccion = ft.Container(
                padding=10,
                border_radius=12,
                bgcolor="#F7EDF9",
                border=ft.Border.all(1, "#E7D6EC"),
                content=ft.Row(
                    tight=True,
                    spacing=8,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE if idioma else ft.Icons.INFO_OUTLINE, color=PURPURA_IOS, size=19),
                        ft.Text(
                            "Espa\u00f1ol seleccionado" if idioma else (
                                f"{continente} seleccionado. Elige una versi\u00f3n de idioma" if continente else "Selecciona un continente para continuar"
                            ),
                            size=12 if es_movil else 13,
                            weight=ft.FontWeight.W_500,
                        ),
                    ],
                ),
            )

            if continente:
                selector_paso = ft.Column(
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=9,
                    controls=[
                        ft.TextButton("Volver a continentes", icon=ft.Icons.ARROW_BACK, on_click=volver_a_continentes),
                        ft.Text("Versiones disponibles", size=13, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "Las banderas reunidas usan la misma versión de idioma.",
                            size=11,
                            color="#746879",
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Column(
                            tight=True,
                            spacing=8,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[grupo_idioma(datos) for datos in IDIOMAS_CONTINENTE.get(continente, ())],
                        ),
                    ],
                )
            else:
                selector_paso = ft.Column(
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=9,
                    controls=[
                        ft.Text("Continentes", size=13, weight=ft.FontWeight.BOLD),
                        ft.Row(
                            wrap=True,
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=9,
                            run_spacing=9,
                            controls=[
                                *[ficha_continente(nombre) for nombre in CONTINENTES_DISPONIBLES],
                                *[ficha_continente(nombre, disponible=False) for nombre in CONTINENTES_BLOQUEADOS],
                            ],
                        ),
                    ],
                )

            contenido_etapa = (
                ft.Column(
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                    controls=[mapa, selector_paso],
                )
                if es_movil or not continente
                else ft.Row(
                    tight=True,
                    spacing=24,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        mapa,
                        ft.Container(width=360, content=selector_paso),
                    ],
                )
            )

            estado_final = (
                ft.Column(
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                    controls=[seleccion],
                )
                if es_movil
                else ft.Row(
                    tight=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=16,
                    controls=[seleccion],
                )
            )

            panel = ft.Container(
                width=max(280, int(ancho_pantalla) - 20) if es_movil else (950 if continente else 900),
                padding=12 if es_movil else 18,
                bgcolor=PERLA_PANEL,
                border_radius=26,
                border=ft.Border.all(1, "#E7DBEB"),
                content=ft.Column(
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=14 if es_movil else 18,
                    controls=[
                        encabezado,
                        contenido_etapa,
                        estado_final,
                        *([
                            ft.ElevatedButton(
                                "Continuar",
                                icon=ft.Icons.ARROW_FORWARD,
                                bgcolor=PURPURA_IOS,
                                color=ft.Colors.WHITE,
                                on_click=continuar,
                            )
                        ] if idioma else []),
                    ],
                ),
            )

            root.content = ft.Container(
                expand=True,
                bgcolor=FONDO_REGION_MARRON,
                content=ft.ListView(
                    expand=True,
                    padding=10 if es_movil else 16,
                    spacing=0,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[panel],
                        )
                    ],
                ),
            )
            page.update()

        construir_pantalla()

    def mostrar_selector_niveles(e=None):
        """Permite escoger un nivel antes de montar las vistas de la app."""
        selector_niveles_activo["valor"] = True
        if page.navigation_bar:
            page.navigation_bar.visible = False
        ancho = getattr(page, "width", None) or 900
        es_movil = ancho < 700

        def adaptar_selector_niveles(evento=None):
            if selector_niveles_activo["valor"]:
                mostrar_selector_niveles()

        page.on_resize = adaptar_selector_niveles

        def tarjeta_nivel(nivel):
            autorizado = PermisosService.esta_autorizado(nivel)

            casilla = ft.Container(
                width=16,
                height=16,
                border_radius=4,
                border=ft.Border.all(1.5, MARRON_ACENTO if autorizado else "#8B778F"),
                bgcolor=MARRON_ACENTO if autorizado else ft.Colors.TRANSPARENT,
                alignment=ft.Alignment(0, 0),
                content=ft.Icon(ft.Icons.CHECK, size=12, color=ft.Colors.WHITE) if autorizado else None,
            )

            estado_acceso = ft.Text(
                "Ingreso habilitado" if autorizado else "Solicita clave la primera vez",
                size=9 if es_movil else 10,
                color="#6E6374",
                text_align=ft.TextAlign.CENTER,
            )

            def alternar_guardar_acceso(ev=None):
                if PermisosService.esta_autorizado(nivel):
                    PermisosService.revocar(nivel)
                    page.run_task(guardar_niveles_web)
                    casilla.bgcolor = ft.Colors.TRANSPARENT
                    casilla.border = ft.Border.all(1.5, "#8B778F")
                    casilla.content = None
                    estado_acceso.value = "Solicitara clave al ingresar"
                else:
                    pedir_clave(nivel)
                    return
                page.update()

            return ft.Container(
                expand=True,
                height=126 if es_movil else 146,
                padding=10,
                border_radius=16,
                bgcolor=PERLA_PANEL,
                border=ft.Border.all(1, MARRON_BORDE),
                content=ft.Column(
                    expand=True,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    spacing=3,
                    controls=[
                        ft.Container(
                            expand=True,
                            ink=True,
                            border_radius=12,
                            on_click=lambda ev, n=nivel: elegir_nivel(n),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Column(
                                tight=True,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=4,
                                controls=[
                                    ft.Container(
                                        width=40,
                                        height=40,
                                        border_radius=14,
                                        bgcolor=MARRON_CLARO,
                                        alignment=ft.Alignment(0, 0),
                                        content=ft.Text(str(nivel), size=21, weight=ft.FontWeight.BOLD, color=MARRON_ACENTO),
                                    ),
                                    ft.Text(f"Nivel {nivel}", size=15, weight=ft.FontWeight.BOLD),
                                    estado_acceso,
                                ],
                            ),
                        ),
                        ft.Container(
                            height=22,
                            ink=True,
                            border_radius=6,
                            on_click=alternar_guardar_acceso,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Row(
                                tight=True,
                                spacing=6,
                                alignment=ft.MainAxisAlignment.CENTER,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    casilla,
                                    ft.Text("Guardar acceso", size=10, color="#5F5365"),
                                ],
                            ),
                        ),
                    ],
                ),
            )

        def volver_niveles(ev=None):
            mostrar_selector_niveles()

        def volver_a_region(ev=None):
            # Mantiene la region actual a la vista para que el usuario pueda
            # volver un paso y cambiar continente o idioma cuando lo necesite.
            mostrar_selector_pais()

        def pedir_clave(nivel):
            clave = ft.TextField(
                label=f"Clave del Nivel {nivel}",
                password=True,
                can_reveal_password=True,
                autofocus=True,
                on_submit=lambda ev: confirmar_clave(),
            )
            guardar_clave = ft.Checkbox(
                label="Guardar contraseña en este dispositivo",
                value=False,
            )
            error = ft.Text("", color=ft.Colors.RED, size=12, visible=False)

            def confirmar_clave(ev=None):
                if PermisosService.validar_clave(nivel, clave.value or ""):
                    if guardar_clave.value:
                        PermisosService.autorizar(nivel, guardar=True)
                    else:
                        PermisosService.revocar(nivel)
                    page.run_task(guardar_niveles_web)
                    iniciar_app(nivel)
                    return
                error.value = "La clave no es correcta."
                error.visible = True
                page.update()

            root.content = ft.Container(
                expand=True,
                alignment=ft.Alignment(0, 0),
                bgcolor=FONDO_REGION_MARRON,
                padding=20,
                content=ft.Container(
                    width=390,
                    padding=26,
                    bgcolor=PERLA_PANEL,
                    border_radius=24,
                    content=ft.Column(
                        tight=True,
                        spacing=14,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            icono_estrella(56),
                            ft.Text(f"Nivel {nivel}", size=24, weight=ft.FontWeight.BOLD),
                            ft.Text("Ingrese la clave para habilitar este nivel en el dispositivo.", size=12, text_align=ft.TextAlign.CENTER),
                            clave,
                            guardar_clave,
                            error,
                            ft.Row(
                                alignment=ft.MainAxisAlignment.END,
                                controls=[
                                    ft.TextButton("Volver", on_click=volver_niveles),
                                    ft.ElevatedButton("Ingresar", icon=ft.Icons.LOCK_OPEN, bgcolor=MARRON_ACENTO, color=ft.Colors.WHITE, on_click=confirmar_clave),
                                ],
                            ),
                        ],
                    ),
                ),
            )
            page.update()

        def elegir_nivel(nivel):
            if PermisosService.esta_autorizado(nivel):
                iniciar_app(nivel)
            else:
                pedir_clave(nivel)

        root.content = ft.Container(
            expand=True,
            alignment=ft.Alignment(0, 0),
            bgcolor=FONDO_REGION_MARRON,
            padding=10 if es_movil else 20,
            content=ft.Container(
                width=None if es_movil else 640,
                padding=18 if es_movil else 28,
                bgcolor=PERLA_PANEL,
                border_radius=26,
                content=ft.Column(
                    tight=True,
                    spacing=12 if es_movil else 18,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            alignment=ft.Alignment(-1, 0),
                            content=ft.TextButton(
                                "Cambiar continente o idioma",
                                icon=ft.Icons.ARROW_BACK,
                                on_click=volver_a_region,
                            ),
                        ),
                        icono_estrella(52 if es_movil else 64),
                        ft.Text("Seleccione un nivel", size=23 if es_movil else 27, weight=ft.FontWeight.BOLD),
                        ft.Text("Elija el nivel con el que desea ingresar.", size=12 if es_movil else 13, color="#6E6374"),
                        ft.Row(
                            spacing=10,
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[tarjeta_nivel(1), tarjeta_nivel(2)],
                        ),
                        ft.Row(
                            spacing=10,
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[tarjeta_nivel(3), tarjeta_nivel(4)],
                        ),
                    ],
                ),
            ),
        )
        page.update()

    try:
        page.run_task(cargar_preferencias_web)
        intro, iniciar_animacion = construir_intro(page, mostrar_selector_pais)
        root.content = intro
        page.update()
        iniciar_animacion()
    except Exception:
        mostrar_selector_pais()


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets", name=APP_NAME)
