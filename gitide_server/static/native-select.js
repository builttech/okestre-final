(function () {
  const ENHANCED_ATTR = 'data-gitide-select-enhanced';

  function getOptionLabel(option) {
    if (!option) return '';
    return option.textContent.trim() || option.value || '';
  }

  function closeAll(except) {
    document.querySelectorAll('.gitide-select.is-open').forEach((node) => {
      if (node !== except) node.classList.remove('is-open');
    });
  }

  function build(select) {
    if (!select || select.getAttribute(ENHANCED_ATTR) === 'true') return;
    if (select.multiple) return;

    select.setAttribute(ENHANCED_ATTR, 'true');
    select.classList.add('gitide-select-original');

    if (select.id === 'project-selector') {
      const bootValue = localStorage.getItem('selected_project_id') || localStorage.getItem('active_project_id');
      if (bootValue && !select.value) {
        select.value = bootValue;
      }
    }

    const wrapper = document.createElement('div');
    wrapper.className = 'gitide-select';

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'gitide-select-trigger';
    button.setAttribute('aria-haspopup', 'listbox');
    button.setAttribute('aria-expanded', 'false');

    const label = document.createElement('span');
    label.className = 'gitide-select-value';

    const icon = document.createElement('i');
    icon.className = 'fa-solid fa-chevron-down gitide-select-icon';
    icon.setAttribute('aria-hidden', 'true');

    const list = document.createElement('div');
    list.className = 'gitide-select-menu';
    list.setAttribute('role', 'listbox');

    button.append(label, icon);
    wrapper.append(button, list);
    select.insertAdjacentElement('afterend', wrapper);

    function ensureProjectSelection() {
      if (select.id !== 'project-selector') return false;
      if (select.value) return false;

      const storedKeys = [
        'selected_project_id',
        'active_project_id',
        'current_project_id',
        'gitide_active_project_id',
        'gitide_selected_project_id'
      ];

      const storedValue = storedKeys
        .map((key) => localStorage.getItem(key))
        .find(Boolean);

      const targetOption = storedValue
        ? Array.from(select.options).find((option) => option.value === storedValue)
        : Array.from(select.options).find((option) => option.value);

      if (!targetOption) return false;

      select.value = targetOption.value;
      Array.from(select.options).forEach((option) => {
        option.selected = option.value === targetOption.value;
      });
      select.dispatchEvent(new Event('change', { bubbles: true }));
      return true;
    }

    function render() {
      ensureProjectSelection();
      const selected = select.options[select.selectedIndex] || select.options[0];
      label.textContent = getOptionLabel(selected);
      list.innerHTML = '';

      Array.from(select.options).forEach((option) => {
        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'gitide-select-option';
        item.textContent = getOptionLabel(option);
        item.dataset.value = option.value;
        item.setAttribute('role', 'option');
        item.setAttribute('aria-selected', option.selected ? 'true' : 'false');
        if (option.disabled) item.disabled = true;
        if (option.selected) item.classList.add('is-selected');

        item.addEventListener('click', () => {
          if (option.disabled) return;
          select.value = option.value;
          Array.from(select.options).forEach((opt) => { opt.selected = opt.value === option.value; });
          select.dispatchEvent(new Event('change', { bubbles: true }));
          wrapper.classList.remove('is-open');
          render();
        });

        list.appendChild(item);
      });
    }

    button.addEventListener('click', (event) => {
      event.stopPropagation();
      const willOpen = !wrapper.classList.contains('is-open');
      closeAll(wrapper);
      wrapper.classList.toggle('is-open', willOpen);
      button.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
    });

    select.addEventListener('change', render);

    const observer = new MutationObserver(render);
    observer.observe(select, { childList: true, subtree: true, attributes: true, attributeFilter: ['selected', 'disabled', 'label'] });

    render();
  }

  function init(root) {
    (root || document).querySelectorAll('select.select-input:not([data-no-native-select])').forEach(build);
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
