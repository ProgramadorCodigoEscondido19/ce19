from decimal import Decimal, InvalidOperation

import flet as ft

from core.app_state import state
from services.biblia_service import BibliaService
from services.calculadora_biblia_service import CalculadoraBibliaService
from ui.nombre_guardado import pedir_nombre_y_carpeta_guardado
from ui.responsive import Responsive
from ui.tema import (
    BLANCO,
    DORADO,
    PERLA_BORDE,
    PERLA_PANEL,
    PURPURA_INICIAL,
    SUPERFICIE_PERLADA,
    TEXTO_PRINCIPAL,
    TEXTO_SECUNDARIO,
    PURPURA_IOS,
    panel_moderno,
    titulo_pagina,
)


class CalculadoraView:
    def __init__(self, page, router):
        self.page = page
        self.router = router
        self.responsive = Responsive(page)
        self.expresion = ""
        self.sumador_biblia = CalculadoraBibliaService()
        self.libros_biblia = BibliaService.libros()
        self.ultimo_resultado_suma = None
        self.display = ft.Text(
            "0",
            size=40,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.RIGHT,
            color=TEXTO_PRINCIPAL,
        )
        self.display_sub = ft.Text(
            "Calculadora interna",
            size=12,
            color=TEXTO_SECUNDARIO,
            text_align=ft.TextAlign.RIGHT,
        )
        self.modo_suma_biblia = ft.Dropdown(
            label="Tipo de suma",
            value="Versiculos",
            options=[
                ft.dropdown.Option("Versiculos"),
                ft.dropdown.Option("Capitulos"),
                ft.dropdown.Option("Libros"),
                ft.dropdown.Option("Biblia completa"),
            ],
            on_select=self._cambiar_modo_suma_biblia,
        )
        self.libro_suma_biblia = ft.Dropdown(
            label="Libro",
            options=[
                ft.dropdown.Option(libro.get("nombre", ""))
                for libro in self.libros_biblia
            ],
            value=self.libros_biblia[0].get("nombre", "") if self.libros_biblia else None,
            on_select=self._cambiar_libro_suma_biblia,
        )
        self.libro_fin_suma_biblia = ft.Dropdown(
            label="Hasta libro",
            options=[
                ft.dropdown.Option(libro.get("nombre", ""))
                for libro in self.libros_biblia
            ],
            value=self.libros_biblia[0].get("nombre", "") if self.libros_biblia else None,
        )
        self.capitulo_inicio_suma_biblia = ft.Dropdown(
            label="Capitulo",
            on_select=self._cambiar_capitulo_suma_biblia,
        )
        self.capitulo_fin_suma_biblia = ft.Dropdown(label="Hasta capitulo")
        self.versiculo_inicio_suma_biblia = ft.Dropdown(label="Versiculo")
        self.versiculo_fin_suma_biblia = ft.Dropdown(label="Hasta versiculo")
        self.resultado_suma_biblia = ft.Text(
            "0",
            size=38,
            weight=ft.FontWeight.BOLD,
            color=PURPURA_IOS,
        )
        self.detalle_suma_biblia = ft.Text(
            "Seleccione un alcance y presione Calcular.",
            size=12,
            color=TEXTO_SECUNDARIO,
        )
        self.boton_guardar_suma = ft.OutlinedButton(
            "Guardar suma",
            icon=ft.Icons.SAVE_ALT,
            disabled=True,
            on_click=self._guardar_suma_biblica,
        )
        self._preparar_selectores_suma_biblia()

    def _on_resize(self, e):
        self.router.refrescar()

    def _puede_sumar_biblia(self):
        comprobar = getattr(self.router, "tiene_capacidad", None)
        return bool(comprobar("calculadora_suma_biblia")) if callable(comprobar) else True

    def obtener_vista(self):
        self.page.on_resize = self._on_resize
        self.page.on_keyboard_event = self._teclado_fisico
        es_movil = self.responsive.is_mobile()
        self.display.size = 36 if es_movil else 52

        calculadora = ft.Column(
            tight=True,
            spacing=12,
            controls=[
                titulo_pagina(
                    "Calculadora",
                    "Operaciones rápidas sin salir de Código Escondido 19",
                    ft.Icons.CALCULATE,
                ),
                ft.Container(
                    height=154 if es_movil else 174,
                    padding=18,
                    alignment=ft.Alignment(1, 0),
                    bgcolor=SUPERFICIE_PERLADA,
                    border_radius=18,
                    border=ft.Border.all(1, PERLA_BORDE),
                    content=ft.Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        auto_scroll=True,
                        spacing=4,
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        controls=[self.display_sub, self.display],
                    ),
                ),
                self._teclado(),
            ],
        )
        sumador = self._sumador_biblico() if self._puede_sumar_biblia() else None
        cuerpo = (
            ft.Column(
                scroll=ft.ScrollMode.AUTO,
                spacing=14,
                controls=[calculadora] + ([sumador] if sumador else []),
            )
            if es_movil
            else ft.Row(
                spacing=18,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(width=430, content=calculadora),
                ] + ([ft.Container(expand=True, content=sumador)] if sumador else []),
            )
        )

        return ft.Container(
            expand=True,
            bgcolor=ft.Colors.TRANSPARENT,
            padding=4 if es_movil else 8,
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=1120,
                        content=panel_moderno(cuerpo, padding=18 if es_movil else 20),
                    )
                ],
            ),
        )

    def _sumador_biblico(self):
        self._sincronizar_controles_suma_biblia()

        if not self.libros_biblia:
            return ft.Container(
                padding=16,
                bgcolor=SUPERFICIE_PERLADA,
                border_radius=18,
                border=ft.Border.all(1, PERLA_BORDE),
                content=ft.Text("No se encontro la Biblia cargada."),
            )

        controles = ft.Column(
            tight=True,
            spacing=12,
            controls=[
                ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.MENU_BOOK, color=DORADO),
                        ft.Text(
                            "Sumar Biblia",
                            size=22,
                            weight=ft.FontWeight.BOLD,
                            color=TEXTO_PRINCIPAL,
                        ),
                    ],
                ),
                ft.Text(
                    "Calcula solo la suma total de los valores de letras.",
                    size=12,
                    color=TEXTO_SECUNDARIO,
                ),
                ft.Column(
                    tight=True,
                    spacing=10,
                    controls=[
                        ft.Row(
                            wrap=True,
                            spacing=10,
                            run_spacing=10,
                            controls=[
                                ft.Container(width=190, content=self.modo_suma_biblia),
                                ft.Container(width=230, content=self.libro_suma_biblia),
                                ft.Container(width=230, content=self.libro_fin_suma_biblia),
                            ],
                        ),
                        ft.Row(
                            wrap=True,
                            spacing=10,
                            run_spacing=10,
                            controls=[
                                ft.Container(width=140, content=self.capitulo_inicio_suma_biblia),
                                ft.Container(width=160, content=self.capitulo_fin_suma_biblia),
                                ft.Container(width=140, content=self.versiculo_inicio_suma_biblia),
                                ft.Container(width=160, content=self.versiculo_fin_suma_biblia),
                            ],
                        ),
                    ],
                ),
                ft.Row(
                    wrap=True,
                    spacing=10,
                    run_spacing=10,
                    controls=[
                        ft.ElevatedButton(
                            "Calcular",
                            icon=ft.Icons.CALCULATE,
                            bgcolor=PURPURA_IOS,
                            color=BLANCO,
                            on_click=self._calcular_suma_biblica,
                        ),
                        self.boton_guardar_suma,
                    ],
                ),
                ft.Container(
                    padding=16,
                    bgcolor=BLANCO,
                    border_radius=16,
                    border=ft.Border.all(1, PERLA_BORDE),
                    content=ft.Column(
                        tight=True,
                        spacing=6,
                        controls=[
                            ft.Text(
                                "Suma total",
                                size=12,
                                color=TEXTO_SECUNDARIO,
                                weight=ft.FontWeight.BOLD,
                            ),
                            self.resultado_suma_biblia,
                            self.detalle_suma_biblia,
                        ],
                    ),
                ),
            ],
        )

        return ft.Container(
            padding=18,
            bgcolor=SUPERFICIE_PERLADA,
            border_radius=18,
            border=ft.Border.all(1, PERLA_BORDE),
            content=controles,
        )

    def _preparar_selectores_suma_biblia(self):
        self._actualizar_capitulos_suma_biblia()
        self._actualizar_versiculos_suma_biblia()
        self._sincronizar_controles_suma_biblia()

    def _sincronizar_controles_suma_biblia(self):
        modo = self.modo_suma_biblia.value or "Versiculos"
        es_biblia = modo == "Biblia completa"
        es_capitulos = modo == "Capitulos"
        es_versiculos = modo == "Versiculos"
        es_libros = modo == "Libros"

        self.libro_suma_biblia.visible = not es_biblia
        self.libro_fin_suma_biblia.visible = es_libros
        self.capitulo_inicio_suma_biblia.visible = es_capitulos or es_versiculos
        self.capitulo_fin_suma_biblia.visible = es_capitulos
        self.versiculo_inicio_suma_biblia.visible = es_versiculos
        self.versiculo_fin_suma_biblia.visible = es_versiculos

    def _cambiar_modo_suma_biblia(self, e=None):
        self._sincronizar_controles_suma_biblia()
        self._actualizar_control(self.libro_suma_biblia)
        self._actualizar_control(self.libro_fin_suma_biblia)
        self._actualizar_control(self.capitulo_inicio_suma_biblia)
        self._actualizar_control(self.capitulo_fin_suma_biblia)
        self._actualizar_control(self.versiculo_inicio_suma_biblia)
        self._actualizar_control(self.versiculo_fin_suma_biblia)

    def _cambiar_libro_suma_biblia(self, e=None):
        if self.modo_suma_biblia.value == "Libros":
            self.libro_fin_suma_biblia.value = self.libro_suma_biblia.value
            self._actualizar_control(self.libro_fin_suma_biblia)

        self._actualizar_capitulos_suma_biblia()
        self._actualizar_versiculos_suma_biblia()

    def _cambiar_capitulo_suma_biblia(self, e=None):
        self._actualizar_versiculos_suma_biblia()

    def _actualizar_capitulos_suma_biblia(self):
        libro = BibliaService.libro_por_nombre(self.libro_suma_biblia.value)
        total = len(libro.get("capitulos", [])) if libro else 0
        opciones = [ft.dropdown.Option(str(i)) for i in range(1, total + 1)]

        for control in (self.capitulo_inicio_suma_biblia, self.capitulo_fin_suma_biblia):
            valor_actual = control.value
            control.options = opciones

            if not opciones:
                control.value = None
            elif valor_actual and 1 <= int(valor_actual) <= total:
                control.value = valor_actual
            else:
                control.value = "1"

            self._actualizar_control(control)

    def _actualizar_versiculos_suma_biblia(self):
        libro = self.libro_suma_biblia.value
        capitulo = self.capitulo_inicio_suma_biblia.value or 1
        total = len(BibliaService.obtener_capitulo(libro, capitulo))
        opciones = [ft.dropdown.Option(str(i)) for i in range(1, total + 1)]

        for control in (self.versiculo_inicio_suma_biblia, self.versiculo_fin_suma_biblia):
            valor_actual = control.value
            control.options = opciones

            if not opciones:
                control.value = None
            elif valor_actual and 1 <= int(valor_actual) <= total:
                control.value = valor_actual
            else:
                control.value = "1"

            self._actualizar_control(control)

    def _calcular_suma_biblica(self, e=None):
        if not self._puede_sumar_biblia():
            return
        modo = self.modo_suma_biblia.value or "Versiculos"

        try:
            if modo == "Biblia completa":
                resultado = self.sumador_biblia.sumar_biblia_completa()
            elif modo == "Capitulos":
                resultado = self.sumador_biblia.sumar_capitulos(
                    self.libro_suma_biblia.value,
                    self.capitulo_inicio_suma_biblia.value,
                    self.capitulo_fin_suma_biblia.value,
                )
            elif modo == "Libros":
                resultado = self.sumador_biblia.sumar_libros(
                    self.libro_suma_biblia.value,
                    self.libro_fin_suma_biblia.value,
                )
            else:
                resultado = self.sumador_biblia.sumar_versiculos(
                    self.libro_suma_biblia.value,
                    self.capitulo_inicio_suma_biblia.value,
                    self.versiculo_inicio_suma_biblia.value,
                    self.versiculo_fin_suma_biblia.value,
                )
        except (TypeError, ValueError, IndexError):
            self._snack("Seleccione una parte valida de la Biblia.")
            return

        self.ultimo_resultado_suma = resultado
        self.resultado_suma_biblia.value = self._formatear_numero(resultado["total"])
        self.detalle_suma_biblia.value = (
            f"{resultado['referencia']}\n"
            f"Letras sumadas: {self._formatear_numero(resultado['cantidad_letras'])}\n"
            f"Alfabeto: {resultado['alfabeto']}"
        )
        self.boton_guardar_suma.disabled = False
        self._actualizar_control(self.resultado_suma_biblia)
        self._actualizar_control(self.detalle_suma_biblia)
        self._actualizar_control(self.boton_guardar_suma)

    def _guardar_suma_biblica(self, e=None):
        if not self._puede_sumar_biblia():
            return
        if not self.ultimo_resultado_suma:
            self._snack("Primero calcule una suma.")
            return

        resultado = self.ultimo_resultado_suma.copy()
        nombre_default = f"Suma {resultado['referencia']}"

        def guardar_con_nombre(nombre, carpeta=None):
            destino = carpeta or state.carpetas.obtener_por_nombre("CALCULADORA")
            state.guardados.guardar(
                {
                    "tipo": "calculo_biblico",
                    "carpeta": destino["nombre"] if destino else "CALCULADORA",
                    "carpeta_id": destino["id"] if destino else 6,
                    "nombre": nombre or nombre_default,
                    "palabra": resultado["referencia"],
                    "referencia": resultado["referencia"],
                    "alfabeto": resultado["alfabeto"],
                    "suma": (
                        f"Referencia: {resultado['referencia']}\n"
                        f"Alcance: {resultado['alcance']}\n"
                        f"Letras sumadas: {resultado['cantidad_letras']}\n"
                        f"Suma total: {resultado['total']}"
                    ),
                    "resultado": resultado["total"],
                    "contenido": {
                        "tipo": "calculo_biblico",
                        **resultado,
                    },
                }
            )
            self._mostrar_guardado_correcto(nombre or nombre_default)

        pedir_nombre_y_carpeta_guardado(
            self.page,
            "Guardar suma biblica",
            nombre_default,
            state.carpetas,
            "CALCULADORA",
            guardar_con_nombre,
            "Se guardara en CALCULADORA.",
        )

    def _mostrar_guardado_correcto(self, nombre):
        def cerrar(e=None):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Guardado correctamente"),
            content=ft.Text(nombre),
            actions=[ft.ElevatedButton("Aceptar", on_click=cerrar)],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _snack(self, mensaje):
        self.page.snack_bar = ft.SnackBar(content=ft.Text(mensaje))
        self.page.snack_bar.open = True
        self.page.update()

    def _formatear_numero(self, valor):
        try:
            return f"{int(valor):,}".replace(",", ".")
        except (TypeError, ValueError):
            return str(valor)

    def _actualizar_control(self, control):
        try:
            control.update()
        except (RuntimeError, AssertionError):
            pass

    def _boton(self, valor):
        es_operador = valor in {"+", "-", "*", "/", "="}
        es_control = valor in {"C", "⌫", "±"}
        if es_operador:
            bgcolor = PURPURA_IOS
            color = BLANCO
        elif es_control:
            bgcolor = "#FFF1E8"
            color = "#9A4B18"
        else:
            bgcolor = PERLA_PANEL
            color = TEXTO_PRINCIPAL

        return ft.ElevatedButton(
            valor,
            expand=True,
            height=50,
            bgcolor=bgcolor,
            color=color,
            on_click=lambda e, v=valor: self._presionar(v),
        )

    def _teclado(self):
        filas = [
            ["C", "⌫", "/", "*"],
            ["7", "8", "9", "-"],
            ["4", "5", "6", "+"],
            ["1", "2", "3", "="],
            ["0", ".", "±"],
        ]

        return ft.Container(
            height=310,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Column(
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Row(spacing=8, controls=[self._boton(valor) for valor in fila])
                    for fila in filas
                ],
            ),
        )

    def _presionar(self, valor):
        if valor == "⌫":
            self.expresion = self.expresion[:-1]
            self._actualizar_display()
            return

        if valor == "±":
            self._cambiar_signo()
            self._actualizar_display()
            return

        if valor == "C":
            self.expresion = ""
        elif valor == "=":
            self._calcular()
        elif valor in "+-*/":
            self._agregar_operador(valor)
        elif valor == ".":
            self._agregar_decimal()
        else:
            self.expresion += valor

        self._actualizar_display()

    def _teclado_fisico(self, e):
        """Permite usar el teclado numerico sin interceptar las otras vistas."""
        if getattr(self.router, "activo", None) != "calculadora":
            return
        if any(getattr(e, modificador, False) for modificador in ("ctrl", "alt", "meta")):
            return

        tecla = str(getattr(e, "key", "") or "")
        normalizada = tecla.lower().replace(" ", "")
        equivalencias = {
            "enter": "=",
            "numpadenter": "=",
            "=": "=",
            "add": "+",
            "numpadadd": "+",
            "subtract": "-",
            "numpadsubtract": "-",
            "multiply": "*",
            "numpadmultiply": "*",
            "divide": "/",
            "numpaddivide": "/",
            "decimal": ".",
            "numpaddecimal": ".",
            ",": ".",
            ".": ".",
            "backspace": "⌫",
            "delete": "⌫",
            "escape": "C",
        }
        valor = equivalencias.get(normalizada)

        if valor is None:
            if len(tecla) == 1 and tecla in "0123456789+-*/":
                valor = tecla
            elif normalizada.startswith(("numpad", "num", "digit")) and normalizada[-1:] in "0123456789":
                valor = normalizada[-1]

        if valor is not None:
            self._presionar(valor)

    def _agregar_operador(self, operador):
        if not self.expresion:
            if operador == "-":
                self.expresion = "-"
            return

        if self.expresion[-1] in "+-*/.":
            self.expresion = self.expresion[:-1] + operador
        else:
            self.expresion += operador

    def _agregar_decimal(self):
        parte = self._ultima_parte()
        if "." not in parte:
            self.expresion += "." if parte else "0."

    def _cambiar_signo(self):
        if not self.expresion:
            self.expresion = "-"
            return

        parte = self._ultima_parte()
        if not parte:
            return

        inicio = len(self.expresion) - len(parte)
        if parte.startswith("-"):
            self.expresion = self.expresion[:inicio] + parte[1:]
        else:
            self.expresion = self.expresion[:inicio] + "-" + parte

    def _ultima_parte(self):
        if not self.expresion:
            return ""

        inicio = 0
        for indice in range(len(self.expresion) - 1, -1, -1):
            if self.expresion[indice] in "+*/":
                inicio = indice + 1
                break
            if self.expresion[indice] == "-" and indice > 0:
                inicio = indice + 1
                break

        return self.expresion[inicio:]

    def _calcular(self):
        if not self.expresion or self.expresion[-1] in "+-*/.":
            return

        try:
            resultado = self._evaluar(self.expresion)
        except (InvalidOperation, ZeroDivisionError, ValueError):
            self.expresion = "Error"
            return

        self.expresion = str(resultado.normalize()).rstrip("0").rstrip(".")

    def _evaluar(self, expresion):
        tokens = self._tokenizar(expresion)
        valores = []
        operadores = []
        prioridad = {"+": 1, "-": 1, "*": 2, "/": 2}

        def aplicar():
            b = valores.pop()
            a = valores.pop()
            op = operadores.pop()
            if op == "+":
                valores.append(a + b)
            elif op == "-":
                valores.append(a - b)
            elif op == "*":
                valores.append(a * b)
            else:
                valores.append(a / b)

        for token in tokens:
            if token in prioridad:
                while operadores and prioridad[operadores[-1]] >= prioridad[token]:
                    aplicar()
                operadores.append(token)
            else:
                valores.append(Decimal(token))

        while operadores:
            aplicar()

        return valores[0]

    def _tokenizar(self, expresion):
        tokens = []
        actual = ""

        for indice, caracter in enumerate(expresion):
            if caracter in "+*/" or (
                caracter == "-" and indice > 0 and expresion[indice - 1] not in "+-*/"
            ):
                if actual:
                    tokens.append(actual)
                    actual = ""
                tokens.append(caracter)
            else:
                actual += caracter

        if actual:
            tokens.append(actual)

        return tokens

    def _actualizar_display(self):
        self.display.value = self.expresion or "0"
        self.display_sub.value = "Resultado" if self.expresion and self.expresion != "Error" else "Calculadora interna"
        try:
            self.display.update()
            self.display_sub.update()
        except (RuntimeError, AssertionError):
            pass
