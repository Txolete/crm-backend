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
    
    // Show Users nav link only for admin
    if (user.role === 'admin') {
        const navUsers = document.getElementById('nav-users');
        if (navUsers) {
            navUsers.style.display = 'block';
        }
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
    const response = await fetch(`/dashboard/targets?year=${year}`, {
        credentials: 'include'
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
}

async function updateTargets(year, payload) {
    const response = await fetch(`/dashboard/targets?year=${year}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload)
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
}

async function loadConfigData() {
    // Each section has its own try/catch so one failure never blocks the rest.

    // Lead sources
    try {
        const resp = await fetch('/config/lead-sources', { credentials: 'include' });
        if (resp.ok) {
            const data = await resp.json();
            const select = document.getElementById('filter-lead-source');
            if (select) {
                (Array.isArray(data) ? data : data.lead_sources || []).forEach(ls => {
                    select.innerHTML += `<option value="${ls.id}">${ls.name}</option>`;
                });
            }
        } else {
            console.warn('[loadConfigData] lead-sources status:', resp.status);
        }
    } catch (e) { console.warn('[loadConfigData] lead-sources error:', e); }

    // Customer types
    try {
        const resp = await fetch('/config/customer-types', { credentials: 'include' });
        if (resp.ok) {
            const data = await resp.json();
            const select = document.getElementById('filter-customer-type');
            if (select) {
                (Array.isArray(data) ? data : data.customer_types || []).forEach(ct => {
                    select.innerHTML += `<option value="${ct.id}">${ct.name}</option>`;
                });
            }
        } else {
            console.warn('[loadConfigData] customer-types status:', resp.status);
        }
    } catch (e) { console.warn('[loadConfigData] customer-types error:', e); }

    // Regions
    try {
        const resp = await fetch('/config/regions', { credentials: 'include' });
        if (resp.ok) {
            const data = await resp.json();
            const select = document.getElementById('filter-region');
            if (select) {
                (Array.isArray(data) ? data : data.regions || []).forEach(r => {
                    select.innerHTML += `<option value="${r.id}">${r.name}</option>`;
                });
            }
        } else {
            console.warn('[loadConfigData] regions status:', resp.status);
        }
    } catch (e) { console.warn('[loadConfigData] regions error:', e); }

    // Users (admin/sales only — silently skipped for other roles)
    try {
        const resp = await fetch('/admin/users', { credentials: 'include' });
        if (resp.ok) {
            const data = await resp.json();
            const select = document.getElementById('filter-owner');
            if (select) {
                (data.users || []).forEach(u => {
                    select.innerHTML += `<option value="${u.id}">${u.name}</option>`;
                });
            }
        } else {
            console.warn('[loadConfigData] users status:', resp.status);
        }
    } catch (e) { console.warn('[loadConfigData] users error:', e); }
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
                    label: 'Cerrado Acumulado',
                    data: series.closed_cum,
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.3,
                    fill: true,
                    type: 'line'
                },
                {
                    label: 'Cerrado Mensual',
                    data: series.closed_monthly || [],
                    backgroundColor: 'rgba(40, 167, 69, 0.6)',
                    borderColor: '#28a745',
                    borderWidth: 1,
                    type: 'bar',
                    yAxisID: 'y'
                },
                {
                    label: 'Target Acumulado',
                    data: series.target_closed_cum,
                    borderColor: '#6c757d',
                    borderDash: [5, 5],
                    tension: 0.3,
                    fill: false,
                    type: 'line'
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

    // Load tasks (and admin user filter) when tasks tab is shown
    const tasksTab = document.getElementById('tasks-tab');
    if (tasksTab) {
        let tasksFilterInitialized = false;
        tasksTab.addEventListener('shown.bs.tab', async function () {
            if (!tasksFilterInitialized) {
                await initTasksUserFilter();
                tasksFilterInitialized = true;
            }
            loadMyTasks();
        });

        // Also init if tasks tab is already active on page load (e.g. via URL hash)
        if (tasksTab.classList.contains('active')) {
            initTasksUserFilter().then(() => loadMyTasks());
        }
    }

    // Ensure activityModal cleanup on close (prevents stuck backdrop)
    const activityModal = document.getElementById('activityModal');
    if (activityModal) {
        activityModal.addEventListener('hidden.bs.modal', function () {
            setTimeout(forceModalCleanup, 300);
        });
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
    console.log('[DASHBOARD] === DOMContentLoaded START ===');
    console.log('[DASHBOARD] Current URL:', window.location.href);
    console.log('[DASHBOARD] Current hash:', window.location.hash);
    
    detectUser();
    await loadConfigData();
    await loadDashboard();
    bindEvents();
    
    console.log('[DASHBOARD] === DOMContentLoaded COMPLETE ===');
    
    // Method 1: Immediate check
    activateKanbanIfNeeded('DOMContentLoaded-immediate');
    
    // Method 2: After 100ms
    setTimeout(() => {
        activateKanbanIfNeeded('DOMContentLoaded-100ms');
    }, 100);
    
    // Method 3: After 300ms
    setTimeout(() => {
        activateKanbanIfNeeded('DOMContentLoaded-300ms');
    }, 300);
    
    // Method 4: After 500ms (last resort)
    setTimeout(() => {
        activateKanbanIfNeeded('DOMContentLoaded-500ms');
    }, 500);
});

// Helper function to activate Kanban tab
function activateKanbanIfNeeded(source) {
    const hash = window.location.hash;
    console.log(`[DASHBOARD] activateKanbanIfNeeded called from: ${source}, hash: "${hash}"`);
    
    // Parse hash to get tab and parameters
    // Format: #kanban or #kanban&account=xxx or #kanban&opp=xxx
    const parts = hash.split('&');
    const tab = parts[0];
    const accountParam = parts.find(p => p.startsWith('account='));
    const oppParam = parts.find(p => p.startsWith('opp='));
    const accountId = accountParam ? accountParam.split('=')[1] : null;
    const oppId = oppParam ? oppParam.split('=')[1] : null;
    
    if (tab !== '#kanban') {
        console.log(`[DASHBOARD] Hash is not #kanban, skipping (source: ${source})`);
        return;
    }
    
    console.log(`[DASHBOARD] Attempting to activate Kanban tab (source: ${source})`, {
        tab,
        accountId: accountId || 'none',
        oppId: oppId || 'none'
    });
    
    // Find the tab elements
    const kanbanTab = document.getElementById('kanban-tab');
    const kanbanPane = document.getElementById('kanban-pane');
    const overviewTab = document.getElementById('overview-tab');
    const overviewPane = document.getElementById('overview-pane');
    
    console.log('[DASHBOARD] Elements found:', {
        kanbanTab: !!kanbanTab,
        kanbanPane: !!kanbanPane,
        overviewTab: !!overviewTab,
        overviewPane: !!overviewPane
    });
    
    if (!kanbanTab) {
        console.error('[DASHBOARD] Kanban tab element not found!');
        return;
    }
    
    // Check current state
    console.log('[DASHBOARD] Current tab states:', {
        kanbanTabActive: kanbanTab.classList.contains('active'),
        kanbanPaneActive: kanbanPane?.classList.contains('active'),
        overviewTabActive: overviewTab?.classList.contains('active'),
        overviewPaneActive: overviewPane?.classList.contains('active')
    });
    
    // If Kanban is already active, skip activation but still highlight if needed
    if (kanbanTab.classList.contains('active')) {
        console.log('[DASHBOARD] Kanban tab is already active');
        if (accountId) {
            console.log('[DASHBOARD] Attempting to highlight account opportunities:', accountId);
            setTimeout(() => highlightAccountOpportunities(accountId), 500);
        } else if (oppId) {
            console.log('[DASHBOARD] Attempting to highlight opportunity:', oppId);
            setTimeout(() => highlightOpportunity(oppId), 500);
        }
        return;
    }
    
    // Try multiple methods to activate
    console.log('[DASHBOARD] Trying activation methods...');
    
    // Method A: Direct click
    try {
        console.log('[DASHBOARD] Method A: Direct click()');
        kanbanTab.click();
        console.log('[DASHBOARD] ✅ Method A: Click executed');
    } catch (error) {
        console.error('[DASHBOARD] ❌ Method A failed:', error);
    }
    
    // Method B: Bootstrap Tab API
    try {
        console.log('[DASHBOARD] Method B: Bootstrap Tab API');
        const tab = new bootstrap.Tab(kanbanTab);
        tab.show();
        console.log('[DASHBOARD] ✅ Method B: Bootstrap Tab.show() executed');
    } catch (error) {
        console.error('[DASHBOARD] ❌ Method B failed:', error);
    }
    
    // Method C: Manual class manipulation
    try {
        console.log('[DASHBOARD] Method C: Manual classes');
        
        // Remove active from overview
        if (overviewTab) {
            overviewTab.classList.remove('active');
            overviewTab.setAttribute('aria-selected', 'false');
        }
        if (overviewPane) {
            overviewPane.classList.remove('show', 'active');
        }
        
        // Add active to kanban
        kanbanTab.classList.add('active');
        kanbanTab.setAttribute('aria-selected', 'true');
        if (kanbanPane) {
            kanbanPane.classList.add('show', 'active');
        }
        
        console.log('[DASHBOARD] ✅ Method C: Manual classes applied');
    } catch (error) {
        console.error('[DASHBOARD] ❌ Method C failed:', error);
    }
    
    // Verify final state
    setTimeout(() => {
        console.log('[DASHBOARD] Final verification after activation:', {
            kanbanTabActive: kanbanTab.classList.contains('active'),
            kanbanPaneActive: kanbanPane?.classList.contains('active'),
            overviewTabActive: overviewTab?.classList.contains('active'),
            overviewPaneActive: overviewPane?.classList.contains('active')
        });
        
        // Highlight opportunities if specified
        if (accountId) {
            console.log('[DASHBOARD] Tab activated, now highlighting account opportunities:', accountId);
            // Wait a bit more for Kanban to fully render
            setTimeout(() => highlightAccountOpportunities(accountId), 1000);
        } else if (oppId) {
            console.log('[DASHBOARD] Tab activated, now highlighting opportunity:', oppId);
            setTimeout(() => highlightOpportunity(oppId), 1000);
        }
    }, 50);
}

// Helper function to highlight all opportunities from a specific account
function highlightAccountOpportunities(accountId) {
    console.log('[DASHBOARD] highlightAccountOpportunities called for account:', accountId);
    
    // Find all cards belonging to this account
    const cardSelector = `[data-account-id="${accountId}"]`;
    const cards = document.querySelectorAll(cardSelector);
    
    if (cards.length === 0) {
        console.warn('[DASHBOARD] No opportunity cards found for account:', accountId);
        console.log('[DASHBOARD] Searched for selector:', cardSelector);
        return;
    }
    
    console.log(`[DASHBOARD] Found ${cards.length} opportunity cards for account, highlighting...`);
    
    // Scroll to first card
    cards[0].scrollIntoView({
        behavior: 'smooth',
        block: 'center'
    });
    
    // Apply highlight to all cards
    cards.forEach((card, index) => {
        // Stagger the animation slightly
        setTimeout(() => {
            card.style.transition = 'all 0.3s ease';
            card.style.boxShadow = '0 0 20px rgba(0, 153, 51, 0.8)';
            card.style.transform = 'scale(1.03)';
            card.style.zIndex = '1000';
            
            // Flash effect
            let flashCount = 0;
            const flashInterval = setInterval(() => {
                if (flashCount % 2 === 0) {
                    card.style.boxShadow = '0 0 30px rgba(0, 153, 51, 0.9)';
                    card.style.backgroundColor = '#e8f5e9';
                } else {
                    card.style.boxShadow = '0 0 20px rgba(0, 153, 51, 0.8)';
                    card.style.backgroundColor = '';
                }
                flashCount++;
                
                if (flashCount >= 6) {
                    clearInterval(flashInterval);
                    // Remove highlight after 3 seconds
                    setTimeout(() => {
                        card.style.boxShadow = '';
                        card.style.transform = '';
                        card.style.backgroundColor = '';
                        card.style.zIndex = '';
                    }, 3000);
                }
            }, 300);
        }, index * 100); // Stagger by 100ms per card
    });
    
    console.log('[DASHBOARD] Highlight applied to all cards');
}

// Helper function to highlight a specific opportunity card in Kanban
function highlightOpportunity(oppId) {
    console.log('[DASHBOARD] highlightOpportunity called for:', oppId);
    
    // Find the card in the Kanban
    const cardSelector = `[data-opportunity-id="${oppId}"]`;
    const card = document.querySelector(cardSelector);
    
    if (!card) {
        console.warn('[DASHBOARD] Opportunity card not found in Kanban:', oppId);
        console.log('[DASHBOARD] Searched for selector:', cardSelector);
        return;
    }
    
    console.log('[DASHBOARD] Found opportunity card, highlighting...');
    
    // Scroll to card
    card.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
    });
    
    // Add highlight effect
    card.style.transition = 'all 0.3s ease';
    card.style.boxShadow = '0 0 20px rgba(0, 102, 204, 0.8)';
    card.style.transform = 'scale(1.05)';
    card.style.zIndex = '1000';
    
    // Flash effect
    let flashCount = 0;
    const flashInterval = setInterval(() => {
        if (flashCount % 2 === 0) {
            card.style.boxShadow = '0 0 30px rgba(0, 102, 204, 0.9)';
            card.style.backgroundColor = '#e3f2fd';
        } else {
            card.style.boxShadow = '0 0 20px rgba(0, 102, 204, 0.8)';
            card.style.backgroundColor = '';
        }
        flashCount++;
        
        if (flashCount >= 6) {
            clearInterval(flashInterval);
            // Remove highlight after 3 seconds
            setTimeout(() => {
                card.style.boxShadow = '';
                card.style.transform = '';
                card.style.backgroundColor = '';
                card.style.zIndex = '';
            }, 3000);
        }
    }, 300);
    
    console.log('[DASHBOARD] Highlight applied successfully');
}

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
// DESACTIVADO - Ahora se maneja en tasks.js (FASE 2 PASO 3)

/*
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
*/

/*
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
*/

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
        
        // Load quick account form data when collapse is shown
        document.getElementById('quickAccountForm').addEventListener('shown.bs.collapse', loadQuickAccountFormData);
        
    } catch (error) {
        console.error('Error in showNewOpportunityModal:', error);
        alert('❌ Error: ' + error.message + '\n\nAbre F12 → Console para más detalles.');
    }
}

// Load data for quick account form (regions and customer types)
window.loadQuickAccountFormData = async function() {
    try {
        // Load regions
        const regionsResponse = await fetch('/config/regions', { credentials: 'include' });
        if (regionsResponse.ok) {
            const regions = await regionsResponse.json();
            const regionSelect = document.getElementById('quick-account-region');
            regionSelect.innerHTML = '<option value="">Seleccionar...</option>';
            regions.filter(r => r.is_active).forEach(region => {
                const option = document.createElement('option');
                option.value = region.id;
                option.textContent = region.name;
                regionSelect.appendChild(option);
            });
        }
        
        // Load customer types
        const typesResponse = await fetch('/config/customer-types', { credentials: 'include' });
        if (typesResponse.ok) {
            const types = await typesResponse.json();
            const typeSelect = document.getElementById('quick-account-type');
            typeSelect.innerHTML = '<option value="">Seleccionar...</option>';
            types.filter(t => t.is_active).forEach(type => {
                const option = document.createElement('option');
                option.value = type.id;
                option.textContent = type.name;
                typeSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading quick account form data:', error);
    }
}

// Save quick account and update the accounts select
window.saveQuickAccount = async function() {
    try {
        const name = document.getElementById('quick-account-name').value.trim();
        
        if (!name) {
            alert('⚠️ El nombre de la cuenta es obligatorio');
            document.getElementById('quick-account-name').focus();
            return;
        }
        
        const regionId = document.getElementById('quick-account-region').value || null;
        const customerTypeId = document.getElementById('quick-account-type').value || null;
        
        const payload = {
            name: name,
            region_id: regionId,
            customer_type_id: customerTypeId,
            status: 'active'
        };
        
        const response = await fetch('/accounts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error('Error al crear cuenta');
        }
        
        const newAccount = await response.json();
        
        // Add new account to the select and select it
        const accountSelect = document.getElementById('new-opp-account');
        const option = document.createElement('option');
        option.value = newAccount.id;
        option.textContent = newAccount.name;
        option.selected = true;
        accountSelect.appendChild(option);
        
        // Clear and close the quick form
        document.getElementById('quick-account-name').value = '';
        document.getElementById('quick-account-region').value = '';
        document.getElementById('quick-account-type').value = '';
        
        const collapseElement = document.getElementById('quickAccountForm');
        const bsCollapse = bootstrap.Collapse.getInstance(collapseElement);
        if (bsCollapse) {
            bsCollapse.hide();
        } else {
            new bootstrap.Collapse(collapseElement, { toggle: true });
        }
        
        // Show success message
        const btn = document.getElementById('btn-save-quick-account');
        const originalHTML = btn.innerHTML;
        btn.innerHTML = '<i class="bi bi-check-circle-fill"></i> ¡Creada!';
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-success');
        btn.disabled = true;
        
        setTimeout(() => {
            btn.innerHTML = originalHTML;
            btn.classList.remove('btn-success');
            btn.classList.add('btn-primary');
            btn.disabled = false;
        }, 2000);
        
        console.log('Quick account created:', newAccount);
        
    } catch (error) {
        console.error('Error saving quick account:', error);
        alert('❌ Error al crear cuenta: ' + error.message);
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
    document.getElementById('btn-mark-won').style.display = 'none';
    document.getElementById('btn-mark-lost').style.display = 'none';
    
    modal.show();
    
    try {
        // Load opportunity data
        await loadOpportunityDetail(opportunityId);
        
        // Load tasks (NUEVO - PASO 4)
        await loadOpportunityTasks(opportunityId);

        // Load activities
        await loadOpportunityActivities(opportunityId);

        // Load AI section (Sprint 4E)
        if (currentOpportunityData) await loadAISection(currentOpportunityData);
        
        // Hide loading, show content
        document.getElementById('oppDetailLoading').style.display = 'none';
        document.getElementById('oppDetailContent').style.display = 'block';

        // B5/B6: mostrar botones won/lost ahora que todo ha cargado
        const isOpen = currentOpportunityData &&
            (currentOpportunityData.close_outcome === 'open' || !currentOpportunityData.close_outcome);
        document.getElementById('btn-mark-won').style.display = isOpen ? 'inline-block' : 'none';
        document.getElementById('btn-mark-lost').style.display = isOpen ? 'inline-block' : 'none';

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
    document.getElementById('detail-account').innerHTML =
        `<a href="/accounts/page?q=${encodeURIComponent(opp.account_name || '')}" target="_blank">${opp.account_name || '-'} <i class="bi bi-box-arrow-up-right" style="font-size:0.75rem"></i></a>`;
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
    console.log('[TIMELINE] Loading for opportunity:', opportunityId);
    
    const loadingDiv = document.getElementById('detail-activities-loading');
    const contentDiv = document.getElementById('detail-activities-content');
    const emptyDiv = document.getElementById('detail-activities-empty');
    
    loadingDiv.style.display = 'block';
    contentDiv.style.display = 'none';
    emptyDiv.style.display = 'none';
    
    try {
        const response = await fetch(`/activities/opportunity/${opportunityId}`);
        if (!response.ok) {
            throw new Error('Error loading timeline');
        }
        
        const data = await response.json();
        const activities = data.activities || [];
        
        console.log('[TIMELINE] Activities loaded:', activities.length);
        
        // Update counter
        document.getElementById('timeline-count').textContent = activities.length;
        
        if (activities.length === 0) {
            loadingDiv.style.display = 'none';
            emptyDiv.style.display = 'block';
        } else {
            renderTimeline(activities);
            loadingDiv.style.display = 'none';
            contentDiv.style.display = 'block';
        }
        
    } catch (error) {
        console.error('[TIMELINE] Error:', error);
        loadingDiv.innerHTML = '<div class="alert alert-danger">Error al cargar actividades</div>';
    }
}

/**
 * Renderizar timeline
 */
function renderTimeline(activities) {
    const contentDiv = document.getElementById('detail-activities-content');
    
    let html = '<div class="timeline">';
    
    activities.forEach((activity, index) => {
        const icon = getActivityIcon(activity.type);
        const color = getActivityColor(activity.type);
        const isLast = index === activities.length - 1;
        const canEdit = canEditActivity(activity);
        
        html += `
            <div class="timeline-item ${isLast ? 'timeline-item-last' : ''}">
                <div class="timeline-marker ${color}">
                    ${icon}
                </div>
                <div class="timeline-content">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <div class="fw-bold">${escapeHtml(activity.summary)}</div>
                            <small class="text-muted">
                                <i class="bi bi-clock"></i> ${formatActivityDateTime(activity.occurred_at)}
                                ${activity.created_by_name ? `<span class="ms-2"><i class="bi bi-person"></i> ${escapeHtml(activity.created_by_name)}</span>` : ''}
                            </small>
                        </div>
                        ${canEdit ? `
                        <div class="btn-group btn-group-sm ms-2">
                            <button class="btn btn-outline-secondary btn-sm" onclick="editActivity('${activity.id}')" title="Editar">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-outline-danger btn-sm" onclick="deleteActivity('${activity.id}')" title="Eliminar">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    contentDiv.innerHTML = html;
}

/**
 * Get icon for activity type
 */
function getActivityIcon(type) {
    const icons = {
        'note': '📝',
        'call': '📞',
        'meeting': '🤝',
        'email': '📧',
        'status_change': '🔄',
        'task_created': '➕',
        'task_completed': '✅',
        'won': '🎉',
        'lost': '❌'
    };
    return icons[type] || '•';
}

/**
 * Get color for activity type
 */
function getActivityColor(type) {
    const colors = {
        'note': 'bg-secondary',
        'call': 'bg-primary',
        'meeting': 'bg-info',
        'email': 'bg-warning',
        'status_change': 'bg-info',
        'task_created': 'bg-success',
        'task_completed': 'bg-success',
        'won': 'bg-success',
        'lost': 'bg-danger'
    };
    return colors[type] || 'bg-secondary';
}

/**
 * Check if user can edit activity
 */
function canEditActivity(activity) {
    // Only manual activities (note, call, meeting, email) can be edited
    const manualTypes = ['note', 'call', 'meeting', 'email'];
    return manualTypes.includes(activity.type);
}

/**
 * Format datetime for timeline
 */
function formatActivityDateTime(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    // Relative time for recent activities
    if (diffMins < 1) {
        return 'Hace un momento';
    } else if (diffMins < 60) {
        return `Hace ${diffMins} min`;
    } else if (diffHours < 24) {
        return `Hace ${diffHours}h`;
    } else if (diffDays === 1) {
        return 'Ayer ' + date.toLocaleTimeString('es-ES', {hour: '2-digit', minute: '2-digit'});
    } else if (diffDays < 7) {
        return `Hace ${diffDays} días`;
    }
    
    // Absolute date for older activities
    return date.toLocaleString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Show modal to create activity
 */
function showCreateActivityModal() {
    if (!currentOpportunityId) {
        showToast('Error: No hay oportunidad seleccionada', 'danger');
        return;
    }
    
    // Reset form
    document.getElementById('activityForm').reset();
    document.getElementById('activity-id').value = '';
    document.getElementById('activity-modal-title').textContent = 'Nueva Actividad';
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('activityModal'));
    modal.show();
}

/**
 * Save activity
 */
async function saveActivity() {
    const activityId = document.getElementById('activity-id').value;
    const type = document.getElementById('activity-type').value;
    const summary = document.getElementById('activity-summary').value;
    const occurred = document.getElementById('activity-occurred').value;
    
    if (!type || !summary) {
        showToast('Por favor completa todos los campos requeridos', 'warning');
        return;
    }
    
    try {
        const payload = {
            opportunity_id: currentOpportunityId,
            type: type,
            summary: summary
        };
        
        if (occurred) {
            payload.occurred_at = new Date(occurred).toISOString();
        }
        
        let response;
        if (activityId) {
            // Update
            response = await fetch(`/activities/${activityId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    summary: summary, 
                    occurred_at: payload.occurred_at 
                })
            });
        } else {
            // Create
            response = await fetch('/activities', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al guardar actividad');
        }
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('activityModal'));
        modal.hide();
        
        // Reload timeline
        await loadOpportunityActivities(currentOpportunityId);
        
        showToast(activityId ? 'Actividad actualizada' : 'Actividad creada', 'success');
        
    } catch (error) {
        console.error('Error saving activity:', error);
        showToast(error.message || 'Error al guardar actividad', 'danger');
    }
}

/**
 * Edit activity
 */
async function editActivity(activityId) {
    try {
        // Load activity data (from current timeline)
        const response = await fetch(`/activities/opportunity/${currentOpportunityId}`);
        if (!response.ok) {
            throw new Error('Error loading activity');
        }
        
        const data = await response.json();
        const activity = data.activities.find(a => a.id === activityId);
        
        if (!activity) {
            throw new Error('Actividad no encontrada');
        }
        
        // Fill form
        document.getElementById('activity-id').value = activity.id;
        document.getElementById('activity-type').value = activity.type;
        document.getElementById('activity-summary').value = activity.summary;
        
        // Convert ISO to datetime-local format
        if (activity.occurred_at) {
            const date = new Date(activity.occurred_at);
            const localDateTime = date.toISOString().slice(0, 16);
            document.getElementById('activity-occurred').value = localDateTime;
        }
        
        document.getElementById('activity-modal-title').textContent = 'Editar Actividad';
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('activityModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error loading activity:', error);
        showToast(error.message || 'Error al cargar actividad', 'danger');
    }
}

/**
 * Delete activity
 */
async function deleteActivity(activityId) {
    if (!confirm('¿Estás seguro de eliminar esta actividad?')) {
        return;
    }
    
    try {
        const response = await fetch(`/activities/${activityId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Error al eliminar actividad');
        }
        
        // Reload timeline
        await loadOpportunityActivities(currentOpportunityId);
        
        showToast('Actividad eliminada', 'success');
        
    } catch (error) {
        console.error('Error deleting activity:', error);
        showToast('Error al eliminar actividad', 'danger');
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
        document.getElementById('btn-mark-won').style.display = 'none';
        document.getElementById('btn-mark-lost').style.display = 'none';
        
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

    // Restaurar botones won/lost si la opp está abierta
    const isOpen = currentOpportunityData &&
        (currentOpportunityData.close_outcome === 'open' || !currentOpportunityData.close_outcome);
    document.getElementById('btn-mark-won').style.display = isOpen ? 'inline-block' : 'none';
    document.getElementById('btn-mark-lost').style.display = isOpen ? 'inline-block' : 'none';
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
        console.error('[EDIT] Error updating opportunity:', error);
        showToast('❌ Error al guardar: ' + error.message, 'danger');
    }
}

/**
 * Archive opportunity (soft delete)
 */
window.archiveOpportunity = async function() {
    console.log('[ARCHIVE] Archiving opportunity');
    
    if (!currentOpportunityId || !currentOpportunityData) {
        console.error('[ARCHIVE] No opportunity data');
        return;
    }
    
    const accountName = currentOpportunityData.account_name || 'esta oportunidad';
    
    // Confirm action
    if (!confirm(`¿Estás seguro de archivar "${accountName}"?\n\nLa oportunidad no se eliminará permanentemente, solo se marcará como archivada y no aparecerá en el Kanban ni en los reportes.`)) {
        return;
    }
    
    try {
        // Send PUT request with status=archived
        const response = await fetch(`/opportunities/${currentOpportunityId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                status: 'archived'
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al archivar oportunidad');
        }
        
        console.log('[ARCHIVE] Opportunity archived successfully');
        
        // Reload dashboard and kanban FIRST (before closing modal)
        console.log('[ARCHIVE] Reloading dashboard and kanban...');
        
        // Reload dashboard (KPIs and charts)
        await loadDashboard();
        console.log('[ARCHIVE] Dashboard reloaded');
        
        // Reload kanban if function exists
        if (typeof loadKanbanData === 'function') {
            await loadKanbanData();
            console.log('[ARCHIVE] Kanban reloaded');
        }
        
        // NOW close modal
        const modalElement = document.getElementById('oppDetailModal');
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) {
            modal.hide();
        }
        
        // Show success message AFTER everything
        showToast(`✅ "${accountName}" archivada correctamente`, 'success');
        
    } catch (error) {
        console.error('[ARCHIVE] Error archiving opportunity:', error);
        showToast('❌ Error al archivar: ' + error.message, 'danger');
    }
}

// ========================================
// KANBAN FUNCTIONALITY
// ========================================

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
    
    // Save Quick Account button
    const btnSaveQuickAccount = document.getElementById('btn-save-quick-account');
    if (btnSaveQuickAccount) {
        btnSaveQuickAccount.addEventListener('click', saveQuickAccount);
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
    
    // Archive Opportunity button
    const btnArchiveOpp = document.getElementById('btn-archive-opp');
    if (btnArchiveOpp) {
        btnArchiveOpp.addEventListener('click', archiveOpportunity);
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
        console.log('[KANBAN] Stages recibidos:', data.columns.map(c => c.stage_key || 'NO_KEY').join(', '));
        console.log('[KANBAN] Total oportunidades:', data.columns.reduce((sum, c) => sum + c.opportunities.length, 0));
        
        // Create stages map for outcome lookup
        const stagesMap = {};
        if (data.stages) {
            data.stages.forEach(stage => {
                stagesMap[stage.id] = stage;
            });
        }
        
        // Verificar si hay columnas won/lost
        const hasWon = data.columns.some(c => {
            const stage = stagesMap[c.stage_id];
            return stage && stage.outcome === 'won';
        });
        const hasLost = data.columns.some(c => {
            const stage = stagesMap[c.stage_id];
            return stage && stage.outcome === 'lost';
        });
        console.log('[KANBAN] Tiene columna won:', hasWon);
        console.log('[KANBAN] Tiene columna lost:', hasLost);
        console.log('=== FIN DIAGNÓSTICO ===');
        
        // Render kanban with stages map
        renderKanban(data, stagesMap);
        
    } catch (error) {
        console.error('[KANBAN] Error loading data:', error);
        showToast('Error al cargar Kanban: ' + error.message, 'danger');
    }
}

function renderKanban(data, stagesMap = {}) {
    console.log('[KANBAN] Rendering kanban...');
    console.log('[KANBAN] Columnas a renderizar:', data.columns.map(c => {
        return `${c.stage_key || 'NO_KEY'} (${c.opportunities ? c.opportunities.length : 0} opps)`;
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
        console.log(`[KANBAN] Renderizando columna: ${column.stage_key} (stage_id: ${column.stage_id})`);
        const columnEl = createKanbanColumn(column, stagesMap);
        kanbanBoard.appendChild(columnEl);
        console.log(`[KANBAN] Columna añadida al DOM: ${column.stage_key}`);
    });
    
    console.log('[KANBAN] Rendered', data.columns.length, 'columns');
    
    // Verificar que las columnas están en el DOM
    const columnsInDom = kanbanBoard.querySelectorAll('.kanban-column');
    console.log('[KANBAN] Columnas en DOM después de renderizar:', columnsInDom.length);
    columnsInDom.forEach((col, i) => {
        const rect = col.getBoundingClientRect();
        console.log(`[KANBAN] Columna ${i}: width=${rect.width}px, height=${rect.height}px, visible=${rect.width > 0 && rect.height > 0}`);
    });
    
    // Detectar si hay scroll horizontal
    setTimeout(() => {
        const hasScroll = kanbanBoard.scrollWidth > kanbanBoard.clientWidth;
        console.log(`[KANBAN] Scroll horizontal: ${hasScroll} (scrollWidth=${kanbanBoard.scrollWidth}, clientWidth=${kanbanBoard.clientWidth})`);
        
        if (hasScroll) {
            kanbanBoard.classList.add('has-scroll');
            // Mostrar toast indicando que hay más columnas
            showScrollIndicator();
        } else {
            kanbanBoard.classList.remove('has-scroll');
        }
    }, 100);
}

function showScrollIndicator() {
    // Solo mostrar una vez por sesión
    if (sessionStorage.getItem('kanban-scroll-shown')) return;
    
    const indicator = document.createElement('div');
    indicator.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        background: #0d6efd;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 9999;
        font-size: 14px;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 10px;
        animation: slideIn 0.3s ease-out;
    `;
    indicator.innerHTML = `
        <span>→</span>
        <span>Haz scroll horizontal para ver más columnas</span>
        <button onclick="this.parentElement.remove()" style="background: none; border: none; color: white; font-size: 20px; cursor: pointer; padding: 0; margin-left: 10px;">×</button>
    `;
    
    document.body.appendChild(indicator);
    
    // Auto-ocultar después de 5 segundos
    setTimeout(() => {
        indicator.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => indicator.remove(), 300);
    }, 5000);
    
    sessionStorage.setItem('kanban-scroll-shown', 'true');
}

function createKanbanColumn(column, stagesMap = {}) {
    const col = document.createElement('div');
    col.className = 'kanban-column';
    col.dataset.stageId = column.stage_id || 'unknown';
    
    // Get stage info from stagesMap
    const stage = stagesMap[column.stage_id];
    
    // Add 'closed' class for won/lost columns
    if (stage && (stage.outcome === 'won' || stage.outcome === 'lost')) {
        col.classList.add('closed');
        console.log(`[KANBAN] Añadida clase 'closed' a columna ${column.stage_key} (outcome: ${stage.outcome})`);
    }
    
    // Column header
    const header = document.createElement('div');
    header.className = 'kanban-column-header';
    const stageName = column.stage_name || column.stage_key || 'Sin nombre';
    const stageDesc = stagesMap && stagesMap[column.stage_id] ? stagesMap[column.stage_id].description : null;
    const tooltipIcon = stageDesc
        ? `<i class="bi bi-info-circle ms-1 stage-tooltip-icon"
              style="cursor:help;font-size:0.85rem;color:#6c757d;"
              title="${stageDesc.replace(/"/g, '&quot;')}"></i>`
        : '';
    header.innerHTML = `
        <h5>${stageName}${tooltipIcon}</h5>
        <span class="badge bg-secondary">${column.opportunities ? column.opportunities.length : 0}</span>
    `;
    // Inicializar tooltip Bootstrap si hay descripción
    if (stageDesc) {
        const iconEl = header.querySelector('.stage-tooltip-icon');
        if (iconEl && typeof bootstrap !== 'undefined') {
            new bootstrap.Tooltip(iconEl, { trigger: 'hover', placement: 'bottom' });
        }
    }
    col.appendChild(header);
    
    // Column body (cards container)
    const body = document.createElement('div');
    body.className = 'kanban-column-body';
    body.dataset.stageId = column.stage_id;
    
    // Make column body a drop target
    body.addEventListener('dragover', handleDragOver);
    body.addEventListener('drop', handleDrop);
    body.addEventListener('dragenter', handleDragEnter);
    body.addEventListener('dragleave', handleDragLeave);
    
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
    
    const stageKey = column.stage_key || 'NO_KEY';
    console.log(`[KANBAN] Columna creada: ${stageKey}, width: ${col.style.width || 'auto'}, display: ${col.style.display || 'default'}`);
    
    return col;
}

function createKanbanCard(opp) {
    const card = document.createElement('div');
    card.className = 'kanban-card';
    card.dataset.opportunityId = opp.opportunity_id;
    card.dataset.accountId = opp.account_id; // Add account ID for highlighting
    
    // Make card draggable
    card.draggable = true;
    card.dataset.accountName = opp.account_name;
    card.dataset.expectedValue = opp.expected_value_eur;
    
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
    
    // Drag event listeners
    card.addEventListener('dragstart', handleDragStart);
    card.addEventListener('dragend', handleDragEnd);
    
    // Click handler (prevent when dragging)
    card.addEventListener('click', (e) => {
        if (!card.classList.contains('dragging')) {
            showOpportunityDetails(opp.opportunity_id);
        }
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

// ========================================
// DRAG & DROP FUNCTIONALITY
// ========================================

let draggedCard = null;

function handleDragStart(e) {
    draggedCard = this;
    this.classList.add('dragging');
    
    // Set data for drag
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', this.innerHTML);
    
    console.log('[DRAG] Started dragging opportunity:', this.dataset.opportunityId);
}

function handleDragEnd(e) {
    this.classList.remove('dragging');
    
    // Remove all drop-target classes
    document.querySelectorAll('.kanban-column-body').forEach(col => {
        col.classList.remove('drag-over');
    });
    
    console.log('[DRAG] Ended dragging');
}

function handleDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault(); // Allows drop
    }
    e.dataTransfer.dropEffect = 'move';
    return false;
}

function handleDragEnter(e) {
    this.classList.add('drag-over');
}

function handleDragLeave(e) {
    // Only remove if leaving the column body itself, not child elements
    if (e.target === this) {
        this.classList.remove('drag-over');
    }
}

async function handleDrop(e) {
    if (e.stopPropagation) {
        e.stopPropagation(); // Stops browser from redirecting
    }
    
    this.classList.remove('drag-over');
    
    if (!draggedCard) {
        console.error('[DRAG] No dragged card found');
        return false;
    }
    
    const opportunityId = draggedCard.dataset.opportunityId;
    const newStageId = this.dataset.stageId;
    const currentColumn = draggedCard.closest('.kanban-column-body');
    const currentStageId = currentColumn.dataset.stageId;
    
    // Check if dropped in same column
    if (newStageId === currentStageId) {
        console.log('[DRAG] Dropped in same column, no action needed');
        return false;
    }
    
    console.log('[DRAG] Drop opportunity', opportunityId, 'to stage', newStageId);
    
    // Show loading indicator on card
    draggedCard.style.opacity = '0.5';
    draggedCard.style.pointerEvents = 'none';
    
    try {
        // Update opportunity stage via API
        const response = await fetch(`/opportunities/${opportunityId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                stage_id: newStageId
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al mover oportunidad');
        }
        
        const result = await response.json();
        console.log('[DRAG] Move successful:', result);
        
        // Show success toast
        const accountName = draggedCard.dataset.accountName || 'Oportunidad';
        showToast(`${accountName} movida correctamente`, 'success');
        
        // Reload kanban to reflect changes
        await loadKanbanData();
        
        // Reload dashboard KPIs (FIX: nombre correcto de la función)
        if (typeof loadDashboard === 'function') {
            await loadDashboard();
        }
        
    } catch (error) {
        console.error('[DRAG] Error moving opportunity:', error);
        showToast('Error al mover oportunidad: ' + error.message, 'danger');
        
        // Restore card state
        draggedCard.style.opacity = '1';
        draggedCard.style.pointerEvents = 'auto';
    }
    
    return false;
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

// ============================================================================
// PASO 4 - TASKS IN OPPORTUNITY (FASE 2)
// ============================================================================

/**
 * Load tasks for the opportunity
 */
window.loadOpportunityTasks = async function(opportunityId) {
    console.log('[TASKS] Loading tasks for opportunity:', opportunityId);
    
    const loadingDiv = document.getElementById('opp-tasks-loading');
    const contentDiv = document.getElementById('opp-tasks-content');
    const emptyDiv = document.getElementById('opp-tasks-empty');
    
    loadingDiv.style.display = 'block';
    contentDiv.style.display = 'none';
    emptyDiv.style.display = 'none';
    
    try {
        const response = await fetch(`/tasks/opportunity/${opportunityId}`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Error loading tasks');
        }
        
        const data = await response.json();
        const tasks = data.tasks || [];
        
        console.log('[TASKS] Tasks loaded:', tasks.length);
        
        // Update counter
        document.getElementById('opp-tasks-count').textContent = tasks.length;
        
        if (tasks.length === 0) {
            loadingDiv.style.display = 'none';
            emptyDiv.style.display = 'block';
        } else {
            renderOpportunityTasks(tasks);
            loadingDiv.style.display = 'none';
            contentDiv.style.display = 'block';
            
            // Update "Siguiente Paso" card with next task
            updateNextStepCard(tasks);
        }
        
    } catch (error) {
        console.error('[TASKS] Error loading tasks:', error);
        loadingDiv.innerHTML = '<div class="alert alert-danger">Error al cargar tareas</div>';
    }
}

/**
 * Render tasks for opportunity
 */
function renderOpportunityTasks(tasks) {
    const contentDiv = document.getElementById('opp-tasks-content');
    
    // Sort tasks: incomplete first, by due date
    const sortedTasks = tasks.sort((a, b) => {
        // Incomplete tasks first
        if (a.status === 'completed' && b.status !== 'completed') return 1;
        if (a.status !== 'completed' && b.status === 'completed') return -1;
        
        // Then by due date
        if (!a.due_date) return 1;
        if (!b.due_date) return -1;
        return a.due_date.localeCompare(b.due_date);
    });
    
    let html = '<div class="list-group">';
    
    sortedTasks.forEach(task => {
        const isCompleted = task.status === 'completed';
        const statusIcon = isCompleted ? '✅' : '⏳';
        const priorityIcon = { high: '🔴', medium: '🟡', low: '🟢' }[task.priority] || '⚪';
        
        // Calculate due status
        let dueClass = '';
        let dueText = '';
        if (task.due_date && !isCompleted) {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const due = new Date(task.due_date + 'T00:00:00');
            const diffTime = due - today;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            if (diffDays < 0) {
                dueClass = 'text-danger';
                dueText = `Vencida hace ${Math.abs(diffDays)} días`;
            } else if (diffDays === 0) {
                dueClass = 'text-warning';
                dueText = 'Vence hoy';
            } else if (diffDays === 1) {
                dueClass = 'text-warning';
                dueText = 'Vence mañana';
            } else {
                dueText = `En ${diffDays} días`;
            }
        }
        
        // Task template badge
        const templateBadge = task.task_template_name 
            ? `<span class="badge bg-info me-1"><i class="bi bi-tag"></i> ${escapeHtml(task.task_template_name)}</span>` 
            : '';
        
        html += `
            <div class="list-group-item ${isCompleted ? 'opacity-50' : ''}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="fw-bold ${isCompleted ? 'text-decoration-line-through' : ''}">
                            ${statusIcon} ${priorityIcon} ${escapeHtml(task.title)}
                        </div>
                        <div class="small text-muted mt-1">
                            ${templateBadge}
                            ${task.assigned_to_name ? `<span class="badge bg-secondary me-1"><i class="bi bi-person"></i> ${escapeHtml(task.assigned_to_name)}</span>` : ''}
                            ${task.due_date ? `<span class="badge bg-light text-dark me-1"><i class="bi bi-calendar"></i> ${task.due_date}</span>` : ''}
                            ${dueText ? `<span class="${dueClass}">${dueText}</span>` : ''}
                        </div>
                        ${task.description ? `<div class="small mt-1">${escapeHtml(task.description).substring(0, 100)}${task.description.length > 100 ? '...' : ''}</div>` : ''}
                    </div>
                    <div class="ms-3 d-flex gap-1">
                        ${!isCompleted ? `
                        <button class="btn btn-sm btn-outline-success opp-task-complete" data-task-id="${task.id}" title="Completar">
                            <i class="bi bi-check-lg"></i>
                        </button>
                        ` : ''}
                        <button class="btn btn-sm btn-outline-primary opp-task-edit" data-task-id="${task.id}" title="Editar">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger opp-task-delete" data-task-id="${task.id}" data-task-title="${escapeHtml(task.title)}" title="Eliminar">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    contentDiv.innerHTML = html;

    // Adjuntar listeners directamente a cada botón (innerHTML reemplaza el DOM,
    // no hay acumulación de listeners en re-renders)
    contentDiv.querySelectorAll('.opp-task-complete').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            await completeTaskFromOpp(btn.dataset.taskId);
        });
    });

    contentDiv.querySelectorAll('.opp-task-edit').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            await editTaskFromOpp(btn.dataset.taskId);
        });
    });

    contentDiv.querySelectorAll('.opp-task-delete').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const title = btn.dataset.taskTitle || 'esta tarea';
            if (!confirm(`¿Eliminar "${title}"?`)) return;
            try {
                const res = await fetch(`/tasks/${btn.dataset.taskId}`, {
                    method: 'DELETE', credentials: 'include'
                });
                if (!res.ok) throw new Error('Error eliminando tarea');
                showToast('Tarea eliminada', 'success');
                await loadOpportunityTasks(currentOpportunityId);
                if (typeof loadKanbanData === 'function') loadKanbanData();
            } catch (err) {
                console.error('[TASKS] Error deleting:', err);
                showToast('Error al eliminar tarea', 'danger');
            }
        });
    });
}

/**
 * Update "Siguiente Paso" card based on next task
 */
function updateNextStepCard(tasks) {
    // Find next incomplete task
    const incompleteTasks = tasks.filter(t => t.status !== 'completed' && t.status !== 'cancelled');
    
    if (incompleteTasks.length === 0) {
        document.getElementById('detail-task-card').style.display = 'none';
        return;
    }
    
    // Sort by due date
    incompleteTasks.sort((a, b) => {
        if (!a.due_date) return 1;
        if (!b.due_date) return -1;
        return a.due_date.localeCompare(b.due_date);
    });
    
    const nextTask = incompleteTasks[0];
    const priorityIcon = { high: '🔴', medium: '🟡', low: '🟢' }[nextTask.priority] || '⚪';
    
    const taskContent = document.getElementById('detail-task-content');
    taskContent.innerHTML = `
        <div class="d-flex justify-content-between align-items-start">
            <div>
                <div class="fw-bold">${priorityIcon} ${escapeHtml(nextTask.title)}</div>
                ${nextTask.task_template_name ? `<div class="small"><span class="badge bg-info"><i class="bi bi-tag"></i> ${escapeHtml(nextTask.task_template_name)}</span></div>` : ''}
                ${nextTask.due_date ? `<div class="small text-muted mt-1"><i class="bi bi-calendar"></i> ${nextTask.due_date}</div>` : ''}
                ${nextTask.assigned_to_name ? `<div class="small text-muted"><i class="bi bi-person"></i> ${escapeHtml(nextTask.assigned_to_name)}</div>` : ''}
            </div>
            <button class="btn btn-sm btn-success" onclick="completeTaskFromOpp('${nextTask.id}')">
                <i class="bi bi-check-lg"></i> Completar
            </button>
        </div>
    `;
    
    document.getElementById('detail-task-card').style.display = 'block';
}

/**
 * Show create task modal with opportunity pre-selected
 */
window.showCreateTaskFromOpp = function() {
    if (!currentOpportunityId) {
        showToast('Error: No hay oportunidad seleccionada', 'danger');
        return;
    }
    // U2: pasar preselección directamente — se aplica tras loadTaskFormOptions
    showCreateTaskModal({
        opportunity_id: currentOpportunityId,
        account_id: currentOpportunityData ? currentOpportunityData.account_id : null
    });
}

// deleteTaskFromOpp eliminado — lógica movida a event delegation en renderOpportunityTasks

/**
 * Edit task from opportunity
 */
window.editTaskFromOpp = async function(taskId) {
    await editTask(taskId);
}

/**
 * Complete task from opportunity
 */
window.completeTaskFromOpp = async function(taskId) {
    try {
        const response = await fetch(`/tasks/${taskId}/complete`, {
            method: 'POST',
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Error completing task');
        }
        
        showToast('Tarea completada', 'success');
        
        // Reload tasks
        await loadOpportunityTasks(currentOpportunityId);
        
    } catch (error) {
        console.error('[TASKS] Error completing task:', error);
        showToast('Error al completar tarea', 'danger');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ---------------------------------------------------------------------------
// B5/B6 — Cerrar oportunidad como Ganada / Perdida
// ---------------------------------------------------------------------------

/**
 * Abre el modal de confirmación para marcar como Ganada.
 * Pre-rellena el valor esperado y muestra aviso si hay override activo.
 */
window.openWonConfirm = function() {
    const opp = currentOpportunityData;
    if (!opp) return;

    document.getElementById('won-confirm-opp-name').textContent =
        `"${opp.name || opp.account_name}"`;

    // Advertencia si hay override de probabilidad
    const warningEl = document.getElementById('won-override-warning');
    if (opp.probability_override !== null && opp.probability_override !== undefined) {
        document.getElementById('won-override-value').textContent =
            (opp.probability_override * 100).toFixed(0);
        warningEl.classList.remove('d-none');
    } else {
        warningEl.classList.add('d-none');
    }

    // Pre-rellenar valor esperado
    document.getElementById('won-final-value').value = opp.expected_value_eur || 0;

    // Fecha de hoy por defecto
    document.getElementById('won-close-date').value = new Date().toISOString().split('T')[0];

    // Ocultar modal de detalle y mostrar confirmación
    bootstrap.Modal.getInstance(document.getElementById('oppDetailModal'))?.hide();
    new bootstrap.Modal(document.getElementById('wonConfirmModal')).show();
};

/**
 * Confirma el cierre como Ganada y llama al endpoint /kanban/{id}/close.
 */
window.confirmCloseWon = async function() {
    const opp = currentOpportunityData;
    if (!opp) return;

    const wonValue = parseFloat(document.getElementById('won-final-value').value);
    const closeDate = document.getElementById('won-close-date').value;

    if (!closeDate) {
        showToast('Indica la fecha de cierre', 'warning');
        return;
    }

    try {
        const response = await fetch(`/kanban/${opp.id}/close`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                close_outcome: 'won',
                close_date: closeDate,
                won_value_eur: isNaN(wonValue) ? opp.expected_value_eur : wonValue
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || `Error ${response.status}`);
        }

        bootstrap.Modal.getInstance(document.getElementById('wonConfirmModal'))?.hide();
        showToast('Oportunidad marcada como Ganada', 'success');
        await loadKanbanData();
        if (typeof loadDashboard === 'function') await loadDashboard();

    } catch (error) {
        console.error('[CLOSE-WON] Error:', error);
        showToast(`Error: ${error.message}`, 'danger');
    }
};

/**
 * Abre el modal de confirmación para marcar como Perdida.
 */
// ============================================================================
// AI — Sprint 4E
// ============================================================================

/**
 * Rellena el bloque AI cuando se abre la ficha de oportunidad.
 * Carga los selectores de estado mental y tipo, y muestra los valores guardados.
 */
async function loadAISection(opp) {
    // Síntesis ejecutiva
    const summaryEl = document.getElementById('ai-executive-summary');
    summaryEl.value = opp.executive_summary || '';
    summaryEl.addEventListener('input', () => {
        document.getElementById('btn-save-summary').style.display = 'inline-block';
    }, { once: false });

    // Objetivo y próxima acción
    document.getElementById('ai-strategic-objective').value = opp.strategic_objective || '';
    document.getElementById('ai-next-action').value = opp.next_strategic_action || '';

    // ChatGPT URL / thread
    document.getElementById('ai-chatgpt-url').value = opp.chatgpt_url || '';
    if (opp.chatgpt_thread_id) {
        document.getElementById('ai-thread-badge').style.display = 'inline-block';
        document.getElementById('ai-thread-id-display').textContent = `Thread: ${opp.chatgpt_thread_id}`;
        document.getElementById('ai-history-section').style.display = 'block';
    } else {
        document.getElementById('ai-thread-badge').style.display = 'none';
        document.getElementById('ai-thread-id-display').textContent = '';
        document.getElementById('ai-history-section').style.display = 'none';
    }

    // Reset chat
    document.getElementById('ai-chat-response').style.display = 'none';
    document.getElementById('ai-chat-input').value = '';

    // Cargar selectores desde API
    await Promise.all([
        _loadAISelect('/config/client-mental-states', 'ai-mental-state', opp.client_mental_state_id),
        _loadAISelect('/config/opportunity-types', 'ai-opp-type', opp.opportunity_type_id)
    ]);
}

async function _loadAISelect(url, selectId, selectedValue) {
    const select = document.getElementById(selectId);
    select.innerHTML = '<option value="">No definido</option>';
    try {
        const res = await fetch(url, { credentials: 'include' });
        if (res.ok) {
            const items = await res.json();
            items.forEach(item => {
                const opt = document.createElement('option');
                opt.value = item.id;
                opt.textContent = item.name;
                if (item.id === selectedValue) opt.selected = true;
                select.appendChild(opt);
            });
        }
    } catch(e) { /* silencioso */ }
}

/**
 * Llama a POST /opportunities/{id}/ai/analyze y actualiza la síntesis.
 */
window.analyzeWithAI = async function() {
    const opp = currentOpportunityData;
    if (!opp) return;

    const btn = document.getElementById('btn-ai-analyze');
    const spinner = document.getElementById('ai-analyzing-spinner');

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Analizando...';
    spinner.style.display = 'block';

    try {
        const res = await fetch(`/opportunities/${opp.id}/ai/analyze`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || `Error ${res.status}`);
        }

        const data = await res.json();

        // Actualizar UI con la síntesis generada
        document.getElementById('ai-executive-summary').value = data.executive_summary;
        document.getElementById('btn-save-summary').style.display = 'none';

        // Actualizar thread_id en datos locales
        currentOpportunityData.executive_summary = data.executive_summary;
        currentOpportunityData.chatgpt_thread_id = data.thread_id;

        document.getElementById('ai-thread-badge').style.display = 'inline-block';
        document.getElementById('ai-thread-id-display').textContent = `Thread: ${data.thread_id}`;
        document.getElementById('ai-history-section').style.display = 'block';

        showToast('✨ Análisis completado', 'success');

    } catch(e) {
        console.error('[AI] analyze error:', e);
        showToast(`Error al analizar: ${e.message}`, 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-stars me-1"></i> Analizar con IA';
        spinner.style.display = 'none';
    }
};

/**
 * Guarda solo la síntesis ejecutiva editada manualmente.
 */
window.saveAISummary = async function() {
    const opp = currentOpportunityData;
    if (!opp) return;
    const summary = document.getElementById('ai-executive-summary').value;
    try {
        const res = await fetch(`/opportunities/${opp.id}`, {
            method: 'PUT',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ executive_summary: summary })
        });
        if (!res.ok) throw new Error(`Error ${res.status}`);
        currentOpportunityData.executive_summary = summary;
        document.getElementById('btn-save-summary').style.display = 'none';
        showToast('Síntesis guardada', 'success');
    } catch(e) {
        showToast(`Error al guardar: ${e.message}`, 'danger');
    }
};

/**
 * Guarda los campos estratégicos (estado mental, tipo, objetivo, próxima acción, URL).
 */
window.saveAIFields = async function() {
    const opp = currentOpportunityData;
    if (!opp) return;
    const payload = {
        client_mental_state_id: document.getElementById('ai-mental-state').value || null,
        opportunity_type_id: document.getElementById('ai-opp-type').value || null,
        strategic_objective: document.getElementById('ai-strategic-objective').value || null,
        next_strategic_action: document.getElementById('ai-next-action').value || null,
        chatgpt_url: document.getElementById('ai-chatgpt-url').value || null
    };
    try {
        const res = await fetch(`/opportunities/${opp.id}`, {
            method: 'PUT',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error(`Error ${res.status}`);
        Object.assign(currentOpportunityData, payload);
        showToast('Campos estratégicos guardados', 'success');
    } catch(e) {
        showToast(`Error al guardar: ${e.message}`, 'danger');
    }
};

/**
 * Envía un mensaje al thread de IA de la oportunidad.
 */
window.sendAIChat = async function() {
    const opp = currentOpportunityData;
    if (!opp) return;

    const input = document.getElementById('ai-chat-input');
    const message = input.value.trim();
    if (!message) return;

    if (!opp.chatgpt_thread_id) {
        showToast('Primero analiza la oportunidad con IA para iniciar el thread', 'warning');
        return;
    }

    const chatSpinner = document.getElementById('ai-chat-spinner');
    const chatResponse = document.getElementById('ai-chat-response');
    const chatBtn = document.getElementById('btn-ai-chat');

    chatSpinner.style.display = 'block';
    chatResponse.style.display = 'none';
    chatBtn.disabled = true;

    try {
        const res = await fetch(`/opportunities/${opp.id}/ai/chat`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || `Error ${res.status}`);
        }
        const data = await res.json();
        document.getElementById('ai-chat-response-text').textContent = data.response;
        chatResponse.style.display = 'block';
        input.value = '';
    } catch(e) {
        console.error('[AI] chat error:', e);
        showToast(`Error: ${e.message}`, 'danger');
    } finally {
        chatSpinner.style.display = 'none';
        chatBtn.disabled = false;
    }
};

/**
 * Abre la URL de ChatGPT en nueva pestaña.
 */
window.openChatGPTUrl = function() {
    const url = document.getElementById('ai-chatgpt-url').value;
    if (url) window.open(url, '_blank');
    else showToast('No hay URL configurada', 'warning');
};

window.openLostConfirm = async function() {
    const opp = currentOpportunityData;
    if (!opp) return;

    document.getElementById('lost-confirm-opp-name').textContent =
        `"${opp.name || opp.account_name}"`;
    document.getElementById('lost-reason-detail').value = '';
    document.getElementById('lost-close-date').value = new Date().toISOString().split('T')[0];

    // Cargar motivos de pérdida desde la API
    const select = document.getElementById('lost-reason-select');
    select.innerHTML = '<option value="">Seleccionar motivo...</option>';
    try {
        const res = await fetch('/config/lost-reasons', { credentials: 'include' });
        if (res.ok) {
            const reasons = await res.json();
            reasons.forEach(r => {
                const opt = document.createElement('option');
                opt.value = r.id;
                opt.textContent = r.name;
                select.appendChild(opt);
            });
        }
    } catch (e) {
        console.warn('[LOST-MODAL] No se pudieron cargar los motivos:', e);
    }

    bootstrap.Modal.getInstance(document.getElementById('oppDetailModal'))?.hide();
    new bootstrap.Modal(document.getElementById('lostConfirmModal')).show();
};

/**
 * Confirma el cierre como Perdida.
 */
window.confirmCloseLost = async function() {
    const opp = currentOpportunityData;
    if (!opp) return;

    const lostReasonId = document.getElementById('lost-reason-select').value;
    const lostReasonDetail = document.getElementById('lost-reason-detail').value.trim();
    const closeDate = document.getElementById('lost-close-date').value;

    if (!lostReasonId) {
        showToast('El motivo de pérdida es obligatorio', 'warning');
        document.getElementById('lost-reason-select').focus();
        return;
    }
    if (!closeDate) {
        showToast('Indica la fecha de cierre', 'warning');
        return;
    }

    try {
        const response = await fetch(`/kanban/${opp.id}/close`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                close_outcome: 'lost',
                close_date: closeDate,
                lost_reason_id: lostReasonId,
                lost_reason_detail: lostReasonDetail || null
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || `Error ${response.status}`);
        }

        bootstrap.Modal.getInstance(document.getElementById('lostConfirmModal'))?.hide();
        showToast('Oportunidad marcada como Perdida', 'danger');
        await loadKanbanData();
        if (typeof loadDashboard === 'function') await loadDashboard();

    } catch (error) {
        console.error('[CLOSE-LOST] Error:', error);
        showToast(`Error: ${error.message}`, 'danger');
    }
};

console.log('[KANBAN] Module loaded, loadKanbanData registered');

// Additional handler for URL hash (executes after full page load including images)
window.addEventListener('load', function() {
    console.log('[DASHBOARD] === Window LOAD event ===');
    console.log('[DASHBOARD] Current hash on window.load:', window.location.hash);
    activateKanbanIfNeeded('window-load');
});
