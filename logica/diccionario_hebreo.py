import re
import unicodedata


def normalizar_palabra(texto):
    texto = str(texto or "").strip().lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(letra for letra in texto if unicodedata.category(letra) != "Mn")
    return texto


DICCIONARIO_HEBREO = [
    {
        "palabra": "Jehova",
        "hebreo": "יהוה",
        "transliteracion": "YHWH / Yahweh",
        "significado": "El que es; el Eterno; nombre del Senor.",
        "descripcion": "Nombre sagrado de Dios en el texto hebreo. En Reina-Valera suele aparecer como Jehova.",
        "aliases": ["Jehova", "Jehová", "Jah", "Yahweh", "Yahveh"],
    },
    {
        "palabra": "Aleluya",
        "hebreo": "הללו־יה",
        "transliteracion": "Hallelu-Yah",
        "significado": "Alabad a Jah / alabad al Senor.",
        "descripcion": "Expresion hebrea de adoracion y alabanza.",
        "aliases": ["Aleluya", "Alleluya"],
    },
    {
        "palabra": "Amen",
        "hebreo": "אמן",
        "transliteracion": "Amen",
        "significado": "Verdad; firme; asi sea.",
        "descripcion": "Expresion de confirmacion, fidelidad y acuerdo delante de Dios.",
        "aliases": ["Amen", "Amén"],
    },
    {
        "palabra": "Hosanna",
        "hebreo": "הושיעה נא",
        "transliteracion": "Hoshia na",
        "significado": "Salva ahora, te rogamos.",
        "descripcion": "Clamor de salvacion y alabanza usado en la entrada triunfal.",
        "aliases": ["Hosanna", "Hosana"],
    },
    {
        "palabra": "Rabí",
        "hebreo": "רבי",
        "transliteracion": "Rabbi",
        "significado": "Mi maestro.",
        "descripcion": "Titulo de respeto para un maestro espiritual.",
        "aliases": ["Rabi", "Rabí", "Rabboni", "Raboni"],
    },
    {
        "palabra": "Mesias",
        "hebreo": "משיח",
        "transliteracion": "Mashiaj",
        "significado": "Ungido.",
        "descripcion": "Titulo hebreo del Ungido prometido por Dios.",
        "aliases": ["Mesias", "Mesías", "Mashiaj", "Mesiás"],
    },
    {
        "palabra": "Emanuel",
        "hebreo": "עמנו אל",
        "transliteracion": "Immanu El",
        "significado": "Dios con nosotros.",
        "descripcion": "Nombre profetico asociado al nacimiento del Mesias.",
        "aliases": ["Emanuel", "Emmanuel"],
    },
    {
        "palabra": "Sion",
        "hebreo": "ציון",
        "transliteracion": "Tsiyyon",
        "significado": "Sion; monte o ciudad escogida.",
        "descripcion": "Nombre biblico vinculado a Jerusalen, al pueblo de Dios y a su monte santo.",
        "aliases": ["Sion", "Sión"],
    },
    {
        "palabra": "Eden",
        "hebreo": "עדן",
        "transliteracion": "Eden",
        "significado": "Delicia; placer; lugar de deleite.",
        "descripcion": "Nombre del jardin donde Dios puso al hombre al principio.",
        "aliases": ["Eden", "Edén"],
    },
    {
        "palabra": "Satanas",
        "hebreo": "שטן",
        "transliteracion": "Satan",
        "significado": "Adversario; acusador.",
        "descripcion": "Nombre usado para el enemigo y acusador.",
        "aliases": ["Satanas", "Satanás", "Satan"],
    },
    {
        "palabra": "Querubin",
        "hebreo": "כרוב",
        "transliteracion": "Keruv",
        "significado": "Ser celestial asociado a la presencia y gloria de Dios.",
        "descripcion": "En plural, querubines. Aparecen guardando lugares santos y ligados al arca.",
        "aliases": ["Querubin", "Querubín", "Querubines"],
    },
    {
        "palabra": "Serafin",
        "hebreo": "שרף",
        "transliteracion": "Saraf",
        "significado": "Ardiente.",
        "descripcion": "Ser celestial mencionado en la vision de Isaias.",
        "aliases": ["Serafin", "Serafín", "Serafines"],
    },
    {
        "palabra": "Abba",
        "hebreo": "אבא",
        "transliteracion": "Abba",
        "significado": "Padre.",
        "descripcion": "Termino de cercania filial usado en oracion a Dios.",
        "aliases": ["Abba"],
    },
    {
        "palabra": "Maranata",
        "hebreo": "מרנא תא",
        "transliteracion": "Maranatha",
        "significado": "El Senor viene / ven, Senor.",
        "descripcion": "Expresion aramea usada por la iglesia primitiva.",
        "aliases": ["Maranata", "Maranatha"],
    },
    {
        "palabra": "Golgota",
        "hebreo": "גלגלתא",
        "transliteracion": "Golgotha",
        "significado": "Lugar de la calavera.",
        "descripcion": "Nombre del lugar donde fue crucificado Jesus.",
        "aliases": ["Golgota", "Gólgota"],
    },
    {
        "palabra": "Elí",
        "hebreo": "אלי",
        "transliteracion": "Eli",
        "significado": "Dios mio.",
        "descripcion": "Parte del clamor: Eli, Eli, lama sabactani.",
        "aliases": ["Eli", "Elí", "Eloi", "Eloí"],
    },
    {
        "palabra": "Sabactani",
        "hebreo": "שבקתני",
        "transliteracion": "Shabaqtani",
        "significado": "Me has desamparado.",
        "descripcion": "Parte del clamor de Jesus en la cruz.",
        "aliases": ["Sabactani", "Sabactaní"],
    },
]


_INDICE = {}
for entrada in DICCIONARIO_HEBREO:
    for alias in entrada.get("aliases", []):
        _INDICE[normalizar_palabra(alias)] = entrada


_PATRON_FRAGMENTOS = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+|[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+")


def entradas_diccionario():
    return DICCIONARIO_HEBREO[:]


def entrada_para_palabra(palabra):
    return _INDICE.get(normalizar_palabra(palabra))


def fragmentos_con_diccionario(texto):
    for coincidencia in _PATRON_FRAGMENTOS.finditer(str(texto or "")):
        fragmento = coincidencia.group(0)
        yield fragmento, entrada_para_palabra(fragmento), coincidencia.start(), coincidencia.end()
