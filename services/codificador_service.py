from logica.codificador import Codificador
from logica.diccionarios import ALFABETO_COMPLETO


class CodificadorService:
    """Servicio central para codificar texto sin duplicar logica en vistas."""

    def __init__(self):
        self.motor = Codificador(ALFABETO_COMPLETO)

    def codificar(self, texto, usar_ch=True, usar_ll=True, usar_enie=True, **opciones):
        for clave in ("usar_ñ", "usar_Ã±", "usar_Ñ"):
            if clave in opciones:
                usar_enie = opciones[clave]
                break

        usar_enie = bool(usar_enie)
        self.motor.crear_diccionario(
            usar_ch=usar_ch,
            usar_ll=usar_ll,
            usar_enie=usar_enie,
        )
        return self.motor.codificar(texto or "")

    def codificar_29(self, texto):
        return self.codificar(texto, usar_ch=True, usar_ll=True, usar_enie=True)

    def decodificar_numeros_29(self, codigo):
        self.motor.crear_diccionario(
            usar_ch=True,
            usar_ll=True,
            usar_enie=True,
        )
        return self.motor.decodificar_numeros(codigo or "")

    def comparar_alfabetos(self, texto):
        return [
            {
                "nombre": "Americano 26 letras",
                "usar_ch": False,
                "usar_ll": False,
                "usar_enie": False,
                "datos": self.codificar(texto, False, False, False),
            },
            {
                "nombre": "Español moderno 27 letras",
                "usar_ch": False,
                "usar_ll": False,
                "usar_enie": True,
                "datos": self.codificar(texto, False, False, True),
            },
            {
                "nombre": "Español antiguo 29 letras",
                "usar_ch": True,
                "usar_ll": True,
                "usar_enie": True,
                "datos": self.codificar(texto, True, True, True),
            },
        ]
