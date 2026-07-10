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

    // Mobile navigation toggle handler
    const navToggle = document.getElementById("nav-toggle");
    const navLinksMenu = document.getElementById("nav-links-menu");

    if (navToggle && navLinksMenu) {
        navToggle.addEventListener("click", () => {
            const isExpanded = navToggle.getAttribute("aria-expanded") === "true";
            navToggle.setAttribute("aria-expanded", !isExpanded);
            navLinksMenu.classList.toggle("open");
            const icon = navToggle.querySelector(".material-symbols-outlined");
            if (icon) {
                icon.textContent = isExpanded ? "menu" : "close";
            }
        });

        // Close menu when clicking outside of navbar
        document.addEventListener("click", (event) => {
            if (!navLinksMenu.classList.contains("open")) return;
            const isClickInside = navToggle.contains(event.target) || navLinksMenu.contains(event.target);
            if (!isClickInside) {
                navToggle.setAttribute("aria-expanded", "false");
                navLinksMenu.classList.remove("open");
                const icon = navToggle.querySelector(".material-symbols-outlined");
                if (icon) icon.textContent = "menu";
            }
        });

        // Close menu on Escape key press
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && navLinksMenu.classList.contains("open")) {
                navToggle.setAttribute("aria-expanded", "false");
                navLinksMenu.classList.remove("open");
                const icon = navToggle.querySelector(".material-symbols-outlined");
                if (icon) icon.textContent = "menu";
                navToggle.focus();
            }
        });
    }
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
