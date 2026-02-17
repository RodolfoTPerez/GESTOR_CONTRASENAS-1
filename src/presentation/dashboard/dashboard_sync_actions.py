import logging
from PyQt5.QtWidgets import QProgressDialog, QApplication
from PyQt5.QtCore import Qt
from src.domain.messages import MESSAGES
from src.presentation.ui_utils import PremiumMessage
from src.presentation.notifications.notification_manager import Notifications

logger = logging.getLogger(__name__)

class DashboardSyncActions:
    """Acciones relacionadas con la sincronización y respaldo en la nube."""

    def _sync_async(self, record_id):
        """Sincronización en segundo plano (Ghost Sync) para evitar lag en la UI."""
        logger.info(f"[SYNC] _sync_async called for record_id: {record_id}")
        
        if not getattr(self, 'internet_online', False):
            logger.warning(f"[SYNC] Skipping sync - internet_online is False")
            return
        
        logger.info(f"[SYNC] Internet is online, starting background sync thread")
            
        from threading import Thread
        def run_sync():
            try:
                logger.info(f"[SYNC] Thread started for record {record_id}")
                if hasattr(self, 'sync_manager'):
                    logger.info(f"[SYNC] Calling sync_manager.sync_single_record({record_id})")
                    self.sync_manager.sync_single_record(record_id)
                    logger.info(f"[SYNC] sync_single_record completed for {record_id}")
                else:
                    logger.error(f"[SYNC] No sync_manager attribute found!")
                    
                # Refrescar la tabla de forma segura para actualizar el icono de sync
                if hasattr(self, 'sync_finished'):
                    self.sync_finished.emit()
            except Exception as e:
                logger.error(f"Ghost Sync Error for record {record_id}: {e}", exc_info=True)
        
        Thread(target=run_sync, daemon=True).start()

    def _full_sync_async(self):
        """Ejecuta una sincronización bidireccional completa en segundo plano (Silent Startup)."""
        if not getattr(self, 'internet_online', False):
            return

        from threading import Thread
        def run():
            try:
                if hasattr(self, 'sync_manager') and self.sync_manager:
                    # Sincronizar usuarios creados offline primero
                    synced_users = self.sync_manager.sync_pending_users()
                    if synced_users > 0:
                        logger.info(f"Synced {synced_users} offline user(s) during startup")
                    
                    # Luego sincronizar registros
                    self.sync_manager.sync(cloud_user_id=self.user_profile.get("id"))
                logger.info("Silent Startup Sync Completed.")
            except Exception as e:
                logger.error(f"Silent Startup Sync Error: {e}")

        Thread(target=run, daemon=True).start()

    def _auto_sync_on_login(self):
        """Manejador para el timer de auto-sincronización periódica."""
        logger.info("Auto-Sync: Ejecutando ciclo de sincronización en segundo plano.")
        self._full_sync_async()

    def _delete_async(self, record_id):
        """Borrado en la nube en segundo plano."""
        if not getattr(self, 'internet_online', False): return
        from threading import Thread
        def run_del():
            try:
                if hasattr(self, 'sync_manager'):
                    self.sync_manager.delete_from_supabase(record_id)
            except Exception as e:
                logger.error(f"Async Delete Error: {e}")
        Thread(target=run_del, daemon=True).start()

    def _on_backup(self):
        records = self.sm.get_all()
        if not records:
            PremiumMessage.info(self, MESSAGES.COMMON.TITLE_INFO, MESSAGES.DASHBOARD.NO_LOCAL_DATA)
            return
        self._run_sync_op(MESSAGES.DASHBOARD.TITLE_BACKUP_CLOUD, self.sync_manager.backup_to_supabase)

    def _on_restore(self):
        if not getattr(self, 'internet_online', False):
            PremiumMessage.error(self, MESSAGES.COMMON.TITLE_ERROR, MESSAGES.LOGIN.TITLE_OFFLINE_ERROR)
            return
        self._run_sync_op(MESSAGES.DASHBOARD.TITLE_RESTORE_CLOUD, self.sync_manager.restore_from_supabase)

    def _on_sync(self):
        """Sincronización Bidireccional Inteligente + Registro en Auditoría."""
        if not getattr(self, 'internet_online', False):
            PremiumMessage.error(self, MESSAGES.COMMON.TITLE_ERROR, "No puedes sincronizar sin conexión a internet.")
            return

        def sync_operation(progress_callback):
            stats = self.sync_manager.sync(
                progress_callback=progress_callback, 
                cloud_user_id=self.user_profile.get("id")
            )
            self.sm.log_event("SYNC_BIDIRECCIONAL", details="Sincronización manual ejecutada")
            return stats

        self._run_sync_op(MESSAGES.DASHBOARD.TITLE_SYNC_CLOUD, sync_operation, show_summary=True)

    def _run_sync_op(self, title, func, show_summary=False):
        progress = None
        stats = None
        try:
            self.syncing_active = True
            progress = QProgressDialog(MESSAGES.DASHBOARD.PROGRESS_STARTING.format(title=title), "Cancelar", 0, 100, self)
            progress.setWindowTitle(title)
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.setAutoClose(False)
            progress.show()
            
            def cb(val, msg):
                if progress and not progress.wasCanceled():
                    progress.setValue(val)
                    progress.setLabelText(msg)
                    if val % 5 == 0:
                        QApplication.processEvents()
            
            QApplication.processEvents()
            stats = func(progress_callback=cb)
            
            if hasattr(self, '_load_table'):
                self._load_table()
            
            if show_summary and isinstance(stats, dict):
                if progress: progress.close()
                progress = None
                
                up = stats.get('uploaded', 0)
                down = stats.get('downloaded', 0)
                err = stats.get('errors', 0)
                
                if up > 0 or down > 0 or err > 0:
                    msg = (f"Operación finalizada correctamente.\n\n"
                           f"⬆️ Subidos: {up}\n"
                           f"⬇️ Descargados: {down}\n"
                           f"⚠️ Errores: {err}")
                    PremiumMessage.success(self, "Reporte de Sincronización", msg)
                else:
                    Notifications.show_toast(self, "Sincronización al día", "Bóveda sincronizada. Sin cambios pendientes.", "🔄", "#10b981")
            else:
                if progress: progress.close()
                progress = None
                PremiumMessage.success(self, MESSAGES.DASHBOARD.TITLE_SYNC_COMPLETE, MESSAGES.DASHBOARD.TEXT_SYNC_OP_SUCCESS.format(title=title))
                
        except Exception as e:
            err_text = str(e)
            logger.error(f"SYNC ERROR: {err_text}")
            if "internet" in err_text.lower() or "conexión" in err_text.lower():
                PremiumMessage.error(self, "Fallo de Red", "No se pudo contactar con la nube. Revisa tu conexión.")
            else:
                PremiumMessage.error(self, "Error de Sincronización", str(e))
        finally:
            if progress:
                progress.close()
            self.syncing_active = False
            if hasattr(self, 'status_sync') and hasattr(self, 'table'):
                self.status_sync.setText("⬆️⬇️ Cantidad de Secretos: " + str(self.table.rowCount()))
