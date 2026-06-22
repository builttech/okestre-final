(function () {
  const SELECTOR_ID = 'project-selector';

  function optionLabel(option) {
    return option ? (option.textContent || option.value || '').trim() : '-- Selecione um Projeto --';
  }

  function closeMenu(root) {
    if (!root) return;
    root.classList.remove('is-open');
    const trigger = root.querySelector('.workspace-switcher-trigger');
    if (trigger) trigger.setAttribute('aria-expanded', 'false');
  }

  function buildWorkspaceSwitcher() {
    const select = document.getElementById(SELECTOR_ID);
    if (!select || select.dataset.workspaceSwitcherReady === 'true') return;

    select.dataset.workspaceSwitcherReady = 'true';
    select.classList.add('workspace-switcher-native');

    const root = document.createElement('div');
    root.className = 'workspace-switcher';

    root.innerHTML = `
      <button class="workspace-switcher-trigger" type="button" aria-haspopup="listbox" aria-expanded="false">
        <span class="workspace-switcher-avatar" aria-hidden="true">GI</span>
        <span class="workspace-switcher-copy">
          <strong class="workspace-switcher-title">-- Selecione um Projeto --</strong>
          <span class="workspace-switcher-subtitle">Projeto ativo</span>
        </span>
        <i class="fa-solid fa-chevron-down workspace-switcher-chevron" aria-hidden="true"></i>
      </button>
      <div class="workspace-switcher-menu" role="listbox">
        <div class="workspace-switcher-search">
          <i class="fa-solid fa-magnifying-glass" aria-hidden="true"></i>
          <input type="text" placeholder="Buscar workspace..." autocomplete="off">
        </div>
        <div class="workspace-switcher-options"></div>
        <button class="workspace-switcher-create" type="button">
          <i class="fa-solid fa-plus" aria-hidden="true"></i>
          <span>Criar workspace</span>
        </button>
      </div>
    `;

    select.insertAdjacentElement('afterend', root);

    const trigger = root.querySelector('.workspace-switcher-trigger');
    const title = root.querySelector('.workspace-switcher-title');
    const avatar = root.querySelector('.workspace-switcher-avatar');
    const optionsBox = root.querySelector('.workspace-switcher-options');
    const searchInput = root.querySelector('.workspace-switcher-search input');
    const createButton = root.querySelector('.workspace-switcher-create');

    function initials(text) {
      const clean = (text || 'GI').replace(/[^a-z0-9\s-]/gi, '').trim();
      if (!clean) return 'GI';
      const parts = clean.split(/[\s-]+/).filter(Boolean);
      if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
      return (parts[0][0] + parts[1][0]).toUpperCase();
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
      title.textContent = text;
      avatar.textContent = initials(text);
    }

    function renderOptions(filterValue) {
      const filter = (filterValue || '').toLowerCase();
      optionsBox.innerHTML = '';

      Array.from(select.options).forEach((option) => {
        if (!option.value) return;
        const text = optionLabel(option);
        if (filter && !text.toLowerCase().includes(filter)) return;

        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'workspace-switcher-option';
        item.setAttribute('role', 'option');
        item.setAttribute('aria-selected', option.selected ? 'true' : 'false');
        if (option.selected || option.value === select.value) item.classList.add('is-selected');

        item.innerHTML = `
          <span class="workspace-switcher-avatar" aria-hidden="true">${initials(text)}</span>
          <span class="workspace-switcher-copy">
            <strong>${text}</strong>
            <span>Workspace</span>
          </span>
          <i class="fa-solid fa-check workspace-switcher-check" aria-hidden="true"></i>
        `;

        item.addEventListener('click', () => {
          select.value = option.value;
          Array.from(select.options).forEach((opt) => { opt.selected = opt.value === option.value; });
          select.dispatchEvent(new Event('change', { bubbles: true }));
          syncTitle();
          renderOptions(searchInput.value);
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
    }

    function openMenu() {
      document.querySelectorAll('.workspace-switcher.is-open').forEach((node) => {
        if (node !== root) closeMenu(node);
      });
      root.classList.add('is-open');
      trigger.setAttribute('aria-expanded', 'true');
      renderOptions(searchInput.value);
      window.setTimeout(() => searchInput.focus(), 0);
    }

    trigger.addEventListener('click', (event) => {
      event.stopPropagation();
      root.classList.contains('is-open') ? closeMenu(root) : openMenu();
    });

    searchInput.addEventListener('input', () => renderOptions(searchInput.value));

    createButton.addEventListener('click', () => {
      closeMenu(root);
      const addButton = document.getElementById('btn-new-project') || document.getElementById('btn-state-new-project');
      if (addButton) addButton.click();
    });

    select.addEventListener('change', () => {
      syncTitle();
      renderOptions(searchInput.value);
    });

    const observer = new MutationObserver(() => {
      syncTitle();
      renderOptions(searchInput.value);
    });
    observer.observe(select, { childList: true, subtree: true, attributes: true, attributeFilter: ['selected', 'disabled'] });

    document.addEventListener('click', (event) => {
      if (!root.contains(event.target)) closeMenu(root);
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeMenu(root);
    });

    window.setInterval(() => {
      syncTitle();
    }, 1000);

    syncTitle();
    renderOptions('');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', buildWorkspaceSwitcher);
  } else {
    buildWorkspaceSwitcher();
  }
})();
