(function () {
  const SELECT_ID = 'git-branch-input';

  function label(option) {
    return option ? (option.textContent || option.value || '').trim() : '';
  }

  function getActive(select) {
    const options = Array.from(select.options || []);
    return options.find((option) => option.value === select.value)
      || options.find((option) => option.selected)
      || options[0];
  }

  function build() {
    const select = document.getElementById(SELECT_ID);
    if (!select || select.dataset.gitBranchActionsReady === 'true') return;

    select.dataset.gitBranchActionsReady = 'true';
    select.classList.add('git-branch-select-native-hidden');

    const status = document.createElement('span');
    status.className = 'git-branch-status-pill';
    select.insertAdjacentElement('afterend', status);

    const list = document.createElement('div');
    list.className = 'git-branch-actions-list';
    status.insertAdjacentElement('afterend', list);

    function syncStatus() {
      const active = getActive(select);
      status.textContent = label(active) || 'Sem branch';
    }

    function render() {
      const activeValue = select.value;
      list.innerHTML = '';

      Array.from(select.options || []).forEach((option) => {
        if (!option.value) return;
        const text = label(option);
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'git-branch-action-btn';
        if (option.value === activeValue || option.selected) button.classList.add('is-active');
        button.innerHTML = `
          <i class="fa-solid fa-code-branch" aria-hidden="true"></i>
          <span>${text}</span>
          <i class="fa-solid fa-check git-branch-action-check" aria-hidden="true"></i>
        `;

        button.addEventListener('click', () => {
          select.value = option.value;
          Array.from(select.options || []).forEach((opt) => {
            opt.selected = opt.value === option.value;
          });
          select.dispatchEvent(new Event('change', { bubbles: true }));
          syncStatus();
          render();
        });

        list.appendChild(button);
      });

      syncStatus();
    }

    select.addEventListener('change', render);
    const observer = new MutationObserver(render);
    observer.observe(select, { childList: true, subtree: true, attributes: true, attributeFilter: ['selected', 'disabled'] });

    render();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }
})();
