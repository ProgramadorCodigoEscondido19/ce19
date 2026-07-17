import base64
import re
import time
from pathlib import Path

from core.rutas import RAIZ_PROYECTO, ruta_exportacion


BASE_TARJETA = RAIZ_PROYECTO / "assets" / "tarjeta_versiculo_base.png"
FUENTE_TARJETA_NEGRITA = (
    RAIZ_PROYECTO / "assets" / "fonts" / "DejaVuSerif-Bold.ttf"
)
ANCHO_TARJETA = 1536
ALTO_TARJETA = 1024
MIME_TARJETA = "image/jpeg"
EXTENSION_TARJETA = "jpg"


class TarjetaBiblicaError(Exception):
    pass


def _pil():
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
    except Exception as exc:
        raise TarjetaBiblicaError("No se pudo cargar el generador de imagenes.") from exc

    return Image, ImageDraw, ImageFilter, ImageFont, ImageOps


def _slug(texto):
    texto = re.sub(r"\s+", "_", str(texto or "").strip())
    texto = re.sub(r"[^A-Za-z0-9_]+", "", texto)
    return texto.strip("_") or "versiculo"


def _datos_base64(captura, mime_default="image/png"):
    if isinstance(captura, bytes):
        return base64.b64encode(captura).decode("ascii"), mime_default

    texto = str(captura or "").strip()
    mime = mime_default

    if texto.startswith("data:") and "," in texto:
        encabezado, texto = texto.split(",", 1)
        mime = encabezado[5:].split(";", 1)[0] or mime_default

    return texto, mime


def _extension_desde_mime(mime):
    mime = (mime or "").lower()

    if "jpeg" in mime or "jpg" in mime:
        return "jpg"

    if "webp" in mime:
        return "webp"

    return "png"


def _fuente(ImageFont, tamano, negrita=False):
    nombres = [
        "georgiab.ttf" if negrita else "georgia.ttf",
        "timesbd.ttf" if negrita else "times.ttf",
        "arialbd.ttf" if negrita else "arial.ttf",
        "DejaVuSerif-Bold.ttf" if negrita else "DejaVuSerif.ttf",
        "DejaVuSans-Bold.ttf" if negrita else "DejaVuSans.ttf",
    ]

    rutas_empaquetadas = [FUENTE_TARJETA_NEGRITA]
    rutas_windows = [
        Path("C:/Windows/Fonts") / nombre
        for nombre in nombres
    ]

    # Esta fuente viaja dentro de la app. Es necesaria en Android, donde las
    # fuentes de Windows no existen y Pillow usaría una letra diminuta.
    for ruta in [*rutas_empaquetadas, *rutas_windows]:
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


def _bbox(draw, texto, fuente):
    try:
        return draw.textbbox((0, 0), texto, font=fuente)
    except Exception:
        ancho = len(texto) * max(getattr(fuente, "size", 18) * 0.55, 8)
        alto = max(getattr(fuente, "size", 18), 14)
        return (0, 0, int(ancho), int(alto))


def _ancho_texto(draw, texto, fuente):
    caja = _bbox(draw, texto, fuente)
    return caja[2] - caja[0]


def _alto_texto(draw, texto, fuente):
    caja = _bbox(draw, texto, fuente)
    return caja[3] - caja[1]


def _envolver_texto(draw, texto, fuente, ancho_maximo):
    palabras = re.sub(r"\s+", " ", str(texto or "").strip()).split(" ")
    lineas = []
    actual = ""

    for palabra in palabras:
        prueba = palabra if not actual else f"{actual} {palabra}"

        if _ancho_texto(draw, prueba, fuente) <= ancho_maximo:
            actual = prueba
            continue

        if actual:
            lineas.append(actual)
            actual = palabra
        else:
            fragmento = ""
            for letra in palabra:
                prueba_fragmento = fragmento + letra
                if _ancho_texto(draw, prueba_fragmento, fuente) <= ancho_maximo:
                    fragmento = prueba_fragmento
                else:
                    if fragmento:
                        lineas.append(fragmento)
                    fragmento = letra
            actual = fragmento

    if actual:
        lineas.append(actual)

    return lineas or [""]


def _dibujar_resplandor_linea(imagen, draw, texto, xy, fuente, color=(255, 225, 104)):
    Image, _, ImageFilter, _, _ = _pil()
    x, y = xy

    for radio, alpha in ((18, 72), (9, 105), (4, 130)):
        capa = Image.new("RGBA", imagen.size, (0, 0, 0, 0))
        capa_draw = draw.__class__(capa)
        capa_draw.text(
            (x, y),
            texto,
            font=fuente,
            fill=(color[0], color[1], color[2], alpha),
        )
        imagen.alpha_composite(capa.filter(ImageFilter.GaussianBlur(radio)))

    draw.text((x + 2, y + 3), texto, font=fuente, fill=(65, 30, 0, 150))
    draw.text((x, y), texto, font=fuente, fill=(255, 243, 174, 255))
    draw.text((x, y), texto, font=fuente, fill=(250, 205, 70, 230))


def _dibujar_centrado(imagen, draw, lineas, fuente, centro_y, separacion, color=(255, 225, 104)):
    altos = [_alto_texto(draw, linea, fuente) for linea in lineas]
    total = sum(altos) + separacion * max(len(lineas) - 1, 0)
    y = centro_y - total / 2

    for linea, alto in zip(lineas, altos):
        ancho = _ancho_texto(draw, linea, fuente)
        x = (imagen.width - ancho) / 2
        _dibujar_resplandor_linea(imagen, draw, linea, (x, y), fuente, color)
        y += alto + separacion


def _preparar_lienzo():
    Image, ImageDraw, _, _, ImageOps = _pil()

    if BASE_TARJETA.exists():
        imagen = Image.open(BASE_TARJETA).convert("RGB")
        resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
        imagen = ImageOps.fit(imagen, (ANCHO_TARJETA, ALTO_TARJETA), method=resampling)
    else:
        imagen = Image.new("RGB", (ANCHO_TARJETA, ALTO_TARJETA), "#240048")

    return imagen.convert("RGBA"), ImageDraw.Draw


def generar_tarjeta_versiculo(referencia, texto, nombre_archivo=None):
    Image, ImageDraw, _, ImageFont, _ = _pil()
    imagen, draw_class = _preparar_lienzo()
    draw = draw_class(imagen)

    referencia = str(referencia or "").strip()
    texto = str(texto or "").strip()

    margen_x = int(ANCHO_TARJETA * 0.12)
    ancho_texto = ANCHO_TARJETA - margen_x * 2

    for tamano in range(80, 42, -2):
        fuente_ref = _fuente(ImageFont, tamano, negrita=True)
        if _ancho_texto(draw, referencia, fuente_ref) <= ancho_texto:
            break

    ref_x = (ANCHO_TARJETA - _ancho_texto(draw, referencia, fuente_ref)) / 2
    _dibujar_resplandor_linea(
        imagen,
        draw,
        referencia,
        (ref_x, 120),
        fuente_ref,
        color=(255, 218, 86),
    )

    draw.line(
        (margen_x, 226, ANCHO_TARJETA - margen_x, 226),
        fill=(255, 225, 105, 160),
        width=3,
    )

    for tamano in range(58, 29, -2):
        fuente_texto = _fuente(ImageFont, tamano, negrita=True)
        lineas = _envolver_texto(draw, texto, fuente_texto, ancho_texto)
        alto_linea = max(_alto_texto(draw, linea, fuente_texto) for linea in lineas)
        total = len(lineas) * alto_linea + max(len(lineas) - 1, 0) * 18

        if total <= 390:
            break

    _dibujar_centrado(
        imagen,
        draw,
        lineas,
        fuente_texto,
        centro_y=430,
        separacion=18,
        color=(255, 218, 86),
    )

    imagen = imagen.convert("RGB")
    nombre = nombre_archivo or f"tarjeta_{_slug(referencia)}_{int(time.time() * 1000)}.{EXTENSION_TARJETA}"
    ruta = Path(ruta_exportacion(nombre))
    ruta.parent.mkdir(parents=True, exist_ok=True)
    imagen.save(ruta, format="JPEG", quality=94, optimize=True)
    return str(ruta)


def tarjeta_versiculo_base64(referencia, texto, nombre_archivo=None):
    archivo = generar_tarjeta_versiculo(referencia, texto, nombre_archivo=nombre_archivo)
    datos = Path(archivo).read_bytes()
    return {
        "archivo": archivo,
        "base64": base64.b64encode(datos).decode("ascii"),
        "mime": MIME_TARJETA,
        "extension": EXTENSION_TARJETA,
    }


def datos_tarjeta_versiculo(referencia, texto, nombre_archivo=None, incluir_base64=False):
    archivo = generar_tarjeta_versiculo(referencia, texto, nombre_archivo=nombre_archivo)
    datos = {
        "archivo": archivo,
        "mime": MIME_TARJETA,
        "extension": EXTENSION_TARJETA,
    }

    if incluir_base64:
        datos["base64"] = base64.b64encode(Path(archivo).read_bytes()).decode("ascii")

    return datos


def guardar_captura_tarjeta_base64(referencia, captura, incluir_base64=False):
    captura_base64, mime = _datos_base64(captura)

    if not captura_base64:
        raise TarjetaBiblicaError("No se pudo capturar la tarjeta.")

    datos_originales = base64.b64decode(captura_base64)
    mime_salida = MIME_TARJETA
    extension_salida = EXTENSION_TARJETA
    nombre = f"tarjeta_{_slug(referencia)}_{int(time.time() * 1000)}.{extension_salida}"
    archivo = Path(ruta_exportacion(nombre))
    archivo.parent.mkdir(parents=True, exist_ok=True)

    try:
        from io import BytesIO

        Image, _, _, _, _ = _pil()
        imagen = Image.open(BytesIO(datos_originales)).convert("RGB")
        imagen.save(archivo, format="JPEG", quality=94, optimize=True)
    except Exception:
        mime_salida = mime or "image/png"
        extension_salida = _extension_desde_mime(mime_salida)
        archivo = Path(
            ruta_exportacion(
                f"tarjeta_{_slug(referencia)}_{int(time.time() * 1000)}.{extension_salida}"
            )
        )
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_bytes(datos_originales)

    datos = {
        "archivo": str(archivo),
        "mime": mime_salida,
        "extension": extension_salida,
    }

    if incluir_base64:
        datos["base64"] = base64.b64encode(archivo.read_bytes()).decode("ascii")

    return datos
