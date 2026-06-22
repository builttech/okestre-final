(function () {
  function activeProjectContext() {
    const selector = document.getElementById('project-selector');
    const selected = selector?.selectedOptions?.[0];
    const projectName = (selected?.textContent || selector?.value || 'Projeto ativo').trim();
    const projectId = selector?.value || '';
    const token = document.getElementById('api-token-full-view')?.value
      || document.getElementById('api-token-preview')?.textContent
      || '';

    return { projectName, projectId, token };
  }

  function buildPromptCopyText() {
    const { projectName, projectId, token } = activeProjectContext();
    return [
      `Projeto ativo: ${projectName}`,
      projectId ? `ID do projeto: ${projectId}` : 'ID do projeto: não selecionado',
      '',
      'Use sempre o ID de projeto acima em todas as chamadas de API do GitIDE.',
      'Exemplo: /api/projects/' + (projectId || '{project_id}') + '/...',
      token ? `Token GitIDE: ${token}` : ''
    ].filter(Boolean).join('\n');
  }

  function copyText(text) {
    if (navigator.clipboard?.writeText) return navigator.clipboard.writeText(text);

    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.setAttribute('readonly', 'true');
    textarea.className = 'is-hidden';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    textarea.remove();
    return Promise.resolve();
  }

  function updatePromptPreview() {
    const preview = document.getElementById('prompt-copy-preview');
    if (preview) preview.value = buildPromptCopyText();
  }

  function setCopyStatus(message) {
    const status = document.getElementById('prompt-copy-status');
    if (!status) return;
    status.textContent = message;
    window.setTimeout(() => {
      if (status.textContent === message) status.textContent = '';
    }, 2400);
  }

  function setActiveTab(tabName) {
    document.querySelectorAll('[data-settings-tab-target]').forEach((button) => {
      const isActive = button.dataset.settingsTabTarget === tabName;
      button.classList.toggle('is-active', isActive);
      button.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    document.querySelectorAll('[data-settings-tab-panel]').forEach((panel) => {
      panel.classList.toggle('is-active', panel.dataset.settingsTabPanel === tabName);
    });

    if (tabName === 'prompt-copy') updatePromptPreview();
  }

  function createTabButton(tabName, icon, label, active) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `settings-tab-button${active ? ' is-active' : ''}`;
    button.dataset.settingsTabTarget = tabName;
    button.setAttribute('role', 'tab');
    button.setAttribute('aria-selected', active ? 'true' : 'false');
    button.innerHTML = `<i data-lucide="${icon}" aria-hidden="true"></i><span>${label}</span>`;
    button.addEventListener('click', () => setActiveTab(tabName));
    return button;
  }

  function createPanel(tabName, active) {
    const panel = document.createElement('div');
    panel.className = `settings-tab-panel${active ? ' is-active' : ''}`;
    panel.dataset.settingsTabPanel = tabName;
    return panel;
  }

  function createPromptCopyPanel() {
    const panel = createPanel('prompt-copy', true);
    panel.innerHTML = `
      <div class="settings-card card prompt-copy-card">
        <div class="card-header">
          <h4><i data-lucide="clipboard-copy"></i> Prompt Copy</h4>
        </div>
        <div class="card-body prompt-copy-grid">
          <p class="help-text">Copie rapidamente o contexto do workspace/projeto ativo para usar em conversas ou automações.</p>
          <textarea id="prompt-copy-preview" class="prompt-copy-preview" readonly></textarea>
          <div class="prompt-copy-actions">
            <button class="btn btn-primary" id="btn-copy-prompt-copy" type="button"><i data-lucide="copy"></i> Copiar Prompt</button>
            <button class="btn btn-secondary" id="btn-copy-project-context" type="button"><i data-lucide="file-text"></i> Copiar Contexto</button>
            <button class="btn btn-secondary" id="btn-refresh-prompt-copy" type="button"><i data-lucide="refresh-cw"></i> Atualizar</button>
            <span class="prompt-copy-status" id="prompt-copy-status"></span>
          </div>
        </div>
      </div>
    `;
    return panel;
  }

  function wirePromptActions() {
    document.getElementById('btn-refresh-prompt-copy')?.addEventListener('click', updatePromptPreview);

    document.getElementById('btn-copy-prompt-copy')?.addEventListener('click', () => {
      const preview = document.getElementById('prompt-copy-preview');
      copyText(preview?.value || buildPromptCopyText())
        .then(() => setCopyStatus('Prompt copiado.'))
        .catch(() => setCopyStatus('Não foi possível copiar.'));
    });

    document.getElementById('btn-copy-project-context')?.addEventListener('click', () => {
      const { projectName, projectId } = activeProjectContext();
      copyText(`Projeto ativo: ${projectName}\nID do projeto: ${projectId || 'não selecionado'}`)
        .then(() => setCopyStatus('Contexto copiado.'))
        .catch(() => setCopyStatus('Não foi possível copiar.'));
    });
  }

  function initSettingsTabs() {
    const layout = document.querySelector('#tab-settings .settings-dashboard-layout');
    if (!layout || layout.dataset.settingsTabsReady === 'true') return;

    const cards = Array.from(layout.children).filter((child) => child.classList?.contains('settings-card'));
    const agentCard = cards[0];
    const gptCard = cards[1];
    if (!agentCard || !gptCard) return;

    layout.dataset.settingsTabsReady = 'true';
    layout.classList.add('gitide-settings-tabs-ready');

    const sidebar = document.createElement('nav');
    sidebar.className = 'settings-tabs-sidebar';
    sidebar.setAttribute('role', 'tablist');
    sidebar.innerHTML = '<div class="settings-tabs-title">Settings</div>';
    sidebar.appendChild(createTabButton('prompt-copy', 'clipboard-copy', 'Prompt Copy', true));
    sidebar.appendChild(createTabButton('agent-config', 'bot', 'Configurações do Agente', false));
    sidebar.appendChild(createTabButton('gpt-action', 'rocket', 'Configurações do GPT Action', false));

    const content = document.createElement('div');
    content.className = 'settings-tabs-content';

    const promptPanel = createPromptCopyPanel();
    const agentPanel = createPanel('agent-config', false);
    const gptPanel = createPanel('gpt-action', false);

    agentPanel.appendChild(agentCard);
    gptPanel.appendChild(gptCard);
    content.appendChild(promptPanel);
    content.appendChild(agentPanel);
    content.appendChild(gptPanel);

    layout.innerHTML = '';
    layout.appendChild(sidebar);
    layout.appendChild(content);

    wirePromptActions();
    document.getElementById('project-selector')?.addEventListener('change', updatePromptPreview);
    updatePromptPreview();

    if (typeof window.refreshLucideIcons === 'function') window.refreshLucideIcons();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSettingsTabs);
  } else {
    initSettingsTabs();
  }
})();
