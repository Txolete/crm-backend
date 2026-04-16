/**
 * Config Management UI
 * PASO 7 - Admin panel for cfg_* tables
 */

// State
const state = {
    currentEntity: 'regions',
    currentItem: null,
    items: []
};

// Entity configurations
const entityConfig = {
    'regions': {
        title: 'Provincias',
        endpoint: '/config-ui/regions',
        fields: [
            { name: 'name', label: 'Nombre', type: 'text', required: true },
            { name: 'country_code', label: 'Código País', type: 'text', required: false, default: 'ES' },
            { name: 'sort_order', label: 'Orden', type: 'number', required: false, default: 0 },
            { name: 'is_active', label: 'Activo', type: 'checkbox', required: false, default: true }
        ],
        columns: ['Nombre', 'País', 'Orden', 'Estado', 'Acciones']
    },
    'customer-types': {
        title: 'Tipos de Cliente',
        endpoint: '/config-ui/customer-types',
        fields: [
            { name: 'name', label: 'Nombre', type: 'text', required: true },
            { name: 'sort_order', label: 'Orden', type: 'number', required: false, default: 0 },
            { name: 'is_active', label: 'Activo', type: 'checkbox', required: false, default: true }
        ],
        columns: ['Nombre', 'Orden', 'Estado', 'Acciones']
    },
    'lead-sources': {
        title: 'Canales',
        endpoint: '/config-ui/lead-sources',
        fields: [
            { name: 'name', label: 'Nombre', type: 'text', required: true },
            { name: 'category', label: 'Categoría', type: 'text', required: false },
            { name: 'sort_order', label: 'Orden', type: 'number', required: false, default: 0 },
            { name: 'is_active', label: 'Activo', type: 'checkbox', required: false, default: true }
        ],
        columns: ['Nombre', 'Categoría', 'Orden', 'Estado', 'Acciones']
    },
    'contact-roles': {
        title: 'Roles de Contacto',
        endpoint: '/config-ui/contact-roles',
        fields: [
            { name: 'name', label: 'Nombre', type: 'text', required: true },
            { name: 'sort_order', label: 'Orden', type: 'number', required: false, default: 0 },
            { name: 'is_active', label: 'Activo', type: 'checkbox', required: false, default: true }
        ],
        columns: ['Nombre', 'Orden', 'Estado', 'Acciones']
    },
    'task-templates': {
        title: 'Plantillas de Tareas',
        endpoint: '/config-ui/task-templates',
        fields: [
            { name: 'name', label: 'Nombre', type: 'text', required: true },
            { name: 'default_due_days', label: 'Días hasta vencimiento', type: 'number', required: false },
            { name: 'sort_order', label: 'Orden', type: 'number', required: false, default: 0 },
            { name: 'is_active', label: 'Activo', type: 'checkbox', required: false, default: true }
        ],
        columns: ['Nombre', 'Días', 'Orden', 'Estado', 'Acciones']
    },
    'stages': {
        title: 'Etapas (Stages)',
        endpoint: '/config-ui/stages',
        fields: [
            { name: 'key', label: 'Clave', type: 'text', required: true },
            { name: 'name', label: 'Nombre', type: 'text', required: true },
            { name: 'description', label: 'Descripción (tooltip en Kanban)', type: 'textarea', required: false },
            { name: 'outcome', label: 'Resultado', type: 'select', required: true, options: ['open', 'won', 'lost'] },
            { name: 'sort_order', label: 'Orden', type: 'number', required: true },
            { name: 'is_terminal', label: 'Terminal', type: 'checkbox', required: false, default: false },
            { name: 'is_active', label: 'Activo', type: 'checkbox', required: false, default: true }
        ],
        columns: ['Clave', 'Nombre', 'Orden', 'Resultado', 'Terminal', 'Estado', 'Acciones']
    },
    'stage-probabilities': {
        title: 'Probabilidades por Etapa',
        endpoint: '/config-ui/stage-probabilities',
        fields: [
            { name: 'stage_id', label: 'Etapa', type: 'stage-select', required: true },
            { name: 'probability', label: 'Probabilidad (0-1)', type: 'number', required: true, min: 0, max: 1, step: 0.01 }
        ],
        columns: ['Etapa', 'Probabilidad', 'Acciones']
    },
    'opportunity-types': {
        title: 'Tipos de Oportunidad',
        endpoint: '/config-ui/opportunity-types',
        responseKey: 'opportunity_types',
        fields: [
            { name: 'name', label: 'Nombre', type: 'text', required: true },
            { name: 'sort_order', label: 'Orden', type: 'number', required: false, default: 0 },
            { name: 'is_active', label: 'Activo', type: 'checkbox', required: false, default: true }
        ],
        columns: ['Nombre', 'Orden', 'Estado', 'Acciones']
    },
    'lost-reasons': {
        title: 'Motivos de Pérdida',
        endpoint: '/config-ui/lost-reasons',
        responseKey: 'lost_reasons',
        fields: [
            { name: 'name', label: 'Nombre', type: 'text', required: true },
            { name: 'sort_order', label: 'Orden', type: 'number', required: false, default: 0 },
            { name: 'is_active', label: 'Activo', type: 'checkbox', required: false, default: true }
        ],
        columns: ['Nombre', 'Orden', 'Estado', 'Acciones']
    },
    'client-mental-states': {
        title: 'Estado Mental del Cliente',
        endpoint: '/config-ui/client-mental-states',
        responseKey: 'client_mental_states',
        fields: [
            { name: 'name', label: 'Nombre', type: 'text', required: true },
            { name: 'sort_order', label: 'Orden', type: 'number', required: false, default: 0 },
            { name: 'is_active', label: 'Activo', type: 'checkbox', required: false, default: true }
        ],
        columns: ['Nombre', 'Orden', 'Estado', 'Acciones']
    }
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    bindTabEvents();
    loadCurrentEntity();
});

// Bind tab click events
function bindTabEvents() {
    document.querySelectorAll('#config-tabs .nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            document.querySelectorAll('#config-tabs .nav-link').forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            state.currentEntity = link.dataset.entity;
            loadCurrentEntity();
        });
    });
    
    document.getElementById('btn-create').addEventListener('click', () => showCreateModal());
}

// Load current entity data
async function loadCurrentEntity() {
    const config = entityConfig[state.currentEntity];
    document.getElementById('entity-title').textContent = config.title;
    
    showLoading();
    
    try {
        const response = await fetch(config.endpoint, {
            credentials: 'include'
        });
        
        if (!response.ok) throw new Error('Failed to load data');
        
        const data = await response.json();
        
        // Extract items array
        const itemsKey = Object.keys(data).find(k => Array.isArray(data[k]));
        state.items = data[itemsKey] || [];
        
        renderTable();
    } catch (error) {
        console.error('Error loading data:', error);
        showToast('Error al cargar datos', 'danger');
    } finally {
        hideLoading();
    }
}

// Render table
function renderTable() {
    const config = entityConfig[state.currentEntity];
    const thead = document.getElementById('table-header');
    const tbody = document.getElementById('table-body');
    
    // Render header
    thead.innerHTML = `
        <tr>
            ${config.columns.map(col => `<th>${col}</th>`).join('')}
        </tr>
    `;
    
    // Render body
    if (state.items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="' + config.columns.length + '" class="text-center text-muted">No hay datos</td></tr>';
        return;
    }
    
    tbody.innerHTML = state.items.map(item => renderRow(item)).join('');
}

// Render single row
function renderRow(item) {
    const config = entityConfig[state.currentEntity];
    
    switch (state.currentEntity) {
        case 'regions':
            return `
                <tr>
                    <td>${item.name}</td>
                    <td>${item.country_code}</td>
                    <td>${item.sort_order}</td>
                    <td><span class="badge badge-${item.is_active ? 'active' : 'inactive'}">${item.is_active ? 'Activo' : 'Inactivo'}</span></td>
                    <td>${renderActions(item)}</td>
                </tr>
            `;
        case 'customer-types':
        case 'contact-roles':
            return `
                <tr>
                    <td>${item.name}</td>
                    <td>${item.sort_order}</td>
                    <td><span class="badge badge-${item.is_active ? 'active' : 'inactive'}">${item.is_active ? 'Activo' : 'Inactivo'}</span></td>
                    <td>${renderActions(item)}</td>
                </tr>
            `;
        case 'lead-sources':
            return `
                <tr>
                    <td>${item.name}</td>
                    <td>${item.category || '-'}</td>
                    <td>${item.sort_order}</td>
                    <td><span class="badge badge-${item.is_active ? 'active' : 'inactive'}">${item.is_active ? 'Activo' : 'Inactivo'}</span></td>
                    <td>${renderActions(item)}</td>
                </tr>
            `;
        case 'task-templates':
            return `
                <tr>
                    <td>${item.name}</td>
                    <td>${item.default_due_days || '-'}</td>
                    <td>${item.sort_order}</td>
                    <td><span class="badge badge-${item.is_active ? 'active' : 'inactive'}">${item.is_active ? 'Activo' : 'Inactivo'}</span></td>
                    <td>${renderActions(item)}</td>
                </tr>
            `;
        case 'stages':
            return `
                <tr>
                    <td>${item.key}</td>
                    <td>${item.name}</td>
                    <td>${item.sort_order}</td>
                    <td><span class="badge bg-info">${item.outcome}</span></td>
                    <td>${item.is_terminal ? '✓' : '-'}</td>
                    <td><span class="badge badge-${item.is_active ? 'active' : 'inactive'}">${item.is_active ? 'Activo' : 'Inactivo'}</span></td>
                    <td>${renderActions(item)}</td>
                </tr>
            `;
        case 'stage-probabilities':
            return `
                <tr>
                    <td>${item.stage_name || item.stage_id}</td>
                    <td>${(item.probability * 100).toFixed(0)}%</td>
                    <td>${renderActions(item, true)}</td>
                </tr>
            `;
        case 'opportunity-types':
        case 'lost-reasons':
        case 'client-mental-states':
            return `
                <tr>
                    <td>${item.name}</td>
                    <td>${item.sort_order}</td>
                    <td><span class="badge badge-${item.is_active ? 'active' : 'inactive'}">${item.is_active ? 'Activo' : 'Inactivo'}</span></td>
                    <td>${renderActions(item)}</td>
                </tr>
            `;
        default:
            return '';
    }
}

// Render action buttons
function renderActions(item, isProbability = false) {
    const id = isProbability ? item.stage_id : item.id;
    const isActive = item.is_active !== false; // stage_probabilities don't have is_active
    
    let html = `<div class="table-actions">`;
    
    html += `<button class="btn btn-sm btn-outline-primary" onclick="showEditModal('${id}')">
        <i class="bi bi-pencil"></i>
    </button>`;
    
    if (!isProbability && isActive) {
        html += `<button class="btn btn-sm btn-outline-danger" onclick="deactivateItem('${id}')">
            <i class="bi bi-x-circle"></i>
        </button>`;
    } else if (!isProbability && !isActive) {
        html += `<button class="btn btn-sm btn-outline-success" onclick="activateItem('${id}')">
            <i class="bi bi-check-circle"></i>
        </button>`;
    }
    
    if (isProbability) {
        html += `<button class="btn btn-sm btn-outline-danger" onclick="deleteItem('${id}')">
            <i class="bi bi-trash"></i>
        </button>`;
    }
    
    html += `</div>`;
    return html;
}

// Show create modal
function showCreateModal() {
    state.currentItem = null;
    document.getElementById('modal-title').textContent = 'Crear ' + entityConfig[state.currentEntity].title;
    renderForm();
    const modal = new bootstrap.Modal(document.getElementById('entityModal'));
    modal.show();
    
    document.getElementById('btn-save').onclick = saveItem;
}

// Show edit modal
window.showEditModal = function(id) {
    const item = state.items.find(i => {
        if (state.currentEntity === 'stage-probabilities') {
            return i.stage_id === id;
        }
        return i.id === id;
    });
    
    if (!item) return;
    
    state.currentItem = item;
    document.getElementById('modal-title').textContent = 'Editar ' + entityConfig[state.currentEntity].title;
    renderForm(item);
    const modal = new bootstrap.Modal(document.getElementById('entityModal'));
    modal.show();
    
    document.getElementById('btn-save').onclick = saveItem;
};

// Render form
async function renderForm(item = null) {
    const config = entityConfig[state.currentEntity];
    const form = document.getElementById('entity-form');
    
    let html = '';
    
    for (const field of config.fields) {
        let value = item ? item[field.name] : (field.default !== undefined ? field.default : '');
        
        if (field.type === 'checkbox') {
            const checked = item ? item[field.name] : field.default;
            html += `
                <div class="mb-3">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="${field.name}" name="${field.name}" ${checked ? 'checked' : ''}>
                        <label class="form-check-label" for="${field.name}">${field.label}</label>
                    </div>
                </div>
            `;
        } else if (field.type === 'select') {
            html += `
                <div class="mb-3">
                    <label class="form-label">${field.label}${field.required ? ' *' : ''}</label>
                    <select class="form-select" id="${field.name}" name="${field.name}" ${field.required ? 'required' : ''}>
                        ${field.options.map(opt => `<option value="${opt}" ${value === opt ? 'selected' : ''}>${opt}</option>`).join('')}
                    </select>
                </div>
            `;
        } else if (field.type === 'stage-select') {
            // Load stages for stage_probabilities
            const stagesResp = await fetch('/config-ui/stages', { credentials: 'include' });
            const stagesData = await stagesResp.json();
            const stages = stagesData.stages || [];
            
            html += `
                <div class="mb-3">
                    <label class="form-label">${field.label}${field.required ? ' *' : ''}</label>
                    <select class="form-select" id="${field.name}" name="${field.name}" ${field.required ? 'required' : ''} ${item ? 'disabled' : ''}>
                        <option value="">Seleccionar...</option>
                        ${stages.map(s => `<option value="${s.id}" ${value === s.id ? 'selected' : ''}>${s.name}</option>`).join('')}
                    </select>
                </div>
            `;
        } else if (field.type === 'textarea') {
            html += `
                <div class="mb-3">
                    <label class="form-label">${field.label}${field.required ? ' *' : ''}</label>
                    <textarea class="form-control" id="${field.name}" name="${field.name}" rows="3" maxlength="500" ${field.required ? 'required' : ''}>${value || ''}</textarea>
                    <small class="text-muted">Máx. 500 caracteres</small>
                </div>
            `;
        } else {
            const attrs = [];
            if (field.min !== undefined) attrs.push(`min="${field.min}"`);
            if (field.max !== undefined) attrs.push(`max="${field.max}"`);
            if (field.step !== undefined) attrs.push(`step="${field.step}"`);

            html += `
                <div class="mb-3">
                    <label class="form-label">${field.label}${field.required ? ' *' : ''}</label>
                    <input type="${field.type}" class="form-control" id="${field.name}" name="${field.name}" value="${value || ''}" ${field.required ? 'required' : ''} ${attrs.join(' ')}>
                </div>
            `;
        }
    }
    
    form.innerHTML = html;
}

// Save item (create or update)
async function saveItem(force = false) {
    const config = entityConfig[state.currentEntity];
    const form = document.getElementById('entity-form');
    const formData = new FormData(form);
    
    // Always read checkboxes directly from DOM (FormData omits unchecked boxes)
    const data = {};
    config.fields.forEach(field => {
        if (field.type === 'checkbox') {
            const el = document.getElementById(field.name);
            data[field.name] = el ? el.checked : false;
        }
    });
    for (const [key, value] of formData.entries()) {
        const field = config.fields.find(f => f.name === key);
        if (field && field.type !== 'checkbox') {
            if (field.type === 'number') {
                const parsed = parseFloat(value);
                data[key] = isNaN(parsed) ? (field.default !== undefined ? field.default : 0) : parsed;
            } else {
                data[key] = value;
            }
        }
    }
    
    const isUpdate = state.currentItem !== null;
    const id = state.currentEntity === 'stage-probabilities' ? state.currentItem?.stage_id : state.currentItem?.id;
    const url = isUpdate ? 
        (force ? `${config.endpoint}/${id}?force=true` : `${config.endpoint}/${id}`) : 
        config.endpoint;
    const method = isUpdate ? 'PUT' : 'POST';
    
    try {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });
        
        // HOTFIX 7.1: Handle IN_USE conflict on update
        if (response.status === 409) {
            const error = await response.json();
            if (error.detail && error.detail.code === 'IN_USE') {
                showConfirmForceModal(error.detail, () => saveItem(true));
                return;
            }
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail?.message || error.detail || 'Error al guardar');
        }
        
        const result = await response.json();
        const message = result.forced ? 
            `${isUpdate ? 'Actualizado' : 'Creado'} correctamente (forzado)` : 
            `${isUpdate ? 'Actualizado' : 'Creado'} correctamente`;
        showToast(message, result.forced ? 'warning' : 'success');
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('entityModal'));
        modal.hide();
        
        await loadCurrentEntity();
    } catch (error) {
        console.error('Error saving:', error);
        showToast(error.message || 'Error al guardar', 'danger');
    }
}

// Deactivate item
window.deactivateItem = async function(id) {
    if (!confirm('¿Desactivar este elemento?')) return;
    
    const config = entityConfig[state.currentEntity];
    
    await performDeactivate(id, false);
};

// HOTFIX 7.1: Perform deactivate with force option
async function performDeactivate(id, force = false) {
    const config = entityConfig[state.currentEntity];
    const url = force ? `${config.endpoint}/${id}?force=true` : `${config.endpoint}/${id}`;
    
    try {
        const response = await fetch(url, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (response.status === 409) {
            // HOTFIX 7.1: Handle IN_USE conflict
            const error = await response.json();
            if (error.detail && error.detail.code === 'IN_USE') {
                showConfirmForceModal(error.detail, () => performDeactivate(id, true));
                return;
            }
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail?.message || error.detail || 'Error al desactivar');
        }
        
        const result = await response.json();
        const message = result.forced ? 
            'Desactivado correctamente (forzado)' : 
            'Desactivado correctamente';
        showToast(message, result.forced ? 'warning' : 'success');
        await loadCurrentEntity();
    } catch (error) {
        console.error('Error deactivating:', error);
        showToast(error.message || 'Error al desactivar', 'danger');
    }
}

// Activate item
window.activateItem = async function(id) {
    const config = entityConfig[state.currentEntity];
    const item = state.items.find(i => i.id === id);
    
    if (!item) return;
    
    try {
        const response = await fetch(`${config.endpoint}/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ is_active: true })
        });
        
        if (!response.ok) throw new Error('Error al activar');
        
        showToast('Activado correctamente', 'success');
        await loadCurrentEntity();
    } catch (error) {
        console.error('Error activating:', error);
        showToast('Error al activar', 'danger');
    }
};

// Delete item (only for stage_probabilities)
window.deleteItem = async function(id) {
    if (!confirm('¿Eliminar este elemento permanentemente?')) return;
    
    const config = entityConfig[state.currentEntity];
    
    try {
        const response = await fetch(`${config.endpoint}/${id}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al eliminar');
        }
        
        showToast('Eliminado correctamente', 'success');
        await loadCurrentEntity();
    } catch (error) {
        console.error('Error deleting:', error);
        showToast(error.message || 'Error al eliminar', 'danger');
    }
};

// Utilities
function showLoading() {
    document.getElementById('loading').style.display = 'block';
    document.querySelector('.table-responsive').style.display = 'none';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
    document.querySelector('.table-responsive').style.display = 'block';
}

function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    const toastId = 'toast-' + Date.now();
    const bgClass = { success: 'bg-success', danger: 'bg-danger', warning: 'bg-warning', info: 'bg-info' }[type] || 'bg-info';
    
    container.insertAdjacentHTML('beforeend', `
        <div id="${toastId}" class="toast ${bgClass} text-white" role="alert">
            <div class="toast-body">${message}</div>
        </div>
    `);
    
    const toastEl = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
    toast.show();
    
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

// HOTFIX 7.1: Show force confirmation modal
function showConfirmForceModal(errorDetail, retryCallback) {
    const existingModal = document.getElementById('confirmForceModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    const modalHTML = `
        <div class="modal fade" id="confirmForceModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-warning">
                        <h5 class="modal-title">
                            <i class="bi bi-exclamation-triangle"></i> Advertencia: Elemento en Uso
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p><strong>${errorDetail.message}</strong></p>
                        <p class="mb-2">Detalles:</p>
                        <ul>
                            <li>Registros afectados: <strong>${errorDetail.in_use_count}</strong></li>
                            ${errorDetail.change_type ? `<li>Tipo de cambio: <strong>${errorDetail.change_type}</strong></li>` : ''}
                        </ul>
                        <div class="alert alert-warning mb-0">
                            <i class="bi bi-info-circle"></i> Forzar esta operación puede afectar datos en producción. ¿Estás seguro?
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                        <button type="button" class="btn btn-warning" id="btn-force-confirm">
                            <i class="bi bi-lightning-fill"></i> Forzar Operación
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    const modal = new bootstrap.Modal(document.getElementById('confirmForceModal'));
    modal.show();
    
    document.getElementById('btn-force-confirm').addEventListener('click', () => {
        modal.hide();
        retryCallback();
    });
    
    // Clean up modal after hide
    document.getElementById('confirmForceModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// HOTFIX 7.1: Add hint for stages
function addStagesHint() {
    if (state.currentEntity === 'stages') {
        const titleDiv = document.getElementById('entity-title').parentElement;
        const existingHint = document.getElementById('stages-hint');
        if (!existingHint) {
            titleDiv.insertAdjacentHTML('beforeend', `
                <p id="stages-hint" class="text-muted small mb-0 mt-2">
                    <i class="bi bi-info-circle"></i> El Kanban usa <strong>sort_order</strong> para ordenar columnas.
                </p>
            `);
        }
    } else {
        const existingHint = document.getElementById('stages-hint');
        if (existingHint) {
            existingHint.remove();
        }
    }
}

// Update loadCurrentEntity to add hint
const originalLoadCurrentEntity = loadCurrentEntity;
loadCurrentEntity = async function() {
    await originalLoadCurrentEntity();
    addStagesHint();
};
