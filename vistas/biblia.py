# Camino 2 - Biblia visual unificada
# Mantiene la logica del Camino 1 y solo mejora presentacion.

import json
import random
import re
import unicodedata
from pathlib import Path

import flet as ft

from core.app_state import state
from logica.biblia import (
    BIBLIA_ARCHIVO,
    buscar_texto,
    cargar_biblia,
    cargar_resaltados,
    guardar_resaltados,
    verso_id,
)
from logica.diccionario_hebreo import (
    entradas_diccionario,
    fragmentos_con_diccionario,
)
from services.biblia_service import BibliaService
from services.codificador_service import CodificadorService
from ui.clipboard import copiar_al_portapapeles
from ui.compartir import compartir_texto
from ui.nombre_guardado import pedir_nombre_y_carpeta_guardado
from ui.responsive import Responsive
from ui.tema import (
    PERLA_BORDE,
    PERLA_PANEL,
    PERLA_VIOLETA,
    SUPERFICIE_PERLADA,
    TEXTO_PRINCIPAL as TEMA_TEXTO_PRINCIPAL,
    TEXTO_SECUNDARIO as TEMA_TEXTO_SECUNDARIO,
    VIOLETA_IOS,
    sombra_suave,
)
from ui.teclado import ocultar_teclado


COLOR_BLANCO_BORDE = "Blanco borde"
BORDER_MARRON = "#B97852"

COLORES_RESALTADO = {
    "Negro": "#000000",
    "Marron": "#B97852",
    "Rojo": "#F01824",
    "Naranja": "#FF7A24",
    "Amarillo": "#FFF300",
    "Verde": "#24AE52",
    "Azul": "#4448C8",
    "Violeta": "#A44BA8",
    "Gris": "#C9C9C9",
    COLOR_BLANCO_BORDE: "#FFFFFF",
}
COLORES_TEXTO_RESALTADO = {
    "Negro": "#FFFFFF",
    "Azul": "#FFFFFF",
    "Violeta": "#FFFFFF",
}
ALIAS_COLORES_RESALTADO = {
    "Blanco": COLOR_BLANCO_BORDE,
}
DIGITO_A_COLOR = {
    1: "Marron",
    2: "Rojo",
    3: "Naranja",
    4: "Amarillo",
    5: "Verde",
    6: "Azul",
    7: "Violeta",
    8: "Gris",
    9: COLOR_BLANCO_BORDE,
}


# ===== ESTILO MODERNO LIMPIO PARA BIBLIA =====
FONDO_BIBLIA_MODERNO = ft.Colors.TRANSPARENT
TARJETA_BLANCA = SUPERFICIE_PERLADA
BORDE_SUAVE = PERLA_BORDE
TEXTO_PRINCIPAL = TEMA_TEXTO_PRINCIPAL
TEXTO_SECUNDARIO = TEMA_TEXTO_SECUNDARIO
ROJO_ACCENTO = "#FF2D55"
NARANJA_ACCENTO = "#FF9500"
AZUL_ACCENTO = "#0A84FF"
VIOLETA_ACCENTO = "#7C3AED"
VERDE_ACCENTO = "#34C759"
GRIS_SUAVE = "#F8F3FA"
ULTIMA_LECTURA_ARCHIVO = Path("datos/ultima_lectura_biblia.json")
LIBROS_PALABRAS_CORDERO = {"mateo", "marcos", "lucas", "juan", "apocalipsis"}
COLOR_PALABRAS_CORDERO = "#C1121F"
HISTORIAL_REFERENCIAS_ARCHIVO = Path("datos/historial_referencias_biblia.json")

CATEGORIAS_RANDOM_BIBLIA = [
    "General",
    "Salmos",
    "Evangelios",
    "Sabiduria",
    "Profecia",
]

LIBROS_RANDOM_POR_CATEGORIA = {
    "Salmos": {"salmos"},
    "Evangelios": {"mateo", "marcos", "lucas", "juan"},
    "Sabiduria": {"proverbios", "eclesiastes", "job", "santiago"},
    "Profecia": {
        "isaias",
        "jeremias",
        "ezequiel",
        "daniel",
        "oseas",
        "joel",
        "amos",
        "abdias",
        "jonas",
        "miqueas",
        "nahum",
        "habacuc",
        "sofonias",
        "hageo",
        "zacarias",
        "malaquias",
        "apocalipsis",
    },
}

ABREVIATURAS_LIBROS = {
    "Génesis": ("gn", "gen", "ge"),
    "Éxodo": ("ex", "exo"),
    "Levítico": ("lv", "lev"),
    "Números": ("nm", "num", "nu"),
    "Deuteronomio": ("dt", "deut"),
    "Josué": ("jos", "josue", "js"),
    "Jueces": ("jue", "juec", "jueces"),
    "Rut": ("rt", "rut"),
    "1 Samuel": ("1s", "1sa", "1sam", "1 sam", "1 sm"),
    "2 Samuel": ("2s", "2sa", "2sam", "2 sam", "2 sm"),
    "1 Reyes": ("1r", "1re", "1rey", "1 re", "1 rey"),
    "2 Reyes": ("2r", "2re", "2rey", "2 re", "2 rey"),
    "1 Crónicas": ("1cr", "1cro", "1 cron", "1 cronicas", "1 cr"),
    "2 Crónicas": ("2cr", "2cro", "2 cron", "2 cronicas", "2 cr"),
    "Esdras": ("esd", "esdr"),
    "Nehemías": ("neh", "ne"),
    "Ester": ("est", "ester"),
    "Job": ("job", "jb"),
    "Salmos": ("sal", "sl", "salmo", "salmos", "ps"),
    "Proverbios": ("pr", "prov", "pro"),
    "Eclesiastés": ("ec", "ecl", "ecles"),
    "Cantares": ("cnt", "cant", "ct"),
    "Isaías": ("is", "isa"),
    "Jeremías": ("jer", "jr"),
    "Lamentaciones": ("lam", "lm"),
    "Ezequiel": ("ez", "eze"),
    "Daniel": ("dn", "dan"),
    "Oseas": ("os", "ose"),
    "Joel": ("jl", "joel"),
    "Amós": ("am", "amos"),
    "Abdías": ("abd", "ab"),
    "Jonás": ("jon", "jonas"),
    "Miqueas": ("miq", "mi"),
    "Nahúm": ("nah", "na"),
    "Habacuc": ("hab", "ha"),
    "Sofonías": ("sof", "so"),
    "Hageo": ("hag", "hg"),
    "Zacarías": ("zac", "zc"),
    "Malaquías": ("mal", "ml"),
    "Mateo": ("mt", "mat"),
    "Marcos": ("mc", "mr", "mar"),
    "Lucas": ("lc", "luc"),
    "Juan": ("jn", "juan"),
    "Hechos": ("hch", "hech", "hechos"),
    "Romanos": ("ro", "rom", "rm"),
    "1 Corintios": ("1co", "1cor", "1 cor", "1 co"),
    "2 Corintios": ("2co", "2cor", "2 cor", "2 co"),
    "Gálatas": ("ga", "gal"),
    "Efesios": ("ef", "efe"),
    "Filipenses": ("fil", "flp"),
    "Colosenses": ("col", "co"),
    "1 Tesalonicenses": ("1tes", "1ts", "1 tes", "1 ts"),
    "2 Tesalonicenses": ("2tes", "2ts", "2 tes", "2 ts"),
    "1 Timoteo": ("1tim", "1ti", "1 tim", "1 ti"),
    "2 Timoteo": ("2tim", "2ti", "2 tim", "2 ti"),
    "Tito": ("tit", "tt"),
    "Filemón": ("flm", "fm"),
    "Hebreos": ("heb", "he"),
    "Santiago": ("stg", "sant", "sg"),
    "1 Pedro": ("1p", "1pe", "1ped", "1 ped", "1 pe"),
    "2 Pedro": ("2p", "2pe", "2ped", "2 ped", "2 pe"),
    "1 Juan": ("1jn", "1ju", "1 jn", "1 juan"),
    "2 Juan": ("2jn", "2ju", "2 jn", "2 juan"),
    "3 Juan": ("3jn", "3ju", "3 jn", "3 juan"),
    "Judas": ("jud", "jd"),
    "Apocalipsis": ("ap", "apo", "apoc", "apocalipsis"),
}


class BibliaView:
    def __init__(self, page, router):
        self.page = page
        self.router = router
        self.responsive = Responsive(page)

        self.libros = BibliaService.libros()
        self.versiculo_random_referencia = ""
        self.versiculo_random_texto = ""
        self.categoria_random = "General"
        self._random_candidatos_cache = {}
        self._random_usados_por_categoria = {}
        self._generar_versiculo_random_inicial()
        self.historial_referencias = self._cargar_historial_referencias()
        self.resaltados = cargar_resaltados()
        ultima_lectura = self._cargar_ultima_lectura()
        self.libro_actual = ultima_lectura.get("libro") or (self.libros[0]["nombre"] if self.libros else None)
        self.capitulo_actual = int(ultima_lectura.get("capitulo") or 1)
        self.verso_seleccionado = None
        self.ultimo_verso_accionado = None
        self.modo_compartir_multiple = False
        self.versos_compartir = set()
        self.color_actual = "Amarillo"
        self.aviso_aceptado = False
        self.modo_vista = ultima_lectura.get("modo") or "Libros"
        self.seccion_movil = "lectura"
        self.objetivo_color = None
        self.objetivo_color_control = None
        self._cache_primer_resaltado = {}
        self.codificador_service = CodificadorService()
        self.resultados_busqueda = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=6,
        )
        self.ultimos_resultados_busqueda = []
        self.ultima_busqueda_texto = ""
        self.panel_lectura = ft.ListView(
            expand=True,
            spacing=6,
            padding=0,
        )
        self.busqueda = ft.TextField(
            hint_text="Buscar",
            prefix_icon=ft.Icons.SEARCH,
            on_submit=self.buscar,
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
        )
        self.referencia_rapida = ft.TextField(
            hint_text="Ir a referencia: Juan 3:16, Salmo 91, Génesis 1",
            prefix_icon=ft.Icons.MENU_BOOK,
            dense=True,
            on_submit=self.ir_a_referencia,
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
        )

        self.random_categoria_texto = ft.Text(
            self.categoria_random.upper(),
            size=11,
            weight=ft.FontWeight.BOLD,
            color=AZUL_ACCENTO,
        )
        self.random_referencia_texto = ft.Text(
            self.versiculo_random_referencia,
            size=15,
            weight=ft.FontWeight.BOLD,
            color=VIOLETA_ACCENTO,
        )
        self.random_versiculo_texto = ft.Text(
            self.versiculo_random_texto,
            size=15,
            color=TEXTO_PRINCIPAL,
            selectable=True,
        )

        self.dropdown_libro = ft.Dropdown(
            label="Libro",
            options=self._opciones_libros(),
            value=self.libro_actual,
            on_select=self.cambiar_libro,
        )
        self.dropdown_capitulo = ft.Dropdown(
            label="Capitulo",
            options=self._opciones_capitulos(),
            value=str(self.capitulo_actual) if self.libro_actual else None,
            on_select=self.cambiar_capitulo,
        )
        self.dropdown_modo = ft.Dropdown(
            label="Vista",
            options=[
                ft.dropdown.Option("Completa"),
                ft.dropdown.Option("Libros"),
                ft.dropdown.Option("Capitulos"),
                ft.dropdown.Option("Versiculos"),
            ],
            value=self.modo_vista,
            on_select=self.cambiar_modo,
        )
        self._normalizar_ultima_lectura()



    def _cargar_ultima_lectura(self):
        try:
            if ULTIMA_LECTURA_ARCHIVO.exists():
                datos = json.loads(ULTIMA_LECTURA_ARCHIVO.read_text(encoding="utf-8"))
                return datos if isinstance(datos, dict) else {}
        except Exception:
            pass
        return {}

    def _guardar_ultima_lectura(self):
        try:
            ULTIMA_LECTURA_ARCHIVO.parent.mkdir(parents=True, exist_ok=True)
            ULTIMA_LECTURA_ARCHIVO.write_text(
                json.dumps(
                    {
                        "libro": self.libro_actual,
                        "capitulo": self.capitulo_actual,
                        "modo": self.modo_vista,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _cargar_historial_referencias(self):
        try:
            if HISTORIAL_REFERENCIAS_ARCHIVO.exists():
                datos = json.loads(HISTORIAL_REFERENCIAS_ARCHIVO.read_text(encoding="utf-8"))
                if isinstance(datos, list):
                    return [item for item in datos if isinstance(item, dict)][:12]
        except Exception:
            pass
        return []

    def _guardar_historial_referencias(self):
        try:
            HISTORIAL_REFERENCIAS_ARCHIVO.parent.mkdir(parents=True, exist_ok=True)
            HISTORIAL_REFERENCIAS_ARCHIVO.write_text(
                json.dumps(self.historial_referencias[:12], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _agregar_historial_referencia(self, libro, capitulo, versiculo=None, texto=""):
        referencia = f"{libro} {capitulo}:{versiculo}" if versiculo else f"{libro} {capitulo}"
        nuevo = {
            "referencia": referencia,
            "libro": libro,
            "capitulo": capitulo,
            "versiculo": versiculo,
            "texto": str(texto or "").strip(),
        }

        historial = [
            item for item in getattr(self, "historial_referencias", [])
            if item.get("referencia") != referencia
        ]
        historial.insert(0, nuevo)
        self.historial_referencias = historial[:12]
        self._guardar_historial_referencias()

    def limpiar_referencia_rapida(self, e=None):
        if hasattr(self, "referencia_rapida"):
            self.referencia_rapida.value = ""
            self.referencia_rapida.update()

    def limpiar_busqueda(self, e=None):
        if hasattr(self, "busqueda"):
            self.busqueda.value = ""
        self.resultados_busqueda.controls.clear()
        self.ultimos_resultados_busqueda = []
        self.ultima_busqueda_texto = ""
        try:
            self.busqueda.update()
            self.resultados_busqueda.update()
        except Exception:
            self.page.update()

    def _normalizar_ultima_lectura(self):
        if not self.libros:
            return

        nombres = [libro.get("nombre") for libro in self.libros]
        if self.libro_actual not in nombres:
            self.libro_actual = nombres[0]

        libro = self._libro_actual()
        cantidad_capitulos = len(libro.get("capitulos", [])) if libro else 1
        if self.capitulo_actual < 1 or self.capitulo_actual > cantidad_capitulos:
            self.capitulo_actual = 1

        if self.modo_vista not in ("Libros", "Capitulos", "Versiculos"):
            self.modo_vista = "Libros"

        if hasattr(self, "dropdown_libro"):
            self.dropdown_libro.value = self.libro_actual
        if hasattr(self, "dropdown_capitulo"):
            self.dropdown_capitulo.options = self._opciones_capitulos()
            self.dropdown_capitulo.value = str(self.capitulo_actual)
        if hasattr(self, "dropdown_modo"):
            self.dropdown_modo.value = self.modo_vista

    def _normalizar_texto_busqueda(self, texto):
        texto = str(texto or "").strip().lower().replace(".", " ")
        texto = unicodedata.normalize("NFD", texto)
        texto = "".join(
            caracter
            for caracter in texto
            if unicodedata.category(caracter) != "Mn"
        )
        texto = re.sub(r"\s+", " ", texto)
        return texto.strip()

    def _normalizar_abreviatura_referencia(self, texto):
        return self._normalizar_texto_busqueda(texto).replace(" ", "")

    def _mapa_abreviaturas_libros(self):
        mapa = {}

        for libro in self.libros or []:
            nombre = libro.get("nombre", "")
            normalizado = self._normalizar_texto_busqueda(nombre)
            compacto = self._normalizar_abreviatura_referencia(nombre)
            mapa[normalizado] = libro
            mapa[compacto] = libro

            for alias in ABREVIATURAS_LIBROS.get(nombre, ()):
                mapa[self._normalizar_texto_busqueda(alias)] = libro
                mapa[self._normalizar_abreviatura_referencia(alias)] = libro

        return mapa

    def _buscar_libro_por_nombre(self, nombre):
        objetivo = self._normalizar_texto_busqueda(nombre)
        if not objetivo:
            return None

        mapa_abreviaturas = self._mapa_abreviaturas_libros()
        libro_por_alias = mapa_abreviaturas.get(objetivo) or mapa_abreviaturas.get(
            self._normalizar_abreviatura_referencia(nombre)
        )
        if libro_por_alias:
            return libro_por_alias

        for libro in self.libros or []:
            nombre_libro = libro.get("nombre", "")
            if self._normalizar_texto_busqueda(nombre_libro) == objetivo:
                return libro

        for libro in self.libros or []:
            nombre_libro = libro.get("nombre", "")
            normalizado = self._normalizar_texto_busqueda(nombre_libro)
            if normalizado.startswith(objetivo) or objetivo.startswith(normalizado):
                return libro

        return None

    def _parsear_referencia(self, referencia):
        texto = str(referencia or "").strip()
        if not texto:
            return None

        coincidencia = re.match(r"^(.+?)\.?\s*(\d+)(?::\s*(\d+))?$", texto)
        if not coincidencia:
            return None

        nombre_libro, capitulo, versiculo = coincidencia.groups()
        libro = self._buscar_libro_por_nombre(nombre_libro)
        if not libro:
            return None

        capitulo = int(capitulo)
        versiculo = int(versiculo) if versiculo else None
        total_capitulos = len(libro.get("capitulos", []))

        if capitulo < 1 or capitulo > total_capitulos:
            return None

        if versiculo is not None:
            total_versiculos = len(libro["capitulos"][capitulo - 1])
            if versiculo < 1 or versiculo > total_versiculos:
                return None

        return libro.get("nombre"), capitulo, versiculo

    def ir_a_referencia(self, e=None):
        texto = self.referencia_rapida.value if hasattr(self, "referencia_rapida") else ""
        referencia = self._parsear_referencia(texto)

        if not referencia:
            self._snack("No pude encontrar esa referencia. Ejemplo válido: Juan 3:16 o Salmo 91.")
            return

        libro, capitulo, versiculo = referencia
        self.libro_actual = libro
        self.capitulo_actual = capitulo
        self.dropdown_libro.value = libro
        self.dropdown_capitulo.options = self._opciones_capitulos()
        self.dropdown_capitulo.value = str(capitulo)
        self.modo_vista = "Versiculos"
        self.dropdown_modo.value = self.modo_vista
        self.verso_seleccionado = verso_id(libro, capitulo, versiculo) if versiculo else None
        self.ultimo_verso_accionado = self.verso_seleccionado
        texto_versiculo = self._texto_versiculo(libro, capitulo, versiculo) if versiculo else ""
        self._agregar_historial_referencia(libro, capitulo, versiculo, texto_versiculo)
        self._guardar_ultima_lectura()
        self.router.refrescar()

    def on_enter(self):
        self.aviso_aceptado = False

    def _on_resize(self, e):
        self.router.refrescar()

    def obtener_vista(self):
        self.page.on_resize = self._on_resize

        if not self.aviso_aceptado:
            return self._aviso_inicial()

        self._render_lectura()

        return ft.Container(
            expand=True,
            padding=self._padding(),
            bgcolor=FONDO_BIBLIA_MODERNO,
            content=ft.Column(
                expand=True,
                spacing=6,
                controls=[
                    self._contenido(),
                ],
            ),
        )

    def _aviso_inicial(self):
        return ft.Container(
            expand=True,
            padding=self._padding(),
            bgcolor=FONDO_BIBLIA_MODERNO,
            alignment=ft.Alignment(0, 0),
            content=self._tarjeta_moderna(
                width=560,
                padding=28,
                content=ft.Column(
                    tight=True,
                    spacing=18,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=68,
                            height=68,
                            border_radius=24,
                            bgcolor=ft.Colors.with_opacity(0.10, VIOLETA_ACCENTO),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(ft.Icons.BOOK, size=38, color=VIOLETA_ACCENTO),
                        ),
                        ft.Text(
                            "Antes de entrar a la Biblia pida permiso y entendimiento a Nuestro Señor Todopoderoso",
                            size=20 if not self.responsive.is_mobile() else 17,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                            color=TEXTO_PRINCIPAL,
                        ),
                        ft.ElevatedButton(
                            "Aceptar",
                            icon=ft.Icons.CHECK,
                            height=44,
                            bgcolor=VIOLETA_ACCENTO,
                            color=ft.Colors.WHITE,
                            on_click=self.aceptar_aviso,
                        ),
                    ],
                ),
            ),
        )

    def aceptar_aviso(self, e=None):
        self.aviso_aceptado = True
        self.router.refrescar()

    def _padding(self):
        if self.responsive.is_mobile():
            return 4
        if self.responsive.is_tablet():
            return 6
        return 6

    def _tarjeta_moderna(self, content, padding=20, expand=False, height=None, width=None):
        return ft.Container(
            expand=expand,
            height=height,
            width=width,
            padding=padding,
            bgcolor=TARJETA_BLANCA,
            border=ft.Border.all(1, BORDE_SUAVE),
            border_radius=18,
            shadow=sombra_suave(0.055, 18, 0, 6),
            content=content,
        )

    def _titulo_seccion(self, texto, icono=None, color=ROJO_ACCENTO):
        controles = []
        if icono:
            controles.append(
                ft.Container(
                    width=34,
                    height=34,
                    border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.10, color),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(icono, size=18, color=color),
                )
            )
        controles.append(
            ft.Text(texto, size=18, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL)
        )
        return ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=controles,
        )

    def _boton_accion_real(self, texto, icono, color, on_click):
        return ft.Container(
            height=42,
            padding=ft.Padding(left=10, top=0, right=12, bottom=0),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.25, color)),
            border_radius=14,
            bgcolor=ft.Colors.with_opacity(0.06, color),
            on_click=on_click,
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icono, size=18, color=color),
                    ft.Text(texto, size=13, color=TEXTO_PRINCIPAL),
                ],
            ),
        )

    def _barra_superior(self):
        return self._tarjeta_moderna(
            padding=18,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=14,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=56,
                                height=56,
                                border_radius=18,
                                bgcolor=ft.Colors.with_opacity(0.10, VIOLETA_ACCENTO),
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(ft.Icons.MENU_BOOK, color=VIOLETA_ACCENTO, size=30),
                            ),
                            ft.Column(
                                tight=True,
                                spacing=2,
                                controls=[
                                    ft.Text(
                                        "Biblia",
                                        size=26 if self.responsive.is_mobile() else 34,
                                        weight=ft.FontWeight.BOLD,
                                        color=TEXTO_PRINCIPAL,
                                    ),
                                    ft.Text(
                                        "Lectura, búsqueda, resaltado y codificación bíblica.",
                                        size=13 if self.responsive.is_mobile() else 15,
                                        color=TEXTO_SECUNDARIO,
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Container(
                        padding=ft.Padding(left=12, top=8, right=12, bottom=8),
                        border_radius=14,
                        bgcolor=GRIS_SUAVE,
                        border=ft.Border.all(1, BORDE_SUAVE),
                        on_click=lambda e: self.recargar(),
                        content=ft.Row(
                            tight=True,
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.REFRESH, size=18, color=TEXTO_SECUNDARIO),
                                ft.Text("Recargar", size=13, color=TEXTO_SECUNDARIO, weight=ft.FontWeight.BOLD),
                            ],
                        ),
                    ),
                ],
            ),
        )

    def _contenido(self):
        lectura = self._panel_lectura()
        busqueda = self._panel_busqueda()

        if not self.responsive.is_desktop():
            return ft.Column(
                expand=True,
                spacing=8,
                controls=[
                    ft.Row(
                        wrap=True,
                        spacing=6,
                        run_spacing=6,
                        controls=[
                            ft.ElevatedButton(
                                "Lectura",
                                bgcolor=(PERLA_VIOLETA if self.seccion_movil == "lectura" else None),
                                on_click=lambda e: self.cambiar_seccion_movil("lectura"),
                            ),
                            ft.ElevatedButton(
                                "Buscar",
                                bgcolor=(PERLA_VIOLETA if self.seccion_movil == "buscar" else None),
                                on_click=lambda e: self.cambiar_seccion_movil("buscar"),
                            ),
                            ft.ElevatedButton(
                                "Azar",
                                bgcolor=(PERLA_VIOLETA if self.seccion_movil == "azar" else None),
                                on_click=lambda e: self.cambiar_seccion_movil("azar"),
                            ),
                        ],
                    ),
                    ft.Container(
                        expand=True,
                        content=(
                            lectura
                            if self.seccion_movil == "lectura"
                            else self._panel_versiculo_random()
                            if self.seccion_movil == "azar"
                            else busqueda
                        ),
                    ),
                ],
            )

        return ft.Row(
            expand=True,
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Container(
                    expand=2,
                    content=lectura,
                ),
                ft.Container(
                    width=390,
                    content=ft.Column(
                        expand=True,
                        spacing=14,
                        scroll=ft.ScrollMode.AUTO,
                        controls=[
                            self._panel_ir_a_referencia(),
                            busqueda,
                            self._panel_versiculo_random(),
                        ],
                    ),
                ),
            ],
        )

    def _generar_versiculo_random_inicial(self):
        referencia, texto = self._obtener_versiculo_random()
        self.versiculo_random_referencia = referencia
        self.versiculo_random_texto = texto

    def _libro_pertenece_categoria_random(self, nombre_libro, categoria):
        categoria = categoria or "General"

        if categoria == "General":
            return True

        nombre_normalizado = self._normalizar_texto_busqueda(nombre_libro)
        permitidos = LIBROS_RANDOM_POR_CATEGORIA.get(categoria, set())
        return nombre_normalizado in permitidos

    def _candidatos_random_categoria(self, categoria):
        categoria = categoria or "General"
        cache = getattr(self, "_random_candidatos_cache", None)

        if cache is None:
            self._random_candidatos_cache = {}
            cache = self._random_candidatos_cache

        if categoria in cache:
            return cache[categoria]

        candidatos = []

        for libro in self.libros or []:
            nombre_libro = libro.get("nombre", "")

            if not self._libro_pertenece_categoria_random(nombre_libro, categoria):
                continue

            for indice_capitulo, capitulo in enumerate(libro.get("capitulos", []), start=1):
                for indice_versiculo, texto in enumerate(capitulo, start=1):
                    texto_limpio = str(texto or "").strip()
                    if texto_limpio:
                        referencia = f"{nombre_libro} {indice_capitulo}:{indice_versiculo}"
                        candidatos.append((referencia, texto_limpio))

        cache[categoria] = candidatos
        return candidatos

    def _obtener_versiculo_random(self):
        categoria = getattr(self, "categoria_random", "General") or "General"
        candidatos = self._candidatos_random_categoria(categoria)

        if not candidatos and categoria != "General":
            candidatos = self._candidatos_random_categoria("General")

        if not candidatos:
            return "Sin versiculo", "No hay texto biblico cargado."

        usados_por_categoria = getattr(self, "_random_usados_por_categoria", None)
        if usados_por_categoria is None:
            self._random_usados_por_categoria = {}
            usados_por_categoria = self._random_usados_por_categoria

        usados = usados_por_categoria.setdefault(categoria, set())
        disponibles = [item for item in candidatos if item[0] not in usados]

        if not disponibles:
            usados.clear()
            disponibles = candidatos[:]

        elegido = random.choice(disponibles)
        usados.add(elegido[0])
        return elegido

    def refrescar_versiculo_random(self, e=None):
        referencia, texto = self._obtener_versiculo_random()
        self.versiculo_random_referencia = referencia
        self.versiculo_random_texto = texto
        self._actualizar_controles_random()

    def cambiar_categoria_random(self, categoria):
        self.categoria_random = categoria
        self.refrescar_versiculo_random()

    def _actualizar_controles_random(self):
        if not hasattr(self, "random_referencia_texto"):
            self.page.update()
            return

        self.random_categoria_texto.value = self.categoria_random.upper()
        self.random_referencia_texto.value = self.versiculo_random_referencia
        self.random_versiculo_texto.value = self.versiculo_random_texto

        for control in (
            self.random_categoria_texto,
            self.random_referencia_texto,
            self.random_versiculo_texto,
        ):
            try:
                control.update()
            except Exception:
                pass

        try:
            self.page.update()
        except Exception:
            pass

    def _chip_categoria_random(self, categoria):
        seleccionado = self.categoria_random == categoria

        return ft.Container(
            padding=ft.Padding(left=12, top=7, right=12, bottom=7),
            border_radius=999,
            bgcolor=(
                ft.Colors.with_opacity(0.14, VIOLETA_ACCENTO)
                if seleccionado
                else ft.Colors.WHITE
            ),
            border=ft.Border.all(
                1.2,
                VIOLETA_ACCENTO if seleccionado else BORDE_SUAVE,
            ),
            content=ft.Text(
                categoria,
                size=12,
                weight=ft.FontWeight.BOLD if seleccionado else None,
                color=VIOLETA_ACCENTO if seleccionado else TEXTO_SECUNDARIO,
            ),
            on_click=lambda e, c=categoria: self.cambiar_categoria_random(c),
        )

    def copiar_versiculo_random(self, e=None):
        referencia = str(getattr(self, "versiculo_random_referencia", "") or "").strip()
        texto = str(getattr(self, "versiculo_random_texto", "") or "").strip()

        if not referencia or not texto:
            self._snack("No hay versiculo random para copiar.")
            return

        copiar_al_portapapeles(self.page, f"{referencia} {texto}")
        self._snack("Versiculo random copiado.")

    def ir_a_versiculo_random(self, e=None):
        referencia = str(getattr(self, "versiculo_random_referencia", "") or "").strip()

        if not referencia:
            self._snack("No hay versiculo random para abrir.")
            return

        if hasattr(self, "referencia_rapida"):
            self.referencia_rapida.value = referencia

        self.ir_a_referencia()

    def _panel_versiculo_random(self):
        if not self.versiculo_random_texto:
            self._generar_versiculo_random_inicial()

        return self._tarjeta_moderna(
            padding=18,
            content=ft.Column(
                tight=True,
                spacing=14,
                controls=[
                    self._titulo_seccion("Versiculo random", ft.Icons.AUTO_AWESOME, VIOLETA_ACCENTO),
                    ft.Row(
                        wrap=True,
                        spacing=7,
                        run_spacing=7,
                        controls=[
                            self._chip_categoria_random(categoria)
                            for categoria in CATEGORIAS_RANDOM_BIBLIA
                        ],
                    ),
                    ft.Container(
                        padding=16,
                        border_radius=18,
                        bgcolor=ft.Colors.with_opacity(0.06, AZUL_ACCENTO),
                        border=ft.Border.all(1, ft.Colors.with_opacity(0.18, AZUL_ACCENTO)),
                        content=ft.Column(
                            tight=True,
                            spacing=8,
                            controls=[
                                self.random_categoria_texto,
                                self.random_referencia_texto,
                                self.random_versiculo_texto,
                            ],
                        ),
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.END,
                        wrap=True,
                        spacing=8,
                        controls=[
                            ft.TextButton(
                                "Copiar",
                                icon=ft.Icons.CONTENT_COPY,
                                on_click=self.copiar_versiculo_random,
                            ),
                            ft.TextButton(
                                "Ver en lectura",
                                icon=ft.Icons.OPEN_IN_NEW,
                                on_click=self.ir_a_versiculo_random,
                            ),
                            ft.ElevatedButton(
                                "Nuevo versiculo",
                                icon=ft.Icons.REFRESH,
                                on_click=self.refrescar_versiculo_random,
                            ),
                        ],
                    ),
                ],
            ),
        )


    def _desarmar_clave_verso(self, clave):
        partes = str(clave or "").split("|")
        if len(partes) < 3:
            return None, None, None

        libro = partes[0]
        try:
            capitulo = int(partes[1])
            versiculo = int(partes[2])
        except Exception:
            return libro, None, None

        return libro, capitulo, versiculo

    def _referencia_desde_clave_verso(self, clave):
        libro, capitulo, versiculo = self._desarmar_clave_verso(clave)
        if not libro or not capitulo or not versiculo:
            return "Seleccione un versículo"
        return f"{libro} {capitulo}:{versiculo}"

    def _texto_desde_clave_verso(self, clave):
        libro, capitulo, versiculo = self._desarmar_clave_verso(clave)
        if not libro or not capitulo or not versiculo:
            return ""
        try:
            return self._texto_versiculo(libro, capitulo, versiculo)
        except Exception:
            return ""

    def _panel_lectura(self):
        if not self.libros:
            return self._tarjeta_moderna(
                expand=True,
                padding=18,
                content=ft.Column(
                    controls=[
                        ft.Text("No hay texto biblico cargado.", weight=ft.FontWeight.BOLD),
                        ft.Text(f"Coloque el archivo en {BIBLIA_ARCHIVO} y pulse recargar."),
                    ],
                ),
            )

        return self._tarjeta_moderna(
            expand=True,
            padding=18 if self.responsive.is_mobile() else 24,
            content=ft.Column(
                expand=True,
                spacing=14,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self._titulo_seccion("Lectura", ft.Icons.BOOK, ROJO_ACCENTO),
                        ],
                    ),
                    self._navegacion_lectura(),
                    self._barra_resaltado(),
                    ft.Divider(height=1, color=BORDE_SUAVE),
                    ft.Container(
                        expand=True,
                        padding=ft.Padding(left=4, top=4, right=4, bottom=4),
                        on_click=self.deseleccionar_actual,
                        content=self.panel_lectura,
                    ),
                ],
            ),
        )

    def _navegacion_lectura(self):
        puede_volver = self.modo_vista in ("Capitulos", "Versiculos")

        if self.modo_vista == "Versiculos":
            titulo = f"{self.libro_actual} {self.capitulo_actual}"
        elif self.modo_vista == "Capitulos":
            titulo = self.libro_actual or "Capitulos"
        else:
            titulo = "Libros"

        return ft.Container(
            padding=ft.Padding(left=8, top=6, right=8, bottom=6),
            bgcolor=GRIS_SUAVE,
            border=ft.Border.all(1, BORDE_SUAVE),
            border_radius=16,
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        tooltip="Volver",
                        visible=puede_volver,
                        icon_color=TEXTO_SECUNDARIO,
                        on_click=lambda e: self.volver_lectura(),
                    ),
                    ft.Container(
                        expand=True,
                        content=ft.Text(
                            titulo,
                            size=16 if self.responsive.is_mobile() else 20,
                            weight=ft.FontWeight.BOLD,
                            color=TEXTO_PRINCIPAL,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ),
                ],
            ),
        )

    def _panel_ir_a_referencia(self):
        return self._tarjeta_moderna(
            padding=18,
            content=ft.Column(
                tight=True,
                spacing=12,
                controls=[
                    self._titulo_seccion("Ir a referencia", ft.Icons.MENU_BOOK, NARANJA_ACCENTO),
                    self.referencia_rapida,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.END,
                        spacing=8,
                        controls=[
                            ft.TextButton(
                                "Limpiar",
                                icon=ft.Icons.CLOSE,
                                on_click=self.limpiar_referencia_rapida,
                            ),
                            ft.ElevatedButton(
                                "Ir",
                                icon=ft.Icons.ARROW_FORWARD,
                                on_click=self.ir_a_referencia,
                            ),
                        ],
                    ),
                ],
            ),
        )

    def _panel_busqueda(self):
        return self._tarjeta_moderna(
            expand=True,
            padding=18,
            content=ft.Column(
                expand=True,
                spacing=14,
                controls=[
                    self._titulo_seccion("Buscar", ft.Icons.SEARCH, AZUL_ACCENTO),
                    self.busqueda,
                    ft.Row(
                        wrap=True,
                        spacing=8,
                        run_spacing=8,
                        controls=[
                            ft.ElevatedButton(
                                "Buscar",
                                icon=ft.Icons.SEARCH,
                                on_click=self.buscar,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CONTENT_COPY,
                                tooltip="Copiar seleccion",
                                icon_color=TEXTO_SECUNDARIO,
                                on_click=lambda e: self.copiar_seleccion(),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.SAVE_ALT,
                                tooltip="Guardar resultados de busqueda",
                                icon_color=NARANJA_ACCENTO,
                                on_click=self.guardar_busqueda,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                tooltip="Limpiar busqueda",
                                icon_color=TEXTO_SECUNDARIO,
                                on_click=self.limpiar_busqueda,
                            ),
                        ],
                    ),
                    ft.Container(
                        height=260 if self.responsive.is_mobile() else 360,
                        border=ft.Border.all(1, BORDE_SUAVE),
                        border_radius=14,
                        padding=8,
                        bgcolor=ft.Colors.with_opacity(0.42, ft.Colors.WHITE),
                        content=self.resultados_busqueda,
                    ),
                ],
            ),
        )

    def dialog_palabras_cordero(self, e=None):
        resultados = self._versiculos_palabras_cordero()
        libros_disponibles = []

        for resultado in resultados:
            libro = resultado.get("libro", "")
            if libro and libro not in libros_disponibles:
                libros_disponibles.append(libro)

        selector_libro = ft.Dropdown(
            label="Filtrar por libro",
            value="Todos",
            options=[ft.dropdown.Option("Todos")] + [
                ft.dropdown.Option(libro)
                for libro in libros_disponibles
            ],
        )
        alto_pagina = getattr(self.page, "height", None)
        if alto_pagina is None and hasattr(self.page, "window"):
            alto_pagina = getattr(self.page.window, "height", None)
        alto_dialogo = max(430, min(620, int((alto_pagina or 760) - 150)))
        lista = ft.ListView(
            expand=True,
            spacing=8,
            padding=ft.Padding(left=0, top=0, right=8, bottom=0),
        )
        contador = ft.Text(size=12, color=TEXTO_SECUNDARIO)

        def resultados_visibles():
            libro = selector_libro.value or "Todos"

            if libro == "Todos":
                return resultados

            return [
                resultado
                for resultado in resultados
                if resultado.get("libro") == libro
            ]

        def cerrar(ev=None):
            dialog.open = False
            self.page.update()
            self.router.refrescar()

        def actualizar_contador():
            total = len(self.versos_compartir)
            visibles = len(resultados_visibles())
            contador.value = (
                f"{visibles} visibles | {total} seleccionado"
                if total == 1
                else f"{visibles} visibles | {total} seleccionados"
            )
            try:
                contador.update()
            except (RuntimeError, AssertionError):
                pass

        def alternar(vid):
            self.toggle_verso_compartir(vid, refrescar=False)
            renderizar_lista()
            actualizar_contador()

        def seleccionar_todos(ev=None):
            for resultado in resultados_visibles():
                self.versos_compartir.add(resultado["id"])
            self.modo_compartir_multiple = True
            renderizar_lista()
            actualizar_contador()

        def deseleccionar_todos(ev=None):
            self.versos_compartir.clear()
            renderizar_lista()
            actualizar_contador()

        def abrir(vid):
            cerrar()
            self.ir_a_verso_clave(vid)

        def compartir(ev=None):
            if not self.versos_compartir:
                self._snack("Seleccione al menos un versiculo.")
                return
            cerrar()
            self.compartir_seleccion()

        def renderizar_lista():
            lista.controls.clear()
            visibles = resultados_visibles()

            if not visibles:
                lista.controls.append(
                    ft.Text(
                        "No se detectaron palabras en rojo con la regla actual.",
                        color=TEXTO_SECUNDARIO,
                    )
                )
            else:
                for resultado in visibles:
                    vid = resultado["id"]
                    seleccionado = vid in self.versos_compartir
                    lista.controls.append(
                        ft.Container(
                            padding=10,
                            border_radius=14,
            bgcolor="#FFF7D6" if seleccionado else ft.Colors.WHITE,
                            border=ft.Border.all(
                                2 if seleccionado else 1,
                                NARANJA_ACCENTO if seleccionado else BORDE_SUAVE,
                            ),
                            content=ft.Row(
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.START,
                                controls=[
                                    ft.Checkbox(
                                        value=seleccionado,
                                        tooltip=(
                                            "Quitar de la seleccion"
                                            if seleccionado
                                            else "Agregar a la seleccion"
                                        ),
                                        on_change=lambda ev, v=vid: alternar(v),
                                    ),
                                    ft.Container(
                                        expand=True,
                                        on_click=lambda ev, v=vid: alternar(v),
                                        content=ft.Column(
                                            tight=True,
                                            spacing=4,
                                            controls=[
                                                ft.Text(
                                                    resultado["referencia"],
                                                    size=13,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=COLOR_PALABRAS_CORDERO,
                                                ),
                                                self._texto_versiculo_visual(
                                                    resultado["libro"],
                                                    resultado["texto"],
                                                    TEXTO_PRINCIPAL,
                                                    expand=False,
                                                ),
                                            ],
                                        ),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.OPEN_IN_NEW,
                                        tooltip="Abrir versiculo",
                                        icon_color=TEXTO_SECUNDARIO,
                                        on_click=lambda ev, v=vid: abrir(v),
                                    ),
                                ],
                            ),
                        )
                    )

            try:
                lista.update()
            except (RuntimeError, AssertionError):
                pass

        def cambiar_filtro(ev=None):
            renderizar_lista()
            actualizar_contador()

        selector_libro.on_select = cambiar_filtro
        renderizar_lista()
        actualizar_contador()

        acciones_inferiores = ft.Container(
            padding=ft.Padding(left=0, top=10, right=0, bottom=0),
            border=ft.Border(
                top=ft.BorderSide(1, BORDE_SUAVE),
            ),
            bgcolor=ft.Colors.WHITE,
            content=ft.Row(
                wrap=True,
                spacing=8,
                run_spacing=8,
                alignment=ft.MainAxisAlignment.END,
                controls=[
                    ft.TextButton("Seleccionar todo", on_click=seleccionar_todos),
                    ft.TextButton("Deseleccionar todo", on_click=deseleccionar_todos),
                    ft.ElevatedButton(
                        "Compartir seleccion",
                        icon=ft.Icons.SHARE,
                        on_click=compartir,
                    ),
                    ft.TextButton("Cerrar", on_click=cerrar),
                ],
            ),
        )

        dialog = ft.AlertDialog(
            title=ft.Text("Palabras del Cordero"),
            content=ft.Container(
                width=760,
                height=alto_dialogo,
                content=ft.Column(
                    expand=True,
                    spacing=12,
                    controls=[
                        ft.Text(
                            "Versiculos donde la app detecta las palabras en rojo.",
                            size=12,
                            color=TEXTO_SECUNDARIO,
                        ),
                        selector_libro,
                        contador,
                        ft.Container(
                            expand=True,
                            content=lista,
                        ),
                        acciones_inferiores,
                    ],
                ),
            ),
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _barra_resaltado(self):
        tamanio = 26 if self.responsive.is_mobile() else 28

        colores = [
            ft.Container(
                width=tamanio,
                height=tamanio,
                bgcolor=color,
                border=ft.Border.all(
                    3 if nombre == self.color_actual else 1,
                    BORDER_MARRON if self._es_blanco_borde(nombre) else ft.Colors.with_opacity(0.38, ft.Colors.BLACK),
                ),
                border_radius=tamanio / 2,
                tooltip=nombre,
                shadow=(
                    ft.BoxShadow(
                        blur_radius=12,
                        spread_radius=0,
                        color=ft.Colors.with_opacity(0.22, color),
                        offset=ft.Offset(0, 4),
                    )
                    if nombre == self.color_actual
                    else None
                ),
                on_click=lambda e, n=nombre: self.seleccionar_color(n),
            )
            for nombre, color in COLORES_RESALTADO.items()
        ]

        acciones = [
            ft.IconButton(icon=ft.Icons.FORMAT_COLOR_RESET, tooltip="Quitar color seleccionado", icon_color=TEXTO_SECUNDARIO, on_click=lambda e: self.quitar_color_objetivo()),
            ft.IconButton(icon=ft.Icons.SAVE_ALT, tooltip="Guardar fragmento", icon_color=NARANJA_ACCENTO, on_click=lambda e: self.guardar_fragmento()),
            ft.IconButton(icon=ft.Icons.CONTENT_COPY, tooltip="Copiar capitulo", icon_color=AZUL_ACCENTO, on_click=lambda e: self.copiar_capitulo()),
            ft.IconButton(icon=ft.Icons.MENU_BOOK, tooltip="Diccionario hebreo", icon_color=VIOLETA_ACCENTO, on_click=lambda e: self.dialog_diccionario_hebreo()),
            ft.IconButton(icon=ft.Icons.RECORD_VOICE_OVER, tooltip="Ver palabras del Cordero", icon_color=COLOR_PALABRAS_CORDERO, on_click=lambda e: self.dialog_palabras_cordero()),
            ft.IconButton(icon=ft.Icons.SELECT_ALL, tooltip="Seleccion multiple de versiculos", icon_color=NARANJA_ACCENTO if self.modo_compartir_multiple else TEXTO_SECUNDARIO, on_click=lambda e: self.toggle_modo_compartir_multiple()),
            ft.IconButton(icon=ft.Icons.CLEAR_ALL, tooltip="Limpiar seleccion multiple", icon_color=TEXTO_SECUNDARIO, on_click=lambda e: self.limpiar_seleccion_multiple()),
            ft.IconButton(icon=ft.Icons.SHARE, tooltip="Compartir seleccion", icon_color=VIOLETA_ACCENTO, on_click=lambda e: self.compartir_seleccion()),
            ft.IconButton(icon=ft.Icons.FILTER_ALT, tooltip="Ver marcados por color", icon_color=VERDE_ACCENTO, on_click=lambda e: self.dialog_versiculos_por_color()),
        ]

        return ft.Container(
            padding=ft.Padding(left=12, top=10, right=12, bottom=10),
            bgcolor=ft.Colors.with_opacity(0.45, ft.Colors.WHITE),
            border=ft.Border.all(1, BORDE_SUAVE),
            border_radius=16,
            content=ft.Row(
                wrap=True,
                spacing=8,
                run_spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("Resaltado", size=13, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                    ft.Text(
                        f"{len(self.versos_compartir)} seleccionados",
                        size=12,
                        color=NARANJA_ACCENTO if self.versos_compartir else TEXTO_SECUNDARIO,
                        visible=self.modo_compartir_multiple or bool(self.versos_compartir),
                    ),
                ] + colores + acciones,
            ),
        )

    def _opciones_libros(self):
        return [
            ft.dropdown.Option(libro["nombre"])
            for libro in self.libros
        ]

    def _opciones_capitulos(self):
        libro = self._libro_actual()

        if not libro:
            return []

        return [
            ft.dropdown.Option(str(indice))
            for indice in range(1, len(libro["capitulos"]) + 1)
        ]

    def _normalizar_color(self, color):
        if isinstance(color, dict):
            return self._normalizar_color(
                next(
                    (
                        item
                        for item in color.get("digitos", [])
                        if item
                    ),
                    None,
                )
            )

        return ALIAS_COLORES_RESALTADO.get(color, color)

    def _hex_color(self, color, default=None):
        color = self._normalizar_color(color)
        return COLORES_RESALTADO.get(color, default)

    def _texto_color(self, color, default=ft.Colors.BLACK):
        color = self._normalizar_color(color)
        return COLORES_TEXTO_RESALTADO.get(color, default)

    def _es_blanco_borde(self, color):
        return self._normalizar_color(color) == COLOR_BLANCO_BORDE

    def _borde_por_color(self, color, default=ft.Colors.GREY_300, ancho=1):
        color = self._normalizar_color(color)

        if color == COLOR_BLANCO_BORDE:
            return ft.Border.all(max(ancho, 2), BORDER_MARRON)

        if color:
            return ft.Border.all(ancho, default)

        return ft.Border.all(ancho, default)

    def _color_principal(self, valor):
        if isinstance(valor, dict):
            return self._normalizar_color(
                next(
                    (
                        color
                        for color in valor.get("digitos", [])
                        if color
                    ),
                    None,
                )
            )

        return self._normalizar_color(valor)

    def _reducir_numero_color(self, numero):
        numero = abs(int(numero))

        while numero > 9:
            numero = sum(int(digito) for digito in str(numero))

        return DIGITO_A_COLOR.get(numero)

    def _objetivo_base(self):
        if not isinstance(self.objetivo_color, str):
            return None

        for separador in ("|DIG|",):
            if separador in self.objetivo_color:
                return self.objetivo_color.split(separador, 1)[0]

        return self.objetivo_color

    def _esta_marcado_para_color(self, clave):
        return self._objetivo_base() == clave

    def _icono_marcado(self, visible=True, size=18):
        return ft.Icon(
            ft.Icons.BOOKMARK_ADDED,
            size=size,
            color=VIOLETA_IOS,
            visible=visible,
        )

    def _parse_objetivo_color(self):
        clave = self.objetivo_color

        if not isinstance(clave, str):
            return None, "completo", None

        if "|DIG|" in clave:
            base, indice = clave.rsplit("|DIG|", 1)
            try:
                return base, "digito", int(indice)
            except ValueError:
                return base, "digito", 0

        return clave, "completo", None

    def _numero_desde_clave_identificador(self, clave):
        partes = clave.split("|")

        if not partes:
            return ""

        return partes[-1]

    def _dato_identificador(self, clave):
        valor = self.resaltados.get(clave)

        if isinstance(valor, dict):
            return valor

        numero = self._numero_desde_clave_identificador(clave)
        return {
            "tipo": "digitos",
            "digitos": [None for _ in str(numero)],
        }

    def _aplicar_color_identificador(self, clave, parte, indice, color):
        color = self._normalizar_color(color)

        if parte == "completo":
            self.resaltados[clave] = color
            return

        dato = self._dato_identificador(clave)
        numero = self._numero_desde_clave_identificador(clave)
        digitos = list(dato.get("digitos", []))

        while len(digitos) < len(str(numero)):
            digitos.append(None)

        if parte == "digito":
            if 0 <= indice < len(digitos):
                digitos[indice] = color
        dato["digitos"] = digitos
        self.resaltados[clave] = dato

    def _aplicar_tres_colores_identificador(self, clave):
        numero = self._numero_desde_clave_identificador(clave)
        digitos = [
            DIGITO_A_COLOR.get(int(digito))
            for digito in str(numero)
            if digito.isdigit()
        ]
        self.resaltados[clave] = {
            "tipo": "digitos",
            "digitos": digitos,
        }
        guardar_resaltados(self.resaltados)
        self.objetivo_color = None
        self.objetivo_color_control = None
        self.router.refrescar()

    def _control_identificador(
        self,
        numero,
        resaltado,
        seleccionado=False,
        ancho=None,
        alto=34,
        sufijo="",
    ):
        texto_numero = str(numero)

        if isinstance(resaltado, dict):
            digitos = list(resaltado.get("digitos", []))
            borde = (
                ft.Border.all(2, VIOLETA_IOS)
                if seleccionado
                else ft.Border.all(1, ft.Colors.GREY_400)
            )
            controles = []

            if seleccionado:
                controles.append(self._icono_marcado(size=15))

            for indice, digito in enumerate(texto_numero):
                color = self._normalizar_color(
                    digitos[indice] if indice < len(digitos) else None
                )
                controles.append(
                    ft.Container(
                        expand=1,
                        height=alto,
                        alignment=ft.Alignment(0, 0),
                        bgcolor=self._hex_color(color, ft.Colors.TRANSPARENT),
                        border=(
                            ft.Border.all(1, BORDER_MARRON)
                            if self._es_blanco_borde(color)
                            else None
                        ),
                        content=ft.Text(
                            digito,
                            color=self._texto_color(color),
                            weight=ft.FontWeight.BOLD,
                        ),
                    )
                )

            if sufijo:
                controles.append(
                    ft.Container(
                        width=7,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text(
                            sufijo,
                            color=ft.Colors.BLACK,
                            weight=ft.FontWeight.BOLD,
                        ),
                    )
                )

            return ft.Container(
                width=ancho or max(34, len(texto_numero) * 18 + 14),
                height=alto,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                border=borde,
                border_radius=6,
                bgcolor=ft.Colors.WHITE,
                content=ft.Row(
                    spacing=0,
                    controls=controles,
                ),
            )

        color = self._normalizar_color(resaltado)
        return ft.Container(
            width=ancho,
            height=alto,
            alignment=ft.Alignment(0, 0),
            padding=ft.Padding(left=7, top=2, right=7, bottom=2),
            border_radius=6,
            bgcolor=(
                self._hex_color(color)
                if color
                else PERLA_VIOLETA
                if seleccionado
                else ft.Colors.TRANSPARENT
            ),
            border=(
                ft.Border.all(2, VIOLETA_IOS)
                if seleccionado
                else self._borde_por_color(color, default=ft.Colors.GREY_400)
                if color
                else None
            ),
            content=ft.Row(
                tight=True,
                spacing=3,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self._icono_marcado(visible=seleccionado, size=15),
                    ft.Text(
                        f"{texto_numero}{sufijo}",
                        color=self._texto_color(color),
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
            ),
        )

    def _libro_actual(self):
        for libro in self.libros:
            if libro["nombre"] == self.libro_actual:
                return libro

        return None

    def _capitulo_actual(self):
        libro = self._libro_actual()

        if not libro:
            return []

        indice = self.capitulo_actual - 1

        if indice < 0 or indice >= len(libro["capitulos"]):
            return []

        return libro["capitulos"][indice]

    def _render_lectura(self):
        self._cache_primer_resaltado = {}
        self.panel_lectura.controls.clear()

        if not self.libros:
            return

        if not self.modo_vista or self.modo_vista == "Completa":
            self.modo_vista = "Libros"
            self._render_libros()
            return

        if self.modo_vista == "Libros":
            self._render_libros()
            return

        if self.modo_vista == "Capitulos":
            self._render_capitulos()
            return

        self._render_versiculos()

    def _render_biblia_completa(self):
        for libro in self.libros:
            self.panel_lectura.controls.append(
                ft.Container(
                    padding=10,
                    bgcolor=ft.Colors.WHITE,
                    border=ft.Border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Text(
                                libro["nombre"],
                                size=18,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Row(
                                wrap=True,
                                spacing=6,
                                run_spacing=6,
                                controls=[
                                    self._boton_capitulo(
                                        libro["nombre"],
                                        indice,
                                        lambda e, l=libro["nombre"], i=indice:
                                            self.ir_a_capitulo_de_libro(l, i),
                                    )
                                    for indice in range(1, len(libro["capitulos"]) + 1)
                                ],
                            ),
                        ],
                    ),
                )
            )

    def _render_libros(self):
        self.panel_lectura.controls.append(
            ft.Text(
                "Seleccione un libro",
                weight=ft.FontWeight.BOLD,
            )
        )

        self.panel_lectura.controls.append(
            ft.Row(
                wrap=True,
                spacing=8,
                run_spacing=8,
                controls=[
                    self._tarjeta_libro(libro)
                    for libro in self.libros
                ],
            )
        )

    def _tarjeta_libro(self, libro):
        nombre = libro["nombre"]
        clave = self._clave_libro(nombre)
        color = self._color_libro_resaltado(nombre)
        fondo = self._hex_color(color, ft.Colors.WHITE)
        texto_color = self._texto_color(color)
        seleccionado = self._esta_marcado_para_color(clave)

        borde = (
            ft.Border.all(2, VIOLETA_IOS)
            if seleccionado
            else self._borde_por_color(
                color,
                default=ft.Colors.GREY_300,
                ancho=1,
            )
        )

        def doble_click_libro(e, libro_nombre=nombre):
            self.codificar_libro_biblia(libro_nombre)

        contenido_libro = ft.GestureDetector(
            on_tap=lambda e, l=nombre: self.ir_a_libro(l),
            on_double_tap=doble_click_libro,
            on_long_press=lambda e, l=nombre: self.seleccionar_libro_para_color(l),
            content=ft.Container(
                padding=ft.Padding(left=12, top=9, right=8, bottom=9),
                content=ft.Row(
                    tight=True,
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self._icono_marcado(visible=seleccionado),
                        ft.Text(
                            f"{nombre} ({len(libro['capitulos'])})",
                            color=texto_color,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                ),
            ),
        )

        controles = [contenido_libro]

        if color:
            controles.append(
                ft.IconButton(
                    icon=ft.Icons.FORMAT_COLOR_RESET,
                    icon_size=16,
                    tooltip="Quitar color del libro",
                    icon_color=texto_color,
                    on_click=lambda e, l=nombre: self.quitar_color_libro(l),
                )
            )

        return ft.Container(
            bgcolor=fondo,
            border=borde,
            border_radius=8,
            content=ft.Row(
                tight=True,
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=controles,
            ),
        )

    def _render_capitulos(self):
        libro = self._libro_actual()

        if not libro:
            return

        self.panel_lectura.controls.append(
            ft.Text(
                f"{libro['nombre']}: capitulos",
                weight=ft.FontWeight.BOLD,
            )
        )

        self.panel_lectura.controls.append(
            ft.Row(
                wrap=True,
                spacing=8,
                run_spacing=8,
                controls=[
                    self._boton_capitulo(
                        libro["nombre"],
                        indice,
                        lambda e, i=indice: self.ir_a_capitulo(i),
                    )
                    for indice in range(1, len(libro["capitulos"]) + 1)
                ],
            )
        )

    def _boton_capitulo(self, libro, capitulo, on_tap):
        color = self._color_capitulo_directo(libro, capitulo)
        clave = self._clave_capitulo(libro, capitulo)
        color_resuelto = color or self._primer_color_resaltado(f"{libro}|{capitulo}|")
        seleccionado = self._objetivo_base() == clave

        contenedor = self._control_identificador(
            capitulo,
            color_resuelto,
            seleccionado=seleccionado,
            ancho=70 if seleccionado else 48 if capitulo >= 10 else 42,
            alto=36,
        )

        return ft.GestureDetector(
            on_tap=on_tap,
            on_double_tap=lambda e, l=libro, c=capitulo:
                self.codificar_capitulo_biblia(l, c),
            on_long_press=lambda e, l=libro, c=capitulo:
                self.elegir_modo_color_identificador(self._clave_capitulo(l, c)),
            content=contenedor,
        )

    def _texto_versiculo_visual(self, libro, texto, color_base, expand=True):
        texto = str(texto or "")
        inicio_rojo = self._inicio_palabras_cordero(libro, texto)
        spans = []
        tiene_palabras_diccionario = False

        for fragmento, entrada, inicio, _fin in fragmentos_con_diccionario(texto):
            es_palabra_cordero = inicio_rojo is not None and inicio >= inicio_rojo
            color_fragmento = COLOR_PALABRAS_CORDERO if es_palabra_cordero else color_base

            if entrada:
                tiene_palabras_diccionario = True
                spans.append(
                    ft.TextSpan(
                        fragmento,
                        style=ft.TextStyle(
                            color=color_fragmento,
                            weight=ft.FontWeight.BOLD,
                            decoration=ft.TextDecoration.UNDERLINE,
                            decoration_color=NARANJA_ACCENTO,
                            decoration_thickness=1.6,
                        ),
                        on_click=lambda e, ent=entrada: self.dialog_palabra_hebreo(ent),
                    )
                )
                continue

            spans.append(
                ft.TextSpan(
                    fragmento,
                    style=ft.TextStyle(
                        color=color_fragmento,
                        weight=ft.FontWeight.W_600 if es_palabra_cordero else None,
                    ),
                )
            )

        if inicio_rojo is None and not tiene_palabras_diccionario:
            return ft.Text(
                texto,
                color=color_base,
                expand=expand,
            )

        return ft.Text(
            spans=spans,
            expand=expand,
        )

    def _texto_detalle_diccionario(self, entrada):
        return ft.Column(
            tight=True,
            spacing=8,
            controls=[
                ft.Text(
                    entrada.get("palabra", ""),
                    size=22,
                    weight=ft.FontWeight.BOLD,
                    color=TEXTO_PRINCIPAL,
                ),
                ft.Text(
                    entrada.get("hebreo", ""),
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=VIOLETA_ACCENTO,
                    text_align=ft.TextAlign.RIGHT,
                ),
                ft.Text(
                    f"Transliteracion: {entrada.get('transliteracion', '')}",
                    size=13,
                    color=TEXTO_SECUNDARIO,
                ),
                ft.Container(
                    padding=10,
                    border_radius=12,
                    bgcolor=ft.Colors.with_opacity(0.08, NARANJA_ACCENTO),
                    content=ft.Text(
                        entrada.get("significado", ""),
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=TEXTO_PRINCIPAL,
                    ),
                ),
                ft.Text(
                    entrada.get("descripcion", ""),
                    size=13,
                    color=TEXTO_PRINCIPAL,
                    selectable=True,
                ),
            ],
        )

    def dialog_palabra_hebreo(self, entrada):
        def cerrar(e=None):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Diccionario hebreo"),
            content=ft.Container(
                width=330 if self.responsive.is_mobile() else 420,
                content=self._texto_detalle_diccionario(entrada),
            ),
            actions=[
                ft.ElevatedButton("Cerrar", on_click=cerrar),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _item_diccionario_hebreo(self, entrada):
        return ft.Container(
            padding=10,
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, BORDE_SUAVE),
            on_click=lambda e, ent=entrada: self.dialog_palabra_hebreo(ent),
            content=ft.Column(
                tight=True,
                spacing=4,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                entrada.get("palabra", ""),
                                weight=ft.FontWeight.BOLD,
                                color=TEXTO_PRINCIPAL,
                            ),
                            ft.Text(
                                entrada.get("hebreo", ""),
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=VIOLETA_ACCENTO,
                            ),
                        ],
                    ),
                    ft.Text(
                        entrada.get("significado", ""),
                        size=12,
                        color=TEXTO_SECUNDARIO,
                    ),
                ],
            ),
        )

    def dialog_diccionario_hebreo(self, e=None):
        def cerrar(ev=None):
            dialog.open = False
            self.page.update()

        lista = ft.ListView(
            height=360 if self.responsive.is_mobile() else 460,
            spacing=8,
            controls=[
                self._item_diccionario_hebreo(entrada)
                for entrada in entradas_diccionario()
            ],
        )

        dialog = ft.AlertDialog(
            title=ft.Text("Diccionario hebreo"),
            content=ft.Container(
                width=340 if self.responsive.is_mobile() else 520,
                content=ft.Column(
                    tight=True,
                    spacing=10,
                    controls=[
                        ft.Text(
                            "Las palabras marcadas en negrita dentro de los versiculos se pueden tocar para ver su significado.",
                            size=12,
                            color=TEXTO_SECUNDARIO,
                        ),
                        lista,
                    ],
                ),
            ),
            actions=[
                ft.ElevatedButton("Cerrar", on_click=cerrar),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _inicio_palabras_cordero(self, libro, texto):
        libro_normalizado = str(libro or "").strip().lower()

        if libro_normalizado not in LIBROS_PALABRAS_CORDERO:
            return None

        verbos = (
            "dijo",
            "dice",
            "respondio",
            "respondió",
            "contesto",
            "contestó",
            "hablo",
            "habló",
            "clamo",
            "clamó",
        )

        for coincidencia in re.finditer(r":\s*", texto):
            previo = texto[max(0, coincidencia.start() - 130):coincidencia.start()].lower()
            menciona_cordero = (
                "jesus" in previo
                or "jesús" in previo
                or "cordero" in previo
            )

            if menciona_cordero and any(verbo in previo for verbo in verbos):
                return coincidencia.end()

        return None

    def _es_versiculo_palabras_cordero(self, libro, texto):
        return self._inicio_palabras_cordero(libro, texto) is not None

    def _versiculos_palabras_cordero(self):
        resultados = []

        for libro in self.libros or []:
            nombre_libro = libro.get("nombre", "")
            capitulos = libro.get("capitulos", [])

            for numero_capitulo, capitulo in enumerate(capitulos, start=1):
                for numero_versiculo, texto in enumerate(capitulo, start=1):
                    if not self._es_versiculo_palabras_cordero(nombre_libro, texto):
                        continue

                    clave = verso_id(nombre_libro, numero_capitulo, numero_versiculo)
                    resultados.append(
                        {
                            "id": clave,
                            "libro": nombre_libro,
                            "capitulo": numero_capitulo,
                            "versiculo": numero_versiculo,
                            "referencia": f"{nombre_libro} {numero_capitulo}:{numero_versiculo}",
                            "texto": texto,
                        }
                    )

        return resultados

    def _versos_ordenados_para_compartir(self, ids=None):
        ids = set(ids or self.versos_compartir)
        resultados = []

        if not ids:
            return resultados

        for libro in self.libros or []:
            nombre_libro = libro.get("nombre", "")

            for numero_capitulo, capitulo in enumerate(libro.get("capitulos", []), start=1):
                for numero_versiculo, texto in enumerate(capitulo, start=1):
                    clave = verso_id(nombre_libro, numero_capitulo, numero_versiculo)

                    if clave in ids:
                        resultados.append(
                            {
                                "id": clave,
                                "libro": nombre_libro,
                                "capitulo": numero_capitulo,
                                "versiculo": numero_versiculo,
                                "referencia": f"{nombre_libro} {numero_capitulo}:{numero_versiculo}",
                                "texto": texto,
                            }
                        )

        return resultados

    def _texto_versos_compartir(self, versos):
        return "\n".join(
            f"{verso['referencia']} {verso['texto']}"
            for verso in versos
        )

    def toggle_modo_compartir_multiple(self):
        self.modo_compartir_multiple = not self.modo_compartir_multiple

        if self.modo_compartir_multiple:
            self.verso_seleccionado = None
            self.objetivo_color = None
            mensaje = "Seleccion multiple activada. Toque versiculos para agregarlos o quitarlos."
        else:
            mensaje = "Seleccion multiple desactivada."

        self._snack(mensaje)
        self.router.refrescar()

    def limpiar_seleccion_multiple(self, e=None):
        self.versos_compartir.clear()
        self.modo_compartir_multiple = False
        self._snack("Seleccion multiple limpia.")
        self.router.refrescar()

    def tocar_versiculo(self, verso):
        if self.modo_compartir_multiple:
            self.toggle_verso_compartir(verso)
            return

        self.seleccionar_verso(verso)

    def toggle_verso_compartir(self, verso, refrescar=True):
        if verso in self.versos_compartir:
            self.versos_compartir.remove(verso)
        else:
            self.versos_compartir.add(verso)

        self.ultimo_verso_accionado = verso

        if refrescar:
            self.router.refrescar()

    def ir_a_verso_clave(self, clave):
        libro, capitulo, versiculo = self._desarmar_clave_verso(clave)

        if not libro or not capitulo or not versiculo:
            return

        self.libro_actual = libro
        self.capitulo_actual = capitulo
        self.dropdown_libro.value = libro
        self.dropdown_capitulo.options = self._opciones_capitulos()
        self.dropdown_capitulo.value = str(capitulo)
        self.modo_vista = "Versiculos"
        self.dropdown_modo.value = self.modo_vista
        self.verso_seleccionado = clave
        self.ultimo_verso_accionado = clave
        self._agregar_historial_referencia(
            libro,
            capitulo,
            versiculo,
            self._texto_versiculo(libro, capitulo, versiculo),
        )
        self._guardar_ultima_lectura()
        self.router.refrescar()

    def _render_versiculos(self):
        capitulo = self._capitulo_actual()

        for indice, texto in enumerate(capitulo, start=1):
            vid = verso_id(self.libro_actual, self.capitulo_actual, indice)
            resaltado = self.resaltados.get(vid)
            clave_numero = self._clave_numero_verso(vid)
            resaltado_numero = self.resaltados.get(clave_numero)
            seleccionado = self.verso_seleccionado == vid
            seleccionado_multiple = vid in self.versos_compartir
            verso_marcado = self._esta_marcado_para_color(vid)
            numero_seleccionado = self._objetivo_base() == clave_numero
            color_fondo = self._hex_color(resaltado)
            color_texto = self._texto_color(resaltado)

            self.panel_lectura.controls.append(
                ft.GestureDetector(
                    on_tap=lambda e, v=vid: self.tocar_versiculo(v),
                    on_double_tap=lambda e, v=vid: self.doble_tap_verso(v),
                    on_long_press=lambda e, v=vid: self.elegir_modo_color_identificador(
                        self._clave_numero_verso(v)
                    ),
                    content=ft.Container(
                        padding=8,
                        border_radius=6,
                        ink=True,
                        ink_color=ft.Colors.with_opacity(0.16, ft.Colors.BLUE),
                        bgcolor=(
                            color_fondo
                            if resaltado
                            else "#FFF7D6"
                            if seleccionado_multiple
                            else PERLA_VIOLETA if seleccionado or verso_marcado else ft.Colors.WHITE
                        ),
                        border=ft.Border.all(
                            2 if seleccionado or verso_marcado or seleccionado_multiple else 1,
                            NARANJA_ACCENTO
                            if seleccionado_multiple
                            else VIOLETA_IOS
                            if seleccionado or verso_marcado
                            else BORDER_MARRON
                            if self._es_blanco_borde(resaltado)
                            else ft.Colors.GREY_300,
                        ),
                        content=ft.Row(
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            spacing=8,
                            controls=[
                                ft.Icon(
                                    ft.Icons.CHECK_CIRCLE,
                                    size=18,
                                    color=NARANJA_ACCENTO,
                                    visible=seleccionado_multiple,
                                ),
                                self._icono_marcado(visible=verso_marcado),
                                self._control_identificador(
                                    indice,
                                    resaltado_numero,
                                    seleccionado=numero_seleccionado,
                                    sufijo=".",
                                    alto=30,
                                ),
                                self._texto_versiculo_visual(
                                    self.libro_actual,
                                    texto,
                                    color_texto,
                                ),
                            ],
                        ),
                    ),
                )
            )
    def cambiar_modo(self, e):
        self.cambiar_modo_valor(e.control.value)

    def cambiar_modo_valor(self, valor):
        self.modo_vista = "Libros" if valor == "Completa" else valor
        self.dropdown_modo.value = valor
        self.verso_seleccionado = None
        self.ultimo_verso_accionado = None
        self._guardar_ultima_lectura()
        self.router.refrescar()

    def cambiar_seccion_movil(self, seccion):
        self.seccion_movil = seccion
        self.router.refrescar()

    def deseleccionar_actual(self, e=None):
        hay_seleccion = any(
            [
                self.verso_seleccionado,
                self.objetivo_color,
                self.objetivo_color_control,
                self.versos_compartir,
            ]
        )

        if not hay_seleccion:
            return

        self.verso_seleccionado = None
        self.objetivo_color = None
        self.objetivo_color_control = None
        self.versos_compartir.clear()

        try:
            self._render_lectura()
            self.page.update()
        except Exception:
            self.router.refrescar()

    def volver_lectura(self):
        if self.modo_vista == "Versiculos":
            self.modo_vista = "Capitulos"
        elif self.modo_vista == "Capitulos":
            self.modo_vista = "Libros"
        else:
            return

        self.dropdown_modo.value = self.modo_vista
        self.verso_seleccionado = None
        self.ultimo_verso_accionado = None
        self._guardar_ultima_lectura()
        self.router.refrescar()

    def cambiar_libro(self, e):
        self.cambiar_libro_valor(e.control.value)

    def cambiar_libro_valor(self, valor):
        self.libro_actual = valor
        self.capitulo_actual = 1
        self.dropdown_capitulo.options = self._opciones_capitulos()
        self.dropdown_capitulo.value = "1"
        self.dropdown_libro.value = valor
        self.verso_seleccionado = None
        self.ultimo_verso_accionado = None
        self._guardar_ultima_lectura()
        self.router.refrescar()

    def cambiar_capitulo(self, e):
        self.cambiar_capitulo_valor(int(e.control.value))

    def cambiar_capitulo_valor(self, valor):
        self.capitulo_actual = valor
        self.dropdown_capitulo.value = str(valor)
        self.verso_seleccionado = None
        self.ultimo_verso_accionado = None
        self._guardar_ultima_lectura()
        self.router.refrescar()

    def ir_a_libro(self, nombre):
        self.libro_actual = nombre
        self.capitulo_actual = 1
        self.dropdown_libro.value = nombre
        self.dropdown_capitulo.options = self._opciones_capitulos()
        self.dropdown_capitulo.value = "1"
        self.modo_vista = "Capitulos"
        self.dropdown_modo.value = self.modo_vista
        self.verso_seleccionado = None
        self.ultimo_verso_accionado = None
        self._guardar_ultima_lectura()
        self.router.refrescar()

    def ir_a_capitulo(self, capitulo):
        self.capitulo_actual = capitulo
        self.dropdown_capitulo.value = str(capitulo)
        self.modo_vista = "Versiculos"
        self.dropdown_modo.value = self.modo_vista
        self.verso_seleccionado = None
        self.ultimo_verso_accionado = None
        self._guardar_ultima_lectura()
        self.router.refrescar()

    def ir_a_capitulo_de_libro(self, libro, capitulo):
        self.libro_actual = libro
        self.dropdown_libro.value = libro
        self.dropdown_capitulo.options = self._opciones_capitulos()
        self.ir_a_capitulo(capitulo)

    def marcar_para_colorear(self, clave, mensaje="Seleccione un color."):
        self.objetivo_color = clave
        self.objetivo_color_control = None
        self.verso_seleccionado = None
        self.ultimo_verso_accionado = None
        self._snack(mensaje)
        self.router.refrescar()

    def seleccionar_color(self, nombre):
        nombre = self._normalizar_color(nombre)
        self.color_actual = nombre

        if self.objetivo_color:
            clave, parte, indice = self._parse_objetivo_color()
            self._aplicar_color_identificador(clave, parte, indice, nombre)
            guardar_resaltados(self.resaltados)
            self.objetivo_color = None
            self.verso_seleccionado = None
            self.objetivo_color_control = None
            self.router.refrescar()
            return

        if self.verso_seleccionado:
            self.resaltar_seleccion()
        else:
            self.router.refrescar()

    def seleccionar_verso(self, verso):
        self.objetivo_color = None
        self.objetivo_color_control = None
        self.verso_seleccionado = verso
        self.ultimo_verso_accionado = verso
        self._render_lectura()
        self.page.update()

    def doble_tap_verso(self, verso):
        if verso in self.resaltados:
            self.resaltados.pop(verso, None)
            guardar_resaltados(self.resaltados)
            self.verso_seleccionado = None
            self.ultimo_verso_accionado = None
            self._snack("Color del versiculo quitado.")
            self._render_lectura()
            self.page.update()
            return

        self.codificar_versiculo_biblia(verso)

    def seleccionar_verso_para_color_completo(self, verso):
        self.marcar_para_colorear(
            verso,
            "Versiculo marcado. Seleccione un color.",
        )

    def seleccionar_capitulo_completo_para_color(self, libro, capitulo):
        self.marcar_para_colorear(
            self._clave_capitulo(libro, capitulo),
            "Capitulo marcado. Seleccione un color.",
        )

    def _clave_capitulo(self, libro, capitulo):
        return f"CAP|{libro}|{capitulo}"

    def _clave_libro(self, libro):
        return f"LIBRO|{libro}"

    def _clave_numero_verso(self, verso):
        return f"NUM|{verso}"

    def _color_capitulo_directo(self, libro, capitulo):
        return self.resaltados.get(self._clave_capitulo(libro, capitulo))

    def _aplicar_estilo_capitulo_control(
        self,
        control,
        libro,
        capitulo,
        color,
        seleccionado=False,
    ):
        color_fondo = (
            self._hex_color(color)
            or self._fondo_capitulo_resaltado(libro, capitulo)
            or ft.Colors.WHITE
        )
        color_texto = (
            self._texto_color(color)
            or self._texto_capitulo_resaltado(libro, capitulo)
            or ft.Colors.BLACK
        )
        control.bgcolor = PERLA_VIOLETA if seleccionado else color_fondo
        control.border = ft.Border.all(
            2 if seleccionado else 1,
            VIOLETA_IOS
            if seleccionado
            else BORDER_MARRON
            if self._es_blanco_borde(color)
            else ft.Colors.GREY_400,
        )

        if getattr(control, "content", None):
            control.content.color = color_texto

        try:
            control.update()
        except (RuntimeError, AssertionError):
            pass

    def seleccionar_capitulo_para_color(self, libro, capitulo, control=None):
        clave = self._clave_capitulo(libro, capitulo)

        if clave in self.resaltados:
            self.resaltados.pop(clave, None)
            guardar_resaltados(self.resaltados)
            self.objetivo_color = None
            self.objetivo_color_control = None
            if control:
                self._aplicar_estilo_capitulo_control(
                    control,
                    libro,
                    capitulo,
                    None,
                    seleccionado=False,
                )
            else:
                self._snack("Color de capitulo quitado.")
        else:
            self.objetivo_color = clave
            self.objetivo_color_control = control
            self.verso_seleccionado = None
            if control:
                self._aplicar_estilo_capitulo_control(
                    control,
                    libro,
                    capitulo,
                    None,
                    seleccionado=True,
                )
            else:
                self._snack("Seleccione un color para el capitulo.")

        if not control:
            self._render_lectura()
            self.page.update()

    def seleccionar_verso_para_color(self, verso):
        clave = self._clave_numero_verso(verso)

        if clave in self.resaltados:
            self.resaltados.pop(clave, None)
            guardar_resaltados(self.resaltados)
            self.objetivo_color = None
            self.verso_seleccionado = None
            self.ultimo_verso_accionado = None
            self._snack("Color del numero quitado.")
        else:
            self.objetivo_color = clave
            self.verso_seleccionado = None
            self.ultimo_verso_accionado = verso
            self._snack("Seleccione un color para el numero del versiculo.")

        self._render_lectura()
        self.page.update()

    def resaltar_seleccion(self):
        if not self.verso_seleccionado:
            self._snack("Seleccione un versiculo.")
            return

        self.resaltados[self.verso_seleccionado] = self.color_actual
        self.ultimo_verso_accionado = self.verso_seleccionado
        guardar_resaltados(self.resaltados)
        self.verso_seleccionado = None
        self.objetivo_color = None
        self.objetivo_color_control = None
        self._render_lectura()
        self.page.update()

    def elegir_modo_color_identificador(self, clave):
        numero = self._numero_desde_clave_identificador(clave)
        es_doble = len(str(numero)) >= 2

        def cerrar(e=None):
            dialog.open = False
            self.page.update()

        def elegir(parte, indice=None):
            cerrar()

            if parte == "completo":
                self.objetivo_color = clave
            else:
                self.objetivo_color = f"{clave}|DIG|{indice}"

            self.verso_seleccionado = None
            self.objetivo_color_control = None
            self._snack("Seleccione un color.")
            self.router.refrescar()

        def aplicar_auto(e=None):
            cerrar()
            self._aplicar_tres_colores_identificador(clave)

        def quitar(e=None):
            cerrar()
            self.quitar_color_identificador(clave)

        acciones = [
            ft.ElevatedButton(
                "Numero completo",
                on_click=lambda e: elegir("completo"),
            ),
        ]

        if es_doble:
            acciones.extend(
                [
                    ft.OutlinedButton(
                        "Primera cifra",
                        on_click=lambda e: elegir("digito", 0),
                    ),
                    ft.OutlinedButton(
                        "Segunda cifra",
                        on_click=lambda e: elegir("digito", 1),
                    ),
                    ft.ElevatedButton(
                        "Automatico por cifras",
                        icon=ft.Icons.AUTO_FIX_HIGH,
                        on_click=aplicar_auto,
                    ),
                ]
            )

        acciones.append(
            ft.TextButton(
                "Quitar color",
                on_click=quitar,
            )
        )

        dialog = ft.AlertDialog(
            title=ft.Text(f"Color del numero {numero}"),
            content=ft.Container(
                width=360,
                content=ft.Column(
                    tight=True,
                    spacing=8,
                    controls=[
                        ft.Text(
                            "Elija que parte quiere pintar.",
                            size=13,
                        ),
                        ft.Row(
                            wrap=True,
                            spacing=8,
                            run_spacing=8,
                            controls=acciones,
                        ),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def quitar_color_identificador(self, clave):
        if clave not in self.resaltados:
            return

        self.resaltados.pop(clave, None)
        guardar_resaltados(self.resaltados)
        self.objetivo_color = None
        self.objetivo_color_control = None
        self.verso_seleccionado = None
        self._snack("Color quitado.")
        self.router.refrescar()

    def quitar_color_objetivo(self):
        if not self.objetivo_color:
            verso = self.verso_seleccionado or self.ultimo_verso_accionado

            if verso and verso in self.resaltados:
                self.resaltados.pop(verso, None)
                guardar_resaltados(self.resaltados)
                self.verso_seleccionado = None
                self.ultimo_verso_accionado = None
                self._snack("Color del versiculo quitado.")
                self._render_lectura()
                self.page.update()
                return

            self._snack("Seleccione un versiculo o marque un elemento.")
            return

        clave, parte, indice = self._parse_objetivo_color()

        if parte == "digito":
            dato = self.resaltados.get(clave)

            if isinstance(dato, dict):
                digitos = list(dato.get("digitos", []))

                if 0 <= indice < len(digitos):
                    digitos[indice] = None

                if any(digitos):
                    dato["digitos"] = digitos
                    self.resaltados[clave] = dato
                else:
                    self.resaltados.pop(clave, None)
            else:
                self.resaltados.pop(clave, None)
        else:
            self.resaltados.pop(clave, None)

        guardar_resaltados(self.resaltados)
        self.objetivo_color = None
        self.objetivo_color_control = None
        self.verso_seleccionado = None
        self._snack("Color quitado.")
        self.router.refrescar()

    def _libro_tiene_resaltados(self, libro):
        prefijo = f"{libro}|"
        return any(
            clave.startswith(prefijo)
            for clave in self.resaltados
        )

    def _capitulo_tiene_resaltados(self, libro, capitulo):
        prefijo = f"{libro}|{capitulo}|"
        return any(
            clave.startswith(prefijo)
            for clave in self.resaltados
        )

    def _primer_color_resaltado(self, prefijo):
        if prefijo in self._cache_primer_resaltado:
            return self._cache_primer_resaltado[prefijo]

        encontrados = []

        for clave, color in self.resaltados.items():
            if not clave.startswith(prefijo):
                continue

            partes = clave.split("|")
            orden = 0

            if partes and partes[-1].isdigit():
                orden = int(partes[-1])

            encontrados.append((orden, color))

        if not encontrados:
            self._cache_primer_resaltado[prefijo] = None
            return None

        encontrados.sort(key=lambda item: item[0])
        color = self._color_principal(encontrados[0][1])
        self._cache_primer_resaltado[prefijo] = color
        return color

    def _fondo_capitulo_resaltado(self, libro, capitulo):
        color = (
            self._color_capitulo_directo(libro, capitulo)
            or self._primer_color_resaltado(f"{libro}|{capitulo}|")
        )
        return self._hex_color(color)

    def _texto_capitulo_resaltado(self, libro, capitulo):
        color = (
            self._color_capitulo_directo(libro, capitulo)
            or self._primer_color_resaltado(f"{libro}|{capitulo}|")
        )
        return self._texto_color(color) if color else None

    def _color_libro_resaltado(self, libro):
        return (
            self.resaltados.get(self._clave_libro(libro))
            or self._primer_color_resaltado(f"CAP|{libro}|")
            or self._primer_color_resaltado(f"NUM|{libro}|")
            or self._primer_color_resaltado(f"{libro}|")
        )

    def _fondo_libro_resaltado(self, libro):
        return self._hex_color(self._color_libro_resaltado(libro))

    def _texto_libro_resaltado(self, libro):
        color = self._color_libro_resaltado(libro)
        return self._texto_color(color) if color else None

    def seleccionar_libro_para_color(self, libro):
        self.marcar_para_colorear(
            self._clave_libro(libro),
            "Libro marcado. Seleccione un color.",
        )

    def quitar_color_libro(self, libro):
        clave_libro = self._clave_libro(libro)

        if clave_libro in self.resaltados:
            self.resaltados.pop(clave_libro, None)
            guardar_resaltados(self.resaltados)
            self.objetivo_color = None
            self._cache_primer_resaltado = {}
            self._snack("Color del libro quitado.")
            self.router.refrescar()
            return

        self.quitar_colores_libro(libro)

    def quitar_colores_libro(self, libro):
        prefijos = (
            f"{libro}|",
            f"CAP|{libro}|",
            f"NUM|{libro}|",
        )
        claves = [
            clave
            for clave in self.resaltados
            if any(clave.startswith(prefijo) for prefijo in prefijos)
        ]

        if not claves:
            self._snack("Ese libro no tiene colores.")
            return

        for clave in claves:
            self.resaltados.pop(clave, None)

        guardar_resaltados(self.resaltados)
        self.objetivo_color = None
        self.verso_seleccionado = None
        self._cache_primer_resaltado = {}
        self._snack("Colores del libro quitados.")
        self.router.refrescar()

    def quitar_resaltado_verso(self, verso):
        if verso not in self.resaltados:
            return

        self.resaltados.pop(verso, None)
        guardar_resaltados(self.resaltados)

        if self.verso_seleccionado == verso:
            self.verso_seleccionado = None

        self.objetivo_color = None
        self.objetivo_color_control = None
        self.ultimo_verso_accionado = verso
        self._render_lectura()
        self.page.update()
        self._snack("Resaltado quitado.")

    def dialog_versiculos_por_color(self):
        color_inicial = self.color_actual if self.color_actual in COLORES_RESALTADO else "Amarillo"
        selector = ft.Dropdown(
            label="Color",
            value=color_inicial,
            options=[
                ft.dropdown.Option(color)
                for color in COLORES_RESALTADO
            ],
        )
        resumen = ft.Text("", size=12, color=ft.Colors.GREY_700)
        lista = ft.ListView(
            height=380 if not self.responsive.is_mobile() else 320,
            spacing=6,
            auto_scroll=False,
        )

        def cerrar(e=None):
            dialog.open = False
            self.page.update()

        def abrir_resultado(resultado):
            cerrar()
            self.ir_a_resultado(resultado)

        def copiar_resultados(e=None):
            resultados = self._versiculos_marcados_por_color(selector.value)

            if not resultados:
                self._snack("No hay versículos para copiar.")
                return

            texto = "\n".join(
                (
                    f"{r['libro']} {r['capitulo']}:{r['versiculo']} "
                    f"{r['texto']}"
                )
                for r in resultados
            )
            copiar_al_portapapeles(self.page, texto)
            self._snack("Lista copiada.")

        def resultados_color_actual():
            return self._versiculos_marcados_por_color(selector.value)

        def compartir_color(e=None):
            resultados = resultados_color_actual()

            if not resultados:
                self._snack("No hay versiculos para compartir.")
                return

            cerrar()
            self._compartir_resultados_filtrados(
                resultados,
                f"Versiculos marcados en {selector.value}",
            )

        def guardar_color(e=None):
            resultados = resultados_color_actual()

            if not resultados:
                self._snack("No hay versiculos para guardar.")
                return

            cerrar()
            self._guardar_resultados_filtrados(
                resultados,
                f"Versiculos marcados en {selector.value}",
            )

        def compartir_todos(e=None):
            resultados = self._versiculos_marcados_todos_colores()

            if not resultados:
                self._snack("No hay versiculos marcados para compartir.")
                return

            cerrar()
            self._compartir_resultados_filtrados(
                resultados,
                "Todos los versiculos marcados por color",
                incluir_color=True,
            )

        def guardar_todos(e=None):
            resultados = self._versiculos_marcados_todos_colores()

            if not resultados:
                self._snack("No hay versiculos marcados para guardar.")
                return

            cerrar()
            self._guardar_resultados_filtrados(
                resultados,
                "Todos los versiculos marcados por color",
                incluir_color=True,
            )

        def renderizar(e=None):
            color = selector.value
            resultados = self._versiculos_marcados_por_color(color)
            lista.controls.clear()
            resumen.value = f"{len(resultados)} versículo(s) marcados en {color}."
            fondo = self._hex_color(color, ft.Colors.WHITE)
            texto_color = self._texto_color(color)
            borde = (
                BORDER_MARRON
                if self._es_blanco_borde(color)
                else ft.Colors.GREY_300
            )

            if not resultados:
                lista.controls.append(
                    ft.Container(
                        padding=10,
                        bgcolor=ft.Colors.WHITE,
                        border=ft.Border.all(1, ft.Colors.GREY_300),
                        border_radius=6,
                        content=ft.Text("No hay versículos con ese color."),
                    )
                )
            else:
                for resultado in resultados:
                    lista.controls.append(
                        ft.Container(
                            padding=10,
                            bgcolor=fondo,
                            border=ft.Border.all(1, borde),
                            border_radius=6,
                            on_click=lambda e, r=resultado: abrir_resultado(r),
                            content=ft.Column(
                                tight=True,
                                spacing=4,
                                controls=[
                                    ft.Text(
                                        (
                                            f"{resultado['libro']} "
                                            f"{resultado['capitulo']}:"
                                            f"{resultado['versiculo']}"
                                        ),
                                        weight=ft.FontWeight.BOLD,
                                        color=texto_color,
                                    ),
                                    ft.Text(
                                        resultado["texto"],
                                        color=texto_color,
                                    ),
                                ],
                            ),
                        )
                    )

            try:
                resumen.update()
                lista.update()
            except (RuntimeError, AssertionError):
                pass

        selector.on_select = renderizar
        acciones_filtro = ft.Container(
            padding=ft.Padding(left=0, top=8, right=0, bottom=8),
            border=ft.Border(
                top=ft.BorderSide(1, BORDE_SUAVE),
                bottom=ft.BorderSide(1, BORDE_SUAVE),
            ),
            content=ft.Column(
                tight=True,
                spacing=8,
                controls=[
                    ft.Row(
                        wrap=True,
                        spacing=8,
                        run_spacing=8,
                        controls=[
                            ft.OutlinedButton(
                                "Compartir color",
                                icon=ft.Icons.SHARE,
                                on_click=compartir_color,
                            ),
                            ft.OutlinedButton(
                                "Guardar color",
                                icon=ft.Icons.SAVE_ALT,
                                on_click=guardar_color,
                            ),
                            ft.TextButton(
                                "Copiar color",
                                icon=ft.Icons.CONTENT_COPY,
                                on_click=copiar_resultados,
                            ),
                        ],
                    ),
                    ft.Row(
                        wrap=True,
                        spacing=8,
                        run_spacing=8,
                        controls=[
                            ft.ElevatedButton(
                                "Compartir todo",
                                icon=ft.Icons.SHARE,
                                on_click=compartir_todos,
                            ),
                            ft.ElevatedButton(
                                "Guardar todo",
                                icon=ft.Icons.SAVE_ALT,
                                on_click=guardar_todos,
                            ),
                        ],
                    ),
                ],
            ),
        )
        dialog = ft.AlertDialog(
            title=ft.Text("Versículos por color"),
            content=ft.Container(
                width=620 if not self.responsive.is_mobile() else 360,
                content=ft.Column(
                    tight=True,
                    spacing=10,
                    controls=[
                        selector,
                        resumen,
                        acciones_filtro,
                        lista,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=cerrar),
            ],
        )

        self.page.overlay.append(dialog)
        renderizar()
        dialog.open = True
        self.page.update()

    def _versiculos_marcados_por_color(self, color):
        resultados = []

        for libro in self.libros:
            for capitulo_indice, capitulo in enumerate(libro["capitulos"], start=1):
                for versiculo_indice, texto in enumerate(capitulo, start=1):
                    clave = verso_id(
                        libro["nombre"],
                        capitulo_indice,
                        versiculo_indice,
                    )

                    if self._normalizar_color(self.resaltados.get(clave)) != color:
                        continue

                    resultados.append(
                        {
                            "libro": libro["nombre"],
                            "capitulo": capitulo_indice,
                            "versiculo": versiculo_indice,
                            "texto": texto,
                        }
                    )

        return resultados

    def _versiculos_marcados_todos_colores(self):
        resultados = []

        for color in COLORES_RESALTADO:
            for resultado in self._versiculos_marcados_por_color(color):
                item = resultado.copy()
                item["color"] = color
                resultados.append(item)

        return resultados

    def _texto_resultados_filtrados(self, resultados, titulo, incluir_color=False):
        lineas = [titulo, ""]

        color_actual = None
        for resultado in resultados:
            color = resultado.get("color")

            if incluir_color and color and color != color_actual:
                if color_actual is not None:
                    lineas.append("")
                lineas.append(f"[{color}]")
                color_actual = color

            lineas.append(
                (
                    f"{resultado['libro']} "
                    f"{resultado['capitulo']}:{resultado['versiculo']} "
                    f"{resultado['texto']}"
                )
            )

        return "\n".join(lineas).strip()

    def _compartir_resultados_filtrados(self, resultados, titulo, incluir_color=False):
        texto = self._texto_resultados_filtrados(resultados, titulo, incluir_color)
        compartir_texto(self.page, texto, titulo)

    def _guardar_resultados_filtrados(self, resultados, titulo, incluir_color=False):
        texto = self._texto_resultados_filtrados(resultados, titulo, incluir_color)

        def guardar_con_nombre(nombre, carpeta=None):
            destino = carpeta or state.carpetas.obtener_por_nombre("FRAGMENTOS BIBLICOS")
            state.guardados.guardar(
                {
                    "tipo": "fragmento_biblico",
                    "carpeta": destino["nombre"] if destino else "FRAGMENTOS BIBLICOS",
                    "carpeta_id": destino["id"] if destino else 3,
                    "nombre": nombre,
                    "palabra": nombre or titulo,
                    "referencia": titulo,
                    "alfabeto": "",
                    "suma": texto,
                    "resultado": "",
                    "contenido": texto,
                }
            )
            self._mostrar_guardado_correcto(nombre or titulo)

        pedir_nombre_y_carpeta_guardado(
            self.page,
            "Guardar filtro biblico",
            titulo,
            state.carpetas,
            "FRAGMENTOS BIBLICOS",
            guardar_con_nombre,
            "Se guardara en FRAGMENTOS BIBLICOS.",
        )


    def _libro_por_nombre(self, nombre):
        for libro in self.libros:
            if libro.get("nombre") == nombre:
                return libro
        return None

    def _texto_libro_biblia(self, libro_nombre):
        libro = self._libro_por_nombre(libro_nombre)

        if not libro:
            return ""

        partes = []

        for numero_capitulo, capitulo in enumerate(libro.get("capitulos", []), start=1):
            partes.append(f"{libro_nombre} {numero_capitulo}")

            for numero_versiculo, texto in enumerate(capitulo, start=1):
                partes.append(f"{numero_versiculo}. {texto}")

        return "\n".join(partes)

    def _texto_capitulo_biblia(self, libro_nombre, capitulo_numero):
        libro = self._libro_por_nombre(libro_nombre)

        if not libro:
            return ""

        capitulos = libro.get("capitulos", [])
        indice = capitulo_numero - 1

        if indice < 0 or indice >= len(capitulos):
            return ""

        partes = [f"{libro_nombre} {capitulo_numero}"]

        for numero_versiculo, texto in enumerate(capitulos[indice], start=1):
            partes.append(f"{numero_versiculo}. {texto}")

        return "\n".join(partes)

    def _detalle_visual_codificacion(self, datos):
        suma = str(datos.get("suma", ""))
        detalle = []

        for parte in suma.replace("\n", " + ").split("+"):
            parte = parte.strip()

            if not parte:
                continue

            if "=" not in parte:
                continue

            simbolo, valor = parte.split("=", 1)
            simbolo = simbolo.strip().upper()
            valor = valor.strip()

            if simbolo and valor:
                detalle.append(
                    {
                        "simbolo": simbolo,
                        "valor": valor,
                    }
                )

        return detalle

    def _codificar_y_guardar_biblia(self, texto, referencia, alcance):
        texto = (texto or "").strip()

        if not texto:
            self._snack("No hay texto para codificar.")
            return

        datos = self.codificador_service.codificar_29(texto)
        detalle_visual = self._detalle_visual_codificacion(datos)
        destino_default = state.carpetas.obtener_por_nombre("FRAGMENTOS BIBLICOS")
        nombre_default = f"{referencia} codificado"

        def guardar_con_nombre(nombre, carpeta=None):
            destino = carpeta or destino_default
            registro = datos.copy()
            registro.update(
                {
                    "tipo": "tarjeta",
                    "carpeta": destino["nombre"] if destino else "FRAGMENTOS BIBLICOS",
                    "carpeta_id": destino["id"] if destino else 3,
                    "nombre": nombre or nombre_default,
                    "palabra": referencia,
                    "referencia": referencia,
                    "origen": "Biblia",
                    "alcance": alcance,
                    "contenido": {
                        "tipo": "biblia_codificada",
                        "alcance": alcance,
                        "referencia": referencia,
                        "texto_original": texto,
                        "detalle_visual": detalle_visual,
                        "datos_codificacion": datos,
                    },
                }
            )

            state.guardados.guardar(registro)
            self._mostrar_guardado_correcto(nombre or nombre_default)

        pedir_nombre_y_carpeta_guardado(
            self.page,
            f"Guardar {alcance.lower()} codificado",
            nombre_default,
            state.carpetas,
            "FRAGMENTOS BIBLICOS",
            guardar_con_nombre,
            "Se guardara en FRAGMENTOS BIBLICOS.",
        )

    def codificar_libro_biblia(self, libro_nombre):
        texto = self._texto_libro_biblia(libro_nombre)
        self._codificar_y_guardar_biblia(
            texto=texto,
            referencia=libro_nombre,
            alcance="Libro",
        )

    def codificar_capitulo_biblia(self, libro_nombre, capitulo_numero):
        texto = self._texto_capitulo_biblia(libro_nombre, capitulo_numero)
        self._codificar_y_guardar_biblia(
            texto=texto,
            referencia=f"{libro_nombre} {capitulo_numero}",
            alcance="Capitulo",
        )

    def codificar_versiculo_biblia(self, verso):
        partes = verso.split("|")

        if len(partes) != 3:
            self._snack("Versiculo invalido.")
            return

        libro, capitulo, versiculo = partes[0], int(partes[1]), int(partes[2])
        texto = self._texto_versiculo(libro, capitulo, versiculo)

        self._codificar_y_guardar_biblia(
            texto=texto,
            referencia=f"{libro} {capitulo}:{versiculo}",
            alcance="Versiculo",
        )

    def guardar_fragmento(self):
        verso = self._verso_activo()

        if not verso:
            self._snack("Seleccione un versiculo.")
            return

        partes = verso.split("|")
        libro, capitulo, versiculo = partes[0], int(partes[1]), int(partes[2])
        texto = self._texto_versiculo(libro, capitulo, versiculo)
        referencia = f"{libro} {capitulo}:{versiculo}"

        def guardar_con_nombre(nombre, carpeta=None):
            destino = carpeta or state.carpetas.obtener_por_nombre("FRAGMENTOS BIBLICOS")
            state.guardados.guardar(
                {
                    "tipo": "fragmento_biblico",
                    "carpeta": destino["nombre"] if destino else "FRAGMENTOS BIBLICOS",
                    "carpeta_id": destino["id"] if destino else 3,
                    "nombre": nombre,
                    "palabra": nombre or referencia,
                    "referencia": referencia,
                    "alfabeto": "",
                    "suma": texto,
                    "resultado": "",
                    "contenido": texto,
                }
            )
            self._mostrar_guardado_correcto(nombre or referencia)

        pedir_nombre_y_carpeta_guardado(
            self.page,
            "Guardar fragmento",
            referencia,
            state.carpetas,
            "FRAGMENTOS BIBLICOS",
            guardar_con_nombre,
            "Se guardara en FRAGMENTOS BIBLICOS.",
        )

    def _guardar_fragmento_legacy(self, referencia, texto):
        state.guardados.guardar(
            {
                "tipo": "fragmento_biblico",
                "carpeta": "FRAGMENTOS BIBLICOS",
                "nombre": referencia,
                "palabra": referencia,
                "referencia": referencia,
                "alfabeto": "",
                "suma": texto,
                "resultado": "",
                "contenido": texto,
            }
        )
        self._mostrar_guardado_correcto(referencia)

    def copiar_seleccion(self):
        versos = self._versos_ordenados_para_compartir()

        if versos:
            copiar_al_portapapeles(self.page, self._texto_versos_compartir(versos))
            self._snack("Versiculos seleccionados copiados.")
            return

        verso = self._verso_activo()

        if not verso:
            self._snack("Seleccione un versiculo.")
            return

        partes = verso.split("|")
        libro, capitulo, versiculo = partes[0], int(partes[1]), int(partes[2])
        texto = self._texto_versiculo(libro, capitulo, versiculo)
        copiar_al_portapapeles(self.page, f"{libro} {capitulo}:{versiculo} {texto}")
        self._snack("Versiculo copiado.")

    def compartir_seleccion(self):
        versos = self._versos_ordenados_para_compartir()

        if versos:
            compartir_texto(
                self.page,
                self._texto_versos_compartir(versos),
                "Versiculos biblicos",
            )
            return

        verso = self._verso_activo()

        if not verso:
            self._snack("Seleccione un versiculo.")
            return

        partes = verso.split("|")
        libro, capitulo, versiculo = partes[0], int(partes[1]), int(partes[2])
        texto = self._texto_versiculo(libro, capitulo, versiculo)
        compartir_texto(
            self.page,
            f"{libro} {capitulo}:{versiculo} {texto}",
            "Fragmento biblico",
        )

    def copiar_capitulo(self):
        capitulo = self._capitulo_actual()

        if not capitulo:
            self._snack("No hay capitulo para copiar.")
            return

        lineas = [
            f"{self.libro_actual} {self.capitulo_actual}",
            "",
        ]
        lineas.extend(
            f"{indice}. {texto}"
            for indice, texto in enumerate(capitulo, start=1)
        )
        copiar_al_portapapeles(self.page, "\n".join(lineas))
        self._snack("Capitulo copiado.")

    def buscar(self, e=None):
        if e is not None:
            ocultar_teclado(self.page, e.control)

        self.resultados_busqueda.controls.clear()

        resultados = buscar_texto(self.libros, self.busqueda.value or "")
        self.ultimos_resultados_busqueda = resultados
        self.ultima_busqueda_texto = (self.busqueda.value or "").strip()

        for resultado in resultados[:80]:
            vid = verso_id(
                resultado["libro"],
                resultado["capitulo"],
                resultado["versiculo"],
            )
            seleccionado_multiple = vid in self.versos_compartir

            self.resultados_busqueda.controls.append(
                ft.Container(
                    padding=8,
                    bgcolor="#FFF7D6" if seleccionado_multiple else ft.Colors.WHITE,
                    border=ft.Border.all(
                        2 if seleccionado_multiple else 1,
                        NARANJA_ACCENTO if seleccionado_multiple else ft.Colors.GREY_300,
                    ),
                    border_radius=6,
                    on_click=(
                        (lambda e, v=vid: self.toggle_verso_compartir(v))
                        if self.modo_compartir_multiple
                        else (lambda e, r=resultado: self.ir_a_resultado(r))
                    ),
                    content=ft.Row(
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE,
                                size=18,
                                color=NARANJA_ACCENTO,
                                visible=seleccionado_multiple,
                            ),
                            ft.Text(
                                (
                                    f"{resultado['libro']} "
                                    f"{resultado['capitulo']}:{resultado['versiculo']} "
                                    f"{resultado['texto']}"
                                ),
                                expand=True,
                                selectable=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.OPEN_IN_NEW,
                                tooltip="Abrir versiculo",
                                icon_color=TEXTO_SECUNDARIO,
                                on_click=lambda e, r=resultado: self.ir_a_resultado(r),
                            ),
                        ],
                    ),
                )
            )

        if not resultados:
            self.resultados_busqueda.controls.append(
                ft.Text("Sin resultados.")
            )

        self.page.update()

    def _texto_resultados_busqueda(self):
        termino = self.ultima_busqueda_texto or "Busqueda"
        lineas = [
            f"Busqueda biblica: {termino}",
            f"Resultados: {len(self.ultimos_resultados_busqueda)}",
            "",
        ]

        for resultado in self.ultimos_resultados_busqueda:
            lineas.append(
                (
                    f"{resultado['libro']} "
                    f"{resultado['capitulo']}:{resultado['versiculo']} "
                    f"{resultado['texto']}"
                )
            )

        return "\n".join(lineas)

    def guardar_busqueda(self, e=None):
        if not self.ultimos_resultados_busqueda:
            self._snack("Primero realice una busqueda con resultados.")
            return

        termino = self.ultima_busqueda_texto or "Busqueda"
        nombre_default = f"Busqueda {termino}"
        texto = self._texto_resultados_busqueda()

        def guardar_con_nombre(nombre, carpeta=None):
            destino = carpeta or state.carpetas.obtener_por_nombre("FRAGMENTOS BIBLICOS")
            state.guardados.guardar(
                {
                    "tipo": "fragmento_biblico",
                    "carpeta": destino["nombre"] if destino else "FRAGMENTOS BIBLICOS",
                    "carpeta_id": destino["id"] if destino else 3,
                    "nombre": nombre or nombre_default,
                    "palabra": nombre or nombre_default,
                    "referencia": f"Busqueda: {termino}",
                    "alfabeto": "",
                    "suma": texto,
                    "resultado": len(self.ultimos_resultados_busqueda),
                    "contenido": texto,
                }
            )
            self._mostrar_guardado_correcto(nombre or nombre_default)

        pedir_nombre_y_carpeta_guardado(
            self.page,
            "Guardar busqueda",
            nombre_default,
            state.carpetas,
            "FRAGMENTOS BIBLICOS",
            guardar_con_nombre,
            "Se guardara en FRAGMENTOS BIBLICOS.",
        )

    def ir_a_resultado(self, resultado):
        self.libro_actual = resultado["libro"]
        self.capitulo_actual = resultado["capitulo"]
        self.dropdown_libro.value = self.libro_actual
        self.dropdown_capitulo.options = self._opciones_capitulos()
        self.dropdown_capitulo.value = str(self.capitulo_actual)
        self.modo_vista = "Versiculos"
        self.dropdown_modo.value = self.modo_vista
        self.verso_seleccionado = verso_id(
            resultado["libro"],
            resultado["capitulo"],
            resultado["versiculo"],
        )
        self.ultimo_verso_accionado = self.verso_seleccionado
        self._agregar_historial_referencia(
            resultado["libro"],
            resultado["capitulo"],
            resultado["versiculo"],
            resultado.get("texto", ""),
        )
        self._guardar_ultima_lectura()
        self.router.refrescar()

    def _verso_activo(self):
        return self.verso_seleccionado or self.ultimo_verso_accionado

    def _texto_versiculo(self, libro_nombre, capitulo, versiculo):
        for libro in self.libros:
            if libro["nombre"] != libro_nombre:
                continue

            return libro["capitulos"][capitulo - 1][versiculo - 1]

        return ""

    def recargar(self):
        self.libros = BibliaService.libros()
        self.resaltados = cargar_resaltados()
        self.libro_actual = self.libros[0]["nombre"] if self.libros else None
        self.capitulo_actual = 1
        self.dropdown_libro.options = self._opciones_libros()
        self.dropdown_libro.value = self.libro_actual
        self.dropdown_capitulo.options = self._opciones_capitulos()
        self.dropdown_capitulo.value = "1" if self.libros else None
        self.modo_vista = "Libros"
        self.dropdown_modo.value = self.modo_vista
        self.verso_seleccionado = None
        self.ultimo_verso_accionado = None
        self.router.refrescar()

    def _snack(self, mensaje):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje),
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _mostrar_guardado_correcto(self, referencia):
        def cerrar(e=None):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Guardado correctamente"),
            content=ft.Text(
                f"{referencia} fue enviado a FRAGMENTOS BIBLICOS.",
            ),
            actions=[
                ft.ElevatedButton(
                    "Aceptar",
                    on_click=cerrar,
                ),
            ],
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
