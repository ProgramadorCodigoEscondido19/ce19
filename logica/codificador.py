import unicodedata


def normalizar_texto_codificador(texto):
    texto = (texto or "").upper()
    texto = texto.replace("Ñ", "\0")
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )
    return texto.replace("\0", "Ñ")


def normalizar_letra(letra):
    return normalizar_texto_codificador(letra)


class Codificador:
    def __init__(self, alfabeto):
        self.alfabeto = alfabeto
        self.diccionario = {}

    def crear_diccionario(self, usar_ch=False, usar_ll=False, **opciones):
        usar_enie = bool(
            opciones.get("usar_ñ")
            or opciones.get("usar_enie")
            or opciones.get("usar_Ñ")
        )
        lista = []

        for letra_original in self.alfabeto:
            letra = normalizar_letra(letra_original)

            if letra == "CH":
                if usar_ch:
                    lista.append(letra)
            elif letra == "LL":
                if usar_ll:
                    lista.append(letra)
            elif letra == "Ñ":
                if usar_enie:
                    lista.append(letra)
            else:
                lista.append(letra)

        self.diccionario = {
            letra: numero
            for numero, letra in enumerate(lista, start=1)
        }
        return self.diccionario

    def obtener_tipo_alfabeto(self):
        return len(self.diccionario)

    def decodificar_numeros(self, codigo):
        if not self.diccionario:
            self.crear_diccionario(usar_ch=True, usar_ll=True, usar_enie=True)

        inverso = {
            numero: letra
            for letra, numero in self.diccionario.items()
        }
        texto_original = (codigo or "").strip()
        if not texto_original:
            raise ValueError("Debe ingresar números para decodificar.")

        lineas_resultado = []
        valores = []
        detalle = []

        def normalizar_palabra(letras):
            palabra = "".join(letras).lower()
            return palabra if len(letras) == 1 else palabra.capitalize()

        for linea in texto_original.splitlines() or [texto_original]:
            linea = linea.strip()
            if not linea:
                lineas_resultado.append("")
                continue

            partes = []
            letras_pendientes = []
            i = 0

            def volcar_palabra():
                if letras_pendientes:
                    partes.append(normalizar_palabra(letras_pendientes))
                    letras_pendientes.clear()

            while i < len(linea):
                if linea.startswith("__", i):
                    volcar_palabra()
                    if partes and partes[-1] != " ":
                        partes.append(" ")
                    i += 2
                    continue

                caracter = linea[i]

                if caracter == "_":
                    i += 1
                    continue

                if caracter.isdigit():
                    j = i
                    while j < len(linea) and linea[j].isdigit():
                        j += 1

                    numero_despues_de_titulo = (
                        partes
                        and partes[-1] == ":"
                        and not letras_pendientes
                        and (
                            j >= len(linea)
                            or linea.startswith("__", j)
                            or linea[j] != "_"
                        )
                    )
                    if numero_despues_de_titulo:
                        volcar_palabra()
                        partes.append(linea[i:j])
                        i = j
                        continue

                    numero = int(linea[i:j])
                    if numero not in inverso:
                        raise ValueError(f"El número {numero} no pertenece al alfabeto 1-29.")

                    letra = inverso[numero]
                    valores.append(numero)
                    letras_pendientes.append(letra)
                    detalle.append(f"{numero}={letra}")
                    i = j
                    continue

                if caracter == ":":
                    volcar_palabra()
                    partes.append(":")
                    i += 1
                    continue

                if caracter.isspace():
                    volcar_palabra()
                    if partes and partes[-1] != " ":
                        partes.append(" ")
                    i += 1
                    continue

                if caracter.isalpha():
                    volcar_palabra()
                    inicio = i
                    while i < len(linea) and linea[i].isalpha():
                        i += 1
                    partes.append(linea[inicio:i])
                    continue

                if caracter in ".,;!?()[]{}-/\\\"'":
                    volcar_palabra()
                    partes.append(caracter)
                    i += 1
                    continue

                raise ValueError(
                    "Use números del 1 al 29, _ entre letras, __ entre palabras. "
                    "También se permiten espacios, texto y signos como ':' para títulos."
                )

            volcar_palabra()
            lineas_resultado.append("".join(partes).strip())

        resultado = "\n".join(lineas_resultado).strip()
        if not resultado:
            raise ValueError("No se encontraron números válidos para decodificar.")

        return {
            "palabra": texto_original,
            "texto_original": texto_original,
            "letras_calculadas": detalle,
            "alfabeto": self.obtener_tipo_alfabeto(),
            "valores": valores,
            "suma": " + ".join(detalle),
            "resultado": resultado,
            "modo_codificacion": "Números a texto",
            "subtipo": "numeros_a_texto",
        }

    def codificar(self, palabra):
        palabra_limpia = normalizar_texto_codificador(palabra)
        texto_limpio = "".join(
            caracter
            for caracter in palabra_limpia
            if caracter.isalpha() or caracter.isspace()
        )
        texto_limpio = " ".join(texto_limpio.split())
        valores = []
        letras = []
        i = 0

        while i < len(palabra_limpia):
            if (
                "CH" in self.diccionario
                and palabra_limpia[i:i + 2] == "CH"
            ):
                valores.append(self.diccionario["CH"])
                letras.append("CH")
                i += 2
                continue

            if (
                "LL" in self.diccionario
                and palabra_limpia[i:i + 2] == "LL"
            ):
                valores.append(self.diccionario["LL"])
                letras.append("LL")
                i += 2
                continue

            letra = palabra_limpia[i]

            if letra in self.diccionario:
                valores.append(self.diccionario[letra])
                letras.append(letra)

            i += 1

        suma = sum(valores)
        texto = " + ".join(str(x) for x in valores)

        return {
            "palabra": texto_limpio,
            "texto_original": palabra,
            "letras_calculadas": letras,
            "alfabeto": self.obtener_tipo_alfabeto(),
            "valores": valores,
            "suma": texto,
            "resultado": suma,
        }
