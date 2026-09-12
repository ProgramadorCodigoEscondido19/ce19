"""Construccion de aros usando exclusivamente los datos biblicos cargados."""

from logica.analizador_colores import analizar_codigo_visual
from logica.circulo_biblico import (
    ALCANCE_BIBLIA, ALCANCE_CAPITULO, ALCANCE_LIBRO, ALCANCE_VERSICULO,
    ModeloAro, anillo_dividido, anillo_solido, reducir_a_un_digito,
)
from services.alfabetos_service import AlfabetosService
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
        cantidades_capitulos = [len(libro.get("capitulos", [])) for libro in libros]
        return ModeloAro(
            ALCANCE_BIBLIA, "biblia-completa", "BIBLIA COMPLETA", f"{cantidad} libros",
            anillo_solido("Cantidad total de libros", cantidad, f"{cantidad} → {primera_suma} → {reduccion}"),
            anillo_dividido("Libros según su cantidad de capítulos", cantidad, "L", cantidades_capitulos),
            "BORDE: TOTAL DE LIBROS", "INTERIOR: LIBROS",
        )

    @classmethod
    def modelo_libro(cls, nombre):
        libro, numero_libro = cls._libro(nombre)
        capitulos = libro.get("capitulos", [])
        return ModeloAro(
            ALCANCE_LIBRO, f"libro-{numero_libro}", str(libro.get("nombre", nombre)).upper(),
            f"Libro {numero_libro} · {len(capitulos)} capítulos",
            anillo_dividido("Número del libro", numero_libro, "L"),
            anillo_dividido("Capítulos", len(capitulos), "C"),
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
            anillo_dividido("Capítulos del libro", len(capitulos), "C"),
            anillo_dividido("Versículos del capítulo", cantidad_versiculos, "V"),
            "BORDE: CAPÍTULOS", "INTERIOR: VERSÍCULOS",
        )

    @classmethod
    def modelo_versiculo(cls, nombre, capitulo, versiculo):
        cls._libro(nombre)
        capitulo, versiculo = int(capitulo), int(versiculo)
        texto = BibliaService.obtener_versiculo(nombre, capitulo, versiculo)
        if not texto:
            raise ValueError("El versículo seleccionado no existe.")
        alfabeto = AlfabetosService.obtener()
        analisis = analizar_codigo_visual(texto, alfabeto.get("valores"))
        suma = int(analisis.get("total_codigo", 0))
        pasos = " → ".join(str(valor) for valor in analisis.get("pasos_reduccion", []))
        return ModeloAro(
            ALCANCE_VERSICULO, f"versiculo-{nombre}-{capitulo}-{versiculo}",
            f"{nombre.upper()} {capitulo}:{versiculo}",
            f"Versículo {versiculo} · suma del texto: {suma} → {analisis['resultado_final']}",
            anillo_dividido("Número de versículo", versiculo, "V"),
            anillo_solido("Suma numérica del texto", suma, f"Σ {suma} → {analisis['resultado_final']}"),
            f"BORDE: VERSÍCULO {versiculo}", "INTERIOR: TEXTO NUMÉRICO", f"Reducción: {pasos}",
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
