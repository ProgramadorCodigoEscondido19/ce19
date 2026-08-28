"""Guardado de archivos en el dispositivo mediante el selector nativo."""

import json
import re
from pathlib import Path

import flet as ft


class ArchivoLocalService:
    @staticmethod
    def _nombre_seguro(nombre, extension):
        base = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', " ", str(nombre or "archivo"))
        base = re.sub(r"\s+", " ", base).strip(" .") or "archivo"
        extension = str(extension or "").lower().lstrip(".")
        if extension and not base.lower().endswith(f".{extension}"):
            base = f"{base}.{extension}"
        return base

    @staticmethod
    def _picker(page):
        picker = getattr(page, "_ce19_file_picker", None)
        if picker is None:
            picker = ft.FilePicker()
            page.services.append(picker)
            setattr(page, "_ce19_file_picker", picker)
            try:
                page.update()
            except (RuntimeError, AssertionError, AttributeError):
                pass
        return picker

    @staticmethod
    def _avisar(page, mensaje, error=False):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje),
            behavior=ft.SnackBarBehavior.FLOATING,
            show_close_icon=True,
            bgcolor=ft.Colors.RED_700 if error else None,
        )
        page.snack_bar.open = True
        page.update()

    @classmethod
    def guardar_bytes(cls, page, datos, nombre, extension, titulo="Guardar archivo"):
        nombre_archivo = cls._nombre_seguro(nombre, extension)
        try:
            page.run_task(
                cls._guardar_bytes_async,
                page,
                bytes(datos),
                nombre_archivo,
                str(extension).lower().lstrip("."),
                titulo,
            )
        except (RuntimeError, AssertionError, AttributeError):
            cls._avisar(page, "No se pudo abrir el selector de archivos.", error=True)

    @classmethod
    async def _guardar_bytes_async(
        cls,
        page,
        datos,
        nombre_archivo,
        extension,
        titulo,
    ):
        picker = cls._picker(page)
        try:
            destino = await picker.save_file(
                dialog_title=titulo,
                file_name=nombre_archivo,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=[extension],
                src_bytes=datos,
            )
        except Exception as error:
            cls._avisar(page, f"No se pudo guardar el archivo: {error}", error=True)
            return

        plataforma = getattr(page, "platform", None)
        es_movil = plataforma in (ft.PagePlatform.ANDROID, ft.PagePlatform.IOS)

        if destino and not es_movil:
            ruta = Path(destino)
            if ruta.suffix.lower() != f".{extension}":
                ruta = ruta.with_suffix(f".{extension}")
            try:
                ruta.write_bytes(datos)
                destino = str(ruta)
            except OSError as error:
                cls._avisar(page, f"No se pudo escribir el archivo: {error}", error=True)
                return

        if destino:
            cls._avisar(page, f"Archivo guardado en el dispositivo: {destino}")
        elif es_movil:
            cls._avisar(page, "Archivo enviado al almacenamiento del dispositivo.")

    @classmethod
    def guardar_texto(cls, page, texto, nombre, titulo="Guardar texto"):
        cls.guardar_bytes(
            page,
            str(texto or "").encode("utf-8"),
            nombre,
            "txt",
            titulo,
        )

    @classmethod
    def guardar_json(cls, page, datos, nombre, titulo="Guardar datos"):
        contenido = json.dumps(datos, ensure_ascii=False, indent=2, default=str)
        cls.guardar_bytes(
            page,
            contenido.encode("utf-8"),
            nombre,
            "json",
            titulo,
        )

    @classmethod
    def guardar_archivo(cls, page, archivo, titulo="Guardar archivo"):
        ruta = Path(archivo)
        try:
            datos = ruta.read_bytes()
        except OSError as error:
            cls._avisar(page, f"No se pudo leer el archivo: {error}", error=True)
            return
        cls.guardar_bytes(
            page,
            datos,
            ruta.stem,
            ruta.suffix.lstrip(".") or "bin",
            titulo,
        )
