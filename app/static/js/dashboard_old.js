/**
 * CRM Dashboard - Modular & Maintainable
 * PASO 5 - KPIs + Charts with Chart.js
 * HOTFIX 9.2 - Auth check
 */

// ============================================================================
// 0. AUTHENTICATION CHECK (HOTFIX 9.2)
// ============================================================================

// Check authentication before loading dashboard
(async function checkAuth() {
    try {
        const response = await fetch('/auth/me', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            // Not authenticated - redirect to login
            console.log('Not authenticated, redirecting to login...');
            window.location.href = '/login';
            return;
        }
        
        const userData = await response.json();
        console.log('User authenticated:', userData.email);
        
        // Store user data in state for later use
        state.currentUser = userData;
        
        // Update navbar with user info if needed
        updateNavbarUser(userData);
        
    } catch (error) {
        console.error('Auth check failed:', error);
        window.location.href = '/login';
    }
})();

function updateNavbarUser(user) {
    // Update user dropdown in navbar if it exists
    const userNameElement = document.getElementById('current-user-name');
    if (userNameElement) {
        userNameElement.textContent = user.name;
    }
    
    const userEmailElement = document.getElementById('current-user-email');
    if (userEmailElement) {
        userEmailElement.textContent = user.email;
    }
    
    const userRoleElement = document.getElementById('current-user-role');
    if (userRoleElement) {
        const roleLabels = {
            'admin': 'Administrador',
            'sales': 'Comercial',
            'viewer': 'Visualización'
        };
        userRoleElement.textContent = roleLabels[user.role] || user.role;
    }
}

// ============================================================================
// 1. STATE MANAGEMENT
// ============================================================================

const state = {
    currentUser: null,
    currentYear: 2026,
    dashboardData: null,
    charts: {}
};

function getFiltersFromUI() {
    return {
        year: parseInt(document.getElementById('filter-year').value),
        lead_source_id: document.getElementById('filter-lead-source').value || null,
        customer_type_id: document.getElementById('filter-customer-type').value || null,
        region_id: document.getElementById('filter-region').value || null,
        owner_user_id: document.getElementById('filter-owner').value || null
    };
}

function setFiltersToUI(filters) {
    document.getElementById('filter-year').value = filters.year || 2026;
    document.getElementById('filter-lead-source').value = filters.lead_source_id || '';
    document.getElementById('filter-customer-type').value = filters.customer_type_id || '';
    document.getElementById('filter-region').value = filters.region_id || '';
    document.getElementById('filter-owner').value = filters.owner_user_id || '';
}

function serializeFilters(filters) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
        if (value !== null && value !== '') params.append(key, value);
    });
    return params.toString();
}

// ============================================================================
// 2. API CALLS
// ============================================================================

async function fetchDashboardSummary(filters) {
    const query = serializeFilters(filters);
    const response = await fetch(`/dashboard/summary?${query}`, {
        credentials: 'include'
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
}

async function getTargets(year) {
    const response = await fetch(`/targets?year=${year}`, {
        credentials: 'include'
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
}

async function updateTargets(year, payload) {
    const response = await fetch(`/targets?year=${year}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload)
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
}

async function loadConfigData() {
    try {
        // Load lead sources
        const lsResp = await fetch('/admin/lead-sources', { credentials: 'include' });
        if (lsResp.ok) {
            const lsData = await lsResp.json();
            const select = document.getElementById('filter-lead-source');
            lsData.lead_sources.forEach(ls => {
                select.innerHTML += `<option value="${ls.id}">${ls.name}</option>`;
            });
        }

        // Load customer types
        const ctResp = await fetch('/admin/customer-types', { credentials: 'include' });
        if (ctResp.ok) {
            const ctData = await ctResp.json();
            const select = document.getElementById('filter-customer-type');
            ctData.customer_types.forEach(ct => {
                select.innerHTML += `<option value="${ct.id}">${ct.name}</option>`;
            });
        }

        // Load regions
        const rgResp = await fetch('/admin/regions', { credentials: 'include' });
        if (rgResp.ok) {
            const rgData = await rgResp.json();
            const select = document.getElementById('filter-region');
            rgData.regions.forEach(r => {
                select.innerHTML += `<option value="${r.id}">${r.name}</option>`;
            });
        }

        // Load users
        const usResp = await fetch('/admin/users', { credentials: 'include' });
        if (usResp.ok) {
            const usData = await usResp.json();
            const select = document.getElementById('filter-owner');
            usData.users.forEach(u => {
                select.innerHTML += `<option value="${u.id}">${u.name}</option>`;
            });
        }
    } catch (error) {
        console.warn('Could not load config data:', error);
    }
}

// ============================================================================
// 3. RENDER KPIs
// ============================================================================

function renderKpiCards(data) {
    const { kpis, targets } = data;
    const container = document.getElementById('kpi-grid');
    
    const cards = [
        {
            id: 'kpi-a',
            title: 'Pipeline Total (A)',
            value: kpis.pipeline_total_A,
            target: targets.target_pipeline_total,
            color: 'info'
        },
        {
            id: 'kpi-b',
            title: 'Pipeline Ponderado (B)',
            value: kpis.pipeline_weighted_B,
            target: targets.target_pipeline_weighted,
            color: 'primary'
        },
        {
            id: 'kpi-c',
            title: 'Cerrado Anual (C)',
            value: kpis.closed_total_C,
            target: targets.target_closed,
            color: 'success'
        },
        {
            id: 'kpi-d',
            title: 'Conversión (C/A)',
            value: kpis.conversion_C_over_A_current,
            target: null,
            color: 'warning',
            isPercent: true
        }
    ];
    
    container.innerHTML = cards.map(card => createKpiCardHTML(card)).join('');
}

function createKpiCardHTML(card) {
    const value = card.isPercent 
        ? (card.value ? `${(card.value * 100).toFixed(1)}%` : 'N/A')
        : formatCurrency(card.value);
    
    let progressHTML = '';
    if (card.target) {
        const percent = Math.min((card.value / card.target) * 100, 100);
        const percentText = percent.toFixed(0);
        progressHTML = `
            <div class="kpi-card-progress">
                <div class="kpi-card-progress-label">
                    <span>Objetivo: ${formatCurrency(card.target)}</span>
                    <span>${percentText}%</span>
                </div>
                <div class="progress">
                    <div class="progress-bar" style="width: ${percent}%"></div>
                </div>
            </div>
        `;
    }
    
    return `
        <div class="kpi-card kpi-${card.id.split('-')[1]}">
            <div class="kpi-card-title">${card.title}</div>
            <div class="kpi-card-value">${value}</div>
            ${progressHTML}
        </div>
    `;
}

// ============================================================================
// 4. CHARTS (Chart.js)
// ============================================================================

function initOrUpdatePacingChart(series, targets) {
    const ctx = document.getElementById('chart-pacing');
    
    if (state.charts.pacing) {
        state.charts.pacing.destroy();
    }
    
    state.charts.pacing = new Chart(ctx, {
        type: 'line',
        data: {
            labels: series.months,
            datasets: [
                {
                    label: 'Cerrado Real',
                    data: series.closed_cum,
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Target Acumulado',
                    data: series.target_closed_cum,
                    borderColor: '#6c757d',
                    borderDash: [5, 5],
                    tension: 0.3,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' },
                tooltip: {
                    callbacks: {
                        label: (context) => `${context.dataset.label}: ${formatCurrency(context.parsed.y)}`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: (value) => formatCurrency(value)
                    }
                }
            }
        }
    });
}

function initOrUpdateStageChart(breakdowns) {
    const ctx = document.getElementById('chart-stage');
    
    if (state.charts.stage) {
        state.charts.stage.destroy();
    }
    
    const data = breakdowns.by_stage;
    
    state.charts.stage = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.label),
            datasets: [{
                label: 'Pipeline Ponderado',
                data: data.map(d => d.value),
                backgroundColor: [
                    '#198754', '#0dcaf0', '#0d6efd', 
                    '#6610f2', '#fd7e14'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (context) => formatCurrency(context.parsed.x)
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: (value) => formatCurrency(value)
                    }
                }
            }
        }
    });
}

function initOrUpdateLeadSourceChart(breakdowns) {
    const ctx = document.getElementById('chart-lead-source');
    
    if (state.charts.leadSource) {
        state.charts.leadSource.destroy();
    }
    
    const data = breakdowns.by_lead_source;
    
    state.charts.leadSource = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.label),
            datasets: [{
                label: 'Pipeline Ponderado',
                data: data.map(d => d.value),
                backgroundColor: '#0066cc'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (context) => formatCurrency(context.parsed.y)
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: (value) => formatCurrency(value)
                    }
                }
            }
        }
    });
}

function initOrUpdateConversionChart(series) {
    const ctx = document.getElementById('chart-conversion');
    
    if (state.charts.conversion) {
        state.charts.conversion.destroy();
    }
    
    // Convert nulls to 0 for display
    const data = series.conversion_c_over_a.map(v => v !== null ? v * 100 : 0);
    
    state.charts.conversion = new Chart(ctx, {
        type: 'line',
        data: {
            labels: series.months,
            datasets: [{
                label: 'Conversión C/A (%)',
                data: data,
                borderColor: '#ffc107',
                backgroundColor: 'rgba(255, 193, 7, 0.1)',
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (context) => `${context.parsed.y.toFixed(1)}%`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: (value) => `${value}%`
                    }
                }
            }
        }
    });
}

// ============================================================================
// 5. UI EVENTS & MAIN FLOW
// ============================================================================

function detectUser() {
    const userSpan = document.querySelector('.navbar-nav .text-muted');
    if (userSpan) {
        const roleMatch = userSpan.textContent.match(/\((\w+)\)/);
        state.currentUser = { role: roleMatch ? roleMatch[1] : 'viewer' };
    }
}

function bindEvents() {
    // Apply filters
    document.querySelector('.filters-bar .btn-primary').addEventListener('click', applyFilters);
    
    // Reset filters
    document.querySelector('.filters-bar .btn-outline-secondary').addEventListener('click', resetFilters);
    
    // Edit targets (hide for non-admin)
    const editTargetsLink = document.querySelector('[onclick*="showEditTargetsModal"]');
    if (editTargetsLink && state.currentUser?.role !== 'admin') {
        editTargetsLink.parentElement.style.display = 'none';
    }
}

async function applyFilters() {
    const filters = getFiltersFromUI();
    state.currentYear = filters.year;
    await loadDashboard();
    showActiveFiltersLabel(filters);
}

function resetFilters() {
    setFiltersToUI({ year: 2026 });
    state.currentYear = 2026;
    loadDashboard();
    hideActiveFiltersLabel();
}

function showActiveFiltersLabel(filters) {
    const label = document.getElementById('filter-active-label');
    const active = [];
    
    if (filters.lead_source_id) active.push('Canal');
    if (filters.customer_type_id) active.push('Tipo Cliente');
    if (filters.region_id) active.push('Provincia');
    if (filters.owner_user_id) active.push('Owner');
    
    if (active.length > 0) {
        label.innerHTML = `<span class="filter-active-label"><i class="bi bi-funnel-fill"></i> Filtros activos: ${active.join(', ')}</span>`;
        label.style.display = 'block';
    } else {
        label.style.display = 'none';
    }
}

function hideActiveFiltersLabel() {
    document.getElementById('filter-active-label').style.display = 'none';
}

async function loadDashboard() {
    try {
        const filters = getFiltersFromUI();
        const data = await fetchDashboardSummary(filters);
        
        state.dashboardData = data;
        
        // Render KPIs
        renderKpiCards(data);
        
        // Render Charts
        initOrUpdatePacingChart(data.series, data.targets);
        initOrUpdateStageChart(data.breakdowns);
        initOrUpdateLeadSourceChart(data.breakdowns);
        initOrUpdateConversionChart(data.series);
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showToast('Error al cargar el dashboard', 'danger');
    }
}

async function showEditTargetsModal() {
    if (state.currentUser?.role !== 'admin') {
        showToast('Solo administradores pueden editar objetivos', 'warning');
        return;
    }
    
    try {
        const targets = await getTargets(state.currentYear);
        
        document.getElementById('modal-year').textContent = state.currentYear;
        document.getElementById('target-pipeline-total').value = targets.target_pipeline_total;
        document.getElementById('target-pipeline-weighted').value = targets.target_pipeline_weighted;
        document.getElementById('target-closed').value = targets.target_closed;
        
        const modal = new bootstrap.Modal(document.getElementById('editTargetsModal'));
        modal.show();
    } catch (error) {
        console.error('Error loading targets:', error);
        showToast('Error al cargar objetivos', 'danger');
    }
}

async function saveTargets() {
    try {
        const payload = {
            target_pipeline_total: parseFloat(document.getElementById('target-pipeline-total').value),
            target_pipeline_weighted: parseFloat(document.getElementById('target-pipeline-weighted').value),
            target_closed: parseFloat(document.getElementById('target-closed').value)
        };
        
        await updateTargets(state.currentYear, payload);
        
        showToast('Objetivos actualizados correctamente', 'success');
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('editTargetsModal'));
        modal.hide();
        
        // Reload dashboard
        await loadDashboard();
        
    } catch (error) {
        console.error('Error saving targets:', error);
        showToast('Error al guardar objetivos', 'danger');
    }
}

// ============================================================================
// 6. UTILITIES
// ============================================================================

function formatCurrency(value) {
    if (value === null || value === undefined) return '€0';
    return new Intl.NumberFormat('es-ES', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
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

// ============================================================================
// 7. INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', async () => {
    detectUser();
    await loadConfigData();
    await loadDashboard();
    bindEvents();
});

// Make functions global for onclick handlers
window.applyFilters = applyFilters;
window.resetFilters = resetFilters;
window.showEditTargetsModal = showEditTargetsModal;
window.saveTargets = saveTargets;

// ============================================================================
// 8. IMPORT EXCEL (PASO 6)
// ============================================================================

function showImportModal() {
    // Check role
    if (state.currentUser?.role === 'viewer') {
        showToast('Solo admin/sales pueden importar', 'warning');
        return;
    }
    
    // Reset form
    document.getElementById('form-import').reset();
    document.getElementById('import-results').style.display = 'none';
    document.getElementById('import-progress').style.display = 'none';
    
    const modal = new bootstrap.Modal(document.getElementById('importExcelModal'));
    modal.show();
}

async function runImport() {
    const fileInput = document.getElementById('import-file');
    const dryRun = document.getElementById('import-dry-run').checked;
    
    if (!fileInput.files.length) {
        showToast('Selecciona un archivo', 'warning');
        return;
    }
    
    const file = fileInput.files[0];
    
    // Show progress
    document.getElementById('import-progress').style.display = 'block';
    document.getElementById('import-results').style.display = 'none';
    document.getElementById('btn-run-import').disabled = true;
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`/import/excel?dry_run=${dryRun}`, {
            method: 'POST',
            credentials: 'include',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error en importación');
        }
        
        const data = await response.json();
        
        // Hide progress
        document.getElementById('import-progress').style.display = 'none';
        
        // Show results
        displayImportResults(data);
        
        showToast(
            `Importación ${dryRun ? 'validada' : 'completada'}: ${data.imported_rows}/${data.total_rows}`,
            data.failed_rows > 0 ? 'warning' : 'success'
        );
        
        // Reload dashboard if not dry run
        if (!dryRun) {
            setTimeout(() => loadDashboard(), 2000);
        }
        
    } catch (error) {
        console.error('Import error:', error);
        document.getElementById('import-progress').style.display = 'none';
        showToast(error.message || 'Error al importar', 'danger');
    } finally {
        document.getElementById('btn-run-import').disabled = false;
    }
}

function displayImportResults(data) {
    // Update summary cards
    document.getElementById('result-total').textContent = data.total_rows;
    document.getElementById('result-imported').textContent = data.imported_rows;
    document.getElementById('result-failed').textContent = data.failed_rows;
    document.getElementById('result-warnings').textContent = data.warnings_count;
    
    // Build table
    const tbody = document.getElementById('import-results-tbody');
    tbody.innerHTML = '';
    
    data.items.forEach(item => {
        const statusClass = item.status === 'imported' ? 'success' : 'danger';
        const statusIcon = item.status === 'imported' ? 'check-circle' : 'x-circle';
        
        const messages = [];
        if (item.errors.length > 0) {
            messages.push(...item.errors.map(e => `<span class="text-danger">❌ ${e}</span>`));
        }
        if (item.warnings.length > 0) {
            messages.push(...item.warnings.map(w => `<span class="text-warning">⚠️ ${w}</span>`));
        }
        
        const row = `
            <tr>
                <td>${item.row}</td>
                <td>${item.account_name || '-'}</td>
                <td>
                    <i class="bi bi-${statusIcon} text-${statusClass}"></i>
                    ${item.status}
                </td>
                <td><small>${messages.join('<br>')}</small></td>
            </tr>
        `;
        
        tbody.innerHTML += row;
    });
    
    document.getElementById('import-results').style.display = 'block';
}

// Bind import button
document.addEventListener('DOMContentLoaded', () => {
    const btnImport = document.getElementById('btn-run-import');
    if (btnImport) {
        btnImport.addEventListener('click', runImport);
    }
    
    // Hide import button for viewers
    const btnImportExcel = document.getElementById('btn-import-excel');
    if (btnImportExcel) {
        const userSpan = document.querySelector('.navbar-nav .text-muted');
        if (userSpan) {
            const roleMatch = userSpan.textContent.match(/\((\w+)\)/);
            const role = roleMatch ? roleMatch[1] : 'viewer';
            if (role === 'viewer') {
                btnImportExcel.style.display = 'none';
            }
        }
    }
});

window.showImportModal = showImportModal;
window.runImport = runImport;

// ============================================================================
// PASO 8 - TASKS OVERVIEW (SEMÁFORO)
// ============================================================================

// Load tasks overview when tab is shown
document.getElementById('tasks-tab').addEventListener('shown.bs.tab', function() {
    loadTasksOverview();
});

async function loadTasksOverview() {
    try {
        const response = await fetch('/tasks/overview?assigned_to=me', {
            credentials: 'include'
        });
        
        if (!response.ok) throw new Error('Failed to load tasks');
        
        const data = await response.json();
        
        // Update badges
        document.getElementById('badge-overdue').textContent = data.total_overdue;
        document.getElementById('badge-due-soon').textContent = data.total_due_soon;
        document.getElementById('badge-upcoming').textContent = data.total_upcoming;
        
        // Render task lists
        renderTaskList('tasks-overdue', data.overdue, 'danger');
        renderTaskList('tasks-due-soon', data.due_soon, 'warning');
        renderTaskList('tasks-upcoming', data.upcoming, 'success');
        
    } catch (error) {
        console.error('Error loading tasks overview:', error);
        showToast('Error al cargar tareas', 'danger');
    }
}

function renderTaskList(containerId, tasks, colorClass) {
    const container = document.getElementById(containerId);
    
    if (tasks.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">Sin tareas</p>';
        return;
    }
    
    let html = '';
    tasks.forEach(task => {
        html += `
            <div class="card mb-2 task-card" style="cursor: pointer;" onclick="openOpportunity('${task.opportunity_id}')">
                <div class="card-body p-2">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <strong>${task.title}</strong>
                            <br>
                            <small class="text-muted">
                                <i class="bi bi-building"></i> ${task.account_name}
                            </small>
                            <br>
                            <small class="text-muted">
                                <i class="bi bi-diagram-3"></i> ${task.stage_name}
                            </small>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-${colorClass}">
                                ${task.due_date}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Open opportunity drawer (reuse existing function)
function openOpportunity(oppId) {
    // This function should already exist from kanban functionality
    // If not, implement drawer opening logic here
    if (typeof window.openOppDrawer === 'function') {
        window.openOppDrawer(oppId);
    } else {
        console.warn('openOppDrawer function not found');
    }
}

// ============================================================================
// LOGOUT HANDLER (HOTFIX 9.4 - FUNCIÓN GLOBAL)
// ============================================================================

window.handleLogout = async function() {
    try {
        const response = await fetch('/auth/logout', {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok) {
            // Redirect to login page
            window.location.href = '/login';
        } else {
            console.error('Logout failed');
            // Still redirect to login even if logout endpoint failed
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Logout error:', error);
        // Still redirect to login on error
        window.location.href = '/login';
    }
}

// ============================================================================
// NUEVA OPORTUNIDAD (HOTFIX 9.4 - FUNCIONES GLOBALES)
// ============================================================================

window.showNewOpportunityModal = async function() {
    console.log('showNewOpportunityModal called');
    
    try {
        console.log('Fetching stages...');
        
        // Load stages first (critical)
        const stagesResponse = await fetch('/config/stages', {
            credentials: 'include'
        });
        
        console.log('Stages response status:', stagesResponse.status);
        
        if (!stagesResponse.ok) {
            console.error('Stages fetch failed with status:', stagesResponse.status);
            alert('❌ Error al cargar stages (código ' + stagesResponse.status + ').\n\nAbre F12 → Console para ver el error.');
            return;
        }
        
        const stagesData = await stagesResponse.json();
        console.log('Stages data:', stagesData);
        
        if (!stagesData || stagesData.length === 0) {
            console.error('No stages in response');
            alert('❌ No se recibieron stages del servidor.\n\nAbre F12 → Console para ver el error.');
            return;
        }
        
        const openStages = stagesData.filter(stage => stage.outcome === 'open');
        console.log('Open stages:', openStages);
        
        if (openStages.length === 0) {
            alert('❌ No hay stages abiertos disponibles.');
            return;
        }
        
        console.log('Fetching accounts...');
        
        // Load accounts
        const accountsResponse = await fetch('/accounts?status=active', {
            credentials: 'include'
        });
        
        console.log('Accounts response status:', accountsResponse.status);
        
        if (!accountsResponse.ok) {
            console.error('Accounts fetch failed');
            alert('⚠️ Error al cargar cuentas.\n\nCrea una cuenta primero.');
            return;
        }
        
        const accountsData = await accountsResponse.json();
        console.log('Accounts data:', accountsData);
        
        // Extract accounts array from response
        const accounts = accountsData.accounts || accountsData;
        
        // Check if there are accounts
        if (!accounts || accounts.length === 0) {
            console.log('No accounts found, offering to create one');
            
            const createAccount = confirm(
                'No hay cuentas creadas.\n\n' +
                '¿Quieres crear una cuenta de ejemplo?\n\n' +
                '(Luego puedes editarla)'
            );
            
            if (createAccount) {
                console.log('Creating example account...');
                
                const accountResponse = await fetch('/accounts', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        name: 'Cuenta de Ejemplo',
                        status: 'active'
                    })
                });
                
                if (accountResponse.ok) {
                    alert('✅ Cuenta creada. Ahora puedes crear la oportunidad.');
                    showNewOpportunityModal();
                    return;
                } else {
                    alert('❌ Error al crear cuenta.');
                    return;
                }
            } else {
                alert('Necesitas crear una cuenta primero.');
                return;
            }
        }
        
        console.log('Populating form...');
        
        // Populate accounts select
        const accountSelect = document.getElementById('new-opp-account');
        if (!accountSelect) {
            console.error('Account select not found!');
            alert('❌ Error: No se encontró el campo de cuenta en el formulario.');
            return;
        }
        
        accountSelect.innerHTML = '<option value="">Seleccionar cuenta...</option>';
        accounts.forEach(account => {
            const option = document.createElement('option');
            option.value = account.id;
            option.textContent = account.name;
            accountSelect.appendChild(option);
        });
        
        // Populate stages select
        const stageSelect = document.getElementById('new-opp-stage');
        if (!stageSelect) {
            console.error('Stage select not found!');
            alert('❌ Error: No se encontró el campo de stage en el formulario.');
            return;
        }
        
        stageSelect.innerHTML = '';
        openStages.forEach(stage => {
            const option = document.createElement('option');
            option.value = stage.id;
            option.textContent = stage.name;
            stageSelect.appendChild(option);
        });
        
        console.log('Showing modal...');
        
        // Show modal
        const modalElement = document.getElementById('newOppModal');
        if (!modalElement) {
            console.error('Modal element not found!');
            alert('❌ Error: No se encontró el modal en el HTML.');
            return;
        }
        
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
        
        console.log('Modal shown successfully');
        
    } catch (error) {
        console.error('Error in showNewOpportunityModal:', error);
        alert('❌ Error: ' + error.message + '\n\nAbre F12 → Console para más detalles.');
    }
}

window.createOpportunity = async function() {
    try {
        const accountId = document.getElementById('new-opp-account').value;
        const name = document.getElementById('new-opp-name').value;
        const stageId = document.getElementById('new-opp-stage').value;
        const value = parseFloat(document.getElementById('new-opp-value').value);
        const forecast = document.getElementById('new-opp-forecast').value;
        
        // Validate
        if (!accountId || !stageId || !value) {
            alert('Por favor completa todos los campos obligatorios');
            return;
        }
        
        // Create opportunity
        const response = await fetch('/opportunities', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                account_id: accountId,
                name: name || null,
                stage_id: stageId,
                expected_value_eur: value,
                forecast_close_month: forecast || null,
                owner_user_id: state.currentUser ? state.currentUser.id : null
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al crear oportunidad');
        }
        
        // Get modal instance
        const modalElement = document.getElementById('newOppModal');
        const modal = bootstrap.Modal.getInstance(modalElement);
        
        // Close modal and clean up
        if (modal) {
            modal.hide();
        }
        
        // Clear form
        document.getElementById('form-new-opp').reset();
        
        // Force cleanup of modal to fix scroll bug
        setTimeout(() => {
            forceModalCleanup();
        }, 300);
        
        // Show success message (non-blocking)
        showToast('Oportunidad creada exitosamente', 'success');
        
        // Reload kanban (if we're on kanban tab) and dashboard
        if (typeof loadKanbanData === 'function') {
            await loadKanbanData();
        }
        await loadDashboard();
        
    } catch (error) {
        console.error('Error creating opportunity:', error);
        alert('❌ Error al crear oportunidad: ' + error.message);
    }
}

// ============================================================================
// OPPORTUNITY DETAIL MODAL
// ============================================================================

let currentOpportunityId = null;

/**
 * Show opportunity detail modal
 */
window.showOpportunityDetail = async function(opportunityId) {
    console.log('[DETAIL] Showing detail for opportunity:', opportunityId);
    
    currentOpportunityId = opportunityId;
    currentOpportunityData = null;
    
    // Show modal with loading state
    const modalElement = document.getElementById('oppDetailModal');
    const modal = new bootstrap.Modal(modalElement);
    
    // Reset to view mode (not edit mode)
    document.getElementById('oppDetailContent').style.display = 'none';
    document.getElementById('oppEditForm').style.display = 'none';
    document.getElementById('oppDetailLoading').style.display = 'block';
    document.getElementById('detail-task-card').style.display = 'none';
    
    // Reset buttons to initial state
    document.getElementById('btn-edit-opp').style.display = 'none';
    document.getElementById('btn-cancel-edit').style.display = 'none';
    document.getElementById('btn-save-opp').style.display = 'none';
    document.getElementById('btn-close-detail').style.display = 'inline-block';
    
    modal.show();
    
    try {
        // Load opportunity data
        await loadOpportunityDetail(opportunityId);
        
        // Load activities
        await loadOpportunityActivities(opportunityId);
        
        // Hide loading, show content
        document.getElementById('oppDetailLoading').style.display = 'none';
        document.getElementById('oppDetailContent').style.display = 'block';
        
    } catch (error) {
        console.error('[DETAIL] Error loading opportunity:', error);
        document.getElementById('oppDetailLoading').innerHTML = `
            <div class="alert alert-danger">
                <strong>Error:</strong> No se pudo cargar la oportunidad.<br>
                ${error.message}
            </div>
        `;
    }
}

/**
 * Load opportunity basic data
 */
async function loadOpportunityDetail(opportunityId) {
    console.log('[DETAIL] Loading opportunity data:', opportunityId);
    
    const response = await fetch(`/opportunities/${opportunityId}`, {
        credentials: 'include'
    });
    
    if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
    }
    
    const opp = await response.json();
    console.log('[DETAIL] Opportunity data loaded:', opp);
    
    // Store opportunity data for editing
    currentOpportunityData = opp;
    
    // Show edit button
    document.getElementById('btn-edit-opp').style.display = 'inline-block';
    
    // Update modal title
    document.getElementById('oppDetailTitle').textContent = 
        opp.name || `Oportunidad ${opp.account_name}`;
    
    // Fill basic data
    document.getElementById('detail-account').textContent = opp.account_name || '-';
    document.getElementById('detail-name').textContent = opp.name || '(Sin nombre)';
    document.getElementById('detail-stage').innerHTML = `
        <span class="badge bg-secondary">${opp.stage_name || '-'}</span>
    `;
    
    // Probability
    const probability = opp.probability_override !== null 
        ? opp.probability_override 
        : opp.stage_probability;
    document.getElementById('detail-probability').textContent = 
        probability !== null ? `${(probability * 100).toFixed(0)}%` : '-';
    
    // Values
    document.getElementById('detail-value').innerHTML = `
        <strong class="text-primary">€${formatNumber(opp.expected_value_eur)}</strong>
    `;
    
    const weightedValue = opp.weighted_value_override_eur !== null
        ? opp.weighted_value_override_eur
        : (opp.expected_value_eur * (probability || 0));
    document.getElementById('detail-weighted').innerHTML = `
        <strong class="text-success">€${formatNumber(weightedValue)}</strong>
    `;
    
    // Forecast
    document.getElementById('detail-forecast').textContent = 
        opp.forecast_close_month || '-';
    
    // Owner
    document.getElementById('detail-owner').textContent = 
        opp.owner_user_name || '(Sin asignar)';
    
    // Next task (if exists)
    if (opp.next_task) {
        document.getElementById('detail-task-card').style.display = 'block';
        
        const dueDate = opp.next_task.due_date ? 
            new Date(opp.next_task.due_date).toLocaleDateString('es-ES') : 
            'Sin fecha';
        
        const isOverdue = opp.next_task.due_date && 
            new Date(opp.next_task.due_date) < new Date();
        
        document.getElementById('detail-task-content').innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <strong>${opp.next_task.title}</strong>
                    <div class="small ${isOverdue ? 'text-danger' : 'text-muted'}">
                        <i class="bi bi-calendar"></i> ${dueDate}
                        ${isOverdue ? '<span class="badge bg-danger ms-2">Atrasada</span>' : ''}
                    </div>
                </div>
                <span class="badge ${opp.next_task.status === 'open' ? 'bg-warning' : 'bg-success'}">
                    ${opp.next_task.status === 'open' ? 'Pendiente' : 'Completada'}
                </span>
            </div>
        `;
    }
}

/**
 * Load opportunity activities (timeline)
 */
async function loadOpportunityActivities(opportunityId) {
    console.log('[DETAIL] Loading activities for opportunity:', opportunityId);
    
    // Show loading
    document.getElementById('detail-activities-loading').style.display = 'block';
    document.getElementById('detail-activities-content').style.display = 'none';
    document.getElementById('detail-activities-empty').style.display = 'none';
    
    try {
        const response = await fetch(`/opportunities/${opportunityId}/activities`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`Error ${response.status}`);
        }
        
        const data = await response.json();
        const activities = data.activities || [];
        console.log('[DETAIL] Activities loaded:', activities.length);
        
        // Hide loading
        document.getElementById('detail-activities-loading').style.display = 'none';
        
        if (activities.length === 0) {
            document.getElementById('detail-activities-empty').style.display = 'block';
            return;
        }
        
        // Render activities
        const activitiesHtml = activities.map(activity => {
            const date = new Date(activity.occurred_at);
            const formattedDate = date.toLocaleDateString('es-ES', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            
            let icon = 'bi-info-circle';
            let color = 'secondary';
            
            if (activity.type === 'status_change') {
                icon = 'bi-arrow-right-circle';
                color = 'primary';
            } else if (activity.type === 'note') {
                icon = 'bi-chat-left-text';
                color = 'info';
            } else if (activity.type === 'email') {
                icon = 'bi-envelope';
                color = 'success';
            }
            
            return `
                <div class="d-flex mb-3 pb-3 border-bottom">
                    <div class="me-3">
                        <div class="rounded-circle bg-${color} text-white d-flex align-items-center justify-content-center" 
                             style="width: 40px; height: 40px;">
                            <i class="bi ${icon}"></i>
                        </div>
                    </div>
                    <div class="flex-grow-1">
                        <div class="d-flex justify-content-between align-items-start">
                            <strong>${activity.summary}</strong>
                            <small class="text-muted">${formattedDate}</small>
                        </div>
                        ${activity.created_by_user_name ? 
                            `<div class="small text-muted">Por: ${activity.created_by_user_name}</div>` : 
                            ''}
                    </div>
                </div>
            `;
        }).join('');
        
        document.getElementById('detail-activities-content').innerHTML = activitiesHtml;
        document.getElementById('detail-activities-content').style.display = 'block';
        
    } catch (error) {
        console.error('[DETAIL] Error loading activities:', error);
        document.getElementById('detail-activities-loading').innerHTML = `
            <div class="text-danger small">Error al cargar actividades</div>
        `;
    }
}

/**
 * Format number with thousands separator
 */
function formatNumber(num) {
    if (num === null || num === undefined) return '0';
    return new Intl.NumberFormat('es-ES', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    }).format(num);
}

// ============================================================================
// EDIT OPPORTUNITY
// ============================================================================

let currentOpportunityData = null;

/**
 * Switch to edit mode
 */
window.switchToEditMode = async function() {
    console.log('[EDIT] Switching to edit mode');
    
    if (!currentOpportunityId || !currentOpportunityData) {
        console.error('[EDIT] No opportunity data loaded');
        return;
    }
    
    try {
        // Load stages and users for selects
        const [stagesResponse, usersResponse] = await Promise.all([
            fetch('/config/stages', { credentials: 'include' }),
            fetch('/admin/users', { credentials: 'include' })  // Corregido: /admin/users
        ]);
        
        if (!stagesResponse.ok || !usersResponse.ok) {
            throw new Error('Error loading form data');
        }
        
        const stages = await stagesResponse.json();
        const usersData = await usersResponse.json();
        const users = usersData.users || usersData;
        
        // Populate stage select (ALL stages including won/lost)
        const stageSelect = document.getElementById('edit-stage');
        stageSelect.innerHTML = '';
        stages.forEach(stage => {
            const option = document.createElement('option');
            option.value = stage.id;
            option.textContent = stage.name;
            option.selected = stage.id === currentOpportunityData.stage_id;
            stageSelect.appendChild(option);
        });
        
        // Populate owner select
        const ownerSelect = document.getElementById('edit-owner');
        ownerSelect.innerHTML = '<option value="">Sin asignar</option>';
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = user.name;
            option.selected = user.id === currentOpportunityData.owner_user_id;
            ownerSelect.appendChild(option);
        });
        
        // Fill form with current data
        document.getElementById('edit-account').value = currentOpportunityData.account_name;
        document.getElementById('edit-name').value = currentOpportunityData.name || '';
        document.getElementById('edit-value').value = currentOpportunityData.expected_value_eur;
        document.getElementById('edit-forecast').value = currentOpportunityData.forecast_close_month || '';
        
        // Weighted override
        if (currentOpportunityData.weighted_value_override_eur !== null) {
            document.getElementById('edit-weighted-override').value = currentOpportunityData.weighted_value_override_eur;
        } else {
            document.getElementById('edit-weighted-override').value = '';
        }
        
        // Probability override (convert to percentage)
        if (currentOpportunityData.probability_override !== null) {
            document.getElementById('edit-probability-override').value = (currentOpportunityData.probability_override * 100).toFixed(0);
        } else {
            document.getElementById('edit-probability-override').value = '';
        }
        
        // Hide view, show edit
        document.getElementById('oppDetailContent').style.display = 'none';
        document.getElementById('oppEditForm').style.display = 'block';
        
        // Hide "Editar", show "Cancelar" and "Guardar"
        document.getElementById('btn-edit-opp').style.display = 'none';
        document.getElementById('btn-cancel-edit').style.display = 'inline-block';
        document.getElementById('btn-save-opp').style.display = 'inline-block';
        document.getElementById('btn-close-detail').style.display = 'none';
        
        console.log('[EDIT] Edit mode activated');
        
    } catch (error) {
        console.error('[EDIT] Error switching to edit mode:', error);
        showToast('Error al cargar formulario de edición', 'error');
    }
}

/**
 * Cancel edit and return to view mode
 */
window.cancelEdit = function() {
    console.log('[EDIT] Canceling edit');
    
    // Show view, hide edit
    document.getElementById('oppDetailContent').style.display = 'block';
    document.getElementById('oppEditForm').style.display = 'none';
    
    // Show "Editar", hide "Cancelar" and "Guardar"
    document.getElementById('btn-edit-opp').style.display = 'inline-block';
    document.getElementById('btn-cancel-edit').style.display = 'none';
    document.getElementById('btn-save-opp').style.display = 'none';
    document.getElementById('btn-close-detail').style.display = 'inline-block';
}

/**
 * Save opportunity changes
 */
window.saveOpportunityChanges = async function() {
    console.log('[EDIT] Saving changes');
    
    if (!currentOpportunityId) {
        console.error('[EDIT] No opportunity ID');
        return;
    }
    
    try {
        // Get form values
        const name = document.getElementById('edit-name').value.trim() || null;
        const stageId = document.getElementById('edit-stage').value;
        const value = parseFloat(document.getElementById('edit-value').value);
        const forecast = document.getElementById('edit-forecast').value || null;
        const ownerId = document.getElementById('edit-owner').value || null;
        
        // Get overrides (optional)
        const weightedOverride = document.getElementById('edit-weighted-override').value;
        const probabilityOverride = document.getElementById('edit-probability-override').value;
        
        // Validate
        if (!stageId || !value || value < 0) {
            alert('Por favor completa todos los campos obligatorios correctamente');
            return;
        }
        
        // Build update payload
        const updateData = {
            name: name,
            stage_id: stageId,
            expected_value_eur: value,
            forecast_close_month: forecast,
            owner_user_id: ownerId
        };
        
        // Add overrides if provided
        if (weightedOverride && weightedOverride.trim() !== '') {
            updateData.weighted_value_override_eur = parseFloat(weightedOverride);
        }
        
        if (probabilityOverride && probabilityOverride.trim() !== '') {
            // Convert percentage to decimal (0-1)
            updateData.probability_override = parseFloat(probabilityOverride) / 100;
        }
        
        console.log('[EDIT] Update data:', updateData);
        
        // Send PUT request
        const response = await fetch(`/opportunities/${currentOpportunityId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(updateData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al actualizar oportunidad');
        }
        
        console.log('[EDIT] Opportunity updated successfully');
        
        // Reload opportunity data
        await loadOpportunityDetail(currentOpportunityId);
        await loadOpportunityActivities(currentOpportunityId);
        
        // Switch back to view mode
        cancelEdit();
        
        // Reload kanban to reflect changes
        if (typeof loadKanbanData === 'function') {
            await loadKanbanData();
        }
        await loadDashboard();
        
        // Show success message at the END (after everything is reloaded)
        showToast('✅ Oportunidad actualizada exitosamente', 'success');
        
    } catch (error) {
        console.error('[EDIT] Error saving changes:', error);
        
        // Show error message with toast (consistent with success)
        showToast('❌ Error al guardar: ' + error.message, 'error');
        
        // Don't switch back to view mode on error - user can fix and retry
    }
}

// ============================================================================
// FIX: Improve modal cleanup to fix scroll bug
// ============================================================================

/**
 * Force cleanup of modal and restore scroll
 */
function forceModalCleanup() {
    // Remove all modal backdrops
    const backdrops = document.querySelectorAll('.modal-backdrop');
    backdrops.forEach(backdrop => backdrop.remove());
    
    // Remove modal-open class from body
    document.body.classList.remove('modal-open');
    
    // Force restore scroll
    document.body.style.overflow = 'auto';
    document.body.style.paddingRight = '';
    
    // Force restore html scroll
    document.documentElement.style.overflow = 'auto';
    
    console.log('[MODAL] Forced cleanup completed');
}

// ============================================================================
// EVENT LISTENERS (HOTFIX 9.3)
// ============================================================================

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    // New Opportunity button
    const btnNewOpp = document.getElementById('btn-new-opp');
    if (btnNewOpp) {
        btnNewOpp.addEventListener('click', showNewOpportunityModal);
    }
    
    // Save New Opportunity button
    const btnSaveNewOpp = document.getElementById('btn-save-new-opp');
    if (btnSaveNewOpp) {
        btnSaveNewOpp.addEventListener('click', createOpportunity);
    }
    
    // Import Excel button (navbar)
    const btnImportExcel = document.getElementById('btn-import-excel');
    if (btnImportExcel) {
        btnImportExcel.addEventListener('click', showImportModal);
    }
    
    // Edit Opportunity button
    const btnEditOpp = document.getElementById('btn-edit-opp');
    if (btnEditOpp) {
        btnEditOpp.addEventListener('click', switchToEditMode);
    }
    
    // Cancel Edit button
    const btnCancelEdit = document.getElementById('btn-cancel-edit');
    if (btnCancelEdit) {
        btnCancelEdit.addEventListener('click', cancelEdit);
    }
    
    // Save Opportunity Changes button
    const btnSaveOpp = document.getElementById('btn-save-opp');
    if (btnSaveOpp) {
        btnSaveOpp.addEventListener('click', saveOpportunityChanges);
    }
    
    // Clean up modals when closed
    const newOppModal = document.getElementById('newOppModal');
    if (newOppModal) {
        newOppModal.addEventListener('hidden.bs.modal', function() {
            console.log('[MODAL] newOppModal closed, forcing cleanup');
            setTimeout(forceModalCleanup, 300);
        });
    }
    
    const oppDetailModal = document.getElementById('oppDetailModal');
    if (oppDetailModal) {
        oppDetailModal.addEventListener('hidden.bs.modal', function() {
            console.log('[MODAL] oppDetailModal closed, forcing cleanup');
            setTimeout(forceModalCleanup, 300);
        });
    }
});

// ============================================================================
// KANBAN - FUNCIONES DE CARGA Y RENDERIZADO
// ============================================================================

async function loadKanbanData() {
    console.log('[KANBAN] Loading kanban data...');
    
    try {
        // Get filters
        const searchValue = document.getElementById('kanban-search')?.value || '';
        const hideClosedCheckbox = document.getElementById('kanban-hide-closed');
        const hideClosed = hideClosedCheckbox?.checked || false;
        
        // DIAGNÓSTICO DETALLADO
        console.log('=== DIAGNÓSTICO KANBAN ===');
        console.log('Checkbox element:', hideClosedCheckbox);
        console.log('Checkbox checked:', hideClosedCheckbox?.checked);
        console.log('hideClosed:', hideClosed);
        console.log('include_closed que se enviará:', !hideClosed);
        
        // Build query params
        const params = new URLSearchParams();
        if (searchValue) params.append('q', searchValue);
        params.append('include_closed', !hideClosed);
        
        const url = `/kanban?${params.toString()}`;
        console.log('URL completa:', url);
        
        // Fetch kanban data
        const response = await fetch(url, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('[KANBAN] Data loaded:', data.columns.length, 'columns');
        console.log('[KANBAN] Stages recibidos:', data.columns.map(c => c.stage ? c.stage.key : 'NO_STAGE').join(', '));
        console.log('[KANBAN] Total oportunidades:', data.columns.reduce((sum, c) => sum + c.opportunities.length, 0));
        
        // Verificar si hay columnas won/lost
        const hasWon = data.columns.some(c => c.stage && c.stage.outcome === 'won');
        const hasLost = data.columns.some(c => c.stage && c.stage.outcome === 'lost');
        console.log('[KANBAN] Tiene columna won:', hasWon);
        console.log('[KANBAN] Tiene columna lost:', hasLost);
        console.log('=== FIN DIAGNÓSTICO ===');
        
        // Render kanban
        renderKanban(data);
        
    } catch (error) {
        console.error('[KANBAN] Error loading data:', error);
        showToast('Error al cargar Kanban: ' + error.message, 'danger');
    }
}

function renderKanban(data) {
    console.log('[KANBAN] Rendering kanban...');
    console.log('[KANBAN] Columnas a renderizar:', data.columns.map(c => {
        if (!c.stage) return `NO_STAGE (${c.opportunities ? c.opportunities.length : 0} opps)`;
        return `${c.stage.key} (${c.opportunities.length} opps)`;
    }).join(', '));
    
    const kanbanBoard = document.getElementById('kanban-board');
    if (!kanbanBoard) {
        console.error('[KANBAN] kanban-board element not found');
        return;
    }
    
    // Clear board
    kanbanBoard.innerHTML = '';
    
    // Render each column
    data.columns.forEach(column => {
        if (!column.stage) {
            console.error('[KANBAN] Columna sin stage:', column);
            return;
        }
        
        console.log(`[KANBAN] Renderizando columna: ${column.stage.key} (outcome: ${column.stage.outcome})`);
        const columnEl = createKanbanColumn(column);
        kanbanBoard.appendChild(columnEl);
        console.log(`[KANBAN] Columna añadida al DOM: ${column.stage.key}`);
    });
    
    console.log('[KANBAN] Rendered', data.columns.length, 'columns');
    
    // Verificar que las columnas están en el DOM
    const columnsInDom = kanbanBoard.querySelectorAll('.kanban-column');
    console.log('[KANBAN] Columnas en DOM después de renderizar:', columnsInDom.length);
    columnsInDom.forEach((col, i) => {
        const rect = col.getBoundingClientRect();
        console.log(`[KANBAN] Columna ${i}: width=${rect.width}px, height=${rect.height}px, visible=${rect.width > 0 && rect.height > 0}`);
    });
}

function createKanbanColumn(column) {
    const col = document.createElement('div');
    col.className = 'kanban-column';
    col.dataset.stageId = column.stage_id || 'unknown';
    
    // Add 'closed' class for won/lost columns
    if (column.stage && (column.stage.outcome === 'won' || column.stage.outcome === 'lost')) {
        col.classList.add('closed');
        console.log(`[KANBAN] Añadida clase 'closed' a columna ${column.stage.key}`);
    }
    
    // Column header
    const header = document.createElement('div');
    header.className = 'kanban-column-header';
    const stageName = column.stage_name || (column.stage ? column.stage.name : null) || column.stage_key || 'Sin nombre';
    header.innerHTML = `
        <h5>${stageName}</h5>
        <span class="badge bg-secondary">${column.opportunities ? column.opportunities.length : 0}</span>
    `;
    col.appendChild(header);
    
    // Column body (cards container)
    const body = document.createElement('div');
    body.className = 'kanban-column-body';
    
    // Render cards
    if (column.opportunities && column.opportunities.length > 0) {
        column.opportunities.forEach(opp => {
            const card = createKanbanCard(opp);
            body.appendChild(card);
        });
    } else {
        // Empty state
        const empty = document.createElement('div');
        empty.className = 'kanban-empty';
        empty.textContent = 'Sin oportunidades';
        body.appendChild(empty);
    }
    
    col.appendChild(body);
    
    const stageKey = column.stage ? column.stage.key : 'NO_STAGE';
    console.log(`[KANBAN] Columna creada: ${stageKey}, width: ${col.style.width || 'auto'}, display: ${col.style.display || 'default'}`);
    
    return col;
}

function createKanbanCard(opp) {
    const card = document.createElement('div');
    card.className = 'kanban-card';
    card.dataset.opportunityId = opp.opportunity_id;
    
    // Card content
    card.innerHTML = `
        <div class="kanban-card-header">
            <strong>${opp.account_name}</strong>
        </div>
        <div class="kanban-card-body">
            ${opp.opportunity_name ? `<div class="text-muted small">${opp.opportunity_name}</div>` : ''}
            <div class="kanban-card-value">
                <span class="badge bg-primary">${formatCurrency(opp.expected_value_eur)}</span>
                ${opp.probability ? `<span class="badge bg-info">${Math.round(opp.probability * 100)}%</span>` : ''}
            </div>
            ${opp.next_task ? `
                <div class="kanban-card-task ${opp.next_task.is_overdue ? 'text-danger' : ''}">
                    <i class="bi bi-check2-square"></i>
                    ${opp.next_task.title}
                    ${opp.next_task.due_date ? `<span class="small"> - ${opp.next_task.due_date}</span>` : ''}
                </div>
            ` : ''}
        </div>
        ${opp.badges ? `
            <div class="kanban-card-footer">
                ${opp.badges.lead_source ? `<span class="badge bg-secondary small">${opp.badges.lead_source}</span>` : ''}
                ${opp.badges.region ? `<span class="badge bg-secondary small">${opp.badges.region}</span>` : ''}
            </div>
        ` : ''}
    `;
    
    // Click handler
    card.addEventListener('click', () => {
        showOpportunityDetails(opp.opportunity_id);
    });
    
    return card;
}

function showOpportunityDetails(opportunityId) {
    console.log('[KANBAN] Show opportunity details:', opportunityId);
    // Open detail modal
    if (typeof showOpportunityDetail === 'function') {
        showOpportunityDetail(opportunityId);
    } else {
        showToast('Error: Modal de detalle no disponible', 'error');
    }
}

// Export functions to global scope
window.loadKanbanData = loadKanbanData;

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Load kanban when tab is shown
    const kanbanTab = document.getElementById('kanban-tab');
    if (kanbanTab) {
        kanbanTab.addEventListener('shown.bs.tab', function() {
            console.log('[KANBAN] Tab shown, loading data...');
            loadKanbanData();
        });
    }
    
    // Search filter
    const searchInput = document.getElementById('kanban-search');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                loadKanbanData();
            }, 500); // Debounce 500ms
        });
    }
    
    // Hide closed checkbox
    const hideClosedCheckbox = document.getElementById('kanban-hide-closed');
    if (hideClosedCheckbox) {
        console.log('[KANBAN] Event listener registrado en checkbox "Ocultar cerradas"');
        hideClosedCheckbox.addEventListener('change', function() {
            console.log('[KANBAN] Checkbox cambiado! Nuevo estado:', hideClosedCheckbox.checked);
            loadKanbanData();
        });
    } else {
        console.error('[KANBAN] NO se encontró el checkbox "kanban-hide-closed"!');
    }
});

console.log('[KANBAN] Module loaded, loadKanbanData registered');
