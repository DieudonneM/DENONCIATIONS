/**
 * JavaScript principal - Plateforme de Dénonciation MEPT-RDC
 * Interactions globales + animations modernes (GSAP/ScrollTrigger)
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeFormValidation();
    initializeMessageAlerts();
    initializeCloseButtons();
    initializeNavigationMenu();
});

function initializeNavigationMenu() {
    const menuToggle = document.getElementById('menuToggle');
    const navMenu = document.getElementById('navMenu');

    if (!menuToggle || !navMenu) {
        return;
    }

    menuToggle.addEventListener('click', function() {
        navMenu.classList.toggle('active');
    });
}

/**
 * Validation des formulaires côté client
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            markFieldError(field, 'Ce champ est obligatoire');
            isValid = false;
        } else {
            clearFieldError(field);
        }
        
        // Validation spécifique par type
        if (field.type === 'email' && field.value) {
            if (!isValidEmail(field.value)) {
                markFieldError(field, 'Email invalide');
                isValid = false;
            }
        }
    });
    
    return isValid;
}

function isValidEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

function markFieldError(field, message) {
    field.classList.add('error');
    let errorMsg = field.parentElement.querySelector('.error-message');
    if (!errorMsg) {
        errorMsg = document.createElement('div');
        errorMsg.className = 'error-message';
        field.parentElement.appendChild(errorMsg);
    }
    errorMsg.textContent = message;
}

function clearFieldError(field) {
    field.classList.remove('error');
    const errorMsg = field.parentElement.querySelector('.error-message');
    if (errorMsg) {
        errorMsg.remove();
    }
}

function createButtonRipple(button, event) {
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const ripple = document.createElement('span');
    const left = event.clientX - rect.left - size / 2;
    const top = event.clientY - rect.top - size / 2;

    ripple.style.position = 'absolute';
    ripple.style.width = `${size}px`;
    ripple.style.height = `${size}px`;
    ripple.style.left = `${left}px`;
    ripple.style.top = `${top}px`;
    ripple.style.borderRadius = '999px';
    ripple.style.pointerEvents = 'none';
    ripple.style.background = 'rgba(255, 255, 255, 0.28)';
    ripple.style.transform = 'scale(0)';
    ripple.style.opacity = '1';

    if (getComputedStyle(button).position === 'static') {
        button.style.position = 'relative';
    }
    button.style.overflow = 'hidden';

    button.appendChild(ripple);

    gsap.to(ripple, {
        scale: 2.2,
        opacity: 0,
        duration: 0.55,
        ease: 'power2.out',
        onComplete: () => ripple.remove()
    });
}

/**
 * Fermeture automatique des messages d'alerte
 */
function initializeMessageAlerts() {
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(alert => {
        // Fermer après 5 secondes (sauf les erreurs)
        if (!alert.classList.contains('alert-error') && !alert.classList.contains('alert-danger')) {
            setTimeout(() => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            }, 5000);
        }
    });
}

/**
 * Boutons de fermeture
 */
function initializeCloseButtons() {
    const closeButtons = document.querySelectorAll('.close');
    
    closeButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            this.parentElement.style.display = 'none';
        });
    });
}

/**
 * Copier le code de suivi dans le presse-papiers
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Code copié dans le presse-papiers');
        }).catch(err => {
            console.error('Erreur lors de la copie:', err);
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

function fallbackCopyToClipboard(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    showNotification('Code copié');
}

/**
 * Afficher une notification
 */
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.textContent = message;
    
    const container = document.querySelector('.messages') || document.body;
    container.insertBefore(notification, container.firstChild);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

/**
 * Gestion de l'affichage conditionnel (anonymat)
 */
function toggleFieldVisibility(checkboxSelector, fieldsSelectors) {
    const checkbox = document.querySelector(checkboxSelector);
    
    if (checkbox) {
        checkbox.addEventListener('change', function() {
            fieldsSelectors.forEach(selector => {
                const field = document.querySelector(selector);
                if (field) {
                    field.parentElement.style.display = this.checked ? 'none' : 'block';
                }
            });
        });
    }
}

/**
 * Format de fichier validation
 */
function validateFileInput(inputElement, allowedExtensions = [], maxSizeInMB = 50) {
    inputElement.addEventListener('change', function() {
        const files = this.files;
        let validFiles = true;
        
        Array.from(files).forEach(file => {
            const fileExtension = file.name.split('.').pop().toLowerCase();
            const fileSizeMB = file.size / (1024 * 1024);
            
            if (allowedExtensions.length > 0 && !allowedExtensions.includes(fileExtension)) {
                showNotification(`Format ${fileExtension} non autorisé`, 'error');
                validFiles = false;
            }
            
            if (fileSizeMB > maxSizeInMB) {
                showNotification(`Le fichier ${file.name} dépasse ${maxSizeInMB}MB`, 'error');
                validFiles = false;
            }
        });
        
        if (!validFiles) {
            this.value = '';
        }
    });
}

/**
 * Animation au défilement
 */
/**
 * Utilitaires pour les formulaires
 */
const FormUtils = {
    // Récupérer les valeurs du formulaire
    getFormData: function(form) {
        const data = new FormData(form);
        return Object.fromEntries(data);
    },
    
    // Remplir les champs du formulaire
    populateForm: function(form, data) {
        Object.keys(data).forEach(key => {
            const field = form.elements[key];
            if (field) {
                field.value = data[key];
            }
        });
    },
    
    // Réinitialiser le formulaire
    resetForm: function(form) {
        form.reset();
        form.querySelectorAll('.error').forEach(el => {
            el.classList.remove('error');
        });
    },
    
    // Désactiver tous les champs
    disableFormFields: function(form, disabled = true) {
        form.querySelectorAll('input, textarea, select, button').forEach(field => {
            field.disabled = disabled;
        });
    }
};

/**
 * Utilitaires pour le tableau de bord
 */
const DashboardUtils = {
    // Mettre à jour les statistiques
    updateStats: function(statsContainer, data) {
        statsContainer.innerHTML = '';
        Object.keys(data).forEach(key => {
            const value = data[key];
            const stat = document.createElement('div');
            stat.className = 'stat-card';
            stat.innerHTML = `<span class="stat-label">${key}</span><span class="stat-value">${value}</span>`;
            statsContainer.appendChild(stat);
        });
    },
    
    // Filtrer les incidents
    filterIncidents: function(incidents, filter) {
        return incidents.filter(incident => {
            if (filter.statut && incident.statut !== filter.statut) return false;
            if (filter.search && !incident.code_suivi.includes(filter.search)) return false;
            return true;
        });
    }
};

/**
 * API Client simple
 */
const APIClient = {
    baseUrl: '/api',
    
    async get(endpoint) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`);
            if (!response.ok) throw new Error('Erreur API');
            return await response.json();
        } catch (error) {
            console.error('Erreur GET:', error);
            throw error;
        }
    },
    
    async post(endpoint, data) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error('Erreur API');
            return await response.json();
        } catch (error) {
            console.error('Erreur POST:', error);
            throw error;
        }
    },
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
};

/**
 * Export pour utilisation globale
 */
window.DenunciationApp = {
    copyToClipboard,
    showNotification,
    toggleFieldVisibility,
    validateFileInput,
    animateOnScroll,
    FormUtils,
    DashboardUtils,
    APIClient
};
