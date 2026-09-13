"""Diálogo de selección múltiple para exportar Aro Arcoiris a PDF."""

import flet as ft

from logica.circulo_biblico import (
    ALCANCE_BIBLIA, ALCANCE_CAPITULO, ALCANCE_LIBRO, ALCANCE_VERSICULO,
)
from services.circulo_biblico_service import CirculoBiblicoService
from ui.dialogos import cerrar_dialogo, mostrar_dialogo
from ui.tema import PURPURA_IOS, BLANCO, TEXTO_SECUNDARIO


class SelectorPdfAro:
    def __init__(self, page, alcance, libro, capitulo, versiculo, al_confirmar):
        self.page = page
        self.al_confirmar = al_confirmar
        self.libros = CirculoBiblicoService.nombres_libros()
        self.alcance_inicial = alcance
        self.libro_inicial = libro or (self.libros[0] if self.libros else None)
        self.capitulo_inicial = int(capitulo or 1)
        self.versiculo_inicial = int(versiculo or 1)
        self.selector_tipo = ft.Dropdown(
            label="Qué desea incluir", value=alcance or ALCANCE_LIBRO, dense=True,
            options=[
                ft.dropdown.Option(ALCANCE_BIBLIA, text="Biblia completa"),
                ft.dropdown.Option(ALCANCE_LIBRO, text="Uno o más libros"),
                ft.dropdown.Option(ALCANCE_CAPITULO, text="Uno o más capítulos"),
                ft.dropdown.Option(ALCANCE_VERSICULO, text="Uno o más versículos"),
            ], on_select=self._cambiar_tipo,
        )
        self.selector_libro = ft.Dropdown(
            label="Libro", value=self.libro_inicial, dense=True, enable_filter=True, enable_search=True,
            options=[ft.dropdown.Option(nombre) for nombre in self.libros], on_select=self._cambiar_libro,
        )
        self.selector_capitulo = ft.Dropdown(label="Capítulo", value=str(self.capitulo_inicial), dense=True,
                                             on_select=self._cambiar_capitulo)
        self.lista = ft.Column(height=310, spacing=2, scroll=ft.ScrollMode.AUTO)
        self.aviso = ft.Text("", color=ft.Colors.RED_700)
        self.dialogo = None
        self._actualizar_capitulos()
        self._reconstruir_lista()

    def _actualizar_capitulos(self):
        if not self.selector_libro.value:
            return
        cantidad = len(CirculoBiblicoService.modelo_libro(self.selector_libro.value).interior.secciones)
        self.selector_capitulo.options = [ft.dropdown.Option(str(numero)) for numero in range(1, cantidad + 1)]
        if int(self.selector_capitulo.value or 1) > cantidad:
            self.selector_capitulo.value = "1"

    def _reconstruir_lista(self):
        tipo = self.selector_tipo.value
        self.selector_libro.visible = tipo in {ALCANCE_CAPITULO, ALCANCE_VERSICULO}
        self.selector_capitulo.visible = tipo == ALCANCE_VERSICULO
        if tipo == ALCANCE_BIBLIA:
            elementos = [("Biblia completa", None)]
        elif tipo == ALCANCE_LIBRO:
            elementos = [(nombre, nombre) for nombre in self.libros]
        elif tipo == ALCANCE_CAPITULO:
            cantidad = len(CirculoBiblicoService.modelo_libro(self.selector_libro.value).interior.secciones)
            elementos = [(f"{self.selector_libro.value} {numero}", numero) for numero in range(1, cantidad + 1)]
        else:
            capitulo = int(self.selector_capitulo.value or 1)
            cantidad = CirculoBiblicoService.cantidad_versiculos(self.selector_libro.value, capitulo)
            elementos = [(f"{self.selector_libro.value} {capitulo}:{numero}", numero) for numero in range(1, cantidad + 1)]
        controles = []
        for etiqueta, valor in elementos:
            seleccionado = False
            if tipo == self.alcance_inicial:
                if tipo == ALCANCE_BIBLIA:
                    seleccionado = True
                elif tipo == ALCANCE_LIBRO:
                    seleccionado = valor == self.libro_inicial
                elif tipo == ALCANCE_CAPITULO:
                    seleccionado = self.selector_libro.value == self.libro_inicial and valor == self.capitulo_inicial
                else:
                    seleccionado = (
                        self.selector_libro.value == self.libro_inicial
                        and int(self.selector_capitulo.value or 1) == self.capitulo_inicial
                        and valor == self.versiculo_inicial
                    )
            controles.append(ft.Checkbox(label=etiqueta, value=seleccionado, data=valor))
        self.lista.controls = controles

    def _refrescar(self):
        self.aviso.value = ""
        self._reconstruir_lista()
        self.page.update()

    def _cambiar_tipo(self, e=None):
        self._refrescar()

    def _cambiar_libro(self, e=None):
        self.selector_capitulo.value = "1"
        self._actualizar_capitulos()
        self._refrescar()

    def _cambiar_capitulo(self, e=None):
        self._refrescar()

    def _marcar_todos(self, valor):
        for control in self.lista.controls:
            control.value = valor
        self.page.update()

    def _confirmar(self, e=None):
        elegidos = [control.data for control in self.lista.controls if control.value]
        if not elegidos:
            self.aviso.value = "Seleccione al menos un elemento."
            self.page.update()
            return
        tipo = self.selector_tipo.value
        libro = self.selector_libro.value
        capitulo = int(self.selector_capitulo.value or 1)
        if tipo == ALCANCE_BIBLIA:
            modelos = [CirculoBiblicoService.modelo_biblia()]
        elif tipo == ALCANCE_LIBRO:
            modelos = [CirculoBiblicoService.modelo_libro(nombre) for nombre in elegidos]
        elif tipo == ALCANCE_CAPITULO:
            modelos = [CirculoBiblicoService.modelo_capitulo(libro, numero) for numero in elegidos]
        else:
            modelos = [CirculoBiblicoService.modelo_versiculo(libro, capitulo, numero) for numero in elegidos]
        cerrar_dialogo(self.page, self.dialogo)
        self.al_confirmar(modelos)

    def mostrar(self):
        self.dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Seleccionar círculos para el PDF", weight=ft.FontWeight.BOLD),
            content=ft.Container(width=520, content=ft.Column(tight=True, spacing=10, controls=[
                ft.Text("Cada elemento seleccionado se exportará como un círculo en una página independiente.",
                        color=TEXTO_SECUNDARIO),
                self.selector_tipo,
                ft.Row(wrap=True, controls=[
                    ft.Container(width=260, content=self.selector_libro),
                    ft.Container(width=150, content=self.selector_capitulo),
                ]),
                ft.Row(wrap=True, controls=[
                    ft.TextButton("Seleccionar todo", on_click=lambda e: self._marcar_todos(True)),
                    ft.TextButton("Quitar selección", on_click=lambda e: self._marcar_todos(False)),
                ]),
                self.lista,
                self.aviso,
            ])),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: cerrar_dialogo(self.page, self.dialogo)),
                ft.Button("Descargar seleccionados", icon=ft.Icons.PICTURE_AS_PDF,
                          bgcolor=PURPURA_IOS, color=BLANCO, on_click=self._confirmar),
            ],
        )
        mostrar_dialogo(self.page, self.dialogo, cerrar_al_tocar_fuera=False)
        return self.dialogo
