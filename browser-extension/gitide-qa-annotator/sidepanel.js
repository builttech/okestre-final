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

async function requestGitide(config, path, options = {}) {
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
    const { response, data } = await requestGitide(config, `/api/projects/${config.projectId}/qa/annotations`, {
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

async function polishQaText(mode, text, context = '') {
  const config = getConnectionConfig();
  if (!validateConnectionConfig(config)) {
    return mode === 'title' ? buildShortTitle(applyLocalTextPolish(text)) : applyLocalTextPolish(text);
  }
  const { response, data } = await requestGitide(config, `/api/projects/${config.projectId}/qa/text/polish`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ mode, text, context })
  });
  if (!response.ok || data.status !== 'success' || !data.text) {
    if (response.status === 404) {
      throw new Error('O servidor Act IA ainda não tem o endpoint de revisão QA. Faça o deploy/pull da versão atual do backend e recarregue a extensão.');
    }
    throw new Error(data.detail || `IA respondeu HTTP ${response.status}`);
  }
  return String(data.text).trim();
}

async function polishDescriptionText() {
  const original = fields.description.value.trim();
  if (!original) {
    setStatus('Escreva uma descrição antes de reescrever com IA.');
    return;
  }
  setStatus('Reescrevendo descrição com IA...');
  try {
    const context = [
      fields.title.value.trim() ? `Título atual: ${fields.title.value.trim()}` : '',
      fields.category.value ? `Tipo: ${fields.category.value}` : '',
      fields.severity.value ? `Severidade: ${fields.severity.value}` : '',
      fields.selector.value.trim() ? `Elemento/selector: ${fields.selector.value.trim()}` : ''
    ].filter(Boolean).join('\n');
    const polished = await polishQaText('description', original, context);
    fields.description.value = polished;
    setStatus(polished === original ? 'Texto já está claro.' : 'Descrição reescrita com IA.');
  } catch (err) {
    const polished = applyLocalTextPolish(original);
    fields.description.value = polished;
    setStatus(`Correção local aplicada. ${err.message}`);
  }
}

async function generateTitleFromDescription() {
  const description = fields.description.value.trim();
  if (!description) {
    setStatus('Preencha a descrição antes de gerar o título.');
    return;
  }
  setStatus('Gerando título com IA...');
  try {
    const title = await polishQaText('title', description, fields.selector.value.trim());
    fields.title.value = title;
    setStatus('Título gerado com IA.');
  } catch (err) {
    const polished = applyLocalTextPolish(description);
    const title = buildShortTitle(polished);
    fields.title.value = title;
    setStatus(`Título local aplicado. ${err.message}`);
  }
}

function buildShortTitle(text) {
  let title = cleanInlineText(text)
    .replace(/[.!?]+$/g, '')
    .replace(/^É necessário\s+/i, '')
    .replace(/^Deve\s+/i, '')
    .replace(/^O sistema deve\s+/i, '');

  const patterns = [
    [/^Reposicionar\s+(.+?)\s+acima\s+(.+)$/i, 'Reposicionar $1'],
    [/^Remover\s+(.+)$/i, 'Remover $1'],
    [/^Adicionar\s+(.+)$/i, 'Adicionar $1'],
    [/^Ajustar\s+(.+)$/i, 'Ajustar $1'],
    [/^Corrigir\s+(.+)$/i, 'Corrigir $1'],
    [/^Melhorar\s+(.+)$/i, 'Melhorar $1']
  ];

  for (const [pattern, replacement] of patterns) {
    if (pattern.test(title)) {
      title = title.replace(pattern, replacement);
      break;
    }
  }

  title = title
    .replace(/\s+para\s+.+$/i, '')
    .replace(/\s+porque\s+.+$/i, '')
    .replace(/\s+pois\s+.+$/i, '')
    .replace(/\s*,\s*$/g, '')
    .trim();

  if (title.length > 72) {
    title = `${title.slice(0, 69).trim()}...`;
  }
  return title.charAt(0).toUpperCase() + title.slice(1);
}

function applyLocalTextPolish(text) {
  let output = text
    .replace(/\s+/g, ' ')
    .replace(/\s+([,.!?;:])/g, '$1')
    .replace(/([,.!?;:])([^\s])/g, '$1 $2')
    .trim();

  const replacements = [
    [/\bespaço\b/gi, 'espaço'],
    [/\bganhar espa[çc]o\b/gi, 'ganhar espaço'],
    [/\bcomprmidas\b/gi, 'comprimidas'],
    [/\bcomprimirdas\b/gi, 'comprimidas'],
    [/\bcomprimida\b/gi, 'comprimida'],
    [/\binforções\b/gi, 'informações'],
    [/\binforcoes\b/gi, 'informações'],
    [/\binformacoes\b/gi, 'informações'],
    [/\blsita\b/gi, 'lista'],
    [/\blsitas\b/gi, 'listas'],
    [/\blista\b/gi, 'lista'],
    [/\bficarem\b/gi, 'ficarem'],
    [/\bopçoes\b/gi, 'opções'],
    [/\bopcoes\b/gi, 'opções'],
    [/\bopcões\b/gi, 'opções'],
    [/\bnao\b/gi, 'não'],
    [/\bpara nao\b/gi, 'para não'],
    [/\bdisplay no top\b/gi, 'display no topo'],
    [/\btop\b/gi, 'topo'],
    [/\bbtn\b/gi, 'botão'],
    [/\bmarge\b/gi, 'merge'],
    [/\bdeletar\b/gi, 'excluir'],
    [/\bessas informações\b/gi, 'as informações'],
    [/\besses informações\b/gi, 'as informações']
  ];

  replacements.forEach(([pattern, value]) => {
    output = output.replace(pattern, value);
  });

  output = rewriteCommonQaIntent(output);

  output = output
    .split(/(?<=[.!?])\s+/)
    .map(sentence => sentence.charAt(0).toUpperCase() + sentence.slice(1))
    .join(' ');

  if (!/[.!?]$/.test(output)) output += '.';
  return output;
}

function rewriteCommonQaIntent(text) {
  const normalized = text.replace(/^["']|["']$/g, '').trim();
  const movePattern = /^deixar\s+(?:o\s+texto\s+)?["“]?(.+?)["”]?\s+para\s+(?:as\s+)?opções?\s+(.+?)\s+para\s+(.+)$/i;
  const moveMatch = normalized.match(movePattern);
  if (moveMatch) {
    const target = cleanInlineText(moveMatch[1]);
    const reason = cleanInlineText(moveMatch[3]);
    return `Reposicionar o texto "${target}" acima das opções para ${reason}`;
  }

  const removePattern = /^(?:remover|remove|tirar)\s+(.+)$/i;
  const removeMatch = normalized.match(removePattern);
  if (removeMatch) {
    return `Remover ${cleanInlineText(removeMatch[1])}`;
  }

  const addPattern = /^(?:adicionar|add)\s+(.+)$/i;
  const addMatch = normalized.match(addPattern);
  if (addMatch) {
    return `Adicionar ${cleanInlineText(addMatch[1])}`;
  }

  const adjustPattern = /^(?:ajustar|corrigir|melhorar)\s+(.+)$/i;
  const adjustMatch = normalized.match(adjustPattern);
  if (adjustMatch) {
    return `Ajustar ${cleanInlineText(adjustMatch[1])}`;
  }

  return normalized;
}

function cleanInlineText(text) {
  return String(text || '')
    .replace(/^["“]+|["”]+$/g, '')
    .replace(/\s+/g, ' ')
    .trim();
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
    const { response, data } = await requestGitide(config, `/api/projects/${config.projectId}/qa/annotations`, {
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
        const { response, data } = await requestGitide(config, `/api/projects/${config.projectId}/qa/annotations`, {
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
document.getElementById('generateTitle').addEventListener('click', generateTitleFromDescription);
document.getElementById('polishDescription').addEventListener('click', polishDescriptionText);
document.getElementById('pickElement').addEventListener('click', pickElement);
document.getElementById('sendAnnotation').addEventListener('click', sendAnnotation);

loadConfig();
