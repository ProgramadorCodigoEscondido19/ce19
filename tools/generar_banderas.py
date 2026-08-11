"""Genera banderas locales para el selector de paises."""

from pathlib import Path

from PIL import Image, ImageDraw


DESTINO = Path(__file__).resolve().parents[1] / "assets" / "banderas"
ANCHO, ALTO = 120, 80


def estrella(cx, cy, radio_externo, radio_interno):
    puntos = []
    for indice in range(10):
        angulo = -1.5707963267948966 + indice * 0.6283185307179586
        radio = radio_externo if indice % 2 == 0 else radio_interno
        puntos.append((cx + radio * __import__("math").cos(angulo), cy + radio * __import__("math").sin(angulo)))
    return puntos


def guardar_chile():
    imagen = Image.new("RGB", (ANCHO, ALTO), "#FFFFFF")
    dibujo = ImageDraw.Draw(imagen)
    dibujo.rectangle((0, ALTO // 2, ANCHO, ALTO), fill="#D52B1E")
    dibujo.rectangle((0, 0, ALTO // 2, ALTO // 2), fill="#0039A6")
    dibujo.polygon(estrella(ALTO // 4, ALTO // 4, 12, 5), fill="#FFFFFF")
    imagen.save(DESTINO / "chile.png", "PNG", optimize=True)


def guardar_cuba():
    imagen = Image.new("RGB", (ANCHO, ALTO), "#FFFFFF")
    dibujo = ImageDraw.Draw(imagen)
    alto_franja = ALTO // 5
    for indice in (0, 2, 4):
        dibujo.rectangle((0, indice * alto_franja, ANCHO, (indice + 1) * alto_franja), fill="#002A8F")
    dibujo.polygon(((0, 0), (0, ALTO), (ALTO - 5, ALTO // 2)), fill="#CF142B")
    dibujo.polygon(estrella(20, ALTO // 2, 11, 4.5), fill="#FFFFFF")
    imagen.save(DESTINO / "cuba.png", "PNG", optimize=True)


def guardar_republica_dominicana():
    imagen = Image.new("RGB", (ANCHO, ALTO), "#FFFFFF")
    dibujo = ImageDraw.Draw(imagen)
    cruz = 10
    mitad_x, mitad_y = ANCHO // 2, ALTO // 2
    dibujo.rectangle((0, 0, mitad_x - cruz // 2, mitad_y - cruz // 2), fill="#002D62")
    dibujo.rectangle((mitad_x + cruz // 2, 0, ANCHO, mitad_y - cruz // 2), fill="#CE1126")
    dibujo.rectangle((0, mitad_y + cruz // 2, mitad_x - cruz // 2, ALTO), fill="#CE1126")
    dibujo.rectangle((mitad_x + cruz // 2, mitad_y + cruz // 2, ANCHO, ALTO), fill="#002D62")
    imagen.save(DESTINO / "republica_dominicana.png", "PNG", optimize=True)


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    guardar_chile()
    guardar_cuba()
    guardar_republica_dominicana()


if __name__ == "__main__":
    main()
