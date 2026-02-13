import logging
from PyQt5.QtWidgets import QDialog
from src.domain.messages import MESSAGES
from src.presentation.ui_utils import PremiumMessage
from src.presentation.dialogs.service_dialog import ServiceDialog

logger = logging.getLogger(__name__)

class DashboardVaultActions:
    """Acciones relacionadas con la gestión de registros en la bóveda."""
    
    def _on_add(self):
        dlg = ServiceDialog(self, "Agregar servicio", secrets_manager=self.sm, app_user=self.current_username, user_role=self.user_role, settings=self.settings, guardian_ai=self.ai)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            try:
                sid = self.sm.add_secret(
                    data["service"], data["username"], data["secret"], 
                    data["notes"], is_private=data.get("is_private", 0)
                )
                self.sm.log_event("AGREGAR", data["service"], details=f"Usuario: {data['username']}")
                self._load_table()
                if hasattr(self, 'dash_search'):
                    self.dash_search.clear()
                
                # Sincronización asíncrona (Sin lag)
                if hasattr(self, '_sync_async'):
                    self._sync_async(sid)
                
                # Actualizar radar si existe
                if hasattr(self, 'heuristic_worker'):
                    self.heuristic_worker.trigger_analysis()
                
                PremiumMessage.success(self, MESSAGES.DASHBOARD.TITLE_ADDED, MESSAGES.DASHBOARD.TEXT_ADDED)
            except Exception as e:
                PremiumMessage.error(self, MESSAGES.COMMON.TITLE_ERROR, str(e))

    def _get_service_name_from_row(self, row):
        """Método auxiliar para extraer el nombre del servicio desde el widget compuesto (Card-Row)."""
        try:
            # En el modelo Card-Row, la celda 3 es un Widget con layout [Icono, Nombre]
            svc_widget = self.table.cellWidget(row, 3)
            if svc_widget:
                layout = svc_widget.layout()
                if layout and layout.count() > 1:
                    lbl = layout.itemAt(1).widget() # El índice 1 es el nombre
                    if lbl: return lbl.text().strip()
            
            # Fallback para el modelo antiguo (si existe)
            item = self.table.item(row, 3)
            if item: return item.text().replace("🔐 ", "").replace("🔑 ", "").replace("🏢 ", "").replace(" (MARCADO PARA BORRAR)", "").strip()
        except: pass
        return None

    def _on_edit(self):
        row = self.table.currentRow()
        if row < 0:
            PremiumMessage.info(self, MESSAGES.DASHBOARD.TITLE_EDIT_REQ, MESSAGES.DASHBOARD.TEXT_EDIT_REQ)
            return
        
        service = self._get_service_name_from_row(row)
        if not service: return

        username = self.table.item(row, 4).text().strip()
        
        record = self.sm.get_record(service, username)
        if record:
            # BLOQUEO DE SEGURIDAD PARA EXPERTO SENIOR
            if "[Bloqueado 🔑]" in record["secret"]:
                PremiumMessage.error(self, "Acceso Denegado", 
                    "No puedes editar este registro porque tu llave actual no lo reconoce.\n\n"
                    "Por favor, solicita al administrador que re-vincule tu acceso o realiza un 'Sincronizar' si hay cambios pendientes.")
                return
            
            # [PRIVACY FIX] Validar propiedad - Solo el dueño puede editar
            owner = record.get("owner_name", "").upper()
            if owner and owner != self.current_username.upper():
                PremiumMessage.error(self, "Solo Lectura", 
                    f"Este registro pertenece a {owner}.\n\n"
                    "Los registros compartidos son de solo lectura.\n"
                    "Solo el propietario puede editarlos.")
                return
            
            self._on_edit_row(record)

    def _on_edit_row(self, record):
        # [PRIVACY FIX] Validar propiedad - Solo el dueño puede editar
        owner = record.get("owner_name", "").upper()
        if owner and owner != self.current_username.upper():
            PremiumMessage.error(self, "Solo Lectura", 
                f"Este registro pertenece a {owner}.\n\n"
                "Los registros compartidos son de solo lectura.\n"
                "Solo el propietario puede editarlos.")
            return
        
        dlg = ServiceDialog(self, "Editar servicio", record, secrets_manager=self.sm, app_user=self.current_username, user_role=self.user_role, settings=self.settings, guardian_ai=self.ai)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            try:
                self.sm.update_secret(
                    record["id"], data["service"], data["username"], 
                    data["secret"], data["notes"], is_private=data.get("is_private", 0)
                )
                self.sm.log_event("EDITAR", data["service"], target_user=data["username"])
                self._load_table()
                
                # Sincronización asíncrona
                if hasattr(self, '_sync_async'):
                    self._sync_async(record["id"])
                
                if hasattr(self, 'heuristic_worker'):
                    self.heuristic_worker.trigger_analysis()
                    
                PremiumMessage.success(self, MESSAGES.DASHBOARD.TITLE_UPDATED, MESSAGES.DASHBOARD.TEXT_UPDATED)
            except Exception as e:
                PremiumMessage.error(self, MESSAGES.COMMON.TITLE_ERROR, str(e))

    def _on_delete(self):
        row = self.table.currentRow()
        if row < 0:
            PremiumMessage.info(self, MESSAGES.DASHBOARD.TITLE_DELETE_REQ, MESSAGES.DASHBOARD.TEXT_DELETE_REQ)
            return

        is_admin = (self.current_role == "admin")
        
        try:
            service = self._get_service_name_from_row(row)
            user_item = self.table.item(row, 4)
            
            if not service or not user_item: return

            username = user_item.text().strip()
            record = self.sm.get_record(service, username)
            if not record: return

            # [PRIVACY FIX] Validar propiedad - Solo el dueño puede eliminar (excepto admin)
            owner = record.get("owner_name", "").upper()
            if not is_admin and owner and owner != self.current_username.upper():
                PremiumMessage.error(self, "Solo Lectura", 
                    f"Este registro pertenece a {owner}.\n\n"
                    "Los registros compartidos son de solo lectura.\n"
                    "Solo el propietario puede eliminarlos.")
                return

            if is_admin:
                # El ADMIN elimina de verdad (Hard Delete de todo)
                if PremiumMessage.question(self, MESSAGES.DASHBOARD.TITLE_DELETE_CONFIRM, MESSAGES.DASHBOARD.TEXT_DELETE_CONFIRM_ADMIN.format(service=service)):
                    # [CORE FIX] ELIMINAR DE NUBE PRIMERO (Necesita el registro local para saber el ID cloud)
                    if getattr(self, 'internet_online', False):
                        if hasattr(self, 'sync_manager'):
                            self.sync_manager.delete_from_supabase(record["id"])
                    
                    self.sm.hard_delete_secret(record["id"])
                    self.sm.log_event("ELIMINACION FISICA", service, target_user=username)
                    self._load_table()
                    PremiumMessage.success(self, MESSAGES.DASHBOARD.TITLE_SYNC_COMPLETE, MESSAGES.DASHBOARD.TEXT_DELETE_SUCCESS)
            else:
                # El USUARIO normal
                if record.get("is_private") == 1:
                    # Si el registro es PRIVADO: Eliminación PERMANENTE permitida al dueño
                    if PremiumMessage.question(self, "Eliminar Registro Privado", f"¿Estás seguro de eliminar PERMANENTEMENTE '{service}'?\nSe borrará de tu equipo y de la nube."):
                        # [CORE FIX] ELIMINAR DE NUBE PRIMERO
                        if getattr(self, 'internet_online', False):
                            if hasattr(self, 'sync_manager'):
                                self.sync_manager.delete_from_supabase(record["id"])
                            
                        self.sm.hard_delete_secret(record["id"])
                        self.sm.log_event("ELIMINACION PRIVADA FISICA", service)
                        self._load_table()
                        PremiumMessage.success(self, "Eliminado", "Registro privado eliminado permanentemente.")
                else:
                    # Si el registro es PÚBLICO: Solo Marca (Soft Delete)
                    if record.get("deleted", 0) == 1:
                        return
                        
                    if PremiumMessage.question(self, MESSAGES.DASHBOARD.TITLE_SOFT_DELETE, "Confirmar eliminación"):
                        self.sm.delete_secret(record["id"])
                        self.sm.log_event("MARCADO PARA BORRAR", service, target_user=username)
                        self._load_table()
                        
                        # Sincronización instantánea
                        if getattr(self, 'internet_online', False):
                            if hasattr(self, 'sync_manager'):
                                self.sync_manager.sync_single_record(record["id"])
                                self._load_table() 
                        
                        PremiumMessage.success(self, MESSAGES.DASHBOARD.TITLE_SOFT_DELETE, "Eliminado exitosamente.")
        except Exception as e:
            PremiumMessage.error(self, MESSAGES.COMMON.TITLE_ERROR, str(e))
            
    def _on_restore_row(self, record):
        if PremiumMessage.question(self, MESSAGES.DASHBOARD.TITLE_RESTORE, MESSAGES.DASHBOARD.TEXT_RESTORE_CONFIRM.format(service=record['service'])):
            try:
                self.sm.restore_secret(record["id"])
                self._load_table()
                
                # Sincronización asíncrona
                if hasattr(self, '_sync_async'):
                    self._sync_async(record["id"])
                    
                PremiumMessage.success(self, MESSAGES.DASHBOARD.TITLE_RESTORE, MESSAGES.DASHBOARD.TEXT_RESTORE_SUCCESS)
            except Exception as e:
                PremiumMessage.error(self, MESSAGES.COMMON.TITLE_ERROR, str(e))
