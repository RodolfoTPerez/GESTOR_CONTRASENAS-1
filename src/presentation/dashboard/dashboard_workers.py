import logging
from PyQt5.QtCore import QThread, pyqtSignal, QDateTime
import hashlib
import time
import string

logger = logging.getLogger(__name__)

class ConnectivityWorker(QThread):
    """Trabajador asíncrono para verificar estados sin congelar la interfaz."""
    status_updated = pyqtSignal(bool, str, str, object, object, bool) # internet, supabase, sqlite, sync_err, audit_err, is_syncing

    def __init__(self, sync_manager, secrets_manager):
        super().__init__()
        self.sync_manager = sync_manager
        self.sm = secrets_manager
        self.running = True

    def run(self):
        while self.running:
            # 1. Internet Check (Ultra rápido)
            internet = self.sync_manager.check_internet()
            
            # 2. Supabase Check (Usa sesión persistente)
            supabase = "🔴 Offline"
            if internet:
                state = "🟢 Online" if self.sync_manager.check_supabase() else "🔴 Offline"
                supabase = f"Supabase: {state}"
            else:
                supabase = "Supabase: 🔴 Offline"
            
            # 3. SQLite Check
            sqlite = "SQLite: 🟢 Online"
            try:
                self.sm.conn.execute("SELECT 1")
            except Exception as e:
                logger.debug(f"SQLite check failed: {e}")
                sqlite = "SQLite: 🔴 Error"

            sync_err = getattr(self.sync_manager, "last_sync_error", None)
            audit_err = getattr(self.sync_manager, "last_audit_error", None)
            is_syncing = getattr(self.sync_manager, "is_busy", False)
            self.status_updated.emit(internet, supabase, sqlite, sync_err, audit_err, is_syncing)
            self.msleep(1000)

    def stop(self):
        self.running = False

class HeuristicWorker(QThread):
    """
    Motor de Heurística de Seguridad (Senior Protocol).
    Analiza la bóveda buscando vulnerabilidades reales sin afectar performance.
    """
    stats_updated = pyqtSignal(dict)

    def __init__(self, sm, um):
        super().__init__()
        self.sm = sm
        self.um = um
        self.running = True

    def run(self):
        # Primer análisis inmediato
        self.trigger_analysis()
        
        while self.running:
            # Ciclo de 5 minutos (300 segundos)
            for _ in range(300):
                if not self.running: break
                self.msleep(1000)
            
            if self.running:
                self.trigger_analysis()

    def trigger_analysis(self):
        """Ejecuta el escaneo heurístico de forma inmediata."""
        stats = self._calculate_real_risk()
        if stats: self.stats_updated.emit(stats)

    def _calculate_real_risk(self):
        try:
            records = self.sm.get_all() or []
            valid_recs = [r for r in records if r.get("deleted", 0) == 0]
            total_count = len(valid_recs)
            
            score_base = 100
            
            # 1. Password Strength Check
            weak_count = 0
            old_count = 0
            secret_hashes = {}
            reused_count = 0
            now = int(time.time())
            
            for r in valid_recs:
                raw = r.get("secret", "")
                if not raw or "[" in raw: continue # Ignorar errores o bloqueados
                
                # Check Weak (< 70 en escala interna)
                if self._internal_score(raw) < 70: weak_count += 1
                
                # Check Stale (> 180 días)
                ts = r.get("updated_at") or r.get("timestamp") or now
                if (now - ts) > (180 * 86400): old_count += 1
                
                # Check Reused
                h = hashlib.md5(raw.encode()).hexdigest()
                secret_hashes[h] = secret_hashes.get(h, 0) + 1
            
            # Count excess records
            reused_count = sum(v - 1 for v in secret_hashes.values() if v > 1)
            
            # -- CÁLCULO DE PENALIZACIONES --
            penalty_weak = 15 if weak_count > 0 else 0
            penalty_reused = 10 if reused_count > 0 else 0
            penalty_old = 10 if old_count > 0 else 0
            
            # -- MFA & ADMIN CHECK --
            admin_no_mfa = 0
            users = []
            try:
                users = self.um.get_users() or [] 
                for u in users:
                    if u.get("role", "").lower() == "admin" and not u.get("totp_secret"):
                        admin_no_mfa += 1
            except Exception as e:
                logger.debug(f"MFA/Admin check failed: {e}")
            
            penalty_mfa = 20 if admin_no_mfa > 0 else 0
            
            # -- LOGIN ATTACK PATTERNS --
            failed_spike = False
            recent_fails = 0
            last_suspicious = "--"
            try:
                logs = self.sm.get_audit_logs(limit=200)
                fails = [l for l in logs if l.get("action") == "LOGIN" and l.get("status") == "FAIL"]
                recent_fails = sum(1 for l in fails if (now - l.get("timestamp",0)) < 86400)
                if recent_fails > 10: failed_spike = True
                
                if fails:
                    last_ts = fails[0].get("timestamp", 0)
                    last_suspicious = QDateTime.fromSecsSinceEpoch(last_ts).toString("hh:mm AP")
            except Exception as e:
                logger.debug(f"Audit log pattern analysis failed: {e}")
            
            penalty_spike = 10 if failed_spike else 0
            
            final_score = score_base - (penalty_weak + penalty_reused + penalty_old + penalty_mfa + penalty_spike)
            final_score = max(0, final_score)
            
            # --- DATA FOR GHOST FIX DIALOG ---
            problematic_records = {
                'reused': {}, # hash -> [records]
                'weak': []    # [records + score]
            }
            for r in valid_recs:
                raw = r.get("secret", "")
                if not raw or "[" in raw: continue
                
                score = self._internal_score(raw)
                if score < 70:
                    r_copy = r.copy()
                    r_copy['score'] = score
                    problematic_records['weak'].append(r_copy)
                
                h = hashlib.md5(raw.encode()).hexdigest()
                if h in secret_hashes and secret_hashes[h] > 1:
                    if h not in problematic_records['reused']:
                        problematic_records['reused'][h] = []
                    problematic_records['reused'][h].append(r)
            
            # Formatear Métricas
            hygiene = 100 - (weak_count / total_count * 100) if total_count > 0 else 100
            mfa_coverage = 100 if admin_no_mfa == 0 else 66 # Simplificado
            
            risk_lvl = "Low"
            if final_score < 60: risk_lvl = "High"
            elif final_score < 85: risk_lvl = "Medium"
            
            return {
                "score": final_score,
                "hygiene": int(hygiene),
                "mfa": int(mfa_coverage),
                "risk": risk_lvl,
                "audit": "OK",
                "weak_count": weak_count,
                "reused_count": reused_count,
                "old_count": old_count,
                "strong_count": max(0, total_count - weak_count - reused_count),
                "total_users": len(users),
                "mfa_users": sum(1 for u in users if u.get("totp_secret")),
                "admin_no_mfa": admin_no_mfa,
                "failed_logins_24h": recent_fails,
                "last_suspicious": last_suspicious,
                "is_critical": final_score < 70,
                "problematic_records": problematic_records
            }
        except Exception as e:
            logger.error(f"Heuristic Analysis Error: {e}")
            return None

    def _internal_score(self, pwd):
        s = 0
        if len(pwd) >= 8: s += 15
        if len(pwd) >= 12: s += 15
        if any(c.isupper() for c in pwd): s += 15
        if any(c.islower() for c in pwd): s += 15
        if any(c.isdigit() for c in pwd): s += 15
        if any(c in string.punctuation for c in pwd): s += 25
        return s
