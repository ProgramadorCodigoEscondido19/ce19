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

    def __init__(self):
        self.valores_alfabeto = {
            letra: numero
            for numero, letra in enumerate(self.ALFABETO_29, start=1)
        }

    def _valores(self, texto):
        normalizado = str(texto or "").upper().replace("Ñ", "{ENIE}")
        normalizado = unicodedata.normalize("NFD", normalizado)
        normalizado = "".join(
            caracter
            for caracter in normalizado
            if unicodedata.category(caracter) != "Mn"
        ).replace("{ENIE}", "Ñ")

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
        return "_".join(str(valor) for valor in self._valores(texto))

    def _codigo_libro(self, nombre):
        return self._codigo(nombre)

    def _codigo_capitulo(self, numero):
        return f"{self._codigo(self.PREFIJO_CAPITULO)}:{int(numero)}"

    def _codigo_versiculo(self, numero, texto, incluir_suma, incluir_texto):
        valores = self._valores(texto)
        codigo = "_".join(str(valor) for valor in valores)
        linea = f"{self._codigo(self.PREFIJO_VERSICULO)}_{int(numero)}: {codigo}"

        if incluir_suma:
            linea += f" | Suma: {sum(valores)}"

        if incluir_texto:
            linea += f" ({str(texto or '').strip()})"

        return linea

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
                lineas.append({"texto": self._codigo_libro(libro), "negrita": True})
                libro_actual = libro
                capitulo_actual = None

            if capitulo != capitulo_actual:
                lineas.append({"texto": self._codigo_capitulo(capitulo), "negrita": False})
                capitulo_actual = capitulo

            lineas.append(
                {
                    "texto": self._codigo_versiculo(
                        numero,
                        texto,
                        incluir_suma=incluir_suma,
                        incluir_texto=incluir_texto,
                    ),
                    "negrita": False,
                }
            )

        return lineas

    @staticmethod
    def _texto_plano(lineas):
        resultado = []

        for linea in lineas:
            texto = str(linea.get("texto", ""))
            resultado.append(f"**{texto}**" if linea.get("negrita") and texto else texto)

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

    def _crear_pdf(self, lineas, destino):
        """Genera un PDF de texto puro, apto incluso para libros completos."""
        paginas = []
        comandos = []
        y = 800

        def cerrar_pagina():
            nonlocal comandos, y
            if comandos:
                paginas.append("\n".join(comandos).encode("ascii"))
            comandos = []
            y = 800

        for item in lineas:
            texto = str(item.get("texto", ""))
            if not texto:
                y -= 8
                continue

            negrita = bool(item.get("negrita"))
            fuente = "F2" if negrita else "F1"
            tamanio = 13 if negrita else 9
            alto_linea = 19 if negrita else 14
            ancho = 64 if negrita else 92

            for fragmento in self._envolver_pdf(texto, ancho=ancho):
                if y < 46:
                    cerrar_pagina()
                comandos.extend(
                    [
                        "BT",
                        f"/{fuente} {tamanio} Tf",
                        f"1 0 0 1 42 {y} Tm",
                        f"<{self._pdf_hex(fragmento)}> Tj",
                        "ET",
                    ]
                )
                y -= alto_linea

            y -= 5 if negrita else 2

        cerrar_pagina()
        if not paginas:
            paginas = [b""]

        objetos = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        ]
        referencias_paginas = []

        for contenido in paginas:
            referencia_pagina = len(objetos) + 1
            referencia_contenido = referencia_pagina + 1
            referencias_paginas.append(referencia_pagina)
            objetos.append(
                (
                    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                    f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
                    f"/Contents {referencia_contenido} 0 R >>"
                ).encode("ascii")
            )
            comprimido = zlib.compress(contenido)
            objetos.append(
                (
                    f"<< /Length {len(comprimido)} /Filter /FlateDecode >>\nstream\n"
                ).encode("ascii")
                + comprimido
                + b"\nendstream"
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
