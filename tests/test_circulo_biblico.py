import io
import re
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from PIL import Image

from logica.circulo_biblico import reducir_a_un_digito
from services.biblia_service import BibliaService
from services.circulo_biblico_service import CirculoBiblicoService
from services.exportador_circulo_biblico import generar_pdf_aros, generar_png_aro
from services.rutas_service import RutasService
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
        self.assertEqual(len(self.biblia.interior.secciones), 66)
        self.assertEqual(self.biblia.interior.secciones[0].valor, 50)
        self.assertEqual(self.biblia.interior.secciones[0].color, "#43A047")

    def test_libro_divide_numero_de_libro_y_capitulos(self):
        self.assertEqual(len(self.genesis.exterior.secciones), 1)
        self.assertEqual(len(self.genesis.interior.secciones), 50)
        salmos = CirculoBiblicoService.modelo_libro("Salmos")
        self.assertEqual(len(salmos.exterior.secciones), 19)
        self.assertEqual(len(salmos.interior.secciones), 150)

    def test_capitulo_divide_capitulos_y_versiculos(self):
        self.assertEqual((len(self.genesis_1.exterior.secciones), len(self.genesis_1.interior.secciones)), (50, 31))
        self.assertEqual((len(self.genesis_24.exterior.secciones), len(self.genesis_24.interior.secciones)), (50, 67))
        self.assertEqual((len(self.apocalipsis_1.exterior.secciones), len(self.apocalipsis_1.interior.secciones)), (22, 20))
        self.assertEqual((len(self.apocalipsis_22.exterior.secciones), len(self.apocalipsis_22.interior.secciones)), (22, 21))

    def test_colores_de_sectores(self):
        self.assertEqual(self.genesis_1.exterior.secciones[0].color, "#795548")
        self.assertEqual(self.genesis_24.exterior.secciones[23].color, "#003BB1")
        self.assertEqual(self.genesis_1.interior.secciones[30].color, "#FDD835")
        self.assertEqual(self.genesis_24.interior.secciones[66].color, "#FDD835")
        self.assertEqual(self.apocalipsis_1.interior.secciones[19].color, "#E53935")
        self.assertEqual(self.apocalipsis_22.interior.secciones[20].color, "#FB8C00")

    def test_versiculo_exterior_e_interior_solido(self):
        modelo = CirculoBiblicoService.modelo_versiculo("Génesis", 1, 16)
        self.assertEqual(len(modelo.exterior.secciones), 16)
        self.assertFalse(modelo.interior.secciones)
        self.assertTrue(modelo.interior.color_solido)
        self.assertIn("suma del texto", modelo.resumen)

    def test_orientacion_independiente(self):
        for anillo in (self.genesis_1.exterior, self.genesis_1.interior):
            self.assertEqual(anillo.secciones[0].inicio_grados, -90.0)
            self.assertGreater(anillo.secciones[1].inicio_grados, anillo.secciones[0].inicio_grados)
            self.assertAlmostEqual(anillo.secciones[0].fin_grados, anillo.secciones[1].inicio_grados)

    def test_exportacion_png_y_pdf_multipagina(self):
        png = generar_png_aro(self.genesis_1, lado=1000)
        with Image.open(io.BytesIO(png)) as imagen:
            self.assertEqual((imagen.format, imagen.size), ("PNG", (1000, 1250)))
        pdf = generar_pdf_aros([self.genesis_1, self.apocalipsis_22], lado=1000)
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertEqual(len(re.findall(rb"/Type /Page\b", pdf)), 2)

    def test_ruta_vista_responsive_y_cola(self):
        self.assertTrue(RutasService.existe("aro_arcoiris"))
        page = SimpleNamespace(width=390, services=[], run_task=MagicMock(), update=MagicMock())
        router = SimpleNamespace(refrescar=MagicMock(), navegar=MagicMock())
        vista = CirculoBiblicoView(page, router)
        self.assertLessEqual(vista._tamano_circulo(), page.width)
        self.assertIsNotNone(vista.obtener_vista())
        vista._agregar()
        self.assertEqual(len(vista.cola), 1)
        vista._agregar()
        self.assertEqual(len(vista.cola), 1)
        page.width = 1280
        self.assertEqual(vista._tamano_circulo(), 760)

    def test_exportacion_se_programa_sin_bloquear(self):
        page = SimpleNamespace(width=390, services=[], run_task=MagicMock(), update=MagicMock())
        router = SimpleNamespace(refrescar=MagicMock(), navegar=MagicMock())
        vista = CirculoBiblicoView(page, router)
        vista._exportar_pdf()
        page.run_task.assert_called_once()
        self.assertEqual(page.run_task.call_args.args[0], vista._exportar_async)


if __name__ == "__main__":
    unittest.main()
