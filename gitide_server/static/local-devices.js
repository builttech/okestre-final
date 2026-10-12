/* Device and folder labels are rendered using textContent; secrets never persist in browser storage. */
(() => {
  const el = (id) => document.getElementById(id);
  let csrf = '', projects = [], devices = [], next = null, loaded = null, busy = false;
  let selectedComputer = '', activeTab = 'computers', pendingRemoval = null, codeTimer = null;
  const errors = {
    device_offline: 'Computador offline. Abra o Okestre Local.',
    read_only: 'A pasta permite somente leitura.',
    conflict: 'O arquivo mudou. Leia novamente antes de salvar.',
    root_unavailable: 'Pasta removida, pausada ou indisponível.',
    local_access_failed: 'Não foi possível acessar o arquivo ou sua pasta.',
    path_blocked: 'Arquivo bloqueado pela política local.',
    device_not_authorized: 'Dispositivo sem autorização.',
    credential_expired: 'A chave de conexão expirou. Cadastre novamente o computador.',
    root_removed: 'O compartilhamento desta pasta foi removido.',
    request_timeout_result_unknown: 'A resposta não chegou. Leia o arquivo para conferir o resultado antes de tentar outra alteração.'
  };
  const computerTab = el('tab-computers'), folderTab = el('tab-folders');

  function notice(text, error = false) {
    el('notice').textContent = text;
    el('notice').className = error ? 'error' : '';
  }
  function currentComputer() { return devices.find((d) => d.id === selectedComputer) || null; }
  function tab(name, focus = false) {
    activeTab = name;
    const computers = name === 'computers';
    for (const [control, panel, visible] of [
      [computerTab, el('panel-computers'), computers],
      [folderTab, el('panel-folders'), !computers]
    ]) {
      control.setAttribute('aria-selected', String(visible));
      control.tabIndex = visible ? 0 : -1;
      control.classList.toggle('is-active', visible);
      panel.hidden = !visible;
    }
    if (focus) (computers ? computerTab : folderTab).focus();
  }
  const tabs = [computerTab, folderTab];
  for (const control of tabs) {
    control.onclick = () => tab(control === computerTab ? 'computers' : 'folders');
    control.onkeydown = (event) => {
      const idx = tabs.indexOf(control);
      const nextTab = event.key === 'ArrowRight' ? tabs[(idx + 1) % 2] :
        event.key === 'ArrowLeft' ? tabs[(idx + 1) % 2] :
        event.key === 'Home' ? tabs[0] : event.key === 'End' ? tabs[1] : null;
      if (nextTab) { event.preventDefault(); tab(nextTab === computerTab ? 'computers' : 'folders', true); }
    };
  }
  async function request(path, body) {
    const response = await fetch(`/api/local/${path}`, { credentials: 'same-origin', cache: 'no-store',
      ...(body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf }, body: JSON.stringify(body) }) });
    let data;
    try { data = await response.json(); } catch { throw new Error('Resposta inválida do servidor.'); }
    if (!response.ok) throw new Error(errors[data.detail] || data.detail || 'Falha na solicitação.');
    return data;
  }
  async function action(fn) {
    if (busy) return;
    busy = true;
    el('projects').disabled = true;
    el('filepath').disabled = true;
    el('content').readOnly = true;
    el('generate-key').disabled = true;
    el('confirm-remove-folder').disabled = true;
    try { await fn(); } catch (error) { notice(error.message, true); }
    finally {
      busy = false;
      el('projects').disabled = false;
      el('filepath').disabled = false;
      el('content').readOnly = false;
      el('generate-key').disabled = false;
      el('confirm-remove-folder').disabled = false;
    }
  }
  function button(text, run, className = '') {
    const b = document.createElement('button');
    b.type = 'button'; b.textContent = text;
    if (className) b.className = className;
    b.onclick = () => action(run);
    return b;
  }
  function selection() { return projects.find((p) => p.id === Number(el('projects').value)); }
  function writable() {
    const p = selection(), d = devices.find((item) => item.id === p?.device_id);
    return !!(d?.online && d.roots.some((r) => r.id === p?.root_id && r.writable));
  }
  function resetEditor() {
    loaded = null; el('content').value = ''; el('content').disabled = true;
    el('save').disabled = true; el('version').textContent = '';
  }
  async function call(operation, args) {
    if (!selection()) throw new Error('Selecione um projeto.');
    return request('call', { project_id: selection().id, operation, arguments: args });
  }
  function textNode(tag, text, className = '') {
    const node = document.createElement(tag); node.textContent = text;
    if (className) node.className = className;
    return node;
  }
  function expiryLabel(device) {
    if (device.revoked) return 'Revogado';
    if (device.pending) return 'Aguardando pareamento';
    if (device.expires_at == null) return 'Sem expiração automática';
    return Number(device.expires_at) <= Date.now() / 1000 ? 'Expirado' :
      'Expira em ' + new Date(Number(device.expires_at) * 1000).toLocaleDateString('pt-BR');
  }
  function onlineLabel(device) {
    return device.revoked ? 'Revogado' : device.pending ? 'Pendente' :
      device.expired ? 'Expirado' : device.online ? 'Online' : 'Offline';
  }
  function renderComputers() {
    const container = el('computer-cards'); container.replaceChildren();
    el('computer-empty').hidden = devices.length !== 0;
    for (const d of devices) {
      const card = document.createElement('article'); card.className = 'device';
      if (d.id === selectedComputer) card.classList.add('is-selected');
      const head = textNode('div', '', 'card-head');
      const titleGroup = document.createElement('div');
      titleGroup.append(textNode('div', d.name, 'card-title'), textNode('div', expiryLabel(d), 'card-subtitle'));
      const status = textNode('span', onlineLabel(d), 'badge');
      if (d.online && !d.expired) status.classList.add('online');
      if (d.expired) status.classList.add('expired');
      head.append(titleGroup, status); card.append(head);
      const total = d.roots?.length || 0;
      card.append(textNode('div', `${total} ${total === 1 ? 'pasta disponível' : 'pastas disponíveis'}`, 'card-meta'));
      const actions = textNode('div', '', 'card-actions');
      if (!d.pending && !d.revoked && !d.expired) {
        actions.append(button(d.id === selectedComputer ? 'Ver pastas selecionadas' : 'Ver pastas', async () => {
          selectedComputer = d.id; renderFolders(); renderComputers(); tab('folders');
        }, 'btn-muted'));
      }
      if (!d.pending && !d.revoked) actions.append(button('Revogar dispositivo', async () => {
        if (!confirm(`Revogar o acesso de ${d.name}? A conexão será encerrada.`)) return;
        await request('revoke', { device_id: d.id });
        await refresh(); notice('Dispositivo revogado.');
      }, 'btn-danger'));
      card.append(actions); container.append(card);
    }
  }
  function renderFolders() {
    const picker = el('folder-computer');
    picker.replaceChildren(new Option('Selecione um computador…', ''));
    const available = devices.filter((d) => !d.revoked && !d.pending && !d.expired);
    if (!available.some((d) => d.id === selectedComputer)) selectedComputer = available[0]?.id || '';
    for (const d of available) picker.add(new Option(d.name, d.id));
    picker.value = selectedComputer;
    const d = currentComputer(), rows = d?.roots || [], grid = el('devices');
    grid.replaceChildren();
    const empty = el('folder-empty');
    empty.hidden = rows.length !== 0;
    el('folder-empty-title').textContent = !d ? 'Nenhum computador conectado' : 'Nenhuma pasta cadastrada';
    el('folder-empty-description').textContent = !d ?
      'Adicione e conecte um computador na primeira aba para começar.' :
      'Adicione pastas no aplicativo Okestre Local e atualize a lista.';
    el('folder-add-empty').textContent = d ? 'Adicionar pasta' : 'Adicionar dispositivo';
    el('add-folder').disabled = !d;
    for (const root of rows) {
      const card = document.createElement('article'); card.className = 'folder-card';
      card.append(textNode('div', '▣', 'folder-icon'), textNode('strong', root.name, 'card-title'));
      const permissions = root.writable ? 'Leitura e edição' : 'Somente leitura';
      card.append(textNode('span', permissions, 'card-subtitle'));
      const bound = projects.find((p) => p.device_id === d.id && p.root_id === root.id);
      card.append(textNode('div', bound ? `Projeto vinculado: ${bound.name}` : 'Não vinculada a um projeto', 'card-meta'));
      const actions = textNode('div', '', 'card-actions');
      if (!bound && !d.revoked) actions.append(button('Vincular projeto', async () => {
        const name = prompt('Nome do projeto no Okestre:', root.name);
        if (!name) return;
        await request('bind', { device_id: d.id, root_id: root.id, name });
        await refresh(); notice('Projeto vinculado. Autorize-o também na conexão OAuth do GPT.');
      }));
      if (!d.revoked) actions.append(button('Excluir pasta', async () => {
        pendingRemoval = { device_id: d.id, root_id: root.id };
        el('remove-folder-name').textContent = root.name;
        el('remove-folder-dialog').showModal();
      }, 'btn-danger'));
      card.append(actions); grid.append(card);
    }
  }
  async function refresh() {
    el('computer-loading').hidden = false;
    try {
      const data = await request('devices');
      csrf = data.csrf_token;
      devices = data.devices || []; projects = data.projects || [];
      const chosen = el('projects').value;
      el('projects').replaceChildren(new Option('Selecione…', ''));
      for (const p of projects) el('projects').add(new Option(p.name, String(p.id)));
      if (projects.some((p) => String(p.id) === chosen)) el('projects').value = chosen;
      else {
        el('projects').value = '';
        if (loaded) resetEditor();
        el('files').replaceChildren(); el('more').hidden = true;
      }
      renderFolders(); renderComputers();
      el('save').disabled = !loaded || !writable();
    } finally { el('computer-loading').hidden = true; }
  }
  async function files(offset = 0) {
    const data = await call('list_files', { offset, limit: 100 });
    if (!offset) el('files').replaceChildren();
    for (const f of data.items) {
      const li = document.createElement('li');
      li.append(button(f.path, () => read(f.path)));
      el('files').append(li);
    }
    next = data.next_offset; el('more').hidden = next == null;
  }
  async function read(path) {
    if (loaded && el('content').value !== loaded.content && !confirm('Descartar as alterações ainda não salvas?')) return;
    resetEditor(); el('filepath').value = path;
    let content = '', start = 1, hash = null;
    do {
      const page = await call('read_file', { filepath: path, start_line: start, limit: 200 });
      if (hash && hash !== page.sha256) throw new Error('O arquivo mudou durante a leitura. Tente novamente.');
      hash = page.sha256; content += page.content; start = page.next_line;
    } while (start != null);
    loaded = { path, hash, content, project: selection().id };
    el('content').value = content; el('content').disabled = false;
    el('save').disabled = !writable(); el('version').textContent = `Versão: ${hash}`;
    notice('Arquivo lido do computador.');
  }
  function clearPairCode() {
    if (codeTimer) clearTimeout(codeTimer);
    codeTimer = null; el('pair-code').textContent = ''; el('pair-result').hidden = true;
    el('pair-form').hidden = false;
  }
  function closeDevice() { clearPairCode(); el('device-dialog').close(); }
  function openDevice() {
    clearPairCode(); el('pair-form').reset(); el('never-warning').hidden = true;
    el('device-dialog').showModal(); el('device-name').focus();
  }
  el('add-device').onclick = openDevice;
  el('add-device-empty').onclick = openDevice;
  el('close-device').onclick = closeDevice;
  el('cancel-device').onclick = closeDevice;
  el('done-device').onclick = closeDevice;
  el('device-dialog').addEventListener('close', clearPairCode);
  el('device-expiry').onchange = () => {
    el('never-warning').hidden = el('device-expiry').value !== 'never';
  };
  el('copy-pair-code').onclick = () => action(async () => {
    if (!el('pair-code').textContent || el('pair-code').textContent === 'Código expirado') return;
    await navigator.clipboard.writeText(el('pair-code').textContent); notice('Código copiado.');
  });
  el('pair-form').onsubmit = (event) => {
    event.preventDefault();
    action(async () => {
      const value = el('device-expiry').value;
      const expires_in_months = value === 'never' ? null : Number(value);
      const data = await request('pair', { name: el('device-name').value, expires_in_months });
      el('pair-code').textContent = data.code;
      el('pair-form').hidden = true;
      el('pair-result').hidden = false;
      if (codeTimer) clearTimeout(codeTimer);
      codeTimer = setTimeout(() => {
        if (el('pair-code').textContent === data.code) el('pair-code').textContent = 'Código expirado';
      }, data.expires_in * 1000);
      await refresh();
      notice('Computador preparado. Utilize o código para pareá-lo no Okestre Local.');
    });
  };
  function closeFolder() { el('folder-dialog').close(); }
  function openFolder() {
    if (!currentComputer()) { tab('computers'); openDevice(); return; }
    el('folder-dialog').showModal();
  }
  el('add-folder').onclick = openFolder;
  el('folder-add-empty').onclick = openFolder;
  el('close-folder').onclick = closeFolder;
  el('cancel-folder').onclick = closeFolder;
  el('refresh-folders').onclick = () => action(async () => {
    await refresh(); closeFolder(); notice('Pastas atualizadas.');
  });
  el('folder-computer').onchange = () => {
    selectedComputer = el('folder-computer').value;
    renderFolders(); renderComputers();
  };
  el('cancel-remove-folder').onclick = () => el('remove-folder-dialog').close();
  el('remove-folder-dialog').addEventListener('close', () => { pendingRemoval = null; });
  el('confirm-remove-folder').onclick = () => action(async () => {
    if (!pendingRemoval) return;
    await request('remove-root', pendingRemoval);
    pendingRemoval = null; el('remove-folder-dialog').close();
    await refresh(); notice('Cadastro da pasta removido. Os arquivos no computador foram preservados.');
  });
  el('refresh').onclick = () => action(refresh);
  el('projects').onchange = () => action(async () => {
    if (loaded && el('content').value !== loaded.content && !confirm('Descartar as alterações ainda não salvas?')) {
      el('projects').value = String(loaded.project); return;
    }
    resetEditor(); el('files').replaceChildren(); el('more').hidden = true;
    if (selection()) await files();
  });
  el('more').onclick = () => action(() => files(next));
  el('read').onclick = () => action(() => read(el('filepath').value));
  el('new-file').onclick = () => action(async () => {
    if (!selection() || !writable()) throw new Error('Selecione um projeto com permissão de edição.');
    const path = el('filepath').value.trim(); if (!path) throw new Error('Informe o caminho do arquivo.');
    if (loaded && el('content').value !== loaded.content && !confirm('Descartar as alterações ainda não salvas?')) return;
    loaded = { path, hash: 'missing', content: '', project: selection().id };
    el('content').value = ''; el('content').disabled = false; el('save').disabled = false;
    el('version').textContent = 'Arquivo novo. A pasta precisa existir. Um arquivo existente não será sobrescrito.';
  });
  el('editor').onsubmit = (event) => {
    event.preventDefault();
    action(async () => {
      if (!loaded || loaded.project !== selection()?.id || loaded.path !== el('filepath').value) throw new Error('Leia o arquivo ou prepare um arquivo novo antes de salvar.');
      const result = await call('write_file', { filepath: loaded.path, content: el('content').value, expected_sha256: loaded.hash });
      loaded.hash = result.sha256; loaded.content = el('content').value;
      el('version').textContent = `Versão: ${loaded.hash}`;
      notice('Salvo no computador. Versão anterior preservada no histórico local.');
    });
  };
  window.addEventListener('beforeunload', (event) => {
    if (loaded && el('content').value !== loaded.content) { event.preventDefault(); event.returnValue = ''; }
  });
  action(async () => {
    await refresh();
    const requested = new URLSearchParams(location.search).get('project');
    if (requested && projects.some((p) => String(p.id) === requested)) {
      el('projects').value = requested;
      selectedComputer = projects.find((p) => String(p.id) === requested).device_id;
      renderFolders(); renderComputers();
      tab('folders'); await files();
    }
  });
})();
