"""Vista responsive Aro Arcoiris con cuatro alcances y PDF multipagina."""

import asyncio
import math

import flet as ft

from logica.circulo_biblico import (
    ALCANCE_BIBLIA, ALCANCE_CAPITULO, ALCANCE_LIBRO, ALCANCE_VERSICULO,
    COLOR_CONTORNO, color_texto_para_digito,
)
from services.archivo_local_service import ArchivoLocalService
from services.circulo_biblico_service import CirculoBiblicoService
from services.exportador_circulo_biblico import generar_pdf_modelos_nativo, generar_png_circulo_nativo
from ui.leyenda_colores import leyenda_nueve_colores
from ui.selector_pdf_arcoiris import SelectorPdfAro
from ui.tema import BLANCO, PURPURA_IOS, TEXTO_PRINCIPAL, TEXTO_SECUNDARIO, panel_moderno


class CirculoBiblicoView:
    def __init__(self, page, router):
        self.page, self.router = page, router
        self.libros = CirculoBiblicoService.nombres_libros()
        self.capturador = None
        self._imagenes_circulo = {}
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
        self.boton_analizar = ft.Button(
            "Iniciar análisis",
            icon=ft.Icons.PLAY_ARROW,
            bgcolor=PURPURA_IOS,
            color=BLANCO,
            on_click=self._analizar,
        )
        self.boton_limpiar = ft.OutlinedButton(
            "Limpiar",
            icon=ft.Icons.RESTART_ALT,
            on_click=self._limpiar,
        )
        self.boton_pdf = ft.Button("Descargar PDF", icon=ft.Icons.PICTURE_AS_PDF, bgcolor=PURPURA_IOS, color=BLANCO, on_click=self._exportar_pdf)
        self.boton_png = ft.OutlinedButton("Guardar PNG", icon=ft.Icons.IMAGE, on_click=self._exportar_png)
        self._actualizar_opciones()
        self.modelo = None

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

    def _marcar_pendiente(self):
        self.modelo = None
        self.router.refrescar()

    def _cambiar_alcance(self, e=None):
        self._marcar_pendiente()

    def _cambiar_libro(self, e=None):
        self.selector_versiculo.value = "1"
        self._actualizar_opciones(reiniciar_capitulo=True)
        self._marcar_pendiente()

    def _cambiar_capitulo(self, e=None):
        self.selector_versiculo.value = "1"
        self._actualizar_opciones()
        self._marcar_pendiente()

    def _cambiar_versiculo(self, e=None):
        self._marcar_pendiente()

    def _analizar(self, e=None):
        try:
            modelo = self._crear_modelo()
            if not modelo:
                raise ValueError("No hay datos bíblicos cargados.")
            self._imagenes_circulo.clear()
            self.modelo = modelo
            self.router.refrescar()
        except Exception as error:
            ArchivoLocalService._avisar(self.page, f"No se pudo iniciar el análisis: {error}", error=True)

    def _limpiar(self, e=None):
        self.selector_alcance.value = ALCANCE_BIBLIA
        self.selector_libro.value = self.libros[0] if self.libros else None
        self.selector_capitulo.value = "1"
        self.selector_versiculo.value = "1"
        self._actualizar_opciones(reiniciar_capitulo=True)
        self.modelo = None
        self.capturador = None
        self._imagenes_circulo.clear()
        self.router.refrescar()

    def _tamano_circulo(self):
        ancho = float(getattr(self.page, "width", 0) or 900)
        return max(250, min(760 if ancho >= 700 else 620, ancho - (340 if ancho >= 700 else 28)))

    def _circulo(self):
        lado = self._tamano_circulo()
        clave_imagen = (self.modelo.clave, round(lado))
        datos = self._imagenes_circulo.get(clave_imagen)
        if datos is None:
            datos = generar_png_circulo_nativo(self.modelo, round(lado * 2))
            self._imagenes_circulo[clave_imagen] = datos
        imagen = ft.Image(
            src=datos,
            width=lado,
            height=lado,
            fit=ft.BoxFit.CONTAIN,
            filter_quality=ft.FilterQuality.HIGH,
            anti_alias=True,
            semantics_label=f"Aro Arcoiris: {self.modelo.titulo}",
            error_content=ft.Text("No se pudo mostrar el círculo.", color=ft.Colors.RED_700),
        )
        centro = lado / 2
        radio_exterior = lado * 0.465
        radio_limite = radio_exterior * 0.76
        radio_hueco = radio_exterior * 0.23
        controles = [imagen]
        controles.extend(self._etiquetas_anillo(self.modelo.exterior, centro, (radio_limite + radio_exterior) / 2, lado))
        controles.extend(self._etiquetas_anillo(self.modelo.interior, centro, (radio_hueco + radio_limite) / 2, lado))
        controles.append(ft.Container(
            left=centro - radio_hueco * 0.92,
            top=centro - radio_hueco * 0.76,
            width=radio_hueco * 1.84,
            height=radio_hueco * 1.52,
            alignment=ft.Alignment(0, 0),
            content=ft.Column(
                spacing=max(1, lado * 0.004),
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(self.modelo.texto_centro_1, size=max(6, lado * 0.014), weight=ft.FontWeight.BOLD,
                            color=COLOR_CONTORNO, text_align=ft.TextAlign.CENTER, max_lines=2),
                    ft.Text(self.modelo.texto_centro_2, size=max(6, lado * 0.013), weight=ft.FontWeight.BOLD,
                            color=COLOR_CONTORNO, text_align=ft.TextAlign.CENTER, max_lines=2),
                    ft.Text(self.modelo.texto_centro_3, size=max(5, lado * 0.009),
                            color=COLOR_CONTORNO, text_align=ft.TextAlign.CENTER, max_lines=3),
                ],
            ),
        ))
        grafico = ft.Stack(width=lado, height=lado, controls=controles)
        return ft.Container(width=lado, height=lado, alignment=ft.Alignment(0, 0), content=grafico)

    @staticmethod
    def _etiquetas_anillo(anillo, centro, radio, lado):
        controles = []
        if anillo.secciones:
            cantidad = len(anillo.secciones)
            tamano = max(3.0, min(12.0, lado * 0.52 / max(35, cantidad * 0.62)))
            for seccion in anillo.secciones:
                angulo = math.radians(seccion.medio_grados)
                giro_grados = seccion.medio_grados % 360
                if 90 < giro_grados < 270:
                    giro_grados += 180
                ancho = max(16, len(seccion.etiqueta) * tamano * 0.72)
                controles.append(ft.Text(
                    seccion.etiqueta,
                    left=centro + radio * math.cos(angulo) - ancho / 2,
                    top=centro + radio * math.sin(angulo) - tamano * 0.8,
                    width=ancho,
                    size=tamano,
                    weight=ft.FontWeight.BOLD,
                    color=color_texto_para_digito(seccion.digito),
                    text_align=ft.TextAlign.CENTER,
                    max_lines=1,
                    rotate=ft.Rotate(angle=math.radians(giro_grados)),
                ))
        elif anillo.etiqueta_solida:
            tamano = max(6, lado * 0.014)
            ancho = max(28, len(anillo.etiqueta_solida) * tamano * 0.72)
            controles.append(ft.Text(
                anillo.etiqueta_solida,
                left=centro - ancho / 2,
                top=centro - radio - tamano * 0.8,
                width=ancho,
                size=tamano,
                weight=ft.FontWeight.BOLD,
                color=color_texto_para_digito(anillo.digito_solido),
                text_align=ft.TextAlign.CENTER,
                max_lines=1,
            ))
        return controles

    def _exportar_png(self, e=None):
        if not self.modelo:
            ArchivoLocalService._avisar(self.page, "Primero pulse Iniciar análisis.", error=True)
            return
        self.page.run_task(self._exportar_png_async)

    def _exportar_pdf(self, e=None):
        SelectorPdfAro(
            self.page,
            self.selector_alcance.value,
            self.selector_libro.value,
            self.selector_capitulo.value,
            self.selector_versiculo.value,
            self._iniciar_exportacion_pdf,
        ).mostrar()

    def _iniciar_exportacion_pdf(self, modelos):
        self.page.run_task(self._exportar_pdf_async, modelos)

    async def _capturar_resultado(self):
        if not self.capturador:
            raise RuntimeError("El resultado todavía no está listo.")
        datos = await self.capturador.capture(pixel_ratio=2)
        if not datos or not bytes(datos).startswith(b"\x89PNG"):
            raise RuntimeError("No se pudo capturar el resultado visible.")
        return bytes(datos)

    async def _guardar_directo(self, datos, nombre, extension, titulo):
        nombre_archivo = ArchivoLocalService._nombre_seguro(nombre, extension)
        await ArchivoLocalService._guardar_bytes_async(
            self.page, bytes(datos), nombre_archivo, extension, titulo,
        )

    async def _exportar_png_async(self):
        self.boton_png.disabled = True
        try:
            self.boton_png.update()
        except (RuntimeError, AssertionError):
            pass
        try:
            datos = await self._capturar_resultado()
            await self._guardar_directo(
                datos, f"Aro Arcoiris - {self.modelo.titulo}", "png", "Guardar Aro Arcoiris como PNG",
            )
        except Exception as error:
            ArchivoLocalService._avisar(self.page, f"No se pudo generar el PNG: {error}", error=True)
        finally:
            self.boton_png.disabled = False
            try:
                self.boton_png.update()
            except (RuntimeError, AssertionError):
                pass

    async def _exportar_pdf_async(self, modelos):
        self.boton_pdf.disabled = True
        try:
            self.boton_pdf.update()
        except (RuntimeError, AssertionError):
            pass
        try:
            datos = await asyncio.to_thread(generar_pdf_modelos_nativo, modelos)
            await self._guardar_directo(datos, "Aro Arcoiris", "pdf", "Guardar Aro Arcoiris como PDF")
        except Exception as error:
            ArchivoLocalService._avisar(self.page, f"No se pudo generar el PDF: {error}", error=True)
        finally:
            self.boton_pdf.disabled = False
            try:
                self.boton_pdf.update()
            except (RuntimeError, AssertionError):
                pass

    def obtener_vista(self):
        if not self.libros:
            return ft.Container(expand=True, alignment=ft.Alignment(0, 0), content=ft.Text("No hay datos bíblicos cargados."))
        alcance = self.selector_alcance.value
        self.selector_libro.visible = alcance != ALCANCE_BIBLIA
        self.selector_capitulo.visible = alcance in {ALCANCE_CAPITULO, ALCANCE_VERSICULO}
        self.selector_versiculo.visible = alcance == ALCANCE_VERSICULO
        self.boton_png.disabled = self.modelo is None
        self.boton_pdf.disabled = not self.libros
        selectores = ft.Row(wrap=True, spacing=10, run_spacing=10, controls=[
            ft.Container(width=240, content=self.selector_alcance), ft.Container(width=240, content=self.selector_libro),
            ft.Container(width=130, content=self.selector_capitulo), ft.Container(width=130, content=self.selector_versiculo),
        ])
        if self.modelo:
            contenido_exportable = ft.Container(bgcolor="#FFFDF8", padding=12, content=ft.Column(tight=True, spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text("Aro Arcoiris", size=28, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                    ft.Text(self.modelo.titulo, size=23, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, color=TEXTO_PRINCIPAL),
                    ft.Text(self.modelo.resumen, color=TEXTO_SECUNDARIO, text_align=ft.TextAlign.CENTER), self._circulo(),
                    ft.Text(f"Borde exterior: {self.modelo.exterior.nombre} · Interior: {self.modelo.interior.nombre}",
                            weight=ft.FontWeight.BOLD, color=COLOR_CONTORNO, text_align=ft.TextAlign.CENTER),
                    leyenda_nueve_colores(),
                ]))
            self.capturador = ft.Screenshot(content=contenido_exportable)
            bloque = self.capturador
        else:
            self.capturador = None
            bloque = ft.Container(
                bgcolor="#FFFDF8",
                padding=32,
                alignment=ft.Alignment(0, 0),
                content=ft.Column(
                    height=220,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.DONUT_LARGE, size=56, color=PURPURA_IOS),
                        ft.Text("El círculo todavía no fue generado.", size=20, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                        ft.Text("Seleccione las opciones y pulse “Iniciar análisis”.", color=TEXTO_SECUNDARIO, text_align=ft.TextAlign.CENTER),
                    ],
                ),
            )
        return ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                panel_moderno(ft.Column(spacing=12, controls=[
                    ft.Text("Aro Arcoiris", size=28, weight=ft.FontWeight.BOLD, color=TEXTO_PRINCIPAL),
                    ft.Text("Primero elija qué desea representar; luego seleccione un elemento.", color=TEXTO_SECUNDARIO),
                    selectores,
                    ft.Row(wrap=True, spacing=10, run_spacing=10, controls=[
                        self.boton_analizar,
                        self.boton_limpiar,
                        self.boton_png, self.boton_pdf,
                    ]),
                    ft.Text(
                        "Al descargar PDF podrá elegir uno o más libros, capítulos o versículos."
                        if self.modelo else "Inicie el análisis para ver el resultado; el PDF permite selección múltiple.",
                        color=TEXTO_SECUNDARIO,
                    ),
                ]), padding=16),
                bloque, ft.Container(height=10),
            ])
