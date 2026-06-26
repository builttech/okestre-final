(function () {
  const ROOT_ID = 'git-status-detail';
  const READY_ATTR = 'data-git-status-actions-ready';

  function textOf(option) {
    return option ? (option.textContent || option.value || '').trim() : '';
  }

  function iconFor(label) {
    const key = (label || '').toLowerCase();
    if (key.includes('new') || key.includes('create')) return 'fa-plus';
    if (key.includes('refresh')) return 'fa-rotate';
    if (key.includes('pull')) return 'fa-code-pull-request';
    if (key.includes('merge')) return 'fa-code-merge';
    if (key.includes('request')) return 'fa-code-pull-request';
    return 'fa-code-branch';
  }

  function shouldEnhance(select) {
    if (!select || select.getAttribute(READY_ATTR) === 'true') return false;
    if (select.id === 'git-branch-input') return false;
    return Boolean(select.closest('#' + ROOT_ID));
  }

  function enhance(select) {
    if (!shouldEnhance(select)) return;

    select.setAttribute(READY_ATTR, 'true');
    select.classList.add('git-status-action-native');

    const selected = select.options[select.selectedIndex];
    const currentText = textOf(selected) || select.value || 'Branch';

    const pill = document.createElement('span');
    pill.className = 'git-status-branch-pill';
    pill.textContent = currentText;

    const actions = document.createElement('div');
    actions.className = 'git-status-actions-list';

    Array.from(select.options || []).forEach((option) => {
      const label = textOf(option);
      if (!label) return;

      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'git-status-action-btn';
      button.innerHTML = `<i class="fa-solid ${iconFor(label)}" aria-hidden="true"></i><span>${label}</span>`;

      button.addEventListener('click', () => {
        select.value = option.value;
        Array.from(select.options || []).forEach((opt) => {
          opt.selected = opt.value === option.value;
        });
        select.dispatchEvent(new Event('change', { bubbles: true }));
      });

      actions.appendChild(button);
    });

    select.insertAdjacentElement('afterend', pill);
    pill.insertAdjacentElement('afterend', actions);
  }

  function init() {
    const root = document.getElementById(ROOT_ID);
    if (!root) return;
    root.querySelectorAll('select').forEach(enhance);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  const observer = new MutationObserver(init);
  observer.observe(document.documentElement, { childList: true, subtree: true });
})();
