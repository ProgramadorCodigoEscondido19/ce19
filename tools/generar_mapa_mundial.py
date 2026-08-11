"""Genera el mapa local de disponibilidad a partir de world.geojson."""

import json
from pathlib import Path

from PIL import Image, ImageDraw


RAIZ = Path(__file__).resolve().parents[1]
ARCHIVO_ENTRADA = RAIZ / "assets" / "world.geojson"
ARCHIVO_SALIDA = RAIZ / "assets" / "mapa_mundo_hispano.png"

PAISES_HISPANOS = {
    "Argentina", "Bolivia", "Chile", "Colombia", "Costa Rica", "Cuba",
    "Dominican Republic", "Ecuador", "El Salvador", "Equatorial Guinea",
    "Guatemala", "Honduras", "Mexico", "Nicaragua", "Panama", "Paraguay",
    "Peru", "Spain", "Uruguay", "Venezuela",
}

ANCHO, ALTO = 1600, 800
LON_MIN, LON_MAX = -180, 180
LAT_MIN, LAT_MAX = -60, 85

VISTAS_CONTINENTE = {
    "america": {
        "salida": RAIZ / "assets" / "mapa_america.png",
        # Incluye Alaska, Canada y toda Sudamerica, sin mostrar otros continentes.
        "limites": (-170, -25, -60, 75),
        "tamano": (1200, 1000),
        "destacados": {
            "Argentina", "Bolivia", "Chile", "Colombia", "Costa Rica", "Cuba",
            "Dominican Republic", "Ecuador", "El Salvador", "Guatemala", "Honduras",
            "Mexico", "Nicaragua", "Panama", "Paraguay", "Peru", "Uruguay", "Venezuela",
        },
    },
    "europa": {
        "salida": RAIZ / "assets" / "mapa_europa.png",
        "limites": (-25, 45, 30, 75),
        "tamano": (1200, 780),
        "destacados": {"Spain"},
    },
    "africa": {
        "salida": RAIZ / "assets" / "mapa_africa.png",
        "limites": (-30, 65, -38, 38),
        "tamano": (1200, 960),
        "destacados": {"Equatorial Guinea"},
    },
}


def proyectar(lon, lat, limites, ancho, alto):
    lon_min, lon_max, lat_min, lat_max = limites
    x = (lon - lon_min) / (lon_max - lon_min) * ancho
    y = (lat_max - lat) / (lat_max - lat_min) * alto
    return round(x), round(y)


def anillos(geometria):
    if geometria["type"] == "Polygon":
        return geometria["coordinates"]
    if geometria["type"] == "MultiPolygon":
        return [anillo for poligono in geometria["coordinates"] for anillo in poligono]
    return []


def generar_mapa(datos, salida, limites, destacados, tamano=(ANCHO, ALTO)):
    ancho, alto = tamano
    # Gama marrón cálida para distinguir el mapa de la interfaz violeta.
    imagen = Image.new("RGB", (ancho, alto), "#F7EDE3")
    dibujo = ImageDraw.Draw(imagen)

    for x in range(0, ancho, max(1, ancho // 10)):
        dibujo.line((x, 0, x, alto), fill="#E8D6C4", width=1)
    for y in range(0, alto, max(1, alto // 8)):
        dibujo.line((0, y, ancho, y), fill="#E8D6C4", width=1)

    for caracteristica in datos["features"]:
        nombre = caracteristica["properties"]["name"]
        for anillo in anillos(caracteristica["geometry"]):
            if not any(
                limites[0] <= lon <= limites[1] and limites[2] <= lat <= limites[3]
                for lon, lat in anillo
            ):
                continue
            relleno = "#8B5A3C" if nombre in destacados else "#E5D4C2"
            borde = "#FFFDF9" if nombre in destacados else "#BFA58E"
            puntos = [proyectar(lon, lat, limites, ancho, alto) for lon, lat in anillo]
            if len(puntos) > 2:
                dibujo.polygon(puntos, fill=relleno)
                dibujo.line(puntos + [puntos[0]], fill=borde, width=2)

    salida.parent.mkdir(parents=True, exist_ok=True)
    imagen.save(salida, "PNG", optimize=True)


def main():
    datos = json.loads(ARCHIVO_ENTRADA.read_text(encoding="utf-8"))
    generar_mapa(datos, ARCHIVO_SALIDA, (LON_MIN, LON_MAX, LAT_MIN, LAT_MAX), PAISES_HISPANOS)
    for vista in VISTAS_CONTINENTE.values():
        generar_mapa(datos, vista["salida"], vista["limites"], vista["destacados"], vista["tamano"])


if __name__ == "__main__":
    main()
