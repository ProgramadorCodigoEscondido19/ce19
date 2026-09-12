import asyncio
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from PIL import Image

from logica.circulo_biblico import crear_modelo_aro, reducir_a_un_digito
from services.biblia_service import BibliaService
from services.archivo_local_service import ArchivoLocalService
from services.exportador_circulo_biblico import generar_png_aro
from services.rutas_service import RutasService
from vistas.circulo_biblico import CirculoBiblicoView


class CirculoBiblicoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.genesis = crear_modelo_aro(BibliaService.libro_por_nombre("Génesis"))
        cls.apocalipsis = crear_modelo_aro(BibliaService.libro_por_nombre("Apocalipsis"))

    def test_reduccion_repetida(self):
        self.assertEqual(reducir_a_un_digito(19), 1)
        self.assertEqual(reducir_a_un_digito(29), 2)
        self.assertEqual(reducir_a_un_digito(67), 4)

    def test_divisiones_reales(self):
        self.assertEqual(self.genesis.cantidad_capitulos, 50)
        self.assertEqual(len(self.genesis.secciones), 50)
        self.assertEqual(self.apocalipsis.cantidad_capitulos, 22)
        self.assertEqual(len(self.apocalipsis.secciones), 22)

    def test_genesis_1_y_24(self):
        c1 = self.genesis.secciones[0]
        self.assertEqual((c1.digito_capitulo, c1.cantidad_versiculos, c1.digito_versiculos), (1, 31, 4))
        self.assertEqual((c1.color_capitulo, c1.color_versiculos), ("#795548", "#FDD835"))
        c24 = self.genesis.secciones[23]
        self.assertEqual((c24.digito_capitulo, c24.cantidad_versiculos, c24.digito_versiculos), (6, 67, 4))
        self.assertEqual((c24.color_capitulo, c24.color_versiculos), ("#003BB1", "#FDD835"))

    def test_apocalipsis_1_y_22(self):
        c1 = self.apocalipsis.secciones[0]
        self.assertEqual((c1.digito_capitulo, c1.cantidad_versiculos, c1.digito_versiculos), (1, 20, 2))
        self.assertEqual((c1.color_capitulo, c1.color_versiculos), ("#795548", "#E53935"))
        c22 = self.apocalipsis.secciones[21]
        self.assertEqual((c22.digito_capitulo, c22.cantidad_versiculos, c22.digito_versiculos), (4, 21, 3))
        self.assertEqual((c22.color_capitulo, c22.color_versiculos), ("#FDD835", "#FB8C00"))

    def test_orientacion_horaria(self):
        primera = self.genesis.secciones[0]
        segunda = self.genesis.secciones[1]
        self.assertEqual(primera.inicio_grados, -90.0)
        self.assertGreater(segunda.inicio_grados, primera.inicio_grados)
        self.assertAlmostEqual(primera.fin_grados, segunda.inicio_grados)

    def test_exportacion_png(self):
        datos = generar_png_aro(self.apocalipsis, lado=1000)
        imagen = Image.open(io.BytesIO(datos))
        self.assertEqual(imagen.format, "PNG")
        self.assertEqual(imagen.size, (1000, 1420))
        self.assertGreater(len(datos), 50_000)

    def test_guardado_png_en_ruta_windows(self):
        datos = generar_png_aro(self.apocalipsis, lado=1000)
        with tempfile.TemporaryDirectory() as carpeta:
            destino = Path(carpeta) / "aro_apocalipsis.png"
            picker = SimpleNamespace(save_file=AsyncMock(return_value=str(destino)))
            page = SimpleNamespace(_ce19_file_picker=picker, update=MagicMock(), snack_bar=None, platform=None)
            asyncio.run(
                ArchivoLocalService._guardar_bytes_async(
                    page,
                    datos,
                    destino.name,
                    "png",
                    "Guardar prueba",
                )
            )
            self.assertTrue(destino.is_file())
            with Image.open(destino) as imagen:
                self.assertEqual(imagen.format, "PNG")
                self.assertEqual(imagen.size, (1000, 1420))

    def test_ruta_y_construccion_responsive(self):
        self.assertTrue(RutasService.existe("aro_arcoiris"))
        page = SimpleNamespace(width=390, services=[], run_task=MagicMock(), update=MagicMock())
        router = SimpleNamespace(refrescar=MagicMock(), navegar=MagicMock())
        vista = CirculoBiblicoView(page, router)
        self.assertLessEqual(vista._tamano_circulo(), page.width)
        self.assertIsNotNone(vista.obtener_vista())
        page.width = 1280
        self.assertEqual(vista._tamano_circulo(), 720)
        self.assertIsNotNone(vista.obtener_vista())

    def test_exportacion_se_programa_sin_bloquear(self):
        page = SimpleNamespace(width=390, services=[], run_task=MagicMock(), update=MagicMock())
        router = SimpleNamespace(refrescar=MagicMock(), navegar=MagicMock())
        vista = CirculoBiblicoView(page, router)
        vista._exportar()
        page.run_task.assert_called_once()
        self.assertEqual(page.run_task.call_args.args[0], vista._exportar_async)
        self.assertTrue(vista.boton_exportar.disabled)


if __name__ == "__main__":
    unittest.main()
