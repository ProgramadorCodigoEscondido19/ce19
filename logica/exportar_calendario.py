"""Exportacion del almanaque biblico de 360 dias."""

import os
import tempfile
import zipfile
from datetime import datetime
from html import escape

from core.rutas import ruta_exportacion
from logica.calendario_360 import MESES_360, fecha_gregoriana_desde_biblica, formatear_fecha_real


MARRON = "FF6A3B2A"
MARRON_CLARO = "FFF2E2D5"
DORADO = "FFE5B94D"


def _archivo_salida(archivo, extension, desde, hasta):
    """Prepara una ruta escribible antes de pedir al usuario la descarga."""
    if archivo:
        os.makedirs(os.path.dirname(os.path.abspath(archivo)), exist_ok=True)
        return archivo

    nombre = f"almanaque_{desde}_{hasta}_{datetime.now():%Y%m%d_%H%M%S}.{extension}"
    try:
        destino = ruta_exportacion(nombre)
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        # Comprueba permisos antes de generar el archivo, para poder usar
        # una ruta temporal si el directorio de exportaciones esta bloqueado.
        with open(destino, "ab"):
            pass
        return destino
    except OSError:
        return os.path.join(tempfile.gettempdir(), nombre)


def _columna_excel(indice):
    letras = ""
    indice += 1
    while indice:
        indice, resto = divmod(indice - 1, 26)
        letras = chr(65 + resto) + letras
    return letras


def _celda(fila, columna, valor, estilo=0):
    referencia = f"{_columna_excel(columna)}{fila}"
    contenido = escape(str(valor))
    return (
        f'<c r="{referencia}" s="{estilo}" t="inlineStr">'
        f'<is><t xml:space="preserve">{contenido}</t></is></c>'
    )


def _celda_formula(fila, columna, formula, estilo=0, valor=0):
    """Crea una celda con formula para que Excel recalcule al abrirla."""
    referencia = f"{_columna_excel(columna)}{fila}"
    formula = escape(str(formula).lstrip("="))
    return f'<c r="{referencia}" s="{estilo}"><f>{formula}</f><v>{valor}</v></c>'


def _celda_formula_texto(fila, columna, formula, estilo=0, valor=""):
    """Crea una formula cuyo resultado es texto, incluso antes de 1900."""
    referencia = f"{_columna_excel(columna)}{fila}"
    formula = escape(str(formula).lstrip("="))
    contenido = escape(str(valor))
    return (
        f'<c r="{referencia}" s="{estilo}" t="str">'
        f'<f>{formula}</f><v>{contenido}</v></c>'
    )


def _celda_numero(fila, columna, valor, estilo=0):
    """Crea una celda numérica editable para los campos del convertidor."""
    referencia = f"{_columna_excel(columna)}{fila}"
    return f'<c r="{referencia}" s="{estilo}"><v>{valor}</v></c>'


def _fila_xml(numero, valores, estilos=None, alto=None):
    estilos = estilos or [0] * len(valores)
    celdas = "".join(
        _celda(numero, columna, valor, estilos[columna])
        for columna, valor in enumerate(valores)
    )
    altura = f' ht="{alto}" customHeight="1"' if alto else ""
    return f'<row r="{numero}"{altura}>{celdas}</row>'


def _estilos_excel():
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<numFmts count="1"><numFmt numFmtId="164" formatCode="dd/mm/yyyy"/></numFmts>'
        '<fonts count="3"><font><sz val="10"/><name val="Aptos"/></font>'
        '<font><b/><color rgb="FFFFFFFF"/><sz val="13"/><name val="Aptos"/></font>'
        '<font><b/><color rgb="FF4A2A20"/><sz val="10"/><name val="Aptos"/></font></fonts>'
        '<fills count="6"><fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill>'
        f'<fill><patternFill patternType="solid"><fgColor rgb="{MARRON}"/><bgColor indexed="64"/></patternFill></fill>'
        f'<fill><patternFill patternType="solid"><fgColor rgb="{MARRON_CLARO}"/><bgColor indexed="64"/></patternFill></fill>'
        f'<fill><patternFill patternType="solid"><fgColor rgb="{DORADO}"/><bgColor indexed="64"/></patternFill></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FFFFF4C7"/><bgColor indexed="64"/></patternFill></fill>'
        '</fills><borders count="3">'
        '<border><left/><right/><top/><bottom/><diagonal/></border>'
        f'<border><left style="thin"><color rgb="{MARRON}"/></left><right style="thin"><color rgb="{MARRON}"/></right><top style="thin"><color rgb="{MARRON}"/></top><bottom style="thin"><color rgb="{MARRON}"/></bottom><diagonal/></border>'
        f'<border><left style="medium"><color rgb="{MARRON}"/></left><right style="medium"><color rgb="{MARRON}"/></right><top style="medium"><color rgb="{MARRON}"/></top><bottom style="medium"><color rgb="{MARRON}"/></bottom><diagonal/></border>'
        '</borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="8">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>'
        '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>'
        '<xf numFmtId="0" fontId="2" fillId="3" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>'
        '<xf numFmtId="0" fontId="2" fillId="4" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>'
        '<xf numFmtId="0" fontId="0" fillId="3" borderId="0" xfId="0" applyFill="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>'
        '<xf numFmtId="164" fontId="2" fillId="3" borderId="0" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>'
        '<xf numFmtId="0" fontId="2" fillId="3" borderId="2" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>'
        '<xf numFmtId="0" fontId="2" fillId="5" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>'
        '</cellXfs></styleSheet>'
    )


def _archivo_convertidor(archivo=None):
    if archivo:
        os.makedirs(os.path.dirname(os.path.abspath(archivo)), exist_ok=True)
        return archivo

    nombre = f"convertidor_calendario_biblico_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    try:
        destino = ruta_exportacion(nombre)
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "ab"):
            pass
        return destino
    except OSError:
        return os.path.join(tempfile.gettempdir(), nombre)


def _hoja_convertidor():
    """Genera un formulario guiado de conversiones para usar sin fórmulas."""
    meses = '"Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre","Enero","Febrero","Marzo"'
    # Excel no puede mostrar sus fechas numéricas anteriores a 1900. Esta
    # formula calcula el calendario gregoriano y devuelve una fecha legible.
    formula_biblica = (
        "LET(z,21650+(A14-6000)*360+(B14-1)*30+C14-1,"
        "q,z+719468,"
        "era,IF(q>=0,QUOTIENT(q,146097),QUOTIENT(q-146096,146097)),"
        "doe,q-era*146097,"
        "yoe,QUOTIENT(doe-QUOTIENT(doe,1460)+QUOTIENT(doe,36524)-QUOTIENT(doe,146096),365),"
        "y,yoe+era*400,"
        "doy,doe-(365*yoe+QUOTIENT(yoe,4)-QUOTIENT(yoe,100)),"
        "mp,QUOTIENT(5*doy+2,153),"
        "d,doy-QUOTIENT(153*mp+2,5)+1,"
        "m,IF(mp<10,mp+3,mp-9),"
        "yy,y+IF(m<=2,1,0),"
        "TEXT(d,\"00\")&\"/\"&TEXT(m,\"00\")&\"/\"&TEXT(IF(yy>=1,yy,1-yy),\"0000\")&IF(yy>=1,\" DC\",\" AC\"))"
    )
    filas = [
        _fila_xml(1, ["CONVERTIDOR DE CALENDARIO BÍBLICO"], [1], alto=28),
        _fila_xml(2, ["Base: 11/04/2029 = año bíblico 6000, mes 1, día 1. No se aplica corrección solar."], [2], alto=22),
        _fila_xml(4, ["PASO 1 · Escribí una fecha del calendario gregoriano"], [1], alto=24),
        _fila_xml(5, ["Día", "Mes", "Año", "Fecha calculada", "Diferencia en días"], [3] * 5),
        '<row r="6">'
        + _celda_numero(6, 0, 11, 6)
        + _celda_numero(6, 1, 4, 6)
        + _celda_numero(6, 2, 2029, 6)
        + _celda_formula(6, 3, "DATE(C6,B6,A6)", 5, 47219)
        + _celda_formula(6, 4, "D6-DATE(2029,4,11)", 7)
        + '</row>',
        _fila_xml(8, ["PASO 2 · Leé la fecha equivalente en el calendario bíblico"], [1], alto=24),
        _fila_xml(9, ["Año bíblico", "Día del año", "Mes bíblico", "Día bíblico", "Nombre del mes"], [3] * 5),
        '<row r="10">'
        + _celda_formula(10, 0, "6000+INT(E6/360)", 7)
        + _celda_formula(10, 1, "MOD(E6,360)+1", 7)
        + _celda_formula(10, 2, "INT((B10-1)/30)+1", 7)
        + _celda_formula(10, 3, "MOD(B10-1,30)+1", 7)
        + _celda_formula(10, 4, f"CHOOSE(C10,{meses})", 7)
        + '</row>',
        _fila_xml(12, ["PASO 3 · O escribí una fecha bíblica para convertirla a gregoriana"], [1], alto=24),
        _fila_xml(13, ["Año bíblico", "Mes (1 a 12)", "Día (1 a 30)", "Fecha gregoriana equivalente"], [3] * 4),
        '<row r="14">'
        + _celda_numero(14, 0, 6000, 6)
        + _celda_numero(14, 1, 1, 6)
        + _celda_numero(14, 2, 1, 6)
        + _celda_formula_texto(14, 3, formula_biblica, 7, "11/04/2029 DC")
        + '</row>',
        _fila_xml(17, ["GUÍA RÁPIDA"], [1], alto=24),
        _fila_xml(18, ["1. Solo modificá las casillas marrones.  2. Las casillas crema se calculan solas."], [2], alto=22),
        _fila_xml(19, ["Usá el Paso 1 y Paso 2 para convertir una fecha real. Usá el Paso 3 para convertir una fecha bíblica."], [2], alto=22),
    ]
    columnas = ''.join(
        f'<col min="{indice}" max="{indice}" width="{ancho}" customWidth="1"/>'
        for indice, ancho in enumerate([20, 18, 18, 32, 24], start=1)
    )
    combinaciones = ''.join(
        f'<mergeCell ref="{referencia}"/>'
        for referencia in ("A1:E1", "A2:E2", "A4:E4", "A8:E8", "A12:E12", "A17:E17", "A18:E18", "A19:E19")
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetViews><sheetView workbookViewId="0"><pane ySplit="4" topLeftCell="A5" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
        '<sheetFormatPr defaultRowHeight="20"/>'
        f'<cols>{columnas}</cols><sheetData>{"".join(filas)}</sheetData>'
        f'<mergeCells count="8">{combinaciones}</mergeCells>'
        '<pageMargins left="0.3" right="0.3" top="0.5" bottom="0.5" header="0.2" footer="0.2"/>'
        '</worksheet>'
    )


def exportar_convertidor_calendario_xlsx(archivo=None):
    """Genera una planilla autónoma de conversiones de calendario."""
    archivo = _archivo_convertidor(archivo)
    os.makedirs(os.path.dirname(archivo), exist_ok=True)
    with zipfile.ZipFile(archivo, "w", compression=zipfile.ZIP_DEFLATED) as paquete:
        paquete.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '</Types>',
        )
        paquete.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>',
        )
        paquete.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Convertidor" sheetId="1" r:id="rId1"/></sheets>'
            '<calcPr calcId="1" fullCalcOnLoad="1" forceFullCalc="1"/>'
            '</workbook>',
        )
        paquete.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            '</Relationships>',
        )
        paquete.writestr("xl/styles.xml", _estilos_excel())
        paquete.writestr("xl/worksheets/sheet1.xml", _hoja_convertidor())
    return archivo


def _hoja_anio(anio):
    referencia = formatear_fecha_real(fecha_gregoriana_desde_biblica(anio))
    filas = [
        _fila_xml(1, [f"ALMANAQUE BIBLICO - ANO {anio}"], [1], alto=26),
        _fila_xml(2, [f"Referencia gregoriana: {referencia}"], [2]),
        _fila_xml(3, ["Mes", *[str(dia) for dia in range(1, 31)]], [3] * 31),
    ]
    for indice, mes in enumerate(MESES_360, start=1):
        fila = [mes]
        estilos = [2]
        for dia in range(1, 31):
            fecha = fecha_gregoriana_desde_biblica(anio, indice, dia)
            fila.append(f"{dia}\n{fecha.dia:02d}/{fecha.mes:02d}/{fecha.anio} {fecha.era}")
            estilos.append(4)
        filas.append(_fila_xml(indice + 3, fila, estilos, alto=38))

    columnas = '<col min="1" max="1" width="17" customWidth="1"/>'
    columnas += '<col min="2" max="31" width="15" customWidth="1"/>'
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<cols>{columnas}</cols>'
        '<sheetViews><sheetView workbookViewId="0"><pane ySplit="3" xSplit="1" '
        'topLeftCell="B4" activePane="bottomRight" state="frozen"/></sheetView></sheetViews>'
        f'<sheetData>{"".join(filas)}</sheetData></worksheet>'
    )


def exportar_almanaque_xlsx(desde, hasta, archivo=None):
    if hasta < desde:
        desde, hasta = hasta, desde
    if hasta - desde > 20:
        raise ValueError("Para Excel el rango maximo es de 21 anos por exportacion.")
    archivo = _archivo_salida(archivo, "xlsx", desde, hasta)

    anios = list(range(desde, hasta + 1))
    os.makedirs(os.path.dirname(archivo), exist_ok=True)
    with zipfile.ZipFile(archivo, "w", compression=zipfile.ZIP_DEFLATED) as paquete:
        overrides = "".join(
            f'<Override PartName="/xl/worksheets/sheet{indice}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            for indice in range(1, len(anios) + 1)
        )
        paquete.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            + overrides + '</Types>',
        )
        paquete.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>',
        )
        hojas = ''.join(
            f'<sheet name="Ano {anio}" sheetId="{indice}" r:id="rId{indice}"/>'
            for indice, anio in enumerate(anios, start=1)
        )
        paquete.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<sheets>{hojas}</sheets></workbook>',
        )
        relaciones = ''.join(
            f'<Relationship Id="rId{indice}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{indice}.xml"/>'
            for indice in range(1, len(anios) + 1)
        )
        relaciones += (
            f'<Relationship Id="rId{len(anios) + 1}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        )
        paquete.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + relaciones + '</Relationships>',
        )
        paquete.writestr("xl/styles.xml", _estilos_excel())
        for indice, anio in enumerate(anios, start=1):
            paquete.writestr(f"xl/worksheets/sheet{indice}.xml", _hoja_anio(anio))
    return archivo


def _pdf_escape(texto):
    return str(texto).encode("cp1252", errors="replace").replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def _lineas_pdf(anio):
    referencia = formatear_fecha_real(fecha_gregoriana_desde_biblica(anio))
    lineas = [f"ALMANAQUE BIBLICO - ANO {anio}", f"Referencia gregoriana: {referencia}", ""]
    for indice, mes in enumerate(MESES_360, start=1):
        lineas.append(f"{mes.upper():<12} " + " ".join(f"{dia:02d}" for dia in range(1, 31)))
        comparacion = [fecha_gregoriana_desde_biblica(anio, indice, dia) for dia in range(1, 31)]
        lineas.append("Gregorianas:  " + " ".join(f"{fecha.dia:02d}" for fecha in comparacion))
    return lineas


def exportar_almanaque_pdf(desde, hasta, archivo=None):
    if hasta < desde:
        desde, hasta = hasta, desde
    if hasta - desde > 8:
        raise ValueError("Para PDF el rango maximo es de 9 anos por exportacion.")
    archivo = _archivo_salida(archivo, "pdf", desde, hasta)

    paginas = [_lineas_pdf(anio) for anio in range(desde, hasta + 1)]
    objetos = [b"<< /Type /Catalog /Pages 2 0 R >>", None,
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"]
    paginas_ids = []
    for lineas in paginas:
        contenido = [
            b"0.32 0.16 0.10 rg", b"0 0 792 612 re f",
            b"0.97 0.91 0.82 rg", b"20 20 752 572 re f",
            b"0.42 0.23 0.16 rg", b"BT", b"/F2 16 Tf", b"50 572 Td", b"20 TL",
        ]
        for indice, linea in enumerate(lineas):
            if indice == 1:
                contenido.extend([b"/F1 9 Tf", b"T*"])
            elif indice >= 3:
                contenido.extend([b"/F1 8 Tf", b"T*"])
            elif indice > 0:
                contenido.append(b"T*")
            contenido.append(b"(" + _pdf_escape(linea) + b") Tj")
        contenido.append(b"ET")
        stream = b"\n".join(contenido)
        pagina_id = len(objetos) + 1
        contenido_id = pagina_id + 1
        paginas_ids.append(pagina_id)
        objetos.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 792 612] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {contenido_id} 0 R >>".encode("ascii")
        )
        objetos.append(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream")
    objetos[1] = ("<< /Type /Pages /Kids [" + " ".join(f"{identificador} 0 R" for identificador in paginas_ids) + f"] /Count {len(paginas_ids)} >>").encode("ascii")
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
