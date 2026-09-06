"""Casos de diccionarios y continuidad incremental de lectura."""
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

_storage = tempfile.TemporaryDirectory()
os.environ["FLET_APP_STORAGE_DATA"] = _storage.name

import flet as ft
from logica.analizador_colores import analizar_codigo_visual, tokenizar, exportar_pdf_colores, resumen_colores_informe
from pathlib import Path
from router import Router
from vistas.analizador_colores import AnalizadorColoresView
from vistas.biblia import BibliaView


def pagina(ancho=390):
    page = MagicMock(width=ancho, height=850, web=False, platform=ft.PagePlatform.WINDOWS)
    page.window = SimpleNamespace(width=ancho, height=850)
    page.overlay = []
    page.services = []
    return page


class CodicolorTest(unittest.TestCase):
    def test_contador_respeta_caracteres_del_diccionario(self):
        self.assertEqual(analizar_codigo_visual("hola matias")["cantidad_letras"], 10)
        self.assertEqual(analizar_codigo_visual("hola matias")["cantidad_palabras"], 2)
        for valores, esperado in (({"CH": 999, "C": 2, "H": 3}, 1), ({"C": 2, "H": 3}, 2), ({"X": 1}, 2)):
            r = analizar_codigo_visual("ch 19", valores)
            self.assertEqual(r["cantidad_letras"], esperado)
            self.assertEqual(r["cantidad_palabras"], 1)

    def test_resumen_colores_suma_cantidades(self):
        r = analizar_codigo_visual("AB", {"A": 10, "B": 20})
        conteos = resumen_colores_informe(r)
        self.assertEqual(sum(conteos["Texto"].values()), 2)
        for digito in range(10):
            self.assertEqual(conteos["Total"][digito], sum(conteos[e][digito] for e in ("Texto", "Primario", "Secundario", "Terciario")))

    def test_pdf_completo_sin_paginas_de_detalle(self):
        resultados = []
        for nombre, valores in (("Biblico", {"CH": 4}), ("Americano", {"C": 3, "H": 8})):
            r = analizar_codigo_visual("CH", valores)
            r["diccionario_nombre"] = nombre
            resultados.append(r)
        with tempfile.TemporaryDirectory() as carpeta:
            for formato, paginas in (("pc", 4), ("celular", 8)):
                ruta = Path(carpeta) / f"{formato}.pdf"
                exportar_pdf_colores(resultados[0], archivo=ruta, formato=formato, resultados=resultados)
                contenido = ruta.read_bytes()
                self.assertIn(f"/Count {paginas}".encode(), contenido)
                self.assertIn(b"Biblico", contenido)
                self.assertIn(b"Americano", contenido)
                self.assertNotIn(b"DETALLE DEL", contenido)
                self.assertEqual(contenido.count(b"RESUMEN DE COLORES"), 2)
                self.assertIn(b"Letras: 1", contenido)
                self.assertIn(b"Letras: 2", contenido)

    def test_analisis_apilados_y_acciones_por_diccionario(self):
        for ancho in (390, 1280):
            page = pagina(ancho)
            vista = AnalizadorColoresView(page, Router(page, 4))
            resultados = []
            for nombre, valor in (("Biblico", 1), ("Americano", 10), ("Otro", 100)):
                resultado = analizar_codigo_visual("AA", {"A": valor})
                resultado["diccionario_nombre"] = nombre
                resultados.append(resultado)
            vista.resultados_comparacion = resultados
            vista.resultado = resultados[0]
            vista._render_resultado()
            secciones = vista.panel_resultado.controls[1:]
            self.assertEqual(len(secciones), 3)
            for seccion, resultado in zip(secciones, resultados):
                encabezado = seccion.controls[0].content.controls[0].value
                self.assertIn(resultado["diccionario_nombre"], encabezado)
                self.assertEqual(len(seccion.controls), 6)
                for indice, metodo in enumerate(("guardar_resultado", "abrir_opciones_pdf", "abrir_opciones_copiado")):
                    with patch.object(vista, metodo) as accion:
                        seccion.controls[4].controls[indice].on_click(None)
                        accion.assert_called_once_with(None)
                        self.assertIs(vista.resultado, resultado)
            # Cambiar la escala o refrescar conserva todos los analisis.
            vista._render_resultado()
            self.assertEqual(len(vista.panel_resultado.controls), 4)

    def test_suma_confirmada(self):
        resultado = analizar_codigo_visual("AB", {"A": 10, "B": 20})
        self.assertEqual(resultado["total_codigo"], 30)
        self.assertEqual(resultado["resultado_final"], 3)
        # Primario visible: 30, 3+0=3, final 3 -> 12; reducidos 1+2 -> 3.
        self.assertEqual(resultado["suma_resultados"], 3 + 12 + 3)

    def test_compuestos_solo_si_existen_y_prioriza_el_mas_largo(self):
        self.assertEqual(tokenizar("CH LL", {"C": 1, "H": 2, "L": 3}), ["C", "H", "L", "L"])
        self.assertEqual(tokenizar("CH LL"), ["CH", "LL"])
        self.assertEqual(tokenizar("ABC", {"A": 1, "AB": 4, "ABC": 8}), ["ABC"])

    def test_hebreo_griego_y_digitos_literales(self):
        for texto, valores, esperado in (("אב 19", {"א": 10, "ב": 20}, 40),
                                         ("άλφα", {"Α": 5, "Λ": 10, "Φ": 20}, 40)):
            self.assertEqual(analizar_codigo_visual(texto, valores)["total_codigo"], esperado)

    def test_comparar_personalizados_y_copiado(self):
        page = pagina()
        vista = AnalizadorColoresView(page, Router(page, 4))
        diccionarios = [{"id": str(i), "nombre": f"Personalizado {i}", "valores": {"A": i}}
                        for i in (1, 10, 100)]
        vista.diccionarios_seleccionados = ["1", "10", "100"]
        vista.texto.value = "AA"
        with patch("vistas.analizador_colores.AlfabetosService.listar", return_value=diccionarios), \
             patch("vistas.analizador_colores.guardar_historial"):
            vista.analizar()
            vista.abrir_diccionarios()
        self.assertEqual([r["total_codigo"] for r in vista.resultados_comparacion], [2, 20, 200])
        vista.resultado = vista.resultados_comparacion[2]
        self.assertIn("Suma de Resultados:", vista._texto_resultados_copiado({}))
        self.assertEqual(vista._resultado_para_guardar()["diccionario_valores"], {"A": 100})
        vista.limpiar()
        self.assertEqual(vista.resultados_comparacion, [])


class LecturaContinuaTest(unittest.TestCase):
    def test_anade_sin_reemplazar_contenido_previo(self):
        for ancho in (390, 1280):
            page = pagina(ancho)
            vista = BibliaView(page, Router(page, 4))
            vista.modo_vista = "Libro"
            vista.libro_actual = vista.libros[0]["nombre"]
            vista._render_lectura()
            lista = vista.panel_lectura
            contenido = vista._contenido_libro_completo
            previos = list(contenido.controls)
            siguiente = vista._siguiente_capitulo_libro
            evento = SimpleNamespace(pixels=10000, viewport_dimension=800, max_scroll_extent=11000)
            vista._al_desplazar_libro_completo(evento)
            self.assertIs(vista.panel_lectura, lista)
            self.assertIs(lista.controls[0], contenido)
            self.assertTrue(all(a is b for a, b in zip(previos, contenido.controls)))
            self.assertEqual(len(contenido.controls), len(previos) + 1)
            self.assertEqual(vista._siguiente_capitulo_libro, siguiente + 1)
            self.assertFalse(lista.auto_scroll)

    def test_no_carga_lejos_del_final_o_fuera_del_modo_libro(self):
        page = pagina()
        vista = BibliaView(page, Router(page, 4))
        vista.modo_vista = "Libro"
        with patch.object(vista, "_agregar_tramo_libro_completo") as agregar:
            vista._al_desplazar_libro_completo(SimpleNamespace(pixels=0, viewport_dimension=800, max_scroll_extent=10000))
            vista.modo_vista = "Versiculos"
            vista._al_desplazar_libro_completo(SimpleNamespace(pixels=10000, viewport_dimension=800, max_scroll_extent=10000))
            agregar.assert_not_called()


if __name__ == "__main__":
    unittest.main()
