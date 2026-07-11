import asyncio
import sys
import unicodedata
from pathlib import Path

import flet as ft

# Permite ejecutar main.py desde la raíz del proyecto sin perder imports.
RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from logica.biblia import cargar_biblia
from ui.tema import DORADO, PURPURA_INICIAL

try:
    import flet_audio as fa
except Exception:
    fa = None


FONDO_INTRO_PC = "intro_pc.png"
INTRO_AUDIO = "santo_santo_intro_loop.mp3"


def _normalizar(texto):
    limpio = unicodedata.normalize("NFD", texto or "")
    limpio = "".join(c for c in limpio if unicodedata.category(c) != "Mn")
    return limpio.upper()


def _obtener_versiculo(libros, libro_buscado, capitulo, versiculo):
    buscado = _normalizar(libro_buscado)

    for libro in libros:
        if _normalizar(libro.get("nombre")) != buscado:
            continue

        try:
            return libro["capitulos"][capitulo - 1][versiculo - 1]
        except (IndexError, KeyError, TypeError):
            return ""

    return ""


def _seguro_update(control):
    try:
        control.update()
    except (RuntimeError, AssertionError, AttributeError):
        pass


def construir_intro(page, on_ingresar):
    ventana = getattr(page, "window", None)
    ancho = getattr(page, "width", None) or getattr(ventana, "width", None) or 1100
    alto = getattr(page, "height", None) or getattr(ventana, "height", None) or 720
    es_movil = ancho < 700

    libros = cargar_biblia()
    apocalipsis = _obtener_versiculo(libros, "Apocalipsis", 13, 18)
    romanos = _obtener_versiculo(libros, "Romanos", 10, 9)

    estado = {
        "listo_para_entrar": False,
        "ingresando": False,
        "audio_iniciado": False,
        "audio_intentando": False,
    }
    audio_intro = None

    if fa is not None:
        try:
            audio_intro = fa.Audio(
                src=INTRO_AUDIO,
                autoplay=True,
                volume=0.68,
                release_mode=fa.ReleaseMode.LOOP,
            )
            if hasattr(page, "services"):
                page.services.append(audio_intro)
            else:
                page.overlay.append(audio_intro)
        except Exception:
            audio_intro = None

    titulo_size = 36 if es_movil else 52
    versiculo_titulo_size = 15 if es_movil else 18
    versiculo_texto_size = 12 if es_movil else 14

    titulo = ft.Container(
        left=20,
        right=20,
        top=alto * (0.14 if es_movil else 0.16),
        opacity=0,
        animate_opacity=ft.Animation(1600, ft.AnimationCurve.EASE_IN_OUT),
        content=ft.Column(
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    "CÓDIGO ESCONDIDO 19",
                    size=titulo_size,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
        ),
    )

    versos = ft.Container(
        left=24,
        right=24,
        bottom=94 if es_movil else 108,
        opacity=0,
        animate_opacity=ft.Animation(1500, ft.AnimationCurve.EASE_IN_OUT),
        content=ft.Container(
            padding=14 if es_movil else 18,
            bgcolor=ft.Colors.with_opacity(0.22, ft.Colors.BLACK),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.22, DORADO)),
            border_radius=14,
            content=ft.Column(
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        "Apocalipsis 13:18",
                        size=versiculo_titulo_size,
                        weight=ft.FontWeight.BOLD,
                        color=DORADO,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        apocalipsis,
                        size=versiculo_texto_size,
                        color=ft.Colors.WHITE,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=3 if es_movil else 2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Divider(height=8, color=ft.Colors.with_opacity(0.18, ft.Colors.WHITE)),
                    ft.Text(
                        "Romanos 10:9",
                        size=versiculo_titulo_size,
                        weight=ft.FontWeight.BOLD,
                        color=DORADO,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        romanos,
                        size=versiculo_texto_size,
                        color=ft.Colors.WHITE,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=3 if es_movil else 2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
            ),
        ),
    )

    indicacion = ft.Container(
        left=20,
        right=20,
        bottom=12,
        opacity=0,
        animate_opacity=ft.Animation(900, ft.AnimationCurve.EASE_IN_OUT),
        content=ft.Text(
            "haga click en cualquier lugar de la pantalla para ingresar",
            color=ft.Colors.WHITE70,
            size=11 if es_movil else 12,
            text_align=ft.TextAlign.CENTER,
        ),
    )

    async def iniciar_audio_intro():
        if audio_intro is None:
            return

        if estado["audio_iniciado"] or estado["audio_intentando"]:
            return

        estado["audio_intentando"] = True

        # El audio debe arrancar junto con la imagen de intro.
        # Por eso no hacemos fade-in largo ni esperamos a que terminen los textos.
        # Reintentamos muchas veces con pausas cortas hasta que Flet lo tenga montado.
        for _ in range(35):
            try:
                audio_intro.volume = 0.68
                audio_intro.update()
                await audio_intro.play()
                estado["audio_iniciado"] = True
                estado["audio_intentando"] = False
                return
            except Exception:
                await asyncio.sleep(0.10)

        estado["audio_intentando"] = False

    def iniciar_audio_cuando_cargue(e=None):
        if audio_intro is None or estado["audio_iniciado"]:
            return

        if hasattr(page, "run_task"):
            page.run_task(iniciar_audio_intro)
        else:
            asyncio.create_task(iniciar_audio_intro())

    if audio_intro is not None:
        audio_intro.on_loaded = iniciar_audio_cuando_cargue

    async def apagar_audio_intro():
        if audio_intro is None:
            return

        volumen_inicial = float(getattr(audio_intro, "volume", 0.42) or 0.42)

        for paso in range(8, -1, -1):
            await asyncio.sleep(0.08)
            try:
                audio_intro.volume = max(0, volumen_inicial * paso / 8)
                audio_intro.update()
            except Exception:
                break

        try:
            await audio_intro.pause()
            await audio_intro.release()
            if hasattr(page, "services") and audio_intro in page.services:
                page.services.remove(audio_intro)
            if audio_intro in page.overlay:
                page.overlay.remove(audio_intro)
        except Exception:
            pass

    async def salir_intro():
        await apagar_audio_intro()
        on_ingresar()

    def ingresar(e=None):
        if not estado["listo_para_entrar"]:
            return

        if estado["ingresando"]:
            return

        estado["ingresando"] = True
        if hasattr(page, "run_task"):
            page.run_task(salir_intro)
        else:
            asyncio.run(salir_intro())

    async def flujo_animacion():
        await asyncio.sleep(0.35)
        titulo.opacity = 1
        _seguro_update(titulo)

        await asyncio.sleep(1.1)
        versos.opacity = 1
        _seguro_update(versos)

        await asyncio.sleep(0.9)
        indicacion.opacity = 1
        _seguro_update(indicacion)
        estado["listo_para_entrar"] = True

    def iniciar_animacion():
        try:
            page.update()
        except Exception:
            pass

        # Apenas la intro queda montada en pantalla, disparamos el audio y la animación
        # en paralelo. Así no ocurre imagen primero y audio después.
        if audio_intro is not None:
            if hasattr(page, "run_task"):
                page.run_task(iniciar_audio_intro)
            else:
                asyncio.create_task(iniciar_audio_intro())

        if hasattr(page, "run_task"):
            page.run_task(flujo_animacion)
        else:
            asyncio.run(flujo_animacion())

    control = ft.Container(
        expand=True,
        bgcolor=PURPURA_INICIAL,
        on_click=ingresar,
        image=ft.DecorationImage(
            src=FONDO_INTRO_PC,
            fit=ft.BoxFit.COVER,
        ),
        content=ft.Stack(
            expand=True,
            controls=[
                ft.Container(
                    expand=True,
                    bgcolor=ft.Colors.with_opacity(0.18, ft.Colors.BLACK),
                ),
                ft.Container(
                    expand=True,
                    gradient=ft.RadialGradient(
                        center=ft.Alignment(0, 0),
                        radius=1.1,
                        colors=[
                            ft.Colors.with_opacity(0.02, ft.Colors.WHITE),
                            ft.Colors.with_opacity(0.18, PURPURA_INICIAL),
                            ft.Colors.with_opacity(0.72, ft.Colors.BLACK),
                        ],
                        stops=[0.0, 0.58, 1.0],
                    ),
                ),
                titulo,
                versos,
                indicacion,
            ],
        ),
    )

    return control, iniciar_animacion
