// main.js — global JavaScript for Spendly features

document.addEventListener("DOMContentLoaded", () => {
    // Standard Toasts handling
    const toasts = document.querySelectorAll(".toast");
    toasts.forEach(toast => {
        // Auto-dismiss after 5 seconds
        const timerId = setTimeout(() => {
            dismissToast(toast);
        }, 5000);

        // Manual dismiss on close button click
        const closeBtn = toast.querySelector(".toast-close-btn");
        if (closeBtn) {
            closeBtn.addEventListener("click", () => {
                clearTimeout(timerId);
                dismissToast(toast);
            });
        }
    });
});

/**
 * Adds the exit animation class to a toast and removes it from the DOM
 * after the animation completes.
 * @param {HTMLElement} toast 
 */
function dismissToast(toast) {
    if (!toast) return;
    toast.classList.add("toast-exit");
    
    // Listen for the animationend event to clean up the DOM
    toast.addEventListener("animationend", function handler() {
        toast.remove();
        toast.removeEventListener("animationend", handler);
    });
}
