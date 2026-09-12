"""Vista responsive Aro Arcoiris con cuatro alcances y PDF multipagina."""

import asyncio
import math

import flet as ft
import flet.canvas as cv

from logica.circulo_biblico import (
    ALCANCE_BIBLIA, ALCANCE_CAPITULO, ALCANCE_LIBRO, ALCANCE_VERSICULO,
    COLOR_CONTORNO, color_texto_para_digito,
)
from services.archivo_local_service import ArchivoLocalService
from services.circulo_biblico_service import CirculoBiblicoService
from services.exportador_circulo_biblico import generar_pdf_aros, generar_png_aro
from ui.leyenda_colores import leyenda_nueve_colores
from ui.tema import BLANCO, PURPURA_IOS, TEXTO_PRINCIPAL, TEXTO_SECUNDARIO, panel_moderno


class CirculoBiblicoView:
    def __init__(self, page, router):
        self.page, self.router = page, router
        self.libros = CirculoBiblicoService.nombres_libros()
        self.cola = []
        self.selector_alcance = ft.Dropdown(
            label="¿Qué desea representar?", value=ALCANCE_BIBLIA, dense=True,
            options=[
                ft.dropdown.Option(ALCANCE_BIBLIA, text="Biblia completa"),
                ft.dropdown.Option(ALCANCE_LIBRO, text="Libro"),
                ft.dropdown.Option(ALCANCE_CAPITULO, text="Capítulo"),
                ft.dropdown.Option(ALCANCE_VERSICULO, text="Versículo"),
            ], on_select=self._cambiar_alcance,
        )
        self.selector_libro = ft.Dropdown(
            label="Libro bíblico", value=self.libros[0] if self.libros else None, dense=True,
            options=[ft.dropdown.Option(nombre) for nombre in self.libros], enable_filter=True, enable_search=True,
            on_select=self._cambiar_libro,
        )
        self.selector_capitulo = ft.Dropdown(label="Capítulo", value="1", dense=True, on_select=self._cambiar_capitulo)
        self.selector_versiculo = ft.Dropdown(label="Versículo", value="1", dense=True, on_select=self._cambiar_versiculo)
        self.boton_pdf = ft.Button("Descargar PDF", icon=ft.Icons.PICTURE_AS_PDF, bgcolor=PURPURA_IOS, color=BLANCO, on_click=self._exportar_pdf)
        self.boton_png = ft.OutlinedButton("Guardar PNG", icon=ft.Icons.IMAGE, on_click=self._exportar_png)
        self._actualizar_opciones()
        self.modelo = self._crear_modelo()

    def _crear_modelo(self):
        if not self.libros:
            return None
        return CirculoBiblicoService.crear_modelo(
            self.selector_alcance.value,
            self.selector_libro.value,
            int(self.selector_capitulo.value or 1),
            int(self.selector_versiculo.value or 1),
        )

    def _actualizar_opciones(self, reiniciar_capitulo=False):
        libro = self.selector_libro.value
        if not libro:
            return
        if reiniciar_capitulo:
            self.selector_capitulo.value = "1"
        cantidad_capitulos = CirculoBiblicoService.modelo_libro(libro).interior.secciones
        self.selector_capitulo.options = [ft.dropdown.Option(str(n)) for n in range(1, len(cantidad_capitulos)+1)]
        capitulo = int(self.selector_capitulo.value or 1)
        if capitulo > len(cantidad_capitulos):
            capitulo = 1
            self.selector_capitulo.value = "1"
        cantidad_versiculos = CirculoBiblicoService.cantidad_versiculos(libro, capitulo)
        self.selector_versiculo.options = [ft.dropdown.Option(str(n)) for n in range(1, cantidad_versiculos+1)]
        if int(self.selector_versiculo.value or 1) > cantidad_versiculos:
            self.selector_versiculo.value = "1" if cantidad_versiculos else None

    def _refrescar_modelo(self):
        self.modelo = self._crear_modelo()
        self.router.refrescar()

    def _cambiar_alcance(self, e=None):
        self._refrescar_modelo()

    def _cambiar_libro(self, e=None):
        self.selector_versiculo.value = "1"
        self._actualizar_opciones(reiniciar_capitulo=True)
        self._refrescar_modelo()

    def _cambiar_capitulo(self, e=None):
        self.selector_versiculo.value = "1"
        self._actualizar_opciones()
        self._refrescar_modelo()

    def _cambiar_versiculo(self, e=None):
        self._refrescar_modelo()

    def _tamano_circulo(self):
        ancho = float(getattr(self.page, "width", 0) or 900)
        return max(250, min(760 if ancho >= 700 else 620, ancho - (340 if ancho >= 700 else 28)))

    @staticmethod
    def _pintura(color, estilo=ft.PaintingStyle.FILL, grosor=None):
        return ft.Paint(color=color, style=estilo, stroke_width=grosor, anti_alias=True)

    def _formas_anillo(self, anillo, centro, radio_desde, radio_hasta, lado):
        formas, grosor = [], max(1.0, lado/420)
        radio_medio, ancho = (radio_desde+radio_hasta)/2, radio_hasta-radio_desde
        if anillo.color_solido:
            formas.append(cv.Circle(centro, centro, radio_medio, self._pintura(anillo.color_solido, ft.PaintingStyle.STROKE, ancho)))
        else:
            for sec in anillo.secciones:
                inicio, barrido = math.radians(sec.inicio_grados), math.radians(sec.fin_grados-sec.inicio_grados)
                formas.append(cv.Arc(centro-radio_medio, centro-radio_medio, radio_medio*2, radio_medio*2,
                                     inicio, barrido, False, self._pintura(sec.color, ft.PaintingStyle.STROKE, ancho)))
            for sec in anillo.secciones:
                a = math.radians(sec.inicio_grados)
                formas.append(cv.Line(centro+radio_desde*math.cos(a), centro+radio_desde*math.sin(a),
                                      centro+radio_hasta*math.cos(a), centro+radio_hasta*math.sin(a),
                                      self._pintura(COLOR_CONTORNO, ft.PaintingStyle.STROKE, grosor)))
        cantidad = len(anillo.secciones)
        if cantidad:
            tamano = max(2.8, min(12.0, lado*0.52/max(35, cantidad*0.62)))
            for sec in anillo.secciones:
                a = math.radians(sec.medio_grados)
                formas.append(cv.Text(centro+radio_medio*math.cos(a), centro+radio_medio*math.sin(a), sec.etiqueta,
                    style=ft.TextStyle(size=tamano, weight=ft.FontWeight.BOLD, color=color_texto_para_digito(sec.digito)),
                    alignment=ft.Alignment(0, 0)))
        elif anillo.etiqueta_solida:
            formas.append(cv.Text(centro, centro-radio_medio, anillo.etiqueta_solida,
                style=ft.TextStyle(size=max(7, lado*0.016), weight=ft.FontWeight.BOLD,
                                   color=color_texto_para_digito(anillo.digito_solido)), alignment=ft.Alignment(0, 0)))
        return formas

    def _formas_circulo(self, lado):
        m = self.modelo
        if not m:
            return []
        c, re = lado/2, lado*0.455
        rl, rh = re*0.76, re*0.23
        g = max(1.0, lado/390)
        formas = self._formas_anillo(m.exterior, c, rl, re, lado)
        formas += self._formas_anillo(m.interior, c, rh, rl, lado)
        formas += [
            cv.Circle(c, c, re, self._pintura(COLOR_CONTORNO, ft.PaintingStyle.STROKE, g*1.6)),
            cv.Circle(c, c, rl, self._pintura(COLOR_CONTORNO, ft.PaintingStyle.STROKE, g*1.6)),
            cv.Circle(c, c, rh, self._pintura("#FFFDF8")),
            cv.Circle(c, c, rh, self._pintura(COLOR_CONTORNO, ft.PaintingStyle.STROKE, g*1.6)),
        ]
        for desplazamiento, texto, maximo, negrita in [(-0.28, m.texto_centro_1, 12, True), (0.04, m.texto_centro_2, 11, True), (0.36, m.texto_centro_3, 8, False)]:
            tamano = max(3.0, min(maximo, rh*1.6/max(8, len(texto)*0.58)))
            formas.append(cv.Text(c, c+rh*desplazamiento, texto, style=ft.TextStyle(size=tamano,
                weight=ft.FontWeight.BOLD if negrita else None, color=COLOR_CONTORNO), alignment=ft.Alignment(0, 0)))
        return formas

    def _circulo(self):
        lado = self._tamano_circulo()
        return ft.Container(width=lado, height=lado, alignment=ft.Alignment(0, 0),
            content=ft.InteractiveViewer(content=cv.Canvas(width=lado, height=lado, shapes=self._formas_circulo(lado)),
                                         min_scale=1, max_scale=5, boundary_margin=24, alignment=ft.Alignment(0, 0)))

    def _agregar(self, e=None):
        if self.modelo and all(item.clave != self.modelo.clave for item in self.cola):
            self.cola.append(self.modelo)
        self.router.refrescar()

    def _quitar(self, clave):
        self.cola = [item for item in self.cola if item.clave != clave]
        self.router.refrescar()

    def _exportar_png(self, e=None):
        self.page.run_task(self._exportar_async, "png", [self.modelo])

    def _exportar_pdf(self, e=None):
        modelos = self.cola or ([self.modelo] if self.modelo else [])
        self.page.run_task(self._exportar_async, "pdf", modelos)

    async def _exportar_async(self, formato, modelos):
        boton = self.boton_pdf if formato == "pdf" else self.boton_png
        boton.disabled = True
        try:
            boton.update()
        except (RuntimeError, AssertionError):
            pass
        try:
            if formato == "pdf":
                datos = await asyncio.to_thread(generar_pdf_aros, modelos)
                ArchivoLocalService.guardar_bytes(self.page, datos, "Aro Arcoiris", "pdf", "Guardar Aro Arcoiris como PDF")
            else:
                datos = await asyncio.to_thread(generar_png_aro, modelos[0])
                ArchivoLocalService.guardar_bytes(self.page, datos, f"Aro Arcoiris - {modelos[0].titulo}", "png", "Guardar Aro Arcoiris como PNG")
        except Exception as error:
            ArchivoLocalService._avisar(self.page, f"No se pudo generar el {formato.upper()}: {error}", error=True)
        finally:
            boton.disabled = False
            try:
                boton.update()
            except (RuntimeError, AssertionError):
                pass

    def obtener_vista(self):
        if not self.modelo:
            return ft.Container(expand=True, alignment=ft.Alignment(0, 0), content=ft.Text("No hay datos bíblicos cargados."))
        alcance = self.selector_alcance.value
        self.selector_libro.visible = alcance != ALCANCE_BIBLIA
        self.selector_capitulo.visible = alcance in {ALCANCE_CAPITULO, ALCANCE_VERSICULO}
        self.selector_versiculo.visible = alcance == ALCANCE_VERSICULO
        selectores = ft.Row(wrap=True, spacing=10, run_spacing=10, controls=[
            ft.Container(width=240, content=self.selector_alcance), ft.Container(width=240, content=self.selector_libro),
            ft.Container(width=130, content=self.selector_capitulo), ft.Container(width=130, content=self.selector_versiculo),
        ])
        cola = ft.Column(spacing=6, controls=[
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                ft.Text(item.titulo, expand=True),
                ft.IconButton(icon=ft.Icons.CLOSE, tooltip="Quitar", on_click=lambda e, clave=item.clave: self._quitar(clave)),
            ]) for item in self.cola
        ])
        bloque = ft.Container(bgcolor="#FFFDF8", padding=12, content=ft.Column(tight=True, spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Text("Aro Arcoiris", size=28, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                ft.Text(self.modelo.titulo, size=23, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, color=TEXTO_PRINCIPAL),
                ft.Text(self.modelo.resumen, color=TEXTO_SECUNDARIO, text_align=ft.TextAlign.CENTER), self._circulo(),
                ft.Text(f"Borde exterior: {self.modelo.exterior.nombre} · Interior: {self.modelo.interior.nombre}",
                        weight=ft.FontWeight.BOLD, color=COLOR_CONTORNO, text_align=ft.TextAlign.CENTER),
                leyenda_nueve_colores(),
            ]))
        return ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                panel_moderno(ft.Column(spacing=12, controls=[
                    ft.Text("Aro Arcoiris", size=28, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                    ft.Text("Primero elija qué desea representar; luego seleccione un elemento.", color=TEXTO_SECUNDARIO),
                    selectores,
                    ft.Row(wrap=True, spacing=10, run_spacing=10, controls=[
                        ft.OutlinedButton("Agregar otro círculo", icon=ft.Icons.ADD, on_click=self._agregar),
                        self.boton_png, self.boton_pdf,
                        ft.OutlinedButton("Volver", icon=ft.Icons.ARROW_BACK, on_click=lambda e: self.router.navegar("inicio")),
                    ]),
                    ft.Text(f"Círculos preparados para PDF: {len(self.cola)}" if self.cola else "El PDF incluirá el círculo mostrado.", color=TEXTO_SECUNDARIO),
                    cola,
                ]), padding=16),
                bloque, ft.Container(height=10),
            ])
