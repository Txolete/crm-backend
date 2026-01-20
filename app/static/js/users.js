/**
 * Users Management JS
 * Handles all user CRUD operations for admin panel
 */

let allUsers = [];
let editingUserId = null;

// Load users on page load
document.addEventListener('DOMContentLoaded', () => {
    loadUsers();
    setupEventListeners();
    loadCurrentUser();
});

function setupEventListeners() {
    document.getElementById('btn-new-user').addEventListener('click', showCreateModal);
    document.getElementById('btn-save-user').addEventListener('click', saveUser);
    document.getElementById('btn-confirm-reset').addEventListener('click', confirmResetPassword);
    document.getElementById('btn-reset-filters').addEventListener('click', resetFilters);
    document.getElementById('filter-role').addEventListener('change', applyFilters);
    document.getElementById('filter-status').addEventListener('change', applyFilters);
}

async function loadCurrentUser() {
    try {
        const response = await fetch('/auth/me', { credentials: 'include' });
        if (response.ok) {
            const user = await response.json();
            document.getElementById('user-name').textContent = user.name;
        }
    } catch (error) {
        console.error('Error loading current user:', error);
    }
}

async function loadUsers() {
    try {
        const response = await fetch('/admin/users', { credentials: 'include' });
        
        if (!response.ok) {
            if (response.status === 403) {
                alert('⛔ No tienes permisos para ver esta página');
                window.location.href = '/dashboard';
                return;
            }
            throw new Error(`Error ${response.status}`);
        }
        
        const data = await response.json();
        allUsers = data.users || [];
        renderUsers(allUsers);
        
    } catch (error) {
        console.error('Error loading users:', error);
        document.getElementById('users-table-body').innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-danger py-4">
                    <i class="bi bi-exclamation-triangle"></i>
                    Error al cargar usuarios: ${error.message}
                </td>
            </tr>
        `;
    }
}

function renderUsers(users) {
    const tbody = document.getElementById('users-table-body');
    
    if (users.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted py-5">
                    <i class="bi bi-people" style="font-size: 3rem;"></i>
                    <p class="mt-2">No hay usuarios que mostrar</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = users.map(user => {
        const initials = user.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
        const roleBadgeClass = `badge-${user.role}`;
        const roleLabel = {
            'admin': 'Admin',
            'sales': 'Sales',
            'viewer': 'Viewer'
        }[user.role] || user.role;
        
        const statusBadge = user.is_active 
            ? '<span class="badge bg-success">Activo</span>'
            : '<span class="badge bg-secondary">Inactivo</span>';
        
        const lastLogin = user.last_login_at 
            ? new Date(user.last_login_at).toLocaleDateString('es-ES', { 
                day: '2-digit', month: '2-digit', year: 'numeric', 
                hour: '2-digit', minute: '2-digit' 
              })
            : '<span class="text-muted">Nunca</span>';
        
        const toggleBtn = user.is_active
            ? `<button class="btn btn-sm btn-outline-warning" onclick="toggleUserStatus('${user.id}', false)" title="Desactivar">
                <i class="bi bi-pause-circle"></i>
               </button>`
            : `<button class="btn btn-sm btn-outline-success" onclick="toggleUserStatus('${user.id}', true)" title="Activar">
                <i class="bi bi-play-circle"></i>
               </button>`;
        
        return `
            <tr>
                <td>
                    <div class="d-flex align-items-center gap-2">
                        <div class="user-avatar">${initials}</div>
                        <div>
                            <div class="fw-semibold">${escapeHtml(user.name)}</div>
                            <small class="text-muted">ID: ${user.id.substring(0, 8)}...</small>
                        </div>
                    </div>
                </td>
                <td>${escapeHtml(user.email)}</td>
                <td>
                    <span class="badge badge-role ${roleBadgeClass}">${roleLabel}</span>
                </td>
                <td>${statusBadge}</td>
                <td>${lastLogin}</td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button class="btn btn-outline-primary" onclick="showEditModal('${user.id}')" title="Editar">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-outline-secondary" onclick="showResetPasswordModal('${user.id}')" title="Resetear contraseña">
                            <i class="bi bi-key"></i>
                        </button>
                        ${toggleBtn}
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function showCreateModal() {
    editingUserId = null;
    document.getElementById('userModalTitle').textContent = 'Nuevo Usuario';
    document.getElementById('user-id').value = '';
    document.getElementById('form-user').reset();
    document.getElementById('user-active').checked = true;
    document.getElementById('password-group').style.display = 'block';
    document.getElementById('user-password').required = true;
    
    const modal = new bootstrap.Modal(document.getElementById('userModal'));
    modal.show();
}

function showEditModal(userId) {
    const user = allUsers.find(u => u.id === userId);
    if (!user) return;
    
    editingUserId = userId;
    document.getElementById('userModalTitle').textContent = 'Editar Usuario';
    document.getElementById('user-id').value = user.id;
    document.getElementById('user-name-input').value = user.name;
    document.getElementById('user-email').value = user.email;
    document.getElementById('user-role').value = user.role;
    document.getElementById('user-active').checked = user.is_active;
    document.getElementById('password-group').style.display = 'none';
    document.getElementById('user-password').required = false;
    
    const modal = new bootstrap.Modal(document.getElementById('userModal'));
    modal.show();
}

async function saveUser() {
    try {
        const name = document.getElementById('user-name-input').value.trim();
        const email = document.getElementById('user-email').value.trim();
        const role = document.getElementById('user-role').value;
        const isActive = document.getElementById('user-active').checked;
        const password = document.getElementById('user-password').value;
        
        // Validation
        if (!name || !email || !role) {
            alert('⚠️ Por favor completa todos los campos obligatorios');
            return;
        }
        
        if (!editingUserId && !password) {
            alert('⚠️ La contraseña es obligatoria para nuevos usuarios');
            return;
        }
        
        if (password && password.length < 6) {
            alert('⚠️ La contraseña debe tener al menos 6 caracteres');
            return;
        }
        
        const payload = {
            name: name,
            email: email,
            role: role,
            is_active: isActive
        };
        
        if (!editingUserId) {
            payload.password = password;
        }
        
        const btn = document.getElementById('btn-save-user');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Guardando...';
        
        const url = editingUserId ? `/admin/users/${editingUserId}` : '/admin/users';
        const method = editingUserId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al guardar usuario');
        }
        
        // Close modal and reload
        bootstrap.Modal.getInstance(document.getElementById('userModal')).hide();
        await loadUsers();
        
        alert(editingUserId ? '✅ Usuario actualizado correctamente' : '✅ Usuario creado correctamente');
        
    } catch (error) {
        console.error('Error saving user:', error);
        alert('❌ Error: ' + error.message);
    } finally {
        const btn = document.getElementById('btn-save-user');
        btn.disabled = false;
        btn.innerHTML = 'Guardar';
    }
}

function showResetPasswordModal(userId) {
    const user = allUsers.find(u => u.id === userId);
    if (!user) return;
    
    document.getElementById('reset-user-id').value = user.id;
    document.getElementById('reset-user-name').textContent = user.name;
    document.getElementById('form-reset-password').reset();
    
    const modal = new bootstrap.Modal(document.getElementById('resetPasswordModal'));
    modal.show();
}

async function confirmResetPassword() {
    try {
        const userId = document.getElementById('reset-user-id').value;
        const password = document.getElementById('reset-password').value;
        const passwordConfirm = document.getElementById('reset-password-confirm').value;
        
        if (!password || password.length < 6) {
            alert('⚠️ La contraseña debe tener al menos 6 caracteres');
            return;
        }
        
        if (password !== passwordConfirm) {
            alert('⚠️ Las contraseñas no coinciden');
            return;
        }
        
        const btn = document.getElementById('btn-confirm-reset');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Reseteando...';
        
        const response = await fetch(`/admin/users/${userId}/reset-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ new_password: password })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al resetear contraseña');
        }
        
        // Close modal
        bootstrap.Modal.getInstance(document.getElementById('resetPasswordModal')).hide();
        
        alert('✅ Contraseña reseteada correctamente');
        
    } catch (error) {
        console.error('Error resetting password:', error);
        alert('❌ Error: ' + error.message);
    } finally {
        const btn = document.getElementById('btn-confirm-reset');
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-key"></i> Resetear Contraseña';
    }
}

async function toggleUserStatus(userId, activate) {
    try {
        const user = allUsers.find(u => u.id === userId);
        if (!user) return;
        
        const action = activate ? 'activar' : 'desactivar';
        if (!confirm(`¿Estás seguro de ${action} a ${user.name}?`)) {
            return;
        }
        
        const response = await fetch(`/admin/users/${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ is_active: activate })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `Error al ${action} usuario`);
        }
        
        await loadUsers();
        alert(`✅ Usuario ${activate ? 'activado' : 'desactivado'} correctamente`);
        
    } catch (error) {
        console.error('Error toggling user status:', error);
        alert('❌ Error: ' + error.message);
    }
}

function applyFilters() {
    const roleFilter = document.getElementById('filter-role').value;
    const statusFilter = document.getElementById('filter-status').value;
    
    let filtered = [...allUsers];
    
    if (roleFilter) {
        filtered = filtered.filter(u => u.role === roleFilter);
    }
    
    if (statusFilter === 'active') {
        filtered = filtered.filter(u => u.is_active);
    } else if (statusFilter === 'inactive') {
        filtered = filtered.filter(u => !u.is_active);
    }
    
    renderUsers(filtered);
}

function resetFilters() {
    document.getElementById('filter-role').value = '';
    document.getElementById('filter-status').value = 'active';
    renderUsers(allUsers);
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}
