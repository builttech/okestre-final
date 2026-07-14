(function () {
  const STORAGE_KEY = 'gitide-theme';
  const VALID_PREFERENCES = new Set(['system', 'light', 'dark']);
  const mediaQuery = window.matchMedia ? window.matchMedia('(prefers-color-scheme: light)') : null;

  function getStoredPreference() {
    const stored = localStorage.getItem(STORAGE_KEY);
    return VALID_PREFERENCES.has(stored) ? stored : 'dark';
  }

  function resolveTheme(preference) {
    if (preference === 'system') {
      return mediaQuery && mediaQuery.matches ? 'light' : 'dark';
    }
    return preference === 'light' ? 'light' : 'dark';
  }

  function syncThemeButtons(preference) {
    document.querySelectorAll('[data-theme-choice]').forEach((button) => {
      const active = button.dataset.themeChoice === preference;
      button.classList.toggle('is-active', active);
      button.setAttribute('aria-pressed', active ? 'true' : 'false');
    });

    const label = document.getElementById('theme-toggle-label');
    const legacyButton = document.getElementById('btn-theme-toggle');
    const legacyIcon = legacyButton ? legacyButton.querySelector('i') : null;
    const effectiveTheme = document.documentElement.dataset.theme || 'dark';

    if (label) {
      label.textContent = preference === 'system'
        ? 'Sistema'
        : effectiveTheme === 'light'
          ? 'Claro'
          : 'Escuro';
    }

    if (legacyIcon) {
      legacyIcon.classList.toggle('fa-sun', effectiveTheme === 'light');
      legacyIcon.classList.toggle('fa-moon', effectiveTheme !== 'light');
    }
  }

  function applyTheme(preference, options = {}) {
    const nextPreference = VALID_PREFERENCES.has(preference) ? preference : 'dark';
    const effectiveTheme = resolveTheme(nextPreference);

    document.documentElement.dataset.themePreference = nextPreference;
    document.documentElement.dataset.theme = effectiveTheme;

    if (options.persist !== false) {
      localStorage.setItem(STORAGE_KEY, nextPreference);
    }

    syncThemeButtons(nextPreference);
    window.dispatchEvent(new CustomEvent('gitide:theme-changed', {
      detail: {
        preference: nextPreference,
        theme: effectiveTheme,
      },
    }));
  }

  function bindThemeControls() {
    document.addEventListener('click', (event) => {
      const button = event.target.closest('[data-theme-choice]');
      if (!button) return;
      event.preventDefault();
      applyTheme(button.dataset.themeChoice);
    });

    const legacyButton = document.getElementById('btn-theme-toggle');
    if (legacyButton) {
      legacyButton.addEventListener('click', () => {
        const current = document.documentElement.dataset.theme || 'dark';
        applyTheme(current === 'dark' ? 'light' : 'dark');
      });
    }

    if (mediaQuery) {
      const onSystemThemeChange = () => {
        if (getStoredPreference() === 'system') {
          applyTheme('system', { persist: false });
        }
      };

      if (typeof mediaQuery.addEventListener === 'function') {
        mediaQuery.addEventListener('change', onSystemThemeChange);
      } else if (typeof mediaQuery.addListener === 'function') {
        mediaQuery.addListener(onSystemThemeChange);
      }
    }

    window.addEventListener('gitide:projects-loaded', () => syncThemeButtons(getStoredPreference()));
  }

  function initThemeToggle() {
    applyTheme(getStoredPreference(), { persist: false });
    bindThemeControls();
  }

  window.gitideTheme = {
    apply: applyTheme,
    getPreference: getStoredPreference,
    getTheme: () => document.documentElement.dataset.theme || resolveTheme(getStoredPreference()),
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initThemeToggle);
  } else {
    initThemeToggle();
  }
})();
