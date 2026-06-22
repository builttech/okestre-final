(function () {
  function refreshLucideIcons() {
    if (!window.lucide || typeof window.lucide.createIcons !== 'function') return;
    window.lucide.createIcons({
      attrs: {
        'stroke-width': 2,
        'aria-hidden': 'true'
      }
    });
  }

  window.refreshLucideIcons = refreshLucideIcons;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', refreshLucideIcons);
  } else {
    refreshLucideIcons();
  }

  const observer = new MutationObserver((mutations) => {
    if (!mutations.some((mutation) => Array.from(mutation.addedNodes).some((node) => node.nodeType === 1 && (node.matches?.('[data-lucide]') || node.querySelector?.('[data-lucide]'))))) {
      return;
    }

    refreshLucideIcons();
  });

  observer.observe(document.documentElement, { childList: true, subtree: true });
})();
