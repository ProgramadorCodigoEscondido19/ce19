from logica.codificador import Codificador
from logica.diccionarios import ALFABETO_COMPLETO


class CodificadorService:
    """Servicio central para codificar texto sin duplicar lógica en vistas."""

    def __init__(self):
        self.motor = Codificador(ALFABETO_COMPLETO)

    def codificar(self, texto, usar_ch=True, usar_ll=True, usar_ñ=True):
        self.motor.crear_diccionario(
            usar_ch=usar_ch,
            usar_ll=usar_ll,
            usar_ñ=usar_ñ,
        )
        return self.motor.codificar(texto or "")

    def codificar_29(self, texto):
        return self.codificar(texto, usar_ch=True, usar_ll=True, usar_ñ=True)

    def comparar_alfabetos(self, texto):
        return [
            {
                "nombre": "Americano 26 letras",
                "usar_ch": False,
                "usar_ll": False,
                "usar_ñ": False,
                "datos": self.codificar(texto, False, False, False),
            },
            {
                "nombre": "Español moderno 27 letras",
                "usar_ch": False,
                "usar_ll": False,
                "usar_ñ": True,
                "datos": self.codificar(texto, False, False, True),
            },
            {
                "nombre": "Español antiguo 29 letras",
                "usar_ch": True,
                "usar_ll": True,
                "usar_ñ": True,
                "datos": self.codificar(texto, True, True, True),
            },
        ]
