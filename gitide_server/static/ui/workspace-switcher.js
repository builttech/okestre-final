(function () {
  const SELECTOR_ID = 'project-selector';

  function optionLabel(option) {
    return option ? (option.textContent || option.value || '').trim() : 'Selecione um workspace';
  }

  function closeMenu(root) {
    if (!root) return;
    root.classList.remove('is-open', 'is-switching-org');
    const trigger = root.querySelector('.workspace-switcher-trigger');
    if (trigger) trigger.setAttribute('aria-expanded', 'false');
  }

  function refreshIcons() {
    if (typeof window.refreshLucideIcons === 'function') {
      window.refreshLucideIcons();
    }
  }

  function getTokenPreview() {
    const fullToken = document.getElementById('api-token-full-view')?.value || '';
    const previewToken = document.getElementById('api-token-preview')?.textContent || '';
    return (fullToken && !fullToken.includes('Carregando')) ? fullToken : previewToken;
  }

  function activateTab(tabId) {
    if (typeof window.gitideActivateTab === 'function') {
      window.gitideActivateTab(tabId);
      return;
    }

    const navButton = document.querySelector(`[data-tab="${tabId}"]`);
    if (navButton) {
      navButton.click();
      return;
    }

    document.querySelectorAll('.tab-pane').forEach((pane) => {
      pane.classList.toggle('active', pane.id === tabId);
    });

    const noProjectState = document.getElementById('no-project-state');
    if (noProjectState) noProjectState.classList.remove('active');
  }

  function buildWorkspaceSwitcher() {
    const select = document.getElementById(SELECTOR_ID);
    if (!select || select.dataset.workspaceSwitcherReady === 'true') return;

    select.dataset.workspaceSwitcherReady = 'true';
    select.classList.add('workspace-switcher-native');

    const root = document.createElement('div');
    root.className = 'workspace-switcher workspace-account-menu';

    root.innerHTML = `
      <button class="workspace-switcher-trigger" type="button" aria-haspopup="menu" aria-expanded="false">
        <span class="workspace-switcher-avatar" aria-hidden="true">GI</span>
        <span class="workspace-switcher-copy">
          <strong class="workspace-switcher-title">Selecione um workspace</strong>
          <span class="workspace-switcher-subtitle">Organization</span>
        </span>
        <i data-lucide="chevron-down" class="workspace-switcher-chevron" aria-hidden="true"></i>
      </button>
      <div class="workspace-switcher-menu workspace-account-popover" role="menu">
        <div class="workspace-account-mode-row" aria-label="Preferências rápidas">
          <button class="workspace-account-mode-btn is-active" type="button" title="Modo desktop"><i data-lucide="monitor"></i></button>
          <button class="workspace-account-mode-btn" type="button" title="Tema claro"><i data-lucide="sun"></i></button>
          <button class="workspace-account-mode-btn" type="button" title="Tema escuro"><i data-lucide="moon"></i></button>
        </div>

        <div class="workspace-account-divider"></div>

        <button class="workspace-account-org-row" type="button" role="menuitem" aria-expanded="false">
          <span class="workspace-switcher-avatar" aria-hidden="true">GI</span>
          <span class="workspace-switcher-copy">
            <strong class="workspace-account-org-title">Selecione um workspace</strong>
            <span>Organization</span>
          </span>
          <i data-lucide="chevron-right" class="workspace-account-chevron" aria-hidden="true"></i>
        </button>

        <div class="workspace-switcher-options workspace-account-org-submenu" role="listbox"></div>

        <div class="workspace-account-divider"></div>

        <button class="workspace-account-item" type="button" data-workspace-action="project-settings" role="menuitem">
          <i data-lucide="settings" aria-hidden="true"></i>
          <span>Configurações</span>
        </button>
        <button class="workspace-account-item" type="button" data-workspace-action="profile-settings" role="menuitem">
          <i data-lucide="circle-user-round" aria-hidden="true"></i>
          <span>Perfil</span>
        </button>

        <div class="workspace-account-divider"></div>

        <button class="workspace-account-item" type="button" data-workspace-action="copy-context" role="menuitem">
          <i data-lucide="copy" aria-hidden="true"></i>
          <span>Copy project context</span>
        </button>
        <button class="workspace-account-item" type="button" data-workspace-action="developer-docs" role="menuitem">
          <i data-lucide="book-open" aria-hidden="true"></i>
          <span>Developer docs</span>
        </button>
        <button class="workspace-account-item" type="button" data-workspace-action="terms" role="menuitem">
          <i data-lucide="file-text" aria-hidden="true"></i>
          <span>Terms & policies</span>
        </button>
        <button class="workspace-account-item" type="button" data-workspace-action="help" role="menuitem">
          <i data-lucide="life-buoy" aria-hidden="true"></i>
          <span>Help</span>
        </button>

        <div class="workspace-account-divider"></div>

        <button class="workspace-account-item workspace-account-item-danger" type="button" data-workspace-action="logout" role="menuitem">
          <i data-lucide="log-out" aria-hidden="true"></i>
          <span>Log out</span>
        </button>
      </div>
    `;

    select.insertAdjacentElement('afterend', root);

    const trigger = root.querySelector('.workspace-switcher-trigger');
    const title = root.querySelector('.workspace-switcher-title');
    const subtitle = root.querySelector('.workspace-switcher-subtitle');
    const avatar = root.querySelector('.workspace-switcher-avatar');
    const orgTitle = root.querySelector('.workspace-account-org-title');
    const orgRow = root.querySelector('.workspace-account-org-row');
    const optionsBox = root.querySelector('.workspace-switcher-options');
    const emailLabel = root.querySelector('#workspace-account-email');

    function initials(text) {
      const clean = (text || 'WO').replace(/[^a-z0-9\s-]/gi, '').trim();
      if (!clean) return 'WO';
      const parts = clean.split(/[\s-]+/).filter(Boolean);
      if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }

    function workspaceSubtitle(option) {
      if (!option || !option.value) return 'Organization';
      return option.dataset.subtitle || option.dataset.path || 'Organization';
    }

    function getActiveOption() {
      const options = Array.from(select.options);
      const valueMatch = options.find((option) => option.value && option.value === select.value);
      if (valueMatch) return valueMatch;

      const selectedMatch = options.find((option) => option.value && option.selected);
      if (selectedMatch) {
        select.value = selectedMatch.value;
        return selectedMatch;
      }

      return options.find((option) => option.value) || select.options[select.selectedIndex] || select.options[0];
    }

    function syncTitle() {
      const selected = getActiveOption();
      const text = optionLabel(selected);
      const detail = workspaceSubtitle(selected);
      title.textContent = text;
      subtitle.textContent = detail;
      orgTitle.textContent = text;
      avatar.textContent = initials(text);
      root.querySelector('.workspace-account-org-row .workspace-switcher-avatar').textContent = initials(text);
      if (emailLabel) emailLabel.textContent = getTokenPreview() || 'GitIDE Workspace';
    }

    function runCopyAction() {
      const legacyCopyButton = document.getElementById('btn-copy-project-gpt-info');
      if (legacyCopyButton) {
        legacyCopyButton.click();
        return;
      }

      const selected = getActiveOption();
      const text = optionLabel(selected);
      const value = selected?.value || '';
      const copyText = `Projeto ativo: ${text}\nID do projeto: ${value}`;
      navigator.clipboard?.writeText(copyText);
    }

    function renderOptions() {
      optionsBox.innerHTML = '';

      Array.from(select.options).forEach((option) => {
        if (!option.value) return;
        const text = optionLabel(option);
        const detail = workspaceSubtitle(option);

        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'workspace-switcher-option workspace-account-org-option';
        item.setAttribute('role', 'option');
        item.setAttribute('aria-selected', option.selected || option.value === select.value ? 'true' : 'false');
        if (option.selected || option.value === select.value) item.classList.add('is-selected');

        item.innerHTML = `
          <span class="workspace-switcher-avatar" aria-hidden="true">${initials(text)}</span>
          <span class="workspace-switcher-copy">
            <strong>${text}</strong>
            <span>${detail}</span>
          </span>
          <i data-lucide="check" class="workspace-switcher-check" aria-hidden="true"></i>
        `;

        item.addEventListener('click', (event) => {
          event.stopPropagation();
          select.value = option.value;
          Array.from(select.options).forEach((opt) => { opt.selected = opt.value === option.value; });
          select.dispatchEvent(new Event('change', { bubbles: true }));
          syncTitle();
          renderOptions();
          closeMenu(root);
        });

        optionsBox.appendChild(item);
      });

      if (!optionsBox.children.length) {
        const empty = document.createElement('div');
        empty.className = 'workspace-switcher-empty';
        empty.textContent = 'Nenhum workspace encontrado.';
        optionsBox.appendChild(empty);
      }

      const createButton = document.createElement('button');
      createButton.type = 'button';
      createButton.className = 'workspace-switcher-create workspace-account-org-create';
      createButton.innerHTML = '<i data-lucide="plus" aria-hidden="true"></i><span>Create workspace</span>';
      createButton.addEventListener('click', (event) => {
        event.stopPropagation();
        closeMenu(root);
        const addButton = document.getElementById('btn-new-project') || document.getElementById('btn-state-new-project');
        if (addButton) addButton.click();
      });
      optionsBox.appendChild(createButton);

      refreshIcons();
    }

    function openMenu() {
      document.querySelectorAll('.workspace-switcher.is-open').forEach((node) => {
        if (node !== root) closeMenu(node);
      });
      root.classList.add('is-open');
      trigger.setAttribute('aria-expanded', 'true');
      renderOptions();
      syncTitle();
    }

    trigger.addEventListener('click', (event) => {
      event.stopPropagation();
      root.classList.contains('is-open') ? closeMenu(root) : openMenu();
    });

    orgRow.addEventListener('click', (event) => {
      event.stopPropagation();
      root.classList.toggle('is-switching-org');
      orgRow.setAttribute('aria-expanded', root.classList.contains('is-switching-org') ? 'true' : 'false');
      renderOptions();
    });

    root.querySelectorAll('[data-workspace-action]').forEach((button) => {
      button.addEventListener('click', (event) => {
        event.stopPropagation();
        const action = button.dataset.workspaceAction;

        if (action === 'copy-context') {
          runCopyAction();
          closeMenu(root);
          return;
        }

        if (action === 'project-settings' || action === 'profile-settings') {
          closeMenu(root);
          activateTab('tab-settings');
          return;
        }

        if (action === 'developer-docs') {
          window.open('/openapi.json', '_blank', 'noopener,noreferrer');
          closeMenu(root);
          return;
        }

        if (action === 'terms' || action === 'help') {
          closeMenu(root);
          activateTab('tab-settings');
          return;
        }

        if (action === 'logout') {
          closeMenu(root);
        }
      });
    });

    select.addEventListener('change', () => {
      syncTitle();
      renderOptions();
    });

    const observer = new MutationObserver(() => {
      syncTitle();
      renderOptions();
    });
    observer.observe(select, { childList: true, subtree: true, attributes: true, attributeFilter: ['selected', 'disabled'] });

    document.addEventListener('click', (event) => {
      if (!root.contains(event.target)) closeMenu(root);
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeMenu(root);
    });

    syncTitle();
    renderOptions();
    refreshIcons();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', buildWorkspaceSwitcher);
  } else {
    buildWorkspaceSwitcher();
  }
})();
