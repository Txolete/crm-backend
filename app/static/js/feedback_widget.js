/**
 * Feedback widget — botón flotante 💬 en todas las vistas.
 * Click → modal con textarea → POST /feedback.
 * Captura vista actual (tab activa) + URL + user-agent automáticamente.
 */
(function () {
    if (window.__feedbackWidgetLoaded) return;
    window.__feedbackWidgetLoaded = true;

    function detectCurrentView() {
        // Identificar la vista/tab activa para dar contexto al feedback
        const activeTab = document.querySelector('.tab-pane.active, .tab-pane.show.active');
        if (activeTab && activeTab.id) return activeTab.id;
        const activeNav = document.querySelector('.nav-link.active');
        if (activeNav) {
            const t = (activeNav.textContent || '').trim().slice(0, 40);
            if (t) return t;
        }
        return document.title || location.pathname;
    }

    function injectStyles() {
        if (document.getElementById('feedback-widget-styles')) return;
        const css = `
            #feedback-widget-btn {
                position: fixed;
                bottom: 24px;
                right: 24px;
                width: 52px;
                height: 52px;
                border-radius: 50%;
                background: #2563eb;
                color: white;
                border: none;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                cursor: pointer;
                z-index: 9998;
                font-size: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: transform 0.15s, background 0.15s;
            }
            #feedback-widget-btn:hover {
                background: #1d4ed8;
                transform: scale(1.08);
            }
            #feedback-widget-btn:focus { outline: 2px solid #93c5fd; outline-offset: 2px; }
            #feedback-widget-modal .modal-header { background:#2563eb; color:white; }
            #feedback-widget-modal .modal-header .btn-close { filter: invert(1); }
            #feedback-widget-modal textarea { min-height: 140px; }
            #feedback-widget-context {
                font-size: 0.75rem; color: #6b7280; margin-top: 4px;
            }
        `;
        const style = document.createElement('style');
        style.id = 'feedback-widget-styles';
        style.textContent = css;
        document.head.appendChild(style);
    }

    function injectModal() {
        if (document.getElementById('feedback-widget-modal')) return;
        const html = `
            <div class="modal fade" id="feedback-widget-modal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">💬 Enviar feedback</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
                        </div>
                        <div class="modal-body">
                            <p class="text-muted small mb-2">
                                Cuéntanos un fallo, una sugerencia o algo que no funciona como esperabas.
                                Lo revisamos para mejorar la herramienta.
                            </p>
                            <textarea id="feedback-widget-text" class="form-control"
                                placeholder="Ej: en el kanban, al arrastrar una oportunidad a 'Ganada', no se actualiza el contador..."
                                maxlength="5000"></textarea>
                            <div id="feedback-widget-context"></div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-primary" id="feedback-widget-send">Enviar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        const div = document.createElement('div');
        div.innerHTML = html;
        document.body.appendChild(div.firstElementChild);
    }

    function injectButton() {
        if (document.getElementById('feedback-widget-btn')) return;
        const btn = document.createElement('button');
        btn.id = 'feedback-widget-btn';
        btn.type = 'button';
        btn.title = 'Enviar feedback / reportar fallo';
        btn.setAttribute('aria-label', 'Enviar feedback');
        btn.innerHTML = '💬';
        btn.addEventListener('click', openFeedbackModal);
        document.body.appendChild(btn);
    }

    function openFeedbackModal() {
        const ta = document.getElementById('feedback-widget-text');
        const ctx = document.getElementById('feedback-widget-context');
        if (ta) ta.value = '';
        const view = detectCurrentView();
        if (ctx) ctx.textContent = `Contexto: ${view} — ${location.pathname}`;
        const modalEl = document.getElementById('feedback-widget-modal');
        if (window.bootstrap && bootstrap.Modal) {
            bootstrap.Modal.getOrCreateInstance(modalEl).show();
        } else {
            modalEl.style.display = 'block';
        }
        setTimeout(() => ta && ta.focus(), 200);
    }

    async function sendFeedback() {
        const ta = document.getElementById('feedback-widget-text');
        const sendBtn = document.getElementById('feedback-widget-send');
        const message = (ta?.value || '').trim();
        if (message.length < 3) {
            alert('Escribe un mensaje (mínimo 3 caracteres).');
            return;
        }
        const payload = {
            message,
            view: detectCurrentView(),
            url: location.pathname + location.search,
        };
        sendBtn.disabled = true;
        sendBtn.textContent = 'Enviando...';
        try {
            const res = await fetch('/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(payload),
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || `Error ${res.status}`);
            }
            const modalEl = document.getElementById('feedback-widget-modal');
            if (window.bootstrap && bootstrap.Modal) {
                bootstrap.Modal.getInstance(modalEl)?.hide();
            }
            // Toast simple
            const toast = document.createElement('div');
            toast.textContent = '✅ Feedback enviado. ¡Gracias!';
            toast.style.cssText = 'position:fixed;bottom:90px;right:24px;background:#16a34a;color:#fff;padding:10px 16px;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,.2);z-index:10000;';
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        } catch (e) {
            console.error('[feedback]', e);
            alert('No se pudo enviar el feedback: ' + (e.message || 'error desconocido'));
        } finally {
            sendBtn.disabled = false;
            sendBtn.textContent = 'Enviar';
        }
    }

    function init() {
        // No mostrar en login
        if (location.pathname.includes('/login')) return;
        injectStyles();
        injectModal();
        injectButton();
        document.getElementById('feedback-widget-send')?.addEventListener('click', sendFeedback);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
