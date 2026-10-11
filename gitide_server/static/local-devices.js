/* All user/device strings are rendered with textContent, never HTML. */
(() => {
  const el = (id) => document.getElementById(id);
  let csrf = '', projects = [], devices = [], next = null, loaded = null, busy = false;
  const errors = { device_offline: 'Computador offline. Abra o Okestre Local.', read_only: 'A pasta permite somente leitura.', conflict: 'O arquivo mudou. Leia novamente antes de salvar.', root_unavailable: 'Pasta removida, pausada ou indisponível.', local_access_failed: 'Não foi possível acessar o arquivo ou sua pasta.', path_blocked: 'Arquivo bloqueado pela política local.', device_not_authorized: 'Dispositivo sem autorização.', request_timeout_result_unknown: 'A resposta não chegou. Leia o arquivo para conferir o resultado antes de tentar outra alteração.' };
  function notice(text, error = false) { el('notice').textContent = text; el('notice').className = error ? 'error' : ''; }
  async function request(path, body) {
    const response = await fetch(`/api/local/${path}`, { credentials: 'same-origin', cache: 'no-store',
      ...(body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf }, body: JSON.stringify(body) }) });
    const data = await response.json();
    if (!response.ok) throw new Error(errors[data.detail] || data.detail || 'Falha na solicitação.');
    return data;
  }
  async function action(fn) {
    if (busy) return;
    busy = true;
    el('projects').disabled = true;
    el('filepath').disabled = true;
    el('content').readOnly = true;
    try { await fn(); } catch (error) { notice(error.message, true); }
    finally {
      busy = false;
      el('projects').disabled = false;
      el('filepath').disabled = false;
      el('content').readOnly = false;
    }
  }
  function button(text, run) { const b = document.createElement('button'); b.type = 'button'; b.textContent = text; b.onclick = () => action(run); return b; }
  function selection() { return projects.find((p) => p.id === Number(el('projects').value)); }
  function writable() { const p = selection(); const d = devices.find((d) => d.id === p?.device_id); return d?.online && d.roots.some((r) => r.id === p?.root_id && r.writable); }
  function resetEditor() { loaded = null; el('content').value = ''; el('content').disabled = true; el('save').disabled = true; el('version').textContent = ''; }
  async function call(operation, args) {
    if (!selection()) throw new Error('Selecione um projeto.');
    return request('call', { project_id: selection().id, operation, arguments: args });
  }
  async function refresh() {
    const data = await request('devices'); csrf = data.csrf_token; devices = data.devices; projects = data.projects;
    const chosen = el('projects').value;
    el('projects').replaceChildren(new Option('Selecione…', ''));
    for (const p of projects) el('projects').add(new Option(p.name, String(p.id)));
    el('projects').value = chosen;
    el('devices').replaceChildren();
    if (!devices.length) el('devices').textContent = 'Nenhum computador conectado ainda.';
    for (const d of devices) {
      const card = document.createElement('div'); card.className = 'device';
      const title = document.createElement('strong'); title.textContent = `${d.name} · ${d.revoked ? 'Revogado' : d.online ? 'Online' : 'Offline'}`; card.append(title);
      for (const r of d.roots) {
        const row = document.createElement('div'); row.className = 'root';
        const text = document.createElement('span'); text.textContent = `${r.name} — ${r.writable ? 'Leitura e edição' : 'Somente leitura'}`; row.append(text);
        const bound = projects.find((p) => p.device_id === d.id && p.root_id === r.id);
        if (bound) { const label = document.createElement('span'); label.textContent = `Projeto #${bound.id}: ${bound.name}`; row.append(label); }
        else if (!d.revoked) row.append(button('Vincular projeto', async () => {
          const name = prompt('Nome do projeto no Okestre:', r.name); if (!name) return;
          await request('bind', { device_id: d.id, root_id: r.id, name }); await refresh(); notice('Projeto vinculado. Autorize-o também na conexão OAuth do GPT.');
        }));
        card.append(row);
      }
      if (!d.revoked) card.append(button('Revogar dispositivo', async () => {
        if (!confirm(`Revogar o acesso de ${d.name}?`)) return;
        await request('revoke', { device_id: d.id }); await refresh(); notice('Dispositivo revogado.');
      }));
      el('devices').append(card);
    }
    el('save').disabled = !loaded || !writable();
  }
  async function files(offset = 0) {
    const data = await call('list_files', { offset, limit: 100 });
    if (!offset) el('files').replaceChildren();
    for (const f of data.items) { const li = document.createElement('li'); li.append(button(f.path, () => read(f.path))); el('files').append(li); }
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
    el('content').value = content; el('content').disabled = false; el('save').disabled = !writable();
    el('version').textContent = `Versão: ${hash}`; notice('Arquivo lido do computador.');
  }
  el('refresh').onclick = () => action(refresh);
  el('pair-form').onsubmit = (event) => { event.preventDefault(); action(async () => {
    const data = await request('pair', { name: el('device-name').value }); el('pair-code').textContent = data.code; el('pair-result').hidden = false;
    setTimeout(() => { if (el('pair-code').textContent === data.code) { el('pair-code').textContent = 'Código expirado'; } }, data.expires_in * 1000);
  }); };
  el('projects').onchange = () => action(async () => {
    if (loaded && el('content').value !== loaded.content && !confirm('Descartar as alterações ainda não salvas?')) {
      el('projects').value = String(loaded.project);
      return;
    }
    resetEditor(); el('files').replaceChildren(); el('more').hidden = true; if (selection()) await files();
  });
  el('more').onclick = () => action(() => files(next));
  el('read').onclick = () => action(() => read(el('filepath').value));
  el('new-file').onclick = () => action(async () => {
    if (!selection() || !writable()) throw new Error('Selecione um projeto com permissão de edição.');
    const path = el('filepath').value.trim(); if (!path) throw new Error('Informe o caminho do arquivo.');
    if (loaded && el('content').value !== loaded.content && !confirm('Descartar as alterações ainda não salvas?')) return;
    loaded = { path, hash: 'missing', content: '', project: selection().id }; el('content').value = ''; el('content').disabled = false; el('save').disabled = false;
    el('version').textContent = 'Arquivo novo. A pasta precisa existir. Um arquivo existente não será sobrescrito.';
  });
  el('editor').onsubmit = (event) => { event.preventDefault(); action(async () => {
    if (!loaded || loaded.project !== selection()?.id || loaded.path !== el('filepath').value) throw new Error('Leia o arquivo ou prepare um arquivo novo antes de salvar.');
    const result = await call('write_file', { filepath: loaded.path, content: el('content').value, expected_sha256: loaded.hash });
    loaded.hash = result.sha256; loaded.content = el('content').value; el('version').textContent = `Versão: ${loaded.hash}`;
    notice('Salvo no computador. Versão anterior preservada no histórico local.');
  }); };
  window.addEventListener('beforeunload', (event) => { if (loaded && el('content').value !== loaded.content) { event.preventDefault(); event.returnValue = ''; } });
  action(async () => {
    await refresh();
    const requested = new URLSearchParams(location.search).get('project');
    if (requested && projects.some((p) => String(p.id) === requested)) {
      el('projects').value = requested;
      await files();
    }
  });
})();
