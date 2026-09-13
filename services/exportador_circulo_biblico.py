"""Render de alta resolucion y PDF multipagina para el Aro Arcoiris."""

import math
import struct
import zlib

from logica.analizador_colores import DIGITO_COLORES
from logica.circulo_biblico import COLOR_CONTORNO, ModeloAro, color_texto_para_digito


def _rgb(color):
    color = str(color).lstrip("#")
    return tuple(int(color[indice:indice + 2], 16) for indice in (0, 2, 4))


def _png_chunk(tipo, datos):
    cuerpo = tipo + datos
    return struct.pack(">I", len(datos)) + cuerpo + struct.pack(">I", zlib.crc32(cuerpo) & 0xFFFFFFFF)


def generar_png_circulo_nativo(modelo: ModeloAro, lado=900) -> bytes:
    """Genera el color base del aro como PNG usando sólo la biblioteca estándar."""
    lado = max(320, min(1200, int(lado)))
    centro = (lado - 1) / 2
    radio_exterior = lado * 0.465
    radio_limite = radio_exterior * 0.76
    radio_hueco = radio_exterior * 0.23
    fondo = _rgb("#FFFDF8")
    contorno = _rgb(COLOR_CONTORNO)
    borde_exterior = _rgb(modelo.exterior.color_borde)
    borde_interior = _rgb(modelo.interior.color_borde)
    exterior_solido = _rgb(modelo.exterior.color_solido) if modelo.exterior.color_solido else None
    interior_solido = _rgb(modelo.interior.color_solido) if modelo.interior.color_solido else None
    colores_exterior = [_rgb(seccion.color) for seccion in modelo.exterior.secciones]
    colores_interior = [_rgb(seccion.color) for seccion in modelo.interior.secciones]
    cantidad_exterior = len(colores_exterior)
    cantidad_interior = len(colores_interior)
    tau = math.tau
    # Al generarse al doble de resolución y reducirse en pantalla, este trazo
    # queda fino y suavizado sin dominar los colores del aro.
    grosor = max(0.65, lado / 1000)

    def color_anillo(solido, colores, cantidad, angulo):
        if solido:
            return solido
        return colores[min(cantidad - 1, int(angulo * cantidad / tau))] if cantidad else fondo

    def es_division(cantidad, angulo, radio):
        if cantidad <= 1:
            return False
        paso = tau / cantidad
        resto = angulo % paso
        distancia_angular = min(resto, paso - resto)
        return distancia_angular * radio <= grosor

    filas = bytearray()
    for y in range(lado):
        fila = bytearray([0])
        dy = y - centro
        for x in range(lado):
            dx = x - centro
            radio = math.hypot(dx, dy)
            if radio < radio_hueco or radio > radio_exterior:
                color = fondo
            else:
                angulo = (math.atan2(dy, dx) + math.pi / 2) % tau
                if radio >= radio_limite:
                    color = color_anillo(exterior_solido, colores_exterior, cantidad_exterior, angulo)
                    division = es_division(cantidad_exterior, angulo, radio)
                else:
                    color = color_anillo(interior_solido, colores_interior, cantidad_interior, angulo)
                    division = es_division(cantidad_interior, angulo, radio)
                if division:
                    color = contorno
                if abs(radio - radio_exterior) <= grosor:
                    color = borde_exterior
                elif abs(radio - radio_limite) <= grosor or abs(radio - radio_hueco) <= grosor:
                    color = borde_interior
            fila.extend(color)
        filas.extend(fila)

    cabecera = struct.pack(">IIBBBBB", lado, lado, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", cabecera)
        + _png_chunk(b"IDAT", zlib.compress(bytes(filas), 7))
        + _png_chunk(b"IEND", b"")
    )


def _decodificar_png_rgb(datos):
    """Convierte un PNG 8-bit RGB/RGBA/gris no entrelazado a pixeles RGB."""
    if not datos.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("La captura no es un PNG válido.")
    posicion = 8
    idat = bytearray()
    ancho = alto = profundidad = tipo_color = entrelazado = None
    while posicion + 12 <= len(datos):
        longitud = struct.unpack(">I", datos[posicion:posicion + 4])[0]
        tipo = datos[posicion + 4:posicion + 8]
        contenido = datos[posicion + 8:posicion + 8 + longitud]
        posicion += 12 + longitud
        if tipo == b"IHDR":
            ancho, alto, profundidad, tipo_color, _, _, entrelazado = struct.unpack(">IIBBBBB", contenido)
        elif tipo == b"IDAT":
            idat.extend(contenido)
        elif tipo == b"IEND":
            break
    canales = {0: 1, 2: 3, 6: 4}.get(tipo_color)
    if not ancho or not alto or profundidad != 8 or canales is None or entrelazado:
        raise ValueError("El formato de la captura PNG no es compatible.")
    bruto = zlib.decompress(bytes(idat))
    paso = ancho * canales
    anterior = bytearray(paso)
    salida = bytearray()

    def paeth(a, b, c):
        p = a + b - c
        pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
        return a if pa <= pb and pa <= pc else (b if pb <= pc else c)

    cursor = 0
    for _ in range(alto):
        filtro = bruto[cursor]
        cursor += 1
        fila = bytearray(bruto[cursor:cursor + paso])
        cursor += paso
        for indice in range(paso):
            izquierda = fila[indice - canales] if indice >= canales else 0
            arriba = anterior[indice]
            diagonal = anterior[indice - canales] if indice >= canales else 0
            if filtro == 1:
                fila[indice] = (fila[indice] + izquierda) & 255
            elif filtro == 2:
                fila[indice] = (fila[indice] + arriba) & 255
            elif filtro == 3:
                fila[indice] = (fila[indice] + ((izquierda + arriba) // 2)) & 255
            elif filtro == 4:
                fila[indice] = (fila[indice] + paeth(izquierda, arriba, diagonal)) & 255
            elif filtro != 0:
                raise ValueError("Filtro PNG no compatible.")
        if tipo_color == 0:
            for valor in fila:
                salida.extend((valor, valor, valor))
        elif tipo_color == 2:
            salida.extend(fila)
        else:
            for indice in range(0, len(fila), 4):
                rojo, verde, azul, alfa = fila[indice:indice + 4]
                salida.extend((
                    (rojo * alfa + 255 * (255 - alfa)) // 255,
                    (verde * alfa + 255 * (255 - alfa)) // 255,
                    (azul * alfa + 255 * (255 - alfa)) // 255,
                ))
        anterior = fila
    return ancho, alto, bytes(salida)


def _texto_pdf(texto):
    texto = str(texto or "").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return texto.encode("cp1252", errors="replace")


def _color_pdf(color):
    rojo, verde, azul = _rgb(color)
    return f"{rojo / 255:.3f} {verde / 255:.3f} {azul / 255:.3f} rg"


def _comando_texto_pdf(texto, x, y, tamano, color=COLOR_CONTORNO, negrita=True, angulo=0):
    radianes = math.radians(angulo)
    coseno, seno = math.cos(radianes), math.sin(radianes)
    ancho_estimado = len(str(texto)) * tamano * 0.29
    x -= coseno * ancho_estimado
    y -= seno * ancho_estimado
    fuente = "/F2" if negrita else "/F1"
    return (
        f"{_color_pdf(color)} BT {fuente} {tamano:.2f} Tf "
        f"{coseno:.5f} {seno:.5f} {-seno:.5f} {coseno:.5f} {x:.3f} {y:.3f} Tm (".encode("ascii")
        + _texto_pdf(texto)
        + b") Tj ET\n"
    )


def generar_pdf_modelos_nativo(modelos, lado=900) -> bytes:
    """Exporta uno o más modelos completos a PDF sin requerir Pillow."""
    modelos = list(modelos or [])
    if not modelos:
        raise ValueError("No hay círculos seleccionados para exportar.")
    lado = max(700, min(1100, int(lado)))
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        None,
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
    ]
    paginas = []
    for modelo in modelos:
        png = generar_png_circulo_nativo(modelo, lado)
        ancho, alto, pixeles = _decodificar_png_rgb(png)
        pagina_id = len(objetos) + 1
        imagen_id = pagina_id + 1
        contenido_id = pagina_id + 2
        paginas.append(pagina_id)
        diametro_pdf = 510.0
        escala = diametro_pdf / lado
        origen_x, origen_y = 42.5, 190.0
        centro_x = origen_x + diametro_pdf / 2
        centro_y = origen_y + diametro_pdf / 2
        comandos = bytearray()
        comandos.extend(f"q {diametro_pdf} 0 0 {diametro_pdf} {origen_x} {origen_y} cm /Img Do Q\n".encode("ascii"))
        comandos.extend(_comando_texto_pdf(modelo.titulo, 297.5, 806, 18, negrita=True))
        comandos.extend(_comando_texto_pdf(modelo.resumen, 297.5, 784, 9, negrita=False))
        radio_exterior = lado * 0.465 * escala
        radio_limite = radio_exterior * 0.76
        radio_hueco = radio_exterior * 0.23
        for anillo, radio in (
            (modelo.exterior, (radio_limite + radio_exterior) / 2),
            (modelo.interior, (radio_hueco + radio_limite) / 2),
        ):
            cantidad = len(anillo.secciones)
            if cantidad:
                tamano = max(3.2, min(8.2, 360 / max(45, cantidad * 0.72)))
                for seccion in anillo.secciones:
                    angulo_pantalla = seccion.medio_grados
                    giro = angulo_pantalla % 360
                    if 90 < giro < 270:
                        giro += 180
                    radianes = math.radians(angulo_pantalla)
                    x = centro_x + radio * math.cos(radianes)
                    y = centro_y - radio * math.sin(radianes)
                    comandos.extend(_comando_texto_pdf(
                        seccion.etiqueta, x, y, tamano,
                        color_texto_para_digito(seccion.digito), True, -giro,
                    ))
            elif anillo.etiqueta_solida:
                comandos.extend(_comando_texto_pdf(
                    anillo.etiqueta_solida, centro_x, centro_y + radio, 7,
                    color_texto_para_digito(anillo.digito_solido), True, 0,
                ))
        comandos.extend(_comando_texto_pdf(modelo.texto_centro_1, centro_x, centro_y + 15, 7.2, negrita=True))
        comandos.extend(_comando_texto_pdf(modelo.texto_centro_2, centro_x, centro_y, 6.8, negrita=True))
        comandos.extend(_comando_texto_pdf(modelo.texto_centro_3, centro_x, centro_y - 15, 5.2, negrita=False))
        comandos.extend(_comando_texto_pdf(
            f"Borde exterior: {modelo.exterior.nombre} - Interior: {modelo.interior.nombre}",
            297.5, 167, 8, negrita=True,
        ))
        for indice in range(1, 10):
            columna = (indice - 1) % 5
            fila = (indice - 1) // 5
            x, y = 46 + columna * 108, 125 - fila * 27
            color = DIGITO_COLORES[indice]["hex"]
            comandos.extend(f"{_color_pdf(color)} {x:.2f} {y:.2f} 11 11 re f\n".encode("ascii"))
            comandos.extend(_comando_texto_pdf(
                f"{indice} {DIGITO_COLORES[indice]['nombre']}", x + 16, y + 2, 6.4,
                COLOR_CONTORNO, False,
            ))
        comprimido = zlib.compress(pixeles, 7)
        objetos.extend([
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> /XObject << /Img {imagen_id} 0 R >> >> /Contents {contenido_id} 0 R >>".encode("ascii"),
            f"<< /Type /XObject /Subtype /Image /Width {ancho} /Height {alto} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode /Length {len(comprimido)} >>\nstream\n".encode("ascii") + comprimido + b"\nendstream",
            f"<< /Length {len(comandos)} >>\nstream\n".encode("ascii") + bytes(comandos) + b"endstream",
        ])
    hijos = " ".join(f"{pagina} 0 R" for pagina in paginas)
    objetos[1] = f"<< /Type /Pages /Count {len(paginas)} /Kids [{hijos}] >>".encode("ascii")
    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    posiciones = [0]
    for numero, objeto in enumerate(objetos, 1):
        posiciones.append(len(pdf))
        pdf.extend(f"{numero} 0 obj\n".encode("ascii"))
        pdf.extend(objeto)
        pdf.extend(b"\nendobj\n")
    inicio_xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for posicion in posiciones[1:]:
        pdf.extend(f"{posicion:010d} 00000 n \n".encode("ascii"))
    pdf.extend(f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{inicio_xref}\n%%EOF\n".encode("ascii"))
    return bytes(pdf)
