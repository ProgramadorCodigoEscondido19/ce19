"""Calculos puros para el Aro Arcoiris biblico."""

from dataclasses import dataclass

from logica.analizador_colores import DIGITO_COLORES


COLOR_CONTORNO = "#35180F"


def reducir_a_un_digito(numero: int) -> int:
    """Reduce un entero no negativo sumando sus digitos repetidamente."""
    numero = abs(int(numero or 0))
    while numero > 9:
        numero = sum(int(digito) for digito in str(numero))
    return numero


def color_para_numero(numero: int) -> str:
    digito = reducir_a_un_digito(numero)
    return DIGITO_COLORES[digito]["hex"]


def color_texto_para_digito(digito: int) -> str:
    return "#FFFFFF" if int(digito) in {1, 2, 5, 6, 7} else COLOR_CONTORNO


@dataclass(frozen=True)
class SeccionAro:
    capitulo: int
    cantidad_versiculos: int
    digito_capitulo: int
    digito_versiculos: int
    color_capitulo: str
    color_versiculos: str
    inicio_grados: float
    fin_grados: float
    medio_grados: float


@dataclass(frozen=True)
class ModeloAro:
    libro: str
    cantidad_capitulos: int
    total_versiculos: int
    digito_total_capitulos: int
    digito_total_versiculos: int
    color_total_capitulos: str
    color_total_versiculos: str
    secciones: tuple[SeccionAro, ...]


def crear_modelo_aro(libro: dict) -> ModeloAro:
    """Crea el modelo angular usando exclusivamente los capitulos cargados."""
    nombre = str((libro or {}).get("nombre") or "")
    capitulos = (libro or {}).get("capitulos") or []
    cantidad_capitulos = len(capitulos)
    total_versiculos = sum(len(capitulo or []) for capitulo in capitulos)
    angulo = 360.0 / cantidad_capitulos if cantidad_capitulos else 0.0
    secciones = []

    for indice, versiculos in enumerate(capitulos, start=1):
        cantidad_versiculos = len(versiculos or [])
        inicio = -90.0 + (indice - 1) * angulo
        fin = inicio + angulo
        digito_capitulo = reducir_a_un_digito(indice)
        digito_versiculos = reducir_a_un_digito(cantidad_versiculos)
        secciones.append(
            SeccionAro(
                capitulo=indice,
                cantidad_versiculos=cantidad_versiculos,
                digito_capitulo=digito_capitulo,
                digito_versiculos=digito_versiculos,
                color_capitulo=color_para_numero(indice),
                color_versiculos=color_para_numero(cantidad_versiculos),
                inicio_grados=inicio,
                fin_grados=fin,
                medio_grados=(inicio + fin) / 2,
            )
        )

    return ModeloAro(
        libro=nombre,
        cantidad_capitulos=cantidad_capitulos,
        total_versiculos=total_versiculos,
        digito_total_capitulos=reducir_a_un_digito(cantidad_capitulos),
        digito_total_versiculos=reducir_a_un_digito(total_versiculos),
        color_total_capitulos=color_para_numero(cantidad_capitulos),
        color_total_versiculos=color_para_numero(total_versiculos),
        secciones=tuple(secciones),
    )
