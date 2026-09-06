import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from ui.sonidos import reproducir_resultado_8
from vistas.inicio import InicioView
from vistas.analizador_colores import AnalizadorColoresView
from services.codificador_service import CodificadorService


class SonidoResultadoTest(unittest.TestCase):
    def test_reutiliza_audio_y_no_repite(self):
        page = SimpleNamespace(services=[], update=MagicMock(), run_task=MagicMock())
        audio = MagicMock(play=AsyncMock())
        with patch("ui.sonidos.fa.Audio", return_value=audio) as crear:
            reproducir_resultado_8(page)
            page.run_task.assert_not_called()
            audio.play.assert_not_awaited()
            # Un segundo pedido mientras carga no duplica la reproduccion.
            reproducir_resultado_8(page)
            asyncio.run(crear.call_args.kwargs["on_loaded"](None))
            audio.play.assert_awaited_once()
            asyncio.run(crear.call_args.kwargs["on_loaded"](None))
            audio.play.assert_awaited_once()
            reproducir_resultado_8(page)
        crear.assert_called_once()
        self.assertEqual(len(page.services), 1)
        for llamada in page.run_task.call_args_list:
            asyncio.run(llamada.args[0]())
        self.assertEqual(audio.play.await_count, 2)
        audio.play.assert_awaited_with(position=0)

    def test_inicio_g_suena_una_vez_en_cada_nivel(self):
        for nivel in (1, 2, 3, 4):
            vista = InicioView.__new__(InicioView)
            vista.page = MagicMock()
            vista.responsive = SimpleNamespace(is_mobile=lambda: False)
            vista.router = SimpleNamespace(nivel=nivel, tiene_capacidad=lambda c: False)
            vista.codificador_service = CodificadorService.__new__(CodificadorService)
            vista.palabra_input = SimpleNamespace(value="g")
            vista.modo_codificacion = SimpleNamespace(value="texto_a_numeros")
            vista.mensaje_error = SimpleNamespace(visible=False)
            vista.mostrar_resultado = MagicMock()
            with patch("vistas.inicio.reproducir_resultado_8") as sonido, patch("vistas.inicio.ejecutar_demorado"):
                vista.codificar(None)
                sonido.assert_called_once_with(vista.page)
                vista.palabra_input.value = "a"
                vista.codificar(None)
                sonido.assert_called_once()

    def test_comparacion_suena_una_vez_sin_sonar_al_renderizar(self):
        vista = AnalizadorColoresView.__new__(AnalizadorColoresView)
        vista.page = MagicMock()
        vista.responsive = SimpleNamespace(is_mobile=lambda: False)
        vista.texto = SimpleNamespace(value="G")
        vista.diccionarios_seleccionados = ["uno", "dos"]
        vista._render_resultado = MagicMock()
        vista._preparar_entrada_texto = MagicMock()
        diccionarios = [{"id": i, "nombre": i, "valores": {"G": 8}} for i in ("uno", "dos")]
        with patch("vistas.analizador_colores.AlfabetosService.listar", return_value=diccionarios), patch("vistas.analizador_colores.guardar_historial"), patch("vistas.analizador_colores.reproducir_resultado_8") as sonido:
            vista.analizar()
            sonido.assert_called_once_with(vista.page)
            vista.texto.value = "GG"
            vista.analizar()
            sonido.assert_called_once()


if __name__ == "__main__":
    unittest.main()
