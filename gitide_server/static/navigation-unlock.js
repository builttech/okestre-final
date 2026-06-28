(function () {
  function activateTab(tabId, sourceButton) {
    if (!tabId) return;

    document.querySelectorAll('.nav-item[data-tab]').forEach((button) => {
      button.classList.toggle('active', button === sourceButton || button.dataset.tab === tabId);
    });

    document.querySelectorAll('.tab-pane').forEach((pane) => {
      pane.classList.toggle('active', pane.id === tabId);
    });

    const noProjectState = document.getElementById('no-project-state');
    if (noProjectState) noProjectState.classList.remove('active');

    // Persist active tab and load its data
    if (typeof state !== 'undefined') {
      state.activeTab = tabId;
      localStorage.setItem('gitide_active_tab', tabId);
      
      if (state.activeProjectId && typeof window.switchTab === 'function') {
        window.switchTab(tabId);
      }
    } else if (typeof window.switchTab === 'function') {
      window.switchTab(tabId);
    }
  }

  function handleNavClick(event) {
    const button = event.target.closest?.('.nav-item[data-tab]');
    if (!button) return;

    const tabId = button.dataset.tab;
    const pane = document.getElementById(tabId);
    if (!pane) return;

    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();

    activateTab(tabId, button);
  }

  document.addEventListener('click', handleNavClick, true);

  window.gitideActivateTab = activateTab;
})();
