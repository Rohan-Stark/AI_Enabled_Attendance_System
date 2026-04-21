/**
 * SmartAttend — Client-side JavaScript
 * Handles flash dismissal, form enhancements, and utility functions.
 */

document.addEventListener('DOMContentLoaded', () => {
    // ── Auto-dismiss flash messages after 5 seconds ───────
    document.querySelectorAll('.flash').forEach(flash => {
        setTimeout(() => {
            flash.style.opacity = '0';
            flash.style.transform = 'translateX(100px)';
            setTimeout(() => flash.remove(), 300);
        }, 5000);
    });

    // ── Confirm dangerous actions ─────────────────────────
    document.querySelectorAll('[data-confirm]').forEach(el => {
        el.addEventListener('click', e => {
            if (!confirm(el.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // ── Animate stat numbers on scroll ────────────────────
    const observerOptions = { threshold: 0.5 };
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.stat-card').forEach(card => {
        observer.observe(card);
    });

    // ── File input label ──────────────────────────────────
    document.querySelectorAll('.file-input').forEach(input => {
        input.addEventListener('change', () => {
            const fileName = input.files[0]?.name;
            if (fileName) {
                const hint = input.nextElementSibling;
                if (hint) hint.textContent = `Selected: ${fileName}`;
            }
        });
    });
});

/**
 * Format a number with commas.
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Show a temporary toast notification.
 */
function showToast(message, type = 'info') {
    const container = document.querySelector('.flash-container') ||
        (() => {
            const div = document.createElement('div');
            div.className = 'flash-container';
            document.body.appendChild(div);
            return div;
        })();

    const iconMap = {
        success: 'fa-check-circle',
        danger: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };

    const flash = document.createElement('div');
    flash.className = `flash flash-${type}`;
    flash.innerHTML = `
        <i class="fas ${iconMap[type] || iconMap.info}"></i>
        <span>${message}</span>
        <button class="flash-close" onclick="this.parentElement.remove()"><i class="fas fa-times"></i></button>
    `;
    container.appendChild(flash);

    setTimeout(() => {
        flash.style.opacity = '0';
        flash.style.transform = 'translateX(100px)';
        setTimeout(() => flash.remove(), 300);
    }, 5000);
}
