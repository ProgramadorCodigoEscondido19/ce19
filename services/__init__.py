"""Servicios reutilizables para Codigo Escondido 19."""

try:
    from .app_paths import AppPaths
    from .biblia_service import BibliaService, CATEGORIAS_RANDOM_BIBLIA
    from .codificador_service import CodificadorService
except Exception:
    # Evita que un import parcial bloquee el arranque de la app.
    pass
