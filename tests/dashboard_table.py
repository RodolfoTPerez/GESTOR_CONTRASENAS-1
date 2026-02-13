from PyQt5.QtWidgets import QTableWidgetItem, QPushButton, QWidget, QHBoxLayout, QVBoxLayout, QApplication, QLabel
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QIcon, QPixmap, QPainter, QFont
from src.presentation.components.custom_widgets import TableEyeButton
from src.domain.messages import MESSAGES

class DashboardTableManager:
    def _load_table(self):
        is_admin = (self.current_role.upper() == "ADMIN")
        records = self.sm.get_all()
        
        # Sincronizar ambas tablas si existen
        tables = []
        if hasattr(self, 'table'): tables.append(self.table)
        if hasattr(self, 'table_vault'): tables.append(self.table_vault)
        
        for t in tables:
            t.setRowCount(len(records))
            # ALTURA REFINADA: 50px es el punto exacto entre elegancia y densidad
            t.verticalHeader().setDefaultSectionSize(50) 
            t.setWordWrap(False)
            t.setTextElideMode(Qt.ElideRight)

        total_score = 0
        valid_records = 0
        weak_count = 0

        for row, r in enumerate(records):
            is_deleted = r.get("deleted", 0) == 1
            secret_raw = r.get("secret", "[⚠️ Error]")
            score = self._score_password(secret_raw)

            if not is_deleted:
                valid_records += 1
                total_score += score
                if score < 70: weak_count += 1
            
            for t in tables:
                def clean_item(text, col_idx=None):
                    it = QTableWidgetItem(str(text))
                    it.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                    it.setTextAlignment(Qt.AlignCenter)
                    it.setData(Qt.UserRole + 1, r)
                    return it

                # Col 0: SELECCIÓN
                sel_lbl = QLabel("○"); sel_lbl.setAlignment(Qt.AlignCenter); sel_lbl.setCursor(Qt.PointingHandCursor)
                sel_lbl.setStyleSheet("font-size: 14px; color: #64748b; font-weight: bold; padding: 5px;")
                self._set_cell_widget_in_table(t, row, 0, sel_lbl)

                # Col 1: LVL
                icon_secure = "🛡️" if score >= 70 else "⚠️" 
                if is_deleted: icon_secure = "☠️"
                t.setItem(row, 1, clean_item(icon_secure))

                # Col 2: SYNC
                is_synced = r.get("synced", 0) == 1
                sync_icon = "☁️" if is_synced else "⏳"
                t.setItem(row, 2, clean_item(sync_icon))

                # Col 3: SERVICIO
                svc_raw = r["service"]
                svc_icon = "🌐" if "google" in svc_raw.lower() else "🔑"
                if is_deleted: svc_icon = "🗑️"
                
                svc_widget = QWidget(); svc_layout = QHBoxLayout(svc_widget); svc_layout.setContentsMargins(10, 0, 10, 0)
                lbl_icon = QLabel(svc_icon); lbl_icon.setStyleSheet("font-size: 14px; font-family: 'Segoe UI Emoji';")
                lbl_name = QLabel(svc_raw); lbl_name.setStyleSheet("font-weight: 700; font-size: 12px; color: #f1f5f9;")
                if is_deleted: lbl_name.setStyleSheet("text-decoration: line-through; color: #64748b;")
                svc_layout.addWidget(lbl_icon); svc_layout.addWidget(lbl_name); svc_layout.addStretch()
                t.setCellWidget(row, 3, svc_widget)

                # Col 4: USUARIO
                t.setItem(row, 4, clean_item(r["username"]))

                # Col 5: CLAVE (MÁSCARA INTELIGENTE)
                if secret_raw == "[⚠️ Error de Llave]":
                    pwd_text = "ERROR 🔑"
                    pwd_color = "#ef4444"
                else:
                    pwd_text = "••••••••"
                    pwd_color = "#94a3b8"
                
                it_pwd = clean_item(pwd_text)
                it_pwd.setForeground(QColor(pwd_color))
                t.setItem(row, 5, it_pwd)

                # Col 6: ESTADO
                is_ok = secret_raw != "[⚠️ Error de Llave]"
                status_lbl = QLabel("✅" if is_ok else "⛔"); status_lbl.setAlignment(Qt.AlignCenter)
                status_lbl.setStyleSheet("font-size: 12px;")
                self._set_cell_widget_in_table(t, row, 6, status_lbl)

        # Actualizar Dashboard Master Widgets (SaaS Moderno)
        if hasattr(self, 'stat_total_val'):
            self.stat_total_val.setText(str(valid_records))
            
        if hasattr(self, 'stat_weak_val'):
            self.stat_weak_val.setText(str(weak_count))
            self.stat_weak_val.setStyleSheet(f"font-size: 32px; font-weight: 900; color: {'#ef4444' if weak_count > 0 else '#64748b'};")

        if hasattr(self, 'gauge'):
            avg_score = int(total_score / valid_records) if valid_records > 0 else 0
            self.gauge.value = avg_score
            self.gauge.update()
            
        self._load_table_audit()

    def _on_search_changed(self, text):
        text = text.strip().lower()
        targets = []
        if hasattr(self, 'table'): targets.append(self.table)
        if hasattr(self, 'table_vault'): targets.append(self.table_vault)
        
        for t in targets:
            for row in range(t.rowCount()):
                # ÍNDICES ACTUALIZADOS (7 COLUMNAS)
                service_widget = t.cellWidget(row, 3) 
                user_item = t.item(row, 4)
                
                svc_text = ""
                if service_widget:
                    lbl = service_widget.findChild(QLabel)
                    if lbl: svc_text = lbl.text().lower()
                
                user_text = user_item.text().lower() if user_item else ""
                
                match = (text in svc_text) or (text in user_text)
                t.setRowHidden(row, not match)

    def _set_cell_widget_in_table(self, table, row, col, widget):
        container = QWidget()
        container.setAttribute(Qt.WA_TranslucentBackground, True)
        layout = QHBoxLayout(container); layout.setContentsMargins(0, 0, 0, 0); layout.setAlignment(Qt.AlignCenter); layout.addWidget(widget)
        table.setCellWidget(row, col, container)

    def _on_table_audit(self):
        """Metodo de carga de auditoria."""
        self._load_table_audit()

    def _load_table_audit(self):
        """Carga los logs de auditoria FORENCES con estadisticas."""
        from PyQt5.QtCore import QDateTime
        try:
            # 1. Fetch Data (Extended Limit)
            # Intentamos obtener device_info si existe
            try:
                cursor = self.sm.conn.execute("SELECT timestamp, user_name, action, service, details, status, device_info FROM security_audit ORDER BY timestamp DESC LIMIT 1000")
            except:
                # Fallback por si la columna device_info no existe en versiones viejas
                cursor = self.sm.conn.execute("SELECT timestamp, user_name, action, service, details, status, 'Unknown' FROM security_audit ORDER BY timestamp DESC LIMIT 1000")

            all_logs = cursor.fetchall()
            
            # 2. Calculate Statistics
            total_recs = len(all_logs)
            unique_users = set()
            critical_count = 0
            
            critical_actions = ["DELETE", "REVOKE", "ADMIN_REVOKE", "PURGE"]
            critical_statuses = ["DENIED", "FAIL", "ERROR"]

            for row in all_logs:
                # row structure: 0:time, 1:user, 2:action, 3:service, 4:details, 5:status, 6:device
                user = row[1]
                action = row[2]
                status = row[5]
                if user: unique_users.add(user)
                if (action in critical_actions) or (status in critical_statuses):
                    critical_count += 1
            
            # 3. Update UI Stats
            if hasattr(self, 'lbl_log_total'): self.lbl_log_total.setText(str(total_recs))
            if hasattr(self, 'lbl_log_critical'): self.lbl_log_critical.setText(str(critical_count))
            if hasattr(self, 'lbl_log_users'): self.lbl_log_users.setText(str(len(unique_users)))

            # 4. Populate Table (7 Columns)
            if hasattr(self, 'table_audit'):
                self.table_audit.setRowCount(len(all_logs))
                for row_idx, log in enumerate(all_logs):
                    # Data Mapping
                    ts, uname, act, svc, det, st, dev = log[0], log[1], log[2], log[3], log[4], log[5], log[6]
                    
                    # Col 0: Date Full
                    dt_str = QDateTime.fromSecsSinceEpoch(ts).toString("yyyy-MM-dd HH:mm:ss")
                    self.table_audit.setItem(row_idx, 0, QTableWidgetItem(dt_str))
                    
                    # Col 1: User
                    self.table_audit.setItem(row_idx, 1, QTableWidgetItem(str(uname)))
                    
                    # Col 2: Action
                    self.table_audit.setItem(row_idx, 2, QTableWidgetItem(str(act)))
                    
                    # Col 3: Service/Target
                    self.table_audit.setItem(row_idx, 3, QTableWidgetItem(str(svc) if svc else "-"))
                    
                    # Col 4: Device
                    self.table_audit.setItem(row_idx, 4, QTableWidgetItem(str(dev) if dev else "-"))
                    
                    # Col 5: Details
                    self.table_audit.setItem(row_idx, 5, QTableWidgetItem(str(det) if det else ""))
                    
                    # Col 6: Status
                    item_st = QTableWidgetItem(str(st))
                    if st in ["DENIED", "FAIL", "ERROR"]:
                        item_st.setForeground(QColor("#ef4444"))
                    elif st == "SUCCESS":
                        item_st.setForeground(QColor("#10b981"))
                    self.table_audit.setItem(row_idx, 6, item_st)

            # Mini Table (Dashboard) logic remains same if needed, or simplified
            if hasattr(self, 'table_mini_audit'):
                mini_logs = all_logs[:5]
                self.table_mini_audit.setRowCount(len(mini_logs))
                self.table_mini_audit.setColumnCount(3)
                for row, log in enumerate(mini_logs):
                    time_str = QDateTime.fromSecsSinceEpoch(log[0]).toString("HH:mm:ss")
                    self.table_mini_audit.setItem(row, 0, QTableWidgetItem(f"[{time_str}]"))
                    self.table_mini_audit.setItem(row, 1, QTableWidgetItem(str(log[2])))
                    self.table_mini_audit.setItem(row, 2, QTableWidgetItem(str(log[3] or "-")))
                    
        except Exception as e:
            print(f">>> Dashboard: Error al cargar auditoría forense: {e}")
