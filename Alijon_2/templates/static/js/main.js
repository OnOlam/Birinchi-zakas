// ==================== GLOBAL FUNCTIONS ====================

// Real-time soat (footer)
function updateFooterTime() {
    const element = document.getElementById('current-time');
    if (element) {
        const now = new Date();
        const options = { 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit',
            day: '2-digit',
            month: 'long',
            year: 'numeric'
        };
        element.textContent = now.toLocaleString('uz-UZ', options);
    }
}

// Har soniyada yangilash
setInterval(updateFooterTime, 1000);
updateFooterTime();

// ==================== FORM VALIDATION ====================

// Bootstrap form validation
(function () {
    'use strict'
    
    const forms = document.querySelectorAll('.needs-validation')
    
    Array.from(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault()
                event.stopPropagation()
            }
            
            form.classList.add('was-validated')
        }, false)
    })
})()

// ==================== CONFIRM DIALOGS ====================

// O'chirish tasdiqlash
document.querySelectorAll('[data-confirm]').forEach(function(element) {
    element.addEventListener('click', function(e) {
        const message = this.getAttribute('data-confirm') || 'Ishonchingiz komilmi?';
        if (!confirm(message)) {
            e.preventDefault();
            return false;
        }
    });
});

// ==================== TOAST NOTIFICATIONS ====================

function showToast(message, type = 'info') {
    const toastHTML = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    const toastElement = toastContainer.lastElementChild;
    const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', function () {
        this.remove();
    });
}

// ==================== AUTO-SAVE INDICATOR ====================

let autoSaveTimeout = null;

function showSaveIndicator(status = 'saving') {
    let indicator = document.getElementById('save-indicator');
    
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'save-indicator';
        indicator.className = 'position-fixed bottom-0 end-0 m-3';
        document.body.appendChild(indicator);
    }
    
    if (status === 'saving') {
        indicator.innerHTML = `
            <div class="alert alert-info d-flex align-items-center" role="alert">
                <div class="spinner-border spinner-border-sm me-2" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                Saqlanmoqda...
            </div>
        `;
    } else if (status === 'saved') {
        indicator.innerHTML = `
            <div class="alert alert-success d-flex align-items-center" role="alert">
                <i class="bi bi-check-circle-fill me-2"></i>
                Saqlandi
            </div>
        `;
        
        setTimeout(() => {
            indicator.innerHTML = '';
        }, 2000);
    } else if (status === 'error') {
        indicator.innerHTML = `
            <div class="alert alert-danger d-flex align-items-center" role="alert">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                Xatolik!
            </div>
        `;
        
        setTimeout(() => {
            indicator.innerHTML = '';
        }, 3000);
    }
}

// ==================== LAZY LOADING ====================

document.addEventListener('DOMContentLoaded', function() {
    const lazyImages = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });
    
    lazyImages.forEach(img => imageObserver.observe(img));
});

// ==================== SMOOTH SCROLL ====================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            e.preventDefault();
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// ==================== KEYBOARD SHORTCUTS ====================

document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + S = Saqlash
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        const saveBtn = document.querySelector('button[type="submit"]');
        if (saveBtn) {
            saveBtn.click();
        }
    }
    
    // ESC = Modal yopish
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }
});

// ==================== AUTO LOGOUT (30 daqiqa faolsizlik) ====================

let inactivityTimer;
const INACTIVITY_TIMEOUT = 30 * 60 * 1000; // 30 daqiqa

function resetInactivityTimer() {
    clearTimeout(inactivityTimer);
    inactivityTimer = setTimeout(() => {
        if (confirm('Siz 30 daqiqa faolsiz edingiz. Tizimdan chiqmoqchimisiz?')) {
            window.location.href = '/logout';
        }
    }, INACTIVITY_TIMEOUT);
}

// Faollikni kuzatish
['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
    document.addEventListener(event, resetInactivityTimer, true);
});

resetInactivityTimer();

// ==================== TABLE SEARCH ====================

function searchTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    
    if (!input || !table) return;
    
    input.addEventListener('keyup', function() {
        const filter = this.value.toLowerCase();
        const rows = table.getElementsByTagName('tr');
        
        for (let i = 1; i < rows.length; i++) {
            const row = rows[i];
            const text = row.textContent.toLowerCase();
            
            if (text.includes(filter)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        }
    });
}

// ==================== COPY TO CLIPBOARD ====================

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Nusxa olindi!', 'success');
    }).catch(err => {
        console.error('Nusxa olishda xatolik:', err);
        showToast('Xatolik yuz berdi!', 'danger');
    });
}

// ==================== PAGE LOAD ANIMATIONS ====================

window.addEventListener('load', function() {
    document.body.classList.add('fade-in');
});

// ==================== CONSOLE WARNING ====================

console.log('%c⚠️ OGOHLANTIRISH!', 'color: red; font-size: 30px; font-weight: bold;');
console.log('%cAgar kimdir sizga bu yerga kod kiritishni aytsa, bu firibgarlik!', 'color: orange; font-size: 16px;');
console.log('%cBu konsoldan foydalanish sizning hisobingizga zarar yetkazishi mumkin.', 'color: orange; font-size: 16px;');

// ==================== ERROR HANDLER ====================

window.addEventListener('error', function(e) {
    console.error('JavaScript xatolik:', e.error);
    // Production da xatoliklarni serverga yuborish mumkin
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Promise xatolik:', e.reason);
});
