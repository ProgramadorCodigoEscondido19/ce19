from decimal import Decimal, InvalidOperation

import flet as ft

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
    VIOLETA_IOS,
    panel_moderno,
    titulo_pagina,
)


class CalculadoraView:
    def __init__(self, page, router):
        self.page = page
        self.router = router
        self.responsive = Responsive(page)
        self.expresion = ""
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

    def _on_resize(self, e):
        self.router.refrescar()

    def obtener_vista(self):
        self.page.on_resize = self._on_resize
        es_movil = self.responsive.is_mobile()
        self.display.size = 36 if es_movil else 52

        cuerpo = ft.Column(
            tight=True,
            spacing=12,
            controls=[
                titulo_pagina(
                    "Calculadora",
                    "Operaciones rápidas sin salir de Código Escondido 19",
                    ft.Icons.CALCULATE,
                ),
                ft.Container(
                    padding=18,
                    alignment=ft.Alignment(1, 0),
                    bgcolor=SUPERFICIE_PERLADA,
                    border_radius=18,
                    border=ft.Border.all(1, PERLA_BORDE),
                    content=ft.Column(
                        tight=True,
                        spacing=4,
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        controls=[self.display_sub, self.display],
                    ),
                ),
                self._teclado(),
            ],
        )

        return ft.Container(
            expand=True,
            bgcolor=ft.Colors.TRANSPARENT,
            padding=4 if es_movil else 8,
            alignment=ft.Alignment(0, 0),
            content=ft.Container(
                width=460,
                content=panel_moderno(cuerpo, padding=18 if es_movil else 20),
            ),
        )

    def _teclado(self):
        filas = [
            ["C", "⌫", "/", "*"],
            ["7", "8", "9", "-"],
            ["4", "5", "6", "+"],
            ["1", "2", "3", "="],
            ["0", ".", "±", "="],
        ]

        return ft.Column(
            spacing=10,
            controls=[
                ft.Row(spacing=10, controls=[self._boton(valor) for valor in fila])
                for fila in filas
            ],
        )

    def _boton(self, valor):
        es_operador = valor in {"+", "-", "*", "/", "="}
        es_control = valor in {"C", "⌫", "±"}
        if es_operador:
            bgcolor = VIOLETA_IOS
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
            height=58,
            bgcolor=bgcolor,
            color=color,
            on_click=lambda e, v=valor: self._presionar(v),
        )

    def _presionar(self, valor):
        if valor == "C":
            self.expresion = ""
        elif valor == "⌫":
            self.expresion = self.expresion[:-1]
        elif valor == "=":
            self._calcular()
        elif valor == "±":
            self._cambiar_signo()
        elif valor in "+-*/":
            self._agregar_operador(valor)
        elif valor == ".":
            self._agregar_decimal()
        else:
            self.expresion += valor

        self._actualizar_display()

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
