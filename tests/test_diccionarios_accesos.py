import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from router import Router
from services.alfabetos_service import AlfabetosService
from services.app_paths import AppPaths
from services.app_config_service import AppConfigService
from vistas.inicio import InicioView
from vistas.ajustes import AjustesView
from ui.sonidos import reproducir_resultado_8
from services.permisos_service import PermisosService


class CambiosTest(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        parche = patch.object(AppPaths, "CONFIG_APP", Path(self.temporal.name) / "config.json")
        parche.start()
        self.addCleanup(parche.stop)

    def test_eliminar_activo_refresca_inicio_y_motor(self):
        page = SimpleNamespace(on_resize=None, update=MagicMock())
        router = Router(page, nivel=4)
        inicio = InicioView(page, router)
        router.vistas["inicio"] = inicio
        ajustes = AjustesView(page, router)
        nuevo = AlfabetosService.guardar("Prueba", {"A": 99})
        inicio.on_enter()
        self.assertEqual(inicio.alfabeto_selector.value, nuevo["id"])
        ajustes.eliminar_alfabeto(nuevo)
        self.assertNotIn(nuevo["id"], [o.key for o in inicio.alfabeto_selector.options])
        self.assertEqual(inicio.alfabeto_selector.value, AlfabetosService.ID_BASE)
        self.assertNotEqual(inicio.motor.diccionario.get("A"), 99)

    def test_reentrada_actualiza_diccionario_no_activo(self):
        page = SimpleNamespace(on_resize=None, update=MagicMock())
        router = Router(page)
        nuevo = AlfabetosService.guardar("Temporal", {"A": 99})
        inicio = InicioView(page, router)
        AlfabetosService.seleccionar(AlfabetosService.ID_BASE)
        AlfabetosService.eliminar(nuevo["id"])
        inicio.on_enter()
        self.assertNotIn(nuevo["id"], [o.key for o in inicio.alfabeto_selector.options])

    def test_tiempo_y_preferencias_todos_los_niveles(self):
        for nivel in range(1, 5):
            router = Router(MagicMock(), nivel)
            self.assertTrue(router.puede_acceder("tiempo"))
            self.assertEqual(router.tiene_capacidad("tiempo_consultar"), nivel >= 3)
            vista = AjustesView(router.page, router)
            with patch.object(vista, "_preferencias", wraps=vista._preferencias) as preferencias:
                vista.obtener_vista()
                preferencias.assert_called_once()




    def test_mute_antes_de_cargar_audio(self):
        page = SimpleNamespace(services=[], update=MagicMock(), run_task=MagicMock())
        audio = MagicMock(play=AsyncMock())
        with patch("ui.sonidos.fa.Audio", return_value=audio) as crear:
            reproducir_resultado_8(page)
            AppConfigService.guardar_json(AppPaths.CONFIG_APP, {"resultado_8_muted": True})
            asyncio.run(crear.call_args.kwargs["on_loaded"](None))
            reproducir_resultado_8(page)
        audio.play.assert_not_awaited()
        page.run_task.assert_not_called()

    def test_accesos_antiguos_no_habilitan_niveles(self):
        AppConfigService.guardar_json(AppPaths.CONFIG_APP, {
            "niveles_autorizados": [1, 2, 3, 4],
            "niveles_autorizados_version": "2026-08-seguras",
        })
        with patch.object(PermisosService, "_niveles_sesion", None):
            self.assertEqual(PermisosService.niveles_autorizados(), set())

    def test_solo_guarda_nivel_con_clave_validada_y_casilla(self):
        with patch.object(PermisosService, "_niveles_sesion", set()), patch.object(PermisosService, "validar_clave", return_value=False):
            with self.assertRaises(ValueError):
                PermisosService.autorizar(4, "incorrecta", guardar=True)
            self.assertFalse(AppPaths.CONFIG_APP.exists())
        with patch.object(PermisosService, "_niveles_sesion", set()), patch.object(PermisosService, "validar_clave", return_value=True):
            PermisosService.autorizar(2, "validada")
            self.assertFalse(AppPaths.CONFIG_APP.exists())
            PermisosService.autorizar(2, "validada", guardar=True)
            self.assertEqual(PermisosService.niveles_autorizados(), {2})
            self.assertFalse(PermisosService.esta_autorizado(4))


if __name__ == "__main__":
    unittest.main()
