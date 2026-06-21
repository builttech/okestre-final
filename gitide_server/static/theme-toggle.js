(function () {
  const STORAGE_KEY = 'gitide-theme';

  function getPreferredTheme() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'dark' || stored === 'light') return stored;
    return document.documentElement.dataset.theme || 'dark';
  }

  function applyTheme(theme) {
    const nextTheme = theme === 'light' ? 'light' : 'dark';
    document.documentElement.dataset.theme = nextTheme;
    localStorage.setItem(STORAGE_KEY, nextTheme);

    const label = document.getElementById('theme-toggle-label');
    const button = document.getElementById('btn-theme-toggle');
    const icon = button ? button.querySelector('i') : null;

    if (label) label.textContent = nextTheme === 'light' ? 'Light' : 'Dark';
    if (icon) {
      icon.classList.toggle('fa-sun', nextTheme === 'light');
      icon.classList.toggle('fa-moon', nextTheme !== 'light');
    }
  }

  function initThemeToggle() {
    applyTheme(getPreferredTheme());

    const button = document.getElementById('btn-theme-toggle');
    if (!button) return;

    button.addEventListener('click', function () {
      const current = document.documentElement.dataset.theme || 'dark';
      applyTheme(current === 'dark' ? 'light' : 'dark');
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initThemeToggle);
  } else {
    initThemeToggle();
  }
})();
