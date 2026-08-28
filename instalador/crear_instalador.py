import platform
import subprocess
import sys
import os
import shutil
import fnmatch
import hashlib
import zipfile
import ast
import tempfile
from pathlib import Path


APP_NOMBRE = "CODIGO ESCONDIDO 19"
PROJECT_NAME = "codigo_escondido_19"
BUNDLE_ID = "com.flet.app_ce_19"
ORG = "com.flet"
ROOT = Path(__file__).resolve().parents[1]


def leer_constante_tema(nombre, predeterminado):
    tema = ROOT / "ui" / "tema.py"
    try:
        arbol = ast.parse(tema.read_text(encoding="utf-8"))
        for nodo in arbol.body:
            if (
                isinstance(nodo, ast.Assign)
                and any(getattr(objetivo, "id", None) == nombre for objetivo in nodo.targets)
                and isinstance(nodo.value, ast.Constant)
            ):
                return str(nodo.value.value)
    except Exception:
        pass
    return predeterminado


VERSION = leer_constante_tema("APP_VERSION", "1.9")
FECHA_ACTUALIZACION = leer_constante_tema("APP_UPDATE_DATE", "2026-08-28")
BUILD_NUMBER = FECHA_ACTUALIZACION.replace("-", "")
VERSION_NATIVA = VERSION if VERSION.count(".") >= 2 else f"{VERSION}.0"
EXCLUSIONES_PAQUETE = [
    ".agents",
    ".codex",
    ".git",
    ".github",
    ".venv",
    "env",
    "build",
    "dist",
    "dist_windows",
    "release",
    "backups",
    "logs",
    "storage",
    "instalador",
    "ejecutador_paquetes",
    "__pycache__",
    "*.pyc",
    "README.md",
    ".gitignore",
    "CODIGO-ESCONDIDO-19-*.apk",
    "CODIGO-ESCONDIDO-19-*.zip",
    "datos/exportaciones",
    "datos/historial.json",
    "datos/guardados.json",
    "datos/carpetas.json",
    "datos/config_tiempo.json",
    "datos/analisis_colores_historial.json",
    "datos/historial_referencias_biblia.json",
    "datos/favoritos_biblia.json",
    "datos/notas_biblia.json",
    "datos/resaltados_biblia.json",
    "datos/ultima_lectura_biblia.json",
]
ARCHIVOS_REQUERIDOS_APP_ZIP = [
    "main.py",
    "core/__init__.py",
    "core/app_state.py",
    "ui/__init__.py",
    "ui/tema.py",
    "vistas/analizador_colores.py",
    "logica/analizador_colores.py",
]
ARCHIVOS_REQUERIDOS_WINDOWS_APP_ZIP = [
    "main.pyc",
    "core/__init__.pyc",
    "core/app_state.pyc",
    "ui/__init__.pyc",
    "ui/tema.pyc",
    "vistas/analizador_colores.pyc",
    "logica/analizador_colores.pyc",
    "datos/biblia_rvr1960.json.gz",
    "assets/icon.png",
]
ARCHIVOS_REQUERIDOS_ANDROID_APP_ZIP = [
    "main.pyc",
    "core/__init__.pyc",
    "core/app_state.pyc",
    "ui/__init__.pyc",
    "ui/tema.pyc",
    "vistas/analizador_colores.pyc",
    "logica/analizador_colores.pyc",
    "datos/biblia_rvr1960.json.gz",
    "assets/icon.png",
]
MARCADORES_REQUERIDOS_APP_ZIP = {
    "logica/analizador_colores.py": [
        "valores_terciarios_colores",
        "total_terciario_colores",
    ],
}
EXCLUSIONES_APP_ZIP = [
    ".agents",
    ".codex",
    ".mypy_cache",
    ".pytest_cache",
    "CODIGO-ESCONDIDO-19-*.apk",
    "CODIGO-ESCONDIDO-19-*.zip",
    "*.log",
]

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
    base = ROOT / "env"

    if platform.system() == "Windows":
        return base / "Scripts" / "flet.exe"

    return base / "bin" / "flet"


def dart_ejecutable():
    dart = shutil.which("dart")
    if dart:
        return Path(dart)

    candidatos = []
    home = Path.home()
    flutter_base = home / "flutter"
    if flutter_base.exists():
        candidatos.extend(
            flutter_base.glob("*/bin/cache/dart-sdk/bin/dart.exe")
            if platform.system() == "Windows"
            else flutter_base.glob("*/bin/cache/dart-sdk/bin/dart")
        )

    for candidato in candidatos:
        if candidato.exists():
            return candidato

    raise RuntimeError(
        "No se encontro dart. Ejecute primero flet build para preparar Flutter, "
        "o agregue Dart al PATH."
    )


def flutter_ejecutable():
    flutter = shutil.which("flutter")
    if flutter:
        return Path(flutter)

    candidatos = []
    home = Path.home()
    flutter_base = home / "flutter"
    if flutter_base.exists():
        candidatos.extend(
            flutter_base.glob("*/bin/flutter.bat")
            if platform.system() == "Windows"
            else flutter_base.glob("*/bin/flutter")
        )

    for candidato in candidatos:
        if candidato.exists():
            return candidato

    raise RuntimeError(
        "No se encontro flutter. Ejecute primero flet build para preparar Flutter, "
        "o agregue Flutter al PATH."
    )


def aapt_ejecutable():
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    candidatos = sorted(
        (base / "Android" / "Sdk" / "build-tools").glob("*/aapt.exe"),
        reverse=True,
    )
    if candidatos:
        return candidatos[0]
    raise RuntimeError("No se encontro aapt para validar la version del APK.")


def normalizar_ruta_cmake(ruta):
    return str(ruta).replace("\\", "/")


def comando_build(destino):
    comando = [
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
        VERSION_NATIVA,
        "--build-number",
        BUILD_NUMBER,
        "--no-rich-output",
        "--yes",
        "--skip-flutter-doctor",
        "--cleanup-app",
        "--exclude",
        *EXCLUSIONES_PAQUETE,
    ]

    return comando


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
    build_dir = ROOT / "build" / "flutter" / "build" / "windows" / "x64"
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
    origen = ROOT / "build" / "flutter" / "build" / "windows" / "x64" / "runner" / "Release"
    exe = origen / f"{APP_NOMBRE}.exe"
    if not exe.exists():
        return None, None

    recrear_app_zip_windows(origen)

    raiz = ROOT / "dist_windows"
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

    zip_base = ROOT / f"CODIGO-ESCONDIDO-19-Windows-{FECHA_ACTUALIZACION}"
    zip_path = Path(str(zip_base) + ".zip")
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(zip_base), "zip", root_dir=raiz, base_dir=APP_NOMBRE)
    validar_zip_windows(zip_path)
    return destino, zip_path


def _ruta_excluida_app_zip(rel):
    rel = rel.replace("\\", "/")
    nombre = rel.rsplit("/", 1)[-1]
    partes = rel.split("/")

    for patron in [*EXCLUSIONES_PAQUETE, *EXCLUSIONES_APP_ZIP]:
        patron = patron.replace("\\", "/")
        if rel == patron or rel.startswith(patron.rstrip("/") + "/"):
            return True
        if fnmatch.fnmatch(rel, patron) or fnmatch.fnmatch(nombre, patron):
            return True
        if "/" not in patron and patron in partes:
            return True

    return False


def recrear_app_zip(app_dir):
    app_dir.mkdir(parents=True, exist_ok=True)
    zip_path = app_dir / "app.zip"
    temporal = app_dir / "app.zip.tmp"

    if temporal.exists():
        temporal.unlink()

    with zipfile.ZipFile(temporal, "w", compression=zipfile.ZIP_DEFLATED) as paquete:
        for carpeta, subcarpetas, archivos in os.walk(ROOT):
            carpeta_path = Path(carpeta)
            rel_carpeta = carpeta_path.relative_to(ROOT).as_posix()
            if rel_carpeta == ".":
                rel_carpeta = ""

            subcarpetas[:] = [
                subcarpeta
                for subcarpeta in subcarpetas
                if not _ruta_excluida_app_zip(
                    f"{rel_carpeta}/{subcarpeta}".strip("/")
                )
            ]

            for archivo in archivos:
                ruta = carpeta_path / archivo
                rel = ruta.relative_to(ROOT).as_posix()
                if _ruta_excluida_app_zip(rel):
                    continue
                paquete.write(ruta, rel)

    shutil.move(str(temporal), str(zip_path))
    (app_dir / "app.zip.hash").write_text(
        hashlib.sha256(zip_path.read_bytes()).hexdigest(),
        encoding="utf-8",
    )
    return zip_path


def copiar_fuente_limpia(destino):
    destino.mkdir(parents=True, exist_ok=True)

    for carpeta, subcarpetas, archivos in os.walk(ROOT):
        carpeta_path = Path(carpeta)
        rel_carpeta = carpeta_path.relative_to(ROOT).as_posix()
        if rel_carpeta == ".":
            rel_carpeta = ""

        subcarpetas[:] = [
            subcarpeta
            for subcarpeta in subcarpetas
            if not _ruta_excluida_app_zip(f"{rel_carpeta}/{subcarpeta}".strip("/"))
        ]

        for archivo in archivos:
            ruta = carpeta_path / archivo
            rel = ruta.relative_to(ROOT).as_posix()
            if _ruta_excluida_app_zip(rel):
                continue

            salida = destino / rel
            salida.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ruta, salida)


def recrear_app_zip_compilado(app_dir, plataforma):
    flutter_dir = ROOT / "build" / "flutter"
    if not (flutter_dir / "pubspec.yaml").exists():
        raise RuntimeError(
            "Falta build/flutter/pubspec.yaml. Cree primero el build con Flet."
        )

    app_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"ce19_{plataforma.lower()}_app_") as temp:
        fuente = Path(temp) / "app"
        copiar_fuente_limpia(fuente)

        comando = [
            str(dart_ejecutable()),
            "run",
            "serious_python:main",
            "package",
            str(fuente),
            "-p",
            plataforma,
            "--asset",
            "app/app.zip",
            "--skip-site-packages",
            "--compile-app",
            "--cleanup-app",
        ]
        resultado = subprocess.run(comando, cwd=flutter_dir)
        if resultado.returncode != 0:
            raise RuntimeError(f"No se pudo recrear app.zip compilado para {plataforma}.")

    generado = flutter_dir / "app" / "app.zip"
    generado_hash = flutter_dir / "app" / "app.zip.hash"
    zip_path = app_dir / "app.zip"
    hash_path = app_dir / "app.zip.hash"
    if generado.resolve() != zip_path.resolve():
        shutil.copy2(generado, zip_path)
    if generado_hash.resolve() != hash_path.resolve():
        shutil.copy2(generado_hash, hash_path)
    return zip_path


def recrear_app_zip_windows_compilado(app_dir):
    zip_path = recrear_app_zip_compilado(app_dir, "Windows")
    validar_app_zip_windows(zip_path)
    return zip_path


def recrear_app_zip_android_compilado(app_dir):
    zip_path = recrear_app_zip_compilado(app_dir, "Android")
    validar_app_zip_android(zip_path)
    return zip_path


def validar_app_zip_bytes(datos, origen, plataforma=None):
    import io

    errores = []
    with zipfile.ZipFile(io.BytesIO(datos)) as paquete:
        nombres = set(paquete.namelist())
        plataforma = plataforma or "source"

        if plataforma == "windows":
            requeridos = ARCHIVOS_REQUERIDOS_WINDOWS_APP_ZIP
        elif plataforma == "android":
            requeridos = ARCHIVOS_REQUERIDOS_ANDROID_APP_ZIP
        else:
            requeridos = ARCHIVOS_REQUERIDOS_APP_ZIP
        for requerido in requeridos:
            if requerido not in nombres:
                errores.append(f"Falta {requerido} en {origen}")

        if plataforma == "source":
            for archivo, marcadores in MARCADORES_REQUERIDOS_APP_ZIP.items():
                if archivo not in nombres:
                    continue
                contenido = paquete.read(archivo).decode("utf-8", errors="ignore")
                for marcador in marcadores:
                    if marcador not in contenido:
                        errores.append(f"Falta marcador {marcador} en {archivo} de {origen}")

        prohibidos = [
            nombre
            for nombre in nombres
            if nombre.startswith((".git/", ".codex/", ".agents/", "env/", "build/"))
            or fnmatch.fnmatch(nombre.rsplit("/", 1)[-1], "CODIGO-ESCONDIDO-19-*.apk")
            or fnmatch.fnmatch(nombre.rsplit("/", 1)[-1], "CODIGO-ESCONDIDO-19-*.zip")
        ]
        if prohibidos:
            errores.append(f"El paquete incluye rutas excluidas: {prohibidos[:3]}")

    if errores:
        raise RuntimeError("\n".join(errores))


def validar_app_zip(ruta):
    validar_app_zip_bytes(Path(ruta).read_bytes(), str(ruta))


def validar_app_zip_windows(ruta):
    validar_app_zip_bytes(Path(ruta).read_bytes(), str(ruta), plataforma="windows")


def validar_app_zip_android(ruta):
    validar_app_zip_bytes(Path(ruta).read_bytes(), str(ruta), plataforma="android")


def validar_zip_windows(zip_path):
    app_zip = f"{APP_NOMBRE}/data/flutter_assets/app/app.zip"
    with zipfile.ZipFile(zip_path) as paquete:
        nombres = set(paquete.namelist())
        requeridos = [
            f"{APP_NOMBRE}/{APP_NOMBRE}.exe",
            f"{APP_NOMBRE}/flutter_windows.dll",
            app_zip,
        ]
        faltantes = [nombre for nombre in requeridos if nombre not in nombres]
        if faltantes:
            raise RuntimeError("Faltan archivos en Windows ZIP: " + ", ".join(faltantes))
        validar_app_zip_bytes(paquete.read(app_zip), app_zip, plataforma="windows")


def validar_apk_android(apk_path):
    app_zip = "assets/flutter_assets/app/app.zip"
    with zipfile.ZipFile(apk_path) as paquete:
        nombres = set(paquete.namelist())
        if app_zip not in nombres:
            raise RuntimeError(f"Falta {app_zip} dentro del APK")
        validar_app_zip_bytes(paquete.read(app_zip), app_zip, plataforma="android")

    resultado = subprocess.run(
        [str(aapt_ejecutable()), "dump", "badging", str(apk_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    manifiesto = resultado.stdout or ""
    if resultado.returncode != 0:
        raise RuntimeError("No se pudo leer el manifiesto de version del APK.")
    if f"versionCode='{BUILD_NUMBER}'" not in manifiesto:
        raise RuntimeError(f"El APK no usa versionCode {BUILD_NUMBER}.")
    if f"versionName='{VERSION_NATIVA}'" not in manifiesto:
        raise RuntimeError(f"El APK no usa versionName {VERSION_NATIVA}.")


def recrear_app_zip_windows(carpeta_release):
    app_dir = carpeta_release / "data" / "flutter_assets" / "app"
    zip_path = recrear_app_zip_windows_compilado(app_dir)
    return zip_path


def recrear_app_zip_android():
    app_dir = ROOT / "build" / "flutter" / "app"
    return recrear_app_zip_android_compilado(app_dir)


def reconstruir_apk_android_con_app_zip_actualizado():
    flutter_dir = ROOT / "build" / "flutter"
    if not (flutter_dir / "pubspec.yaml").exists():
        raise RuntimeError(
            "Falta build/flutter/pubspec.yaml. Cree primero el build Android con Flet."
        )

    comando = [
        str(flutter_ejecutable()),
        "build",
        "apk",
        "--release",
        "--build-name",
        VERSION_NATIVA,
        "--build-number",
        BUILD_NUMBER,
        "--no-tree-shake-icons",
    ]
    entorno = os.environ.copy()
    entorno["SERIOUS_PYTHON_SITE_PACKAGES"] = str(ROOT / "build" / "site-packages")
    resultado = subprocess.run(comando, cwd=flutter_dir, env=entorno)
    if resultado.returncode != 0:
        raise RuntimeError("No se pudo reconstruir el APK Android con el app.zip corregido.")


def copiar_salida_android():
    recrear_app_zip_android()
    reconstruir_apk_android_con_app_zip_actualizado()

    origen = ROOT / "build" / "flutter" / "build" / "app" / "outputs" / "flutter-apk" / "app-release.apk"
    if not origen.exists():
        origen = ROOT / "build" / "apk" / f"{APP_NOMBRE}.apk"
    if not origen.exists():
        return None

    validar_apk_android(origen)

    destino = ROOT / f"CODIGO-ESCONDIDO-19-Android-{FECHA_ACTUALIZACION}.apk"
    if destino.exists():
        destino.unlink()
    shutil.copy2(origen, destino)
    return destino


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


def main(opcion=None):
    print("\n=== CODIGO ESCONDIDO 19 - Crear instalador ===\n", flush=True)
    sistema_actual = platform.system()
    print(f"Sistema actual: {nombre_sistema(sistema_actual)}\n", flush=True)
    print("Seleccione el sistema operativo destino:\n", flush=True)

    for clave, datos in DESTINOS.items():
        disponible = sistema_actual in datos["sistemas"]
        estado = "disponible" if disponible else "no disponible en este equipo"
        print(f"{clave}. {datos['nombre']} - {estado}", flush=True)

    opcion = (opcion or (sys.argv[1] if len(sys.argv) > 1 else "")).strip()
    if opcion:
        print(f"\nOpcion: {opcion}")
    else:
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
    resultado = subprocess.run(comando, env=entorno, cwd=ROOT)
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
        elif destino == "apk":
            apk_path = copiar_salida_android()
            if apk_path:
                print(f"\nListo. APK: {apk_path}")
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
