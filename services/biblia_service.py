import json
import random
import re
import unicodedata
from pathlib import Path

from logica.biblia import cargar_biblia

DATOS_DIR = Path("datos")
ULTIMA_LECTURA_ARCHIVO = DATOS_DIR / "ultima_lectura_biblia.json"
HISTORIAL_REFERENCIAS_ARCHIVO = DATOS_DIR / "historial_referencias_biblia.json"

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


class BibliaService:
    """Servicio de Biblia: carga, búsqueda, referencias y random.

    Mantiene cache en memoria para evitar releer el JSON de Biblia en cada refresco.
    No depende de Flet, por eso se puede probar aparte.
    """

    _cache_libros = None
    _cache_random = {}
    _usados_random = {}

    @classmethod
    def normalizar(cls, texto):
        limpio = unicodedata.normalize("NFD", str(texto or ""))
        limpio = "".join(c for c in limpio if unicodedata.category(c) != "Mn")
        return limpio.strip().lower()

    @classmethod
    def libros(cls, refrescar=False):
        if refrescar or cls._cache_libros is None:
            cls._cache_libros = cargar_biblia() or []
            cls._cache_random.clear()
            cls._usados_random.clear()
        return cls._cache_libros

    @classmethod
    def libro_por_nombre(cls, nombre):
        buscado = cls.normalizar(nombre)
        for libro in cls.libros():
            if cls.normalizar(libro.get("nombre")) == buscado:
                return libro
        return None

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

    @classmethod
    def libro_pertenece_categoria_random(cls, nombre_libro, categoria):
        if categoria == "General":
            return True
        permitidos = LIBROS_RANDOM_POR_CATEGORIA.get(categoria, set())
        return cls.normalizar(nombre_libro) in permitidos

    @classmethod
    def candidatos_random(cls, categoria="General"):
        categoria = categoria or "General"
        if categoria in cls._cache_random:
            return cls._cache_random[categoria]

        candidatos = []
        for libro in cls.libros():
            nombre = libro.get("nombre", "")
            if not cls.libro_pertenece_categoria_random(nombre, categoria):
                continue
            for i_cap, capitulo in enumerate(libro.get("capitulos", []), start=1):
                for i_ver, texto in enumerate(capitulo, start=1):
                    if str(texto or "").strip():
                        candidatos.append({
                            "libro": nombre,
                            "capitulo": i_cap,
                            "versiculo": i_ver,
                            "referencia": cls.referencia_texto(nombre, i_cap, i_ver),
                            "texto": texto,
                        })
        cls._cache_random[categoria] = candidatos
        return candidatos

    @classmethod
    def versiculo_random(cls, categoria="General"):
        categoria = categoria or "General"
        candidatos = cls.candidatos_random(categoria) or cls.candidatos_random("General")
        if not candidatos:
            return {"referencia": "", "texto": ""}

        usados = cls._usados_random.setdefault(categoria, set())
        disponibles = [c for c in candidatos if c["referencia"] not in usados]
        if not disponibles:
            usados.clear()
            disponibles = candidatos[:]

        elegido = random.choice(disponibles)
        usados.add(elegido["referencia"])
        return elegido
