from logica.codificador import Codificador
from services.alfabetos_service import AlfabetosService


class CodificadorService:
    """Servicio central para codificar y comparar alfabetos sin duplicar logica."""

    def __init__(self):
        self.nombre_alfabeto = ""
        self.seleccionar_alfabeto()

    def seleccionar_alfabeto(self, identificador=None):
        alfabeto = AlfabetosService.seleccionar(identificador or AlfabetosService.activo_id())
        self.motor = Codificador(alfabeto["valores"])
        self.nombre_alfabeto = alfabeto["nombre"]
        return alfabeto

    def codificar(self, texto, usar_ch=True, usar_ll=True, usar_enie=True, **opciones):
        for clave in ("usar_\u00f1", "usar_enie", "usar_\u00d1"):
            if clave in opciones:
                usar_enie = opciones[clave]
                break
        self.motor.crear_diccionario(
            usar_ch=usar_ch,
            usar_ll=usar_ll,
            usar_enie=bool(usar_enie),
        )
        datos = self.motor.codificar(texto or "")
        datos["alfabeto"] = self.nombre_alfabeto
        return datos

    def codificar_29(self, texto):
        return self.codificar(texto, usar_ch=True, usar_ll=True, usar_enie=True)

    def decodificar_numeros_29(self, codigo):
        return self.decodificar_numeros(codigo)

    def decodificar_numeros(self, codigo):
        self.motor.crear_diccionario(usar_ch=True, usar_ll=True, usar_enie=True)
        datos = self.motor.decodificar_numeros(codigo or "")
        datos["alfabeto"] = self.nombre_alfabeto
        return datos

    def comparar_alfabetos(self, texto):
        return self.comparar_diccionarios(texto)

    def comparar_diccionarios(self, texto, identificadores=None):
        """Codifica con varios alfabetos sin cambiar la eleccion activa."""
        disponibles = AlfabetosService.listar()
        seleccionados = set(identificadores or [item["id"] for item in disponibles])
        resultados = []
        for alfabeto in disponibles:
            if alfabeto["id"] not in seleccionados:
                continue
            motor = Codificador(alfabeto["valores"])
            motor.crear_diccionario(usar_ch=True, usar_ll=True, usar_enie=True)
            datos = motor.codificar(texto or "")
            datos["alfabeto"] = alfabeto["nombre"]
            datos["modo_codificacion"] = "Comparacion de alfabetos"
            resultados.append(datos)
        return resultados
