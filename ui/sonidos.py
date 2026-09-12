"""Sonidos de resultados, compartidos por las vistas de una misma pagina."""
import flet_audio as fa

from core.error_logger import registrar_error
from services.app_config_service import AppConfigService
from services.app_paths import AppPaths


def resultado_8_habilitado():
    datos = AppConfigService.leer_json(AppPaths.CONFIG_APP, {})
    return not (isinstance(datos, dict) and datos.get("resultado_8_muted", False))


def reproducir_resultado_8(page):
    """Una reproduccion por calculo, sin bucle ni reproductores superpuestos."""
    try:
        if not resultado_8_habilitado():
            return
        audio = getattr(page, "_audio_resultado_8", None)
        if audio is None:
            estado = {"cargado": False, "pendiente": True}

            async def al_cargar(e):
                estado["cargado"] = True
                if estado["pendiente"] and resultado_8_habilitado():
                    estado["pendiente"] = False
                    try:
                        await audio.play(position=0)
                    except Exception as error:
                        registrar_error("sonidos.resultado_8", error)

            audio = fa.Audio(
                src="resultado_8.wav", autoplay=False,
                release_mode=fa.ReleaseMode.STOP,
                on_loaded=al_cargar,
            )
            page._estado_audio_resultado_8 = estado
            page.services.append(audio)
            page._audio_resultado_8 = audio
            page.update()
            return

        estado = page._estado_audio_resultado_8
        if not estado["cargado"]:
            estado["pendiente"] = True
            return

        async def reproducir():
            try:
                if resultado_8_habilitado():
                    await audio.play(position=0)
            except Exception as error:
                registrar_error("sonidos.resultado_8", error)

        page.run_task(reproducir)
    except Exception as error:
        registrar_error("sonidos.preparar_resultado_8", error)
