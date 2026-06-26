(function () {
  let scheduled = false;

  function refreshLucideIcons(root) {
    if (!window.lucide || typeof window.lucide.createIcons !== 'function') return;

    const scope = root && root.querySelectorAll ? root : document;
    const pendingIcons = scope.querySelectorAll('[data-lucide]:not(svg)');
    if (!pendingIcons.length) return;

    window.lucide.createIcons({
      attrs: {
        'stroke-width': 2,
        'aria-hidden': 'true'
      }
    });
  }

  function scheduleRefresh(root) {
    if (scheduled) return;
    scheduled = true;

    window.requestAnimationFrame(() => {
      scheduled = false;
      refreshLucideIcons(root);
    });
  }

  window.refreshLucideIcons = function () {
    scheduleRefresh(document);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => scheduleRefresh(document));
  } else {
    scheduleRefresh(document);
  }

  const observer = new MutationObserver((mutations) => {
    const hasNewLucidePlaceholder = mutations.some((mutation) =>
      Array.from(mutation.addedNodes).some((node) =>
        node.nodeType === 1 &&
        node.tagName !== 'svg' &&
        (node.matches?.('[data-lucide]:not(svg)') || node.querySelector?.('[data-lucide]:not(svg)'))
      )
    );

    if (hasNewLucidePlaceholder) scheduleRefresh(document);
  });

  observer.observe(document.documentElement, { childList: true, subtree: true });
})();
