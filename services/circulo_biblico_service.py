"""Acceso a los datos que alimentan el Aro Arcoiris."""

from logica.circulo_biblico import crear_modelo_aro
from services.biblia_service import BibliaService


class CirculoBiblicoService:
    @staticmethod
    def nombres_libros():
        return BibliaService.nombres_libros()

    @staticmethod
    def modelo_libro(nombre):
        libro = BibliaService.libro_por_nombre(nombre)
        if not libro:
            raise ValueError(f"No se encontro el libro biblico: {nombre}")
        return crear_modelo_aro(libro)

    @staticmethod
    def cantidad_versiculos(nombre, capitulo):
        return len(BibliaService.obtener_capitulo(nombre, capitulo))
