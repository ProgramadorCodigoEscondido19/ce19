import platform
import subprocess
import sys
import os
import shutil
from pathlib import Path


APP_NOMBRE = "CODIGO ESCONDIDO 19"
PROJECT_NAME = "codigo_escondido_19"
BUNDLE_ID = "com.flet.app_ce_19"
ORG = "com.flet"
VERSION = "1.0.0"

DESTINOS = {
    "1": {
        "nombre": "ANDROID",
        "destino": "apk",
        "sistemas": {"Windows", "Linux", "Darwin"},
        "nota": "APK instalable para celulares Android.",
    },
    "2": {
        "nombre": "IOS",
        "destino": "ipa",
        "sistemas": {"Darwin"},
        "nota": "Requiere una Mac con Xcode y firma de Apple.",
    },
    "3": {
        "nombre": "LINUX",
        "destino": "linux",
        "sistemas": {"Linux"},
        "nota": "Debe compilarse desde Linux.",
    },
    "4": {
        "nombre": "WINDOWS",
        "destino": "windows",
        "sistemas": {"Windows"},
        "nota": "Requiere Visual Studio Build Tools con Desarrollo para el escritorio con C++.",
    },
    "5": {
        "nombre": "MACOS",
        "destino": "macos",
        "sistemas": {"Darwin"},
        "nota": "Debe compilarse desde una Mac.",
    },
}


def flet_ejecutable():
    base = Path("env")

    if platform.system() == "Windows":
        return base / "Scripts" / "flet.exe"

    return base / "bin" / "flet"


def normalizar_ruta_cmake(ruta):
    return str(ruta).replace("\\", "/")


def comando_build(destino):
    return [
        str(flet_ejecutable()),
        "build",
        destino,
        "--project",
        PROJECT_NAME,
        "--artifact",
        APP_NOMBRE,
        "--product",
        APP_NOMBRE,
        "--description",
        "Aplicacion Codigo Escondido 19",
        "--company",
        APP_NOMBRE,
        "--org",
        ORG,
        "--bundle-id",
        BUNDLE_ID,
        "--android-adaptive-icon-background",
        "#71106F",
        "--splash-color",
        "#71106F",
        "--splash-dark-color",
        "#71106F",
        "--build-version",
        VERSION,
        "--exclude",
        "datos/audios_biblia",
        "--no-rich-output",
        "--yes",
        "--skip-flutter-doctor",
    ]


def ruta_cmake_visual_studio(ruta_instalacion=""):
    if ruta_instalacion:
        candidato = (
            Path(ruta_instalacion)
            / "Common7"
            / "IDE"
            / "CommonExtensions"
            / "Microsoft"
            / "CMake"
            / "CMake"
            / "bin"
            / "cmake.exe"
        )
        if candidato.exists():
            return candidato

    base = os.environ.get("ProgramFiles(x86)") or "C:/Program Files (x86)"
    candidato = (
        Path(base)
        / "Microsoft Visual Studio"
        / "2022"
        / "BuildTools"
        / "Common7"
        / "IDE"
        / "CommonExtensions"
        / "Microsoft"
        / "CMake"
        / "CMake"
        / "bin"
        / "cmake.exe"
    )
    return candidato if candidato.exists() else None


def carpeta_redist_crt_x64():
    base = os.environ.get("ProgramFiles(x86)") or "C:/Program Files (x86)"
    redist = (
        Path(base)
        / "Microsoft Visual Studio"
        / "2022"
        / "BuildTools"
        / "VC"
        / "Redist"
        / "MSVC"
    )
    if not redist.exists():
        return None

    candidatos = [
        carpeta
        for carpeta in redist.glob("*/x64/Microsoft.VC143.CRT")
        if (carpeta / "vcruntime140_1.dll").exists()
    ]
    if not candidatos:
        return None

    candidatos.sort(key=lambda carpeta: carpeta.stat().st_mtime, reverse=True)
    return candidatos[0]


def estado_visual_studio_cpp():
    estado = {
        "instalado": False,
        "cpp_ok": False,
        "ruta": "",
        "workload_cpp": False,
        "msvc": False,
        "sdk": False,
        "cmake": False,
    }

    if platform.system() != "Windows":
        estado["cpp_ok"] = True
        return estado

    posibles_vswhere = []
    program_files_x86 = os.environ.get("ProgramFiles(x86)")
    if program_files_x86:
        posibles_vswhere.append(
            Path(program_files_x86)
            / "Microsoft Visual Studio"
            / "Installer"
            / "vswhere.exe"
        )
    posibles_vswhere.append(
        Path("C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe")
    )

    for vswhere in posibles_vswhere:
        if not vswhere.exists():
            continue

        try:
            resultado = subprocess.run(
                [
                    str(vswhere),
                    "-products",
                    "*",
                    "-format",
                    "json",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
            )
        except OSError:
            continue

        try:
            import json

            instalaciones = json.loads(resultado.stdout or "[]")
        except ValueError:
            instalaciones = []

        for instalacion in instalaciones:
            ruta = instalacion.get("installationPath", "")
            paquetes = instalacion.get("packages") or []
            ids = {paquete.get("id", "") for paquete in paquetes}

            estado["instalado"] = True
            estado["ruta"] = ruta
            estado["workload_cpp"] = (
                estado["workload_cpp"]
                or "Microsoft.VisualStudio.Workload.NativeDesktop" in ids
            )
            estado["msvc"] = (
                estado["msvc"]
                or "Microsoft.VisualStudio.Component.VC.Tools.x86.x64" in ids
            )
            estado["sdk"] = estado["sdk"] or any(
                componente in paquete
                for paquete in ids
                for componente in (
                    "Microsoft.VisualStudio.Component.Windows10SDK",
                    "Microsoft.VisualStudio.Component.Windows11SDK",
                )
            )
            estado["cmake"] = (
                estado["cmake"]
                or "Microsoft.VisualStudio.Component.VC.CMake.Project" in ids
            )

            ruta_msvc = Path(ruta) / "VC" / "Tools" / "MSVC"
            if ruta_msvc.exists():
                estado["msvc"] = True

            ruta_cmake = (
                Path(ruta)
                / "Common7"
                / "IDE"
                / "CommonExtensions"
                / "Microsoft"
                / "CMake"
                / "CMake"
                / "bin"
                / "cmake.exe"
            )
            if ruta_cmake.exists():
                estado["cmake"] = True

            sdk_base = Path("C:/Program Files (x86)/Windows Kits/10/bin")
            if sdk_base.exists() and any(sdk_base.iterdir()):
                estado["sdk"] = True

    estado["cpp_ok"] = (
        estado["workload_cpp"] or (estado["msvc"] and estado["sdk"] and estado["cmake"])
    )
    return estado


def completar_windows_si_falla():
    build_dir = Path("build") / "flutter" / "build" / "windows" / "x64"
    cmake_install = build_dir / "cmake_install.cmake"
    release_dir = build_dir / "runner" / "Release"
    exe = release_dir / f"{APP_NOMBRE}.exe"
    redist = carpeta_redist_crt_x64()
    estado = estado_visual_studio_cpp()
    cmake = ruta_cmake_visual_studio(estado["ruta"])

    if not cmake_install.exists() or not exe.exists() or redist is None or cmake is None:
        return False

    reemplazos = {
        "C:/WINDOWS/System32/msvcp140.dll": normalizar_ruta_cmake(
            redist / "msvcp140.dll"
        ),
        "C:/WINDOWS/System32/vcruntime140.dll": normalizar_ruta_cmake(
            redist / "vcruntime140.dll"
        ),
        "C:/WINDOWS/System32/vcruntime140_1.dll": normalizar_ruta_cmake(
            redist / "vcruntime140_1.dll"
        ),
    }

    texto = cmake_install.read_text(encoding="utf-8")
    for origen, destino in reemplazos.items():
        texto = texto.replace(origen, destino)
    cmake_install.write_text(texto, encoding="utf-8")

    resultado = subprocess.run(
        [str(cmake), "-DBUILD_TYPE=Release", "-P", "cmake_install.cmake"],
        cwd=build_dir,
    )
    return resultado.returncode == 0


def copiar_salida_windows():
    origen = Path("build") / "flutter" / "build" / "windows" / "x64" / "runner" / "Release"
    exe = origen / f"{APP_NOMBRE}.exe"
    if not exe.exists():
        return None, None

    raiz = Path("dist_windows")
    destino = raiz / APP_NOMBRE
    destino.mkdir(parents=True, exist_ok=True)

    for elemento in origen.iterdir():
        salida = destino / elemento.name
        if elemento.is_dir():
            if salida.exists():
                shutil.rmtree(salida)
            shutil.copytree(elemento, salida)
        else:
            shutil.copy2(elemento, salida)

    zip_base = Path("CODIGO_ESCONDIDO_19_WINDOWS")
    zip_path = zip_base.with_suffix(".zip")
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(zip_base), "zip", root_dir=raiz, base_dir=APP_NOMBRE)
    return destino, zip_path


def tiene_visual_studio_cpp():
    return estado_visual_studio_cpp()["cpp_ok"]


def mostrar_requisito_windows(estado=None):
    estado = estado or estado_visual_studio_cpp()
    print("\nNo se puede crear el instalador de WINDOWS todavia.")
    if estado["instalado"]:
        print("Visual Studio Build Tools esta instalado, pero faltan componentes C++.")
        print(f"Instalacion detectada: {estado['ruta']}")
    else:
        print("Falta instalar la herramienta de compilacion de Visual Studio.")
    print()
    print("Importante: no es Visual Studio Code.")
    print("Abri Visual Studio Installer y entra en MODIFICAR.")
    print("Marca esta opcion:")
    print("- Desarrollo para el escritorio con C++")
    print()
    print("Debe quedar incluido:")
    print("- MSVC C++ x64/x86")
    print("- Windows 10 SDK o Windows 11 SDK")
    print("- Herramientas C++ CMake para Windows")
    print()
    print("Despues de instalarlo, cerra esta ventana, abri de nuevo")
    print("CREAR_INSTALADOR.bat y elegi WINDOWS otra vez.")


def main():
    print("\n=== CODIGO ESCONDIDO 19 - Crear instalador ===\n", flush=True)
    sistema_actual = platform.system()
    print(f"Sistema actual: {nombre_sistema(sistema_actual)}\n", flush=True)
    print("Seleccione el sistema operativo destino:\n", flush=True)

    for clave, datos in DESTINOS.items():
        disponible = sistema_actual in datos["sistemas"]
        estado = "disponible" if disponible else "no disponible en este equipo"
        print(f"{clave}. {datos['nombre']} - {estado}", flush=True)

    opcion = input("\nOpcion: ").strip()

    if opcion not in DESTINOS:
        print("Opcion no valida.")
        return 1

    datos = DESTINOS[opcion]
    nombre = datos["nombre"]
    destino = datos["destino"]
    sistemas = datos["sistemas"]

    if sistema_actual not in sistemas:
        print("\nNo se puede crear ese instalador desde este equipo.")
        print(f"Elegiste: {nombre}")
        print(f"Motivo: {datos['nota']}")
        print(
            "Debe ejecutarse este mismo proyecto desde: "
            + ", ".join(nombre_sistema(s) for s in sorted(sistemas))
        )
        print("\nEn esta PC podes crear ANDROID y WINDOWS.")
        return 0

    estado_cpp = estado_visual_studio_cpp() if destino == "windows" else None
    if destino == "windows" and not estado_cpp["cpp_ok"]:
        mostrar_requisito_windows(estado_cpp)
        return 0

    comando = comando_build(destino)
    print(
        "\nEjecutando:\n" + " ".join(f'"{c}"' if " " in c else c for c in comando),
        flush=True,
    )
    print("Esto puede tardar bastante la primera vez. No cierres la ventana.", flush=True)
    print(flush=True)
    entorno = os.environ.copy()
    entorno["PYTHONIOENCODING"] = "utf-8:replace"
    entorno["PYTHONUTF8"] = "1"
    entorno["PYTHONLEGACYWINDOWSSTDIO"] = "0"
    entorno["FLET_CLI_NO_RICH_OUTPUT"] = "1"
    entorno["NO_COLOR"] = "1"
    entorno["TERM"] = "dumb"
    resultado = subprocess.run(comando, env=entorno)
    codigo = resultado.returncode

    if destino == "windows" and codigo != 0:
        print("\nIntentando completar el paquete Windows con el runtime local...")
        if completar_windows_si_falla():
            codigo = 0

    if codigo == 0:
        if destino == "windows":
            carpeta, zip_path = copiar_salida_windows()
            if carpeta and zip_path:
                print(f"\nListo. Carpeta Windows: {carpeta}")
                print(f"Archivo ZIP: {zip_path}")
            else:
                print(f"\nListo. Revise la carpeta build/{destino}.")
        else:
            print(f"\nListo. Revise la carpeta build/{destino}.")
    else:
        print("\nNo se pudo crear el instalador. Revise el mensaje anterior.")

    return codigo


def nombre_sistema(sistema):
    nombres = {
        "Windows": "Windows",
        "Linux": "Linux",
        "Darwin": "macOS",
    }
    return nombres.get(sistema, sistema)


if __name__ == "__main__":
    raise SystemExit(main())
