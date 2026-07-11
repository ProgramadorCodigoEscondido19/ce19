import os
import zipfile
from datetime import datetime
from html import escape

from core.rutas import ruta_exportacion


def _columna_excel(indice):
    letras = ""
    indice += 1

    while indice:
        indice, resto = divmod(indice - 1, 26)
        letras = chr(65 + resto) + letras

    return letras


def _celda(fila, columna, valor):
    referencia = f"{_columna_excel(columna)}{fila}"
    texto = escape("" if valor is None else str(valor))
    return (
        f'<c r="{referencia}" t="inlineStr">'
        f"<is><t>{texto}</t></is>"
        f"</c>"
    )


def _hoja_xml(filas):
    filas_xml = []

    for fila_indice, fila in enumerate(filas, start=1):
        celdas = "".join(
            _celda(fila_indice, columna, valor)
            for columna, valor in enumerate(fila)
        )
        filas_xml.append(f'<row r="{fila_indice}">{celdas}</row>')

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData>"
        + "".join(filas_xml)
        + "</sheetData></worksheet>"
    )


def exportar_guardados_xlsx(registros, archivo=None):
    if archivo is None:
        marca = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo = ruta_exportacion(f"guardados_{marca}.xlsx")

    filas = [[
        "ID",
        "Tipo",
        "Nombre",
        "Carpeta",
        "Referencia",
        "Resultado",
        "Contenido",
    ]]

    for registro in registros:
        contenido = registro.get("contenido")

        if isinstance(contenido, dict):
            contenido = ", ".join(
                f"{clave}: {valor}"
                for clave, valor in contenido.items()
                if clave not in {"imagen_base64"}
            )

        filas.append([
            registro.get("id", ""),
            registro.get("tipo", ""),
            registro.get("nombre") or registro.get("palabra", ""),
            registro.get("carpeta", ""),
            registro.get("referencia", ""),
            registro.get("resultado", ""),
            contenido or registro.get("suma", ""),
        ])

    os.makedirs(os.path.dirname(archivo), exist_ok=True)
    hoja = _hoja_xml(filas)

    with zipfile.ZipFile(archivo, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            "</Types>",
        )
        z.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>",
        )
        z.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            "<sheets><sheet name=\"Guardados\" sheetId=\"1\" r:id=\"rId1\"/></sheets>"
            "</workbook>",
        )
        z.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            "</Relationships>",
        )
        z.writestr("xl/worksheets/sheet1.xml", hoja)

    return archivo
