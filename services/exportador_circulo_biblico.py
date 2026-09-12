"""Exportacion de un ModeloAro a una imagen PNG de alta resolucion."""

import io
import math

from logica.analizador_colores import DIGITO_COLORES
from logica.circulo_biblico import COLOR_CONTORNO, ModeloAro, color_texto_para_digito


def _fuente(tamano, negrita=False):
    from PIL import ImageFont

    nombres = ["arialbd.ttf" if negrita else "arial.ttf", "DejaVuSans-Bold.ttf" if negrita else "DejaVuSans.ttf"]
    for nombre in nombres:
        try:
            return ImageFont.truetype(nombre, tamano)
        except OSError:
            continue
    return ImageFont.load_default()


def _texto_centrado(draw, posicion, texto, fuente, color):
    caja = draw.textbbox((0, 0), texto, font=fuente)
    ancho = caja[2] - caja[0]
    alto = caja[3] - caja[1]
    draw.text((posicion[0] - ancho / 2, posicion[1] - alto / 2), texto, font=fuente, fill=color)


def _fuente_ajustada(draw, texto, ancho_maximo, tamano_maximo, negrita=False):
    tamano = max(7, int(tamano_maximo))
    while tamano > 7:
        fuente = _fuente(tamano, negrita)
        caja = draw.textbbox((0, 0), texto, font=fuente)
        if caja[2] - caja[0] <= ancho_maximo:
            return fuente
        tamano -= 1
    return _fuente(7, negrita)


def generar_png_aro(modelo: ModeloAro, lado=1800) -> bytes:
    # Pillow se importa solo al exportar. La vista puede abrirse incluso en un
    # paquete antiguo que no lo incluya y usar la captura Flet como respaldo.
    from PIL import Image, ImageDraw

    lado = max(1000, int(lado))
    imagen = Image.new("RGB", (lado, lado + 420), "#FFFFFF")
    draw = ImageDraw.Draw(imagen)
    centro_x = lado / 2
    centro_y = lado / 2 + 150
    radio_exterior = lado * 0.39
    radio_limite = radio_exterior * 0.74
    radio_hueco = radio_exterior * 0.21
    ancho_anillo = radio_exterior - radio_limite
    caja_interior = [centro_x - radio_limite, centro_y - radio_limite, centro_x + radio_limite, centro_y + radio_limite]
    caja_anillo = [centro_x - radio_exterior, centro_y - radio_exterior, centro_x + radio_exterior, centro_y + radio_exterior]

    draw.text((lado * 0.06, 42), "Aro Arcoiris", font=_fuente(58, True), fill=COLOR_CONTORNO)
    draw.text((lado * 0.06, 112), f"{modelo.libro} · {modelo.cantidad_capitulos} capitulos", font=_fuente(36, True), fill="#17131D")

    for seccion in modelo.secciones:
        draw.pieslice(caja_interior, seccion.inicio_grados, seccion.fin_grados, fill=seccion.color_versiculos)
        draw.arc(caja_anillo, seccion.inicio_grados, seccion.fin_grados, fill=seccion.color_capitulo, width=round(ancho_anillo))

    grosor = max(3, lado // 420)
    for seccion in modelo.secciones:
        angulo = math.radians(seccion.inicio_grados)
        x = centro_x + radio_exterior * math.cos(angulo)
        y = centro_y + radio_exterior * math.sin(angulo)
        x_inicio = centro_x + radio_hueco * math.cos(angulo)
        y_inicio = centro_y + radio_hueco * math.sin(angulo)
        draw.line((x_inicio, y_inicio, x, y), fill=COLOR_CONTORNO, width=grosor)

    draw.ellipse([centro_x-radio_exterior, centro_y-radio_exterior, centro_x+radio_exterior, centro_y+radio_exterior], outline=COLOR_CONTORNO, width=grosor)
    draw.ellipse([centro_x-radio_limite, centro_y-radio_limite, centro_x+radio_limite, centro_y+radio_limite], outline=modelo.color_total_versiculos, width=grosor * 3)
    margen_total = grosor * 5
    draw.ellipse([centro_x-radio_exterior-margen_total, centro_y-radio_exterior-margen_total, centro_x+radio_exterior+margen_total, centro_y+radio_exterior+margen_total], outline=modelo.color_total_capitulos, width=grosor * 3)

    fondo_centro = "#FFFDF8"
    draw.ellipse([centro_x-radio_hueco, centro_y-radio_hueco, centro_x+radio_hueco, centro_y+radio_hueco], fill=fondo_centro, outline=COLOR_CONTORNO, width=grosor * 2)
    ancho_centro = radio_hueco * 1.72
    texto_borde = f"BORDE: {modelo.libro.upper()}"
    texto_interior = "INTERIOR: VERSÍCULOS"
    texto_claves = "C = capítulo · V = versículos"
    _texto_centrado(draw, (centro_x, centro_y - 34), texto_borde, _fuente_ajustada(draw, texto_borde, ancho_centro, 22, True), COLOR_CONTORNO)
    _texto_centrado(draw, (centro_x, centro_y + 5), texto_interior, _fuente_ajustada(draw, texto_interior, ancho_centro, 20, True), COLOR_CONTORNO)
    _texto_centrado(draw, (centro_x, centro_y + 43), texto_claves, _fuente_ajustada(draw, texto_claves, ancho_centro, 16), "#4D4248")

    fuente_etiqueta = _fuente(max(7, round(34 - modelo.cantidad_capitulos * 0.40)), True)
    for seccion in modelo.secciones:
        angulo = math.radians(seccion.medio_grados)
        radio_c = radio_limite + ancho_anillo * 0.52
        radio_v = (radio_hueco + radio_limite) / 2
        _texto_centrado(draw, (centro_x + radio_c * math.cos(angulo), centro_y + radio_c * math.sin(angulo)), f"C{seccion.capitulo}", fuente_etiqueta, color_texto_para_digito(seccion.digito_capitulo))
        _texto_centrado(draw, (centro_x + radio_v * math.cos(angulo), centro_y + radio_v * math.sin(angulo)), f"V{seccion.cantidad_versiculos}", fuente_etiqueta, color_texto_para_digito(seccion.digito_versiculos))

    y_texto = centro_y + radio_exterior + 50
    draw.text((lado * 0.06, y_texto), "Borde exterior: capítulos · Interior: versículos", font=_fuente(31, True), fill=COLOR_CONTORNO)
    draw.text((lado * 0.06, y_texto + 50), f"Contorno exterior: total de capítulos ({modelo.cantidad_capitulos}) · Borde interior: total de versículos ({modelo.total_versiculos})", font=_fuente(23), fill="#4D4248")
    inicio_x = lado * 0.06
    y_leyenda = y_texto + 112
    ancho_item = (lado * 0.88) / 9
    for numero in range(1, 10):
        x = inicio_x + (numero - 1) * ancho_item
        color = DIGITO_COLORES[numero]["hex"]
        draw.rounded_rectangle((x, y_leyenda, x + ancho_item - 12, y_leyenda + 82), radius=18, fill=color, outline=COLOR_CONTORNO, width=3)
        _texto_centrado(draw, (x + (ancho_item - 12) / 2, y_leyenda + 41), str(numero), _fuente(31, True), color_texto_para_digito(numero))

    salida = io.BytesIO()
    imagen.save(salida, format="PNG", optimize=True)
    return salida.getvalue()
