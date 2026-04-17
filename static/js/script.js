// Custom JavaScript for Hospital Management System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Counter animation for dashboard
    animateCounters();
    
    // Auto-refresh functionality
    setupAutoRefresh();
    
    // Form validation
    setupFormValidation();
});

// Counter animation
function animateCounters() {
    const counters = document.querySelectorAll('.counter');
    
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-target'));
        const duration = 2000; // 2 seconds
        const increment = target / (duration / 16); // 60 FPS
        let current = 0;
        
        const updateCounter = () => {
            current += increment;
            if (current < target) {
                counter.textContent = Math.ceil(current);
                requestAnimationFrame(updateCounter);
            } else {
                counter.textContent = target;
            }
        };
        
        updateCounter();
    });
}

// Auto-refresh dashboard data
function setupAutoRefresh() {
    const refreshInterval = 30000; // 30 seconds
    
    setInterval(() => {
        if (document.querySelector('.dashboard-stats')) {
            refreshDashboardStats();
        }
    }, refreshInterval);
}

// Refresh dashboard statistics
function refreshDashboardStats() {
    fetch('/api/dashboard-stats/')
        .then(response => response.json())
        .then(data => {
            updateStatCounters(data);
        })
        .catch(error => {
            console.error('Error refreshing stats:', error);
        });
}

// Update stat counters with new data
function updateStatCounters(data) {
    const counters = {
        'patients-count': data.total_patients,
        'doctors-count': data.total_doctors,
        'appointments-count': data.total_appointments,
        'today-appointments': data.today_appointments
    };
    
    Object.keys(counters).forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            animateCounter(element, counters[id]);
        }
    });
}

// Animate single counter
function animateCounter(element, target) {
    const start = parseInt(element.textContent);
    const duration = 1000;
    const increment = (target - start) / (duration / 16);
    let current = start;
    
    const updateCounter = () => {
        current += increment;
        if ((increment > 0 && current < target) || (increment < 0 && current > target)) {
            element.textContent = Math.ceil(current);
            requestAnimationFrame(updateCounter);
        } else {
            element.textContent = target;
        }
    };
    
    updateCounter();
}

// Form validation setup
function setupFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

// Show loading spinner
function showSpinner() {
    const spinnerHtml = `
        <div class="spinner-overlay">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', spinnerHtml);
}

// Hide loading spinner
function hideSpinner() {
    const spinner = document.querySelector('.spinner-overlay');
    if (spinner) {
        spinner.remove();
    }
}

// AJAX form submission
function submitFormAjax(form, successCallback) {
    showSpinner();
    
    fetch(form.action, {
        method: form.method,
        body: new FormData(form),
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        hideSpinner();
        if (data.success) {
            if (successCallback) {
                successCallback(data);
            }
            showAlert(data.message, 'success');
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        hideSpinner();
        showAlert('An error occurred. Please try again.', 'danger');
        console.error('Error:', error);
    });
}

// Show alert message
function showAlert(message, type) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const alertContainer = document.querySelector('.container');
    if (alertContainer) {
        alertContainer.insertAdjacentHTML('afterbegin', alertHtml);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = alertContainer.querySelector('.alert');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }
}

// Confirm action
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Print functionality
function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Print</title>
                    <style>
                        body { font-family: Arial, sans-serif; }
                        table { width: 100%; border-collapse: collapse; }
                        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                        th { background-color: #f2f2f2; }
                    </style>
                </head>
                <body>
                    ${element.innerHTML}
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }
}
