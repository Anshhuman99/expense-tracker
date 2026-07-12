// main.js — global JavaScript for Spendly features

document.addEventListener("DOMContentLoaded", () => {
    // Theme toggle
    const themeToggle = document.getElementById("theme-toggle");
    const themeIcon = document.getElementById("theme-icon");

    if (themeToggle && themeIcon) {
        let currentTheme = "light";
        try {
            currentTheme = localStorage.getItem("spendly-theme");
            if (!currentTheme) {
                const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
                currentTheme = prefersDark ? "dark" : "light";
            }
        } catch (e) {
            console.warn("Storage access not allowed:", e);
        }

        themeIcon.textContent = currentTheme === "dark" ? "light_mode" : "dark_mode";
        themeToggle.setAttribute("aria-label", currentTheme === "dark" ? "Switch to light mode" : "Switch to dark mode");
        themeToggle.setAttribute("title", currentTheme === "dark" ? "Switch to light mode" : "Switch to dark mode");

        themeToggle.addEventListener("click", () => {
            const isDark = document.documentElement.getAttribute("data-theme") === "dark";
            const nextTheme = isDark ? "light" : "dark";
            if (nextTheme === "dark") {
                document.documentElement.setAttribute("data-theme", "dark");
            } else {
                document.documentElement.removeAttribute("data-theme");
            }
            
            try {
                localStorage.setItem("spendly-theme", nextTheme);
            } catch (e) {
                console.warn("Could not save theme preference:", e);
            }

            themeIcon.textContent = nextTheme === "dark" ? "light_mode" : "dark_mode";
            themeToggle.setAttribute("aria-label", nextTheme === "dark" ? "Switch to light mode" : "Switch to dark mode");
            themeToggle.setAttribute("title", nextTheme === "dark" ? "Switch to light mode" : "Switch to dark mode");
        });
    }

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
