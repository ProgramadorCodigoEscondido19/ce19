"""Exporta registros de Guardados a Word y PDF sin dependencias externas."""

import zipfile
from datetime import datetime
from html import escape

from core.rutas import ruta_exportacion


def registros_a_texto(registros):
    lineas = ["CODIGO ESCONDIDO 19 - GUARDADOS", ""]
    for indice, registro in enumerate(registros, start=1):
        titulo = registro.get("nombre") or registro.get("palabra") or registro.get("referencia") or "Sin titulo"
        lineas.append(f"{indice}. {titulo}")
        lineas.append(f"Tipo: {registro.get('tipo', 'registro')}")
        if registro.get("carpeta"):
            lineas.append(f"Carpeta: {registro['carpeta']}")
        if registro.get("referencia"):
            lineas.append(f"Referencia: {registro['referencia']}")
        contenido = registro.get("contenido", "")
        if isinstance(contenido, dict):
            contenido = contenido.get("texto") or contenido.get("texto_original") or str(contenido)
        contenido = str(contenido or registro.get("suma", ""))
        if contenido:
            lineas.extend(["Contenido:", contenido])
        if registro.get("resultado") not in (None, ""):
            lineas.append(f"Resultado: {registro['resultado']}")
        lineas.extend(["-" * 56, ""])
    return "\n".join(lineas)


def exportar_guardados_docx(registros, archivo=None):
    if archivo is None:
        archivo = ruta_exportacion(f"guardados_{datetime.now():%Y%m%d_%H%M%S}.docx")
    texto = registros_a_texto(registros)
    parrafos = []
    for linea in texto.splitlines() or [""]:
        contenido = escape(linea)
        parrafos.append(
            '<w:p><w:r><w:t xml:space="preserve">'
            + contenido
            + "</w:t></w:r></w:p>"
        )
    documento = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>" + "".join(parrafos) + "<w:sectPr/></w:body></w:document>"
    )
    with zipfile.ZipFile(archivo, "w", compression=zipfile.ZIP_DEFLATED) as paquete:
        paquete.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            "</Types>",
        )
        paquete.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            "</Relationships>",
        )
        paquete.writestr("word/document.xml", documento)
    return archivo


def _escapar_pdf(texto):
    return texto.encode("cp1252", errors="replace").replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def exportar_guardados_pdf(registros, archivo=None):
    if archivo is None:
        archivo = ruta_exportacion(f"guardados_{datetime.now():%Y%m%d_%H%M%S}.pdf")
    lineas = []
    for linea in registros_a_texto(registros).splitlines():
        texto = linea or " "
        while len(texto) > 105:
            lineas.append(texto[:105])
            texto = texto[105:]
        lineas.append(texto)
    paginas = [lineas[indice:indice + 46] for indice in range(0, len(lineas), 46)] or [[" "]]
    objetos = []
    objetos.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objetos.append(None)
    objetos.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    pagina_ids = []
    for pagina in paginas:
        contenido = [b"BT", b"/F1 11 Tf", b"50 780 Td", b"14 TL"]
        for linea in pagina:
            contenido.append(b"(" + _escapar_pdf(linea) + b") Tj")
            contenido.append(b"T*")
        contenido.append(b"ET")
        stream = b"\n".join(contenido)
        contenido_id = len(objetos) + 2
        pagina_ids.append(len(objetos) + 1)
        objetos.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents {contenido_id} 0 R >>".encode("ascii")
        )
        objetos.append(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream")
    objetos[1] = ("<< /Type /Pages /Kids [" + " ".join(f"{identificador} 0 R" for identificador in pagina_ids) + f"] /Count {len(pagina_ids)} >>").encode("ascii")
    salida = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for indice, objeto in enumerate(objetos, start=1):
        offsets.append(len(salida))
        salida.extend(f"{indice} 0 obj\n".encode("ascii"))
        salida.extend(objeto)
        salida.extend(b"\nendobj\n")
    inicio_xref = len(salida)
    salida.extend(f"xref\n0 {len(objetos) + 1}\n".encode("ascii"))
    salida.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        salida.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    salida.extend(f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{inicio_xref}\n%%EOF".encode("ascii"))
    with open(archivo, "wb") as destino:
        destino.write(salida)
    return archivo
