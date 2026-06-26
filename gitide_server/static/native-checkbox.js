(function () {
  const READY_ATTR = 'data-gitide-checkbox-ready';

  function sync(input, box) {
    box.classList.toggle('is-checked', input.checked);
    box.classList.toggle('is-disabled', input.disabled);
    box.setAttribute('aria-checked', input.checked ? 'true' : 'false');
    box.setAttribute('aria-disabled', input.disabled ? 'true' : 'false');
  }

  function enhance(input) {
    if (!input || input.type !== 'checkbox') return;
    if (input.getAttribute(READY_ATTR) === 'true') return;

    input.setAttribute(READY_ATTR, 'true');
    input.classList.add('gitide-checkbox-native');

    const box = document.createElement('span');
    box.className = 'gitide-checkbox';
    box.setAttribute('role', 'checkbox');
    box.setAttribute('tabindex', input.disabled ? '-1' : '0');
    box.innerHTML = '<i class="fa-solid fa-check" aria-hidden="true"></i>';

    input.insertAdjacentElement('afterend', box);

    box.addEventListener('click', function (event) {
      event.preventDefault();
      event.stopPropagation();
      if (input.disabled) return;
      input.checked = !input.checked;
      input.dispatchEvent(new Event('change', { bubbles: true }));
      sync(input, box);
    });

    box.addEventListener('keydown', function (event) {
      if (event.key !== ' ' && event.key !== 'Enter') return;
      event.preventDefault();
      box.click();
    });

    input.addEventListener('change', function () {
      sync(input, box);
    });

    const observer = new MutationObserver(function () {
      box.setAttribute('tabindex', input.disabled ? '-1' : '0');
      sync(input, box);
    });

    observer.observe(input, { attributes: true, attributeFilter: ['checked', 'disabled'] });
    sync(input, box);
  }

  function init(root) {
    (root || document).querySelectorAll('input[type="checkbox"]:not([data-no-native-checkbox])').forEach(enhance);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { init(document); });
  } else {
    init(document);
  }

  const pageObserver = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      mutation.addedNodes.forEach(function (node) {
        if (node.nodeType === 1) init(node);
      });
    });
  });

  pageObserver.observe(document.documentElement, { childList: true, subtree: true });
})();
