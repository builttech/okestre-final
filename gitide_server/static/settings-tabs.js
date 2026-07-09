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
      'Use sempre o ID de projeto acima em todas as chamadas de API do Act IA.',
      'Exemplo: /api/projects/' + (projectId || '{project_id}') + '/...',
      token ? `Token Act IA: ${token}` : '',
      '',
      '--- DIRETRIZES DO CUSTOM GPT ---',
      'Você é um Agente de Engenharia de Software conectado ao computador local do usuário via Act IA.',
      'Antes de realizar qualquer tarefa de leitura, escrita ou execução de comandos, você DEVE verificar se existe o arquivo \'GPT_INSTRUCTIONS.md\' na raiz do workspace do projeto atual (usando o endpoint de leitura de arquivos).',
      'Se o arquivo existir, leia e siga rigorosamente todas as diretrizes, fases de análise e o protocolo de execução contidos nele.',
      'REGRA INQUEBRÁVEL: antes de executar qualquer task, valide REQ, DRI e Task List. Depois atualize o plano detalhado em .documents/task/task.details.md, aguarde a autorização explícita do usuário no formato "Aprovado executar TASK-REQ-0000-000" e só depois implemente. O plano detalhado não deve ficar somente no chat. Nunca sobrescreva task.details.md apagando seções anteriores; anexe nova seção ou atualize somente a seção da task atual.'
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
    if (tabName === 'parametrization') {
       if (!paramEditor) setTimeout(initParamEditor, 50);
       else setTimeout(() => paramEditor.refresh(), 50);
    }

    if (tabName === 'prod-validator' && typeof window.loadProdReadinessValidator === 'function') {
      window.loadProdReadinessValidator();
    }
    if (tabName === 'security-rules' && typeof window.loadSecurityRulesPrompt === 'function') {
      window.loadSecurityRulesPrompt();
    }
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
            <button class="btn btn-danger" id="btn-settings-delete-project" type="button"><i data-lucide="trash-2"></i> Deletar Projeto</button>
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

    document.getElementById('btn-settings-delete-project')?.addEventListener('click', () => {
      const legacyDeleteButton = document.getElementById('btn-delete-project');
      if (legacyDeleteButton) {
        legacyDeleteButton.click();
        return;
      }
      setCopyStatus('Ação de deletar indisponível.');
    });

    document.getElementById('btn-copy-gpt-custom-instructions')?.addEventListener('click', () => {
      const text = document.getElementById('gpt-custom-instructions-text')?.textContent || '';
      copyText(text)
        .then(() => alert('Instruções do Custom GPT copiadas com sucesso!'))
        .catch(() => alert('Não foi possível copiar as instruções.'));
    });
  }

  
  let paramEditor = null;
  let currentParamFile = null;
  let currentParamType = null;

  function createParametrizationPanel() {
    const panel = createPanel('parametrization', false);
    panel.innerHTML = `
      <div class="settings-card card parametrization-card" style="height: 100%;">
        <div class="card-header" style="border-bottom: 1px solid var(--border-color); padding-bottom: 12px; margin-bottom: 16px;">
          <h4 style="margin: 0; font-size: 16px; display: flex; align-items: center; gap: 8px;"><i data-lucide="file-edit"></i> Parametrização Base</h4>
        </div>
        <div class="card-body parametrization-grid" style="display: flex; gap: 16px; height: calc(100vh - 180px); min-height: 500px; padding: 0;">
          <div class="parametrization-sidebar" style="width: 250px; border-right: 1px solid var(--border-color); padding-right: 16px; overflow-y: auto;">
             <div style="font-weight: bold; margin-bottom: 8px; color: var(--text-light);">Templates</div>
             <ul id="parametrization-templates-list" style="list-style: none; padding: 0; margin: 0; margin-bottom: 16px; font-size: 13px; display: flex; flex-direction: column; gap: 4px;"></ul>
             <div style="font-weight: bold; margin-bottom: 8px; color: var(--text-light);">Contratos</div>
             <ul id="parametrization-contracts-list" style="list-style: none; padding: 0; margin: 0; font-size: 13px; display: flex; flex-direction: column; gap: 4px;"></ul>
          </div>
          <div class="parametrization-editor-container" style="flex: 1; display: flex; flex-direction: column; gap: 12px; position: relative; width: calc(100% - 250px);">
             <div style="display: flex; justify-content: space-between; align-items: center;">
                <span id="parametrization-current-file" style="font-weight: 500; font-family: var(--font-mono); color: var(--color-primary);">Selecione um arquivo...</span>
                <button class="btn btn-primary btn-sm" id="btn-save-parametrization" disabled><i data-lucide="save"></i> Salvar</button>
             </div>
             <div style="flex: 1; border: 1px solid var(--border-color); border-radius: 4px; position: relative; display: flex; flex-direction: column;" id="parametrization-cm-wrapper">
                <textarea id="parametrization-editor"></textarea>
             </div>
          </div>
        </div>
      </div>
    `;
    return panel;
  }

  function renderParamList(elementId, items, type) {
    const list = document.getElementById(elementId);
    if (!list) return;
    list.innerHTML = items.map(item => `
      <li>
        <a href="#" data-param-file="${item}" data-param-type="${type}" class="param-file-link" style="color: var(--text-muted); text-decoration: none; padding: 4px 8px; display: block; border-radius: 4px;">
          <i data-lucide="file-text" style="width: 14px; height: 14px; margin-right: 6px; vertical-align: text-bottom;"></i>${item}
        </a>
      </li>
    `).join('');
  }

  function initParamEditor() {
    if (paramEditor) return;
    const textarea = document.getElementById('parametrization-editor');
    if (!textarea) return;
    
    paramEditor = CodeMirror.fromTextArea(textarea, {
      mode: 'markdown',
      theme: 'darcula',
      lineNumbers: true,
      lineWrapping: true,
      viewportMargin: Infinity
    });
    paramEditor.setSize('100%', '100%');
    
    paramEditor.on('change', () => {
       document.getElementById('btn-save-parametrization').disabled = false;
    });
  }

  function loadParamFile(file, type) {
    currentParamFile = file;
    currentParamType = type;
    document.getElementById('parametrization-current-file').textContent = file;
    document.getElementById('btn-save-parametrization').disabled = true;
    
    document.querySelectorAll('.param-file-link').forEach(link => {
       if (link.dataset.paramFile === file && link.dataset.paramType === type) {
           link.style.background = 'var(--bg-lighter)';
           link.style.color = 'var(--text-light)';
       } else {
           link.style.background = 'transparent';
           link.style.color = 'var(--text-muted)';
       }
    });

    fetch(`/api/system/parameters/content?type=${type}&filename=${file}`)
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          if (!paramEditor) initParamEditor();
          paramEditor.setValue(data.content);
          document.getElementById('btn-save-parametrization').disabled = true;
        }
      });
  }

  function wireParametrization() {
    fetch('/api/system/parameters')
      .then(res => res.json())
      .then(data => {
         if (data.status === 'success') {
            renderParamList('parametrization-templates-list', data.templates, 'template');
            renderParamList('parametrization-contracts-list', data.contracts, 'contract');
            if (typeof window.refreshLucideIcons === 'function') window.refreshLucideIcons();
            
            document.querySelectorAll('.param-file-link').forEach(link => {
               link.addEventListener('click', (e) => {
                  e.preventDefault();
                  loadParamFile(link.dataset.paramFile, link.dataset.paramType);
               });
            });
         }
      });
      
    document.getElementById('btn-save-parametrization')?.addEventListener('click', () => {
       if (!currentParamFile || !currentParamType || !paramEditor) return;
       const btn = document.getElementById('btn-save-parametrization');
       const originalText = btn.innerHTML;
       btn.innerHTML = 'Salvando...';
       btn.disabled = true;
       
       fetch(`/api/system/parameters/content?type=${currentParamType}&filename=${currentParamFile}`, {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({ content: paramEditor.getValue() })
       }).then(() => {
           btn.innerHTML = 'Salvo!';
           setTimeout(() => { btn.innerHTML = originalText; btn.disabled = true; }, 2000);
       }).catch(() => {
           btn.innerHTML = 'Erro!';
           setTimeout(() => { btn.innerHTML = originalText; btn.disabled = false; }, 2000);
       });
    });
  }

  function initSettingsTabs() {

    const layout = document.querySelector('#tab-settings .settings-dashboard-layout');
    if (!layout || layout.dataset.settingsTabsReady === 'true') return;

    const cards = Array.from(layout.children).filter((child) => child.classList?.contains('settings-card'));
    const agentCard = cards[0];
    const gptCard = cards[1];
    const prodValidatorCard = cards[2];
    const securityRulesCard = cards[3];
    if (!agentCard || !gptCard) return;

    layout.dataset.settingsTabsReady = 'true';
    layout.classList.add('gitide-settings-tabs-ready');

    const sidebar = document.createElement('nav');
    sidebar.className = 'settings-tabs-sidebar';
    sidebar.setAttribute('role', 'tablist');
    sidebar.innerHTML = '<div class="settings-tabs-title">Settings</div>';
    
    sidebar.appendChild(createTabButton('prompt-copy', 'clipboard-copy', 'Prompt Copy', true));
    sidebar.appendChild(createTabButton('parametrization', 'file-edit', 'Parametrização', false));

    sidebar.appendChild(createTabButton('agent-config', 'bot', 'Configurações do Agente', false));
    sidebar.appendChild(createTabButton('gpt-action', 'rocket', 'Configurações do GPT Action', false));
    if (prodValidatorCard) {
      sidebar.appendChild(createTabButton('prod-validator', 'shield-check', 'Prod-Ready Validator', false));
    }
    if (securityRulesCard) {
      sidebar.appendChild(createTabButton('security-rules', 'lock-keyhole', 'Security Rules', false));
    }

    const content = document.createElement('div');
    content.className = 'settings-tabs-content';

    
    const promptPanel = createPromptCopyPanel();
    const parametrizationPanel = createParametrizationPanel();

    const agentPanel = createPanel('agent-config', false);
    const gptPanel = createPanel('gpt-action', false);
    const prodValidatorPanel = createPanel('prod-validator', false);
    const securityRulesPanel = createPanel('security-rules', false);

    agentPanel.appendChild(agentCard);
    gptPanel.appendChild(gptCard);
    if (prodValidatorCard) prodValidatorPanel.appendChild(prodValidatorCard);
    if (securityRulesCard) securityRulesPanel.appendChild(securityRulesCard);
    
    content.appendChild(promptPanel);
    content.appendChild(parametrizationPanel);

    content.appendChild(agentPanel);
    content.appendChild(gptPanel);
    if (prodValidatorCard) content.appendChild(prodValidatorPanel);
    if (securityRulesCard) content.appendChild(securityRulesPanel);

    layout.innerHTML = '';
    layout.appendChild(sidebar);
    layout.appendChild(content);

    
    wirePromptActions();
    wireParametrization();

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
