import os
import subprocess
import sys
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / "env" / "Scripts" / "python.exe"
INSTALADOR = ROOT / "instalador" / "crear_instalador.py"

DESTINOS = {
    "android": ("1", "Android APK"),
    "windows": ("4", "Windows ZIP"),
}


def _python():
    return PYTHON if PYTHON.exists() else Path(sys.executable)


def _version_app():
    tema = ROOT / "ui" / "tema.py"
    try:
        arbol = ast.parse(tema.read_text(encoding="utf-8"))
        for nodo in arbol.body:
            if (
                isinstance(nodo, ast.Assign)
                and any(getattr(objetivo, "id", None) == "APP_VERSION" for objetivo in nodo.targets)
                and isinstance(nodo.value, ast.Constant)
            ):
                return str(nodo.value.value)
    except Exception:
        pass
    return "1.9"


def _entorno():
    entorno = os.environ.copy()
    entorno["PYTHONIOENCODING"] = "utf-8:replace"
    entorno["PYTHONUTF8"] = "1"
    entorno["PYTHONLEGACYWINDOWSSTDIO"] = "0"
    entorno["FLET_CLI_NO_RICH_OUTPUT"] = "1"
    entorno["NO_COLOR"] = "1"
    entorno["TERM"] = "dumb"
    return entorno


def _ejecutar(destino):
    opcion, nombre = DESTINOS[destino]
    comando = [str(_python()), str(INSTALADOR), opcion]
    print(f"\n=== Creando paquete: {nombre} ===\n", flush=True)
    resultado = subprocess.run(comando, cwd=ROOT, env=_entorno())
    if resultado.returncode != 0:
        print(f"\nNo se pudo crear el paquete {nombre}.", flush=True)
    return resultado.returncode


def _resolver_destinos(argumentos):
    if not argumentos:
        print("=== CODIGO ESCONDIDO 19 - Ejecutador de paquetes ===\n")
        print("1. Crear Android y Windows")
        print("2. Crear solo Android")
        print("3. Crear solo Windows")
        opcion = input("\nOpcion: ").strip()
        if opcion == "2":
            return ["android"]
        if opcion == "3":
            return ["windows"]
        if opcion in ("", "1"):
            return ["android", "windows"]
        print("Opcion no valida.")
        return []

    destino = argumentos[0].strip().lower()
    if destino in ("todo", "todos", "ambos", "all"):
        return ["android", "windows"]
    if destino in DESTINOS:
        return [destino]

    print("Destino no valido. Use: todo, android o windows.")
    return []


def main():
    if not INSTALADOR.exists():
        print(f"No se encontro el instalador base: {INSTALADOR}")
        return 1

    destinos = _resolver_destinos(sys.argv[1:])
    if not destinos:
        return 1

    for destino in destinos:
        codigo = _ejecutar(destino)
        if codigo != 0:
            return codigo

    print("\n=== Paquetes finalizados ===")
    version = _version_app()
    print(f"Android: {ROOT / f'CODIGO-ESCONDIDO-19-Android-v{version}.apk'}")
    print(f"Windows: {ROOT / f'CODIGO-ESCONDIDO-19-Windows-v{version}.zip'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
