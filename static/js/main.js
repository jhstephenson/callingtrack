// CallingTrack Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (alert && alert.classList.contains('show')) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });

    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('a[href*="delete"], button[data-action="delete"]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
                return false;
            }
        });
    });

    // Enhanced search functionality
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(function() {
                // Auto-submit search after user stops typing for 500ms
                const form = searchInput.closest('form');
                if (form && searchInput.value.length >= 3) {
                    // Only auto-submit for longer queries
                    // For shorter queries, user needs to press Enter or click search
                }
            }, 500);
        });
    }

    // Status filter buttons
    const filterButtons = document.querySelectorAll('.status-filter-btn');
    filterButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            filterButtons.forEach(btn => btn.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
        });
    });

    // Table sorting functionality
    const sortableHeaders = document.querySelectorAll('th[data-sort]');
    sortableHeaders.forEach(function(header) {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            const sortField = this.dataset.sort;
            const currentUrl = new URL(window.location);
            const currentSort = currentUrl.searchParams.get('sort');
            const currentOrder = currentUrl.searchParams.get('order');
            
            let newOrder = 'asc';
            if (currentSort === sortField && currentOrder === 'asc') {
                newOrder = 'desc';
            }
            
            currentUrl.searchParams.set('sort', sortField);
            currentUrl.searchParams.set('order', newOrder);
            window.location.href = currentUrl.toString();
        });
    });

    // Quick status update buttons
    const statusUpdateButtons = document.querySelectorAll('[data-action="update-status"]');
    statusUpdateButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            const action = this.dataset.action;
            const callingId = this.dataset.callingId;
            const newStatus = this.dataset.status;
            
            if (confirm(`Are you sure you want to update the status to "${this.textContent.trim()}"?`)) {
                // Create form and submit
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = `/callings/callings/${callingId}/update-status/${newStatus}/`;
                
                // Add CSRF token
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
                if (csrfToken) {
                    const csrfInput = document.createElement('input');
                    csrfInput.type = 'hidden';
                    csrfInput.name = 'csrfmiddlewaretoken';
                    csrfInput.value = csrfToken.value;
                    form.appendChild(csrfInput);
                }
                
                document.body.appendChild(form);
                form.submit();
            }
        });
    });

    // Initialize tooltips if Bootstrap tooltips are available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Initialize popovers if Bootstrap popovers are available
    if (typeof bootstrap !== 'undefined' && bootstrap.Popover) {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }

    // Form validation helpers
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Date validation for calling forms
    const dateInputs = {
        called: document.querySelector('input[name="date_called"]'),
        sustained: document.querySelector('input[name="date_sustained"]'),
        setApart: document.querySelector('input[name="date_set_apart"]'),
        released: document.querySelector('input[name="date_released"]')
    };

    function validateDateOrder() {
        const dates = {};
        Object.keys(dateInputs).forEach(key => {
            if (dateInputs[key] && dateInputs[key].value) {
                dates[key] = new Date(dateInputs[key].value);
            }
        });

        // Clear previous custom validity
        Object.values(dateInputs).forEach(input => {
            if (input) input.setCustomValidity('');
        });

        // Validate date order
        if (dates.called && dates.sustained && dates.sustained < dates.called) {
            dateInputs.sustained.setCustomValidity('Sustained date cannot be before called date');
        }

        if (dates.sustained && dates.setApart && dates.setApart < dates.sustained) {
            dateInputs.setApart.setCustomValidity('Set apart date cannot be before sustained date');
        }
    }

    // Add event listeners for date validation
    Object.values(dateInputs).forEach(input => {
        if (input) {
            input.addEventListener('change', validateDateOrder);
        }
    });

    // Console welcome message for developers
    console.log('%cCallingTrack', 'font-size: 20px; font-weight: bold; color: #0d6efd;');
    console.log('Church Leadership Calling Management System');
    console.log('Built with Django and Bootstrap');
});

// Utility functions
window.CallingTrack = {
    
    // Format dates consistently
    formatDate: function(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },

    // Show loading spinner
    showLoading: function(element) {
        if (element) {
            element.innerHTML = '<div class="spinner-border spinner-border-sm me-2" role="status"><span class="visually-hidden">Loading...</span></div>Loading...';
            element.disabled = true;
        }
    },

    // Hide loading spinner
    hideLoading: function(element, originalText) {
        if (element) {
            element.innerHTML = originalText || element.dataset.originalText || 'Submit';
            element.disabled = false;
        }
    },

    // Show toast notification
    showToast: function(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-dismiss after 3 seconds
        setTimeout(() => {
            if (toast && toast.parentNode) {
                toast.remove();
            }
        }, 3000);
    }
};
