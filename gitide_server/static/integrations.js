(() => {
  'use strict';
  window.mountIntegrations = function (panel) {
    panel.innerHTML = `<section class="mcp-connections integrations" aria-labelledby="integrations-title">
      <header class="mcp-connections-toolbar"><h2 id="integrations-title">Integrações</h2><div>
      <button type="button" class="btn btn-secondary" data-refresh aria-label="Atualizar integrações" title="Atualizar integrações"><i data-lucide="refresh-cw"></i></button>
      <button type="button" class="btn btn-primary" data-new>Conectar Supabase</button></div></header>
      <p role="status" data-message></p>
      <div class="mcp-connections-scroll"><table><thead><tr><th>Integração</th><th>Projetos</th><th>Permissão</th><th>Status</th><th>Ações</th></tr></thead><tbody data-items></tbody></table></div>
      <h3>SQL aguardando aprovação</h3><div data-approvals></div>
      <dialog class="mcp-connections-dialog" aria-labelledby="integration-form-title"><form>
        <h3 id="integration-form-title">Supabase PostgreSQL</h3><div class="integration-fields">
        <label>Nome<input name="name" required maxlength="100"></label>
        <label>Host<input name="host" required maxlength="255" placeholder="db.projeto.supabase.co"></label>
        <label>Porta<select name="port"><option value="5432">5432</option><option value="6543">6543</option></select></label>
        <label>Banco<input name="database" required value="postgres"></label>
        <label>Usuário PostgreSQL<input name="username" required autocomplete="off"></label>
        <label>Senha PostgreSQL<input name="password" type="password" autocomplete="new-password" maxlength="4096"></label>
        <label>Permissão<select name="permission"><option value="read">Somente leitura</option><option value="write">Leitura e escrita</option><option value="full">Acesso total ao banco</option></select></label>
        </div><p>O acesso efetivo também depende dos privilégios do usuário PostgreSQL. Acesso total pode excluir dados e alterar a estrutura.</p>
        <fieldset><legend>Projetos autorizados</legend><div data-projects class="integration-projects"></div></fieldset>
        <label class="integration-check"><input type="checkbox" name="require_approval" checked> Exigir aprovação de toda escrita</label>
        <label class="integration-check"><input type="checkbox" name="enabled" checked> Integração ativa</label>
        <p role="alert" data-error></p><footer class="mcp-connections-dialog-actions">
        <button type="button" class="btn btn-secondary" data-cancel>Cancelar</button><button type="submit" class="btn btn-primary">Salvar integração</button></footer>
      </form></dialog></section>`;
    const find = selector => panel.querySelector(selector);
    const dialog = find('dialog'), form = find('form');
    let csrf = '', projects = [], selected = null, busy = false;
    const permission = {read: 'Somente leitura', write: 'Leitura e escrita', full: 'Acesso total ao banco'};
    async function request(path = '', method = 'GET', body) {
      const response = await fetch('/api/integrations' + path, {method, credentials: 'same-origin',
        headers: {'Content-Type': 'application/json', 'X-CSRF-Token': csrf}, body: body === undefined ? undefined : JSON.stringify(body)});
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Falha na integração.');
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
    function edit(item) {
      selected = item; form.reset(); find('[data-error]').textContent = '';
      for (const key of ['name', 'host', 'port', 'database', 'username', 'permission']) {
        if (item) form.elements.namedItem(key).value = item[key];
      }
      form.elements.password.value = ''; form.elements.password.required = !item;
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
    }
    async function load() {
      find('[data-message]').textContent = 'Carregando integrações…';
      const data = await request(); csrf = data.csrf_token; projects = data.projects;
      const body = find('[data-items]'); body.replaceChildren();
      for (const item of data.items) {
        const row = document.createElement('tr');
        [item.name, item.project_ids.map(id => projects.find(p => p.id === id)?.name || `#${id}`).join(', '), permission[item.permission], item.enabled ? 'Ativa' : 'Desativada'].forEach(value => {
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
    }
    find('[data-new]').addEventListener('click', () => edit(null));
    find('[data-refresh]').addEventListener('click', () => action(load));
    find('[data-cancel]').addEventListener('click', () => dialog.close());
    dialog.addEventListener('close', () => { form.elements.password.value = ''; });
    form.addEventListener('submit', event => {
      event.preventDefault();
      action(async () => {
        const values = Object.fromEntries(new FormData(form));
        values.port = Number(values.port); values.project_ids = new FormData(form).getAll('project_ids').map(Number);
        values.enabled = form.elements.enabled.checked; values.require_approval = form.elements.require_approval.checked;
        if (!values.project_ids.length) throw new Error('Selecione pelo menos um projeto.');
        if (!values.require_approval && values.permission !== 'read' && !window.confirm('Permitir escritas sem aprovação no painel?')) return;
        await request(selected ? `/${selected.id}` : '', selected ? 'PUT' : 'POST', values);
        dialog.close(); await load();
      });
    });
    return {load: () => action(load)};
  };
})();
