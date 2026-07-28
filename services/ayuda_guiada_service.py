from services.app_config_service import AppConfigService
from services.app_paths import AppPaths


class AyudaGuiadaService:
    """Preferencias y textos de las vinetas de ayuda."""

    CLAVE_ACTIVA = "ayuda_guiada_activa"
    _pasos_sesion = {}

    TIPS = {
        "inicio": [
            {
                "titulo": "Crear tarjeta",
                "texto": "Escribi una palabra o frase y genera una tarjeta.",
                "accion": "Clic aqui: campo de texto, luego Codificar.",
            },
            {
                "titulo": "Usar resultado",
                "texto": "Despues de codificar podes abrir detalle, copiar, compartir o guardar.",
                "accion": "Clic aqui: botones debajo de la tarjeta.",
            },
            {
                "titulo": "Ayuda visible",
                "texto": "Las vinetas se pueden activar o apagar cuando quieras.",
                "accion": "Clic aqui: interruptor Vinetas de ayuda.",
            },
        ],
        "pizarra": [
            {
                "titulo": "Elegir herramienta",
                "texto": "Usa las herramientas para dibujar, escribir, borrar, seleccionar o mover.",
                "accion": "Clic aqui: boton de herramientas o barra superior.",
            },
            {
                "titulo": "Trabajar el lienzo",
                "texto": "Acerca, aleja y desplazate para ubicar mejor tus dibujos.",
                "accion": "Clic aqui: herramienta mover o controles de zoom.",
            },
            {
                "titulo": "Guardar imagen",
                "texto": "Cuando termines, conserva la pizarra como imagen.",
                "accion": "Clic aqui: boton Guardar.",
            },
        ],
        "colores": [
            {
                "titulo": "Analizar texto",
                "texto": "Escribi texto o importa un segmento biblico para ver letras, valores y colores.",
                "accion": "Clic aqui: Texto o Importar, luego Analizar.",
            },
            {
                "titulo": "Leer codigos",
                "texto": "Cada bloque muestra la letra, su valor, sus cifras y el color resultante.",
                "accion": "Clic aqui: resultado visual para revisar el detalle.",
            },
            {
                "titulo": "Guardar tarjeta",
                "texto": "Podes guardar o descargar el analisis como tarjeta visual.",
                "accion": "Clic aqui: Guardar o Descargar JPG.",
            },
        ],
        "biblia": [
            {
                "titulo": "Navegar lectura",
                "texto": "Entra por libros, capitulos y versiculos tocando cada elemento.",
                "accion": "Clic aqui: libro, capitulo o versiculo.",
            },
            {
                "titulo": "Marcar y seleccionar",
                "texto": "Selecciona versiculos para guardar, compartir o crear tarjeta.",
                "accion": "Clic aqui: versiculo y luego boton de accion.",
            },
            {
                "titulo": "Buscar rapido",
                "texto": "Busca palabras, referencias o abreviaturas de libros.",
                "accion": "Clic aqui: buscador de Biblia.",
            },
        ],
        "tiempo": [
            {
                "titulo": "Reloj vivo",
                "texto": "El reloj principal muestra el calendario de 360 dias en tiempo real.",
                "accion": "Clic aqui: panel principal del reloj.",
            },
            {
                "titulo": "Consultar fecha",
                "texto": "Podes probar fechas hacia adelante o hacia atras.",
                "accion": "Clic aqui: Consultar otra fecha.",
            },
            {
                "titulo": "Guardar consulta",
                "texto": "Guarda el resultado para encontrarlo luego en Guardados.",
                "accion": "Clic aqui: Guardar tiempo actual o Guardar consulta.",
            },
        ],
        "calculadora": [
            {
                "titulo": "Calcular rapido",
                "texto": "Usa la calculadora simple para operaciones basicas.",
                "accion": "Clic aqui: teclas numericas y operadores.",
            },
            {
                "titulo": "Sumar Biblia",
                "texto": "Calcula valores por libro, capitulo o versiculos.",
                "accion": "Clic aqui: panel Sumar Biblia.",
            },
            {
                "titulo": "Guardar suma",
                "texto": "Despues de calcular podes guardar el resultado.",
                "accion": "Clic aqui: Guardar suma.",
            },
        ],
        "guardados": [
            {
                "titulo": "Abrir carpetas",
                "texto": "Cada contenido queda dentro de su carpeta principal.",
                "accion": "Clic aqui: tarjeta de carpeta.",
            },
            {
                "titulo": "Acciones",
                "texto": "Selecciona elementos para ver, mover, eliminar o descargar.",
                "accion": "Clic aqui: iconos de accion.",
            },
            {
                "titulo": "Tarjetas JPG",
                "texto": "Las tarjetas biblicas con imagen se abren y descargan como JPG.",
                "accion": "Clic aqui: tarjeta guardada, luego Descargar JPG.",
            },
        ],
    }

    def __init__(self):
        self._config = self._leer_config()

    def _leer_config(self):
        datos = AppConfigService.leer_json(AppPaths.CONFIG_APP, {})
        if self.CLAVE_ACTIVA not in datos:
            datos[self.CLAVE_ACTIVA] = True
        return datos

    def _guardar(self):
        AppConfigService.guardar_json(AppPaths.CONFIG_APP, self._config)

    def activa(self):
        return bool(self._config.get(self.CLAVE_ACTIVA, True))

    def establecer_activa(self, activa):
        self._config[self.CLAVE_ACTIVA] = bool(activa)
        self._guardar()

    def tips(self, ruta):
        return list(self.TIPS.get(ruta, []))

    def tip_actual(self, ruta):
        tips = self.tips(ruta)
        if not tips:
            return None

        tip = tips[self.paso_actual(ruta)]
        if isinstance(tip, dict):
            return {
                "titulo": str(tip.get("titulo") or "Ayuda"),
                "texto": str(tip.get("texto") or ""),
                "accion": str(tip.get("accion") or ""),
            }

        return {
            "titulo": "Ayuda",
            "texto": str(tip),
            "accion": "",
        }

    def paso_actual(self, ruta):
        tips = self.tips(ruta)
        if not tips:
            return 0
        try:
            return int(self._pasos_sesion.get(ruta, 0)) % len(tips)
        except Exception:
            return 0

    def avanzar(self, ruta):
        tips = self.tips(ruta)
        if not tips:
            return 0
        siguiente = (self.paso_actual(ruta) + 1) % len(tips)
        self._pasos_sesion[ruta] = siguiente
        return siguiente
