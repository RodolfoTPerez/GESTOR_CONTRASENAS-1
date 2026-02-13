import logging
import os
import csv
import json
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QLineEdit, QApplication
from src.domain.messages import MESSAGES
from src.presentation.ui_utils import PremiumMessage

logger = logging.getLogger(__name__)

class DashboardIOActions:
    """Acciones relacionadas con la importación y exportación de datos (CSV, JSON, Excel)."""

    def _on_export(self):
        """Versión Senior Pro: Exportación asíncrona y robusta con reporte detallado."""
        records = self.sm.get_all()
        if not records:
            PremiumMessage.info(self, "Exportar", "No hay registros disponibles para extraer.")
            return

        if not self._verify_action_2fa("Exportar"): return
        
        path, filter_ = QFileDialog.getSaveFileName(
            self, "Exportar Bóveda", "vultrax_backup", 
            "CSV Files (*.csv);;JSON Files (*.json)"
        )
        if not path: return
        
        ext = ".csv" if "csv" in filter_.lower() else ".json"
        if not path.lower().endswith(ext):
            path += ext

        try:
            export_data = []
            for r in records:
                clean_record = {
                    "service": str(r.get("service", "")),
                    "username": str(r.get("username", "")),
                    "password": str(r.get("secret", r.get("password", ""))),
                    "notes": str(r.get("notes", "")),
                    "is_private": int(r.get("is_private", 0))
                }
                export_data.append(clean_record)

            if ext == ".csv":
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["service", "username", "password", "notes", "is_private"])
                    for r in export_data:
                        writer.writerow([
                            r["service"], r["username"], r["password"], r["notes"], r["is_private"]
                        ])
            else:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=4, ensure_ascii=False)
            
            PremiumMessage.success(self, "Exportación Exitosa", 
                f"✅ Se han extraído <b>{len(records)}</b> registros.<br>📂 Destino: <code>{os.path.basename(path)}</code>",
                duration=10000)
                
        except Exception as e:
            logger.error(f"Critical Export Failure: {e}", exc_info=True)
            PremiumMessage.error(self, "Error de Extracción", "No se pudo generar el archivo de exportación.")

    def _on_download_template(self):
        """Genera un archivo CSV de ejemplo."""
        path, _ = QFileDialog.getSaveFileName(self, "Descargar Plantilla de Importación", "plantilla_vultrax.csv", "CSV (*.csv)")
        if not path: return
        
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["service", "username", "password", "notes", "is_private"])
                writer.writerow(["EjemploServicio", "usuario@ejemplo.com", "PasswordSegura123", "Nota opcional", "0"])
            
            PremiumMessage.success(self, "Plantilla Forjada", f"Se ha guardado la plantilla en:\n{path}")
        except Exception as e:
            PremiumMessage.error(self, "Fallo al Forjar Plantilla", str(e))

    def _on_import(self):
        """Versión Senior Pro: Importación masiva con reporte detallado."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Fuente de Datos", "",
            "Formatos Soportados (*.csv *.json *.xlsx *.db);;CSV (*.csv);;JSON (*.json);;Excel (*.xlsx);;SQLite (*.db)"
        )
        if not path: return

        try:
            records = []
            ext = os.path.splitext(path)[1].lower()
            
            if ext == ".db" or path.endswith(".db"):
                ext_pwd, ok = QInputDialog.getText(self, "Recuperación", "Password Maestro de la bóveda externa:", QLineEdit.Password)
                if not ok or not ext_pwd: return
                records = self.sm.import_from_external_vault(path, ext_pwd)
            
            elif ext == ".xlsx":
                try:
                    import pandas as pd
                    records = pd.read_excel(path).fillna("").to_dict('records')
                except ImportError:
                    PremiumMessage.error(self, "Dependencia Faltante", "Para importar archivos Excel (.xlsx) se requiere instalar: pandas y openpyxl")
                    return

            elif ext == ".csv":
                with open(path, 'r', encoding='utf-8-sig') as f:
                    records = list(csv.DictReader(f))
            
            elif ext == ".json":
                with open(path, 'r', encoding='utf-8') as f:
                    records = json.load(f)

            if not records:
                PremiumMessage.warning(self, "Datos Insuficientes", "El archivo no contiene registros procesables.")
                return

            stats = self.sm.bulk_add_secrets(records)
            
            if hasattr(self, '_load_table'):
                self._load_table()
                
            if stats["added"] > 0 and getattr(self, 'internet_online', False):
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(1000, self._on_sync)

            resumen = (f"<b>Misión de Integración Finalizada</b><br><br>"
                       f"✅ Registros Forjados: <b>{stats['added']}</b><br>"
                       f"👯 Duplicados Neutralizados: <b>{stats['skipped']}</b><br>"
                       f"❌ Elementos Corruptos: <b>{stats['errors']}</b>")
            
            PremiumMessage.success(self, "Importación Finalizada", resumen, duration=15000)

        except Exception as e:
            logger.error(f"Professional Import Failure: {e}", exc_info=True)
            PremiumMessage.error(self, "Fallo de Importación", f"No se pudo completar la operación: {e}")
