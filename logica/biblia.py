import json
import os
import re
import unicodedata

from core.rutas import ruta_datos, ruta_recurso

BIBLIA_ARCHIVO = ruta_recurso("datos/biblia_rvr1960.json")
RESALTADOS_ARCHIVO = ruta_datos("resaltados_biblia.json")
NUMEROS_TEXTO = {
    0: "cero",
    1: "uno",
    2: "dos",
    3: "tres",
    4: "cuatro",
    5: "cinco",
    6: "seis",
    7: "siete",
    8: "ocho",
    9: "nueve",
    10: "diez",
    11: "once",
    12: "doce",
    13: "trece",
    14: "catorce",
    15: "quince",
    16: "dieciseis",
    17: "diecisiete",
    18: "dieciocho",
    19: "diecinueve",
    20: "veinte",
    21: "veintiuno",
    22: "veintidos",
    23: "veintitres",
    24: "veinticuatro",
    25: "veinticinco",
    26: "veintiseis",
    27: "veintisiete",
    28: "veintiocho",
    29: "veintinueve",
    30: "treinta",
}


def normalizar_versiculo(texto):
    texto = re.sub(r"\s+", " ", str(texto)).strip()
    texto = re.sub(r"\s+([,.;:!?])", r"\1", texto)
    texto = re.sub(r"([¿¡])\s+", r"\1", texto)
    texto = re.sub(r"\(\s+", "(", texto)
    texto = re.sub(r"\s+\)", ")", texto)
    return texto


def cargar_biblia(archivo=BIBLIA_ARCHIVO):
    if not os.path.exists(archivo):
        return []

    with open(archivo, "r", encoding="utf-8") as entrada:
        datos = json.load(entrada)

    if isinstance(datos, dict):
        datos = datos.get("libros", [])

    libros = []

    for libro in datos:
        nombre = libro.get("nombre") or libro.get("book")
        capitulos = [
            [
                normalizar_versiculo(versiculo)
                for versiculo in capitulo
            ]
            for capitulo in (libro.get("capitulos") or libro.get("chapters") or [])
        ]

        if nombre:
            libros.append(
                {
                    "nombre": nombre,
                    "capitulos": capitulos,
                }
            )

    return libros


def cargar_resaltados(archivo=RESALTADOS_ARCHIVO):
    if not os.path.exists(archivo):
        return {}

    with open(archivo, "r", encoding="utf-8") as entrada:
        return json.load(entrada)


def guardar_resaltados(resaltados, archivo=RESALTADOS_ARCHIVO):
    os.makedirs(os.path.dirname(archivo), exist_ok=True)

    with open(archivo, "w", encoding="utf-8") as salida:
        json.dump(resaltados, salida, indent=4, ensure_ascii=False)


def verso_id(libro, capitulo, versiculo):
    return f"{libro}|{capitulo}|{versiculo}"


def normalizar_busqueda(texto):
    texto = unicodedata.normalize("NFD", texto or "")
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.lower()


def alternativas_consulta(consulta):
    base = normalizar_busqueda(consulta.strip())
    alternativas = {base}

    if base.isdigit():
        numero = int(base)

        if numero in NUMEROS_TEXTO:
            alternativas.add(NUMEROS_TEXTO[numero])
    else:
        invertido = {
            texto: str(numero)
            for numero, texto in NUMEROS_TEXTO.items()
        }

        if base in invertido:
            alternativas.add(invertido[base])

    return [
        alternativa
        for alternativa in alternativas
        if alternativa
    ]


def buscar_texto(libros, consulta):
    consultas = alternativas_consulta(consulta)

    if not consultas:
        return []

    resultados = []

    for libro in libros:
        for capitulo_indice, capitulo in enumerate(libro["capitulos"], start=1):
            for versiculo_indice, texto in enumerate(capitulo, start=1):
                texto_normalizado = normalizar_busqueda(texto)

                if any(c in texto_normalizado for c in consultas):
                    resultados.append(
                        {
                            "libro": libro["nombre"],
                            "capitulo": capitulo_indice,
                            "versiculo": versiculo_indice,
                            "texto": texto,
                        }
                    )

    return resultados
