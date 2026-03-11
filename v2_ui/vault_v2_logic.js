let sysBridge = null;
let vaultBridge = null;
let api = null;
let userListCache = null; // HUD 2.2: User fetching optimization
let lastUserFetchTime = 0;
const CACHE_TTL = 30000; // 30 seconds
// Central Navigation Bridge
let records = [];
let selectedRecord = null;
let selectedRow = null;
let CURRENT_LANG = 'EN'; // Default
let I18N_BUNDLE = {};

function T(key, fallback = '') {
    // 1. Search in the dynamic bundle from Python (Nested by Section)
    if (key.includes('.')) {
        const [section, k] = key.split('.');
        if (I18N_BUNDLE[section] && I18N_BUNDLE[section][k]) {
            return I18N_BUNDLE[section][k];
        }
    } else {
        // Try searching in all sections if no dot provided (fallback for existing flat keys)
        for (let section in I18N_BUNDLE) {
            if (I18N_BUNDLE[section][key]) return I18N_BUNDLE[section][key];
        }
    }

    // 2. Fallback to hardcoded I18N in vault_v2_i18n.js
    if (typeof I18N !== 'undefined' && I18N[key]) {
        return I18N[key][CURRENT_LANG] || I18N[key].EN;
    }

    return fallback || key;
}

function translateUI() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const translated = T(key);
        if (translated !== key) el.innerHTML = translated;
    });
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        const translated = T(key);
        if (translated !== key) el.setAttribute('title', translated);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        const translated = T(key);
        if (translated !== key) el.setAttribute('placeholder', translated);
    });
}

/**
 * 8PX GRID & TACTICAL DATE FORMAT (MM-DD-AAAA)
 */
function formatDate(raw) {
    if (!raw) return '—';
    // If it's already a string with dashes, just return it (assuming bridge handles it)
    if (typeof raw === 'string' && raw.includes('-')) return raw;

    try {
        const date = new Date(raw * 1000);
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const d = String(date.getDate()).padStart(2, '0');
        const y = date.getFullYear();
        return `${m}-${d}-${y}`;
    } catch (e) {
        return raw;
    }
}

function initBridge() {
    console.log("HUD: Initializing Bridge Protocol...");

    if (typeof qt === 'undefined') {
        console.warn("HUD: qt object not ready, retrying handshake...");
        setTimeout(initBridge, 100);
        return;
    }

    try {
        new QWebChannel(qt.webChannelTransport, function (channel) {
            console.log("HUD: Bridge Handshake Established.");

            sysBridge = channel.objects.system;
            vaultBridge = channel.objects.handler;
            api = channel.objects.api;

            if (!vaultBridge || !sysBridge) {
                console.error("HUD: Bridge objects missing.");
                return;
            }

            // 1. Initial Status Check (Forced Password Change, etc)
            console.log("HUD: Executing Initial Health Check...");
            vaultBridge.check_initial_status();

            // Real-time synchronization
            sysBridge.telemetryUpdated.connect(function (res) {
                console.log("HUD: Telemetry Signal Received:", res);
                try { updateUIData(JSON.parse(res)); } catch (e) { console.error("HUD: Parse Error", e); }
            });

            // Vault Sync
            vaultBridge.recordsChanged.connect(function () {
                loadRecords();
                refreshLogs();
                loadUsers(); // HUD 2.3: Refresh operators list on changes
            });

            // Theme Sync
            if (vaultBridge.get_theme_config) {
                vaultBridge.get_theme_config((config) => {
                    try {
                        const c = JSON.parse(config);
                        const root = document.documentElement;
                        if (c.primary_color) root.style.setProperty('--primary', c.primary_color);
                        if (c.secondary_color) root.style.setProperty('--secondary', c.secondary_color);
                        if (c.primary_color && c.primary_color.startsWith('#')) {
                            const hex = c.primary_color.replace('#', '');
                            const r = parseInt(hex.substring(0, 2), 16), g = parseInt(hex.substring(2, 4), 16), b = parseInt(hex.substring(4, 6), 16);
                            root.style.setProperty('--primary-rgb', `${r}, ${g}, ${b}`);
                        }
                    } catch (e) { }
                });
            }

            // DYNAMIC IDENTITY: Load Immediately
            if (vaultBridge && vaultBridge.get_instance_name) {
                console.log("HUD: Requesting get_instance_name from VaultBridge...");
                vaultBridge.get_instance_name((name) => {
                    console.log("HUD: Bridge Callback Identity ->", name);
                    const n = (name && name.trim() !== "") ? name : "VULTRAX CORE";
                    const el3 = document.getElementById('mainIdentityV2');
                    if (el3) {
                        el3.innerText = n;
                        el3.style.visibility = 'visible';
                        el3.style.opacity = '1';
                        console.log("HUD: Element updated successfully.");
                    } else {
                        console.error("HUD: Element 'mainIdentityV2' NOT FOUND in DOM.");
                    }
                });
            }

            if (vaultBridge.get_ui_language) {
                vaultBridge.get_ui_language((lang) => {
                    CURRENT_LANG = lang || 'EN';
                    if (vaultBridge.get_i18n_bundle) {
                        vaultBridge.get_i18n_bundle((bundle) => {
                            try { I18N_BUNDLE = JSON.parse(bundle); translateUI(); } catch (e) { translateUI(); }
                        });
                    } else { translateUI(); }
                });
            }

            refreshStats();
            loadRecords();

            // [AUTO-STARTUP] Always land on Dashboard
            switchView('dashboard');

            // Responsive Connectors
            window.addEventListener('resize', () => {
                const active = document.querySelector('.nav-item.active');
                if (active) updateConnectors(active);
            });
        });
    } catch (err) {
        console.error("HUD: Bridge initialization failed:", err);
    }
}

function refreshStats() {
    if (sysBridge) {
        sysBridge.get_stats((res) => {
            updateUIData(JSON.parse(res));
        });
        refreshLogs();
        loadActivityLogs();
        loadUsers();
    }
}

function refreshLogs() {
    if (sysBridge && sysBridge.get_logs) {
        sysBridge.get_logs((data) => {
            const logs = JSON.parse(data);
            const logStream = document.getElementById('logStream');
            if (logStream && logs.length > 0) {
                logStream.innerHTML = '';
                logs.forEach(l => {
                    const entry = document.createElement('div');
                    entry.className = 'log-entry';
                    entry.innerText = `[${l.time}] ${l.event}: ${l.status}`;
                    logStream.appendChild(entry);
                });
            }
        });
    }
}

function updateUIData(s) {
    // 0. IDENTITY SYNC (Nuclear / Real-time)
    if (s.instance_name) {
        console.log("HUD: Syncing Identity via Telemetry ->", s.instance_name);
        const n = s.instance_name;
        const elDash = document.getElementById('companyNameDash');
        const elIdent = document.getElementById('mainIdentityV2');
        if (elDash) elDash.innerText = n;
        if (elIdent) {
            elIdent.innerText = n;
            elIdent.style.visibility = 'visible';
            elIdent.style.opacity = '1';
        }
    }

    if (s.current_user) {
        const elUser = document.getElementById('currentUserSide');
        if (elUser) elUser.innerText = s.current_user.toUpperCase();
    }
    else {
        console.warn("HUD: No 'instance_name' found in telemetry payload:", s);
    }

    // 1. Security Score (Large Gauge)
    const score = s.security_score || 0;
    const gauge = document.getElementById('securityGauge');
    if (gauge) {
        const offset = 283 - (283 * score / 100);
        gauge.style.strokeDashoffset = offset;
    }
    if (document.getElementById('securityScoreVal')) document.getElementById('securityScoreVal').innerText = score;

    // Detailed Security Card (Wide) & Access Metrics
    if (document.getElementById('coreHealthVal')) document.getElementById('coreHealthVal').innerText = (s.core_health || score) + '%';
    if (document.getElementById('accessIntegrityVal')) document.getElementById('accessIntegrityVal').innerText = (s.access_integrity || 100) + '%';

    if (document.getElementById('memMbVal')) document.getElementById('memMbVal').innerText = s.memory_mb || '-- MB';
    if (document.getElementById('riskExpVal')) document.getElementById('riskExpVal').innerText = s.risk_exposure || 'LOW';
    if (document.getElementById('auditProtVal')) document.getElementById('auditProtVal').innerText = s.audit_protocol || 'OK';

    // Access Security Card Update
    if (document.getElementById('loginAttemptsVal')) document.getElementById('loginAttemptsVal').innerText = `${s.login_attempts || 0} ${T('attempts')} ⚡`;
    if (document.getElementById('lastIncidentVal')) {
        const lastInc = s.last_incident || "--";
        document.getElementById('lastIncidentVal').innerText = lastInc === "--" ? `-- ✅` : `${lastInc} 🛡️`;
    }
    if (document.getElementById('activeSessionsVal')) document.getElementById('activeSessionsVal').innerText = `${s.active_sessions || 1} ${T('active')} ⚡`;

    if (document.getElementById('mfaCoverageVal')) {
        const total = s.total_users || 1;
        const active = Math.round((s.access_integrity / 100) * total); // Approximation based on integrity
        document.getElementById('mfaCoverageVal').innerText = `${active} / ${total}`;
    }

    // Stability
    if (document.getElementById('stabilityStatus')) {
        document.getElementById('stabilityStatus').innerText = s.system_stability || 'NOMINAL';
        document.getElementById('stabilityStatus').className = s.security_score < 80 ? 'red' : 'teal';
    }

    // 2. Password Health - HUD Parity Implementation
    if (s.health_metrics) {
        const hm = s.health_metrics;
        const score = hm.score;
        const cardEl = document.getElementById('v3HealthCard');
        const scoreEl = document.getElementById('vaultScoreVal');
        const gaugeEl = document.getElementById('v3HealthGauge');
        const statusEl = document.getElementById('healthStatusText');

        // Remove old states
        if (cardEl) cardEl.classList.remove('is-good', 'is-warning', 'is-critical');

        // State & Threshold logic synced with HUD design system
        let stateClass = 'is-good';
        let statusText = T('good');

        if (score < 40) {
            stateClass = 'is-critical';
            statusText = T('critical');
        } else if (score < 75) {
            stateClass = 'is-warning';
            statusText = T('warning');
        }

        if (cardEl) cardEl.classList.add(stateClass);
        if (scoreEl) scoreEl.innerText = score;
        if (statusEl) {
            statusEl.innerText = statusText;
            statusEl.className = `v3-status-label ${stateClass.replace('is-', '')}`;
        }

        if (gaugeEl) {
            // Circumference for r=45 is approx 283
            const circumference = 2 * Math.PI * 45;
            const offset = circumference - (score / 100) * circumference;
            gaugeEl.style.strokeDasharray = `${circumference}`;
            gaugeEl.style.strokeDashoffset = offset;
        }

        // HUD Dots indicator (4-dot standard)
        const dots = document.querySelectorAll('.v3-dot');
        const activeCount = score < 40 ? 1 : (score < 75 ? 2 : 4);
        dots.forEach((dot, idx) => {
            dot.classList.toggle('active', idx < activeCount);
        });

        // Numeric fields sync
        if (document.getElementById('valWeak')) document.getElementById('valWeak').innerText = hm.weak;
        if (document.getElementById('valStrong')) document.getElementById('valStrong').innerText = hm.strong;
        if (document.getElementById('valRep')) document.getElementById('valRep').innerText = hm.repeated;
        if (document.getElementById('valExp')) document.getElementById('valExp').innerText = hm.expired;

        if (document.getElementById('lastScanTime')) {
            document.getElementById('lastScanTime').innerText = T('just_now');
        }
    }

    // 3. System Metrics
    const memVal = document.getElementById('memLoadVal');
    if (memVal) memVal.innerText = s.memory_mb || "0.10 MB";

    // 5. Advanced Tactical Metrics (Top Row)
    if (s.admin_secrets !== undefined) document.getElementById('valAdmin').innerText = s.admin_secrets;
    if (s.user_secrets !== undefined) document.getElementById('valUser').innerText = s.user_secrets;
    if (s.total_users !== undefined) document.getElementById('valUsers').innerText = s.total_users;
    if (s.active_sessions !== undefined) document.getElementById('valSessions').innerText = s.active_sessions;
    if (s.log_count !== undefined) document.getElementById('valLogs').innerText = s.log_count;

    // 5. Radar Blips (Tactical Threats) & AI Risk Count
    const threatCount = s.threats_detected || 0;
    renderRadarBlips(threatCount);

    const riskEl = document.getElementById('aiRiskCount');
    if (riskEl) {
        riskEl.innerHTML = `<span style="color: var(--tactical-blue); font-size: 14px; margin-right: 5px;">🛡️</span> ${threatCount} ${T('risks')}`;
        riskEl.style.color = '#ffffff';
        riskEl.style.fontWeight = '700';
    }

    // [NEW] 6. Security Watch (Vigilancia de Seguridad) - TOTAL PARITY
    if (document.getElementById('secWatchCard')) {
        // Bar Values (Using radar metrics as base for bars)
        const metrics = {
            strength: s.core_health || 85,
            auth: s.access_integrity || 90,
            sync: s.network_status ? 100 : 40,
            health: s.health_metrics ? s.health_metrics.score : 0,
            rotation: s.rotation_score || 80
        };

        const updateBar = (id, val, barId) => {
            const valEl = document.getElementById(id);
            const barEl = document.getElementById(barId);
            if (valEl) valEl.innerText = `${val}%`;
            if (barEl) {
                barEl.style.width = `${val}%`;
                // Color mapping: Danger if < 40, Warning if < 75
                barEl.className = 'prog-v2-fill ' + (val < 40 ? 'red' : (val < 75 ? 'orange' : 'teal'));
            }
        };

        updateBar('watch_StrengthVal', metrics.strength, 'watch_StrengthBar');
        updateBar('watch_AuthVal', metrics.auth, 'watch_AuthBar');
        updateBar('watch_SyncVal', metrics.sync, 'watch_SyncBar');
        updateBar('watch_HealthVal', metrics.health, 'watch_HealthBar');
        updateBar('watch_RotVal', metrics.rotation, 'watch_RotBar');

        // Central Intelligence (Alerts)
        if (document.getElementById('watch_ThreatsCount')) document.getElementById('watch_ThreatsCount').innerText = threatCount;
        if (document.getElementById('watch_AlertsCount')) document.getElementById('watch_AlertsCount').innerText = `${threatCount} RISKS`;
        if (document.getElementById('watch_SqliteLoad')) document.getElementById('watch_SqliteLoad').innerText = s.memory_mb || '0.10 MB';
        if (document.getElementById('watch_SysState')) {
            const state = s.system_stability || 'NOMINAL';
            document.getElementById('watch_SysState').innerText = state;
            document.getElementById('watch_SysState').style.color = (state === 'NOMINAL' || state === 'NORMAL') ? 'var(--tactical-teal)' : 'var(--tactical-danger)';
        }
        if (document.getElementById('watch_SecNodes')) {
            const state = s.system_stability || 'NOMINAL';
            document.getElementById('watch_SecNodes').innerText = state;
            document.getElementById('watch_SecNodes').style.color = (state === 'NOMINAL' || state === 'NORMAL') ? 'var(--tactical-teal)' : 'var(--tactical-danger)';
        }

        // Right Column Counts
        if (document.getElementById('watch_HighRisk')) document.getElementById('watch_HighRisk').innerText = s.threats_detected || 0;
        if (document.getElementById('watch_Unused')) document.getElementById('watch_Unused').innerText = Math.floor(s.vault_count / 4) || 0; // Heuristic: 25% unused
        if (document.getElementById('watch_NeverRot')) document.getElementById('watch_NeverRot').innerText = s.user_secrets || 0;
    }

    // 7. Radar Intelligence (Spider Chart)
    updateRadarChart(s);

    lastScore = s.security_score;
}

function updateRadarChart(s) {
    const poly = document.querySelector('#radarSpiderChart polygon');
    if (!poly) return;

    // Mapping 8 points (0 to 100)
    // Fortaleza, Identidad, Salud, Rotación, Inteligencia, Nube, Registros, Riesgo
    const metrics = [
        s.core_health || 85,           // TOP: Fortaleza
        s.access_integrity || 90,     // TR: Identidad
        s.health_score || 75,         // MR: Salud
        s.rotation_score || 80,       // BR: Rotación
        s.security_score || 85,       // BOTTOM: Inteligencia
        s.cloud_exposure || 70,       // BL: Nube
        s.log_health || 95,           // ML: Registros
        100 - (s.threats_detected * 10 || 0) // TL: Riesgo (Inverse of threats)
    ];

    // IDs for value updates
    const valueIds = ['valFort', 'valIdent', 'valHealth', 'valRot', 'valIntel', 'valCloud', 'valReg', 'valRisk'];

    const points = [];
    const center = 50;
    const maxRadius = 45;

    metrics.forEach((m, i) => {
        const val = Math.max(10, Math.min(m, 100)); // Clamp
        const angle = (i * 45 - 90) * (Math.PI / 180); // Start from top (-90deg)
        const radius = (val / 100) * maxRadius;
        const x = center + radius * Math.cos(angle);
        const y = center + radius * Math.sin(angle);
        points.push(`${x},${y}`);

        // Update Text & Color
        const el = document.getElementById(valueIds[i]);
        if (el) {
            el.innerText = `${val}%`;
            // Red if critical, otherwise tactical blue
            const isCritical = (i === 7) ? (val < 50) : (val < 40);
            el.style.color = isCritical ? 'var(--tactical-danger)' : 'var(--tactical-blue)';
            if (el.parentElement) el.parentElement.style.color = isCritical ? 'var(--tactical-danger)' : '#ffffff';
        }
    });

    poly.setAttribute('points', points.join(' '));

    // Change color if critical (Riesgo is index 7)
    const risk = metrics[7];
    if (risk < 50) {
        poly.setAttribute('fill', 'rgba(255, 0, 60, 0.2)');
        poly.setAttribute('stroke', '#ff003c');
    } else {
        poly.setAttribute('fill', 'rgba(0, 242, 255, 0.2)');
        poly.setAttribute('stroke', 'var(--tactical-blue)');
    }
}

let lastThreatCount = -1;
let lastSecurityScore = -1;

function updateIntelFeed(s) {
    const feed = document.getElementById('aiIntelFeed');
    if (!feed) return;

    const threats = s.threats_detected || 0;
    const score = s.security_score || 0;

    // Check if anything actually changed to avoid stuttering DOM wipes
    if (threats === lastThreatCount && score === lastSecurityScore && feed.children.length > 2) return;
    lastThreatCount = threats;
    lastSecurityScore = score;

    // Preserve the header
    const headerHtml = `<div style="font-size: 10px; color: var(--tactical-danger); margin-bottom: 15px; font-weight: 700; letter-spacing: 1px;">INTEL_FEED :: TIEMPO_REAL</div>`;
    feed.innerHTML = headerHtml;

    if (threats > 0) {
        const alert = document.createElement('div');
        alert.className = 'intel-alert';
        const msg = `${T('vuln_detected')} ${threats} ${threats > 1 ? T('vaults') : T('vault')}`;

        alert.innerHTML = `
            <div class="alert-title" style="font-size: 13px; color: #ffffff;">
                <span class="alert-status-dot"></span>
                ${msg}
            </div>
            <div class="alert-actions">
                <button class="intel-btn" onclick="vaultBridge.trigger_ai_audit()">${T('apply')}</button>
                <button class="intel-btn" onclick="openAuditModal()">${T('review')}</button>
                <button class="intel-btn" onclick="this.parentElement.parentElement.remove()">${T('ignore')}</button>
            </div>
        `;
        feed.appendChild(alert);
    }

    const suggestions = document.createElement('div');
    suggestions.style.cssText = 'font-size: 9px; line-height: 1.8; font-weight: 500;';

    let html = '';
    if (score < 90) {
        html += `<div style="color: #ffab00; margin-bottom: 8px; font-weight: 700;">&gt; ${T('degraded_posture')} (${score}%)</div>`;
    }
    if (s.vault_count > 0) {
        html += `<div style="color: var(--tactical-teal); margin-bottom: 8px; font-weight: 700;">&gt; ${T('key_scan_done')} ${s.vault_count} ${T('nodes_prot')}</div>`;
    }
    if (s.threats_detected > 0) {
        html += `<div style="color: var(--tactical-danger); margin-bottom: 8px; font-weight: 700;">&gt; ${s.threats_detected} ${T('vectors_det')}</div>`;
    }
    if (s.active_sessions > 1) {
        html += `<div style="color: #ffab00; margin-bottom: 8px; font-weight: 700;">&gt; ${T('multi_sessions')}</div>`;
    }

    if (!html) {
        html = `<div style="color: var(--tactical-teal)">> ${T('nominal_params')}</div>`;
    }

    suggestions.innerHTML = html;
    feed.appendChild(suggestions);
}

function renderRadarBlips(count) {
    const container = document.getElementById('radarBlips');
    if (!container) return;
    container.innerHTML = '';

    for (let i = 0; i < count; i++) {
        const blip = document.createElement('div');
        blip.className = 'radar-blip';
        // Position blips within the circular bounds
        const angle = Math.random() * Math.PI * 2;
        const dist = Math.random() * 40 + 5; // 5% to 45% radius
        const x = 50 + dist * Math.cos(angle);
        const y = 50 + dist * Math.sin(angle);
        blip.style.left = x + '%';
        blip.style.top = y + '%';
        blip.style.animationDelay = (i * 0.2) + 's';
        container.appendChild(blip);
    }
}

let lastScore = 0;

/* ================================
   VAULT PROCEDURES
================================ */

function loadRecords() {
    if (vaultBridge && vaultBridge.get_vault_records) {
        vaultBridge.get_vault_records((data) => {
            records = JSON.parse(data);
            document.getElementById('count-total').innerText = records.length;
            renderVault(records);
        });
    }
}

function renderVault(data) {
    const body = document.getElementById('vaultBody');
    if (!body) return;
    body.innerHTML = '';

    data.forEach(rec => {
        const row = document.createElement('div');
        row.className = 'v-row';
        const sClass = (rec.strength || 'weak').toLowerCase();

        row.innerHTML = `
            <div class="v-date">${formatDate(rec.last_access)}</div>
            <div class="v-shield ${sClass}">🛡️</div>
            <div class="v-privacy">
                <span class="privacy-badge ${rec.is_private ? 'private' : 'public'}" title="${rec.is_private ? 'PRIVATE NODE' : 'SHARED NODE'}">
                    ${rec.is_private ? '🔒' : '🌐'}
                </span>
            </div>
            <div class="v-id">${rec.identifier}</div>
            <div class="v-owner">${rec.owner || 'UNKNOWN'}</div>
            <div class="v-pass" id="pass-${rec.id}">••••••••</div>
            <div class="v-notes" title="${rec.notes}">${rec.notes}</div>
            <div class="v-actions">
                <button class="v-icon-btn" title="${T('DASHBOARD.COL_SEE', '👁️')}" onclick="event.stopPropagation(); viewNode('${rec.id}')">👁️</button>
                <button class="v-icon-btn" title="${T('DASHBOARD.COL_COPY', '📋')}" onclick="event.stopPropagation(); copyNode('${rec.id}')">📋</button>
            </div>
        `;

        row.onclick = () => selectRow(row, rec);
        row.ondblclick = () => openOps(rec);
        body.appendChild(row);
    });

    // Update filtered count visually
    const filtCount = document.getElementById('count-filtered');
    if (filtCount) filtCount.innerText = data.length;
}

function selectRow(el, rec) {
    if (selectedRow) selectedRow.classList.remove('selected');
    el.classList.add('selected');
    selectedRow = el;
    selectedRecord = rec;
}

function openOps(rec) {
    document.getElementById('targetNodeName').innerText = rec.identifier;
    document.getElementById('opsOverlay').style.display = 'block';
}

function closeOps() {
    document.getElementById('opsOverlay').style.display = 'none';
}

function filterVault() {
    const q = document.getElementById('vaultSearch').value.toLowerCase();
    if (!q) {
        renderVault(records);
        return;
    }
    const filtered = records.filter(r =>
        (r.identifier && r.identifier.toLowerCase().includes(q)) ||
        (r.notes && r.notes.toLowerCase().includes(q)) ||
        (r.owner && r.owner.toLowerCase().includes(q))
    );
    renderVault(filtered);
}

function action(type) {
    if (!selectedRecord) return;
    if (type === 'DELETE') {
        const nodeName = selectedRecord.identifier || T('node_default_name');
        const prompt = `${T('terminate_node_prompt')} [${nodeName}]?`;

        showTacticalConfirm(
            T('vault_system', 'VAULT_SYSTEM'),
            prompt,
            "🗑️",
            () => {
                vaultBridge.delete_record(selectedRecord.id, (ok) => {
                    if (ok) {
                        showToast(T('vault_system'), T('node_purgued'), "success");
                    } else {
                        showToast(T('vault_error'), T('purge_failure'), "danger");
                    }
                    closeOps();
                });
            }
        );
    }
    else if (type === 'EDIT') {
        openServiceModal(selectedRecord.id);
        closeOps();
    }
}

function copyNode(id) {
    if (vaultBridge && vaultBridge.copy_secret) {
        vaultBridge.copy_secret(id, (ok) => {
            if (ok) {
                showToast(T('sync_title'), T('secret_piped'), "success");
            } else {
                showToast(T('critical_error'), T('copy_unauth'), "danger");
            }
        });
    }
}

function viewNode(id) {
    const passEl = document.getElementById(`pass-${id}`);
    if (!passEl) return;

    // Toggle back to masked if already revealed
    if (passEl.classList.contains('revealed')) {
        passEl.innerText = '••••••••';
        passEl.classList.remove('revealed');
        return;
    }

    if (vaultBridge && vaultBridge.view_secret) {
        vaultBridge.view_secret(id, (res) => {
            const data = JSON.parse(res);
            if (data.status === 'success') {
                passEl.innerText = data.secret;
                passEl.classList.add('revealed');
                showToast(T('security_title'), T('decryption_active'), "warning");

                // AUTO-HIDE after 3 seconds
                setTimeout(() => {
                    if (passEl.classList.contains('revealed')) {
                        passEl.innerText = '\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022';
                        passEl.classList.remove('revealed');
                        showToast(T('security_title'), T('secret_remasked'), "success");
                    }
                }, 3000);
            } else {
                showToast(T('access_denied_title'), T('reveal_protocol_failure'), "danger");
            }
        });
    }
}

/**
 * TACTICAL TOAST NOTIFICATION
 * Consolidated version that handles both toastContainer and syncMiniCard fallback.
 */
function showToast(titleOrMsg, msgOrType = '', type = 'info') {
    let title = T(titleOrMsg);
    let msg = T(msgOrType);
    let finalType = type;

    // Handle 2-argument signature: showToast(msg, type)
    if (arguments.length === 2 && (msgOrType === 'success' || msgOrType === 'danger' || msgOrType === 'warning' || msgOrType === 'info')) {
        title = T('vault_system', 'SISTEMA');
        msg = T(titleOrMsg);
        finalType = msgOrType;
    }

    // PRIMARY: Toast Container [REPLACE MODE - solo 1 toast activo]
    const container = document.getElementById('toastContainer');
    if (container) {
        container.querySelectorAll('.tactical-toast').forEach(t => t.remove());

        const toast = document.createElement('div');
        toast.className = `tactical-toast ${finalType}`;
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-msg">${msg}</div>
            </div>
        `;
        container.appendChild(toast);
        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => toast.remove(), 500);
        }, 4000);
    }
}

/**
 * SYNC CARD — Dedicated updater for the #syncMiniCard HUD element.
 * ONLY call this for actual sync/cloud operations. Never use for vault row actions.
 * @param {string} title  - i18n resolved title
 * @param {string} msg    - i18n resolved message
 * @param {string} type   - 'success' | 'error' | 'info'
 */
function showSyncCard(title, msg, type = 'info') {
    const card = document.getElementById('syncMiniCard');
    const statusTxt = document.getElementById('syncStatusText');
    if (!card || !statusTxt) return;

    card.style.display = 'flex';
    card.classList.remove('success', 'error');
    if (type === 'error' || type === 'danger') card.classList.add('error');
    if (type === 'success') card.classList.add('success');
    statusTxt.innerText = `${title}: ${msg}`;

    // Auto-hide after 5s if still visible
    setTimeout(() => { if (card.style.display === 'flex') card.style.display = 'none'; }, 5000);
}

function switchView(viewId) {
    if (viewId === 'users') {
        openUsersModal();
        return;
    }
    console.log("NAV: Switching to", viewId);
    document.querySelectorAll('.view-pane').forEach(p => p.style.display = 'none');
    const target = document.getElementById('view-' + viewId);
    if (target) {
        target.style.display = 'flex';
        // View-specific loaders
        if (viewId === 'vault') loadRecords();
        if (viewId === 'activity') loadActivityLogs();
        if (viewId === 'ai_side') startAIGuardianProtocol();
        if (viewId === 'settings') loadSettings();
    }

    // Toggle active class on sidebar items
    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));

    // Find correctly even if event is null (Direct call)
    let activeItem = null;
    if (window.event && window.event.currentTarget && window.event.currentTarget.classList.contains('nav-item')) {
        window.event.currentTarget.classList.add('active');
        activeItem = window.event.currentTarget;
    } else {
        const items = document.querySelectorAll('.nav-item');
        items.forEach(item => {
            const attr = item.getAttribute('onclick');
            if (attr && attr.includes(`'${viewId}'`)) {
                item.classList.add('active');
                activeItem = item;
            }
        });
    }

    // UPDATE CONNECTORS
    if (activeItem) {
        updateConnectors(activeItem);
    }

    // NOTIFY PYTHON BACKEND (Tactical Mapping)
    if (api && api.handle_navigation) {
        api.handle_navigation(viewId);
    }

    // Refresh stats to ensure real-time data on view entry
    refreshStats();
}

function updateConnectors(navItem) {
    const svgPath = document.getElementById('dynamic-connector');
    if (!svgPath) return;

    const navRect = navItem.getBoundingClientRect();
    const startX = navRect.right - 10;
    const startY = navRect.top + (navRect.height / 2);

    // Find the global header
    const header = document.querySelector('.global-hud-header');
    if (!header) return;

    const headRect = header.getBoundingClientRect();
    const endX = headRect.left + 20;
    const endY = headRect.bottom - 10;

    // Create a smooth tactical curve (CUBIC BEZIER)
    const cp1x = startX + 50;
    const cp1y = startY;
    const cp2x = endX - 50;
    const cp2y = endY;

    const d = `M ${startX} ${startY} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${endX} ${endY}`;
    svgPath.setAttribute('d', d);
}

let allLogs = [];
function loadActivityLogs() {
    console.log("AUDIT: Fetching tactical logs...");
    if (sysBridge && sysBridge.get_detailed_audit) {
        sysBridge.get_detailed_audit((data) => {
            allLogs = JSON.parse(data);
            renderLogs(allLogs);
        });
    }
}

function renderLogs(logs) {
    const tbody = document.getElementById('activity-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    if (logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="flex-center" style="height:200px; opacity:0.5; border:none;">> NO_LOGS_FOUND_IN_THIS_VECTOR</td></tr>';
        return;
    }

    logs.forEach(l => {
        const row = document.createElement('tr');
        const sClass = l.status === 'SUCCESS' ? 'success' : 'danger';

        row.innerHTML = `
            <td class="t-mono">[${l.time}]</td>
            <td class="text-primary" style="font-weight: 500;">${l.user}</td>
            <td class="t-mono">${l.action}</td>
            <td class="t-mono" style="opacity: 0.6;">${l.target || '-'}</td>
            <td class="t-mono" style="opacity: 0.6;">${l.device || 'UNKNOWN'}</td>
            <td style="opacity: 0.8;">${l.details || ''}</td>
            <td><span class="activity-badge ${sClass}">${l.status}</span></td>
        `;
        tbody.appendChild(row);
    });
}

let currentLogFilter = 'ALL';
function setLogFilter(type, btn) {
    currentLogFilter = type;
    document.querySelectorAll('.activity-filter-group .nav-btn-v2').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    filterLogs();
}

function filterLogs() {
    const q = document.getElementById('logSearch').value.toLowerCase();
    const type = currentLogFilter;

    const filtered = allLogs.filter(l => {
        const matchesSearch = l.user.toLowerCase().includes(q) ||
            l.action.toLowerCase().includes(q) ||
            (l.target && l.target.toLowerCase().includes(q)) ||
            (l.device && l.device.toLowerCase().includes(q));

        const act = l.action.toUpperCase();

        if (type === 'ALL') return matchesSearch;
        if (type === 'AUTH' && (act.includes('LOGIN') || act.includes('AUTH') || act.includes('LOGOUT') || act.includes('PASSWORD'))) return matchesSearch;
        if (type === 'SECRETS' && (act.includes('SECRET') || act.includes('VAULT') || act.includes('PURGE') || act.includes('IMPORT'))) return matchesSearch;
        if (type === 'ADMIN' && (act.includes('USER') || act.includes('ADMIN') || act.includes('INVITA') || act.includes('REPAIR') || act.includes('RESET'))) return matchesSearch;
        if (type === 'GLOBAL' && (act.includes('SYNC') || act.includes('CLOUD') || act.includes('REMOTE'))) return matchesSearch;
        return false;
    });

    renderLogs(filtered);
}

function loadUsers() {
    const now = Date.now();
    if (userListCache && (now - lastUserFetchTime < CACHE_TTL)) {
        renderUserList(userListCache);
        return;
    }

    if (vaultBridge && vaultBridge.get_users) {
        vaultBridge.get_users((res) => {
            const users = JSON.parse(res);
            userListCache = users;
            lastUserFetchTime = now;
            renderUserList(users);
        });
    }
}

function renderUserList(users) {
    const tbody = document.getElementById('users-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    const badge = document.getElementById('user-count-badge');
    if (badge) {
        badge.innerText = `[${users.length}/5]`;
        badge.className = users.length >= 5 ? 't-badge danger' : 't-badge';
    }

    if (users.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-dim); padding: 40px;">${T('no_operators_detected')}</td></tr>`;
        return;
    }

    users.forEach(u => {
        const tr = document.createElement('tr');
        // ULTRA-INTENSE Neon Circles (High Visibility)
        const statusCircle = u.active
            ? '<span style="color: #00FF00; font-size: 1.8em; text-shadow: 0 0 15px #00FF00, 0 0 5px #FFFFFF;">●</span>'
            : '<span style="color: #FF0000; font-size: 1.8em; text-shadow: 0 0 15px #FF0000, 0 0 5px #FFFFFF;">●</span>';

        // Debug Log to console (F12) to verify data integrity
        console.log(`HUD_SYNC: User [${u.username}] active_state:`, u.active);

        const faIcon = u.has_2fa ? '<span style="font-size: 1.4em;">🔒</span>' : '<span style="font-size: 1.4em;">🔓</span>';

        // Distinct Action Icons
        const lockIcon = u.active ? '🚫' : '🔄';
        const lockTitle = u.active ? T('tooltip_lock') : T('tooltip_unlock');
        const lockClass = u.active ? 'danger' : 'success';

        tr.innerHTML = `
                <td class="${u.is_current ? 'text-primary' : ''}">${u.username} ${u.is_current ? T('current_user_tag') : ''}</td>
                <td class="t-mono">${u.role.toUpperCase()}</td>
                <td style="text-align:center">${statusCircle}</td>
                <td style="text-align:center" title="${u.has_2fa ? T('tag_2fa_prot') : T('tag_2fa_disabled')}">${faIcon}</td>
                <td style="text-align:center">
                    ${!u.is_current ? `<button class="v-icon-btn ${lockClass}" title="${lockTitle}" onclick="toggleUserLock('${u.username}', ${u.active})">${lockIcon}</button>` : '—'}
                </td>
                <td style="text-align:center">
                    <button class="v-icon-btn" title="${T('tooltip_reset_2fa')}" onclick="reset2FA('${u.username}')">🔑</button>
                </td>
                <td style="text-align:center">
                    <button class="v-icon-btn" title="${T('tooltip_change_pass')}" onclick="resetPassword('${u.username}')">📝</button>
                </td>
                <td style="text-align:center">
                    ${!u.is_current ? `<button class="v-icon-btn danger" title="${T('tooltip_delete')}" onclick="deleteUser('${u.id}', '${u.username}')">🔥</button>` : '—'}
                </td>
            `;
        tbody.appendChild(tr);
    });
}

function loadInvitations() {
    if (vaultBridge && vaultBridge.get_invitations) {
        vaultBridge.get_invitations((data) => {
            const invs = JSON.parse(data);
            const tbody = document.getElementById('invites-tbody');
            if (!tbody) return;
            tbody.innerHTML = '';

            if (invs.length === 0) {
                tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-dim); padding: 20px;">${T('no_active_codes')}</td></tr>`;
                return;
            }

            invs.forEach(i => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="text-primary t-mono" style="cursor:pointer" title="${T('tooltip_copy')}" onclick="copyToClipboard('${i.code}')">${i.code}</td>
                    <td>${i.role.toUpperCase()}</td>
                    <td class="t-mono">${i.created_by || 'SYSTEM'}</td>
                    <td><span class="badge-success">${T('active')}</span></td>
                `;
                tbody.appendChild(tr);
            });
        });
    }
}

function createInvite() {
    const role = confirm("GENERATE ADMIN INVITATION? (Cancel for standard User)") ? "admin" : "user";
    if (vaultBridge && vaultBridge.create_invitation) {
        vaultBridge.create_invitation(role);
        setTimeout(loadInvitations, 1000);
    }
}



function reset2FA(username) {
    if (vaultBridge && vaultBridge.reset_2fa_bridge) {
        vaultBridge.reset_2fa_bridge(username);
    }
}

function resetPassword(username) {
    if (vaultBridge && vaultBridge.reset_password_bridge) {
        vaultBridge.reset_password_bridge(username);
    }
}

function deleteUser(id, name) {
    if (confirm(`¿ELIMINAR_OPERADOR_PERMANENTEMENTE: [${name}]?`)) {
        if (vaultBridge && vaultBridge.delete_user_bridge) {
            // Invalidate frontend cache immediately
            userListCache = null;
            lastUserFetchTime = 0;

            vaultBridge.delete_user_bridge(id, name);
        }
    }
}

function toggleUserLock(username, currentStatus) {
    if (vaultBridge && vaultBridge.set_user_status) {
        // Invalidate frontend cache immediately
        userListCache = null;
        lastUserFetchTime = 0;

        vaultBridge.set_user_status(username, currentStatus);
        showToast("ADMIN_PROTOCOL", "USER_STATUS_TOGGLED", "success");
        setTimeout(loadUsers, 500);
    }
}

let aiSequenceActive = false;
let pendingAIInsight = null;

function startAIGuardianProtocol(insight) {
    const feed = document.getElementById('ai-guardian-feed');
    if (!feed || !sysBridge) return;

    // If called with an insight but sequence is active, queue it
    if (insight && aiSequenceActive) {
        console.log("HUD_IA: Queuing strategic insight...");
        pendingAIInsight = insight;
        return;
    }

    // If sequence already active and no fresh insight, do nothing
    if (aiSequenceActive && !insight) return;

    aiSequenceActive = true;

    // Reset Feed only if we're starting a fresh heuristic pass (no insight passed)
    if (!insight) {
        feed.innerHTML = '';
        pendingAIInsight = null;

        // [INTEGRATION PARITY] Trigger full backend audit if entering manually
        if (vaultBridge && vaultBridge.trigger_ai_audit) {
            console.log("HUD_IA: Triggering fresh neural audit from view entry...");
            vaultBridge.trigger_ai_audit();
        }
    }

    sysBridge.get_stats((res) => {
        try {
            const s = JSON.parse(res);
            const score = s.score || s.security_score || 0;
            const threats = s.threats_detected || 0;

            const sequence = [
                `> ${T('ai_proto_connected')}`,
                `> ${T('ai_analyzing_vault').replace('{}', s.vault_count || s.total_count || 0)}`,
                `> ${T('ai_op_integrity').replace('{}', score)}`,
                `> ${T('ai_risk_state').replace('{}', (s.risk ? s.risk.toUpperCase() : T('nominal')))}`,
                `> ${T('ai_mfa_status').replace('{}', (s.admin_no_mfa > 0 ? T('ai_vulnerable') : T('ai_protected')))}`,
                `> ${T('ai_attack_patterns').replace('{}', (s.failed_logins_24h > 0 ? `${T('ai_detected')} (${s.failed_logins_24h})` : T('ai_none')))}`,
                `> ${T('ai_system_mode').replace('{}', (score > 80 ? T('ai_active_prot') : T('ai_watch_mode')))}`
            ];

            if (threats > 0) {
                sequence.push(`> ${T('ai_threat_alert').replace('{}', threats)}`);
            }

            let i = 0;
            const interval = setInterval(() => {
                if (i >= sequence.length) {
                    clearInterval(interval);
                    aiSequenceActive = false;

                    // Final Insight (either passed now or was queued)
                    const finalInsight = insight || pendingAIInsight;
                    if (finalInsight) {
                        renderStrategicInsight(finalInsight);
                        pendingAIInsight = null;
                    }
                    return;
                }
                const entry = document.createElement('div');
                entry.className = 'log-entry';
                const txt = sequence[i];
                if (txt.includes('VULNERABLE') || txt.includes('ALERTA') || txt.includes('DETECTADOS') || txt.includes('CRÍTICOS')) {
                    entry.style.color = 'var(--tactical-danger)';
                    entry.style.fontWeight = '700';
                }
                entry.innerText = txt;
                feed.appendChild(entry);
                feed.scrollTop = feed.scrollHeight;
                i++;
            }, 500);

            if (typeof renderRadarBlips === 'function') {
                renderRadarBlips(threats);
            }

        } catch (e) {
            console.error("HUD_IA_FAIL:", e);
            aiSequenceActive = false;
            feed.innerHTML = `<div class="log-entry">> ${T('ai_proto_error', 'ERROR_DE_CONEXIÓN_DATÁGORA')}</div>`;
        }
    });
}

function renderStrategicInsight(insight) {
    const feed = document.getElementById('ai-guardian-feed');
    if (!feed) return;

    const entry = document.createElement('div');
    entry.className = 'log-entry intel-insight';
    entry.style.color = 'var(--primary)';
    entry.style.marginTop = '15px';
    entry.style.borderLeft = '3px solid var(--primary)';
    entry.style.paddingLeft = '10px';
    entry.style.background = 'rgba(var(--primary-rgb, 127, 90, 240), 0.05)';
    entry.innerText = '[INTEL] ';
    feed.appendChild(entry);

    let charPos = 0;
    const tpe = setInterval(() => {
        if (charPos < insight.length) {
            entry.innerText += insight.charAt(charPos);
            charPos++;
            feed.scrollTop = feed.scrollHeight;
        } else {
            clearInterval(tpe);
        }
    }, 15);
}

/**
 * RADAR BLIP GENERATOR
 * Injects dynamic risk blips into the tactical radar based on detected vulnerabilities.
 */
function renderRadarBlips(count) {
    const container = document.getElementById('radarBlips');
    if (!container) return;

    container.innerHTML = '';
    const maxBlips = Math.min(count, 12); // Cap blips for performance/visuals

    for (let i = 0; i < maxBlips; i++) {
        const blip = document.createElement('div');
        blip.className = 'radar-blip';

        // Random tactical positioning within the circle (0-100%)
        // We use polar coordinates for better 'radar' feeling
        const angle = Math.random() * Math.PI * 2;
        const dist = 20 + Math.random() * 60; // Keep away from center and extreme edge

        const x = 50 + Math.cos(angle) * dist / 2;
        const y = 50 + Math.sin(angle) * dist / 2;

        blip.style.left = `${x}%`;
        blip.style.top = `${y}%`;

        // Staggered animation
        blip.style.animationDelay = `${Math.random() * 2}s`;

        container.appendChild(blip);
    }
}

function switchTheme(themeId) {
    if (vaultBridge && vaultBridge.set_active_theme) {
        vaultBridge.set_active_theme(themeId);

        // Update local class for instant feedback
        document.body.className = themeId;
        showToast("THEME_MODULATOR", `PROTOCOL_${themeId.toUpperCase()}_INITIATED`, "success");

        // Trigger CSS variable re-injections
        initBridge();
    }
}

/**
 * TRIGGER SYSTEM ACTION (SYNC, IMPORT, EXPORT, BACKUP, RESTORE)
 * Bridges the HUD Footer directly to Python operational handlers.
 */
function triggerAction(actionType) {
    if (window.isActionInProgress) return;

    console.log(`ACTION_HUB: Requesting ${actionType.toUpperCase()} protocol...`);
    let handled = false;

    if (vaultBridge) {
        if (actionType === 'sync') {
            window.isActionInProgress = true;
            if (vaultBridge.trigger_sync) vaultBridge.trigger_sync();
            handled = true;
            // The isActionInProgress flag is reset by sync completion signals
        } else if (actionType === 'ai_audit') {
            // [PARITY FIX] Just switch view; startAIGuardianProtocol will handle the trigger
            switchView('ai_side');
            handled = true;
        }
    }

    if (!handled && api && api.handle_action) {
        api.handle_action(actionType);
        handled = true;
    }

    if (!handled) {
        console.error("ACTION_HUB_ERROR: API Bridge not established.");
        showToast(T('vault_error'), T('bridge_disconnected', 'BRIDGE_DISCONNECTED'), "critical");
    }
}

function updateClock() {
    const now = new Date();
    const clockEl = document.getElementById("clock");
    if (clockEl) clockEl.innerText = now.toLocaleTimeString();
}

function loadSettings() {
    console.log("SETTINGS: Fetching master configuration...");
    if (vaultBridge && vaultBridge.get_settings_config) {
        vaultBridge.get_settings_config((data) => {
            const config = JSON.parse(data);
            renderSettings(config);
        });
    }
}

function renderSettings(c) {
    if (!c || !c.operator) return;

    // Operator Profile
    document.getElementById('set-op-name').innerText = c.operator.username;
    document.getElementById('set-op-role').innerText = c.operator.role;
    document.getElementById('set-op-id').innerText = c.operator.id;

    // Security Engine
    document.getElementById('set-enc-std').innerText = c.security.encryption;
    document.getElementById('set-key-rot').innerText = c.security.last_rotation; // MM-DD-AAAA

    const syncBadge = document.getElementById('set-sync-stat');
    if (syncBadge) {
        syncBadge.innerText = c.security.key_health;
        syncBadge.className = c.security.key_health === 'OPTIMAL' ? 't-badge-success' : 't-badge-warning';
    }

    // HUD Behavior
    const themeSel = document.getElementById('theme-selector');
    if (themeSel) themeSel.value = c.global.theme;

    const autolock = document.getElementById('set-autolock-time');
    if (autolock) autolock.value = c.global.auto_lock;

    // AI Engine & Vault name
    document.getElementById('ai-provider-select').value = c.ai.provider;
    document.getElementById('set-vault-name').value = c.global.vault_name;
    document.getElementById('key-gemini').value = c.ai.keys.gemini;
    document.getElementById('key-chatgpt').value = c.ai.keys.chatgpt;

    // Update AI Indicator
    const aiInd = document.getElementById('ai-status-indicator');
    if (aiInd) {
        aiInd.innerText = c.ai.provider === 'Disabled' ? 'OFF' : 'ACTIVE';
        aiInd.className = c.ai.provider === 'Disabled' ? 't-badge' : 't-badge success';
    }
}

function saveAllSettings() {
    const config = {
        lang: CURRENT_LANG, // Persistence handled by same language
        theme: document.getElementById('theme-selector').value,
        auto_lock: document.getElementById('set-autolock-time').value,
        vault_name: document.getElementById('set-vault-name').value,
        ai: {
            provider: document.getElementById('ai-provider-select').value,
            keys: {
                gemini: document.getElementById('key-gemini').value,
                chatgpt: document.getElementById('key-chatgpt').value
            }
        }
    };

    if (vaultBridge && vaultBridge.save_hud_settings) {
        vaultBridge.save_hud_settings(JSON.stringify(config), (success) => {
            if (success) {
                // Apply theme locally for instant effect if possible
                document.body.className = config.theme;
                loadSettings();
            }
        });
    }
}

function runRepair() {
    if (vaultBridge && vaultBridge.open_repair_tool) {
        vaultBridge.open_repair_tool();
    }
}

setInterval(updateClock, 1000);
updateClock();

const brightInp = document.getElementById("brightness");
if (brightInp) {
    brightInp.addEventListener("input", function () {
        document.documentElement.style.setProperty("--global-brightness", this.value);
    });
}

const themeBtn = document.getElementById("themeToggle");
if (themeBtn) {
    themeBtn.addEventListener("click", function () {
        const body = document.body;
        let themeId = "vultrax";

        if (body.classList.contains("aura")) {
            body.classList.remove("aura");
            body.classList.add("nebula");
            themeId = "nebula";
        } else if (body.classList.contains("nebula")) {
            body.classList.remove("nebula");
            themeId = "vultrax";
        } else {
            body.classList.add("aura");
            themeId = "aura";
        }

        // NOTIFY PYTHON CORE
        if (vaultBridge && vaultBridge.set_active_theme) {
            vaultBridge.set_active_theme(themeId);
            showToast("SINCRONIZACIÓN", `MATRIZ_${themeId.toUpperCase()}_ACTIVA`, "success");
        }
    });
}

/* ================================
   SERVICE MODAL LOGIC (1:1 REPLICA)
================================ */
function openServiceModal(id = 0) {
    const modal = document.getElementById('serviceModal');
    const title = document.getElementById('modalTitle');
    const nodeId = document.getElementById('nodeId');

    // Reset form
    document.getElementById('nodeService').value = '';
    document.getElementById('nodePass').value = '';
    document.getElementById('nodeNotes').value = '';
    document.getElementById('nodePrivate').value = "0";
    document.getElementById('nodePass').type = 'password';
    document.getElementById('btnToggleReveal').innerText = '👁️';
    nodeId.value = id;

    // Update Strength Color/Label
    updateStrengthVisuals(0, T('security_pending_lbl'));

    // Set current user as owner
    if (vaultBridge && vaultBridge.get_current_user) {
        vaultBridge.get_current_user((user) => {
            document.getElementById('nodeUser').value = user;
        });
    }

    if (id !== 0) {
        title.innerText = T('service_modal_title_edit').replace('{}', id);
        if (vaultBridge && vaultBridge.prepare_edit) {
            vaultBridge.prepare_edit(id.toString(), (res) => {
                const data = JSON.parse(res);
                if (data.id) {
                    document.getElementById('nodeService').value = data.service;
                    document.getElementById('nodeUser').value = data.username;
                    document.getElementById('nodePass').value = data.secret;
                    document.getElementById('nodeNotes').value = data.notes;
                    document.getElementById('nodePrivate').value = data.is_private.toString();
                    onPassChange();
                }
            });
        }
    } else {
        title.innerText = T('service_modal_title_new');
    }

    modal.style.display = 'flex';
    validateForm();
}

function closeServiceModal() {
    document.getElementById('serviceModal').style.display = 'none';
}

function onPassChange() {
    const pwd = document.getElementById('nodePass').value;
    vaultBridge.calculate_strength(pwd, (res) => {
        const data = JSON.parse(res);
        const localizedName = T(data.level + '_lbl') || data.name;
        updateStrengthVisuals(data.score, localizedName, data.level);
    });
    validateForm();
}

function updateStrengthVisuals(score, name, level) {
    const bar = document.getElementById('strengthBar');
    const label = document.getElementById('strengthLabel');
    bar.style.width = score + '%';

    if (level) {
        label.innerText = T('security_status_lbl').replace('{}', name);
    } else {
        label.innerText = name; // PENDING_INPUT case
    }

    // USE CSS VARIABLES - ZERO HARDCODE
    const varName = {
        "weak": "var(--danger)",
        "medium": "var(--warning)",
        "strong": "var(--primary)",
        "secure": "var(--success)"
    }[level] || "var(--danger)";

    bar.style.background = varName;
    label.style.color = varName;
    bar.style.boxShadow = `0 0 10px ${varName}`;
}

function generateSecurePass() {
    if (vaultBridge && vaultBridge.generate_password_advanced) {
        vaultBridge.generate_password_advanced((pwd) => {
            const passInp = document.getElementById('nodePass');
            passInp.value = pwd;
            passInp.type = 'text';
            document.getElementById('btnToggleReveal').innerText = '🙈';
            onPassChange();
        });
    }
}

function copyNodePass() {
    const text = document.getElementById('nodePass').value;
    if (text) {
        const dummy = document.createElement("textarea");
        document.body.appendChild(dummy);
        dummy.value = text;
        dummy.select();
        document.execCommand("copy");
        document.body.removeChild(dummy);
        showToast(T('security_title'), T('secret_piped'), "success");
    }
}

function showHeuristics() {
    if (!pwd) {
        showToast(T('ai_guardian_title'), T('enter_secret_msg'), "warning");
        return;
    }
    if (vaultBridge && vaultBridge.get_heuristic_analysis) {
        vaultBridge.get_heuristic_analysis(pwd, (res) => {
            const data = JSON.parse(res);
            const msg = `${T('entropy_lbl')}: ${data.entropy} bits | ${T('crack_time_lbl')}: ${data.crack_time}`;
            showToast(T('ai_guardian_title'), msg, "success");
            // Log the full findings to the UI console if available
            console.log("HEURISTICS:", data.findings);
        });
    }
}

/* ================================
   AI EXPLANATION (GHOST) LOGIC
================================ */
function openAIExplanation(cardType) {
    if (sysBridge && sysBridge.get_ai_explanation) {
        sysBridge.get_ai_explanation(cardType, (res) => {
            const data = JSON.parse(res);
            const body = document.getElementById('aiExpBody');
            document.getElementById('aiExpTitle').innerText = data.title;
            body.innerHTML = '';

            data.metrics.forEach(m => {
                const row = document.createElement('div');
                row.className = 'ai-metric-row';
                row.innerHTML = `
                    <div class="flex-between">
                        <span class="m-key">${m.key}</span>
                        <span class="m-val" style="color: var(--${m.color})">${m.value}</span>
                    </div>
                    <div class="m-interp" style="color: var(--${m.color})">➤ ${m.interp}</div>
                `;
                body.appendChild(row);
            });

            document.getElementById('aiExplanationModal').style.display = 'flex';
        });
    }
}

function closeAIModal() {
    document.getElementById('aiExplanationModal').style.display = 'none';
}

// Close on double click inside the modal (ghost style)
const modal = document.getElementById('aiExplanationModal');
if (modal) modal.ondblclick = closeAIModal;

// HUD Namespace for Tactical Extensions
const HUD = {
    showExplanation: function (type) {
        console.log("HUD_INTEL: Requesting deep analysis for", type);
        // Map lowercase keys from HTML to bridge-expected uppercase types
        const mapping = {
            'operator_profile': 'OPERATOR',
            'security_engine': 'SECURITY',
            'system': 'SYSTEM',
            'health': 'HEALTH',
            'radar': 'RADAR'
        };
        const target = mapping[type] || type.toUpperCase();
        openAIExplanation(target);
    }
};

/* ================================
   HEALTH DASHBOARD LOGIC
================================ */
function renderHealthDashboardDisplay(res) {
    const data = JSON.parse(res);

    // 1. Gauge
    const score = Math.max(0, Math.min(100, data.score || 0));
    const offset = 251 - (251 * score / 100);
    let gaugeFill = document.getElementById('healthGaugeFill');
    if (gaugeFill) gaugeFill.style.strokeDashoffset = offset;

    let scoreVal = document.getElementById('healthScoreVal');
    if (scoreVal) scoreVal.innerText = score + "%";

    const stTxt = document.getElementById('healthStatusText');
    if (stTxt) {
        stTxt.innerText = (data.status || 'DESCONOCIDO').toUpperCase();
        stTxt.style.color = score < 50 ? 'var(--danger)' : score < 80 ? 'var(--warning)' : 'var(--success)';
    }

    // 2. Stats
    const statsRow = document.getElementById('healthStatsRow');
    const total = data.stats ? (data.stats.total || 0) : 0;
    const userTotal = data.stats ? (data.stats.user_total || 0) : 0;
    const isWeak = data.stats ? (data.stats.user_weak || 0) : 0;

    if (statsRow) {
        statsRow.innerHTML = `
            <div class="h-stat-card">
                <small>${T('health_total_vault', 'TOTAL_VAULT') || 'TOTAL_VAULT'}</small>
                <div class="val">${total}</div>
            </div>
            <div class="h-stat-card">
                <small>${T('health_user_total', 'USR_TOTAL') || 'USR_TOTAL'}</small>
                <div class="val">${userTotal}</div>
            </div>
            <div class="h-stat-card ${isWeak > 0 ? 'danger' : ''}">
                <small>${T('health_vulnerable', 'VULNERABLES') || 'VULNERABLES'}</small>
                <div class="val">${isWeak}</div>
            </div>
        `;
    }

    // 3. Findings
    const findingsCont = document.getElementById('healthFindings');
    if (findingsCont) {
        findingsCont.innerHTML = `<h4>${T('health_findings_title', 'DETALLE_DE_HALLAZGOS_DE_SEGURIDAD') || 'DETALLE_DE_HALLAZGOS'}</h4>`;
        if (data.findings && data.findings.length > 0) {
            data.findings.forEach(f => {
                const card = document.createElement('div');
                card.className = `finding-card ${f.type || 'info'}`;
                card.innerHTML = `
                    <div class="f-title">${f.title || 'Alerta'}</div>
                    <div class="f-desc">${f.desc || ''}</div>
                `;
                findingsCont.appendChild(card);
            });
        } else {
            findingsCont.innerHTML += `<p style="opacity:0.6; padding: 10px;" class="mono">${T('health_no_findings', 'SISTEMA ÓPTIMO. CERO BRECHAS DETECTADAS.') || 'SISTEMA ÓPTIMO'}</p>`;
        }
    }

    const healthModal = document.getElementById('healthModal');
    if (healthModal) healthModal.style.display = 'flex';

    // Simulate AI Console
    const consoleEl = document.getElementById('healthAIConsole');
    if (consoleEl) {
        consoleEl.innerHTML = '⏳ INICIANDO PROTOCOLO_SALUD...';
        setTimeout(() => {
            consoleEl.innerHTML += '<br>> Escaneando vectores de ataque...';
            setTimeout(() => {
                consoleEl.innerHTML += '<br>> Analizando entropía de claves...';
                setTimeout(() => {
                    consoleEl.innerHTML = `🤖 GUARDIAN_AI ANALYSIS:<br>El núcleo se encuentra en estado ${(data.status || 'NOMINAL').toUpperCase()}. Se recomienda rotación de firmas en nodos vulnerables.`;
                }, 800);
            }, 500);
        }, 400);
    }
}

function openHealthDashboard() {
    if (sysBridge && sysBridge.get_health_data) {
        sysBridge.get_health_data((res) => {
            renderHealthDashboardDisplay(res);
        });
    }
}

// Called by bridge_handlers.py async AI scanner replacing the PyQt Dialog
function renderIntelligenceReport(res) {
    showToast("ANÁLISIS COMPLETADO", "success");
    renderHealthDashboardDisplay(res);
}

function closeHealthModal() {
    const healthModal = document.getElementById('healthModal');
    if (healthModal) healthModal.style.display = 'none';
}

/* ================================
   AUDIT MODAL LOGIC
================================ */
function openAuditModal() {
    if (sysBridge && sysBridge.get_detailed_audit) {
        sysBridge.get_detailed_audit((res) => {
            const logs = JSON.parse(res);
            const body = document.getElementById('auditTableBody');
            body.innerHTML = '';

            logs.forEach(l => {
                const row = document.createElement('tr');
                const sClass = l.status === 'SUCCESS' ? 'success' : 'danger';
                const aClass = l.action.includes('PURGA') ? 'danger bold' : '';

                row.innerHTML = `
                    <td class="mono">${l.time}</td>
                    <td>${l.user}</td>
                    <td class="${aClass}">${l.action}</td>
                    <td>${l.service}</td>
                    <td>${l.details}</td>
                    <td class="${sClass}">${l.status}</td>
                `;
                body.appendChild(row);
            });

            document.getElementById('auditModal').style.display = 'flex';
        });
    }
}

function closeAuditModal() {
    document.getElementById('auditModal').style.display = 'none';
}

/* ================================
   SESSIONS MONITOR MODAL LOGIC (V2 TACTICAL)
================================ */
function openSessionsModal() {
    if (vaultBridge && vaultBridge.get_active_sessions_bridge) {
        vaultBridge.get_active_sessions_bridge((res) => {
            const sessions = JSON.parse(res);
            const body = document.getElementById('sessionsTableBody');
            body.innerHTML = '';

            if (sessions.length === 0) {
                body.innerHTML = '<tr><td colspan="5" style="text-align:center; opacity:0.5;" class="mono">' + T('no_active_sessions', 'NO HAY SESIONES ACTIVAS') + '</td></tr>';
            } else {
                sessions.forEach(s => {
                    const row = document.createElement('tr');
                    const isActive = s.status === 'ACTIVE';
                    const sClass = isActive ? 'success' : 'warning';
                    const statusText = isActive ? T('session_active', 'ACTIVA') : T('session_stale', 'INACTIVA_STALE');

                    row.innerHTML = `
                        <td class="mono">${s.node || 'UNKNOWN_NODE'}</td>
                        <td class="mono">${s.ip || 'LOCAL_LOOPBACK'}</td>
                        <td>${s.start_time || '--:--:--'}</td>
                        <td class="${sClass}">${statusText}</td>
                        <td>
                            <button class="v-btn-tactical danger small" onclick="killSession('${s.session_id}')">
                                ${T('btn_kill', 'TERMINAR')}
                            </button>
                        </td>
                    `;
                    body.appendChild(row);
                });
            }

            document.getElementById('sessionsModal').style.display = 'flex';
        });
    } else {
        showToast("ERROR", "VAULT_BRIDGE NO DISPONIBLE", "critical");
    }
}

function closeSessionsModal() {
    document.getElementById('sessionsModal').style.display = 'none';
}

function killSession(id) {
    if (confirm(T('confirm_kill_session', '¿Terminar esta sesión remotamente?'))) {
        if (vaultBridge && vaultBridge.disconnect_session_bridge) {
            vaultBridge.disconnect_session_bridge(id);
            // Refresh modal after 1s
            setTimeout(openSessionsModal, 1000);
        }
    }
}

function validateForm() {
    const serviceInput = document.getElementById('nodeService');
    const passInput = document.getElementById('nodePass');
    const btn = document.getElementById('btnSaveNode');
    const id = document.getElementById('nodeId').value;

    if (!serviceInput || !passInput || !btn) return;

    const service = serviceInput.value.trim();
    const pass = passInput.value.trim();
    let isValid = (service.length >= 3 && pass.length > 0);

    // Real-time Duplicate Check for NEW nodes
    if (isValid && (id === '0' || id === 0)) {
        if (vaultBridge && vaultBridge.check_service_exists) {
            vaultBridge.check_service_exists(service, (exists) => {
                if (exists) {
                    serviceInput.classList.add('error-border');
                    // We only show the toast if they stop typing or on blur would be better, 
                    // but for now let's ensure it shows.
                    showToast(T('vault_error'), T('duplicate_service_err'), "danger");
                    btn.disabled = true;
                } else {
                    serviceInput.classList.remove('error-border');
                    btn.disabled = false;
                }
            });
            return; // Wait for bridge callback
        }
    } else {
        serviceInput.classList.remove('error-border');
    }

    btn.disabled = !isValid;
}

function submitService() {
    const serviceInput = document.getElementById('nodeService');
    const passInput = document.getElementById('nodePass');
    const userInput = document.getElementById('nodeUser');
    const notesInput = document.getElementById('nodeNotes');

    const data = {
        id: document.getElementById('nodeId').value,
        service: serviceInput.value.trim(),
        username: userInput.value.trim(),
        secret: passInput.value.trim(),
        notes: notesInput.value.trim(),
        is_private: document.getElementById('nodePrivate').value
    };

    if (vaultBridge && vaultBridge.save_record) {
        vaultBridge.save_record(JSON.stringify(data));
        showToast(T('vault_system'), T('persistence_nominal'), "success");
        closeServiceModal();
    }
}

function togglePassVisibility() {
    const passInp = document.getElementById('nodePass');
    const btn = document.getElementById('btnToggleReveal');
    if (passInp.type === 'password') {
        passInp.type = 'text';
        btn.innerText = '🙈';
    } else {
        passInp.type = 'password';
        btn.innerText = '👁️';
    }
}

function openNativeUserManager() {
    if (sysBridge && sysBridge.open_user_manager) {
        sysBridge.open_user_manager();
    }
}

function runRepair() {
    if (sysBridge && sysBridge.trigger_ai_audit) {
        sysBridge.trigger_ai_audit();
    }
}


// GHOST EXPLANATION SYSTEM - BILINGUAL & DETAILED
// GHOST_EXPLANATIONS data moved to vault_v2_i18n.js

function setupGhostExplanations() {
    // Top Stats
    document.querySelectorAll('.stat-card-v2').forEach(card => {
        const small = card.querySelector('small');
        if (small) {
            const i18nKey = small.getAttribute('data-i18n');
            const titleText = small.innerText.trim();
            card.addEventListener('dblclick', (e) => {
                e.preventDefault();
                showGhostExplanation(i18nKey || titleText);
            });
            card.style.cursor = 'help';
            card.title = T('dbl_click_details');
        }
    });

    // Middle Panes and Bottom Cards
    const hudCards = [
        { id: 'globalSecurityCard', selector: '.hud-pane:first-child' },
        { id: 'aiGuardianCard', selector: '.hud-pane:last-child' },
        { id: 'accessSecurityCard', selector: '#accessSecurityCard' },
        { id: 'v3HealthCard', selector: '#v3HealthCard' },
        { id: 'secWatchCard', selector: '#secWatchCard' }
    ];

    hudCards.forEach(cardData => {
        const el = document.querySelector(cardData.selector);
        if (el) {
            const titleEl = el.querySelector('[data-i18n], h4 span, .hud-pane-header span:first-child');
            if (titleEl) {
                const i18nKey = titleEl.getAttribute('data-i18n');
                const titleText = titleEl.innerText.trim();

                el.addEventListener('dblclick', (e) => {
                    e.preventDefault();
                    // Try i18n key first, fallback to text
                    showGhostExplanation(i18nKey || titleText);
                });
                el.style.cursor = 'help';
                el.title = T('dbl_click_details');
            }
        }
    });

    console.log("Ghost Explanation System Initialized.");
}

function showGhostExplanation(key) {
    const data = GHOST_EXPLANATIONS[key];
    if (!data) {
        console.warn("No explanation found for key:", key);
        return;
    }

    const overlay = document.getElementById('ghostOverlay');
    const title = document.getElementById('ghostTitle');
    const content = document.getElementById('ghostContent');

    // Title is now a bilingual object
    title.innerHTML = data.title[CURRENT_LANG] || data.title.EN || data.title;

    // Process body: If both EN and ES tags exist, wrap them in a toggle or just show both if bilingual requested?
    // The user said "dependiendo de la configuración", so I'll show only the relevant tag if present, 
    // or both if the tag is not found.
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = data.body;

    let localBody = '';

    let foundMatch = false;
    tempDiv.querySelectorAll('p').forEach(p => {
        const text = p.innerHTML;
        const isEN = text.includes('[EN]');
        const isES = text.includes('[ES]');

        if (CURRENT_LANG === 'ES' && isES) {
            localBody += `<p>${text}</p>`;
            foundMatch = true;
        } else if (CURRENT_LANG === 'EN' && isEN) {
            localBody += `<p>${text}</p>`;
            foundMatch = true;
        }
    });

    if (!foundMatch) localBody = data.body; // Fallback to both if logic fails

    // --- DYNAMIC VERDICT LOGIC ---
    let verdictHtml = '';
    const verdictTitle = CURRENT_LANG === 'ES' ? 'VEREDICTO EN VIVO' : 'LIVE VERDICT';

    if (key === 'global_security_title') {
        const scoreEl = document.getElementById('securityScoreVal');
        const score = scoreEl ? parseInt(scoreEl.innerText) || 0 : 0;
        if (score >= 85) verdictHtml = `<div class="ghost-verdict safe"><span>${verdictTitle}:</span> NOMINAL (${score}%) - System Optimal</div>`;
        else if (score >= 60) verdictHtml = `<div class="ghost-verdict warning"><span>${verdictTitle}:</span> GUARDED (${score}%) - Monitor Logs</div>`;
        else verdictHtml = `<div class="ghost-verdict danger"><span>${verdictTitle}:</span> CRITICAL (${score}%) - Exposure Detected</div>`;
    }
    else if (key === 'ai_guardian_title') {
        const riskEl = document.getElementById('valRisk');
        const risk = riskEl ? parseInt(riskEl.innerText) || 0 : 0;
        if (risk < 20) verdictHtml = `<div class="ghost-verdict safe"><span>${verdictTitle}:</span> BALANCED - Low Exposure Symmetry</div>`;
        else verdictHtml = `<div class="ghost-verdict danger"><span>${verdictTitle}:</span> ASYMMETRIC - Threat Vectors Active</div>`;
    }
    else if (key === 'access_security_title') {
        const loginEl = document.getElementById('loginAttemptsVal');
        const logins = loginEl ? parseInt(loginEl.innerText) || 0 : 0;
        if (logins > 5) verdictHtml = `<div class="ghost-verdict danger"><span>${verdictTitle}:</span> ALERT - Brute Force Signature Detected</div>`;
        else verdictHtml = `<div class="ghost-verdict safe"><span>${verdictTitle}:</span> SECURE - Normal Traffic Volume</div>`;
    }
    else if (key === 'pass_health_title') {
        const weakEl = document.getElementById('valWeak');
        const repEl = document.getElementById('valRep');
        const weak = weakEl ? parseInt(weakEl.innerText) || 0 : 0;
        const rep = repEl ? parseInt(repEl.innerText) || 0 : 0;
        if (weak > 0 || rep > 0) verdictHtml = `<div class="ghost-verdict danger"><span>${verdictTitle}:</span> VULNERABLE - ${weak} Weak / ${rep} Repeated Keys</div>`;
        else verdictHtml = `<div class="ghost-verdict safe"><span>${verdictTitle}:</span> FORTIFIED - Strong Entropy Maintained</div>`;
    }
    else if (key === 'sec_watch_title') {
        const threatsEl = document.getElementById('watch_ThreatsCount');
        const threats = threatsEl ? parseInt(threatsEl.innerText) || 0 : 0;
        if (threats > 0) verdictHtml = `<div class="ghost-verdict danger"><span>${verdictTitle}:</span> ACTION REQUIRED - ${threats} Active Threat(s)</div>`;
        else verdictHtml = `<div class="ghost-verdict safe"><span>${verdictTitle}:</span> CLEAR - No Anomalies Detected</div>`;
    }

    if (verdictHtml) {
        localBody += verdictHtml;
    }
    // ----------------------------------

    content.innerHTML = localBody;
    overlay.classList.add('active');
}

function closeGhostExplanation() {
    const overlay = document.getElementById('ghostOverlay');
    if (overlay) overlay.classList.remove('active');
}

window.onload = function () {
    initBridge();
    setTimeout(setupGhostExplanations, 1000);
};
/* ================================
   SYNC MANAGEMENT (ULTRA-COMPACT HUD)
================================ */
function openSyncModal(title) {
    const card = document.getElementById('syncMiniCard');
    if (!card) return;

    // Reset UI state
    card.classList.remove('success', 'error');
    document.getElementById('syncProgressBar').style.width = '0%';
    document.getElementById('syncPercent').innerText = "0%";
    document.getElementById('syncStatusText').innerText = T('initializing_protocol');

    card.style.display = 'flex';
}

function updateSyncProgress(val, msg) {
    const bar = document.getElementById('syncProgressBar');
    const pct = document.getElementById('syncPercent');
    const txt = document.getElementById('syncStatusText');

    if (bar) bar.style.width = val + '%';
    if (pct) pct.innerText = val + '%';
    if (txt) {
        // Tactical formatting: No spaces, all caps
        txt.innerText = msg.toUpperCase().replace(/ /g, '_');
    }
}

/**
 * Handles terminal sync summary with tactical feedback
 * @param {Object|string} stats - Success/Error stats or error message
 */
function showSyncSummary(stats) {
    window.isActionInProgress = false; // RESET STATE

    // Si stats es un objeto con error, mostrar toast y cerrar modal
    if (stats && stats.error) {
        showToast("SYNC_ERROR", stats.error, "critical");
        closeSyncModal();
        return;
    }

    // ... resto de la lógica de resumen ...
    const card = document.getElementById('syncMiniCard');
    const txt = document.getElementById('syncStatusText');
    const pct = document.getElementById('syncPercent');

    if (!card) return;

    if (typeof stats === 'string') {
        // ERROR STATE
        card.classList.add('error');
        if (txt) txt.innerText = T('sync_error_fail', "ERROR:_SYNC_FAIL");
        console.error("SYNC_BRIDGE: Fallo táctico ->", stats);
        // Toast persistent for error until manual close or timeout
        setTimeout(closeSyncModal, 5000);
    } else {
        // SUCCESS STATE (OR NO CHANGES)
        card.classList.add('success');
        if (pct) pct.innerText = "100%";

        const up = stats.uploaded || 0;
        const down = stats.downloaded || 0;

        if (txt) {
            if (up > 0 || down > 0) {
                txt.innerText = T('sync_ok_status', `SINCRO_OK:_+{}_- {}`).replace('{}', up).replace('{}', down);
            } else {
                txt.innerText = T('sync_up_to_date', "SINCRO_AL_DIA");
            }
        }

        // Auto-close after 3.5 seconds for success
        setTimeout(closeSyncModal, 3500);
    }
}

function closeSyncModal() {
    const card = document.getElementById('syncMiniCard');
    if (card) {
        card.style.opacity = '0';
        setTimeout(() => {
            card.style.display = 'none';
            card.style.opacity = '1';
        }, 400);
    }
}

/**
 * TACTICAL VIEW SWITCHER
 * Hides all view panes and shows the requested one. Updates navigation buttons.
 */
function openUsersModal() {
    console.log("NAV: Opening Operator Control Center Modal");
    const modal = document.getElementById('view-users');
    if (modal) {
        modal.style.display = 'flex';
        translateUI(); // Apply translations
        loadUsers();
        loadInvitations();
    }
}

function closeUsersModal() {
    const modal = document.getElementById('view-users');
    if (modal) modal.style.display = 'none';
}

/**
 * TACTICAL VIEW SWITCHER
 * Hides all view panes and shows the requested one. Updates navigation buttons.
 */
function switchView(viewId) {
    // Special Case: Users is now a Modal
    if (viewId === 'users') {
        openUsersModal();
        return;
    }

    // 1. Hide all panes
    const panes = document.querySelectorAll('.view-pane');
    panes.forEach(p => p.style.display = 'none');

    // 2. Show target pane
    const target = document.getElementById(`view-${viewId}`);
    if (target) {
        target.style.display = 'block';
    } else {
        console.warn("View not found:", viewId);
    }

    // 3. Update sidebar active state
    const navItems = document.querySelectorAll('.sidebar-nav .nav-item');
    navItems.forEach(item => {
        // Simple heuristic: if the onclick text contains the viewId, make it active
        if (item.getAttribute('onclick') && item.getAttribute('onclick').includes(viewId)) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // 4. Trigger specific loads if needed
    if (viewId === 'vault') loadRecords();
    if (viewId === 'activity') loadActivityLogs();
    if (viewId === 'settings') loadSettings();
    if (viewId === 'ai_side') startAIGuardianProtocol();
}

/* =================================
   TACTICAL CONFIRMATION SYSTEM
   Replaces native browser dialogs
   ================================= */
let confirmCallback = null;

function showTacticalConfirm(title, message, icon, onConfirm) {
    const modal = document.getElementById('confirmationModal');
    if (!modal) {
        // Fallback if modal not in DOM
        if (confirm(message)) onConfirm();
        return;
    }

    // Set content
    const titleEl = document.getElementById('confirmTitle');
    const msgEl = document.getElementById('confirmMessage');
    const iconEl = document.getElementById('confirmIcon');

    if (titleEl) titleEl.innerText = title || "PROTOCOL_CONFIRMATION";
    if (msgEl) msgEl.innerText = message || "¿PROCEDER CON LA OPERACIÓN?";
    if (iconEl) iconEl.innerText = icon || "⚠️";

    // Store callback
    confirmCallback = onConfirm;

    // Setup action button
    const confirmBtn = document.getElementById('confirmActionBtn');
    if (confirmBtn) {
        confirmBtn.onclick = () => {
            if (confirmCallback) confirmCallback();
            closeConfirmModal();
        };
    }

    modal.style.display = 'flex';
}

function closeConfirmModal() {
    const modal = document.getElementById('confirmationModal');
    if (modal) modal.style.display = 'none';
    confirmCallback = null;
}
