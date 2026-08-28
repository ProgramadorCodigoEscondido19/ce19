import json
import re
import threading
import unicodedata
from pathlib import Path

from logica.biblia import cargar_biblia, crear_indice_busqueda

DATOS_DIR = Path("datos")
ULTIMA_LECTURA_ARCHIVO = DATOS_DIR / "ultima_lectura_biblia.json"
HISTORIAL_REFERENCIAS_ARCHIVO = DATOS_DIR / "historial_referencias_biblia.json"

class BibliaService:
    """Servicio de Biblia: carga, búsqueda y referencias.

    Mantiene cache en memoria para evitar releer el JSON de Biblia en cada refresco.
    No depende de Flet, por eso se puede probar aparte.
    """

    _cache_libros = None
    _cache_indice_busqueda = None
    _cache_libros_por_nombre = None
    _bloqueo_indice_busqueda = threading.Lock()

    @classmethod
    def normalizar(cls, texto):
        limpio = unicodedata.normalize("NFD", str(texto or ""))
        limpio = "".join(c for c in limpio if unicodedata.category(c) != "Mn")
        return limpio.strip().lower()

    @classmethod
    def libros(cls, refrescar=False):
        if refrescar or cls._cache_libros is None:
            cls._cache_libros = cargar_biblia() or []
            cls._cache_indice_busqueda = None
            cls._cache_libros_por_nombre = None
        return cls._cache_libros

    @classmethod
    def indice_busqueda(cls):
        with cls._bloqueo_indice_busqueda:
            if cls._cache_indice_busqueda is None:
                cls._cache_indice_busqueda = crear_indice_busqueda(cls.libros())
        return cls._cache_indice_busqueda

    @classmethod
    def _libros_por_nombre(cls):
        if cls._cache_libros_por_nombre is None:
            cls._cache_libros_por_nombre = {
                cls.normalizar(libro.get("nombre")): libro
                for libro in cls.libros()
                if libro.get("nombre")
            }
        return cls._cache_libros_por_nombre

    @classmethod
    def libro_por_nombre(cls, nombre):
        return cls._libros_por_nombre().get(cls.normalizar(nombre))

    @classmethod
    def nombres_libros(cls):
        return [libro.get("nombre", "") for libro in cls.libros()]

    @classmethod
    def cantidad_capitulos(cls, libro_nombre):
        libro = cls.libro_por_nombre(libro_nombre)
        if not libro:
            return 0
        return len(libro.get("capitulos", []))

    @classmethod
    def obtener_capitulo(cls, libro_nombre, capitulo):
        libro = cls.libro_por_nombre(libro_nombre)
        if not libro:
            return []
        try:
            return libro.get("capitulos", [])[int(capitulo) - 1]
        except (ValueError, TypeError, IndexError):
            return []

    @classmethod
    def obtener_secciones(cls, libro_nombre, capitulo):
        libro = cls.libro_por_nombre(libro_nombre)
        if not libro:
            return []
        try:
            secciones = libro.get("secciones", [])[int(capitulo) - 1]
            return secciones if isinstance(secciones, list) else []
        except (ValueError, TypeError, IndexError):
            return []

    @classmethod
    def obtener_parrafos(cls, libro_nombre, capitulo):
        libro = cls.libro_por_nombre(libro_nombre)
        if not libro:
            return []
        try:
            parrafos = libro.get("parrafos", [])[int(capitulo) - 1]
            return parrafos if isinstance(parrafos, list) else []
        except (ValueError, TypeError, IndexError):
            return []

    @classmethod
    def obtener_versiculo(cls, libro_nombre, capitulo, versiculo):
        cap = cls.obtener_capitulo(libro_nombre, capitulo)
        try:
            return cap[int(versiculo) - 1]
        except (ValueError, TypeError, IndexError):
            return ""

    @classmethod
    def referencia_texto(cls, libro, capitulo, versiculo=None):
        if versiculo:
            return f"{libro} {capitulo}:{versiculo}"
        return f"{libro} {capitulo}"

    @classmethod
    def parsear_referencia(cls, referencia):
        """Acepta: Juan 3:16, Salmo 91, Genesis 1, Apocalipsis 13:18."""
        texto = str(referencia or "").strip()
        if not texto:
            return None

        texto = re.sub(r"\s+", " ", texto)
        patron = r"^(.+?)\s+(\d+)(?:\s*[:.]\s*(\d+))?$"
        m = re.match(patron, texto)
        if not m:
            return None

        libro_txt = m.group(1).strip()
        capitulo = int(m.group(2))
        versiculo = int(m.group(3)) if m.group(3) else None

        libro = cls.libro_por_nombre(libro_txt)
        if not libro:
            # Permite abreviaciones por comienzo: Apo 13:18, Gen 1, Sal 91.
            buscado = cls.normalizar(libro_txt)
            coincidencias = [
                l for l in cls.libros()
                if cls.normalizar(l.get("nombre", "")).startswith(buscado)
            ]
            libro = coincidencias[0] if coincidencias else None

        if not libro:
            return None

        total_capitulos = len(libro.get("capitulos", []))
        if capitulo < 1 or capitulo > total_capitulos:
            return None

        if versiculo is not None:
            total_versiculos = len(libro.get("capitulos", [])[capitulo - 1])
            if versiculo < 1 or versiculo > total_versiculos:
                return None

        return {
            "libro": libro.get("nombre"),
            "capitulo": capitulo,
            "versiculo": versiculo,
            "referencia": cls.referencia_texto(libro.get("nombre"), capitulo, versiculo),
        }

    @classmethod
    def guardar_ultima_lectura(cls, libro, capitulo, modo="Versiculos", versiculo=None):
        DATOS_DIR.mkdir(parents=True, exist_ok=True)
        datos = {
            "libro": libro,
            "capitulo": int(capitulo or 1),
            "modo": modo or "Versiculos",
            "versiculo": versiculo,
        }
        ULTIMA_LECTURA_ARCHIVO.write_text(
            json.dumps(datos, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return datos

    @classmethod
    def cargar_ultima_lectura(cls):
        try:
            return json.loads(ULTIMA_LECTURA_ARCHIVO.read_text(encoding="utf-8"))
        except Exception:
            return {}

    @classmethod
    def cargar_historial_referencias(cls):
        try:
            datos = json.loads(HISTORIAL_REFERENCIAS_ARCHIVO.read_text(encoding="utf-8"))
            return datos if isinstance(datos, list) else []
        except Exception:
            return []

    @classmethod
    def guardar_historial_referencias(cls, historial):
        DATOS_DIR.mkdir(parents=True, exist_ok=True)
        limpio = historial if isinstance(historial, list) else []
        HISTORIAL_REFERENCIAS_ARCHIVO.write_text(
            json.dumps(limpio[:20], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return limpio[:20]

    @classmethod
    def agregar_historial_referencia(cls, libro, capitulo, versiculo=None, texto=""):
        item = {
            "libro": libro,
            "capitulo": int(capitulo or 1),
            "versiculo": versiculo,
            "referencia": cls.referencia_texto(libro, capitulo, versiculo),
            "texto": str(texto or "")[:220],
        }
        historial = cls.cargar_historial_referencias()
        historial = [h for h in historial if h.get("referencia") != item["referencia"]]
        historial.insert(0, item)
        return cls.guardar_historial_referencias(historial)
