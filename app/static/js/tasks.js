/**
 * TASKS MANAGEMENT - Dashboard Tasks Tab
 * ========================================
 * 
 * Funciones para gestionar tareas en el dashboard:
 * - Listar tareas (semáforo: overdue, due soon, upcoming)
 * - Crear/Editar tareas
 * - Completar tareas
 * - Filtros y búsqueda
 */

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Obtener usuario actual desde el state de dashboard.js o desde API
 */
async function getCurrentUser() {
    // Si estamos en dashboard y existe state
    if (typeof state !== 'undefined' && state.currentUser) {
        return state.currentUser;
    }
    
    // Si no, hacer fetch a /auth/me (para accounts.html)
    try {
        const response = await fetch('/auth/me', { credentials: 'include' });
        if (!response.ok) {
            throw new Error('No autenticado');
        }
        const user = await response.json();
        return user;
    } catch (error) {
        console.error('Error getting current user:', error);
        throw new Error('Usuario no disponible');
    }
}

/**
 * Mostrar alerta usando el sistema de toast del dashboard
 */
function showAlert(message, type = 'info') {
    if (typeof showToast !== 'undefined') {
        showToast(message, type);
    } else {
        console.log(`[${type.toUpperCase()}] ${message}`);
        alert(message);
    }
}

// ============================================================================
// STATE
// ============================================================================

// Estado global de tareas
let allTasks = [];
let currentTaskFilter = {
    status: 'open',
    priority: '',
    search: '',
    overdue: false
};

/**
 * Init admin user selector in tasks tab (shown only to admins)
 */
async function initTasksUserFilter() {
    const currentUser = await getCurrentUser();
    if (currentUser.role !== 'admin') return;

    const wrapper = document.getElementById('filter-task-user-wrapper');
    if (!wrapper) return;
    wrapper.style.display = '';

    const select = document.getElementById('filter-task-user');
    // Idempotent: skip if already populated
    if (select && select.options.length > 1) return;

    try {
        const response = await fetch('/admin/users', { credentials: 'include' });
        if (!response.ok) return;
        const data = await response.json();
        (data.users || []).forEach(u => {
            const opt = document.createElement('option');
            opt.value = u.id;
            opt.textContent = `${u.name} (${u.role})`;
            if (u.id === currentUser.id) opt.selected = true;
            select.appendChild(opt);
        });
    } catch (e) {
        console.error('Error loading users for task filter:', e);
    }
}

/**
 * Cargar mis tareas asignadas
 */
async function loadMyTasks() {
    try {
        // Obtener usuario actual
        const currentUser = await getCurrentUser();

        // Construir URL con filtros
        const params = new URLSearchParams();

        // Admin: use user selector if present; otherwise load own tasks
        const userFilterEl = document.getElementById('filter-task-user');
        if (userFilterEl && currentUser.role === 'admin') {
            if (userFilterEl.value) {
                params.append('assigned_to', userFilterEl.value);
            }
            // no assigned_to means see all tasks (admin sees everything)
        } else {
            params.append('assigned_to', currentUser.id);
        }
        
        // Aplicar filtros adicionales (solo si existen los elementos)
        const statusFilterEl = document.getElementById('filter-task-status');
        if (statusFilterEl && statusFilterEl.value) {
            params.append('status', statusFilterEl.value);
        }
        
        const priorityFilterEl = document.getElementById('filter-task-priority');
        if (priorityFilterEl && priorityFilterEl.value) {
            params.append('priority', priorityFilterEl.value);
        }
        
        const overdueFilterEl = document.getElementById('filter-task-overdue');
        if (overdueFilterEl && overdueFilterEl.checked) {
            params.append('overdue', 'true');
        }
        
        // Hacer request
        const response = await fetch(`/tasks?${params.toString()}`);
        
        if (!response.ok) {
            throw new Error('Error al cargar tareas');
        }
        
        const data = await response.json();
        allTasks = data.tasks || [];
        
        // Aplicar filtro de búsqueda local
        const searchFilter = document.getElementById('filter-task-search').value.toLowerCase();
        if (searchFilter) {
            allTasks = allTasks.filter(task => 
                task.title.toLowerCase().includes(searchFilter)
            );
        }
        
        // Renderizar en vista semáforo
        renderTasksSemaphore(allTasks);
        
        // Actualizar contador en el tab
        updateTasksCounter();
        
    } catch (error) {
        console.error('Error loading tasks:', error);
        showAlert('Error al cargar tareas', 'danger');
    }
}

/**
 * Renderizar tareas en vista semáforo
 */
function renderTasksSemaphore(tasks) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const twoDaysFromNow = new Date(today);
    twoDaysFromNow.setDate(twoDaysFromNow.getDate() + 2);
    
    const tenDaysFromNow = new Date(today);
    tenDaysFromNow.setDate(tenDaysFromNow.getDate() + 10);
    
    // Clasificar tareas
    const overdue = [];
    const dueSoon = [];
    const upcoming = [];
    
    tasks.forEach(task => {
        if (!task.due_date) {
            upcoming.push(task); // Sin fecha → upcoming
            return;
        }
        
        const dueDate = new Date(task.due_date + 'T00:00:00');
        
        if (dueDate < today) {
            overdue.push(task);
        } else if (dueDate <= twoDaysFromNow) {
            dueSoon.push(task);
        } else if (dueDate <= tenDaysFromNow) {
            upcoming.push(task);
        }
    });
    
    // Renderizar cada columna
    renderTaskColumn('tasks-overdue', overdue, 'badge-overdue');
    renderTaskColumn('tasks-due-soon', dueSoon, 'badge-due-soon');
    renderTaskColumn('tasks-upcoming', upcoming, 'badge-upcoming');
}

/**
 * Renderizar columna de tareas
 */
function renderTaskColumn(containerId, tasks, badgeId) {
    const container = document.getElementById(containerId);
    const badge = document.getElementById(badgeId);
    
    // Actualizar badge
    badge.textContent = tasks.length;
    
    if (tasks.length === 0) {
        container.innerHTML = '<p class="text-muted text-center py-3"><i class="bi bi-check-circle"></i> Sin tareas</p>';
        return;
    }
    
    // Ordenar por fecha (nulls al final)
    tasks.sort((a, b) => {
        if (!a.due_date) return 1;
        if (!b.due_date) return -1;
        return a.due_date.localeCompare(b.due_date);
    });
    
    // Renderizar tarjetas
    container.innerHTML = tasks.map(task => createTaskCard(task)).join('');
}

/**
 * Crear HTML de tarjeta de tarea
 */
function createTaskCard(task) {
    const priorityIcon = {
        high: '🔴',
        medium: '🟡',
        low: '🟢'
    }[task.priority] || '⚪';
    
    const dueDate = task.due_date ? formatDate(task.due_date) : 'Sin fecha';
    const isCompleted = task.status === 'completed';
    
    // Calcular días restantes
    let dueDays = '';
    if (task.due_date) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const due = new Date(task.due_date + 'T00:00:00');
        const diffTime = due - today;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays < 0) {
            dueDays = `<span class="text-danger">Vencida hace ${Math.abs(diffDays)} días</span>`;
        } else if (diffDays === 0) {
            dueDays = '<span class="text-warning">Vence hoy</span>';
        } else if (diffDays === 1) {
            dueDays = '<span class="text-warning">Vence mañana</span>';
        } else {
            dueDays = `En ${diffDays} días`;
        }
    }
    
    return `
        <div class="task-card priority-${task.priority} ${isCompleted ? 'completed' : ''}"
             data-task-id="${task.id}"
             onclick="editTask('${task.id}')"
             style="cursor:pointer;">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <div class="flex-grow-1">
                    <div class="task-title">${escapeHtml(task.title)}</div>
                    ${task.task_template_name ? `<div class="mt-1"><span class="badge bg-info"><i class="bi bi-tag"></i> ${escapeHtml(task.task_template_name)}</span></div>` : ''}
                    <div class="task-meta">
                        <span>${priorityIcon} ${getPriorityText(task.priority)}</span>
                        ${task.due_date ? `<span><i class="bi bi-calendar3"></i> ${dueDate} ${dueDays}</span>` : ''}
                        ${task.opportunity_name ? `<span><i class="bi bi-bullseye"></i> ${escapeHtml(task.opportunity_name)}</span>` : ''}
                        ${task.account_name ? `<span><i class="bi bi-building"></i> ${escapeHtml(task.account_name)}</span>` : ''}
                    </div>
                </div>
                <div>
                    <input type="checkbox"
                           class="task-checkbox form-check-input"
                           ${isCompleted ? 'checked' : ''}
                           ${isCompleted ? 'disabled' : ''}
                           onclick="event.stopPropagation(); toggleTaskComplete('${task.id}', this.checked)"
                           title="${isCompleted ? 'Completada' : 'Marcar como completada'}">
                </div>
            </div>

            <div class="task-actions">
                <button class="btn btn-sm btn-outline-primary" onclick="event.stopPropagation(); editTask('${task.id}')">
                    <i class="bi bi-pencil"></i> Editar
                </button>
                ${!isCompleted ? `
                <button class="btn btn-sm btn-outline-success" onclick="event.stopPropagation(); completeTask('${task.id}')">
                    <i class="bi bi-check-lg"></i> Completar
                </button>
                ` : ''}
                <button class="btn btn-sm btn-outline-danger" onclick="event.stopPropagation(); deleteTask('${task.id}')">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        </div>
    `;
}

/**
 * Mostrar modal para crear tarea
 */
async function showCreateTaskModal(preselect = {}) {
    // Verificar que el formulario existe
    const taskForm = document.getElementById('taskForm');
    if (!taskForm) {
        console.error('taskForm not found in DOM');
        return;
    }
    
    // Limpiar formulario
    taskForm.reset();
    document.getElementById('task-id').value = '';

    // Re-habilitar campos (pueden estar deshabilitados si se vino de viewTaskDetails)
    ['task-title','task-description','task-template','task-opportunity','task-account',
     'task-priority','task-due-date','task-assigned-to'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = false;
    });
    const saveBtn = document.querySelector('#taskModal .btn-primary');
    if (saveBtn) saveBtn.style.display = '';
    
    // Cambiar título
    document.getElementById('taskModalTitle').innerHTML = '<i class="bi bi-plus-circle"></i> Nueva Tarea';
    
    // Mostrar modal primero
    const modalElement = document.getElementById('taskModal');
    if (!modalElement) {
        console.error('taskModal not found in DOM');
        return;
    }
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
    
    // Cargar opciones (async)
    await loadTaskFormOptions();

    // Aplicar preselección después de que las opciones estén cargadas
    if (preselect.opportunity_id) {
        const oppEl = document.getElementById('task-opportunity');
        if (oppEl) oppEl.value = preselect.opportunity_id;
    }
    if (preselect.account_id) {
        const accEl = document.getElementById('task-account');
        if (accEl) accEl.value = preselect.account_id;
    }
    // Prefill desde propuesta IA
    if (preselect.title) {
        const el = document.getElementById('task-title');
        if (el) el.value = preselect.title;
    }
    if (preselect.description) {
        const el = document.getElementById('task-description');
        if (el) el.value = preselect.description;
    }
    if (preselect.priority) {
        const el = document.getElementById('task-priority');
        if (el) el.value = preselect.priority;
    }
    if (preselect.due_date) {
        const el = document.getElementById('task-due-date');
        if (el) el.value = preselect.due_date;
    }
}

/**
 * Editar tarea existente
 */
async function editTask(taskId) {
    try {
        // Re-habilitar campos (pueden estar deshabilitados si se vino de viewTaskDetails)
        ['task-title','task-description','task-template','task-opportunity','task-account',
         'task-priority','task-due-date','task-assigned-to'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.disabled = false;
        });
        const saveBtn = document.querySelector('#taskModal .btn-primary');
        if (saveBtn) saveBtn.style.display = '';

        // Obtener datos de la tarea
        const response = await fetch(`/tasks/${taskId}`);
        
        if (!response.ok) {
            throw new Error('Error al cargar tarea');
        }
        
        const task = await response.json();
        
        // Llenar formulario
        document.getElementById('task-id').value = task.id;
        document.getElementById('task-title').value = task.title;
        document.getElementById('task-description').value = task.description || '';
        document.getElementById('task-template').value = task.task_template_id || '';
        document.getElementById('task-opportunity').value = task.opportunity_id || '';
        document.getElementById('task-account').value = task.account_id || '';
        document.getElementById('task-priority').value = task.priority;
        document.getElementById('task-due-date').value = task.due_date || '';
        document.getElementById('task-assigned-to').value = task.assigned_to_user_id || '';
        
        // Cambiar título
        document.getElementById('taskModalTitle').innerHTML = '<i class="bi bi-pencil"></i> Editar Tarea';
        
        // Cargar opciones
        await loadTaskFormOptions();
        
        // Reseleccionar valores (por si se perdieron al cargar options)
        document.getElementById('task-template').value = task.task_template_id || '';
        document.getElementById('task-opportunity').value = task.opportunity_id || '';
        document.getElementById('task-account').value = task.account_id || '';
        document.getElementById('task-assigned-to').value = task.assigned_to_user_id || '';
        
        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('taskModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error loading task:', error);
        showAlert('Error al cargar tarea', 'danger');
    }
}

/**
 * Cargar opciones del formulario (oportunidades, cuentas, usuarios)
 */
async function loadTaskFormOptions() {
    try {
        // Cargar plantillas de tareas (task templates)
        const templatesResponse = await fetch('/config/task-templates');
        if (!templatesResponse.ok) {
            console.error('Error loading templates:', templatesResponse.status);
        }
        const templates = await templatesResponse.json(); // Es un array directo, no un objeto
        
        const templateSelect = document.getElementById('task-template');
        templateSelect.innerHTML = '<option value="">Sin tipo específico</option>';
        templates.filter(t => t.is_active).forEach(template => {
            templateSelect.innerHTML += `<option value="${template.id}" data-due-days="${template.default_due_days || ''}">${escapeHtml(template.name)}</option>`;
        });
        
        // Cargar oportunidades
        const oppsResponse = await fetch('/opportunities');
        const oppsData = await oppsResponse.json();
        const opportunities = oppsData.opportunities || [];
        
        const oppSelect = document.getElementById('task-opportunity');
        oppSelect.innerHTML = '<option value="">Sin oportunidad</option>';
        opportunities.forEach(opp => {
            const oppName = opp.name || `Opp ${opp.id.substring(0, 8)}...`;
            oppSelect.innerHTML += `<option value="${opp.id}">${escapeHtml(oppName)}</option>`;
        });
        
        // Cargar cuentas
        const accountsResponse = await fetch('/accounts');
        const accountsData = await accountsResponse.json();
        const accounts = accountsData.accounts || [];
        
        const accSelect = document.getElementById('task-account');
        accSelect.innerHTML = '<option value="">Sin cuenta</option>';
        accounts.forEach(acc => {
            accSelect.innerHTML += `<option value="${acc.id}">${escapeHtml(acc.name)}</option>`;
        });
        
        // Cargar usuarios (solo admin y sales pueden ver todos)
        const currentUser = await getCurrentUser();
        const usersResponse = await fetch('/admin/users');
        
        if (usersResponse.ok) {
            const usersData = await usersResponse.json();
            const users = usersData.users || [];
            
            const userSelect = document.getElementById('task-assigned-to');
            userSelect.innerHTML = '<option value="">Sin asignar</option>';
            users.forEach(user => {
                if (user.is_active) {
                    userSelect.innerHTML += `<option value="${user.id}">${escapeHtml(user.name)}</option>`;
                }
            });
        }
        
    } catch (error) {
        console.error('Error loading form options:', error);
    }
}

/**
 * Handler cuando cambia la plantilla de tarea
 */
function onTaskTemplateChange() {
    const templateSelect = document.getElementById('task-template');
    const selectedOption = templateSelect.options[templateSelect.selectedIndex];
    const dueDays = selectedOption.getAttribute('data-due-days');
    
    // Auto-calcular fecha de vencimiento si la plantilla tiene días por defecto
    if (dueDays && dueDays !== '') {
        const today = new Date();
        today.setDate(today.getDate() + parseInt(dueDays));
        
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        
        document.getElementById('task-due-date').value = `${year}-${month}-${day}`;
        
        // Mostrar feedback al usuario
        if (parseInt(dueDays) > 0) {
            showAlert(`Fecha establecida a ${dueDays} días desde hoy`, 'info');
        }
    }
}

/**
 * Guardar tarea (crear o editar)
 */
async function saveTask() {
    try {
        const taskId = document.getElementById('task-id').value;
        const title = document.getElementById('task-title').value.trim();
        const description = document.getElementById('task-description').value.trim();
        const templateId = document.getElementById('task-template').value;
        const opportunityId = document.getElementById('task-opportunity').value;
        const accountId = document.getElementById('task-account').value;
        const priority = document.getElementById('task-priority').value;
        const dueDate = document.getElementById('task-due-date').value;
        const assignedTo = document.getElementById('task-assigned-to').value;

        // Validar título
        if (!title) {
            showAlert('El título es obligatorio', 'warning');
            return;
        }

        // Validar vinculación
        if (!opportunityId && !accountId) {
            showAlert('Debes vincular la tarea a una oportunidad o una cuenta', 'warning');
            return;
        }

        // Guardar opportunity_id original para poder refrescar la card Kanban anterior
        let originalOppId = null;
        if (taskId) {
            const existingTask = allTasks.find(t => t.id === taskId);
            if (existingTask) {
                originalOppId = existingTask.opportunity_id || null;
            }
        }

        // Construir payload
        const payload = {
            title: title,
            description: description || null,
            task_template_id: templateId || null,
            opportunity_id: opportunityId || null,
            account_id: accountId || null,
            priority: priority,
            due_date: dueDate || null,
            assigned_to_user_id: assignedTo || null
        };

        // Crear o editar
        let response;
        if (taskId) {
            // Editar
            response = await fetch(`/tasks/${taskId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } else {
            // Crear
            response = await fetch('/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }

        if (!response.ok) {
            const error = await response.json();
            const detail = error.detail;
            if (Array.isArray(detail)) {
                throw new Error(detail.map(e => e.msg || JSON.stringify(e)).join('; '));
            }
            throw new Error(typeof detail === 'string' ? detail : 'Error al guardar tarea');
        }

        const savedTask = await response.json();
        const newOppId = savedTask.opportunity_id || null;

        // Actualizar referencia local para reasignaciones consecutivas sin F5
        if (taskId) {
            const localTask = allTasks.find(t => t.id === taskId);
            if (localTask) {
                localTask.opportunity_id = newOppId;
            }
        }

        // Cerrar modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('taskModal'));
        modal.hide();

        // Recargar lista de tareas (cubre FIX 4: desvincular oportunidad refresca el panel)
        if (typeof loadMyTasks === 'function' && document.getElementById('filter-task-status')) {
            await loadMyTasks();
        }

        // Refrescar Kanban: siempre recargar para capturar oportunidad original y nueva
        // (cubre FIX 3: segunda reasignación consecutiva funciona porque se usa loadKanbanData completo)
        if (typeof window.loadKanbanData === 'function') {
            window.loadKanbanData();
        }

        // Si estamos en modal de oportunidad, recargar ese panel también
        if (typeof currentOpportunityId !== 'undefined' && currentOpportunityId) {
            if (typeof loadOpportunityTasks === 'function') {
                await loadOpportunityTasks(currentOpportunityId);
            }
        }

        // Si estamos en modal de cuenta (accounts.html), recargar ese panel también
        if (typeof currentAccountId !== 'undefined' && currentAccountId) {
            if (typeof loadAccountTasks === 'function') {
                await loadAccountTasks(currentAccountId);
            }
        }

        showAlert(taskId ? 'Tarea actualizada correctamente' : 'Tarea creada correctamente', 'success');

    } catch (error) {
        console.error('Error saving task:', error);
        showAlert(error.message || 'Error al guardar tarea', 'danger');
    }
}

/**
 * Completar tarea
 */
async function completeTask(taskId) {
    try {
        const response = await fetch(`/tasks/${taskId}/complete`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Error al completar tarea');
        }
        
        // Recargar tareas
        await loadMyTasks();
        
        showAlert('Tarea completada', 'success');
        
    } catch (error) {
        console.error('Error completing task:', error);
        showAlert('Error al completar tarea', 'danger');
    }
}

/**
 * Toggle completar tarea (checkbox)
 */
async function toggleTaskComplete(taskId, isCompleted) {
    if (isCompleted) {
        await completeTask(taskId);
    }
}

/**
 * Eliminar tarea
 */
async function deleteTask(taskId) {
    if (!confirm('¿Estás seguro de que quieres eliminar esta tarea?')) {
        return;
    }
    
    try {
        const response = await fetch(`/tasks/${taskId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Error al eliminar tarea');
        }
        
        // Recargar tareas
        await loadMyTasks();
        
        showAlert('Tarea eliminada', 'success');
        
    } catch (error) {
        console.error('Error deleting task:', error);
        showAlert('Error al eliminar tarea', 'danger');
    }
}

/**
 * Actualizar contador de tareas pendientes en el tab
 */
function updateTasksCounter() {
    const pendingTasks = allTasks.filter(t => 
        t.status === 'open' || t.status === 'in_progress'
    );
    
    const counter = document.getElementById('tasks-counter');
    
    if (pendingTasks.length > 0) {
        counter.textContent = pendingTasks.length;
        counter.style.display = 'inline-block';
    } else {
        counter.style.display = 'none';
    }
}

/**
 * Helpers
 */
function getPriorityText(priority) {
    const texts = {
        high: 'Alta',
        medium: 'Media',
        low: 'Baja'
    };
    return texts[priority] || priority;
}

function formatDate(dateStr) {
    const date = new Date(dateStr + 'T00:00:00');
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Inicializar cuando se activa el tab de tareas
 */
document.addEventListener('DOMContentLoaded', function() {
    // Cargar tareas cuando se activa el tab
    const tasksTab = document.getElementById('tasks-tab');
    if (tasksTab) {
        tasksTab.addEventListener('shown.bs.tab', function() {
            loadMyTasks();
        });
    }
    
    // Cargar archivo cuando se activa el sub-tab de archivo
    const archiveSubTab = document.getElementById('archive-tasks-subtab');
    if (archiveSubTab) {
        archiveSubTab.addEventListener('shown.bs.tab', function() {
            loadArchivedTasks();
        });
    }
});

/**
 * Cargar tareas archivadas (completadas y canceladas)
 */
async function loadArchivedTasks() {
    try {
        // Obtener usuario actual
        const currentUser = await getCurrentUser();
        
        // Construir URL para tareas completadas y canceladas
        const params = new URLSearchParams();
        params.append('assigned_to', currentUser.id);
        
        // Obtener ambos estados
        const completedParams = new URLSearchParams(params);
        completedParams.append('status', 'completed');
        
        const cancelledParams = new URLSearchParams(params);
        cancelledParams.append('status', 'cancelled');
        
        // Hacer ambos requests
        const [completedResponse, cancelledResponse] = await Promise.all([
            fetch(`/tasks?${completedParams.toString()}`),
            fetch(`/tasks?${cancelledParams.toString()}`)
        ]);
        
        if (!completedResponse.ok || !cancelledResponse.ok) {
            throw new Error('Error al cargar tareas archivadas');
        }
        
        const completedData = await completedResponse.json();
        const cancelledData = await cancelledResponse.json();
        
        const completedTasks = completedData.tasks || [];
        const cancelledTasks = cancelledData.tasks || [];
        
        // Combinar y ordenar por fecha de actualización (más reciente primero)
        const allArchived = [...completedTasks, ...cancelledTasks].sort((a, b) => {
            return b.updated_at.localeCompare(a.updated_at);
        });
        
        // Renderizar
        renderArchivedTasks(allArchived);
        
        // Actualizar contador
        document.getElementById('archive-counter').textContent = allArchived.length;
        
    } catch (error) {
        console.error('Error loading archived tasks:', error);
        showAlert('Error al cargar archivo de tareas', 'danger');
    }
}

/**
 * Renderizar tareas archivadas
 */
function renderArchivedTasks(tasks) {
    const container = document.getElementById('tasks-archive');
    
    if (tasks.length === 0) {
        container.innerHTML = '<p class="text-muted text-center py-4"><i class="bi bi-archive"></i> No hay tareas archivadas</p>';
        return;
    }
    
    // Agrupar por estado
    const completed = tasks.filter(t => t.status === 'completed');
    const cancelled = tasks.filter(t => t.status === 'cancelled');
    
    let html = '';
    
    // Completadas
    if (completed.length > 0) {
        html += '<h6 class="text-success mb-3"><i class="bi bi-check-circle-fill"></i> Completadas (' + completed.length + ')</h6>';
        html += '<div class="mb-4">';
        completed.forEach(task => {
            html += createArchivedTaskCard(task);
        });
        html += '</div>';
    }
    
    // Canceladas
    if (cancelled.length > 0) {
        html += '<h6 class="text-danger mb-3"><i class="bi bi-x-circle-fill"></i> Canceladas (' + cancelled.length + ')</h6>';
        html += '<div>';
        cancelled.forEach(task => {
            html += createArchivedTaskCard(task);
        });
        html += '</div>';
    }
    
    container.innerHTML = html;
}

/**
 * Crear tarjeta de tarea archivada
 */
function createArchivedTaskCard(task) {
    const statusIcon = task.status === 'completed' ? '✅' : '❌';
    const statusClass = task.status === 'completed' ? 'success' : 'danger';
    const statusText = task.status === 'completed' ? 'Completada' : 'Cancelada';
    
    const completedDate = task.completed_at ? formatDate(task.completed_at.split('T')[0]) : '';
    const completedBy = task.completed_by_name || 'Sistema';
    
    const priorityIcon = {
        high: '🔴',
        medium: '🟡',
        low: '🟢'
    }[task.priority] || '⚪';
    
    return `
        <div class="task-card priority-${task.priority} completed mb-3" 
             style="opacity: 0.8;">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <div class="flex-grow-1">
                    <div class="task-title">${statusIcon} ${escapeHtml(task.title)}</div>
                    <div class="task-meta">
                        <span class="badge bg-${statusClass}">${statusText}</span>
                        ${task.task_template_name ? `<span class="badge bg-info"><i class="bi bi-tag"></i> ${escapeHtml(task.task_template_name)}</span>` : ''}
                        <span>${priorityIcon} ${getPriorityText(task.priority)}</span>
                        ${task.completed_at ? `<span><i class="bi bi-calendar-check"></i> ${completedDate}</span>` : ''}
                        ${task.completed_by_name ? `<span><i class="bi bi-person"></i> ${escapeHtml(completedBy)}</span>` : ''}
                        ${task.opportunity_name ? `<span><i class="bi bi-bullseye"></i> ${escapeHtml(task.opportunity_name)}</span>` : ''}
                        ${task.account_name ? `<span><i class="bi bi-building"></i> ${escapeHtml(task.account_name)}</span>` : ''}
                    </div>
                    ${task.description ? `
                    <div class="mt-2">
                        <small class="text-muted">${escapeHtml(task.description).substring(0, 150)}${task.description.length > 150 ? '...' : ''}</small>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            <div class="task-actions">
                ${task.status === 'completed' ? `
                <button class="btn btn-sm btn-outline-warning" onclick="reopenTask('${task.id}')">
                    <i class="bi bi-arrow-counterclockwise"></i> Reabrir
                </button>
                ` : ''}
                <button class="btn btn-sm btn-outline-primary" onclick="viewTaskDetails('${task.id}')">
                    <i class="bi bi-eye"></i> Ver detalles
                </button>
            </div>
        </div>
    `;
}

/**
 * Reabrir tarea completada
 */
async function reopenTask(taskId) {
    if (!confirm('¿Reabrir esta tarea? Volverá al estado "pendiente".')) {
        return;
    }
    
    try {
        const response = await fetch(`/tasks/${taskId}/reopen`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Error al reabrir tarea');
        }
        
        // Recargar archivo
        await loadArchivedTasks();
        
        showAlert('Tarea reabierta correctamente', 'success');
        
    } catch (error) {
        console.error('Error reopening task:', error);
        showAlert('Error al reabrir tarea', 'danger');
    }
}

/**
 * Ver detalles de tarea (reutiliza editTask pero en modo lectura)
 */
async function viewTaskDetails(taskId) {
    await editTask(taskId);
    
    // Deshabilitar campos para solo lectura
    document.getElementById('task-title').disabled = true;
    document.getElementById('task-description').disabled = true;
    document.getElementById('task-opportunity').disabled = true;
    document.getElementById('task-account').disabled = true;
    document.getElementById('task-priority').disabled = true;
    document.getElementById('task-due-date').disabled = true;
    document.getElementById('task-assigned-to').disabled = true;
    
    // Cambiar título y ocultar botón guardar
    document.getElementById('taskModalTitle').innerHTML = '<i class="bi bi-eye"></i> Detalles de Tarea';
    document.querySelector('#taskModal .btn-primary').style.display = 'none';
}
