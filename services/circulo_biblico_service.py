"""Construccion de aros usando exclusivamente los datos biblicos cargados."""

from logica.analizador_colores import analizar_codigo_visual
from logica.circulo_biblico import (
    ALCANCE_BIBLIA, ALCANCE_CAPITULO, ALCANCE_LIBRO, ALCANCE_VERSICULO,
    ModeloAro, anillo_dividido, anillo_solido, reducir_a_un_digito,
)
from services.biblia_service import BibliaService


class CirculoBiblicoService:
    @staticmethod
    def nombres_libros():
        return BibliaService.nombres_libros()

    @staticmethod
    def cantidad_versiculos(nombre, capitulo):
        return len(BibliaService.obtener_capitulo(nombre, capitulo))

    @classmethod
    def _libro(cls, nombre):
        libros = BibliaService.libros()
        libro = BibliaService.libro_por_nombre(nombre)
        if not libro:
            raise ValueError(f"No se encontró el libro bíblico: {nombre}")
        indice = next(i for i, item in enumerate(libros, 1) if item is libro)
        return libro, indice

    @classmethod
    def modelo_biblia(cls):
        libros = BibliaService.libros()
        cantidad = len(libros)
        primera_suma = sum(int(c) for c in str(cantidad))
        reduccion = reducir_a_un_digito(cantidad)
        return ModeloAro(
            ALCANCE_BIBLIA, "biblia-completa", "BIBLIA COMPLETA", f"{cantidad} libros",
            anillo_solido("Cantidad total de libros", cantidad, f"{cantidad} → {primera_suma} → {reduccion}", valor_borde=cantidad),
            anillo_dividido("Libros según su número", cantidad, "L", valor_borde=cantidad),
            "BORDE: TOTAL DE LIBROS", "INTERIOR: LIBROS",
        )

    @classmethod
    def modelo_libro(cls, nombre):
        libro, numero_libro = cls._libro(nombre)
        capitulos = libro.get("capitulos", [])
        return ModeloAro(
            ALCANCE_LIBRO, f"libro-{numero_libro}", str(libro.get("nombre", nombre)).upper(),
            f"Libro {numero_libro} · {len(capitulos)} capítulos",
            anillo_dividido("Número del libro", numero_libro, "L", valor_borde=numero_libro),
            anillo_dividido("Capítulos", len(capitulos), "C", valor_borde=len(capitulos)),
            f"BORDE: LIBRO {numero_libro}", "INTERIOR: CAPÍTULOS",
        )

    @classmethod
    def modelo_capitulo(cls, nombre, capitulo):
        libro, _ = cls._libro(nombre)
        capitulos = libro.get("capitulos", [])
        capitulo = int(capitulo)
        if capitulo < 1 or capitulo > len(capitulos):
            raise ValueError("El capítulo seleccionado no existe.")
        cantidad_versiculos = len(capitulos[capitulo - 1])
        return ModeloAro(
            ALCANCE_CAPITULO, f"capitulo-{nombre}-{capitulo}", f"{nombre.upper()} {capitulo}",
            f"{len(capitulos)} capítulos · capítulo {capitulo}: {cantidad_versiculos} versículos",
            anillo_dividido(
                "Número del capítulo", capitulo, "C",
                valor_borde=len(capitulos) if capitulo > 1 else None,
            ),
            anillo_dividido("Versículos del capítulo", cantidad_versiculos, "V", valor_borde=cantidad_versiculos),
            f"BORDE: CAPÍTULO {capitulo}", "INTERIOR: VERSÍCULOS",
        )

    @classmethod
    def modelo_versiculo(cls, nombre, capitulo, versiculo):
        cls._libro(nombre)
        capitulo, versiculo = int(capitulo), int(versiculo)
        texto = BibliaService.obtener_versiculo(nombre, capitulo, versiculo)
        if not texto:
            raise ValueError("El versículo seleccionado no existe.")
        # La Biblia cargada está en español: se usa el alfabeto numérico base
        # para que el resultado no cambie si el usuario dejó activo hebreo,
        # griego o un diccionario personalizado en CODICOLOR.
        analisis = analizar_codigo_visual(texto)
        suma = int(analisis.get("total_codigo", 0))
        cifras = [int(cifra) for cifra in str(abs(suma))] or [0]
        pasos = " → ".join(str(valor) for valor in analisis.get("pasos_reduccion", []))
        return ModeloAro(
            ALCANCE_VERSICULO, f"versiculo-{nombre}-{capitulo}-{versiculo}",
            f"{nombre.upper()} {capitulo}:{versiculo}",
            f"Versículo {versiculo} · suma del texto: {suma} → {analisis['resultado_final']}",
            # El borde exterior representa el número del versículo elegido,
            # no la cantidad total de versículos del capítulo.
            anillo_dividido("Número de versículo", versiculo, "V", valor_borde=versiculo),
            anillo_dividido(
                "Cifras de la suma alfabética", len(cifras), "D", valores=cifras,
                etiquetas=[f"D{cifra}" for cifra in cifras], valor_borde=suma,
            ),
            f"BORDE: VERSÍCULO {versiculo}", "INTERIOR: CIFRAS DE LA SUMA", f"Reducción: {pasos}",
        )

    @classmethod
    def crear_modelo(cls, alcance, nombre=None, capitulo=1, versiculo=1):
        if alcance == ALCANCE_BIBLIA:
            return cls.modelo_biblia()
        if alcance == ALCANCE_LIBRO:
            return cls.modelo_libro(nombre)
        if alcance == ALCANCE_CAPITULO:
            return cls.modelo_capitulo(nombre, capitulo)
        if alcance == ALCANCE_VERSICULO:
            return cls.modelo_versiculo(nombre, capitulo, versiculo)
        raise ValueError("Seleccione Biblia completa, Libro, Capítulo o Versículo.")
