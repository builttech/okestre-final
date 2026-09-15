(() => {
  'use strict';
  window.mountMcpAudit = function (panel) {
    panel.innerHTML = `<section class="mcp-connections mcp-audit" aria-labelledby="mcp-audit-title">
      <header class="mcp-connections-toolbar"><h2 id="mcp-audit-title">Histórico MCP</h2>
      <button class="btn btn-secondary" type="button" data-audit-refresh aria-label="Atualizar histórico" title="Atualizar histórico"><i data-lucide="refresh-cw"></i></button></header>
      <form class="mcp-audit-filters">
        <label><span id="mcp-audit-connection-label">Conexão</span><select name="connection_id" aria-labelledby="mcp-audit-connection-label"><option value="">Todas</option></select></label>
        <label><span id="mcp-audit-project-label">Projeto</span><select name="project_id" aria-labelledby="mcp-audit-project-label"><option value="">Todos</option></select></label>
        <label><span id="mcp-audit-tool-label">Ferramenta</span><select name="tool" aria-labelledby="mcp-audit-tool-label"><option value="">Todas</option></select></label>
        <label><span id="mcp-audit-outcome-label">Resultado</span><select name="outcome" aria-labelledby="mcp-audit-outcome-label"><option value="">Todos</option><option value="success">Sucesso</option><option value="error">Erro</option><option value="denied">Acesso negado</option></select></label>
        <label>De<input type="datetime-local" name="start"></label><label>Até<input type="datetime-local" name="end"></label>
        <div><button class="btn btn-primary" type="submit">Filtrar</button> <button class="btn btn-secondary" type="reset">Limpar</button></div>
      </form>
      <p data-audit-message role="status" aria-live="polite"></p>
      <div class="mcp-connections-scroll" tabindex="0" aria-label="Histórico de chamadas">
        <table><thead><tr><th>Data</th><th>Aplicativo / Conta</th><th>Projeto</th><th>Ferramenta</th><th>Resultado</th><th>Duração</th><th>Conexão</th></tr></thead><tbody></tbody></table>
      </div><footer class="mcp-connections-toolbar"><span data-audit-count></span><div class="mcp-connections-pager">
        <button type="button" class="btn btn-secondary" data-audit-prev aria-label="Página anterior do histórico" title="Página anterior"><i data-lucide="chevron-left"></i></button>
        <button type="button" class="btn btn-secondary" data-audit-next aria-label="Próxima página do histórico" title="Próxima página"><i data-lucide="chevron-right"></i></button>
      </div></footer></section>`;
    const find = (selector) => panel.querySelector(selector);
    const form = find('form');
    let offset = 0, next = null, busy = false, filters = new URLSearchParams();
    function controls() {
      panel.querySelectorAll('button, input, select').forEach((element) => { element.disabled = busy; });
      find('[data-audit-prev]').disabled = busy || offset === 0;
      find('[data-audit-next]').disabled = busy || next == null;
    }
    function options(name, items) {
      const select = form.elements.namedItem(name);
      const selected = select.value;
      select.replaceChildren(new Option('Todos', ''));
      items.forEach((item) => select.add(new Option(item.name, item.id)));
      select.value = selected;
    }
    async function load() {
      if (busy) return;
      busy = true; controls();
      find('[data-audit-message]').textContent = 'Carregando histórico…';
      try {
        const params = new URLSearchParams(filters);
        params.set('offset', offset); params.set('limit', 25);
        const response = await fetch(`/api/mcp/audit?${params}`, { credentials: 'same-origin' });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Falha ao consultar histórico.');
        options('connection_id', data.connections.map((item) => ({ id: item.id, name: `${item.name} (${item.id.slice(0, 8)})` })));
        options('project_id', data.projects.map((item) => ({ id: String(item.id), name: `${item.name} (#${item.id})` })));
        options('tool', data.tools.map((tool) => ({ id: tool, name: tool })));
        next = data.next_offset;
        const body = find('tbody'); body.replaceChildren();
        for (const item of data.items) {
          const row = document.createElement('tr');
          const values = [new Date(item.occurred_at * 1000).toLocaleString('pt-BR'), `${item.application}\n${item.account}`,
            item.project_name || 'Não se aplica', item.tool || 'Autenticação',
            { success: 'Sucesso', error: 'Erro', denied: 'Acesso negado' }[item.outcome], `${item.duration_ms} ms`];
          values.forEach((value) => { const cell = document.createElement('td'); cell.textContent = value; row.append(cell); });
          const cell = document.createElement('td');
          if (item.connection_id) {
            const button = document.createElement('button'); button.type = 'button'; button.className = 'btn btn-secondary'; button.textContent = 'Ver conexão';
            button.addEventListener('click', () => window.dispatchEvent(new CustomEvent('gitide:mcp-show-connection', { detail: item.connection_id })));
            cell.append(button);
          } else cell.textContent = 'Não se aplica';
          row.append(cell); body.append(row);
        }
        find('[data-audit-message]').textContent = data.total ? '' : 'Nenhuma chamada encontrada.';
        find('[data-audit-count]').textContent = data.total ? `${offset + 1}–${Math.min(offset + 25, data.total)} de ${data.total}` : '0 chamadas';
      } catch (error) {
        find('[data-audit-message]').textContent = error.message;
      } finally { busy = false; controls(); }
    }
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      const nextFilters = new URLSearchParams();
      for (const [key, value] of new FormData(form)) {
        if (value) nextFilters.set(key, ['start', 'end'].includes(key) ? String(new Date(value).getTime() / 1000) : value);
      }
      if (nextFilters.has('start') && nextFilters.has('end') && Number(nextFilters.get('start')) > Number(nextFilters.get('end'))) {
        find('[data-audit-message]').textContent = 'O início deve ser anterior ao fim.'; return;
      }
      filters = nextFilters; offset = 0; load();
    });
    form.addEventListener('reset', () => { filters = new URLSearchParams(); offset = 0; setTimeout(load, 0); });
    find('[data-audit-refresh]').addEventListener('click', load);
    find('[data-audit-prev]').addEventListener('click', () => { offset = Math.max(0, offset - 25); load(); });
    find('[data-audit-next]').addEventListener('click', () => { if (next != null) { offset = next; load(); } });
    controls();
    return { load };
  };
})();
