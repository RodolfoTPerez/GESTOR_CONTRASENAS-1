import secrets
import string
import logging
from PyQt5.QtWidgets import (
    QApplication, QInputDialog, QLineEdit, QDialog, QLabel, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from pathlib import Path
from src.infrastructure.config.path_manager import PathManager
from src.domain.messages import MESSAGES
from src.presentation.ui_utils import PremiumMessage
from src.presentation.notifications.notification_manager import Notifications

# Import extracted actions
from src.presentation.dashboard.dashboard_vault_actions import DashboardVaultActions
from src.presentation.dashboard.dashboard_sync_actions import DashboardSyncActions
from src.presentation.dashboard.dashboard_io_actions import DashboardIOActions

logger = logging.getLogger(__name__)

class DashboardActions(DashboardVaultActions, DashboardSyncActions, DashboardIOActions):
    """
    Controlador de acciones del Dashboard.
    Hereda lógica especializada de gestión de bóveda, sincronización e importación/exportación.
    """

    def _on_ai_audit(self):
        PremiumMessage.success(self, "IDENTIFICACIÓN NEURONAL", "Iniciando análisis profundo de la bóveda...")
        records = self.sm.get_all()
        audit_logs = self.sm.get_audit_logs(limit=500)
        report = self.ai.analyze_vault(records, audit_logs=audit_logs, current_user=self.current_username)
        self.sm.log_event("AI_AUDIT_REQUEST", details=f"Análisis de {len(records)} registros solicitado al Agente Gemini.")
        
        from src.presentation.dialogs.health_dashboard import HealthDashboardDialog
        dlg = HealthDashboardDialog(report, self.ai, self)
        dlg.exec_()

    def _copy_password(self, record):
        QApplication.clipboard().setText(record["secret"])
        self.sm.log_event("COPIAR", record["service"], target_user=record["username"])
        PremiumMessage.success(self, MESSAGES.DASHBOARD.TITLE_COPY, MESSAGES.DASHBOARD.TEXT_COPY_SUCCESS)

    def _show_password_in_table(self, btn):
        if not btn: return
        target_table = self._find_target_table(btn)
        if target_table:
            row = self._find_row_by_pos(target_table, btn)
            if row >= 0:
                item = target_table.item(row, 7)
                pwd_widget = target_table.cellWidget(row, 7)
                if item and pwd_widget: 
                    lbl_pwd = pwd_widget.findChild(QLabel)
                    record = item.data(Qt.UserRole + 1)
                    if record and lbl_pwd:
                        lbl_pwd.setText(record.get("secret", ""))
                        lbl_pwd.setProperty("visible_state", "true")
                        lbl_pwd.style().unpolish(lbl_pwd); lbl_pwd.style().polish(lbl_pwd)
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(100, lambda: self._audit_view(target_table, row))

    def _hide_password_in_table(self, btn):
        if not btn: return
        target_table = self._find_target_table(btn)
        if target_table:
            row = self._find_row_by_pos(target_table, btn)
            if row >= 0:
                pwd_widget = target_table.cellWidget(row, 7)
                if pwd_widget:
                    lbl_pwd = pwd_widget.findChild(QLabel)
                    if lbl_pwd:
                        lbl_pwd.setText("••••••••")
                        lbl_pwd.setProperty("visible_state", "false")
                        lbl_pwd.style().unpolish(lbl_pwd); lbl_pwd.style().polish(lbl_pwd)

    def _find_target_table(self, widget):
        p = widget.parentWidget()
        from PyQt5.QtWidgets import QTableWidget
        while p:
            if isinstance(p, QTableWidget): return p
            p = p.parentWidget()
        return getattr(self, 'table', None)

    def _find_row_by_pos(self, table, widget):
        viewport = table.viewport()
        global_pos = widget.mapToGlobal(widget.rect().center())
        local_pos = viewport.mapFromGlobal(global_pos)
        return table.rowAt(local_pos.y())

    def _audit_view(self, table, row):
        try:
            svc_widget = table.cellWidget(row, 3)
            svc_name = "Servicio Desconocido"
            if svc_widget:
                layout = svc_widget.layout()
                if layout and layout.count() > 1:
                    lbl = layout.itemAt(1).widget()
                    if lbl: svc_name = lbl.text()
            self.sm.log_event("VER", svc_name, details="👁️ Visualización en Dashboard")
            if hasattr(self, '_load_table_audit'): self._load_table_audit()
        except Exception as e:
            logger.debug(f"Audit log event for dashboard view failed: {e}")

    def _on_change_company_name(self):
        """
        [ENTERPRISE SYNC]
        Actualiza el nombre de la compañía al presionar ENTER.
        Sincroniza con SQLite, Supabase y QSettings con feedback al usuario.
        """
        if not hasattr(self, 'txt_company_name'): return
        if getattr(self, 'user_role', 'user').lower() != 'admin':
            from src.presentation.ui_utils import PremiumMessage
            PremiumMessage.error(self, "Acceso Denegado", "Solo el administrador puede cambiar la identidad de la bóveda.")
            return
        
        if not new_name:
            new_name = "It Security" # [UNIFIED] Matching Sentence Case
            self.txt_company_name.setText(new_name)

        try:
            # 1. Guardar en SQLite (Local DB)
            if hasattr(self, 'sm') and self.sm:
                self.sm.set_meta("instance_name", new_name)
                
                # 2. Sincronizar con Supabase (Cloud)
                from src.infrastructure.user_manager import UserManager
                um = UserManager(self.sm)
                
                v_id = self.sm.session.current_vault_id
                if v_id:
                    import threading
                    threading.Thread(target=um.sync_vault_name, args=(v_id, new_name), daemon=True).start()

            # 3. Guardar en QSettings (Compatibilidad y Login Screen)
            from PyQt5.QtCore import QSettings
            from src.presentation.theme_manager import ThemeManager
            settings = QSettings(ThemeManager.APP_ID, "VultraxCore_Global")
            settings.setValue("company_name", new_name)

            # 4. Actualizar HUD Principal inmediatamente
            if hasattr(self, 'lbl_v_name'):
                self.lbl_v_name.setText(new_name)
            
            # 5. Notificar Éxito
            from src.presentation.ui_utils import PremiumMessage
            PremiumMessage.success(self, MESSAGES.SETTINGS.TITLE_SAVED, f"Nombre de compañía actualizado a '{new_name}'. Los cambios se han sincronizado con la nube.")
                
        except Exception as e:
            logger.error(f"Error guardando nombre de compañía: {e}")
            from src.presentation.ui_utils import PremiumMessage
            PremiumMessage.error(self, "Error de Guardado", "No se pudo actualizar el nombre en la base de datos.")
        finally:
            # Revert to read-only state (Preservando estilo de bordes)
            if hasattr(self, 'txt_company_name'):
                self.txt_company_name.setReadOnly(True)
                self.txt_company_name.setStyleSheet(self.theme.apply_tokens("""
                    QLineEdit#settings_input_branding {
                        background: @ghost_white_5;
                        border: 1px solid @border;
                        border-radius: 6px;
                        padding: 6px 12px;
                        color: @text_dim;
                        font-family: @font-family-main;
                        font-size: 11px;
                        font-weight: 500;
                    }
                """))
            if hasattr(self, 'btn_mod_company'):
                self.btn_mod_company.setEnabled(True)
                self.btn_mod_company.setText(MESSAGES.SETTINGS.BTN_MOD) # [UNIFIED] Sentence Case

    def _enable_company_name_edit(self):
        """Habilita la edición del nombre de la compañía/bóveda."""
        if not hasattr(self, 'txt_company_name'): return
        if getattr(self, 'user_role', 'user').lower() != 'admin': return
        
        self.txt_company_name.setReadOnly(False)
        self.txt_company_name.setFocus()
        self.txt_company_name.setStyleSheet(self.theme.apply_tokens("""
            QLineEdit#settings_input_branding {
                background: @ghost_primary_10;
                border: 1px solid @primary;
                border-radius: 6px;
                padding: 6px 12px;
                color: @text;
                font-family: @font-family-main;
                font-size: 11px;
                font-weight: 600;
            }
        """))
        
        if hasattr(self, 'btn_mod_company'):
            self.btn_mod_company.setEnabled(False)
            self.btn_mod_company.setText("Editando...") # [UNIFIED] Sentence Case

    def _on_change_logo(self):
        """
        Permite al usuario subir un logo corporativo (Raster o Vectorial .SVG).
        Aplica renderizado de alta calidad para archivos vectoriales.
        """
        if getattr(self, 'user_role', 'user').lower() != 'admin':
            from src.presentation.ui_utils import PremiumMessage
            PremiumMessage.error(self, "Acceso Denegado", "Solo el administrador puede actualizar el logo corporativo.")
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            MESSAGES.SETTINGS.BTN_CHANGE_LOGO, 
            "", 
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.svg)"
        )
        
        if not file_path:
            return

        try:
            from PyQt5.QtGui import QPixmap, QImage, QPainter
            from PyQt5.QtCore import Qt, QSize
            
            # Detectar si es SVG
            if file_path.lower().endswith(".svg"):
                from PyQt5.QtSvg import QSvgRenderer
                renderer = QSvgRenderer(file_path)
                if not renderer.isValid():
                    from src.presentation.ui_utils import PremiumMessage
                    PremiumMessage.error(self, "Error SVG", "El archivo SVG no es válido o está corrupto.")
                    return
                
                # Renderizar SVG a un QImage de alta resolución (512x512)
                # Esto garantiza nitidez extrema independientemente del archivo fuente
                img = QImage(QSize(512, 512), QImage.Format_ARGB32)
                img.fill(Qt.transparent)
                
                painter = QPainter(img)
                renderer.render(painter)
                painter.end()
                
                pix = QPixmap.fromImage(img)
            else:
                pix = QPixmap(file_path)

            if pix.isNull():
                from src.presentation.ui_utils import PremiumMessage
                PremiumMessage.error(self, "Error de Imagen", "El archivo seleccionado no es una imagen válida.")
                return

            # Destino persistente
            custom_logo_path = PathManager.DATA_DIR / "custom_logo.png"
            
            # 2. Guardar a disco (Normalizado a PNG)
            save_pix = pix.scaled(512, 512, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            save_pix.save(str(custom_logo_path), "PNG")

            # 3. Actualizar Preview en Settings
            if hasattr(self, 'lbl_logo_preview'):
                preview_pix = save_pix.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.lbl_logo_preview.setPixmap(preview_pix)

            # 3c. Actualizar Logo en Header Principal
            if hasattr(self, 'lbl_v_icon'):
                header_pix = save_pix.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.lbl_v_icon.setPixmap(header_pix)

            # 4. Notificar éxito
            from src.presentation.ui_utils import PremiumMessage
            PremiumMessage.success(self, MESSAGES.SETTINGS.TITLE_SAVED, "Logo corporativo actualizado con éxito (Soporte Vectorial Activo).")
            
            # Auditoría
            if hasattr(self, 'sm') and self.sm:
                self.sm.log_event("REBRANDING", "LOGO_UPDATE", details=f"Nuevo logo establecido desde {Path(file_path).name}")

        except Exception as e:
            logger.error(f"Error actualizando el logo: {e}")
            from src.presentation.ui_utils import PremiumMessage
            PremiumMessage.error(self, "Error de Sistema", f"No se pudo procesar el logo: {str(e)}")

    def _verify_action_2fa(self, action_name):
        secret = self.user_profile.get("totp_secret")
        if not secret: secret = self.user_manager.get_user_totp_secret(self.sm.current_user)
        if not secret: return True 
            
        token, ok = QInputDialog.getText(self, MESSAGES.TWOFACTOR.TITLE_VERIFY, f"{MESSAGES.TWOFACTOR.LABEL_TOKEN} {action_name}")
        if ok and token:
            if self.user_manager.verify_totp(str(secret), token.strip()): return True
            else: PremiumMessage.error(self, MESSAGES.TWOFACTOR.TITLE_VERIFY, MESSAGES.TWOFACTOR.ERR_INVALID)
        return False
        
    def _on_panic(self):
        try:
            if hasattr(self, 'sync_manager'):
                self.sync_manager.send_heartbeat(action="EMERGENCY_LOCK", status="LOCKED")
            if hasattr(self, 'sm'): self.sm.cleanup_vault_cache()
            import sys
            sys.exit(0)
        except:
            import sys
            sys.exit(0)

    def _on_change_password(self):
        from src.presentation.change_password_dialog import ChangePasswordDialog
        dlg = ChangePasswordDialog(self.sm, self.user_manager, self.user_profile, self.sync_manager, self)
        dlg.exec_()

    def _on_local_backup(self):
        if not self.sm.get_all():
            PremiumMessage.info(self, MESSAGES.DASHBOARD.TITLE_BACKUP_OK, "No hay nada que respaldar localmente.")
            return
        try:
            path = self.sm.create_local_backup()
            PremiumMessage.success(self, MESSAGES.DASHBOARD.TITLE_BACKUP_OK, MESSAGES.DASHBOARD.TEXT_BACKUP_PATH.format(path=path))
        except Exception as e: PremiumMessage.error(self, MESSAGES.COMMON.TITLE_ERROR, str(e))

    def _on_local_restore(self):
        try:
            from pathlib import Path
            backups_dir = Path(r"C:\PassGuardian_v2\data\backups") / self.current_username.lower()
            backups_dir.mkdir(parents=True, exist_ok=True)
            path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Backup Local", str(backups_dir), "Backup Encriptado (*.enc)")
            if not path: return
            if not PremiumMessage.question(self, "Restaurar Backup", f"¿Estás seguro de restaurar este backup?\n\n{path}\n\nEsto REEMPLAZARÁ todos tus registros actuales."): return
            self.sm.local_restore(backup_path=path)
            self._load_table()
            PremiumMessage.success(self, MESSAGES.DASHBOARD.TITLE_RESTORE_OK, MESSAGES.DASHBOARD.TEXT_RESTORE_LOCAL_SUCCESS)
        except Exception as e: PremiumMessage.error(self, MESSAGES.COMMON.TITLE_ERROR, str(e))

    def _on_length_changed(self, value):
        self.length_label.setText(MESSAGES.DASHBOARD.GEN_CHARS.format(count=value))

    def _generate_password_advanced(self, *args):
        length = self.length_slider.value()
        chars = ""
        if self.cb_upper.isChecked(): chars += string.ascii_uppercase
        if self.cb_lower.isChecked(): chars += string.ascii_lowercase
        if self.cb_digits.isChecked(): chars += string.digits
        if self.cb_symbols.isChecked(): chars += "!@#$%^&*()-_=+[]{}<>?/|\\;:.,~"
        if not chars: return
        pwd = "".join(secrets.choice(chars) for _ in range(length))
        colors = self.theme_manager.get_theme_colors() if hasattr(self, 'theme_manager') else {}
        Notifications.show_toast(self, MESSAGES.DASHBOARD.TITLE_ADDED, pwd, "🔑", colors.get("success", "#10b981"))

    def _on_generate_ai(self):
        prompt = self.input_ai_prompt.text().strip()
        if not prompt:
            PremiumMessage.warning(self, "Entrada Requerida", "Escribe una frase o semilla.")
            return
        try:
            self.btn_generate_ai.setEnabled(False)
            self.btn_generate_ai.setText("PROCESANDO...")
            QApplication.processEvents()
            pwd = self.ai.generate_strategic_password(prompt)
            if pwd:
                self.input_ai_prompt.clear()
                colors = self.theme_manager.get_theme_colors() if hasattr(self, 'theme_manager') else {}
                Notifications.show_toast(self, "IA: Clave Generada", pwd, "⚡", colors.get("success", "#10b981"))
            else:
                PremiumMessage.error(self, "IA: Error", "No se pudo generar la clave.")
        finally:
            self.btn_generate_ai.setEnabled(True)
            self.btn_generate_ai.setText("⚡ GENERAR (AI)")

    def _on_lang_changed(self, index):
        """Maneja el cambio de idioma con confirmación de reinicio."""
        lang = "ES" if index == 0 else "EN"
        lang_name = "Español" if lang == "ES" else "English"
        self.settings.setValue("language", lang)
        
        # Mostrar notificación antes de la pregunta de reinicio
        colors = self.theme_manager.get_theme_colors() if hasattr(self, 'theme_manager') else {}
        Notifications.show_toast(
            self, 
            "Idioma Cambiado" if lang == "ES" else "Language Changed", 
            f"Idioma configurado: {lang_name}. Se requiere reiniciar." if lang == "ES" else f"Language set: {lang_name}. Restart required.",
            "🌐", 
            colors.get("info", "#06b6d4"),
            duration=5000
        )
        
        if PremiumMessage.question(self, MESSAGES.COMMON.TITLE_RESTART, MESSAGES.COMMON.MSG_RESTART):
            self.sm.cleanup_vault_cache()
            if hasattr(self, 'sync_manager'):
                self.sync_manager.send_heartbeat(action="EMERGENCY_LOCK", status="RESTARTING")
            QApplication.quit()
            import sys
            sys.exit(0)

    def _on_lock_time_changed(self):
        """Maneja el cambio de tiempo de bloqueo automático con notificación."""
        lock_map = {0: 1, 1: 5, 2: 10, 3: 30, 4: 60}
        lock_min = lock_map.get(self.combo_lock_time.currentIndex(), 10)
        
        self._save_settings_from_ui(silent=True)
        
        # Mostrar notificación de confirmación
        colors = self.theme_manager.get_theme_colors() if hasattr(self, 'theme_manager') else {}
        Notifications.show_toast(
            self, 
            "Tiempo de Bloqueo Ajustado", 
            f"La aplicación se bloqueará automáticamente después de {lock_min} minuto(s) de inactividad.",
            "⏱️", 
            colors.get("success", "#10b981"),
            duration=6000
        )

    def _on_theme_changed(self, index):
        """Aplica el cambio de tema de forma inmediata."""
        self._save_settings_from_ui(silent=True)

    def _save_settings_from_ui(self, silent=False):
        """Persiste todos los ajustes de la interfaz en QSettings."""
        lang = "ES" if self.combo_lang.currentIndex() == 0 else "EN"
        
        theme_idx = self.combo_theme.currentIndex()
        theme_map = {
            0: "tactical_dark", 
            1: "phantom_glass", 
            2: "bunker_ops", 
            3: "obsidian_flow",
            4: "neon_overdrive",
            5: "saas_commercial"
        }
        theme_code = theme_map.get(theme_idx, "tactical_dark")
        
        lock_map = {0: 1, 1: 5, 2: 10, 3: 30, 4: 60}
        lock_min = lock_map.get(self.combo_lock_time.currentIndex(), 10)
        
        self.settings.setValue("language", lang)
        self.settings.setValue("theme_active", theme_code)
        self.settings.setValue("auto_lock_time", lock_min)
        
        # API Keys
        if hasattr(self, 'input_key_gemini'): self.settings.setValue("ai_key_gemini", self.input_key_gemini.text().strip())
        if hasattr(self, 'input_key_chatgpt'): self.settings.setValue("ai_key_chatgpt", self.input_key_chatgpt.text().strip())
        if hasattr(self, 'input_key_claude'): self.settings.setValue("ai_key_claude", self.input_key_claude.text().strip())
        
        provider = self.combo_provider.currentText()
        self.settings.setValue("ai_provider_active", provider)
        
        # Aplicar cambios Live si es posible
        if hasattr(self, 'theme_manager'):
            self.theme_manager.set_theme(theme_code)
            self.theme_manager.apply_app_theme(QApplication.instance())
            if hasattr(self, '_refresh_all_widget_themes'): self._refresh_all_widget_themes()
        
        if hasattr(self, "_init_watcher"): self._init_watcher()
        
        if not silent:
            colors = self.theme_manager.get_theme_colors() if hasattr(self, 'theme_manager') else {}
            Notifications.show_toast(self, "Settings Synchronized", "Configuración actualizada correctamente.", "⚙️", colors.get("primary", "#06b6d4"))

    def _on_sync_audit(self):
        """Refresca el historial de auditoría sincronizando opcionalmente con la nube."""
        if hasattr(self, '_load_table_audit'):
            self._load_table_audit()
        colors = self.theme_manager.get_theme_colors() if hasattr(self, 'theme_manager') else {}
        Notifications.show_toast(self, "Auditoría", "Historial sincronizado.", "📜", colors.get("primary", "#06b6d4"))

    def _on_repair_vault_dashboard(self):
        """Dispara el protocolo de reparación de integridad de la bóveda."""
        from src.presentation.dialogs.ghost_fix_dialog import GhostFixDialog
        issues = getattr(self, 'last_heuristic_issues', {})
        if not issues:
            PremiumMessage.info(self, "Integridad", "No se detectaron problemas críticos que requieran reparación inmediata.")
            return
        dlg = GhostFixDialog(issues, self.sm, self)
        dlg.exec_()

    def _on_purge_private(self):
        """Eliminación física permanente de todos los registros privados del usuario."""
        if PremiumMessage.question(self, "ZONA DE PELIGRO", "Esto eliminará permanentEMENTE todos tus registros privados de este equipo y la nube.\n\n¿Deseas continuar?"):
            try:
                self.sm.physical_purge_private()
                self._load_table()
                PremiumMessage.success(self, "Purga Completada", "Todos los registros privados han sido eliminados.")
            except Exception as e:
                PremiumMessage.error(self, "Error de Purga", str(e))

    def _on_settings(self):
        """Navega a la página de ajustes."""
        if hasattr(self, 'main_stack') and hasattr(self, 'view_settings'):
            self.main_stack.setCurrentWidget(self.view_settings)

    def _on_dash_search_return(self):
        """Acción rápida al presionar enter en la búsqueda del dashboard."""
        if hasattr(self, 'main_stack') and hasattr(self, 'view_vault'):
            self.main_stack.setCurrentWidget(self.view_vault)
            if hasattr(self, 'search_vault'):
                self.search_vault.setText(self.dash_search.text())
                self.search_vault.setFocus()

    def _get_last_selected_record(self):
        """Obtiene el último registro seleccionado de la memoria de la sesión."""
        sel = getattr(self, "_selected_records", {})
        if not sel: return None
        rid = list(sel.keys())[-1]
        return sel[rid]

    def _on_copy_selected(self):
        """Copia la clave del nodo seleccionado."""
        record = self._get_last_selected_record()
        if record: self._copy_password(record)

    def _on_view_selected(self):
        """Abre la vista de detalles (diálogo de edición) del nodo seleccionado."""
        record = self._get_last_selected_record()
        if record: self._on_edit_row(record)

    def _on_edit_selected(self):
        """Inicia el protocolo de edición para el nodo seleccionado."""
        record = self._get_last_selected_record()
        if record: self._on_edit_row(record)

    def _on_delete_selected(self):
        """Ejecuta el protocolo de eliminación para los nodos seleccionados."""
        sel = getattr(self, "_selected_records", {})
        if not sel: return
        
        record = self._get_last_selected_record()
        if not record: return

        # Swap temporal de tabla para que DashboardVaultActions._on_delete encuentre la fila correcta
        old_table = getattr(self, "table", None)
        self.table = self.table_vault
        
        try:
            # Buscar la fila y seleccionarla para que currentRow() funcione
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if item and item.data(Qt.UserRole) == record.get("id"):
                    self.table.setCurrentCell(row, 0)
                    break
            
            self._on_delete()
        finally:
            self.table = old_table

    def _on_table_cell_clicked(self, row, col):
        """Maneja el click en una celda de la tabla para mostrar detalles si es necesario."""
        pass # Por ahora delegamos a las acciones específicas de cada botón en la fila

    def _on_header_clicked(self, col):
        """Maneja el click en la cabecera para ordenamiento o selección masiva."""
        pass
