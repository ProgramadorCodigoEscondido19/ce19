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


def detalle_por_palabras(texto, valores):
    """Agrupa los valores codificados sin separar la lectura por letras."""
    palabras = str(texto or "").split()
    detalle = []
    indice = 0

    for palabra in palabras:
        tokens = []
        mayusculas = palabra.upper()
        posicion = 0
        while posicion < len(mayusculas):
            compuesto = mayusculas[posicion:posicion + 2]
            if compuesto in ("CH", "LL"):
                tokens.append(compuesto)
                posicion += 2
            elif mayusculas[posicion].isalpha() or mayusculas[posicion].isdigit():
                tokens.append(mayusculas[posicion])
                posicion += 1
            else:
                posicion += 1

        cantidad = len(tokens)
        valores_palabra = list(valores[indice:indice + cantidad])
        indice += cantidad
        detalle.append(
            {
                "palabra": palabra,
                "valores": valores_palabra,
                "subtotal": sum(valores_palabra),
            }
        )

    return detalle


class Codificador:
    def __init__(self, alfabeto):
        self.alfabeto = alfabeto
        self.diccionario = {}

    def crear_diccionario(self, usar_ch=False, usar_ll=False, **opciones):
        if isinstance(self.alfabeto, dict):
            self.diccionario = {
                normalizar_letra(letra): int(numero)
                for letra, numero in self.alfabeto.items()
            }
            return self.diccionario

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

                # El asterisco se admite como marca visual y no forma parte
                # del codigo ni del texto resultante.
                if caracter == "*":
                    i += 1
                    continue

                if caracter == "_":
                    i += 1
                    continue

                if caracter.isdigit():
                    # Referencia de versiculo: 25 (V) + "_" + 1 o 2 digitos + ":".
                    # El numero del versiculo es una referencia, no una letra.
                    if linea.startswith("25_", i):
                        inicio_versiculo = i + 3
                        fin_versiculo = inicio_versiculo

                        while (
                            fin_versiculo < len(linea)
                            and linea[fin_versiculo].isdigit()
                            and fin_versiculo - inicio_versiculo < 2
                        ):
                            fin_versiculo += 1

                        es_referencia_versiculo = (
                            fin_versiculo > inicio_versiculo
                            and fin_versiculo < len(linea)
                            and linea[fin_versiculo] == ":"
                        )
                        if es_referencia_versiculo:
                            volcar_palabra()
                            letra_versiculo = inverso[25]
                            valores.append(25)
                            detalle.append(f"25={letra_versiculo}")
                            partes.append(
                                f"{normalizar_palabra([letra_versiculo])}"
                                f"{linea[inicio_versiculo:fin_versiculo]}:"
                            )
                            i = fin_versiculo + 1
                            continue

                    j = i
                    while j < len(linea) and linea[j].isdigit():
                        j += 1

                    numero_despues_de_titulo = (
                        partes
                        and partes[-1] == ":"
                        and not letras_pendientes
                        and 1 <= j - i <= 2
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
            "palabra": texto_original.replace("*", ""),
            "texto_original": texto_original.replace("*", ""),
            "letras_calculadas": detalle,
            "alfabeto": self.obtener_tipo_alfabeto(),
            "valores": valores,
            "suma": " + ".join(detalle),
            "resultado": resultado,
            "modo_codificacion": "Números a texto",
            "subtipo": "numeros_a_texto",
        }

    def codificar(self, palabra):
        texto_original = str(palabra or "").replace("*", "")
        palabra_limpia = normalizar_texto_codificador(texto_original)
        texto_limpio = "".join(
            caracter
            for caracter in palabra_limpia
            if caracter.isalpha() or caracter.isdigit() or caracter.isspace()
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

            # Los numeros escritos junto al texto se conservan como digitos
            # literales. Por ejemplo, 19 aporta 1 + 9; no se decodifica como
            # una letra del alfabeto ni se interpreta como el valor diecinueve.
            if letra.isdigit():
                valores.append(int(letra))
                letras.append(letra)
                i += 1
                continue

            if letra in self.diccionario:
                valores.append(self.diccionario[letra])
                letras.append(letra)

            i += 1

        suma = sum(valores)
        texto = " + ".join(str(x) for x in valores)

        return {
            "palabra": texto_limpio,
            "texto_original": texto_original,
            "letras_calculadas": letras,
            "alfabeto": self.obtener_tipo_alfabeto(),
            "valores": valores,
            "suma": texto,
            "resultado": suma,
            "detalle_palabras": detalle_por_palabras(texto_limpio, valores),
        }
