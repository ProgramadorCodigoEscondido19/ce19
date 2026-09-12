"""Vista responsive del Aro Arcoiris biblico."""

import asyncio
import math

import flet as ft
import flet.canvas as cv

from logica.circulo_biblico import COLOR_CONTORNO, color_texto_para_digito
from services.archivo_local_service import ArchivoLocalService
from services.circulo_biblico_service import CirculoBiblicoService
from services.exportador_circulo_biblico import generar_png_aro
from ui.leyenda_colores import leyenda_nueve_colores
from ui.tema import (
    BLANCO,
    PERLA_BORDE,
    PERLA_PANEL,
    PURPURA_IOS,
    TEXTO_PRINCIPAL,
    TEXTO_SECUNDARIO,
    panel_moderno,
)


class CirculoBiblicoView:
    def __init__(self, page, router):
        self.page = page
        self.router = router
        self.screenshot_ref = ft.Ref[ft.Screenshot]()
        self.libros = CirculoBiblicoService.nombres_libros()
        self.libro_actual = self.libros[0] if self.libros else ""
        self.modelo = CirculoBiblicoService.modelo_libro(self.libro_actual) if self.libro_actual else None

        self.selector_libro = ft.Dropdown(
            label="Libro bíblico",
            value=self.libro_actual or None,
            options=[ft.dropdown.Option(nombre) for nombre in self.libros],
            enable_filter=True,
            enable_search=True,
            dense=True,
            on_select=self._cambiar_libro,
        )
        self.selector_capitulo = ft.Dropdown(label="Capítulo", value="1", dense=True, on_select=self._cambiar_capitulo)
        self.selector_versiculo = ft.Dropdown(label="Versículo", value="1", dense=True, on_select=self._cambiar_versiculo)
        self.boton_exportar = ft.Button(
            "Guardar PNG",
            icon=ft.Icons.IMAGE,
            bgcolor=PURPURA_IOS,
            color=BLANCO,
            on_click=self._exportar,
        )
        self._actualizar_selectores()

    def _actualizar_selectores(self, reiniciar_capitulo=False):
        if not self.modelo:
            return
        if reiniciar_capitulo:
            self.selector_capitulo.value = "1"
        self.selector_capitulo.options = [
            ft.dropdown.Option(str(numero))
            for numero in range(1, self.modelo.cantidad_capitulos + 1)
        ]
        try:
            capitulo = int(self.selector_capitulo.value or 1)
        except ValueError:
            capitulo = 1
        cantidad = CirculoBiblicoService.cantidad_versiculos(self.libro_actual, capitulo)
        self.selector_versiculo.options = [ft.dropdown.Option(str(numero)) for numero in range(1, cantidad + 1)]
        if not self.selector_versiculo.value or int(self.selector_versiculo.value) > cantidad:
            self.selector_versiculo.value = "1" if cantidad else None

    def _cambiar_libro(self, e=None):
        self.libro_actual = self.selector_libro.value
        self.modelo = CirculoBiblicoService.modelo_libro(self.libro_actual)
        self.selector_versiculo.value = "1"
        self._actualizar_selectores(reiniciar_capitulo=True)
        self.router.refrescar()

    def _cambiar_capitulo(self, e=None):
        self.selector_versiculo.value = "1"
        self._actualizar_selectores()
        self.router.refrescar()

    def _cambiar_versiculo(self, e=None):
        self.router.refrescar()

    def _tamano_circulo(self):
        ancho = float(getattr(self.page, "width", 0) or 900)
        if ancho < 700:
            return max(210, min(620, ancho - 34))
        return max(420, min(720, ancho - 350))

    @staticmethod
    def _pintura(color, estilo=ft.PaintingStyle.FILL, grosor=None):
        return ft.Paint(color=color, style=estilo, stroke_width=grosor, anti_alias=True)

    @staticmethod
    def _tamano_texto_centro(lado, radio_hueco, texto, maximo):
        estimado = (radio_hueco * 1.52) / max(1, len(texto) * 0.62)
        return max(3.2, min(float(maximo), estimado, lado * 0.018))

    def _formas_circulo(self, lado):
        modelo = self.modelo
        if not modelo:
            return []
        centro = lado / 2
        radio_exterior = lado * 0.455
        radio_limite = radio_exterior * 0.74
        radio_hueco = radio_exterior * 0.21
        ancho_anillo = radio_exterior - radio_limite
        formas = []

        for seccion in modelo.secciones:
            inicio = math.radians(seccion.inicio_grados)
            barrido = math.radians(seccion.fin_grados - seccion.inicio_grados)
            formas.append(
                cv.Arc(
                    centro - radio_limite,
                    centro - radio_limite,
                    radio_limite * 2,
                    radio_limite * 2,
                    inicio,
                    barrido,
                    True,
                    self._pintura(seccion.color_versiculos),
                )
            )
            radio_anillo = radio_limite + ancho_anillo / 2
            formas.append(
                cv.Arc(
                    centro - radio_anillo,
                    centro - radio_anillo,
                    radio_anillo * 2,
                    radio_anillo * 2,
                    inicio,
                    barrido,
                    False,
                    self._pintura(seccion.color_capitulo, ft.PaintingStyle.STROKE, ancho_anillo),
                )
            )

        grosor = max(1.0, lado / 380)
        for seccion in modelo.secciones:
            angulo = math.radians(seccion.inicio_grados)
            formas.append(
                cv.Line(
                    centro + radio_hueco * math.cos(angulo),
                    centro + radio_hueco * math.sin(angulo),
                    centro + radio_exterior * math.cos(angulo),
                    centro + radio_exterior * math.sin(angulo),
                    self._pintura(COLOR_CONTORNO, ft.PaintingStyle.STROKE, grosor),
                )
            )

        formas.extend(
            [
                cv.Circle(centro, centro, radio_exterior, self._pintura(COLOR_CONTORNO, ft.PaintingStyle.STROKE, grosor * 1.5)),
                cv.Circle(centro, centro, radio_limite, self._pintura(modelo.color_total_versiculos, ft.PaintingStyle.STROKE, grosor * 4)),
                cv.Circle(centro, centro, radio_exterior + grosor * 3, self._pintura(modelo.color_total_capitulos, ft.PaintingStyle.STROKE, grosor * 3)),
                cv.Circle(centro, centro, radio_hueco, self._pintura("#FFFDF8")),
                cv.Circle(centro, centro, radio_hueco, self._pintura(COLOR_CONTORNO, ft.PaintingStyle.STROKE, grosor * 2)),
            ]
        )

        tamano_fuente = max(4.5, min(13.0, 18.0 - modelo.cantidad_capitulos * 0.25))
        for seccion in modelo.secciones:
            angulo = math.radians(seccion.medio_grados)
            radio_c = radio_limite + ancho_anillo * 0.52
            radio_v = (radio_hueco + radio_limite) / 2
            estilo_c = ft.TextStyle(size=tamano_fuente, weight=ft.FontWeight.BOLD, color=color_texto_para_digito(seccion.digito_capitulo))
            estilo_v = ft.TextStyle(size=tamano_fuente, weight=ft.FontWeight.BOLD, color=color_texto_para_digito(seccion.digito_versiculos))
            formas.append(cv.Text(centro + radio_c * math.cos(angulo), centro + radio_c * math.sin(angulo), f"C{seccion.capitulo}", style=estilo_c, alignment=ft.Alignment(0, 0)))
            formas.append(cv.Text(centro + radio_v * math.cos(angulo), centro + radio_v * math.sin(angulo), f"V{seccion.cantidad_versiculos}", style=estilo_v, alignment=ft.Alignment(0, 0)))
        texto_borde = f"BORDE: {modelo.libro.upper()}"
        texto_interior = "INTERIOR: VERSÍCULOS"
        texto_claves = "C = capítulo · V = versículos"
        tamano_borde = self._tamano_texto_centro(lado, radio_hueco, texto_borde, 13)
        tamano_interior = self._tamano_texto_centro(lado, radio_hueco, texto_interior, 12)
        tamano_claves = self._tamano_texto_centro(lado, radio_hueco, texto_claves, 9)
        formas.extend(
            [
                cv.Text(centro, centro - radio_hueco * 0.30, texto_borde, style=ft.TextStyle(size=tamano_borde, weight=ft.FontWeight.BOLD, color=COLOR_CONTORNO), alignment=ft.Alignment(0, 0)),
                cv.Text(centro, centro + radio_hueco * 0.06, texto_interior, style=ft.TextStyle(size=tamano_interior, weight=ft.FontWeight.BOLD, color=COLOR_CONTORNO), alignment=ft.Alignment(0, 0)),
                cv.Text(centro, centro + radio_hueco * 0.39, texto_claves, style=ft.TextStyle(size=tamano_claves, color=TEXTO_SECUNDARIO), alignment=ft.Alignment(0, 0)),
            ]
        )
        return formas

    def _circulo(self):
        lado = self._tamano_circulo()
        canvas = cv.Canvas(width=lado, height=lado, shapes=self._formas_circulo(lado))
        return ft.Container(
            width=lado,
            height=lado,
            alignment=ft.Alignment(0, 0),
            content=ft.InteractiveViewer(
                content=canvas,
                min_scale=1,
                max_scale=4,
                boundary_margin=24,
                alignment=ft.Alignment(0, 0),
            ),
        )

    def _exportar(self, e=None):
        if not self.modelo or self.boton_exportar.disabled:
            return
        self.boton_exportar.disabled = True
        self.boton_exportar.content = "Generando..."
        try:
            self.boton_exportar.update()
        except (RuntimeError, AssertionError):
            pass
        self.page.run_task(self._exportar_async, self.modelo)

    async def _exportar_async(self, modelo):
        try:
            try:
                datos = await asyncio.to_thread(generar_png_aro, modelo)
            except ModuleNotFoundError as error:
                if getattr(error, "name", "") not in {"PIL", "Pillow"}:
                    raise
                captura = self.screenshot_ref.current
                if captura is None:
                    raise RuntimeError("La vista todavía no está lista para capturarse.") from error
                datos = captura.capture(pixel_ratio=3, delay=100)
                if not datos:
                    raise RuntimeError("Flet no devolvió datos de la captura.")
            ArchivoLocalService.guardar_bytes(
                self.page,
                datos,
                f"Aro Arcoiris - {modelo.libro}",
                "png",
                "Guardar Aro Arcoiris como PNG",
            )
        except Exception as error:
            ArchivoLocalService._avisar(self.page, f"No se pudo generar el PNG: {error}", error=True)
        finally:
            self.boton_exportar.disabled = False
            self.boton_exportar.content = "Guardar PNG"
            try:
                self.boton_exportar.update()
            except (RuntimeError, AssertionError):
                pass

    def obtener_vista(self):
        if not self.modelo:
            return ft.Container(expand=True, alignment=ft.Alignment(0, 0), content=ft.Text("No hay datos bíblicos cargados."))

        try:
            capitulo = int(self.selector_capitulo.value or 1)
        except ValueError:
            capitulo = 1
        versiculo = self.selector_versiculo.value or "-"
        cantidad_versiculos = CirculoBiblicoService.cantidad_versiculos(self.libro_actual, capitulo)
        selectores = ft.Row(
            wrap=True,
            spacing=10,
            run_spacing=10,
            controls=[
                ft.Container(width=260, content=self.selector_libro),
                ft.Container(width=130, content=self.selector_capitulo),
                ft.Container(width=130, content=self.selector_versiculo),
            ],
        )
        acciones = ft.Row(
            wrap=True,
            spacing=10,
            run_spacing=10,
            controls=[
                ft.OutlinedButton("Volver", icon=ft.Icons.ARROW_BACK, on_click=lambda e: self.router.navegar("inicio")),
                self.boton_exportar,
            ],
        )

        bloque_exportable = ft.Container(
            bgcolor="#FFFDF8",
            padding=12,
            content=ft.Column(
                tight=True,
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("Aro Arcoiris", size=28, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                    ft.Text(self.modelo.libro.upper(), size=24, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL, text_align=ft.TextAlign.CENTER),
                    ft.Text(f"{self.modelo.cantidad_capitulos} capítulos · {self.modelo.total_versiculos} versículos", size=15, color=TEXTO_SECUNDARIO),
                    self._circulo(),
                    ft.Text("Borde exterior: capítulos · Interior: versículos", weight=ft.FontWeight.BOLD, color=COLOR_CONTORNO, text_align=ft.TextAlign.CENTER),
                    ft.Text(
                        f"Contorno exterior: total de capítulos ({self.modelo.cantidad_capitulos}) · Borde interior: total de versículos ({self.modelo.total_versiculos})",
                        size=12,
                        color=TEXTO_SECUNDARIO,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    leyenda_nueve_colores(),
                ],
            ),
        )

        return ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                panel_moderno(
                    ft.Column(
                        spacing=12,
                        controls=[
                            ft.Text("Aro Arcoiris", size=28, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                            selectores,
                            ft.Text(f"Selección: {self.modelo.libro} {capitulo}:{versiculo} · Capítulo {capitulo}: {cantidad_versiculos} versículos", color=TEXTO_SECUNDARIO),
                        ],
                    ),
                    padding=16,
                ),
                ft.Screenshot(ref=self.screenshot_ref, content=bloque_exportable),
                acciones,
                ft.Container(height=10),
            ],
        )
