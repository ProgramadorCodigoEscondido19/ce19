import unicodedata


def normalizar_texto_codificador(texto):
    texto = (texto or "").upper()
    texto = texto.replace("Ã‘", "Ñ")
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
            or opciones.get("usar_Ã±")
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
