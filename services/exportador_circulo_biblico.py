"""Render de alta resolucion y PDF multipagina para el Aro Arcoiris."""

import io
import math

from logica.analizador_colores import DIGITO_COLORES
from logica.circulo_biblico import COLOR_CONTORNO, ModeloAro, color_texto_para_digito


def _fuente(tamano, negrita=False):
    from PIL import ImageFont
    nombres = ["arialbd.ttf" if negrita else "arial.ttf", "DejaVuSans-Bold.ttf" if negrita else "DejaVuSans.ttf"]
    for nombre in nombres:
        try:
            return ImageFont.truetype(nombre, max(7, int(tamano)))
        except OSError:
            continue
    return ImageFont.load_default()


def _texto_centrado(draw, posicion, texto, fuente, color):
    caja = draw.textbbox((0, 0), texto, font=fuente)
    draw.text((posicion[0] - (caja[2]-caja[0])/2, posicion[1] - (caja[3]-caja[1])/2), texto, font=fuente, fill=color)


def _fuente_sector(cantidad, lado):
    return _fuente(max(7, min(lado * 0.016, lado * 0.82 / max(35, cantidad * 0.66))), True)


def _dibujar_anillo(draw, anillo, caja, centro, radio_etiqueta, radio_desde, radio_hasta, grosor):
    if anillo.color_solido:
        draw.ellipse(caja, fill=anillo.color_solido)
    else:
        for seccion in anillo.secciones:
            draw.pieslice(caja, seccion.inicio_grados, seccion.fin_grados, fill=seccion.color)
        for seccion in anillo.secciones:
            angulo = math.radians(seccion.inicio_grados)
            draw.line((
                centro[0] + radio_desde * math.cos(angulo), centro[1] + radio_desde * math.sin(angulo),
                centro[0] + radio_hasta * math.cos(angulo), centro[1] + radio_hasta * math.sin(angulo),
            ), fill=COLOR_CONTORNO, width=grosor)

    if anillo.secciones:
        fuente = _fuente_sector(len(anillo.secciones), radio_hasta * 2)
        for seccion in anillo.secciones:
            angulo = math.radians(seccion.medio_grados)
            _texto_centrado(draw, (
                centro[0] + radio_etiqueta * math.cos(angulo),
                centro[1] + radio_etiqueta * math.sin(angulo),
            ), seccion.etiqueta, fuente, color_texto_para_digito(seccion.digito))
    elif anillo.etiqueta_solida:
        _texto_centrado(draw, (centro[0], centro[1] - radio_etiqueta), anillo.etiqueta_solida,
                        _fuente(max(12, radio_hasta * 0.045), True), color_texto_para_digito(anillo.digito_solido))


def generar_imagen_aro(modelo: ModeloAro, lado=1800):
    from PIL import Image, ImageDraw
    lado = max(1000, int(lado))
    alto = round(lado * 1.25)
    imagen = Image.new("RGB", (lado, alto), "#FFFDF8")
    draw = ImageDraw.Draw(imagen)
    cx, cy = lado / 2, lado * 0.55
    radio_exterior = lado * 0.43
    radio_limite = radio_exterior * 0.76
    radio_hueco = radio_exterior * 0.23
    grosor = max(3, lado // 480)
    caja_exterior = (cx-radio_exterior, cy-radio_exterior, cx+radio_exterior, cy+radio_exterior)
    caja_interior = (cx-radio_limite, cy-radio_limite, cx+radio_limite, cy+radio_limite)

    _texto_centrado(draw, (cx, 55), "ARO ARCOIRIS", _fuente(lado * 0.033, True), COLOR_CONTORNO)
    _texto_centrado(draw, (cx, 120), modelo.titulo, _fuente(lado * 0.026, True), COLOR_CONTORNO)
    _texto_centrado(draw, (cx, 170), modelo.resumen, _fuente(lado * 0.016), "#5B4A43")

    _dibujar_anillo(draw, modelo.exterior, caja_exterior, (cx, cy), (radio_limite+radio_exterior)/2,
                    radio_limite, radio_exterior, grosor)
    _dibujar_anillo(draw, modelo.interior, caja_interior, (cx, cy), (radio_hueco+radio_limite)/2,
                    radio_hueco, radio_limite, grosor)

    draw.ellipse(caja_exterior, outline=COLOR_CONTORNO, width=grosor * 2)
    draw.ellipse(caja_interior, outline=COLOR_CONTORNO, width=grosor * 2)
    draw.ellipse((cx-radio_hueco, cy-radio_hueco, cx+radio_hueco, cy+radio_hueco), fill="#FFFDF8", outline=COLOR_CONTORNO, width=grosor * 2)
    ancho_centro = radio_hueco * 1.7
    for y, texto, maximo, negrita in [
        (cy-radio_hueco*0.28, modelo.texto_centro_1, lado*0.013, True),
        (cy+radio_hueco*0.05, modelo.texto_centro_2, lado*0.012, True),
        (cy+radio_hueco*0.38, modelo.texto_centro_3, lado*0.009, False),
    ]:
        tamano = min(maximo, ancho_centro / max(8, len(texto)*0.58))
        _texto_centrado(draw, (cx, y), texto, _fuente(tamano, negrita), COLOR_CONTORNO)

    y_info = cy + radio_exterior + 45
    _texto_centrado(draw, (cx, y_info), f"Borde exterior: {modelo.exterior.nombre} · Interior: {modelo.interior.nombre}",
                    _fuente(lado * 0.014, True), COLOR_CONTORNO)
    y_leyenda = y_info + 70
    margen, espacio = lado * 0.045, lado * 0.012
    ancho = (lado - margen*2 - espacio*8) / 9
    for numero in range(1, 10):
        x = margen + (numero-1)*(ancho+espacio)
        color = DIGITO_COLORES[numero]["hex"]
        draw.rounded_rectangle((x, y_leyenda, x+ancho, y_leyenda+65), radius=12, fill=color, outline=COLOR_CONTORNO, width=2)
        _texto_centrado(draw, (x+ancho/2, y_leyenda+32), str(numero), _fuente(lado*0.015, True), color_texto_para_digito(numero))
    return imagen


def generar_png_aro(modelo: ModeloAro, lado=1800) -> bytes:
    salida = io.BytesIO()
    generar_imagen_aro(modelo, lado).save(salida, format="PNG", optimize=True)
    return salida.getvalue()


def generar_pdf_aros(modelos, lado=1800) -> bytes:
    modelos = list(modelos or [])
    if not modelos:
        raise ValueError("Agregue al menos un círculo para crear el PDF.")
    paginas = [generar_imagen_aro(modelo, lado).convert("RGB") for modelo in modelos]
    salida = io.BytesIO()
    paginas[0].save(salida, format="PDF", save_all=True, append_images=paginas[1:], resolution=150.0)
    return salida.getvalue()
