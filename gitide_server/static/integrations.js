(() => {
  'use strict';
  window.mountIntegrations = function (panel) {
    panel.innerHTML = `<section class="mcp-connections integrations" aria-labelledby="integrations-title">
      <header class="mcp-connections-toolbar"><h2 id="integrations-title">Integrações</h2><div>
      <button type="button" class="btn btn-secondary" data-refresh aria-label="Atualizar integrações" title="Atualizar integrações"><i data-lucide="refresh-cw"></i></button>
      <button type="button" class="btn btn-secondary" data-new>PostgreSQL avançado</button>
      <button type="button" class="btn btn-secondary" data-bind hidden>Vincular projeto Supabase</button>
      <button type="button" class="btn btn-primary" data-oauth>Conectar Supabase</button></div></header>
      <p role="status" data-message></p>
      <div class="mcp-connections-scroll"><table><thead><tr><th>Integração</th><th>Projetos</th><th>Permissão</th><th>Status</th><th>Ações</th></tr></thead><tbody data-items></tbody></table></div>
      <h3>SQL aguardando aprovação</h3><div data-approvals></div>
      <dialog class="mcp-connections-dialog" aria-labelledby="integration-form-title"><form>
        <h3 id="integration-form-title">Supabase PostgreSQL</h3><div class="integration-fields">
        <label>Nome<input name="name" required maxlength="100"></label>
        <label data-oauth-account hidden>Autorização Supabase<select name="account_id" disabled></select></label>
        <label data-oauth-project hidden>Projeto Supabase<select name="project_ref" disabled></select></label>
        <label>Host<input name="host" required maxlength="255" placeholder="db.projeto.supabase.co"></label>
        <label>Porta<select name="port"><option value="5432">5432</option><option value="6543">6543</option></select></label>
        <label>Banco<input name="database" required value="postgres"></label>
        <label>Usuário PostgreSQL<input name="username" required autocomplete="off"></label>
        <label>Senha PostgreSQL<input name="password" type="password" autocomplete="new-password" maxlength="4096"></label>
        <label>Permissão<select name="permission"><option value="read">Somente leitura</option><option value="write">Leitura e escrita</option><option value="full">Acesso total ao banco</option></select></label>
        </div><p data-access-note>O acesso efetivo também depende dos privilégios do usuário PostgreSQL. Acesso total pode excluir dados e alterar a estrutura.</p>
        <fieldset><legend>Projetos autorizados</legend><div data-projects class="integration-projects"></div></fieldset>
        <label class="integration-check"><input type="checkbox" name="require_approval" checked> Exigir aprovação de toda escrita</label>
        <label class="integration-check"><input type="checkbox" name="enabled" checked> Integração ativa</label>
        <p role="alert" data-error></p><footer class="mcp-connections-dialog-actions">
        <button type="button" class="btn btn-danger" data-disconnect hidden>Desconectar autorização</button>
        <button type="button" class="btn btn-secondary" data-cancel>Cancelar</button><button type="submit" class="btn btn-primary">Salvar integração</button></footer>
      </form></dialog></section>`;
    const find = selector => panel.querySelector(selector);
    const dialog = find('dialog'), form = find('form');
    let csrf = '', projects = [], selected = null, busy = false;
    let oauthMode = false, oauthState = {configured: false, accounts: []};
    const permission = {read: 'Somente leitura', write: 'Leitura e escrita', full: 'Acesso total ao banco'};
    async function request(path = '', method = 'GET', body) {
      const response = await fetch('/api/integrations' + path, {method, credentials: 'same-origin',
        headers: {'Content-Type': 'application/json', 'Accept': 'application/json', 'X-CSRF-Token': csrf}, body: body === undefined ? undefined : JSON.stringify(body)});
      const status = `HTTP ${response.status}`;
      if (response.status === 401 || new URL(response.url).pathname === '/login') {
        throw new Error(`Sessão expirada ou autenticação necessária (${status}). Entre novamente no Okestre.`);
      }
      const type = (response.headers.get('content-type') || '').split(';')[0].trim().toLowerCase();
      if (type !== 'application/json' && !type.endsWith('+json')) {
        if (response.status === 502 || response.status === 503 || response.status === 504) {
          throw new Error(`Servidor ou proxy indisponível (${status}). A API não retornou JSON. Verifique os logs do backend e do proxy.`);
        }
        throw new Error(`Resposta inesperada da API (${status}): conteúdo não JSON. Verifique a rota /api/integrations e a configuração do proxy.`);
      }
      let data;
      try { data = await response.json(); }
      catch { throw new Error(`Resposta JSON inválida da API (${status}). Verifique os logs do servidor.`); }
      if (!response.ok) throw new Error(`${typeof data?.detail === 'string' ? data.detail : 'Falha na integração.'} (${status})`);
      if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error(`Formato inesperado da API (${status}).`);
      return data;
    }
    async function action(callback) {
      if (busy) return;
      busy = true;
      panel.querySelectorAll('button').forEach(button => { button.disabled = true; });
      try { await callback(); } catch (error) {
        (dialog.open ? find('[data-error]') : find('[data-message]')).textContent = error.message;
      } finally {
        busy = false;
        panel.querySelectorAll('button').forEach(button => { button.disabled = false; });
      }
    }
    function button(label, callback, icon) {
      const button = document.createElement('button'); button.type = 'button'; button.className = 'btn btn-secondary';
      button.title = label; button.setAttribute('aria-label', label);
      if (icon) { const i = document.createElement('i'); i.dataset.lucide = icon; button.append(i); }
      else button.textContent = label;
      button.addEventListener('click', () => action(callback)); return button;
    }
    async function loadSupabaseProjects(ref = '') {
      const account = form.elements.account_id.value;
      form.elements.project_ref.replaceChildren(new Option('Carregando projetos…', ''));
      if (!account) { form.elements.project_ref.replaceChildren(new Option('Conecte o Supabase novamente', '')); return; }
      const data = await request(`/supabase/projects?account_id=${encodeURIComponent(account)}`);
      if (form.elements.account_id.value !== account) return;
      form.elements.project_ref.replaceChildren(new Option('Selecione o projeto', ''));
      data.items.forEach(item => form.elements.project_ref.add(new Option(`${item.name} (${item.ref}) · ${item.status}`, item.ref)));
      if (ref) form.elements.project_ref.value = ref;
      if (!data.items.length) throw new Error('Nenhum projeto disponível nesta autorização Supabase.');
    }
    async function edit(item, useOAuth = false) {
      selected = item; form.reset(); find('[data-error]').textContent = '';
      oauthMode = item ? item.auth_type === 'oauth' : useOAuth;
      find('#integration-form-title').textContent = oauthMode ? 'Supabase OAuth' : 'Supabase PostgreSQL';
      find('[data-access-note]').textContent = oauthMode
        ? 'O acesso também depende dos escopos autorizados no Supabase. Acesso total pode excluir dados e alterar a estrutura.'
        : 'O acesso efetivo também depende dos privilégios do usuário PostgreSQL. Acesso total pode excluir dados e alterar a estrutura.';
      for (const key of ['host', 'port', 'database', 'username', 'password']) {
        form.elements.namedItem(key).disabled = oauthMode;
        form.elements.namedItem(key).closest('label').hidden = oauthMode;
      }
      for (const key of ['account_id', 'project_ref']) {
        form.elements.namedItem(key).disabled = !oauthMode;
        form.elements.namedItem(key).required = oauthMode;
        form.elements.namedItem(key).closest('label').hidden = !oauthMode;
      }
      find('[data-disconnect]').hidden = !oauthMode;
      for (const key of ['name', 'host', 'port', 'database', 'username', 'permission']) {
        if (item && item[key] != null) form.elements.namedItem(key).value = item[key];
      }
      form.elements.password.value = ''; form.elements.password.required = !item && !oauthMode;
      form.elements.password.placeholder = item ? 'Manter senha atual' : '';
      form.elements.enabled.checked = item?.enabled ?? true;
      form.elements.require_approval.checked = item?.require_approval ?? true;
      const list = find('[data-projects]'); list.replaceChildren();
      projects.forEach(project => {
        const label = document.createElement('label'), input = document.createElement('input');
        input.type = 'checkbox'; input.name = 'project_ids'; input.value = project.id;
        input.checked = item?.project_ids.includes(project.id) ?? false;
        label.append(input, document.createTextNode(` ${project.name} (#${project.id})`)); list.append(label);
      });
      dialog.showModal();
      if (oauthMode) {
        form.elements.account_id.replaceChildren();
        oauthState.accounts.forEach(account => form.elements.account_id.add(new Option(`Autorização de ${new Date(account.connected_at * 1000).toLocaleString('pt-BR')} (${account.id.slice(0, 6)})`, account.id)));
        if (item) form.elements.account_id.value = item.account_id;
        await loadSupabaseProjects(item?.project_ref);
      }
    }
    async function load() {
      find('[data-message]').textContent = 'Carregando integrações…';
      const data = await request(); csrf = data.csrf_token; projects = data.projects;
      oauthState = data.supabase_oauth || {configured: false, accounts: []};
      find('[data-bind]').hidden = !oauthState.accounts.length;
      const body = find('[data-items]'); body.replaceChildren();
      for (const item of data.items) {
        const row = document.createElement('tr');
        [item.name + (item.auth_type === 'oauth' ? ' · OAuth' : ' · PostgreSQL'), item.project_ids.map(id => projects.find(p => p.id === id)?.name || `#${id}`).join(', '), permission[item.permission], item.enabled ? 'Ativa' : 'Desativada'].forEach(value => {
          const cell = document.createElement('td'); cell.textContent = value; row.append(cell);
        });
        const actions = document.createElement('td'); actions.className = 'integration-actions';
        actions.append(button('Testar conexão', async () => { await request(`/${item.id}/test`, 'POST'); find('[data-message]').textContent = 'Conexão PostgreSQL validada.'; }, 'activity'),
          button('Editar integração', () => edit(item), 'pencil'),
          button('Excluir integração', async () => {
            if (!window.confirm(`Excluir a integração ${item.name}? O banco remoto não será excluído.`)) return;
            await request(`/${item.id}`, 'DELETE'); await load();
          }, 'trash-2'));
        row.append(actions); body.append(row);
      }
      const approvals = find('[data-approvals]'); approvals.replaceChildren();
      for (const pending of data.approvals) {
        const section = document.createElement('article'); section.className = 'integration-approval';
        const title = document.createElement('h4'); title.textContent = `${data.items.find(i => i.id === pending.integration_id)?.name || 'Integração removida'} · Projeto #${pending.project_id}`;
        const sql = document.createElement('pre'); sql.textContent = pending.sql;
        section.append(title, sql, button('Aprovar SQL', async () => {
          if (!window.confirm('Autorizar a execução deste SQL? Alterações podem ser irreversíveis.')) return;
          await request(`/${pending.approval_id}/approve`, 'POST'); await load();
        }), button('Rejeitar SQL', async () => { await request(`/${pending.approval_id}/reject`, 'POST'); await load(); }));
        approvals.append(section);
      }
      if (!data.approvals.length) approvals.textContent = 'Nenhuma solicitação pendente.';
      find('[data-message]').textContent = data.items.length ? `${data.items.length} integração(ões)` : 'Nenhuma integração cadastrada.';
      window.lucide?.createIcons();
      if (new URL(location.href).searchParams.get('supabase') === 'connected') {
        const url = new URL(location.href); url.searchParams.delete('supabase'); history.replaceState(null, '', url);
        await edit(null, true);
      }
    }
    find('[data-new]').addEventListener('click', () => action(() => edit(null)));
    find('[data-bind]').addEventListener('click', () => action(() => edit(null, true)));
    find('[data-oauth]').addEventListener('click', () => action(async () => {
      if (!oauthState.configured) throw new Error(`OAuth não configurado no servidor. Configure Client ID e Client Secret. URL de retorno: ${oauthState.callback_url || 'consulte a configuração do servidor'}`);
      const data = await request('/supabase/start', 'POST');
      const destination = new URL(data.authorize_url);
      if (destination.origin !== 'https://api.supabase.com' || destination.pathname !== '/v1/oauth/authorize') throw new Error('Destino OAuth inválido.');
      localStorage.setItem('gitide_active_tab', 'tab-settings');
      location.assign(destination.href);
    }));
    form.elements.account_id.addEventListener('change', () => action(() => loadSupabaseProjects()));
    find('[data-disconnect]').addEventListener('click', () => action(async () => {
      if (!confirm('Desconectar esta autorização? Todos os vínculos que dependem dela perderão acesso. O projeto Supabase não será excluído.')) return;
      await request('/supabase/disconnect', 'POST', {account_id: form.elements.account_id.value}); dialog.close(); await load();
    }));
    find('[data-refresh]').addEventListener('click', () => action(load));
    find('[data-cancel]').addEventListener('click', () => dialog.close());
    dialog.addEventListener('close', () => { form.elements.password.value = ''; });
    form.addEventListener('submit', event => {
      event.preventDefault();
      action(async () => {
        const values = Object.fromEntries(new FormData(form));
        if (!oauthMode) values.port = Number(values.port);
        values.project_ids = new FormData(form).getAll('project_ids').map(Number);
        values.enabled = form.elements.enabled.checked; values.require_approval = form.elements.require_approval.checked;
        if (!values.project_ids.length) throw new Error('Selecione pelo menos um projeto.');
        if (!values.require_approval && values.permission !== 'read' && !window.confirm('Permitir escritas sem aprovação no painel?')) return;
        if (oauthMode) {
          if (selected) values.id = selected.id;
          await request('/supabase/bind', 'POST', values);
        } else await request(selected ? `/${selected.id}` : '', selected ? 'PUT' : 'POST', values);
        dialog.close(); await load();
      });
    });
    return {load: () => action(load)};
  };
})();
