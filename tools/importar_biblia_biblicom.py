import gzip
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path


LIBROS_ESPERADOS = [
    ("Génesis", 50),
    ("Éxodo", 40),
    ("Levítico", 27),
    ("Números", 36),
    ("Deuteronomio", 34),
    ("Josué", 24),
    ("Jueces", 21),
    ("Rut", 4),
    ("1 Samuel", 31),
    ("2 Samuel", 24),
    ("1 Reyes", 22),
    ("2 Reyes", 25),
    ("1 Crónicas", 29),
    ("2 Crónicas", 36),
    ("Esdras", 10),
    ("Nehemías", 13),
    ("Ester", 10),
    ("Job", 42),
    ("Salmos", 150),
    ("Proverbios", 31),
    ("Eclesiastés", 12),
    ("Cantar de los Cantares", 8),
    ("Isaías", 66),
    ("Jeremías", 52),
    ("Lamentaciones de Jeremías", 5),
    ("Ezequiel", 48),
    ("Daniel", 12),
    ("Oseas", 14),
    ("Joel", 3),
    ("Amós", 9),
    ("Abdías", 1),
    ("Jonás", 4),
    ("Miqueas", 7),
    ("Nahúm", 3),
    ("Habacuc", 3),
    ("Sofonías", 3),
    ("Hageo", 2),
    ("Zacarías", 14),
    ("Malaquías", 4),
    ("Mateo", 28),
    ("Marcos", 16),
    ("Lucas", 24),
    ("Juan", 21),
    ("Hechos", 28),
    ("Romanos", 16),
    ("1 Corintios", 16),
    ("2 Corintios", 13),
    ("Gálatas", 6),
    ("Efesios", 6),
    ("Filipenses", 4),
    ("Colosenses", 4),
    ("1 Tesalonicenses", 5),
    ("2 Tesalonicenses", 3),
    ("1 Timoteo", 6),
    ("2 Timoteo", 4),
    ("Tito", 3),
    ("Filemón", 1),
    ("Hebreos", 13),
    ("Santiago", 5),
    ("1 Pedro", 5),
    ("2 Pedro", 3),
    ("1 Juan", 5),
    ("2 Juan", 1),
    ("3 Juan", 1),
    ("Judas", 1),
    ("Apocalipsis", 22),
]


def limpiar_espacios(texto):
    texto = html.unescape(str(texto or "")).replace("\xa0", " ")
    texto = re.sub(r"\s+", " ", texto).strip()
    texto = re.sub(r"\s+([,.;:!?])", r"\1", texto)
    texto = re.sub(r"([¿¡])\s+", r"\1", texto)
    return texto


class ChapterParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items = []
        self.versos = {}
        self.secciones = []
        self._heading_tag = None
        self._heading_parts = []
        self._paragraph = None
        self._span_parts = None
        self._sup_parts = None
        self._skip_depth = 0
        self._active_verse = None
        self._pending_heading = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        clases = set(str(attrs_dict.get("class", "")).split())

        if self._skip_depth:
            self._skip_depth += 1
            return

        if tag == "a" and "note" in clases:
            self._skip_depth = 1
            return

        if tag in {"h2", "h3", "h4"}:
            self._heading_tag = tag
            self._heading_parts = []
            return

        if tag == "p":
            self._paragraph = {"tipo": "parrafo", "segmentos": []}
            return

        if tag == "sup" and "numverse" in clases:
            self._sup_parts = []
            return

        if tag == "span" and "versetxt" in clases:
            self._span_parts = []

    def handle_endtag(self, tag):
        if self._skip_depth:
            self._skip_depth -= 1
            return

        if tag == self._heading_tag:
            titulo = limpiar_espacios("".join(self._heading_parts))
            if titulo:
                self._pending_heading = titulo
                self.items.append({"tipo": "titulo", "texto": titulo})
            self._heading_tag = None
            self._heading_parts = []
            return

        if tag == "sup" and self._sup_parts is not None:
            numero = limpiar_espacios("".join(self._sup_parts))
            if numero.isdigit():
                self._active_verse = int(numero)
            self._sup_parts = None
            return

        if tag == "span" and self._span_parts is not None:
            texto = limpiar_espacios("".join(self._span_parts))
            if texto and self._active_verse is not None:
                if self._pending_heading:
                    self.secciones.append(
                        {"versiculo": self._active_verse, "titulo": self._pending_heading}
                    )
                    self._pending_heading = None
                self.versos.setdefault(self._active_verse, []).append(texto)
                if self._paragraph is not None:
                    self._paragraph["segmentos"].append(
                        {
                            "versiculo": self._active_verse
                            if len(self.versos[self._active_verse]) == 1
                            else None,
                            "texto": texto,
                        }
                    )
            self._span_parts = None
            return

        if tag == "p" and self._paragraph is not None:
            if self._paragraph["segmentos"]:
                self.items.append(self._paragraph)
            self._paragraph = None

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._heading_tag:
            self._heading_parts.append(data)
            return
        if self._sup_parts is not None:
            self._sup_parts.append(data)
            return
        if self._span_parts is not None:
            self._span_parts.append(data)


def extraer_capitulo(texto_html):
    inicio = re.search(r'<div\s+class=["\']chapter["\']\s*>', texto_html, re.I)
    if not inicio:
        return None
    fin = re.search(r'<div\s+class=["\']copyrights\b', texto_html[inicio.end() :], re.I)
    cuerpo = texto_html[inicio.end() : inicio.end() + fin.start()] if fin else texto_html[inicio.end() :]
    parser = ChapterParser()
    parser.feed(cuerpo)
    if not parser.versos:
        return None
    max_verso = max(parser.versos)
    versiculos = [
        limpiar_espacios(" ".join(parser.versos.get(indice, [])))
        for indice in range(1, max_verso + 1)
    ]
    return {
        "versiculos": versiculos,
        "secciones": parser.secciones,
        "parrafos": parser.items,
    }


def referencia_archivo(texto_html):
    libro = re.search(r'bible\.book_name",\s*"([^"]+)"', texto_html)
    capitulo = re.search(r'bible\.num_chapter",\s*"(\d+)"', texto_html)
    if libro and capitulo:
        return normalizar_nombre_libro(html.unescape(libro.group(1))), int(capitulo.group(1))

    titulo = re.search(r"<h1[^>]*>(.*?)</h1>", texto_html, re.S | re.I)
    if not titulo:
        return None
    limpio = limpiar_espacios(re.sub(r"<[^>]+>", "", titulo.group(1)))
    for nombre, _total in sorted(LIBROS_ESPERADOS, key=lambda item: len(item[0]), reverse=True):
        if limpio == nombre:
            return normalizar_nombre_libro(nombre), 1
        prefijo = f"{nombre} "
        if limpio.startswith(prefijo):
            numero = limpio[len(prefijo) :].strip()
            if numero.isdigit():
                return normalizar_nombre_libro(nombre), int(numero)
    return None


def normalizar_nombre_libro(nombre):
    if nombre == "Salmo":
        return "Salmos"
    return nombre


def puntaje_capitulo(capitulo):
    texto = " ".join(capitulo["versiculos"])
    return (len(capitulo["versiculos"]), len(texto), -texto.count("\ufffd"))


def importar(origen, destino):
    origen = Path(origen)
    destino = Path(destino)
    candidatos = {}

    for ruta in origen.glob("*.html"):
        if ruta.name.lower().startswith("index"):
            continue
        texto_html = ruta.read_text(encoding="utf-8", errors="replace")
        referencia = referencia_archivo(texto_html)
        if not referencia:
            continue
        capitulo = extraer_capitulo(texto_html)
        if not capitulo:
            continue
        actual = candidatos.get(referencia)
        if actual is None or puntaje_capitulo(capitulo) > puntaje_capitulo(actual[1]):
            candidatos[referencia] = (ruta.name, capitulo)

    libros = []
    faltantes = []
    for nombre, total_capitulos in LIBROS_ESPERADOS:
        capitulos = []
        secciones = []
        parrafos = []
        for numero in range(1, total_capitulos + 1):
            entrada = candidatos.get((nombre, numero))
            if not entrada:
                faltantes.append(f"{nombre} {numero}")
                capitulos.append([])
                secciones.append([])
                parrafos.append([])
                continue
            capitulo = entrada[1]
            capitulos.append(capitulo["versiculos"])
            secciones.append(capitulo["secciones"])
            parrafos.append(capitulo["parrafos"])
        libros.append(
            {
                "nombre": nombre,
                "capitulos": capitulos,
                "secciones": secciones,
                "parrafos": parrafos,
            }
        )

    datos = {
        "version": "Reina-Valera 1960",
        "fuente": "HTML proporcionado por el usuario",
        "formato": 2,
        "libros": libros,
    }
    destino.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(destino, "wt", encoding="utf-8") as salida:
        json.dump(datos, salida, ensure_ascii=False, separators=(",", ":"))

    total_versiculos = sum(len(capitulo) for libro in libros for capitulo in libro["capitulos"])
    print(f"Capítulos importados: {len(candidatos)}")
    print(f"Versículos importados: {total_versiculos}")
    print(f"Destino: {destino}")
    if faltantes:
        print("Faltantes:")
        for item in faltantes:
            print(f"- {item}")
        raise SystemExit(1)


if __name__ == "__main__":
    importar(
        Path(r"C:\Users\USER\AppData\Local\Temp"),
        Path("datos/biblia_rvr1960.json.gz"),
    )
