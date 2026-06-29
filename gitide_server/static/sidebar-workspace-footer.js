(function () {
  function moveWorkspaceSwitcherToTopbar() {
    const sidebar = document.querySelector('.sidebar');
    const projectSection = sidebar?.querySelector('.sidebar-section');
    const statusPanel = document.querySelector('.topbar .status-panel');

    if (!sidebar || !projectSection || !statusPanel || projectSection.dataset.topbarMounted === 'true') return;

    projectSection.dataset.topbarMounted = 'true';
    projectSection.classList.remove('sidebar-workspace-footer-section');
    projectSection.classList.add('topbar-workspace-section');
    statusPanel.insertBefore(projectSection, statusPanel.firstElementChild);

    if (typeof window.refreshLucideIcons === 'function') window.refreshLucideIcons();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', moveWorkspaceSwitcherToTopbar);
  } else {
    moveWorkspaceSwitcherToTopbar();
  }
})();
