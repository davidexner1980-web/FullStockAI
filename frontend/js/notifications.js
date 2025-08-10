/**
 * Utility for displaying toast notifications.
 * @param {string} message - Message to display.
 * @param {'success'|'error'|'info'} [type='info'] - Type of toast.
 */
function createToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) {
        console.error('Toast container not found');
        return;
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    // Trigger show transition
    requestAnimationFrame(() => {
        toast.classList.add('show');
    });

    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        toast.addEventListener('transitionend', () => toast.remove(), { once: true });
    }, 5000);
}

window.createToast = createToast;
window.showNotification = createToast;

