(function () {
  function moveWorkspaceSwitcherToFooter() {
    const sidebar = document.querySelector('.sidebar');
    const projectSection = sidebar?.querySelector('.sidebar-section');
    const footer = sidebar?.querySelector('.sidebar-footer');

    if (!sidebar || !projectSection || !footer || projectSection.dataset.footerMounted === 'true') return;

    projectSection.dataset.footerMounted = 'true';
    projectSection.classList.add('sidebar-workspace-footer-section');
    footer.insertBefore(projectSection, footer.firstElementChild);

    if (typeof window.refreshLucideIcons === 'function') window.refreshLucideIcons();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', moveWorkspaceSwitcherToFooter);
  } else {
    moveWorkspaceSwitcherToFooter();
  }
})();
