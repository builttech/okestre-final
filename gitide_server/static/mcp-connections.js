(() => {
  'use strict';

  window.mountMcpConnections = function (panel) {
    panel.innerHTML = `
      <section class="mcp-connections" aria-labelledby="mcp-connections-title">
        <header class="mcp-connections-toolbar">
          <h2 id="mcp-connections-title">Conexões MCP</h2>
          <button type="button" class="btn btn-secondary" data-mcp-clear-filter hidden>Mostrar todas</button>
          <button type="button" class="btn btn-secondary" data-mcp-refresh title="Atualizar conexões" aria-label="Atualizar conexões"><i data-lucide="refresh-cw" aria-hidden="true"></i></button>
        </header>
        <p data-mcp-message role="status" aria-live="polite"></p>
        <div class="mcp-connections-scroll" tabindex="0" aria-label="Conexões autorizadas">
          <table><thead><tr><th>Aplicativo / Conta</th><th>Projetos</th><th>Acesso</th><th>Autorização</th><th>Último acesso</th><th>Status</th><th>Ação</th></tr></thead><tbody></tbody></table>
        </div>
        <footer class="mcp-connections-toolbar">
          <span data-mcp-count></span><div class="mcp-connections-pager">
            <button type="button" class="btn btn-secondary" data-mcp-prev title="Página anterior" aria-label="Página anterior"><i data-lucide="chevron-left" aria-hidden="true"></i></button>
            <button type="button" class="btn btn-secondary" data-mcp-next title="Próxima página" aria-label="Próxima página"><i data-lucide="chevron-right" aria-hidden="true"></i></button>
          </div>
        </footer>
        <dialog class="mcp-connections-dialog" aria-labelledby="mcp-revoke-title">
          <h3 id="mcp-revoke-title">Revogar conexão?</h3><p data-mcp-revoke-name></p>
          <p>O aplicativo perderá o acesso por esta conexão e precisará de uma nova autorização.</p>
          <p data-mcp-revoke-error role="alert"></p>
          <div class="mcp-connections-dialog-actions"><button type="button" class="btn btn-secondary" data-mcp-cancel>Cancelar</button><button type="button" class="btn btn-danger" data-mcp-confirm>Revogar conexão</button></div>
        </dialog>
      </section>`;
    const find = (selector) => panel.querySelector(selector);
    const body = find('tbody');
    const message = find('[data-mcp-message]');
    const dialog = find('dialog');
    let offset = 0, next = null, total = 0, csrf = '', busy = false, revoking = false, selected = null;
    const size = 25;
    let connectionFilter = '';
    const date = (value) => value == null ? 'Não registrado' : new Date(value * 1000).toLocaleString('pt-BR');

    function controls() {
      find('[data-mcp-refresh]').disabled = busy || revoking;
      find('[data-mcp-prev]').disabled = busy || revoking || offset === 0;
      find('[data-mcp-next]').disabled = busy || revoking || next == null;
      body.querySelectorAll('button').forEach((button) => { button.disabled = busy || revoking; });
      find('[data-mcp-confirm]').disabled = revoking;
      find('[data-mcp-cancel]').disabled = revoking;
    }

    async function request(url, options) {
      const response = await fetch(url, { credentials: 'same-origin', ...options });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || `Falha ao consultar conexões (${response.status}).`);
      return data;
    }

    function render(items) {
      body.replaceChildren();
      for (const item of items) {
        const row = document.createElement('tr');
        const app = document.createElement('td');
        const name = document.createElement('strong');
        name.textContent = item.client_name;
        const account = document.createElement('small');
        account.textContent = item.account;
        app.append(name, account);
        row.append(app);
        const projects = item.projects == null ? 'Todos, inclusive futuros' : item.projects.map((p) => `${p.name} (#${p.id})`).join(', ');
        const status = { active: 'Ativa', revoked: 'Revogada', expired: 'Expirada' }[item.status] || item.status;
        for (const value of [projects, item.can_execute ? 'Leitura, edição e terminal' : item.can_write ? 'Leitura e edição' : 'Somente leitura', date(item.authorized_at), date(item.last_used_at), status]) {
          const cell = document.createElement('td');
          cell.textContent = value;
          row.append(cell);
        }
        const action = document.createElement('td');
        if (item.status === 'active') {
          const button = document.createElement('button');
          button.type = 'button';
          button.className = 'btn btn-danger';
          button.textContent = 'Revogar';
          button.setAttribute('aria-label', `Revogar ${item.client_name}`);
          button.addEventListener('click', () => {
            selected = item;
            find('[data-mcp-revoke-name]').textContent = `${item.client_name} · ${item.account}`;
            find('[data-mcp-revoke-error]').textContent = '';
            dialog.showModal();
            find('[data-mcp-cancel]').focus();
          });
          action.append(button);
        } else {
          action.textContent = '—';
        }
        row.append(action);
        body.append(row);
      }
    }

    async function load() {
      if (busy || revoking) return;
      busy = true;
      controls();
      message.textContent = 'Carregando conexões…';
      try {
        const filter = connectionFilter ? `&connection_id=${encodeURIComponent(connectionFilter)}` : '';
        let data = await request(`/api/mcp/connections?offset=${offset}&limit=${size}${filter}`);
        if (offset > 0 && offset >= data.total) {
          offset = Math.max(0, Math.floor((data.total - 1) / size) * size);
          data = await request(`/api/mcp/connections?offset=${offset}&limit=${size}${filter}`);
        }
        total = data.total;
        next = data.next_offset;
        csrf = data.csrf_token;
        render(data.items);
        message.textContent = total ? '' : 'Nenhuma conexão OAuth autorizada.';
        find('[data-mcp-count]').textContent = total ? `${offset + 1}–${Math.min(offset + size, total)} de ${total}` : '0 conexões';
      } catch (error) {
        message.textContent = error.message;
      } finally {
        busy = false;
        controls();
      }
    }

    find('[data-mcp-refresh]').addEventListener('click', load);
    find('[data-mcp-clear-filter]').addEventListener('click', () => {
      connectionFilter = ''; offset = 0; find('[data-mcp-clear-filter]').hidden = true; load();
    });
    find('[data-mcp-prev]').addEventListener('click', () => { offset = Math.max(0, offset - size); load(); });
    find('[data-mcp-next]').addEventListener('click', () => { if (next != null) { offset = next; load(); } });
    find('[data-mcp-cancel]').addEventListener('click', () => dialog.close());
    dialog.addEventListener('cancel', (event) => { if (revoking) event.preventDefault(); });
    find('[data-mcp-confirm]').addEventListener('click', async () => {
      if (!selected || revoking) return;
      revoking = true;
      controls();
      try {
        await request(`/api/mcp/connections/${encodeURIComponent(selected.id)}/revoke`, {
          method: 'POST', headers: { 'X-CSRF-Token': csrf }
        });
        dialog.close();
        selected = null;
      } catch (error) {
        find('[data-mcp-revoke-error]').textContent = error.message;
      } finally {
        revoking = false;
        controls();
      }
      if (!dialog.open) await load();
    });
    controls();
    return { load, selectConnection(id) {
      connectionFilter = id; offset = 0; find('[data-mcp-clear-filter]').hidden = false;
    } };
  };
})();
