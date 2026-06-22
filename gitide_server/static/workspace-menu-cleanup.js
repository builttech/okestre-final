(function () {
  function cleanupSidebarSettings() {
    const buttons = Array.from(document.querySelectorAll('button, a, .nav-item'));

    buttons.forEach((element) => {
      const text = (element.textContent || '').trim();
      if (text === 'Configurações') {
        const sidebar = element.closest('.sidebar');
        if (sidebar) {
          element.style.display = 'none';
        }
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', cleanupSidebarSettings);
  } else {
    cleanupSidebarSettings();
  }
})();