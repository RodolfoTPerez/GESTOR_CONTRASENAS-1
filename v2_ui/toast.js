/**
 * PassGuardian V2 - Tactical Toast System
 * Premium Glassmorphic Notifications
 */

const toast = {
    container: null,

    init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.style.cssText = `
                position: fixed;
                bottom: 2rem;
                right: 2rem;
                display: flex;
                flex-direction: column;
                gap: 1rem;
                z-index: 9999;
                pointer-events: none;
            `;
            document.body.appendChild(this.container);
        }
    },

    show(message, type = 'normal', duration = 4000) {
        this.init();

        // [REPLACE MODE] Dismiss all existing toasts instantly before showing new one
        this._clearAll();

        const card = document.createElement('div');
        card.className = `toast-card toast-${type}`;

        const colors = {
            normal: '#00ffaa',
            warning: '#ffae00',
            critical: '#ff003c'
        };

        const borderColor = colors[type] || colors.normal;

        card.style.cssText = `
            min-width: 320px;
            max-width: 450px;
            background: rgba(10, 15, 25, 0.6);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-left: 5px solid ${borderColor};
            color: #f0f4f8;
            padding: 1.2rem 1.8rem;
            border-radius: 16px; /* Modern rounded corners */
            font-family: 'Share Tech Mono', monospace;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
            transform: translateX(120%);
            transition: all 0.5s cubic-bezier(0.19, 1, 0.22, 1);
            pointer-events: auto;
            position: relative;
            overflow: hidden;
            margin-bottom: 10px;
        `;

        const typeLabel = type.toUpperCase();
        card.innerHTML = `
            <div style="font-size: 0.6rem; color: ${borderColor}; margin-bottom: 4px; letter-spacing: 1px;">SYSTEM_${typeLabel}</div>
            <div style="font-size: 0.9rem; line-height: 1.4;">${message}</div>
            <div class="toast-progress" style="position: absolute; bottom: 0; left: 0; height: 2px; width: 100%; background: ${borderColor}; opacity: 0.3;"></div>
        `;

        this.container.appendChild(card);

        // Animate in
        requestAnimationFrame(() => {
            card.style.transform = 'translateX(0)';
        });

        // Progress bar animation
        const progress = card.querySelector('.toast-progress');
        progress.style.transition = `width ${duration}ms linear`;
        requestAnimationFrame(() => {
            progress.style.width = '0%';
        });

        // Remove
        setTimeout(() => {
            card.style.transform = 'translateX(120%)';
            setTimeout(() => {
                if (card.parentNode) card.parentNode.removeChild(card);
            }, 400);
        }, duration);
    },

    _clearAll() {
        if (!this.container) return;
        // Slide out all existing cards immediately
        const cards = this.container.querySelectorAll('.toast-card');
        cards.forEach(c => {
            c.style.transition = 'transform 0.25s ease';
            c.style.transform = 'translateX(120%)';
            setTimeout(() => { if (c.parentNode) c.parentNode.removeChild(c); }, 260);
        });
    }
};
