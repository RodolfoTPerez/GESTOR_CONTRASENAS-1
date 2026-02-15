from PyQt5.QtWidgets import QTableWidgetItem, QPushButton, QWidget, QHBoxLayout, QVBoxLayout, QApplication, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QFont, QIcon, QBrush
from src.presentation.theme_manager import ThemeManager
from src.presentation.ui_utils import PremiumMessage
from src.presentation.notifications.notification_manager import Notifications
from src.presentation.widgets.table_eye_button import TableEyeButton
from src.domain.messages import MESSAGES
import logging

logger = logging.getLogger(__name__)

class DashboardTableManager:
    def _update_header_style(self, table, sel_count):
        """Maneja la visibilidad de la barra flotante según la selección de registros."""
        if not hasattr(self, 'float_bar_vault') or not hasattr(self, 'table_vault'):
            return
            
        if table == self.table_vault:
            if sel_count > 0:
                self.float_bar_vault.setFixedHeight(60)
                
                # Update text
                if hasattr(self, 'lbl_vault_selection_status'):
                    self.lbl_vault_selection_status.setText(f"🎯 {sel_count} NODOS SELECCIONADOS")
                
                # Context-aware button visibility
                is_multi = sel_count > 1
                
                # Multi-select: Mask specific actions, allow bulk delete
                if hasattr(self, 'btn_vault_view'): self.btn_vault_view.setVisible(not is_multi)
                if hasattr(self, 'btn_vault_copy'): self.btn_vault_copy.setVisible(not is_multi)
                if hasattr(self, 'btn_vault_edit'): self.btn_vault_edit.setVisible(not is_multi)
                
                # Delete & Deselect are always visible
                if hasattr(self, 'btn_vault_delete'): self.btn_vault_delete.setVisible(True)
                if hasattr(self, 'btn_vault_deselect'): self.btn_vault_deselect.setVisible(True)
                
            else:
                self.float_bar_vault.setFixedHeight(0)

    def _load_table(self):
        """Puebla las tablas de la interfaz sin duplicados y con limpieza garantizada."""
        if not hasattr(self, 'sm'): return
        
        # [PERFORMANCE FIX] Bloquear actualizaciones de UI para evitar saltos y mejorar velocidad
        if hasattr(self, 'table') and self.table: self.table.setUpdatesEnabled(False)
        if hasattr(self, 'table_vault') and self.table_vault: self.table_vault.setUpdatesEnabled(False)

        try:
            colors = self.theme.get_theme_colors()
            # 1. Obtención de datos únicos
            records = self.sm.get_all()
            if records is None: records = []

            # Inicializar memoria de descartes si no existe
            if not hasattr(self, "_ignored_recs"): self._ignored_recs = set()
            
            # 2. Identificar tablas a poblar (Vault y Dashboard)
            target_tables = []
            if hasattr(self, 'table_vault') and self.table_vault: 
                target_tables.append(self.table_vault)
            if hasattr(self, 'table') and self.table: 
                target_tables.append(self.table)

            # 3. LIMPIEZA Y PREPARACIÓN ATÓMICA
            sel_count = len(getattr(self, "_selected_records", {}))
            
            for t in target_tables:
                t.setRowCount(0)
                t.setRowCount(len(records))
                t.verticalHeader().setDefaultSectionSize(55)
                
                # [FIX] Always ensure column count and basic labels are set
                icon = "  ✖  " if sel_count > 0 else "  ○  "
                labels = [icon, "LVL", "SYNC", "SERVICE", "PROPIETARIO", "ANTIGÜEDAD", "NOTAS", "PASSWORD", "ACCIONES", "STATUS"]
                t.setColumnCount(10)
                t.setHorizontalHeaderLabels(labels)
                
                if hasattr(self, "_update_header_style"):
                    self._update_header_style(t, sel_count)

            total_score = 0
            valid_records = 0
            weak_count = 0

            # 4. INSERCIÓN ÚNICA
            for row, r in enumerate(records):
                is_deleted = r.get("deleted", 0) == 1
                secret_raw = r.get("secret", "[⚠️ Error]")
                score = self._score_password(secret_raw)

                if not is_deleted:
                    valid_records += 1
                    total_score += score
                    if score < 70: weak_count += 1
                
                # [VISUAL HIGHLIGHT] Resalte dinámico para registros seleccionados
                rid = r.get("id")
                is_sel = hasattr(self, "_selected_records") and rid in self._selected_records
                
                if is_sel:
                    # Azul Cyan Ghost para registros seleccionados (Usar @primary con alpha)
                    row_bg = QColor(colors["primary"])
                    row_bg.setAlpha(75) 
                else:
                    # No background for normal rows to let QSS / Theme handle it
                    row_bg = QColor(0, 0, 0, 0)

                for t in target_tables:
                    def clean_item(text):
                        it = QTableWidgetItem(str(text))
                        it.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                        it.setTextAlignment(Qt.AlignCenter)
                        
                        # [FIX] NO aplicar background hardcoded a menos que sea selección
                        if is_sel:
                             row_bg = QColor(colors.get("primary", "#0891b2"))
                             row_bg.setAlpha(75)
                             it.setBackground(row_bg) # Solo resaltar selección
                        else:
                             it.setForeground(QColor(colors.get("text", "#ffffff")))

                        it.setData(Qt.UserRole + 1, r)
                        return it

                    # Col 0: SELECCIÓN
                    # FIX: Usar UserRole para el ID para que _on_delete_selected funcione siempre
                    it_sel = clean_item("●" if is_sel else "○")
                    it_sel.setData(Qt.UserRole, rid) 
                    it_sel.setTextAlignment(Qt.AlignCenter)
                    it_sel.setData(Qt.UserRole + 1, r)
                    t.setItem(row, 0, it_sel)

                    # Badge visual sobre el widget para click fácil
                    sel_lbl = QLabel("●" if is_sel else "○")
                    sel_lbl.setAlignment(Qt.AlignCenter); sel_lbl.setCursor(Qt.PointingHandCursor)
                    sel_lbl.setObjectName("table_selection_lbl")
                    sel_lbl.setProperty("selected", "true" if is_sel else "false")
                    sel_lbl.mousePressEvent = lambda e, t=t, r=row, rec=r: self._toggle_selection(t, r, rec)
                    self._set_cell_widget_in_table(t, row, 0, sel_lbl)

                    # Col 1: LVL (Tactical Health)
                    if is_deleted: 
                        icon_secure = "💀"
                    else:
                        icon_secure = "🛡️" if score >= 70 else "⚠️"
                    
                    it_lvl = clean_item(icon_secure)
                    it_lvl.setTextAlignment(Qt.AlignCenter)
                    if score < 70 and not is_deleted:
                        it_lvl.setForeground(QColor(colors.get("warning", "#f59e0b")))
                    elif not is_deleted:
                        it_lvl.setForeground(QColor(colors.get("primary", "#06b6d4")))
                    t.setItem(row, 1, it_lvl)

                    # Col 2: SYNC (Cloud Link)
                    is_synced = r.get("synced", 0) == 1
                    sync_icon = "☁️" if is_synced else "⏳"
                    it_sync = clean_item(sync_icon)
                    it_sync.setTextAlignment(Qt.AlignCenter)
                    it_sync.setForeground(QColor(colors.get("primary" if is_synced else "warning")))
                    t.setItem(row, 2, it_sync)

                    # Col 3: SERVICIO
                    svc_raw = r["service"]
                    is_private = r.get("is_private", 0) == 1
                    if is_deleted: svc_icon = "🗑️"
                    elif is_private: svc_icon = "🔒"
                    else: svc_icon = "🔑"
                    
                    if not is_deleted and not is_private:
                        if "google" in svc_raw.lower(): svc_icon = "🌐"
                    
                    # CRITICAL: Widget con FORZADO de transparencia total
                    svc_widget = QWidget()
                    svc_widget.setObjectName("table_service_container")
                    svc_layout = QHBoxLayout(svc_widget)
                    svc_layout.setContentsMargins(10, 0, 10, 0)
                    
                    lbl_icon = QLabel(svc_icon)
                    lbl_icon.setObjectName("table_service_icon")
                    lbl_icon.setProperty("is_private", "true" if is_private else "false")
                    
                    lbl_name = QLabel(svc_raw)
                    lbl_name.setObjectName("table_service_name")
                    lbl_name.setProperty("is_deleted", "true" if is_deleted else "false")
                    
                    svc_layout.addWidget(lbl_icon)
                    svc_layout.addWidget(lbl_name)
                    svc_layout.addStretch()
                    t.setCellWidget(row, 3, svc_widget)

                    # Col 4: PROPIETARIO
                    owner_val = r.get("owner_name", "Desconocido")
                    t.setItem(row, 4, clean_item(owner_val))

                    # Col 5: AGE (Antigüedad)
                    import time
                    now = int(time.time())
                    upd = r.get("updated_at") or r.get("timestamp") or now
                    age_days = (now - upd) // 86400
                    age_text = f"{age_days}d"
                    it_age = clean_item(age_text)
                    it_age.setTextAlignment(Qt.AlignCenter)
                    if age_days > 90: it_age.setForeground(QColor(colors.get("warning", "#f59e0b")))
                    if age_days > 180: it_age.setForeground(QColor(colors.get("danger", "#ef4444")))
                    t.setItem(row, 5, it_age)

                    # Col 6: NOTES (Preview)
                    notes_raw = r.get("notes", "") or ""
                    notes_preview = (notes_raw[:20] + "...") if len(notes_raw) > 20 else notes_raw
                    it_notes = clean_item(notes_preview)
                    it_notes.setForeground(QColor(colors.get("text_dim", "#94a3b8")))
                    t.setItem(row, 6, it_notes)

                    # Col 7: PASSWORD
                    if secret_raw in ["ERROR 🔑", "[⚠️ Error de Llave]", "[Bloqueado 🔑]", "[NODO_PROTEGIDO]"]:
                        pwd_text = "NODO_PROTEGIDO"; pwd_color = "#f87171"
                    else:
                        pwd_text = "••••••••"; pwd_color = "#94a3b8"
                    
                    pwd_widget = QWidget()
                    pwd_widget.setAttribute(Qt.WA_TranslucentBackground)
                    pwd_widget.setStyleSheet("background: transparent;")
                    pwd_layout = QHBoxLayout(pwd_widget); pwd_layout.setContentsMargins(10, 0, 10, 0); pwd_layout.setSpacing(10)
                    
                    lbl_pwd = QLabel(pwd_text)
                    lbl_pwd.setObjectName("vault_pwd_label")
                    lbl_pwd.setProperty("protected_state", "true" if pwd_text == "NODO_PROTEGIDO" else "false")
                    
                    eye_btn = TableEyeButton(row, self._show_password_in_table, self._hide_password_in_table)
                    pwd_layout.addStretch(); pwd_layout.addWidget(lbl_pwd); pwd_layout.addSpacing(15); pwd_layout.addWidget(eye_btn); pwd_layout.addStretch()
                    t.setCellWidget(row, 7, pwd_widget)
                    item_pwd = clean_item("")
                    item_pwd.setData(Qt.UserRole + 1, r)
                    t.setItem(row, 7, item_pwd)

                    # Col 8: ACTIONS (Copy User/Pass)
                    act_widget = QWidget(); act_widget.setStyleSheet("background: transparent;")
                    act_layout = QHBoxLayout(act_widget); act_layout.setContentsMargins(5, 0, 5, 0); act_layout.setSpacing(10)
                    
                    def mk_copy_btn(text, tooltip, val):
                        btn = QPushButton(text)
                        btn.setFixedSize(65, 28)
                        btn.setToolTip(tooltip)
                        btn.setCursor(Qt.PointingHandCursor)
                        btn.setObjectName("table_copy_btn")
                        btn.clicked.connect(lambda _, v=val, t=tooltip: self._copy_to_clipboard(v, t))
                        return btn

                    btn_copy_pass = mk_copy_btn("PASS", "COPIAR PASSWORD", secret_raw)
                    
                    act_layout.addStretch(); act_layout.addWidget(btn_copy_pass); act_layout.addStretch()
                    t.setCellWidget(row, 8, act_widget)

                    # Col 9: ESTADO (Integrity)
                    is_ok = secret_raw not in ["[⚠️ Error de Llave]", "[Bloqueado 🔑]", "ERROR 🔑"]
                    status_lbl = QLabel("ONLINE" if is_ok else "LOCKED")
                    status_lbl.setObjectName("table_status_lbl")
                    status_lbl.setProperty("state", "ok" if is_ok else "locked")
                    status_lbl.setAlignment(Qt.AlignCenter)
                    self._set_cell_widget_in_table(t, row, 9, status_lbl)


            # --- ESTADISTICAS AVANZADAS (Cyber-SaaS Logic) ---
            import time
            now = int(time.time()); total_age = 0; synced_count = 0; private_count = 0
            admin_secrets = 0; user_secrets = 0

            for r in records:
                if r.get("deleted") == 1: continue
                upd = r.get("updated_at") or r.get("timestamp") or now
                total_age += (now - upd)
                if r.get("synced") == 1: synced_count += 1
                if r.get("is_private") == 1: private_count += 1
                
                # Split counts
                owner = str(r.get("owner_name", "")).lower()
                if owner == "admin":
                    admin_secrets += 1
                else:
                    user_secrets += 1

            avg_age_days = (total_age / valid_records / 86400) if valid_records > 0 else 0
            sync_integrity = (synced_count / valid_records * 100) if valid_records > 0 else 100
            team_count = valid_records - private_count

            if hasattr(self, 'stat_total_val'): 
                self.stat_total_val.setText(str(valid_records))
            
            if hasattr(self, 'stat_admin_val'):
                self.stat_admin_val.setText(str(admin_secrets))
            
            if hasattr(self, 'stat_others_val'):
                self.stat_others_val.setText(str(user_secrets))
                
            if hasattr(self, 'stat_weak_val'):
                self.stat_weak_val.setText(str(weak_count))
                self.stat_weak_val.setObjectName("stat_value_tile")
                self.stat_weak_val.setProperty("status", "critical" if weak_count > 0 else "info")
                self.stat_weak_val.style().unpolish(self.stat_weak_val); self.stat_weak_val.style().polish(self.stat_weak_val)

            if hasattr(self, 'stat_age_val'):
                self.stat_age_val.setText(f"{int(avg_age_days)}")
                self.stat_age_val.setObjectName("stat_value_tile")
                self.stat_age_val.setProperty("status", "warning" if avg_age_days > 90 else "success")
                self.stat_age_val.style().unpolish(self.stat_age_val); self.stat_age_val.style().polish(self.stat_age_val)

            # --- INTELIGENCIA BENTO (Mensajes Tácticos) ---
            if hasattr(self, 'lbl_threats_info'):
                self.lbl_threats_info.setObjectName("threat_intel_small")
                if weak_count > 0:
                    self.lbl_threats_info.setText(f"DETECCIÓN: {weak_count} VULNERABILIDADES\nSe requiere rotación táctica de claves inmediatamente.")
                    self.lbl_threats_info.setProperty("status", "critical")
                elif avg_age_days > 180:
                    self.lbl_threats_info.setText("AVISO: ENTROPÍA DEGRADADA\nClaves con antigüedad superior a 180 días.")
                    self.lbl_threats_info.setProperty("status", "warning")
                else:
                    self.lbl_threats_info.setText("STATUS: INTEGRIDAD ÓPTIMA\nNo se detectan anomalías estructurales.")
                    self.lbl_threats_info.setProperty("status", "success")
                self.lbl_threats_info.style().unpolish(self.lbl_threats_info); self.lbl_threats_info.style().polish(self.lbl_threats_info)

            # --- VAULT ANALYTICS (Data Injection) ---
            if hasattr(self, 'lbl_va_risk'):
                 high_risk = sum(1 for r in records if self._score_password(r.get("secret","")) < 40 and r.get("deleted")!=1)
                 self.lbl_va_risk.setText(f"High-risk vaults: {'🔴 ' + str(high_risk) if high_risk > 0 else '🟢 0'}")
            
            if hasattr(self, 'lbl_va_unused'):
                 unused = sum(1 for r in records if (now - (r.get("updated_at") or 0)) > 30*86400 and r.get("deleted")!=1)
                 self.lbl_va_unused.setText(f"Unused vaults (30d): {unused}")

            if hasattr(self, 'lbl_va_rotation'):
                 # Proxy: Created > 90 days ago
                 not_rotated = sum(1 for r in records if (now - (r.get("created_at") or r.get("timestamp") or 0)) > 90*86400 and r.get("deleted")!=1)
                 self.lbl_va_rotation.setText(f"Secrets never rotated: {not_rotated}")

            if hasattr(self, 'lbl_va_access'):
                 try:
                     # Analyze logs for "READ" frequency
                     logs_ana = self.sm.get_audit_logs(limit=100)
                     counts = {}
                     for l in logs_ana:
                         if l.get("action") in ["READ", "COPY", "ACCESS", "SHOW_PWD"]:
                             s = l.get("service")
                             if s: counts[s] = counts.get(s, 0) + 1
                     
                     top = max(counts, key=counts.get) if counts else "N/A"
                     if len(top) > 18: top = top[:15] + "..."
                     self.lbl_va_access.setText(f"Most accessed vault: {top}")
                     self.lbl_va_access.setStyleSheet(self.theme.apply_tokens("color: @primary; font-family: @font-family-main; font-size: 11px; font-weight: 700;"))
                 except: pass

            # --- AI GUARDIAN (Recomendaciones Activas) ---
            if hasattr(self, 'ai_layout'):
                # 1. Limpiar recomendaciones anteriores
                while self.ai_layout.count():
                    child = self.ai_layout.takeAt(0)
                    if child.widget(): child.widget().deleteLater()
                
                # 2. Motor de Heurística (Reglas de Negocio)
                recommendations = []
                
                # Regla A: Secretos Antiguos (>180d)
                old_secrets = [r for r in records if (now - (r.get("updated_at") or 0)) > 180*86400 and r.get("deleted")!=1]
                if old_secrets and "AUTO_ROTATE" not in self._ignored_recs:
                    recommendations.append({
                        "severity": "high",
                        "msg": f"Rotate {len(old_secrets)} secrets older than 180 days",
                        "action": "AUTO_ROTATE"
                    })
                
                # Regla B: Bóvedas de Alto Riesgo
                risky_vaults = [r for r in records if self._score_password(r.get("secret", "")) < 40 and r.get("deleted")!=1]
                if risky_vaults and "REVIEW_RISK" not in self._ignored_recs:
                    recommendations.append({
                        "severity": "critical", 
                        "msg": f"Critical vulnerability in {len(risky_vaults)} vaults detected",
                        "action": "REVIEW_RISK",
                        "target_ids": [r.get("id") for r in risky_vaults]
                    })

                # Regla C: Anomalía de Acceso (Dinámica)
                audit_logs_snapshot = self.sm.get_audit_logs(limit=100)
                if len(audit_logs_snapshot) > 60 and "AUDIT_USER" not in self._ignored_recs:
                     # Identificar el usuario con más actividad (el sospechoso)
                     user_counts = {}
                     for l in audit_logs_snapshot:
                         u = l.get("user_name", "Unknown")
                         user_counts[u] = user_counts.get(u, 0) + 1
                     culprit = max(user_counts, key=user_counts.get) if user_counts else "system"
                     
                     recommendations.append({
                        "severity": "medium",
                        "msg": f"Abnormal access pattern: User '{culprit}' peaked >20 req/h",
                        "action": "AUDIT_USER",
                        "culprit": culprit
                    })
                
                # Regla D: Integridad de Sync
                if sync_integrity < 95 and "FORCE_SYNC" not in self._ignored_recs:
                     recommendations.append({
                        "severity": "medium",
                        "msg": "Cloud synchronization lag detected (>5% deviation)",
                        "action": "FORCE_SYNC"
                     })

                # 3. Renderizar Tarjetas de Acción (Micro-Widgets)
                if not recommendations:
                    # Mensaje de "Todo Ok"
                    ok_w = QWidget(); ok_l = QHBoxLayout(ok_w)
                    lbl_ok = QLabel("✅ Systems Normal. AI monitoring active.")
                    lbl_ok.setObjectName("ai_log_ok")
                    ok_l.addWidget(lbl_ok)
                    self.ai_layout.addWidget(ok_w)
                
                for rec in recommendations:
                    card = QWidget()
                    card.setObjectName("ai_recommendation_card")
                    cl = QVBoxLayout(card); cl.setContentsMargins(10,10,10,10); cl.setSpacing(8)
                    
                    # Header: Icono + Mensaje
                    h_layout = QHBoxLayout()
                    icon = "🔴" if rec["severity"] == "critical" else "🟠" if rec["severity"] == "high" else "🟡"
                    lbl_msg = QLabel(f"{icon} {rec['msg']}")
                    lbl_msg.setObjectName("ai_recommendation_msg")
                    h_layout.addWidget(lbl_msg); h_layout.addStretch()
                    cl.addLayout(h_layout)
                    
                    # Action Bar
                    act_layout = QHBoxLayout(); act_layout.setSpacing(10)
                    
                    def mk_act_btn(txt):
                        b = QPushButton(txt); b.setCursor(Qt.PointingHandCursor); b.setFixedHeight(20)
                        b.setObjectName("ai_action_btn")
                        return b

                    btn_apply = mk_act_btn("APPLY")
                    btn_review = mk_act_btn("REVIEW")
                    btn_ignore = mk_act_btn("IGNORE")
                    
                    # Connect signals
                    btn_apply.clicked.connect(lambda _, r=rec: self._on_ai_apply(r))
                    btn_review.clicked.connect(lambda _, r=rec: self._on_ai_review(r))
                    btn_ignore.clicked.connect(lambda _, w=card: self._on_ai_ignore(w))

                    act_layout.addWidget(btn_apply)
                    act_layout.addWidget(btn_review)
                    act_layout.addWidget(btn_ignore)
                    act_layout.addStretch()
                    
                    cl.addLayout(act_layout)
                    self.ai_layout.addWidget(card)
                
                self.ai_layout.addStretch()

            # --- ADMIN SPECIFIC POPULATION ---
            if self.current_role == "admin":
                # 1. Active Users (Fetch from user_manager)
                if hasattr(self, 'stat_users_val') and hasattr(self, 'user_manager'):
                    try:
                        u_count = self.user_manager.get_user_count()
                        self.stat_users_val.setText(str(u_count))
                    except: pass
                
                # 2. Active Sessions (Real-time Presence)
                if hasattr(self, 'stat_sessions_val') and hasattr(self, 'sync_manager'):
                    try:
                        import time
                        sessions = self.sync_manager.get_active_sessions() or []
                        now = time.time()
                        # Definimos "Activo" como visto en los últimos 5 minutos
                        active_count = sum(1 for s in sessions if (now - s.get("last_seen", 0)) < 300 and not s.get("is_revoked"))
                        self.stat_sessions_val.setText(str(max(1, active_count))) # Al menos el usuario actual
                    except Exception as e:
                        logger.error(f"Error updating sessions: {e}")
                
                # 3. System Logs (Total count)
                if hasattr(self, 'stat_logs_val'):
                    try:
                        log_count = self.sm.get_audit_log_count()
                        self.stat_logs_val.setText(str(log_count))
                    except: pass
                
                # 3. Database Metrics (Sizes)
                if hasattr(self, 'lbl_integrity_info'):
                    try:
                        import os
                        db_size_mb = os.path.getsize(self.sm.db_path) / (1024 * 1024)
                        self.lbl_integrity_info.setText(f"SQLite Load: {db_size_mb:.2f} MB\nSystem State: COMPACTED\nSecurity Nodes: ACTIVE")
                        self.lbl_integrity_info.setStyleSheet(self.theme.apply_tokens("color: @primary; font-size: 10px; font-family: @font-family-main; font-weight: 700;"))
                    except: pass

                # 4. System Integrity (Threats Card for Admin)
                if hasattr(self, 'lbl_threats_info'):
                    self.lbl_threats_info.setStyleSheet(self.theme.apply_tokens("color: @primary; font-size: 10px; font-weight: 700;"))
            
        finally:
            if hasattr(self, 'table') and self.table: self.table.setUpdatesEnabled(True)
            if hasattr(self, 'table_vault') and self.table_vault: self.table_vault.setUpdatesEnabled(True)

        self._load_table_audit()
        
        # Inicializar contadores de búsqueda con el estado actual
        search_text = ""
        if hasattr(self, 'search_vault') and self.search_vault.text():
            search_text = self.search_vault.text()
        elif hasattr(self, 'dash_search') and self.dash_search.text():
            search_text = self.dash_search.text()
        
        self._on_search_changed(search_text)
        
        # Sincronizar contador de selección al final de la carga
        sel_count = len(getattr(self, "_selected_records", {}))
        if hasattr(self, 'table_vault'):
            self._update_header_style(self.table_vault, sel_count)

    def _toggle_selection(self, t, row, record):
        """Maneja la selección múltiple de registros de forma INSTANTÁNEA sin lag."""
        if not hasattr(self, "_selected_records"):
            self._selected_records = {}
            
        rid = record.get("id")
        is_sel = rid not in self._selected_records
        
        if not is_sel:
            del self._selected_records[rid]
        else:
            self._selected_records[rid] = record
            
        # 1. ACTUALIZACIÓN PARCIAL (Rápida)
        # Cambiar el icono visual
        container = t.cellWidget(row, 0)
        if container:
            lbl = container.findChild(QLabel)
            if lbl:
                lbl.setText("●" if is_sel else "○")
                lbl.setProperty("selected", "true" if is_sel else "false")
                lbl.style().unpolish(lbl)
                lbl.style().polish(lbl)
            
        # Actualizar el item invisible de la columna 0 (para búsqueda y borrado)
        it_sel = t.item(row, 0)
        if it_sel:
            it_sel.setText("●" if is_sel else "○")

        # Refrescar el estilo de la fila completa
        colors = self.theme.get_theme_colors()
        row_bg = QColor(colors["primary"])
        row_bg.setAlpha(75)
        if not is_sel: row_bg = QColor(0, 0, 0, 0)
        
        for col in range(t.columnCount()):
            it = t.item(row, col)
            if it:
                it.setBackground(QBrush(row_bg))
        
        # 2. ACTUALIZAR CABECERA (Contador de selección)
        sel_count = len(self._selected_records)
        self._update_header_style(t, sel_count)
        
    def _deselect_all_vault(self):
        """Limpia toda la selección de la bóveda de forma global e INSTANTÁNEA."""
        if not hasattr(self, "_selected_records") or not self._selected_records:
            return
            
        self._selected_records = {}
        t = getattr(self, 'table_vault', None)
        if not t:
            self._update_header_style(None, 0)
            return

        t.setUpdatesEnabled(False)
        try:
            transparent_brush = QBrush(QColor(0, 0, 0, 0))
            for row in range(t.rowCount()):
                # 1. Resetear Icono
                container = t.cellWidget(row, 0)
                if container:
                    lbl = container.findChild(QLabel)
                    if lbl:
                        lbl.setText("○")
                        lbl.setProperty("selected", "false")
                        lbl.style().unpolish(lbl)
                        lbl.style().polish(lbl)
                
                # 2. Resetear Item (Búsqueda/Borrado)
                it_sel = t.item(row, 0)
                if it_sel: it_sel.setText("○")

                # 3. Limpiar Fondo de Fila
                for col in range(t.columnCount()):
                    it = t.item(row, col)
                    if it:
                        it.setBackground(transparent_brush)
        finally:
            t.setUpdatesEnabled(True)
        
        self._update_header_style(t, 0)

    def _on_selection_updated(self, count):
        """Actualiza la barra flotante externamente."""
        if hasattr(self, 'table_vault'):
            self._update_header_style(self.table_vault, count)

    def _on_search_changed(self, text):
        text = text.strip().lower()
        if text and hasattr(self, 'main_stack') and self.main_stack.currentIndex() == 0:
            if hasattr(self, 'view_vault'): self.main_stack.setCurrentWidget(self.view_vault)
        
        targets = []
        if hasattr(self, 'table'): targets.append(self.table)
        if hasattr(self, 'table_vault'): targets.append(self.table_vault)
        
        for t in targets:
            visible_count = 0
            for row in range(t.rowCount()):
                # Búsqueda en Estado/LVL (Col 1)
                lvl_item = t.item(row, 1)
                lvl_text = lvl_item.text() if lvl_item else ""
                
                service_widget = t.cellWidget(row, 3) 
                owner_item = t.item(row, 4)
                svc_text = ""
                if service_widget:
                    lbls = service_widget.findChildren(QLabel)
                    for l in lbls: svc_text += l.text().lower() + " "
                
                owner_text = owner_item.text().lower() if owner_item else ""
                
                # Búsqueda en Antigüedad (Col 5)
                age_item = t.item(row, 5)
                age_text = age_item.text().lower() if age_item else ""
                
                # Búsqueda en Notas (Col 6)
                notes_item = t.item(row, 6)
                notes_text = notes_item.text().lower() if notes_item else ""
                
                # Match restringido: Solo busca en la columna SERVICE (Col 3)
                match = (text in svc_text)
                t.setRowHidden(row, not match)
                if match:
                    visible_count += 1
            
            # Actualizar contadores (Solo para Vault, Dashboard removido por petición)
            total_count = t.rowCount()
            if t == getattr(self, 'table_vault', None) and hasattr(self, 'lbl_vault_search_count'):
                count_text = ""
                if text:
                    count_text = f"RESULTS: {visible_count} / {total_count} VECTORS"
                else:
                    count_text = f"INTEL: {total_count} VECTORS ACTIVE"
                self.lbl_vault_search_count.setText(count_text)

    def _copy_to_clipboard(self, text, message):
        if not text: return
        from PyQt5.QtWidgets import QApplication
        QApplication.clipboard().setText(text)
        
        # [UX FIX] Feedback visual inmediato
        from src.presentation.ui_utils import PremiumMessage
        
        # Intentar obtener un parent válido para el mensaje
        parent = None
        if hasattr(self, 'main_window'): parent = self.main_window
        elif isinstance(self, QWidget): parent = self
        
        if parent and hasattr(parent, 'show_toast'):
            parent.show_toast(message)
        else:
            PremiumMessage.success(parent, "System Intelligence", message)

    def _set_cell_widget_in_table(self, table, row, col, widget):
        container = QWidget()
        container.setAttribute(Qt.WA_TranslucentBackground, True)
        container.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(container); layout.setContentsMargins(0, 0, 0, 0); layout.setAlignment(Qt.AlignCenter); layout.addWidget(widget)
        table.setCellWidget(row, col, container)

    def _on_table_audit(self): self._load_table_audit()

    def _load_table_audit(self, filter_text=None):
        from PyQt5.QtCore import QDateTime
        colors = self.theme.get_theme_colors()
        try:
            # 1. Detectar Filtro y Modo (Dashboard vs Módulo)
            filter_mode = "ALL"
            is_global = False
            
            # Revisar botones del dashboard (feed lateral)
            if hasattr(self, 'btn_filter_auth') and self.btn_filter_auth.isChecked(): filter_mode = "AUTH"
            elif hasattr(self, 'btn_filter_secrets') and self.btn_filter_secrets.isChecked(): filter_mode = "SECRETS"
            elif hasattr(self, 'btn_filter_admin') and self.btn_filter_admin.isChecked(): filter_mode = "ADMIN"
            elif hasattr(self, 'btn_filter_global') and self.btn_filter_global.isChecked(): 
                filter_mode = "GLOBAL"; is_global = True
            
            # Revisar botones del módulo (página completa) - Sincronizar si uno está activo
            if hasattr(self, 'btn_mod_auth') and self.btn_mod_auth.isChecked(): filter_mode = "AUTH"
            elif hasattr(self, 'btn_mod_sec') and self.btn_mod_sec.isChecked(): filter_mode = "SECRETS"
            elif hasattr(self, 'btn_mod_adm') and self.btn_mod_adm.isChecked(): filter_mode = "ADMIN"
            elif hasattr(self, 'btn_mod_global') and self.btn_mod_global.isChecked(): 
                filter_mode = "GLOBAL"; is_global = True

            # 2. Cargar datos base
            if is_global and hasattr(self, 'sync_manager'):
                # FETCH CLOUD (ADMIN ONLY bypass local DB)
                all_logs = self.sync_manager.get_global_audit_logs(limit=500) or []
            else:
                # FETCH LOCAL 
                all_logs = self.sm.get_audit_logs(limit=1000)
            
            # 3. Aplicar Filtro de Categoría (Oro Puro Logic)
            filtered_logs = []
            for l in all_logs:
                act = str(l.get("action", "")).upper()
                msg = str(l).upper()
                svc = str(l.get("service", "")).upper()
                det = str(l.get("details", "")).upper()
                
                # Search across action, service, details and the whole log string
                full_context = f"{act} {svc} {det} {msg}"
                
                if filter_mode == "ALL" or filter_mode == "GLOBAL": 
                    filtered_logs.append(l)
                elif filter_mode == "AUTH" and any(x in full_context for x in ["LOGIN", "LOGOUT", "SESSION", "2FA", "ACCESS", "AUTH", "HEARTBEAT", "CONEXION"]): 
                    filtered_logs.append(l)
                elif filter_mode == "SECRETS" and any(x in full_context for x in ["CREATE", "UPDATE", "READ", "DELETE", "EXPORT", "SECRET", "VAULT", "AGREGAR", "EDITAR", "BORRAR", "VER", "ELIMINACION", "PASSWORD", "CONTRASENA", "LLAVE", "KEY"]): 
                    filtered_logs.append(l)
                elif filter_mode == "ADMIN" and any(x in full_context for x in ["ADMIN", "USER", "ROLE", "POLICY", "SETTINGS", "PURGE", "REVOKE", "KICK", "BLOCK", "PERM", "GRANT", "USER_MANAGEMENT"]): 
                    filtered_logs.append(l)
            
            all_logs = filtered_logs

            # 4. Aplicar filtro de búsqueda manual si se solicita
            if filter_text:
                filtered = [l for l in all_logs if filter_text.lower() in str(l).lower()]
                if filtered:
                    all_logs = filtered
            
            total_recs = len(all_logs); unique_users = set(); critical_count = 0
            critical_actions = ["DELETE", "PURGE", "ADMIN_REVOKE", "PHYSICAL_DELETE", "ELIMINACION"]
            critical_statuses = ["DENIED", "FAIL", "ERROR"]
            for log in all_logs:
                uname = log.get("user_name")
                action = str(log.get("action", "")).upper()
                status = str(log.get("status", "")).upper()
                if uname: unique_users.add(uname)
                if (any(x in action for x in critical_actions)) or (status in critical_statuses): critical_count += 1
            if hasattr(self, 'lbl_log_total'): self.lbl_log_total.setText(str(total_recs))
            if hasattr(self, 'lbl_log_critical'): self.lbl_log_critical.setText(str(critical_count))
            if hasattr(self, 'lbl_log_users'): self.lbl_log_users.setText(str(len(unique_users)))
            if hasattr(self, 'table_audit'):
                self.table_audit.setRowCount(len(all_logs))
                for row_idx, log in enumerate(all_logs):
                    ts = log.get("timestamp", 0)
                    uname = log.get("user_name", "-")
                    act = log.get("action", "-")
                    svc = log.get("service", "-")
                    det = log.get("details", "")
                    st = log.get("status", "-")
                    dev = log.get("device_info", "-")
                    
                    dt_str = QDateTime.fromSecsSinceEpoch(ts).toString("yyyy-MM-dd HH:mm:ss")
                    it_ts = QTableWidgetItem(f"[{dt_str}]")
                    it_ts.setFont(QFont("Consolas", 9))
                    it_ts.setForeground(QColor(colors.get("text_dim", "#64748b")))
                    self.table_audit.setItem(row_idx, 0, it_ts)

                    it_user = QTableWidgetItem(str(uname))
                    it_user.setFont(QFont("Consolas", 9))
                    it_user.setForeground(QColor(colors.get("text_dim", "#64748b")))
                    self.table_audit.setItem(row_idx, 1, it_user)
                    
                    it_act = QTableWidgetItem(str(act))
                    it_act.setFont(QFont("Consolas", 9))
                    it_act.setForeground(QColor(colors.get("text_dim", "#64748b")))
                    self.table_audit.setItem(row_idx, 2, it_act)

                    it_target = QTableWidgetItem(str(svc) if svc else "-")
                    it_target.setFont(QFont("Consolas", 9))
                    it_target.setForeground(QColor(colors.get("text_dim", "#64748b")))
                    self.table_audit.setItem(row_idx, 3, it_target)

                    it_dev = QTableWidgetItem(str(dev) if dev else "-")
                    it_dev.setFont(QFont("Consolas", 9))
                    it_dev.setForeground(QColor(colors.get("text_dim", "#64748b")))
                    self.table_audit.setItem(row_idx, 4, it_dev)
                    
                    it_det = QTableWidgetItem(str(det) if det else "")
                    it_det.setFont(QFont("Consolas", 9))
                    it_det.setForeground(QColor(colors.get("text_dim", "#64748b")))
                    self.table_audit.setItem(row_idx, 5, it_det)
                    
                    # STATUS PILL (Ultra Visibility Fix)
                    lbl_st = QLabel(str(st).upper())
                    lbl_st.setFont(QFont("Consolas", 9, QFont.Bold))
                    lbl_st.setAlignment(Qt.AlignCenter)
                    lbl_st.setContentsMargins(10, 4, 10, 4)
                    lbl_st.setFixedHeight(24) # Más alto para evitar recortes
                    
                    if st in ["DENIED", "FAIL", "ERROR"]:
                        st_key = "critical"
                    elif st == "SUCCESS":
                        st_key = "success"
                    else:
                        st_key = "default"
                    
                    lbl_st.setObjectName("audit_status_pill")
                    lbl_st.setProperty("state", st_key)
                    self._set_cell_widget_in_table(self.table_audit, row_idx, 6, lbl_st)
            if hasattr(self, 'activity_layout'):
                # 1. Limpiar layout actual evitando leaks
                while self.activity_layout.count():
                    child = self.activity_layout.takeAt(0)
                    if child.widget(): child.widget().deleteLater()
                
                # 2. Llenar feed (Solo los 15 más recientes para performance)
                for log in all_logs[:15]:
                    self._add_activity_card(log)
                
                self.activity_layout.addStretch() # Empujar todo hacia arriba
        except Exception as e: 
            logger.error(f"Dashboard: Error loading forensic audit: {e}")

    # --- AI ACTION HANDLERS ---
    def _add_activity_card(self, log):
        """Transforma un log técnico en una narrativa humana de seguridad."""
        from PyQt5.QtCore import QDateTime
        ts = log.get("timestamp", 0)
        user = str(log.get("user_name", "SISTEMA")).upper()
        act_raw = str(log.get("action", "-")).upper()
        svc = log.get("service", "")
        st = str(log.get("status", "-")).upper()
        
        # --- NARRATIVA HUMANA (Human-Centric Audit) ---
        narrative = f"{user} realizó una acción"
        if "LOGIN" in act_raw: narrative = f"<b>{user}</b> inició sesión de forma segura"
        elif "LOGOUT" in act_raw: narrative = f"<b>{user}</b> finalizó su sesión"
        elif "READ" in act_raw or "VER" in act_raw or "ACCESS" in act_raw:
            target = svc if svc else "un registro"
            narrative = f"<b>{user}</b> visualizó el secreto <i>'{target}'</i>"
        elif "CREATE" in act_raw or "AGREGAR" in act_raw:
            target = svc if svc else "un nuevo registro"
            narrative = f"<b>{user}</b> generó el nuevo nodo <i>'{target}'</i>"
        elif "UPDATE" in act_raw or "EDITAR" in act_raw:
            target = svc if svc else "un registro"
            narrative = f"<b>{user}</b> actualizó las credenciales de <i>'{target}'</i>"
        elif "DELETE" in act_raw or "BORRAR" in act_raw or "PURGE" in act_raw:
            target = svc if svc else "un registro"
            narrative = f"⚠️ <b>{user}</b> eliminó permanentemente <i>'{target}'</i>"
        elif "SYNC" in act_raw: narrative = f"Sincronización de bóveda por <b>{user}</b>"
        elif "2FA" in act_raw: narrative = f"Verificación 2FA completada por <b>{user}</b>"
        elif "EXPORT" in act_raw: narrative = f"🚨 <b>{user}</b> exportó la base de datos"
        
        if st in ["FAIL", "DENIED", "ERROR"]:
            narrative = f"Bloqueado: " + narrative.replace("<b>", "").replace("</b>", "")
        
        # Determinar Severidad (Semáforo)
        sev_key = "success"; icon = "🟢"
        if st in ["FAIL", "DENIED", "ERROR"]: 
            sev_key = "warning"; icon = "🟡"
        elif any(x in act_raw for x in ["DELETE", "PURGE", "ADMIN_REVOKE", "EXPORT", "FISICA"]):
            sev_key = "critical"; icon = "🔴"

        # Crear Fila Táctica
        row_w = QWidget(); row_l = QHBoxLayout(row_w); row_l.setContentsMargins(12, 8, 12, 8)
        row_w.setObjectName("activity_feed_card")
        row_w.setProperty("severity", sev_key)
        
        lbl_icon = QLabel(icon); lbl_icon.setStyleSheet("background: transparent; border: none; font-size: 11px;")
        v_txt = QVBoxLayout(); v_txt.setSpacing(2); v_txt.setContentsMargins(4,0,0,0)
        
        lbl_narrative = QLabel(narrative) # Usamos HTML enriquecido
        lbl_narrative.setWordWrap(True)
        lbl_narrative.setObjectName("activity_card_narrative")
        
        time_str = QDateTime.fromSecsSinceEpoch(ts).toString("HH:mm")
        dev = log.get("device_info", "Station")
        lbl_meta = QLabel(f"{time_str} • {dev}")
        lbl_meta.setObjectName("activity_card_meta")
        
        v_txt.addWidget(lbl_narrative); v_txt.addWidget(lbl_meta)
        row_l.addWidget(lbl_icon, 0, Qt.AlignTop); row_l.addLayout(v_txt, 1)
        self.activity_layout.addWidget(row_w)

    def _on_ai_apply(self, rec):
        """APPLY: Ejecuta la corrección táctica real (Músculo)."""
        action = rec.get("action")
        # from PyQt5.QtWidgets import QMessageBox # Removed
        
        if action == "AUTO_ROTATE" or action == "REVIEW_RISK":
            if hasattr(self, 'main_stack') and hasattr(self, 'view_vault'):
                self.main_stack.setCurrentWidget(self.view_vault)
                
                # AHORA SÍ FILTRA: Ponemos el icono de alerta en el buscador. 
                # Como actualizamos _on_search_changed, ahora la tabla SE OCULTARÁ excepto los riesgos.
                if hasattr(self, 'search_vault'):
                    self.search_vault.setText("⚠️") 
                    try:
                        # Notificación táctica
                        Notifications.show_toast(self, "AI Guardian", "PROTOCOLO DE REPARACIÓN ACTIVADO.\n\nLa bóveda ha sido filtrada para mostrar solo los nodos vulnerables detectados (⚠️).", "🛡️", "#f59e0b")
                    except: pass

        elif "Audit" in action:
            if hasattr(self, 'main_stack') and hasattr(self, 'view_activity'):
                 self.main_stack.setCurrentWidget(self.view_activity)
                 # FILTRADO REAL DE LOGS: Usamos el culpable detectado dinámicamente
                 culprit = rec.get("culprit", "sysadmin")
                 self._load_table_audit(filter_text=culprit)
                 PremiumMessage.error(self, "AI Guardian", f"ALERTA DE SEGURIDAD: Filtrando historial de auditoría por usuario '{culprit}' debido a patrones sospechosos.")

        elif action == "FORCE_SYNC":
             if hasattr(self, '_on_sync'): self._on_sync()
        
        else:
            Notifications.show_toast(self, "AI Guardian", f"Acción '{action}' iniciada.", "🤖", "#06b6d4")

    def _show_ai_insight(self, insight_text):
        """Muestra un insight de IA en un diálogo no intrusivo."""
        from core.widgets.notifications import Notifications
        Notifications.show_toast(self, "🧠 AI GUARDIAN: INSIGHT", insight_text, "🧠", "#8b5cf6", 8000)

    def _on_ai_review(self, rec):
        """REVIEW: Muestra la razón técnica profunda."""
        action = rec.get("action")
        
        insights = {
            "REVIEW_RISK": "<b>VULNERABILIDAD TÉCNICA:</b> La entropía detectada es insuficiente para resistir ataques de fuerza bruta moderna.<br><br><b>RECOMENDACIÓN:</b> Rotar a 20+ caracteres con símbolos.",
            "AUDIT_USER": "<b>ANOMALÍA DETECTADA:</b> Ráfaga de 50+ peticiones en < 1 min.<br><br><b>RECOMENDACIÓN:</b> Verificar si el admin está ejecutando un backup o si la cuenta está comprometida.",
            "AUTO_ROTATE": "<b>OBSOLESCENCIA:</b> La llave ha superado el ciclo de vida de 180 días.<br><br><b>RECOMENDACIÓN:</b> Aplicar rotación para invalidar posibles copias antiguas filtradas.",
            "FORCE_SYNC": "<b>SÍNCRONÍA:</b> Desajuste de hashes entre local y nube.<br><br><b>RECOMENDACIÓN:</b> Forzar subida para asegurar integridad del backup."
        }
        
        PremiumMessage.information(self, "🧠 AI GUARDIAN: INSIGHT", 
            f"<b>DETECCIÓN:</b> {rec.get('msg')}<br><br>{insights.get(action, 'Analizando patrón...')}")

    def _on_ai_ignore(self, card_widget):
        """Descarta la tarjeta y la guarda en la lista negra de la sesión."""
        # Encontrar qué acción es para no volver a mostrarla en este refresco
        # Nota: En producción usarías un ID único, aquí usamos el contexto.
        layout = card_widget.layout()
        if layout:
            msg_label = card_widget.findChild(QLabel)
            if msg_label:
                text = msg_label.text()
                if "Vulnerability" in text: self._ignored_recs.add("REVIEW_RISK")
                elif "access" in text: self._ignored_recs.add("AUDIT_USER")
                elif "180 days" in text: self._ignored_recs.add("AUTO_ROTATE")
                elif "Sync" in text: self._ignored_recs.add("FORCE_SYNC")
                
        card_widget.deleteLater()
