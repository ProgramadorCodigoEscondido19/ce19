"""Conversiones deterministas a calendarios historicos y lunisolares."""

from logica.calendario_360 import _dias_desde_civil


MAYA_CORRELACION_GMT = 584283
ISLAMICO_EPOCA_CIVIL = -492148  # 1 Muharram 1 AH, 16/07/622 juliano
EGIPCIO_EPOCA_NABONASAR = -991950  # 1 Thoth, 26/02/747 a. C. juliano
HEBREO_EPOCA = -2092590  # 1 Tishri 1, 07/10/3761 a. C. juliano

MESES_HIJRI = (
    "Muharram", "Safar", "Rabi I", "Rabi II", "Jumada I", "Jumada II",
    "Rajab", "Sha'ban", "Ramadan", "Shawwal", "Dhu al-Qi'dah", "Dhu al-Hijjah",
)
MESES_HEBREOS = (
    "Tishri", "Cheshvan", "Kislev", "Tevet", "Shevat", "Adar",
    "Nisan", "Iyar", "Sivan", "Tammuz", "Av", "Elul",
)
MESES_HEBREOS_BISIESTO = (
    "Tishri", "Cheshvan", "Kislev", "Tevet", "Shevat", "Adar I", "Adar II",
    "Nisan", "Iyar", "Sivan", "Tammuz", "Av", "Elul",
)
MESES_EGIPCIOS = (
    "Thoth", "Phaophi", "Hathyr", "Choiak", "Tybi", "Mechir",
    "Phamenoth", "Pharmuthi", "Pachons", "Payni", "Epiphi", "Mesore",
)
MESES_SUMERIOS = (
    "Bara-zag-gar", "Gu4-si-su", "Šeg12-a", "Šu-numun-a", "Ne-ne-gar",
    "Kin-inin-na", "Du6-kug", "Apin-du8-a", "Gan-gan-na", "Ab-e3",
    "Ud-duru5", "Še-gur10-kud",
)
MESES_BABILONIOS = (
    "Nisannu", "Ayyaru", "Simanu", "Du'uzu", "Abu", "Ululu",
    "Tashritu", "Arahsamna", "Kislimu", "Tebetu", "Shabatu", "Addaru",
)
MESES_ATICOS = (
    "Hekatombaion", "Metageitnion", "Boedromion", "Pyanepsion", "Maimakterion",
    "Poseideon", "Gamelion", "Anthesterion", "Elaphebolion", "Mounichion",
    "Thargelion", "Skirophorion",
)
DIAS_TZOLKIN = (
    "Imix", "Ik'", "Ak'b'al", "K'an", "Chikchan", "Kimi", "Manik'", "Lamat",
    "Muluk", "Ok", "Chuwen", "Eb'", "B'en", "Ix", "Men", "Kib'", "Kab'an",
    "Etz'nab'", "Kawak", "Ajaw",
)
MESES_HAAB = (
    "Pop", "Wo", "Sip", "Sotz'", "Sek", "Xul", "Yaxk'in", "Mol", "Ch'en",
    "Yax", "Sak'", "Keh", "Mak", "K'ank'in", "Muwan", "Pax", "K'ayab",
    "Kumk'u", "Wayeb'",
)


def _dias_absolutos(fecha):
    anio = fecha.anio_astronomico
    return _dias_desde_civil(anio, fecha.mes, fecha.dia)


def _convertir_maya(dias):
    cuenta = dias + 2440588 - MAYA_CORRELACION_GMT
    if cuenta < 0:
        raise ValueError("La fecha queda antes del inicio de la Cuenta Larga maya GMT.")
    baktun, resto = divmod(cuenta, 144000)
    katun, resto = divmod(resto, 7200)
    tun, resto = divmod(resto, 360)
    uinal, kin = divmod(resto, 20)
    tzolkin_numero = (cuenta + 3) % 13 + 1
    tzolkin_dia = DIAS_TZOLKIN[(cuenta + 19) % 20]
    haab_indice = (cuenta + 347) % 365
    haab_mes, haab_dia = divmod(haab_indice, 20)
    if haab_mes == 18:
        haab_dia = haab_indice - 360
    return (
        f"Cuenta Larga: {baktun}.{katun}.{tun}.{uinal}.{kin}\n"
        f"Tzolk'in: {tzolkin_numero} {tzolkin_dia}\n"
        f"Haab': {haab_dia} {MESES_HAAB[haab_mes]}"
    )


def _convertir_egipcio(dias):
    dias_desde_epoca = dias - EGIPCIO_EPOCA_NABONASAR
    anio, dia_anio = divmod(dias_desde_epoca, 365)
    anio += 1
    if dia_anio < 360:
        mes, dia = divmod(dia_anio, 30)
        estacion = ("Akhet", "Peret", "Shemu")[mes // 4]
        return f"Año {anio} de la era Nabonassar\n{estacion}, mes {mes % 4 + 1}, día {dia + 1} ({MESES_EGIPCIOS[mes]})"
    return f"Año {anio} de la era Nabonassar\nDía epagómeno {dia_anio - 359} de los cinco días añadidos al año"


def _islamico_inicio_anio(anio):
    return ISLAMICO_EPOCA_CIVIL + 354 * (anio - 1) + (3 + 11 * anio) // 30


def _islamico_bisiesto(anio):
    return (11 * anio + 14) % 30 < 11


def _convertir_lunar(dias):
    if dias < ISLAMICO_EPOCA_CIVIL:
        raise ValueError("El calendario Hijri tabular comienza el 16/07/622 del calendario juliano.")
    anio = max(1, (30 * (dias - ISLAMICO_EPOCA_CIVIL) + 10646) // 10631)
    while dias < _islamico_inicio_anio(anio):
        anio -= 1
    while dias >= _islamico_inicio_anio(anio + 1):
        anio += 1
    dia_anio = dias - _islamico_inicio_anio(anio)
    mes = 1
    while mes < 12:
        largo = 30 if mes % 2 else 29
        if mes == 11 and _islamico_bisiesto(anio):
            largo = 30
        if dia_anio < largo:
            break
        dia_anio -= largo
        mes += 1
    return f"{dia_anio + 1} de {MESES_HIJRI[mes - 1]} del año {anio} AH"


def _hebreo_bisiesto(anio):
    return (7 * anio + 1) % 19 < 7


def _hebreo_dias_transcurridos(anio):
    meses = 235 * ((anio - 1) // 19) + 12 * ((anio - 1) % 19) + (7 * ((anio - 1) % 19) + 1) // 19
    partes = 204 + 793 * (meses % 1080)
    horas = 5 + 12 * meses + 793 * (meses // 1080) + partes // 1080
    dia = 1 + 29 * meses + horas // 24
    partes_dia = 1080 * (horas % 24) + partes % 1080
    if (
        partes_dia >= 19440
        or (dia % 7 == 2 and partes_dia >= 9924 and not _hebreo_bisiesto(anio))
        or (dia % 7 == 1 and partes_dia >= 16789 and _hebreo_bisiesto(anio - 1))
    ):
        dia += 1
    if dia % 7 in (0, 3, 5):
        dia += 1
    return dia


def _hebreo_inicio_anio(anio):
    return HEBREO_EPOCA + _hebreo_dias_transcurridos(anio) - 1


def _convertir_israelita(dias):
    if dias < _hebreo_inicio_anio(1):
        raise ValueError("La fecha queda antes del inicio de la era del calendario hebreo calculado.")
    anio = max(1, (dias + 2092591) // 365 + 1)
    while dias < _hebreo_inicio_anio(anio):
        anio -= 1
    while dias >= _hebreo_inicio_anio(anio + 1):
        anio += 1
    largo_anio = _hebreo_inicio_anio(anio + 1) - _hebreo_inicio_anio(anio)
    bisiesto = _hebreo_bisiesto(anio)
    meses = list(MESES_HEBREOS_BISIESTO if bisiesto else MESES_HEBREOS)
    largos = [30, 30 if largo_anio % 10 == 5 else 29, 29 if largo_anio % 10 == 3 else 30, 29, 30]
    largos += [30, 29] if bisiesto else [29]
    largos += [30, 29, 30, 29, 30, 29]
    dia_anio = dias - _hebreo_inicio_anio(anio)
    for mes, largo in zip(meses, largos):
        if dia_anio < largo:
            return f"{dia_anio + 1} de {mes} del año {anio} AM"
        dia_anio -= largo
    raise ValueError("No se pudo resolver la fecha del calendario hebreo.")


def _fecha_juliana(dias):
    """Fecha juliana proléptica correspondiente al día gregoriano absoluto."""
    j = dias + 2440588
    c = j + 32082
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153
    dia = e - (153 * m + 2) // 5 + 1
    mes = m + 3 - 12 * (m // 10)
    anio = d - 4800 + m // 10
    return anio, mes, dia


def _mostrar_anio(anio):
    return f"{1 - anio} a. C." if anio <= 0 else f"{anio} d. C."


def _convertir_juliano(dias):
    anio, mes, dia = _fecha_juliana(dias)
    return f"{dia:02d}-{mes:02d}-{_mostrar_anio(anio)} (año juliano proléptico {anio})"


def _convertir_romano(dias):
    anio, mes, dia = _fecha_juliana(dias)
    meses = ("Ianuarius", "Februarius", "Martius", "Aprilis", "Maius", "Iunius",
             "Quintilis", "Sextilis", "September", "October", "November", "December")
    idus = 15 if mes in (3, 5, 7, 10) else 13
    if dia == 1:
        texto = f"Kalendas de {meses[mes - 1]}"
    elif dia == idus:
        texto = f"Idus de {meses[mes - 1]}"
    elif dia < idus:
        distancia = idus - dia + 1
        texto = f"{distancia} {('día' if distancia == 1 else 'días')} antes de las Idus de {meses[mes - 1]}"
    else:
        siguiente = mes % 12 + 1
        distancia = (31 if mes in (1, 3, 5, 7, 8, 10, 12) else 30) - dia + 2
        texto = f"{distancia} días antes de las Kalendas de {meses[siguiente - 1]}"
    return f"{texto}, año {_mostrar_anio(anio)} (notación romana sobre fecha juliana proléptica)"


def _convertir_lunisolar_reconstruido(dias, meses, nombre, atico=False):
    # Modelo determinista metónico: 12 meses alternos de 30/29 días y mes
    # intercalar en los años 3, 6, 8, 11, 14, 17 y 19 del ciclo.
    ciclo = (3, 6, 8, 11, 14, 17, 19)
    longitudes = []
    for anio in range(1, 20):
        es_bisiesto = anio in ciclo
        cantidad = 13 if es_bisiesto else 12
        longitudes.append(sum(30 if mes % 2 == 0 else 29 for mes in range(cantidad)))
    largo_ciclo = sum(longitudes)
    epoch = _dias_desde_civil(1, 1, 1)
    ciclo_num, dia_ciclo = divmod(dias - epoch, largo_ciclo)
    anio_ciclo = 1
    for largo in longitudes:
        if dia_ciclo < largo:
            break
        dia_ciclo -= largo
        anio_ciclo += 1
    anio = ciclo_num * 19 + anio_ciclo
    cantidad = 13 if anio_ciclo in ciclo else 12
    if dia_ciclo >= cantidad * 29 + cantidad // 2:
        mes = cantidad - 1
        dia = dia_ciclo - sum(30 if i % 2 == 0 else 29 for i in range(mes)) + 1
    else:
        mes = 0
        while mes < cantidad - 1:
            largo = 30 if mes % 2 == 0 else 29
            if dia_ciclo < largo:
                break
            dia_ciclo -= largo
            mes += 1
        dia = dia_ciclo + 1
    if mes >= len(meses):
        mes_nombre = "Addaru II" if nombre == "babilónico" else ("Second Poseideon" if atico else "Iti-diri")
    else:
        mes_nombre = meses[mes]
    sufijo = "; intercalación metónica proléptica" if nombre != "sumerio" else "; reconstrucción Nippur metónica proléptica"
    return f"Día {dia} de {mes_nombre}, año proléptico {anio}{sufijo}"


def _convertir_sumerio(dias):
    return _convertir_lunisolar_reconstruido(dias, MESES_SUMERIOS, "sumerio")


def _convertir_babilonico(dias):
    return _convertir_lunisolar_reconstruido(dias, MESES_BABILONIOS, "babilónico")


def _convertir_helenico(dias):
    return _convertir_lunisolar_reconstruido(dias, MESES_ATICOS, "helénico", atico=True)


def convertir_fecha(fecha, calendario):
    """Convierte una FechaExtendida al calendario destino indicado."""
    dias = _dias_absolutos(fecha)
    conversiones = {
        "maya": _convertir_maya,
        "egipcio": _convertir_egipcio,
        "lunar": _convertir_lunar,
        "israelita": _convertir_israelita,
        "sumerio": _convertir_sumerio,
        "babilonico": _convertir_babilonico,
        "romano": _convertir_romano,
        "juliano": _convertir_juliano,
        "helenico": _convertir_helenico,
    }
    try:
        return conversiones[calendario](dias)
    except KeyError as error:
        raise ValueError("Seleccione un calendario de destino válido.") from error

