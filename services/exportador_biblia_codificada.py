"""Exportacion local de fragmentos biblicos codificados en alfabeto de 29 letras."""

from datetime import datetime
from pathlib import Path
import re
import textwrap
import unicodedata
import zlib

from core.rutas import ruta_exportacion


class ExportadorBibliaCodificada:
    """Convierte versiculos en valores y los entrega como TXT o PDF local."""

    ALFABETO_29 = (
        "A", "B", "C", "CH", "D", "E", "F", "G", "H", "I", "J", "K", "L",
        "LL", "M", "N", "Ñ", "O", "P", "Q", "R", "S", "T", "U", "V", "W",
        "X", "Y", "Z",
    )
    PREFIJO_VERSICULO = "V"
    PREFIJO_CAPITULO = "CAPITULO"
    RESALTADOS = {
        "marron": {"hex": "#795548", "texto": "#FFFFFF", "marca": "🟫"},
        "naranja": {"hex": "#FB8C00", "texto": "#17131D", "marca": "🟧"},
        "violeta": {"hex": "#8E24AA", "texto": "#FFFFFF", "marca": "🟪"},
    }

    def __init__(self):
        self.valores_alfabeto = {
            letra: numero
            for numero, letra in enumerate(self.ALFABETO_29, start=1)
        }

    @staticmethod
    def _normalizar(texto):
        normalizado = str(texto or "").upper().replace("Ñ", "{ENIE}")
        normalizado = unicodedata.normalize("NFD", normalizado)
        return "".join(
            caracter
            for caracter in normalizado
            if unicodedata.category(caracter) != "Mn"
        ).replace("{ENIE}", "Ñ")

    def _valores(self, texto):
        normalizado = self._normalizar(texto)

        valores = []
        indice = 0

        while indice < len(normalizado):
            compuesto = normalizado[indice:indice + 2]

            if compuesto in ("CH", "LL"):
                valores.append(self.valores_alfabeto[compuesto])
                indice += 2
                continue

            valor = self.valores_alfabeto.get(normalizado[indice])
            if valor is not None:
                valores.append(valor)
            indice += 1

        return valores

    def _codigo(self, texto):
        palabras = re.findall(r"[A-ZÑ]+", self._normalizar(texto))
        codigos = [
            "_".join(str(valor) for valor in self._valores(palabra))
            for palabra in palabras
        ]
        return "__".join(codigo for codigo in codigos if codigo)

    def _codigo_libro(self, nombre):
        return self._codigo(nombre)

    def _codigo_capitulo(self, numero):
        return f"{self._codigo(self.PREFIJO_CAPITULO)}:{int(numero)}"

    def _codigo_versiculo(self, numero, texto, incluir_suma, incluir_texto):
        valores = self._valores(texto)
        codigo = self._codigo(texto)
        prefijo = f"{self._codigo(self.PREFIJO_VERSICULO)}_{int(numero)}:"
        linea = codigo

        if incluir_suma:
            linea += f" | Suma: {sum(valores)}"

        if incluir_texto:
            linea += f" ({str(texto or '').strip()})"

        return prefijo, linea

    @staticmethod
    def _ordenar_versos(versos):
        # La vista de Biblia ya entrega la seleccion en orden canonico.
        # Lo preservamos para no reordenar los libros alfabeticamente.
        return [verso for verso in versos if isinstance(verso, dict)]

    def construir_documento(self, versos, incluir_suma=False, incluir_texto=False):
        """Devuelve lineas con encabezados de libro/capitulo y versiculos codificados."""
        lineas = []
        libro_actual = None
        capitulo_actual = None

        for verso in self._ordenar_versos(versos):
            libro = str(verso.get("libro", "")).strip()
            capitulo = int(verso.get("capitulo", 0) or 0)
            numero = int(verso.get("versiculo", 0) or 0)
            texto = str(verso.get("texto", "")).strip()

            if not libro or capitulo <= 0 or numero <= 0:
                continue

            if libro != libro_actual:
                if lineas:
                    lineas.append({"texto": "", "negrita": False})
                lineas.append(
                    {
                        "texto": self._codigo_libro(libro),
                        "negrita": True,
                        "resaltado": "marron",
                        "resaltado_texto": self._codigo_libro(libro),
                        "destino": f"libro:{libro}",
                        "indice_tipo": "libro",
                    }
                )
                libro_actual = libro
                capitulo_actual = None

            if capitulo != capitulo_actual:
                lineas.append(
                    {
                        "texto": self._codigo_capitulo(capitulo),
                        "negrita": True,
                        "resaltado": "naranja",
                        "resaltado_texto": self._codigo_capitulo(capitulo),
                        "destino": f"capitulo:{libro}:{capitulo}",
                        "indice_tipo": "capitulo",
                    }
                )
                capitulo_actual = capitulo

            prefijo, codigo_versiculo = self._codigo_versiculo(
                numero,
                texto,
                incluir_suma=incluir_suma,
                incluir_texto=incluir_texto,
            )
            lineas.append(
                {
                    "texto": codigo_versiculo,
                    "prefijo": prefijo,
                    "negrita": False,
                    "resaltado": "violeta",
                    "resaltado_texto": prefijo,
                }
            )

        return lineas

    @staticmethod
    def _texto_plano(lineas):
        resultado = []

        for linea in lineas:
            texto = str(linea.get("texto", ""))
            prefijo = str(linea.get("prefijo", "")).strip()
            contenido = " ".join(parte for parte in (prefijo, texto) if parte)
            resaltado = linea.get("resaltado")
            marca = ExportadorBibliaCodificada.RESALTADOS.get(resaltado, {}).get("marca", "")
            if linea.get("negrita") and contenido:
                contenido = f"**{contenido}**"
            resultado.append(f"{marca} {contenido}".strip() if marca else contenido)

        return "\n".join(resultado).strip() + "\n"

    @staticmethod
    def _nombre_archivo(extension):
        marca = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"biblia_codificada_{marca}.{extension}"

    @staticmethod
    def _envolver_pdf(texto, ancho=92):
        """Parte lineas extensas para una pagina A4 sin cargar imagenes en memoria."""
        texto = str(texto or "")
        return textwrap.wrap(
            texto,
            width=ancho,
            break_long_words=True,
            break_on_hyphens=False,
        ) or [""]

    @staticmethod
    def _pdf_hex(texto):
        # WinAnsi soporta los acentos habituales del texto biblico en espanol.
        return str(texto).encode("cp1252", errors="replace").hex().upper()

    @staticmethod
    def _pdf_rgb(hexadecimal):
        color = str(hexadecimal or "#000000").lstrip("#")
        if len(color) != 6:
            return "0 0 0"
        try:
            return " ".join(f"{int(color[indice:indice + 2], 16) / 255:.3f}" for indice in (0, 2, 4))
        except ValueError:
            return "0 0 0"

    @staticmethod
    def _ancho_aproximado(texto, tamanio):
        return min(510, max(28, len(str(texto)) * tamanio * 0.56 + 10))

    def _crear_paginas_indice(self, entradas, destinos, cantidad_paginas_indice):
        """Crea un indice compacto y navegable por libros y capitulos."""
        paginas = []
        por_pagina = 48

        for inicio in range(0, len(entradas), por_pagina):
            comandos = []
            enlaces = []
            y = 800
            titulo = self._codigo("INDICE")
            comandos.extend(
                [
                    "BT",
                    "/F2 15 Tf",
                    f"{self._pdf_rgb(self.RESALTADOS['marron']['hex'])} rg",
                    f"1 0 0 1 42 {y} Tm",
                    f"<{self._pdf_hex(titulo)}> Tj",
                    "ET",
                ]
            )
            y -= 28

            for entrada in entradas[inicio:inicio + por_pagina]:
                destino = entrada["destino"]
                destino_pdf = destinos.get(destino)
                if not destino_pdf:
                    continue

                tipo = entrada.get("tipo")
                sangria = 42 if tipo == "libro" else 62
                fuente = "F2" if tipo == "libro" else "F1"
                tamanio = 10 if tipo == "libro" else 9
                pagina_destino = cantidad_paginas_indice + destino_pdf["pagina"] + 1
                codigo = entrada.get("codigo", "")
                texto = f"{codigo}  ................................  {pagina_destino}"
                comandos.extend(
                    [
                        "BT",
                        f"/{fuente} {tamanio} Tf",
                        "0.090 0.075 0.114 rg",
                        f"1 0 0 1 {sangria} {y} Tm",
                        f"<{self._pdf_hex(texto)}> Tj",
                        "ET",
                    ]
                )
                enlaces.append(
                    {
                        "x1": sangria - 2,
                        "y1": y - 4,
                        "x2": 550,
                        "y2": y + 11,
                        "destino": destino,
                    }
                )
                y -= 15

            paginas.append({"contenido": "\n".join(comandos).encode("ascii"), "enlaces": enlaces})

        return paginas or [{"contenido": b"", "enlaces": []}]

    def _crear_pdf(self, lineas, destino):
        """Genera un PDF con indice inicial y enlaces a cada libro."""
        paginas_cuerpo = []
        destinos = {}
        entradas_indice = []
        comandos = []
        y = 800

        def cerrar_pagina():
            nonlocal comandos, y
            if comandos:
                paginas_cuerpo.append({"contenido": "\n".join(comandos).encode("ascii"), "enlaces": []})
            comandos = []
            y = 800

        for item in lineas:
            texto = str(item.get("texto", ""))
            prefijo = str(item.get("prefijo", "")).strip()
            texto_completo = " ".join(parte for parte in (prefijo, texto) if parte)
            if not texto_completo:
                y -= 8
                continue

            # Evita que un destino del indice apunte a una pagina anterior.
            if y < 46:
                cerrar_pagina()

            destino_item = item.get("destino")
            if destino_item and destino_item not in destinos:
                destinos[destino_item] = {"pagina": len(paginas_cuerpo), "y": y}
                entradas_indice.append(
                    {
                        "destino": destino_item,
                        "codigo": texto,
                        "tipo": item.get("indice_tipo", "capitulo"),
                    }
                )

            negrita = bool(item.get("negrita"))
            resaltado = self.RESALTADOS.get(item.get("resaltado"))
            texto_resaltado = str(item.get("resaltado_texto", "")).strip()
            fuente = "F2" if negrita else "F1"
            tamanio = 13 if negrita else 9
            alto_linea = 19 if negrita else 14
            ancho = 64 if negrita else 92

            for indice_fragmento, fragmento in enumerate(self._envolver_pdf(texto_completo, ancho=ancho)):
                if y < 46:
                    cerrar_pagina()

                x_texto = 42
                texto_a_dibujar = fragmento
                comandos_resaltado = []

                # Resalta solo la altura real de cada subtitulo, sin alcanzar otros renglones.
                if resaltado and texto_resaltado and indice_fragmento == 0 and fragmento.startswith(texto_resaltado):
                    ancho_fondo = self._ancho_aproximado(texto_resaltado, tamanio)
                    base_fondo = y - (3 if negrita else 2)
                    alto_fondo = 15 if negrita else 11
                    comandos_resaltado.extend(
                        [
                            "q",
                            f"{self._pdf_rgb(resaltado['hex'])} rg",
                            f"42 {base_fondo} {ancho_fondo:.1f} {alto_fondo} re f",
                            "Q",
                            "BT",
                            f"/{fuente} {tamanio} Tf",
                            f"{self._pdf_rgb(resaltado['texto'])} rg",
                            f"1 0 0 1 42 {y} Tm",
                            f"<{self._pdf_hex(texto_resaltado)}> Tj",
                            "ET",
                        ]
                    )
                    texto_a_dibujar = fragmento[len(texto_resaltado):].lstrip()
                    x_texto += ancho_fondo + 4

                comandos.extend(
                    comandos_resaltado + [
                        "BT",
                        f"/{fuente} {tamanio} Tf",
                        "0.090 0.075 0.114 rg",
                        f"1 0 0 1 {x_texto:.1f} {y} Tm",
                        f"<{self._pdf_hex(texto_a_dibujar)}> Tj",
                        "ET",
                    ]
                )
                y -= alto_linea

            y -= 5 if negrita else 2

        cerrar_pagina()
        if not paginas_cuerpo:
            paginas_cuerpo = [{"contenido": b"", "enlaces": []}]

        cantidad_paginas_indice = max(1, (len(entradas_indice) + 47) // 48)
        paginas_indice = self._crear_paginas_indice(
            entradas_indice,
            destinos,
            cantidad_paginas_indice,
        )
        paginas = paginas_indice + paginas_cuerpo
        desplazamiento_indice = len(paginas_indice)

        objetos = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        ]
        referencias_paginas = [5 + indice * 2 for indice in range(len(paginas))]
        referencias_anotaciones = [[] for _ in paginas]
        siguiente_anotacion = 5 + len(paginas) * 2

        for indice, pagina in enumerate(paginas):
            for enlace in pagina["enlaces"]:
                destino_enlace = destinos.get(enlace["destino"])
                if not destino_enlace:
                    continue
                enlace["referencia"] = siguiente_anotacion
                enlace["pagina_destino"] = referencias_paginas[
                    desplazamiento_indice + destino_enlace["pagina"]
                ]
                enlace["y_destino"] = destino_enlace["y"]
                referencias_anotaciones[indice].append(siguiente_anotacion)
                siguiente_anotacion += 1

        for indice, pagina in enumerate(paginas):
            referencia_pagina = referencias_paginas[indice]
            referencia_contenido = referencia_pagina + 1
            anotaciones = referencias_anotaciones[indice]
            bloque_anotaciones = (
                f" /Annots [{' '.join(f'{referencia} 0 R' for referencia in anotaciones)}]"
                if anotaciones
                else ""
            )
            objetos.append(
                (
                    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                    f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
                    f"/Contents {referencia_contenido} 0 R{bloque_anotaciones} >>"
                ).encode("ascii")
            )
            comprimido = zlib.compress(pagina["contenido"])
            objetos.append(
                (
                    f"<< /Length {len(comprimido)} /Filter /FlateDecode >>\nstream\n"
                ).encode("ascii")
                + comprimido
                + b"\nendstream"
            )

        for pagina in paginas:
            for enlace in pagina["enlaces"]:
                if "referencia" not in enlace:
                    continue
                objetos.append(
                    (
                        "<< /Type /Annot /Subtype /Link "
                        f"/Rect [{enlace['x1']:.1f} {enlace['y1']:.1f} {enlace['x2']:.1f} {enlace['y2']:.1f}] "
                        "/Border [0 0 0] "
                        f"/A << /S /GoTo /D [{enlace['pagina_destino']} 0 R /XYZ null {enlace['y_destino']:.1f} null] >> >>"
                    ).encode("ascii")
                )

        hijos = " ".join(f"{referencia} 0 R" for referencia in referencias_paginas)
        objetos[1] = f"<< /Type /Pages /Kids [{hijos}] /Count {len(referencias_paginas)} >>".encode("ascii")

        partes = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
        posiciones = [0]
        cursor = len(partes[0])

        for indice, objeto in enumerate(objetos, start=1):
            bloque = f"{indice} 0 obj\n".encode("ascii") + objeto + b"\nendobj\n"
            posiciones.append(cursor)
            partes.append(bloque)
            cursor += len(bloque)

        inicio_xref = cursor
        xref = [f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n"]
        xref.extend(f"{posicion:010d} 00000 n \n" for posicion in posiciones[1:])
        trailer = (
            "trailer\n"
            f"<< /Size {len(objetos) + 1} /Root 1 0 R >>\n"
            f"startxref\n{inicio_xref}\n%%EOF\n"
        )
        partes.append("".join(xref).encode("ascii") + trailer.encode("ascii"))

        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(b"".join(partes))
        return str(destino)

    def exportar(self, versos, formato="txt", incluir_suma=False, incluir_texto=False):
        lineas = self.construir_documento(
            versos,
            incluir_suma=incluir_suma,
            incluir_texto=incluir_texto,
        )

        if not lineas:
            raise ValueError("No hay versiculos validos para exportar.")

        formato = str(formato or "txt").lower()
        if formato not in {"txt", "pdf"}:
            raise ValueError("El formato de exportacion no es valido.")

        destino = Path(ruta_exportacion(self._nombre_archivo(formato)))

        if formato == "pdf":
            return self._crear_pdf(lineas, destino)

        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(self._texto_plano(lineas), encoding="utf-8")
        return str(destino)
