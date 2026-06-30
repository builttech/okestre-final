const fields = {
  apiBase: document.getElementById('apiBase'),
  projectId: document.getElementById('projectId'),
  token: document.getElementById('token'),
  severity: document.getElementById('severity'),
  title: document.getElementById('title'),
  description: document.getElementById('description'),
  selector: document.getElementById('selector'),
  includeScreenshot: document.getElementById('includeScreenshot'),
  status: document.getElementById('status')
};

let pickedElement = null;

function setStatus(message) {
  fields.status.textContent = message;
}

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function loadConfig() {
  const saved = await chrome.storage.sync.get(['apiBase', 'projectId', 'token']);
  fields.apiBase.value = saved.apiBase || 'http://127.0.0.1:8000';
  fields.projectId.value = saved.projectId || '';
  fields.token.value = saved.token || '';
}

async function saveConfig() {
  await chrome.storage.sync.set({
    apiBase: fields.apiBase.value.trim().replace(/\/$/, ''),
    projectId: fields.projectId.value.trim(),
    token: fields.token.value.trim()
  });
  setStatus('Configuração salva.');
}

async function pickElement() {
  const tab = await getActiveTab();
  if (!tab?.id) return;
  setStatus('Clique em um elemento da página. Esc cancela.');
  try {
    const response = await chrome.tabs.sendMessage(tab.id, { type: 'GITIDE_QA_PICK_ELEMENT' });
    if (!response?.ok) {
      setStatus('Seleção cancelada.');
      return;
    }
    pickedElement = response;
    fields.selector.value = response.selector || '';
    if (!fields.title.value && response.text) {
      fields.title.value = response.text.slice(0, 80);
    }
    setStatus('Elemento selecionado.');
  } catch (_err) {
    await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ['content.js'] });
    const response = await chrome.tabs.sendMessage(tab.id, { type: 'GITIDE_QA_PICK_ELEMENT' });
    pickedElement = response?.ok ? response : null;
    fields.selector.value = pickedElement?.selector || '';
    setStatus(pickedElement ? 'Elemento selecionado.' : 'Não foi possível selecionar.');
  }
}

async function captureScreenshot() {
  if (!fields.includeScreenshot.checked) return null;
  try {
    return await chrome.tabs.captureVisibleTab(null, { format: 'png', quality: 80 });
  } catch (_err) {
    return null;
  }
}

async function sendAnnotation() {
  const apiBase = fields.apiBase.value.trim().replace(/\/$/, '');
  const projectId = fields.projectId.value.trim();
  const token = fields.token.value.trim();
  const title = fields.title.value.trim();
  if (!apiBase || !projectId || !token) {
    setStatus('Configure API Base, Project ID e Token.');
    return;
  }
  if (!title) {
    setStatus('Informe um título curto.');
    return;
  }

  const tab = await getActiveTab();
  const screenshot = await captureScreenshot();
  const payload = {
    title,
    description: fields.description.value.trim(),
    severity: fields.severity.value,
    status: 'open',
    url: tab?.url || '',
    selector: fields.selector.value.trim(),
    browser: navigator.userAgent,
    screenshot,
    viewport: {
      width: window.screen.width,
      height: window.screen.height
    },
    metadata: {
      tabTitle: tab?.title || '',
      elementRect: pickedElement?.rect || null,
      selectedText: pickedElement?.text || ''
    }
  };

  setStatus('Enviando...');
  const response = await fetch(`${apiBase}/api/projects/${projectId}/qa/annotations`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'X-GitIDE-Source': 'qa-extension'
    },
    body: JSON.stringify(payload)
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || data.status !== 'success') {
    setStatus(data.detail || 'Erro ao enviar anotação.');
    return;
  }
  fields.title.value = '';
  fields.description.value = '';
  fields.selector.value = '';
  pickedElement = null;
  setStatus(`Enviado: ${data.annotation.id}`);
}

document.getElementById('saveConfig').addEventListener('click', saveConfig);
document.getElementById('pickElement').addEventListener('click', pickElement);
document.getElementById('sendAnnotation').addEventListener('click', sendAnnotation);

loadConfig();
