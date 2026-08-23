import asyncio
import sys
import unicodedata
from pathlib import Path

import flet as ft

try:
    import flet_audio as fa
except Exception:
    fa = None

# Permite ejecutar main.py desde la raíz del proyecto sin perder imports.
RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from ui.tema import (
    AMARILLO,
    AZUL,
    BLANCO,
    DORADO,
    GRIS,
    MARRON,
    NARANJA,
    NEGRO,
    PURPURA,
    ROJO,
    VERDE,
)
from services.app_config_service import AppConfigService
from services.app_paths import AppPaths

FONDO_INTRO_PC = "intro_pc.webp"
INTRO_AUDIO = "santo_santo_intro_loop.mp3"
CLAVE_INTRO_MUTED = "intro_audio_muted"
PURPURA_INTRO_CLARO = "#A05AA3"
APOCALIPSIS_13_18 = (
    "Aqu\u00ed hay sabidur\u00eda. El que tiene entendimiento, cuente el n\u00famero de la bestia, "
    "pues es n\u00famero de hombre. Y su n\u00famero es seiscientos sesenta y seis."
)
ROMANOS_10_9 = (
    "que si confesares con tu boca que Jes\u00fas es el Se\u00f1or, y creyeres en tu coraz\u00f3n "
    "que Dios le levant\u00f3 de los muertos, ser\u00e1s salvo."
)

ALFABETO_29_INTRO = [
    "A", "B", "C", "CH", "D", "E", "F", "G", "H", "I", "J", "K", "L",
    "LL", "M", "N", "Ñ", "O", "P", "Q", "R", "S", "T", "U", "V", "W",
    "X", "Y", "Z",
]
VALOR_LETRA_INTRO = {
    letra: valor
    for valor, letra in enumerate(ALFABETO_29_INTRO, start=1)
}
COLOR_DIGITO_INTRO = {
    0: NEGRO,
    1: MARRON,
    2: ROJO,
    3: NARANJA,
    4: AMARILLO,
    5: VERDE,
    6: AZUL,
    7: PURPURA,
    8: GRIS,
    9: BLANCO,
}
BORDE_DIGITO_INTRO = {
    4: MARRON,
    8: NEGRO,
    9: MARRON,
}


def _normalizar_letra_intro(texto):
    texto = str(texto or "").upper().replace("Ñ", "\0")
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )
    return texto.replace("\0", "Ñ")


def _reducir_valor_intro(valor):
    numero = abs(int(valor))
    while numero >= 10:
        numero = sum(int(digito) for digito in str(numero))
    return numero


def _digito_titulo_intro(token):
    normalizado = _normalizar_letra_intro(token)
    if normalizado.isdigit():
        return int(normalizado)
    valor = VALOR_LETRA_INTRO.get(normalizado)
    return _reducir_valor_intro(valor) if valor is not None else None


def _estilo_titulo_intro(digito):
    if digito is None:
        return None
    color = COLOR_DIGITO_INTRO.get(digito, BLANCO)
    borde_color = BORDE_DIGITO_INTRO.get(digito, ft.Colors.with_opacity(0.55, ft.Colors.BLACK))
    return ft.TextStyle(
        color=color,
        shadow=[
            ft.BoxShadow(blur_radius=0, spread_radius=0, color=borde_color, offset=ft.Offset(0.75, 0)),
            ft.BoxShadow(blur_radius=0, spread_radius=0, color=borde_color, offset=ft.Offset(-0.75, 0)),
            ft.BoxShadow(blur_radius=0, spread_radius=0, color=borde_color, offset=ft.Offset(0, 0.75)),
            ft.BoxShadow(blur_radius=8, spread_radius=0, color=ft.Colors.with_opacity(0.34, color), offset=ft.Offset(0, 0)),
        ],
    )


def _spans_titulo_intro(texto):
    spans = []
    indice = 0
    while indice < len(texto):
        par = _normalizar_letra_intro(texto[indice:indice + 2])
        if par in ("CH", "LL"):
            token = texto[indice:indice + 2]
            indice += 2
        else:
            token = texto[indice]
            indice += 1

        spans.append(
            ft.TextSpan(
                token,
                style=_estilo_titulo_intro(_digito_titulo_intro(token)),
            )
        )
    return spans


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

    apocalipsis = APOCALIPSIS_13_18
    romanos = ROMANOS_10_9
    config_intro = AppConfigService.leer_json(AppPaths.CONFIG_APP, {})
    audio_muted = {"valor": bool(config_intro.get(CLAVE_INTRO_MUTED, False))}

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
                autoplay=not audio_muted["valor"],
                volume=0 if audio_muted["valor"] else 0.68,
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
                    spans=_spans_titulo_intro("CODIGO ESCONDIDO 19"),
                    size=titulo_size,
                    weight=ft.FontWeight.BOLD,
                    semantics_label="CODIGO ESCONDIDO 19",
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

    mute_boton = ft.IconButton(
        icon=ft.Icons.VOLUME_OFF if audio_muted["valor"] else ft.Icons.VOLUME_UP,
        icon_color=ft.Colors.WHITE,
        bgcolor=ft.Colors.with_opacity(0.22, ft.Colors.BLACK),
        tooltip="Activar sonido" if audio_muted["valor"] else "Silenciar intro",
    )
    mute_control = ft.Container(right=16, top=16, content=mute_boton)

    def guardar_mute():
        datos = AppConfigService.leer_json(AppPaths.CONFIG_APP, {})
        datos[CLAVE_INTRO_MUTED] = audio_muted["valor"]
        AppConfigService.guardar_json(AppPaths.CONFIG_APP, datos)

    async def aplicar_mute_audio():
        if audio_intro is None:
            return

        try:
            if audio_muted["valor"]:
                audio_intro.volume = 0
                audio_intro.update()
                await audio_intro.pause()
            else:
                audio_intro.volume = 0.68
                audio_intro.update()
                await audio_intro.play()
                estado["audio_iniciado"] = True
        except Exception:
            pass

    def alternar_mute(e=None):
        audio_muted["valor"] = not audio_muted["valor"]
        guardar_mute()
        mute_boton.icon = ft.Icons.VOLUME_OFF if audio_muted["valor"] else ft.Icons.VOLUME_UP
        mute_boton.tooltip = "Activar sonido" if audio_muted["valor"] else "Silenciar intro"
        _seguro_update(mute_boton)

        if hasattr(page, "run_task"):
            page.run_task(aplicar_mute_audio)
        else:
            asyncio.create_task(aplicar_mute_audio())

    mute_boton.on_click = alternar_mute

    def crear_capa_estrellas(cantidad, escala, opacidad, offset, duracion):
        puntos = []

        for indice in range(cantidad):
            x = ancho * (((indice * 37) + 11) % 100) / 100
            y = alto * (((indice * 53) + 19) % 100) / 100
            tam = (1.4 + (indice % 4) * 0.65) * escala

            puntos.append(
                ft.Container(
                    left=x,
                    top=y,
                    width=tam,
                    height=tam,
                    border_radius=tam,
                    bgcolor=ft.Colors.with_opacity(
                        opacidad * (0.58 + (indice % 5) * 0.09),
                        ft.Colors.WHITE,
                    ),
                    shadow=ft.BoxShadow(
                        blur_radius=5 + tam,
                        spread_radius=0,
                        color=ft.Colors.with_opacity(opacidad * 0.55, ft.Colors.WHITE),
                        offset=ft.Offset(0, 0),
                    ),
                )
            )

        return ft.Container(
            expand=True,
            ignore_interactions=True,
            offset=offset,
            animate_offset=ft.Animation(duracion, ft.AnimationCurve.EASE_IN_OUT),
            content=ft.Stack(expand=True, controls=puntos),
        )

    estrella_grande = ft.Container(
        expand=True,
        opacity=0.24,
        scale=ft.Scale(1.0),
        animate_opacity=ft.Animation(900, ft.AnimationCurve.EASE_IN_OUT),
        animate_scale=ft.Animation(900, ft.AnimationCurve.EASE_IN_OUT),
        image=ft.DecorationImage(
            src=FONDO_INTRO_PC,
            fit=ft.BoxFit.COVER,
        ),
    )

    fondo_estrellas_adelante = crear_capa_estrellas(
        cantidad=42,
        escala=1.0,
        opacidad=0.68,
        offset=ft.Offset(-0.035, 0.018),
        duracion=6200,
    )
    fondo_estrellas_atras = crear_capa_estrellas(
        cantidad=34,
        escala=0.8,
        opacidad=0.42,
        offset=ft.Offset(0.028, -0.018),
        duracion=8200,
    )
    fondo_estrellas_profundo = crear_capa_estrellas(
        cantidad=26,
        escala=0.62,
        opacidad=0.30,
        offset=ft.Offset(0, 0.026),
        duracion=10400,
    )

    async def iniciar_audio_intro():
        if audio_intro is None:
            return

        if audio_muted["valor"]:
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

        if audio_muted["valor"]:
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

    async def animar_estrella():
        await asyncio.sleep(0.25)

        while not estado["ingresando"]:
            estrella_grande.scale = ft.Scale(1.035)
            estrella_grande.opacity = 0.34
            _seguro_update(estrella_grande)
            await asyncio.sleep(0.95)

            estrella_grande.scale = ft.Scale(0.985)
            estrella_grande.opacity = 0.22
            _seguro_update(estrella_grande)
            await asyncio.sleep(0.95)

    async def animar_estrellas():
        await asyncio.sleep(0.20)

        while not estado["ingresando"]:
            fondo_estrellas_adelante.offset = ft.Offset(0.045, -0.028)
            fondo_estrellas_atras.offset = ft.Offset(-0.038, 0.026)
            fondo_estrellas_profundo.offset = ft.Offset(0.024, -0.035)
            _seguro_update(fondo_estrellas_adelante)
            _seguro_update(fondo_estrellas_atras)
            _seguro_update(fondo_estrellas_profundo)
            await asyncio.sleep(6.2)

            fondo_estrellas_adelante.offset = ft.Offset(-0.048, 0.030)
            fondo_estrellas_atras.offset = ft.Offset(0.040, -0.028)
            fondo_estrellas_profundo.offset = ft.Offset(-0.026, 0.036)
            _seguro_update(fondo_estrellas_adelante)
            _seguro_update(fondo_estrellas_atras)
            _seguro_update(fondo_estrellas_profundo)
            await asyncio.sleep(6.2)

    def iniciar_animacion():
        try:
            page.update()
        except Exception:
            pass

        # Apenas la intro queda montada en pantalla, disparamos el audio y la animación
        # en paralelo. Así no ocurre imagen primero y audio después.
        if audio_intro is not None and not audio_muted["valor"]:
            if hasattr(page, "run_task"):
                page.run_task(iniciar_audio_intro)
            else:
                asyncio.create_task(iniciar_audio_intro())

        if hasattr(page, "run_task"):
            page.run_task(flujo_animacion)
            page.run_task(animar_estrella)
            page.run_task(animar_estrellas)
        else:
            asyncio.run(flujo_animacion())

    control = ft.Container(
        expand=True,
        bgcolor=PURPURA_INTRO_CLARO,
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
                    bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                ),
                fondo_estrellas_profundo,
                fondo_estrellas_atras,
                fondo_estrellas_adelante,
                estrella_grande,
                ft.Container(
                    expand=True,
                    gradient=ft.RadialGradient(
                        center=ft.Alignment(0, 0),
                        radius=1.1,
                        colors=[
                            ft.Colors.with_opacity(0.02, ft.Colors.WHITE),
                            ft.Colors.with_opacity(0.10, PURPURA_INTRO_CLARO),
                            ft.Colors.with_opacity(0.30, PURPURA_INTRO_CLARO),
                        ],
                        stops=[0.0, 0.58, 1.0],
                    ),
                ),
                titulo,
                versos,
                indicacion,
                mute_control,
            ],
        ),
    )

    return control, iniciar_animacion
