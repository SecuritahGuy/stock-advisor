/**
 * Stock Advisor - Main JavaScript file
 * Contains common functionality used across the web application
 */

// Format large numbers with K/M/B suffixes
function formatNumber(num) {
    if (num === null || num === undefined) return '-';
    
    if (num >= 1000000000) {
        return (num / 1000000000).toFixed(1) + 'B';
    }
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// Format a decimal as a percentage
function formatPercent(decimal, digits = 2) {
    if (decimal === null || decimal === undefined) return '-';
    return (decimal * 100).toFixed(digits) + '%';
}

// Format a number as currency
function formatCurrency(number, digits = 2) {
    if (number === null || number === undefined) return '-';
    return '$' + number.toFixed(digits).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Show toast notification
function showToast(message, type = 'info') {
    // Check if the toast container exists
    let toastContainer = document.getElementById('toast-container');
    
    // Create it if it doesn't exist
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
        toastContainer.style.zIndex = 1050;
        document.body.appendChild(toastContainer);
    }
    
    // Create a unique ID for this toast
    const toastId = 'toast-' + Date.now();
    
    // Create the toast HTML
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add the toast to the container
    toastContainer.appendChild(toast);
    
    // Initialize and show the toast
    const toastInstance = new bootstrap.Toast(toast, {
        animation: true,
        autohide: true,
        delay: 5000
    });
    
    toastInstance.show();
    
    // Return the toast ID in case it's needed later
    return toastId;
}

// Load data with loading indicator
function loadData(url, elementId, renderFunction) {
    const element = document.getElementById(elementId);
    
    if (!element) {
        console.error(`Element with id ${elementId} not found`);
        return;
    }
    
    // Show loading indicator
    element.innerHTML = `
        <div class="text-center my-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading data...</p>
        </div>
    `;
    
    // Fetch data
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Render the data
            renderFunction(data, element);
        })
        .catch(error => {
            console.error('Error loading data:', error);
            element.innerHTML = `
                <div class="alert alert-danger my-3">
                    <i class="bi bi-exclamation-triangle-fill"></i> Error loading data: ${error.message}
                </div>
            `;
        });
}

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    // Add any global event listeners or initializations here
    
    // Example: Initialize all tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Activate current nav item based on URL
    const path = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === path) {
            link.classList.add('active');
        }
    });
});
