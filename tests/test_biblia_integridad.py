"""Regresiones de lectura y persistencia; no utiliza los datos del usuario."""
import json
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

# Las rutas se resuelven durante los imports de la aplicacion.
_storage = tempfile.TemporaryDirectory()
os.environ["FLET_APP_STORAGE_DATA"] = _storage.name

from logica.biblia import (
    buscar_texto, cargar_comentarios, cargar_resaltados,
    crear_indice_busqueda, guardar_comentarios, guardar_resaltados,
)
from services.app_config_service import AppConfigService
from services.biblia_service import BibliaService


class IntegridadBibliaTest(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / "datos.json"
        self.libros = [{
            "nombre": "Prueba", "capitulos": [["amor y paz", "ultimo"], ["final"]],
            "secciones": [[{"titulo": "Inicio"}], [{"titulo": "Fin"}]],
            "parrafos": [[1], [2]],
        }]

    def test_indices_invalidos_no_devuelven_final(self):
        with patch.object(BibliaService, "libro_por_nombre", return_value=self.libros[0]):
            for indice in (0, -1, -2, "0", None, "invalido", 999):
                for metodo in ("obtener_capitulo", "obtener_secciones", "obtener_parrafos"):
                    self.assertEqual(getattr(BibliaService, metodo)("Prueba", indice), [])
                self.assertEqual(BibliaService.obtener_versiculo("Prueba", 1, indice), "")
            self.assertEqual(BibliaService.obtener_versiculo("Prueba", 1, 2), "ultimo")

    def test_resaltados_danados_o_tipo_incorrecto(self):
        for contenido in ('{', 'null', '[]', '42', '"texto"'):
            self.ruta.write_text(contenido, encoding="utf-8")
            self.assertEqual(cargar_resaltados(self.ruta), {})
            self.assertEqual(cargar_comentarios(self.ruta), {})

    def test_guardados_conservan_texto_y_referencias(self):
        datos = {"Prueba|1|1": {"texto": "Anotación", "referencias": ["Juan 3:16"]}}
        for guardar, cargar in ((guardar_resaltados, cargar_resaltados),
                                (guardar_comentarios, cargar_comentarios)):
            guardar(datos, self.ruta)
            self.assertEqual(cargar(self.ruta), datos)

    def test_escrituras_concurrentes_generan_json_completo(self):
        def guardar(numero):
            AppConfigService.guardar_json(self.ruta, {"numero": numero, "texto": "ñ" * 1000})
        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(guardar, range(60)))
        datos = json.loads(self.ruta.read_text(encoding="utf-8"))
        self.assertIn(datos["numero"], range(60))
        self.assertEqual(datos["texto"], "ñ" * 1000)
        self.assertEqual(list(self.ruta.parent.glob("*.tmp")), [])

    def test_fallo_de_reemplazo_conserva_original_y_limpia_temporal(self):
        self.ruta.write_text('{"original": true}', encoding="utf-8")
        with patch.object(Path, "replace", side_effect=OSError("fallo simulado")):
            with self.assertRaises(OSError):
                AppConfigService.guardar_json(self.ruta, {"nuevo": True})
        self.assertEqual(json.loads(self.ruta.read_text()), {"original": True})
        self.assertEqual(list(self.ruta.parent.glob("*.tmp")), [])

    def test_ultima_lectura_y_historial_toleran_tipos_incorrectos(self):
        with patch("services.biblia_service.ULTIMA_LECTURA_ARCHIVO", self.ruta):
            self.ruta.write_text('[]', encoding="utf-8")
            self.assertEqual(BibliaService.cargar_ultima_lectura(), {})
        with patch("services.biblia_service.HISTORIAL_REFERENCIAS_ARCHIVO", self.ruta):
            self.ruta.write_text('[null, 4, {"referencia": "Juan 3:16"}]', encoding="utf-8")
            self.assertEqual(BibliaService.cargar_historial_referencias(), [{"referencia": "Juan 3:16"}])

    def test_carga_concurrente_y_refresco_de_indices(self):
        class ServicioAislado(BibliaService):
            _cache_libros = None
            _cache_libros_por_nombre = None
            _cache_indice_busqueda = None
        with patch("services.biblia_service.cargar_biblia", return_value=self.libros) as cargar:
            with ThreadPoolExecutor(max_workers=8) as executor:
                indices = list(executor.map(lambda _: ServicioAislado.indice_busqueda(), range(30)))
            cargar.assert_called_once()
            self.assertTrue(all(indice is indices[0] for indice in indices))
            ServicioAislado.libro_por_nombre("Prueba")
            ServicioAislado.libros(refrescar=True)
            self.assertIsNot(ServicioAislado.indice_busqueda(), indices[0])
            self.assertEqual(ServicioAislado.libro_por_nombre("Prueba"), self.libros[0])

    def test_busqueda_indexada_y_directa_equivalentes(self):
        indice = crear_indice_busqueda(self.libros)
        for consulta in ("amor", "AMÓR", "final", "paz", "", "19", "diecinueve", "ausente"):
            self.assertEqual(buscar_texto(self.libros, consulta, indice), buscar_texto(self.libros, consulta))
        self.assertEqual(len(buscar_texto(self.libros, "amor", indice)), 1)


if __name__ == "__main__":
    unittest.main()
