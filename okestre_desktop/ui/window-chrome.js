
(() => {
    if (document.getElementById('desktop-window-controls')) return;
    const header = document.querySelector('.topbar');
    if (!header) return;
    const style = document.createElement('style');
    style.textContent = `
      .topbar { padding-right: 0 !important; user-select: none; }
      .desktop-drag-region { flex: 1 1 auto; align-self: stretch; min-width: 24px; }
      #desktop-window-controls { display:flex; align-self:stretch; flex-shrink:0; margin-left:12px; }
      #desktop-window-controls button { width:46px !important; min-width:46px !important; height:100% !important; padding:0 !important; border:0 !important; border-radius:0 !important; background:transparent !important; color:var(--shell-text) !important; display:grid; place-items:center; }
      #desktop-window-controls button:hover { background:var(--shell-hover) !important; }
      #desktop-window-controls button:last-child:hover { background:#c42b1c !important; color:white !important; }
      #desktop-window-controls button:focus-visible { outline:2px solid currentColor; outline-offset:-4px; }
      #desktop-window-controls svg { width:12px; height:12px; pointer-events:none; }
    `;
    document.head.append(style);
    const drag = document.createElement('div');
    drag.className = 'desktop-drag-region';
    drag.setAttribute('aria-hidden', 'true');
    header.insertBefore(drag, header.querySelector('.status-panel'));
    const controls = document.createElement('div');
    controls.id = 'desktop-window-controls';
    const paths = ['M2 6h8', 'M2 2h8v8H2z', 'M2 2l8 8M10 2l-8 8'];
    const labels = ['Minimizar', 'Maximizar / restaurar', 'Fechar'];
    const actions = ['minimize', 'toggle_maximize', 'close'];
    labels.forEach((label, index) => {
        const button = document.createElement('button');
        button.type = 'button'; button.title = label; button.setAttribute('aria-label', label);
        button.innerHTML = `<svg viewBox="0 0 12 12" fill="none" stroke="currentColor"><path d="${paths[index]}"/></svg>`;
        button.addEventListener('click', () => window.pywebview.api[actions[index]]());
        controls.append(button);
    });
    header.append(controls);
    header.addEventListener('dblclick', event => {
        if (event.target === header || event.target === drag) window.pywebview.api.toggle_maximize();
    });
})();
