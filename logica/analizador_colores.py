import csv
import colorsys
import json
import os
import re
import unicodedata

from core.rutas import ruta_datos
from collections import Counter


ALFABETO_29 = [
    "A", "B", "C", "CH", "D", "E", "F", "G", "H", "I",
    "J", "K", "L", "LL", "M", "N", "Ñ", "O", "P", "Q",
    "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
]

VALORES = {
    letra: indice
    for indice, letra in enumerate(ALFABETO_29, start=1)
}

COLORES = {
    1: {"nombre": "MARRON", "hex": "#795548"},
    2: {"nombre": "ROJO", "hex": "#E53935"},
    3: {"nombre": "NARANJA", "hex": "#FB8C00"},
    4: {"nombre": "AMARILLO", "hex": "#FDD835"},
    5: {"nombre": "VERDE", "hex": "#43A047"},
    6: {"nombre": "AZUL", "hex": "#1E88E5"},
    7: {"nombre": "VIOLETA", "hex": "#8E24AA"},
    8: {"nombre": "GRIS", "hex": "#757575"},
    9: {"nombre": "BLANCO", "hex": "#FFFFFF"},
}


def limpiar_texto(texto):
    texto = texto.upper()
    texto = texto.replace("Ñ", "__ENIE__")
    texto = texto.replace("Ü", "U")
    texto = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caracter) != "Mn"
    )
    texto = re.sub(r"[^A-Z\s_]", " ", texto)
    texto = texto.replace("__ENIE__", "Ñ")
    return re.sub(r"\s+", " ", texto).strip()


def tokenizar(texto):
    limpio = limpiar_texto(texto)
    tokens = []
    i = 0

    while i < len(limpio):
        if limpio[i].isspace():
            i += 1
            continue

        dos = limpio[i:i + 2]

        if dos in ("CH", "LL"):
            tokens.append(dos)
            i += 2
            continue

        letra = limpio[i]

        if letra in VALORES:
            tokens.append(letra)

        i += 1

    return tokens


def reducir_numero(numero):
    while numero > 9:
        numero = sum(int(digito) for digito in str(numero))

    return numero


def analizar_colores(texto):
    letras = tokenizar(texto)
    detalle = []

    for letra in letras:
        valor = VALORES[letra]
        reducido = reducir_numero(valor)
        color = COLORES[reducido]
        detalle.append(
            {
                "letra": letra,
                "valor": valor,
                "reducido": reducido,
                "color": color["nombre"],
                "hex": color["hex"],
            }
        )

    conteo = Counter(item["color"] for item in detalle)
    conteo_ordenado = {
        COLORES[numero]["nombre"]: conteo.get(COLORES[numero]["nombre"], 0)
        for numero in COLORES
    }

    positivos = {
        color: cantidad
        for color, cantidad in conteo_ordenado.items()
        if cantidad > 0
    }

    maximo = max(positivos.values(), default=0)
    minimo = min(positivos.values(), default=0)

    predominantes = [
        color
        for color, cantidad in positivos.items()
        if cantidad == maximo
    ]
    menores = [
        color
        for color, cantidad in positivos.items()
        if cantidad == minimo
    ]

    return {
        "texto_limpio": limpiar_texto(texto),
        "total_letras": len(letras),
        "detalle": detalle,
        "conteo": conteo_ordenado,
        "predominantes": predominantes,
        "menores": menores,
        "maximo": maximo,
        "minimo": minimo,
        "secuencia": [item["color"] for item in detalle],
        "mezcla": calcular_mezcla(conteo_ordenado),
    }


def calcular_mezcla(conteo):
    colores_presentes = [
        color
        for color in COLORES.values()
        if conteo.get(color["nombre"], 0) > 0
    ]
    total = len(colores_presentes)

    if total == 0:
        return {
            "nombre": "Sin datos",
            "hex": "#FFFFFF",
            "colores_usados": [],
            "metodo": "Sin repetir colores",
        }

    r = 0
    g = 0
    b = 0

    for color in colores_presentes:
        hex_color = color["hex"].lstrip("#")
        r += int(hex_color[0:2], 16)
        g += int(hex_color[2:4], 16)
        b += int(hex_color[4:6], 16)

    promedio = (
        round(r / total),
        round(g / total),
        round(b / total),
    )

    nombre = color_base_mezcla(promedio)
    hex_promedio = "#{:02X}{:02X}{:02X}".format(*promedio)

    return {
        "nombre": nombre,
        "hex": hex_color_puro(nombre, hex_promedio),
        "hex_calculado": hex_promedio,
        "colores_usados": [
            color["nombre"]
            for color in colores_presentes
        ],
        "metodo": "Sin repetir colores",
    }


def describir_mezcla(rgb):
    base = color_base_mezcla(rgb)
    detalle = _detalle_luminosidad(rgb)

    if detalle:
        return f"{base.lower()} {detalle}"

    return base


def color_base_mezcla(rgb):
    r, g, b = rgb
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    hue = h * 360

    if v < 0.16:
        return "NEGRO"

    if s < 0.12:
        if v > 0.86:
            return "BLANCO"
        if v < 0.36:
            return "GRIS"
        return "GRIS"

    if 8 <= hue < 68 and v < 0.72:
        if g > r * 1.05:
            return "MARRON VERDOSO"
        else:
            return "MARRON"
    elif 68 <= hue < 95 and v < 0.66 and r > b * 1.35:
        return "MARRON VERDOSO"
    elif hue < 16 or hue >= 344:
        return "ROJO"
    elif hue < 42:
        return "NARANJA"
    elif hue < 68:
        return "AMARILLO"
    elif hue < 166:
        return "VERDE"
    elif hue < 246:
        return "AZUL"
    elif hue < 326:
        return "VIOLETA"
    else:
        return "ROJO VIOLACEO"


def hex_color_puro(nombre, fallback="#FFFFFF"):
    nombre = str(nombre or "").upper().strip()

    equivalencias = {
        "MARRON VERDOSO": "MARRON",
        "ROJO VIOLACEO": "ROJO",
        "NEGRO": "MARRON",
    }
    nombre = equivalencias.get(nombre, nombre)

    for color in COLORES.values():
        if color["nombre"] == nombre:
            return color["hex"]

    return fallback


def _detalle_luminosidad(rgb):
    r, g, b = rgb
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

    if v < 0.42:
        return "oscuro"
    if v > 0.74:
        return "claro"

    return "medio"


def guardar_historial(resultado, archivo=None):
    archivo = archivo or ruta_datos("analisis_colores_historial.json")
    os.makedirs(os.path.dirname(archivo), exist_ok=True)

    historial = []

    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as entrada:
            historial = json.load(entrada)

    historial.insert(0, resultado)
    historial = historial[:50]

    with open(archivo, "w", encoding="utf-8") as salida:
        json.dump(historial, salida, indent=4, ensure_ascii=False)


def exportar_json(resultado, archivo=None):
    archivo = archivo or ruta_datos("analisis_colores_export.json", copiar_desde_datos=False)
    os.makedirs(os.path.dirname(archivo), exist_ok=True)

    with open(archivo, "w", encoding="utf-8") as salida:
        json.dump(resultado, salida, indent=4, ensure_ascii=False)

    return archivo


def exportar_csv(resultado, archivo=None):
    archivo = archivo or ruta_datos("analisis_colores_export.csv", copiar_desde_datos=False)
    os.makedirs(os.path.dirname(archivo), exist_ok=True)

    with open(archivo, "w", encoding="utf-8", newline="") as salida:
        writer = csv.writer(salida)
        writer.writerow(["letra", "valor", "reducido", "color"])

        for item in resultado["detalle"]:
            writer.writerow(
                [
                    item["letra"],
                    item["valor"],
                    item["reducido"],
                    item["color"],
                ]
            )

    return archivo
