from core.backup_datos import crear_backup_datos, listar_backups, restaurar_backup
from core.diagnostico_app import crear_reporte_diagnostico, reporte_como_texto
from core.reparador_datos import analizar_datos, reparar_datos, reporte_reparacion_como_texto
from core.error_logger import leer_ultimos_errores, limpiar_log_errores, ruta_log
from core.limpieza_app import reporte_limpieza, reporte_limpieza_texto, ejecutar_limpieza_segura


class MantenimientoService:
    """Centraliza acciones de mantenimiento para que Guardados no dependa
    directamente de muchos módulos core.
    """

    def crear_backup_manual(self):
        return crear_backup_datos("manual")

    def listar_backups(self, limite=30):
        return listar_backups(limite)

    def restaurar_backup(self, carpeta, crear_respaldo_actual=True):
        return restaurar_backup(carpeta, crear_respaldo_actual=crear_respaldo_actual)

    def crear_diagnostico(self):
        reporte = crear_reporte_diagnostico()
        return reporte, reporte_como_texto(reporte)

    def analizar_reparacion(self):
        reporte = analizar_datos()
        return reporte, reporte_reparacion_como_texto(reporte)

    def reparar_datos(self, aplicar=True):
        return reparar_datos(aplicar=aplicar)

    def reporte_reparacion_texto(self, reporte):
        return reporte_reparacion_como_texto(reporte)

    def leer_log_errores(self):
        return leer_ultimos_errores(), ruta_log()

    def limpiar_log_errores(self):
        return limpiar_log_errores()

    def crear_reporte_limpieza(self):
        reporte = reporte_limpieza()
        return reporte, reporte_limpieza_texto(reporte)

    def texto_limpieza(self, reporte):
        return reporte_limpieza_texto(reporte)

    def ejecutar_limpieza_segura(self, mantener_backups=10, max_log_kb=512):
        return ejecutar_limpieza_segura(
            mantener_backups=mantener_backups,
            max_log_kb=max_log_kb,
        )
