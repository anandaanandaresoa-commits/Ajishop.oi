// Main JavaScript for AJSHOP Panel

// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Get token from localStorage
function getToken() {
    return localStorage.getItem('token');
}

// Check if user is authenticated
function isAuthenticated() {
    return localStorage.getItem('token') != null;
}

// Get current user info
function getCurrentUser() {
    const userJson = localStorage.getItem('user');
    return userJson ? JSON.parse(userJson) : null;
}

// Logout function
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}

// Setup axios interceptor for authorization
axios.interceptors.request.use(function(config) {
    const token = getToken();
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
}, function(error) {
    return Promise.reject(error);
});

// Handle 401 responses
axios.interceptors.response.use(function(response) {
    return response;
}, function(error) {
    if (error.response && error.response.status === 401) {
        logout();
    }
    return Promise.reject(error);
});

// Utility function to show alerts
function showAlert(message, type = 'info', duration = 5000) {
    const alertId = 'alert-' + Date.now();
    const alertHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" id="${alertId}" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const alertContainer = document.querySelector('.main-content') || document.body;
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = alertHTML;
    alertContainer.insertBefore(tempDiv.firstElementChild, alertContainer.firstChild);
    
    if (duration > 0) {
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) alert.remove();
        }, duration);
    }
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Format currency
function formatCurrency(value) {
    return new Intl.NumberFormat('id-ID', {
        style: 'currency',
        currency: 'IDR'
    }).format(value);
}

// Confirm dialog
function confirmAction(message) {
    return new Promise((resolve) => {
        const result = confirm(message);
        resolve(result);
    });
}

// Redirect to page with delay
function redirectTo(url, delay = 1500) {
    setTimeout(() => {
        window.location.href = url;
    }, delay);
}

// Export data to CSV
function exportToCSV(data, filename = 'export.csv') {
    let csv = '';
    
    if (data.length > 0) {
        // Headers
        const headers = Object.keys(data[0]);
        csv += headers.join(',') + '\n';
        
        // Data
        data.forEach(row => {
            const values = headers.map(header => {
                const value = row[header];
                return typeof value === 'string' && value.includes(',') ? `"${value}"` : value;
            });
            csv += values.join(',') + '\n';
        });
    }
    
    // Create download link
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Validate email
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Validate password strength
function validatePassword(password) {
    return password.length >= 6;
}

// Generate random string
function generateRandomString(length = 8) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize tooltips (Bootstrap 5)
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize popovers (Bootstrap 5)
function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Document ready
document.addEventListener('DOMContentLoaded', function() {
    // Check authentication status on protected pages
    const currentUser = getCurrentUser();
    if (currentUser) {
        // User is authenticated
        console.log('User logged in:', currentUser.username);
    }
    
    // Initialize Bootstrap components
    initializeTooltips();
    initializePopovers();
});

// Logout functionality
const logoutBtn = document.querySelector('[data-action="logout"]');
if (logoutBtn) {
    logoutBtn.addEventListener('click', function(e) {
        e.preventDefault();
        logout();
    });
}
