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

function getConnectionConfig() {
  return {
    apiBase: fields.apiBase.value.trim().replace(/\/$/, ''),
    projectId: fields.projectId.value.trim(),
    token: fields.token.value.trim()
  };
}

function validateConnectionConfig(config) {
  if (!config.apiBase || !config.projectId || !config.token) {
    setStatus('Configure API Base, Project ID e Token.');
    return false;
  }
  if (!/^https?:\/\//i.test(config.apiBase)) {
    setStatus('API Base precisa começar com http:// ou https://.');
    return false;
  }
  return true;
}

async function requestGitIde(config, path, options = {}) {
  const response = await fetch(`${config.apiBase}${path}`, {
    mode: 'cors',
    cache: 'no-store',
    ...options,
    headers: {
      ...(options.headers || {}),
      'Authorization': `Bearer ${config.token}`
    }
  });
  const data = await response.json().catch(() => ({}));
  return { response, data };
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
  await chrome.storage.sync.set(getConnectionConfig());
  setStatus('Configuração salva.');
}

async function testConnection() {
  const config = getConnectionConfig();
  if (!validateConnectionConfig(config)) return;
  setStatus('Testando conexão...');
  try {
    const { response, data } = await requestGitIde(config, `/api/projects/${config.projectId}/qa/annotations`, {
      method: 'GET'
    });
    if (!response.ok) {
      setStatus(data.detail || `Conexão respondeu HTTP ${response.status}. Confira token e Project ID.`);
      return;
    }
    setStatus(`Conexão OK. ${data.total ?? 0} anotação(ões) no projeto.`);
  } catch (err) {
    setStatus(buildNetworkErrorMessage(err));
  }
}

function buildNetworkErrorMessage(err) {
  const message = err?.message || 'Falha de rede';
  return `Falha de conexão: ${message}. Se só ocorre nesta máquina, verifique VPN/proxy/firewall, permissão da extensão e se https://ide.builtt.com.br abre neste navegador.`;
}

function polishDescriptionText() {
  const original = fields.description.value.trim();
  if (!original) {
    setStatus('Escreva uma descrição antes de corrigir com IA.');
    return;
  }
  const polished = applyLocalTextPolish(original);
  fields.description.value = polished;
  setStatus(polished === original ? 'Texto já está adequado.' : 'Descrição revisada.');
}

function applyLocalTextPolish(text) {
  let output = text
    .replace(/\s+/g, ' ')
    .replace(/\s+([,.!?;:])/g, '$1')
    .replace(/([,.!?;:])([^\s])/g, '$1 $2')
    .trim();

  const replacements = [
    [/\bespaço\b/gi, 'espaço'],
    [/\bganhar espaço\b/gi, 'ganhar espaço'],
    [/\bcomprmidas\b/gi, 'comprimidas'],
    [/\bcomprimida\b/gi, 'comprimida'],
    [/\bficarem\b/gi, 'ficarem'],
    [/\bopçoes\b/gi, 'opções'],
    [/\bopcoes\b/gi, 'opções'],
    [/\bnao\b/gi, 'não'],
    [/\bpara nao\b/gi, 'para não'],
    [/\bdisplay no top\b/gi, 'Display no topo'],
    [/\bbtn\b/gi, 'botão'],
    [/\bmarge\b/gi, 'merge'],
    [/\bdeletar\b/gi, 'excluir']
  ];

  replacements.forEach(([pattern, value]) => {
    output = output.replace(pattern, value);
  });

  output = output
    .split(/(?<=[.!?])\s+/)
    .map(sentence => sentence.charAt(0).toUpperCase() + sentence.slice(1))
    .join(' ');

  if (!/[.!?]$/.test(output)) output += '.';
  return output;
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
  const config = getConnectionConfig();
  const title = fields.title.value.trim();
  if (!validateConnectionConfig(config)) return;
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
    const { response, data } = await requestGitIde(config, `/api/projects/${config.projectId}/qa/annotations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });
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
    if (payload.screenshot) {
      setStatus('Falha no envio com print. Tentando enviar sem screenshot...');
      try {
        payload.screenshot = null;
        const { response, data } = await requestGitIde(config, `/api/projects/${config.projectId}/qa/annotations`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        });
        if (!response.ok || data.status !== 'success') {
          setStatus(data.detail || `Erro ao enviar sem screenshot. HTTP ${response.status}`);
          return;
        }
        fields.title.value = '';
        fields.description.value = '';
        fields.selector.value = '';
        pickedElement = null;
        setStatus(`Enviado sem screenshot: ${data.annotation.id}`);
        return;
      } catch (fallbackErr) {
        setStatus(buildNetworkErrorMessage(fallbackErr));
        return;
      }
    }
    setStatus(buildNetworkErrorMessage(err));
  }
}

document.getElementById('saveConfig').addEventListener('click', saveConfig);
document.getElementById('testConnection').addEventListener('click', testConnection);
document.getElementById('polishDescription').addEventListener('click', polishDescriptionText);
document.getElementById('pickElement').addEventListener('click', pickElement);
document.getElementById('sendAnnotation').addEventListener('click', sendAnnotation);

loadConfig();
