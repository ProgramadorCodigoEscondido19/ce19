import base64
from io import BytesIO
import math
import struct
import zlib


COLOR_BLANCO_BORDE = "#FFFFFF"
COLOR_MARRON_BORDE = "#795548"


def _hex_rgb(color):
    color = (color or "#111111").lstrip("#")

    if len(color) != 6:
        return (17, 17, 17)

    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _es_blanco_borde(color):
    return (color or "").upper() == COLOR_BLANCO_BORDE


def _color_borde_para(color):
    return _hex_rgb(COLOR_MARRON_BORDE) if _es_blanco_borde(color) else None


def _png_base64(ancho, alto, pixeles):
    def chunk(tipo, datos):
        cuerpo = tipo + datos
        return (
            struct.pack(">I", len(datos))
            + cuerpo
            + struct.pack(">I", zlib.crc32(cuerpo) & 0xFFFFFFFF)
        )

    filas = []

    for y in range(alto):
        inicio = y * ancho * 3
        fin = inicio + ancho * 3
        filas.append(b"\x00" + bytes(pixeles[inicio:fin]))

    datos = zlib.compress(b"".join(filas), 9)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", datos)
        + chunk(b"IEND", b"")
    )
    return base64.b64encode(png).decode("ascii")


def _poner_pixel(pixeles, ancho, alto, x, y, color):
    x = int(round(x))
    y = int(round(y))

    if x < 0 or y < 0 or x >= ancho or y >= alto:
        return

    i = (y * ancho + x) * 3
    pixeles[i:i + 3] = color


def _circulo(pixeles, ancho, alto, cx, cy, radio, color):
    radio = max(1, int(round(radio)))
    r2 = radio * radio

    for y in range(int(cy - radio), int(cy + radio) + 1):
        for x in range(int(cx - radio), int(cx + radio) + 1):
            if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= r2:
                _poner_pixel(pixeles, ancho, alto, x, y, color)


def _linea(pixeles, ancho, alto, x1, y1, x2, y2, grosor, color):
    pasos = max(int(max(abs(x2 - x1), abs(y2 - y1))), 1)
    radio = max(grosor / 2, 1)

    for paso in range(pasos + 1):
        t = paso / pasos
        x = x1 + (x2 - x1) * t
        y = y1 + (y2 - y1) * t
        _circulo(pixeles, ancho, alto, x, y, radio, color)


def _bounds(objetos):
    xs = []
    ys = []

    for objeto in objetos:
        if objeto.get("tipo") == "trazo":
            for x, y in objeto.get("puntos", []):
                xs.append(x)
                ys.append(y)
        elif "desde" in objeto:
            xs.extend([objeto["desde"][0], objeto["hasta"][0]])
            ys.extend([objeto["desde"][1], objeto["hasta"][1]])
        elif "x" in objeto:
            xs.append(objeto["x"])
            ys.append(objeto["y"])

    if not xs or not ys:
        return (0, 0, 900, 520)

    return (min(xs), min(ys), max(xs), max(ys))


def renderizar_lienzo_png_base64(lienzo, ancho=900, alto=520):
    fondo = _hex_rgb(lienzo.get("fondo", "#FFFFFF"))
    objetos = lienzo.get("objetos", [])
    pixeles = bytearray(fondo * ancho * alto)

    min_x, min_y, max_x, max_y = _bounds(objetos)
    margen = 24
    escala = min(
        (ancho - margen * 2) / max(max_x - min_x, 1),
        (alto - margen * 2) / max(max_y - min_y, 1),
        1.0,
    )

    def p(punto):
        return (
            (punto[0] - min_x) * escala + margen,
            (punto[1] - min_y) * escala + margen,
        )

    for objeto in objetos:
        tipo = objeto.get("tipo")
        color_hex = objeto.get("color", "#111111")
        color = _hex_rgb(color_hex)
        borde = _color_borde_para(color_hex)
        grosor = max(objeto.get("grosor", 3) * escala, 1)
        grosor_borde = grosor + 4 * escala

        if tipo == "trazo":
            puntos = objeto.get("puntos", [])

            if len(puntos) == 1:
                x, y = p(puntos[0])
                if borde:
                    _circulo(pixeles, ancho, alto, x, y, grosor_borde / 2, borde)
                _circulo(pixeles, ancho, alto, x, y, grosor / 2, color)

            for i in range(len(puntos) - 1):
                x1, y1 = p(puntos[i])
                x2, y2 = p(puntos[i + 1])
                if borde:
                    _linea(pixeles, ancho, alto, x1, y1, x2, y2, grosor_borde, borde)
                _linea(pixeles, ancho, alto, x1, y1, x2, y2, grosor, color)

        elif tipo == "linea":
            x1, y1 = p(objeto["desde"])
            x2, y2 = p(objeto["hasta"])
            if borde:
                _linea(pixeles, ancho, alto, x1, y1, x2, y2, grosor_borde, borde)
            _linea(pixeles, ancho, alto, x1, y1, x2, y2, grosor, color)

        elif tipo == "rectangulo":
            x1, y1 = p(objeto["desde"])
            x2, y2 = p(objeto["hasta"])
            if borde:
                _linea(pixeles, ancho, alto, x1, y1, x2, y1, grosor_borde, borde)
                _linea(pixeles, ancho, alto, x2, y1, x2, y2, grosor_borde, borde)
                _linea(pixeles, ancho, alto, x2, y2, x1, y2, grosor_borde, borde)
                _linea(pixeles, ancho, alto, x1, y2, x1, y1, grosor_borde, borde)
            _linea(pixeles, ancho, alto, x1, y1, x2, y1, grosor, color)
            _linea(pixeles, ancho, alto, x2, y1, x2, y2, grosor, color)
            _linea(pixeles, ancho, alto, x2, y2, x1, y2, grosor, color)
            _linea(pixeles, ancho, alto, x1, y2, x1, y1, grosor, color)

        elif tipo == "circulo":
            x1, y1 = p(objeto["desde"])
            x2, y2 = p(objeto["hasta"])
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            rx = abs(x2 - x1) / 2
            ry = abs(y2 - y1) / 2
            pasos = max(int((rx + ry) * math.pi / 2), 24)
            anterior = None

            for paso in range(pasos + 1):
                angulo = 2 * math.pi * paso / pasos
                punto = (cx + math.cos(angulo) * rx, cy + math.sin(angulo) * ry)

                if anterior:
                    if borde:
                        _linea(
                            pixeles,
                            ancho,
                            alto,
                            anterior[0],
                            anterior[1],
                            punto[0],
                            punto[1],
                            grosor_borde,
                            borde,
                        )
                    _linea(
                        pixeles,
                        ancho,
                        alto,
                        anterior[0],
                        anterior[1],
                        punto[0],
                        punto[1],
                        grosor,
                        color,
                    )

                anterior = punto

        elif tipo == "texto":
            x, y = p((objeto.get("x", 0), objeto.get("y", 0)))
            texto = objeto.get("texto", "")
            ancho_texto = max(len(texto) * max(grosor * 3, 6), 36)
            alto_texto = max(grosor * 5, 18)
            if borde:
                _linea(pixeles, ancho, alto, x, y, x + ancho_texto, y, grosor_borde, borde)
                _linea(pixeles, ancho, alto, x, y + alto_texto, x + ancho_texto, y + alto_texto, grosor_borde, borde)
                _linea(pixeles, ancho, alto, x, y, x, y + alto_texto, grosor_borde, borde)
                _linea(pixeles, ancho, alto, x + ancho_texto, y, x + ancho_texto, y + alto_texto, grosor_borde, borde)
            _linea(pixeles, ancho, alto, x, y, x + ancho_texto, y, grosor, color)
            _linea(pixeles, ancho, alto, x, y + alto_texto, x + ancho_texto, y + alto_texto, grosor, color)
            _linea(pixeles, ancho, alto, x, y, x, y + alto_texto, grosor, color)
            _linea(pixeles, ancho, alto, x + ancho_texto, y, x + ancho_texto, y + alto_texto, grosor, color)

    return _png_base64(ancho, alto, pixeles)


def convertir_png_base64_a_jpg_base64(imagen_png_base64, calidad=88):
    from PIL import Image

    datos = base64.b64decode(imagen_png_base64)
    entrada = BytesIO(datos)
    salida = BytesIO()
    imagen = Image.open(entrada).convert("RGB")
    imagen.save(salida, format="JPEG", quality=calidad, optimize=True)
    return base64.b64encode(salida.getvalue()).decode("ascii")


def renderizar_lienzo_jpg_base64(lienzo, ancho=900, alto=520, calidad=88):
    return convertir_png_base64_a_jpg_base64(
        renderizar_lienzo_png_base64(lienzo, ancho, alto),
        calidad=calidad,
    )


def renderizar_lienzo_exportable_base64(lienzo, ancho=900, alto=520):
    png = renderizar_lienzo_png_base64(lienzo, ancho, alto)

    try:
        return {
            "base64": convertir_png_base64_a_jpg_base64(png),
            "mime": "image/jpeg",
            "extension": "jpg",
        }
    except Exception:
        return {
            "base64": png,
            "mime": "image/png",
            "extension": "png",
        }
