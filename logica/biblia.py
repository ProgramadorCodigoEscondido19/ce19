import json
import gzip
import os
import re
import unicodedata

from core.rutas import ruta_datos, ruta_recurso

BIBLIA_ARCHIVO = ruta_recurso("datos/biblia_rvr1960.json.gz")
RESALTADOS_ARCHIVO = ruta_datos("resaltados_biblia.json")
UNIDADES = {
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
}
ESPECIALES = {
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
}
DECENAS = {
    30: "treinta",
    40: "cuarenta",
    50: "cincuenta",
    60: "sesenta",
    70: "setenta",
    80: "ochenta",
    90: "noventa",
}
CENTENAS = {
    100: "cien",
    200: "doscientos",
    300: "trescientos",
    400: "cuatrocientos",
    500: "quinientos",
    600: "seiscientos",
    700: "setecientos",
    800: "ochocientos",
    900: "novecientos",
}
ERRORES_NUMEROS = {
    "sies": "seis",
    "ceis": "seis",
    "seiz": "seis",
    "ses": "seis",
    "dies": "diez",
    "diese": "diez",
    "diezs": "diez",
    "dose": "doce",
    "doces": "doce",
    "trese": "trece",
    "treses": "trece",
    "catorse": "catorce",
    "quinse": "quince",
    "diesiseis": "dieciseis",
    "dieciseiz": "dieciseis",
    "veinti dos": "veintidos",
    "veinti tres": "veintitres",
    "veinti seis": "veintiseis",
    "veinteidos": "veintidos",
    "veintitres": "veintitres",
}


def numero_a_texto(numero):
    numero = int(numero)

    if numero < 0:
        return "menos " + numero_a_texto(abs(numero))

    if numero < 10:
        return UNIDADES[numero]

    if numero in ESPECIALES:
        return ESPECIALES[numero]

    if numero < 100:
        decena = numero // 10 * 10
        unidad = numero % 10
        return DECENAS[decena] if unidad == 0 else f"{DECENAS[decena]} y {UNIDADES[unidad]}"

    if numero < 1000:
        centena = numero // 100 * 100
        resto = numero % 100

        if numero == 100:
            return "cien"

        prefijo = "ciento" if centena == 100 else CENTENAS[centena]
        return prefijo if resto == 0 else f"{prefijo} {numero_a_texto(resto)}"

    if numero < 1000000:
        miles = numero // 1000
        resto = numero % 1000
        prefijo = "mil" if miles == 1 else f"{numero_a_texto(miles)} mil"
        return prefijo if resto == 0 else f"{prefijo} {numero_a_texto(resto)}"

    return str(numero)


def variantes_numero(numero):
    texto = numero_a_texto(numero)
    variantes = {texto}

    if "uno" in texto:
        variantes.add(texto.replace("uno", "un"))
        variantes.add(texto.replace("uno", "una"))

    if 21 <= int(numero) <= 29:
        variantes.add(texto.replace("veinti", "veinte y "))

    return {normalizar_busqueda(variante) for variante in variantes}


def normalizar_versiculo(texto):
    texto = re.sub(r"\s+", " ", str(texto)).strip()
    texto = re.sub(r"\s+([,.;:!?])", r"\1", texto)
    texto = re.sub(r"([¿¡])\s+", r"\1", texto)
    texto = re.sub(r"\(\s+", "(", texto)
    texto = re.sub(r"\s+\)", ")", texto)
    return texto


def cargar_biblia(archivo=BIBLIA_ARCHIVO):
    if not os.path.exists(archivo):
        archivo_json = ruta_recurso("datos/biblia_rvr1960.json")
        if os.path.exists(archivo_json):
            archivo = archivo_json
        else:
            return []

    if str(archivo).lower().endswith(".gz"):
        with gzip.open(archivo, "rt", encoding="utf-8") as entrada:
            datos = json.load(entrada)
    else:
        with open(archivo, "r", encoding="utf-8") as entrada:
            datos = json.load(entrada)

    if isinstance(datos, dict):
        datos = datos.get("libros", [])

    libros = []

    for libro in datos:
        nombre = libro.get("nombre") or libro.get("book")
        capitulos_origen = libro.get("capitulos") or libro.get("chapters") or []
        capitulos = [
            [
                normalizar_versiculo(versiculo)
                for versiculo in capitulo
            ]
            for capitulo in capitulos_origen
        ]

        if nombre:
            libro_limpio = {
                "nombre": nombre,
                "capitulos": capitulos,
            }

            secciones = libro.get("secciones")
            parrafos = libro.get("parrafos")
            if isinstance(secciones, list):
                libro_limpio["secciones"] = secciones
            if isinstance(parrafos, list):
                libro_limpio["parrafos"] = parrafos

            libros.append(libro_limpio)

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
    texto = unicodedata.normalize("NFD", str(texto or ""))
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^a-zA-Z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip().lower()


NUMEROS_TEXTO = {numero: numero_a_texto(numero) for numero in range(0, 1000)}
TEXTO_NUMEROS = {
    variante: numero
    for numero in range(0, 1000)
    for variante in variantes_numero(numero)
}


def alternativas_consulta(consulta, incluir_errores=False):
    base = normalizar_busqueda(consulta.strip())
    alternativas = {base}

    compacto = base.replace(" ", "")

    if compacto.isdigit():
        alternativas.update(variantes_numero(int(compacto)))
    else:
        numero = TEXTO_NUMEROS.get(base)
        if numero is not None:
            alternativas.update(variantes_numero(numero))
            alternativas.add(str(numero))

    if incluir_errores:
        corregida = ERRORES_NUMEROS.get(base)
        if corregida:
            alternativas.add(corregida)

        for palabra in base.split():
            corregida = ERRORES_NUMEROS.get(palabra)
            if corregida:
                alternativas.add(corregida)

    return [
        alternativa
        for alternativa in alternativas
        if alternativa
    ]


def buscar_texto(libros, consulta):
    consultas = alternativas_consulta(consulta)

    if not consultas:
        return []

    resultados = _buscar_por_alternativas(libros, consultas)

    if resultados:
        return resultados

    consultas_con_errores = alternativas_consulta(consulta, incluir_errores=True)
    nuevas_consultas = [
        consulta
        for consulta in consultas_con_errores
        if consulta not in consultas
    ]

    if not nuevas_consultas:
        return []

    return _buscar_por_alternativas(libros, nuevas_consultas)


def _buscar_por_alternativas(libros, consultas):
    resultados = []
    referencias_vistas = set()

    consultas_validas = [
        normalizar_busqueda(consulta)
        for consulta in consultas
        if normalizar_busqueda(consulta)
    ]

    if not consultas_validas:
        return resultados

    for libro in libros or []:
        if not isinstance(libro, dict):
            continue

        nombre_libro = str(libro.get("nombre") or "").strip()
        if not nombre_libro:
            continue

        for capitulo_indice, capitulo in enumerate(libro.get("capitulos") or [], start=1):
            if not isinstance(capitulo, (list, tuple)):
                continue

            for versiculo_indice, texto in enumerate(capitulo, start=1):
                texto_normalizado = normalizar_busqueda(texto)

                if any(consulta in texto_normalizado for consulta in consultas_validas):
                    referencia = (nombre_libro, capitulo_indice, versiculo_indice)
                    if referencia in referencias_vistas:
                        continue
                    referencias_vistas.add(referencia)
                    resultados.append(
                        {
                            "tipo": "versiculo",
                            "libro": nombre_libro,
                            "capitulo": capitulo_indice,
                            "versiculo": versiculo_indice,
                            "texto": texto,
                        }
                    )

    return resultados
