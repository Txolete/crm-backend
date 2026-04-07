// accounts.js - Complete Accounts management

// ============================================================================
// GLOBAL STATE
// ============================================================================
let allAccounts = [];
let filteredAccounts = [];
let currentPage = 1;
const ITEMS_PER_PAGE = 20;
let currentSort = { field: 'name', direction: 'asc' };
let currentAccountId = null; // For tasks integration

// Config data
let customerTypes = [];
let regions = [];
let leadSources = [];
let stages = [];
let users = [];

// ============================================================================
// INITIALIZATION
// ============================================================================
document.addEventListener('DOMContentLoaded', async function() {
    console.log('[ACCOUNTS] Initializing...');
    
    // Load config data (wait for it to complete)
    await loadConfigData();
    
    // Load accounts
    await loadAccounts();
    
    // Setup event listeners
    setupEventListeners();
});

// ============================================================================
// LOAD DATA
// ============================================================================
async function loadConfigData() {
    console.log('[ACCOUNTS] Loading config data...');
    try {
        // Load customer types
        console.log('[ACCOUNTS] Fetching customer types...');
        const typesResp = await fetch('/config/customer-types');
        console.log('[ACCOUNTS] Customer types response:', typesResp.status);
        if (typesResp.ok) {
            const typesData = await typesResp.json();
            console.log('[ACCOUNTS] Customer types response data:', typesData);
            // Backend returns array directly, not {customer_types: [...]}
            customerTypes = Array.isArray(typesData) ? typesData : (typesData.customer_types || []);
            console.log('[ACCOUNTS] Loaded', customerTypes.length, 'customer types');
            populateCustomerTypesFilter();
        } else {
            console.error('[ACCOUNTS] Failed to load customer types:', typesResp.status);
        }
        
        // Load regions
        console.log('[ACCOUNTS] Fetching regions...');
        const regionsResp = await fetch('/config/regions');
        console.log('[ACCOUNTS] Regions response:', regionsResp.status);
        if (regionsResp.ok) {
            const regionsData = await regionsResp.json();
            console.log('[ACCOUNTS] Regions response data:', regionsData);
            // Backend returns array directly, not {regions: [...]}
            regions = Array.isArray(regionsData) ? regionsData : (regionsData.regions || []);
            console.log('[ACCOUNTS] Loaded', regions.length, 'regions');
            populateRegionsFilter();
        } else {
            console.error('[ACCOUNTS] Failed to load regions:', regionsResp.status);
        }
        
        // Load lead sources
        console.log('[ACCOUNTS] Fetching lead sources...');
        const sourcesResp = await fetch('/config/lead-sources');
        console.log('[ACCOUNTS] Lead sources response:', sourcesResp.status);
        if (sourcesResp.ok) {
            const sourcesData = await sourcesResp.json();
            console.log('[ACCOUNTS] Lead sources response data:', sourcesData);
            // Backend returns array directly, not {lead_sources: [...]}
            leadSources = Array.isArray(sourcesData) ? sourcesData : (sourcesData.lead_sources || []);
            console.log('[ACCOUNTS] Loaded', leadSources.length, 'lead sources');
        } else {
            console.error('[ACCOUNTS] Failed to load lead sources:', sourcesResp.status);
        }
        
        // Load stages
        console.log('[ACCOUNTS] Fetching stages...');
        const stagesResp = await fetch('/config/stages');
        console.log('[ACCOUNTS] Stages response:', stagesResp.status);
        if (stagesResp.ok) {
            const stagesData = await stagesResp.json();
            console.log('[ACCOUNTS] Stages response data:', stagesData);
            // Backend returns array directly, not {stages: [...]}
            stages = Array.isArray(stagesData) ? stagesData : (stagesData.stages || []);
            console.log('[ACCOUNTS] Loaded', stages.length, 'stages');
        } else {
            console.error('[ACCOUNTS] Failed to load stages:', stagesResp.status);
        }
        
        // Load users
        console.log('[ACCOUNTS] Fetching users...');
        const usersResp = await fetch('/admin/users');
        console.log('[ACCOUNTS] Users response:', usersResp.status);
        if (usersResp.ok) {
            const usersData = await usersResp.json();
            console.log('[ACCOUNTS] Users response data:', usersData);
            // Users endpoint might return {users: [...]} or array
            users = Array.isArray(usersData) ? usersData : (usersData.users || []);
            console.log('[ACCOUNTS] Loaded', users.length, 'users');
            populateOwnersFilter();
        } else {
            console.error('[ACCOUNTS] Failed to load users:', usersResp.status);
        }
        
        console.log('[ACCOUNTS] Config data loading complete');
    } catch (error) {
        console.error('[ACCOUNTS] Error loading config:', error);
    }
}

async function loadAccounts() {
    console.log('[ACCOUNTS] Loading accounts...');
    
    showLoading(true);
    
    try {
        const status = document.getElementById('filter-status').value;
        const url = `/accounts?status=${status}`;
        
        console.log(`[ACCOUNTS] Fetching: ${url}`);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        allAccounts = data.accounts || [];
        
        console.log(`[ACCOUNTS] Loaded ${allAccounts.length} accounts with status="${status}"`);
        
        // Get real breakdown from ALL accounts (not filtered)
        const breakdownResponse = await fetch('/accounts?status=all');
        if (breakdownResponse.ok) {
            const breakdownData = await breakdownResponse.json();
            const allAccountsForBreakdown = breakdownData.accounts || [];
            console.log(`[ACCOUNTS] Real breakdown (from BD):`, {
                total: allAccountsForBreakdown.length,
                active: allAccountsForBreakdown.filter(a => a.status === 'active').length,
                archived: allAccountsForBreakdown.filter(a => a.status === 'archived').length
            });
        }
        
        // Enrich accounts with display data
        enrichAccountsData();
        
        // Apply filters
        applyFilters();
        
        // Display
        displayAccounts();
        
        showLoading(false);
        
    } catch (error) {
        console.error('[ACCOUNTS] Error loading accounts:', error);
        showLoading(false);
        showToast('Error al cargar clientes', 'danger');
    }
}

function enrichAccountsData() {
    allAccounts.forEach(account => {
        // Customer type name
        if (account.customer_type_id) {
            const type = customerTypes.find(t => t.id === account.customer_type_id);
            account._customer_type_name = type ? type.name : account.customer_type_other_text || '-';
        } else {
            account._customer_type_name = account.customer_type_other_text || '-';
        }
        
        // Region name
        if (account.region_id) {
            const region = regions.find(r => r.id === account.region_id);
            account._region_name = region ? region.name : account.region_other_text || '-';
        } else {
            account._region_name = account.region_other_text || '-';
        }
        
        // Owner name
        if (account.owner_user_id) {
            const owner = users.find(u => u.id === account.owner_user_id);
            account._owner_name = owner ? owner.name : '-';
        } else {
            account._owner_name = '-';
        }
        
        // Format date
        if (account.updated_at) {
            const date = new Date(account.updated_at);
            account._formatted_date = date.toLocaleDateString('es-ES');
        } else {
            account._formatted_date = '-';
        }
    });
}

// ============================================================================
// FILTERS
// ============================================================================
function applyFilters() {
    const searchTerm = document.getElementById('filter-search').value.toLowerCase();
    const statusFilter = document.getElementById('filter-status').value;
    const typeFilter = document.getElementById('filter-customer-type').value;
    const regionFilter = document.getElementById('filter-region').value;
    const ownerFilter = document.getElementById('filter-owner').value;
    
    filteredAccounts = allAccounts.filter(account => {
        // Search
        if (searchTerm && !account.name.toLowerCase().includes(searchTerm)) {
            return false;
        }
        
        // Status
        if (statusFilter !== 'all' && account.status !== statusFilter) {
            return false;
        }
        
        // Customer type
        if (typeFilter && account.customer_type_id !== typeFilter) {
            return false;
        }
        
        // Region
        if (regionFilter && account.region_id !== regionFilter) {
            return false;
        }
        
        // Owner
        if (ownerFilter && account.owner_user_id !== ownerFilter) {
            return false;
        }
        
        return true;
    });
    
    console.log(`[ACCOUNTS] Filtered: ${filteredAccounts.length} of ${allAccounts.length}`);
    
    // Sort
    sortAccounts();
    
    // Reset to page 1
    currentPage = 1;
}

function sortAccounts() {
    const { field, direction } = currentSort;
    
    filteredAccounts.sort((a, b) => {
        let valA, valB;
        
        switch(field) {
            case 'name':
                valA = a.name || '';
                valB = b.name || '';
                break;
            case 'customer_type':
                valA = a._customer_type_name || '';
                valB = b._customer_type_name || '';
                break;
            case 'region':
                valA = a._region_name || '';
                valB = b._region_name || '';
                break;
            case 'owner':
                valA = a._owner_name || '';
                valB = b._owner_name || '';
                break;
            case 'updated_at':
                valA = a.updated_at || '';
                valB = b.updated_at || '';
                break;
            default:
                return 0;
        }
        
        if (valA < valB) return direction === 'asc' ? -1 : 1;
        if (valA > valB) return direction === 'asc' ? 1 : -1;
        return 0;
    });
}

// ============================================================================
// DISPLAY
// ============================================================================
function displayAccounts() {
    const tbody = document.getElementById('accounts-table-body');
    const loadingEl = document.getElementById('loading');
    const tableContent = document.getElementById('table-content');
    const emptyState = document.getElementById('empty-state');
    
    if (filteredAccounts.length === 0) {
        tbody.innerHTML = '';
        loadingEl.style.display = 'none';
        tableContent.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    
    // Calculate pagination
    const totalPages = Math.ceil(filteredAccounts.length / ITEMS_PER_PAGE);
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = Math.min(startIndex + ITEMS_PER_PAGE, filteredAccounts.length);
    const pageAccounts = filteredAccounts.slice(startIndex, endIndex);
    
    // Render rows
    tbody.innerHTML = pageAccounts.map(account => `
        <tr data-account-id="${account.id}">
            <td>
                <div class="account-name" onclick="viewAccountDetail('${account.id}')">
                    ${escapeHtml(account.name)}
                </div>
                ${account.website ? `<small class="text-muted"><i class="bi bi-globe"></i> ${escapeHtml(account.website)}</small>` : ''}
            </td>
            <td>
                <span class="badge bg-secondary">${escapeHtml(account._customer_type_name)}</span>
            </td>
            <td>${escapeHtml(account._region_name)}</td>
            <td>${escapeHtml(account._owner_name)}</td>
            <td class="text-center">
                <span class="badge bg-info">${account.opportunities_count || 0}</span>
            </td>
            <td class="text-center">
                <span class="badge bg-info">${account.contacts_count || 0}</span>
            </td>
            <td>
                <small class="text-muted">${account._formatted_date}</small>
            </td>
            <td class="text-center">
                <button class="btn btn-sm btn-outline-primary" onclick="viewAccountDetail('${account.id}')" title="Ver detalle">
                    <i class="bi bi-eye"></i>
                </button>
            </td>
        </tr>
    `).join('');
    
    // Update pagination info
    document.getElementById('showing-from').textContent = startIndex + 1;
    document.getElementById('showing-to').textContent = endIndex;
    document.getElementById('total-accounts').textContent = filteredAccounts.length;
    
    // Render pagination
    renderPagination(totalPages);
    
    // Update sort indicators
    updateSortIndicators();
    
    // Show table
    loadingEl.style.display = 'none';
    emptyState.style.display = 'none';
    tableContent.style.display = 'block';
}

function renderPagination(totalPages) {
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Previous button
    html += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage - 1}); return false;">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Page numbers
    const maxVisible = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    
    if (endPage - startPage < maxVisible - 1) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }
    
    if (startPage > 1) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(1); return false;">1</a></li>`;
        if (startPage > 2) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        html += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(${totalPages}); return false;">${totalPages}</a></li>`;
    }
    
    // Next button
    html += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage + 1}); return false;">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;
    
    pagination.innerHTML = html;
}

function updateSortIndicators() {
    // Remove all sorted classes
    document.querySelectorAll('th').forEach(th => {
        th.classList.remove('sorted-asc', 'sorted-desc');
    });
    
    // Add class to current sorted column
    const th = document.querySelector(`th[data-sort="${currentSort.field}"]`);
    if (th) {
        th.classList.add(currentSort.direction === 'asc' ? 'sorted-asc' : 'sorted-desc');
    }
}

function changePage(page) {
    const totalPages = Math.ceil(filteredAccounts.length / ITEMS_PER_PAGE);
    if (page < 1 || page > totalPages) return;
    
    currentPage = page;
    displayAccounts();
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ============================================================================
// POPULATE FILTERS
// ============================================================================
function populateCustomerTypesFilter() {
    const select = document.getElementById('filter-customer-type');
    const activeTypes = customerTypes.filter(t => t.is_active);
    
    activeTypes.forEach(type => {
        const option = document.createElement('option');
        option.value = type.id;
        option.textContent = type.name;
        select.appendChild(option);
    });
}

function populateRegionsFilter() {
    const select = document.getElementById('filter-region');
    const activeRegions = regions.filter(r => r.is_active);
    
    activeRegions.forEach(region => {
        const option = document.createElement('option');
        option.value = region.id;
        option.textContent = region.name;
        select.appendChild(option);
    });
}

function populateOwnersFilter() {
    const select = document.getElementById('filter-owner');
    const activeUsers = users.filter(u => u.is_active);
    
    activeUsers.forEach(user => {
        const option = document.createElement('option');
        option.value = user.id;
        option.textContent = user.name;
        select.appendChild(option);
    });
}

// ============================================================================
// EVENT LISTENERS
// ============================================================================
function setupEventListeners() {
    // Search input (debounced)
    let searchTimeout;
    document.getElementById('filter-search').addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            applyFilters();
            displayAccounts();
        }, 300);
    });
    
    // Status filter - RELOAD from server
    document.getElementById('filter-status').addEventListener('change', function() {
        console.log('[ACCOUNTS] Status filter changed, reloading from server...');
        loadAccounts(); // This reloads from server with new status
    });
    
    // Other filter selects - filter locally
    ['filter-customer-type', 'filter-region', 'filter-owner'].forEach(id => {
        document.getElementById(id).addEventListener('change', function() {
            applyFilters();
            displayAccounts();
        });
    });
    
    // Sort columns
    document.querySelectorAll('th[data-sort]').forEach(th => {
        th.addEventListener('click', function() {
            const field = this.getAttribute('data-sort');
            
            if (currentSort.field === field) {
                currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
            } else {
                currentSort.field = field;
                currentSort.direction = 'asc';
            }
            
            sortAccounts();
            displayAccounts();
        });
    });
    
    // New account button
    document.getElementById('btn-new-account').addEventListener('click', showCreateModal);
    
    // Detail modal buttons (register once on page load)
    const btnEdit = document.getElementById('btn-edit-account');
    const btnArchive = document.getElementById('btn-archive-account');
    
    if (btnEdit) {
        btnEdit.addEventListener('click', editAccountDetail);
    }
    
    if (btnArchive) {
        btnArchive.addEventListener('click', archiveAccount);
    }
    
    // Contact form submit
    const contactForm = document.getElementById('contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', handleContactFormSubmit);
    }
}

// ============================================================================
// MODAL FUNCTIONS
// ============================================================================

let currentAccountDetail = null;
let accountDetailModal = null;
let accountFormModal = null;
let currentEditingAccountId = null;

async function showCreateModal() {
    console.log('[ACCOUNTS] Opening create account modal');

    // Always reload config so changes in /config are reflected immediately
    await loadConfigData();
    
    // Initialize modal if not done
    if (!accountFormModal) {
        const modalEl = document.getElementById('accountFormModal');
        accountFormModal = new bootstrap.Modal(modalEl);
    }
    
    // Reset form
    document.getElementById('account-form').reset();
    document.getElementById('form-modal-title').textContent = 'Nuevo Cliente';
    document.getElementById('btn-save-account').innerHTML = '<i class="bi bi-save"></i> Crear';
    currentEditingAccountId = null;
    
    // Populate dropdowns
    console.log('[ACCOUNTS] Calling populateFormDropdowns...');
    populateFormDropdowns();
    
    // Verify dropdowns were populated
    const customerTypeOptions = document.getElementById('form-customer-type').options.length;
    const regionOptions = document.getElementById('form-region').options.length;
    const leadSourceOptions = document.getElementById('form-lead-source').options.length;
    const ownerOptions = document.getElementById('form-owner').options.length;
    
    console.log('[ACCOUNTS] Dropdown options count:', {
        customerType: customerTypeOptions,
        region: regionOptions,
        leadSource: leadSourceOptions,
        owner: ownerOptions
    });
    
    // Show modal
    accountFormModal.show();
}

async function editAccountDetail() {
    if (!currentAccountDetail) return;

    console.log('[ACCOUNTS] Opening edit modal for:', currentAccountDetail.id);

    // Always reload config so changes in /config are reflected immediately
    await loadConfigData();
    
    // Initialize modal if not done
    if (!accountFormModal) {
        const modalEl = document.getElementById('accountFormModal');
        accountFormModal = new bootstrap.Modal(modalEl);
    }
    
    // Set mode to edit
    document.getElementById('form-modal-title').textContent = 'Editar Cliente';
    document.getElementById('btn-save-account').innerHTML = '<i class="bi bi-save"></i> Guardar Cambios';
    currentEditingAccountId = currentAccountDetail.id;
    
    // Populate dropdowns first
    populateFormDropdowns();
    
    // Pre-fill form with current data
    document.getElementById('form-name').value = currentAccountDetail.name || '';
    document.getElementById('form-website').value = currentAccountDetail.website || '';
    document.getElementById('form-phone').value = currentAccountDetail.phone || '';
    document.getElementById('form-email').value = currentAccountDetail.email || '';
    document.getElementById('form-tax-id').value = currentAccountDetail.tax_id || '';
    document.getElementById('form-address').value = currentAccountDetail.address || '';
    document.getElementById('form-customer-type').value = currentAccountDetail.customer_type_id || '';
    document.getElementById('form-region').value = currentAccountDetail.region_id || '';
    document.getElementById('form-lead-source').value = currentAccountDetail.lead_source_id || '';
    document.getElementById('form-lead-source-detail').value = currentAccountDetail.lead_source_detail || '';
    document.getElementById('form-owner').value = currentAccountDetail.owner_user_id || '';
    document.getElementById('form-notes').value = currentAccountDetail.notes || '';
    
    // Close detail modal and show form modal
    if (accountDetailModal) {
        accountDetailModal.hide();
    }
    
    accountFormModal.show();
}

function populateFormDropdowns() {
    console.log('[ACCOUNTS] Populating form dropdowns...');
    console.log('[ACCOUNTS] Data available:', {
        customerTypes: customerTypes.length,
        regions: regions.length,
        leadSources: leadSources.length,
        users: users.length
    });
    
    // Customer types
    const customerTypeSelect = document.getElementById('form-customer-type');
    customerTypeSelect.innerHTML = '<option value="">Seleccionar...</option>';
    customerTypes.filter(t => t.is_active).forEach(type => {
        const option = document.createElement('option');
        option.value = type.id;
        option.textContent = type.name;
        customerTypeSelect.appendChild(option);
    });
    
    // Regions
    const regionSelect = document.getElementById('form-region');
    regionSelect.innerHTML = '<option value="">Seleccionar...</option>';
    regions.filter(r => r.is_active).forEach(region => {
        const option = document.createElement('option');
        option.value = region.id;
        option.textContent = region.name;
        regionSelect.appendChild(option);
    });
    
    // Lead sources
    const leadSourceSelect = document.getElementById('form-lead-source');
    leadSourceSelect.innerHTML = '<option value="">Seleccionar...</option>';
    leadSources.filter(s => s.is_active).forEach(source => {
        const option = document.createElement('option');
        option.value = source.id;
        option.textContent = source.name;
        leadSourceSelect.appendChild(option);
    });
    
    // Owners
    const ownerSelect = document.getElementById('form-owner');
    ownerSelect.innerHTML = '<option value="">Sin asignar</option>';
    users.filter(u => u.is_active).forEach(user => {
        const option = document.createElement('option');
        option.value = user.id;
        option.textContent = user.name;
        ownerSelect.appendChild(option);
    });
    
    console.log('[ACCOUNTS] Dropdowns populated');
}

// Helper function to normalize website URLs
function normalizeWebsite(url) {
    if (!url) return null;
    
    url = url.trim();
    if (!url) return null;
    
    // If already has protocol, return as is
    if (url.startsWith('http://') || url.startsWith('https://')) {
        return url;
    }
    
    // Add https:// prefix
    return 'https://' + url;
}

// Handle form submission
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('account-form');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Validate
            if (!form.checkValidity()) {
                e.stopPropagation();
                form.classList.add('was-validated');
                return;
            }
            
            // Get form data
            const formData = {
                name: document.getElementById('form-name').value.trim(),
                website: normalizeWebsite(document.getElementById('form-website').value.trim()),
                phone: document.getElementById('form-phone').value.trim() || null,
                email: document.getElementById('form-email').value.trim() || null,
                tax_id: document.getElementById('form-tax-id').value.trim() || null,
                address: document.getElementById('form-address').value.trim() || null,
                customer_type_id: document.getElementById('form-customer-type').value || null,
                region_id: document.getElementById('form-region').value || null,
                lead_source_id: document.getElementById('form-lead-source').value || null,
                lead_source_detail: document.getElementById('form-lead-source-detail').value.trim() || null,
                owner_user_id: document.getElementById('form-owner').value || null,
                notes: document.getElementById('form-notes').value.trim() || null
            };
            
            console.log('[ACCOUNTS] Submitting form:', currentEditingAccountId ? 'UPDATE' : 'CREATE', formData);
            
            // Disable button
            const btnSave = document.getElementById('btn-save-account');
            const originalHtml = btnSave.innerHTML;
            btnSave.disabled = true;
            btnSave.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Guardando...';
            
            try {
                let response;
                
                if (currentEditingAccountId) {
                    // UPDATE
                    response = await fetch(`/accounts/${currentEditingAccountId}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(formData)
                    });
                } else {
                    // CREATE
                    response = await fetch('/accounts', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(formData)
                    });
                }
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || `HTTP ${response.status}`);
                }
                
                const result = await response.json();
                console.log('[ACCOUNTS] Save successful:', result);
                
                // Save ID if editing (before resetting)
                const savedAccountId = currentEditingAccountId;
                
                // Show success message
                showToast(
                    savedAccountId ? 'Cliente actualizado correctamente' : 'Cliente creado correctamente',
                    'success'
                );
                
                // Close modal
                accountFormModal.hide();
                
                // Reset form
                form.reset();
                form.classList.remove('was-validated');
                currentEditingAccountId = null;
                
                // Reload list
                await loadAccounts();
                
                // If we were editing, reload the detail modal
                if (savedAccountId) {
                    await viewAccountDetail(savedAccountId);
                }
                
            } catch (error) {
                console.error('[ACCOUNTS] Error saving account:', error);
                showToast('Error al guardar cliente: ' + error.message, 'danger');
            } finally {
                btnSave.disabled = false;
                btnSave.innerHTML = originalHtml;
            }
        });
    }
});

async function viewAccountDetail(accountId) {
    console.log('[ACCOUNTS] View detail:', accountId);
    
    // Set current account ID for tasks integration
    currentAccountId = accountId;
    
    // Initialize modal if not done
    if (!accountDetailModal) {
        const modalEl = document.getElementById('accountDetailModal');
        accountDetailModal = new bootstrap.Modal(modalEl);
    }
    
    // Show modal with loading
    accountDetailModal.show();
    showDetailLoading(true);
    
    try {
        const response = await fetch(`/accounts/${accountId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        currentAccountDetail = await response.json();
        console.log('[ACCOUNTS] Account detail loaded:', currentAccountDetail);
        
        // Populate modal
        populateAccountDetail(currentAccountDetail);
        
        showDetailLoading(false);
        
    } catch (error) {
        console.error('[ACCOUNTS] Error loading account detail:', error);
        showToast('Error al cargar detalles del cliente', 'danger');
        accountDetailModal.hide();
    }
}

function populateAccountDetail(account) {
    // Title
    document.getElementById('detail-account-name').textContent = account.name || '-';
    
    // Basic info
    document.getElementById('detail-name').textContent = account.name || '-';
    
    const statusBadge = account.status === 'active' 
        ? '<span class="badge badge-active">Activo</span>'
        : '<span class="badge badge-archived">Archivado</span>';
    document.getElementById('detail-status').innerHTML = statusBadge;
    
    // Contact info
    document.getElementById('detail-website').innerHTML = account.website 
        ? `<a href="${escapeHtml(account.website)}" target="_blank" class="text-primary">
            <i class="bi bi-globe"></i> ${escapeHtml(account.website)}
           </a>`
        : '<span class="text-muted">-</span>';
    
    document.getElementById('detail-phone').innerHTML = account.phone 
        ? `<a href="tel:${escapeHtml(account.phone)}" class="text-primary">
            <i class="bi bi-telephone"></i> ${escapeHtml(account.phone)}
           </a>`
        : '<span class="text-muted">-</span>';
    
    document.getElementById('detail-email').innerHTML = account.email 
        ? `<a href="mailto:${escapeHtml(account.email)}" class="text-primary">
            <i class="bi bi-envelope"></i> ${escapeHtml(account.email)}
           </a>`
        : '<span class="text-muted">-</span>';
    
    document.getElementById('detail-tax-id').textContent = account.tax_id || '-';
    document.getElementById('detail-address').textContent = account.address || '-';
    
    // Classification
    const customerTypeName = getCustomerTypeName(account);
    const regionName = getRegionName(account);
    const leadSourceName = getLeadSourceName(account);
    const ownerName = getOwnerName(account);
    
    document.getElementById('detail-customer-type').innerHTML = customerTypeName 
        ? `<span class="badge bg-secondary">${escapeHtml(customerTypeName)}</span>`
        : '<span class="text-muted">-</span>';
    
    document.getElementById('detail-region').innerHTML = regionName 
        ? `<span class="badge bg-secondary">${escapeHtml(regionName)}</span>`
        : '<span class="text-muted">-</span>';
    
    document.getElementById('detail-lead-source').innerHTML = leadSourceName 
        ? `<span class="badge bg-secondary">${escapeHtml(leadSourceName)}</span>`
        : '<span class="text-muted">-</span>';
    
    document.getElementById('detail-owner').textContent = ownerName || '-';
    
    // Notes
    const notesSection = document.getElementById('detail-notes-section');
    if (account.notes) {
        notesSection.style.display = 'block';
        document.getElementById('detail-notes').textContent = account.notes;
    } else {
        notesSection.style.display = 'none';
    }
    
    // Stats
    document.getElementById('detail-opps-count').textContent = account.opportunities_count || 0;
    document.getElementById('detail-contacts-count').textContent = account.contacts_count || 0;
    
    const pipelineFormatted = new Intl.NumberFormat('es-ES', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(account.pipeline_total || 0);
    document.getElementById('detail-pipeline').textContent = pipelineFormatted;
    
    // Contacts
    populateContactsList(account.contacts || []);
    
    // Opportunities
    populateOpportunitiesList(account.opportunities || []);
    
    // Tasks (PASO 5)
    if (typeof loadAccountTasks === 'function') {
        loadAccountTasks(account.id);
    }
    
    // Setup "Ver en Kanban" button with account_id
    const btnViewKanban = document.getElementById('btn-view-in-kanban');
    if (btnViewKanban) {
        btnViewKanban.onclick = (e) => {
            e.preventDefault();
            window.location.href = `/dashboard#kanban&account=${account.id}`;
        };
    }
    
    // Update archive button
    const archiveBtn = document.getElementById('btn-archive-account');
    if (account.status === 'archived') {
        archiveBtn.innerHTML = '<i class="bi bi-arrow-counterclockwise"></i> Reactivar';
        archiveBtn.classList.remove('btn-danger');
        archiveBtn.classList.add('btn-success');
    } else {
        archiveBtn.innerHTML = '<i class="bi bi-archive"></i> Archivar';
        archiveBtn.classList.remove('btn-success');
        archiveBtn.classList.add('btn-danger');
    }
}

function populateContactsList(contacts) {
    const container = document.getElementById('detail-contacts-list');
    
    if (!contacts || contacts.length === 0) {
        container.innerHTML = '<p class="text-muted text-center py-3">No hay contactos</p>';
        return;
    }
    
    const html = contacts.map(contact => {
        const fullName = [contact.first_name, contact.last_name].filter(Boolean).join(' ') || 'Sin nombre';
        
        // Get role name from contact_role_id
        let roleName = '-';
        if (contact.contact_role_id) {
            const role = contactRoles.find(r => r.id === contact.contact_role_id);
            roleName = role ? role.name : contact.contact_role_id;
        }
        if (contact.contact_role_other_text) {
            roleName = contact.contact_role_other_text;
        }
        
        // Get channels
        const emails = (contact.channels || [])
            .filter(ch => ch.type === 'email')
            .map(ch => `
                <div class="small">
                    <i class="bi bi-envelope${ch.is_primary ? '-fill text-primary' : ''}"></i>
                    <a href="mailto:${escapeHtml(ch.value)}">${escapeHtml(ch.value)}</a>
                    ${ch.is_primary ? '<span class="badge bg-primary ms-1">Principal</span>' : ''}
                </div>
            `).join('');
        
        const phones = (contact.channels || [])
            .filter(ch => ch.type === 'phone')
            .map(ch => `
                <div class="small">
                    <i class="bi bi-telephone${ch.is_primary ? '-fill text-primary' : ''}"></i>
                    <a href="tel:${escapeHtml(ch.value)}">${escapeHtml(ch.value)}</a>
                    ${ch.is_primary ? '<span class="badge bg-primary ms-1">Principal</span>' : ''}
                </div>
            `).join('');
        
        return `
            <div class="card mb-2">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <div class="fw-bold">${escapeHtml(fullName)}</div>
                            <div class="small text-muted mb-2">
                                <i class="bi bi-person-badge"></i> ${escapeHtml(roleName)}
                            </div>
                            ${emails}
                            ${phones}
                        </div>
                        <div class="btn-group-vertical">
                            <button class="btn btn-sm btn-outline-secondary" onclick="editContact('${contact.id}')" title="Editar contacto">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteContact('${contact.id}')" title="Eliminar contacto">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = html;
}

function populateOpportunitiesList(opportunities) {
    const container = document.getElementById('detail-opportunities-list');
    
    if (!opportunities || opportunities.length === 0) {
        container.innerHTML = '<p class="text-muted text-center py-3">No hay oportunidades</p>';
        return;
    }
    
    const html = opportunities.map(opp => {
        const value = new Intl.NumberFormat('es-ES', {
            style: 'currency',
            currency: 'EUR',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(opp.expected_value_eur || 0);
        
        let statusBadge = '';
        if (opp.close_outcome === 'won') {
            statusBadge = '<span class="badge bg-success">Ganada</span>';
        } else if (opp.close_outcome === 'lost') {
            statusBadge = '<span class="badge bg-danger">Perdida</span>';
        } else {
            const stage = getStageById(opp.stage_id);
            statusBadge = `<span class="badge bg-info">${stage ? stage.name : 'Open'}</span>`;
        }
        
        return `
            <div class="card mb-2">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <div class="fw-bold">${escapeHtml(opp.name || 'Sin nombre')}</div>
                            <div class="small text-muted">
                                ${value} ${statusBadge}
                            </div>
                        </div>
                        <a href="/dashboard#kanban&opp=${opp.id}" class="btn btn-sm btn-outline-primary" title="Ver en Kanban">
                            <i class="bi bi-kanban"></i>
                        </a>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = html;
}

function showDetailLoading(show) {
    const loading = document.getElementById('detail-loading');
    const content = document.getElementById('detail-content');
    
    if (show) {
        loading.style.display = 'block';
        content.style.display = 'none';
    } else {
        loading.style.display = 'none';
        content.style.display = 'block';
    }
}

async function archiveAccount() {
    if (!currentAccountDetail) return;
    
    const isArchived = currentAccountDetail.status === 'archived';
    const action = isArchived ? 'reactivar' : 'archivar';
    const actionCaps = isArchived ? 'Reactivar' : 'Archivar';
    
    const confirmed = confirm(
        `¿${actionCaps} cliente "${currentAccountDetail.name}"?\n\n` +
        `Esto ${isArchived ? 'reactivará' : 'archivará'} el cliente ${isArchived ? 'y volverá a estar visible' : 'pero no borrará los datos'}.`
    );
    
    if (!confirmed) return;
    
    try {
        const newStatus = isArchived ? 'active' : 'archived';
        
        console.log(`[ACCOUNTS] Archiving account ${currentAccountDetail.id} to status: ${newStatus}`);
        
        const response = await fetch(`/accounts/${currentAccountDetail.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: newStatus })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`[ACCOUNTS] Archive failed: ${response.status}`, errorText);
            throw new Error(`HTTP ${response.status}`);
        }
        
        const updatedAccount = await response.json();
        console.log(`[ACCOUNTS] Account ${action}d successfully:`, updatedAccount);
        console.log(`[ACCOUNTS] New status in response: ${updatedAccount.status}`);
        
        showToast(
            `Cliente ${action}do correctamente`, 
            'success'
        );
        
        // Close modal
        accountDetailModal.hide();
        
        // Reload list
        console.log('[ACCOUNTS] Reloading accounts after archive...');
        await loadAccounts();
        console.log('[ACCOUNTS] Reload complete');
        
    } catch (error) {
        console.error(`[ACCOUNTS] Error ${action}ing account:`, error);
        showToast(`Error al ${action} cliente`, 'danger');
    }
}

// ============================================================================
// CONTACT MANAGEMENT
// ============================================================================

let contactFormModal = null;
let currentEditingContactId = null;
let emailFieldCounter = 0;
let phoneFieldCounter = 0;
let contactRoles = [];

async function loadContactRoles() {
    try {
        const resp = await fetch('/config/contact-roles', { credentials: 'include' });
        if (resp.ok) {
            const data = await resp.json();
            contactRoles = Array.isArray(data) ? data : (data.contact_roles || []);
        } else {
            console.warn('[ACCOUNTS] Failed to load contact roles:', resp.status);
        }
    } catch (e) {
        console.error('[ACCOUNTS] Error loading contact roles:', e);
    }
}

async function showAddContactModal() {
    if (!currentAccountDetail) {
        showToast('Error: No hay cliente seleccionado', 'danger');
        return;
    }
    
    console.log('[ACCOUNTS] Opening add contact modal');
    
    // Initialize modal if not done
    if (!contactFormModal) {
        const modalEl = document.getElementById('contactFormModal');
        contactFormModal = new bootstrap.Modal(modalEl);
    }
    
    // Reset form
    document.getElementById('contact-form').reset();
    document.getElementById('contact-form-modal-title').textContent = 'Nuevo Contacto';
    document.getElementById('btn-save-contact').innerHTML = '<i class="bi bi-save"></i> Crear';
    currentEditingContactId = null;
    
    // Reset counters and clear containers
    emailFieldCounter = 0;
    phoneFieldCounter = 0;
    document.getElementById('emails-container').innerHTML = '';
    document.getElementById('phones-container').innerHTML = '';
    
    // Add initial fields
    addEmailField();
    addPhoneField();
    
    // Load and populate contact roles
    await loadContactRoles();
    populateContactRoles();

    // Show modal
    contactFormModal.show();
}

async function editContact(contactId) {
    if (!currentAccountDetail) return;
    
    console.log('[ACCOUNTS] Opening edit contact modal for:', contactId);
    
    // Find contact
    const contact = currentAccountDetail.contacts.find(c => c.id === contactId);
    if (!contact) {
        showToast('Error: Contacto no encontrado', 'danger');
        return;
    }
    
    // Initialize modal
    if (!contactFormModal) {
        const modalEl = document.getElementById('contactFormModal');
        contactFormModal = new bootstrap.Modal(modalEl);
    }
    
    // Set edit mode
    document.getElementById('contact-form-modal-title').textContent = 'Editar Contacto';
    document.getElementById('btn-save-contact').innerHTML = '<i class="bi bi-save"></i> Guardar Cambios';
    currentEditingContactId = contactId;
    
    // Reset counters and clear containers
    emailFieldCounter = 0;
    phoneFieldCounter = 0;
    document.getElementById('emails-container').innerHTML = '';
    document.getElementById('phones-container').innerHTML = '';
    
    // Populate basic info
    document.getElementById('contact-first-name').value = contact.first_name || '';
    document.getElementById('contact-last-name').value = contact.last_name || '';
    
    // Load and populate contact roles
    await loadContactRoles();
    populateContactRoles();
    document.getElementById('contact-role').value = contact.contact_role_id || '';
    
    // Populate emails
    const emails = (contact.channels || []).filter(ch => ch.type === 'email');
    if (emails.length > 0) {
        emails.forEach(email => addEmailField(email.value, email.is_primary, email.id));
    } else {
        addEmailField();
    }
    
    // Populate phones
    const phones = (contact.channels || []).filter(ch => ch.type === 'phone');
    if (phones.length > 0) {
        phones.forEach(phone => addPhoneField(phone.value, phone.is_primary, phone.id));
    } else {
        addPhoneField();
    }
    
    // Close detail modal, show contact form
    if (accountDetailModal) {
        accountDetailModal.hide();
    }
    
    contactFormModal.show();
}

async function deleteContact(contactId) {
    if (!currentAccountDetail) {
        showToast('Error: No hay cliente seleccionado', 'danger');
        return;
    }
    
    // Find contact to get name for confirmation
    const contact = currentAccountDetail.contacts.find(c => c.id === contactId);
    if (!contact) {
        showToast('Error: Contacto no encontrado', 'danger');
        return;
    }
    
    const contactName = [contact.first_name, contact.last_name].filter(Boolean).join(' ') || 'este contacto';
    
    // Confirm deletion
    if (!confirm(`¿Estás seguro de que quieres eliminar a ${contactName}?`)) {
        return;
    }
    
    console.log('[ACCOUNTS] Deleting contact:', contactId);
    
    try {
        const response = await fetch(`/contacts/${contactId}/archive`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        
        console.log('[ACCOUNTS] Contact deleted successfully');
        
        // Show success message
        showToast('Contacto eliminado correctamente', 'success');
        
        // Reload account detail to show updated contacts list
        await viewAccountDetail(currentAccountDetail.id);
        
    } catch (error) {
        console.error('[ACCOUNTS] Error deleting contact:', error);
        showToast('Error al eliminar contacto: ' + error.message, 'danger');
    }
}

function populateContactRoles() {
    const roleSelect = document.getElementById('contact-role');
    roleSelect.innerHTML = '<option value="">Seleccionar...</option>';

    const activeRoles = contactRoles.filter(r => r.is_active !== false);
    activeRoles.forEach(role => {
        const option = document.createElement('option');
        option.value = role.id;
        option.textContent = role.name;
        roleSelect.appendChild(option);
    });
}

function addEmailField(value = '', isPrimary = false, channelId = null) {
    const container = document.getElementById('emails-container');
    const fieldId = `email-${emailFieldCounter++}`;
    
    const fieldHtml = `
        <div class="input-group mb-2" id="email-group-${fieldId}">
            <input type="email" class="form-control" id="${fieldId}" 
                   placeholder="email@ejemplo.com" value="${escapeHtml(value || '')}"
                   data-channel-id="${channelId || ''}"
                   data-type="email">
            <button class="btn btn-outline-secondary" type="button" 
                    onclick="togglePrimary('${fieldId}')" 
                    title="Marcar como principal">
                <i class="bi bi-star${isPrimary ? '-fill text-warning' : ''}"></i>
            </button>
            <button class="btn btn-outline-danger" type="button" 
                    onclick="removeChannelField('email-group-${fieldId}')" 
                    title="Eliminar">
                <i class="bi bi-trash"></i>
            </button>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', fieldHtml);
}

function addPhoneField(value = '', isPrimary = false, channelId = null) {
    const container = document.getElementById('phones-container');
    const fieldId = `phone-${phoneFieldCounter++}`;
    
    const fieldHtml = `
        <div class="input-group mb-2" id="phone-group-${fieldId}">
            <input type="tel" class="form-control" id="${fieldId}" 
                   placeholder="+34 ..." value="${escapeHtml(value || '')}"
                   data-channel-id="${channelId || ''}"
                   data-type="phone">
            <button class="btn btn-outline-secondary" type="button" 
                    onclick="togglePrimary('${fieldId}')" 
                    title="Marcar como principal">
                <i class="bi bi-star${isPrimary ? '-fill text-warning' : ''}"></i>
            </button>
            <button class="btn btn-outline-danger" type="button" 
                    onclick="removeChannelField('phone-group-${fieldId}')" 
                    title="Eliminar">
                <i class="bi bi-trash"></i>
            </button>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', fieldHtml);
}

function togglePrimary(fieldId) {
    const input = document.getElementById(fieldId);
    if (!input) return;
    
    const type = input.dataset.type;
    const container = type === 'email' ? 'emails-container' : 'phones-container';
    
    // Remove primary from all in this container
    const allStars = document.querySelectorAll(`#${container} .bi-star, #${container} .bi-star-fill`);
    allStars.forEach(star => {
        star.classList.remove('bi-star-fill', 'text-warning');
        star.classList.add('bi-star');
    });
    
    // Set this one as primary
    const button = document.querySelector(`button[onclick*="${fieldId}"]`);
    if (button) {
        const star = button.querySelector('i');
        if (star) {
            star.classList.remove('bi-star');
            star.classList.add('bi-star-fill', 'text-warning');
        }
    }
}

function removeChannelField(groupId) {
    const group = document.getElementById(groupId);
    if (group) {
        group.remove();
    }
}

// Handle contact form submission
async function handleContactFormSubmit(e) {
    e.preventDefault();
    
    if (!currentAccountDetail) {
        showToast('Error: No hay cliente seleccionado', 'danger');
        return;
    }
    
    // Gather form data
    const formData = {
        account_id: currentAccountDetail.id,
        first_name: document.getElementById('contact-first-name').value.trim() || null,
        last_name: document.getElementById('contact-last-name').value.trim() || null,
        contact_role_id: document.getElementById('contact-role').value || null,
        channels: []
    };
    
    // Gather emails
    const emailInputs = document.querySelectorAll('#emails-container input[type="email"]');
    emailInputs.forEach(input => {
        const value = input.value.trim();
        if (value) {
            // Find star icon in the same input-group
            const inputGroup = input.closest('.input-group');
            const starIcon = inputGroup ? inputGroup.querySelector('.bi-star, .bi-star-fill') : null;
            const isPrimary = starIcon && starIcon.classList.contains('bi-star-fill');
            
            formData.channels.push({
                type: 'email',
                value: value,
                is_primary: isPrimary || false
            });
        }
    });
    
    // Gather phones
    const phoneInputs = document.querySelectorAll('#phones-container input[type="tel"]');
    phoneInputs.forEach(input => {
        const value = input.value.trim();
        if (value) {
            // Find star icon in the same input-group
            const inputGroup = input.closest('.input-group');
            const starIcon = inputGroup ? inputGroup.querySelector('.bi-star, .bi-star-fill') : null;
            const isPrimary = starIcon && starIcon.classList.contains('bi-star-fill');
            
            formData.channels.push({
                type: 'phone',
                value: value,
                is_primary: isPrimary || false
            });
        }
    });
    
    console.log('[ACCOUNTS] Submitting contact:', currentEditingContactId ? 'UPDATE' : 'CREATE', formData);
    
    // Disable button
    const btnSave = document.getElementById('btn-save-contact');
    const originalHtml = btnSave.innerHTML;
    btnSave.disabled = true;
    btnSave.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Guardando...';
    
    try {
        let response;
        
        if (currentEditingContactId) {
            // UPDATE
            response = await fetch(`/contacts/${currentEditingContactId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
        } else {
            // CREATE
            response = await fetch('/contacts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        
        const result = await response.json();
        console.log('[ACCOUNTS] Contact saved:', result);
        
        showToast(
            currentEditingContactId ? 'Contacto actualizado correctamente' : 'Contacto creado correctamente',
            'success'
        );
        
        // Close modal
        contactFormModal.hide();
        
        // Reset
        currentEditingContactId = null;
        
        // Reload account detail
        await viewAccountDetail(currentAccountDetail.id);
        
    } catch (error) {
        console.error('[ACCOUNTS] Error saving contact:', error);
        showToast('Error al guardar contacto: ' + error.message, 'danger');
    } finally {
        btnSave.disabled = false;
        btnSave.innerHTML = originalHtml;
    }
}

// ============================================================================
// HELPER FUNCTIONS FOR DETAIL
// ============================================================================

function getCustomerTypeName(account) {
    if (account.customer_type_id) {
        const type = customerTypes.find(t => t.id === account.customer_type_id);
        return type ? type.name : account.customer_type_other_text;
    }
    return account.customer_type_other_text;
}

function getRegionName(account) {
    if (account.region_id) {
        const region = regions.find(r => r.id === account.region_id);
        return region ? region.name : account.region_other_text;
    }
    return account.region_other_text;
}

function getLeadSourceName(account) {
    if (account.lead_source_id) {
        const source = leadSources.find(s => s.id === account.lead_source_id);
        const sourceName = source ? source.name : null;
        if (account.lead_source_detail) {
            return sourceName ? `${sourceName} - ${account.lead_source_detail}` : account.lead_source_detail;
        }
        return sourceName;
    }
    return account.lead_source_detail;
}

function getOwnerName(account) {
    if (account.owner_user_id) {
        const owner = users.find(u => u.id === account.owner_user_id);
        return owner ? owner.name : null;
    }
    return null;
}

function getStageById(stageId) {
    return stages.find(s => s.id === stageId);
}

// ============================================================================
// UTILITIES
// ============================================================================
function showLoading(show) {
    const loading = document.getElementById('loading');
    const tableContent = document.getElementById('table-content');
    const emptyState = document.getElementById('empty-state');
    
    if (show) {
        loading.style.display = 'block';
        tableContent.style.display = 'none';
        emptyState.style.display = 'none';
    } else {
        loading.style.display = 'none';
    }
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    
    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'success' ? 'bg-success' : type === 'danger' ? 'bg-danger' : 'bg-info';
    
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${escapeHtml(message)}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================================
// PASO 5 - TASKS IN ACCOUNT
// ============================================================================

/**
 * Load tasks for account (direct + from opportunities)
 */
window.loadAccountTasks = async function(accountId) {
    console.log('[TASKS] Loading tasks for account:', accountId);
    
    const loadingDiv = document.getElementById('account-tasks-loading');
    const contentDiv = document.getElementById('account-tasks-content');
    const emptyDiv = document.getElementById('account-tasks-empty');
    
    loadingDiv.style.display = 'block';
    contentDiv.style.display = 'none';
    emptyDiv.style.display = 'none';
    
    try {
        const response = await fetch(`/tasks/account/${accountId}`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Error loading tasks');
        }
        
        const data = await response.json();
        const tasks = data.tasks || [];
        
        console.log('[TASKS] Tasks loaded:', tasks.length);
        
        // Update counter
        document.getElementById('account-tasks-count').textContent = tasks.length;
        
        // Count overdue tasks
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const overdueTasks = tasks.filter(t => {
            if (t.status === 'completed' || t.status === 'cancelled' || !t.due_date) return false;
            const due = new Date(t.due_date + 'T00:00:00');
            return due < today;
        });
        
        if (overdueTasks.length > 0) {
            document.getElementById('account-tasks-count').classList.add('bg-danger');
            document.getElementById('account-tasks-count').classList.remove('bg-primary');
        } else {
            document.getElementById('account-tasks-count').classList.add('bg-primary');
            document.getElementById('account-tasks-count').classList.remove('bg-danger');
        }
        
        if (tasks.length === 0) {
            loadingDiv.style.display = 'none';
            emptyDiv.style.display = 'block';
        } else {
            renderAccountTasks(tasks);
            loadingDiv.style.display = 'none';
            contentDiv.style.display = 'block';
        }
        
    } catch (error) {
        console.error('[TASKS] Error loading tasks:', error);
        loadingDiv.innerHTML = '<div class="alert alert-danger small">Error al cargar tareas</div>';
    }
}

/**
 * Render tasks for account
 */
function renderAccountTasks(tasks) {
    const contentDiv = document.getElementById('account-tasks-content');
    
    // Separate active and completed
    const activeTasks = tasks.filter(t => t.status !== 'completed' && t.status !== 'cancelled');
    const completedTasks = tasks.filter(t => t.status === 'completed' || t.status === 'cancelled');
    
    // Sort active by due date
    activeTasks.sort((a, b) => {
        if (!a.due_date) return 1;
        if (!b.due_date) return -1;
        return a.due_date.localeCompare(b.due_date);
    });
    
    let html = '';
    
    // Active tasks
    if (activeTasks.length > 0) {
        html += '<div class="mb-3">';
        html += '<small class="text-muted fw-bold">Pendientes (' + activeTasks.length + ')</small>';
        html += '<div class="list-group mt-2">';
        activeTasks.forEach(task => {
            html += renderAccountTaskCard(task);
        });
        html += '</div></div>';
    }
    
    // Completed tasks (collapsed)
    if (completedTasks.length > 0) {
        html += '<div class="mb-3">';
        html += '<small class="text-muted fw-bold">Completadas (' + completedTasks.length + ')</small>';
        html += '<div class="list-group mt-2" style="opacity: 0.6;">';
        completedTasks.slice(0, 3).forEach(task => {
            html += renderAccountTaskCard(task);
        });
        if (completedTasks.length > 3) {
            html += '<div class="list-group-item text-center small text-muted">... y ' + (completedTasks.length - 3) + ' más</div>';
        }
        html += '</div></div>';
    }
    
    contentDiv.innerHTML = html;
}

/**
 * Render single task card
 */
function renderAccountTaskCard(task) {
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
            dueClass = 'text-danger fw-bold';
            dueText = `⚠️ Vencida hace ${Math.abs(diffDays)} días`;
        } else if (diffDays === 0) {
            dueClass = 'text-warning fw-bold';
            dueText = '⚠️ Vence hoy';
        } else if (diffDays === 1) {
            dueClass = 'text-warning';
            dueText = 'Vence mañana';
        } else {
            dueText = `En ${diffDays} días`;
        }
    }
    
    // Template badge
    const templateBadge = task.task_template_name 
        ? `<span class="badge bg-info me-1"><i class="bi bi-tag"></i> ${escapeHtml(task.task_template_name)}</span>` 
        : '';
    
    // Opportunity badge (if task is from opportunity)
    const oppBadge = task.opportunity_name 
        ? `<span class="badge bg-primary me-1"><i class="bi bi-bullseye"></i> ${escapeHtml(task.opportunity_name)}</span>` 
        : '<span class="badge bg-secondary me-1"><i class="bi bi-folder"></i> Tarea directa</span>';
    
    return `
        <div class="list-group-item ${isCompleted ? 'opacity-50' : ''}">
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <div class="small fw-bold ${isCompleted ? 'text-decoration-line-through' : ''}">
                        ${statusIcon} ${priorityIcon} ${escapeHtml(task.title)}
                    </div>
                    <div class="small mt-1">
                        ${templateBadge}
                        ${oppBadge}
                        ${task.assigned_to_name ? `<span class="badge bg-secondary me-1"><i class="bi bi-person"></i> ${escapeHtml(task.assigned_to_name)}</span>` : ''}
                        ${task.due_date ? `<span class="badge bg-light text-dark me-1"><i class="bi bi-calendar"></i> ${task.due_date}</span>` : ''}
                        ${dueText ? `<span class="${dueClass} ms-1">${dueText}</span>` : ''}
                    </div>
                </div>
                <div class="ms-2">
                    ${!isCompleted ? `
                    <button class="btn btn-sm btn-outline-success" onclick="completeTaskFromAccount('${task.id}')" title="Completar">
                        <i class="bi bi-check-lg"></i>
                    </button>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

/**
 * Show create task modal with account pre-selected
 */
window.showCreateTaskFromAccount = async function() {
    if (!currentAccountId) {
        showToast('Error: No hay cliente seleccionado', 'danger');
        return;
    }
    
    // Use the tasks.js function and wait for options to load
    if (typeof showCreateTaskModal === 'function') {
        await showCreateTaskModal();
        
        // Now pre-select account (options are already loaded)
        const accountSelect = document.getElementById('task-account');
        if (accountSelect) {
            accountSelect.value = currentAccountId;
        }
    } else {
        showToast('Error: Función de tareas no disponible', 'danger');
    }
}

/**
 * Complete task from account
 */
window.completeTaskFromAccount = async function(taskId) {
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
        if (currentAccountId) {
            await loadAccountTasks(currentAccountId);
        }
        
    } catch (error) {
        console.error('[TASKS] Error completing task:', error);
        showToast('Error al completar tarea', 'danger');
    }
}

console.log('[ACCOUNTS] Script loaded successfully');
