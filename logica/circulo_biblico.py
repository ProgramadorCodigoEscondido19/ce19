"""Modelo y geometria puros para los cuatro alcances del Aro Arcoiris."""

from dataclasses import dataclass

from logica.analizador_colores import DIGITO_COLORES

COLOR_CONTORNO = "#35180F"
ALCANCE_BIBLIA = "biblia"
ALCANCE_LIBRO = "libro"
ALCANCE_CAPITULO = "capitulo"
ALCANCE_VERSICULO = "versiculo"


def reducir_a_un_digito(numero: int) -> int:
    numero = abs(int(numero or 0))
    while numero > 9:
        numero = sum(int(digito) for digito in str(numero))
    return numero


def color_para_numero(numero: int) -> str:
    return DIGITO_COLORES[reducir_a_un_digito(numero)]["hex"]


def color_texto_para_digito(digito: int) -> str:
    return "#FFFFFF" if int(digito) in {1, 2, 5, 6, 7} else COLOR_CONTORNO


@dataclass(frozen=True)
class SeccionAro:
    numero: int
    etiqueta: str
    valor: int
    digito: int
    color: str
    inicio_grados: float
    fin_grados: float
    medio_grados: float


@dataclass(frozen=True)
class AnilloAro:
    nombre: str
    secciones: tuple[SeccionAro, ...] = ()
    color_solido: str | None = None
    etiqueta_solida: str = ""
    digito_solido: int = 0
    color_borde: str = COLOR_CONTORNO


@dataclass(frozen=True)
class ModeloAro:
    alcance: str
    clave: str
    titulo: str
    resumen: str
    exterior: AnilloAro
    interior: AnilloAro
    texto_centro_1: str
    texto_centro_2: str
    texto_centro_3: str = "Inicio arriba · sentido horario"


def crear_secciones(cantidad: int, prefijo: str, valores=None, etiquetas=None) -> tuple[SeccionAro, ...]:
    """Crea sectores independientes, comenzando a las 12 y avanzando a la derecha."""
    cantidad = max(0, int(cantidad or 0))
    if not cantidad:
        return ()
    valores = list(valores) if valores is not None else list(range(1, cantidad + 1))
    if len(valores) != cantidad:
        raise ValueError("La cantidad de valores debe coincidir con los sectores.")
    etiquetas = list(etiquetas) if etiquetas is not None else [f"{prefijo}{indice}" for indice in range(1, cantidad + 1)]
    if len(etiquetas) != cantidad:
        raise ValueError("La cantidad de etiquetas debe coincidir con los sectores.")
    angulo = 360.0 / cantidad
    resultado = []
    for indice, valor in enumerate(valores, start=1):
        valor = int(valor)
        inicio = -90.0 + (indice - 1) * angulo
        digito = reducir_a_un_digito(valor)
        resultado.append(SeccionAro(
            numero=indice,
            etiqueta=str(etiquetas[indice - 1]),
            valor=valor,
            digito=digito,
            color=color_para_numero(valor),
            inicio_grados=inicio,
            fin_grados=inicio + angulo,
            medio_grados=inicio + angulo / 2,
        ))
    return tuple(resultado)


def anillo_dividido(nombre: str, cantidad: int, prefijo: str, valores=None, etiquetas=None, valor_borde=None) -> AnilloAro:
    color_borde = COLOR_CONTORNO if valor_borde is None else color_para_numero(valor_borde)
    return AnilloAro(
        nombre=nombre,
        secciones=crear_secciones(cantidad, prefijo, valores, etiquetas),
        color_borde=color_borde,
    )


def anillo_solido(nombre: str, valor: int, etiqueta: str, valor_borde=None) -> AnilloAro:
    digito = reducir_a_un_digito(valor)
    return AnilloAro(
        nombre=nombre,
        color_solido=color_para_numero(valor),
        etiqueta_solida=etiqueta,
        digito_solido=digito,
        color_borde=color_para_numero(valor if valor_borde is None else valor_borde),
    )
