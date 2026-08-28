# Camino 2 - Biblia visual unificada
# Mantiene la logica del Camino 1 y solo mejora presentacion.

import asyncio
import copy
import json
import random
import re
import unicodedata
from pathlib import Path

import flet as ft

from logica.biblia import (
    BIBLIA_ARCHIVO,
    buscar_texto,
    cargar_comentarios,
    cargar_resaltados,
    guardar_comentarios,
    guardar_resaltados,
    verso_id,
)
from logica.diccionario_hebreo import (
    entradas_diccionario,
    fragmentos_con_diccionario,
)
from logica.tarjeta_biblica import (
    datos_tarjeta_versiculo,
)
from services.biblia_service import BibliaService
from services.archivo_local_service import ArchivoLocalService
from services.exportador_biblia_codificada import ExportadorBibliaCodificada
from ui.clipboard import copiar_al_portapapeles
from ui.compartir import compartir_archivo, compartir_texto, descargar_archivo
from ui.responsive import Responsive
from ui.tema import (
    PERLA_PANEL,
    SUPERFICIE_PERLADA,
    TEXTO_PRINCIPAL as TEMA_TEXTO_PRINCIPAL,
    TEXTO_SECUNDARIO as TEMA_TEXTO_SECUNDARIO,
    sombra_suave,
)
from ui.teclado import ocultar_teclado


COLOR_BLANCO_BORDE = "Blanco borde"
BORDER_MARRON = "#B97852"
MARRON_ACENTO = "#9A5D43"
MARRON_PERLA = "#F8EEE8"
MARRON_BORDE = "#E8D0C3"

COLORES_RESALTADO = {
    "Negro": "#16181D",
    "Marron": "#965B3E",
    "Rojo": "#D61F3C",
    "Naranja": "#E86F16",
    "Amarillo": "#F5C400",
    "Verde": "#129447",
    "Azul": "#2457D6",
    "Purpura": "#7E22CE",
    "Gris": "#64748B",
    COLOR_BLANCO_BORDE: "#FFFFFF",
}
COLORES_TEXTO_RESALTADO = {
    "Negro": "#FFFFFF",
    "Marron": "#FFFFFF",
    "Rojo": "#FFFFFF",
    "Azul": "#FFFFFF",
    "Purpura": "#FFFFFF",
    "Gris": "#FFFFFF",
}
ALIAS_COLORES_RESALTADO = {
    "Blanco": COLOR_BLANCO_BORDE,
    "Violeta": "Purpura",
    "violeta": "Purpura",
    "VIOLETA": "Purpura",
    "Púrpura": "Purpura",
}
DIGITO_A_COLOR = {
    1: "Marron",
    2: "Rojo",
    3: "Naranja",
    4: "Amarillo",
    5: "Verde",
    6: "Azul",
    7: "Purpura",
    8: "Gris",
    9: COLOR_BLANCO_BORDE,
}


# ===== ESTILO MODERNO LIMPIO PARA BIBLIA =====
FONDO_BIBLIA_MODERNO = ft.Colors.TRANSPARENT
TARJETA_BLANCA = SUPERFICIE_PERLADA
BORDE_SUAVE = MARRON_BORDE
TEXTO_PRINCIPAL = TEMA_TEXTO_PRINCIPAL
TEXTO_SECUNDARIO = TEMA_TEXTO_SECUNDARIO
ROJO_ACCENTO = "#FF2D55"
NARANJA_ACCENTO = "#FF9500"
AZUL_ACCENTO = "#0A84FF"
PURPURA_ACCENTO = MARRON_ACENTO
VERDE_ACCENTO = "#34C759"
GRIS_SUAVE = "#F8F3FA"
CHOCOLATE_LECTURA = "#7B3F00"
SUBTITULO_LECTURA = ft.Colors.BLACK
FUENTE_LECTURA_BIBLIA = "Georgia"
OPACIDAD_RESALTADO_LECTURA = 0.52
ESPERA_SELECTOR_COLOR_TEXTO = 0.65
MARCADOR_COMENTARIO = " \u270E "
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
        self.comentarios = cargar_comentarios()
        ultima_lectura = self._cargar_ultima_lectura()
        self.libro_actual = ultima_lectura.get("libro") or (self.libros[0]["nombre"] if self.libros else None)
        self.capitulo_actual = int(ultima_lectura.get("capitulo") or 1)
        self.verso_seleccionado = None
        self.ultimo_verso_accionado = None
        self.modo_compartir_multiple = False
        self.versos_compartir = set()
        self.color_actual = "Amarillo"
        self.tamano_fuente_lectura = self._normalizar_tamano_fuente(
            ultima_lectura.get("tamano_fuente")
        )
        self.aviso_aceptado = False
        self.modo_vista = ultima_lectura.get("modo") or "Libros"
        self.seccion_movil = "lectura"
        self.objetivo_color = None
        self.objetivo_color_control = None
        self.objetivos_color = set()
        self.seleccion_texto_resaltado = None
        self._version_seleccion_resaltado = 0
        self._version_guardado_resaltados = 0
        self._indice_busqueda_programado = False
        self._dialog_color_contextual = None
        self._cache_primer_resaltado = {}
        self._cache_partes_resaltado_palabras = {}
        # Referencias a los textos ya montados: permiten repintar solamente el
        # parrafo afectado, sin reconstruir todo el capitulo o el libro.
        self._controles_texto_lectura = {}
        self._controles_tamano_lectura = {}
        self._rangos_seleccion_lectura = {}
        self._libro_completo_cargado = None
        self._siguiente_capitulo_libro = 1
        self._cargando_tramo_libro = False
        self._perfil_tamano_biblia = None
        self._version_redimension_biblia = 0
        self._lista_barra_libros = None
        self._libro_barra_pendiente = None
        self.exportador_biblia_codificada = ExportadorBibliaCodificada()
        self.ultimos_resultados_busqueda = []
        self.ultima_busqueda_texto = ""
        self.panel_lectura = ft.ListView(
            expand=True,
            spacing=6,
            # El carril derecho evita que el scrollbar superpuesto cubra texto seleccionable.
            padding=ft.Padding(left=0, top=0, right=34, bottom=0),
            build_controls_on_demand=True,
            cache_extent=120,
            # Evita enviar un evento Python por cada pixel desplazado.
            scroll_interval=180,
            on_scroll=self._al_desplazar_libro_completo,
            scroll=ft.Scrollbar(
                thumb_visibility=True,
                track_visibility=True,
                thickness=9,
                radius=5,
                interactive=True,
                orientation=ft.ScrollbarOrientation.RIGHT,
            ),
        )
        self._controles_versiculos = {}
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
            color=PURPURA_ACCENTO,
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
                ft.dropdown.Option("Libro"),
                ft.dropdown.Option("Versiculos"),
            ],
            value=self.modo_vista,
            on_select=self.cambiar_modo,
        )
        self._normalizar_ultima_lectura()

    def _solo_lectura(self):
        return getattr(self.router, "nivel", 4) == 1

    def _puede(self, capacidad):
        comprobar = getattr(self.router, "tiene_capacidad", None)
        return bool(comprobar(capacidad)) if callable(comprobar) else True

    def _normalizar_tamano_fuente(self, valor):
        try:
            return min(24, max(13, int(valor or 16)))
        except (TypeError, ValueError):
            return 16

    def cambiar_tamano_fuente_lectura(self, delta):
        nuevo_tamano = self._normalizar_tamano_fuente(
            self.tamano_fuente_lectura + delta
        )
        if nuevo_tamano == self.tamano_fuente_lectura:
            return
        self.tamano_fuente_lectura = nuevo_tamano
        self._guardar_ultima_lectura()
        if self._actualizar_tamano_lectura_visible():
            return
        self._refrescar_lectura_actual()

    def _tamano_numero_lectura(self):
        return max(9, self.tamano_fuente_lectura - 5)

    def _tamano_subtitulo_lectura(self):
        return max(13, self.tamano_fuente_lectura - 2)

    def _alto_linea_lectura(self):
        return 1.58 if self.tamano_fuente_lectura >= 19 else 1.65

    def _refrescar_lectura_actual(self):
        try:
            self._render_lectura()
            self.page.update(
                self.panel_lectura,
                self.dropdown_libro,
                self.dropdown_capitulo,
                self.dropdown_modo,
            )
            self._programar_desplazamiento_barra_libros()
        except (RuntimeError, AssertionError, AttributeError):
            self.router.refrescar()

    def _abrir_dialogo_biblia(self, dialogo):
        """Monta solo el dialogo, sin reenviar toda la pantalla de lectura."""
        try:
            self.page.show_dialog(dialogo)
            return
        except (AttributeError, RuntimeError, AssertionError):
            pass
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()

    def _cerrar_dialogo_biblia(self, dialogo):
        dialogo.open = False
        try:
            dialogo.update()
        except (RuntimeError, AssertionError):
            self.page.update()

    def _registrar_control_tamano_lectura(self, control, actualizar):
        self._controles_tamano_lectura[id(control)] = (control, actualizar)

    def _actualizar_tamano_lectura_visible(self):
        """Cambia tipografia en lote sin volver a construir la lectura."""
        if not self._controles_tamano_lectura:
            return False

        controles = []
        try:
            for control, actualizar in self._controles_tamano_lectura.values():
                actualizar()
                controles.append(control)
            self.page.update(*controles)
            return True
        except (RuntimeError, AssertionError, AttributeError):
            return False

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
                        "tamano_fuente": self.tamano_fuente_lectura,
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

        if self.modo_vista not in ("Libros", "Capitulos", "Libro", "Versiculos"):
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
        self._ir_a_referencia_texto(texto)

    def _ir_a_referencia_texto(self, texto):
        referencia = self._parsear_referencia(texto)

        if not referencia:
            self._snack("No pude encontrar esa referencia. Ejemplo válido: Juan 3:16 o Salmo 91.")
            return

        libro, capitulo, versiculo = referencia
        self._limpiar_seleccion_transitoria()
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
        self._refrescar_lectura_actual()

    def _tiene_comentario(self, clave):
        comentario = self.comentarios.get(clave)
        return isinstance(comentario, dict) and bool(
            str(comentario.get("texto") or "").strip()
            or str(comentario.get("referencia") or "").strip()
        )

    def _span_indicador_comentario(self, clave):
        return ft.TextSpan(
            MARCADOR_COMENTARIO,
            tooltip="Ver comentario",
            style=ft.TextStyle(
                size=self._tamano_numero_lectura(),
                color=NARANJA_ACCENTO,
                weight=ft.FontWeight.BOLD,
            ),
            on_click=lambda e, destino=clave: self.dialog_comentario_biblia(destino),
        )

    def _boton_comentario_titulo(self, clave, tooltip):
        """Abre el mismo comentario para titulos, capitulos y subtitulos."""
        tiene_comentario = self._tiene_comentario(clave)
        return ft.IconButton(
            icon=(
                ft.Icons.CHAT_BUBBLE
                if tiene_comentario
                else ft.Icons.CHAT_BUBBLE_OUTLINE
            ),
            tooltip=tooltip,
            icon_size=16,
            icon_color=NARANJA_ACCENTO if tiene_comentario else "#8C8279",
            width=28,
            height=28,
            on_click=lambda e, destino=clave: self.dialog_comentario_biblia(destino),
        )

    def _span_boton_comentario_titulo(self, clave):
        tiene_comentario = self._tiene_comentario(clave)
        return ft.TextSpan(
            MARCADOR_COMENTARIO,
            tooltip=(
                "Ver comentario o referencia"
                if tiene_comentario
                else "Agregar comentario o referencia"
            ),
            style=ft.TextStyle(
                size=self._tamano_numero_lectura(),
                color=NARANJA_ACCENTO if tiene_comentario else "#8C8279",
                weight=ft.FontWeight.BOLD if tiene_comentario else None,
            ),
            on_click=lambda e, destino=clave: self.dialog_comentario_biblia(destino),
        )

    def _clave_subtitulo(self, libro, capitulo, indice_bloque):
        return f"SUB|{libro}|{capitulo}|{indice_bloque}"

    def _texto_subtitulo_comentario(self, libro, capitulo, indice_bloque):
        try:
            parrafos = BibliaService.obtener_parrafos(libro, int(capitulo))
            bloque = parrafos[int(indice_bloque)]
            texto = str(bloque.get("texto") or "").strip()
            return texto or "Subtitulo"
        except (IndexError, TypeError, ValueError, AttributeError):
            return "Subtitulo"

    def _referencia_comentario(self, clave):
        if str(clave).startswith("LIBRO|"):
            partes = str(clave).split("|", 1)
            return partes[1] if len(partes) == 2 else "Libro"

        if str(clave).startswith("CAP|"):
            partes = str(clave).split("|", 2)
            return f"{partes[1]} {partes[2]}" if len(partes) == 3 else "Capitulo"

        if str(clave).startswith("SUB|"):
            partes = str(clave).split("|", 3)
            if len(partes) == 4:
                texto = self._texto_subtitulo_comentario(partes[1], partes[2], partes[3])
                return f"{partes[1]} {partes[2]}: {texto}"
            return "Subtitulo"

        libro, capitulo, versiculo = self._desarmar_clave_verso(clave)
        if libro and capitulo and versiculo:
            return f"{libro} {capitulo}:{versiculo}"
        return "Comentario biblico"

    def _guardar_comentarios_biblia(self):
        try:
            guardar_comentarios(self.comentarios)
        except OSError:
            self._snack("No se pudo guardar el comentario.")

    def _refrescar_comentario_visible(self, clave):
        if str(clave).startswith(("LIBRO|", "CAP|", "SUB|")):
            self._refrescar_lectura_actual()
            return
        self._refrescar_lectura_colores({clave})

    def dialog_comentario_contextual(self):
        clave = self.verso_seleccionado or self.ultimo_verso_accionado
        if not clave:
            clave = self._clave_capitulo(self.libro_actual, self.capitulo_actual)
        self.dialog_comentario_biblia(clave)

    def dialog_comentario_biblia(self, clave):
        comentario = self.comentarios.get(clave, {})
        comentario = comentario if isinstance(comentario, dict) else {}
        puede_editar = not self._solo_lectura() and self._puede("biblia_marcas")
        campo_texto = ft.TextField(
            label="Comentario",
            value=str(comentario.get("texto") or ""),
            multiline=True,
            min_lines=3,
            max_lines=6,
            read_only=not puede_editar,
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
        )
        campo_referencia = ft.TextField(
            label="Referencia biblica opcional",
            hint_text="Juan 3:16",
            value=str(comentario.get("referencia") or ""),
            read_only=not puede_editar,
            on_tap_outside=lambda e: ocultar_teclado(self.page, e.control),
        )

        def cerrar(e=None):
            self._cerrar_dialogo_biblia(dialog)

        def guardar(e=None):
            texto = str(campo_texto.value or "").strip()
            referencia = str(campo_referencia.value or "").strip()
            if not texto and not referencia:
                self._snack("Escriba un comentario o una referencia.")
                return
            if referencia and not self._parsear_referencia(referencia):
                self._snack("La referencia no es valida. Ejemplo: Juan 3:16.")
                return
            self.comentarios[clave] = {"texto": texto, "referencia": referencia}
            self._guardar_comentarios_biblia()
            cerrar()
            self._refrescar_comentario_visible(clave)

        def eliminar(e=None):
            self.comentarios.pop(clave, None)
            self._guardar_comentarios_biblia()
            cerrar()
            self._refrescar_comentario_visible(clave)

        def ir_a_referencia_guardada(e=None):
            referencia = str(comentario.get("referencia") or "").strip()
            if not self._parsear_referencia(referencia):
                return
            cerrar()
            self._ir_a_referencia_texto(referencia)

        contenido = [campo_texto, campo_referencia]
        referencia_guardada = str(comentario.get("referencia") or "").strip()
        if referencia_guardada and self._parsear_referencia(referencia_guardada):
            contenido.append(
                ft.TextButton(
                    referencia_guardada,
                    icon=ft.Icons.OPEN_IN_NEW,
                    tooltip="Ir a esta referencia",
                    on_click=ir_a_referencia_guardada,
                )
            )

        acciones = [ft.TextButton("Cerrar" if not puede_editar else "Cancelar", on_click=cerrar)]
        if puede_editar and self._tiene_comentario(clave):
            acciones.append(ft.TextButton("Eliminar", on_click=eliminar))
        if puede_editar:
            acciones.append(
                ft.ElevatedButton("Guardar", icon=ft.Icons.SAVE, on_click=guardar)
            )

        dialog = ft.AlertDialog(
            modal=False,
            title=self._titulo_seccion(
                self._referencia_comentario(clave),
                ft.Icons.CHAT_BUBBLE_OUTLINE,
                NARANJA_ACCENTO,
            ),
            content=ft.Container(
                width=360 if self.responsive.is_mobile() else 480,
                content=ft.Column(tight=True, spacing=10, controls=contenido),
            ),
            actions=acciones,
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._abrir_dialogo_biblia(dialog)

    def dialog_ir_a_referencia(self, e=None):
        campo = ft.TextField(
            hint_text="Juan 3:16, Salmo 91, Génesis 1",
            prefix_icon=ft.Icons.MENU_BOOK,
            autofocus=True,
            dense=True,
            on_tap_outside=lambda ev: ocultar_teclado(self.page, ev.control),
        )

        def cerrar(dialog):
            self._cerrar_dialogo_biblia(dialog)

        def ir(dialog):
            texto = str(campo.value or "").strip()
            if not texto:
                self._snack("Escriba una referencia.")
                return
            cerrar(dialog)
            self._ir_a_referencia_texto(texto)

        dialog = ft.AlertDialog(
            modal=False,
            title=self._titulo_seccion("Ir a referencia", ft.Icons.MENU_BOOK, NARANJA_ACCENTO),
            content=ft.Container(
                width=360 if self.responsive.is_mobile() else 520,
                content=campo,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: cerrar(dialog)),
                ft.ElevatedButton("Ir", icon=ft.Icons.ARROW_FORWARD, on_click=lambda ev: ir(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        campo.on_submit = lambda ev: ir(dialog)
        self._abrir_dialogo_biblia(dialog)

    def on_enter(self):
        self.aviso_aceptado = False
        self._limpiar_seleccion_transitoria()

    def _precalentar_indice_busqueda(self):
        if self._indice_busqueda_programado:
            return
        self._indice_busqueda_programado = True
        try:
            self.page.run_task(self._construir_indice_busqueda_en_segundo_plano)
        except (RuntimeError, AssertionError, AttributeError):
            pass

    async def _construir_indice_busqueda_en_segundo_plano(self):
        try:
            await asyncio.to_thread(BibliaService.indice_busqueda)
        except Exception:
            self._indice_busqueda_programado = False

    def on_leave(self):
        self._limpiar_seleccion_transitoria()

    def _limpiar_seleccion_transitoria(self):
        """Descarta marcas pendientes antes de abandonar una lectura."""
        self._version_seleccion_resaltado += 1
        self.seleccion_texto_resaltado = None
        self.verso_seleccionado = None
        self.ultimo_verso_accionado = None
        self.objetivo_color = None
        self.objetivo_color_control = None
        self.objetivos_color.clear()
        self.versos_compartir.clear()
        self.modo_compartir_multiple = False

    def _perfil_responsivo_biblia(self):
        ancho = self.responsive.width()
        if ancho < 700:
            return "movil"
        if ancho < 820:
            return "compacto"
        return "amplio"

    def _on_resize(self, e):
        perfil = self._perfil_responsivo_biblia()
        if perfil == self._perfil_tamano_biblia:
            actualizar_barra = getattr(self.router, "_actualizar_barra_inferior", None)
            if callable(actualizar_barra):
                actualizar_barra()
            return

        # Durante el arrastre de la ventana se reciben muchos eventos. Solo la
        # ultima medida que se estabiliza reconstruye el marco responsivo.
        self._perfil_tamano_biblia = perfil
        self._version_redimension_biblia += 1
        version = self._version_redimension_biblia
        try:
            self.page.run_task(self._refrescar_despues_de_redimensionar, version)
        except (RuntimeError, AssertionError, AttributeError):
            self.router.refrescar()

    async def _refrescar_despues_de_redimensionar(self, version):
        await asyncio.sleep(0.18)
        if version != self._version_redimension_biblia:
            return
        self.router.refrescar()

    def obtener_vista(self):
        self.page.on_resize = self._on_resize
        self._perfil_tamano_biblia = self._perfil_responsivo_biblia()
        self._preparar_snack_biblia()
        self._precalentar_indice_busqueda()

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
                            bgcolor=ft.Colors.with_opacity(0.10, PURPURA_ACCENTO),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(ft.Icons.BOOK, size=38, color=PURPURA_ACCENTO),
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
                            bgcolor=PURPURA_ACCENTO,
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
                                bgcolor=ft.Colors.with_opacity(0.10, PURPURA_ACCENTO),
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(ft.Icons.MENU_BOOK, color=PURPURA_ACCENTO, size=30),
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
        puede_buscar = self._puede("biblia_buscar")
        puede_azar = self._puede("biblia_aleatorio")

        if self.responsive.width() < 820:
            return ft.Column(
                expand=True,
                spacing=8,
                controls=[
                    self._barra_compacta_lectura(puede_buscar, puede_azar),
                    ft.Container(expand=True, content=lectura),
                ],
            )

        return ft.Row(
            expand=True,
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                self._riel_lateral_navegacion(puede_buscar, puede_azar),
                ft.Container(expand=True, content=lectura),
                self._riel_lateral_resaltado(),
            ],
        )

    def _barra_compacta_lectura(self, puede_buscar, puede_azar):
        botones = [
            self._boton_lateral(ft.Icons.ARROW_BACK, "Volver", lambda e: self.volver_lectura()),
            self._boton_lateral(ft.Icons.MENU_BOOK, "Ir a referencia", self.dialog_ir_a_referencia),
        ]
        if puede_buscar:
            botones.append(self._boton_lateral(ft.Icons.SEARCH, "Buscar", self.dialog_busqueda))
        if puede_azar:
            botones.append(self._boton_lateral(ft.Icons.AUTO_AWESOME, "Aleatorio", self.dialog_versiculo_random))
        botones.extend(
            [
                self._boton_lateral(ft.Icons.ZOOM_IN, "Aumentar letra", lambda e: self.cambiar_tamano_fuente_lectura(1)),
                self._boton_lateral(ft.Icons.ZOOM_OUT, "Achicar letra", lambda e: self.cambiar_tamano_fuente_lectura(-1)),
                self._boton_lateral(ft.Icons.PIN, "Codificar secciones en numeros", lambda e: self.dialog_exportar_biblia_codificada(), color=PURPURA_ACCENTO),
                self._boton_lateral(ft.Icons.CHAT_BUBBLE_OUTLINE, "Agregar o ver comentario", lambda e: self.dialog_comentario_contextual(), color=NARANJA_ACCENTO),
            ]
        )
        return ft.Container(
            padding=ft.Padding(left=6, top=4, right=6, bottom=4),
            bgcolor=ft.Colors.with_opacity(0.82, ft.Colors.WHITE),
            border=ft.Border.all(1, BORDE_SUAVE),
            border_radius=12,
            content=ft.Row(wrap=True, spacing=2, run_spacing=2, controls=botones),
        )

    def _boton_lateral(self, icono, ayuda, on_click, color=TEXTO_SECUNDARIO, activo=False):
        return ft.IconButton(
            icon=icono,
            tooltip=ayuda,
            width=42,
            height=42,
            icon_color=NARANJA_ACCENTO if activo else color,
            bgcolor=MARRON_PERLA if activo else None,
            on_click=on_click,
        )

    def _riel_lateral_navegacion(self, puede_buscar, puede_azar):
        botones = [
            self._boton_lateral(
                ft.Icons.ARROW_BACK,
                "Volver",
                lambda e: self.volver_lectura(),
                activo=self.modo_vista in ("Capitulos", "Libro", "Versiculos"),
            ),
            self._boton_lateral(ft.Icons.MENU_BOOK, "Ir a referencia", self.dialog_ir_a_referencia),
        ]

        if puede_buscar:
            botones.append(
                self._boton_lateral(ft.Icons.SEARCH, "Buscar", self.dialog_busqueda)
            )

        if puede_azar:
            botones.append(
                self._boton_lateral(ft.Icons.AUTO_AWESOME, "Aleatorio", self.dialog_versiculo_random)
            )

        if self.libro_actual and self.modo_vista == "Capitulos":
            botones.append(
                self._boton_lateral(
                    ft.Icons.ARTICLE,
                    "Leer libro completo",
                    lambda e: self.ir_a_libro_completo(self.libro_actual),
                )
            )

        return ft.Container(
            width=48,
            padding=ft.Padding(left=3, top=4, right=3, bottom=4),
            bgcolor=ft.Colors.with_opacity(0.70, ft.Colors.WHITE),
            border=ft.Border.all(1, BORDE_SUAVE),
            border_radius=14,
            content=ft.Column(
                tight=True,
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=botones,
            ),
        )

    def _riel_lateral_resaltado(self):
        puede_color = self._puede("biblia_color") and not self._solo_lectura()
        puede_marcas = self._puede("biblia_marcas")
        puede_cordero = self._puede("biblia_cordero")
        puede_diccionario = self._puede("biblia_diccionario_hebreo")

        botones = [
            self._boton_lateral(ft.Icons.ZOOM_IN, "Aumentar letra", lambda e: self.cambiar_tamano_fuente_lectura(1)),
            self._boton_lateral(ft.Icons.ZOOM_OUT, "Achicar letra", lambda e: self.cambiar_tamano_fuente_lectura(-1)),
        ]

        if puede_marcas:
            botones.append(
                self._boton_lateral(
                    ft.Icons.CHAT_BUBBLE_OUTLINE,
                    "Agregar o ver comentario",
                    lambda e: self.dialog_comentario_contextual(),
                    color=NARANJA_ACCENTO,
                )
            )

        self._boton_seleccion_multiple_control = None
        botones.append(
            self._boton_lateral(
                ft.Icons.PIN,
                "Codificar secciones en numeros",
                lambda e: self.dialog_exportar_biblia_codificada(),
                color=PURPURA_ACCENTO,
            )
        )
        if puede_diccionario:
            botones.append(self._boton_lateral(ft.Icons.MENU_BOOK, "Diccionario hebreo", lambda e: self.dialog_diccionario_hebreo(), color=PURPURA_ACCENTO))
        if puede_cordero:
            botones.append(self._boton_lateral(ft.Icons.RECORD_VOICE_OVER, "Palabras del Cordero", lambda e: self.dialog_palabras_cordero(), color=COLOR_PALABRAS_CORDERO))
        if puede_marcas:
            botones.append(self._boton_lateral(ft.Icons.FILTER_ALT, "Ver resaltados", lambda e: self.dialog_versiculos_por_color(), color=VERDE_ACCENTO))

        return ft.Container(
            width=48,
            padding=ft.Padding(left=3, top=4, right=3, bottom=4),
            bgcolor=ft.Colors.with_opacity(0.70, ft.Colors.WHITE),
            border=ft.Border.all(1, BORDE_SUAVE),
            border_radius=14,
            content=ft.Column(
                tight=True,
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=botones,
            ),
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

    def _libros_random_categoria(self, categoria):
        categoria = categoria or "General"
        cache = getattr(self, "_random_candidatos_cache", None)

        if cache is None:
            self._random_candidatos_cache = {}
            cache = self._random_candidatos_cache

        if categoria in cache:
            return cache[categoria]

        libros = [
            libro
            for libro in self.libros or []
            if self._libro_pertenece_categoria_random(libro.get("nombre", ""), categoria)
            and libro.get("capitulos")
        ]
        cache[categoria] = libros
        return libros

    def _obtener_versiculo_random(self):
        categoria = getattr(self, "categoria_random", "General") or "General"
        libros = self._libros_random_categoria(categoria)

        if not libros and categoria != "General":
            libros = self._libros_random_categoria("General")

        if not libros:
            return "Sin versiculo", "No hay texto biblico cargado."

        usados_por_categoria = getattr(self, "_random_usados_por_categoria", None)
        if usados_por_categoria is None:
            self._random_usados_por_categoria = {}
            usados_por_categoria = self._random_usados_por_categoria

        usados = usados_por_categoria.setdefault(categoria, set())
        elegido = None

        # Elegir directamente un libro, capitulo y versiculo evita crear una
        # lista de los mas de 31 mil versiculos cada vez que se abre Biblia.
        for _ in range(24):
            libro = random.choice(libros)
            capitulos = libro.get("capitulos", [])
            capitulo_numero = random.randrange(1, len(capitulos) + 1)
            capitulo = capitulos[capitulo_numero - 1]
            if not capitulo:
                continue
            versiculo_numero = random.randrange(1, len(capitulo) + 1)
            texto = str(capitulo[versiculo_numero - 1] or "").strip()
            if not texto:
                continue
            referencia = f"{libro['nombre']} {capitulo_numero}:{versiculo_numero}"
            elegido = (referencia, texto)
            if referencia not in usados:
                break

        if elegido is None:
            return "Sin versiculo", "No hay texto biblico cargado."

        if elegido[0] in usados and len(usados) >= 24:
            usados.clear()
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
                ft.Colors.with_opacity(0.14, PURPURA_ACCENTO)
                if seleccionado
                else ft.Colors.WHITE
            ),
            border=ft.Border.all(
                1.2,
                PURPURA_ACCENTO if seleccionado else BORDE_SUAVE,
            ),
            content=ft.Text(
                categoria,
                size=12,
                weight=ft.FontWeight.BOLD if seleccionado else None,
                color=PURPURA_ACCENTO if seleccionado else TEXTO_SECUNDARIO,
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
        self._snack("Copiado correctamente")

    def ir_a_versiculo_random(self, e=None):
        referencia = str(getattr(self, "versiculo_random_referencia", "") or "").strip()

        if not referencia:
            self._snack("No hay versiculo random para abrir.")
            return

        if hasattr(self, "referencia_rapida"):
            self.referencia_rapida.value = referencia

        self._ir_a_referencia_texto(referencia)

    def dialog_versiculo_random(self, e=None):
        if not self.versiculo_random_texto:
            self._generar_versiculo_random_inicial()

        categoria = ft.Dropdown(
            label="Categoría",
            value=self.categoria_random,
            options=[ft.dropdown.Option(c) for c in CATEGORIAS_RANDOM_BIBLIA],
            dense=True,
        )
        categoria_texto = ft.Text(
            self.categoria_random.upper(),
            size=11,
            weight=ft.FontWeight.BOLD,
            color=TEXTO_SECUNDARIO,
        )
        referencia_texto = ft.Text(
            self.versiculo_random_referencia,
            size=16,
            weight=ft.FontWeight.BOLD,
            color=TEXTO_PRINCIPAL,
        )
        versiculo_texto = ft.Text(
            self.versiculo_random_texto,
            size=15,
            color=TEXTO_PRINCIPAL,
            selectable=True,
        )

        def cerrar(dialog):
            self._cerrar_dialogo_biblia(dialog)

        def refrescar_local(e=None):
            referencia, texto = self._obtener_versiculo_random()
            self.versiculo_random_referencia = referencia
            self.versiculo_random_texto = texto
            categoria_texto.value = self.categoria_random.upper()
            referencia_texto.value = referencia
            versiculo_texto.value = texto
            self.page.update(categoria_texto, referencia_texto, versiculo_texto)

        def cambiar_categoria(e):
            self.categoria_random = e.control.value or "General"
            refrescar_local()

        def ver_en_lectura(dialog):
            cerrar(dialog)
            self.ir_a_versiculo_random()

        categoria.on_change = cambiar_categoria

        dialog = ft.AlertDialog(
            modal=False,
            title=self._titulo_seccion("Versiculo random", ft.Icons.AUTO_AWESOME, PURPURA_ACCENTO),
            content=ft.Container(
                width=360 if self.responsive.is_mobile() else 560,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    controls=[
                        categoria,
                        ft.Container(
                            padding=16,
                            border_radius=18,
                            bgcolor=ft.Colors.with_opacity(0.06, AZUL_ACCENTO),
                            border=ft.Border.all(1, ft.Colors.with_opacity(0.18, AZUL_ACCENTO)),
                            content=ft.Column(
                                tight=True,
                                spacing=8,
                                controls=[
                                    categoria_texto,
                                    referencia_texto,
                                    versiculo_texto,
                                ],
                            ),
                        ),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Ver", icon=ft.Icons.OPEN_IN_NEW, on_click=lambda ev: ver_en_lectura(dialog)),
                ft.ElevatedButton("Nuevo", icon=ft.Icons.REFRESH, on_click=refrescar_local),
                ft.TextButton("Cerrar", on_click=lambda ev: cerrar(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._abrir_dialogo_biblia(dialog)

    def _panel_versiculo_random(self):
        if not self.versiculo_random_texto:
            self._generar_versiculo_random_inicial()

        return self._tarjeta_moderna(
            padding=18,
            content=ft.Column(
                tight=True,
                spacing=14,
                controls=[
                    self._titulo_seccion("Versiculo random", ft.Icons.AUTO_AWESOME, PURPURA_ACCENTO),
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

        controles_lectura = [
            ft.Container(
                expand=True,
                padding=ft.Padding(left=4, top=4, right=4, bottom=4),
                content=self.panel_lectura,
            ),
        ]

        return self._tarjeta_moderna(
            expand=True,
            padding=12 if self.responsive.is_mobile() else 22,
            content=ft.Column(
                expand=True,
                spacing=0,
                controls=controles_lectura,
            ),
        )

    def _barra_navegacion_rapida(self, controles):
        return ft.Container(
            height=58,
            margin=ft.Margin(left=0, top=10, right=0, bottom=2),
            padding=ft.Padding(left=4, top=4, right=4, bottom=8),
            bgcolor=GRIS_SUAVE,
            border=ft.Border.all(1, BORDE_SUAVE),
            border_radius=8,
            content=ft.ListView(
                expand=True,
                horizontal=True,
                spacing=6,
                # El espacio inferior es exclusivo para el scrollbar y evita
                # que se superponga con los chips de navegacion.
                padding=ft.Padding(left=2, top=0, right=2, bottom=8),
                build_controls_on_demand=True,
                cache_extent=120,
                scroll=ft.Scrollbar(
                    thickness=5,
                    radius=3,
                    interactive=True,
                    orientation=ft.ScrollbarOrientation.BOTTOM,
                ),
                controls=controles,
            ),
        )

    def _chip_navegacion_rapida(
        self,
        texto,
        seleccionado,
        on_tap,
        ancho=None,
        clave_desplazamiento=None,
    ):
        return ft.GestureDetector(
            key=clave_desplazamiento,
            mouse_cursor=ft.MouseCursor.CLICK,
            on_tap=on_tap,
            content=ft.Container(
                width=ancho,
                height=34,
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding(left=12, top=0, right=12, bottom=0),
                bgcolor=MARRON_PERLA if seleccionado else ft.Colors.WHITE,
                border=ft.Border.all(
                    2 if seleccionado else 1,
                    MARRON_ACENTO if seleccionado else BORDE_SUAVE,
                ),
                border_radius=8,
                content=ft.Text(
                    texto,
                    size=12,
                    weight=ft.FontWeight.BOLD if seleccionado else ft.FontWeight.W_500,
                    color=TEXTO_PRINCIPAL,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ),
        )

    def _barra_rapida_libros(self):
        barra = self._barra_navegacion_rapida(
            [
                self._chip_navegacion_rapida(
                    libro["nombre"],
                    libro["nombre"] == self.libro_actual,
                    lambda e, nombre=libro["nombre"]: self._ir_a_libro_desde_barra(nombre),
                    ancho=min(148, max(82, len(libro["nombre"]) * 8 + 28)),
                    clave_desplazamiento=self._clave_desplazamiento_libro(libro["nombre"]),
                )
                for libro in self.libros
            ]
        )
        self._lista_barra_libros = barra.content
        return barra

    def _clave_desplazamiento_libro(self, nombre):
        return f"barra-libro-{self._normalizar_texto_busqueda(nombre).replace(' ', '-')}"

    def _ir_a_libro_desde_barra(self, nombre):
        if nombre == self.libro_actual and self.modo_vista == "Libro":
            return
        self._libro_barra_pendiente = nombre
        self.ir_a_libro_completo(nombre)

    def _programar_desplazamiento_barra_libros(self):
        nombre = self._libro_barra_pendiente
        if not nombre:
            return
        self._libro_barra_pendiente = None
        try:
            self.page.run_task(self._desplazar_barra_libros_a_seleccion, nombre)
        except (RuntimeError, AssertionError, AttributeError):
            pass

    async def _desplazar_barra_libros_a_seleccion(self, nombre):
        # La barra se crea durante el refresco; cedemos un ciclo para que Flet la monte.
        await asyncio.sleep(0.03)
        lista = self._lista_barra_libros
        if lista is None:
            return
        try:
            await lista.scroll_to(
                scroll_key=self._clave_desplazamiento_libro(nombre),
                duration=180,
            )
        except (RuntimeError, AssertionError, AttributeError):
            return

    def _barra_rapida_capitulos(self):
        libro = self._libro_actual()
        if not libro:
            return ft.Container(visible=False, height=0)

        return self._barra_navegacion_rapida(
            [
                self._chip_navegacion_rapida(
                    str(numero),
                    numero == self.capitulo_actual,
                    lambda e, capitulo=numero: self._ir_a_capitulo_desde_barra(capitulo),
                    ancho=42 if numero < 10 else 50,
                )
                for numero in range(1, len(libro.get("capitulos", [])) + 1)
            ]
        )

    def _ir_a_capitulo_desde_barra(self, capitulo):
        if capitulo == self.capitulo_actual:
            return
        self.cambiar_capitulo_valor(capitulo)

    def _navegacion_lectura(self):
        puede_volver = self.modo_vista in ("Capitulos", "Libro", "Versiculos")

        if self.modo_vista == "Versiculos":
            titulo = f"{self.libro_actual} {self.capitulo_actual}"
        elif self.modo_vista == "Libro":
            titulo = f"{self.libro_actual}: libro completo"
        elif self.modo_vista == "Capitulos":
            titulo = self.libro_actual or "Capitulos"
        else:
            titulo = "Libros"

        if self.responsive.is_mobile() and not puede_volver:
            return ft.Container(visible=False, height=0)

        if self.responsive.is_mobile():
            return ft.Row(
                tight=True,
                spacing=2,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        tooltip="Volver",
                        icon_color=TEXTO_SECUNDARIO,
                        on_click=lambda e: self.volver_lectura(),
                    ),
                    ft.Text(
                        titulo,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=TEXTO_PRINCIPAL,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
            )

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
            padding=18,
            content=ft.Column(
                tight=True,
                spacing=14,
                controls=[
                    self._titulo_seccion("Buscar", ft.Icons.SEARCH, AZUL_ACCENTO),
                    ft.Text(
                        "Abra una busqueda completa para revisar resultados por libro o todos juntos.",
                        size=12,
                        color=TEXTO_SECUNDARIO,
                    ),
                    ft.ElevatedButton(
                        "Buscar",
                        icon=ft.Icons.SEARCH,
                        on_click=self.dialog_busqueda,
                    ),
                ],
            ),
        )

    def dialog_busqueda(self, e=None):
        """Abre un cuadro compacto; los resultados se crean en otro dialogo.

        Evitar mutar controles dentro de un AlertDialog abierto previene que Flet
        conserve una superficie vacia de ListView antes de una busqueda.
        """
        if not self._puede("biblia_buscar"):
            self._snack("La busqueda requiere el Nivel 2.")
            return
        ancho = 350 if self.responsive.is_mobile() else 560
        campo = ft.TextField(
            label="Buscar en toda la Biblia",
            prefix_icon=ft.Icons.SEARCH,
            autofocus=True,
            expand=True,
            always_call_on_tap=True,
            on_click=lambda ev: campo.focus(),
            on_tap_outside=lambda ev: ocultar_teclado(self.page, ev.control),
        )
        modo = ft.Dropdown(
            label="Vista de resultados",
            value="Por libros",
            width=180,
            options=[
                ft.dropdown.Option("Por libros"),
                ft.dropdown.Option("Todos juntos"),
            ],
        )

        def crear_flotante_busqueda(titulo, contenido, ancho_modal, al_cerrar):
            """Flotante con fondo clickeable y cuadro central independiente."""
            ancho_pagina = getattr(self.page, "width", None) or 760
            alto_pagina = getattr(self.page, "height", None) or 720
            fondo = ft.GestureDetector(
                on_tap=lambda ev: al_cerrar(),
                content=ft.Container(
                    width=ancho_pagina,
                    height=alto_pagina,
                    bgcolor=ft.Colors.with_opacity(0.62, ft.Colors.BLACK),
                ),
            )
            cuadro = ft.Container(
                width=min(ancho_modal, max(300, ancho_pagina - 32)),
                padding=ft.Padding(24, 22, 24, 20),
                border_radius=24,
                bgcolor=PERLA_PANEL,
                shadow=sombra_suave(),
                content=ft.Column(
                    tight=True,
                    spacing=14,
                    controls=[
                        ft.Text(
                            titulo,
                            size=24,
                            weight=ft.FontWeight.W_500,
                            color=TEXTO_PRINCIPAL,
                        ),
                        contenido,
                    ],
                ),
            )
            return ft.Stack(
                data="biblia_flotante",
                width=ancho_pagina,
                height=alto_pagina,
                alignment=ft.Alignment(0, 0),
                controls=[fondo, cuadro],
            )

        def cerrar_dialogo(dialogo):
            self._cerrar_flotante_biblia(dialogo)

        def abrir_resultados(resultados, vista):
            alto_pagina = getattr(self.page, "height", None)
            if alto_pagina is None and hasattr(self.page, "window"):
                alto_pagina = getattr(self.page.window, "height", None)
            if self.responsive.is_mobile():
                alto_lista = max(220, min(330, int((alto_pagina or 720) - 330)))
            else:
                alto_lista = max(260, min(510, int((alto_pagina or 760) - 265)))
            lista = ft.ListView(
                height=alto_lista,
                spacing=7,
                padding=ft.Padding(left=0, top=0, right=8, bottom=0),
            )
            estado_resultados = {
                "limite": 30,
                "libros_abiertos": {},
            }
            conteo_libros = {}
            for resultado in resultados:
                libro = resultado.get("libro", "")
                if libro:
                    conteo_libros[libro] = conteo_libros.get(libro, 0) + 1
            libros_encontrados = ", ".join(
                f"{libro} ({cantidad})"
                for libro, cantidad in conteo_libros.items()
            )

            dialogo_resultados_ref = {"control": None}

            def cerrar_resultados(ev=None):
                cerrar_dialogo(dialogo_resultados_ref["control"])

            def abrir_resultado(resultado):
                cerrar_resultados()
                self.ir_a_resultado(resultado)

            resumen_resultados = ft.Text(
                size=12,
                color=TEXTO_SECUNDARIO,
            )

            def renderizar_resultados():
                """Muestra resultados por tramos para no sobrecargar la ventana."""
                limite = min(estado_resultados["limite"], len(resultados))
                visibles = resultados[:limite]
                lista.controls.clear()

                if vista == "Por libros":
                    for titulo, grupo in self._grupos_resultados_busqueda(visibles):
                        clave_grupo = titulo.rsplit(" (", 1)[0]
                        abierto = estado_resultados["libros_abiertos"].setdefault(clave_grupo, True)
                        cuerpo = ft.Container(
                            visible=abierto,
                            padding=ft.Padding(left=4, top=2, right=0, bottom=6),
                            content=ft.Column(
                                spacing=7,
                                controls=[
                                    self._control_resultado_busqueda(
                                        resultado,
                                        al_abrir=lambda r=resultado: abrir_resultado(r),
                                    )
                                    for resultado in grupo
                                ],
                            ),
                        )
                        icono = ft.Icon(
                            ft.Icons.KEYBOARD_ARROW_DOWN if abierto else ft.Icons.KEYBOARD_ARROW_RIGHT,
                            color=PURPURA_ACCENTO,
                            size=20,
                        )

                        def alternar_grupo(ev, clave=clave_grupo, contenido=cuerpo, indicador=icono):
                            nuevo_estado = not estado_resultados["libros_abiertos"].get(clave, True)
                            estado_resultados["libros_abiertos"][clave] = nuevo_estado
                            contenido.visible = nuevo_estado
                            indicador.name = (
                                ft.Icons.KEYBOARD_ARROW_DOWN
                                if nuevo_estado
                                else ft.Icons.KEYBOARD_ARROW_RIGHT
                            )
                            lista.update()

                        lista.controls.extend([
                            ft.GestureDetector(
                                on_tap=alternar_grupo,
                                content=ft.Container(
                                    padding=ft.Padding(left=8, top=8, right=8, bottom=8),
                                    border_radius=8,
                                    bgcolor="#F7F0FA",
                                    content=ft.Row(
                                        spacing=6,
                                        controls=[
                                            icono,
                                            ft.Text(
                                                titulo,
                                                size=12,
                                                weight=ft.FontWeight.BOLD,
                                                color=PURPURA_ACCENTO,
                                            ),
                                        ],
                                    ),
                                ),
                            ),
                            cuerpo,
                        ])
                else:
                    lista.controls.extend(
                        self._control_resultado_busqueda(
                            resultado,
                            al_abrir=lambda r=resultado: abrir_resultado(r),
                        )
                        for resultado in visibles
                    )

                resumen_resultados.value = (
                    f"Mostrando {limite} de {len(resultados)} resultados."
                )
                if limite < len(resultados):
                    lista.controls.append(
                        ft.Container(
                            alignment=ft.Alignment(0, 0),
                            padding=ft.Padding(top=6, bottom=4),
                            content=ft.OutlinedButton(
                                "Ver 30 mas",
                                icon=ft.Icons.ADD,
                                on_click=lambda ev: cargar_mas(),
                            ),
                        )
                    )
                if lista.page:
                    lista.update()

            def cargar_mas():
                estado_resultados["limite"] += 30
                renderizar_resultados()

            contenido = ft.Column(
                width=ancho,
                tight=True,
                spacing=10,
                controls=[
                    resumen_resultados,
                    ft.Text(
                        f"Libros: {libros_encontrados}",
                        size=11,
                        color=PURPURA_ACCENTO,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.END,
                        spacing=8,
                        controls=[
                            ft.ElevatedButton(
                                "Guardar",
                                icon=ft.Icons.SAVE_ALT,
                                on_click=self.guardar_busqueda,
                            ),
                            ft.TextButton("Cerrar", on_click=cerrar_resultados),
                        ],
                    ),
                    ft.Container(
                        height=alto_lista + 16,
                        padding=8,
                        border=ft.Border.all(1, BORDE_SUAVE),
                        border_radius=12,
                        bgcolor="#FFFFFF",
                        content=lista,
                    ),
                ],
            )
            dialogo_resultados = crear_flotante_busqueda(
                "Resultados de la busqueda", contenido, ancho + 48, cerrar_resultados
            )
            dialogo_resultados_ref["control"] = dialogo_resultados
            self.page.overlay.append(dialogo_resultados)
            self.page.update()
            # La lista debe pertenecer primero al flotante y a la pagina. En
            # Flet Web, actualizarla antes de este punto provoca el error
            # "Control must be added to the page first".
            renderizar_resultados()

        def ejecutar_busqueda(ev=None):
            termino = (campo.value or "").strip()
            if not termino:
                self._snack("Escriba una palabra para buscar.")
                return

            try:
                resultados = buscar_texto(
                    self.libros or [],
                    termino,
                    indice=BibliaService.indice_busqueda(),
                )
            except Exception:
                self._snack("No se pudo realizar la busqueda. Intente nuevamente.")
                return

            ocultar_teclado(self.page, campo)
            self.ultima_busqueda_texto = termino
            self.ultimos_resultados_busqueda = resultados
            cerrar_busqueda()
            if not self.ultimos_resultados_busqueda:
                self._snack("No se encontraron resultados para esta busqueda.")
                return
            abrir_resultados(
                self.ultimos_resultados_busqueda,
                modo.value or "Por libros",
            )

        campo.on_submit = ejecutar_busqueda
        contenido_busqueda = ft.Column(
            width=ancho,
            tight=True,
            spacing=10,
            controls=[
                campo,
                ft.Row(
                    wrap=True,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        modo,
                        ft.ElevatedButton(
                            "Buscar",
                            icon=ft.Icons.SEARCH,
                            on_click=ejecutar_busqueda,
                        ),
                        ft.TextButton(
                            "Cancelar",
                            on_click=lambda ev: cerrar_busqueda(),
                        ),
                    ],
                ),
            ],
        )
        dialogo_busqueda_ref = {"control": None}

        def cerrar_busqueda(ev=None):
            self._cerrar_flotante_biblia(dialogo_busqueda_ref["control"])

        dialogo_busqueda = crear_flotante_busqueda(
            "Buscar", contenido_busqueda, ancho + 48, cerrar_busqueda
        )
        dialogo_busqueda_ref["control"] = dialogo_busqueda
        self.page.overlay.append(dialogo_busqueda)
        self.page.update()

    def dialog_palabras_cordero(self, e=None):
        if not self._puede("biblia_cordero"):
            self._snack("Las palabras del Cordero requieren el Nivel 3.")
            return
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
            self._cerrar_dialogo_biblia(dialog)

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
        if self._solo_lectura():
            return ft.Container()

        movil = self.responsive.is_mobile()
        puede_color = self._puede("biblia_color")
        puede_marcas = self._puede("biblia_marcas")
        puede_cordero = self._puede("biblia_cordero")
        puede_diccionario = self._puede("biblia_diccionario_hebreo")

        def accion(icono, ayuda, color, callback):
            return ft.IconButton(
                icon=icono,
                tooltip=ayuda,
                icon_color=color,
                icon_size=20 if movil else 24,
                on_click=lambda e: callback(),
            )

        def crear_acciones_principales():
            return [
                accion(ft.Icons.PIN, "Codificar secciones en numeros", PURPURA_ACCENTO, self.dialog_exportar_biblia_codificada),
                accion(ft.Icons.CHAT_BUBBLE_OUTLINE, "Agregar o ver comentario", NARANJA_ACCENTO, self.dialog_comentario_contextual),
            ]

        def crear_menu_extra():
            items = []
            if puede_diccionario:
                items.append(ft.PopupMenuItem(content="Diccionario hebreo", icon=ft.Icons.MENU_BOOK, on_click=lambda e: self.dialog_diccionario_hebreo()))
            if puede_cordero:
                items.append(ft.PopupMenuItem(content="Palabras del Cordero", icon=ft.Icons.RECORD_VOICE_OVER, on_click=lambda e: self.dialog_palabras_cordero()))
            if puede_marcas:
                items.append(ft.PopupMenuItem(content="Ver resaltados", icon=ft.Icons.FILTER_ALT, on_click=lambda e: self.dialog_versiculos_por_color()))
            if not items:
                return None
            return ft.PopupMenuButton(
                icon=ft.Icons.MORE_VERT,
                icon_color=TEXTO_SECUNDARIO,
                tooltip="Mas acciones",
                items=items,
            )


        if movil:
            acciones_movil = [
                accion(ft.Icons.PIN, "Codificar secciones en numeros", PURPURA_ACCENTO, self.dialog_exportar_biblia_codificada),
            ]
            menu_extra = crear_menu_extra()
            if menu_extra is not None:
                acciones_movil.append(menu_extra)
            return ft.Container(
                padding=ft.Padding(left=10, top=8, right=10, bottom=7),
                bgcolor=ft.Colors.with_opacity(0.45, ft.Colors.WHITE),
                border=ft.Border.all(1, BORDE_SUAVE),
                border_radius=14,
                content=ft.Column(
                    tight=True,
                    spacing=5,
                    controls=[ft.Row(tight=True, spacing=2, controls=acciones_movil)],
                ),
            )

        acciones = crear_acciones_principales()
        if puede_diccionario:
            acciones.append(accion(ft.Icons.MENU_BOOK, "Diccionario hebreo", PURPURA_ACCENTO, self.dialog_diccionario_hebreo))
        if puede_cordero:
            acciones.append(accion(ft.Icons.RECORD_VOICE_OVER, "Ver palabras del Cordero", COLOR_PALABRAS_CORDERO, self.dialog_palabras_cordero))
        if puede_marcas:
            acciones.append(accion(ft.Icons.FILTER_ALT, "Ver resaltados", VERDE_ACCENTO, self.dialog_versiculos_por_color))
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
                controls=acciones,
            ),
        )

    def _guardar_seleccion_texto_resaltado(self, evento, libro_nombre, capitulo_numero):
        seleccion = self._seleccion_final_del_evento(evento)
        if seleccion is None:
            self.seleccion_texto_resaltado = None
            self._version_seleccion_resaltado += 1
            self._cerrar_selector_color_contextual()
            return

        verso, texto = seleccion
        self.seleccion_texto_resaltado = {"verso": verso, "texto": texto}
        self.verso_seleccionado = verso
        self.ultimo_verso_accionado = verso
        self._programar_selector_color_contextual()

    def _seleccion_final_del_evento(self, evento):
        """Acepta solo el rango final contenido por completo en un versiculo."""
        control = getattr(evento, "control", None)
        seleccion = getattr(evento, "selection", None)
        rangos = self._rangos_seleccion_lectura.get(id(control), ())
        if seleccion is None or not rangos:
            return None

        try:
            inicio = min(int(seleccion.base_offset), int(seleccion.extent_offset))
            fin = max(int(seleccion.base_offset), int(seleccion.extent_offset))
        except (AttributeError, TypeError, ValueError):
            return None

        if inicio >= fin:
            return None

        for rango in rangos:
            if inicio < rango["inicio"] or fin > rango["fin"]:
                continue
            texto = rango["texto"][inicio - rango["inicio"] : fin - rango["inicio"]].strip()
            if texto:
                return rango["verso"], texto
        return None

    def _programar_selector_color_contextual(self, objetivos=None):
        if self._solo_lectura() or not self._puede("biblia_color"):
            return

        self._version_seleccion_resaltado += 1
        version = self._version_seleccion_resaltado
        objetivos_programados = None if objetivos is None else set(objetivos)
        try:
            self.page.run_task(
                self._mostrar_selector_color_contextual_diferido,
                version,
                objetivos_programados,
            )
        except (RuntimeError, AssertionError, AttributeError):
            self._mostrar_selector_color_contextual(objetivos_programados)

    async def _mostrar_selector_color_contextual_diferido(self, version, objetivos):
        await asyncio.sleep(ESPERA_SELECTOR_COLOR_TEXTO)
        if version != self._version_seleccion_resaltado:
            return
        self._mostrar_selector_color_contextual(objetivos)

    def _mostrar_selector_color_contextual(self, objetivos=None):
        if self._solo_lectura() or not self._puede("biblia_color"):
            return

        hay_texto = objetivos is None and isinstance(self.seleccion_texto_resaltado, dict)
        objetivos = (
            set()
            if hay_texto
            else set(objetivos or self._objetivos_color_activos())
        )
        if not hay_texto and not objetivos:
            return

        if objetivos:
            self.objetivos_color = set(objetivos)
            self.objetivo_color = next(iter(objetivos), None)

        self._cerrar_selector_color_contextual()

        def cerrar(e=None):
            self._cerrar_selector_color_contextual()

        def aplicar(nombre):
            def _aplicar(e=None):
                self.color_actual = self._normalizar_color(nombre)
                cerrar()
                if hay_texto:
                    self._resaltar_seleccion_texto_actual()
                else:
                    self.seleccionar_color(self.color_actual)
            return _aplicar

        def despintar(e=None):
            cerrar()
            if hay_texto:
                self._quitar_resaltado_seleccion_texto_actual()
            else:
                self._quitar_colores_seleccionados(objetivos)

        muestras = [
            ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK,
                on_tap=aplicar(nombre),
                content=ft.Container(
                    width=42,
                    height=42,
                    border_radius=21,
                    bgcolor=color,
                    tooltip=nombre,
                    border=ft.Border.all(
                        2 if nombre == self.color_actual else 1,
                        BORDER_MARRON if self._es_blanco_borde(nombre) else TEXTO_PRINCIPAL,
                    ),
                ),
            )
            for nombre, color in COLORES_RESALTADO.items()
        ]

        dialog = ft.AlertDialog(
            modal=False,
            title=ft.Text("Pintar o despintar"),
            content=ft.Container(
                width=360,
                content=ft.Column(
                    tight=True,
                    spacing=10,
                    controls=[
                        ft.Text("Elija el color para la seleccion.", size=12, color=TEXTO_SECUNDARIO),
                        ft.Row(wrap=True, spacing=8, run_spacing=8, controls=muestras),
                    ],
                ),
            ),
            actions=[
                ft.OutlinedButton("Despintar", icon=ft.Icons.FORMAT_COLOR_RESET, on_click=despintar),
                ft.TextButton("Cancelar", on_click=cerrar),
            ],
        )
        self._dialog_color_contextual = dialog
        self._abrir_dialogo_biblia(dialog)

    def _cerrar_selector_color_contextual(self):
        dialog = self._dialog_color_contextual
        self._dialog_color_contextual = None
        if dialog is None:
            return
        try:
            if hasattr(self.page, "close"):
                self.page.close(dialog)
            else:
                self._cerrar_dialogo_biblia(dialog)
        except Exception:
            self._cerrar_dialogo_biblia(dialog)
        try:
            while dialog in self.page.overlay:
                self.page.overlay.remove(dialog)
        except Exception:
            pass

    def _resaltar_seleccion_texto_actual(self):
        seleccion = self.seleccion_texto_resaltado
        if not isinstance(seleccion, dict):
            return False

        verso = seleccion.get("verso")
        texto = str(seleccion.get("texto") or "").strip()
        if not verso or not texto:
            return False

        clave = self._clave_resaltado_palabras(verso)
        actuales = [
            item
            for item in self._resaltados_palabras_verso(verso)
            if self._normalizar_texto_busqueda(item.get("texto")) != self._normalizar_texto_busqueda(texto)
        ]
        actuales.append({"texto": texto, "color": self.color_actual})
        self.resaltados[clave] = actuales
        self._programar_guardado_resaltados()
        self.seleccion_texto_resaltado = None
        self.verso_seleccionado = None
        self._refrescar_lectura_colores({verso})
        return True

    def _quitar_resaltado_seleccion_texto_actual(self):
        seleccion = self.seleccion_texto_resaltado
        if not isinstance(seleccion, dict):
            return False

        verso = seleccion.get("verso")
        texto = str(seleccion.get("texto") or "").strip()
        if not verso or not texto:
            return False

        texto_normalizado = self._normalizar_texto_busqueda(texto)
        texto_versiculo = self._normalizar_texto_busqueda(
            self._texto_desde_clave_verso(verso)
        )
        clave = self._clave_resaltado_palabras(verso)
        anteriores = self._resaltados_palabras_verso(verso)
        if not texto_normalizado or not texto_versiculo:
            return False

        # Una seleccion que cubre el versiculo entero borra todas sus capas:
        # color general y marcas de palabras. No deja restos de resaltado.
        if texto_normalizado == texto_versiculo:
            self.resaltados.pop(verso, None)
            self.resaltados.pop(clave, None)
        else:
            # No usamos coincidencias parciales: seleccionar una letra dentro
            # de una franja nunca debe borrar una palabra o frase distinta.
            candidatos = [
                (len(marca), indice)
                for indice, item in enumerate(anteriores)
                for marca in [self._normalizar_texto_busqueda(item.get("texto"))]
                if marca and (marca == texto_normalizado or marca in texto_normalizado)
            ]
            if not candidatos:
                return False

            _tamano, indice = max(candidatos, key=lambda item: item[0])
            actuales = [
                item for posicion, item in enumerate(anteriores) if posicion != indice
            ]
            if actuales:
                self.resaltados[clave] = actuales
            else:
                self.resaltados.pop(clave, None)
        self._programar_guardado_resaltados()
        self.seleccion_texto_resaltado = None
        self.verso_seleccionado = None
        self._refrescar_lectura_colores({verso})
        return True

    def _clave_resaltado_palabras(self, verso):
        return f"PAL|{verso}"

    def _resaltados_palabras_verso(self, verso):
        datos = self.resaltados.get(self._clave_resaltado_palabras(verso), [])
        if not isinstance(datos, list):
            return []
        return [
            item
            for item in datos
            if isinstance(item, dict) and str(item.get("texto") or "").strip()
        ]

    def _normalizado_con_mapa(self, texto):
        normalizado = []
        mapa = []
        for indice, caracter in enumerate(str(texto or "")):
            base = " " if caracter == "." else unicodedata.normalize("NFD", caracter.lower())
            for pieza in base:
                if unicodedata.category(pieza) == "Mn":
                    continue
                normalizado.append(pieza)
                mapa.append(indice)
        return "".join(normalizado), mapa

    def _partes_resaltado_palabras(self, texto, verso):
        if not verso or self._clave_resaltado_palabras(verso) not in self.resaltados:
            return [(texto, None)]

        marcas_guardadas = self._resaltados_palabras_verso(verso)
        firma = tuple(
            (
                str(item.get("texto") or ""),
                self._normalizar_color(item.get("color") or self.color_actual),
            )
            for item in marcas_guardadas
        )
        clave_cache = (verso, str(texto or ""), firma)
        partes_cacheadas = self._cache_partes_resaltado_palabras.get(clave_cache)
        if partes_cacheadas is not None:
            return partes_cacheadas

        marcas = []
        for item in marcas_guardadas:
            texto_marca = str(item.get("texto") or "").strip()
            color = self._normalizar_color(item.get("color") or self.color_actual)
            normalizado, _mapa = self._normalizado_con_mapa(texto_marca)
            normalizado = normalizado.strip()
            if normalizado and self._hex_color(color):
                marcas.append((normalizado, color))

        if not marcas:
            return [(texto, None)]

        normalizado_texto, mapa = self._normalizado_con_mapa(texto)
        if not normalizado_texto or not mapa:
            return [(texto, None)]

        marcas.sort(key=lambda item: len(item[0]), reverse=True)
        partes = []
        cursor_texto = 0
        cursor_normalizado = 0
        largo_texto = len(texto)

        while cursor_normalizado < len(normalizado_texto):
            encontrada = None
            for marca, color in marcas:
                indice = normalizado_texto.find(marca, cursor_normalizado)
                if indice < 0:
                    continue
                candidata = (indice, len(marca), color)
                if encontrada is None or indice < encontrada[0] or (
                    indice == encontrada[0] and len(marca) > encontrada[1]
                ):
                    encontrada = candidata

            if encontrada is None:
                break

            inicio_norm, largo_marca, color = encontrada
            fin_norm = inicio_norm + largo_marca - 1
            if fin_norm >= len(mapa):
                break

            inicio = mapa[inicio_norm]
            fin = min(largo_texto, mapa[fin_norm] + 1)
            if inicio < cursor_texto or fin <= inicio:
                cursor_normalizado = inicio_norm + max(1, largo_marca)
                continue

            if cursor_texto < inicio:
                partes.append((texto[cursor_texto:inicio], None))
            partes.append((texto[inicio:fin], color))
            cursor_texto = fin
            cursor_normalizado = inicio_norm + max(1, largo_marca)

        if cursor_texto < largo_texto:
            partes.append((texto[cursor_texto:], None))

        resultado = partes or [(texto, None)]
        self._cache_partes_resaltado_palabras[clave_cache] = resultado
        return resultado

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

    def _fondo_resaltado_lectura(self, color):
        color_hex = self._hex_color(color)
        if not color_hex:
            return None
        return ft.Colors.with_opacity(OPACIDAD_RESALTADO_LECTURA, color_hex)

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

    def _objetivos_color_activos(self):
        objetivos = set(self.objetivos_color)

        if self.objetivo_color:
            objetivos.add(self.objetivo_color)

        if self.verso_seleccionado:
            objetivos.add(self.verso_seleccionado)

        if self.modo_compartir_multiple:
            objetivos.update(self.versos_compartir)

        return objetivos

    def _esta_marcado_para_color(self, clave):
        if self._objetivo_base() == clave:
            return True

        for objetivo in self._objetivos_color_activos():
            if objetivo == clave or objetivo.split("|DIG|", 1)[0] == clave:
                return True

        return False

    def _limpiar_objetivos_color(self):
        self.objetivos_color.clear()
        self.objetivo_color = None
        self.objetivo_color_control = None
        self.verso_seleccionado = None
        self.versos_compartir.clear()
        self.modo_compartir_multiple = False

    def _refrescar_lectura_colores(self, objetivos=None):
        """Repinta primero los textos visibles y reconstruye solo si es necesario."""
        objetivos = set(objetivos or [])

        if objetivos and self._actualizar_textos_lectura_resaltados(objetivos):
            return

        son_versiculos_visibles = bool(objetivos) and all(
            objetivo in self._controles_versiculos
            and "|DIG|" not in objetivo
            for objetivo in objetivos
        )

        if son_versiculos_visibles:
            try:
                if all(self._actualizar_versiculo_seleccionado(verso) for verso in objetivos):
                    return
            except (RuntimeError, AssertionError, AttributeError):
                pass

        self._refrescar_lectura_actual()

    def _registrar_control_texto_lectura(self, control, versos, actualizar):
        for verso in set(versos):
            if not verso:
                continue
            controles = self._controles_texto_lectura.setdefault(verso, {})
            controles[id(control)] = actualizar

    def _registrar_rangos_seleccion_lectura(self, control, rangos):
        self._rangos_seleccion_lectura[id(control)] = tuple(rangos)

    def _rangos_versiculos_parrafo(self, segmentos, libro_nombre, capitulo_numero):
        """Replica el texto plano del parrafo para ubicar su seleccion final."""
        posicion = 0
        rangos = []
        for segmento in segmentos:
            texto = str(segmento.get("texto") or "").strip()
            if not texto:
                continue

            numero = segmento.get("versiculo")
            try:
                numero = int(numero)
                verso = verso_id(libro_nombre, capitulo_numero, numero)
            except (TypeError, ValueError):
                verso = None

            if verso:
                posicion += len(f"{numero} ")
                if self._tiene_comentario(verso):
                    posicion += len(MARCADOR_COMENTARIO)

            inicio = posicion
            posicion += len(texto)
            if verso:
                rangos.append(
                    {
                        "verso": verso,
                        "inicio": inicio,
                        "fin": posicion,
                        "texto": texto,
                    }
                )
            posicion += 1
        return rangos

    def _actualizar_textos_lectura_resaltados(self, versos):
        actualizadores = {}
        for verso in versos:
            for identificador, actualizar in self._controles_texto_lectura.get(verso, {}).items():
                actualizadores[identificador] = actualizar

        if not actualizadores:
            return False

        try:
            for actualizar in actualizadores.values():
                actualizar()
            return True
        except (RuntimeError, AssertionError, AttributeError):
            return False

    def _alternar_objetivo_color(self, clave, mensaje=None):
        if clave in self.objetivos_color:
            self.objetivos_color.remove(clave)
            if self.objetivo_color == clave:
                self.objetivo_color = next(iter(self.objetivos_color), None)
        else:
            self.objetivos_color.add(clave)
            self.objetivo_color = clave

        self.objetivo_color_control = None
        self.verso_seleccionado = None
        self.ultimo_verso_accionado = None

        if mensaje:
            self._snack(mensaje)

    def _icono_marcado(self, visible=True, size=18):
        return ft.Icon(
            ft.Icons.BOOKMARK_ADDED,
            size=size,
            color=MARRON_ACENTO,
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
        self._programar_guardado_resaltados()
        self.objetivo_color = None
        self.objetivo_color_control = None
        self._refrescar_lectura_colores({clave})

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
                ft.Border.all(2, MARRON_ACENTO)
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
                else MARRON_PERLA
                if seleccionado
                else ft.Colors.TRANSPARENT
            ),
            border=(
                ft.Border.all(2, MARRON_ACENTO)
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
        self._cache_partes_resaltado_palabras.clear()
        self._controles_versiculos.clear()
        self._controles_texto_lectura.clear()
        self._controles_tamano_lectura.clear()
        self._rangos_seleccion_lectura.clear()
        self.panel_lectura.controls.clear()
        # El callback solo es necesario mientras se lee un libro completo.
        self.panel_lectura.on_scroll = (
            self._al_desplazar_libro_completo
            if self.modo_vista == "Libro"
            else None
        )

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

        if self.modo_vista == "Libro":
            self._render_libro_completo_lectura()
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
        movil = self.responsive.is_mobile()
        clave = self._clave_libro(nombre)
        color = self._color_libro_resaltado(nombre)
        fondo = self._hex_color(color, ft.Colors.WHITE)
        texto_color = self._texto_color(color)
        seleccionado = self._esta_marcado_para_color(clave)

        borde = (
            ft.Border.all(2, MARRON_ACENTO)
            if seleccionado
            else self._borde_por_color(
                color,
                default=ft.Colors.GREY_300,
                ancho=1,
            )
        )

        def doble_click_libro(e, libro_nombre=nombre):
            self.codificar_libro_biblia(libro_nombre)

        def tocar_libro(e, libro_nombre=nombre):
            self.seleccionar_libro_para_color(libro_nombre)

        contenido_libro = ft.GestureDetector(
            on_tap=tocar_libro,
            on_double_tap=doble_click_libro,
            on_long_press=tocar_libro,
            content=ft.Container(
                width=132 if movil else 152,
                height=68,
                alignment=ft.Alignment(0, 0),
                padding=8,
                content=ft.Row(
                    spacing=2,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(
                            f"{nombre}\n({len(libro['capitulos'])})",
                            expand=True,
                            color=texto_color,
                            weight=ft.FontWeight.BOLD,
                            size=13 if movil else 14,
                            text_align=ft.TextAlign.CENTER,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.ARROW_FORWARD,
                            tooltip="Abrir capitulos",
                            icon_size=16,
                            width=28,
                            height=28,
                            on_click=lambda e, libro_nombre=nombre:
                                self.ir_a_libro(libro_nombre),
                        ),
                    ],
                ),
            ),
        )

        return ft.Container(
            width=132 if movil else 152,
            height=68,
            bgcolor=fondo,
            border=borde,
            border_radius=8,
            content=contenido_libro,
        )

    def _render_capitulos(self):
        libro = self._libro_actual()

        if not libro:
            return

        self.panel_lectura.controls.append(self._encabezado_libro_capitulos(libro))

        self.panel_lectura.controls.append(
            ft.ElevatedButton(
                "Leer libro completo",
                icon=ft.Icons.ARTICLE,
                on_click=lambda e: self.ir_a_libro_completo(libro["nombre"]),
            )
        )

        self.panel_lectura.controls.append(
            ft.Column(
                tight=True,
                spacing=8,
                controls=[
                    self._tarjeta_capitulo_lista(
                        libro["nombre"],
                        indice,
                    )
                    for indice in range(1, len(libro["capitulos"]) + 1)
                ],
            )
        )

    def _encabezado_libro_capitulos(self, libro):
        nombre = libro["nombre"]
        clave = self._clave_libro(nombre)
        color = self.resaltados.get(clave)
        seleccionado = self._esta_marcado_para_color(clave)

        def tocar_libro(e=None):
            self.seleccionar_libro_para_color(nombre)

        return ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            on_tap=tocar_libro,
            on_long_press=tocar_libro,
            content=ft.Container(
                padding=ft.Padding(left=12, top=10, right=10, bottom=10),
                border_radius=12,
                bgcolor=self._hex_color(color, MARRON_PERLA if seleccionado else ft.Colors.WHITE),
                border=(
                    ft.Border.all(2, MARRON_ACENTO)
                    if seleccionado
                    else self._borde_por_color(color, default=BORDE_SUAVE, ancho=1)
                ),
                content=ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self._icono_marcado(visible=seleccionado, size=16),
                        ft.Text(
                            f"{nombre}: capítulos",
                            expand=True,
                            weight=ft.FontWeight.BOLD,
                            color=self._texto_color(color),
                            font_family=FUENTE_LECTURA_BIBLIA,
                        ),
                        self._boton_comentario_titulo(
                            clave,
                            "Agregar o ver comentario del libro",
                        ),
                    ],
                ),
            ),
        )

    def _tarjeta_capitulo_lista(self, libro, capitulo):
        clave = self._clave_capitulo(libro, capitulo)
        color = self._color_capitulo_directo(libro, capitulo)
        color_resuelto = color
        seleccionado = self._esta_marcado_para_color(clave)

        def tocar_capitulo(e=None):
            self.marcar_para_colorear(clave, "Titulo del capitulo seleccionado.")

        def marcar_capitulo(e=None):
            self.marcar_para_colorear(clave, "Titulo del capitulo seleccionado.")

        return ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            on_tap=tocar_capitulo,
            on_double_tap=lambda e, l=libro, c=capitulo:
                self.codificar_capitulo_biblia(l, c),
            on_long_press=marcar_capitulo,
            content=ft.Container(
                padding=ft.Padding(left=10, top=8, right=10, bottom=8),
                border_radius=12,
                bgcolor=(
                    self._hex_color(color_resuelto)
                    if color_resuelto
                    else MARRON_PERLA
                    if seleccionado
                    else ft.Colors.WHITE
                ),
                border=(
                    ft.Border.all(2, MARRON_ACENTO)
                    if seleccionado
                    else self._borde_por_color(color_resuelto, default=BORDE_SUAVE, ancho=1)
                ),
                content=ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self._control_identificador(
                            capitulo,
                            color_resuelto,
                            seleccionado=seleccionado,
                            ancho=58 if capitulo >= 10 else 48,
                            alto=34,
                        ),
                        ft.Text(
                            f"Capítulo {capitulo}",
                            expand=True,
                            weight=ft.FontWeight.BOLD,
                            color=self._texto_color(color_resuelto),
                            font_family=FUENTE_LECTURA_BIBLIA,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.ARTICLE_OUTLINED,
                            tooltip="Leer capitulo",
                            icon_size=18,
                            width=30,
                            height=30,
                            on_click=lambda e, c=capitulo: self.ir_a_capitulo(c),
                        ),
                        self._boton_comentario_titulo(
                            clave,
                            "Agregar o ver comentario del capítulo",
                        ),
                    ],
                ),
            ),
        )

    def _boton_capitulo(self, libro, capitulo, on_tap):
        color = self._color_capitulo_directo(libro, capitulo)
        clave = self._clave_capitulo(libro, capitulo)
        color_resuelto = color
        seleccionado = self._esta_marcado_para_color(clave)

        contenedor = self._control_identificador(
            capitulo,
            color_resuelto,
            seleccionado=seleccionado,
            ancho=70 if seleccionado else 48 if capitulo >= 10 else 42,
            alto=36,
        )

        def tocar_capitulo(e):
            on_tap(e)

        return ft.GestureDetector(
            on_tap=tocar_capitulo,
            on_double_tap=lambda e, l=libro, c=capitulo:
                self.codificar_capitulo_biblia(l, c),
            on_long_press=lambda e, clave=clave: self.marcar_para_colorear(
                clave,
                "Titulo del capitulo seleccionado.",
            ),
            content=contenedor,
        )

    def _texto_versiculo_visual(self, libro, texto, color_base, expand=True):
        texto = str(texto or "")
        inicio_rojo = self._inicio_palabras_cordero(libro, texto)
        spans = []
        tiene_palabras_diccionario = False

        fragmentos = (
            fragmentos_con_diccionario(texto)
            if self._puede("biblia_diccionario_hebreo")
            else [(texto, None, 0, len(texto))]
        )
        for fragmento, entrada, inicio, _fin in fragmentos:
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
                    color=PURPURA_ACCENTO,
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
            try:
                if dialog in self.page.overlay:
                    self.page.overlay.remove(dialog)
            except Exception:
                pass
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
                                color=PURPURA_ACCENTO,
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
        if not self._puede("biblia_diccionario_hebreo"):
            self._snack("El diccionario hebreo requiere el Nivel 4.")
            return
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

    def _referencia_versos(self, versos):
        if not versos:
            return ""

        if len(versos) == 1:
            return versos[0]["referencia"]

        primero = versos[0]
        ultimo = versos[-1]

        if primero["libro"] == ultimo["libro"] and primero["capitulo"] == ultimo["capitulo"]:
            numeros = [verso["versiculo"] for verso in versos]
            consecutivos = numeros == list(range(numeros[0], numeros[-1] + 1))

            if consecutivos:
                return f"{primero['libro']} {primero['capitulo']}:{primero['versiculo']}-{ultimo['versiculo']}"

            return (
                f"{primero['libro']} {primero['capitulo']}:"
                + ", ".join(str(numero) for numero in numeros)
            )

        if primero["libro"] == ultimo["libro"]:
            return (
                f"{primero['libro']} "
                f"{primero['capitulo']}:{primero['versiculo']}-"
                f"{ultimo['capitulo']}:{ultimo['versiculo']}"
            )

        return f"{primero['referencia']} - {ultimo['referencia']}"

    def _datos_texto_biblia_actual(self):
        versos = self._versos_ordenados_para_compartir()

        if versos:
            return {
                "referencia": self._referencia_versos(versos),
                "texto": self._texto_versos_compartir(versos),
                "versos": versos,
            }

        return self._datos_versiculo_activo()

    def _datos_tarjeta_biblia_actual(self):
        versos = self._versos_ordenados_para_compartir()

        if versos:
            return {
                "referencia": self._referencia_versos(versos),
                "texto": "\n".join(
                    f"{verso['versiculo']}. {verso['texto']}"
                    for verso in versos
                ),
                "versos": versos,
            }

        return self._datos_versiculo_activo()

    def toggle_modo_compartir_multiple(self):
        if self._solo_lectura():
            return
        afectados = set(self.versos_compartir)
        activar = not (self.modo_compartir_multiple or bool(self.versos_compartir))
        self.modo_compartir_multiple = activar

        if activar:
            self.verso_seleccionado = None
            self.objetivo_color = None
            self.objetivos_color.clear()
            mensaje = "Seleccion multiple activada. Toque versiculos para agregarlos o quitarlos."
        else:
            self.versos_compartir.clear()
            self.objetivo_color = None
            self.objetivos_color.clear()
            mensaje = "Seleccion multiple desactivada."

        self._snack(mensaje)
        self._actualizar_boton_seleccion_multiple()
        if afectados:
            self._refrescar_lectura_colores(afectados)

    def limpiar_seleccion_multiple(self, e=None):
        afectados = set(self.versos_compartir)
        self.versos_compartir.clear()
        self.modo_compartir_multiple = False
        self._snack("Seleccion multiple limpia.")
        self._actualizar_boton_seleccion_multiple()
        if afectados:
            self._refrescar_lectura_colores(afectados)

    def _actualizar_boton_seleccion_multiple(self):
        try:
            boton = self._boton_seleccion_multiple_control
            activo = self.modo_compartir_multiple or bool(self.versos_compartir)
            boton.icon_color = NARANJA_ACCENTO
            boton.bgcolor = MARRON_PERLA if activo else None
            boton.update()
        except (AttributeError, RuntimeError, AssertionError):
            pass

    def _actualizar_control_verso_multiple(self, evento, verso):
        try:
            contenedor = evento.control.content
            resaltado = self.resaltados.get(verso)
            seleccionado = self.verso_seleccionado == verso
            seleccionado_multiple = verso in self.versos_compartir
            verso_marcado = self._esta_marcado_para_color(verso)
            color_fondo = self._hex_color(resaltado)

            contenedor.bgcolor = (
                color_fondo
                if resaltado
                else "#FFF7D6"
                if seleccionado_multiple
                else MARRON_PERLA
                if seleccionado or verso_marcado
                else ft.Colors.WHITE
            )
            contenedor.border = ft.Border.all(
                2 if seleccionado or verso_marcado or seleccionado_multiple else 1,
                NARANJA_ACCENTO
                if seleccionado_multiple
                else MARRON_ACENTO
                if seleccionado or verso_marcado
                else BORDER_MARRON
                if self._es_blanco_borde(resaltado)
                else ft.Colors.GREY_300,
            )

            fila = contenedor.content
            if getattr(fila, "controls", None):
                fila.controls[0].visible = seleccionado_multiple

            contenedor.update()
        except Exception:
            self._refrescar_lectura_colores({verso})

    def tocar_versiculo(self, verso, evento=None):
        if self.modo_compartir_multiple:
            self.toggle_verso_compartir(verso, refrescar=False)

            if evento is not None:
                self._actualizar_control_verso_multiple(evento, verso)

            return

        self.seleccionar_verso(verso, evento)
        self._programar_selector_color_contextual({verso})

    def toggle_verso_compartir(self, verso, refrescar=True):
        if verso in self.versos_compartir:
            self.versos_compartir.remove(verso)
        else:
            self.versos_compartir.add(verso)

        self.ultimo_verso_accionado = verso

        if refrescar:
            self._refrescar_lectura_colores({verso})

    def ir_a_verso_clave(self, clave):
        libro, capitulo, versiculo = self._desarmar_clave_verso(clave)

        if not libro or not capitulo or not versiculo:
            return

        self._limpiar_seleccion_transitoria()
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
        self._refrescar_lectura_actual()

    def _render_versiculos(self):
        self._render_versiculos_lectura()

    def _render_versiculos_lectura(self):
        capitulo = self._capitulo_actual()
        parrafos = BibliaService.obtener_parrafos(self.libro_actual, self.capitulo_actual)

        if not parrafos:
            parrafos = [
                {
                    "tipo": "parrafo",
                    "segmentos": [
                        {"versiculo": indice, "texto": texto}
                        for indice, texto in enumerate(capitulo, start=1)
                    ],
                }
            ]

        movil = self.responsive.is_mobile()
        bloques = [
            self._control_bloque_lectura(
                bloque,
                indice_bloque=indice_bloque,
                libro_nombre=self.libro_actual,
                capitulo_numero=self.capitulo_actual,
            )
            for indice_bloque, bloque in enumerate(parrafos)
        ]
        bloques = [bloque for bloque in bloques if bloque is not None]

        titulo_libro = ft.Text(
            self.libro_actual or "",
            size=self.tamano_fuente_lectura + (6 if movil else 8),
            weight=ft.FontWeight.BOLD,
            color=self._texto_color(
                self.resaltados.get(self._clave_libro(self.libro_actual)),
                ft.Colors.BLACK,
            ),
            font_family=FUENTE_LECTURA_BIBLIA,
        )
        self._registrar_control_tamano_lectura(
            titulo_libro,
            lambda control=titulo_libro, extra=6 if movil else 8: setattr(
                control, "size", self.tamano_fuente_lectura + extra
            ),
        )
        self.panel_lectura.controls.append(
            ft.Container(
                padding=ft.Padding(left=0, top=0, right=0, bottom=10),
                border=ft.Border(bottom=ft.BorderSide(1, "#E8E8EA")),
                content=ft.Column(
                    tight=True,
                    spacing=2,
                    controls=[
                        self._encabezado_libro_lectura(
                            self.libro_actual,
                            titulo_libro,
                        ),
                        self._titulo_capitulo_lectura(
                            self.libro_actual,
                            self.capitulo_actual,
                            self.tamano_fuente_lectura + (4 if movil else 6),
                        ),
                        self._barra_rapida_capitulos(),
                    ],
                ),
            )
        )

        # La lectura de capitulos se mantiene siempre en una sola columna.
        self.panel_lectura.controls.extend(bloques)

    def _render_libro_completo_lectura(self):
        libro = self._libro_actual()
        if not libro:
            return

        movil = self.responsive.is_mobile()
        self._libro_completo_cargado = libro["nombre"]
        self._siguiente_capitulo_libro = 1
        color_libro = self._color_libro_resaltado(libro["nombre"])
        titulo_libro = ft.Text(
            libro["nombre"],
            size=self.tamano_fuente_lectura + (6 if movil else 8),
            weight=ft.FontWeight.BOLD,
            color=self._texto_color(color_libro) if color_libro else ft.Colors.BLACK,
            font_family=FUENTE_LECTURA_BIBLIA,
        )
        subtitulo_libro = ft.Text(
            "Libro completo",
            size=self.tamano_fuente_lectura + (2 if movil else 4),
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLACK,
            font_family=FUENTE_LECTURA_BIBLIA,
        )
        self._registrar_control_tamano_lectura(
            titulo_libro,
            lambda control=titulo_libro, extra=6 if movil else 8: setattr(
                control, "size", self.tamano_fuente_lectura + extra
            ),
        )
        self._registrar_control_tamano_lectura(
            subtitulo_libro,
            lambda control=subtitulo_libro, extra=2 if movil else 4: setattr(
                control, "size", self.tamano_fuente_lectura + extra
            ),
        )
        self.panel_lectura.controls.append(
            ft.Container(
                padding=ft.Padding(left=0, top=0, right=0, bottom=10),
                border=ft.Border(bottom=ft.BorderSide(1, "#E8E8EA")),
                content=ft.Column(
                    tight=True,
                    spacing=2,
                    controls=[
                        self._encabezado_libro_lectura(
                            libro["nombre"],
                            titulo_libro,
                        ),
                        subtitulo_libro,
                        self._barra_rapida_libros(),
                    ],
                ),
            )
        )

        self._agregar_tramo_libro_completo()

    def _encabezado_libro_lectura(self, libro_nombre, titulo_control):
        clave = self._clave_libro(libro_nombre)
        color = self.resaltados.get(clave)
        seleccionado = self._esta_marcado_para_color(clave)

        def tocar_titulo(e=None):
            self.marcar_para_colorear(clave, "Titulo del libro seleccionado.")

        return ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            on_tap=tocar_titulo,
            on_long_press=tocar_titulo,
            content=ft.Container(
                padding=ft.Padding(
                    left=6 if color or seleccionado else 0,
                    top=3 if color or seleccionado else 0,
                    right=6 if color or seleccionado else 0,
                    bottom=3 if color or seleccionado else 0,
                ),
                border_radius=8,
                bgcolor=(
                    self._fondo_resaltado_lectura(color)
                    if color
                    else MARRON_PERLA
                    if seleccionado
                    else None
                ),
                border=ft.Border.all(2, MARRON_ACENTO) if seleccionado else None,
                content=ft.Row(
                    tight=True,
                    spacing=2,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self._icono_marcado(visible=seleccionado, size=16),
                        titulo_control,
                        self._boton_comentario_titulo(
                            clave,
                            "Agregar o ver comentario del libro",
                        ),
                    ],
                ),
            ),
        )

    def _bloques_libro_completo_movil(self, bloques):
        """Mantiene una separacion visible y estable entre capitulos."""
        return [
            ft.Container(
                border=ft.Border(bottom=ft.BorderSide(1.2, ft.Colors.BLACK)),
                content=bloque,
            )
            for bloque in bloques
        ]

    def _agregar_tramo_libro_completo(self):
        libro = self._libro_actual()
        if not libro or libro["nombre"] != self._libro_completo_cargado:
            return False

        capitulos = libro.get("capitulos", [])
        inicio = self._siguiente_capitulo_libro
        if inicio > len(capitulos):
            return False

        # Pocos capitulos por lote mantienen la respuesta de las herramientas
        # inmediata, incluso en los libros mas extensos. La lectura siempre se
        # muestra en una sola columna para que los bloques ya visibles no se
        # reordenen cuando se agrega contenido al final.
        cantidad = 2 if self.responsive.is_mobile() else 3
        fin = min(len(capitulos), inicio + cantidad - 1)
        bloques = [
            self._crear_bloque_capitulo_libro_completo(
                libro,
                numero_capitulo,
                capitulos[numero_capitulo - 1],
            )
            for numero_capitulo in range(inicio, fin + 1)
        ]
        self._siguiente_capitulo_libro = fin + 1
        self.panel_lectura.controls.extend(
            self._bloques_libro_completo_movil(bloques)
        )
        return True

    def _al_desplazar_libro_completo(self, evento):
        if (
            self.modo_vista != "Libro"
            or self._cargando_tramo_libro
        ):
            return

        try:
            posicion_actual = max(0, float(evento.pixels))
            cerca_del_final = (
                posicion_actual + evento.viewport_dimension
                >= evento.max_scroll_extent - 260
            )
        except (AttributeError, TypeError, ValueError):
            return

        if not cerca_del_final:
            return

        self._cargando_tramo_libro = True
        try:
            if self._agregar_tramo_libro_completo():
                self.panel_lectura.update()
        except (RuntimeError, AssertionError):
            pass
        finally:
            self._cargando_tramo_libro = False

    def _crear_bloque_capitulo_libro_completo(
        self,
        libro,
        numero_capitulo,
        versiculos,
    ):
        parrafos = self._parrafos_capitulo_libro(libro, numero_capitulo, versiculos)
        spans, peso, rangos_seleccion = self._spans_capitulo_libro_completo(
            parrafos,
            libro["nombre"],
            numero_capitulo,
        )
        texto_capitulo = ft.Text(
            spans=spans,
            size=self.tamano_fuente_lectura,
            color=ft.Colors.BLACK,
            font_family=FUENTE_LECTURA_BIBLIA,
            text_align=ft.TextAlign.JUSTIFY,
            selectable=True,
            enable_interactive_selection=True,
            on_selection_change=lambda e, l=libro["nombre"], c=numero_capitulo:
                self._guardar_seleccion_texto_resaltado(e, l, c),
            style=self._estilo_texto_lectura(
                libro["nombre"],
                numero_capitulo,
                parrafos,
            ),
        )
        versos_capitulo = [
            verso_id(libro["nombre"], numero_capitulo, int(segmento["versiculo"]))
            for bloque in parrafos
            for segmento in bloque.get("segmentos", [])
            if isinstance(segmento, dict) and str(segmento.get("versiculo") or "").isdigit()
        ]
        self._registrar_rangos_seleccion_lectura(texto_capitulo, rangos_seleccion)

        def actualizar_texto_capitulo(
            control=texto_capitulo,
            parrafos_capitulo=parrafos,
            nombre_libro=libro["nombre"],
            capitulo=numero_capitulo,
        ):
            spans_actualizados, _peso, rangos_actualizados = self._spans_capitulo_libro_completo(
                parrafos_capitulo,
                nombre_libro,
                capitulo,
            )
            control.spans = spans_actualizados
            self._registrar_rangos_seleccion_lectura(control, rangos_actualizados)
            control.style = self._estilo_texto_lectura(
                nombre_libro,
                capitulo,
                parrafos_capitulo,
            )
            control.update()

        self._registrar_control_texto_lectura(
            texto_capitulo,
            versos_capitulo,
            actualizar_texto_capitulo,
        )
        self._registrar_control_tamano_lectura(
            texto_capitulo,
            lambda control=texto_capitulo, parrafos_capitulo=parrafos,
            nombre_libro=libro["nombre"], capitulo=numero_capitulo: (
                setattr(control, "size", self.tamano_fuente_lectura),
                setattr(
                    control,
                    "style",
                    self._estilo_texto_lectura(
                        nombre_libro,
                        capitulo,
                        parrafos_capitulo,
                    ),
                ),
            ),
        )
        return ft.Container(
            data={"peso": peso},
            padding=ft.Padding(left=0, top=10, right=0, bottom=8),
            content=ft.Column(
                tight=True,
                spacing=8,
                controls=[
                    self._titulo_capitulo_lectura(
                        libro["nombre"],
                        numero_capitulo,
                        self.tamano_fuente_lectura + 2,
                    ),
                    texto_capitulo,
                ],
            ),
        )

    def _titulo_capitulo_lectura(self, libro, capitulo, tamano):
        color = self._color_capitulo_directo(libro, capitulo)
        clave_comentario = self._clave_capitulo(libro, capitulo)
        seleccionado = self._esta_marcado_para_color(clave_comentario)
        titulo = ft.Text(
            f"Capítulo {capitulo}",
            size=tamano,
            weight=ft.FontWeight.BOLD,
            color=self._texto_color(color) if color else ft.Colors.BLACK,
            font_family=FUENTE_LECTURA_BIBLIA,
        )
        diferencia_tamano = tamano - self.tamano_fuente_lectura
        self._registrar_control_tamano_lectura(
            titulo,
            lambda control=titulo, extra=diferencia_tamano: setattr(
                control, "size", self.tamano_fuente_lectura + extra
            ),
        )

        def tocar_titulo(e):
            self.marcar_para_colorear(
                clave_comentario,
                "Titulo del capitulo seleccionado.",
            )

        return ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            on_tap=tocar_titulo,
            on_long_press=tocar_titulo,
            content=ft.Container(
                padding=ft.Padding(
                    left=6 if color or seleccionado else 0,
                    top=3 if color or seleccionado else 0,
                    right=6 if color or seleccionado else 0,
                    bottom=3 if color or seleccionado else 0,
                ),
                border_radius=8,
                bgcolor=(
                    self._fondo_resaltado_lectura(color)
                    if color
                    else MARRON_PERLA
                    if seleccionado
                    else None
                ),
                border=ft.Border.all(2, MARRON_ACENTO) if seleccionado else None,
                content=ft.Row(
                    tight=True,
                    spacing=2,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self._icono_marcado(visible=seleccionado, size=16),
                        titulo,
                        self._boton_comentario_titulo(
                            clave_comentario,
                            "Agregar o ver comentario del capitulo",
                        ),
                    ],
                ),
            ),
        )

    def _estilo_texto_lectura(self, libro, capitulo, bloques):
        tiene_resaltado_amplio = bool(self._color_capitulo_directo(libro, capitulo))
        if not tiene_resaltado_amplio:
            for bloque in bloques:
                for segmento in bloque.get("segmentos", []) if isinstance(bloque, dict) else []:
                    numero = segmento.get("versiculo") if isinstance(segmento, dict) else None
                    if numero:
                        try:
                            tiene_resaltado_amplio = bool(
                                self.resaltados.get(verso_id(libro, capitulo, int(numero)))
                            )
                        except (TypeError, ValueError):
                            continue
                        if tiene_resaltado_amplio:
                            break
                if tiene_resaltado_amplio:
                    break

        return ft.TextStyle(
            height=self._alto_linea_lectura() + (0.12 if tiene_resaltado_amplio else 0),
            font_family=FUENTE_LECTURA_BIBLIA,
        )

    def _parrafos_capitulo_libro(self, libro, numero_capitulo, versiculos):
        try:
            parrafos = libro.get("parrafos", [])[numero_capitulo - 1]
            if isinstance(parrafos, list) and parrafos:
                return parrafos
        except (TypeError, IndexError):
            pass

        return [
            {
                "tipo": "parrafo",
                "segmentos": [
                    {"versiculo": indice, "texto": texto}
                    for indice, texto in enumerate(versiculos, start=1)
                ],
            }
        ]

    def _spans_capitulo_libro_completo(self, parrafos, libro_nombre, numero_capitulo):
        spans = []
        peso = 0
        posicion = 0
        rangos_seleccion = []
        for indice_bloque, bloque in enumerate(parrafos):
            tipo = bloque.get("tipo")
            if tipo == "titulo":
                texto = str(bloque.get("texto") or "").strip()
                if texto:
                    if spans:
                        spans.append(ft.TextSpan("\n"))
                        posicion += 1
                    clave_subtitulo = self._clave_subtitulo(
                        libro_nombre,
                        numero_capitulo,
                        indice_bloque,
                    )
                    color_subtitulo = self.resaltados.get(clave_subtitulo)
                    spans.append(
                        ft.TextSpan(
                            texto,
                            style=ft.TextStyle(
                                color=self._texto_color(color_subtitulo, SUBTITULO_LECTURA),
                                bgcolor=self._fondo_resaltado_lectura(color_subtitulo),
                                weight=ft.FontWeight.BOLD,
                            ),
                            on_click=lambda e, clave=clave_subtitulo:
                                self.marcar_para_colorear(
                                    clave,
                                    "Subtitulo seleccionado.",
                                ),
                        )
                    )
                    posicion += len(texto)
                    spans.append(self._span_boton_comentario_titulo(clave_subtitulo))
                    posicion += len(MARCADOR_COMENTARIO)
                    spans.append(ft.TextSpan("\n"))
                    posicion += 1
                    peso += max(1, len(texto) // 120)
                continue

            segmentos = bloque.get("segmentos") if isinstance(bloque, dict) else None
            if not segmentos:
                continue

            for segmento in segmentos:
                texto = str(segmento.get("texto") or "").strip()
                if not texto:
                    continue
                numero = segmento.get("versiculo")
                vid = None
                resaltado = None
                seleccionado = False
                seleccionado_multiple = False
                if numero:
                    try:
                        numero = int(numero)
                        vid = verso_id(libro_nombre, numero_capitulo, numero)
                        resaltado = self.resaltados.get(vid)
                        seleccionado = self.verso_seleccionado == vid or self._esta_marcado_para_color(vid)
                        seleccionado_multiple = vid in self.versos_compartir
                    except (TypeError, ValueError):
                        vid = None

                    spans.append(
                        ft.TextSpan(
                            f"{numero} ",
                            style=ft.TextStyle(
                                size=self._tamano_numero_lectura(),
                                color=CHOCOLATE_LECTURA,
                                weight=ft.FontWeight.BOLD,
                                bgcolor="#FFF1D6" if seleccionado or seleccionado_multiple else None,
                            ),
                            on_click=lambda e, v=vid: self.tocar_versiculo(v, e) if v else None,
                        )
                    )
                    posicion += len(f"{numero} ")
                    if vid and self._tiene_comentario(vid):
                        spans.append(self._span_indicador_comentario(vid))
                        posicion += len(MARCADOR_COMENTARIO)
                color_texto = ft.Colors.BLACK
                fondo = self._fondo_resaltado_lectura(resaltado)
                if seleccionado_multiple:
                    fondo = "#FFF7D6"
                elif seleccionado:
                    fondo = MARRON_PERLA

                inicio_texto = posicion
                spans.extend(
                    self._spans_texto_lectura(
                        texto,
                        vid,
                        color_texto,
                        fondo,
                        interactivo=False,
                        usar_diccionario=False,
                        libro_nombre=libro_nombre,
                    )
                )
                posicion += len(texto)
                if vid:
                    rangos_seleccion.append(
                        {
                            "verso": vid,
                            "inicio": inicio_texto,
                            "fin": posicion,
                            "texto": texto,
                        }
                    )
                spans.append(ft.TextSpan(" "))
                posicion += 1
                peso += max(1, len(texto) // 160)
            spans.append(ft.TextSpan("\n\n"))
            posicion += 2

        return spans, max(1, peso), rangos_seleccion

    def _control_bloque_lectura(
        self,
        bloque,
        indice_bloque=None,
        libro_nombre=None,
        capitulo_numero=None,
    ):
        tipo = bloque.get("tipo")

        if tipo == "titulo":
            texto = str(bloque.get("texto") or "").strip()
            if not texto:
                return None
            clave_subtitulo = None
            if (
                indice_bloque is not None
                and libro_nombre
                and capitulo_numero is not None
            ):
                clave_subtitulo = self._clave_subtitulo(
                    libro_nombre,
                    capitulo_numero,
                    indice_bloque,
                )
            color = self.resaltados.get(clave_subtitulo) if clave_subtitulo else None
            seleccionado = bool(
                clave_subtitulo and self._esta_marcado_para_color(clave_subtitulo)
            )
            subtitulo = ft.Text(
                texto,
                size=self._tamano_subtitulo_lectura(),
                weight=ft.FontWeight.BOLD,
                color=self._texto_color(color, SUBTITULO_LECTURA),
                font_family=FUENTE_LECTURA_BIBLIA,
            )
            self._registrar_control_tamano_lectura(
                subtitulo,
                lambda control=subtitulo: setattr(
                    control, "size", self._tamano_subtitulo_lectura()
                ),
            )
            contenido = ft.Container(
                padding=ft.Padding(
                    left=6 if color or seleccionado else 0,
                    top=3,
                    right=6 if color or seleccionado else 0,
                    bottom=3,
                ),
                border_radius=8,
                bgcolor=(
                    self._fondo_resaltado_lectura(color)
                    if color
                    else MARRON_PERLA
                    if seleccionado
                    else None
                ),
                border=ft.Border.all(2, MARRON_ACENTO) if seleccionado else None,
                content=ft.Row(
                    tight=True,
                    spacing=2,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self._icono_marcado(visible=seleccionado, size=16),
                        subtitulo,
                        *(
                            [
                                self._boton_comentario_titulo(
                                    clave_subtitulo,
                                    "Agregar o ver comentario del subtitulo",
                                )
                            ]
                            if clave_subtitulo
                            else []
                        ),
                    ],
                ),
            )
            if not clave_subtitulo:
                return contenido
            return ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK,
                on_tap=lambda e, clave=clave_subtitulo: self.marcar_para_colorear(
                    clave,
                    "Subtitulo seleccionado.",
                ),
                on_long_press=lambda e, clave=clave_subtitulo: self.marcar_para_colorear(
                    clave,
                    "Subtitulo seleccionado.",
                ),
                content=contenido,
            )

        segmentos = bloque.get("segmentos") if isinstance(bloque, dict) else None
        if not segmentos:
            return None

        control = ft.Text(
            spans=self._spans_parrafo_lectura(segmentos),
            size=self.tamano_fuente_lectura,
            color=ft.Colors.BLACK,
            font_family=FUENTE_LECTURA_BIBLIA,
            text_align=ft.TextAlign.JUSTIFY,
            selectable=True,
            enable_interactive_selection=True,
            on_selection_change=lambda e: self._guardar_seleccion_texto_resaltado(
                e,
                self.libro_actual,
                self.capitulo_actual,
            ),
            style=self._estilo_texto_lectura(
                self.libro_actual,
                self.capitulo_actual,
                [bloque],
            ),
        )

        versos = [
            verso_id(self.libro_actual, self.capitulo_actual, int(segmento["versiculo"]))
            for segmento in segmentos
            if isinstance(segmento, dict) and str(segmento.get("versiculo") or "").isdigit()
        ]
        self._registrar_rangos_seleccion_lectura(
            control,
            self._rangos_versiculos_parrafo(
                segmentos,
                self.libro_actual,
                self.capitulo_actual,
            ),
        )

        def actualizar_texto_parrafo(
            texto_control=control,
            segmentos_parrafo=segmentos,
            nombre_libro=self.libro_actual,
            capitulo=self.capitulo_actual,
        ):
            texto_control.spans = self._spans_parrafo_lectura(
                segmentos_parrafo,
                nombre_libro,
                capitulo,
            )
            texto_control.style = self._estilo_texto_lectura(
                nombre_libro,
                capitulo,
                [{"segmentos": segmentos_parrafo}],
            )
            self._registrar_rangos_seleccion_lectura(
                texto_control,
                self._rangos_versiculos_parrafo(
                    segmentos_parrafo,
                    nombre_libro,
                    capitulo,
                ),
            )
            texto_control.update()

        self._registrar_control_texto_lectura(
            control,
            versos,
            actualizar_texto_parrafo,
        )
        self._registrar_control_tamano_lectura(
            control,
            lambda texto_control=control, segmentos_parrafo=segmentos,
            nombre_libro=self.libro_actual, capitulo=self.capitulo_actual: (
                setattr(texto_control, "size", self.tamano_fuente_lectura),
                setattr(
                    texto_control,
                    "style",
                    self._estilo_texto_lectura(
                        nombre_libro,
                        capitulo,
                        [{"segmentos": segmentos_parrafo}],
                    ),
                ),
            ),
        )
        return control

    def _spans_parrafo_lectura(
        self,
        segmentos,
        libro_nombre=None,
        capitulo_numero=None,
    ):
        libro_nombre = libro_nombre or self.libro_actual
        capitulo_numero = capitulo_numero or self.capitulo_actual
        spans = []
        for segmento in segmentos:
            texto = str(segmento.get("texto") or "").strip()
            if not texto:
                continue

            numero = segmento.get("versiculo")
            vid = None
            resaltado = None
            seleccionado = False
            seleccionado_multiple = False
            if numero:
                try:
                    numero = int(numero)
                    vid = verso_id(libro_nombre, capitulo_numero, numero)
                    resaltado = self.resaltados.get(vid)
                    seleccionado = self.verso_seleccionado == vid or self._esta_marcado_para_color(vid)
                    seleccionado_multiple = vid in self.versos_compartir
                except (TypeError, ValueError):
                    vid = None

            if vid:
                spans.append(
                    ft.TextSpan(
                        f"{numero} ",
                        style=ft.TextStyle(
                            size=self._tamano_numero_lectura(),
                            color=CHOCOLATE_LECTURA,
                            weight=ft.FontWeight.BOLD,
                            bgcolor="#FFF1D6" if seleccionado or seleccionado_multiple else None,
                        ),
                        on_click=lambda e, v=vid: self.tocar_versiculo(v, e),
                    )
                )
                if self._tiene_comentario(vid):
                    spans.append(self._span_indicador_comentario(vid))

            color_texto = ft.Colors.BLACK
            fondo = self._fondo_resaltado_lectura(resaltado)
            if seleccionado_multiple:
                fondo = "#FFF7D6"
            elif seleccionado:
                fondo = MARRON_PERLA

            spans.extend(
                self._spans_texto_lectura(
                    texto,
                    vid,
                    color_texto,
                    fondo,
                    interactivo=False,
                    usar_diccionario=False,
                    libro_nombre=libro_nombre,
                )
            )
            spans.append(ft.TextSpan(" "))

        return spans

    def _spans_texto_lectura(
        self,
        texto,
        vid,
        color_base,
        fondo,
        interactivo=True,
        usar_diccionario=True,
        libro_nombre=None,
    ):
        inicio_rojo = self._inicio_palabras_cordero(
            libro_nombre or self.libro_actual,
            texto,
        )
        fragmentos = (
            fragmentos_con_diccionario(texto)
            if usar_diccionario and self._puede("biblia_diccionario_hebreo")
            else [(texto, None, 0, len(texto))]
        )
        spans = []

        for fragmento, entrada, inicio, _fin in fragmentos:
            es_palabra_cordero = inicio_rojo is not None and inicio >= inicio_rojo
            color_fragmento = COLOR_PALABRAS_CORDERO if es_palabra_cordero else color_base
            for parte, color_palabra in self._partes_resaltado_palabras(fragmento, vid):
                estilo = ft.TextStyle(
                    color=(
                        self._texto_color(color_palabra, color_fragmento)
                        if color_palabra
                        else color_fragmento
                    ),
                    bgcolor=self._hex_color(color_palabra, fondo) if color_palabra else fondo,
                    weight=ft.FontWeight.W_600 if es_palabra_cordero else None,
                )

                if entrada and interactivo:
                    estilo.weight = ft.FontWeight.BOLD
                    estilo.decoration = ft.TextDecoration.UNDERLINE
                    estilo.decoration_color = NARANJA_ACCENTO
                    estilo.decoration_thickness = 1.6
                    spans.append(
                        ft.TextSpan(
                            parte,
                            style=estilo,
                            on_click=lambda e, ent=entrada: self.dialog_palabra_hebreo(ent),
                        )
                    )
                    continue

                spans.append(
                    ft.TextSpan(
                        parte,
                        style=estilo,
                        on_click=(
                            (lambda e, v=vid: self.tocar_versiculo(v, e))
                            if interactivo and vid
                            else None
                        ),
                    )
                )

        return spans

    def _render_versiculos_interactiva(self):
        capitulo = self._capitulo_actual()

        for indice, texto in enumerate(capitulo, start=1):
            vid = verso_id(self.libro_actual, self.capitulo_actual, indice)
            resaltado = self.resaltados.get(vid)
            clave_numero = self._clave_numero_verso(vid)
            resaltado_numero = self.resaltados.get(clave_numero)
            seleccionado = self.verso_seleccionado == vid
            seleccionado_multiple = vid in self.versos_compartir
            verso_marcado = self._esta_marcado_para_color(vid)
            numero_seleccionado = self._esta_marcado_para_color(clave_numero)
            color_fondo = self._hex_color(resaltado)
            color_texto = self._texto_color(resaltado)

            contenedor_verso = ft.Container(
                padding=8,
                border_radius=6,
                ink=True,
                ink_color=ft.Colors.with_opacity(0.16, ft.Colors.BLUE),
                bgcolor=(
                    color_fondo
                    if resaltado
                    else "#FFF7D6"
                    if seleccionado_multiple
                    else MARRON_PERLA if seleccionado or verso_marcado else ft.Colors.WHITE
                ),
                border=ft.Border.all(
                    2 if seleccionado or verso_marcado or seleccionado_multiple else 1,
                    NARANJA_ACCENTO
                    if seleccionado_multiple
                    else MARRON_ACENTO
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
                        *(
                            [
                                ft.IconButton(
                                    icon=ft.Icons.CHAT_BUBBLE_OUTLINE,
                                    tooltip="Ver comentario del versiculo",
                                    icon_size=16,
                                    icon_color=NARANJA_ACCENTO,
                                    width=28,
                                    height=28,
                                    on_click=lambda e, clave=vid: self.dialog_comentario_biblia(clave),
                                )
                            ]
                            if self._tiene_comentario(vid)
                            else []
                        ),
                        self._texto_versiculo_visual(
                            self.libro_actual,
                            texto,
                            color_texto,
                        ),
                    ],
                ),
            )
            self._controles_versiculos[vid] = contenedor_verso
            self.panel_lectura.controls.append(
                ft.GestureDetector(
                    on_tap=lambda e, v=vid: self.tocar_versiculo(v, e),
                    on_double_tap=lambda e, v=vid: self.doble_tap_verso(v),
                    on_long_press=lambda e, v=vid: self.elegir_modo_color_identificador(
                        self._clave_numero_verso(v)
                    ),
                    content=contenedor_verso,
                )
            )
    def cambiar_modo(self, e):
        self.cambiar_modo_valor(e.control.value)

    def cambiar_modo_valor(self, valor):
        self._limpiar_seleccion_transitoria()
        self.modo_vista = "Libros" if valor == "Completa" else valor
        self.dropdown_modo.value = valor
        self.verso_seleccionado = None
        self.ultimo_verso_accionado = None
        self._guardar_ultima_lectura()
        self._refrescar_lectura_actual()

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

        self._refrescar_lectura_actual()

    def volver_lectura(self):
        if self.modo_vista == "Versiculos":
            self.modo_vista = "Capitulos"
        elif self.modo_vista == "Libro":
            self.modo_vista = "Capitulos"
        elif self.modo_vista == "Capitulos":
            self.modo_vista = "Libros"
        else:
            return

        self._limpiar_seleccion_transitoria()
        self.dropdown_modo.value = self.modo_vista
        self.verso_seleccionado = None
        self.ultimo_verso_accionado = None
        self._guardar_ultima_lectura()
        self._refrescar_lectura_actual()

    def cambiar_libro(self, e):
        self.cambiar_libro_valor(e.control.value)

    def cambiar_libro_valor(self, valor):
        self._limpiar_seleccion_transitoria()
        self.libro_actual = valor
        self.capitulo_actual = 1
        self.dropdown_capitulo.options = self._opciones_capitulos()
        self.dropdown_capitulo.value = "1"
        self.dropdown_libro.value = valor
        self.verso_seleccionado = None
        self.ultimo_verso_accionado = None
        self._guardar_ultima_lectura()
        self._refrescar_lectura_actual()

    def cambiar_capitulo(self, e):
        self.cambiar_capitulo_valor(int(e.control.value))

    def cambiar_capitulo_valor(self, valor):
        self._limpiar_seleccion_transitoria()
        self.capitulo_actual = valor
        self.dropdown_capitulo.value = str(valor)
        self.verso_seleccionado = None
        self.ultimo_verso_accionado = None
        self._guardar_ultima_lectura()
        self._refrescar_lectura_actual()

    def ir_a_libro(self, nombre):
        self._limpiar_seleccion_transitoria()
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
        self._refrescar_lectura_actual()

    def ir_a_libro_completo(self, nombre=None):
        self._limpiar_seleccion_transitoria()
        if nombre:
            self.libro_actual = nombre
            self.capitulo_actual = 1
            self.dropdown_libro.value = nombre
            self.dropdown_capitulo.options = self._opciones_capitulos()
            self.dropdown_capitulo.value = "1"

        self.modo_vista = "Libro"
        self.dropdown_modo.value = self.modo_vista
        self.verso_seleccionado = None
        self.ultimo_verso_accionado = None
        self._guardar_ultima_lectura()
        self._refrescar_lectura_actual()

    def ir_a_capitulo(self, capitulo):
        self._limpiar_seleccion_transitoria()
        self.capitulo_actual = capitulo
        self.dropdown_capitulo.value = str(capitulo)
        self.modo_vista = "Versiculos"
        self.dropdown_modo.value = self.modo_vista
        self.verso_seleccionado = None
        self.ultimo_verso_accionado = None
        self._guardar_ultima_lectura()
        self._refrescar_lectura_actual()

    def ir_a_capitulo_de_libro(self, libro, capitulo):
        self.libro_actual = libro
        self.dropdown_libro.value = libro
        self.dropdown_capitulo.options = self._opciones_capitulos()
        self.ir_a_capitulo(capitulo)

    def marcar_para_colorear(self, clave, mensaje="Seleccione un resaltado."):
        self.seleccion_texto_resaltado = None
        self._alternar_objetivo_color(clave, mensaje)
        self.objetivos_color = {clave}
        self.objetivo_color = clave
        self._refrescar_lectura_colores({clave})
        self._programar_selector_color_contextual({clave})

    def seleccionar_color(self, nombre):
        if self._solo_lectura() or not self._puede("biblia_color"):
            return
        nombre = self._normalizar_color(nombre)
        self.color_actual = nombre
        objetivos = set(self._objetivos_color_activos())

        if objetivos:
            for objetivo in objetivos:
                clave, parte, indice = self._parsear_objetivo_color(objetivo)
                self._aplicar_color_identificador(clave, parte, indice, nombre)
            self._programar_guardado_resaltados()
            self._limpiar_objetivos_color()
            self._refrescar_lectura_colores(objetivos)
            return


    def _parsear_objetivo_color(self, objetivo):
        if "|DIG|" not in objetivo:
            return objetivo, "completo", None

        clave, indice = objetivo.rsplit("|DIG|", 1)
        try:
            return clave, "digito", int(indice)
        except ValueError:
            return clave, "digito", 0

    def _quitar_colores_seleccionados(self, objetivos):
        if self._solo_lectura() or not self._puede("biblia_color"):
            return
        objetivos = set(objetivos)
        for objetivo in objetivos:
            clave, parte, indice = self._parsear_objetivo_color(objetivo)

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
                continue

            self.resaltados.pop(clave, None)
            libro, capitulo, versiculo = self._desarmar_clave_verso(clave)
            if libro and capitulo and versiculo:
                # Tocar un versiculo en modo quitar elimina todo lo que se ve
                # en ese versiculo, incluidas las palabras resaltadas.
                self.resaltados.pop(self._clave_resaltado_palabras(clave), None)

        self._programar_guardado_resaltados()
        self._limpiar_objetivos_color()
        self._snack("Resaltado quitado.")
        self._refrescar_lectura_colores(objetivos)

    def _actualizar_versiculo_seleccionado(self, verso):
        """Cambia el borde del versiculo tocado sin reconstruir el capitulo."""
        control = self._controles_versiculos.get(verso)
        if control is None:
            return False

        resaltado = self.resaltados.get(verso)
        seleccionado = self.verso_seleccionado == verso
        seleccionado_multiple = verso in self.versos_compartir
        marcado = self._esta_marcado_para_color(verso)

        control.bgcolor = (
            self._hex_color(resaltado)
            if resaltado
            else "#FFF7D6"
            if seleccionado_multiple
            else MARRON_PERLA if seleccionado or marcado else ft.Colors.WHITE
        )
        control.border = ft.Border.all(
            2 if seleccionado or marcado or seleccionado_multiple else 1,
            NARANJA_ACCENTO
            if seleccionado_multiple
            else MARRON_ACENTO
            if seleccionado or marcado
            else BORDER_MARRON
            if self._es_blanco_borde(resaltado)
            else ft.Colors.GREY_300,
        )

        try:
            fila = control.content
            fila.controls[0].visible = seleccionado_multiple
            fila.controls[1].visible = marcado
            texto_control = fila.controls[-1]
            color_texto = self._texto_color(resaltado)
            if getattr(texto_control, "spans", None):
                for span in texto_control.spans:
                    estilo = getattr(span, "style", None)
                    if estilo and estilo.color != COLOR_PALABRAS_CORDERO:
                        estilo.color = color_texto
            else:
                texto_control.color = color_texto
            control.update()
        except (AttributeError, RuntimeError, AssertionError):
            return False

        return True

    def seleccionar_verso(self, verso, evento=None):
        verso_anterior = self.verso_seleccionado
        if verso == self.verso_seleccionado:
            self.objetivos_color.clear()
            self.verso_seleccionado = None
            self.objetivo_color = None
        else:
            # Fuera del modo multiple solo puede quedar un versiculo seleccionado.
            self.objetivos_color = {verso}
            self.objetivo_color = verso
            self.verso_seleccionado = verso

        self.objetivo_color_control = None
        self.ultimo_verso_accionado = verso

        actualizados = all(
            self._actualizar_versiculo_seleccionado(clave)
            for clave in {clave for clave in (verso_anterior, verso) if clave}
        )
        if actualizados:
            return

        self._refrescar_lectura_colores()

    def doble_tap_verso(self, verso):
        if verso in self.resaltados:
            self.resaltados.pop(verso, None)
            self._programar_guardado_resaltados()
            self.verso_seleccionado = None
            self.ultimo_verso_accionado = None
            self._snack("Resaltado del versiculo quitado.")
            self._refrescar_lectura_colores({verso})
            return

        self.codificar_versiculo_biblia(verso)

    def seleccionar_verso_para_color_completo(self, verso):
        self.marcar_para_colorear(
            verso,
            "Versiculo marcado. Seleccione un resaltado.",
        )

    def seleccionar_capitulo_completo_para_color(self, libro, capitulo):
        clave = self._clave_capitulo(libro, capitulo)
        self.marcar_para_colorear(
            clave,
            "Capítulo marcado. Selecciona un resaltado.",
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
        control.bgcolor = MARRON_PERLA if seleccionado else color_fondo
        control.border = ft.Border.all(
            2 if seleccionado else 1,
            MARRON_ACENTO
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

        self.objetivo_color = clave
        self.objetivo_color_control = control
        self.objetivos_color = {clave}
        self.verso_seleccionado = None
        if control:
            self._aplicar_estilo_capitulo_control(
                control,
                libro,
                capitulo,
                self.resaltados.get(clave),
                seleccionado=True,
            )
        else:
            self._snack("Capítulo marcado. Selecciona un resaltado.")

        if not control:
            self._render_lectura()
            self.page.update()
        self._programar_selector_color_contextual({clave})

    def seleccionar_verso_para_color(self, verso):
        clave = self._clave_numero_verso(verso)

        self.objetivo_color = clave
        self.objetivos_color = {clave}
        self.verso_seleccionado = None
        self.ultimo_verso_accionado = verso
        self._snack("Numero marcado. Seleccione un resaltado.")

        self._refrescar_lectura_colores({clave})
        self._programar_selector_color_contextual({clave})

    def elegir_modo_color_identificador(self, clave):
        numero = self._numero_desde_clave_identificador(clave)
        es_doble = len(str(numero)) >= 2

        def cerrar(e=None):
            self._cerrar_dialogo_biblia(dialog)

        def elegir(parte, indice=None):
            cerrar()

            if parte == "completo":
                destino = clave
            else:
                destino = f"{clave}|DIG|{indice}"

            self._alternar_objetivo_color(destino, "Numero seleccionado.")
            self._refrescar_lectura_colores({destino})
            self._programar_selector_color_contextual({destino})

        def aplicar_auto(e=None):
            cerrar()
            self._aplicar_tres_colores_identificador(clave)

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

        dialog = ft.AlertDialog(
            title=ft.Text(f"Resaltado del numero {numero}"),
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
        self._programar_guardado_resaltados()
        self.objetivo_color = None
        self.objetivo_color_control = None
        self.verso_seleccionado = None
        self._snack("Resaltado quitado.")
        self._refrescar_lectura_colores({clave})

    def quitar_color_objetivo(self):
        if not self.objetivo_color:
            verso = self.verso_seleccionado or self.ultimo_verso_accionado

            if verso and verso in self.resaltados:
                self.resaltados.pop(verso, None)
                self._programar_guardado_resaltados()
                self.verso_seleccionado = None
                self.ultimo_verso_accionado = None
                self._snack("Resaltado del versiculo quitado.")
                self._refrescar_lectura_colores({verso})
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

        self._programar_guardado_resaltados()
        self.objetivo_color = None
        self.objetivo_color_control = None
        self.verso_seleccionado = None
        self._snack("Resaltado quitado.")
        self._refrescar_lectura_colores({clave})

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
        return self.resaltados.get(self._clave_libro(libro))

    def _fondo_libro_resaltado(self, libro):
        return self._hex_color(self._color_libro_resaltado(libro))

    def _texto_libro_resaltado(self, libro):
        color = self._color_libro_resaltado(libro)
        return self._texto_color(color) if color else None

    def seleccionar_libro_para_color(self, libro):
        clave = self._clave_libro(libro)
        self.marcar_para_colorear(
            clave,
            "Libro marcado. Selecciona un resaltado.",
        )

    def quitar_color_libro(self, libro):
        clave_libro = self._clave_libro(libro)

        if clave_libro in self.resaltados:
            self.resaltados.pop(clave_libro, None)
            self._programar_guardado_resaltados()
            self.objetivo_color = None
            self._cache_primer_resaltado = {}
            self._snack("Resaltado del libro quitado.")
            self._refrescar_lectura_actual()
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
            self._snack("Ese libro no tiene resaltados.")
            return

        for clave in claves:
            self.resaltados.pop(clave, None)

        self._programar_guardado_resaltados()
        self.objetivo_color = None
        self.verso_seleccionado = None
        self._cache_primer_resaltado = {}
        self._snack("Resaltados del libro quitados.")
        self._refrescar_lectura_actual()

    def quitar_resaltado_verso(self, verso):
        if verso not in self.resaltados:
            return

        self.resaltados.pop(verso, None)
        self._programar_guardado_resaltados()

        if self.verso_seleccionado == verso:
            self.verso_seleccionado = None

        self.objetivo_color = None
        self.objetivo_color_control = None
        self.ultimo_verso_accionado = verso
        self._refrescar_lectura_colores({verso})
        self._snack("Resaltado quitado.")

    def dialog_versiculos_por_color(self):
        if not self._puede("biblia_marcas"):
            self._snack("Los resaltados requieren el Nivel 3.")
            return
        color_inicial = self.color_actual if self.color_actual in COLORES_RESALTADO else "Amarillo"
        selector = ft.Dropdown(
            label="Resaltado",
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
                f"Versiculos resaltados en {selector.value}",
            )

        def guardar_color(e=None):
            resultados = resultados_color_actual()

            if not resultados:
                self._snack("No hay versiculos para guardar.")
                return

            cerrar()
            self._guardar_resultados_filtrados(
                resultados,
                f"Versiculos resaltados en {selector.value}",
            )

        def compartir_todos(e=None):
            resultados = self._versiculos_marcados_todos_colores()

            if not resultados:
                self._snack("No hay versiculos resaltados para compartir.")
                return

            cerrar()
            self._compartir_resultados_filtrados(
                resultados,
                "Todos los versiculos resaltados",
                incluir_color=True,
            )

        def guardar_todos(e=None):
            resultados = self._versiculos_marcados_todos_colores()

            if not resultados:
                self._snack("No hay versiculos resaltados para guardar.")
                return

            cerrar()
            self._guardar_resultados_filtrados(
                resultados,
                "Todos los versiculos resaltados",
                incluir_color=True,
            )

        def renderizar(e=None):
            color = selector.value
            resultados = self._versiculos_marcados_por_color(color)
            lista.controls.clear()
            resumen.value = f"{len(resultados)} versiculo(s) resaltados en {color}."
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
                        content=ft.Text("No hay versiculos con ese resaltado."),
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
                                "Guardar resaltado",
                                icon=ft.Icons.SAVE_ALT,
                                on_click=guardar_color,
                            ),
                        ],
                    ),
                    ft.Row(
                        wrap=True,
                        spacing=8,
                        run_spacing=8,
                        controls=[
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
            title=ft.Text("Versiculos resaltados"),
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
        ArchivoLocalService.guardar_texto(
            self.page,
            texto,
            titulo,
            "Guardar filtro biblico en el dispositivo",
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

    def codificar_libro_biblia(self, libro_nombre):
        self.dialog_exportar_biblia_codificada(
            alcance_preseleccionado="libro",
            libro_preseleccionado=libro_nombre,
        )

    def codificar_capitulo_biblia(self, libro_nombre, capitulo_numero):
        self.dialog_exportar_biblia_codificada(
            alcance_preseleccionado="capitulos",
            libro_preseleccionado=libro_nombre,
            capitulo_preseleccionado=capitulo_numero,
        )

    def codificar_versiculo_biblia(self, verso):
        partes = verso.split("|")

        if len(partes) != 3:
            self._snack("Versiculo invalido.")
            return

        libro, capitulo, versiculo = partes[0], int(partes[1]), int(partes[2])
        self.dialog_exportar_biblia_codificada(
            alcance_preseleccionado="versiculos",
            libro_preseleccionado=libro,
            capitulo_preseleccionado=capitulo,
            versiculo_preseleccionado=versiculo,
        )

    def _datos_versiculo_activo(self):
        verso = self._verso_activo()

        if not verso and len(self.versos_compartir) == 1:
            verso = next(iter(self.versos_compartir))

        if not verso:
            return None

        partes = verso.split("|")

        if len(partes) != 3:
            return None

        libro, capitulo, versiculo = partes[0], int(partes[1]), int(partes[2])
        texto = self._texto_versiculo(libro, capitulo, versiculo)
        referencia = f"{libro} {capitulo}:{versiculo}"

        return {
            "id": verso,
            "libro": libro,
            "capitulo": capitulo,
            "versiculo": versiculo,
            "referencia": referencia,
            "texto": texto,
        }

    def _versos_rango_capitulos_para_exportar(self, libro_nombre, desde, hasta=None):
        libro = self._libro_por_nombre(libro_nombre)

        if not libro:
            return []

        capitulos = libro.get("capitulos", [])
        inicio = max(1, int(desde or 1))
        final = min(len(capitulos), int(hasta or inicio))

        if final < inicio:
            inicio, final = final, inicio

        resultados = []

        for numero_capitulo in range(inicio, final + 1):
            capitulo = capitulos[numero_capitulo - 1]
            resultados.extend(
                {
                    "libro": libro_nombre,
                    "capitulo": numero_capitulo,
                    "versiculo": numero_versiculo,
                    "texto": texto,
                }
                for numero_versiculo, texto in enumerate(capitulo, start=1)
            )

        return resultados

    def _versos_rango_versiculos_para_exportar(self, libro_nombre, capitulo, desde, hasta=None):
        libro = self._libro_por_nombre(libro_nombre)

        if not libro:
            return []

        capitulos = libro.get("capitulos", [])
        numero_capitulo = int(capitulo or 1)

        if numero_capitulo < 1 or numero_capitulo > len(capitulos):
            return []

        versiculos = capitulos[numero_capitulo - 1]
        inicio = max(1, int(desde or 1))
        final = min(len(versiculos), int(hasta or inicio))

        if final < inicio:
            inicio, final = final, inicio

        return [
            {
                "libro": libro_nombre,
                "capitulo": numero_capitulo,
                "versiculo": numero_versiculo,
                "texto": versiculos[numero_versiculo - 1],
            }
            for numero_versiculo in range(inicio, final + 1)
        ]

    def _versos_libro_para_exportar(self, libro_nombre):
        libro = self._libro_por_nombre(libro_nombre)
        total_capitulos = len(libro.get("capitulos", [])) if libro else 0
        return self._versos_rango_capitulos_para_exportar(libro_nombre, 1, total_capitulos)

    def _versos_rango_libros_para_exportar(self, desde, hasta=None):
        nombres = [libro.get("nombre", "") for libro in self.libros]

        try:
            inicio = nombres.index(desde)
        except ValueError:
            return []

        try:
            final = nombres.index(hasta or desde)
        except ValueError:
            final = inicio

        if final < inicio:
            inicio, final = final, inicio

        resultados = []
        for nombre in nombres[inicio : final + 1]:
            resultados.extend(self._versos_libro_para_exportar(nombre))
        return resultados

    def _versos_biblia_completa_para_exportar(self):
        resultados = []

        for libro in self.libros:
            resultados.extend(self._versos_libro_para_exportar(libro.get("nombre", "")))

        return resultados

    def _opciones_exportacion_codificada(self):
        opciones = []
        seleccion = self._versos_ordenados_para_compartir()

        if seleccion:
            etiqueta = (
                "Versiculo seleccionado"
                if len(seleccion) == 1
                else f"{len(seleccion)} versiculos seleccionados"
            )
            opciones.append(("seleccion", etiqueta))

        opciones.extend(
            [
                ("versiculos", "Versiculos por rango"),
                ("capitulos", "Capitulos por rango"),
                ("libros", "Libros por rango"),
                ("libro", "Libro completo"),
                ("biblia_completa", "Biblia completa"),
            ]
        )

        return opciones

    def _versos_para_exportacion_codificada(
        self,
        alcance,
        libro_nombre=None,
        libro_hasta=None,
        capitulo_desde=None,
        capitulo_hasta=None,
        versiculo_desde=None,
        versiculo_hasta=None,
    ):
        if alcance == "seleccion":
            return self._versos_ordenados_para_compartir()

        if alcance == "versiculos":
            return self._versos_rango_versiculos_para_exportar(
                libro_nombre,
                capitulo_desde,
                versiculo_desde,
                versiculo_hasta,
            )

        if alcance == "capitulos":
            return self._versos_rango_capitulos_para_exportar(
                libro_nombre,
                capitulo_desde,
                capitulo_hasta,
            )

        if alcance == "libro":
            return self._versos_libro_para_exportar(libro_nombre)

        if alcance == "libros":
            return self._versos_rango_libros_para_exportar(libro_nombre, libro_hasta)

        if alcance == "biblia_completa":
            return self._versos_biblia_completa_para_exportar()

        return []

    def dialog_exportar_biblia_codificada(
        self,
        e=None,
        alcance_preseleccionado=None,
        libro_preseleccionado=None,
        capitulo_preseleccionado=None,
        versiculo_preseleccionado=None,
    ):
        if self._solo_lectura():
            self._snack("El Nivel 1 permite solo lectura.")
            return
        opciones_alcance = self._opciones_exportacion_codificada()

        if not opciones_alcance:
            self._snack("Seleccione un versiculo, capitulo o libro para exportar.")
            return

        self._limpiar_flotantes_biblia()
        dialog_ref = {"control": None}
        libro_inicial = (
            libro_preseleccionado
            if self._libro_por_nombre(libro_preseleccionado)
            else self.libro_actual
            if self._libro_por_nombre(self.libro_actual)
            else self.libros[0]["nombre"]
        )
        capitulo_inicial = int(capitulo_preseleccionado or self.capitulo_actual or 1)
        versiculo_inicial = int(versiculo_preseleccionado or 1)
        ancho_page = getattr(self.page, "width", None) or 760
        ancho_selector = int(min(480, max(260, ancho_page - 96)))
        alcances_validos = {clave for clave, _etiqueta in opciones_alcance}
        alcance_actual = {
            "valor": (
                alcance_preseleccionado
                if alcance_preseleccionado in alcances_validos
                else opciones_alcance[0][0]
            )
        }
        botones_alcance = {}
        libro_hasta_personalizado = {"valor": False}
        selector_libro = ft.Dropdown(
            label="Libro",
            options=[ft.dropdown.Option(libro["nombre"]) for libro in self.libros],
            value=libro_inicial,
            width=ancho_selector,
            height=52,
            dense=True,
            menu_height=240,
            menu_width=ancho_selector,
            expand=False,
        )
        selector_libro_hasta = ft.Dropdown(
            label="Hasta libro",
            options=[ft.dropdown.Option(libro["nombre"]) for libro in self.libros],
            value=libro_inicial,
            width=ancho_selector,
            height=52,
            dense=True,
            menu_height=240,
            menu_width=ancho_selector,
            expand=False,
        )
        selector_capitulo_desde = ft.TextField(
            label="Desde capitulo",
            value=str(capitulo_inicial),
            width=ancho_selector,
            height=52,
            dense=True,
        )
        selector_capitulo_hasta = ft.TextField(
            label="Hasta capitulo",
            value=str(capitulo_inicial),
            width=ancho_selector,
            height=52,
            dense=True,
        )
        selector_versiculo_desde = ft.TextField(
            label="Desde versiculo",
            value=str(versiculo_inicial),
            width=ancho_selector,
            height=52,
            dense=True,
        )
        selector_versiculo_hasta = ft.TextField(
            label="Hasta versiculo",
            value=str(versiculo_inicial),
            width=ancho_selector,
            height=52,
            dense=True,
        )
        selector_formato = ft.Dropdown(
            label="Formato",
            options=[
                ft.dropdown.Option("txt", text="TXT"),
                ft.dropdown.Option("pdf", text="PDF"),
            ],
            value="txt",
            width=150,
            height=52,
            dense=True,
            menu_height=120,
            expand=False,
        )
        bloque_capitulos = ft.Column(
            tight=True,
            spacing=8,
            controls=[selector_capitulo_desde, selector_capitulo_hasta],
        )
        bloque_versiculos = ft.Column(
            tight=True,
            spacing=8,
            controls=[selector_versiculo_desde, selector_versiculo_hasta],
        )
        fila_libros = ft.Column(
            tight=True,
            spacing=10,
            controls=[selector_libro, selector_libro_hasta],
        )
        contenido = ft.ListView(
            expand=True,
            spacing=12,
            padding=0,
        )
        descripcion_alcance = ft.Text(size=12, color=TEXTO_SECUNDARIO)

        def numero_valido(valor, maximo, predeterminado=1):
            try:
                numero = int(str(valor).strip())
            except (TypeError, ValueError):
                numero = predeterminado
            return max(1, min(maximo, numero))

        def actualizar_versiculos(reiniciar=False):
            libro = self._libro_por_nombre(selector_libro.value)
            capitulos = libro.get("capitulos", []) if libro else []
            numero_capitulo = numero_valido(
                selector_capitulo_desde.value,
                max(1, len(capitulos)),
            )
            selector_capitulo_desde.value = str(numero_capitulo)
            if reiniciar:
                selector_capitulo_hasta.value = str(numero_capitulo)
            versiculos = capitulos[numero_capitulo - 1] if 0 < numero_capitulo <= len(capitulos) else []
            maximo = max(1, len(versiculos))
            if reiniciar:
                selector_versiculo_desde.value = "1"
                selector_versiculo_hasta.value = str(maximo)
            else:
                selector_versiculo_desde.value = str(numero_valido(selector_versiculo_desde.value, maximo))
                selector_versiculo_hasta.value = str(numero_valido(selector_versiculo_hasta.value, maximo))

        def actualizar_capitulos(reiniciar=False):
            libro = self._libro_por_nombre(selector_libro.value)
            total = len(libro.get("capitulos", [])) if libro else 0
            actual = self.capitulo_actual if selector_libro.value == self.libro_actual else 1
            selector_capitulo_desde.value = str(numero_valido(selector_capitulo_desde.value, max(1, total), actual))
            if reiniciar:
                selector_capitulo_hasta.value = selector_capitulo_desde.value
            else:
                selector_capitulo_hasta.value = str(
                    numero_valido(selector_capitulo_hasta.value, max(1, total), selector_capitulo_desde.value)
                )
            actualizar_versiculos(reiniciar=reiniciar and versiculo_preseleccionado is None)

        def actualizar_visibilidad(ev=None):
            alcance = alcance_actual["valor"]
            usa_libro = alcance in {"versiculos", "capitulos", "libro", "libros"}
            fila_libros.visible = usa_libro
            selector_libro_hasta.visible = alcance == "libros"
            bloque_capitulos.visible = alcance in {"versiculos", "capitulos"}
            selector_capitulo_hasta.visible = alcance == "capitulos"
            bloque_versiculos.visible = alcance == "versiculos"

            descripciones = {
                "seleccion": "Se exportaran los versiculos seleccionados en la lectura.",
                "versiculos": "Elija un libro, un capitulo y el rango de versiculos.",
                "capitulos": "Elija un libro y el rango de capitulos.",
                "libros": "Elija desde que libro hasta que libro desea exportar.",
                "libro": "Elija el libro completo que desea exportar.",
                "biblia_completa": "Se exportara toda la Biblia; no hace falta elegir rangos.",
            }
            descripcion_alcance.value = descripciones.get(alcance, "")
            for clave, boton in botones_alcance.items():
                activo = clave == alcance
                boton.style = ft.ButtonStyle(
                    color=ft.Colors.WHITE if activo else PURPURA_ACCENTO,
                    bgcolor=PURPURA_ACCENTO if activo else ft.Colors.with_opacity(0.5, ft.Colors.WHITE),
                    side=ft.BorderSide(1, PURPURA_ACCENTO),
                    shape=ft.RoundedRectangleBorder(radius=12),
                )
            if hasattr(contenido, "update"):
                try:
                    contenido.update()
                except Exception:
                    pass
            try:
                self.page.update()
            except Exception:
                pass

        def al_cambiar_libro(ev=None):
            actualizar_capitulos(reiniciar=True)
            if not libro_hasta_personalizado["valor"]:
                selector_libro_hasta.value = selector_libro.value
            actualizar_visibilidad()

        def al_cambiar_libro_hasta(ev=None):
            libro_hasta_personalizado["valor"] = True
            actualizar_visibilidad()

        def seleccionar_alcance(clave):
            alcance_actual["valor"] = clave
            actualizar_visibilidad()

        for clave, etiqueta in opciones_alcance:
            botones_alcance[clave] = ft.OutlinedButton(
                etiqueta,
                on_click=lambda ev, valor=clave: seleccionar_alcance(valor),
            )

        selector_libro.on_select = al_cambiar_libro
        selector_libro_hasta.on_select = al_cambiar_libro_hasta
        actualizar_capitulos(reiniciar=True)
        actualizar_visibilidad()

        def cerrar(ev=None):
            self._cerrar_flotante_biblia(dialog_ref["control"])

        def descargar(ev=None):
            libro = self._libro_por_nombre(selector_libro.value)
            capitulos = libro.get("capitulos", []) if libro else []
            capitulo_desde = numero_valido(selector_capitulo_desde.value, max(1, len(capitulos)))
            capitulo_hasta = numero_valido(selector_capitulo_hasta.value, max(1, len(capitulos)))
            versiculos_capitulo = (
                capitulos[capitulo_desde - 1]
                if 0 < capitulo_desde <= len(capitulos)
                else []
            )
            versiculo_desde = numero_valido(selector_versiculo_desde.value, max(1, len(versiculos_capitulo)))
            versiculo_hasta = numero_valido(selector_versiculo_hasta.value, max(1, len(versiculos_capitulo)))
            versos = self._versos_para_exportacion_codificada(
                alcance_actual["valor"],
                libro_nombre=selector_libro.value,
                libro_hasta=selector_libro_hasta.value,
                capitulo_desde=capitulo_desde,
                capitulo_hasta=capitulo_hasta,
                versiculo_desde=versiculo_desde,
                versiculo_hasta=versiculo_hasta,
            )

            if not versos:
                self._snack("No hay versiculos validos para exportar.")
                return

            try:
                ruta = self.exportador_biblia_codificada.exportar(
                    versos,
                    formato=selector_formato.value,
                    incluir_suma=False,
                    incluir_texto=False,
                )
            except Exception as error:
                self._snack(f"No se pudo preparar la exportacion: {error}")
                return

            cerrar()
            descargar_archivo(
                self.page,
                ruta,
                f"Descargar Biblia codificada ({str(selector_formato.value).upper()})",
            )

        contenido.controls = [
            ft.Text(
                "Elija versiculo, versiculos, capitulo, capitulos, libro o Biblia completa. "
                "Se descarga solo codigo numerico: _ entre letras y __ entre palabras.",
                size=12,
                color=TEXTO_SECUNDARIO,
            ),
            ft.Text("Seccion a exportar", size=13, weight=ft.FontWeight.BOLD),
            ft.Row(
                wrap=True,
                spacing=8,
                run_spacing=8,
                controls=list(botones_alcance.values()),
            ),
            descripcion_alcance,
            fila_libros,
            bloque_capitulos,
            bloque_versiculos,
            selector_formato,
        ]
        dialog = self._crear_flotante_biblia(
            "Codificar Biblia en numeros",
            contenido,
            [
                ft.ElevatedButton("Descargar", icon=ft.Icons.DOWNLOAD, on_click=descargar),
                ft.TextButton("Cancelar", on_click=cerrar),
            ],
            ancho=560,
            alto=620,
        )
        dialog_ref["control"] = dialog
        self.page.overlay.append(dialog)
        self.page.update()

    def _cerrar_flotante_biblia(self, control):
        if control is None:
            return

        try:
            control.open = False
        except Exception:
            pass

        try:
            if hasattr(self.page, "close"):
                self.page.close(control)
        except Exception:
            pass

        try:
            while control in self.page.overlay:
                self.page.overlay.remove(control)
        except Exception:
            pass

        try:
            self.page.update()
        except Exception:
            pass

    def _programar_guardado_resaltados(self):
        """Agrupa cambios seguidos y evita bloquear el gesto de resaltado."""
        self._cache_primer_resaltado = {}
        self._version_guardado_resaltados += 1
        version = self._version_guardado_resaltados
        try:
            self.page.run_task(self._guardar_resaltados_diferido, version)
        except (RuntimeError, AssertionError, AttributeError):
            guardar_resaltados(self.resaltados)

    async def _guardar_resaltados_diferido(self, version):
        await asyncio.sleep(0.2)
        if version != self._version_guardado_resaltados:
            return

        datos = copy.deepcopy(self.resaltados)
        try:
            await asyncio.to_thread(guardar_resaltados, datos)
        except Exception:
            # La vista ya se actualizo; un fallo de disco no debe romper la lectura.
            return

    def _limpiar_flotantes_biblia(self):
        titulos_biblia = {
            "Guardar",
            "Compartir",
            "Guardar tarjeta",
            "Tarjeta del versiculo",
            "Tarjeta del versículo",
            "Guardado correctamente",
            "Pintar o despintar",
        }

        for control in list(getattr(self.page, "overlay", [])):
            titulo = ""

            try:
                title = getattr(control, "title", None)
                titulo = getattr(title, "value", "") or getattr(title, "text", "") or ""
            except Exception:
                titulo = ""

            if getattr(control, "data", None) == "biblia_flotante" or titulo in titulos_biblia:
                self._cerrar_flotante_biblia(control)

    def _crear_flotante_biblia(self, titulo, contenido, acciones, ancho=None, alto=None):
        ancho_page = getattr(self.page, "width", None) or 760
        alto_page = getattr(self.page, "height", None) or 720
        es_movil = self.responsive.is_mobile()
        ancho_modal = min(ancho or 620, max(300, ancho_page - 32))
        alto_preferido = alto or (alto_page - 80)

        # En celular una fila de acciones se sale del modal. Las apilamos y
        # reservamos espacio para que cada opcion conserve su ancho legible.
        if es_movil and len(acciones) > 1:
            alto_preferido = max(alto_preferido, 220 + len(acciones) * 58)

        alto_modal = min(alto_preferido, max(320, alto_page - 40))
        acciones_control = (
            ft.Column(
                tight=True,
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.END,
                controls=acciones,
            )
            if es_movil
            else ft.Row(
                alignment=ft.MainAxisAlignment.END,
                spacing=10,
                controls=acciones,
            )
        )

        return ft.Container(
            data="biblia_flotante",
            width=ancho_page,
            height=alto_page,
            bgcolor=ft.Colors.with_opacity(0.62, ft.Colors.BLACK),
            alignment=ft.Alignment(0, 0),
            content=ft.Container(
                width=ancho_modal,
                height=alto_modal,
                padding=ft.Padding(24, 22, 24, 18),
                border_radius=26,
                bgcolor=PERLA_PANEL,
                shadow=sombra_suave(),
                content=ft.Column(
                    spacing=14,
                    controls=[
                        ft.Text(
                            titulo,
                            size=24,
                            weight=ft.FontWeight.W_500,
                            color=TEXTO_PRINCIPAL,
                        ),
                        ft.Container(
                            expand=True,
                            alignment=ft.Alignment(0, 0),
                            content=contenido,
                        ),
                        acciones_control,
                    ],
                ),
            ),
        )

    def dialog_compartir_biblia(self):
        if self._solo_lectura():
            self._snack("El Nivel 1 permite solo lectura.")
            return
        datos = self._datos_tarjeta_biblia_actual()
        versos = self._versos_ordenados_para_compartir()

        if not datos and not versos:
            self._snack("Seleccione un versiculo.")
            return

        self._limpiar_flotantes_biblia()
        dialog_ref = {"control": None}

        def cerrar(e=None):
            self._cerrar_flotante_biblia(dialog_ref["control"])

        def compartir_texto_accion(e=None):
            cerrar()
            self.compartir_seleccion()

        def compartir_imagen(e=None):
            if not datos:
                self._snack("Seleccione al menos un versiculo.")
                return

            cerrar()
            self.compartir_tarjeta_versiculo()

        acciones = [
            ft.ElevatedButton("Texto", icon=ft.Icons.TEXT_SNIPPET, on_click=compartir_texto_accion),
        ]

        if datos:
            acciones.append(
                ft.ElevatedButton("Imagen de tarjeta", icon=ft.Icons.IMAGE, on_click=compartir_imagen)
            )

        acciones.append(ft.TextButton("Cancelar", on_click=cerrar))

        dialog = self._crear_flotante_biblia(
            "Compartir",
            ft.Text("Elija como quiere compartir la seleccion."),
            acciones,
            ancho=520,
            alto=260,
        )

        dialog_ref["control"] = dialog
        self.page.overlay.append(dialog)
        self.page.update()

    def _texto_dorado_tarjeta(self, texto, size, max_lines=None):
        return ft.Text(
            texto,
            text_align=ft.TextAlign.CENTER,
            max_lines=max_lines,
            overflow=ft.TextOverflow.ELLIPSIS,
            style=ft.TextStyle(
                size=size,
                weight=ft.FontWeight.BOLD,
                color="#FFE47A",
                shadow=[
                    ft.BoxShadow(
                        blur_radius=16,
                        color=ft.Colors.with_opacity(0.70, "#E8AA23"),
                        offset=ft.Offset(0, 0),
                    ),
                    ft.BoxShadow(
                        blur_radius=3,
                        color=ft.Colors.with_opacity(0.55, "#4A2100"),
                        offset=ft.Offset(2, 3),
                    ),
                ],
            ),
        )

    def _control_tarjeta_versiculo(self, datos, ancho):
        ancho = max(300, min(float(ancho or 720), 760))
        alto = ancho * 2 / 3
        largo_texto = len(datos["texto"])
        ref_size = max(24, min(44, ancho * 0.058))
        texto_size = max(
            15,
            min(
                34,
                ancho * (0.052 if largo_texto < 130 else 0.044 if largo_texto < 230 else 0.036),
            ),
        )

        return ft.Container(
            width=ancho,
            height=alto,
            border_radius=18,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            shadow=sombra_suave(),
            content=ft.Stack(
                controls=[
                    ft.Image(
                        src="tarjeta_versiculo_base.png",
                        width=ancho,
                        height=alto,
                        fit=ft.BoxFit.COVER,
                    ),
                    ft.Container(
                        left=ancho * 0.10,
                        right=ancho * 0.10,
                        top=alto * 0.11,
                        content=self._texto_dorado_tarjeta(datos["referencia"], ref_size, max_lines=1),
                    ),
                    ft.Container(
                        left=ancho * 0.12,
                        right=ancho * 0.12,
                        top=alto * 0.23,
                        height=2,
                        bgcolor=ft.Colors.with_opacity(0.82, "#FFE47A"),
                    ),
                    ft.Container(
                        left=ancho * 0.09,
                        right=ancho * 0.09,
                        top=alto * 0.34,
                        content=self._texto_dorado_tarjeta(datos["texto"], texto_size, max_lines=6),
                    ),
                ],
            ),
        )

    def _generar_archivo_tarjeta(self, datos, incluir_base64=False):
        # La captura de controles se ve diminuta en Android. El JPG se compone
        # directamente para conservar la proporción y el tamaño del texto.
        return datos_tarjeta_versiculo(
            datos["referencia"],
            datos["texto"],
            incluir_base64=incluir_base64,
        )

    def dialog_tarjeta_versiculo(self, modo=None):
        datos = self._datos_tarjeta_biblia_actual()

        if not datos:
            self._snack("Seleccione un versiculo.")
            return

        self._limpiar_flotantes_biblia()
        ancho_page = getattr(self.page, "width", None) or 760
        alto_page = getattr(self.page, "height", None) or 720
        ancho_tarjeta = min(560, max(300, ancho_page - 96))
        alto_contenido = min(620, max(420, alto_page - 150))
        dialogos_tarjeta = {"principal": None, "selector": None}

        def crear_flotante(titulo, contenido, acciones, ancho=None, alto=None):
            return self._crear_flotante_biblia(
                titulo,
                contenido,
                acciones,
                ancho=ancho,
                alto=alto,
            )

        def cerrar_flotante(control):
            self._cerrar_flotante_biblia(control)

        def cerrar(e=None):
            cerrar_flotante(dialogos_tarjeta.get("selector"))
            cerrar_flotante(dialogos_tarjeta.get("principal"))
            dialogos_tarjeta["selector"] = None
            dialogos_tarjeta["principal"] = None
            self.page.update()

        def capturar(incluir_base64=False):
            try:
                return self._generar_archivo_tarjeta(
                    datos,
                    incluir_base64=incluir_base64,
                )
            except Exception as error:
                self._snack(f"No se pudo preparar la tarjeta: {error}")
                return None

        def guardar_imagen(e=None):
            imagen = capturar(incluir_base64=False)
            if not imagen:
                return
            cerrar()
            ArchivoLocalService.guardar_archivo(
                self.page,
                imagen["archivo"],
                "Guardar tarjeta biblica en el dispositivo",
            )

        def compartir_imagen(e=None):
            imagen = capturar(incluir_base64=False)

            if not imagen:
                return

            cerrar()
            compartir_archivo(
                self.page,
                imagen["archivo"],
                f"Tarjeta {datos['referencia']}",
                imagen["mime"],
            )

        tarjeta = self._control_tarjeta_versiculo(datos, ancho_tarjeta)
        controles = [tarjeta]

        acciones = [ft.TextButton("Cerrar", on_click=cerrar)]

        if modo in (None, "guardar"):
            acciones.append(
                ft.ElevatedButton("Guardar", icon=ft.Icons.SAVE_ALT, on_click=guardar_imagen)
            )

        dialog = crear_flotante(
            "Tarjeta del versiculo",
            ft.Container(
                width=ancho_tarjeta,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=controles,
                ),
            ),
            acciones,
            ancho=ancho_tarjeta + 64,
            alto=alto_contenido,
        )

        self.page.overlay.append(dialog)
        dialogos_tarjeta["principal"] = dialog
        self.page.update()

    def guardar_tarjeta_versiculo(self):
        self.dialog_tarjeta_versiculo(modo="guardar")

    def compartir_tarjeta_versiculo(self):
        self.dialog_tarjeta_versiculo(modo="compartir")

    def copiar_seleccion(self):
        versos = self._versos_ordenados_para_compartir()

        if versos:
            copiar_al_portapapeles(self.page, self._texto_versos_compartir(versos))
            self._snack("Copiado correctamente")
            return

        verso = self._verso_activo()

        if not verso:
            self._snack("Seleccione un versiculo.")
            return

        partes = verso.split("|")
        libro, capitulo, versiculo = partes[0], int(partes[1]), int(partes[2])
        texto = self._texto_versiculo(libro, capitulo, versiculo)
        copiar_al_portapapeles(self.page, f"{libro} {capitulo}:{versiculo} {texto}")
        self._snack("Copiado correctamente")

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
        texto = self._texto_capitulo_actual()

        if not texto:
            self._snack("No hay capitulo para copiar.")
            return

        copiar_al_portapapeles(self.page, texto)
        self._snack("Copiado correctamente")

    def _texto_capitulo_actual(self):
        capitulo = self._capitulo_actual()

        if not capitulo:
            return ""

        lineas = [f"{self.libro_actual} {self.capitulo_actual}", ""]
        lineas.extend(
            f"{indice}. {texto}"
            for indice, texto in enumerate(capitulo, start=1)
        )
        return "\n".join(lineas)

    def _texto_libro_actual(self):
        libro = self._libro_actual()

        if not libro:
            return ""

        lineas = [libro["nombre"], ""]
        for numero_capitulo, versiculos in enumerate(libro["capitulos"], start=1):
            lineas.append(f"{libro['nombre']} {numero_capitulo}")
            lineas.extend(
                f"{numero_versiculo}. {texto}"
                for numero_versiculo, texto in enumerate(versiculos, start=1)
            )
            lineas.append("")

        return "\n".join(lineas).rstrip()

    def copiar_libro(self):
        texto = self._texto_libro_actual()

        if not texto:
            self._snack("No hay libro para copiar.")
            return

        copiar_al_portapapeles(self.page, texto)
        self._snack("Copiado correctamente")

    def _ayuda_copiar_contexto(self):
        if self.modo_vista == "Versiculos":
            return "Copiar versiculo seleccionado"
        if self.modo_vista == "Capitulos":
            return "Copiar capitulo actual"
        return "Copiar libro actual"

    def copiar_contexto_lectura(self):
        if self._solo_lectura():
            self._snack("El Nivel 1 permite solo lectura.")
            return
        if self.modo_vista == "Versiculos":
            self.copiar_seleccion()
            return

        if self.modo_vista == "Capitulos":
            self.copiar_capitulo()
            return

        self.copiar_libro()

    def _grupos_resultados_busqueda(self, resultados):
        actuales = [
            resultado
            for resultado in resultados
            if resultado.get("libro") == self.libro_actual
        ]
        restantes = [
            resultado
            for resultado in resultados
            if resultado.get("libro") != self.libro_actual
        ]

        grupos = []
        if actuales:
            grupos.append((f"Libro actual: {self.libro_actual} ({len(actuales)})", actuales))

        libro_actual = None
        grupo_actual = []
        for resultado in restantes:
            libro = resultado.get("libro", "")
            if libro != libro_actual:
                if grupo_actual:
                    grupos.append((f"{libro_actual} ({len(grupo_actual)})", grupo_actual))
                libro_actual = libro
                grupo_actual = []
            grupo_actual.append(resultado)

        if grupo_actual:
            grupos.append((f"{libro_actual} ({len(grupo_actual)})", grupo_actual))

        return grupos

    def _control_resultado_busqueda(self, resultado, al_abrir=None):
        vid = verso_id(
            resultado["libro"],
            resultado["capitulo"],
            resultado["versiculo"],
        )
        seleccionado_multiple = vid in self.versos_compartir

        def abrir(ev=None):
            if al_abrir:
                al_abrir()
                return

            self.ir_a_resultado(resultado)

        return ft.Container(
            padding=8,
            bgcolor=(
                "#FFF7D6"
                if seleccionado_multiple
                else ft.Colors.WHITE
            ),
            border=ft.Border.all(
                2 if seleccionado_multiple else 1,
                NARANJA_ACCENTO
                if seleccionado_multiple
                else ft.Colors.GREY_300,
            ),
            border_radius=6,
            on_click=(
                (lambda e, v=vid: self.toggle_verso_compartir(v))
                if self.modo_compartir_multiple
                else abrir
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
                        on_click=abrir,
                    ),
                ],
            ),
        )

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
        ArchivoLocalService.guardar_texto(
            self.page,
            texto,
            nombre_default,
            "Guardar busqueda biblica en el dispositivo",
        )

    def ir_a_resultado(self, resultado):
        self._limpiar_seleccion_transitoria()
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
        self._refrescar_lectura_actual()

    def _verso_activo(self):
        return self.verso_seleccionado or self.ultimo_verso_accionado

    def _texto_versiculo(self, libro_nombre, capitulo, versiculo):
        for libro in self.libros:
            if libro["nombre"] != libro_nombre:
                continue

            return libro["capitulos"][capitulo - 1][versiculo - 1]

        return ""

    def recargar(self):
        self._limpiar_seleccion_transitoria()
        self._version_guardado_resaltados += 1
        self.libros = BibliaService.libros()
        self.resaltados = cargar_resaltados()
        self.comentarios = cargar_comentarios()
        self._rangos_seleccion_lectura.clear()
        self._random_candidatos_cache.clear()
        self._random_usados_por_categoria.clear()
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
        self._refrescar_lectura_actual()

    def _snack(self, mensaje):
        barra = getattr(self, "_snack_bar_biblia", None)
        if barra is None:
            barra = self._preparar_snack_biblia()

        contenido = getattr(barra, "content", None)
        if isinstance(contenido, ft.Text):
            contenido.value = mensaje
        barra.open = True
        try:
            self.page.update(barra)
        except (RuntimeError, AssertionError, AttributeError):
            self.page.snack_bar = barra
            self.page.update()

    def _preparar_snack_biblia(self):
        barra = getattr(self, "_snack_bar_biblia", None)
        if barra is None:
            barra = ft.SnackBar(content=ft.Text(""), open=False)
            self._snack_bar_biblia = barra
            self.page.snack_bar = barra
        return barra
