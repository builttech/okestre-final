/* Presentation-only navigation; existing tab buttons retain their handlers. */
(() => {
  function mount() {
    const sidebar = document.querySelector('.sidebar');
    const layout = document.querySelector('.main-layout');
    const nav = sidebar?.querySelector('.sidebar-nav');
    if (!nav || !layout || document.querySelector('.ok-activity-rail')) return;
    const groups = [...nav.querySelectorAll('.sidebar-category')];
    const rail = document.createElement('nav');
    rail.className = 'ok-activity-rail';
    rail.setAttribute('aria-label', 'Áreas do Okestre');
    const heading = document.createElement('div');
    heading.className = 'ok-context-heading';
    sidebar.insertBefore(heading, nav);
    const title = document.createElement('span');
    title.className = 'ok-page-title';
    document.querySelector('.topbar .brand')?.append(title);
    let selected = -1;
    const buttons = [];
    function choose(index) {
      selected = index;
      groups.forEach((group, i) => { group.hidden = index !== -1 && i !== index; });
      buttons.forEach((button, i) => button.setAttribute('aria-pressed', String(i - 1 === index)));
      heading.textContent = index === -1 ? 'Todas as áreas' : labels[index];
    }
    const labels = groups.map(group => group.querySelector('.sidebar-category-title')?.textContent.replace(/^\d+\.\s*/, '').trim() || 'Área');
    const icons = ['layout-grid', 'folder-open', 'terminal', 'database', 'check-check', 'bot', 'search'];
    ['Todas as áreas', ...labels].forEach((label, i) => {
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'ok-activity-button';
      button.title = label; button.setAttribute('aria-label', label);
      const icon = document.createElement('i'); icon.dataset.lucide = icons[i] || 'folder';
      button.append(icon); rail.append(button); buttons.push(button);
      button.addEventListener('click', () => {
        choose(i - 1);
        if (i > 0) {
          const group = groups[i - 1];
          (group.querySelector('.nav-item.active') || group.querySelector('.nav-item'))?.click();
        }
      });
    });
    layout.insertBefore(rail, document.querySelector('.ok-workspace-surface'));
    function sync() {
      const active = nav.querySelector('.nav-item.active');
      title.textContent = active?.querySelector('.nav-label')?.textContent || active?.textContent.trim() || 'Workspace';
      const group = active?.closest('.sidebar-category');
      if (selected !== -1 && group && groups.indexOf(group) !== selected) choose(groups.indexOf(group));
    }
    new MutationObserver(sync).observe(nav, { subtree: true, attributes: true, attributeFilter: ['class'] });
    choose(-1); sync();
    if (typeof window.refreshLucideIcons === 'function') window.refreshLucideIcons();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
})();
