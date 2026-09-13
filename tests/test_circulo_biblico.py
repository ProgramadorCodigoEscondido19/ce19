import re
import struct
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

import flet as ft

from logica.circulo_biblico import reducir_a_un_digito
from services.biblia_service import BibliaService
from services.circulo_biblico_service import CirculoBiblicoService
from services.exportador_circulo_biblico import (
    MULTIPLICADOR_BORDE_SUMA, generar_pdf_modelos_nativo, generar_png_circulo_nativo,
)
from services.rutas_service import RutasService
from ui.selector_pdf_arcoiris import SelectorPdfAro
from vistas.circulo_biblico import CirculoBiblicoView


class CirculoBiblicoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.biblia = CirculoBiblicoService.modelo_biblia()
        cls.genesis = CirculoBiblicoService.modelo_libro("Génesis")
        cls.genesis_1 = CirculoBiblicoService.modelo_capitulo("Génesis", 1)
        cls.genesis_24 = CirculoBiblicoService.modelo_capitulo("Génesis", 24)
        cls.apocalipsis_1 = CirculoBiblicoService.modelo_capitulo("Apocalipsis", 1)
        cls.apocalipsis_22 = CirculoBiblicoService.modelo_capitulo("Apocalipsis", 22)

    def test_reduccion_repetida(self):
        self.assertEqual((reducir_a_un_digito(19), reducir_a_un_digito(29), reducir_a_un_digito(67)), (1, 2, 4))

    def test_biblia_completa(self):
        self.assertEqual(len(BibliaService.libros()), 66)
        self.assertEqual(self.biblia.exterior.color_solido, "#FB8C00")
        self.assertEqual(self.biblia.exterior.color_borde, "#FB8C00")
        self.assertEqual(self.biblia.interior.color_borde, "#FB8C00")
        self.assertEqual(len(self.biblia.interior.secciones), 66)
        self.assertEqual(self.biblia.interior.secciones[0].valor, 1)
        self.assertEqual(self.biblia.interior.secciones[0].color, "#795548")
        self.assertEqual(self.biblia.interior.secciones[1].color, "#E53935")

    def test_libro_divide_numero_de_libro_y_capitulos(self):
        self.assertEqual(len(self.genesis.exterior.secciones), 1)
        self.assertEqual(len(self.genesis.interior.secciones), 50)
        self.assertEqual(self.genesis.exterior.color_borde, "#795548")
        self.assertEqual(self.genesis.interior.color_borde, "#43A047")
        salmos = CirculoBiblicoService.modelo_libro("Salmos")
        self.assertEqual(len(salmos.exterior.secciones), 19)
        self.assertEqual(len(salmos.interior.secciones), 150)

    def test_capitulo_divide_capitulos_y_versiculos(self):
        self.assertEqual((len(self.genesis_1.exterior.secciones), len(self.genesis_1.interior.secciones)), (1, 31))
        self.assertEqual((len(self.genesis_24.exterior.secciones), len(self.genesis_24.interior.secciones)), (24, 67))
        self.assertEqual((len(self.apocalipsis_1.exterior.secciones), len(self.apocalipsis_1.interior.secciones)), (1, 20))
        self.assertEqual((len(self.apocalipsis_22.exterior.secciones), len(self.apocalipsis_22.interior.secciones)), (22, 21))
        self.assertEqual(self.genesis_24.exterior.color_borde, "#43A047")
        self.assertEqual(self.genesis_24.interior.color_borde, "#FDD835")

    def test_colores_de_sectores(self):
        self.assertEqual(self.genesis_1.exterior.secciones[0].color, "#795548")
        self.assertEqual(self.genesis_24.exterior.secciones[23].color, "#003BB1")
        self.assertEqual(self.genesis_1.interior.secciones[30].color, "#FDD835")
        self.assertEqual(self.genesis_24.interior.secciones[66].color, "#FDD835")
        self.assertEqual(self.apocalipsis_1.interior.secciones[19].color, "#E53935")
        self.assertEqual(self.apocalipsis_22.interior.secciones[20].color, "#FB8C00")

    def test_versiculo_exterior_y_cifras_interiores(self):
        modelo = CirculoBiblicoService.modelo_versiculo("Génesis", 1, 16)
        self.assertEqual(len(modelo.exterior.secciones), 16)
        self.assertNotEqual(len(modelo.exterior.secciones), CirculoBiblicoService.cantidad_versiculos("Génesis", 1))
        self.assertEqual(modelo.exterior.secciones[-1].etiqueta, "V16")
        suma = int(modelo.resumen.split("suma del texto: ", 1)[1].split(" ", 1)[0])
        self.assertEqual([seccion.valor for seccion in modelo.interior.secciones], [int(cifra) for cifra in str(suma)])
        self.assertFalse(modelo.interior.color_solido)
        self.assertIn("suma del texto", modelo.resumen)

        genesis_3_4 = CirculoBiblicoService.modelo_versiculo("Génesis", 3, 4)
        self.assertEqual(genesis_3_4.exterior.color_borde, "#FDD835")
        self.assertEqual(MULTIPLICADOR_BORDE_SUMA, 4)

    def test_orientacion_independiente(self):
        for anillo in (self.genesis_24.exterior, self.genesis_1.interior):
            self.assertEqual(anillo.secciones[0].inicio_grados, -90.0)
            self.assertGreater(anillo.secciones[1].inicio_grados, anillo.secciones[0].inicio_grados)
            self.assertAlmostEqual(anillo.secciones[0].fin_grados, anillo.secciones[1].inicio_grados)

    def test_exportacion_png_y_pdf_multipagina(self):
        png_nativo = generar_png_circulo_nativo(self.genesis_1, lado=500)
        self.assertTrue(png_nativo.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(struct.unpack(">II", png_nativo[16:24]), (500, 500))
        pdf_modelos = generar_pdf_modelos_nativo([self.genesis_1, self.apocalipsis_22], lado=700)
        self.assertTrue(pdf_modelos.startswith(b"%PDF"))
        self.assertEqual(len(re.findall(rb"/Type /Page\b", pdf_modelos)), 2)

    def test_ruta_vista_responsive(self):
        self.assertTrue(RutasService.existe("aro_arcoiris"))
        page = SimpleNamespace(width=390, services=[], run_task=MagicMock(), update=MagicMock())
        router = SimpleNamespace(refrescar=MagicMock(), navegar=MagicMock())
        vista = CirculoBiblicoView(page, router)
        self.assertLessEqual(vista._tamano_circulo(), page.width)
        control = vista.obtener_vista()
        self.assertIsNotNone(control)
        self.assertIn("Iniciar análisis", repr(control))
        self.assertNotIn("Volver", repr(control))
        self.assertIsNone(vista.modelo)
        self.assertTrue(vista.boton_png.disabled)
        self.assertFalse(vista.boton_pdf.disabled)
        vista._analizar()
        self.assertIsNotNone(vista.modelo)
        vista.obtener_vista()
        grafico = vista._circulo().content
        self.assertIsInstance(grafico, ft.Stack)
        self.assertIsInstance(grafico.controls[0], ft.Image)
        self.assertTrue(grafico.controls[0].src.startswith(b"\x89PNG"))
        self.assertTrue(any(getattr(control, "rotate", None) for control in grafico.controls[1:]))
        self.assertFalse(vista.boton_png.disabled)
        self.assertFalse(vista.boton_pdf.disabled)
        self.assertNotIn("Agregar otro círculo", repr(vista.obtener_vista()))
        vista.selector_alcance.value = "versiculo"
        vista._limpiar()
        self.assertIsNone(vista.modelo)
        self.assertEqual(vista.selector_alcance.value, "biblia")
        self.assertEqual(vista.selector_capitulo.value, "1")
        page.width = 1280
        self.assertEqual(vista._tamano_circulo(), 760)

    def test_exportacion_se_programa_sin_bloquear(self):
        page = SimpleNamespace(width=390, services=[], run_task=MagicMock(), update=MagicMock())
        router = SimpleNamespace(refrescar=MagicMock(), navegar=MagicMock())
        vista = CirculoBiblicoView(page, router)
        vista._analizar()
        vista._iniciar_exportacion_pdf([vista.modelo])
        page.run_task.assert_called_once()
        self.assertEqual(page.run_task.call_args.args[0], vista._exportar_pdf_async)

    def test_selector_pdf_admite_varios_capitulos(self):
        page = SimpleNamespace(update=MagicMock())
        confirmar = MagicMock()
        selector = SelectorPdfAro(page, "capitulo", "Génesis", 1, 1, confirmar)
        selector.lista.controls[0].value = True
        selector.lista.controls[1].value = True
        selector._confirmar()
        modelos = confirmar.call_args.args[0]
        self.assertEqual([modelo.clave for modelo in modelos], ["capitulo-Génesis-1", "capitulo-Génesis-2"])


if __name__ == "__main__":
    unittest.main()
