/* Setup only. Device strings are rendered with textContent, never HTML. */
(() => {
  const el = (id) => document.getElementById(id);
  let csrf = '', devices = [], projects = [], selected = '', step = 1, busy = false;
  const drafts = new Map();
  const errors = { device_not_authorized: 'O computador não está autorizado. Atualize a conexão.', project_name_exists: 'Um dos nomes já está em uso. Altere o nome e tente novamente. Nenhum projeto do lote foi adicionado.', invalid_project: 'Confira as pastas e os nomes dos projetos.', root_session_required: 'Entre novamente com sua conta de administração.', csrf_invalid: 'Sua sessão mudou. Atualize a página.', invalid_request_or_duplicate_project: 'Confira os nomes: cada projeto deve ter um nome exclusivo.' };
  const usable = (d) => !d.revoked && !d.pending && !d.expired;
  const current = () => devices.find((d) => d.id === selected && usable(d));
  const linked = () => projects.filter((p) => p.device_id === selected);
  const key = (root) => selected + ':' + root.id;
  const isBound = (root) => linked().some((p) => p.root_id === root.id);
  function notice(text, error = false) { el('notice').textContent = text; el('notice').className = error ? 'error' : ''; }
  function node(tag, text, className) { const n = document.createElement(tag); if (text) n.textContent = text; if (className) n.className = className; return n; }
  function button(text, callback) { const b = node('button', text, 'secondary'); b.type = 'button'; b.onclick = () => action(callback); return b; }
  async function request(path, body) {
    const response = await fetch('/api/local/' + path, { credentials: 'same-origin', cache: 'no-store',
      ...(body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf }, body: JSON.stringify(body) }) });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(errors[data.detail] || 'Não foi possível concluir. Atualize a conexão e tente novamente.');
    return data;
  }
  function controls() {
    document.querySelectorAll('button,input,select').forEach((n) => { n.disabled = busy; });
    const available = (current()?.roots || []).filter((r) => !isBound(r));
    const count = available.filter((r) => drafts.get(key(r))?.checked).length;
    document.querySelector('[data-step="2"]').disabled = busy || !current();
    document.querySelector('[data-step="3"]').disabled = busy || !linked().length || !current();
    el('to-projects').disabled = busy || !current();
    el('add-projects').disabled = busy || !count;
    el('add-projects').textContent = count ? 'Adicionar ' + count + ' projeto(s) selecionado(s)' : 'Adicionar projetos selecionados';
    el('selection-count').textContent = count + ' selecionado(s)';
    el('select-all').disabled = busy || !available.length;
    el('select-all').checked = available.length > 0 && count === available.length;
    el('select-all').indeterminate = count > 0 && count < available.length;
    el('to-gpt').hidden = !linked().length;
  }
  async function action(callback) {
    if (busy) return;
    busy = true; controls();
    try { await callback(); } catch (error) { notice(error.message, true); }
    finally { busy = false; controls(); }
  }
  function go(next, focus = true) {
    if ((next > 1 && !current()) || (next === 3 && !linked().length)) return;
    step = next;
    for (let i = 1; i <= 3; i++) {
      el('step-' + i).hidden = i !== step;
      const tab = document.querySelector('[data-step="' + i + '"]');
      if (i === step) tab.setAttribute('aria-current', 'step'); else tab.removeAttribute('aria-current');
    }
    controls();
    if (focus) el(['', 'computer-title', 'projects-title', 'gpt-title'][step]).focus();
  }
  function render() {
    const active = devices.filter(usable);
    el('devices').replaceChildren();
    if (!active.length) el('devices').append(node('div', 'Nenhum computador pareado. Comece gerando um código abaixo.', 'empty'));
    for (const d of devices) {
      const card = node('div', null, 'card');
      const label = node('label', null, 'device-choice');
      const radio = document.createElement('input'); radio.type = 'radio'; radio.name = 'device'; radio.value = d.id; radio.checked = selected === d.id;
      radio.onchange = () => { selected = d.id; notice(''); render(); };
      const info = node('div'); info.append(node('strong', d.name), node('p', d.roots.length + ' pasta(s) compartilhada(s)'), node('span', d.online ? 'Online' : 'Offline — abra o Okestre Local no Windows', 'badge' + (d.online ? '' : ' offline')));
      if (usable(d)) label.append(radio);
      const state = d.revoked ? 'Revogado' : d.pending ? 'Aguardando pareamento' : d.expired ? 'Credencial expirada' : d.expires_at ? 'Acesso válido até ' + new Date(d.expires_at * 1000).toLocaleDateString('pt-BR') : 'Sem expiração automática';
      if (!usable(d)) info.querySelector('.badge').remove();
      info.append(node('p', state));
      label.append(info); card.append(label);
      if (!d.pending && !d.revoked) card.append(button('Revogar', async () => {
        if (!confirm('Revogar o acesso de ' + d.name + '? Os arquivos serão preservados.')) return;
        await request('revoke', { device_id: d.id }); await refresh(); notice('Acesso do computador revogado.');
      })); el('devices').append(card);
    }
    el('pair-details').querySelector('summary').textContent = active.length ? 'Adicionar outro computador' : 'Conectar meu computador';
    if (!active.length) el('pair-details').open = true;
    const device = current();
    el('computer-summary').textContent = device ? 'Selecionado: ' + device.name : 'Escolha um computador para continuar.';
    el('selected-computer').textContent = device ? 'Pastas compartilhadas por ' + device.name + (device.online ? '.' : ' — computador offline.') : '';
    el('roots').replaceChildren();
    if (!device?.roots.length) el('roots').append(node('div', 'Nenhuma pasta recebida ainda. Adicione as pastas no aplicativo Windows e clique em Atualizar pastas.', 'empty'));
    for (const root of device?.roots || []) {
      const card = node('div', null, 'card');
      const bound = linked().find((p) => p.root_id === root.id);
      if (bound) {
        const info = node('div'); info.append(node('strong', bound.name), node('p', 'Pasta: ' + root.name)); card.append(info, node('span', 'Já adicionado', 'badge'));
      } else {
        if (!drafts.has(key(root))) drafts.set(key(root), { checked: false, name: root.name });
        const draft = drafts.get(key(root));
        const choice = node('label', null, 'root-choice');
        const check = document.createElement('input'); check.type = 'checkbox'; check.checked = draft.checked; check.setAttribute('aria-label', 'Selecionar ' + root.name);
        check.onchange = () => { draft.checked = check.checked; controls(); };
        choice.append(check, node('span', root.name));
        const nameLabel = node('label', 'Nome do projeto', 'root-name');
        const name = document.createElement('input'); name.value = draft.name; name.maxLength = 100; name.setAttribute('aria-label', 'Nome do projeto ' + root.name); name.oninput = () => { draft.name = name.value; };
        nameLabel.append(name); card.append(choice, nameLabel);
      }
      card.append(node('span', root.writable ? 'Leitura e edição' : 'Somente leitura', 'root-permission'));
      card.append(button('Remover acesso', async () => {
        if (!confirm('Remover o acesso à pasta ' + root.name + '? Os arquivos no computador serão preservados.')) return;
        await request('remove-root', { device_id: selected, root_id: root.id });
        drafts.delete(key(root));
        await refresh(); notice('Acesso à pasta removido. Nenhum arquivo local foi apagado.');
      }));
      el('roots').append(card);
    }
    el('connected-projects').replaceChildren();
    for (const project of linked()) {
      const root = device?.roots.find((r) => r.id === project.root_id);
      const card = node('div', null, 'card'); const info = node('div');
      info.append(node('strong', project.name), node('p', device?.name || 'Computador indisponível'));
      card.append(info, node('span', !root ? 'Pasta não compartilhada no agente' : !device.online ? 'Computador offline' : 'Cadastrado no Okestre', 'badge'));
      el('connected-projects').append(card);
    }
    if (!current()) step = 1; else if (step === 3 && !linked().length) step = 2;
    go(step, false);
  }
  async function refresh() {
    const data = await request('devices'); csrf = data.csrf_token; devices = data.devices; projects = data.projects;
    if (!current()) selected = devices.find(usable)?.id || '';
    render();
  }
  document.querySelectorAll('[data-step]').forEach((b) => { b.onclick = () => go(Number(b.dataset.step)); });
  document.querySelectorAll('[data-back]').forEach((b) => { b.onclick = () => go(Number(b.dataset.back)); });
  el('refresh').onclick = el('refresh-roots').onclick = () => action(async () => { await refresh(); notice('Conexão e pastas atualizadas.'); });
  el('to-projects').onclick = () => go(2);
  el('to-gpt').onclick = () => go(3);
  el('select-all').onchange = () => { for (const r of current()?.roots || []) if (!isBound(r)) drafts.get(key(r)).checked = el('select-all').checked; render(); };
  el('add-projects').onclick = () => action(async () => {
    const selections = (current()?.roots || []).filter((r) => !isBound(r) && drafts.get(key(r))?.checked).map((r) => ({ root_id: r.id, name: drafts.get(key(r)).name.trim() }));
    if (!selections.length || selections.some((p) => !p.name)) throw new Error('Selecione as pastas e preencha o nome de cada projeto.');
    if (new Set(selections.map((p) => p.name)).size !== selections.length) throw new Error('Use um nome diferente para cada projeto.');
    await request('bind-many', { device_id: selected, projects: selections });
    await refresh(); go(3); notice(selections.length + ' projeto(s) adicionado(s). Agora autorize o acesso no GPT.');
  });
  el('pair-form').onsubmit = (event) => { event.preventDefault(); action(async () => {
    const expiry = el('device-expiry').value;
    const data = await request('pair', { name: el('device-name').value, expires_in_months: expiry === 'never' ? null : Number(expiry) });
    el('pair-code').value = data.code; el('pair-result').hidden = false; el('pair-expiry').textContent = 'Sem expiração por tempo. Válido para um único pareamento; gerar outro código para este computador substitui o anterior.';
  }); };
  el('server-url').value = location.origin;
  el('device-expiry').onchange = () => { el('never-warning').hidden = el('device-expiry').value !== 'never'; };
  el('pair-details').addEventListener('toggle', () => { if (!el('pair-details').open) { el('pair-code').value = ''; el('pair-result').hidden = true; } });
  window.addEventListener('pagehide', () => { el('pair-code').value = ''; });
  el('copy-code').onclick = () => action(async () => {
    if (!el('pair-code').value) return;
    try { await navigator.clipboard.writeText(el('pair-code').value); notice('Código copiado.'); }
    catch (_) { notice('Selecione o código para copiá-lo.'); }
  });
  el('mcp-url').value = location.origin + '/mcp/';
  el('copy-url').onclick = () => action(async () => {
    try { await navigator.clipboard.writeText(el('mcp-url').value); notice('URL copiada.'); }
    catch (_) { el('mcp-url').focus(); el('mcp-url').select(); notice('Selecione e copie a URL acima.'); }
  });
  action(async () => {
    await refresh();
    const requested = new URLSearchParams(location.search).get('project');
    const project = projects.find((p) => String(p.id) === requested);
    if (project && devices.some((d) => d.id === project.device_id && usable(d))) { selected = project.device_id; step = 3; render(); }
  });
})();
