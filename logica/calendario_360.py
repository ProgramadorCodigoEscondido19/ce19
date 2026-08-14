import json
import os
import re
from dataclasses import dataclass
from datetime import datetime

from core.rutas import ruta_datos


# Regla fija del calendario biblico: el 11/04/2029 del calendario gregoriano
# corresponde al primer dia del anio 6000. Los 360 dias del calendario se
# cuentan como dias reales transcurridos, sin aplicar correcciones solares.
BASE_REAL = datetime(2029, 4, 11, 0, 0, 0)
BASE_ANIO = 6000
ANIOS_BIBLICOS_PREVIOS = 0
SEGUNDOS_DIA = 24 * 60 * 60
DIAS_ANIO = 360
DIAS_MES = 30
SEGUNDOS_ANIO = DIAS_ANIO * SEGUNDOS_DIA
CONFIG_ARCHIVO = ruta_datos("config_tiempo.json")

MESES_360 = [
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
    "Enero",
    "Febrero",
    "Marzo",
]


@dataclass(frozen=True)
class FechaExtendida:
    anio: int
    mes: int
    dia: int
    hora: int = 0
    minuto: int = 0
    segundo: int = 0
    era: str = "DC"

    @property
    def anio_astronomico(self):
        return self.anio if self.era == "DC" else 1 - self.anio

    def isoformat(self):
        sufijo = "DC" if self.era == "DC" else "AC"
        return (
            f"{self.anio:04d}-{self.mes:02d}-{self.dia:02d}"
            f"T{self.hora:02d}:{self.minuto:02d}:{self.segundo:02d} {sufijo}"
        )


def fecha_extendida_desde_datetime(fecha):
    return FechaExtendida(
        fecha.year,
        fecha.month,
        fecha.day,
        fecha.hour,
        fecha.minute,
        fecha.second,
        "DC",
    )


def _normalizar_era(era):
    valor = (era or "DC").strip().upper().replace(".", "")

    if valor in {"AC", "A C", "BC", "B C", "ANTES DE CRISTO"}:
        return "AC"

    return "DC"


def _es_bisiesto(anio_astronomico):
    return (
        anio_astronomico % 4 == 0
        and (anio_astronomico % 100 != 0 or anio_astronomico % 400 == 0)
    )


def _dias_mes_gregoriano(anio_astronomico, mes):
    if mes == 2:
        return 29 if _es_bisiesto(anio_astronomico) else 28

    if mes in {4, 6, 9, 11}:
        return 30

    return 31


def _dias_desde_civil(anio, mes, dia):
    # Algoritmo gregoriano proleptico; admite años astronomicos negativos.
    anio -= 1 if mes <= 2 else 0
    era = anio // 400 if anio >= 0 else (anio - 399) // 400
    yoe = anio - era * 400
    mp = mes + (-3 if mes > 2 else 9)
    doy = (153 * mp + 2) // 5 + dia - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146097 + doe - 719468


def _civil_desde_dias(dias):
    """Inverso de _dias_desde_civil para fechas gregorianas prolepticas."""
    z = dias + 719468
    era = z // 146097 if z >= 0 else (z - 146096) // 146097
    doe = z - era * 146097
    yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
    anio = yoe + era * 400
    dia_anio = doe - (365 * yoe + yoe // 4 - yoe // 100)
    mes_previo = (5 * dia_anio + 2) // 153
    dia = dia_anio - (153 * mes_previo + 2) // 5 + 1
    mes = mes_previo + 3 if mes_previo < 10 else mes_previo - 9
    anio += 1 if mes <= 2 else 0
    return anio, mes, dia


def _segundos_absolutos(fecha):
    if isinstance(fecha, datetime):
        fecha = fecha_extendida_desde_datetime(fecha)

    dias = _dias_desde_civil(
        fecha.anio_astronomico,
        fecha.mes,
        fecha.dia,
    )
    segundos_dia = fecha.hora * 3600 + fecha.minuto * 60 + fecha.segundo
    return dias * SEGUNDOS_DIA + segundos_dia


def formatear_fecha_real(fecha):
    if isinstance(fecha, datetime):
        return fecha.strftime("%d/%m/%Y %H:%M:%S DC")

    return (
        f"{fecha.dia:02d}/{fecha.mes:02d}/{fecha.anio:04d} "
        f"{fecha.hora:02d}:{fecha.minuto:02d}:{fecha.segundo:02d} {fecha.era}"
    )


def fecha_gregoriana_desde_biblica(anio, mes=1, dia=1):
    """Devuelve la fecha gregoriana equivalente sin correccion solar.

    Cada dia biblico se compara contra un dia real a partir de la base fija.
    Esto permite exportar consultas incluso en anos anteriores a Cristo.
    """
    if mes < 1 or mes > 12 or dia < 1 or dia > 30:
        raise ValueError("El calendario biblico usa meses del 1 al 12 y dias del 1 al 30.")

    indice_biblico = ((anio - BASE_ANIO) * DIAS_ANIO) + ((mes - 1) * DIAS_MES) + (dia - 1)
    base = fecha_extendida_desde_datetime(BASE_REAL)
    dias_base = _dias_desde_civil(base.anio_astronomico, base.mes, base.dia)
    anio_astronomico, mes_real, dia_real = _civil_desde_dias(dias_base + indice_biblico)
    era = "DC" if anio_astronomico >= 1 else "AC"
    anio_real = anio_astronomico if era == "DC" else 1 - anio_astronomico
    return FechaExtendida(anio_real, mes_real, dia_real, era=era)


def parsear_fecha_consulta(texto, era="DC"):
    valor = (texto or "").strip()

    if not valor:
        raise ValueError("Ingrese una fecha para consultar.")

    era_detectada = None
    patron_era = re.search(
        r"\b(AC|A\.?C\.?|BC|B\.?C\.?|DC|D\.?C\.?|AD|A\.?D\.?)\b$",
        valor,
        re.IGNORECASE,
    )

    if patron_era:
        era_detectada = patron_era.group(1)
        valor = valor[: patron_era.start()].strip()

    era_final = _normalizar_era(era_detectada or era)
    partes = valor.split()
    fecha_texto = partes[0]
    hora_texto = partes[1] if len(partes) > 1 else "00:00:00"

    if "/" in fecha_texto:
        trozos = fecha_texto.split("/")
        if len(trozos) != 3:
            raise ValueError("Use una fecha como 05/07/2026 14:30:00.")
        dia, mes, anio = [int(t) for t in trozos]
    elif "-" in fecha_texto:
        trozos = fecha_texto.split("-")
        if len(trozos) != 3:
            raise ValueError("Use una fecha como 2026-07-05 14:30:00.")
        anio, mes, dia = [int(t) for t in trozos]
    else:
        raise ValueError("Use una fecha como 05/07/2026 14:30:00.")

    hora_partes = [int(t) for t in hora_texto.split(":")]
    if len(hora_partes) == 2:
        hora_partes.append(0)

    if len(hora_partes) != 3:
        raise ValueError("Use la hora como HH:MM o HH:MM:SS.")

    hora, minuto, segundo = hora_partes
    _validar_fecha(anio, mes, dia, hora, minuto, segundo, era_final)

    return FechaExtendida(anio, mes, dia, hora, minuto, segundo, era_final)


def _validar_fecha(anio, mes, dia, hora, minuto, segundo, era):
    if anio <= 0:
        raise ValueError("El año debe ser mayor a 0. Para antes de Cristo use la era AC.")

    if mes < 1 or mes > 12:
        raise ValueError("El mes debe estar entre 1 y 12.")

    anio_astronomico = anio if era == "DC" else 1 - anio
    max_dia = _dias_mes_gregoriano(anio_astronomico, mes)

    if dia < 1 or dia > max_dia:
        raise ValueError(f"Ese mes admite dias del 1 al {max_dia}.")

    if hora < 0 or hora > 23 or minuto < 0 or minuto > 59 or segundo < 0 or segundo > 59:
        raise ValueError("La hora debe estar entre 00:00:00 y 23:59:59.")


def cargar_base_calendario():
    # La base no es configurable: evita que consultas previas cambien el
    # resultado de todo el calendario.
    return fecha_extendida_desde_datetime(BASE_REAL)


def guardar_base_calendario(fecha):
    if isinstance(fecha, datetime):
        fecha = fecha_extendida_desde_datetime(fecha)

    os.makedirs(os.path.dirname(CONFIG_ARCHIVO), exist_ok=True)

    with open(CONFIG_ARCHIVO, "w", encoding="utf-8") as archivo:
        json.dump(
            {
                "anio": fecha.anio,
                "mes": fecha.mes,
                "dia": fecha.dia,
                "hora": fecha.hora,
                "minuto": fecha.minuto,
                "segundo": fecha.segundo,
                "era": fecha.era,
            },
            archivo,
            indent=4,
            ensure_ascii=False,
        )


def calcular_calendario_360(fecha_real=None, base_real=None):
    fecha_real = fecha_real or datetime.now()
    base_real = base_real or fecha_extendida_desde_datetime(BASE_REAL)
    delta_segundos = _segundos_absolutos(fecha_real) - _segundos_absolutos(base_real)
    bloque_anios, resto_anio = divmod(delta_segundos, SEGUNDOS_ANIO)

    dia_indice = resto_anio // SEGUNDOS_DIA
    resto_dia = resto_anio % SEGUNDOS_DIA
    mes_indice = dia_indice // DIAS_MES
    dia_mes = dia_indice % DIAS_MES + 1

    hora = resto_dia // 3600
    minuto = (resto_dia % 3600) // 60
    segundo = resto_dia % 60

    return {
        "fecha_real": fecha_real,
        "fecha_real_texto": formatear_fecha_real(fecha_real),
        "base_real": base_real,
        "base_real_texto": formatear_fecha_real(base_real),
        "anio": BASE_ANIO + ANIOS_BIBLICOS_PREVIOS + bloque_anios,
        "mes_numero": mes_indice + 1,
        "mes": MESES_360[mes_indice],
        "dia_mes": dia_mes,
        "dia_anio": dia_indice + 1,
        "hora": hora,
        "minuto": minuto,
        "segundo": segundo,
        "hora_texto": f"{hora:02d}:{minuto:02d}:{segundo:02d}",
        "dias_restantes_anio": DIAS_ANIO - (dia_indice + 1),
        "segundos_desde_base": delta_segundos,
    }


def texto_calendario_360(datos):
    return (
        f"Año calendario: {datos['anio']}\n"
        f"Mes calendario: {datos['mes']} (mes {datos['mes_numero']}/12)\n"
        f"Día del mes: {datos['dia_mes']}/30\n"
        f"Día del año: {datos['dia_anio']}/360\n"
        f"Hora calendario: {datos['hora_texto']}\n"
        f"Fecha real usada: {datos['fecha_real_texto']}\n"
        f"Base del año {BASE_ANIO + ANIOS_BIBLICOS_PREVIOS}: {datos['base_real_texto']}"
    )
