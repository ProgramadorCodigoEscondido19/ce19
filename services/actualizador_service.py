from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from core.backup_datos import crear_backup_datos
from core.rutas import RAIZ_PROYECTO, carpeta_datos_usuario
from ui.tema import APP_UPDATE_DATE


REPO = "ProgramadorCodigoEscondido19/ce19"
RELEASES_API = f"https://api.github.com/repos/{REPO}/releases/latest"


@dataclass
class ActualizacionDisponible:
    fecha_local: str
    fecha_remota: str
    sistema: str
    archivo: str
    url: str
    notas: str = ""


class ActualizadorService:
    """Busca y descarga actualizaciones sin tocar datos personales."""

    EXCLUIR_BACKUP_PROGRAMA = {
        ".git",
        ".github",
        "__pycache__",
        ".venv",
        "env",
        "build",
        "dist",
        "dist_windows",
        "release",
        "backups",
        "logs",
        "storage",
        "datos_usuario",
    }

    def __init__(self, sistema: str | None = None):
        self.sistema = sistema or self.detectar_sistema()
        self.base_usuario = carpeta_datos_usuario()
        self.carpeta_updates = self.base_usuario / "updates"
        self.carpeta_updates.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def detectar_sistema() -> str:
        nombre = platform.system().lower()
        if "android" in nombre:
            return "android"
        if nombre.startswith("win"):
            return "windows"
        return nombre or "windows"

    @staticmethod
    def normalizar_fecha(valor: str) -> str | None:
        texto = str(valor or "")
        patrones = (
            (r"(?<!\d)(\d{4})[-_/](\d{1,2})[-_/](\d{1,2})(?!\d)", (1, 2, 3)),
            (r"(?<!\d)(\d{1,2})[-_/](\d{1,2})[-_/](\d{4})(?!\d)", (3, 2, 1)),
        )
        for patron, orden in patrones:
            coincidencia = re.search(patron, texto)
            if not coincidencia:
                continue
            try:
                anio, mes, dia = (int(coincidencia.group(indice)) for indice in orden)
                return date(anio, mes, dia).isoformat()
            except ValueError:
                continue
        return None

    @classmethod
    def es_nueva_actualizacion(cls, local: str, remota: str) -> bool:
        fecha_local = cls.normalizar_fecha(local)
        fecha_remota = cls.normalizar_fecha(remota)
        if not fecha_local or not fecha_remota:
            raise ValueError("No se pudo comparar la fecha de actualizacion.")
        return fecha_remota > fecha_local

    @classmethod
    def formatear_fecha(cls, valor: str) -> str:
        normalizada = cls.normalizar_fecha(valor)
        if not normalizada:
            return str(valor or "")
        anio, mes, dia = normalizada.split("-")
        return f"{dia}-{mes}-{anio}"

    @classmethod
    def _fecha_release(cls, datos: dict) -> str:
        for clave in ("tag_name", "name"):
            fecha = cls.normalizar_fecha(datos.get(clave))
            if fecha:
                return fecha
        for clave in ("published_at", "created_at"):
            fecha = cls.normalizar_fecha(datos.get(clave))
            if fecha:
                return fecha
        raise RuntimeError(
            "La ultima Release de GitHub no tiene una fecha de actualizacion valida."
        )

    def buscar_actualizacion(self) -> ActualizacionDisponible | None:
        datos = self._leer_json_url(RELEASES_API)
        fecha_remota = self._fecha_release(datos)

        if not self.es_nueva_actualizacion(APP_UPDATE_DATE, fecha_remota):
            return None

        archivo, url = self._asset_para_sistema(datos, fecha_remota)
        return ActualizacionDisponible(
            fecha_local=APP_UPDATE_DATE,
            fecha_remota=fecha_remota,
            sistema=self.sistema,
            archivo=archivo,
            url=url,
            notas=str(datos.get("body") or ""),
        )

    def descargar(self, actualizacion: ActualizacionDisponible, progreso=None) -> Path:
        destino = self.carpeta_updates / actualizacion.archivo
        temporal = destino.with_suffix(destino.suffix + ".tmp")
        request = urllib.request.Request(
            actualizacion.url,
            headers={"User-Agent": "Codigo-Escondido-19-Updater"},
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as respuesta:
                total = int(respuesta.headers.get("Content-Length") or 0)
                descargado = 0
                with temporal.open("wb") as salida:
                    while True:
                        bloque = respuesta.read(1024 * 256)
                        if not bloque:
                            break
                        salida.write(bloque)
                        descargado += len(bloque)
                        if callable(progreso):
                            progreso(descargado, total)
        except urllib.error.URLError as error:
            raise RuntimeError(f"No se pudo descargar la actualizacion: {error}") from error

        temporal.replace(destino)
        return destino

    def preparar_instalacion(self, paquete: Path, actualizacion: ActualizacionDisponible) -> dict:
        backup_datos = crear_backup_datos("antes_actualizar")

        if actualizacion.sistema == "windows":
            return self._preparar_windows(paquete, backup_datos)

        if actualizacion.sistema == "android":
            return {
                "accion": "abrir_instalador",
                "paquete": str(paquete),
                "backup_datos": backup_datos,
                "mensaje": "APK descargado. Android pedira confirmar la instalacion.",
            }

        return {
            "accion": "descargado",
            "paquete": str(paquete),
            "backup_datos": backup_datos,
            "mensaje": "Paquete descargado. Instalacion automatica disponible solo para Windows y Android.",
        }

    def ejecutar_instalacion_preparada(self, preparacion: dict):
        accion = preparacion.get("accion")
        if accion == "windows_script":
            script = preparacion.get("script")
            if not script:
                raise RuntimeError("No se preparo el script de actualizacion.")
            subprocess.Popen(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    script,
                ],
                close_fds=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return

        if accion == "abrir_instalador":
            paquete = Path(str(preparacion.get("paquete") or ""))
            if not paquete.exists():
                raise RuntimeError("No se encontro el APK descargado.")
            self._abrir_archivo(paquete)

    def _leer_json_url(self, url: str) -> dict:
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "Codigo-Escondido-19-Updater"},
        )
        try:
            with urllib.request.urlopen(request, timeout=18) as respuesta:
                return json.loads(respuesta.read().decode("utf-8"))
        except Exception as error:
            raise RuntimeError(f"No se pudo consultar GitHub: {error}") from error

    def _asset_para_sistema(self, datos: dict, fecha: str) -> tuple[str, str]:
        fecha_iso = self.normalizar_fecha(fecha)
        if not fecha_iso:
            raise RuntimeError("La fecha de la actualizacion no es valida.")
        fecha_visible = self.formatear_fecha(fecha_iso)

        if self.sistema == "android":
            prefijo = "CODIGO-ESCONDIDO-19-Android-"
            extension = ".apk"
        elif self.sistema == "windows":
            prefijo = "CODIGO-ESCONDIDO-19-Windows-"
            extension = ".zip"
        else:
            prefijo = f"CODIGO-ESCONDIDO-19-{self.sistema}-"
            extension = ".zip"

        esperados = {
            f"{prefijo}{fecha_iso}{extension}",
            f"{prefijo}{fecha_visible}{extension}",
        }
        activos = []

        for asset in datos.get("assets") or []:
            nombre = str(asset.get("name") or "")
            url = str(asset.get("browser_download_url") or "")
            if nombre in esperados and url:
                return nombre, url
            if nombre.startswith(prefijo) and nombre.lower().endswith(extension) and url:
                activos.append((nombre, url))

        if len(activos) == 1:
            return activos[0]

        esperado = f"{prefijo}{fecha_iso}{extension}"
        raise RuntimeError(
            f"La Release no contiene el paquete requerido: {esperado}"
        )

    def _preparar_windows(self, paquete: Path, backup_datos: dict) -> dict:
        if not zipfile.is_zipfile(paquete):
            raise RuntimeError("El paquete de Windows no es un ZIP valido.")

        destino_programa = RAIZ_PROYECTO
        backup_programa = self.carpeta_updates / f"programa_anterior_{int(time.time())}"
        script = self.carpeta_updates / "aplicar_actualizacion_windows.ps1"
        exe_actual = Path(sys.executable)
        exe_reinicio = exe_actual if exe_actual.exists() else destino_programa / "CODIGO ESCONDIDO 19.exe"

        script.write_text(
            self._script_windows(
                paquete=paquete,
                destino=destino_programa,
                backup=backup_programa,
                exe=exe_reinicio,
                pid=os.getpid(),
            ),
            encoding="utf-8",
        )

        return {
            "accion": "windows_script",
            "script": str(script),
            "backup_datos": backup_datos,
            "backup_programa": str(backup_programa),
            "mensaje": "Actualizacion preparada. La app se cerrara, reemplazara el programa y volvera a iniciar.",
        }

    def _script_windows(self, paquete: Path, destino: Path, backup: Path, exe: Path, pid: int) -> str:
        excluir = "@(" + ",".join(f"'{item}'" for item in sorted(self.EXCLUIR_BACKUP_PROGRAMA)) + ")"
        return f"""
$ErrorActionPreference = 'Stop'
$package = '{self._ps(paquete)}'
$target = '{self._ps(destino)}'
$backup = '{self._ps(backup)}'
$exe = '{self._ps(exe)}'
$pidActual = {pid}
$exclude = {excluir}
$extract = Join-Path (Split-Path $package -Parent) ('extract_' + [DateTimeOffset]::Now.ToUnixTimeSeconds())

try {{
    Wait-Process -Id $pidActual -Timeout 20 -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Path $backup -Force | Out-Null
    Get-ChildItem -LiteralPath $target -Force | Where-Object {{
        $exclude -notcontains $_.Name
    }} | ForEach-Object {{
        Move-Item -LiteralPath $_.FullName -Destination (Join-Path $backup $_.Name) -Force
    }}

    Expand-Archive -LiteralPath $package -DestinationPath $extract -Force
    $source = $extract
    $items = Get-ChildItem -LiteralPath $extract -Force
    if (($items | Measure-Object).Count -eq 1 -and $items[0].PSIsContainer) {{
        $source = $items[0].FullName
    }}

    Get-ChildItem -LiteralPath $source -Force | Where-Object {{
        $exclude -notcontains $_.Name
    }} | ForEach-Object {{
        Move-Item -LiteralPath $_.FullName -Destination (Join-Path $target $_.Name) -Force
    }}

    if (Test-Path -LiteralPath $exe) {{
        Start-Process -FilePath $exe -WorkingDirectory $target
    }}
}} catch {{
    if (Test-Path -LiteralPath $backup) {{
        Get-ChildItem -LiteralPath $backup -Force | ForEach-Object {{
            Move-Item -LiteralPath $_.FullName -Destination (Join-Path $target $_.Name) -Force
        }}
    }}
    if (Test-Path -LiteralPath $exe) {{
        Start-Process -FilePath $exe -WorkingDirectory $target
    }}
    throw
}} finally {{
    if (Test-Path -LiteralPath $extract) {{
        Remove-Item -LiteralPath $extract -Recurse -Force -ErrorAction SilentlyContinue
    }}
}}
""".strip()

    @staticmethod
    def _ps(ruta: Path) -> str:
        return str(Path(ruta).resolve()).replace("'", "''")

    @staticmethod
    def _abrir_archivo(ruta: Path):
        if sys.platform.startswith("win"):
            os.startfile(str(ruta))
            return
        import webbrowser

        webbrowser.open(ruta.resolve().as_uri())
