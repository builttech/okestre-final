(function () {
  const READY_ATTR = 'data-gitide-select-ready';
  const EXCLUDED_IDS = new Set(['project-selector', 'git-branch-input']);

  function optionLabel(option) {
    return option ? (option.textContent || option.value || '').trim() : '';
  }

  function closeAll(except) {
    document.querySelectorAll('.gitide-select.is-open').forEach((node) => {
      if (node !== except) node.classList.remove('is-open');
      const trigger = node.querySelector('.gitide-select-trigger');
      if (trigger) trigger.setAttribute('aria-expanded', 'false');
    });
  }

  function getActiveOption(select) {
    const options = Array.from(select.options);
    return options.find((option) => option.value === select.value)
      || options.find((option) => option.selected)
      || options[0];
  }

  function enhance(select) {
    if (!select || select.multiple) return;
    if (select.getAttribute(READY_ATTR) === 'true') return;
    if (select.hasAttribute('data-no-native-select')) return;
    if (EXCLUDED_IDS.has(select.id)) return;

    select.setAttribute(READY_ATTR, 'true');
    select.classList.add('gitide-select-native');

    const root = document.createElement('div');
    root.className = 'gitide-select';
    root.innerHTML = `
      <button class="gitide-select-trigger" type="button" aria-haspopup="listbox" aria-expanded="false">
        <span class="gitide-select-value"></span>
        <i class="fa-solid fa-chevron-down gitide-select-icon" aria-hidden="true"></i>
      </button>
      <div class="gitide-select-menu" role="listbox"></div>
    `;

    select.insertAdjacentElement('afterend', root);

    const trigger = root.querySelector('.gitide-select-trigger');
    const value = root.querySelector('.gitide-select-value');
    const menu = root.querySelector('.gitide-select-menu');

    function sync() {
      const active = getActiveOption(select);
      value.textContent = optionLabel(active);
      render();
    }

    function render() {
      const activeValue = select.value;
      menu.innerHTML = '';

      Array.from(select.options).forEach((option) => {
        if (option.hidden) return;

        const label = optionLabel(option);
        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'gitide-select-option';
        item.setAttribute('role', 'option');
        item.setAttribute('aria-selected', option.value === activeValue ? 'true' : 'false');
        item.disabled = option.disabled;
        if (option.value === activeValue || option.selected) item.classList.add('is-selected');

        item.innerHTML = `
          <span>${label}</span>
          <i class="fa-solid fa-check gitide-select-check" aria-hidden="true"></i>
        `;

        item.addEventListener('click', () => {
          if (option.disabled) return;
          select.value = option.value;
          Array.from(select.options).forEach((opt) => { opt.selected = opt.value === option.value; });
          select.dispatchEvent(new Event('change', { bubbles: true }));
          closeAll();
          sync();
        });

        menu.appendChild(item);
      });
    }

    trigger.addEventListener('click', (event) => {
      event.stopPropagation();
      const willOpen = !root.classList.contains('is-open');
      closeAll(root);
      root.classList.toggle('is-open', willOpen);
      trigger.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
      render();
    });

    select.addEventListener('change', sync);

    const observer = new MutationObserver(sync);
    observer.observe(select, { childList: true, subtree: true, attributes: true, attributeFilter: ['selected', 'disabled'] });

    sync();
  }

  function init(root) {
    (root || document).querySelectorAll('select.select-input').forEach(enhance);
  }

  document.addEventListener('click', () => closeAll());
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeAll();
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => init(document));
  } else {
    init(document);
  }

  const pageObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === 1) init(node);
      });
    });
  });

  pageObserver.observe(document.documentElement, { childList: true, subtree: true });
})();
