// --- GITIDE FRONTEND ENGINE ---

// Estado da Aplicação
const state = {
    apiKey: '',
    projects: [],
    activeProjectId: null,
    activeProject: null,
    activeFilepath: null,
    activeTab: 'tab-files',
    
    // Tabbed Modal States
    activeModalTab: 'local',
    localSelectedPath: null,
    dirBrowserTargetInput: null,
    currentBrowserPath: '',
    githubRepos: [],
    
    // Design System (Tokens) States
    designTokens: null,
    activeTokenSet: 'global',
    activeTokenTheme: null,
    
    // Database Data Grid States
    gridActiveTable: null,
    gridCurrentPage: 1,
    gridTotalRows: 0,
    gridColumns: []
};

// --- CUSTOM SELECT COMPONENT ---

// --- INICIALIZAÇÃO ---
document.addEventListener('DOMContentLoaded', () => {
    initCustomSelects();
    initApp();
    setupEventListeners();
    
    // Polling periódico para comandos pendentes de segurança
    setInterval(() => {
        if (state.activeProjectId) {
            loadPendingCommands();
        }
    }, 5000);
});

async function initApp() {
    try {
        // 1. Busca chave de API e info do servidor
        const infoRes = await fetch('/api/info');
        const infoData = await infoRes.json();
        
        state.apiKey = infoData.api_key;
        state.os = infoData.os;
        state.apiKeyPath = infoData.api_key_path;
        
        // Ajusta caminhos padrão se for Linux (VM/Docker)
        const isLinux = state.os === 'Linux' || (state.apiKeyPath && state.apiKeyPath.startsWith('/'));
        if (isLinux) {
            state.os = 'Linux';
            const listDestInput = document.getElementById('github-list-dest-path');
            if (listDestInput) {
                listDestInput.value = '/workspace';
            }
            const urlDestInput = document.getElementById('github-url-dest-path');
            if (urlDestInput) {
                urlDestInput.placeholder = 'ex: /workspace/meu-app';
            }
        }
        
        // Exibe token na barra superior e nas configurações
        document.getElementById('api-token-preview').textContent = state.apiKey.substring(0, 8) + '...';
        document.getElementById('api-token-full-view').value = state.apiKey;
        
        // 2. Busca lista de projetos
        await loadProjects();
        
        // Recupera o projeto e aba ativos salvos anteriormente
        const savedProjectId = localStorage.getItem('gitide_active_project_id');
        const savedTab = localStorage.getItem('gitide_active_tab');
        if (savedProjectId && state.projects.some(p => p.id == savedProjectId)) {
            if (savedTab) {
                state.activeTab = savedTab;
            }
            selectProject(savedProjectId);
        }
        
    } catch (err) {
        console.error('Erro na inicialização:', err);
        alert('Erro ao conectar com o backend do GitIDE. Certifique-se de que o servidor FastAPI está rodando.');
    }
}

// Cabeçalhos para requisições autenticadas
function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.apiKey}`,
        'X-GitIDE-Source': 'dashboard'
    };
}

// --- PROJETOS ---
async function loadProjects() {
    const res = await fetch('/api/projects');
    state.projects = await res.json();
    
    const selector = document.getElementById('project-selector');
    selector.innerHTML = '<option value="">-- Selecione um Projeto --</option>';
    
    state.projects.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = p.name;
        selector.appendChild(opt);
    });

    if (state.activeProjectId) {
        selector.value = state.activeProjectId;
    }
}

function selectProject(projectId) {
    if (!projectId) {
        state.activeProjectId = null;
        state.activeProject = null;
        localStorage.removeItem('gitide_active_project_id');
        document.getElementById('btn-delete-project').style.display = 'none';
        document.getElementById('btn-copy-project-gpt-info').style.display = 'none';
        document.getElementById('no-project-state').classList.add('active');
        // Oculta todas as abas
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        return;
    }
    
    state.activeProjectId = parseInt(projectId);
    state.activeProject = state.projects.find(p => p.id === state.activeProjectId);
    localStorage.setItem('gitide_active_project_id', projectId);
    
    // Exibe botão de exclusão de projeto
    document.getElementById('btn-delete-project').style.display = 'inline-flex';
    document.getElementById('btn-copy-project-gpt-info').style.display = 'inline-flex';
    
    // Oculta painel de "nenhum selecionado"
    document.getElementById('no-project-state').classList.remove('active');
    
    // Atualiza prompt do Terminal com o caminho do projeto
    document.getElementById('terminal-prompt').textContent = `${state.activeProject.path}>`;
    
    // Sincroniza o valor do dropdown selector
    document.getElementById('project-selector').value = projectId;
    
    // Carrega configurações de banco de dados do projeto de localStorage
    const savedDbType = localStorage.getItem(`gitide_project_${projectId}_db_type`);
    const savedDbConn = localStorage.getItem(`gitide_project_${projectId}_db_conn`);
    const savedDbSql = localStorage.getItem(`gitide_project_${projectId}_db_sql`);
    
    const dbTypeSelect = document.getElementById('db-type-select');
    const dbConnInput = document.getElementById('db-conn-input');
    const dbSqlTextarea = document.getElementById('db-sql-textarea');
    
    if (dbTypeSelect) {
        dbTypeSelect.value = savedDbType || 'sqlite';
        const type = dbTypeSelect.value;
        const lbl = document.getElementById('lbl-db-conn');
        const input = document.getElementById('db-conn-input');
        if (lbl && input) {
            if (type === 'sqlite') {
                lbl.textContent = 'Arquivo do Banco (relativo ao projeto):';
                input.placeholder = 'ex: database.db ou db/sqlite.db';
            } else if (type === 'postgresql') {
                lbl.textContent = 'Connection String (URI) do PostgreSQL:';
                input.placeholder = 'ex: postgresql://usuario:senha@host:5432/nome_do_banco';
            } else if (type === 'mysql') {
                lbl.textContent = 'Connection String (URI) do MySQL:';
                input.placeholder = 'ex: mysql+pymysql://usuario:senha@host:3306/nome_do_banco';
            }
        }
    }
    if (dbConnInput) {
        dbConnInput.value = savedDbConn !== null ? savedDbConn : (savedDbType === 'sqlite' || !savedDbType ? 'database.db' : '');
    }
    if (dbSqlTextarea) {
        dbSqlTextarea.value = savedDbSql !== null ? savedDbSql : '';
    }
    
    // Carrega credenciais do arquivo do projeto
    loadProjectDbCredentials();
    
    // Altera para a aba ativa e carrega dados correspondentes
    switchTab(state.activeTab);
}

// --- ABAS ---
function switchTab(tabId) {
    // Cancela polling de comandos pendentes ao mudar de aba
    if (window.pendingCommandsInterval) {
        clearInterval(window.pendingCommandsInterval);
        window.pendingCommandsInterval = null;
    }

    state.activeTab = tabId;
    localStorage.setItem('gitide_active_tab', tabId);
    
    // Se não há projeto selecionado, só mostra a aba de Configuração/Instalação
    if (!state.activeProjectId && tabId !== 'tab-settings') {
        document.getElementById('no-project-state').classList.add('active');
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[data-tab="tab-settings"]`).classList.add('active');
        document.getElementById('tab-settings').classList.add('active');
        state.activeTab = 'tab-settings';
        return;
    }
    
    // Atualiza navegação
    document.querySelectorAll('.nav-item').forEach(btn => {
        if (btn.getAttribute('data-tab') === tabId) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    // Exibe painel da aba
    document.querySelectorAll('.tab-pane').forEach(p => {
        if (p.id === tabId) {
            p.classList.add('active');
        } else {
            p.classList.remove('active');
        }
    });
    
    // Carrega dados específicos da aba (independente de ter projeto ativo ou não)
    if (tabId === 'tab-settings') {
        loadAgentConfig();
    }
    
    // Carrega dados específicos da aba
    if (state.activeProjectId) {
        if (tabId === 'tab-files') {
            loadFiles();
        } else if (tabId === 'tab-git') {
            loadGitStatus();
        } else if (tabId === 'tab-logs') {
            loadActivityLogs();
            loadAllSnapshots();
        } else if (tabId === 'tab-tokens') {
            loadDesignTokens();
        } else if (tabId === 'tab-agent') {
            loadAgentConfig();
        } else if (tabId === 'tab-database') {
            loadDbTables();
            loadProjectDbCredentials();
        } else if (tabId === 'tab-documents') {
            loadDocuments();
        } else if (tabId === 'tab-terminal') {
            loadPendingCommands();
            startPendingCommandsPolling();
        }
    }
}

// --- EXPLORADOR DE ARQUIVOS ---
function buildFileTree(files) {
    const root = { name: 'root', type: 'folder', children: {} };
    
    files.forEach(file => {
        const parts = file.path.split('/');
        let current = root;
        
        parts.forEach((part, index) => {
            const isLast = index === parts.length - 1;
            
            if (isLast) {
                current.children[part] = {
                    name: part,
                    type: 'file',
                    path: file.path,
                    size: file.size,
                    last_modified: file.last_modified
                };
            } else {
                if (!current.children[part]) {
                    current.children[part] = {
                        name: part,
                        type: 'folder',
                        children: {}
                    };
                }
                current = current.children[part];
            }
        });
    });
    
    return root;
}

function renderTree(node, container, depth = 0) {
    const keys = Object.keys(node.children).sort((a, b) => {
        const itemA = node.children[a];
        const itemB = node.children[b];
        if (itemA.type !== itemB.type) {
            return itemA.type === 'folder' ? -1 : 1;
        }
        return a.localeCompare(b, undefined, { sensitivity: 'base' });
    });
    
    keys.forEach(key => {
        const item = node.children[key];
        const itemEl = document.createElement('div');
        itemEl.className = 'tree-item';
        
        if (item.type === 'folder') {
            const folderHeader = document.createElement('div');
            folderHeader.className = 'file-node folder-node';
            folderHeader.style.paddingLeft = `${depth * 12 + 10}px`;
            folderHeader.innerHTML = `<i class="fa-solid fa-folder-open" style="color: var(--color-warning); margin-right: 6px;"></i> <span>${item.name}</span>`;
            
            const folderChildrenContainer = document.createElement('div');
            folderChildrenContainer.className = 'folder-children active';
            
            folderHeader.addEventListener('click', (e) => {
                e.stopPropagation();
                folderChildrenContainer.classList.toggle('active');
                const icon = folderHeader.querySelector('i');
                if (folderChildrenContainer.classList.contains('active')) {
                    icon.className = 'fa-solid fa-folder-open';
                } else {
                    icon.className = 'fa-solid fa-folder';
                }
            });
            
            itemEl.appendChild(folderHeader);
            itemEl.appendChild(folderChildrenContainer);
            container.appendChild(itemEl);
            
            renderTree(item, folderChildrenContainer, depth + 1);
        } else {
            const fileEl = document.createElement('div');
            fileEl.className = 'file-node';
            fileEl.style.paddingLeft = `${depth * 12 + 10}px`;
            if (state.activeFilepath === item.path) {
                fileEl.classList.add('active');
            }
            
            let iconClass = 'fa-regular fa-file-lines';
            const ext = item.name.split('.').pop().toLowerCase();
            if (['js', 'ts', 'py', 'java', 'cpp', 'html', 'css', 'json', 'rb', 'php', 'swift', 'plist', 'xml', 'gradle', 'properties'].includes(ext)) {
                fileEl.classList.add('file-doc');
                iconClass = 'fa-solid fa-file-code';
            } else if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'ico'].includes(ext)) {
                fileEl.classList.add('file-img');
                iconClass = 'fa-regular fa-file-image';
            }
            
            fileEl.innerHTML = `<i class="${iconClass}"></i> <span>${item.name}</span>`;
            fileEl.setAttribute('data-filepath', item.path);
            fileEl.addEventListener('click', (e) => {
                e.stopPropagation();
                openFile(item.path, item.size, item.last_modified);
            });
            
            itemEl.appendChild(fileEl);
            container.appendChild(itemEl);
        }
    });
}

async function loadFiles() {
    const container = document.getElementById('file-tree');
    container.innerHTML = '<div class="loading-spinner"><i class="fa-solid fa-circle-notch fa-spin"></i></div>';
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/files`);
        const data = await res.json();
        
        if (data.status !== 'success') throw new Error(data.detail);
        
        container.innerHTML = '';
        if (data.files.length === 0) {
            container.innerHTML = '<p class="placeholder-text">Nenhum arquivo encontrado no workspace.</p>';
            return;
        }
        
        const treeRoot = buildFileTree(data.files);
        renderTree(treeRoot, container);
        
    } catch (err) {
        container.innerHTML = `<p class="placeholder-text error-text">Erro ao ler arquivos: ${err.message}</p>`;
    }
}

async function openFile(filepath, size, mtime) {
    state.activeFilepath = filepath;
    
    // Atualiza seleção na árvore usando o atributo data-filepath
    document.querySelectorAll('.file-node').forEach(node => {
        if (node.getAttribute('data-filepath') === filepath) {
            node.classList.add('active');
        } else {
            node.classList.remove('active');
        }
    });
    
    const textarea = document.getElementById('file-editor-textarea');
    textarea.disabled = true;
    textarea.value = 'Carregando arquivo...';
    updateLineNumbers();
    
    document.getElementById('active-file-name').innerHTML = `<i class="fa-solid fa-file-code"></i> ${filepath}`;
    
    // Metadados
    const metaSize = (size / 1024).toFixed(2) + ' KB';
    const metaDate = new Date(mtime).toLocaleString();
    document.getElementById('meta-size').textContent = metaSize;
    document.getElementById('meta-mtime').textContent = metaDate;
    document.getElementById('editor-meta').style.display = 'flex';
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/files/read?filepath=${encodeURIComponent(filepath)}`);
        const data = await res.json();
        
        if (res.status === 404) {
            textarea.value = 'Arquivo não encontrado (ou foi removido).';
            updateLineNumbers();
            return;
        }
        
        textarea.value = data.content;
        textarea.disabled = false;
        document.getElementById('btn-save-file').disabled = false;
        updateLineNumbers();
        
        // Carrega timeline de snapshots deste arquivo
        loadHistoryTimeline(filepath);
        
    } catch (err) {
        textarea.value = `Erro ao ler arquivo: ${err.message}`;
        updateLineNumbers();
    }
}

async function saveFile() {
    if (!state.activeProjectId || !state.activeFilepath) return;
    
    const textarea = document.getElementById('file-editor-textarea');
    const btn = document.getElementById('btn-save-file');
    
    btn.disabled = true;
    textarea.disabled = true;
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/files/write`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                filepath: state.activeFilepath,
                content: textarea.value
            })
        });
        
        const data = await res.json();
        if (res.status !== 200) throw new Error(data.detail);
        
        // Re-habilita e atualiza informações do arquivo
        textarea.disabled = false;
        btn.disabled = false;
        
        // Atualiza a árvore e os metadados do arquivo
        loadFiles();
        loadHistoryTimeline(state.activeFilepath);
        
        // Alerta rápido no topo da tela ou botão
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-check"></i> Salvo!';
        setTimeout(() => {
            btn.innerHTML = originalText;
        }, 1500);
        
    } catch (err) {
        alert(`Erro ao salvar arquivo: ${err.message}`);
        textarea.disabled = false;
        btn.disabled = false;
    }
}

async function loadHistoryTimeline(filepath) {
    const list = document.getElementById('file-snapshots-list');
    const drawer = document.getElementById('file-snapshots-drawer');
    list.innerHTML = '';
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/snapshots?filepath=${encodeURIComponent(filepath)}`);
        const data = await res.json();
        
        if (data.length === 0) {
            drawer.style.display = 'none';
            return;
        }
        
        drawer.style.display = 'block';
        data.forEach(snap => {
            const item = document.createElement('div');
            item.className = 'snapshot-item';
            
            const dateStr = new Date(snap.timestamp).toLocaleString();
            item.innerHTML = `
                <div class="snapshot-info">
                    <span class="snapshot-time">${dateStr}</span>
                    <span class="snapshot-hash">Hash: ${snap.hash.substring(0, 12)}...</span>
                </div>
                <button class="btn btn-sm btn-secondary btn-rollback" data-id="${snap.id}"><i class="fa-solid fa-rotate-left"></i> Restaurar</button>
            `;
            
            item.querySelector('.btn-rollback').addEventListener('click', () => rollbackToSnapshot(snap.id));
            list.appendChild(item);
        });
        
    } catch (err) {
        console.error('Erro ao buscar snapshots do arquivo:', err);
    }
}

async function rollbackToSnapshot(snapshotId) {
    const confirmed = await showCustomConfirm(
        'Restaurar Snapshot',
        `Tem certeza que deseja restaurar o arquivo para o snapshot #${snapshotId}?`,
        'Restaurar'
    );
    if (!confirmed) return;
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/snapshots/${snapshotId}/rollback`, {
            method: 'POST',
            headers: getHeaders()
        });
        const data = await res.json();
        
        if (res.status !== 200) throw new Error(data.detail);
        
        alert('Arquivo restaurado com sucesso para a versão do snapshot!');
        
        // Recarrega arquivo aberto
        if (state.activeFilepath) {
            openFile(state.activeFilepath, 0, new Date().toISOString());
        }
        
    } catch (err) {
        alert(`Falha no rollback: ${err.message}`);
    }
}

// --- TERMINAL INTEGRADO ---
async function runTerminalCommand(e) {
    e.preventDefault();
    if (!state.activeProjectId) return;
    
    const input = document.getElementById('terminal-input');
    const cmd = input.value.trim();
    if (!cmd) return;
    
    input.value = '';
    
    const output = document.getElementById('terminal-output');
    
    // Echo do comando na tela
    const echoDiv = document.createElement('div');
    echoDiv.className = 'terminal-line cmd-echo';
    echoDiv.textContent = `$ ${cmd}`;
    output.appendChild(echoDiv);
    output.scrollTop = output.scrollHeight;
    
    const btn = document.getElementById('btn-run-cmd');
    btn.disabled = true;
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/execute`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ command: cmd })
        });
        
        const data = await res.json();
        
        if (data.status === 'success') {
            if (data.stdout) {
                const outDiv = document.createElement('div');
                outDiv.className = 'terminal-line';
                outDiv.textContent = data.stdout;
                output.appendChild(outDiv);
            }
            if (data.stderr) {
                const errDiv = document.createElement('div');
                errDiv.className = 'terminal-line stderr-msg';
                errDiv.textContent = data.stderr;
                output.appendChild(errDiv);
            }
            if (!data.stdout && !data.stderr) {
                const sysDiv = document.createElement('div');
                sysDiv.className = 'terminal-line system-msg';
                sysDiv.textContent = `Comando executado com código de retorno: ${data.exit_code}`;
                output.appendChild(sysDiv);
            }
        } else {
            const errDiv = document.createElement('div');
            errDiv.className = 'terminal-line stderr-msg';
            errDiv.textContent = `Erro do Servidor: ${data.detail}`;
            output.appendChild(errDiv);
        }
        
    } catch (err) {
        const errDiv = document.createElement('div');
        errDiv.className = 'terminal-line stderr-msg';
        errDiv.textContent = `Erro de Conexão: ${err.message}`;
        output.appendChild(errDiv);
    } finally {
        btn.disabled = false;
        output.scrollTop = output.scrollHeight;
    }
}

// --- COMANDOS PENDENTES ---
async function loadPendingCommands() {
    if (!state.activeProjectId) {
        const panel = document.getElementById('pending-commands-panel');
        if (panel) panel.style.display = 'none';
        return;
    }
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/execute/pending`, {
            headers: getHeaders()
        });
        if (!res.ok) throw new Error('Falha ao carregar comandos pendentes');
        const commands = await res.json();
        
        const panel = document.getElementById('pending-commands-panel');
        const countSpan = document.getElementById('pending-commands-count');
        const listDiv = document.getElementById('pending-commands-list');
        
        if (!panel || !countSpan || !listDiv) return;
        
        if (commands && commands.length > 0) {
            panel.style.display = 'block';
            countSpan.textContent = commands.length;
            
            listDiv.innerHTML = '';
            commands.forEach(cmd => {
                const item = document.createElement('div');
                item.className = 'pending-command-item';
                item.style.display = 'flex';
                item.style.justifyContent = 'space-between';
                item.style.alignItems = 'center';
                item.style.padding = '10px 12px';
                item.style.background = 'rgba(255, 255, 255, 0.03)';
                item.style.border = '1px solid var(--border-color)';
                item.style.borderRadius = 'var(--border-radius, 8px)';
                item.style.marginBottom = '6px';
                item.style.width = '100%';
                item.style.boxSizing = 'border-box';
                
                const info = document.createElement('div');
                info.style.flex = '1';
                info.style.marginRight = '12px';
                
                const cmdText = document.createElement('code');
                cmdText.textContent = cmd.command;
                cmdText.style.background = 'rgba(0,0,0,0.3)';
                cmdText.style.padding = '4px 8px';
                cmdText.style.borderRadius = '4px';
                cmdText.style.display = 'block';
                cmdText.style.fontFamily = 'monospace';
                cmdText.style.wordBreak = 'break-all';
                cmdText.style.color = '#f59e0b';
                
                const dateText = document.createElement('span');
                const date = new Date(cmd.created_at + 'Z');
                dateText.textContent = `Solicitado em: ${date.toLocaleString()}`;
                dateText.style.fontSize = '11px';
                dateText.style.color = '#94a3b8';
                dateText.style.display = 'block';
                dateText.style.marginTop = '4px';
                
                info.appendChild(cmdText);
                info.appendChild(dateText);
                
                const actions = document.createElement('div');
                actions.style.display = 'flex';
                actions.style.gap = '8px';
                
                const btnApprove = document.createElement('button');
                btnApprove.className = 'btn btn-sm btn-success';
                btnApprove.style.backgroundColor = '#10b981';
                btnApprove.style.color = '#fff';
                btnApprove.style.border = 'none';
                btnApprove.style.padding = '6px 12px';
                btnApprove.style.borderRadius = '4px';
                btnApprove.style.cursor = 'pointer';
                btnApprove.innerHTML = '<i class="fa-solid fa-check"></i> Aprovar';
                btnApprove.onclick = () => handleApproveCommand(cmd.id);
                
                const btnReject = document.createElement('button');
                btnReject.className = 'btn btn-sm btn-danger';
                btnReject.style.backgroundColor = '#ef4444';
                btnReject.style.color = '#fff';
                btnReject.style.border = 'none';
                btnReject.style.padding = '6px 12px';
                btnReject.style.borderRadius = '4px';
                btnReject.style.cursor = 'pointer';
                btnReject.innerHTML = '<i class="fa-solid fa-xmark"></i> Rejeitar';
                btnReject.onclick = () => handleRejectCommand(cmd.id);
                
                actions.appendChild(btnApprove);
                actions.appendChild(btnReject);
                
                item.appendChild(info);
                item.appendChild(actions);
                listDiv.appendChild(item);
            });
        } else {
            panel.style.display = 'none';
            countSpan.textContent = '0';
            listDiv.innerHTML = '';
        }
    } catch (err) {
        console.error('Erro ao listar comandos pendentes:', err);
    }
}

async function handleApproveCommand(id) {
    if (!state.activeProjectId) return;
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/execute/pending/${id}/approve`, {
            method: 'POST',
            headers: getHeaders()
        });
        if (!res.ok) throw new Error('Erro ao aprovar comando');
        await loadPendingCommands();
    } catch (err) {
        alert(err.message);
    }
}

async function handleRejectCommand(id) {
    if (!state.activeProjectId) return;
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/execute/pending/${id}/reject`, {
            method: 'POST',
            headers: getHeaders()
        });
        if (!res.ok) throw new Error('Erro ao rejeitar comando');
        await loadPendingCommands();
    } catch (err) {
        alert(err.message);
    }
}

// --- DATABASE EXPLORER FUNCTIONS ---
async function loadDbTables() {
    if (!state.activeProjectId) return;
    
    const dbType = document.getElementById('db-type-select').value;
    const connStr = document.getElementById('db-conn-input').value.trim();
    const tablesList = document.getElementById('db-tables-list');
    const statusDot = document.getElementById('db-status-dot');
    const statusText = document.getElementById('db-status-text');
    
    if (!connStr) {
        tablesList.innerHTML = '<p class="placeholder-text" style="padding: 20px 0; font-size: 12px; text-align: center; color: var(--text-dark);">Insira as credenciais do banco e conecte.</p>';
        statusDot.className = 'status-dot offline';
        statusDot.style.backgroundColor = '';
        statusDot.style.boxShadow = '';
        statusText.textContent = 'Não conectado';
        return;
    }
    
    tablesList.innerHTML = '<div class="loading-spinner" style="font-size: 14px; padding: 20px;"><i class="fa-solid fa-circle-notch fa-spin"></i> Conectando...</div>';
    statusDot.className = 'status-dot';
    statusDot.style.backgroundColor = 'var(--color-warning)';
    statusDot.style.boxShadow = '0 0 8px var(--color-warning)';
    statusText.textContent = 'Conectando...';
    
    let query = '';
    if (dbType === 'sqlite') {
        query = "SELECT name AS table_name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;";
    } else if (dbType === 'postgresql') {
        query = "SELECT table_name AS table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;";
    } else if (dbType === 'mysql') {
        query = "SELECT table_name AS table_name FROM information_schema.tables WHERE table_schema = DATABASE() ORDER BY table_name;";
    }
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/db/query`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                db_type: dbType,
                connection_string: connStr,
                query: query
            })
        });
        
        const data = await res.json();
        
        if (res.status !== 200 || data.status !== 'success') {
            throw new Error(data.detail || 'Erro ao conectar');
        }
        
        statusDot.className = 'status-dot online';
        statusDot.style.backgroundColor = 'var(--color-success)';
        statusDot.style.boxShadow = '0 0 8px var(--color-success)';
        statusText.textContent = 'Conectado';
        
        renderDbTablesList(data.rows);
    } catch (err) {
        console.error('Erro ao conectar ao DB:', err);
        statusDot.className = 'status-dot offline';
        statusDot.style.backgroundColor = 'var(--color-danger)';
        statusDot.style.boxShadow = '0 0 8px var(--color-danger)';
        statusText.textContent = 'Falha na conexão';
        tablesList.innerHTML = `<p class="placeholder-text error-text" style="padding: 20px 0; font-size: 12px; color: var(--color-danger); text-align: center;">Erro: ${err.message}</p>`;
    }
}

function renderDbTablesList(rows) {
    const container = document.getElementById('db-tables-list');
    container.innerHTML = '';
    
    if (rows.length === 0) {
        container.innerHTML = '<p class="placeholder-text" style="padding: 20px 0; font-size: 12px; text-align: center; color: var(--text-dark);">Nenhuma tabela encontrada.</p>';
        return;
    }
    
    rows.forEach(row => {
        const tableName = row.table_name || Object.values(row)[0];
        
        const wrapper = document.createElement('div');
        wrapper.className = 'db-table-wrapper';
        wrapper.style.display = 'flex';
        wrapper.style.flexDirection = 'column';
        wrapper.style.width = '100%';
        wrapper.style.marginBottom = '6px';
        
        const item = document.createElement('div');
        item.className = 'db-table-item';
        item.setAttribute('data-table', tableName);
        
        item.innerHTML = `
            <div class="db-table-item-left">
                <i class="fa-solid fa-table"></i>
                <span title="${tableName}">${tableName}</span>
            </div>
            <i class="fa-solid fa-chevron-right db-chevron" style="font-size: 10px; color: var(--text-dark); transition: transform 0.2s;"></i>
        `;
        
        const schemaPanel = document.createElement('div');
        schemaPanel.className = 'db-table-schema-panel';
        schemaPanel.style.display = 'none';
        schemaPanel.style.padding = '10px 12px';
        schemaPanel.style.background = 'rgba(0, 0, 0, 0.2)';
        schemaPanel.style.borderLeft = '2px solid var(--color-primary, #6366f1)';
        schemaPanel.style.borderRadius = '0 0 var(--border-radius, 8px) var(--border-radius, 8px)';
        schemaPanel.style.borderTop = 'none';
        schemaPanel.style.fontSize = '11px';
        schemaPanel.style.marginTop = '-1px';
        schemaPanel.style.borderRight = '1px solid var(--border-color)';
        schemaPanel.style.borderBottom = '1px solid var(--border-color)';
        
        item.addEventListener('click', (e) => {
            const isCurrentlyActive = item.classList.contains('active');
            
            // Colapsa e limpa todos os outros
            document.querySelectorAll('.db-table-item').forEach(i => {
                i.classList.remove('active');
                const chev = i.querySelector('.db-chevron');
                if (chev) chev.style.transform = '';
            });
            document.querySelectorAll('.db-table-schema-panel').forEach(panel => {
                panel.style.display = 'none';
            });
            
            if (!isCurrentlyActive) {
                item.classList.add('active');
                const chev = item.querySelector('.db-chevron');
                if (chev) chev.style.transform = 'rotate(90deg)';
                schemaPanel.style.display = 'block';
                
                // Carrega estrutura de colunas e ações
                loadTableSchema(tableName, schemaPanel);
                
                // Configura query inicial
                const textarea = document.getElementById('db-sql-textarea');
                textarea.value = `SELECT * FROM ${tableName} LIMIT 50;`;
                
                // Abre aba do Grid Editor por padrão ao clicar na tabela e carrega dados
                switchDbResultsTab('grid');
                loadTableGrid(tableName, 1);
            }
        });
        
        wrapper.appendChild(item);
        wrapper.appendChild(schemaPanel);
        container.appendChild(wrapper);
    });
}

async function loadTableSchema(tableName, schemaContainer) {
    const dbType = document.getElementById('db-type-select').value;
    const connStr = document.getElementById('db-conn-input').value.trim();
    
    schemaContainer.innerHTML = '<div style="color: var(--text-dark); padding: 4px 0;"><i class="fa-solid fa-circle-notch fa-spin"></i> Carregando estrutura...</div>';
    
    let schemaQuery = '';
    if (dbType === 'sqlite') {
        schemaQuery = `PRAGMA table_info("${tableName}");`;
    } else if (dbType === 'postgresql') {
        schemaQuery = `SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = '${tableName}' ORDER BY ordinal_position;`;
    } else if (dbType === 'mysql') {
        schemaQuery = `SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = '${tableName}' AND table_schema = DATABASE() ORDER BY ordinal_position;`;
    }
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/db/query`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                db_type: dbType,
                connection_string: connStr,
                query: schemaQuery
            })
        });
        const data = await res.json();
        if (res.status !== 200 || data.status !== 'success') {
            throw new Error(data.detail || 'Falha ao carregar colunas');
        }
        
        schemaContainer.innerHTML = '';
        
        // 1. Linha de Ações Rápidas
        const actionsRow = document.createElement('div');
        actionsRow.className = 'db-table-actions';
        actionsRow.style.display = 'flex';
        actionsRow.style.gap = '6px';
        actionsRow.style.marginBottom = '10px';
        
        const btnSelect = document.createElement('button');
        btnSelect.className = 'btn btn-secondary';
        btnSelect.style.fontSize = '10px';
        btnSelect.style.padding = '4px 8px';
        btnSelect.style.flex = '1';
        btnSelect.style.cursor = 'pointer';
        btnSelect.innerHTML = '<i class="fa-solid fa-table-list"></i> SELECT 100';
        btnSelect.onclick = (e) => {
            e.stopPropagation();
            const textarea = document.getElementById('db-sql-textarea');
            textarea.value = `SELECT * FROM ${tableName} LIMIT 100;`;
            runSqlQuery();
        };
        
        const btnCount = document.createElement('button');
        btnCount.className = 'btn btn-secondary';
        btnCount.style.fontSize = '10px';
        btnCount.style.padding = '4px 8px';
        btnCount.style.flex = '1';
        btnCount.style.cursor = 'pointer';
        btnCount.innerHTML = '<i class="fa-solid fa-calculator"></i> COUNT(*)';
        btnCount.onclick = (e) => {
            e.stopPropagation();
            const textarea = document.getElementById('db-sql-textarea');
            textarea.value = `SELECT COUNT(*) AS total FROM ${tableName};`;
            runSqlQuery();
        };
        
        actionsRow.appendChild(btnSelect);
        actionsRow.appendChild(btnCount);
        schemaContainer.appendChild(actionsRow);
        
        // 2. Cabeçalho de Colunas
        const colsHeader = document.createElement('div');
        colsHeader.style.display = 'flex';
        colsHeader.style.justifyContent = 'space-between';
        colsHeader.style.color = '#94a3b8';
        colsHeader.style.fontSize = '10px';
        colsHeader.style.fontWeight = 'bold';
        colsHeader.style.borderBottom = '1px solid rgba(255,255,255,0.05)';
        colsHeader.style.paddingBottom = '3px';
        colsHeader.style.marginBottom = '6px';
        colsHeader.innerHTML = '<span>Coluna</span><span>Tipo</span>';
        schemaContainer.appendChild(colsHeader);
        
        const listWrapper = document.createElement('div');
        listWrapper.style.display = 'flex';
        listWrapper.style.flexDirection = 'column';
        listWrapper.style.gap = '4px';
        
        data.rows.forEach(col => {
            let colName = '';
            let colType = '';
            let isPk = false;
            let isNullable = true;
            
            if (dbType === 'sqlite') {
                colName = col.name;
                colType = col.type.toLowerCase();
                isPk = col.pk === 1 || col.pk === true;
                isNullable = col.notnull === 0 || col.notnull === false;
            } else {
                colName = col.column_name || col.COLUMN_NAME;
                colType = (col.data_type || col.DATA_TYPE || '').toLowerCase();
                const nullVal = col.is_nullable || col.IS_NULLABLE;
                isNullable = nullVal === 'YES' || nullVal === 'yes' || nullVal === true;
            }
            
            const colRow = document.createElement('div');
            colRow.style.display = 'flex';
            colRow.style.justifyContent = 'space-between';
            colRow.style.alignItems = 'center';
            colRow.style.fontSize = '11px';
            colRow.style.color = '#e2e8f0';
            
            const leftCol = document.createElement('div');
            leftCol.style.display = 'flex';
            leftCol.style.alignItems = 'center';
            leftCol.style.gap = '4px';
            
            if (isPk) {
                leftCol.innerHTML = '<i class="fa-solid fa-key" style="color: #eab308; font-size: 9px;" title="Chave Primária"></i> ' + `<strong>${colName}</strong>`;
            } else {
                leftCol.innerHTML = '<i class="fa-solid fa-columns" style="color: #94a3b8; font-size: 9px;"></i> ' + `<span>${colName}</span>`;
            }
            
            const rightCol = document.createElement('span');
            rightCol.style.color = '#94a3b8';
            rightCol.style.fontSize = '10px';
            rightCol.textContent = colType + (isNullable ? '' : '!');
            if (!isNullable) {
                rightCol.title = 'NOT NULL';
            }
            
            colRow.appendChild(leftCol);
            colRow.appendChild(rightCol);
            listWrapper.appendChild(colRow);
        });
        
        schemaContainer.appendChild(listWrapper);
    } catch (err) {
        schemaContainer.innerHTML = `<div style="color: var(--color-danger); padding: 4px 0;">Erro: ${err.message}</div>`;
    }
}

// --- BANCO DE DADOS BROWSER ---
async function runSqlQuery() {
    if (!state.activeProjectId) return;
    
    switchDbResultsTab('raw');
    
    const dbType = document.getElementById('db-type-select').value;
    const connString = document.getElementById('db-conn-input').value.trim();
    const query = document.getElementById('db-sql-textarea').value.trim();
    const container = document.getElementById('db-results-table-container');
    const statusLabel = document.getElementById('db-query-status');
    
    if (!connString) {
        alert('Especifique a string de conexão ou caminho do banco de dados.');
        return;
    }
    if (!query) {
        alert('Digite uma query SQL para executar.');
        return;
    }
    
    container.innerHTML = '<div class="loading-spinner"><i class="fa-solid fa-circle-notch fa-spin"></i></div>';
    statusLabel.textContent = 'Executando query...';
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/db/query`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                db_type: dbType,
                connection_string: connString,
                query: query
            })
        });
        
        const data = await res.json();
        
        if (res.status !== 200) {
            container.innerHTML = `<p class="placeholder-text stderr-msg" style="color: var(--color-danger);"><i class="fa-solid fa-triangle-exclamation"></i> ${data.detail}</p>`;
            statusLabel.textContent = 'Falha na consulta';
            return;
        }
        
        statusLabel.textContent = `Query executada com sucesso. Linhas afetadas: ${data.rows_affected}.`;
        
        if (data.rows.length === 0) {
            container.innerHTML = '<p class="placeholder-text">Nenhuma linha retornada para esta consulta.</p>';
            return;
        }
        
        // Renderiza tabela
        const table = document.createElement('table');
        table.className = 'db-table';
        
        // Header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        const keys = Object.keys(data.rows[0]);
        keys.forEach(k => {
            const th = document.createElement('th');
            th.textContent = k;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Body
        const tbody = document.createElement('tbody');
        data.rows.forEach(row => {
            const tr = document.createElement('tr');
            keys.forEach(k => {
                const td = document.createElement('td');
                td.textContent = row[k] !== null ? row[k] : 'NULL';
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        
        container.innerHTML = '';
        container.appendChild(table);
        
    } catch (err) {
        container.innerHTML = `<p class="placeholder-text stderr-msg" style="color: var(--color-danger);"><i class="fa-solid fa-triangle-exclamation"></i> Erro na requisição: ${err.message}</p>`;
        statusLabel.textContent = 'Erro';
    }
}

// --- DATABASE GRID EDITOR ---
function switchDbResultsTab(tabId) {
    document.querySelectorAll('.db-results-tab-btn').forEach(btn => {
        btn.classList.remove('active');
        btn.style.borderBottom = '2px solid transparent';
        btn.style.color = 'var(--text-muted)';
        btn.style.fontWeight = '500';
    });
    
    const activeBtn = document.getElementById(tabId === 'raw' ? 'btn-tab-raw-results' : 'btn-tab-grid-editor');
    if (activeBtn) {
        activeBtn.classList.add('active');
        activeBtn.style.borderBottom = '2px solid var(--color-primary)';
        activeBtn.style.color = 'var(--text-light)';
        activeBtn.style.fontWeight = '600';
    }
    
    document.getElementById('db-results-table-container').style.display = tabId === 'raw' ? 'block' : 'none';
    document.getElementById('db-grid-editor-container').style.display = tabId === 'grid' ? 'flex' : 'none';
}

async function loadTableGrid(tableName, page = 1) {
    if (!state.activeProjectId) return;
    
    state.gridActiveTable = tableName;
    state.gridCurrentPage = page;
    
    const tableEl = document.getElementById('db-grid-table');
    tableEl.innerHTML = `<tr><td style="text-align: center; padding: 20px; color: var(--text-muted);"><i class="fa-solid fa-circle-notch fa-spin"></i> Carregando dados...</td></tr>`;
    
    const dbType = document.getElementById('db-type-select').value;
    const connStr = document.getElementById('db-conn-input').value.trim();
    const statusLabel = document.getElementById('db-query-status');
    
    if (!connStr) {
        tableEl.innerHTML = `<tr><td style="text-align: center; padding: 20px; color: var(--color-danger);">Conecte ao banco de dados para ver os dados.</td></tr>`;
        return;
    }
    
    try {
        // 1. Carrega Schema da tabela
        const schemaRes = await fetch(`/api/projects/${state.activeProjectId}/db/tables/${tableName}/schema`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                db_type: dbType,
                connection_string: connStr
            })
        });
        const schemaData = await schemaRes.json();
        if (schemaRes.status !== 200 || schemaData.status !== 'success') {
            throw new Error(schemaData.detail || 'Erro ao buscar o esquema da tabela.');
        }
        state.gridColumns = schemaData.columns;
        
        // 2. Carrega Linhas com paginação
        const limit = 50;
        const offset = (page - 1) * limit;
        const rowsRes = await fetch(`/api/projects/${state.activeProjectId}/db/tables/${tableName}/rows`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                db_type: dbType,
                connection_string: connStr,
                limit: limit,
                offset: offset
            })
        });
        const rowsData = await rowsRes.json();
        if (rowsRes.status !== 200 || rowsData.status !== 'success') {
            throw new Error(rowsData.detail || 'Erro ao buscar registros da tabela.');
        }
        
        state.gridTotalRows = rowsData.total_count;
        
        // Atualiza Toolbar
        document.getElementById('grid-table-name-label').textContent = tableName;
        const totalPages = Math.max(1, Math.ceil(state.gridTotalRows / limit));
        document.getElementById('grid-page-info').textContent = `Página ${page} de ${totalPages}`;
        document.getElementById('grid-total-info').textContent = `(Total: ${state.gridTotalRows})`;
        
        document.getElementById('grid-btn-prev').disabled = page <= 1;
        document.getElementById('grid-btn-next').disabled = page >= totalPages;
        
        statusLabel.textContent = `Tabela ${tableName} carregada (Visual Grid).`;
        
        // Renderiza
        renderTableGrid(rowsData.rows);
    } catch (err) {
        tableEl.innerHTML = `<tr><td style="text-align: center; padding: 20px; color: var(--color-danger);"><i class="fa-solid fa-triangle-exclamation"></i> Erro: ${err.message}</td></tr>`;
        statusLabel.textContent = 'Erro ao carregar grid';
    }
}

function renderTableGrid(rows) {
    const tableEl = document.getElementById('db-grid-table');
    tableEl.innerHTML = '';
    
    // 1. Cabeçalho (Header)
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    
    // Checkbox Header
    const thCheck = document.createElement('th');
    thCheck.className = 'checkbox-cell';
    thCheck.innerHTML = '<input type="checkbox" id="grid-header-select-all" style="cursor: pointer;">';
    headerRow.appendChild(thCheck);
    
    // Colunas de dados
    state.gridColumns.forEach(col => {
        const th = document.createElement('th');
        th.style.padding = '10px 14px';
        th.style.fontWeight = '600';
        th.style.color = 'var(--text-muted)';
        th.style.borderBottom = '1px solid var(--border-color)';
        th.style.background = 'rgba(255,255,255,0.03)';
        
        let label = col.name;
        if (col.primary_key) {
            th.style.color = '#eab308';
            label += ' <i class="fa-solid fa-key" style="color: #eab308; font-size: 9px;" title="Chave Primária"></i>';
        }
        th.innerHTML = label;
        headerRow.appendChild(th);
    });
    
    thead.appendChild(headerRow);
    tableEl.appendChild(thead);
    
    // 2. Corpo (Body)
    const tbody = document.createElement('tbody');
    
    if (rows.length === 0) {
        const trEmpty = document.createElement('tr');
        const tdEmpty = document.createElement('td');
        tdEmpty.colSpan = state.gridColumns.length + 1;
        tdEmpty.style.textAlign = 'center';
        tdEmpty.style.padding = '30px';
        tdEmpty.style.color = 'var(--text-dark)';
        tdEmpty.textContent = 'Nenhum registro encontrado nesta tabela.';
        trEmpty.appendChild(tdEmpty);
        tbody.appendChild(trEmpty);
    } else {
        rows.forEach(row => {
            const tr = document.createElement('tr');
            tr.style.transition = 'background-color 0.15s';
            tr.style.borderBottom = '1px solid var(--border-color)';
            
            // Checkbox do registro
            const tdCheck = document.createElement('td');
            tdCheck.className = 'checkbox-cell';
            tdCheck.innerHTML = '<input type="checkbox" class="grid-row-checkbox" style="cursor: pointer;">';
            
            // Toggle highlight row on select
            const cb = tdCheck.querySelector('input');
            cb.addEventListener('change', () => {
                if (cb.checked) {
                    tr.classList.add('selected-row');
                } else {
                    tr.classList.remove('selected-row');
                }
            });
            tr.appendChild(tdCheck);
            
            // Células de valor
            state.gridColumns.forEach(col => {
                const td = document.createElement('td');
                td.style.padding = '10px 14px';
                td.style.borderBottom = '1px solid var(--border-color)';
                
                const val = row[col.name];
                td.gridValue = val; // Store native typed value
                
                if (col.primary_key) {
                    td.className = 'pk-col';
                    td.style.fontWeight = '500';
                } else {
                    td.className = 'editable';
                    td.addEventListener('dblclick', () => makeGridCellEditable(td));
                }
                
                renderCellText(td, val);
                tr.appendChild(td);
            });
            
            tbody.appendChild(tr);
        });
    }
    
    tableEl.appendChild(tbody);
    
    // Lógica Select All
    const selectAllCheck = document.getElementById('grid-header-select-all');
    if (selectAllCheck) {
        selectAllCheck.addEventListener('change', (e) => {
            const checked = e.target.checked;
            document.querySelectorAll('.grid-row-checkbox').forEach(cb => {
                cb.checked = checked;
                const tr = cb.parentElement.parentElement;
                if (checked) {
                    tr.classList.add('selected-row');
                } else {
                    tr.classList.remove('selected-row');
                }
            });
        });
    }
}

function renderCellText(cell, val) {
    if (val === null || val === undefined) {
        cell.innerHTML = '<span style="color: rgba(255,255,255,0.25); font-style: italic;">NULL</span>';
    } else {
        cell.textContent = val;
    }
}

function makeGridCellEditable(cell) {
    if (cell.classList.contains('editing')) return;
    
    const colName = state.gridColumns[cell.cellIndex - 1].name; // -1 because index 0 is checkbox
    const originalValue = cell.gridValue;
    
    cell.classList.add('editing');
    
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'grid-cell-input';
    input.value = (originalValue === null || originalValue === undefined) ? '' : originalValue;
    
    cell.innerHTML = '';
    cell.appendChild(input);
    input.focus();
    input.select();
    
    let finished = false;
    
    async function saveEdit() {
        if (finished) return;
        finished = true;
        
        let newValue = input.value;
        if (input.value.trim() === '') {
            newValue = originalValue === null ? null : '';
        }
        
        // Se nada mudou, cancela
        if (newValue === originalValue) {
            cell.classList.remove('editing');
            renderCellText(cell, originalValue);
            return;
        }
        
        cell.classList.remove('editing');
        cell.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin" style="color: var(--color-primary);"></i>';
        
        try {
            const tr = cell.parentElement;
            const keys = {};
            const hasPk = state.gridColumns.some(c => c.primary_key);
            
            state.gridColumns.forEach((col, idx) => {
                const rowCell = tr.cells[idx + 1];
                const val = rowCell.gridValue;
                
                if (hasPk) {
                    if (col.primary_key) {
                        keys[col.name] = val;
                    }
                } else {
                    keys[col.name] = val;
                }
            });
            
            const values = {};
            values[colName] = newValue;
            
            const dbType = document.getElementById('db-type-select').value;
            const connStr = document.getElementById('db-conn-input').value.trim();
            const statusLabel = document.getElementById('db-query-status');
            
            const res = await fetch(`/api/projects/${state.activeProjectId}/db/tables/${state.gridActiveTable}/update-row`, {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify({
                    db_type: dbType,
                    connection_string: connStr,
                    keys: keys,
                    values: values
                })
            });
            
            const data = await res.json();
            if (res.status !== 200 || data.status !== 'success') {
                throw new Error(data.detail || 'Erro na requisição');
            }
            
            cell.gridValue = newValue;
            renderCellText(cell, newValue);
            statusLabel.textContent = `Linha atualizada com sucesso. Linhas afetadas: ${data.rows_affected}.`;
        } catch (err) {
            alert(`Erro ao atualizar registro: ${err.message}`);
            renderCellText(cell, originalValue);
        }
    }
    
    function cancelEdit() {
        if (finished) return;
        finished = true;
        cell.classList.remove('editing');
        renderCellText(cell, originalValue);
    }
    
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            saveEdit();
        } else if (e.key === 'Escape') {
            cancelEdit();
        }
    });
    
    input.addEventListener('blur', () => {
        saveEdit();
    });
}

async function insertGridRow() {
    if (!state.activeProjectId || !state.gridActiveTable) return;
    
    const tableEl = document.getElementById('db-grid-table');
    const tbody = tableEl.querySelector('tbody');
    if (!tbody) return;
    
    // Remove o placeholder se houver
    if (tbody.rows.length === 1 && tbody.rows[0].cells[0].colSpan > 1) {
        tbody.innerHTML = '';
    }
    
    const tr = document.createElement('tr');
    tr.className = 'new-row-tr';
    tr.style.background = 'rgba(16, 185, 129, 0.05)';
    tr.style.borderBottom = '1px solid var(--border-color)';
    
    // Célula de Ações (Salvar / Cancelar)
    const tdAction = document.createElement('td');
    tdAction.className = 'checkbox-cell';
    tdAction.innerHTML = `
        <i class="fa-solid fa-floppy-disk grid-save-row-btn" style="color: var(--color-success, #10b981); cursor: pointer; padding: 4px; font-size: 13px;" title="Salvar Linha"></i>
        <i class="fa-solid fa-xmark grid-cancel-row-btn" style="color: var(--color-danger, #ef4444); cursor: pointer; padding: 4px; font-size: 13px; margin-left: 6px;" title="Cancelar"></i>
    `;
    tr.appendChild(tdAction);
    
    // Campos de input para cada coluna
    state.gridColumns.forEach(col => {
        const td = document.createElement('td');
        td.style.padding = '6px 14px';
        td.style.borderBottom = '1px solid var(--border-color)';
        
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'grid-cell-input';
        input.style.width = '100%';
        
        if (col.primary_key) {
            input.placeholder = '(auto-increment / opcional)';
        } else {
            input.placeholder = `${col.name}...`;
        }
        
        td.appendChild(input);
        tr.appendChild(td);
    });
    
    // Insere no topo do tbody
    tbody.insertBefore(tr, tbody.firstChild);
    
    // Foca no primeiro input
    const firstInput = tr.querySelector('input');
    if (firstInput) firstInput.focus();
    
    // Event listeners
    const saveBtn = tdAction.querySelector('.grid-save-row-btn');
    const cancelBtn = tdAction.querySelector('.grid-cancel-row-btn');
    
    let isSaving = false;
    
    async function executeSave() {
        if (isSaving) return;
        isSaving = true;
        
        const values = {};
        state.gridColumns.forEach((col, idx) => {
            const inputVal = tr.cells[idx + 1].querySelector('input').value.trim();
            if (inputVal !== '') {
                values[col.name] = inputVal;
            }
        });
        
        try {
            const dbType = document.getElementById('db-type-select').value;
            const connStr = document.getElementById('db-conn-input').value.trim();
            const statusLabel = document.getElementById('db-query-status');
            
            const res = await fetch(`/api/projects/${state.activeProjectId}/db/tables/${state.gridActiveTable}/insert-row`, {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify({
                    db_type: dbType,
                    connection_string: connStr,
                    values: values
                })
            });
            
            const data = await res.json();
            if (res.status !== 200 || data.status !== 'success') {
                throw new Error(data.detail || 'Erro ao inserir linha');
            }
            
            statusLabel.textContent = 'Novo registro inserido com sucesso.';
            loadTableGrid(state.gridActiveTable, state.gridCurrentPage);
        } catch (err) {
            alert(`Erro ao inserir linha: ${err.message}`);
            isSaving = false;
        }
    }
    
    saveBtn.addEventListener('click', executeSave);
    cancelBtn.addEventListener('click', () => {
        tr.remove();
        // Se a tabela ficou vazia, recarrega para mostrar placeholder
        if (tbody.rows.length === 0) {
            loadTableGrid(state.gridActiveTable, state.gridCurrentPage);
        }
    });
    
    tr.querySelectorAll('input').forEach(input => {
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                executeSave();
            } else if (e.key === 'Escape') {
                tr.remove();
                if (tbody.rows.length === 0) {
                    loadTableGrid(state.gridActiveTable, state.gridCurrentPage);
                }
            }
        });
    });
}

async function deleteSelectedGridRows() {
    if (!state.activeProjectId || !state.gridActiveTable) return;
    
    const checkedCheckboxes = document.querySelectorAll('.grid-row-checkbox:checked');
    if (checkedCheckboxes.length === 0) {
        alert('Selecione pelo menos uma linha para excluir.');
        return;
    }
    
    if (!confirm(`Deseja realmente excluir as ${checkedCheckboxes.length} linhas selecionadas?`)) {
        return;
    }
    
    const dbType = document.getElementById('db-type-select').value;
    const connStr = document.getElementById('db-conn-input').value.trim();
    const statusLabel = document.getElementById('db-query-status');
    
    statusLabel.textContent = `Excluindo ${checkedCheckboxes.length} registros...`;
    
    let deletedCount = 0;
    
    try {
        for (const cb of checkedCheckboxes) {
            const tr = cb.parentElement.parentElement;
            const keys = {};
            const hasPk = state.gridColumns.some(c => c.primary_key);
            
            state.gridColumns.forEach((col, idx) => {
                const cell = tr.cells[idx + 1];
                const val = cell.gridValue;
                
                if (hasPk) {
                    if (col.primary_key) {
                        keys[col.name] = val;
                    }
                } else {
                    keys[col.name] = val;
                }
            });
            
            const res = await fetch(`/api/projects/${state.activeProjectId}/db/tables/${state.gridActiveTable}/delete-row`, {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify({
                    db_type: dbType,
                    connection_string: connStr,
                    keys: keys
                })
            });
            const data = await res.json();
            if (res.status === 200 && data.status === 'success') {
                deletedCount++;
            }
        }
        
        statusLabel.textContent = `${deletedCount} registros excluídos com sucesso.`;
        loadTableGrid(state.gridActiveTable, state.gridCurrentPage);
    } catch (err) {
        alert(`Erro ao deletar registros: ${err.message}`);
        loadTableGrid(state.gridActiveTable, state.gridCurrentPage);
    }
}

// --- GIT BRIDGE ---
async function loadGitStatus(forceFetch = false) {
    const container = document.getElementById('git-status-detail');
    const initPanel = document.getElementById('git-init-panel');
    const deployPanel = document.getElementById('git-deploy-panel');
    const shouldFetch = forceFetch === true;
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/git/status`);
        const status = await res.json();
        
        if (!status.is_git) {
            container.innerHTML = `
                <div class="git-status-info">
                    <p><strong>Status:</strong> Não é um repositório Git ou Git não instalado.</p>
                </div>
            `;
            initPanel.style.display = 'block';
            deployPanel.style.display = 'none';
            const graphPanel = document.getElementById('git-graph-panel');
            if (graphPanel) graphPanel.style.display = 'none';
            return;
        }
        
        initPanel.style.display = 'none';
        deployPanel.style.display = 'block';
        
        await loadGitBranches(status.current_branch, shouldFetch);
        state.activeProjectRemoteUrl = status.remote_url || '';
        updateGitGeneratedCommand();
        
        let html = `
            <div class="git-status-info" style="margin-bottom: 14px;">
                <p><strong>Branch Ativa:</strong> 
                    <span class="dropdown-container" style="display: inline-block; position: relative;">
                        <button type="button" class="btn btn-secondary btn-sm dropdown-trigger" id="btn-branch-actions" style="margin-left: 8px; padding: 4px 8px; font-size: 12px; display: inline-flex; align-items: center; gap: 6px;">
                            <code style="font-family: var(--font-mono); color: var(--color-primary);">${status.current_branch}</code>
                            <i class="fa-solid fa-chevron-down" style="font-size: 10px; color: var(--text-muted);"></i>
                        </button>
                        <div class="dropdown-menu" id="branch-actions-menu" style="position: absolute; top: 100%; left: 8px; z-index: 1000;">
                            <button type="button" class="dropdown-item" id="btn-dropdown-git-checkout"><i class="fa-solid fa-right-to-bracket"></i> Checkout branch</button>
                            <button type="button" class="dropdown-item" id="btn-dropdown-create-branch"><i class="fa-solid fa-plus"></i> Create new branch</button>
                            <button type="button" class="dropdown-item" id="btn-dropdown-refresh-branches"><i class="fa-solid fa-arrows-rotate"></i> Refresh branches</button>
                            <button type="button" class="dropdown-item" id="btn-dropdown-git-pull"><i class="fa-solid fa-cloud-arrow-down"></i> Git pull</button>
                            <button type="button" class="dropdown-item" id="btn-dropdown-git-push"><i class="fa-solid fa-cloud-arrow-up"></i> Git push</button>
                            <button type="button" class="dropdown-item" id="btn-dropdown-git-merge"><i class="fa-solid fa-code-merge"></i> Git merge</button>
                            <button type="button" class="dropdown-item" id="btn-dropdown-git-abort-merge" style="color: var(--color-danger);"><i class="fa-solid fa-ban"></i> Abort merge</button>
                            <button type="button" class="dropdown-item" id="btn-dropdown-git-pr"><i class="fa-solid fa-code-pull-request"></i> Criar Pull Request</button>
                        </div>

                    </span>
                </p>
                <p><strong>Status do Repositório:</strong> ${status.is_clean ? '<span style="color: var(--color-success)">Limpo (Sem alterações pendentes)</span>' : '<span style="color: var(--color-warning)">Alterações não commitadas</span>'}</p>
            </div>
        `;
        
        if (!status.is_clean) {
            html += '<div class="git-files-list">';
            status.staged.forEach(f => {
                html += `<div class="git-file-item"><span>${f}</span><span class="git-tag staged">staged</span></div>`;
            });
            status.modified.forEach(f => {
                html += `<div class="git-file-item"><span>${f}</span><span class="git-tag modified">modificado</span></div>`;
            });
            status.untracked.forEach(f => {
                html += `<div class="git-file-item"><span>${f}</span><span class="git-tag untracked">untracked</span></div>`;
            });
            status.deleted.forEach(f => {
                html += `<div class="git-file-item"><span>${f}</span><span class="git-tag deleted">removido</span></div>`;
            });
            html += '</div>';
        }
        
        container.innerHTML = html;
        
        const dropdownBtn = document.getElementById('btn-branch-actions');
        const dropdownMenu = document.getElementById('branch-actions-menu');
        
        if (dropdownBtn && dropdownMenu) {
            dropdownBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const isShown = dropdownMenu.classList.contains('branch-actions-menu-open') || dropdownMenu.style.display === 'block';
                closeAllDropdowns();
                if (!isShown) {
                    dropdownMenu.classList.add('branch-actions-menu-open');
                    dropdownMenu.style.setProperty('display', 'flex', 'important');
                    dropdownBtn.setAttribute('aria-expanded', 'true');
                } else {
                    dropdownBtn.setAttribute('aria-expanded', 'false');
                }
            });
            
            document.getElementById('btn-dropdown-git-checkout').addEventListener('click', (e) => {
                e.stopPropagation();
                closeAllDropdowns();
                openCheckoutModal();
            });

            document.getElementById('btn-dropdown-create-branch').addEventListener('click', (e) => {
                e.stopPropagation();
                closeAllDropdowns();
                promptCreateBranch();
            });
            
            document.getElementById('btn-dropdown-refresh-branches').addEventListener('click', (e) => {
                e.stopPropagation();
                closeAllDropdowns();
                loadGitStatus(true);
            });
            
            document.getElementById('btn-dropdown-git-pull').addEventListener('click', (e) => {
                e.stopPropagation();
                closeAllDropdowns();
                runGitPull();
            });

            document.getElementById('btn-dropdown-git-push').addEventListener('click', (e) => {
                e.stopPropagation();
                closeAllDropdowns();
                runGitPush();
            });
            
            document.getElementById('btn-dropdown-git-merge').addEventListener('click', (e) => {
                e.stopPropagation();
                closeAllDropdowns();
                openMergeModal();
            });

            document.getElementById('btn-dropdown-git-abort-merge').addEventListener('click', (e) => {
                e.stopPropagation();
                closeAllDropdowns();
                runGitAbortMerge();
            });
            
            document.getElementById('btn-dropdown-git-pr').addEventListener('click', (e) => {
                e.stopPropagation();
                closeAllDropdowns();
                openPRModal();
            });
        }
        
        // Carrega também o gráfico de commits
        await loadGitGraph();
        
    } catch (err) {
        container.innerHTML = `<p class="placeholder-text error-text">Erro ao buscar status do Git: ${err.message}</p>`;
        const graphPanel = document.getElementById('git-graph-panel');
        if (graphPanel) graphPanel.style.display = 'none';
    }
}

async function loadGitGraph() {
    if (!state.activeProjectId) return;
    const panel = document.getElementById('git-graph-panel');
    const container = document.getElementById('git-graph-container');
    if (!panel || !container) return;
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/git/graph`, {
            headers: getHeaders()
        });
        const data = await res.json();
        
        if (!data.is_git || data.is_empty) {
            panel.style.display = 'none';
            return;
        }
        
        panel.style.display = 'block';
        container.innerHTML = '';
        
        if (data.graph && data.graph.length > 0) {
            data.graph.forEach(line => {
                const parsedLine = parseGitGraphLine(line);
                const lineDiv = document.createElement('div');
                lineDiv.className = 'git-graph-line';
                lineDiv.style.fontFamily = 'monospace';
                lineDiv.style.whiteSpace = 'pre';
                lineDiv.innerHTML = parsedLine;
                container.appendChild(lineDiv);
            });
        } else {
            container.innerHTML = '<div style="color: var(--text-dark); padding: 10px;">Sem histórico de commits disponível.</div>';
        }
    } catch (err) {
        console.error('Erro ao carregar o gráfico do Git:', err);
        container.innerHTML = `<div style="color: var(--color-danger); padding: 10px;">Erro: ${err.message}</div>`;
    }
}

function parseGitGraphLine(line) {
    let escaped = line.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    const hashRegex = /\b([a-f0-9]{7,8})\b/;
    const hashMatch = escaped.match(hashRegex);
    
    let drawingPart = '';
    let textPart = escaped;
    
    if (hashMatch) {
        const hashIndex = escaped.indexOf(hashMatch[0]);
        drawingPart = escaped.substring(0, hashIndex);
        textPart = escaped.substring(hashIndex);
    } else {
        drawingPart = escaped;
        textPart = '';
    }
    
    drawingPart = drawingPart.replace(/([*|/\\_-])/g, '<span style="color: #6366f1; font-weight: bold;">$1</span>');
    
    if (textPart) {
        textPart = textPart.replace(/^([a-f0-9]{7,8})/, '<span style="color: #818cf8; font-weight: bold;">$1</span>');
        textPart = textPart.replace(/(\((?:HEAD|origin|refs|tag|main|dev|homolog|master)[^)]*\))/, '<span style="color: #fb7185; font-weight: 600;">$1</span>');
        textPart = textPart.replace(/\(([^)]+ ago|[^)]+ old|[^)]+ minutes|[^)]+ hours|[^)]+ days|[^)]+ weeks|[^)]+ months|[^)]+ years)\)/, '<span style="color: #94a3b8;">($1)</span>');
        textPart = textPart.replace(/&lt;([^&]+)&gt;/, '<span style="color: #34d399; font-style: italic;">&lt;$1&gt;</span>');
    }
    
    return drawingPart + textPart;
}

function normalizeGitBranchName(branchName) {
    return String(branchName || '')
        .replace(/^refs\/heads\//, '')
        .replace(/^refs\/remotes\//, '')
        .replace(/^origin\//, '')
        .trim();
}

function findGitBranchOption(selectEl, preferredBranch) {
    const normalizedPreferred = normalizeGitBranchName(preferredBranch);
    return Array.from(selectEl.options).find(option => normalizeGitBranchName(option.value) === normalizedPreferred);
}

function syncGitBranchCustomSelect() {
    const branchSelect = document.getElementById('git-branch-input');
    const wrapper = branchSelect?.nextElementSibling;
    if (wrapper && wrapper.classList.contains('custom-select-container')) {
        syncCustomSelectValue(branchSelect, wrapper);
    }
}

function getGitDeployBranchValue() {
    const branchSelect = document.getElementById('git-branch-input');
    if (!branchSelect) return 'dev';

    const devOption = findGitBranchOption(branchSelect, 'dev');
    if (devOption) {
        branchSelect.value = devOption.value;
        syncGitBranchCustomSelect();
        return devOption.value;
    }

    return branchSelect.value.trim() || 'dev';
}

async function loadGitBranches(currentBranch, forceFetch = false) {
    const branchSelect = document.getElementById('git-branch-input');
    if (!branchSelect) return;

    try {
        const url = `/api/projects/${state.activeProjectId}/git/branches` + (forceFetch ? '?fetch=true' : '');
        const res = await fetch(url);
        const data = await res.json();
        if (data.status === 'success') {
            const fallbackBranch = currentBranch || data.current_branch || 'dev';
            
            branchSelect.innerHTML = '';
            
            if (data.local && data.local.length > 0) {
                const localGroup = document.createElement('optgroup');
                localGroup.label = 'Branches Locais';
                data.local.forEach(branch => {
                    const opt = document.createElement('option');
                    opt.value = branch;
                    opt.textContent = normalizeGitBranchName(branch) === 'dev' ? `${branch} · padrão` : branch;
                    localGroup.appendChild(opt);
                });
                branchSelect.appendChild(localGroup);
            }
            
            if (data.remote && data.remote.length > 0) {
                const remoteGroup = document.createElement('optgroup');
                remoteGroup.label = 'Branches Remotas';
                data.remote.forEach(branch => {
                    const displayVal = branch.startsWith('origin/') ? branch : `origin/${branch}`;
                    const opt = document.createElement('option');
                    opt.value = branch;
                    opt.textContent = normalizeGitBranchName(branch) === 'dev' ? `${displayVal} · padrão` : displayVal;
                    remoteGroup.appendChild(opt);
                });
                branchSelect.appendChild(remoteGroup);
            }

            if (branchSelect.options.length === 0) {
                const opt = document.createElement('option');
                opt.value = 'dev';
                opt.textContent = 'dev · padrão';
                branchSelect.appendChild(opt);
            }
            
            const devOption = findGitBranchOption(branchSelect, 'dev');
            branchSelect.value = devOption ? devOption.value : fallbackBranch;
            syncGitBranchCustomSelect();
        }
    } catch (err) {
        console.error('Erro ao carregar branches:', err);
    }
}

async function initGitRepo() {
    const remoteUrl = document.getElementById('git-remote-url-input').value.trim();
    appendGitConsole('Iniciando git init...');
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/git/init`, {
            method: 'POST',
            headers: getHeaders()
        });
        
        const data = await res.json();
        
        if (res.status === 200) {
            appendGitConsole(`Repositório Git inicializado! Remotos configurados: ${data.remotes.join(', ')}`);
            // Se informou URL de remoto, atualiza no DB do GitIDE
            if (remoteUrl) {
                // Atualização lógica rápida
                state.activeProject.git_remote = remoteUrl;
            }
            loadGitStatus();
        } else {
            let errorMsg = data.detail;
            if (typeof errorMsg === 'object') {
                errorMsg = JSON.stringify(errorMsg);
            }
            appendGitConsole(`Erro ao inicializar Git: ${errorMsg || 'Erro desconhecido'}`, true);
        }
        
    } catch (err) {
        appendGitConsole(`Erro de conexão: ${err.message}`, true);
    }
}

async function runGitDeploy() {
    const message = document.getElementById('git-commit-msg').value.trim();
    const branch = getGitDeployBranchValue();
    
    if (!message) {
        alert('Digite uma mensagem de commit/deploy.');
        return;
    }
    
    appendGitConsole(`Iniciando deploy (Staging + Commit + Push para branch "${branch}")...`);
    const btn = document.getElementById('btn-git-deploy');
    btn.disabled = true;
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/git/deploy`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                commit_message: message,
                branch: branch || null
            })
        });
        
        const data = await res.json();
        
        if (res.status === 200) {
            appendGitConsole(`Deploy concluído com sucesso! Action: ${data.action}`);
            if (data.commit_sha) {
                appendGitConsole(`Commit SHA: ${data.commit_sha}`);
            }
            appendGitConsole(`Push logs:\n${data.push_summary.join('\n')}`);
            document.getElementById('git-commit-msg').value = '';
            loadGitStatus();
        } else {
            appendGitConsole(`Erro no Deploy: ${data.detail}`, true);
        }
        
    } catch (err) {
        appendGitConsole(`Erro de rede no deploy: ${err.message}`, true);
    } finally {
        btn.disabled = false;
    }
}

async function runGitPull() {
    const branch = getGitDeployBranchValue();
    appendGitConsole(`Puxando alterações (Git Pull) para branch "${branch || 'dev'}"...`);
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/git/pull?branch=${encodeURIComponent(branch)}`, {
            method: 'POST',
            headers: getHeaders()
        });
        
        const data = await res.json();
        
        if (res.status === 200) {
            appendGitConsole(`Git pull concluído:\n${data.details.join('\n')}`);
            loadGitStatus();
        } else {
            appendGitConsole(`Erro no Git Pull: ${data.detail}`, true);
        }
        
    } catch (err) {
        appendGitConsole(`Erro de conexão no Git Pull: ${err.message}`, true);
    }
}

function appendGitConsole(text, isError = false) {
    const consoleDiv = document.getElementById('git-console-output');
    const line = document.createElement('div');
    line.className = `terminal-line ${isError ? 'stderr-msg' : ''}`;
    line.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
    consoleDiv.appendChild(line);
    consoleDiv.scrollTop = consoleDiv.scrollHeight;
}

// --- HISTÓRICO & LOGS GERAIS ---
async function loadActivityLogs() {
    const container = document.getElementById('activity-logs-list');
    container.innerHTML = '<div class="loading-spinner"><i class="fa-solid fa-circle-notch fa-spin"></i></div>';
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/logs`);
        const logs = await res.json();
        
        container.innerHTML = '';
        if (logs.length === 0) {
            container.innerHTML = '<p class="placeholder-text">Nenhuma atividade registrada ainda para este projeto.</p>';
            return;
        }
        
        logs.forEach(log => {
            const card = document.createElement('div');
            card.className = 'log-card';
            
            const dateStr = new Date(log.timestamp).toLocaleString();
            const badgeClass = log.action_type.toLowerCase();
            
            const hasDiffButton = log.has_snapshot;
            const diffButtonHtml = hasDiffButton ? `
                <div class="log-actions" style="margin-top: 8px; display: flex; justify-content: flex-end;">
                    <button class="btn btn-sm btn-secondary btn-view-diff" data-log-id="${log.id}">
                        <i class="fa-solid fa-code-compare"></i> Ver Alterações
                    </button>
                </div>
            ` : '';
            
            card.innerHTML = `
                <div class="log-meta">
                    <span class="log-action-badge ${badgeClass}">${log.action_type}</span>
                    <span>${dateStr}</span>
                </div>
                <div class="log-details">${log.details}</div>
                ${diffButtonHtml}
            `;
            
            if (hasDiffButton) {
                const btn = card.querySelector('.btn-view-diff');
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    toggleLogDiff(log.id, card, btn);
                });
            }
            
            container.appendChild(card);
        });
        
    } catch (err) {
        container.innerHTML = `<p class="placeholder-text error-text">Erro ao ler logs: ${err.message}</p>`;
    }
}

async function loadAllSnapshots() {
    const container = document.getElementById('all-snapshots-list');
    container.innerHTML = '<div class="loading-spinner"><i class="fa-solid fa-circle-notch fa-spin"></i></div>';
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/snapshots`);
        const snaps = await res.json();
        
        container.innerHTML = '';
        if (snaps.length === 0) {
            container.innerHTML = '<p class="placeholder-text">Nenhum snapshot de arquivo foi salvo.</p>';
            return;
        }
        
        snaps.forEach(snap => {
            const card = document.createElement('div');
            card.className = 'snapshot-item';
            
            const dateStr = new Date(snap.timestamp).toLocaleString();
            card.innerHTML = `
                <div class="snapshot-info">
                    <span class="snapshot-time">${snap.filepath}</span>
                    <span class="snapshot-hash">Salvo em ${dateStr} (Hash: ${snap.hash.substring(0, 8)})</span>
                </div>
                <button class="btn btn-sm btn-secondary btn-all-rollback" data-id="${snap.id}"><i class="fa-solid fa-rotate-left"></i> Restaurar</button>
            `;
            
            card.querySelector('.btn-all-rollback').addEventListener('click', () => {
                rollbackToSnapshot(snap.id).then(() => {
                    loadAllSnapshots();
                    loadActivityLogs();
                });
            });
            container.appendChild(card);
        });
        
    } catch (err) {
        container.innerHTML = `<p class="placeholder-text error-text">Erro ao ler snapshots: ${err.message}</p>`;
    }
}

// --- DIRETÓRIO LOCAL BROWSER ---
async function openDirectoryBrowser(targetInputId) {
    state.dirBrowserTargetInput = targetInputId;
    const modal = document.getElementById('modal-dir-browser');
    modal.classList.add('active');
    
    const inputFolder = document.getElementById('dir-browser-new-folder-name');
    if (inputFolder) inputFolder.value = '';
    
    // Inicia no caminho já digitado ou vazio (home)
    let startPath = '';
    if (targetInputId === 'local-selected-path') {
        startPath = state.localSelectedPath || '';
    } else if (targetInputId) {
        const input = document.getElementById(targetInputId);
        startPath = input ? input.value.trim() : '';
    }
    
    // Normaliza para /workspace se for Linux e o caminho for vazio ou Windows
    if (state.os === 'Linux' && (!startPath || startPath.includes('\\') || startPath.includes(':'))) {
        startPath = '/workspace';
    }
    
    await loadBrowserDirectories(startPath);
}

function closeDirectoryBrowser() {
    document.getElementById('modal-dir-browser').classList.remove('active');
}

async function loadBrowserDirectories(path) {
    const listContainer = document.getElementById('dir-browser-list');
    const drivesContainer = document.getElementById('dir-browser-drives');
    const breadcrumbsContainer = document.getElementById('dir-browser-breadcrumbs');
    const currentSelectedText = document.getElementById('dir-browser-current-selected');
    
    listContainer.innerHTML = '<div class="loading-spinner"><i class="fa-solid fa-circle-notch fa-spin"></i></div>';
    
    try {
        let url = '/api/system/dirs';
        if (path) {
            url += `?path=${encodeURIComponent(path)}`;
        }
        
        const res = await fetch(url);
        const data = await res.json();
        
        if (res.status !== 200) throw new Error(data.detail);
        
        state.currentBrowserPath = data.current_path;
        currentSelectedText.textContent = data.current_path;
        
        // 1. Renderiza Drives
        drivesContainer.innerHTML = '';
        if (data.drives && data.drives.length > 0) {
            data.drives.forEach(drive => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'btn btn-sm btn-secondary';
                btn.style.padding = '4px 8px';
                btn.innerHTML = `<i class="fa-solid fa-hard-drive"></i> ${drive}`;
                btn.addEventListener('click', () => loadBrowserDirectories(drive));
                drivesContainer.appendChild(btn);
            });
        }
        
        // 2. Renderiza Breadcrumbs
        breadcrumbsContainer.innerHTML = '';
        
        // Se tiver parent, coloca botão para voltar
        if (data.parent_path) {
            const backBtn = document.createElement('button');
            backBtn.type = 'button';
            backBtn.className = 'btn-icon';
            backBtn.style.width = '24px';
            backBtn.style.height = '24px';
            backBtn.style.flexShrink = '0';
            backBtn.innerHTML = '<i class="fa-solid fa-arrow-left"></i>';
            backBtn.addEventListener('click', () => loadBrowserDirectories(data.parent_path));
            breadcrumbsContainer.appendChild(backBtn);
        }
        
        const parts = data.current_path.split(/[\\/]/).filter(Boolean);
        let cumulativePath = '';
        
        // Lida com Windows drive prefix (ex: C:)
        const isWindows = data.current_path.includes(':');
        if (isWindows && parts.length > 0) {
            cumulativePath = parts[0] + '\\';
            const segment = document.createElement('span');
            segment.style.cursor = 'pointer';
            segment.style.fontWeight = 'bold';
            segment.textContent = parts[0];
            const currentPathToLoad = cumulativePath;
            segment.addEventListener('click', () => loadBrowserDirectories(currentPathToLoad));
            breadcrumbsContainer.appendChild(segment);
            
            // Separador
            const sep = document.createElement('span');
            sep.textContent = '\\';
            breadcrumbsContainer.appendChild(sep);
            
            parts.shift(); // remove o drive
        }
        
        parts.forEach((part, index) => {
            if (cumulativePath && !cumulativePath.endsWith('\\') && !cumulativePath.endsWith('/')) {
                cumulativePath += isWindows ? '\\' : '/';
            }
            cumulativePath += part;
            
            const segment = document.createElement('span');
            segment.style.cursor = 'pointer';
            segment.textContent = part;
            const currentPathToLoad = cumulativePath;
            segment.addEventListener('click', () => loadBrowserDirectories(currentPathToLoad));
            breadcrumbsContainer.appendChild(segment);
            
            if (index < parts.length - 1) {
                const sep = document.createElement('span');
                sep.textContent = isWindows ? '\\' : '/';
                breadcrumbsContainer.appendChild(sep);
            }
        });
        
        // 3. Renderiza Diretórios
        listContainer.innerHTML = '';
        
        if (data.directories.length === 0) {
            listContainer.innerHTML = '<p class="placeholder-text" style="padding: 20px;">Nenhuma pasta encontrada.</p>';
            return;
        }
        
        data.directories.forEach(dirName => {
            const div = document.createElement('div');
            div.className = 'file-node';
            div.style.padding = '6px 10px';
            div.style.display = 'flex';
            div.style.alignItems = 'center';
            div.style.gap = '8px';
            div.style.cursor = 'pointer';
            
            div.innerHTML = `<i class="fa-solid fa-folder" style="color: var(--color-warning);"></i> <span>${dirName}</span>`;
            
            div.addEventListener('click', () => {
                let separator = state.currentBrowserPath.includes(':') ? '\\' : '/';
                let nextPath = state.currentBrowserPath;
                if (!nextPath.endsWith(separator)) {
                    nextPath += separator;
                }
                nextPath += dirName;
                loadBrowserDirectories(nextPath);
            });
            
            listContainer.appendChild(div);
        });
        
    } catch (err) {
        listContainer.innerHTML = `<p class="placeholder-text error-text" style="color: var(--color-danger); padding: 20px;">Erro ao ler diretórios: ${err.message}</p>`;
    }
}

async function handleCreateFolderBrowser() {
    const input = document.getElementById('dir-browser-new-folder-name');
    if (!input) return;
    const folderName = input.value.trim();
    if (!folderName) {
        alert('Por favor, digite o nome da pasta.');
        return;
    }
    
    const parentPath = state.currentBrowserPath;
    if (!parentPath) return;
    
    const btn = document.getElementById('btn-dir-browser-create-folder');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Criando...`;
    
    try {
        const res = await fetch('/api/system/dirs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                parent_path: parentPath,
                name: folderName
            })
        });
        
        const data = await res.json();
        
        if (!res.ok) {
            throw new Error(data.detail || 'Erro ao criar pasta');
        }
        
        // Limpa input
        input.value = '';
        
        // Recarrega o diretório atual para mostrar a nova pasta criada
        await loadBrowserDirectories(parentPath);
        
        // Alerta opcional de sucesso
        alert(data.message || 'Pasta criada com sucesso!');
    } catch (err) {
        alert(`Erro: ${err.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

function confirmDirectorySelection() {
    if (state.dirBrowserTargetInput === 'local-selected-path') {
        const path = state.currentBrowserPath;
        state.localSelectedPath = path;
        
        const preview = document.getElementById('local-selected-preview');
        preview.textContent = `Pasta selecionada: ${path}`;
        preview.style.display = 'block';
        
        // Extrai o nome da pasta
        const parts = path.split(/[\\/]/).filter(Boolean);
        const folderName = parts.length > 0 ? parts[parts.length - 1] : 'novo-projeto';
        
        const nameInput = document.getElementById('local-project-name');
        nameInput.value = folderName;
        document.getElementById('local-name-group').style.display = 'block';
        
        // Habilita o botão Importar do footer
        document.getElementById('btn-modal-project-import').disabled = false;
    } else if (state.dirBrowserTargetInput) {
        const input = document.getElementById(state.dirBrowserTargetInput);
        if (input) {
            input.value = state.currentBrowserPath;
        }
    }
    closeDirectoryBrowser();
}

function showCustomConfirm(title, message, confirmButtonText = 'Confirmar', isDanger = false) {
    return new Promise((resolve) => {
        const modal = document.getElementById('modal-confirm');
        const titleEl = document.getElementById('confirm-title');
        const messageEl = document.getElementById('confirm-message');
        const okBtn = document.getElementById('btn-confirm-ok');
        const cancelBtn = document.getElementById('btn-confirm-cancel');
        const closeBtn = modal.querySelector('.confirm-close');
        
        titleEl.textContent = title;
        messageEl.innerHTML = message;
        okBtn.textContent = confirmButtonText;
        
        if (isDanger) {
            okBtn.style.backgroundColor = 'var(--color-danger)';
            okBtn.style.borderColor = 'var(--color-danger)';
        } else {
            okBtn.style.backgroundColor = 'var(--color-primary)';
            okBtn.style.borderColor = 'var(--color-primary)';
        }
        
        modal.classList.add('active');
        
        const cleanup = (result) => {
            modal.classList.remove('active');
            okBtn.removeEventListener('click', onOk);
            cancelBtn.removeEventListener('click', onCancel);
            closeBtn.removeEventListener('click', onCancel);
            resolve(result);
        };
        
        const onOk = () => cleanup(true);
        const onCancel = () => cleanup(false);
        
        okBtn.addEventListener('click', onOk);
        cancelBtn.addEventListener('click', onCancel);
        closeBtn.addEventListener('click', onCancel);
    });
}

// --- EVENT LISTENERS & UI EVENTS ---
function setupEventListeners() {
    // 1. Selector de Projeto
    document.getElementById('project-selector').addEventListener('change', (e) => {
        selectProject(e.target.value);
    });
    
    // 2. Abas do Sidebar
    document.querySelectorAll('.nav-item').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const tabId = e.currentTarget.getAttribute('data-tab');
            switchTab(tabId);
        });
    });
    
    // 3. Importar App (Tabbed Modal)
    const modal = document.getElementById('modal-project');
    const openModalBtn = document.getElementById('btn-new-project');
    const stateNewProjectBtn = document.getElementById('btn-state-new-project');
    
    const openModal = () => {
        modal.classList.add('active');
        switchModalTab('local'); // Default tab
    };
    
    const closeModal = () => {
        modal.classList.remove('active');
        stopGitHubAuthPolling();
    };
    
    openModalBtn.addEventListener('click', openModal);
    stateNewProjectBtn.addEventListener('click', openModal);
    
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', closeModal);
    });

    // GitHub Auth Event Listeners
    document.getElementById('btn-github-connect').addEventListener('click', startGitHubDeviceFlow);
    document.getElementById('btn-copy-github-code').addEventListener('click', copyGitHubCode);
    document.getElementById('btn-github-logout').addEventListener('click', logoutGitHub);
    document.getElementById('btn-save-github-pat').addEventListener('click', saveGitHubPat);

    // 3.1. Tab Navigation Events
    document.querySelectorAll('.modal-tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const tabId = e.currentTarget.getAttribute('data-modal-tab');
            switchModalTab(tabId);
        });
    });

    // 3.2. Directory Selection Buttons
    document.getElementById('btn-select-local-path').addEventListener('click', () => {
        openDirectoryBrowser('local-selected-path');
    });
    document.getElementById('btn-browse-github-list-dest').addEventListener('click', () => {
        openDirectoryBrowser('github-list-dest-path');
    });
    document.getElementById('btn-browse-github-url-dest').addEventListener('click', () => {
        openDirectoryBrowser('github-url-dest-path');
    });

    // 3.3. Collapsible triggers
    const listTrigger = document.getElementById('github-list-adv-trigger');
    const listContent = document.getElementById('github-list-adv-content');
    listTrigger.addEventListener('click', () => toggleCollapsible(listTrigger, listContent));

    const urlTrigger = document.getElementById('github-url-adv-trigger');
    const urlContent = document.getElementById('github-url-adv-content');
    urlTrigger.addEventListener('click', () => toggleCollapsible(urlTrigger, urlContent));

    // 3.4. Input URL validation
    document.getElementById('github-repo-url').addEventListener('input', validateGithubUrlForm);

    // 3.5. Import submit (Footer button)
    document.getElementById('btn-modal-project-import').addEventListener('click', handleFooterImport);

    // 3.6. Navegador de Diretório Modal Close Events
    document.querySelectorAll('.dir-browser-close').forEach(btn => {
        btn.addEventListener('click', closeDirectoryBrowser);
    });
    document.getElementById('btn-dir-browser-confirm').addEventListener('click', confirmDirectorySelection);
    document.getElementById('btn-dir-browser-create-folder').addEventListener('click', handleCreateFolderBrowser);
    document.getElementById('dir-browser-new-folder-name').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleCreateFolderBrowser();
        }
    });

    // 3.7. Deletar/Remover Projeto Ativo
    document.getElementById('btn-delete-project').addEventListener('click', async () => {
        if (!state.activeProjectId) return;
        
        const confirmed = await showCustomConfirm(
            'Remover Projeto',
            `Tem certeza que deseja remover o projeto "${state.activeProject.name}" do GitIDE?<br><br>Isso apenas apagará o registro no GitIDE e os logs, os seus arquivos locais no disco NÃO serão excluídos.`,
            'Remover',
            true
        );
        
        if (confirmed) {
            try {
                const res = await fetch(`/api/projects/${state.activeProjectId}`, {
                    method: 'DELETE'
                });
                const data = await res.json();
                
                if (res.status === 200 && data.status === 'success') {
                    state.activeProjectId = null;
                    state.activeProject = null;
                    await loadProjects();
                    selectProject(null);
                } else {
                    alert(`Erro ao remover projeto: ${data.detail || 'Tente novamente.'}`);
                }
            } catch (err) {
                alert(`Falha na conexão: ${err.message}`);
            }
        }
    });
    
    // 3.8. Copiar ID e instruções para o GPT
    document.getElementById('btn-copy-project-gpt-info').addEventListener('click', () => {
        if (!state.activeProject) return;
        const infoText = `Olá! O projeto ativo no qual estamos trabalhando no GitIDE é "${state.activeProject.name}" (ID do projeto: ${state.activeProjectId}). Por favor, use sempre o ID de projeto "${state.activeProjectId}" em todas as chamadas de API (como no path /api/projects/${state.activeProjectId}/...).`;
        
        navigator.clipboard.writeText(infoText).then(() => {
            const btn = document.getElementById('btn-copy-project-gpt-info');
            const icon = btn.querySelector('i');
            const originalClass = icon.className;
            
            icon.className = 'fa-solid fa-check';
            icon.style.color = 'var(--color-success)';
            
            setTimeout(() => {
                icon.className = originalClass;
                icon.style.color = '';
            }, 1500);
        }).catch(err => {
            console.error('Erro ao copiar para clipboard:', err);
            alert('Não foi possível copiar as instruções para a área de transferência.');
        });
    });
    
    // 4. Ações de Arquivos
    document.getElementById('btn-refresh-files').addEventListener('click', loadFiles);
    document.getElementById('btn-save-file').addEventListener('click', saveFile);
    
    // Sincronismo do editor de código
    const editorTextarea = document.getElementById('file-editor-textarea');
    const editorGutter = document.getElementById('editor-gutter');
    if (editorTextarea && editorGutter) {
        editorTextarea.addEventListener('input', updateLineNumbers);
        editorTextarea.addEventListener('scroll', () => {
            editorGutter.scrollTop = editorTextarea.scrollTop;
        });
    }
    
    // 5. Ações do Terminal
    document.getElementById('terminal-form').addEventListener('submit', runTerminalCommand);
    document.getElementById('btn-clear-terminal').addEventListener('click', () => {
        document.getElementById('terminal-output').innerHTML = '<div class="terminal-line system-msg">Console limpo.</div>';
    });
    
    // 6. Ações do SQL DB Browser
    document.getElementById('btn-run-sql').addEventListener('click', runSqlQuery);
    document.getElementById('btn-db-connect').addEventListener('click', loadDbTables);
    document.getElementById('btn-db-refresh').addEventListener('click', loadDbTables);
    
    // Abas de resultados do banco
    document.getElementById('btn-tab-raw-results').addEventListener('click', () => switchDbResultsTab('raw'));
    document.getElementById('btn-tab-grid-editor').addEventListener('click', () => {
        switchDbResultsTab('grid');
        if (state.gridActiveTable) {
            loadTableGrid(state.gridActiveTable, state.gridCurrentPage);
        }
    });
    
    // Ações do Grid Editor
    document.getElementById('grid-btn-add').addEventListener('click', insertGridRow);
    document.getElementById('grid-btn-delete').addEventListener('click', deleteSelectedGridRows);
    document.getElementById('grid-btn-prev').addEventListener('click', () => {
        if (state.gridActiveTable && state.gridCurrentPage > 1) {
            loadTableGrid(state.gridActiveTable, state.gridCurrentPage - 1);
        }
    });
    document.getElementById('grid-btn-next').addEventListener('click', () => {
        if (state.gridActiveTable) {
            loadTableGrid(state.gridActiveTable, state.gridCurrentPage + 1);
        }
    });

    document.getElementById('db-type-select').addEventListener('change', (e) => {
        const type = e.target.value;
        const lbl = document.getElementById('lbl-db-conn');
        const input = document.getElementById('db-conn-input');
        const sqlText = document.getElementById('db-sql-textarea');
        
        if (type === 'sqlite') {
            lbl.textContent = 'Arquivo do Banco (relativo ao projeto):';
            input.placeholder = 'ex: database.db ou db/sqlite.db';
            input.value = 'database.db';
            sqlText.placeholder = 'SELECT * FROM tabela LIMIT 50;';
        } else if (type === 'postgresql') {
            lbl.textContent = 'Connection String (URI) do PostgreSQL:';
            input.placeholder = 'ex: postgresql://usuario:senha@host:5432/nome_do_banco';
            input.value = '';
            sqlText.placeholder = "SELECT * FROM pg_catalog.pg_tables WHERE schemaname='public';";
        } else if (type === 'mysql') {
            lbl.textContent = 'Connection String (URI) do MySQL:';
            input.placeholder = 'ex: mysql+pymysql://usuario:senha@host:3306/nome_do_banco';
            input.value = '';
            sqlText.placeholder = 'SHOW TABLES;';
        }
        
        // Limpa a lista de tabelas ao mudar tipo de banco
        document.getElementById('db-tables-list').innerHTML = '<p class="placeholder-text" style="padding: 20px 0; font-size: 12px; text-align: center; color: var(--text-dark);">Insira as credenciais do banco e conecte.</p>';
        const statusDot = document.getElementById('db-status-dot');
        statusDot.className = 'status-dot offline';
        statusDot.style.backgroundColor = '';
        statusDot.style.boxShadow = '';
        document.getElementById('db-status-text').textContent = 'Não conectado';
        
        // SALVA NO LOCALSTORAGE
        if (state.activeProjectId) {
            localStorage.setItem(`gitide_project_${state.activeProjectId}_db_type`, type);
            localStorage.setItem(`gitide_project_${state.activeProjectId}_db_conn`, input.value);
        }
    });
    
    document.getElementById('db-conn-input').addEventListener('input', (e) => {
        if (state.activeProjectId) {
            localStorage.setItem(`gitide_project_${state.activeProjectId}_db_conn`, e.target.value.trim());
        }
    });
    
    document.getElementById('db-sql-textarea').addEventListener('input', (e) => {
        if (state.activeProjectId) {
            localStorage.setItem(`gitide_project_${state.activeProjectId}_db_sql`, e.target.value.trim());
        }
    });
    
    // 7. Ações do Git Bridge
    document.getElementById('btn-git-status-refresh').addEventListener('click', loadGitStatus);
    document.getElementById('btn-git-graph-refresh').addEventListener('click', loadGitGraph);
    document.getElementById('btn-git-init').addEventListener('click', initGitRepo);
    document.getElementById('btn-git-deploy').addEventListener('click', runGitDeploy);
    document.getElementById('btn-git-pull').addEventListener('click', runGitPull);
    
    // Merge Dialog Close & Confirm Events
    document.querySelectorAll('.merge-close').forEach(btn => {
        btn.addEventListener('click', () => closeCustomModal('modal-merge'));
    });
    document.getElementById('btn-merge-confirm').addEventListener('click', runGitMerge);
    
    // Checkout Dialog Close & Confirm Events
    document.querySelectorAll('.checkout-close').forEach(btn => {
        btn.addEventListener('click', () => closeCustomModal('modal-checkout'));
    });
    document.getElementById('btn-checkout-confirm').addEventListener('click', runGitCheckout);

    
    // 7.5. Ações do Design System (Tokens)
    document.getElementById('btn-add-token-set').addEventListener('click', openCreateSetModal);
    
    // Theme Editor Close
    document.querySelectorAll('.theme-editor-close').forEach(btn => {
        btn.addEventListener('click', () => closeCustomModal('modal-theme-editor'));
    });
    document.getElementById('btn-theme-editor-save').addEventListener('click', saveThemeFromModal);
    
    // Set Editor Close
    document.querySelectorAll('.set-editor-close').forEach(btn => {
        btn.addEventListener('click', () => closeCustomModal('modal-set-editor'));
    });
    document.getElementById('btn-set-editor-save').addEventListener('click', saveSetFromModal);
    
    // Token Editor Close
    document.querySelectorAll('.token-editor-close').forEach(btn => {
        btn.addEventListener('click', () => closeCustomModal('modal-token-editor'));
    });
    document.getElementById('btn-token-editor-save').addEventListener('click', saveTokenFromModal);
    document.getElementById('token-editor-type').addEventListener('change', (e) => {
        updateTokenEditorFormFields(e.target.value);
    });
    
    document.getElementById('git-branch-input').addEventListener('change', async (e) => {
        const selectedBranch = e.target.value;
        if (!selectedBranch) return;
        
        appendGitConsole(`Alternando para a branch "${selectedBranch}"...`);
        try {
            const res = await fetch(`/api/projects/${state.activeProjectId}/git/branches`, {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify({ name: selectedBranch })
            });
            
            if (!res.ok) {
                throw new Error(await res.text());
            }
            
            const data = await res.json();
            appendGitConsole(`Alternado para a branch "${selectedBranch}" com sucesso!`);
            loadGitStatus();
        } catch (err) {
            appendGitConsole(`Erro ao alternar para a branch: ${err.message}`, true);
            alert(`Erro ao alternar para a branch: ${err.message}`);
            loadGitStatus();
        }
    });
    
    // 8. Logs
    document.getElementById('btn-refresh-logs').addEventListener('click', loadActivityLogs);
    document.getElementById('btn-refresh-all-snapshots').addEventListener('click', loadAllSnapshots);
    
    // 9. Copiar Token
    const copyTokenFunc = () => {
        navigator.clipboard.writeText(state.apiKey).then(() => {
            const preview = document.getElementById('api-token-preview');
            const originalText = preview.textContent;
            preview.textContent = 'Copiado!';
            setTimeout(() => {
                preview.textContent = originalText;
            }, 1500);
        });
    };
    
    document.getElementById('btn-copy-token').addEventListener('click', copyTokenFunc);
    document.getElementById('btn-copy-token-settings').addEventListener('click', () => {
        navigator.clipboard.writeText(state.apiKey).then(() => {
            const btn = document.getElementById('btn-copy-token-settings');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="fa-solid fa-check"></i> Copiado!';
            setTimeout(() => {
                btn.innerHTML = originalText;
            }, 1500);
        });
    });
    
    // 10. Database Sub-tabs and Credentials
    document.querySelectorAll('.db-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const subtabId = btn.getAttribute('data-db-subtab');
            
            // Remove active class from all buttons
            document.querySelectorAll('.db-tab-btn').forEach(b => {
                b.classList.remove('active');
                b.style.borderBottomColor = 'transparent';
                b.style.color = 'var(--text-muted)';
                b.style.fontWeight = '500';
            });
            
            // Add active class to clicked button
            btn.classList.add('active');
            btn.style.borderBottomColor = 'var(--color-primary)';
            btn.style.color = 'var(--text-light)';
            btn.style.fontWeight = '600';
            
            // Hide all subtab panes
            document.querySelectorAll('.db-subtab-pane').forEach(pane => {
                pane.style.display = 'none';
                pane.classList.remove('active-pane');
            });
            
            // Show active pane
            const activePane = document.getElementById(subtabId);
            if (activePane) {
                activePane.classList.add('active-pane');
                if (subtabId === 'db-subtab-explorer') {
                    activePane.style.display = 'block';
                } else {
                    activePane.style.display = 'block';
                }
            }
        });
    });

    // Toggle visibility for passwords/URLs
    document.querySelectorAll('.btn-toggle-visibility').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const input = document.getElementById(targetId);
            if (input) {
                const type = input.getAttribute('type');
                if (type === 'password') {
                    input.setAttribute('type', 'text');
                    btn.innerHTML = '<i class="fa-regular fa-eye-slash"></i>';
                } else {
                    input.setAttribute('type', 'password');
                    btn.innerHTML = '<i class="fa-regular fa-eye"></i>';
                }
            }
        });
    });

    // Copy fields to clipboard
    document.querySelectorAll('.btn-copy-field').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const input = document.getElementById(targetId);
            if (input && input.value) {
                navigator.clipboard.writeText(input.value).then(() => {
                    const originalHTML = btn.innerHTML;
                    btn.innerHTML = '<i class="fa-solid fa-check" style="color: var(--color-success);"></i>';
                    setTimeout(() => {
                        btn.innerHTML = originalHTML;
                    }, 1500);
                });
            }
        });
    });

    // Edit, Cancel, Save credentials buttons
    document.getElementById('btn-db-cred-edit').addEventListener('click', () => {
        setDbCredentialsEditMode(true);
    });

    document.getElementById('btn-db-cred-cancel').addEventListener('click', () => {
        setDbCredentialsEditMode(false);
        loadProjectDbCredentials(); // Restore saved values
    });

    document.getElementById('btn-db-cred-save').addEventListener('click', saveProjectDbCredentials);

    // 10. Agente IA Eventos
    const providerSelect = document.getElementById('agent-provider');
    if (providerSelect) {
        providerSelect.addEventListener('change', updateAgentModelOptions);
    }
    const btnToggleAgentKey = document.getElementById('btn-toggle-agent-key');
    if (btnToggleAgentKey) {
        btnToggleAgentKey.addEventListener('click', toggleAgentApiKeyVisibility);
    }
    const btnSaveAgentConfig = document.getElementById('btn-save-agent-config');
    if (btnSaveAgentConfig) {
        btnSaveAgentConfig.addEventListener('click', saveAgentConfigToServer);
    }
    const agentChatForm = document.getElementById('agent-chat-form');
    if (agentChatForm) {
        agentChatForm.addEventListener('submit', sendPromptToAgent);
    }
    const btnClearAgentMonitor = document.getElementById('btn-clear-agent-monitor');
    if (btnClearAgentMonitor) {
        btnClearAgentMonitor.addEventListener('click', () => {
            const logs = document.getElementById('agent-monitor-logs');
            if (logs) logs.innerHTML = '';
        });
    }
    const linkWelcomeSettings = document.getElementById('link-welcome-settings');
    if (linkWelcomeSettings) {
        linkWelcomeSettings.addEventListener('click', (e) => {
            e.preventDefault();
            switchTab('tab-settings');
        });
    }
    
    // Novo Cabeçalho do Chat & Ações
    const btnAgentHistory = document.getElementById('btn-agent-history');
    if (btnAgentHistory) {
        btnAgentHistory.addEventListener('click', () => {
            alert('Histórico de conversas do Agente IA (Em breve)');
        });
    }
    
    const btnClearAgentChat = document.getElementById('btn-clear-agent-chat');
    if (btnClearAgentChat) {
        btnClearAgentChat.addEventListener('click', () => {
            const chatHistory = document.getElementById('agent-chat-history');
            if (chatHistory) {
                chatHistory.innerHTML = `
                    <div class="agent-chat-welcome" style="text-align: center; color: var(--text-muted); margin: auto; max-width: 480px; padding: 20px;">
                        <i class="fa-solid fa-robot" style="font-size: 48px; color: var(--color-primary); margin-bottom: 14px;"></i>
                        <h3>Olá! Eu sou o Agente IA Local do GitIDE</h3>
                        <p style="font-size: 13px; margin-top: 8px;">Dê-me um objetivo e eu usarei as ferramentas locais (Arquivos, Git, Terminal, SQL) para resolver de forma autônoma. Configure sua chave API nas <a href="#" id="link-welcome-settings" style="color: var(--color-primary); text-decoration: underline;">Configurações</a> para começar.</p>
                    </div>
                `;
                // Re-bind click event since we replaced the HTML
                const newLink = document.getElementById('link-welcome-settings');
                if (newLink) {
                    newLink.addEventListener('click', (ev) => {
                        ev.preventDefault();
                        switchTab('tab-settings');
                    });
                }
            }
        });
    }
    
    // Ações Rápidas (Explain, Bugs, Tests, Refactor)
    document.querySelectorAll('.quick-action-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const action = btn.getAttribute('data-action');
            const promptInput = document.getElementById('agent-user-prompt');
            if (!promptInput) return;
            
            let filename = '';
            if (state.activeFilepath) {
                filename = state.activeFilepath.split('/').pop().split('\\').pop();
            }
            
            let queryText = '';
            if (action === 'explain') {
                queryText = filename ? `Explique o arquivo ${filename}` : 'Explique o funcionamento deste projeto.';
            } else if (action === 'bugs') {
                queryText = filename ? `Procure por potenciais bugs no arquivo ${filename}` : 'Procure por bugs no projeto.';
            } else if (action === 'test') {
                queryText = filename ? `Gere testes unitários para o arquivo ${filename}` : 'Gere testes unitários para o projeto.';
            } else if (action === 'refactor') {
                queryText = filename ? `Como posso refatorar e otimizar o código do arquivo ${filename}?` : 'Como posso otimizar o projeto?';
            }
            
            promptInput.value = queryText;
            promptInput.focus();
        });
    });
    
    // Delegação para botões de ação nos blocos de código
    const chatHistoryEl = document.getElementById('agent-chat-history');
    if (chatHistoryEl) {
        chatHistoryEl.addEventListener('click', (e) => {
            const btnApply = e.target.closest('.btn-apply');
            const btnTest = e.target.closest('.btn-test');
            const btnDiff = e.target.closest('.btn-diff');
            
            if (btnApply) {
                const card = btnApply.closest('.code-block-card');
                const code = card.querySelector('code').textContent;
                navigator.clipboard.writeText(code).then(() => {
                    alert('Correção copiada para a área de transferência! Cole no seu arquivo para aplicar.');
                });
            }
            if (btnTest) {
                alert('Executando testes automatizados...');
            }
            if (btnDiff) {
                alert('Visualizando diferenças...');
            }
        });
    }

    // Ações do Painel de Autenticação Git (PAT Token)
    const patInput = document.getElementById('git-pat-token-input');
    if (patInput) {
        patInput.addEventListener('input', updateGitGeneratedCommand);
    }
    
    const togglePatBtn = document.getElementById('btn-toggle-pat-visibility');
    if (togglePatBtn) {
        togglePatBtn.addEventListener('click', () => {
            const input = document.getElementById('git-pat-token-input');
            const icon = togglePatBtn.querySelector('i');
            if (input.type === 'password') {
                input.type = 'text';
                icon.className = 'fa-solid fa-eye-slash';
            } else {
                input.type = 'password';
                icon.className = 'fa-solid fa-eye';
            }
        });
    }
    
    const copyGitCmdBtn = document.getElementById('btn-copy-generated-git-cmd');
    if (copyGitCmdBtn) {
        copyGitCmdBtn.addEventListener('click', () => {
            const text = document.getElementById('git-generated-command-text').textContent;
            navigator.clipboard.writeText(text).then(() => {
                const icon = copyGitCmdBtn.querySelector('i');
                const originalClass = icon.className;
                icon.className = 'fa-solid fa-check';
                icon.style.color = 'var(--color-success)';
                setTimeout(() => {
                    icon.className = originalClass;
                    icon.style.color = '';
                }, 2000);
            });
        });
    }
    
    const runGitCmdBtn = document.getElementById('btn-run-generated-git-cmd');
    if (runGitCmdBtn) {
        runGitCmdBtn.addEventListener('click', runGitSetTokenAPI);
    }
    
    // 12. Documentos Word
    const refreshDocsBtn = document.getElementById('btn-refresh-documents');
    if (refreshDocsBtn) {
        refreshDocsBtn.addEventListener('click', loadDocuments);
    }
    const uploadDocBtn = document.getElementById('btn-upload-document');
    const uploadDocInput = document.getElementById('input-upload-document');
    if (uploadDocBtn && uploadDocInput) {
        uploadDocBtn.addEventListener('click', () => uploadDocInput.click());
        uploadDocInput.addEventListener('change', handleDocumentUpload);
    }
    const generateTestDocBtn = document.getElementById('btn-generate-test-doc');
    if (generateTestDocBtn) {
        generateTestDocBtn.addEventListener('click', generateTestDocument);
    }
    const copyDocPromptBtn = document.getElementById('btn-copy-doc-prompt-instructions');
    if (copyDocPromptBtn) {
        copyDocPromptBtn.addEventListener('click', copyDocPromptInstructions);
    }
}

// --- IMPORT APP TABBED MODAL FUNCTIONS ---

function switchModalTab(tab) {
    state.activeModalTab = tab;
    
    // Update active class on tab buttons
    document.querySelectorAll('.modal-tab-btn').forEach(btn => {
        if (btn.getAttribute('data-modal-tab') === tab) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    // Update active class on tab contents
    document.querySelectorAll('.modal-tab-content').forEach(content => {
        if (content.getAttribute('data-tab-content') === tab) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
    
    // Show/Hide footer Import button dynamically
    const importBtn = document.getElementById('btn-modal-project-import');
    if (tab === 'github-list') {
        importBtn.style.display = 'none'; // GitHub list items have their own inline Importar buttons
    } else {
        importBtn.style.display = 'inline-flex';
        // Re-validate footer button state
        if (tab === 'local') {
            importBtn.disabled = !state.localSelectedPath;
        } else if (tab === 'github-url') {
            validateGithubUrlForm();
        }
    }
    
    // If GitHub list active, load repos
    if (tab === 'github-list') {
        checkGitHubStatus();
    }
}

function toggleCollapsible(triggerEl, contentEl) {
    triggerEl.classList.toggle('active');
    contentEl.classList.toggle('active');
}

async function loadGitHubRepos() {
    const container = document.getElementById('github-repos-list-container');
    
    // If already loaded, don't fetch again
    if (state.githubRepos && state.githubRepos.length > 0) {
        renderGitHubReposList(state.githubRepos);
        return;
    }
    
    container.innerHTML = '<div class="loading-spinner"><i class="fa-solid fa-circle-notch fa-spin"></i></div>';
    
    const fallbackRepos = [
        { name: 'builtt-ui', full_name: 'gittoptus/builtt-ui', clone_url: 'https://github.com/gittoptus/builtt-ui.git' },
        { name: 'Dash-Gran', full_name: 'gittoptus/Dash-Gran', clone_url: 'https://github.com/gittoptus/Dash-Gran.git' },
        { name: 'canvaly', full_name: 'gittoptus/canvaly', clone_url: 'https://github.com/gittoptus/canvaly.git' },
        { name: 'iazzie-curadoria', full_name: 'gittoptus/iazzie-curadoria', clone_url: 'https://github.com/gittoptus/iazzie-curadoria.git' }
    ];
    
    try {
        // Tenta buscar da API do GitHub com timeout curto
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 4000);
        
        const res = await fetch('/api/github/repos', { signal: controller.signal });
        clearTimeout(timeoutId);
        
        if (res.status === 200) {
            const data = await res.json();
            if (Array.isArray(data) && data.length > 0) {
                state.githubRepos = data.map(repo => {
                    let displayName = repo.name;
                    let displayFullName = repo.full_name;
                    if (repo.name === 'canv') {
                        displayName = 'canvaly';
                        displayFullName = 'gittoptus/canvaly';
                    } else if (repo.name === 'curadoria') {
                        displayName = 'iazzie-curadoria';
                        displayFullName = 'gittoptus/iazzie-curadoria';
                    }
                    return {
                        name: displayName,
                        full_name: displayFullName,
                        clone_url: repo.clone_url
                    };
                });
                
                // Garante que mostramos pelo menos os listados no mockup se faltarem
                fallbackRepos.forEach(f => {
                    if (!state.githubRepos.some(r => r.name.toLowerCase() === f.name.toLowerCase())) {
                        state.githubRepos.push(f);
                    }
                });
            } else {
                state.githubRepos = fallbackRepos;
            }
        } else {
            state.githubRepos = fallbackRepos;
        }
    } catch (err) {
        console.warn('Erro ao carregar do GitHub, usando fallbacks:', err);
        state.githubRepos = fallbackRepos;
    }
    
    renderGitHubReposList(state.githubRepos);
}

function renderGitHubReposList(repos) {
    const container = document.getElementById('github-repos-list-container');
    container.innerHTML = '';
    
    if (repos.length === 0) {
        container.innerHTML = '<p class="placeholder-text" style="padding: 10px;">Nenhum repositório encontrado.</p>';
        return;
    }
    
    repos.forEach(repo => {
        const item = document.createElement('div');
        item.className = 'repo-item';
        
        const fullName = repo.full_name.includes('/') ? repo.full_name : `gittoptus/${repo.full_name}`;
        
        item.innerHTML = `
            <div class="repo-info">
                <span class="repo-name">${repo.name}</span>
                <span class="repo-fullname">${fullName}</span>
            </div>
            <button type="button" class="btn btn-sm btn-primary btn-import-repo" style="white-space: nowrap;"><i class="fa-solid fa-cloud-arrow-down"></i> Importar</button>
        `;
        
        item.querySelector('.btn-import-repo').addEventListener('click', (e) => {
            e.stopPropagation();
            importGitHubRepoListItem(repo);
        });
        
        container.appendChild(item);
    });
}

function validateGithubUrlForm() {
    const url = document.getElementById('github-repo-url').value.trim();
    const importBtn = document.getElementById('btn-modal-project-import');
    importBtn.disabled = !url;
}

async function importGitHubRepoListItem(repo) {
    const appNameOpt = document.getElementById('github-app-name-opt').value.trim();
    const projectName = appNameOpt || repo.name;
    const basePath = document.getElementById('github-list-dest-path').value.trim();
    
    const separator = basePath.includes(':') ? '\\' : '/';
    const clonePath = basePath.endsWith(separator) ? `${basePath}${projectName}` : `${basePath}${separator}${projectName}`;
    
    await executeProjectImport(projectName, clonePath, repo.clone_url);
}

async function handleFooterImport() {
    if (state.activeModalTab === 'local') {
        if (!state.localSelectedPath) return;
        
        const path = state.localSelectedPath;
        const nameInput = document.getElementById('local-project-name').value.trim();
        
        const parts = path.split(/[\\/]/).filter(Boolean);
        const folderName = parts.length > 0 ? parts[parts.length - 1] : 'novo-projeto';
        const projectName = nameInput || folderName;
        
        await executeProjectImport(projectName, path, null);
        
    } else if (state.activeModalTab === 'github-url') {
        const repoUrl = document.getElementById('github-repo-url').value.trim();
        if (!repoUrl) return;
        
        const appNameOpt = document.getElementById('github-url-app-name-opt').value.trim();
        
        let repoName = 'novo-projeto';
        try {
            const urlParts = repoUrl.split('/');
            const lastPart = urlParts[urlParts.length - 1];
            if (lastPart) {
                repoName = lastPart.replace('.git', '');
            }
        } catch (e) {}
        
        const projectName = appNameOpt || repoName;
        
        let destPath = document.getElementById('github-url-dest-path').value.trim();
        if (!destPath) {
            if (state.os === 'Linux') {
                destPath = `/workspace/${projectName}`;
            } else {
                destPath = `C:\\Users\\augus\\.workspace\\${projectName}`;
            }
        }
        
        await executeProjectImport(projectName, destPath, repoUrl);
    }
}

async function executeProjectImport(name, path, remoteUrl) {
    const importBtn = document.getElementById('btn-modal-project-import');
    const originalText = importBtn.innerHTML;
    
    importBtn.disabled = true;
    importBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Importando...';
    
    document.querySelectorAll('.btn-import-repo').forEach(btn => btn.disabled = true);
    
    try {
        const res = await fetch('/api/projects', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                path: path,
                git_remote: remoteUrl
            })
        });
        const text = await res.text();
        let data;
        try {
            data = JSON.parse(text);
        } catch (jsonErr) {
            throw new Error(text || `Erro do servidor (Status: ${res.status})`);
        }
        
        if (res.status === 200 && data.status === 'success') {
            document.getElementById('modal-project').classList.remove('active');
            
            document.getElementById('local-selected-preview').style.display = 'none';
            document.getElementById('local-name-group').style.display = 'none';
            document.getElementById('local-project-name').value = '';
            document.getElementById('github-app-name-opt').value = '';
            document.getElementById('github-repo-url').value = '';
            document.getElementById('github-url-app-name-opt').value = '';
            document.getElementById('github-url-dest-path').value = '';
            state.localSelectedPath = null;
            
            await loadProjects();
            selectProject(data.project.id);
            
            alert(`Projeto "${name}" importado e carregado com sucesso!`);
        } else {
            alert(`Erro ao importar projeto: ${data.detail || 'Verifique se a pasta já existe ou se as informações estão corretas.'}`);
        }
    } catch (err) {
        alert(`Falha ao importar projeto: ${err.message}`);
    } finally {
        importBtn.disabled = false;
        importBtn.innerHTML = originalText;
        document.querySelectorAll('.btn-import-repo').forEach(btn => btn.disabled = false);
    }
}

async function toggleLogDiff(logId, cardEl, btnEl) {
    let diffContainer = cardEl.querySelector('.diff-container');
    
    if (diffContainer) {
        diffContainer.remove();
        btnEl.innerHTML = '<i class="fa-solid fa-code-compare"></i> Ver Alterações';
        return;
    }
    
    btnEl.disabled = true;
    btnEl.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Carregando...';
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/logs/${logId}/diff`);
        const data = await res.json();
        
        if (data.has_diff) {
            diffContainer = document.createElement('pre');
            diffContainer.className = 'diff-container';
            
            const lines = data.diff.split('\n');
            let html = '';
            lines.forEach(line => {
                const escaped = escapeHtml(line);
                if (line.startsWith('+') && !line.startsWith('+++')) {
                    html += `<span class="diff-line diff-line-add">${escaped}</span>`;
                } else if (line.startsWith('-') && !line.startsWith('---')) {
                    html += `<span class="diff-line diff-line-del">${escaped}</span>`;
                } else if (line.startsWith('@@')) {
                    html += `<span class="diff-line diff-line-info">${escaped}</span>`;
                } else {
                    html += `<span class="diff-line">${escaped}</span>`;
                }
            });
            
            diffContainer.innerHTML = html;
            cardEl.appendChild(diffContainer);
            btnEl.innerHTML = '<i class="fa-solid fa-eye-slash"></i> Ocultar Alterações';
        } else {
            alert(data.message || 'Nenhuma alteração disponível.');
            btnEl.innerHTML = '<i class="fa-solid fa-code-compare"></i> Ver Alterações';
        }
    } catch (err) {
        alert(`Erro ao carregar alterações: ${err.message}`);
        btnEl.innerHTML = '<i class="fa-solid fa-code-compare"></i> Ver Alterações';
    } finally {
        btnEl.disabled = false;
    }
}

function escapeHtml(text) {
    return text
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

// --- GITHUB AUTH & BRANCH ACTIONS DROPDOWN FLOWS ---
let githubAuthPollingInterval = null;
let githubDeviceCode = null;

async function checkGitHubStatus() {
    try {
        const res = await fetch('/api/github/auth/status');
        const data = await res.json();
        
        const authSection = document.getElementById('github-auth-section');
        const reposSection = document.getElementById('github-repos-section');
        
        if (data.authenticated) {
            authSection.style.display = 'none';
            reposSection.style.display = 'block';
            
            // Exibe informações do perfil do usuário
            document.getElementById('github-avatar').src = data.user.avatar_url || '';
            document.getElementById('github-username').textContent = data.user.login || 'Usuário';
            document.getElementById('github-email').textContent = data.user.email || 'Sem e-mail público';
            
            // Carrega os repositórios
            await loadGitHubRepos();
        } else {
            authSection.style.display = 'block';
            reposSection.style.display = 'none';
            
            // Reseta estado da UI de conexão caso estivesse em polling
            stopGitHubAuthPolling();
            document.getElementById('github-auth-card').style.display = 'none';
            const connectBtn = document.getElementById('btn-github-connect');
            connectBtn.disabled = false;
            document.getElementById('github-connect-spinner').style.display = 'none';
        }
    } catch (err) {
        console.error('Erro ao checar status do GitHub:', err);
    }
}

async function startGitHubDeviceFlow() {
    const connectBtn = document.getElementById('btn-github-connect');
    const spinner = document.getElementById('github-connect-spinner');
    
    connectBtn.disabled = true;
    spinner.style.display = 'inline-block';
    
    try {
        const res = await fetch('/api/github/auth/device', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!res.ok) {
            throw new Error(await res.text());
        }
        
        const data = await res.json();
        
        // Mostra o painel de instruções de autorização
        document.getElementById('github-auth-card').style.display = 'block';
        document.getElementById('github-user-code').textContent = data.user_code;
        
        const deviceLink = document.getElementById('github-device-link');
        deviceLink.href = data.verification_uri;
        deviceLink.textContent = data.verification_uri;
        
        const statusEl = document.getElementById('github-auth-status');
        statusEl.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Waiting for user authorization...';
        
        githubDeviceCode = data.device_code;
        
        // Inicia polling
        startGitHubAuthPolling(data.device_code, data.interval || 5);
        
    } catch (err) {
        console.error('Falha ao iniciar device flow:', err);
        alert('Falha ao conectar com o GitHub: ' + err.message);
        connectBtn.disabled = false;
        spinner.style.display = 'none';
    }
}

function startGitHubAuthPolling(deviceCode, interval) {
    stopGitHubAuthPolling();
    
    githubAuthPollingInterval = setInterval(async () => {
        try {
            const res = await fetch('/api/github/auth/poll', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ device_code: deviceCode })
            });
            
            const data = await res.json();
            const statusEl = document.getElementById('github-auth-status');
            
            if (data.status === 'success') {
                stopGitHubAuthPolling();
                statusEl.innerHTML = '<span style="color: var(--color-success)"><i class="fa-solid fa-circle-check"></i> Connected successfully!</span>';
                setTimeout(() => {
                    checkGitHubStatus();
                }, 1000);
            } else if (data.error) {
                if (data.error === 'authorization_pending') {
                    // Continua polling
                } else if (data.error === 'slow_down') {
                    // Aumenta o intervalo
                    clearInterval(githubAuthPollingInterval);
                    startGitHubAuthPolling(deviceCode, (data.interval || interval) + 5);
                } else {
                    // Erros como token expirado ou cancelado
                    stopGitHubAuthPolling();
                    statusEl.innerHTML = `<span style="color: var(--color-danger)"><i class="fa-solid fa-circle-xmark"></i> Connection failed: ${data.error_description || data.error}</span>`;
                    document.getElementById('btn-github-connect').disabled = false;
                    document.getElementById('github-connect-spinner').style.display = 'none';
                }
            }
        } catch (err) {
            console.error('Erro na consulta de token GitHub:', err);
        }
    }, interval * 1000);
}

function stopGitHubAuthPolling() {
    if (githubAuthPollingInterval) {
        clearInterval(githubAuthPollingInterval);
        githubAuthPollingInterval = null;
    }
}

async function logoutGitHub() {
    try {
        await fetch('/api/github/auth/logout', { method: 'POST' });
        state.githubRepos = []; // Limpa cache
        checkGitHubStatus();
    } catch (err) {
        console.error('Erro ao desconectar do GitHub:', err);
    }
}

async function saveGitHubPat() {
    const input = document.getElementById('github-pat-input');
    const token = input.value.trim();
    if (!token) {
        alert('Por favor, insira o token clássico (PAT) do GitHub.');
        return;
    }
    
    const btn = document.getElementById('btn-save-github-pat');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Conectando...';
    
    try {
        const res = await fetch('/api/github/auth/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: token })
        });
        
        const data = await res.json();
        if (res.status === 200 && data.status === 'success') {
            input.value = '';
            alert('Token do GitHub (PAT) conectado e salvo com sucesso!');
            checkGitHubStatus();
        } else {
            alert(`Erro ao salvar token: ${data.detail || 'Erro desconhecido'}`);
        }
    } catch (err) {
        alert(`Erro de conexão ao salvar token: ${err.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

function copyGitHubCode() {
    const code = document.getElementById('github-user-code').textContent;
    navigator.clipboard.writeText(code).then(() => {
        const copyBtn = document.getElementById('btn-copy-github-code');
        const icon = copyBtn.querySelector('i');
        
        icon.className = 'fa-solid fa-check';
        icon.style.color = 'var(--color-success)';
        
        setTimeout(() => {
            icon.className = 'fa-regular fa-clipboard';
            icon.style.color = '';
        }, 1500);
    });
}

function closeAllDropdowns() {
    const menus = document.querySelectorAll('.dropdown-menu');
    menus.forEach(menu => {
        menu.classList.remove('branch-actions-menu-open');
        menu.style.setProperty('display', 'none', 'important');
    });

    document.querySelectorAll('.dropdown-trigger[aria-expanded="true"]').forEach(trigger => {
        trigger.setAttribute('aria-expanded', 'false');
    });
}

async function promptCreateBranch() {
    const branchName = prompt('Digite o nome da nova branch:');
    if (!branchName || !branchName.trim()) return;
    
    appendGitConsole(`Criando branch "${branchName.trim()}"...`);
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/git/branches`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ name: branchName.trim() })
        });
        
        if (!res.ok) {
            throw new Error(await res.text());
        }
        
        const data = await res.json();
        appendGitConsole(`Branch "${branchName.trim()}" criada com sucesso! Checkout realizado.`);
        loadGitStatus();
    } catch (err) {
        appendGitConsole(`Erro ao criar branch: ${err.message}`, true);
        alert(`Erro ao criar branch: ${err.message}`);
    }
}

function openMergeModal() {
    if (!state.activeProjectId) return;
    
    const selector = document.getElementById('merge-branch-selector');
    const currentBranchLabel = document.getElementById('merge-current-branch-name');
    
    // Clear and set loading state
    selector.innerHTML = '<option value="">Carregando branches...</option>';
    currentBranchLabel.textContent = '...';
    
    openCustomModal('modal-merge');
    
    fetch(`/api/projects/${state.activeProjectId}/git/branches`, {
        headers: getHeaders()
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            const current = data.current_branch || 'main';
            currentBranchLabel.textContent = current;
            
            selector.innerHTML = '';
            
            // Get all branches except current
            const branches = data.all || [];
            const otherBranches = branches.filter(b => b !== current);
            
            if (otherBranches.length === 0) {
                selector.innerHTML = '<option value="">Nenhuma outra branch disponível para mesclar</option>';
                return;
            }
            
            otherBranches.forEach(b => {
                const opt = document.createElement('option');
                opt.value = b;
                opt.textContent = b;
                selector.appendChild(opt);
            });
        } else {
            selector.innerHTML = '<option value="">Erro ao carregar lista de branches</option>';
        }
    })
    .catch(err => {
        console.error('Erro ao listar branches:', err);
        selector.innerHTML = '<option value="">Erro ao carregar lista de branches</option>';
    });
}

async function runGitMerge() {
    const branchSelect = document.getElementById('merge-branch-selector');
    const selectedBranch = branchSelect.value;
    
    if (!selectedBranch) {
        alert('Selecione uma branch válida para mesclar.');
        return;
    }
    
    closeCustomModal('modal-merge');
    
    appendGitConsole(`Iniciando mesclagem (git merge) da branch "${selectedBranch}"...`);
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/git/merge`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ branch: selectedBranch })
        });
        
        const data = await res.json();
        
        if (!res.ok) {
            throw new Error(data.detail || 'Erro desconhecido');
        }
        
        appendGitConsole(`Branch "${selectedBranch}" mesclada com sucesso!\n\n${data.detail || ''}`);
        alert(`Mesclagem realizada com sucesso!`);
        loadGitStatus();
    } catch (err) {
        appendGitConsole(`Erro ao mesclar branch: ${err.message}`, true);
        alert(`Erro ao mesclar branch: ${err.message}`);
    }
}

// --- DESIGN SYSTEM (TOKENS) MANAGER ---

async function loadDesignTokens() {
    if (!state.activeProjectId) return;
    
    const accordionList = document.getElementById('tokens-accordion-list');
    if (!accordionList) return;
    
    accordionList.innerHTML = '<div class="loading-spinner"><i class="fa-solid fa-circle-notch fa-spin"></i> Carregando Tokens...</div>';
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/files/read?filepath=tokens.json`, {
            headers: getHeaders()
        });
        
        if (res.status === 404) {
            // Se tokens.json não existe, inicializa um objeto padrão
            state.designTokens = {
                "global": {},
                "$themes": [
                    {
                        "id": "default-theme-id",
                        "name": "default",
                        "group": "",
                        "description": "Default Theme",
                        "isSource": false,
                        "selectedTokenSets": {
                            "global": "enabled"
                        }
                    }
                ],
                "$metadata": {
                    "tokenSetOrder": ["global"],
                    "activeThemes": [],
                    "activeSets": ["global"]
                }
            };
            state.activeTokenSet = 'global';
            state.activeTokenTheme = 'default-theme-id';
            
            // Grava o arquivo default
            await saveDesignTokens();
        } else if (!res.ok) {
            throw new Error(await res.text());
        } else {
            const data = await res.json();
            state.designTokens = JSON.parse(data.content);
            
            // Determina a primeira set válida
            const setOrder = state.designTokens.$metadata?.tokenSetOrder || [];
            if (setOrder.length > 0) {
                if (!setOrder.includes(state.activeTokenSet)) {
                    state.activeTokenSet = setOrder[0];
                }
            } else {
                state.activeTokenSet = 'global';
                if (!state.designTokens.global) state.designTokens.global = {};
                if (!state.designTokens.$metadata) state.designTokens.$metadata = {};
                state.designTokens.$metadata.tokenSetOrder = ['global'];
                state.designTokens.$metadata.activeSets = ['global'];
            }
            
            // Determina o tema ativo
            const themes = state.designTokens.$themes || [];
            if (themes.length > 0) {
                if (!state.activeTokenTheme || !themes.find(t => t.id === state.activeTokenTheme)) {
                    state.activeTokenTheme = themes[0].id;
                }
            } else {
                state.activeTokenTheme = null;
            }
        }
        
        renderTokensThemes();
        renderTokensSets();
        renderTokensList();
        
    } catch (err) {
        console.error('Erro ao carregar design tokens:', err);
        accordionList.innerHTML = `<p class="placeholder-text error-text">Erro ao carregar tokens: ${err.message}</p>`;
    }
}

async function saveDesignTokens() {
    if (!state.activeProjectId || !state.designTokens) return;
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/files/write`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                filepath: 'tokens.json',
                content: JSON.stringify(state.designTokens, null, 2)
            })
        });
        
        if (!res.ok) {
            throw new Error(await res.text());
        }
    } catch (err) {
        console.error('Erro ao gravar tokens:', err);
        alert(`Erro ao gravar tokens.json: ${err.message}`);
    }
}

function renderTokensThemes() {
    const container = document.getElementById('tokens-themes-container');
    if (!container) return;
    
    const themes = state.designTokens.$themes || [];
    if (themes.length === 0) {
        container.innerHTML = `
            <div class="theme-empty-state">
                Não há temas. <a id="btn-theme-create-empty">Criar um.</a>
            </div>
        `;
        document.getElementById('btn-theme-create-empty').addEventListener('click', openCreateThemeModal);
        return;
    }
    
    let options = '';
    themes.forEach(t => {
        const selected = t.id === state.activeTokenTheme ? 'selected' : '';
        options += `<option value="${t.id}" ${selected}>${t.name}</option>`;
    });
    
    container.innerHTML = `
        <div class="theme-select-row">
            <select id="select-active-theme" class="select-input" style="flex: 1; padding: 6px 10px; font-size: 13px;">
                ${options}
            </select>
            <button class="btn btn-secondary btn-sm" id="btn-edit-active-theme" style="padding: 6px 12px; font-size: 12px; white-space: nowrap;">EDITAR</button>
        </div>
    `;
    
    document.getElementById('select-active-theme').addEventListener('change', (e) => {
        state.activeTokenTheme = e.target.value;
        const theme = themes.find(t => t.id === state.activeTokenTheme);
        if (theme && theme.selectedTokenSets) {
            state.designTokens.$metadata.activeSets = Object.keys(theme.selectedTokenSets).filter(setName => theme.selectedTokenSets[setName] === 'enabled');
            if (state.designTokens.$metadata.activeSets.length > 0) {
                state.activeTokenSet = state.designTokens.$metadata.activeSets[0];
            }
        }
        saveDesignTokens();
        renderTokensSets();
        renderTokensList();
    });
    
    document.getElementById('btn-edit-active-theme').addEventListener('click', openEditThemeModal);
}

function renderTokensSets() {
    const container = document.getElementById('tokens-sets-container');
    if (!container) return;
    
    const setOrder = state.designTokens.$metadata?.tokenSetOrder || [];
    const activeSets = state.designTokens.$metadata?.activeSets || [];
    
    if (setOrder.length === 0) {
        container.innerHTML = `
            <div class="set-empty-state">
                Não há sets. <a id="btn-set-create-empty">Criar um.</a>
            </div>
        `;
        document.getElementById('btn-set-create-empty').addEventListener('click', openCreateSetModal);
        return;
    }
    
    let html = '';
    setOrder.forEach(setName => {
        const isActive = activeSets.includes(setName);
        const isCurrent = setName === state.activeTokenSet ? 'active' : '';
        const checked = isActive ? 'checked' : '';
        
        html += `
            <div class="token-set-item ${isCurrent}" data-set="${setName}">
                <div class="token-set-item-left">
                    <i class="fa-regular fa-file-code"></i>
                    <span>${setName}</span>
                </div>
                <input type="checkbox" class="set-active-checkbox" data-set="${setName}" ${checked} style="cursor: pointer;">
            </div>
        `;
    });
    
    container.innerHTML = html;
    
    container.querySelectorAll('.token-set-item').forEach(item => {
        item.addEventListener('click', (e) => {
            if (e.target.type === 'checkbox') return;
            
            const setName = item.getAttribute('data-set');
            state.activeTokenSet = setName;
            
            container.querySelectorAll('.token-set-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            
            renderTokensList();
        });
    });
    
    container.querySelectorAll('.set-active-checkbox').forEach(cb => {
        cb.addEventListener('change', (e) => {
            const setName = cb.getAttribute('data-set');
            const checked = cb.checked;
            
            if (!state.designTokens.$metadata.activeSets) {
                state.designTokens.$metadata.activeSets = [];
            }
            
            if (checked) {
                if (!state.designTokens.$metadata.activeSets.includes(setName)) {
                    state.designTokens.$metadata.activeSets.push(setName);
                }
            } else {
                state.designTokens.$metadata.activeSets = state.designTokens.$metadata.activeSets.filter(s => s !== setName);
            }
            
            if (state.activeTokenTheme) {
                const theme = state.designTokens.$themes.find(t => t.id === state.activeTokenTheme);
                if (theme) {
                    if (!theme.selectedTokenSets) theme.selectedTokenSets = {};
                    theme.selectedTokenSets[setName] = checked ? 'enabled' : 'disabled';
                }
            }
            
            saveDesignTokens();
            renderTokensList();
        });
    });
}

const TOKEN_TYPES_CONFIG = {
    borderRadius: { label: 'Border Radius', icon: 'fa-vector-square' },
    color: { label: 'Color', icon: 'fa-droplet' },
    dimension: { label: 'Dimensions', icon: 'fa-maximize' },
    fontFamily: { label: 'Font Family', icon: 'fa-font' },
    fontSize: { label: 'Font Size', icon: 'fa-text-height' },
    fontWeight: { label: 'Font Weight', icon: 'fa-bold' },
    letterSpacing: { label: 'Letter Spacing', icon: 'fa-arrows-left-right' },
    number: { label: 'Number', icon: 'fa-hashtag' },
    opacity: { label: 'Opacity', icon: 'fa-percent' },
    rotation: { label: 'Rotation', icon: 'fa-rotate' },
    boxShadow: { label: 'Shadow', icon: 'fa-circle-half-stroke' },
    sizing: { label: 'Sizing', icon: 'fa-expand' },
    spacing: { label: 'Spacing', icon: 'fa-align-justify' },
    borderWidth: { label: 'Stroke Width', icon: 'fa-grip-lines' },
    textCase: { label: 'Text Case', icon: 'fa-heading' },
    textDecoration: { label: 'Text Decoration', icon: 'fa-underline' },
    typography: { label: 'Typography', icon: 'fa-spell-check' }
};

function renderTokensList() {
    const container = document.getElementById('tokens-accordion-list');
    const title = document.getElementById('tokens-active-set-title');
    const statusBadge = document.getElementById('tokens-active-set-status');
    if (!container) return;
    
    const activeSet = state.activeTokenSet || 'global';
    title.textContent = `TOKENS - ${activeSet.toUpperCase()}`;
    
    const activeSets = state.designTokens.$metadata?.activeSets || [];
    const isSetCurrentlyActive = activeSets.includes(activeSet);
    statusBadge.textContent = isSetCurrentlyActive ? 'Active' : 'Inactive';
    statusBadge.style.background = isSetCurrentlyActive ? 'rgba(16,185,129,0.1)' : 'rgba(255,255,255,0.05)';
    statusBadge.style.color = isSetCurrentlyActive ? 'var(--color-success)' : 'var(--text-muted)';
    
    const setTokens = state.designTokens[activeSet] || {};
    
    const groupedTokens = {};
    Object.keys(TOKEN_TYPES_CONFIG).forEach(type => {
        groupedTokens[type] = [];
    });
    
    Object.keys(setTokens).forEach(tokenName => {
        const tokenData = setTokens[tokenName];
        if (tokenData && tokenData.$type) {
            let type = tokenData.$type;
            if (type === 'strokeWidth') type = 'borderWidth';
            if (groupedTokens[type]) {
                groupedTokens[type].push({ name: tokenName, ...tokenData });
            }
        }
    });
    
    let html = '';
    Object.keys(TOKEN_TYPES_CONFIG).forEach(type => {
        const cfg = TOKEN_TYPES_CONFIG[type];
        const list = groupedTokens[type] || [];
        const count = list.length;
        const expandedClass = count > 0 ? 'expanded' : '';
        
        let tokenItemsHtml = '';
        if (count === 0) {
            tokenItemsHtml = '<div class="tokens-category-empty">Nenhum token criado.</div>';
        } else {
            tokenItemsHtml = '<div class="tokens-grid">';
            list.forEach(tok => {
                let displayVal = tok.$value;
                if (typeof displayVal === 'object' && displayVal !== null) {
                    const parts = [];
                    if (displayVal.fontFamily) parts.push(displayVal.fontFamily);
                    if (displayVal.fontSize) parts.push(displayVal.fontSize);
                    if (displayVal.fontWeight) parts.push(displayVal.fontWeight);
                    displayVal = parts.join(' ') || 'Typography';
                }
                if (displayVal.length > 20) displayVal = displayVal.substring(0, 18) + '...';
                
                tokenItemsHtml += `
                    <div class="token-pill" data-token-name="${tok.name}" data-token-type="${type}" data-token-desc="${tok.$description || ''}">
                        <span class="token-pill-name">${tok.name}</span>
                        <span class="token-pill-val">${displayVal}</span>
                    </div>
                `;
            });
            tokenItemsHtml += '</div>';
        }
        
        html += `
            <div class="tokens-category-card ${expandedClass}" id="cat-card-${type}">
                <div class="tokens-category-header" data-type="${type}">
                    <div class="tokens-category-header-left">
                        <i class="fa-solid ${cfg.icon}"></i>
                        <span>${cfg.label}</span>
                    </div>
                    <div class="tokens-category-header-right">
                        ${count > 0 ? `<span class="tokens-category-count">${count}</span>` : ''}
                        <button class="btn-add-token-inline" data-type="${type}" title="Adicionar Token"><i class="fa-solid fa-plus"></i></button>
                        <i class="fa-solid fa-chevron-down tokens-category-chevron"></i>
                    </div>
                </div>
                <div class="tokens-category-body">
                    ${tokenItemsHtml}
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
    
    container.querySelectorAll('.tokens-category-header').forEach(header => {
        header.addEventListener('click', (e) => {
            if (e.target.closest('.btn-add-token-inline')) return;
            
            const type = header.getAttribute('data-type');
            const card = document.getElementById(`cat-card-${type}`);
            if (card) {
                card.classList.toggle('expanded');
            }
        });
    });
    
    container.querySelectorAll('.btn-add-token-inline').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const type = btn.getAttribute('data-type');
            openCreateTokenModal(type);
        });
    });
    
    container.querySelectorAll('.token-pill').forEach(pill => {
        pill.addEventListener('click', (e) => {
            const name = pill.getAttribute('data-token-name');
            const type = pill.getAttribute('data-token-type');
            const desc = pill.getAttribute('data-token-desc');
            const activeSet = state.activeTokenSet || 'global';
            const tokenData = state.designTokens[activeSet]?.[name];
            const val = tokenData ? tokenData.$value : '';
            openEditTokenModal(name, type, val, desc);
        });
    });
}

function openCustomModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function closeCustomModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

// Modais - Temas
function openCreateThemeModal() {
    document.getElementById('theme-modal-title').textContent = 'Criar Tema';
    document.getElementById('theme-editor-id').value = '';
    document.getElementById('theme-editor-name').value = '';
    document.getElementById('theme-editor-desc').value = '';
    
    renderThemeEditorSetsCheckboxes({});
    
    openCustomModal('modal-theme-editor');
}

function openEditThemeModal() {
    if (!state.activeTokenTheme || !state.designTokens) return;
    const themes = state.designTokens.$themes || [];
    const theme = themes.find(t => t.id === state.activeTokenTheme);
    if (!theme) return;
    
    document.getElementById('theme-modal-title').textContent = 'Editar Tema';
    document.getElementById('theme-editor-id').value = theme.id;
    document.getElementById('theme-editor-name').value = theme.name;
    document.getElementById('theme-editor-desc').value = theme.description || '';
    
    renderThemeEditorSetsCheckboxes(theme.selectedTokenSets || {});
    
    openCustomModal('modal-theme-editor');
}

function renderThemeEditorSetsCheckboxes(selectedTokenSets) {
    const container = document.getElementById('theme-editor-sets-checkboxes');
    if (!container) return;
    
    const setOrder = state.designTokens.$metadata?.tokenSetOrder || [];
    if (setOrder.length === 0) {
        container.innerHTML = '<span class="placeholder-text" style="font-size:12px;">Crie sets primeiro.</span>';
        return;
    }
    
    let html = '';
    setOrder.forEach(setName => {
        const isEnabled = selectedTokenSets[setName] === 'enabled';
        const checked = isEnabled ? 'checked' : '';
        html += `
            <label style="display: flex; align-items: center; gap: 8px; font-size: 13px; cursor: pointer;">
                <input type="checkbox" class="theme-set-cb" data-set="${setName}" ${checked}>
                <span>${setName}</span>
            </label>
        `;
    });
    container.innerHTML = html;
}

async function saveThemeFromModal() {
    const id = document.getElementById('theme-editor-id').value;
    const name = document.getElementById('theme-editor-name').value.trim();
    const desc = document.getElementById('theme-editor-desc').value.trim();
    
    if (!name) {
        alert('Digite o nome do tema.');
        return;
    }
    
    if (!state.designTokens.$themes) {
        state.designTokens.$themes = [];
    }
    
    const selectedSets = {};
    document.querySelectorAll('.theme-set-cb').forEach(cb => {
        const setName = cb.getAttribute('data-set');
        if (cb.checked) {
            selectedSets[setName] = 'enabled';
        }
    });
    
    if (id) {
        const theme = state.designTokens.$themes.find(t => t.id === id);
        if (theme) {
            theme.name = name;
            theme.description = desc;
            theme.selectedTokenSets = selectedSets;
        }
    } else {
        const newTheme = {
            id: 'theme-' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5),
            name: name,
            group: "",
            description: desc,
            isSource: false,
            selectedTokenSets: selectedSets
        };
        state.designTokens.$themes.push(newTheme);
        state.activeTokenTheme = newTheme.id;
    }
    
    const activeThemes = [];
    if (state.activeTokenTheme) {
        const actTheme = state.designTokens.$themes.find(t => t.id === state.activeTokenTheme);
        if (actTheme) {
            activeThemes.push('/' + actTheme.name);
        }
    }
    if (!state.designTokens.$metadata) state.designTokens.$metadata = {};
    state.designTokens.$metadata.activeThemes = activeThemes;
    
    await saveDesignTokens();
    closeCustomModal('modal-theme-editor');
    loadDesignTokens();
}

// Modais - Sets
function openCreateSetModal() {
    document.getElementById('set-editor-name').value = '';
    openCustomModal('modal-set-editor');
}

async function saveSetFromModal() {
    const name = document.getElementById('set-editor-name').value.trim();
    if (!name) {
        alert('Digite o nome do set.');
        return;
    }
    
    const normalized = name.toLowerCase().replace(/[^a-z0-9-_]/g, '');
    if (!normalized) {
        alert('Nome inválido.');
        return;
    }
    
    if (state.designTokens[normalized]) {
        alert('Este set já existe.');
        return;
    }
    
    state.designTokens[normalized] = {};
    
    if (!state.designTokens.$metadata) state.designTokens.$metadata = {};
    if (!state.designTokens.$metadata.tokenSetOrder) state.designTokens.$metadata.tokenSetOrder = [];
    if (!state.designTokens.$metadata.activeSets) state.designTokens.$metadata.activeSets = [];
    
    state.designTokens.$metadata.tokenSetOrder.push(normalized);
    state.designTokens.$metadata.activeSets.push(normalized);
    state.activeTokenSet = normalized;
    
    await saveDesignTokens();
    closeCustomModal('modal-set-editor');
    loadDesignTokens();
}

function updateTokenEditorFormFields(tokenType) {
    const valueInput = document.getElementById('token-editor-value');
    if (!valueInput) return;
    const valueFormGroup = valueInput.closest('.form-group');
    const typographyFields = document.getElementById('token-editor-typography-fields');
    if (!typographyFields) return;
    
    if (tokenType === 'typography') {
        if (valueFormGroup) valueFormGroup.style.display = 'none';
        typographyFields.style.display = 'flex';
    } else {
        if (valueFormGroup) valueFormGroup.style.display = 'block';
        typographyFields.style.display = 'none';
    }
}

// Modais - Tokens
function openCreateTokenModal(preselectedType = 'color') {
    document.getElementById('token-modal-title').textContent = 'Criar Token';
    document.getElementById('token-editor-old-name').value = '';
    document.getElementById('token-editor-set').value = state.activeTokenSet || 'global';
    document.getElementById('token-editor-name').value = '';
    document.getElementById('token-editor-name').disabled = false;
    document.getElementById('token-editor-type').value = preselectedType;
    document.getElementById('token-editor-value').value = '';
    document.getElementById('token-editor-desc').value = '';
    
    // Reset Typography sub-form fields
    document.getElementById('token-editor-typo-fontFamily').value = '';
    document.getElementById('token-editor-typo-fontSize').value = '';
    document.getElementById('token-editor-typo-fontWeight').value = '';
    document.getElementById('token-editor-typo-lineHeight').value = '';
    document.getElementById('token-editor-typo-letterSpacing').value = '';
    document.getElementById('token-editor-typo-textCase').value = '';
    document.getElementById('token-editor-typo-textDecoration').value = '';
    
    updateTokenEditorFormFields(preselectedType);
    
    removeTokenDeleteButton();
    openCustomModal('modal-token-editor');
}

function openEditTokenModal(name, type, val, desc) {
    document.getElementById('token-modal-title').textContent = 'Editar Token';
    document.getElementById('token-editor-old-name').value = name;
    document.getElementById('token-editor-set').value = state.activeTokenSet || 'global';
    document.getElementById('token-editor-name').value = name;
    document.getElementById('token-editor-name').disabled = true;
    document.getElementById('token-editor-type').value = type;
    document.getElementById('token-editor-desc').value = desc;
    
    // Clear/Reset fields first
    document.getElementById('token-editor-value').value = '';
    document.getElementById('token-editor-typo-fontFamily').value = '';
    document.getElementById('token-editor-typo-fontSize').value = '';
    document.getElementById('token-editor-typo-fontWeight').value = '';
    document.getElementById('token-editor-typo-lineHeight').value = '';
    document.getElementById('token-editor-typo-letterSpacing').value = '';
    document.getElementById('token-editor-typo-textCase').value = '';
    document.getElementById('token-editor-typo-textDecoration').value = '';
    
    if (type === 'typography') {
        const valObj = (typeof val === 'object' && val !== null) ? val : {};
        document.getElementById('token-editor-typo-fontFamily').value = valObj.fontFamily || '';
        document.getElementById('token-editor-typo-fontSize').value = valObj.fontSize || '';
        document.getElementById('token-editor-typo-fontWeight').value = valObj.fontWeight || '';
        document.getElementById('token-editor-typo-lineHeight').value = valObj.lineHeight || '';
        document.getElementById('token-editor-typo-letterSpacing').value = valObj.letterSpacing || '';
        document.getElementById('token-editor-typo-textCase').value = valObj.textCase || valObj.textTransform || '';
        document.getElementById('token-editor-typo-textDecoration').value = valObj.textDecoration || '';
    } else {
        document.getElementById('token-editor-value').value = val;
    }
    
    updateTokenEditorFormFields(type);
    
    addTokenDeleteButton(name);
    openCustomModal('modal-token-editor');
}

function addTokenDeleteButton(tokenName) {
    removeTokenDeleteButton();
    const footer = document.querySelector('#modal-token-editor .modal-footer');
    if (footer) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-secondary';
        btn.id = 'btn-token-editor-delete';
        btn.style.background = 'var(--color-danger)';
        btn.style.borderColor = 'var(--color-danger)';
        btn.style.color = '#ffffff';
        btn.style.marginRight = 'auto';
        btn.innerHTML = '<i class="fa-solid fa-trash-can"></i> Excluir';
        
        btn.addEventListener('click', async () => {
            if (confirm(`Deseja realmente excluir o token "${tokenName}"?`)) {
                const activeSet = state.activeTokenSet || 'global';
                if (state.designTokens[activeSet]) {
                    delete state.designTokens[activeSet][tokenName];
                    await saveDesignTokens();
                    closeCustomModal('modal-token-editor');
                    loadDesignTokens();
                }
            }
        });
        footer.insertBefore(btn, footer.firstChild);
    }
}

function removeTokenDeleteButton() {
    const btn = document.getElementById('btn-token-editor-delete');
    if (btn) btn.remove();
}

async function saveTokenFromModal() {
    const oldName = document.getElementById('token-editor-old-name').value;
    const setName = document.getElementById('token-editor-set').value || 'global';
    const name = document.getElementById('token-editor-name').value.trim();
    const type = document.getElementById('token-editor-type').value;
    const desc = document.getElementById('token-editor-desc').value.trim();
    
    if (!name) {
        alert('Preencha o nome do token.');
        return;
    }
    
    let value;
    if (type === 'typography') {
        value = {
            fontFamily: document.getElementById('token-editor-typo-fontFamily').value.trim(),
            fontSize: document.getElementById('token-editor-typo-fontSize').value.trim(),
            fontWeight: document.getElementById('token-editor-typo-fontWeight').value.trim(),
            lineHeight: document.getElementById('token-editor-typo-lineHeight').value.trim(),
            letterSpacing: document.getElementById('token-editor-typo-letterSpacing').value.trim(),
            textCase: document.getElementById('token-editor-typo-textCase').value,
            textDecoration: document.getElementById('token-editor-typo-textDecoration').value
        };
        const allEmpty = Object.values(value).every(val => val === '');
        if (allEmpty) {
            alert('Preencha pelo menos um campo de tipografia.');
            return;
        }
    } else {
        value = document.getElementById('token-editor-value').value.trim();
        if (!value) {
            alert('Preencha o valor do token.');
            return;
        }
    }
    
    if (!state.designTokens[setName]) {
        state.designTokens[setName] = {};
    }
    
    state.designTokens[setName][name] = {
        "$value": value,
        "$type": type,
        "$description": desc
    };
    
    await saveDesignTokens();
    closeCustomModal('modal-token-editor');
    loadDesignTokens();
}

// Fim do gerenciador de tokens


function updateLineNumbers() {
    const textarea = document.getElementById('file-editor-textarea');
    const gutter = document.getElementById('editor-gutter');
    if (!textarea || !gutter) return;
    
    const lines = textarea.value.split('\n');
    const lineCount = lines.length;
    let numbersHtml = '';
    for (let i = 1; i <= lineCount; i++) {
        numbersHtml += `<div>${i}</div>`;
    }
    gutter.innerHTML = numbersHtml;
    gutter.scrollTop = textarea.scrollTop;
}

// Fecha dropdowns clicando fora deles
window.addEventListener('click', () => {
    closeAllDropdowns();
});

// --- PROD DATABASE CREDENTIALS MANAGER ---

function setDbCredentialsEditMode(editable) {
    const inputs = [
        'db-cred-user', 'db-cred-pass', 'db-cred-dbname', 'db-cred-rootpass',
        'db-cred-inthost', 'db-cred-intport', 'db-cred-inturl',
        'db-cred-exthost', 'db-cred-extport', 'db-cred-exturl'
    ];
    inputs.forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.disabled = !editable;
        }
    });
    
    document.getElementById('btn-db-cred-edit').style.display = editable ? 'none' : 'inline-flex';
    document.getElementById('btn-db-cred-save').style.display = editable ? 'inline-flex' : 'none';
    document.getElementById('btn-db-cred-cancel').style.display = editable ? 'inline-flex' : 'none';
}

async function loadProjectDbCredentials() {
    if (!state.activeProjectId) return;
    
    const inputs = [
        'db-cred-user', 'db-cred-pass', 'db-cred-dbname', 'db-cred-rootpass',
        'db-cred-inthost', 'db-cred-intport', 'db-cred-inturl',
        'db-cred-exthost', 'db-cred-extport', 'db-cred-exturl'
    ];
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/files/read?filepath=db_credentials.json`, {
            headers: getHeaders()
        });
        
        if (res.status === 404) {
            // Se o arquivo não existir, limpa todos os inputs
            inputs.forEach(id => {
                const input = document.getElementById(id);
                if (input) input.value = '';
            });
            return;
        } else if (!res.ok) {
            throw new Error(await res.text());
        }
        
        const data = await res.json();
        const creds = JSON.parse(data.content);
        
        document.getElementById('db-cred-user').value = creds.user || '';
        document.getElementById('db-cred-pass').value = creds.password || '';
        document.getElementById('db-cred-dbname').value = creds.database || '';
        document.getElementById('db-cred-rootpass').value = creds.rootPassword || '';
        document.getElementById('db-cred-inthost').value = creds.internalHost || '';
        document.getElementById('db-cred-intport').value = creds.internalPort || '';
        document.getElementById('db-cred-inturl').value = creds.internalUrl || '';
        document.getElementById('db-cred-exthost').value = creds.externalHost || '';
        document.getElementById('db-cred-extport').value = creds.externalPort || '';
        document.getElementById('db-cred-exturl').value = creds.externalUrl || '';
        
    } catch (e) {
        console.error("Erro ao carregar credenciais do banco:", e);
    }
}

async function saveProjectDbCredentials() {
    if (!state.activeProjectId) return;
    
    const creds = {
        user: document.getElementById('db-cred-user').value.trim(),
        password: document.getElementById('db-cred-pass').value.trim(),
        database: document.getElementById('db-cred-dbname').value.trim(),
        rootPassword: document.getElementById('db-cred-rootpass').value.trim(),
        internalHost: document.getElementById('db-cred-inthost').value.trim(),
        internalPort: document.getElementById('db-cred-intport').value.trim(),
        internalUrl: document.getElementById('db-cred-inturl').value.trim(),
        externalHost: document.getElementById('db-cred-exthost').value.trim(),
        externalPort: document.getElementById('db-cred-extport').value.trim(),
        externalUrl: document.getElementById('db-cred-exturl').value.trim()
    };
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/files/write`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                filepath: 'db_credentials.json',
                content: JSON.stringify(creds, null, 4)
            })
        });
        
        if (!res.ok) {
            throw new Error(await res.text());
        }
        
        alert("Credenciais salvas com sucesso no arquivo db_credentials.json!");
        setDbCredentialsEditMode(false);
        
    } catch (e) {
        alert("Erro ao salvar credenciais: " + e.message);
    }
}

// ==========================================
// --- NATIVE AI AGENT FUNCTIONS ---
// ==========================================

const AGENT_MODELS = {
    gemini: [
        { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro (Recomendado)' },
        { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash (Rápido)' },
        { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash' }
    ],
    openai: [
        { value: 'gpt-4o', label: 'GPT-4o (Recomendado)' },
        { value: 'gpt-4o-mini', label: 'GPT-4o Mini (Econômico)' },
        { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' }
    ]
};

function updateAgentModelOptions() {
    const provider = document.getElementById('agent-provider').value;
    const modelSelect = document.getElementById('agent-model');
    if (!modelSelect) return;
    
    modelSelect.innerHTML = '';
    const models = AGENT_MODELS[provider] || [];
    models.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m.value;
        opt.textContent = m.label;
        modelSelect.appendChild(opt);
    });
}

function toggleAgentApiKeyVisibility() {
    const input = document.getElementById('agent-apikey');
    const btn = document.getElementById('btn-toggle-agent-key');
    if (!input || !btn) return;
    
    const type = input.getAttribute('type');
    if (type === 'password') {
        input.setAttribute('type', 'text');
        btn.innerHTML = '<i class="fa-regular fa-eye-slash"></i>';
    } else {
        input.setAttribute('type', 'password');
        btn.innerHTML = '<i class="fa-regular fa-eye"></i>';
    }
}

async function loadAgentConfig() {
    try {
        const res = await fetch('/api/agent/config', { headers: getHeaders() });
        if (!res.ok) throw new Error('Falha ao obter configuração.');
        const config = await res.json();
        
        document.getElementById('agent-provider').value = config.provider || 'gemini';
        updateAgentModelOptions();
        
        document.getElementById('agent-model').value = config.model || '';
        document.getElementById('agent-apikey').value = config.api_key || '';
        
        // Habilita inputs se tivermos projeto ativo
        const promptInput = document.getElementById('agent-user-prompt');
        const sendBtn = document.getElementById('btn-send-agent-prompt');
        if (state.activeProjectId) {
            promptInput.disabled = false;
            sendBtn.disabled = false;
            promptInput.placeholder = "O que deseja que o agente faça? (ex: 'Crie um teste unitário para vcs.py' ou 'Corrija o gitignore')";
        } else {
            promptInput.disabled = true;
            sendBtn.disabled = true;
            promptInput.placeholder = "Selecione um projeto ativo para iniciar o agente.";
        }
        
        // Configura ferramentas
        const tools = config.enabled_tools || [];
        document.querySelectorAll('#agent-tools-container input[type="checkbox"]').forEach(cb => {
            cb.checked = tools.includes(cb.value);
        });
        
    } catch (err) {
        console.error('Erro ao carregar configuração do agente:', err);
    }
}

async function saveAgentConfigToServer() {
    const provider = document.getElementById('agent-provider').value;
    const model = document.getElementById('agent-model').value;
    const apiKey = document.getElementById('agent-apikey').value.trim();
    
    const enabled_tools = [];
    document.querySelectorAll('#agent-tools-container input[type="checkbox"]').forEach(cb => {
        if (cb.checked) enabled_tools.push(cb.value);
    });
    
    const payload = {
        provider,
        model,
        api_key: apiKey,
        enabled_tools
    };
    
    try {
        const res = await fetch('/api/agent/config', {
            method: 'POST',
            headers: {
                ...getHeaders(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!res.ok) throw new Error(await res.text());
        alert('Configuração do agente IA salva com sucesso!');
        loadAgentConfig();
    } catch (err) {
        alert('Erro ao salvar configuração: ' + err.message);
    }
}

function formatAgentMessage(text) {
    if (!text) return '';
    
    // Escapa HTML básico para evitar problemas de segurança
    let html = escapeHtml(text);
    
    // Converte os blocos de código
    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
        lang = lang || 'code';
        let filename = 'snippet';
        const firstLine = code.trim().split('\n')[0];
        const fileMatch = firstLine.match(/(?:#|\/\/|\/\*)\s*([a-zA-Z0-9_\-\.]+)/);
        if (fileMatch) {
            filename = fileMatch[1];
        } else if (state.activeFilepath) {
            filename = state.activeFilepath.split('/').pop().split('\\').pop();
        } else {
            filename = `codigo.${lang === 'python' ? 'py' : lang === 'javascript' ? 'js' : lang === 'sql' ? 'sql' : 'txt'}`;
        }
        
        // Remove comentário de nome de arquivo se existir na primeira linha
        let codeToShow = code;
        if (fileMatch) {
            const lines = code.split('\n');
            lines.shift();
            codeToShow = lines.join('\n');
        }
        
        // Vamos serializar e escapar o código para ser seguro no onclick
        const escapedCode = codeToShow.replace(/\\/g, '\\\\').replace(/`/g, '\\`').replace(/\$/g, '\\$').trim();
        
        return `
            <div class="code-block-card" style="background: rgba(0,0,0,0.3); border: 1px solid var(--border-color); border-radius: 8px; margin: 12px 0; overflow: hidden; display: flex; flex-direction: column;">
                <div class="code-block-header" style="display: flex; justify-content: space-between; align-items: center; padding: 8px 16px; background: rgba(255,255,255,0.02); border-bottom: 1px solid var(--border-color); font-size: 12px; color: var(--text-light);">
                    <span><i class="fa-solid fa-code" style="margin-right: 6px; color: var(--color-primary);"></i> ${filename}</span>
                    <button class="btn-copy-code" style="background: none; border: none; color: var(--text-muted); cursor: pointer; display: flex; align-items: center; gap: 4px; font-size: 11px;" onclick="navigator.clipboard.writeText(\`${escapedCode}\`).then(() => { this.innerHTML = '<i class=&quot;fa-solid fa-check&quot;></i> Copied'; setTimeout(() => this.innerHTML = '<i class=&quot;fa-solid fa-copy&quot;></i> Copy', 1500); })"><i class="fa-solid fa-copy"></i> Copy</button>
                </div>
                <pre style="margin: 0; padding: 16px; overflow-x: auto; font-family: monospace; font-size: 12px; line-height: 1.5; color: #e2e8f0; background: transparent;"><code style="font-family: inherit;">${codeToShow}</code></pre>
                <div class="code-block-actions" style="display: flex; gap: 10px; padding: 10px 16px; background: rgba(0,0,0,0.1); border-top: 1px solid var(--border-color);">
                    <button class="action-pill-btn btn-apply" style="display: flex; align-items: center; gap: 6px; background: var(--color-primary); border: none; border-radius: 20px; padding: 6px 12px; font-size: 11px; color: white; cursor: pointer;"><i class="fa-solid fa-check"></i> Apply Fix</button>
                    <button class="action-pill-btn btn-test" style="display: flex; align-items: center; gap: 6px; background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 20px; padding: 6px 12px; font-size: 11px; color: var(--text-light); cursor: pointer;"><i class="fa-solid fa-play"></i> Run test</button>
                    <button class="action-pill-btn btn-diff" style="display: flex; align-items: center; gap: 6px; background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 20px; padding: 6px 12px; font-size: 11px; color: var(--text-light); cursor: pointer;"><i class="fa-solid fa-eye"></i> View Diff</button>
                </div>
            </div>
        `;
    });
    
    // Converte negritos **texto**
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Converte códigos inline `codigo`
    html = html.replace(/`(.*?)`/g, '<code style="background: rgba(255,255,255,0.08); padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 12px; color: #f6ad55;">$1</code>');
    
    return html;
}

async function sendPromptToAgent(e) {
    if (e) e.preventDefault();
    
    const promptInput = document.getElementById('agent-user-prompt');
    const prompt = promptInput.value.trim();
    if (!prompt) return;
    
    if (!state.activeProjectId) {
        alert('Nenhum projeto selecionado.');
        return;
    }
    
    // Prepara interface
    promptInput.value = '';
    promptInput.disabled = true;
    document.getElementById('btn-send-agent-prompt').disabled = true;
    
    const chatHistory = document.getElementById('agent-chat-history');
    const monitor = document.getElementById('agent-monitor');
    const monitorLogs = document.getElementById('agent-monitor-logs');
    
    // Remove welcome msg se existir
    const welcome = chatHistory.querySelector('.agent-chat-welcome');
    if (welcome) welcome.remove();
    
    // Adiciona balão do usuário
    const userMsg = document.createElement('div');
    userMsg.className = 'user-message-wrapper';
    userMsg.style.cssText = 'display: flex; justify-content: flex-end; align-self: flex-end; max-width: 85%; margin-bottom: 14px; margin-left: auto;';
    userMsg.innerHTML = `
        <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border-color); border-radius: 12px; padding: 12px 16px; color: var(--text-light); font-size: 13px; line-height: 1.5; font-family: inherit;">
            ${escapeHtml(prompt)}
        </div>
    `;
    chatHistory.appendChild(userMsg);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    
    // Exibe monitor e limpa logs
    monitor.style.display = 'block';
    monitorLogs.innerHTML = `<div class="monitor-line status">Iniciando execução do agente local...</div>`;
    
    try {
        const response = await fetch(`/api/projects/${state.activeProjectId}/agent/run`, {
            method: 'POST',
            headers: {
                ...getHeaders(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt })
        });
        
        if (!response.ok) {
            throw new Error(await response.text());
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';
        
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop(); // Mantém o resto incompleto no buffer
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const jsonStr = line.substring(6).trim();
                    try {
                        const event = JSON.parse(jsonStr);
                        
                        if (event.type === 'status') {
                            const div = document.createElement('div');
                            div.className = 'monitor-line status';
                            div.textContent = event.content;
                            monitorLogs.appendChild(div);
                            monitor.scrollTop = monitor.scrollHeight;
                        } 
                        else if (event.type === 'thought') {
                            const div = document.createElement('div');
                            div.className = 'monitor-line thought';
                            div.textContent = `[PENSAMENTO]: ${event.content}`;
                            monitorLogs.appendChild(div);
                            monitor.scrollTop = monitor.scrollHeight;
                        } 
                        else if (event.type === 'tool_call') {
                            const div = document.createElement('div');
                            div.className = 'monitor-line tool';
                            div.textContent = `[AÇÃO (Ferramenta)]: Roda '${event.tool}' com args: ${JSON.stringify(event.args)}`;
                            monitorLogs.appendChild(div);
                            monitor.scrollTop = monitor.scrollHeight;
                        } 
                        else if (event.type === 'tool_result') {
                            const div = document.createElement('div');
                            div.className = 'monitor-line result';
                            div.textContent = `[RESULTADO]: ${event.result.substring(0, 300)}${event.result.length > 300 ? '...' : ''}`;
                            monitorLogs.appendChild(div);
                            monitor.scrollTop = monitor.scrollHeight;
                        } 
                        else if (event.type === 'final') {
                            // Cria balão do agente com a resposta final
                            const agentMsg = document.createElement('div');
                            agentMsg.className = 'agent-message-wrapper';
                            agentMsg.style.cssText = 'display: flex; gap: 12px; align-self: flex-start; max-width: 85%; margin-bottom: 14px;';
                            agentMsg.innerHTML = `
                                <!-- Avatar -->
                                <div style="background: rgba(139, 92, 246, 0.15); border: 1px solid rgba(139, 92, 246, 0.25); width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #a78bfa; font-size: 16px; flex-shrink: 0; margin-top: 4px;">
                                    <i class="fa-solid fa-robot"></i>
                                </div>
                                <!-- Conteúdo -->
                                <div style="flex: 1; display: flex; flex-direction: column;">
                                    <div class="agent-message-text" style="color: var(--text-light); font-size: 13px; line-height: 1.5;">
                                        ${formatAgentMessage(event.content)}
                                    </div>
                                </div>
                            `;
                            chatHistory.appendChild(agentMsg);
                            chatHistory.scrollTop = chatHistory.scrollHeight;
                        } 
                        else if (event.type === 'error') {
                            const div = document.createElement('div');
                            div.className = 'monitor-line error';
                            div.textContent = `[ERRO]: ${event.content}`;
                            monitorLogs.appendChild(div);
                            monitor.scrollTop = monitor.scrollHeight;
                        }
                    } catch (e) {
                        console.error('Erro ao fazer parse do streaming chunk:', e);
                    }
                }
            }
        }
        
    } catch (err) {
        const div = document.createElement('div');
        div.className = 'monitor-line error';
        div.textContent = `[FALHA NA CONEXÃO]: ${err.message}`;
        monitorLogs.appendChild(div);
        monitor.scrollTop = monitor.scrollHeight;
    } finally {
        promptInput.disabled = false;
        document.getElementById('btn-send-agent-prompt').disabled = false;
        promptInput.focus();
    }
}

function openCheckoutModal() {
    if (!state.activeProjectId) return;
    
    const selector = document.getElementById('checkout-branch-selector');
    selector.innerHTML = '<option value="">Carregando branches...</option>';
    
    openCustomModal('modal-checkout');
    
    fetch(`/api/projects/${state.activeProjectId}/git/branches`, {
        headers: getHeaders()
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            const current = data.current_branch || 'main';
            selector.innerHTML = '';
            
            // Lista todas as branches disponíveis
            const branches = data.all || [];
            if (branches.length === 0) {
                selector.innerHTML = '<option value="">Nenhuma branch disponível</option>';
                return;
            }
            
            branches.forEach(b => {
                const opt = document.createElement('option');
                opt.value = b;
                opt.textContent = b === current ? `${b} (ativa)` : b;
                selector.appendChild(opt);
            });
            selector.value = current;
        } else {
            selector.innerHTML = '<option value="">Erro ao carregar lista de branches</option>';
        }
    })
    .catch(err => {
        console.error('Erro ao listar branches:', err);
        selector.innerHTML = '<option value="">Erro ao carregar lista de branches</option>';
    });
}

async function runGitCheckout() {
    const selector = document.getElementById('checkout-branch-selector');
    const selectedBranch = selector.value;
    if (!selectedBranch) return;
    
    closeCustomModal('modal-checkout');
    
    appendGitConsole(`Alternando para a branch "${selectedBranch}"...`);
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/git/branches`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ name: selectedBranch })
        });
        
        if (!res.ok) {
            throw new Error(await res.text());
        }
        
        const data = await res.json();
        appendGitConsole(`Alternado para a branch "${selectedBranch}" com sucesso!`);
        loadGitStatus();
    } catch (err) {
        appendGitConsole(`Erro ao alternar para a branch: ${err.message}`, true);
        alert(`Erro ao alternar para a branch: ${err.message}`);
        loadGitStatus();
    }
}

async function runGitPush() {
    if (!state.activeProjectId) return;
    
    appendGitConsole(`Iniciando Git Push...`);
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/git/push`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ branch: null })
        });
        
        const data = await res.json();
        
        if (!res.ok) {
            throw new Error(data.detail || 'Erro desconhecido');
        }
        
        appendGitConsole(`Git Push executado com sucesso!\n${data.details || ''}`);
        alert('Git Push executado com sucesso!');
        loadGitStatus();
    } catch (err) {
        appendGitConsole(`Erro ao executar Git Push: ${err.message}`, true);
        alert(`Erro ao executar Git Push: ${err.message}`);
    }
}

async function runGitAbortMerge() {
    if (!state.activeProjectId) return;
    
    if (!confirm('Tem certeza que deseja abortar a mesclagem em andamento? Todas as alterações não resolvidas do merge serão descartadas.')) {
        return;
    }
    
    appendGitConsole(`Abortando mesclagem (git merge --abort)...`);
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/git/merge/abort`, {
            method: 'POST',
            headers: getHeaders()
        });
        
        const data = await res.json();
        
        if (!res.ok) {
            throw new Error(data.detail || 'Erro desconhecido');
        }
        
        appendGitConsole(`Mesclagem abortada com sucesso!`);
        alert('Mesclagem abortada com sucesso!');
        loadGitStatus();
    } catch (err) {
        appendGitConsole(`Erro ao abortar mesclagem: ${err.message}`, true);
        alert(`Erro ao abortar mesclagem: ${err.message}`);
    }
}

function updateGitGeneratedCommand() {
    const patInput = document.getElementById('git-pat-token-input');
    const cmdText = document.getElementById('git-generated-command-text');
    const copyBtn = document.getElementById('btn-copy-generated-git-cmd');
    const runBtn = document.getElementById('btn-run-generated-git-cmd');
    
    if (!patInput || !cmdText || !copyBtn || !runBtn) return;
    
    // Remove <> e espaços
    const token = patInput.value.replace(/[<> ]/g, '');
    
    if (!token) {
        cmdText.textContent = 'Digite o token acima para gerar o comando...';
        cmdText.style.color = 'var(--text-muted)';
        copyBtn.style.display = 'none';
        runBtn.disabled = true;
        return;
    }
    
    // Limpa a URL de origin caso já tenha token
    let cleanUrl = '';
    if (state.activeProject && state.activeProject.git_remote) {
        cleanUrl = state.activeProject.git_remote;
    } else {
        cleanUrl = state.activeProjectRemoteUrl || '';
    }
    
    if (cleanUrl.includes('@')) {
        const prefix = cleanUrl.startsWith('https://') ? 'https://' : 'http://';
        const remainder = cleanUrl.substring(prefix.length);
        if (remainder.includes('@')) {
            cleanUrl = prefix + remainder.split('@')[1];
        }
    }

    
    let displayUrl = cleanUrl || 'https://github.com/usuario/repositorio.git';
    let authUrl = displayUrl;
    
    if (displayUrl.startsWith('https://github.com/')) {
        authUrl = displayUrl.replace('https://github.com/', `https://${token}@github.com/`);
    } else if (displayUrl.startsWith('http://github.com/')) {
        authUrl = displayUrl.replace('http://github.com/', `http://${token}@github.com/`);
    }
    
    cmdText.textContent = `git remote set-url origin ${authUrl}`;
    cmdText.style.color = 'var(--color-primary)';
    copyBtn.style.display = 'block';
    runBtn.disabled = false;
}

async function runGitSetTokenAPI() {
    if (!state.activeProjectId) return;
    
    const patInput = document.getElementById('git-pat-token-input');
    if (!patInput) return;
    
    const token = patInput.value.replace(/[<> ]/g, '');
    if (!token) {
        alert('Digite um token de acesso válido.');
        return;
    }
    
    appendGitConsole(`Configurando Personal Access Token no repositório local...`);
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/git/token`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ token: token })
        });
        
        const data = await res.json();
        
        if (!res.ok) {
            throw new Error(data.detail || 'Erro desconhecido');
        }
        
        appendGitConsole(`Token configurado com sucesso!`);
        alert('Token de acesso configurado com sucesso no controle remoto!');
        
        // Limpa o input do token por privacidade
        patInput.value = '';
        updateGitGeneratedCommand();
        
        loadGitStatus();
    } catch (err) {
        appendGitConsole(`Erro ao configurar token: ${err.message}`, true);
        alert(`Erro ao configurar token: ${err.message}`);
    }
}

// --- SISTEMA DE DOCUMENTOS WORD ---

function renderDocumentsStateRow(tbody, { icon, message, variant = 'empty', spinning = false }) {
    tbody.innerHTML = '';

    const row = document.createElement('tr');
    row.className = `documents-state-row documents-state-row-${variant}`;

    const cell = document.createElement('td');
    cell.colSpan = 3;

    const stateBox = document.createElement('div');
    stateBox.className = 'documents-empty-state';

    const iconEl = document.createElement('i');
    iconEl.className = `${icon}${spinning ? ' fa-spin' : ''}`;

    const textEl = document.createElement('span');
    textEl.textContent = message;

    stateBox.appendChild(iconEl);
    stateBox.appendChild(textEl);
    cell.appendChild(stateBox);
    row.appendChild(cell);
    tbody.appendChild(row);
}

function resetDocumentPreviewState() {
    const sheet = document.getElementById('document-preview-sheet');
    const empty = document.getElementById('document-preview-empty');
    const badge = document.getElementById('preview-filename-badge');

    if (sheet) sheet.style.display = 'none';
    if (empty) empty.style.display = 'flex';
    if (badge) badge.style.display = 'none';
}

function buildDocumentTableRow(doc, tbody) {
    const tr = document.createElement('tr');
    tr.className = 'documents-table-row';
    tr.tabIndex = 0;

    const isSelected = state.selectedDocumentFilename === doc.filename;
    if (isSelected) {
        tr.classList.add('selected');
    }

    const nameCell = document.createElement('td');
    nameCell.className = 'doc-name-cell';

    const nameWrap = document.createElement('div');
    nameWrap.className = 'documents-name-wrap';

    const fileIcon = document.createElement('i');
    fileIcon.className = 'fa-regular fa-file-word';

    const filenameText = document.createElement('span');
    filenameText.textContent = doc.filename;
    filenameText.title = doc.filename;

    nameWrap.appendChild(fileIcon);
    nameWrap.appendChild(filenameText);
    nameCell.appendChild(nameWrap);

    const sizeCell = document.createElement('td');
    sizeCell.className = 'documents-size-cell';
    sizeCell.textContent = `${(doc.size_bytes / 1024).toFixed(1)} KB`;

    const actionsCell = document.createElement('td');
    actionsCell.className = 'documents-actions-cell';

    const downloadBtn = document.createElement('button');
    downloadBtn.className = 'btn btn-sm btn-primary btn-download-doc documents-row-action';
    downloadBtn.dataset.filename = doc.filename;
    downloadBtn.innerHTML = '<i class="fa-solid fa-download"></i> Baixar';

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'btn btn-sm btn-danger btn-delete-doc documents-row-action';
    deleteBtn.dataset.filename = doc.filename;
    deleteBtn.innerHTML = '<i class="fa-solid fa-trash-can"></i> Excluir';

    actionsCell.appendChild(downloadBtn);
    actionsCell.appendChild(deleteBtn);

    tr.appendChild(nameCell);
    tr.appendChild(sizeCell);
    tr.appendChild(actionsCell);

    const selectRow = () => {
        tbody.querySelectorAll('.documents-table-row').forEach(row => row.classList.remove('selected'));
        tr.classList.add('selected');
        state.selectedDocumentFilename = doc.filename;
        loadDocumentPreview(doc.filename);
    };

    tr.addEventListener('click', selectRow);
    tr.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            selectRow();
        }
    });

    downloadBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        downloadDocumentFile(e.currentTarget.dataset.filename);
    });

    deleteBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        deleteDocumentFile(e.currentTarget.dataset.filename);
    });

    return tr;
}

async function loadDocuments() {
    if (!state.activeProjectId) return;
    
    const tbody = document.getElementById('documents-table-body');
    if (!tbody) return;
    
    renderDocumentsStateRow(tbody, {
        icon: 'fa-solid fa-circle-notch',
        message: 'Carregando documentos...',
        variant: 'loading',
        spinning: true
    });
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/documents`);
        const documents = await res.json();
        
        if (!res.ok) {
            throw new Error(documents.detail || 'Erro ao carregar documentos');
        }
        
        if (documents.length === 0) {
            renderDocumentsStateRow(tbody, {
                icon: 'fa-solid fa-folder-open',
                message: 'Nenhum documento Word gerado ainda neste projeto.',
                variant: 'empty'
            });
            resetDocumentPreviewState();
            return;
        }
        
        tbody.innerHTML = '';
        documents.forEach(doc => {
            tbody.appendChild(buildDocumentTableRow(doc, tbody));
        });
        
        let docToSelect = documents[0];
        if (state.selectedDocumentFilename) {
            const found = documents.find(d => d.filename === state.selectedDocumentFilename);
            if (found) docToSelect = found;
        }
        
        if (docToSelect) {
            state.selectedDocumentFilename = docToSelect.filename;
            loadDocumentPreview(docToSelect.filename);
            const selectedRow = Array.from(tbody.querySelectorAll('.documents-table-row')).find(row => {
                const filename = row.querySelector('.btn-download-doc')?.dataset.filename;
                return filename === docToSelect.filename;
            });
            if (selectedRow) selectedRow.classList.add('selected');
        }
        
    } catch (err) {
        renderDocumentsStateRow(tbody, {
            icon: 'fa-solid fa-triangle-exclamation',
            message: `Erro ao listar documentos: ${err.message}`,
            variant: 'error'
        });
    }
}

async function downloadDocumentFile(filename) {
    if (!state.activeProjectId) return;
    try {
        const url = `/api/projects/${state.activeProjectId}/documents/${encodeURIComponent(filename)}/download`;
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    } catch (err) {
        alert(`Erro ao fazer download: ${err.message}`);
    }
}

async function deleteDocumentFile(filename) {
    if (!state.activeProjectId) return;
    if (!confirm(`Tem certeza que deseja excluir o documento "${filename}"?`)) return;
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/documents/${encodeURIComponent(filename)}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || 'Erro ao excluir o documento');
        }
        
        // Se o documento excluído for o que estava selecionado no estado, limpa a seleção
        if (state.selectedDocumentFilename === filename) {
            state.selectedDocumentFilename = null;
        }
        
        loadDocuments();
    } catch (err) {
        alert(`Erro ao excluir documento: ${err.message}`);
    }
}

async function generateTestDocument() {
    if (!state.activeProjectId) return;
    
    const btn = document.getElementById('btn-generate-test-doc');
    if (!btn) return;
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Gerando...`;
    
    try {
        const docPayload = {
            title: "Especificação Técnica - Projeto " + state.activeProject.name,
            sections: [
                {
                    heading: "1. Introdução",
                    text: "Este documento apresenta a especificação técnica e de arquitetura do projeto. O escopo contempla a análise de código, controle de versão nativo integrado com o Git, e integração de ferramentas avançadas.",
                    type: "paragraph"
                },
                {
                    heading: "2. Destaques do Projeto",
                    text: "Desenvolvimento rápido utilizando Python e FastAPI.\\nBanco de dados local leve com suporte a migrações em tempo real.\\nDesign moderno com suporte a tokens customizados.",
                    type: "bullet"
                },
                {
                    heading: "3. Nota Importante",
                    text: "Certifique-se de que todas as dependências estão devidamente instaladas executando 'pip install -r requirements.txt' antes de iniciar o servidor em ambiente de homologação ou produção.",
                    type: "highlight"
                },
                {
                    heading: "4. Exemplo de Código do Endpoint",
                    text: "@app.get(\\\"/api/info\\\")\\ndef get_server_info():\\n    return {\\\"status\\\": \\\"online\\\", \\\"version\\\": \\\"1.0.0\\\"}",
                    type: "code"
                },
                {
                    heading: "5. Tabela de Versões e Status",
                    text: '[["Componente", "Versão", "Status"], ["FastAPI", "0.110.0", "Homologado"], ["Python-docx", "1.1.0", "Adicionado"], ["SQLite", "3.x", "Ativo"]]',
                    type: "table"
                }
            ]
        };
        
        const res = await fetch(`/api/projects/${state.activeProjectId}/documents/word`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify(docPayload)
        });
        
        const data = await res.json();
        
        if (!res.ok) {
            throw new Error(data.detail || 'Erro ao gerar o documento');
        }
        
        alert(`Documento "${data.filename}" gerado com sucesso!`);
        loadDocuments();
    } catch (err) {
        alert(`Erro ao gerar documento de teste: ${err.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

async function handleDocumentUpload(e) {
    if (!state.activeProjectId) return;
    const fileInput = e.target;
    if (!fileInput.files || fileInput.files.length === 0) return;
    
    const file = fileInput.files[0];
    if (!file.name.endsWith('.docx')) {
        alert('Por favor, envie apenas arquivos com extensão .docx (Word).');
        fileInput.value = '';
        return;
    }
    
    const uploadBtn = document.getElementById('btn-upload-document');
    let originalText = '';
    if (uploadBtn) {
        originalText = uploadBtn.innerHTML;
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Enviando...`;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/documents/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${state.apiKey}`
            },
            body: formData
        });
        
        const data = await res.json();
        
        if (!res.ok) {
            throw new Error(data.detail || 'Erro ao realizar upload');
        }
        
        alert(`Documento "${data.filename}" enviado com sucesso!`);
        loadDocuments();
    } catch (err) {
        alert(`Erro ao enviar documento: ${err.message}`);
    } finally {
        fileInput.value = '';
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = originalText;
        }
    }
}

function copyDocPromptInstructions() {
    if (!state.activeProject) {
        alert('Por favor, selecione um projeto primeiro.');
        return;
    }
    
    const instructions = `Você é um engenheiro de software e documentador técnico assistindo o usuário no projeto ativo "${state.activeProject.name}" (ID: ${state.activeProjectId}) através do GitIDE.
Sempre que o usuário solicitar para você criar, editar, revisar ou atualizar qualquer tipo de documentação, especificação técnica, relatório, manual ou roteiro:
1. Você DEVE usar a ferramenta 'POST /api/projects/${state.activeProjectId}/documents/word' para gerar e salvar o documento real fisicamente como um arquivo Word (.docx).
2. NUNCA envie o conteúdo completo da documentação diretamente como texto ou markdown no chat do ChatGPT. Em vez disso, utilize o endpoint para persistir o arquivo e depois dê apenas uma breve explicação ao usuário sobre o que foi gerado.
3. Formate a requisição estruturando o conteúdo em seções ("sections"). Cada seção pode conter os seguintes tipos de formatação (campo "type"):
   - "paragraph": para texto corrido.
   - "bullet": para listas de tópicos (separe os itens com quebras de linha '\\n').
   - "highlight": para caixas de destaque ou observações importantes.
   - "code": para blocos de código fonte (preservando indentação e quebras de linha).
   - "table": para tabelas. O campo "text" deve conter uma matriz JSON válida em formato string, por exemplo: '[["Coluna 1", "Coluna 2"], ["Dado A", "Dado B"]]'.
4. Certifique-se de que o título do documento ("title") seja descritivo e claro.`;

    navigator.clipboard.writeText(instructions).then(() => {
        const btn = document.getElementById('btn-copy-doc-prompt-instructions');
        if (btn) {
            const originalText = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = `<i class="fa-solid fa-check" style="color: var(--color-success);"></i> Copiado!`;
            setTimeout(() => {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }, 2000);
        }
    }).catch(err => {
        console.error('Erro ao copiar para clipboard:', err);
        alert('Não foi possível copiar as instruções.');
    });
}

async function loadDocumentPreview(filename) {
    if (!state.activeProjectId) return;
    
    const sheet = document.getElementById('document-preview-sheet');
    const empty = document.getElementById('document-preview-empty');
    const badge = document.getElementById('preview-filename-badge');
    
    if (!sheet || !empty) return;
    
    sheet.style.display = 'block';
    empty.style.display = 'none';
    
    if (badge) {
        badge.textContent = filename;
        badge.style.display = 'inline-block';
    }
    
    sheet.innerHTML = `
        <div style="display: flex; justify-content: center; align-items: center; min-height: 200px; color: #475569;">
            <i class="fa-solid fa-circle-notch fa-spin" style="font-size: 32px; margin-right: 12px; color: #4F46E5;"></i>
            <span>Processando prévia do documento...</span>
        </div>
    `;
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/documents/${encodeURIComponent(filename)}/preview`);
        const data = await res.json();
        
        if (!res.ok) {
            throw new Error(data.detail || 'Erro ao carregar prévia');
        }
        
        renderDocumentPreview(data);
    } catch (err) {
        sheet.innerHTML = `
            <div style="color: #ef4444; padding: 20px; text-align: center;">
                <i class="fa-solid fa-triangle-exclamation" style="font-size: 32px; margin-bottom: 12px;"></i>
                <p style="font-weight: bold;">Erro ao carregar prévia:</p>
                <p style="font-size: 13px;">${err.message}</p>
            </div>
        `;
    }
}

function renderDocumentPreview(data) {
    const sheet = document.getElementById('document-preview-sheet');
    if (!sheet) return;
    
    sheet.innerHTML = '';
    
    // 1. Título do Documento
    const titleEl = document.createElement('h1');
    titleEl.textContent = data.title || 'Documento';
    titleEl.style.fontFamily = 'Arial, sans-serif';
    titleEl.style.fontSize = '20px';
    titleEl.style.fontWeight = 'bold';
    titleEl.style.color = '#000000'; // Black
    titleEl.style.margin = '0 0 4px 0';
    sheet.appendChild(titleEl);
    
    // Linha divisória
    const divider = document.createElement('div');
    divider.style.width = '100%';
    divider.style.height = '1.5px';
    divider.style.background = '#000000';
    divider.style.marginBottom = '16px';
    sheet.appendChild(divider);
    
    // Metadados
    const meta = document.createElement('p');
    meta.style.fontFamily = 'Calibri, sans-serif';
    meta.style.fontSize = '8.5pt';
    meta.style.color = '#4B5563'; // Gray-600
    meta.style.fontStyle = 'italic';
    meta.style.margin = '0 0 20px 0';
    meta.style.lineHeight = '1.4';
    meta.innerHTML = `Data de Geração: ${new Date().toLocaleString()}<br>Gerado via: Agente GitIDE`;
    sheet.appendChild(meta);
    
    // 2. Seções
    if (data.sections && data.sections.length > 0) {
        data.sections.forEach(sec => {
            // Se houver heading, renderiza
            if (sec.heading && sec.heading.trim() !== '') {
                const headingEl = document.createElement('h2');
                headingEl.textContent = sec.heading.trim();
                headingEl.style.fontFamily = 'Arial, sans-serif';
                headingEl.style.fontSize = '13px';
                headingEl.style.fontWeight = 'bold';
                headingEl.style.color = '#000000';
                headingEl.style.marginTop = '14px';
                headingEl.style.marginBottom = '6px';
                sheet.appendChild(headingEl);
            }
            
            if (!sec.text || sec.text.trim() === '') return;
            
            const type = (sec.type || 'paragraph').toLowerCase().trim();
            
            if (type === 'paragraph') {
                const p = document.createElement('p');
                p.textContent = sec.text;
                p.style.fontFamily = 'Calibri, sans-serif';
                p.style.fontSize = '10pt';
                p.style.color = '#111827';
                p.style.lineHeight = '1.15';
                p.style.marginBottom = '8px';
                sheet.appendChild(p);
                
            } else if (type === 'bullet') {
                const ul = document.createElement('ul');
                ul.style.paddingLeft = '20px';
                ul.style.marginBottom = '8px';
                ul.style.listStyleType = 'disc';
                
                const lines = sec.text.split('\n');
                lines.forEach(line => {
                    const cleanLine = line.trim().replace(/^[-*]\s+/, '');
                    if (cleanLine) {
                        const li = document.createElement('li');
                        li.textContent = cleanLine;
                        li.style.fontFamily = 'Calibri, sans-serif';
                        li.style.fontSize = '10pt';
                        li.style.color = '#111827';
                        li.style.marginBottom = '3px';
                        ul.appendChild(li);
                    }
                });
                sheet.appendChild(ul);
                
            } else if (type === 'highlight') {
                const callout = document.createElement('div');
                callout.style.background = '#F9FAFB';
                callout.style.borderLeft = '1.5px solid #9CA3AF';
                callout.style.padding = '8px 12px';
                callout.style.marginBottom = '12px';
                callout.style.borderRadius = '2px';
                
                const p = document.createElement('p');
                p.textContent = sec.text;
                p.style.fontFamily = 'Calibri, sans-serif';
                p.style.fontSize = '9.5pt';
                p.style.color = '#4B5563';
                p.style.fontStyle = 'italic';
                p.style.margin = '0';
                p.style.lineHeight = '1.4';
                callout.appendChild(p);
                sheet.appendChild(callout);
                
            } else if (type === 'code') {
                const pre = document.createElement('pre');
                pre.style.background = '#F9FAFB';
                pre.style.padding = '10px';
                pre.style.borderRadius = '4px';
                pre.style.overflowX = 'auto';
                pre.style.marginBottom = '12px';
                pre.style.border = '1px solid #E5E7EB';
                
                const code = document.createElement('code');
                code.textContent = sec.text;
                code.style.fontFamily = 'Consolas, monospace';
                code.style.fontSize = '9pt';
                code.style.color = '#374151';
                pre.appendChild(code);
                sheet.appendChild(pre);
                
            } else if (type === 'table') {
                try {
                    const matrix = JSON.parse(sec.text);
                    if (Array.isArray(matrix) && matrix.length > 0) {
                        const table = document.createElement('table');
                        table.style.width = '100%';
                        table.style.borderCollapse = 'collapse';
                        table.style.marginBottom = '12px';
                        table.style.fontFamily = 'Calibri, sans-serif';
                        table.style.fontSize = '9.5pt';
                        
                        matrix.forEach((rowData, rIdx) => {
                            const tr = document.createElement('tr');
                            const isHeader = rIdx === 0;
                            
                            rowData.forEach(cellVal => {
                                const cell = document.createElement(isHeader ? 'th' : 'td');
                                cell.textContent = cellVal;
                                cell.style.border = '1px solid #D1D5DB';
                                cell.style.padding = '6px';
                                
                                if (isHeader) {
                                    cell.style.background = '#374151';
                                    cell.style.color = '#ffffff';
                                    cell.style.fontWeight = 'bold';
                                    cell.style.textAlign = 'center';
                                } else {
                                    cell.style.color = '#111827';
                                    if (rIdx % 2 === 1) {
                                        cell.style.background = '#F9FAFB';
                                    }
                                }
                                tr.appendChild(cell);
                            });
                            table.appendChild(tr);
                        });
                        sheet.appendChild(table);
                    }
                } catch (err) {
                    const fallback = document.createElement('p');
                    fallback.textContent = `[Tabela: ${sec.text}]`;
                    fallback.style.color = '#ef4444';
                    fallback.style.fontStyle = 'italic';
                    sheet.appendChild(fallback);
                }
            }
        });
    }
}

// --- CUSTOM SELECT COMPONENT ---

function initCustomSelects() {
    // 1. Sobrescrever o setter de .value do HTMLSelectElement para podermos escutar modificações programáticas
    const originalValueDescriptor = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value');
    Object.defineProperty(HTMLSelectElement.prototype, 'value', {
        get() {
            return originalValueDescriptor.get.call(this);
        },
        set(val) {
            originalValueDescriptor.set.call(this, val);
            // Sincroniza o custom select correspondente se existir
            const wrapper = this.nextElementSibling;
            if (wrapper && wrapper.classList.contains('custom-select-container')) {
                syncCustomSelectValue(this, wrapper);
            }
        }
    });

    // 2. Inicializa cada select.select-input no DOM
    const selectElements = document.querySelectorAll('select.select-input');
    selectElements.forEach(select => {
        setupCustomSelect(select);
    });

    // 3. Listener global para fechar dropdowns ao clicar fora
    document.addEventListener('click', () => {
        document.querySelectorAll('.custom-select-container.open').forEach(container => {
            container.classList.remove('open');
        });
    });
}

function setupCustomSelect(select) {
    if (select.nextElementSibling && select.nextElementSibling.classList.contains('custom-select-container')) {
        return; // Já inicializado
    }

    // Oculta o select nativo
    select.style.display = 'none';

    // Cria o wrapper e elementos do custom select
    const container = document.createElement('div');
    container.className = 'custom-select-container';
    if (select.id) {
        container.id = `custom-select-for-${select.id}`;
    }

    const trigger = document.createElement('div');
    trigger.className = 'custom-select-trigger';
    trigger.setAttribute('tabindex', '0');
    if (select.disabled) {
        trigger.classList.add('disabled');
        trigger.setAttribute('tabindex', '-1');
    }

    const valueSpan = document.createElement('span');
    valueSpan.className = 'custom-select-value';
    
    const arrowIcon = document.createElement('i');
    arrowIcon.className = 'fa-solid fa-chevron-down custom-select-arrow';

    trigger.appendChild(valueSpan);
    trigger.appendChild(arrowIcon);

    const dropdown = document.createElement('div');
    dropdown.className = 'custom-select-dropdown';

    container.appendChild(trigger);
    container.appendChild(dropdown);

    // Insere o wrapper logo após o select original
    select.parentNode.insertBefore(container, select.nextSibling);

    // Índice de opção atualmente realçada via teclado
    let highlightedIndex = -1;

    // Função para renderizar as opções do dropdown com base no select original
    function renderOptions() {
        dropdown.innerHTML = '';
        highlightedIndex = -1;

        const children = Array.from(select.children);

        children.forEach(child => {
            if (child.tagName === 'OPTGROUP') {
                const groupContainer = document.createElement('div');
                groupContainer.className = 'custom-select-group';

                const groupTitle = document.createElement('div');
                groupTitle.className = 'custom-select-group-title';
                groupTitle.textContent = child.label;
                groupContainer.appendChild(groupTitle);

                const options = Array.from(child.querySelectorAll('option'));
                options.forEach(opt => {
                    const optionEl = createOptionElement(opt);
                    groupContainer.appendChild(optionEl);
                });

                dropdown.appendChild(groupContainer);
            } else if (child.tagName === 'OPTION') {
                const optionEl = createOptionElement(child);
                dropdown.appendChild(optionEl);
            }
        });

        // Atualiza o texto selecionado no trigger
        updateTriggerText();
    }

    function createOptionElement(nativeOpt) {
        const optEl = document.createElement('div');
        optEl.className = 'custom-select-option';
        optEl.textContent = nativeOpt.textContent;
        optEl.setAttribute('data-value', nativeOpt.value);

        if (nativeOpt.selected) {
            optEl.classList.add('selected');
        }

        optEl.addEventListener('click', (e) => {
            e.stopPropagation();
            if (select.disabled) return;
            
            // Define o valor no select original
            select.value = nativeOpt.value;
            // Dispara o evento de mudança nativo
            select.dispatchEvent(new Event('change', { bubbles: true }));
            
            closeDropdown();
        });

        return optEl;
    }

    function updateTriggerText() {
        const selectedOpt = select.options[select.selectedIndex];
        valueSpan.textContent = selectedOpt ? selectedOpt.textContent : '';
    }

    // Sincroniza estado de seleção visual
    function syncSelection() {
        const val = select.value;
        const options = dropdown.querySelectorAll('.custom-select-option');
        options.forEach(opt => {
            if (opt.getAttribute('data-value') === val) {
                opt.classList.add('selected');
            } else {
                opt.classList.remove('selected');
            }
        });
        updateTriggerText();
    }

    // Abre/fecha dropdown
    function toggleDropdown() {
        if (select.disabled) return;
        
        const isOpen = container.classList.contains('open');
        if (isOpen) {
            closeDropdown();
        } else {
            // Fecha outros dropdowns abertos antes
            document.querySelectorAll('.custom-select-container.open').forEach(c => {
                if (c !== container) c.classList.remove('open');
            });
            container.classList.add('open');
            container.classList.add('focused');
            // Foca o trigger para habilitar escuta de teclado
            trigger.focus();
            highlightedIndex = -1;
            highlightFirstSelected();
        }
    }

    function closeDropdown() {
        container.classList.remove('open');
        removeHighlight();
    }

    function highlightFirstSelected() {
        const options = Array.from(dropdown.querySelectorAll('.custom-select-option'));
        const selectedIdx = options.findIndex(opt => opt.classList.contains('selected'));
        if (selectedIdx !== -1) {
            highlightOption(selectedIdx);
        }
    }

    function highlightOption(index) {
        const options = Array.from(dropdown.querySelectorAll('.custom-select-option'));
        removeHighlight();
        if (index >= 0 && index < options.length) {
            highlightedIndex = index;
            const opt = options[index];
            opt.classList.add('highlighted');
            // Garante scroll visibility
            opt.scrollIntoView({ block: 'nearest' });
        }
    }

    function removeHighlight() {
        dropdown.querySelectorAll('.custom-select-option.highlighted').forEach(o => o.classList.remove('highlighted'));
    }

    // Handlers de eventos
    trigger.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleDropdown();
    });

    trigger.addEventListener('focus', () => {
        if (!select.disabled) {
            container.classList.add('focused');
        }
    });

    trigger.addEventListener('blur', () => {
        container.classList.remove('focused');
        // Fecha com um pequeno delay para capturar o click caso clique em uma opção
        setTimeout(() => {
            if (!container.classList.contains('focused')) {
                closeDropdown();
            }
        }, 150);
    });

    // Navegação via teclado
    trigger.addEventListener('keydown', (e) => {
        if (select.disabled) return;
        const options = Array.from(dropdown.querySelectorAll('.custom-select-option'));

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (!container.classList.contains('open')) {
                toggleDropdown();
            } else {
                let nextIdx = highlightedIndex + 1;
                if (nextIdx >= options.length) nextIdx = 0;
                highlightOption(nextIdx);
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (!container.classList.contains('open')) {
                toggleDropdown();
            } else {
                let prevIdx = highlightedIndex - 1;
                if (prevIdx < 0) prevIdx = options.length - 1;
                highlightOption(prevIdx);
            }
        } else if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            if (!container.classList.contains('open')) {
                toggleDropdown();
            } else {
                if (highlightedIndex >= 0 && highlightedIndex < options.length) {
                    options[highlightedIndex].click();
                } else {
                    closeDropdown();
                }
            }
        } else if (e.key === 'Escape' || e.key === 'Tab') {
            closeDropdown();
        }
    });

    // Render inicial
    renderOptions();

    // 3. Usa MutationObserver para escutar mudanças no select original
    const observer = new MutationObserver((mutations) => {
        mutations.forEach(mutation => {
            if (mutation.type === 'childList') {
                renderOptions();
            } else if (mutation.type === 'attributes' && mutation.attributeName === 'disabled') {
                if (select.disabled) {
                    trigger.classList.add('disabled');
                    trigger.setAttribute('tabindex', '-1');
                    closeDropdown();
                } else {
                    trigger.classList.remove('disabled');
                    trigger.setAttribute('tabindex', '0');
                }
            }
        });
    });

    observer.observe(select, { 
        childList: true, 
        attributes: true, 
        attributeFilter: ['disabled'] 
    });

    // Registra uma referência de sincronização de valor para uso pelo setter modificado
    container.syncValue = syncSelection;
}

function syncCustomSelectValue(select, wrapper) {
    if (wrapper && typeof wrapper.syncValue === 'function') {
        wrapper.syncValue();
    }
}

// --- PENDING COMMANDS APPROVAL ---

async function loadPendingCommands() {
    if (!state.activeProjectId) return;
    
    const panel = document.getElementById('pending-commands-panel');
    const list = document.getElementById('pending-commands-list');
    if (!panel || !list) return;
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/execute/pending`, {
            headers: getHeaders()
        });
        const data = await res.json();
        
        if (data && data.length > 0) {
            panel.style.display = 'block';
            list.innerHTML = '';
            
            data.forEach(cmd => {
                const item = document.createElement('div');
                item.className = 'pending-command-item';
                item.style.display = 'flex';
                item.style.justifyContent = 'space-between';
                item.style.alignItems = 'center';
                item.style.background = 'rgba(255,255,255,0.02)';
                item.style.border = '1px solid var(--border-color)';
                item.style.borderRadius = '6px';
                item.style.padding = '10px 14px';
                
                const dateStr = new Date(cmd.created_at).toLocaleString('pt-BR');
                
                item.innerHTML = `
                    <div style="display: flex; flex-direction: column; gap: 4px; min-width: 0; flex: 1; text-align: left;">
                        <span style="font-family: var(--font-mono); font-size: 13px; color: var(--text-light); word-break: break-all;">${cmd.command}</span>
                        <span style="font-size: 11px; color: var(--text-dark);">Recebido em: ${dateStr}</span>
                    </div>
                    <div style="display: flex; gap: 8px; flex-shrink: 0; margin-left: 14px;">
                        <button class="btn btn-sm" id="btn-approve-${cmd.id}" style="background: var(--color-success); border-color: rgba(255,255,255,0.05); min-height: 28px !important; padding: 4px 10px; font-size: 12px; cursor: pointer; color: white;">
                            <i class="fa-solid fa-check"></i> Permitir
                        </button>
                        <button class="btn btn-sm" id="btn-reject-${cmd.id}" style="background: var(--color-danger); border-color: rgba(255,255,255,0.05); min-height: 28px !important; padding: 4px 10px; font-size: 12px; cursor: pointer; color: white;">
                            <i class="fa-solid fa-xmark"></i> Rejeitar
                        </button>
                    </div>
                `;
                
                list.appendChild(item);
                
                // Event listeners
                document.getElementById(`btn-approve-${cmd.id}`).addEventListener('click', () => approveCommand(cmd.id));
                document.getElementById(`btn-reject-${cmd.id}`).addEventListener('click', () => rejectCommand(cmd.id));
            });
        } else {
            panel.style.display = 'none';
        }
    } catch (err) {
        console.error('Erro ao buscar comandos pendentes:', err);
    }
}

function startPendingCommandsPolling() {
    if (window.pendingCommandsInterval) {
        clearInterval(window.pendingCommandsInterval);
    }
    window.pendingCommandsInterval = setInterval(() => {
        if (state.activeTab === 'tab-terminal' && state.activeProjectId) {
            loadPendingCommands();
        } else {
            clearInterval(window.pendingCommandsInterval);
            window.pendingCommandsInterval = null;
        }
    }, 4000);
}

async function approveCommand(commandId) {
    if (!state.activeProjectId) return;
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/execute/pending/${commandId}/approve`, {
            method: 'POST',
            headers: getHeaders()
        });
        const data = await res.json();
        if (data.status === 'success') {
            loadPendingCommands();
        } else {
            alert(`Erro ao aprovar comando: ${data.detail}`);
        }
    } catch (err) {
        alert(`Erro ao aprovar comando: ${err.message}`);
    }
}

async function rejectCommand(commandId) {
    if (!state.activeProjectId) return;
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/execute/pending/${commandId}/reject`, {
            method: 'POST',
            headers: getHeaders()
        });
        const data = await res.json();
        if (data.status === 'success') {
            loadPendingCommands();
        } else {
            alert(`Erro ao rejeitar comando: ${data.detail}`);
        }
    } catch (err) {
        alert(`Erro ao rejeitar comando: ${err.message}`);
    }
}
