/* ═══════════════════════════════════════════════════════
   SmartRice AI – Main JavaScript
═══════════════════════════════════════════════════════ */

"use strict";

// ── Counter Animation ──────────────────────────────────
function animateCounters() {
  document.querySelectorAll('.counter').forEach(el => {
    const target = parseInt(el.dataset.target || el.textContent);
    if (isNaN(target)) return;
    let current = 0;
    const step = Math.ceil(target / 60);
    const timer = setInterval(() => {
      current += step;
      if (current >= target) { el.textContent = target; clearInterval(timer); return; }
      el.textContent = current;
    }, 16);
  });
}

// ── Intersection Observer for Animations ──────────────
function setupScrollAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animationPlayState = 'running';
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.animate-slide-up, .animate-fade-up').forEach(el => {
    el.style.animationPlayState = 'paused';
    observer.observe(el);
  });
}

// ── Navbar Scroll Effect ───────────────────────────────
function setupNavbarScroll() {
  const nav = document.getElementById('mainNav');
  if (!nav) return;
  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      nav.style.boxShadow = '0 4px 30px rgba(22,101,52,0.4)';
    } else {
      nav.style.boxShadow = '0 2px 20px rgba(22,101,52,0.3)';
    }
  }, { passive: true });
}

// ── Smooth Page Transitions ────────────────────────────
function setupPageTransitions() {
  document.querySelectorAll('a[href]').forEach(link => {
    if (link.target === '_blank' || link.href.startsWith('#') || link.href.startsWith('javascript')) return;
    link.addEventListener('click', function(e) {
      if (this.closest('form')) return;
      const body = document.body;
      body.style.opacity = '0.8';
      body.style.transition = 'opacity 0.2s ease';
    });
  });
  document.body.style.opacity = '1';
  document.body.style.transition = 'opacity 0.3s ease';
}

// ── Tooltip Init (Bootstrap) ──────────────────────────
function initTooltips() {
  const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipEls.forEach(el => new bootstrap.Tooltip(el));
}

// ── Image Preview Helpers ─────────────────────────────
function clearPreview() {
  const previewImg = document.getElementById('previewImg');
  const dropzoneInner = document.getElementById('dropzoneInner');
  const fileInput = document.getElementById('fileInput');
  if (previewImg) {
    previewImg.classList.add('d-none');
    previewImg.src = '';
  }
  if (dropzoneInner) dropzoneInner.classList.remove('d-none');
  if (fileInput) fileInput.value = '';
  const dropzone = document.getElementById('dropzone');
  if (dropzone) dropzone.classList.remove('has-preview');
}

// ── Notification Toast ─────────────────────────────────
function showToast(message, type = 'success') {
  const existing = document.getElementById('smartToast');
  if (existing) existing.remove();

  const bg = type === 'success' ? '#16a34a' : type === 'error' ? '#dc2626' : '#2563eb';
  const toast = document.createElement('div');
  toast.id = 'smartToast';
  toast.innerHTML = `
    <div style="
      position:fixed; bottom:1.5rem; right:1.5rem; z-index:9999;
      background:${bg}; color:#fff; padding:1rem 1.5rem;
      border-radius:12px; font-weight:600; font-size:0.9rem;
      box-shadow:0 8px 30px rgba(0,0,0,0.2); max-width:320px;
      animation: slideInRight 0.3s ease;
    ">
      ${message}
    </div>
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

// ── Number Input Range Hints ───────────────────────────
function addInputHints() {
  document.querySelectorAll('input[type="number"]').forEach(input => {
    const min = input.getAttribute('min');
    const max = input.getAttribute('max');
    if (min && max) {
      input.addEventListener('blur', function() {
        const val = parseFloat(this.value);
        if (!isNaN(val)) {
          if (val < parseFloat(min)) {
            this.style.borderColor = '#f97316';
            this.title = `Value below minimum (${min})`;
          } else if (val > parseFloat(max)) {
            this.style.borderColor = '#ef4444';
            this.title = `Value above maximum (${max})`;
          } else {
            this.style.borderColor = '';
            this.title = '';
          }
        }
      });
    }
  });
}

// ── Particle Background (Hero) ─────────────────────────
function createParticles() {
  const container = document.getElementById('particles');
  if (!container) return;
  for (let i = 0; i < 20; i++) {
    const p = document.createElement('div');
    const size = Math.random() * 6 + 3;
    const x = Math.random() * 100;
    const y = Math.random() * 100;
    const delay = Math.random() * 4;
    p.style.cssText = `
      position: absolute;
      width: ${size}px; height: ${size}px;
      left: ${x}%; top: ${y}%;
      background: rgba(255,255,255,${Math.random() * 0.15 + 0.05});
      border-radius: 50%;
      animation: pulse-ring ${3 + Math.random() * 4}s ease-in-out ${delay}s infinite;
      pointer-events: none;
    `;
    container.appendChild(p);
  }
}

// ── Active Nav Highlighting ────────────────────────────
function highlightActiveNav() {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-pill').forEach(link => {
    if (link.getAttribute('href') === path) {
      link.classList.add('active');
    }
  });
}

// ── DOMContentLoaded ──────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  animateCounters();
  setupScrollAnimations();
  setupNavbarScroll();
  setupPageTransitions();
  initTooltips();
  addInputHints();
  createParticles();
  highlightActiveNav();

  // Auto-dismiss alerts
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s ease';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 500);
    }, 5000);
  });
});