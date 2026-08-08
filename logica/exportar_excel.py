"""Exportacion de Guardados a un libro Excel organizado por carpetas."""

import math
import os
import re
import zipfile
from collections import OrderedDict
from datetime import datetime
from html import escape

from core.rutas import ruta_exportacion


ENCABEZADOS = [
    "ID",
    "Tipo",
    "Nombre",
    "Carpeta",
    "Referencia",
    "Resultado",
    "Contenido",
]
ANCHO_MINIMO = [10, 14, 20, 16, 18, 20, 28]
ANCHO_MAXIMO = [16, 22, 34, 26, 28, 42, 58]


def _columna_excel(indice):
    letras = ""
    indice += 1
    while indice:
        indice, resto = divmod(indice - 1, 26)
        letras = chr(65 + resto) + letras
    return letras


def _celda(fila, columna, valor, estilo=2):
    referencia = f"{_columna_excel(columna)}{fila}"
    texto = escape("" if valor is None else str(valor))
    return (
        f'<c r="{referencia}" s="{estilo}" t="inlineStr">'
        f'<is><t xml:space="preserve">{texto}</t></is>'
        "</c>"
    )


def _ancho_columna(filas, columna):
    mayor = 0
    for fila in filas:
        valor = str(fila[columna] if columna < len(fila) else "")
        mayor = max(mayor, *(len(linea) for linea in valor.splitlines() or [""]))
    return max(ANCHO_MINIMO[columna], min(ANCHO_MAXIMO[columna], mayor + 2))


def _altura_fila(fila, anchos):
    lineas = 1
    for indice, valor in enumerate(fila):
        ancho = max(1, int(anchos[indice]))
        lineas = max(
            lineas,
            sum(max(1, math.ceil(len(linea) / ancho)) for linea in str(valor).splitlines() or [""]),
        )
    return min(120, max(22, 15 * lineas + 7))


def _hoja_xml(filas):
    anchos = [_ancho_columna(filas, indice) for indice in range(len(ENCABEZADOS))]
    columnas = "".join(
        f'<col min="{indice + 1}" max="{indice + 1}" width="{ancho}" customWidth="1"/>'
        for indice, ancho in enumerate(anchos)
    )
    filas_xml = []
    for fila_indice, fila in enumerate(filas, start=1):
        estilo = 1 if fila_indice == 1 else 2
        altura = 24 if fila_indice == 1 else _altura_fila(fila, anchos)
        celdas = "".join(
            _celda(fila_indice, columna, valor, estilo)
            for columna, valor in enumerate(fila)
        )
        filas_xml.append(
            f'<row r="{fila_indice}" ht="{altura}" customHeight="1">{celdas}</row>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<cols>{columnas}</cols>'
        '<sheetViews><sheetView workbookViewId="0">'
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
        '</sheetView></sheetViews>'
        "<sheetData>" + "".join(filas_xml) + "</sheetData></worksheet>"
    )


def _nombre_hoja(nombre, existentes):
    limpio = re.sub(r"[\\/*?:\[\]]", " ", str(nombre or "Sin carpeta")).strip() or "Sin carpeta"
    base = limpio[:31]
    candidato = base
    numero = 2
    while candidato.lower() in existentes:
        sufijo = f" ({numero})"
        candidato = f"{base[:31 - len(sufijo)]}{sufijo}"
        numero += 1
    existentes.add(candidato.lower())
    return candidato


def _texto_comparacion(comparacion):
    bloques = []
    for fila in comparacion or []:
        palabras = []
        for detalle in fila.get("detalle_palabras", []):
            valores = " + ".join(str(valor) for valor in detalle.get("valores", []))
            palabras.append(
                f"{detalle.get('palabra', '')} ({valores} = {detalle.get('subtotal', 0)})"
            )
        cuerpo = "  ".join(palabras) or "Sin caracteres compatibles"
        bloques.append(
            f"{fila.get('alfabeto', 'Diccionario')}\n{cuerpo}\nResultado: {fila.get('resultado', '')}"
        )
    return "\n\n".join(bloques)


def _contenido_registro(registro):
    comparacion = registro.get("comparacion")
    if isinstance(comparacion, list) and comparacion:
        return _texto_comparacion(comparacion)

    contenido = registro.get("contenido")
    if isinstance(contenido, dict):
        return "\n".join(
            f"{clave}: {valor}"
            for clave, valor in contenido.items()
            if clave not in {"imagen_base64"}
        )
    return contenido or registro.get("suma", "")


def _fila_registro(registro):
    return [
        registro.get("id", ""),
        registro.get("tipo", ""),
        registro.get("nombre") or registro.get("palabra", ""),
        registro.get("carpeta", ""),
        registro.get("referencia", ""),
        registro.get("resultado", ""),
        _contenido_registro(registro),
    ]


def _hojas_por_carpeta(registros, carpetas=None):
    grupos = OrderedDict()
    for carpeta in carpetas or []:
        grupos[str(carpeta or "Sin carpeta")] = []
    for registro in registros:
        nombre = str(registro.get("carpeta") or "Sin carpeta")
        grupos.setdefault(nombre, []).append(registro)
    return grupos or OrderedDict({"Guardados": []})


def _estilos_xml():
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="2"><font><sz val="11"/><name val="Aptos"/></font>'
        '<font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Aptos"/></font></fonts>'
        '<fills count="3"><fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FF6E2A8A"/><bgColor indexed="64"/></patternFill></fill></fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="3">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>'
        '</cellXfs></styleSheet>'
    )


def exportar_guardados_xlsx(registros, archivo=None, carpetas=None):
    """Exporta registros en una hoja por carpeta, con celdas legibles y ajustadas."""
    if archivo is None:
        marca = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo = ruta_exportacion(f"guardados_{marca}.xlsx")

    hojas = _hojas_por_carpeta(registros, carpetas)
    nombres = []
    usados = set()
    for carpeta in hojas:
        nombres.append(_nombre_hoja(carpeta, usados))

    os.makedirs(os.path.dirname(archivo), exist_ok=True)
    with zipfile.ZipFile(archivo, "w", compression=zipfile.ZIP_DEFLATED) as paquete:
        overrides = "".join(
            f'<Override PartName="/xl/worksheets/sheet{indice}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            for indice in range(1, len(hojas) + 1)
        )
        paquete.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            + overrides + "</Types>",
        )
        paquete.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>",
        )
        libros = "".join(
            f'<sheet name="{escape(nombre)}" sheetId="{indice}" r:id="rId{indice}"/>'
            for indice, nombre in enumerate(nombres, start=1)
        )
        paquete.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f"<sheets>{libros}</sheets></workbook>",
        )
        relaciones = "".join(
            f'<Relationship Id="rId{indice}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{indice}.xml"/>'
            for indice in range(1, len(hojas) + 1)
        )
        relaciones += (
            f'<Relationship Id="rId{len(hojas) + 1}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
            'Target="styles.xml"/>'
        )
        paquete.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + relaciones + "</Relationships>",
        )
        paquete.writestr("xl/styles.xml", _estilos_xml())
        for indice, registros_carpeta in enumerate(hojas.values(), start=1):
            filas = [ENCABEZADOS] + [_fila_registro(registro) for registro in registros_carpeta]
            paquete.writestr(f"xl/worksheets/sheet{indice}.xml", _hoja_xml(filas))
    return archivo
