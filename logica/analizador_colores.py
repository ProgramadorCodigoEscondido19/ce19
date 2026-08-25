import csv
import colorsys
import base64
import json
import os
import re
import time
import unicodedata
from pathlib import Path

from core.rutas import ruta_datos, ruta_exportacion
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
    7: {"nombre": "PURPURA", "hex": "#8E24AA"},
    8: {"nombre": "GRIS", "hex": "#757575"},
    9: {"nombre": "BLANCO", "hex": "#FFFFFF"},
}

DIGITO_COLORES = {
    0: {"nombre": "NEGRO", "hex": "#000000"},
    **COLORES,
}


# Resultado de mezclar pigmentos de los colores puros disponibles en la app.
# Se priorizan los tres resultados primarios y se evita promediar RGB/HSV,
# porque dicho promedio produce tonos que no representan una mezcla de pintura.
MEZCLAS_PIGMENTOS = {
    frozenset(("ROJO", "AMARILLO")): "NARANJA",
    frozenset(("ROJO", "AZUL")): "PURPURA",
    frozenset(("AMARILLO", "AZUL")): "VERDE",
    frozenset(("ROJO", "NARANJA")): "NARANJA",
    frozenset(("NARANJA", "AMARILLO")): "NARANJA",
    frozenset(("AMARILLO", "VERDE")): "VERDE",
    frozenset(("VERDE", "AZUL")): "VERDE",
    frozenset(("AZUL", "PURPURA")): "PURPURA",
    frozenset(("PURPURA", "ROJO")): "PURPURA",
}


def nombre_color_publico(nombre):
    nombre = str(nombre or "").upper().strip()
    equivalencias = {
        "VIOLETA": "PURPURA",
        "PÚRPURA": "PURPURA",
    }
    return equivalencias.get(nombre, nombre)


def mezclar_pigmentos(nombre_a, nombre_b):
    """Devuelve el color puro resultante de dos pigmentos de la paleta."""
    color_a = nombre_color_publico(nombre_a)
    color_b = nombre_color_publico(nombre_b)

    if color_a not in {color["nombre"] for color in COLORES.values()}:
        return color_b or "MARRON"
    if color_b not in {color["nombre"] for color in COLORES.values()}:
        return color_a or "MARRON"
    if color_a == color_b:
        return color_a

    mezcla = frozenset((color_a, color_b))
    if "BLANCO" in mezcla or "GRIS" in mezcla:
        return next(color for color in mezcla if color not in {"BLANCO", "GRIS"})
    if "MARRON" in mezcla:
        return "MARRON"

    return MEZCLAS_PIGMENTOS.get(mezcla, "MARRON")


def limpiar_texto(texto):
    texto = texto.upper()
    texto = texto.replace("Ñ", "__ENIE__")
    texto = texto.replace("Ü", "U")
    texto = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caracter) != "Mn"
    )
    texto = re.sub(r"[^A-Z0-9\s_]", " ", texto)
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

        if letra.isdigit():
            # Cada digito se analiza como un valor literal. Asi 19 se muestra
            # y suma como 1 + 9, sin convertirse en una letra del alfabeto.
            tokens.append(letra)
            i += 1
            continue

        if letra in VALORES:
            tokens.append(letra)

        i += 1

    return tokens


def reducir_numero(numero):
    while numero > 9:
        numero = sum(int(digito) for digito in str(numero))

    return numero


def proceso_reduccion(numero):
    pasos = [int(numero or 0)]
    actual = int(numero or 0)

    while actual > 9:
        actual = sum(int(digito) for digito in str(actual))
        pasos.append(actual)

    return pasos


def analizar_colores(texto):
    letras = tokenizar(texto)
    detalle = []

    for letra in letras:
        es_numero = letra.isdigit()
        valor = int(letra) if es_numero else VALORES[letra]
        reducido = reducir_numero(valor)
        color = DIGITO_COLORES[reducido]
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
        DIGITO_COLORES[numero]["nombre"]: conteo.get(DIGITO_COLORES[numero]["nombre"], 0)
        for numero in DIGITO_COLORES
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


def analizar_codigo_visual(texto):
    letras = tokenizar(texto)
    detalle = []
    total_codigo = 0

    for letra in letras:
        es_numero = letra.isdigit()
        valor = int(letra) if es_numero else VALORES[letra]
        reducido = reducir_numero(valor)
        digitos = [int(digito) for digito in str(valor)]
        color = DIGITO_COLORES[reducido]
        total_codigo += valor
        detalle.append(
            {
                "letra": letra,
                "valor": valor,
                "digitos": digitos,
                "reducido": reducido,
                "color": color["nombre"],
                "hex": color["hex"],
                "digitos_colores": [
                    {
                        "digito": digito,
                        "color": DIGITO_COLORES[digito]["nombre"],
                        "hex": DIGITO_COLORES[digito]["hex"],
                    }
                    for digito in digitos
                ],
            }
        )

    pasos = proceso_reduccion(total_codigo)
    resultado_final = pasos[-1] if pasos else 0
    color_final = DIGITO_COLORES.get(resultado_final, DIGITO_COLORES[0])
    base = analizar_colores(texto)

    base.update(
        {
            "detalle_visual": detalle,
            "total_codigo": total_codigo,
            "pasos_reduccion": pasos,
            "resultado_final": resultado_final,
            "color_final": color_final["nombre"],
            "hex_final": color_final["hex"],
        }
    )
    return base


def _pil_colores():
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageOps
    except Exception as exc:
        raise RuntimeError("No se pudo cargar el generador de tarjetas.") from exc

    return Image, ImageDraw, ImageFont, ImageOps


def _fuente_colores(ImageFont, tamano, negrita=False):
    nombres = [
        "arialbd.ttf" if negrita else "arial.ttf",
        "DejaVuSans-Bold.ttf" if negrita else "DejaVuSans.ttf",
    ]
    rutas = [Path("C:/Windows/Fonts") / nombre for nombre in nombres]

    for ruta in rutas:
        try:
            return ImageFont.truetype(str(ruta), tamano)
        except Exception:
            pass

    for nombre in nombres:
        try:
            return ImageFont.truetype(nombre, tamano)
        except Exception:
            pass

    return ImageFont.load_default()


def _color_texto_para(hex_color):
    color = str(hex_color or "#FFFFFF").lstrip("#")
    if len(color) != 6:
        return "#111111"
    r, g, b = (int(color[i:i + 2], 16) for i in (0, 2, 4))
    return "#111111" if (r * 0.299 + g * 0.587 + b * 0.114) > 160 else "#FFFFFF"


def _slug_colores(texto):
    texto = re.sub(r"\s+", "_", str(texto or "").strip())
    texto = re.sub(r"[^A-Za-z0-9_]+", "", texto)
    return texto.strip("_") or "colores"


def generar_tarjeta_colores(resultado, titulo=None, nombre_archivo=None):
    Image, ImageDraw, ImageFont, ImageOps = _pil_colores()
    ancho, alto = 1536, 1024
    fondo_base = Path(__file__).resolve().parent / "recursos" / "tarjeta_versiculo_base.png"

    if fondo_base.exists():
        resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
        imagen = ImageOps.fit(Image.open(fondo_base).convert("RGB"), (ancho, alto), method=resampling)
    else:
        imagen = Image.new("RGB", (ancho, alto), "#25004A")

    draw = ImageDraw.Draw(imagen)
    fuente_titulo = _fuente_colores(ImageFont, 54, True)
    fuente = _fuente_colores(ImageFont, 30, False)
    fuente_negrita = _fuente_colores(ImageFont, 34, True)
    fuente_chica = _fuente_colores(ImageFont, 23, True)

    panel = (86, 76, ancho - 86, alto - 78)
    draw.rounded_rectangle(panel, radius=34, fill=(255, 252, 247), outline=(222, 205, 226), width=3)

    titulo = str(titulo or resultado.get("texto_limpio") or "Codigo de colores").strip()
    if len(titulo) > 48:
        titulo = titulo[:45] + "..."
    draw.text((ancho / 2, 112), titulo, font=fuente_titulo, fill="#4A2A18", anchor="mm")

    detalle = resultado.get("detalle_visual", [])[:24]
    x, y = 130, 178
    tile_w, tile_h = 118, 170
    gap_x, gap_y = 14, 22
    por_fila = 8

    for indice, item in enumerate(detalle):
        col = indice % por_fila
        fila = indice // por_fila
        tx = x + col * (tile_w + gap_x)
        ty = y + fila * (tile_h + gap_y)
        color = item.get("hex", "#FFFFFF")
        borde = "#795548" if item.get("reducido") == 9 else "#FFFFFF"
        draw.rounded_rectangle((tx, ty, tx + tile_w, ty + 42), radius=7, fill=color, outline=borde, width=3)
        draw.text((tx + tile_w / 2, ty + 21), item.get("letra", ""), font=fuente_chica, fill=_color_texto_para(color), anchor="mm")
        draw.text((tx + tile_w / 2, ty + 62), str(item.get("valor", "")), font=fuente_chica, fill="#17131D", anchor="mm")

        digitos = item.get("digitos_colores", [])
        dx = tx + (tile_w - len(digitos) * 35 - max(len(digitos) - 1, 0) * 4) / 2
        for digito in digitos:
            digito_hex = digito.get("hex", "#FFFFFF")
            digito_valor = digito.get("digito", "")
            draw.text((dx + 17, ty + 86), str(digito_valor), font=fuente_chica, fill="#17131D", anchor="mm")
            draw.rectangle((dx, ty + 102, dx + 34, ty + 134), fill=digito_hex, outline="#795548" if digito_valor == 9 else "#777777", width=2)
            dx += 39

        if len(digitos) > 1:
            reducido = item.get("reducido", "")
            reducido_hex = item.get("hex", "#FFFFFF")
            draw.rectangle(
                (tx + tile_w / 2 - 20, ty + 142, tx + tile_w / 2 + 20, ty + 178),
                fill=reducido_hex,
                outline="#795548" if reducido == 9 else "#777777",
                width=2,
            )
            draw.text(
                (tx + tile_w / 2, ty + 160),
                str(reducido),
                font=fuente_chica,
                fill=_color_texto_para(reducido_hex),
                anchor="mm",
            )

    total = resultado.get("total_codigo", 0)
    pasos = resultado.get("pasos_reduccion", [total])
    final = resultado.get("resultado_final", 0)
    final_hex = resultado.get("hex_final", "#FFFFFF")
    resumen_y = 780
    draw.rounded_rectangle((230, resumen_y, ancho - 230, resumen_y + 54), radius=8, fill="#F5EFE7")
    draw.text((ancho / 2, resumen_y + 27), f"TOTAL DE CODIGOS: {total}", font=fuente_negrita, fill="#4A2A18", anchor="mm")

    proceso = " -> ".join(str(p) for p in pasos)
    draw.text((ancho / 2, resumen_y + 94), f"PROCESO DE REDUCCION: {proceso}", font=fuente, fill="#4A2A18", anchor="mm")
    draw.rounded_rectangle((ancho / 2 - 75, resumen_y + 126, ancho / 2 + 75, resumen_y + 206), radius=8, fill=final_hex, outline="#795548", width=3)
    draw.text((ancho / 2, resumen_y + 166), str(final), font=fuente_titulo, fill=_color_texto_para(final_hex), anchor="mm")

    if len(resultado.get("detalle_visual", [])) > len(detalle):
        draw.text((ancho / 2, alto - 112), f"Vista resumida: {len(detalle)} de {len(resultado.get('detalle_visual', []))} caracteres", font=fuente, fill="#6F6677", anchor="mm")

    nombre = nombre_archivo or f"tarjeta_colores_{_slug_colores(titulo)}_{int(time.time() * 1000)}.jpg"
    ruta = Path(ruta_exportacion(nombre))
    ruta.parent.mkdir(parents=True, exist_ok=True)
    imagen.save(ruta, format="JPEG", quality=94, optimize=True)
    return str(ruta)


def datos_tarjeta_colores(resultado, titulo=None, incluir_base64=False):
    archivo = generar_tarjeta_colores(resultado, titulo=titulo)
    datos = {
        "archivo": archivo,
        "mime": "image/jpeg",
        "extension": "jpg",
    }
    if incluir_base64:
        datos["base64"] = base64.b64encode(Path(archivo).read_bytes()).decode("ascii")
    return datos


def valores_secundarios_colores(resultado):
    return [
        int(item.get("reducido") or 0)
        for item in (resultado or {}).get("detalle_visual", [])
    ]


def total_secundario_colores(resultado):
    return sum(valores_secundarios_colores(resultado))


def valores_terciarios_colores(resultado):
    """Devuelve los digitos tal como aparecen en todo el analisis primario."""
    resultado = resultado or {}
    total = resultado.get("total_codigo", 0)
    pasos = list(resultado.get("pasos_reduccion") or [])
    final = resultado.get("resultado_final", pasos[-1] if pasos else total)

    def digitos(valor):
        return [int(digito) for digito in str(abs(int(valor or 0)))]

    # El panel primario muestra el total, ambos lados de cada reduccion y el
    # resultado final. El terciario suma todos esos bloques visibles.
    valores = digitos(total)
    if len(pasos) <= 1:
        valores.extend(digitos(pasos[0] if pasos else total))
    else:
        for indice in range(len(pasos) - 1):
            valores.extend(digitos(pasos[indice]))
            valores.extend(digitos(pasos[indice + 1]))
    valores.extend(digitos(final))
    return valores or [0]


def total_terciario_colores(resultado):
    return sum(valores_terciarios_colores(resultado))


def _pdf_escape(texto):
    return str(texto).encode("cp1252", errors="replace").replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def _pdf_rgb(hex_color):
    color = str(hex_color or "#000000").strip().lstrip("#")
    if len(color) != 6:
        color = "000000"
    try:
        return tuple(int(color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except ValueError:
        return (0, 0, 0)


def _pdf_color(hex_color, operador="rg"):
    r, g, b = _pdf_rgb(hex_color)
    return f"{r:.3f} {g:.3f} {b:.3f} {operador}".encode("ascii")


def _pdf_text_width(texto, tamano):
    return len(str(texto or "")) * tamano * 0.52


def _pdf_texto(comandos, texto, x, y, tamano=10, color="#17131D", negrita=False, centrado=False):
    if centrado:
        x -= _pdf_text_width(texto, tamano) / 2
    fuente = "F2" if negrita else "F1"
    comandos.append(
        b"BT /" + fuente.encode("ascii") + f" {tamano} Tf ".encode("ascii")
        + _pdf_color(color)
        + f" 1 0 0 1 {x:.2f} {y:.2f} Tm ".encode("ascii")
        + b"(" + _pdf_escape(texto) + b") Tj ET"
    )


def _pdf_rect(comandos, x, y, ancho, alto, relleno="#FFFFFF", borde="#EFD7DB", grosor=1):
    comandos.append(
        b"q "
        + f"{grosor:.2f} w ".encode("ascii")
        + _pdf_color(relleno, "rg") + b" "
        + _pdf_color(borde, "RG") + b" "
        + f"{x:.2f} {y:.2f} {ancho:.2f} {alto:.2f} re B Q".encode("ascii")
    )


def _pdf_bloque_digito(comandos, digito, x, y, tamano=28):
    digito = int(digito or 0)
    info = DIGITO_COLORES.get(digito, DIGITO_COLORES[0])
    color = info["hex"]
    borde = "#795548" if digito == 9 else "#EFD7DB"
    _pdf_rect(comandos, x, y, tamano, tamano, color, borde, 1.2)
    _pdf_texto(
        comandos,
        str(digito),
        x + tamano / 2,
        y + tamano * 0.34,
        max(8, tamano * 0.42),
        _color_texto_para(color),
        True,
        True,
    )


def _pdf_digitos_numero(valor):
    texto = str(abs(int(valor or 0)))
    return [int(digito) for digito in texto] or [0]


def _pdf_fila_digitos(comandos, digitos, centro_x, y, tamano=30, espacio=12):
    ancho = len(digitos) * tamano + max(0, len(digitos) - 1) * espacio
    x = centro_x - ancho / 2
    for digito in digitos:
        _pdf_bloque_digito(comandos, digito, x, y, tamano)
        x += tamano + espacio


def _pdf_fila_suma(comandos, valores, centro_x, y, tamano=24, max_ancho=300, resultado=None):
    elementos = []
    for indice, valor in enumerate(valores):
        if indice:
            elementos.append("+")
        elementos.append(int(valor or 0))
    if resultado is not None:
        elementos.append("=")
        elementos.extend(_pdf_digitos_numero(resultado))

    ancho = 0
    for elemento in elementos:
        ancho += tamano if isinstance(elemento, int) else 12
    ancho += max(0, len(elementos) - 1) * 6
    x = centro_x - min(ancho, max_ancho) / 2
    cursor_x = x
    cursor_y = y

    for elemento in elementos:
        ancho_elemento = tamano if isinstance(elemento, int) else 12
        if cursor_x + ancho_elemento > centro_x + max_ancho / 2 and cursor_x > x:
            cursor_x = x
            cursor_y -= tamano + 10
        if isinstance(elemento, int):
            _pdf_bloque_digito(comandos, elemento, cursor_x, cursor_y, tamano)
        else:
            _pdf_texto(comandos, elemento, cursor_x + 5, cursor_y + 7, 13, "#171717", True)
        cursor_x += ancho_elemento + 6
    return cursor_y


def _pdf_wrap(texto, max_chars):
    palabras = str(texto or "").split()
    lineas = []
    actual = ""
    for palabra in palabras:
        candidato = f"{actual} {palabra}".strip()
        if len(candidato) > max_chars and actual:
            lineas.append(actual)
            actual = palabra
        else:
            actual = candidato
    if actual:
        lineas.append(actual)
    return lineas or [""]


def _pdf_pagina_resumen(resultado, titulo):
    ancho, alto = 842, 595
    comandos = [
        b"0.988 0.980 1.000 rg 0 0 842 595 re f",
    ]
    _pdf_texto(comandos, "CODIGO ESCONDIDO 19 - COLORES", 421, 558, 18, "#17131D", True, True)
    _pdf_texto(comandos, titulo or "Analisis de colores", 421, 536, 10, "#6F6677", False, True)

    texto = resultado.get("texto_limpio", "")
    _pdf_rect(comandos, 32, 485, 778, 38, "#FFFEFC", "#EFD7DB")
    for indice, linea in enumerate(_pdf_wrap(texto, 112)[:2]):
        _pdf_texto(comandos, linea or "Sin texto", 46, 508 - indice * 13, 10, "#17131D", indice == 0)

    total = resultado.get("total_codigo", 0)
    pasos = resultado.get("pasos_reduccion", [])
    final = resultado.get("resultado_final", 0)
    final_hex = resultado.get("hex_final", "#FFFFFF")
    panel_y = 150
    panel_alto = 318
    panel_ancho = 365
    izquierdo_x = 36
    derecho_x = 441

    _pdf_rect(comandos, izquierdo_x, panel_y, panel_ancho, panel_alto, "#FFFEFC", "#171717", 1.6)
    _pdf_texto(comandos, "ANALISIS PRIMARIO", izquierdo_x + panel_ancho / 2, panel_y + panel_alto - 24, 12, "#17131D", True, True)
    _pdf_texto(comandos, "TOTAL DE CODIGOS:", izquierdo_x + panel_ancho / 2, panel_y + panel_alto - 56, 14, "#17131D", True, True)
    _pdf_fila_digitos(comandos, _pdf_digitos_numero(total), izquierdo_x + panel_ancho / 2, panel_y + panel_alto - 98, 30, 18)
    _pdf_texto(comandos, "PROCESO DE REDUCCION", izquierdo_x + panel_ancho / 2, panel_y + panel_alto - 130, 10, "#6F6677", True, True)
    y = panel_y + panel_alto - 168
    if len(pasos) <= 1:
        _pdf_fila_digitos(comandos, _pdf_digitos_numero(total), izquierdo_x + panel_ancho / 2, y, 26, 10)
    else:
        for indice in range(len(pasos) - 1):
            y = _pdf_fila_suma(
                comandos,
                _pdf_digitos_numero(pasos[indice]),
                izquierdo_x + panel_ancho / 2,
                y,
                25,
                panel_ancho - 30,
                pasos[indice + 1],
            ) - 42
    _pdf_texto(comandos, "RESULTADO FINAL", izquierdo_x + panel_ancho / 2, panel_y + 76, 10, "#6F6677", True, True)
    _pdf_rect(comandos, izquierdo_x + panel_ancho / 2 - 42, panel_y + 26, 84, 42, final_hex, "#795548", 1.4)
    _pdf_texto(comandos, str(final), izquierdo_x + panel_ancho / 2, panel_y + 39, 24, _color_texto_para(final_hex), True, True)

    valores = valores_secundarios_colores(resultado)
    total_secundario = sum(valores)
    _pdf_rect(comandos, derecho_x, panel_y, panel_ancho, panel_alto, "#FFFEFC", "#171717", 1.6)
    _pdf_texto(comandos, "ANALISIS SECUNDARIO", derecho_x + panel_ancho / 2, panel_y + panel_alto - 24, 12, "#17131D", True, True)
    _pdf_texto(comandos, "SUMA DE RESULTADOS EN 1 DIGITO:", derecho_x + panel_ancho / 2, panel_y + panel_alto - 58, 11, "#17131D", True, True)
    visibles = valores[:48]
    y_sec = _pdf_fila_suma(comandos, visibles, derecho_x + panel_ancho / 2, panel_y + panel_alto - 102, 21, panel_ancho - 32)
    if len(valores) > len(visibles):
        _pdf_texto(comandos, f"+ {len(valores) - len(visibles)} valores mas en el detalle", derecho_x + panel_ancho / 2, y_sec - 22, 9, "#6F6677", False, True)
    _pdf_texto(comandos, "RESULTADO SIN REDUCIR:", derecho_x + panel_ancho / 2, panel_y + 110, 10, "#6F6677", True, True)
    _pdf_fila_digitos(comandos, _pdf_digitos_numero(total_secundario), derecho_x + panel_ancho / 2, panel_y + 66, 30, 8)

    valores_terciarios = valores_terciarios_colores(resultado)
    total_terciario = sum(valores_terciarios)
    terciario_y = 22
    _pdf_rect(comandos, 36, terciario_y, 770, 112, "#FFFEFC", "#EFD7DB", 1.0)
    _pdf_texto(comandos, "ANALISIS TERCIARIO", 421, terciario_y + 92, 11, "#17131D", True, True)
    _pdf_texto(comandos, "SUMA DE TODOS LOS NUMEROS DEL ANALISIS PRIMARIO:", 421, terciario_y + 74, 9, "#6F6677", True, True)
    _pdf_fila_suma(comandos, valores_terciarios[:36], 421, terciario_y + 51, 17, 708)
    if len(valores_terciarios) > 36:
        _pdf_texto(comandos, f"+ {len(valores_terciarios) - 36} valores incluidos", 421, terciario_y + 35, 8, "#6F6677", False, True)
    _pdf_texto(comandos, "RESULTADO SIN REDUCIR:", 330, terciario_y + 15, 9, "#6F6677", True, True)
    _pdf_fila_digitos(comandos, _pdf_digitos_numero(total_terciario), 500, terciario_y + 8, 22, 6)
    return comandos


def _pdf_paginas_detalle(resultado):
    detalle = resultado.get("detalle_visual", [])
    paginas = []
    ancho, alto = 842, 595
    por_pagina = 30
    for inicio in range(0, len(detalle), por_pagina):
        comandos = [b"0.988 0.980 1.000 rg 0 0 842 595 re f"]
        _pdf_texto(comandos, "DETALLE DEL ANALISIS", 36, 560, 16, "#17131D", True)
        _pdf_texto(comandos, f"Bloques {inicio + 1} - {min(inicio + por_pagina, len(detalle))} de {len(detalle)}", 36, 540, 9, "#6F6677")
        y = 506
        for indice, item in enumerate(detalle[inicio:inicio + por_pagina], start=inicio + 1):
            _pdf_rect(comandos, 36, y - 6, 770, 22, "#FFFEFC", "#EFD7DB", 0.6)
            color = item.get("hex", "#FFFFFF")
            _pdf_rect(comandos, 48, y - 2, 20, 16, color, "#795548" if item.get("reducido") == 9 else "#EFD7DB", 0.8)
            _pdf_texto(comandos, str(item.get("letra", "")), 58, y + 3, 8, _color_texto_para(color), True, True)
            _pdf_texto(comandos, f"{indice}. valor {item.get('valor', '')}", 80, y + 2, 9, "#17131D")
            _pdf_texto(comandos, f"resultado {item.get('reducido', '')} - {item.get('color', '')}", 180, y + 2, 9, "#17131D")
            x = 360
            for digito in item.get("digitos_colores", [])[:6]:
                _pdf_bloque_digito(comandos, digito.get("digito", 0), x, y - 3, 17)
                x += 22
            y -= 30
        paginas.append(comandos)
    return paginas


def _pdf_guardar(paginas, archivo):
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        None,
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
    ]
    paginas_ids = []
    for comandos in paginas:
        stream = b"\n".join(comandos)
        pagina_id = len(objetos) + 1
        contenido_id = pagina_id + 1
        paginas_ids.append(pagina_id)
        objetos.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 595] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {contenido_id} 0 R >>".encode("ascii")
        )
        objetos.append(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream")

    objetos[1] = ("<< /Type /Pages /Kids [" + " ".join(f"{identificador} 0 R" for identificador in paginas_ids) + f"] /Count {len(paginas_ids)} >>").encode("ascii")
    salida = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for indice, objeto in enumerate(objetos, start=1):
        offsets.append(len(salida))
        salida.extend(f"{indice} 0 obj\n".encode("ascii"))
        salida.extend(objeto)
        salida.extend(b"\nendobj\n")
    inicio_xref = len(salida)
    salida.extend(f"xref\n0 {len(objetos) + 1}\n".encode("ascii"))
    salida.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        salida.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    salida.extend(f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{inicio_xref}\n%%EOF".encode("ascii"))

    with open(archivo, "wb") as destino:
        destino.write(salida)
    return archivo


def exportar_pdf_colores(resultado, titulo=None, archivo=None):
    titulo = str(titulo or (resultado or {}).get("texto_limpio") or "Analisis de colores").strip()
    if archivo is None:
        archivo = ruta_exportacion(f"analisis_colores_{_slug_colores(titulo)}_{int(time.time() * 1000)}.pdf")
    Path(archivo).parent.mkdir(parents=True, exist_ok=True)
    paginas = [_pdf_pagina_resumen(resultado or {}, titulo)]
    paginas.extend(_pdf_paginas_detalle(resultado or {}))
    return _pdf_guardar(paginas or [[b"BT ET"]], archivo)


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
        return "PURPURA"
    else:
        return "ROJO VIOLACEO"


def hex_color_puro(nombre, fallback="#FFFFFF"):
    nombre = str(nombre or "").upper().strip()

    equivalencias = {
        "MARRON VERDOSO": "MARRON",
        "ROJO VIOLACEO": "ROJO",
        "VIOLETA": "PURPURA",
        "PÚRPURA": "PURPURA",
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
