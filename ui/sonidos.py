"""Sonidos de resultados, compartidos por las vistas de una misma pagina."""
import flet_audio as fa

from core.error_logger import registrar_error


def reproducir_resultado_8(page):
    """Una reproduccion por calculo, sin bucle ni reproductores superpuestos."""
    try:
        audio = getattr(page, "_audio_resultado_8", None)
        if audio is None:
            estado = {"cargado": False, "pendiente": True}

            async def al_cargar(e):
                estado["cargado"] = True
                if estado["pendiente"]:
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
                await audio.play(position=0)
            except Exception as error:
                registrar_error("sonidos.resultado_8", error)

        page.run_task(reproducir)
    except Exception as error:
        registrar_error("sonidos.preparar_resultado_8", error)
