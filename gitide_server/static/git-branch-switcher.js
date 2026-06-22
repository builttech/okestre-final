(function () {
  const SELECTOR_ID = 'git-branch-input';

  function getLabel(option) {
    return option ? (option.textContent || option.value || '').trim() : 'Branch';
  }

  function close(root) {
    if (!root) return;
    root.classList.remove('is-open');
  }

  function build() {
    const select = document.getElementById(SELECTOR_ID);
    if (!select || select.dataset.branchSwitcherReady === 'true') return;

    select.dataset.branchSwitcherReady = 'true';
    select.classList.add('git-branch-native');

    const root = document.createElement('div');
    root.className = 'git-branch-switcher';
    root.innerHTML = `
      <button class="git-branch-trigger" type="button" aria-haspopup="listbox" aria-expanded="false">
        <i class="fa-solid fa-code-branch" aria-hidden="true"></i>
        <span class="git-branch-value">Branch</span>
        <i class="fa-solid fa-chevron-down git-branch-chevron" aria-hidden="true"></i>
      </button>
      <div class="git-branch-menu" role="listbox"></div>
    `;

    select.insertAdjacentElement('afterend', root);

    const trigger = root.querySelector('.git-branch-trigger');
    const value = root.querySelector('.git-branch-value');
    const menu = root.querySelector('.git-branch-menu');

    function getActiveOption() {
      const options = Array.from(select.options);
      return options.find((option) => option.value === select.value)
        || options.find((option) => option.selected)
        || options[0];
    }

    function sync() {
      const active = getActiveOption();
      value.textContent = getLabel(active);
      render();
    }

    function render() {
      const activeValue = select.value;
      menu.innerHTML = '';

      Array.from(select.options).forEach((option) => {
        if (!option.value && !getLabel(option)) return;

        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'git-branch-option';
        item.setAttribute('role', 'option');
        item.setAttribute('aria-selected', option.value === activeValue ? 'true' : 'false');
        if (option.value === activeValue) item.classList.add('is-selected');
        item.innerHTML = `
          <i class="fa-solid fa-code-branch" aria-hidden="true"></i>
          <span>${getLabel(option)}</span>
          <i class="fa-solid fa-check git-branch-check" aria-hidden="true"></i>
        `;

        item.addEventListener('click', () => {
          select.value = option.value;
          Array.from(select.options).forEach((opt) => { opt.selected = opt.value === option.value; });
          select.dispatchEvent(new Event('change', { bubbles: true }));
          sync();
          close(root);
        });

        menu.appendChild(item);
      });
    }

    trigger.addEventListener('click', (event) => {
      event.stopPropagation();
      const willOpen = !root.classList.contains('is-open');
      document.querySelectorAll('.git-branch-switcher.is-open').forEach(close);
      root.classList.toggle('is-open', willOpen);
      trigger.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
      render();
    });

    select.addEventListener('change', sync);

    const observer = new MutationObserver(sync);
    observer.observe(select, { childList: true, subtree: true, attributes: true, attributeFilter: ['selected', 'disabled'] });

    document.addEventListener('click', (event) => {
      if (!root.contains(event.target)) close(root);
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') close(root);
    });

    sync();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }
})();
