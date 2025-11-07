// Scripts personalizados para el sistema de control de acceso

// Auto-ocultar alertas después de 5 segundos
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Form enhancements
    enhanceForms();
    
    // Table enhancements
    enhanceTables();
    
    // Dashboard interactions
    initDashboard();
});

// Mejoras para formularios
function enhanceForms() {
    // Auto-focus en el primer campo de los formularios
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const firstInput = form.querySelector('input[type="text"], input[type="email"], input[type="password"]');
        if (firstInput && !firstInput.value) {
            firstInput.focus();
        }
    });

    // Validación en tiempo real para contraseñas
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        input.addEventListener('input', function() {
            validatePassword(this);
        });
    });

    // Confirmación para acciones destructivas
    const destructiveLinks = document.querySelectorAll('a[href*="estado"], a[href*="eliminar"]');
    destructiveLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const action = this.textContent.trim().toLowerCase();
            if (!confirm(`¿Está seguro que desea ${action} este registro?`)) {
                e.preventDefault();
            }
        });
    });
}

// Validación de contraseñas
function validatePassword(input) {
    const value = input.value;
    const feedback = document.getElementById(`${input.id}-feedback`) || createPasswordFeedback(input);
    
    if (value.length > 0 && value.length < 8) {
        feedback.textContent = 'La contraseña debe tener al menos 8 caracteres';
        feedback.className = 'form-text text-danger';
        input.classList.add('is-invalid');
    } else if (value.length >= 8) {
        feedback.textContent = 'Contraseña válida';
        feedback.className = 'form-text text-success';
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
    } else {
        feedback.textContent = 'Mínimo 8 caracteres';
        feedback.className = 'form-text text-muted';
        input.classList.remove('is-invalid', 'is-valid');
    }
}

function createPasswordFeedback(input) {
    const feedback = document.createElement('div');
    feedback.id = `${input.id}-feedback`;
    feedback.className = 'form-text text-muted';
    feedback.textContent = 'Mínimo 8 caracteres';
    input.parentNode.appendChild(feedback);
    return feedback;
}

// Mejoras para tablas
function enhanceTables() {
    // Ordenamiento de tablas
    const sortableHeaders = document.querySelectorAll('th[data-sort]');
    sortableHeaders.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            sortTable(this);
        });
    });

    // Búsqueda en tablas
    const searchInputs = document.querySelectorAll('input[data-search]');
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            filterTable(this);
        });
    });
}

// Funcionalidad de ordenamiento
function sortTable(header) {
    const table = header.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const columnIndex = Array.from(header.parentNode.children).indexOf(header);
    const isAscending = !header.classList.contains('asc');
    
    // Remover clases de ordenamiento de todos los headers
    table.querySelectorAll('th').forEach(th => {
        th.classList.remove('asc', 'desc');
    });
    
    // Ordenar filas
    rows.sort((a, b) => {
        const aValue = a.children[columnIndex].textContent.trim();
        const bValue = b.children[columnIndex].textContent.trim();
        
        let comparison = 0;
        if (aValue > bValue) comparison = 1;
        else if (aValue < bValue) comparison = -1;
        
        return isAscending ? comparison : -comparison;
    });
    
    // Reinsertar filas ordenadas
    rows.forEach(row => tbody.appendChild(row));
    
    // Actualizar clase del header
    header.classList.add(isAscending ? 'asc' : 'desc');
}

// Funcionalidad de filtrado
function filterTable(input) {
    const table = input.closest('.card').querySelector('table');
    const filterValue = input.value.toLowerCase();
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(filterValue) ? '' : 'none';
    });
}

// Interacciones del dashboard
function initDashboard() {
    // Actualizar estadísticas en tiempo real (cada 30 segundos)
    if (window.location.pathname === '/dashboard') {
        setInterval(updateDashboardStats, 30000);
    }
    
    // Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Actualizar estadísticas del dashboard
function updateDashboardStats() {
    fetch('/dashboard/stats')
        .then(response => response.json())
        .then(data => {
            updateStatCard('total_visitantes', data.total_visitantes);
            updateStatCard('accesos_hoy', data.accesos_hoy);
            updateStatCard('alertas_hoy', data.alertas_hoy);
            updateStatCard('total_usuarios', data.total_usuarios);
        })
        .catch(error => console.error('Error updating stats:', error));
}

function updateStatCard(statId, value) {
    const element = document.querySelector(`[data-stat="${statId}"]`);
    if (element) {
        // Animación de conteo
        animateCount(element, value);
    }
}

function animateCount(element, targetValue) {
    const currentValue = parseInt(element.textContent);
    if (currentValue === targetValue) return;
    
    const increment = targetValue > currentValue ? 1 : -1;
    let current = currentValue;
    
    const timer = setInterval(() => {
        current += increment;
        element.textContent = current;
        
        if (current === targetValue) {
            clearInterval(timer);
        }
    }, 50);
}

// Utilidades para fechas
function formatDate(dateString) {
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString('es-ES', options);
}

// Exportar funciones globalmente
window.SistemaControlAcceso = {
    formatDate,
    validatePassword,
    sortTable,
    filterTable
};

// Manejo de errores de conexión
window.addEventListener('online', function() {
    showConnectionStatus('Conexión restaurada', 'success');
});

window.addEventListener('offline', function() {
    showConnectionStatus('Sin conexión', 'warning');
});

function showConnectionStatus(message, type) {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);
    
    setTimeout(() => {
        alert.remove();
    }, 5000);
}