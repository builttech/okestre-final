const fields = {
  apiBase: document.getElementById('apiBase'),
  projectId: document.getElementById('projectId'),
  token: document.getElementById('token'),
  category: document.getElementById('category'),
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
  const tab = await getActiveTab();
  try {
    if (tab?.id && pickedElement?.rect) {
      await chrome.tabs.sendMessage(tab.id, {
        type: 'GITIDE_QA_SHOW_EVIDENCE_MARKER',
        rect: pickedElement.rect
      }).catch(() => null);
      await new Promise(resolve => setTimeout(resolve, 120));
    }
    const screenshot = await chrome.tabs.captureVisibleTab(null, { format: 'jpeg', quality: 70 });
    return await resizeScreenshot(screenshot);
  } catch (_err) {
    return null;
  } finally {
    if (tab?.id) {
      await chrome.tabs.sendMessage(tab.id, { type: 'GITIDE_QA_CLEAR_EVIDENCE_MARKER' }).catch(() => null);
    }
  }
}

function resizeScreenshot(dataUrl) {
  return new Promise(resolve => {
    if (!dataUrl) {
      resolve(null);
      return;
    }
    const image = new Image();
    image.onload = () => {
      const maxWidth = 1280;
      const scale = image.width > maxWidth ? maxWidth / image.width : 1;
      const canvas = document.createElement('canvas');
      canvas.width = Math.max(1, Math.round(image.width * scale));
      canvas.height = Math.max(1, Math.round(image.height * scale));
      const context = canvas.getContext('2d');
      if (!context) {
        resolve(dataUrl);
        return;
      }
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      resolve(canvas.toDataURL('image/jpeg', 0.72));
    };
    image.onerror = () => resolve(dataUrl);
    image.src = dataUrl;
  });
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
    category: fields.category.value,
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
  try {
    const response = await fetch(`${apiBase}/api/projects/${projectId}/qa/annotations`, {
      method: 'POST',
      mode: 'cors',
      cache: 'no-store',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.status !== 'success') {
      setStatus(data.detail || `Erro ao enviar anotação. HTTP ${response.status}`);
      return;
    }
    fields.title.value = '';
    fields.description.value = '';
    fields.selector.value = '';
    pickedElement = null;
    setStatus(`Enviado: ${data.annotation.id}`);
  } catch (err) {
    const message = err?.message || 'Falha de rede';
    setStatus(`Falha ao conectar no GitIDE: ${message}. Verifique API Base, token, HTTPS e recarregue a extensão.`);
  }
}

document.getElementById('saveConfig').addEventListener('click', saveConfig);
document.getElementById('pickElement').addEventListener('click', pickElement);
document.getElementById('sendAnnotation').addEventListener('click', sendAnnotation);

loadConfig();
