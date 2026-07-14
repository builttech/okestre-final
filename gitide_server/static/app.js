// --- Act IA FRONTEND ENGINE ---

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
    gridColumns: [],

    // Git conflict resolver
    gitConflicts: [],
    gitConflictActiveFile: null,
    gitConflictBlocks: [],

    // Ops Infra
    opsEnvVariables: [],
    opsVmAccess: null,
    opsVmBrowserPath: '/',

    // Native Agent
    agentChatMessages: [],
    agentWorkflowEvents: [],
    agentHistoryLoadedProjectId: null,

    // QA
    qaAnnotations: [],
    qaView: 'list',

    // Engineering Metrics
    engineeringMetrics: null,

    // Project Estimation
    estimationReport: null,
    estimationMode: 'comparison',
    estimationView: 'open'
};

window.gitideAppState = state;

const uiCanvasState = {
    files: [],
    filepath: '',
    doc: null,
    selectedLayerId: null,
    tool: 'select',
    zoom: 1,
    drag: null,
    resize: null
};

const UI_CANVAS_FRAME_PRESETS = {
    section: { name: 'Section', width: 960, height: 540 },
    iphone17: { name: 'iPhone 17', width: 402, height: 874 },
    iphone16: { name: 'iPhone 16', width: 393, height: 852 },
    'android-compact': { name: 'Android Compact', width: 412, height: 917 },
    'ipad-mini': { name: 'iPad mini 8.3', width: 744, height: 1133 },
    'ipad-pro': { name: 'iPad Pro 12.9', width: 1024, height: 1366 },
    desktop: { name: 'Desktop', width: 1440, height: 1024 },
    'macbook-air': { name: 'MacBook Air', width: 1280, height: 832 },
    'slide-16-9': { name: 'Slide 16:9', width: 1920, height: 1080 }
};

const UI_CANVAS_ICON_OPTIONS = [
    'sparkles', 'plus', 'x', 'check', 'arrow-right', 'arrow-left', 'chevron-down',
    'search', 'settings', 'user', 'users', 'home', 'menu', 'bell', 'heart',
    'star', 'trash-2', 'edit-3', 'copy', 'download', 'upload', 'save',
    'folder', 'file', 'image', 'video', 'calendar', 'clock', 'mail',
    'phone', 'link', 'lock', 'unlock', 'shield', 'bug', 'git-branch',
    'database', 'terminal', 'layout-dashboard', 'panel-right'
];

const workspaceDeleteState = {
    filepath: '',
    name: '',
    type: 'file'
};

async function loadProdReadinessValidator() {
    const target = document.getElementById('prod-readiness-validator-text');
    if (!target) return;
    target.textContent = buildProdReadinessValidatorPrompt();
    target.dataset.loaded = 'true';
}
window.loadProdReadinessValidator = loadProdReadinessValidator;

function buildProdReadinessValidatorPrompt() {
    const projectName = state.activeProject?.name || 'Projeto ativo não selecionado';
    const projectId = state.activeProjectId || 'NÃO INFORMADO';
    return `Execute a auditoria Production-Ready neste projeto do Act IA.

Project ID: ${projectId}
Projeto: ${projectName}

Antes de iniciar, leia e siga rigorosamente o arquivo PROD_READINESS_VALIDATOR.md na raiz do workspace.

Audite o projeto de ponta a ponta, salve o relatório completo em:
.documents/prod-readiness/prod-readiness-report.md

Depois siga o fluxo Harness obrigatório descrito no arquivo: crie ou atualize REQ, revise Design, crie Task List e task.details, aguarde validação do usuário e execute somente uma task por vez quando aprovada.

No chat, responda somente com:
- veredito final;
- pontuação de prontidão;
- quantidade de Blockers, Warnings e Infos;
- caminho do relatório salvo;
- documentos Harness atualizados;
- tasks criadas;
- próximos passos mínimos para aprovação.`;
}

async function loadSecurityRulesPrompt() {
    const target = document.getElementById('security-rules-text');
    if (!target) return;
    target.textContent = buildSecurityRulesPrompt();
    target.dataset.loaded = 'true';
}
window.loadSecurityRulesPrompt = loadSecurityRulesPrompt;

function buildSecurityRulesPrompt() {
    const projectName = state.activeProject?.name || 'Projeto ativo não selecionado';
    const projectId = state.activeProjectId || 'NÃO INFORMADO';
    return `Execute o Security Review/AppSec neste projeto do Act IA.

Project ID: ${projectId}
Projeto: ${projectName}

Antes de iniciar, leia e siga rigorosamente o arquivo SECURITY_RULES.md na raiz do workspace.

Audite código, arquitetura, autenticação, autorização, segredos, dados, dependências e infraestrutura.

Salve o relatório completo em:
.documents/security/security-review-report.md

Depois siga o fluxo Harness obrigatório descrito no arquivo: crie ou atualize REQ, revise Design, crie Task List e task.details, aguarde validação do usuário e execute somente uma task por vez quando aprovada.

No chat, responda somente com:
- veredito de segurança;
- quantidade de Critical, High, Medium, Low e Info;
- principais riscos bloqueantes;
- caminho do relatório salvo;
- documentos Harness atualizados;
- tasks criadas;
- próximos passos mínimos de mitigação.`;
}

function buildOpsInfraGptActionPrompt() {
    const projectName = state.activeProject?.name || 'Projeto ativo não selecionado';
    const projectId = state.activeProjectId || 'NÃO INFORMADO';
    return `Execute a gestao e operacao Ops Infra deste projeto no Act IA.

Project ID: ${projectId}
Projeto: ${projectName}

Antes de iniciar, leia e siga rigorosamente o arquivo OPS_INFRA_OPERATOR.md na raiz do workspace.

Use o OpenAPI dedicado do Ops Infra:
/api/ops-infra-openapi.json

Objetivo:
- validar acesso SSH da VM;
- preparar a VM instalando Docker, Docker Compose, Git e portas basicas;
- sincronizar o projeto na VM via Git;
- detectar stack;
- validar ambiente e secrets;
- gerar/revisar artefatos de deploy;
- configurar dominio/Caddy quando solicitado;
- validar DNS apontando para a VM;
- operar Docker Compose na VM com build, up, status, logs, restart ou down.
- validar banco e health check HTTP/HTTPS depois do deploy.

Regras:
- Nunca peça senha, chave privada ou token no chat.
- Nunca exponha secrets.
- Nao execute down ou acao destrutiva sem confirmacao explicita.
- Use sempre o Project ID acima em todas as chamadas.
- Ao falhar, diagnostique com status/logs antes de tentar novamente.

No chat, responda somente com:
- estado atual da VM/app;
- acoes executadas;
- evidencias relevantes;
- riscos ou pendencias;
- proximo passo recomendado.`;
}

function refreshOpsInfraGptActionPrompt() {
    const target = document.getElementById('ops-gpt-action-prompt');
    if (!target) return;
    target.textContent = buildOpsInfraGptActionPrompt();
}

// --- CUSTOM SELECT COMPONENT ---

// --- INICIALIZAÇÃO ---
document.addEventListener('DOMContentLoaded', () => {
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
        applySidebarCollapsedState(localStorage.getItem('gitide_sidebar_collapsed') === 'true');

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
        alert('Erro ao conectar com o backend do Act IA. Certifique-se de que o servidor FastAPI está rodando.');
    }
}

async function logoutGitide() {
    try {
        await fetch('/api/auth/logout', { method: 'POST', headers: getHeaders() });
    } catch (_err) {
        // Redireciona mesmo se o backend já tiver invalidado a sessão.
    }
    window.location.href = '/login';
}

function applySidebarCollapsedState(collapsed) {
    const app = document.querySelector('.app-container');
    const btn = document.getElementById('btn-sidebar-collapse');
    if (!app) return;
    app.classList.toggle('sidebar-collapsed', collapsed);
    if (btn) {
        btn.setAttribute('aria-expanded', String(!collapsed));
        btn.setAttribute('aria-label', collapsed ? 'Expandir sidebar' : 'Colapsar sidebar');
        btn.title = collapsed ? 'Expandir sidebar' : 'Colapsar sidebar';
        btn.innerHTML = collapsed ? '<i data-lucide="panel-left-open"></i>' : '<i data-lucide="panel-left-close"></i>';
        if (window.lucide) lucide.createIcons();
    }
}

function toggleSidebarCollapsed() {
    const app = document.querySelector('.app-container');
    const collapsed = !app?.classList.contains('sidebar-collapsed');
    localStorage.setItem('gitide_sidebar_collapsed', String(collapsed));
    applySidebarCollapsedState(collapsed);
}

// Cabeçalhos para requisições autenticadas
function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.apiKey}`,
        'x-gitide-source': 'dashboard'
    };
}

function notifyActiveProjectChanged() {
    const selector = document.getElementById('project-selector');
    if (selector) {
        selector.value = state.activeProjectId ? String(state.activeProjectId) : '';
    }

    window.dispatchEvent(new CustomEvent('gitide:active-project-changed', {
        detail: {
            projectId: state.activeProjectId,
            project: state.activeProject,
            projects: state.projects
        }
    }));
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

    window.dispatchEvent(new CustomEvent('gitide:projects-loaded', {
        detail: {
            projectId: state.activeProjectId,
            project: state.activeProject,
            projects: state.projects
        }
    }));
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
        notifyActiveProjectChanged();
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
    loadProdReadinessValidator();
    loadSecurityRulesPrompt();
    
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
    notifyActiveProjectChanged();
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
        loadProdReadinessValidator();
        loadSecurityRulesPrompt();
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
        } else if (tabId === 'tab-ui-canvas') {
            loadUiCanvasFiles();
        } else if (tabId === 'tab-qa') {
            loadQaAnnotations();
        } else if (tabId === 'tab-engineering-metrics') {
            loadEngineeringMetrics();
            loadEngineeringReports();
        } else if (tabId === 'tab-estimation') {
            loadEstimationPage();
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
        } else if (tabId === 'tab-sdd') {
            sddLoadCharter();
            sddLoadSpecs(true);
        } else if (tabId === 'tab-ops-infra') {
            opsInfraDetect();
            opsInfraLoadEnv();
            opsInfraLoadVmAccess();
            refreshOpsInfraGptActionPrompt();
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
                        path: parts.slice(0, index + 1).join('/'),
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
            folderHeader.setAttribute('data-filepath', item.path);
            folderHeader.setAttribute('data-type', 'folder');
            folderHeader.innerHTML = `
                <div class="file-node-main">
                    <i class="fa-solid fa-folder-open" style="color: var(--color-warning); margin-right: 6px;"></i>
                    <span>${escapeHtml(item.name)}</span>
                </div>
                <button class="workspace-tree-delete" title="Excluir pasta" aria-label="Excluir pasta ${escapeHtml(item.name)}">
                    <i class="fa-solid fa-trash-can"></i>
                </button>`;
            
            const folderChildrenContainer = document.createElement('div');
            folderChildrenContainer.className = 'folder-children active';
            
            folderHeader.querySelector('.workspace-tree-delete')?.addEventListener('click', (e) => {
                e.stopPropagation();
                openWorkspaceDeleteModal(item.path, item.name, 'folder');
            });

            folderHeader.addEventListener('click', (e) => {
                e.stopPropagation();
                folderChildrenContainer.classList.toggle('active');
                const icon = folderHeader.querySelector('.file-node-main i');
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
            
            fileEl.innerHTML = `
                <div class="file-node-main">
                    <i class="${iconClass}"></i>
                    <span>${escapeHtml(item.name)}</span>
                </div>
                <button class="workspace-tree-delete" title="Excluir arquivo" aria-label="Excluir arquivo ${escapeHtml(item.name)}">
                    <i class="fa-solid fa-trash-can"></i>
                </button>`;
            fileEl.setAttribute('data-filepath', item.path);
            fileEl.setAttribute('data-type', 'file');
            fileEl.querySelector('.workspace-tree-delete')?.addEventListener('click', (e) => {
                e.stopPropagation();
                openWorkspaceDeleteModal(item.path, item.name, 'file');
            });
            fileEl.addEventListener('click', (e) => {
                e.stopPropagation();
                openFile(item.path, item.size, item.last_modified);
            });
            
            itemEl.appendChild(fileEl);
            container.appendChild(itemEl);
        }
    });
}

function openWorkspaceDeleteModal(filepath, name, type = 'file') {
    if (!state.activeProjectId) {
        gitideNotify({ title: 'Projeto obrigatório', message: 'Selecione um projeto antes de excluir itens.', variant: 'warning' });
        return;
    }

    const modal = document.getElementById('modal-workspace-delete');
    const nameEl = document.getElementById('workspace-delete-name');
    const pathEl = document.getElementById('workspace-delete-path');
    const kindEl = document.getElementById('workspace-delete-kind');
    const input = document.getElementById('workspace-delete-confirm-input');
    const btn = document.getElementById('btn-workspace-confirm-delete');
    if (!modal || !nameEl || !pathEl || !kindEl || !input || !btn) return;

    workspaceDeleteState.filepath = filepath;
    workspaceDeleteState.name = name;
    workspaceDeleteState.type = type;
    nameEl.textContent = name;
    pathEl.textContent = filepath;
    kindEl.textContent = type === 'folder' ? 'Pasta' : 'Arquivo';
    input.value = '';
    btn.disabled = true;
    modal.classList.add('active');
    setTimeout(() => input.focus(), 40);
}

function closeWorkspaceDeleteModal() {
    const modal = document.getElementById('modal-workspace-delete');
    if (modal) modal.classList.remove('active');
}

function updateWorkspaceDeleteConfirmState() {
    const input = document.getElementById('workspace-delete-confirm-input');
    const btn = document.getElementById('btn-workspace-confirm-delete');
    if (!input || !btn) return;
    btn.disabled = input.value !== workspaceDeleteState.name;
}

async function deleteWorkspaceItemFromModal() {
    if (!state.activeProjectId || !workspaceDeleteState.filepath) return;
    const btn = document.getElementById('btn-workspace-confirm-delete');
    const input = document.getElementById('workspace-delete-confirm-input');
    if (!btn || !input || input.value !== workspaceDeleteState.name) return;

    const originalHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i>';

    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/files/delete?filepath=${encodeURIComponent(workspaceDeleteState.filepath)}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            throw new Error(data.detail || 'Não foi possível excluir o item.');
        }

        const deletedPath = workspaceDeleteState.filepath;
        const deletedType = workspaceDeleteState.type;
        closeWorkspaceDeleteModal();
        gitideNotify({
            title: deletedType === 'folder' ? 'Pasta excluída' : 'Arquivo excluído',
            message: deletedPath,
            variant: 'success'
        });

        if (state.activeFilepath === deletedPath || state.activeFilepath?.startsWith(`${deletedPath}/`)) {
            state.activeFilepath = null;
            document.getElementById('active-file-name').innerHTML = '<i class="fa-solid fa-code"></i> Selecione um arquivo para visualizar';
            const textarea = document.getElementById('file-editor-textarea');
            textarea.value = '';
            textarea.disabled = true;
            document.getElementById('btn-save-file').disabled = true;
            document.getElementById('editor-meta').style.display = 'none';
            document.getElementById('file-snapshots-drawer').style.display = 'none';
            updateLineNumbers();
        }

        await loadFiles();
    } catch (err) {
        gitideNotify({ title: 'Erro ao excluir', message: err.message, variant: 'danger' });
    } finally {
        btn.innerHTML = originalHtml;
        updateWorkspaceDeleteConfirmState();
    }
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

async function exportWorkspaceZip() {
    if (!state.activeProjectId) {
        gitideNotify({ title: 'Projeto obrigatório', message: 'Selecione um projeto antes de exportar.', variant: 'warning' });
        return;
    }

    const btn = document.getElementById('btn-export-workspace-zip');
    const originalHtml = btn?.innerHTML;
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i>';
    }

    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/files/export.zip`);
        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            throw new Error(data.detail || 'Não foi possível exportar o projeto.');
        }

        const blob = await res.blob();
        const disposition = res.headers.get('content-disposition') || '';
        const filenameMatch = disposition.match(/filename="?([^"]+)"?/i);
        const filename = filenameMatch?.[1] || 'workspace.zip';
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        gitideNotify({ title: 'Exportação iniciada', message: filename, variant: 'success' });
    } catch (err) {
        gitideNotify({ title: 'Erro ao exportar projeto', message: err.message, variant: 'danger' });
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
            if (window.lucide) lucide.createIcons();
        }
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
    
    // Troca o modo de syntax highlighting dependendo da extensão
    if (window.cmEditor) {
        const ext = filepath.split('.').pop().toLowerCase();
        const modeMap = {
            'md': 'markdown',
            'js': 'javascript',
            'json': 'javascript',
            'py': 'python',
            'html': 'xml',
            'sql': 'sql',
            'xml': 'xml',
            'css': 'css'
        };
        window.cmEditor.setOption('mode', modeMap[ext] || 'markdown');
        // Corrige bug visual do codemirror ao carregar em div oculta
        setTimeout(() => window.cmEditor.refresh(), 50);
    }
    
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

function openWorkspaceNewFileModal() {
    if (!state.activeProjectId) {
        gitideNotify({ title: 'Projeto obrigatório', message: 'Selecione um projeto antes de criar arquivos.', variant: 'warning' });
        return;
    }

    const modal = document.getElementById('modal-workspace-new-file');
    const pathInput = document.getElementById('workspace-new-file-path');
    const contentInput = document.getElementById('workspace-new-file-content');
    if (!modal || !pathInput || !contentInput) return;

    pathInput.value = '';
    contentInput.value = '';
    modal.classList.add('active');
    setTimeout(() => pathInput.focus(), 40);
}

function closeWorkspaceNewFileModal() {
    const modal = document.getElementById('modal-workspace-new-file');
    if (modal) modal.classList.remove('active');
}

function normalizeWorkspaceFilePath(rawPath) {
    return String(rawPath || '').trim().replace(/\\+/g, '/').replace(/^\.\//, '');
}

function validateWorkspaceNewFilePath(filepath) {
    if (!filepath) return 'Informe o caminho relativo do arquivo.';
    if (filepath.endsWith('/')) return 'Informe também o nome do arquivo, não apenas a pasta.';
    if (filepath.startsWith('/')) return 'Use caminho relativo, sem barra inicial.';
    if (/^[a-zA-Z]:\//.test(filepath)) return 'Caminhos absolutos não são permitidos.';
    if (filepath.split('/').some(part => part === '..')) return 'O caminho não pode conter "..".';
    if (filepath.split('/').some(part => part.trim() === '')) return 'O caminho contém segmentos vazios ou barras duplicadas.';
    return '';
}

async function workspaceFileExists(filepath) {
    const res = await fetch(`/api/projects/${state.activeProjectId}/files/read?filepath=${encodeURIComponent(filepath)}`, {
        headers: getHeaders()
    });
    if (res.ok) return true;
    if (res.status === 404) return false;
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Não foi possível validar se o arquivo já existe.');
}

async function createWorkspaceFileFromModal() {
    if (!state.activeProjectId) return;

    const pathInput = document.getElementById('workspace-new-file-path');
    const contentInput = document.getElementById('workspace-new-file-content');
    const btn = document.getElementById('btn-workspace-create-file');
    if (!pathInput || !contentInput || !btn) return;

    const filepath = normalizeWorkspaceFilePath(pathInput.value);
    const validationError = validateWorkspaceNewFilePath(filepath);
    if (validationError) {
        gitideNotify({ title: 'Caminho inválido', message: validationError, variant: 'warning' });
        pathInput.focus();
        return;
    }

    const originalHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Criando...';

    try {
        const exists = await workspaceFileExists(filepath);
        if (exists) {
            gitideNotify({ title: 'Arquivo já existe', message: 'Escolha outro caminho para evitar sobrescrita.', variant: 'warning' });
            pathInput.focus();
            return;
        }

        const res = await fetch(`/api/projects/${state.activeProjectId}/files/write`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                filepath,
                content: contentInput.value || ''
            })
        });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') {
            throw new Error(data.detail || 'Não foi possível criar o arquivo.');
        }

        closeWorkspaceNewFileModal();
        gitideNotify({ title: 'Arquivo criado', message: filepath, variant: 'success' });
        await loadFiles();
        openFile(filepath, new Blob([contentInput.value || '']).size, new Date().toISOString());
    } catch (err) {
        gitideNotify({ title: 'Erro ao criar arquivo', message: err.message, variant: 'danger' });
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalHtml;
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

function clearGitStatusFileList() {
    document.querySelectorAll('#git-status-detail .git-files-list').forEach(list => list.remove());
}

function renderGitChangedFiles(status) {
    clearGitStatusFileList();
    const container = document.getElementById('git-changed-files-list');
    if (!container) return;

    container.innerHTML = '';

    const groups = [
        { key: 'staged', label: 'Staged', tag: 'staged', files: status?.staged || [] },
        { key: 'modified', label: 'Modificados', tag: 'modified', files: status?.modified || [] },
        { key: 'untracked', label: 'Untracked', tag: 'untracked', files: status?.untracked || [] },
        { key: 'deleted', label: 'Removidos', tag: 'deleted', files: status?.deleted || [] }
    ].filter(group => group.files.length > 0);

    if (!groups.length) {
        const emptyState = document.createElement('div');
        emptyState.className = 'git-side-empty-state';
        emptyState.innerHTML = '<i class="fa-solid fa-circle-check"></i><span>Nenhum arquivo alterado no momento.</span>';
        container.appendChild(emptyState);
        return;
    }

    groups.forEach(group => {
        const section = document.createElement('section');
        section.className = 'git-changed-files-group';

        const header = document.createElement('div');
        header.className = 'git-changed-files-group-header';

        const title = document.createElement('span');
        title.textContent = group.label;

        const count = document.createElement('strong');
        count.textContent = String(group.files.length);

        header.appendChild(title);
        header.appendChild(count);
        section.appendChild(header);

        group.files.forEach(file => {
            const item = document.createElement('div');
            item.className = 'git-file-item git-changed-file-item';

            const name = document.createElement('span');
            name.className = 'git-changed-file-name';
            name.textContent = file;
            name.title = file;

            const badge = document.createElement('span');
            badge.className = `git-tag ${group.tag}`;
            badge.textContent = group.tag;

            item.appendChild(name);
            item.appendChild(badge);
            section.appendChild(item);
        });

        container.appendChild(section);
    });
}

// --- GIT BRIDGE ---
async function loadGitStatus(forceFetch = false) {
    const container = document.getElementById('git-status-detail');
    const initPanel = document.getElementById('git-init-panel');
    const deployPanel = document.getElementById('git-deploy-panel');
    const refreshButton = document.getElementById('btn-git-status-refresh');
    const shouldFetch = forceFetch === true;
    refreshButton?.classList.add('is-refreshing');
    refreshButton?.setAttribute('aria-busy', 'true');
    
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
            renderGitChangedFiles({ staged: [], modified: [], untracked: [], deleted: [] });
            return;
        }
        
        setGitCurrentBranchLabel(status.current_branch);
        state.activeProjectRemoteUrl = status.remote_url || '';
        if (state.activeProject && status.remote_url) {
            state.activeProject.git_remote = status.remote_url;
        }
        const remoteInput = document.getElementById('git-remote-url-input');
        if (remoteInput && status.remote_url) {
            remoteInput.value = status.remote_url;
        }
        initPanel.style.display = status.remote_url ? 'none' : 'block';
        deployPanel.style.display = 'block';
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
                        </div>

                    </span>
                </p>
                <p><strong>Status do Repositório:</strong> ${status.is_clean ? '<span style="color: var(--color-success)">Limpo (Sem alterações pendentes)</span>' : '<span style="color: var(--color-warning)">Alterações não commitadas</span>'}</p>
            </div>
        `;
        
        container.innerHTML = html;
        clearGitStatusFileList();
        renderGitChangedFiles(status);
        if (status.has_conflicts || (status.conflicted && status.conflicted.length)) {
            loadGitConflicts();
        } else {
            state.gitConflicts = [];
            state.gitConflictActiveFile = null;
            hideGitConflictsPanelIfEmpty();
        }
        
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
            
        }
        
        // Carrega o gráfico apenas quando a aba Git Graph estiver ativa no painel lateral.
        const isGraphPanelActive = document.querySelector('.git-side-tab[data-git-side-tab="graph"]')?.classList.contains('active');
        if (isGraphPanelActive) {
            await loadGitGraph();
        }
        
    } catch (err) {
        container.innerHTML = `<p class="placeholder-text error-text">Erro ao buscar status do Git: ${err.message}</p>`;
        const graphContainer = document.getElementById('git-graph-container');
        if (graphContainer) {
            graphContainer.innerHTML = `<div class="git-side-empty-state">Não foi possível carregar o histórico Git.</div>`;
        }
    } finally {
        refreshButton?.classList.remove('is-refreshing');
        refreshButton?.setAttribute('aria-busy', 'false');
    }
}

async function loadGitGraph() {
    if (!state.activeProjectId) return;
    const panel = document.getElementById('git-graph-panel');
    const container = document.getElementById('git-graph-container');
    const refreshButton = document.getElementById('btn-git-graph-refresh');
    if (!panel || !container) return;
    refreshButton?.classList.add('is-refreshing');
    refreshButton?.setAttribute('aria-busy', 'true');
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/git/graph`, {
            headers: getHeaders()
        });
        const data = await res.json();
        
        if (!data.is_git || data.is_empty) {
            container.innerHTML = '<div class="git-side-empty-state">Sem histórico de commits disponível para este repositório.</div>';
            return;
        }
        
        panel.style.removeProperty('display');
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
    } finally {
        refreshButton?.classList.remove('is-refreshing');
        refreshButton?.setAttribute('aria-busy', 'false');
    }
}

function switchGitSidePanelTab(tabName) {
    const tabs = document.querySelectorAll('.git-side-tab');
    const panes = document.querySelectorAll('.git-side-panel-pane');
    if (!tabs.length || !panes.length) return;

    tabs.forEach(tab => {
        const isActive = tab.dataset.gitSideTab === tabName;
        tab.classList.toggle('active', isActive);
        tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    panes.forEach(pane => {
        const isActive = pane.dataset.gitSidePane === tabName;
        pane.classList.toggle('active', isActive);
        pane.hidden = !isActive;
        pane.style.setProperty('display', isActive ? 'flex' : 'none', 'important');
    });

    if (tabName === 'graph') {
        loadGitGraph();
    }

    if (tabName === 'files') {
        const filesContainer = document.getElementById('git-changed-files-list');
        const needsRefresh = !filesContainer || filesContainer.textContent.includes('Nenhuma alteração carregada ainda');
        if (needsRefresh) {
            loadGitStatus();
        }
    }

    if (tabName === 'ignore') {
        loadGitignore();
    }
}

async function loadGitignore() {
    if (!state.activeProjectId) return;
    const list = document.getElementById('gitignore-list');
    const status = document.getElementById('gitignore-status');
    if (!list) return;
    list.innerHTML = '<div class="git-side-empty-state">Carregando .gitignore...</div>';
    if (status) status.textContent = 'Lendo arquivo .gitignore...';
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/git/gitignore`, {
            headers: getHeaders()
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao carregar .gitignore');
        renderGitignoreEntries(data.entries || []);
        if (status) {
            status.textContent = data.exists
                ? `${(data.entries || []).length} regra(s) no .gitignore`
                : '.gitignore ainda não existe. Adicione uma regra para criar.';
        }
    } catch (err) {
        list.innerHTML = `<div class="git-side-empty-state danger">${escapeHtml(err.message || String(err))}</div>`;
        if (status) status.textContent = 'Erro ao carregar .gitignore.';
    }
}

function getGitignoreEntriesFromDom() {
    return Array.from(document.querySelectorAll('[data-gitignore-entry]'))
        .map(item => item.dataset.gitignoreEntry)
        .filter(Boolean);
}

function renderGitignoreEntries(entries) {
    const list = document.getElementById('gitignore-list');
    if (!list) return;
    const cleanEntries = Array.from(new Set((entries || []).map(item => String(item || '').trim()).filter(Boolean)));
    if (!cleanEntries.length) {
        list.innerHTML = '<div class="git-side-empty-state">Nenhuma regra cadastrada. Adicione arquivos ou pastas para ignorar.</div>';
        return;
    }
    list.innerHTML = cleanEntries.map(entry => `
        <div class="gitignore-entry" data-gitignore-entry="${escapeHtml(entry)}">
            <span><i data-lucide="eye-off"></i>${escapeHtml(entry)}</span>
            <button type="button" class="gitignore-remove" title="Remover regra" aria-label="Remover ${escapeHtml(entry)}"><i data-lucide="x"></i></button>
        </div>
    `).join('');
    list.querySelectorAll('.gitignore-remove').forEach(button => {
        button.addEventListener('click', () => {
            button.closest('.gitignore-entry')?.remove();
            saveGitignoreEntries();
        });
    });
    if (window.lucide) lucide.createIcons();
}

function normalizeGitignoreInput(value) {
    return String(value || '').trim().replace(/\\/g, '/').replace(/^\/+/, '');
}

async function addGitignoreEntry(entry) {
    const clean = normalizeGitignoreInput(entry);
    if (!clean) return;
    if (clean.includes('\n') || clean.includes('\r')) {
        gitideNotify({ title: 'Regra inválida', message: 'Adicione uma regra por vez.', variant: 'warning' });
        return;
    }
    const currentEntries = getGitignoreEntriesFromDom();
    if (currentEntries.includes(clean)) {
        gitideNotify({ title: 'Regra já existe', message: clean, variant: 'info' });
        return;
    }
    renderGitignoreEntries([...currentEntries, clean]);
    document.getElementById('gitignore-entry-input').value = '';
    await saveGitignoreEntries();
}

async function saveGitignoreEntries() {
    if (!state.activeProjectId) return;
    const entries = getGitignoreEntriesFromDom();
    const status = document.getElementById('gitignore-status');
    if (status) status.textContent = 'Salvando .gitignore...';
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/git/gitignore`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify({ entries })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao salvar .gitignore');
        renderGitignoreEntries(data.entries || []);
        if (status) status.textContent = `${(data.entries || []).length} regra(s) salva(s) em .gitignore`;
        appendGitConsole(`.gitignore atualizado com ${(data.entries || []).length} regra(s).`);
        loadGitStatus();
    } catch (err) {
        if (status) status.textContent = 'Erro ao salvar .gitignore.';
        gitideNotify({ title: 'Erro no .gitignore', message: err.message || String(err), variant: 'danger' });
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

function setGitCurrentBranchLabel(branch) {
    const label = document.getElementById('git-current-branch-readonly');
    if (!label) return;
    label.textContent = branch ? normalizeGitBranchName(branch) : '-';
}

function getGitDeployBranchValue() {
    const label = document.getElementById('git-current-branch-readonly');
    const branch = label?.textContent?.trim();
    return branch && branch !== '-' ? normalizeGitBranchName(branch) : '';
}

async function initGitRepo() {
    const remoteUrl = document.getElementById('git-remote-url-input').value.trim();
    appendGitConsole(remoteUrl ? `Configurando publicação Git em ${remoteUrl}...` : 'Inicializando repositório Git local...');
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/git/init`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ remote_url: remoteUrl || null })
        });
        
        const data = await res.json();
        
        if (res.status === 200) {
            appendGitConsole(`Repositório Git pronto. Remotos configurados: ${(data.remotes || []).join(', ') || 'nenhum'}`);
            if (remoteUrl) {
                state.activeProject.git_remote = remoteUrl;
                state.activeProjectRemoteUrl = remoteUrl;
                appendGitConsole('Origin configurado e salvo no projeto. Agora use "Commitar e Fazer Deploy (Push)" para enviar os arquivos.');
                gitideNotify({ title: 'Projeto pronto para Git', message: 'Remote origin configurado. Faça commit/push para publicar.', variant: 'success' });
            } else {
                gitideNotify({ title: 'Git inicializado', message: 'Informe uma URL remota para publicar o projeto.', variant: 'warning' });
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
    if (!branch) {
        appendGitConsole('Não foi possível identificar a branch atual para deploy.', true);
        gitideNotify({ title: 'Branch atual indisponível', message: 'Atualize o status do Git antes de executar o deploy.', variant: 'warning' });
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

async function generateGitCommitMessage() {
    if (!state.activeProjectId) return;

    const input = document.getElementById('git-commit-msg');
    const btn = document.getElementById('btn-git-commit-ai');
    const icon = btn?.querySelector('i');
    if (!input || !btn) return;

    btn.disabled = true;
    btn.classList.add('is-loading');
    if (icon) icon.className = 'fa-solid fa-circle-notch fa-spin';

    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/git/commit-message/suggest`, {
            method: 'POST',
            headers: getHeaders()
        });
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || 'Não foi possível gerar a mensagem.');
        }

        input.value = data.message || '';
        input.focus();
        input.setSelectionRange(input.value.length, input.value.length);

        if (data.status === 'fallback') {
            gitideNotify({
                title: 'Sugestão local aplicada',
                message: 'Configure a IA para gerar mensagens mais precisas pelo diff.',
                variant: 'warning'
            });
        } else {
            gitideNotify({ title: 'Commit sugerido', message: input.value, variant: 'success' });
        }
    } catch (err) {
        gitideNotify({ title: 'Erro ao gerar commit', message: err.message, variant: 'error' });
        appendGitConsole(`Erro ao gerar mensagem de commit: ${err.message}`, true);
    } finally {
        btn.disabled = false;
        btn.classList.remove('is-loading');
        if (icon) icon.className = 'fa-solid fa-wand-magic-sparkles';
    }
}

async function runGitPull() {
    const branch = getGitDeployBranchValue();
    if (!branch) {
        appendGitConsole('Não foi possível identificar a branch atual para sincronizar.', true);
        gitideNotify({ title: 'Branch atual indisponível', message: 'Atualize o status do Git antes de sincronizar.', variant: 'warning' });
        return;
    }
    appendGitConsole(`Puxando alterações (Git Pull) para branch "${branch}"...`);
    
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
            const detail = normalizeGitErrorDetail(data.detail);
            appendGitConsole(`Erro no Git Pull: ${detail.message || data.detail}`, true);
            await maybeLoadGitConflicts(detail);
        }
        
    } catch (err) {
        appendGitConsole(`Erro de conexão no Git Pull: ${err.message}`, true);
        await loadGitConflicts();
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

function normalizeGitErrorDetail(detail) {
    if (!detail) return { message: 'Erro desconhecido' };
    if (typeof detail === 'string') return { message: detail };
    return detail;
}

async function maybeLoadGitConflicts(detail = null) {
    const normalized = normalizeGitErrorDetail(detail);
    if (normalized.has_conflicts && Array.isArray(normalized.conflicts)) {
        state.gitConflicts = normalized.conflicts;
        renderGitConflictFiles();
        showGitConflictsPanel();
        if (state.gitConflicts[0]) await loadGitConflictFile(state.gitConflicts[0].filepath);
        return true;
    }
    return loadGitConflicts();
}

function showGitConflictsPanel() {
    const card = document.getElementById('git-conflicts-card');
    if (card) card.style.display = 'flex';
}

function hideGitConflictsPanelIfEmpty() {
    const card = document.getElementById('git-conflicts-card');
    if (card && (!state.gitConflicts || state.gitConflicts.length === 0)) {
        card.style.display = 'none';
    }
}

async function loadGitConflicts() {
    if (!state.activeProjectId) return false;
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/git/conflicts`, { headers: getHeaders() });
        const data = await res.json();
        state.gitConflicts = data.files || [];
        renderGitConflictFiles();
        if (state.gitConflicts.length) {
            showGitConflictsPanel();
            if (!state.gitConflictActiveFile) await loadGitConflictFile(state.gitConflicts[0].filepath);
            return true;
        }
        state.gitConflictActiveFile = null;
        state.gitConflictBlocks = [];
        renderGitConflictBlocks([]);
        hideGitConflictsPanelIfEmpty();
        return false;
    } catch (err) {
        appendGitConsole(`Erro ao carregar conflitos: ${err.message}`, true);
        return false;
    }
}

function renderGitConflictFiles() {
    const list = document.getElementById('git-conflict-files-list');
    if (!list) return;
    if (!state.gitConflicts.length) {
        list.innerHTML = '<div class="git-side-empty-state">Nenhum conflito encontrado.</div>';
        return;
    }
    list.innerHTML = state.gitConflicts.map(file => `
        <button type="button" class="git-conflict-file ${state.gitConflictActiveFile === file.filepath ? 'active' : ''}" data-filepath="${escapeGitConflictHtml(file.filepath)}">
            <i data-lucide="file-warning"></i>
            <span>${escapeGitConflictHtml(file.filepath)}</span>
            <strong>${file.blocks_count}</strong>
        </button>
    `).join('');
    list.querySelectorAll('.git-conflict-file').forEach(btn => {
        btn.addEventListener('click', () => loadGitConflictFile(btn.dataset.filepath));
    });
    if (window.lucide) lucide.createIcons();
}

async function loadGitConflictFile(filepath) {
    if (!state.activeProjectId || !filepath) return;
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/git/conflicts/file?filepath=${encodeURIComponent(filepath)}`, { headers: getHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao carregar arquivo em conflito');
        state.gitConflictActiveFile = filepath;
        state.gitConflictBlocks = data.blocks || [];
        document.getElementById('git-conflict-active-file').textContent = filepath;
        document.getElementById('btn-git-conflict-save-file').disabled = !state.gitConflictBlocks.length;
        renderGitConflictFiles();
        renderGitConflictBlocks(state.gitConflictBlocks);
    } catch (err) {
        appendGitConsole(`Erro ao abrir conflito: ${err.message}`, true);
    }
}

function escapeGitConflictHtml(value) {
    return String(value || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function renderGitConflictBlocks(blocks) {
    const container = document.getElementById('git-conflict-blocks');
    if (!container) return;
    if (!blocks.length) {
        container.innerHTML = '<div class="git-side-empty-state">Nenhum bloco conflitante neste arquivo.</div>';
        return;
    }
    container.innerHTML = blocks.map(block => `
        <article class="git-conflict-block" data-index="${block.index}">
            <header>
                <div>
                    <span>Bloco ${block.index + 1}</span>
                    <strong>Linhas ${block.start_line}-${block.end_line}</strong>
                </div>
                <div class="git-conflict-choice">
                    <button type="button" class="btn btn-sm btn-secondary" data-choice="ours">Manter Meu</button>
                    <button type="button" class="btn btn-sm btn-secondary" data-choice="theirs">Manter Remoto</button>
                    <button type="button" class="btn btn-sm btn-primary" data-choice="manual">Manual</button>
                </div>
            </header>
            <div class="git-conflict-three-way">
                <section>
                    <h5>Meu (${escapeGitConflictHtml(block.ours_label)})</h5>
                    <pre>${escapeGitConflictHtml(block.ours)}</pre>
                </section>
                <section>
                    <h5>Remoto (${escapeGitConflictHtml(block.theirs_label)})</h5>
                    <pre>${escapeGitConflictHtml(block.theirs)}</pre>
                </section>
            </div>
            <label class="git-conflict-manual-label">Merge manual</label>
            <textarea class="git-conflict-manual text-input">${escapeGitConflictHtml(block.ours || block.theirs)}</textarea>
        </article>
    `).join('');
    container.querySelectorAll('.git-conflict-block').forEach(blockEl => {
        blockEl.dataset.resolution = 'manual';
        blockEl.querySelectorAll('[data-choice]').forEach(btn => {
            btn.addEventListener('click', () => {
                blockEl.dataset.resolution = btn.dataset.choice;
                blockEl.querySelectorAll('[data-choice]').forEach(b => b.classList.toggle('active', b === btn));
                const idx = Number(blockEl.dataset.index);
                const block = state.gitConflictBlocks.find(item => item.index === idx);
                const manual = blockEl.querySelector('.git-conflict-manual');
                if (btn.dataset.choice === 'ours') manual.value = block?.ours || '';
                if (btn.dataset.choice === 'theirs') manual.value = block?.theirs || '';
            });
        });
    });
}

async function applyGitConflictResolutions() {
    if (!state.activeProjectId || !state.gitConflictActiveFile) return;
    const blockEls = Array.from(document.querySelectorAll('.git-conflict-block'));
    const resolutions = blockEls.map(el => ({
        index: Number(el.dataset.index),
        resolution: el.dataset.resolution || 'manual',
        content: el.querySelector('.git-conflict-manual')?.value || ''
    }));
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/git/conflicts/resolve`, {
            method: 'POST',
            headers: { ...getHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filepath: state.gitConflictActiveFile,
                resolutions,
                stage_file: true
            })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao aplicar resoluções');
        appendGitConsole(`Conflitos resolvidos em ${state.gitConflictActiveFile}. Restantes: ${data.remaining_blocks}`);
        gitideNotify({ title: 'Conflito resolvido', message: state.gitConflictActiveFile, variant: 'success' });
        state.gitConflictActiveFile = null;
        await loadGitConflicts();
        loadGitStatus();
    } catch (err) {
        appendGitConsole(`Erro ao resolver conflito: ${err.message}`, true);
        gitideNotify({ title: 'Erro ao resolver conflito', message: err.message, variant: 'danger' });
    }
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

function gitideNotify({ title = 'Act IA', message = '', variant = 'info', duration = 3500 } = {}) {
    const viewport = document.getElementById('gitide-toast-viewport');
    if (!viewport) return;
    const icons = {
        info: 'info',
        success: 'check-circle-2',
        warning: 'triangle-alert',
        danger: 'circle-alert'
    };
    const toast = document.createElement('div');
    toast.className = `gitide-toast gitide-toast-${variant}`;
    toast.innerHTML = `
        <div class="gitide-toast-icon"><i data-lucide="${icons[variant] || icons.info}"></i></div>
        <div class="gitide-toast-copy">
            <strong>${title}</strong>
            <span>${message}</span>
        </div>
        <button type="button" class="gitide-toast-close" aria-label="Fechar"><i data-lucide="x"></i></button>
    `;
    viewport.appendChild(toast);
    if (window.lucide) lucide.createIcons();
    const remove = () => {
        toast.classList.add('is-leaving');
        setTimeout(() => toast.remove(), 180);
    };
    toast.querySelector('.gitide-toast-close')?.addEventListener('click', remove);
    if (duration) setTimeout(remove, duration);
}

async function loadQaAnnotations() {
    if (!state.activeProjectId) return;
    const list = document.getElementById('qa-annotations-list');
    const filter = document.getElementById('qa-status-filter')?.value || '';
    if (list) {
        list.innerHTML = '<div class="qa-empty-state"><i data-lucide="loader-circle"></i><h5>Carregando anotações...</h5></div>';
        if (window.lucide) lucide.createIcons();
    }
    try {
        const query = filter ? `?status=${encodeURIComponent(filter)}` : '';
        const res = await fetch(`/api/projects/${state.activeProjectId}/qa/annotations${query}`, { headers: getHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao carregar anotações QA');
        state.qaAnnotations = data.annotations || [];
        renderQaAnnotations();
        updateQaExtensionInfo();
    } catch (err) {
        if (list) {
            list.innerHTML = `<div class="qa-empty-state"><i data-lucide="circle-alert"></i><h5>Erro ao carregar QA</h5><p>${escapeHtml(String(err.message || err))}</p></div>`;
            if (window.lucide) lucide.createIcons();
        }
    }
}

function updateQaExtensionInfo() {
    const apiBase = `${window.location.protocol}//${window.location.host}`;
    const apiEl = document.getElementById('qa-extension-api-base');
    const projectEl = document.getElementById('qa-extension-project-id');
    const tokenEl = document.getElementById('qa-extension-token');
    if (apiEl) apiEl.textContent = apiBase;
    if (projectEl) projectEl.textContent = state.activeProjectId || '-';
    if (tokenEl) tokenEl.textContent = state.apiKey ? `${state.apiKey.slice(0, 8)}...` : '-';
}

function renderQaAnnotations() {
    const list = document.getElementById('qa-annotations-list');
    const board = document.getElementById('qa-kanban-board');
    if (!list || !board) return;
    const items = state.qaAnnotations || [];
    const idFilter = (document.getElementById('qa-id-filter')?.value || '').trim().toLowerCase();
    const visibleItems = idFilter
        ? items.filter(item => String(item.id || '').toLowerCase().includes(idFilter))
        : items;
    const counts = { open: 0, reviewing: 0, resolved: 0 };
    items.forEach(item => {
        if (counts[item.status] !== undefined) counts[item.status] += 1;
    });
    const openEl = document.getElementById('qa-count-open');
    const reviewingEl = document.getElementById('qa-count-reviewing');
    const resolvedEl = document.getElementById('qa-count-resolved');
    if (openEl) openEl.textContent = counts.open;
    if (reviewingEl) reviewingEl.textContent = counts.reviewing;
    if (resolvedEl) resolvedEl.textContent = counts.resolved;
    const kanbanOpen = document.getElementById('qa-kanban-count-open');
    const kanbanReviewing = document.getElementById('qa-kanban-count-reviewing');
    const kanbanResolved = document.getElementById('qa-kanban-count-resolved');
    if (kanbanOpen) kanbanOpen.textContent = counts.open;
    if (kanbanReviewing) kanbanReviewing.textContent = counts.reviewing;
    if (kanbanResolved) kanbanResolved.textContent = counts.resolved;

    list.style.display = state.qaView === 'kanban' ? 'none' : 'flex';
    board.style.display = state.qaView === 'kanban' ? 'grid' : 'none';

    if (!items.length) {
        list.innerHTML = `
            <div class="qa-empty-state">
                <i data-lucide="message-square-warning"></i>
                <h5>Nenhuma anotação QA recebida</h5>
                <p>Instale a extensão, selecione um elemento na aplicação e envie a anotação para este projeto.</p>
            </div>
        `;
        board.querySelectorAll('.qa-kanban-items').forEach(column => {
            column.innerHTML = '<div class="qa-kanban-empty">Sem anotações</div>';
        });
        if (window.lucide) lucide.createIcons();
        return;
    }

    if (!visibleItems.length) {
        list.innerHTML = `
            <div class="qa-empty-state">
                <i data-lucide="search-x"></i>
                <h5>Nenhuma anotação encontrada</h5>
                <p>Nenhum ID QA corresponde ao filtro informado.</p>
            </div>
        `;
    } else {
        list.innerHTML = renderQaGroupedList(visibleItems);
    }

    renderQaKanban(visibleItems);
    bindQaAnnotationActions();
    if (window.lucide) lucide.createIcons();
}

function renderQaGroupedList(items) {
    const groups = [
        { status: 'open', label: 'Abertas', icon: 'circle-dot', items: items.filter(item => item.status === 'open') },
        { status: 'reviewing', label: 'Em revisão', icon: 'loader-circle', items: items.filter(item => item.status === 'reviewing') },
        { status: 'resolved', label: 'Resolvidas', icon: 'circle-check', items: items.filter(item => item.status === 'resolved') }
    ];
    return groups
        .filter(group => group.items.length)
        .map(group => `
            <section class="qa-status-group" data-qa-status-group="${group.status}">
                <div class="qa-status-group-title">
                    <span><i data-lucide="${group.icon}"></i>${group.label}</span>
                    <strong>${group.items.length}</strong>
                </div>
                <div class="qa-status-group-items">
                    ${group.items.map(renderQaListCard).join('')}
                </div>
            </section>
        `).join('');
}

function renderQaListCard(item) {
    const id = String(item.id || '');
    const idSafe = escapeHtml(id);
    return `
        <article class="qa-card" data-qa-id="${idSafe}" role="button" tabindex="0">
            <div class="qa-card-main">
                ${qaAnnotationCardContent(item)}
            </div>
            ${item.screenshot ? `<img class="qa-card-shot" src="${item.screenshot}" alt="Captura da anotação ${idSafe}">` : ''}
            <div class="qa-card-actions">
                <button class="btn-icon qa-detail-button" data-qa-open="${idSafe}" type="button" title="Ver detalhes"><i data-lucide="panel-right-open"></i></button>
                <button class="btn-icon qa-delete-button" data-qa-delete="${idSafe}" type="button" title="Deletar anotação"><i data-lucide="trash-2"></i></button>
                <select class="select-input qa-status-select" data-qa-status="${idSafe}">
                    <option value="open" ${item.status === 'open' ? 'selected' : ''}>Aberta</option>
                    <option value="reviewing" ${item.status === 'reviewing' ? 'selected' : ''}>Em revisão</option>
                    <option value="resolved" ${item.status === 'resolved' ? 'selected' : ''}>Resolvida</option>
                </select>
            </div>
        </article>
    `;
}

function qaAnnotationCardContent(item) {
    const id = escapeHtml(String(item.id || ''));
    const created = item.created_at ? new Date(item.created_at).toLocaleString('pt-BR') : '-';
    const category = escapeHtml(String(item.category || 'functional'));
    const severity = escapeHtml(String(item.severity || 'medium'));
    const status = escapeHtml(String(item.status || 'open'));
    return `
        <div class="qa-card-topline">
            <span class="qa-id">${id}</span>
            <span class="qa-pill qa-category-${category}">${qaCategoryLabel(item.category)}</span>
            <span class="qa-pill qa-severity-${severity}">${severity}</span>
            <span class="qa-pill qa-status-${status}">${qaStatusLabel(item.status)}</span>
        </div>
        <h5>${escapeHtml(String(item.title || 'Anotação QA'))}</h5>
        <p>${escapeHtml(String(item.description || 'Sem descrição.'))}</p>
        <div class="qa-card-meta">
            <span><i data-lucide="link"></i>${escapeHtml(String(item.url || '-'))}</span>
            <span><i data-lucide="mouse-pointer-click"></i>${escapeHtml(String(item.selector || 'sem seletor'))}</span>
            <span><i data-lucide="clock"></i>${created}</span>
        </div>
    `;
}

function renderQaKanban(items) {
    ['open', 'reviewing', 'resolved'].forEach(status => {
        const column = document.getElementById(`qa-kanban-${status}`);
        if (!column) return;
        const columnItems = items.filter(item => item.status === status);
        column.innerHTML = columnItems.length
            ? columnItems.map(item => {
                const id = escapeHtml(String(item.id || ''));
                return `
                    <article class="qa-kanban-card" data-qa-id="${id}" role="button" tabindex="0">
                        ${qaAnnotationCardContent(item)}
                        <div class="qa-kanban-actions">
                            <button class="btn-icon qa-detail-button" data-qa-open="${id}" type="button" title="Ver detalhes"><i data-lucide="panel-right-open"></i></button>
                            <button class="btn-icon qa-delete-button" data-qa-delete="${id}" type="button" title="Deletar anotação"><i data-lucide="trash-2"></i></button>
                        </div>
                    </article>
                `;
            }).join('')
            : '<div class="qa-kanban-empty">Sem anotações</div>';
    });
}

function bindQaAnnotationActions() {
    document.querySelectorAll('.qa-status-select').forEach(select => {
        select.addEventListener('click', event => event.stopPropagation());
        select.addEventListener('change', () => updateQaAnnotationStatus(select.dataset.qaStatus, select.value));
    });
    document.querySelectorAll('[data-qa-open]').forEach(btn => {
        btn.addEventListener('click', event => {
            event.stopPropagation();
            openQaAnnotationDrawer(btn.dataset.qaOpen);
        });
    });
    document.querySelectorAll('[data-qa-delete]').forEach(btn => {
        btn.addEventListener('click', event => {
            event.stopPropagation();
            deleteQaAnnotation(btn.dataset.qaDelete);
        });
    });
    document.querySelectorAll('.qa-card, .qa-kanban-card').forEach(card => {
        card.addEventListener('click', () => openQaAnnotationDrawer(card.dataset.qaId));
        card.addEventListener('keydown', event => {
            if (event.key === 'Enter') openQaAnnotationDrawer(card.dataset.qaId);
        });
    });
}

function qaStatusLabel(status) {
    return {
        open: 'Aberta',
        reviewing: 'Em revisão',
        resolved: 'Resolvida'
    }[status] || 'Aberta';
}

function qaCategoryLabel(category) {
    return {
        functional: 'Funcionais',
        interface: 'Interface',
        content: 'Conteúdo',
        interaction: 'Interação',
        design: 'Design',
        structure: 'Estrutura',
        visual: 'Visual'
    }[category] || 'Funcionais';
}

async function updateQaAnnotationStatus(annotationId, statusValue) {
    if (!state.activeProjectId || !annotationId) return;
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/qa/annotations/${encodeURIComponent(annotationId)}`, {
            method: 'PATCH',
            headers: getHeaders(),
            body: JSON.stringify({ status: statusValue })
        });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') throw new Error(data.detail || 'Erro ao atualizar anotação');
        const index = state.qaAnnotations.findIndex(item => item.id === annotationId);
        if (index >= 0) state.qaAnnotations[index] = data.annotation;
        renderQaAnnotations();
        gitideNotify({ title: 'QA atualizado', message: `${annotationId} agora está ${qaStatusLabel(statusValue).toLowerCase()}.`, variant: 'success' });
    } catch (err) {
        gitideNotify({ title: 'Erro no QA', message: err.message, variant: 'danger' });
        loadQaAnnotations();
    }
}

function openQaAnnotationDrawer(annotationId) {
    const item = (state.qaAnnotations || []).find(annotation => annotation.id === annotationId);
    if (!item) return;
    const drawer = document.getElementById('qa-detail-drawer');
    const backdrop = document.getElementById('qa-drawer-backdrop');
    const body = document.getElementById('qa-detail-body');
    const title = document.getElementById('qa-detail-title');
    const id = document.getElementById('qa-detail-id');
    if (!drawer || !body) return;
    if (title) title.textContent = item.title || 'Detalhe da anotação';
    if (id) id.textContent = item.id || 'QA';
    const created = item.created_at ? new Date(item.created_at).toLocaleString('pt-BR') : '-';
    const updated = item.updated_at ? new Date(item.updated_at).toLocaleString('pt-BR') : '-';
    const metadata = item.metadata || {};
    const viewport = item.viewport || {};
    body.innerHTML = `
        ${item.screenshot ? `<img class="qa-detail-shot" src="${item.screenshot}" alt="Print da anotação ${escapeHtml(item.id || '')}">` : '<div class="qa-detail-no-shot">Sem print anexado</div>'}
        <div class="qa-detail-section">
            <h5>Resumo</h5>
            <p>${escapeHtml(String(item.description || 'Sem descrição.'))}</p>
            <div class="qa-detail-pills">
                <span class="qa-pill qa-category-${escapeHtml(item.category || 'functional')}">${qaCategoryLabel(item.category)}</span>
                <span class="qa-pill qa-severity-${escapeHtml(item.severity || 'medium')}">${escapeHtml(item.severity || 'medium')}</span>
                <span class="qa-pill qa-status-${escapeHtml(item.status || 'open')}">${qaStatusLabel(item.status)}</span>
            </div>
        </div>
        <div class="qa-detail-section">
            <h5>Contexto</h5>
            <dl class="qa-detail-list">
                <dt>URL</dt><dd>${escapeHtml(String(item.url || '-'))}</dd>
                <dt>Seletor</dt><dd>${escapeHtml(String(item.selector || '-'))}</dd>
                <dt>Viewport</dt><dd>${escapeHtml(`${viewport.width || '-'} x ${viewport.height || '-'}`)}</dd>
                <dt>Criado</dt><dd>${created}</dd>
                <dt>Atualizado</dt><dd>${updated}</dd>
                <dt>Tab</dt><dd>${escapeHtml(String(metadata.tabTitle || '-'))}</dd>
                <dt>Texto selecionado</dt><dd>${escapeHtml(String(metadata.selectedText || '-'))}</dd>
            </dl>
        </div>
        <div class="qa-detail-section">
            <h5>Navegador</h5>
            <code>${escapeHtml(String(item.browser || '-'))}</code>
        </div>
    `;
    drawer.classList.add('is-open');
    backdrop?.classList.add('is-open');
    drawer.setAttribute('aria-hidden', 'false');
    if (window.lucide) lucide.createIcons();
}

function closeQaAnnotationDrawer() {
    const drawer = document.getElementById('qa-detail-drawer');
    const backdrop = document.getElementById('qa-drawer-backdrop');
    drawer?.classList.remove('is-open');
    backdrop?.classList.remove('is-open');
    drawer?.setAttribute('aria-hidden', 'true');
}

async function deleteQaAnnotation(annotationId) {
    if (!state.activeProjectId || !annotationId) return;
    const confirmed = await gitideConfirm({
        title: 'Deletar anotação QA',
        message: `Deseja deletar a anotação <strong>${escapeHtml(annotationId)}</strong>? Esta ação não pode ser desfeita.`,
        confirmText: 'Deletar',
        cancelText: 'Cancelar',
        variant: 'danger',
        kicker: 'QA'
    });
    if (!confirmed) return;
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/qa/annotations/${encodeURIComponent(annotationId)}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') throw new Error(data.detail || 'Erro ao deletar anotação');
        state.qaAnnotations = state.qaAnnotations.filter(item => item.id !== annotationId);
        closeQaAnnotationDrawer();
        renderQaAnnotations();
        gitideNotify({ title: 'Anotação deletada', message: annotationId, variant: 'success' });
    } catch (err) {
        gitideNotify({ title: 'Erro ao deletar QA', message: err.message, variant: 'danger' });
    }
}

function setQaView(view) {
    state.qaView = view === 'kanban' ? 'kanban' : 'list';
    document.querySelectorAll('.qa-view-tab').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.qaView === state.qaView);
    });
    renderQaAnnotations();
}

function copyQaExtensionConfig() {
    if (!state.activeProjectId) {
        gitideNotify({ title: 'Projeto obrigatório', message: 'Selecione um projeto antes de copiar a configuração.', variant: 'warning' });
        return;
    }
    const configText = JSON.stringify({
        apiBase: `${window.location.protocol}//${window.location.host}`,
        projectId: state.activeProjectId,
        token: state.apiKey
    }, null, 2);
    navigator.clipboard.writeText(configText).then(() => {
        gitideNotify({ title: 'Config copiada', message: 'Cole estes dados nas opções da extensão QA.', variant: 'success' });
    }).catch(err => {
        gitideNotify({ title: 'Erro ao copiar', message: err.message, variant: 'danger' });
    });
}

function exportQaAnnotations(format) {
    if (!state.activeProjectId) {
        gitideNotify({ title: 'Projeto obrigatório', message: 'Selecione um projeto antes de exportar.', variant: 'warning' });
        return;
    }
    const safeFormat = format === 'xlsx' ? 'xlsx' : 'pdf';
    const filter = document.getElementById('qa-status-filter')?.value || '';
    const query = filter ? `?status=${encodeURIComponent(filter)}` : '';
    const url = `/api/projects/${state.activeProjectId}/qa/export.${safeFormat}${query}`;
    window.open(url, '_blank');
}

async function loadEngineeringMetrics() {
    if (!state.activeProjectId) return;
    const period = document.getElementById('engineering-metrics-period')?.value || '30';
    renderEngineeringMetricsLoading();
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/engineering-metrics/dora?days=${encodeURIComponent(period)}`, {
            headers: getHeaders()
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao carregar métricas DORA');
        state.engineeringMetrics = data;
        renderEngineeringMetrics(data);
    } catch (err) {
        renderEngineeringMetricsError(err.message || String(err));
    }
}

function setEngineeringPanel(panelName) {
    const nextPanel = panelName || 'dora';
    document.querySelectorAll('.engineering-tab').forEach(button => {
        const isActive = button.dataset.engineeringPanel === nextPanel;
        button.classList.toggle('active', isActive);
        button.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });
    document.querySelectorAll('.engineering-panel-view').forEach(panel => {
        panel.classList.toggle('active', panel.dataset.engineeringPanelView === nextPanel);
    });
    if (nextPanel === 'prod-readiness' || nextPanel === 'security') {
        loadEngineeringReport(nextPanel);
    }
    if (window.lucide) lucide.createIcons();
}

async function loadEngineeringReports() {
    await Promise.all([
        loadEngineeringReport('prod-readiness'),
        loadEngineeringReport('security')
    ]);
}

function renderEngineeringReportMarkdown(markdown) {
    const lines = String(markdown || '').split('\n');
    if (!lines.some(line => line.trim())) return '<div class="engineering-empty">Relatório vazio.</div>';
    return lines.map((line) => {
        const trimmed = line.trim();
        if (!trimmed) return '<br>';
        if (/^#{1,6}\s+/.test(trimmed)) {
            const level = Math.min(4, (trimmed.match(/^#+/)?.[0]?.length || 2) + 1);
            return `<h${level}>${escapeHtml(trimmed.replace(/^#{1,6}\s+/, ''))}</h${level}>`;
        }
        if (/^[-*]\s+/.test(trimmed)) {
            return `<p class="engineering-report-list-item">${escapeHtml(trimmed.replace(/^[-*]\s+/, ''))}</p>`;
        }
        if (/^\|.+\|$/.test(trimmed)) {
            return `<pre class="engineering-report-table-line">${escapeHtml(trimmed)}</pre>`;
        }
        if (/^```/.test(trimmed)) {
            return '';
        }
        return `<p>${escapeHtml(trimmed)}</p>`;
    }).join('');
}

async function loadEngineeringReport(reportType) {
    if (!state.activeProjectId) return;
    const contentId = reportType === 'security' ? 'security-report-content' : 'prod-readiness-report-content';
    const metaId = reportType === 'security' ? 'security-report-meta' : 'prod-readiness-report-meta';
    const contentEl = document.getElementById(contentId);
    const metaEl = document.getElementById(metaId);
    if (!contentEl || !metaEl) return;

    contentEl.innerHTML = '<div class="engineering-empty">Carregando relatório...</div>';
    metaEl.textContent = 'Carregando...';
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/engineering-metrics/reports/${encodeURIComponent(reportType)}`, {
            headers: getHeaders()
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao carregar relatório');
        const updated = data.updated_at ? new Date(data.updated_at).toLocaleString('pt-BR') : 'Ainda não gerado';
        metaEl.innerHTML = `<span>${escapeHtml(data.filepath || '')}</span><strong>${escapeHtml(updated)}</strong>`;
        if (data.status === 'empty') {
            contentEl.innerHTML = `<div class="engineering-empty">${escapeHtml(data.message || 'Relatório não encontrado.')}</div>`;
            return;
        }
        contentEl.innerHTML = renderEngineeringReportMarkdown(data.content || '');
    } catch (err) {
        metaEl.textContent = 'Erro ao carregar relatório.';
        contentEl.innerHTML = `<div class="engineering-empty danger">${escapeHtml(err.message || String(err))}</div>`;
    }
}

function openEngineeringReportFile(filepath) {
    if (!state.activeProjectId || !filepath) return;
    switchTab('tab-files');
    openFile(filepath, 0, new Date().toISOString());
}

function setMetricText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function renderEngineeringMetricsLoading() {
    setMetricText('dora-performance-level', 'Carregando...');
    setMetricText('dora-performance-note', 'Calculando sinais do projeto.');
    setMetricText('dora-success-rate', '-');
    setMetricText('dora-risk-level', '-');
    setMetricText('dora-risk-note', '-');
    setMetricText('metric-deploy-frequency', '-');
    setMetricText('metric-deploy-frequency-context', 'Deploys por período');
    setMetricText('metric-lead-time', '-');
    setMetricText('metric-failure-rate', '-');
    setMetricText('metric-mttr', '-');
    const bars = document.getElementById('engineering-flow-bars');
    const signals = document.getElementById('engineering-signal-list');
    if (bars) bars.innerHTML = '<div class="engineering-empty">Carregando métricas...</div>';
    if (signals) signals.innerHTML = '<div class="engineering-empty">Carregando sinais...</div>';
}

function renderEngineeringMetricsError(message) {
    setMetricText('dora-performance-level', 'Erro');
    setMetricText('dora-performance-note', message);
    const bars = document.getElementById('engineering-flow-bars');
    const signals = document.getElementById('engineering-signal-list');
    if (bars) bars.innerHTML = `<div class="engineering-empty danger">${escapeHtml(message)}</div>`;
    if (signals) signals.innerHTML = `<div class="engineering-empty danger">Não foi possível calcular agora.</div>`;
}

function engineeringMetricPercent(value, max = 100) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return 0;
    return Math.max(4, Math.min(100, (Number(value) / max) * 100));
}

function renderEngineeringMetrics(data) {
    const metrics = data.metrics || {};
    const signals = data.signals || {};
    const success = metrics.success_rate || {};
    const deployFrequency = metrics.deploy_frequency || {};
    setMetricText('dora-performance-level', data.performance_level || '-');
    setMetricText('dora-performance-note', `Baseado nos últimos ${data.period_days || 30} dias.`);
    setMetricText('dora-success-rate', success.label || 'Sem dados');
    setMetricText('dora-risk-level', data.risk_level || '-');
    setMetricText('dora-risk-note', data.risk_note || '-');
    setMetricText('metric-deploy-frequency', deployFrequency.label || 'Sem dados');
    setMetricText('metric-deploy-frequency-context', deployFrequency.context || 'Deploys por período');
    setMetricText('metric-lead-time', metrics.lead_time?.label || 'Sem dados');
    setMetricText('metric-failure-rate', metrics.change_failure_rate?.label || 'Sem dados');
    setMetricText('metric-mttr', metrics.mttr?.label || 'Sem dados');

    const bars = document.getElementById('engineering-flow-bars');
    if (bars) {
        const flowItems = [
            ['Commits', signals.commits || 0, Math.max(signals.commits || 0, 10)],
            ['Deploys', signals.deploys || 0, Math.max(signals.deploys || 0, 5)],
            ['Tasks concluídas', signals.tasks_done || 0, Math.max(signals.tasks_total || 0, 1)],
            ['QA resolvidas', signals.qa_resolved || 0, Math.max((signals.qa_open || 0) + (signals.qa_reviewing || 0) + (signals.qa_resolved || 0), 1)]
        ];
        bars.innerHTML = flowItems.map(([label, value, max]) => `
            <div class="engineering-flow-row">
                <span>${escapeHtml(label)}</span>
                <div class="engineering-flow-track"><i style="width:${engineeringMetricPercent(value, max)}%"></i></div>
                <strong>${value}</strong>
            </div>
        `).join('');
    }

    const signalList = document.getElementById('engineering-signal-list');
    if (signalList) {
        const signalItems = [
            ['Tasks', `${signals.tasks_done || 0}/${signals.tasks_total || 0} concluídas`, success.value === null || success.value === undefined ? 'neutral' : success.value >= 80 ? 'good' : 'warn'],
            ['QA abertas', `${signals.qa_open || 0} abertas, ${signals.qa_reviewing || 0} em revisão`, (signals.qa_open || 0) === 0 ? 'good' : 'warn'],
            ['QA crítica', `${signals.critical_open || 0} alta/crítica aberta`, (signals.critical_open || 0) === 0 ? 'good' : 'danger'],
            ['Falhas operacionais', `${signals.failure_logs || 0} log(s) com falha`, (signals.failure_logs || 0) === 0 ? 'good' : 'danger']
        ];
        signalList.innerHTML = signalItems.map(([label, value, variant]) => `
            <div class="engineering-signal ${variant}">
                <span>${escapeHtml(label)}</span>
                <strong>${escapeHtml(value)}</strong>
            </div>
        `).join('');
    }

    if (window.lucide) lucide.createIcons();
}

function gitideConfirm({ title = 'Confirmar ação', message = '', confirmText = 'Confirmar', cancelText = 'Cancelar', variant = 'info', kicker = 'Act IA' } = {}) {
    return new Promise((resolve) => {
        const modal = document.getElementById('modal-confirm');
        const titleEl = document.getElementById('confirm-title');
        const kickerEl = document.getElementById('confirm-kicker');
        const messageEl = document.getElementById('confirm-message');
        const iconEl = document.getElementById('confirm-icon');
        const okBtn = document.getElementById('btn-confirm-ok');
        const cancelBtn = document.getElementById('btn-confirm-cancel');
        const closeBtn = modal.querySelector('.confirm-close');
        const icons = {
            info: 'info',
            success: 'check-circle-2',
            warning: 'triangle-alert',
            danger: 'trash-2'
        };
        
        titleEl.textContent = title;
        if (kickerEl) kickerEl.textContent = kicker;
        messageEl.innerHTML = message;
        okBtn.textContent = confirmText;
        cancelBtn.textContent = cancelText;
        modal.dataset.variant = variant;
        if (iconEl) iconEl.innerHTML = `<i data-lucide="${icons[variant] || icons.info}"></i>`;
        okBtn.classList.toggle('btn-danger-confirm', variant === 'danger');
        
        modal.classList.add('active');
        if (window.lucide) lucide.createIcons();
        
        const cleanup = (result) => {
            modal.classList.remove('active');
            delete modal.dataset.variant;
            okBtn.classList.remove('btn-danger-confirm');
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

function showCustomConfirm(title, message, confirmButtonText = 'Confirmar', isDanger = false) {
    return gitideConfirm({
        title,
        message,
        confirmText: confirmButtonText,
        variant: isDanger ? 'danger' : 'info'
    });
}

function syncDbTypeSelectShell() {
    const select = document.getElementById('db-type-select');
    const valueLabel = document.getElementById('db-type-select-value');
    const options = document.querySelectorAll('.db-type-select-option');
    if (!select || !valueLabel || !options.length) return;

    const selectedOption = select.options[select.selectedIndex] || select.options[0];
    valueLabel.textContent = selectedOption ? selectedOption.textContent.trim() : 'Selecionar banco';

    options.forEach(option => {
        const isSelected = option.dataset.value === select.value;
        option.classList.toggle('is-selected', isSelected);
        option.setAttribute('aria-selected', isSelected ? 'true' : 'false');
    });
}

function closeDbTypeSelectShell() {
    const shell = document.getElementById('db-type-select-shell');
    const trigger = document.getElementById('db-type-select-trigger');
    if (!shell || !trigger) return;

    shell.classList.remove('is-open');
    trigger.setAttribute('aria-expanded', 'false');
}

function initDbTypeSelectShell() {
    const select = document.getElementById('db-type-select');
    const shell = document.getElementById('db-type-select-shell');
    const trigger = document.getElementById('db-type-select-trigger');
    const options = document.querySelectorAll('.db-type-select-option');
    if (!select || !shell || !trigger || !options.length) return;

    trigger.addEventListener('click', (event) => {
        event.stopPropagation();
        const willOpen = !shell.classList.contains('is-open');
        shell.classList.toggle('is-open', willOpen);
        trigger.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
    });

    options.forEach(option => {
        option.addEventListener('click', (event) => {
            event.stopPropagation();
            select.value = option.dataset.value;
            select.dispatchEvent(new Event('change', { bubbles: true }));
            closeDbTypeSelectShell();
        });
    });

    document.addEventListener('click', closeDbTypeSelectShell);
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') closeDbTypeSelectShell();
    });

    select.addEventListener('change', syncDbTypeSelectShell);
    syncDbTypeSelectShell();
}

// --- OPS INFRA ---
function getOpsInfraPayload() {
    return {
        environment: document.getElementById('ops-env-select')?.value || 'prod',
        domain: document.getElementById('ops-domain-input')?.value?.trim() || null,
        database: document.getElementById('ops-db-select')?.value || null
    };
}

function getOpsVmAccessPayload() {
    return {
        host: document.getElementById('ops-vm-host')?.value?.trim() || '',
        user: document.getElementById('ops-vm-user')?.value?.trim() || '',
        port: Number(document.getElementById('ops-vm-port')?.value || 22),
        app_path: document.getElementById('ops-vm-path')?.value?.trim() || '',
        auth_method: document.getElementById('ops-vm-auth-method')?.value || 'key',
        private_key: document.getElementById('ops-vm-private-key')?.value || '',
        password: document.getElementById('ops-vm-password')?.value || ''
    };
}

function setOpsVmAccessFields(data = {}) {
    const host = document.getElementById('ops-vm-host');
    const user = document.getElementById('ops-vm-user');
    const port = document.getElementById('ops-vm-port');
    const appPath = document.getElementById('ops-vm-path');
    const authMethod = document.getElementById('ops-vm-auth-method');
    const privateKey = document.getElementById('ops-vm-private-key');
    const password = document.getElementById('ops-vm-password');
    const publicKey = document.getElementById('ops-vm-public-key');
    const privateKeyStatus = document.getElementById('ops-vm-private-key-status');
    const passwordStatus = document.getElementById('ops-vm-password-status');
    if (host) host.value = data.host || '';
    if (user) user.value = data.user || '';
    if (port) port.value = data.port || 22;
    if (appPath) appPath.value = data.app_path || '';
    if (authMethod) authMethod.value = data.auth_method || 'key';
    if (privateKey) privateKey.value = '';
    if (password) password.value = '';
    if (publicKey) publicKey.value = data.public_key || '';
    if (privateKeyStatus) privateKeyStatus.textContent = data.has_private_key ? 'Chave privada já cadastrada. Preencha apenas se quiser substituir.' : '';
    if (passwordStatus) passwordStatus.textContent = data.has_password ? 'Senha já cadastrada. Preencha apenas se quiser substituir.' : '';
    state.opsVmAccess = data;
    syncOpsVmAuthFields();
}

function syncOpsVmAuthFields() {
    const method = document.getElementById('ops-vm-auth-method')?.value || 'key';
    const keyField = document.getElementById('ops-vm-private-key-field');
    const passwordField = document.getElementById('ops-vm-password-field');
    if (keyField) keyField.style.display = method === 'key' ? '' : 'none';
    if (passwordField) passwordField.style.display = method === 'password' ? '' : 'none';
}

async function opsInfraGenerateVmKey() {
    if (!state.activeProjectId) return;
    const consoleEl = document.getElementById('ops-console-output');
    if (consoleEl) consoleEl.textContent = 'Gerando par de chaves SSH...';
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/ops-infra/vm-access/generate-key`, {
            method: 'POST',
            headers: getHeaders()
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao gerar chave SSH.');
        setOpsVmAccessFields(data);
        if (consoleEl) {
            consoleEl.textContent = `Chave pública gerada.\n\nCadastre esta chave no painel da VPS e depois clique em Salvar e testar SSH:\n\n${data.public_key || ''}`;
        }
        gitideNotify({ title: 'Chave pública gerada', message: 'Cadastre a chave pública na VPS antes de testar o SSH.', variant: 'success' });
    } catch (err) {
        if (consoleEl) consoleEl.textContent = `Erro: ${err.message}`;
        gitideNotify({ title: 'Erro ao gerar chave', message: err.message, variant: 'error' });
    }
}

async function opsInfraCopyPublicKey() {
    const value = document.getElementById('ops-vm-public-key')?.value?.trim();
    if (!value) {
        gitideNotify({ title: 'Sem chave pública', message: 'Gere uma chave pública primeiro.', variant: 'warning' });
        return;
    }
    await navigator.clipboard.writeText(value);
    gitideNotify({ title: 'Chave pública copiada', message: 'Cole esta chave no painel SSH da VPS.', variant: 'success' });
}

async function opsInfraLoadVmAccess() {
    if (!state.activeProjectId) return;
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/ops-infra/vm-access`, { headers: getHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao carregar acesso da VM.');
        setOpsVmAccessFields(data);
    } catch (err) {
        setOpsVmAccessFields({ host: '', user: '', port: 22, app_path: '' });
        gitideNotify({ title: 'Erro ao carregar VM', message: err.message, variant: 'error' });
    }
}

function opsVmNormalizePath(path) {
    const value = (path || '/').trim();
    if (!value) return '/';
    return value.startsWith('/') ? value.replace(/\/+/g, '/') : `/${value}`.replace(/\/+/g, '/');
}

function renderOpsVmDirectories(data) {
    const browser = document.getElementById('ops-vm-browser');
    const pathEl = document.getElementById('ops-vm-browser-path');
    const list = document.getElementById('ops-vm-dir-list');
    if (browser) browser.hidden = false;
    state.opsVmBrowserPath = data.path || state.opsVmBrowserPath || '/';
    state.opsVmBrowserParent = data.parent || '/';
    if (pathEl) pathEl.textContent = state.opsVmBrowserPath;
    if (!list) return;
    const dirs = data.directories || [];
    if (!dirs.length) {
        list.innerHTML = '<span class="ops-muted">Nenhum subdiretório encontrado.</span>';
        return;
    }
    list.innerHTML = dirs.map(dir => `
        <button type="button" class="ops-vm-dir-item" data-ops-vm-path="${escapeHtml(dir.path)}">
            <i data-lucide="folder"></i>
            <span>${escapeHtml(dir.name)}</span>
            <small>${escapeHtml(dir.path)}</small>
        </button>
    `).join('');
    list.querySelectorAll('.ops-vm-dir-item').forEach(item => {
        item.addEventListener('click', () => opsInfraBrowseVmPath(item.dataset.opsVmPath));
    });
    if (window.lucide) lucide.createIcons();
}

async function opsInfraBrowseVmPath(path) {
    if (!state.activeProjectId) return;
    const targetPath = opsVmNormalizePath(path || document.getElementById('ops-vm-path')?.value || state.opsVmBrowserPath || '/');
    const list = document.getElementById('ops-vm-dir-list');
    if (list) list.innerHTML = '<span class="ops-muted">Carregando diretórios da VM...</span>';
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/ops-infra/vm/directories`, {
            method: 'POST',
            headers: { ...getHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: targetPath })
        });
        const data = await res.json();
        if (!res.ok || data.status === 'error') throw new Error(data.stderr || data.detail || 'Erro ao listar diretórios.');
        renderOpsVmDirectories(data);
    } catch (err) {
        if (list) list.innerHTML = `<span class="ops-error">${escapeHtml(err.message)}</span>`;
        gitideNotify({ title: 'Erro ao listar VM', message: err.message, variant: 'error' });
    }
}

function opsInfraUseVmBrowserPath() {
    const input = document.getElementById('ops-vm-path');
    if (input) input.value = state.opsVmBrowserPath || '/';
    gitideNotify({ title: 'Diretório selecionado', message: `${state.opsVmBrowserPath} aplicado no campo da VM.`, variant: 'success' });
}

async function opsInfraCreateVmDirectory() {
    if (!state.activeProjectId) return;
    const input = document.getElementById('ops-vm-new-dir');
    const raw = input?.value?.trim();
    if (!raw) {
        gitideNotify({ title: 'Informe a pasta', message: 'Digite o nome ou caminho absoluto da pasta a criar.', variant: 'warning' });
        return;
    }
    const base = state.opsVmBrowserPath || '/';
    const path = raw.startsWith('/') ? raw : `${base.replace(/\/$/, '')}/${raw}`;
    const list = document.getElementById('ops-vm-dir-list');
    if (list) list.innerHTML = '<span class="ops-muted">Criando diretório na VM...</span>';
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/ops-infra/vm/directories/create`, {
            method: 'POST',
            headers: { ...getHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: opsVmNormalizePath(path) })
        });
        const data = await res.json();
        if (!res.ok || data.status === 'error') throw new Error(data.stderr || data.detail || 'Erro ao criar diretório.');
        if (input) input.value = '';
        renderOpsVmDirectories(data);
        const pathInput = document.getElementById('ops-vm-path');
        if (pathInput) pathInput.value = data.created || data.path || path;
        gitideNotify({ title: 'Diretório criado', message: data.created || path, variant: 'success' });
    } catch (err) {
        if (list) list.innerHTML = `<span class="ops-error">${escapeHtml(err.message)}</span>`;
        gitideNotify({ title: 'Erro ao criar diretório', message: err.message, variant: 'error' });
    }
}

function opsInfraSwitchFlowTab(tabName) {
    document.querySelectorAll('.ops-flow-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.opsFlowTab === tabName);
    });
    document.querySelectorAll('.ops-flow-panel').forEach(panel => {
        panel.classList.toggle('active', panel.dataset.opsFlowPanel === tabName);
    });
    if (tabName === 'environment') opsInfraLoadEnv();
}

function renderOpsEnvVariables() {
    const target = document.getElementById('ops-env-list');
    if (!target) return;
    if (!state.opsEnvVariables.length) {
        target.innerHTML = '<span class="ops-muted">Nenhuma variável cadastrada para este ambiente.</span>';
        return;
    }
    target.innerHTML = state.opsEnvVariables.map((item, index) => `
        <div class="ops-env-row" data-ops-env-row="${index}">
            <input class="text-input ops-env-key" value="${escapeHtml(item.key || '')}" placeholder="APP_KEY">
            <input class="text-input ops-env-value" value="${escapeHtml(item.value || '')}" placeholder="valor" ${item.secret ? 'type="password"' : 'type="text"'}>
            <label class="ops-env-secret"><input type="checkbox" class="ops-env-secret-input" ${item.secret ? 'checked' : ''}> secret</label>
            <button class="btn btn-secondary ops-env-remove" type="button"><i class="fa-solid fa-trash"></i></button>
        </div>
    `).join('');
    target.querySelectorAll('.ops-env-row').forEach(row => {
        const index = Number(row.dataset.opsEnvRow);
        row.querySelector('.ops-env-key').addEventListener('input', e => state.opsEnvVariables[index].key = e.target.value);
        row.querySelector('.ops-env-value').addEventListener('input', e => state.opsEnvVariables[index].value = e.target.value);
        row.querySelector('.ops-env-secret-input').addEventListener('change', e => {
            state.opsEnvVariables[index].secret = e.target.checked;
            renderOpsEnvVariables();
        });
        row.querySelector('.ops-env-remove').addEventListener('click', () => {
            state.opsEnvVariables.splice(index, 1);
            renderOpsEnvVariables();
        });
    });
}

function opsInfraAddEnvVariable(key = '', value = '', secret = false) {
    state.opsEnvVariables.push({ key, value, secret });
    renderOpsEnvVariables();
}

async function opsInfraLoadEnv() {
    if (!state.activeProjectId) return;
    const env = document.getElementById('ops-env-select')?.value || 'prod';
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/ops-infra/env/${encodeURIComponent(env)}`, { headers: getHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao carregar ambiente.');
        state.opsEnvVariables = data.variables || [];
        renderOpsEnvVariables();
    } catch (err) {
        state.opsEnvVariables = [];
        renderOpsEnvVariables();
        gitideNotify({ title: 'Erro ao carregar .env', message: err.message, variant: 'error' });
    }
}

async function opsInfraSaveEnv() {
    if (!state.activeProjectId) return;
    const env = document.getElementById('ops-env-select')?.value || 'prod';
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/ops-infra/env`, {
            method: 'POST',
            headers: { ...getHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ environment: env, variables: state.opsEnvVariables, write_env_file: true })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao salvar ambiente.');
        state.opsEnvVariables = data.variables || [];
        renderOpsEnvVariables();
        gitideNotify({ title: 'Ambiente salvo', message: `${env} salvo e ${data.env_file || '.env'} gerado.`, variant: 'success' });
        loadFiles();
    } catch (err) {
        gitideNotify({ title: 'Erro ao salvar ambiente', message: err.message, variant: 'error' });
    }
}

async function opsInfraValidateEnv() {
    if (!state.activeProjectId) return;
    const env = document.getElementById('ops-env-select')?.value || 'prod';
    const target = document.getElementById('ops-env-validation');
    if (target) target.innerHTML = '<span class="ops-muted">Validando .env...</span>';
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/ops-infra/env/validate`, {
            method: 'POST',
            headers: { ...getHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ environment: env, variables: state.opsEnvVariables, write_env_file: false })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao validar .env.');
        target.innerHTML = data.valid
            ? '<span class="ops-valid">.env válido para o deploy.</span>'
            : `<ul>${(data.issues || []).map(issue => `<li>${escapeHtml(issue)}</li>`).join('')}</ul>`;
    } catch (err) {
        if (target) target.innerHTML = `<span class="ops-error">${escapeHtml(err.message)}</span>`;
    }
}

function renderOpsDetected(data) {
    const target = document.getElementById('ops-detected-card');
    if (!target) return;
    target.innerHTML = `
        <div class="ops-detected-row"><span>Stack</span><strong>${data.stack || '-'}</strong></div>
        <div class="ops-detected-row"><span>Runtime</span><strong>${data.runtime || '-'}</strong></div>
        <div class="ops-detected-row"><span>Porta</span><strong>${data.port || '-'}</strong></div>
        <div class="ops-detected-row"><span>Build</span><code>${data.build_command || '-'}</code></div>
        <div class="ops-detected-row"><span>Start</span><code>${data.start_command || '-'}</code></div>
    `;
}

function renderOpsPlan(data) {
    const target = document.getElementById('ops-plan-output');
    if (!target) return;
    const ai = data.ai;
    const steps = ai?.steps || data.steps || [];
    const risks = ai?.risks || [];
    target.innerHTML = `
        ${ai?.summary ? `<p>${escapeHtml(ai.summary)}</p>` : ''}
        <h5>Plano de deploy</h5>
        <ol>${steps.map(step => `<li>${escapeHtml(String(step))}</li>`).join('')}</ol>
        ${risks.length ? `<h5>Riscos</h5><ul>${risks.map(risk => `<li>${escapeHtml(String(risk))}</li>`).join('')}</ul>` : ''}
    `;
}

async function opsInfraDetect() {
    if (!state.activeProjectId) return;
    const target = document.getElementById('ops-detected-card');
    if (target) target.innerHTML = '<span class="ops-muted">Detectando stack...</span>';
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/ops-infra/detect`, { headers: getHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao detectar stack.');
        renderOpsDetected(data);
    } catch (err) {
        if (target) target.innerHTML = `<span class="ops-error">${escapeHtml(err.message)}</span>`;
    }
}

async function opsInfraPlan() {
    if (!state.activeProjectId) return;
    const target = document.getElementById('ops-plan-output');
    if (target) target.innerHTML = '<span class="ops-muted">Gerando plano...</span>';
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/ops-infra/plan`, {
            method: 'POST',
            headers: { ...getHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify(getOpsInfraPayload())
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao gerar plano.');
        renderOpsDetected(data.detected || {});
        renderOpsPlan(data);
    } catch (err) {
        if (target) target.innerHTML = `<span class="ops-error">${escapeHtml(err.message)}</span>`;
    }
}

async function opsInfraGenerateArtifacts() {
    if (!state.activeProjectId) return;
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/ops-infra/artifacts`, {
            method: 'POST',
            headers: { ...getHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ ...getOpsInfraPayload(), overwrite: false })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao gerar arquivos.');
        gitideNotify({
            title: 'Arquivos Ops gerados',
            message: `Criados: ${data.written.join(', ') || 'nenhum'}${data.skipped.length ? ` | Mantidos: ${data.skipped.join(', ')}` : ''}`,
            variant: 'success'
        });
        renderOpsDetected(data.detected || {});
        loadFiles();
    } catch (err) {
        gitideNotify({ title: 'Erro no Ops Infra', message: err.message, variant: 'error' });
    }
}

function renderOpsCaddyPreview(data) {
    const target = document.getElementById('ops-caddy-output');
    if (!target) return;
    target.innerHTML = `
        <div class="ops-caddy-domain"><span>Domínio</span><strong>${escapeHtml(data.domain || '-')}</strong></div>
        <h5>DNS necessário</h5>
        <ul>${(data.dns || []).map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul>
        <h5>Caddyfile</h5>
        <pre>${escapeHtml(data.caddyfile || '')}</pre>
        <h5>Docker Compose</h5>
        <ul>${(data.compose_notes || []).map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul>
    `;
}

async function opsInfraCaddyPreview() {
    if (!state.activeProjectId) return;
    const domain = document.getElementById('ops-domain-input')?.value?.trim();
    if (!domain) {
        gitideNotify({ title: 'Domínio obrigatório', message: 'Informe o domínio antes de gerar a prévia do Caddy.', variant: 'warning' });
        return;
    }
    const target = document.getElementById('ops-caddy-output');
    if (target) target.innerHTML = '<span class="ops-muted">Gerando prévia do Caddy...</span>';
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/ops-infra/domain/preview`, {
            method: 'POST',
            headers: { ...getHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ domain, environment: document.getElementById('ops-env-select')?.value || 'prod' })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao gerar prévia do Caddy.');
        renderOpsCaddyPreview(data);
    } catch (err) {
        if (target) target.innerHTML = `<span class="ops-error">${escapeHtml(err.message)}</span>`;
    }
}

async function opsInfraCaddyApply() {
    if (!state.activeProjectId) return;
    const domain = document.getElementById('ops-domain-input')?.value?.trim();
    if (!domain) {
        gitideNotify({ title: 'Domínio obrigatório', message: 'Informe o domínio antes de aplicar o Caddyfile.', variant: 'warning' });
        return;
    }
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/ops-infra/domain/apply`, {
            method: 'POST',
            headers: { ...getHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ domain, environment: document.getElementById('ops-env-select')?.value || 'prod', overwrite: true })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao aplicar Caddyfile.');
        renderOpsCaddyPreview(data);
        gitideNotify({ title: 'Caddyfile aplicado', message: `Domínio configurado: ${data.domain}`, variant: 'success' });
        loadFiles();
    } catch (err) {
        gitideNotify({ title: 'Erro no Caddy', message: err.message, variant: 'error' });
    }
}

async function opsInfraTestVmAccess() {
    if (!state.activeProjectId) return;
    const consoleEl = document.getElementById('ops-console-output');
    const button = document.getElementById('btn-ops-vm-test');
    const payload = getOpsVmAccessPayload();
    if (consoleEl) consoleEl.textContent = `Testando SSH em ${payload.user || '?'}@${payload.host || '?'}:${payload.port || 22}...`;
    if (button) button.disabled = true;
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/ops-infra/vm-access/test`, {
            method: 'POST',
            headers: { ...getHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        const test = data.test || {};
        state.opsVmAccess = data;
        if (consoleEl) {
            consoleEl.textContent = `$ ${test.command || 'ssh'}\n\n[exit ${test.exit_code ?? '-'}]\n\n${test.stdout || ''}${test.stderr ? `\n[stderr]\n${test.stderr}` : ''}`;
        }
        if (!res.ok || data.status === 'error') throw new Error(test.stderr || data.detail || 'Falha ao testar SSH.');
        gitideNotify({ title: 'SSH validado', message: `Conexão OK com ${data.user}@${data.host}.`, variant: 'success' });
    } catch (err) {
        if (consoleEl) consoleEl.textContent += `\n\nErro: ${err.message}`;
        gitideNotify({ title: 'Falha no SSH', message: err.message, variant: 'error' });
    } finally {
        if (button) button.disabled = false;
    }
}

function opsInfraWriteConsole(data, fallbackCommand = '') {
    const consoleEl = document.getElementById('ops-console-output');
    if (!consoleEl) return;
    const stdout = data.stdout || data.body_preview || '';
    const stderr = data.stderr || data.detail || '';
    const command = data.command || data.url || fallbackCommand;
    const exitCode = data.exit_code ?? data.status_code ?? '-';
    consoleEl.textContent = `$ ${command}\n\n[exit ${exitCode}]\n\n${stdout}${stderr ? `\n[stderr]\n${stderr}` : ''}`;
}

async function opsInfraRunOperation(label, endpoint, payload = {}) {
    if (!state.activeProjectId) return;
    const consoleEl = document.getElementById('ops-console-output');
    if (consoleEl) consoleEl.textContent = `${label}...`;
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/ops-infra/${endpoint}`, {
            method: 'POST',
            headers: { ...getHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        opsInfraWriteConsole(data, endpoint);
        if (!res.ok || data.status === 'error') throw new Error(data.stderr || data.detail || 'Operação falhou.');
        gitideNotify({ title: 'Ops Infra', message: `${label} concluído.`, variant: 'success' });
        return data;
    } catch (err) {
        if (consoleEl) consoleEl.textContent += `\n\nErro: ${err.message}`;
        gitideNotify({ title: 'Erro no Ops Infra', message: err.message, variant: 'error' });
        return null;
    }
}

async function opsInfraBootstrapVm() {
    return opsInfraRunOperation('Preparando VM', 'bootstrap');
}

async function opsInfraSyncProject() {
    return opsInfraRunOperation('Sincronizando projeto na VM', 'sync');
}

async function opsInfraCheckDns() {
    const domain = document.getElementById('ops-domain-input')?.value?.trim();
    if (!domain) {
        gitideNotify({ title: 'Domínio obrigatório', message: 'Informe o domínio antes de validar DNS.', variant: 'warning' });
        return;
    }
    const data = await opsInfraRunOperation('Validando DNS', 'dns/check', { domain });
    if (data) {
        const target = document.getElementById('ops-caddy-output');
        if (target) {
            target.innerHTML = `
                <div class="ops-caddy-domain"><span>Domínio</span><strong>${escapeHtml(data.domain || domain)}</strong></div>
                <h5>Resultado DNS</h5>
                <ul>
                    <li>Esperado: ${escapeHtml(data.expected || '-')}</li>
                    <li>Encontrado: ${escapeHtml((data.records || []).join(', ') || '-')}</li>
                    <li>Status: ${data.matches ? '<span class="ops-valid">apontando para a VM</span>' : '<span class="ops-error">não aponta para a VM</span>'}</li>
                </ul>
            `;
        }
    }
}

async function opsInfraHealthCheck() {
    const domain = document.getElementById('ops-domain-input')?.value?.trim();
    return opsInfraRunOperation('Executando health check', 'health', { domain });
}

async function opsInfraCheckDatabase() {
    return opsInfraRunOperation('Validando banco na VM', 'database/check');
}

async function opsInfraRunCommand(action) {
    if (!state.activeProjectId) return;
    const consoleEl = document.getElementById('ops-console-output');
    if (consoleEl) consoleEl.textContent = `Executando ${action} na VM...`;
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/ops-infra/remote-command`, {
            method: 'POST',
            headers: { ...getHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        });
        const data = await res.json();
        if (consoleEl) {
            consoleEl.textContent = `$ ${data.command}\n\n[exit ${data.exit_code}]\n\n${data.stdout || ''}${data.stderr ? `\n[stderr]\n${data.stderr}` : ''}`;
        }
        if (!res.ok || data.status === 'error') throw new Error(data.stderr || data.detail || 'Comando falhou.');
    } catch (err) {
        if (consoleEl) consoleEl.textContent += `\n\nErro: ${err.message}`;
    }
}

// =============================================================================
// --- UI CANVAS MODULE ---
// =============================================================================

function uiCanvasSlug(value) {
    return (value || 'novo-canvas')
        .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '') || 'novo-canvas';
}

function uiCanvasCreateDocument(name = 'Novo Canvas') {
    return {
        version: 1,
        name,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        viewport: { width: 2600, height: 1800 },
        frames: [],
        layers: []
    };
}

function uiCanvasEnsureDraft() {
    if (uiCanvasState.doc) return uiCanvasState.doc;
    const stamp = new Date();
    const name = `Canvas ${stamp.toLocaleDateString('pt-BR')} ${stamp.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`;
    uiCanvasState.doc = uiCanvasCreateDocument(name);
    uiCanvasState.filepath = `.documents/canvas/${uiCanvasSlug(name)}.canvas.json`;
    uiCanvasState.selectedLayerId = null;
    return uiCanvasState.doc;
}

function uiCanvasLayerLabel(type) {
    const labels = {
        frame: 'Frame',
        group: 'Group',
        section: 'Section',
        rect: 'Retângulo',
        text: 'Texto',
        heading: 'Heading',
        paragraph: 'Text Basic',
        line: 'Linha',
        divider: 'Divider',
        button: 'Button',
        input: 'Input',
        card: 'Card',
        table: 'Table',
        list: 'List',
        icon: 'Icon',
        image: 'Image',
        video: 'Video'
    };
    return labels[type] || type;
}

function uiCanvasDefaultLayer(type, x, y) {
    const id = `${type}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
    const framePresetKey = type === 'frame' ? document.getElementById('ui-canvas-frame-preset')?.value : '';
    const framePreset = framePresetKey ? UI_CANVAS_FRAME_PRESETS[framePresetKey] : null;
    const normalizedType = type === 'section' ? 'frame' : type;
    const isText = ['text', 'heading', 'paragraph', 'button', 'input', 'list'].includes(normalizedType);
    const base = {
        id,
        type: normalizedType,
        name: framePreset?.name || uiCanvasLayerLabel(normalizedType),
        x: Math.round(x),
        y: Math.round(y),
        width: framePreset?.width || (normalizedType === 'text' ? 220 : normalizedType === 'line' || normalizedType === 'divider' ? 220 : normalizedType === 'frame' ? 375 : normalizedType === 'table' ? 420 : normalizedType === 'image' || normalizedType === 'video' ? 260 : 180),
        height: framePreset?.height || (normalizedType === 'text' ? 44 : normalizedType === 'heading' ? 48 : normalizedType === 'paragraph' ? 76 : normalizedType === 'line' || normalizedType === 'divider' ? 2 : normalizedType === 'frame' ? 667 : normalizedType === 'table' ? 180 : normalizedType === 'image' || normalizedType === 'video' ? 160 : 96),
        widthMode: 'fixed',
        heightMode: 'fixed',
        fill: normalizedType === 'frame' ? '#101012' : normalizedType === 'line' || normalizedType === 'divider' ? '#f8fafc' : isText ? 'transparent' : '#1f1f22',
        stroke: isText ? 'transparent' : '#2d2d31',
        radius: normalizedType === 'frame' ? 18 : normalizedType === 'button' || normalizedType === 'input' ? 12 : 10,
        opacity: 1,
        token: '',
        parentId: null
    };
    if (normalizedType === 'frame' || normalizedType === 'group') {
        return { ...base, autoLayout: { enabled: false, direction: 'vertical', gap: 12, padding: 16 } };
    }
    if (normalizedType === 'heading') {
        return { ...base, text: 'Heading', color: '#f8fafc', fontSize: 28, fontWeight: 800 };
    }
    if (normalizedType === 'paragraph') {
        return { ...base, text: 'Texto básico', color: '#a1a1aa', fontSize: 16, fontWeight: 500 };
    }
    if (normalizedType === 'button') {
        return { ...base, text: 'Button', color: '#050505', fill: '#f8fafc', stroke: 'transparent', fontSize: 15, fontWeight: 700, width: 128, height: 44 };
    }
    if (normalizedType === 'input') {
        return { ...base, text: 'Placeholder', color: '#71717a', fill: '#111113', stroke: '#2d2d31', fontSize: 14, fontWeight: 500, width: 260, height: 44 };
    }
    if (normalizedType === 'list') {
        return { ...base, text: 'Item 1\nItem 2\nItem 3', color: '#f8fafc', fontSize: 15, fontWeight: 500, width: 220, height: 100 };
    }
    if (normalizedType === 'icon') {
        return { ...base, icon: 'sparkles', text: '', color: '#f8fafc', fontSize: 24, fontWeight: 700, width: 48, height: 48 };
    }
    if (normalizedType === 'image' || normalizedType === 'video') {
        return { ...base, text: normalizedType === 'image' ? 'Image' : 'Video', color: '#71717a', fill: '#151518', stroke: '#34343a', fontSize: 14, fontWeight: 700 };
    }
    if (normalizedType === 'table') {
        return { ...base, text: 'Table', fill: '#151518', stroke: '#34343a' };
    }
    if (normalizedType === 'text') {
        return { ...base, text: 'Texto', color: '#f8fafc', fontSize: 18, fontWeight: 700 };
    }
    return base;
}

function uiCanvasGetLayers() {
    return uiCanvasState.doc?.layers || [];
}

function uiCanvasGetSelectedLayer() {
    return uiCanvasGetLayers().find(layer => layer.id === uiCanvasState.selectedLayerId) || null;
}

function uiCanvasSetTool(tool) {
    if (tool && tool !== 'select') {
        uiCanvasEnsureDraft();
        uiCanvasRender();
    }
    uiCanvasState.tool = tool || 'select';
    document.querySelectorAll('.ui-canvas-tool').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.uiCanvasTool === uiCanvasState.tool);
    });
}

function uiCanvasSetZoom(nextZoom) {
    uiCanvasState.zoom = Math.max(0.35, Math.min(2, Number(nextZoom) || 1));
    const viewport = document.getElementById('ui-canvas-viewport');
    if (viewport) viewport.style.transform = `scale(${uiCanvasState.zoom})`;
    const label = document.getElementById('ui-canvas-zoom-label');
    if (label) label.textContent = `${Math.round(uiCanvasState.zoom * 100)}%`;
}

function uiCanvasUpdateHeader() {
    document.getElementById('ui-canvas-title').textContent = uiCanvasState.doc?.name || 'Sem canvas selecionado';
    document.getElementById('ui-canvas-filepath').textContent = uiCanvasState.filepath || '.documents/canvas';
}

function uiCanvasRender() {
    const viewport = document.getElementById('ui-canvas-viewport');
    if (!viewport) return;
    uiCanvasUpdateHeader();
    if (!uiCanvasState.doc) {
        viewport.innerHTML = '<div class="ui-canvas-start-state">Crie ou selecione um canvas para começar.</div>';
        renderUiCanvasLayers();
        renderUiCanvasProperties();
        return;
    }

    uiCanvasAssignParents();
    uiCanvasApplyAutoLayouts();
    viewport.style.width = `${uiCanvasState.doc.viewport?.width || 2600}px`;
    viewport.style.height = `${uiCanvasState.doc.viewport?.height || 1800}px`;
    viewport.innerHTML = uiCanvasGetLayers().map(layer => uiCanvasLayerHtml(layer)).join('');
    viewport.querySelectorAll('.ui-canvas-layer').forEach(el => {
        el.addEventListener('pointerdown', uiCanvasLayerPointerDown);
    });
    viewport.querySelectorAll('.ui-canvas-resize-handle').forEach(el => {
        el.addEventListener('pointerdown', uiCanvasResizePointerDown);
    });
    renderUiCanvasLayers();
    renderUiCanvasProperties();
    if (window.lucide) lucide.createIcons();
}

function uiCanvasLayerHtml(layer) {
    const selected = layer.id === uiCanvasState.selectedLayerId ? ' is-selected' : '';
    const dimensions = uiCanvasGetRenderedDimensions(layer);
    const commonStyle = [
        `left:${layer.x}px`,
        `top:${layer.y}px`,
        `width:${dimensions.width}px`,
        `height:${dimensions.height}px`,
        `opacity:${layer.opacity ?? 1}`,
        `border-radius:${layer.radius || 0}px`,
        `border-color:${layer.stroke || 'transparent'}`
    ].join(';');

    if (['text', 'heading', 'paragraph', 'button', 'input', 'list', 'icon', 'image', 'video'].includes(layer.type)) {
        if (layer.type === 'icon') {
            return `<div class="ui-canvas-layer ui-canvas-layer-text ui-canvas-layer-icon${selected}" data-layer-id="${layer.id}" style="${commonStyle};background:${layer.fill || 'transparent'};color:${layer.color || '#f8fafc'};border-color:${layer.stroke || 'transparent'};"><i data-lucide="${escapeHtml(layer.icon || 'sparkles')}" style="width:${layer.fontSize || 24}px;height:${layer.fontSize || 24}px;"></i><span class="ui-canvas-resize-handle" data-layer-id="${layer.id}"></span></div>`;
        }
        const text = layer.type === 'list' ? escapeHtml(layer.text || '').replace(/\n/g, '<br>') : escapeHtml(layer.text || uiCanvasLayerLabel(layer.type));
        return `<div class="ui-canvas-layer ui-canvas-layer-text ui-canvas-layer-${layer.type}${selected}" data-layer-id="${layer.id}" style="${commonStyle};background:${layer.fill || 'transparent'};color:${layer.color || '#f8fafc'};font-size:${layer.fontSize || 16}px;font-weight:${layer.fontWeight || 600};border-color:${layer.stroke || 'transparent'};">${text}<span class="ui-canvas-resize-handle" data-layer-id="${layer.id}"></span></div>`;
    }
    if (layer.type === 'line' || layer.type === 'divider') {
        return `<div class="ui-canvas-layer ui-canvas-layer-line${selected}" data-layer-id="${layer.id}" style="left:${layer.x}px;top:${layer.y}px;width:${dimensions.width}px;height:${Math.max(2, dimensions.height || 2)}px;background:${layer.fill || '#f8fafc'};opacity:${layer.opacity ?? 1};"><span class="ui-canvas-resize-handle" data-layer-id="${layer.id}"></span></div>`;
    }
    if (layer.type === 'table') {
        return `<div class="ui-canvas-layer ui-canvas-layer-table${selected}" data-layer-id="${layer.id}" style="${commonStyle};background:${layer.fill || '#151518'};"><span class="ui-canvas-table-grid"></span><span class="ui-canvas-layer-name">${escapeHtml(layer.name || 'Table')}</span><span class="ui-canvas-resize-handle" data-layer-id="${layer.id}"></span></div>`;
    }
    const cls = layer.type === 'frame' ? 'ui-canvas-layer-frame' : layer.type === 'group' ? 'ui-canvas-layer-group' : 'ui-canvas-layer-rect';
    return `<div class="ui-canvas-layer ${cls}${selected}" data-layer-id="${layer.id}" style="${commonStyle};background:${layer.fill || 'transparent'};"><span class="ui-canvas-layer-name">${escapeHtml(layer.name || layer.type)}</span><span class="ui-canvas-resize-handle" data-layer-id="${layer.id}"></span></div>`;
}

function uiCanvasGetParentLayer(layer) {
    return layer?.parentId ? uiCanvasGetLayers().find(item => item.id === layer.parentId) || null : null;
}

function uiCanvasGetAutoDimension(layer, axis) {
    if (layer.type === 'line' || layer.type === 'divider') return axis === 'width' ? Number(layer.width || 220) : 2;
    if (layer.type === 'icon') {
        const size = Math.max(24, Number(layer.fontSize || 24) + 20);
        return size;
    }
    if (['heading', 'paragraph', 'text', 'button', 'input', 'list'].includes(layer.type)) {
        const text = String(layer.text || uiCanvasLayerLabel(layer.type));
        const lines = text.split('\n');
        const longest = Math.max(...lines.map(line => line.length), 1);
        const fontSize = Number(layer.fontSize || 16);
        if (axis === 'width') return Math.max(48, Math.round(longest * fontSize * 0.58) + 24);
        return Math.max(24, Math.round(lines.length * fontSize * 1.45) + 16);
    }
    return axis === 'width' ? Number(layer.width || 180) : Number(layer.height || 96);
}

function uiCanvasGetFullDimension(layer, axis) {
    const parent = uiCanvasGetParentLayer(layer);
    if (!parent) return axis === 'width' ? Number(layer.width || 180) : Number(layer.height || 96);
    const parentDimensions = uiCanvasGetRenderedDimensions(parent);
    const offset = axis === 'width' ? layer.x - parent.x : layer.y - parent.y;
    const fallback = axis === 'width' ? Number(layer.width || 180) : Number(layer.height || 96);
    return Math.max(12, Math.round(parentDimensions[axis] - Math.max(0, offset) - 16)) || fallback;
}

function uiCanvasGetRenderedDimensions(layer) {
    const widthMode = layer.widthMode || 'fixed';
    const heightMode = layer.heightMode || 'fixed';
    return {
        width: widthMode === 'auto' ? uiCanvasGetAutoDimension(layer, 'width') : widthMode === 'full' ? uiCanvasGetFullDimension(layer, 'width') : Number(layer.width || 0),
        height: heightMode === 'auto' ? uiCanvasGetAutoDimension(layer, 'height') : heightMode === 'full' ? uiCanvasGetFullDimension(layer, 'height') : Number(layer.height || 0)
    };
}

function renderUiCanvasLayers() {
    const list = document.getElementById('ui-canvas-layer-list');
    if (!list) return;
    const layers = uiCanvasGetLayers();
    if (!layers.length) {
        list.innerHTML = '<div class="ui-canvas-empty">Nenhum layer.</div>';
        return;
    }
    uiCanvasAssignParents();
    const tree = uiCanvasBuildLayerTree();
    list.innerHTML = tree.map(node => uiCanvasLayerTreeHtml(node)).join('');
    list.querySelectorAll('.ui-canvas-layer-item').forEach(btn => {
        btn.addEventListener('click', () => {
            uiCanvasState.selectedLayerId = btn.dataset.layerId;
            uiCanvasRender();
        });
    });
    if (window.lucide) lucide.createIcons();
}

function uiCanvasLayerIcon(type) {
    const icons = {
        text: 'type',
        heading: 'heading-1',
        paragraph: 'pilcrow',
        button: 'rectangle-ellipsis',
        input: 'text-cursor-input',
        frame: 'scan',
        group: 'folder',
        section: 'layout',
        line: 'minus',
        divider: 'separator-horizontal',
        table: 'table',
        list: 'list',
        icon: 'sparkles',
        image: 'image',
        video: 'video',
        card: 'panel-top',
        rect: 'square'
    };
    return icons[type] || 'square';
}

function uiCanvasLayerTreeHtml(node, depth = 0) {
    const layer = node.layer;
    const children = node.children || [];
    return `
        <div class="ui-canvas-tree-node">
            <button class="ui-canvas-layer-item ${layer.id === uiCanvasState.selectedLayerId ? 'active' : ''}" data-layer-id="${layer.id}" style="--tree-depth:${depth}">
                <i data-lucide="${uiCanvasLayerIcon(layer.type)}"></i>
                <span>${escapeHtml(layer.name || uiCanvasLayerLabel(layer.type))}</span>
            </button>
            ${children.length ? `<div class="ui-canvas-tree-children">${children.map(child => uiCanvasLayerTreeHtml(child, depth + 1)).join('')}</div>` : ''}
        </div>
    `;
}

function uiCanvasLayerContains(parent, child) {
    if (!['frame', 'group'].includes(parent.type) || parent.id === child.id) return false;
    const parentDimensions = uiCanvasGetRenderedDimensions(parent);
    const childDimensions = uiCanvasGetRenderedDimensions(child);
    const parentArea = parentDimensions.width * parentDimensions.height;
    const childArea = childDimensions.width * childDimensions.height;
    if (parentArea <= childArea) return false;
    return child.x >= parent.x
        && child.y >= parent.y
        && child.x + childDimensions.width <= parent.x + parentDimensions.width
        && child.y + childDimensions.height <= parent.y + parentDimensions.height;
}

function uiCanvasAssignParents() {
    const layers = uiCanvasGetLayers();
    layers.forEach(layer => {
        const candidates = layers
            .filter(parent => uiCanvasLayerContains(parent, layer))
            .sort((a, b) => (a.width * a.height) - (b.width * b.height));
        layer.parentId = candidates[0]?.id || null;
    });
}

function uiCanvasBuildLayerTree() {
    const layers = uiCanvasGetLayers();
    const nodeById = new Map(layers.map(layer => [layer.id, { layer, children: [] }]));
    const roots = [];
    layers.forEach(layer => {
        const node = nodeById.get(layer.id);
        if (layer.parentId && nodeById.has(layer.parentId)) {
            nodeById.get(layer.parentId).children.push(node);
        } else {
            roots.push(node);
        }
    });
    const sortNodes = nodes => nodes
        .sort((a, b) => uiCanvasGetLayers().indexOf(b.layer) - uiCanvasGetLayers().indexOf(a.layer))
        .map(node => ({ ...node, children: sortNodes(node.children) }));
    return sortNodes(roots);
}

function uiCanvasApplyAutoLayouts() {
    const layers = uiCanvasGetLayers();
    const containers = layers.filter(layer => ['frame', 'group'].includes(layer.type) && layer.autoLayout?.enabled);
    containers.forEach(container => {
        const layout = container.autoLayout || {};
        const children = layers
            .filter(layer => layer.parentId === container.id)
            .sort((a, b) => (a.y - b.y) || (a.x - b.x));
        let cursor = Number(layout.padding ?? 16);
        const padding = Number(layout.padding ?? 16);
        const gap = Number(layout.gap ?? 12);
        children.forEach(child => {
            const childDimensions = uiCanvasGetRenderedDimensions(child);
            if (layout.direction === 'horizontal') {
                child.x = Math.round(container.x + cursor);
                child.y = Math.round(container.y + padding);
                cursor += childDimensions.width + gap;
            } else {
                child.x = Math.round(container.x + padding);
                child.y = Math.round(container.y + cursor);
                cursor += childDimensions.height + gap;
            }
        });
    });
}

function renderUiCanvasProperties() {
    const form = document.getElementById('ui-canvas-property-form');
    const label = document.getElementById('ui-canvas-selected-label');
    if (!form) return;
    const layer = uiCanvasGetSelectedLayer();
    if (label) label.textContent = layer ? layer.name : 'Nenhum layer';
    if (!layer) {
        form.innerHTML = '<div class="ui-canvas-empty">Selecione um elemento no canvas.</div>';
        return;
    }
    const textTypes = ['text', 'heading', 'paragraph', 'button', 'input', 'list', 'image', 'video'];
    const hasText = textTypes.includes(layer.type);
    const hasAutoLayout = ['frame', 'group'].includes(layer.type);
    form.innerHTML = `
        ${uiCanvasField('name', 'Nome', layer.name || '')}
        ${hasText ? uiCanvasField('text', 'Texto', layer.text || '') : ''}
        ${layer.type === 'icon' ? uiCanvasIconSelect(layer) : ''}
        <div class="ui-canvas-grid-2">
            ${uiCanvasField('x', 'X', layer.x, 'number')}
            ${uiCanvasField('y', 'Y', layer.y, 'number')}
        </div>
        ${uiCanvasDimensionControls(layer)}
        <div class="ui-canvas-grid-2">
            ${uiCanvasField('fill', 'Fill', layer.fill || '#1f1f22', 'color')}
            ${uiCanvasField('stroke', 'Borda', layer.stroke || '#2d2d31', 'color')}
        </div>
        ${hasText ? `<div class="ui-canvas-grid-2">${uiCanvasField('color', 'Cor', layer.color || '#f8fafc', 'color')}${uiCanvasField('fontSize', 'Font size', layer.fontSize || 16, 'number')}</div>` : ''}
        <div class="ui-canvas-grid-2">
            ${uiCanvasField('radius', 'Radius', layer.radius || 0, 'number')}
            ${uiCanvasField('opacity', 'Opacity', layer.opacity ?? 1, 'number', '0.1')}
        </div>
        ${hasText ? uiCanvasField('fontWeight', 'Peso', layer.fontWeight || 600, 'number') : ''}
        ${hasAutoLayout ? uiCanvasAutoLayoutFields(layer) : ''}
        ${uiCanvasField('token', 'Token aplicado', layer.token || '', 'text', '', 'ex: color.surface.card')}
        <button class="btn btn-secondary btn-sm" id="btn-ui-canvas-delete-layer"><i data-lucide="trash-2"></i> Remover layer</button>
    `;
    form.querySelectorAll('[data-ui-prop]').forEach(input => {
        input.addEventListener('change', () => uiCanvasUpdateLayerProp(input.dataset.uiProp, input.value, input.type));
    });
    form.querySelectorAll('[data-ui-dimension-mode]').forEach(input => {
        input.addEventListener('change', () => uiCanvasUpdateLayerProp(`${input.dataset.uiDimensionMode}Mode`, input.value, input.type));
    });
    form.querySelectorAll('[data-ui-autolayout]').forEach(input => {
        input.addEventListener('change', () => uiCanvasUpdateAutoLayoutProp(input.dataset.uiAutolayout, input.type === 'checkbox' ? input.checked : input.value));
    });
    document.getElementById('btn-ui-canvas-delete-layer')?.addEventListener('click', uiCanvasDeleteSelectedLayer);
    if (window.lucide) lucide.createIcons();
}

function uiCanvasDimensionControls(layer) {
    return `
        <div class="ui-canvas-dimensions">
            <label class="ui-canvas-field">
                <span>Width</span>
                <div class="ui-canvas-dimension-control">
                    <input class="text-input" data-ui-prop="width" type="number" value="${escapeHtml(String(layer.width ?? 0))}">
                    ${uiCanvasDimensionModeSelect('width', layer.widthMode || 'fixed')}
                </div>
            </label>
            <label class="ui-canvas-field">
                <span>Height</span>
                <div class="ui-canvas-dimension-control">
                    <input class="text-input" data-ui-prop="height" type="number" value="${escapeHtml(String(layer.height ?? 0))}">
                    ${uiCanvasDimensionModeSelect('height', layer.heightMode || 'fixed')}
                </div>
            </label>
        </div>
    `;
}

function uiCanvasDimensionModeSelect(axis, value) {
    return `
        <select class="select-input ui-canvas-dimension-mode" data-ui-dimension-mode="${axis}">
            <option value="fixed" ${value === 'fixed' ? 'selected' : ''}>fixo</option>
            <option value="auto" ${value === 'auto' ? 'selected' : ''}>auto</option>
            <option value="full" ${value === 'full' ? 'selected' : ''}>full</option>
        </select>
    `;
}

function uiCanvasIconSelect(layer) {
    return `
        <label class="ui-canvas-field">
            <span>Ícone Lucide</span>
            <select class="select-input" data-ui-prop="icon">
                ${UI_CANVAS_ICON_OPTIONS.map(icon => `<option value="${escapeHtml(icon)}" ${(layer.icon || 'sparkles') === icon ? 'selected' : ''}>${escapeHtml(icon)}</option>`).join('')}
            </select>
        </label>
    `;
}

function uiCanvasAutoLayoutFields(layer) {
    const layout = layer.autoLayout || { enabled: false, direction: 'vertical', gap: 12, padding: 16 };
    return `
        <div class="ui-canvas-property-group">
            <div class="ui-canvas-section-title">Auto layout</div>
            <label class="ui-canvas-checkbox-field">
                <input type="checkbox" data-ui-autolayout="enabled" ${layout.enabled ? 'checked' : ''}>
                <span>Ativar auto layout</span>
            </label>
            <label class="ui-canvas-field">
                <span>Direção</span>
                <select class="select-input" data-ui-autolayout="direction">
                    <option value="vertical" ${layout.direction === 'vertical' ? 'selected' : ''}>Vertical</option>
                    <option value="horizontal" ${layout.direction === 'horizontal' ? 'selected' : ''}>Horizontal</option>
                </select>
            </label>
            <div class="ui-canvas-grid-2">
                ${uiCanvasField('autoLayout.gap', 'Gap', layout.gap ?? 12, 'number')}
                ${uiCanvasField('autoLayout.padding', 'Padding', layout.padding ?? 16, 'number')}
            </div>
        </div>
    `;
}

function uiCanvasField(prop, label, value, type = 'text', step = '', placeholder = '') {
    return `<label class="ui-canvas-field"><span>${label}</span><input class="text-input" data-ui-prop="${prop}" type="${type}" ${step ? `step="${step}"` : ''} value="${escapeHtml(String(value ?? ''))}" placeholder="${escapeHtml(placeholder)}"></label>`;
}

function uiCanvasUpdateLayerProp(prop, value, inputType) {
    const layer = uiCanvasGetSelectedLayer();
    if (!layer) return;
    const numeric = ['x', 'y', 'width', 'height', 'radius', 'opacity', 'fontSize', 'fontWeight'];
    if (prop.startsWith('autoLayout.')) {
        layer.autoLayout = layer.autoLayout || { enabled: false, direction: 'vertical', gap: 12, padding: 16 };
        const key = prop.split('.')[1];
        layer.autoLayout[key] = Number(value);
    } else {
        layer[prop] = numeric.includes(prop) ? Number(value) : value;
        if (prop === 'width') layer.widthMode = 'fixed';
        if (prop === 'height') layer.heightMode = 'fixed';
    }
    uiCanvasAssignParents();
    uiCanvasState.doc.updatedAt = new Date().toISOString();
    uiCanvasRender();
}

function uiCanvasUpdateAutoLayoutProp(prop, value) {
    const layer = uiCanvasGetSelectedLayer();
    if (!layer) return;
    layer.autoLayout = layer.autoLayout || { enabled: false, direction: 'vertical', gap: 12, padding: 16 };
    layer.autoLayout[prop] = prop === 'enabled' ? Boolean(value) : value;
    uiCanvasAssignParents();
    uiCanvasState.doc.updatedAt = new Date().toISOString();
    uiCanvasRender();
}

function uiCanvasDeleteSelectedLayer() {
    if (!uiCanvasState.doc || !uiCanvasState.selectedLayerId) return;
    const selectedId = uiCanvasState.selectedLayerId;
    const idsToRemove = new Set([selectedId]);
    let changed = true;
    while (changed) {
        changed = false;
        uiCanvasGetLayers().forEach(layer => {
            if (layer.parentId && idsToRemove.has(layer.parentId) && !idsToRemove.has(layer.id)) {
                idsToRemove.add(layer.id);
                changed = true;
            }
        });
    }
    uiCanvasState.doc.layers = uiCanvasGetLayers().filter(layer => !idsToRemove.has(layer.id));
    uiCanvasState.selectedLayerId = null;
    uiCanvasRender();
}

async function loadUiCanvasFiles() {
    if (!state.activeProjectId) return;
    const list = document.getElementById('ui-canvas-file-list');
    if (list) list.innerHTML = '<div class="ui-canvas-empty">Carregando...</div>';
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/files`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao listar arquivos');
        uiCanvasState.files = (data.files || [])
            .filter(file => file.path?.startsWith('.documents/canvas/') && file.path.endsWith('.canvas.json'))
            .sort((a, b) => a.path.localeCompare(b.path));
        renderUiCanvasFileList();
    } catch (err) {
        if (list) list.innerHTML = `<div class="ui-canvas-empty is-error">${escapeHtml(err.message)}</div>`;
    }
}

function renderUiCanvasFileList() {
    const list = document.getElementById('ui-canvas-file-list');
    if (!list) return;
    if (!uiCanvasState.files.length) {
        list.innerHTML = '<div class="ui-canvas-empty">Nenhum canvas encontrado.</div>';
        return;
    }
    list.innerHTML = uiCanvasState.files.map(file => {
        const name = file.path.split('/').pop().replace('.canvas.json', '');
        return `<button class="ui-canvas-file-item ${file.path === uiCanvasState.filepath ? 'active' : ''}" data-filepath="${escapeHtml(file.path)}"><i data-lucide="file-json"></i><span>${escapeHtml(name)}</span></button>`;
    }).join('');
    list.querySelectorAll('.ui-canvas-file-item').forEach(btn => btn.addEventListener('click', () => loadUiCanvasDocument(btn.dataset.filepath)));
    if (window.lucide) lucide.createIcons();
}

async function loadUiCanvasDocument(filepath) {
    if (!state.activeProjectId || !filepath) return;
    const res = await fetch(`/api/projects/${state.activeProjectId}/files/read?filepath=${encodeURIComponent(filepath)}`, { headers: getHeaders() });
    const data = await res.json();
    if (!res.ok) {
        gitideNotify({ title: 'Erro ao abrir canvas', message: data.detail || 'Arquivo não encontrado.', variant: 'danger' });
        return;
    }
    try {
        uiCanvasState.doc = JSON.parse(data.content || '{}');
        uiCanvasState.filepath = filepath;
        uiCanvasState.selectedLayerId = null;
        uiCanvasRender();
        renderUiCanvasFileList();
    } catch (err) {
        gitideNotify({ title: 'Canvas inválido', message: err.message, variant: 'danger' });
    }
}

function newUiCanvasDocument() {
    const stamp = new Date();
    const name = `Nova Tela ${stamp.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`;
    uiCanvasState.doc = uiCanvasCreateDocument(name);
    uiCanvasState.filepath = `.documents/canvas/${uiCanvasSlug(name)}.canvas.json`;
    uiCanvasState.selectedLayerId = null;
    uiCanvasSetTool('select');
    uiCanvasRender();
    renderUiCanvasFileList();
}

async function saveUiCanvasDocument() {
    if (!state.activeProjectId || !uiCanvasState.doc) return;
    uiCanvasState.doc.updatedAt = new Date().toISOString();
    const res = await fetch(`/api/projects/${state.activeProjectId}/files/write`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
            filepath: uiCanvasState.filepath,
            content: JSON.stringify(uiCanvasState.doc, null, 2)
        })
    });
    const data = await res.json();
    if (!res.ok) {
        gitideNotify({ title: 'Erro ao salvar canvas', message: data.detail || 'Falha ao salvar.', variant: 'danger' });
        return;
    }
    gitideNotify({ title: 'Canvas salvo', message: uiCanvasState.filepath, variant: 'success' });
    await loadUiCanvasFiles();
}

function uiCanvasExportJson() {
    if (!uiCanvasState.doc) return;
    navigator.clipboard.writeText(JSON.stringify(uiCanvasState.doc, null, 2));
    gitideNotify({ title: 'JSON copiado', message: 'Arquivo do canvas copiado para a área de transferência.', variant: 'success' });
}

function uiCanvasStagePoint(event) {
    const viewport = document.getElementById('ui-canvas-viewport');
    const rect = viewport.getBoundingClientRect();
    return {
        x: (event.clientX - rect.left) / uiCanvasState.zoom,
        y: (event.clientY - rect.top) / uiCanvasState.zoom
    };
}

function uiCanvasStagePointerDown(event) {
    if (event.target.closest('.ui-canvas-layer')) return;
    uiCanvasEnsureDraft();
    const point = uiCanvasStagePoint(event);
    if (uiCanvasState.tool === 'select') {
        uiCanvasState.selectedLayerId = null;
        uiCanvasRender();
        return;
    }
    const layer = uiCanvasDefaultLayer(uiCanvasState.tool, point.x, point.y);
    uiCanvasState.doc.layers.push(layer);
    uiCanvasState.selectedLayerId = layer.id;
    uiCanvasSetTool('select');
    uiCanvasRender();
}

function uiCanvasLayerPointerDown(event) {
    event.stopPropagation();
    if (event.target.classList.contains('ui-canvas-resize-handle')) return;
    const id = event.currentTarget.dataset.layerId;
    const layer = uiCanvasGetLayers().find(item => item.id === id);
    if (!layer) return;
    uiCanvasState.selectedLayerId = id;
    const point = uiCanvasStagePoint(event);
    uiCanvasState.drag = { id, offsetX: point.x - layer.x, offsetY: point.y - layer.y };
    event.currentTarget.setPointerCapture?.(event.pointerId);
    uiCanvasRender();
}

function uiCanvasResizePointerDown(event) {
    event.stopPropagation();
    const id = event.currentTarget.dataset.layerId;
    const layer = uiCanvasGetLayers().find(item => item.id === id);
    if (!layer) return;
    uiCanvasState.selectedLayerId = id;
    const point = uiCanvasStagePoint(event);
    uiCanvasState.resize = { id, startX: point.x, startY: point.y, width: layer.width, height: layer.height };
}

function uiCanvasPointerMove(event) {
    if (uiCanvasState.drag) {
        const layer = uiCanvasGetLayers().find(item => item.id === uiCanvasState.drag.id);
        if (!layer) return;
        const point = uiCanvasStagePoint(event);
        layer.x = Math.round(point.x - uiCanvasState.drag.offsetX);
        layer.y = Math.round(point.y - uiCanvasState.drag.offsetY);
        uiCanvasRender();
    } else if (uiCanvasState.resize) {
        const layer = uiCanvasGetLayers().find(item => item.id === uiCanvasState.resize.id);
        if (!layer) return;
        const point = uiCanvasStagePoint(event);
        layer.width = Math.max(12, Math.round(uiCanvasState.resize.width + point.x - uiCanvasState.resize.startX));
        layer.height = Math.max(layer.type === 'line' ? 2 : 12, Math.round(uiCanvasState.resize.height + point.y - uiCanvasState.resize.startY));
        layer.widthMode = 'fixed';
        layer.heightMode = 'fixed';
        uiCanvasRender();
    }
}

function uiCanvasPointerUp() {
    if (uiCanvasState.drag || uiCanvasState.resize) {
        if (uiCanvasState.doc) uiCanvasState.doc.updatedAt = new Date().toISOString();
        uiCanvasState.drag = null;
        uiCanvasState.resize = null;
        uiCanvasRender();
    }
}

// --- EVENT LISTENERS & UI EVENTS ---
function setupEventListeners() {
    // SDD Module
    setupSddEventListeners();
    initDiscoveryTab();

    document.getElementById('btn-sidebar-collapse')?.addEventListener('click', toggleSidebarCollapsed);
    document.getElementById('btn-auth-logout')?.addEventListener('click', logoutGitide);

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

    document.getElementById('btn-qa-refresh')?.addEventListener('click', loadQaAnnotations);
    document.getElementById('qa-status-filter')?.addEventListener('change', loadQaAnnotations);
    document.getElementById('qa-id-filter')?.addEventListener('input', renderQaAnnotations);
    document.getElementById('btn-qa-copy-extension-config')?.addEventListener('click', copyQaExtensionConfig);
    document.getElementById('btn-qa-export-pdf')?.addEventListener('click', () => exportQaAnnotations('pdf'));
    document.getElementById('btn-qa-export-xlsx')?.addEventListener('click', () => exportQaAnnotations('xlsx'));
    document.getElementById('btn-engineering-metrics-refresh')?.addEventListener('click', loadEngineeringMetrics);
    document.getElementById('engineering-metrics-period')?.addEventListener('change', loadEngineeringMetrics);
    document.getElementById('btn-estimation-generate')?.addEventListener('click', generateProjectEstimation);
    const refreshEstimationConfig = () => saveEstimationConfig()
        .then(loadEstimationPage)
        .catch(error => {
            gitideNotify({ title: 'Configuração da estimativa', message: error.message, variant: 'danger' });
        });
    document.getElementById('estimation-hourly-rate')?.addEventListener('change', refreshEstimationConfig);
    document.getElementById('estimation-daily-hours')?.addEventListener('change', refreshEstimationConfig);
    document.querySelectorAll('[data-estimation-mode]').forEach(btn => {
        btn.addEventListener('click', () => applyEstimationMode(btn.dataset.estimationMode));
    });
    document.querySelectorAll('[data-estimation-view]').forEach(btn => {
        btn.addEventListener('click', () => applyEstimationView(btn.dataset.estimationView));
    });
    document.querySelectorAll('.engineering-tab').forEach(btn => {
        btn.addEventListener('click', () => setEngineeringPanel(btn.dataset.engineeringPanel));
    });
    document.querySelectorAll('[data-engineering-report-refresh]').forEach(btn => {
        btn.addEventListener('click', () => loadEngineeringReport(btn.dataset.engineeringReportRefresh));
    });
    document.querySelectorAll('[data-engineering-report-open]').forEach(btn => {
        btn.addEventListener('click', () => openEngineeringReportFile(btn.dataset.engineeringReportOpen));
    });
    document.getElementById('btn-ui-canvas-refresh')?.addEventListener('click', loadUiCanvasFiles);
    document.getElementById('btn-ui-canvas-new')?.addEventListener('click', newUiCanvasDocument);
    document.getElementById('btn-ui-canvas-save')?.addEventListener('click', saveUiCanvasDocument);
    document.getElementById('btn-ui-canvas-export-json')?.addEventListener('click', uiCanvasExportJson);
    document.getElementById('btn-ui-canvas-zoom-in')?.addEventListener('click', () => uiCanvasSetZoom(uiCanvasState.zoom + 0.1));
    document.getElementById('btn-ui-canvas-zoom-out')?.addEventListener('click', () => uiCanvasSetZoom(uiCanvasState.zoom - 0.1));
    document.querySelectorAll('.ui-canvas-tool').forEach(btn => {
        btn.addEventListener('click', () => uiCanvasSetTool(btn.dataset.uiCanvasTool));
    });
    document.getElementById('ui-canvas-frame-preset')?.addEventListener('change', () => uiCanvasSetTool('frame'));
    document.getElementById('ui-canvas-element-preset')?.addEventListener('change', (event) => {
        const type = event.target.value;
        if (!type) return;
        uiCanvasSetTool(type);
        event.target.value = '';
    });
    document.getElementById('ui-canvas-viewport')?.addEventListener('pointerdown', uiCanvasStagePointerDown);
    document.addEventListener('pointermove', uiCanvasPointerMove);
    document.addEventListener('pointerup', uiCanvasPointerUp);
    document.querySelectorAll('.qa-view-tab').forEach(btn => {
        btn.addEventListener('click', () => setQaView(btn.dataset.qaView));
    });
    document.getElementById('btn-qa-detail-close')?.addEventListener('click', closeQaAnnotationDrawer);
    document.getElementById('qa-drawer-backdrop')?.addEventListener('click', closeQaAnnotationDrawer);
    
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
        const projectName = state.activeProject?.name || 'projeto selecionado';
        const projectPath = state.activeProject?.path || 'caminho não informado';
        
        const confirmed = await showCustomConfirm(
            'Excluir Projeto',
            `Tem certeza que deseja excluir o projeto "${escapeHtml(projectName)}"?<br><br>Essa ação removerá o cadastro, logs e todos os arquivos da pasta do projeto na máquina:<br><strong>${escapeHtml(projectPath)}</strong>`,
            'Continuar',
            true
        );
        
        if (confirmed) {
            const finalConfirmed = await showCustomConfirm(
                'Confirmação final',
                `Esta é a última confirmação. Ao continuar, a pasta do projeto "${escapeHtml(projectName)}" será excluída completamente do disco e não ficará resquício local do workspace.`,
                'Excluir tudo',
                true
            );
            if (!finalConfirmed) return;

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
                    alert(`Erro ao excluir projeto: ${data.detail || 'Tente novamente.'}`);
                }
            } catch (err) {
                alert(`Falha na conexão: ${err.message}`);
            }
        }
    });
    
    // 3.8. Copiar ID e instruções para o GPT
    document.getElementById('btn-copy-project-gpt-info').addEventListener('click', () => {
        if (!state.activeProject) return;
        const infoText = `Olá! O projeto ativo no qual estamos trabalhando no Act IA é "${state.activeProject.name}" (ID do projeto: ${state.activeProjectId}). Por favor, use sempre o ID de projeto "${state.activeProjectId}" em todas as chamadas de API (como no path /api/projects/${state.activeProjectId}/...).`;
        
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
    document.getElementById('btn-new-workspace-file')?.addEventListener('click', openWorkspaceNewFileModal);
    document.getElementById('btn-export-workspace-zip')?.addEventListener('click', exportWorkspaceZip);
    document.getElementById('btn-workspace-create-file')?.addEventListener('click', createWorkspaceFileFromModal);
    document.querySelectorAll('.workspace-new-file-close').forEach(btn => {
        btn.addEventListener('click', closeWorkspaceNewFileModal);
    });
    document.getElementById('btn-workspace-confirm-delete')?.addEventListener('click', deleteWorkspaceItemFromModal);
    document.getElementById('workspace-delete-confirm-input')?.addEventListener('input', updateWorkspaceDeleteConfirmState);
    document.getElementById('workspace-delete-confirm-input')?.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !document.getElementById('btn-workspace-confirm-delete')?.disabled) {
            event.preventDefault();
            deleteWorkspaceItemFromModal();
        }
    });
    document.querySelectorAll('.workspace-delete-close').forEach(btn => {
        btn.addEventListener('click', closeWorkspaceDeleteModal);
    });
    document.getElementById('workspace-new-file-path')?.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            createWorkspaceFileFromModal();
        }
    });
    document.getElementById('workspace-new-file-content')?.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
            event.preventDefault();
            createWorkspaceFileFromModal();
        }
    });
    
    // Inicialização do CodeMirror (Editor de código)
    const editorTextarea = document.getElementById('file-editor-textarea');
    const editorGutter = document.getElementById('editor-gutter');
    if (editorTextarea) {
        if (editorGutter) editorGutter.style.display = 'none';
        
        window.cmEditor = CodeMirror.fromTextArea(editorTextarea, {
            mode: 'markdown',
            theme: 'darcula',
            lineNumbers: true,
            lineWrapping: true
        });
        
        // Override textarea properties to proxy to CodeMirror
        Object.defineProperty(editorTextarea, 'value', {
            get: function() { return window.cmEditor.getValue(); },
            set: function(val) { window.cmEditor.setValue(val); }
        });
        
        Object.defineProperty(editorTextarea, 'disabled', {
            get: function() { return window.cmEditor.getOption('readOnly') !== false; },
            set: function(val) { window.cmEditor.setOption('readOnly', val ? 'nocursor' : false); }
        });
        
        // Substitui a função original para evitar conflitos, já que o CM cuida dos números de linha
        window.updateLineNumbers = function() {};
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

    initDbTypeSelectShell();

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
    document.getElementById('btn-gitignore-refresh')?.addEventListener('click', loadGitignore);
    document.getElementById('btn-gitignore-add')?.addEventListener('click', () => {
        addGitignoreEntry(document.getElementById('gitignore-entry-input')?.value || '');
    });
    document.getElementById('gitignore-entry-input')?.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            addGitignoreEntry(event.currentTarget.value);
        }
    });
    document.querySelectorAll('[data-gitignore-preset]').forEach(button => {
        button.addEventListener('click', () => addGitignoreEntry(button.dataset.gitignorePreset));
    });
    document.querySelectorAll('.git-side-tab').forEach(tab => {
        tab.addEventListener('click', () => switchGitSidePanelTab(tab.dataset.gitSideTab));
    });
    switchGitSidePanelTab('console');
    document.getElementById('btn-git-init').addEventListener('click', initGitRepo);
    document.getElementById('btn-git-deploy').addEventListener('click', runGitDeploy);
    document.getElementById('btn-git-commit-ai').addEventListener('click', generateGitCommitMessage);
    document.getElementById('btn-git-pull').addEventListener('click', runGitPull);
    document.getElementById('btn-git-push').addEventListener('click', runGitPush);
    document.getElementById('btn-git-merge').addEventListener('click', openMergeModal);
    document.getElementById('btn-git-pr').addEventListener('click', openPRModal);
    document.getElementById('btn-git-abort-merge').addEventListener('click', runGitAbortMerge);
    document.getElementById('btn-git-conflicts-refresh').addEventListener('click', loadGitConflicts);
    document.getElementById('btn-git-conflict-save-file').addEventListener('click', applyGitConflictResolutions);
    document.getElementById('btn-git-conflicts-abort').addEventListener('click', runGitAbortMerge);
    
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
    document.getElementById('btn-git-checkout-inline')?.addEventListener('click', openCheckoutModal);

    
    // 7.5. Ações do Design System (Tokens)
    document.getElementById('btn-add-token-set').addEventListener('click', openCreateSetModal);
    document.getElementById('btn-add-token-theme')?.addEventListener('click', openCreateThemeModal);
    
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
    
    // 8. Logs
    document.getElementById('btn-refresh-logs').addEventListener('click', loadActivityLogs);
    document.getElementById('btn-refresh-all-snapshots').addEventListener('click', loadAllSnapshots);

    // Ops Infra
    document.getElementById('btn-ops-detect')?.addEventListener('click', opsInfraDetect);
    document.getElementById('btn-ops-plan')?.addEventListener('click', opsInfraPlan);
    document.getElementById('btn-ops-artifacts')?.addEventListener('click', opsInfraGenerateArtifacts);
    document.getElementById('btn-ops-artifacts-deploy')?.addEventListener('click', opsInfraGenerateArtifacts);
    document.getElementById('btn-ops-env-add')?.addEventListener('click', () => opsInfraAddEnvVariable());
    document.getElementById('btn-ops-env-save')?.addEventListener('click', opsInfraSaveEnv);
    document.getElementById('btn-ops-env-validate')?.addEventListener('click', opsInfraValidateEnv);
    document.getElementById('ops-env-select')?.addEventListener('change', opsInfraLoadEnv);
    document.getElementById('ops-vm-auth-method')?.addEventListener('change', syncOpsVmAuthFields);
    document.getElementById('btn-ops-vm-generate-key')?.addEventListener('click', opsInfraGenerateVmKey);
    document.getElementById('btn-ops-vm-copy-public-key')?.addEventListener('click', opsInfraCopyPublicKey);
    document.getElementById('btn-ops-vm-browse')?.addEventListener('click', () => opsInfraBrowseVmPath());
    document.getElementById('btn-ops-vm-parent')?.addEventListener('click', () => opsInfraBrowseVmPath(state.opsVmBrowserParent || '/'));
    document.getElementById('btn-ops-vm-use-path')?.addEventListener('click', opsInfraUseVmBrowserPath);
    document.getElementById('btn-ops-vm-create-dir')?.addEventListener('click', opsInfraCreateVmDirectory);
    document.getElementById('btn-ops-vm-test')?.addEventListener('click', opsInfraTestVmAccess);
    document.getElementById('btn-ops-bootstrap')?.addEventListener('click', opsInfraBootstrapVm);
    document.getElementById('btn-ops-sync')?.addEventListener('click', opsInfraSyncProject);
    document.getElementById('btn-ops-dns-check')?.addEventListener('click', opsInfraCheckDns);
    document.getElementById('btn-ops-health')?.addEventListener('click', opsInfraHealthCheck);
    document.getElementById('btn-ops-db-check')?.addEventListener('click', opsInfraCheckDatabase);
    document.getElementById('btn-ops-copy-gpt-action')?.addEventListener('click', async () => {
        const text = buildOpsInfraGptActionPrompt();
        await navigator.clipboard.writeText(text);
        const target = document.getElementById('ops-gpt-action-prompt');
        if (target) target.textContent = text;
        gitideNotify({ title: 'Prompt Ops copiado', message: 'Cole no GPT Action operador da VM/aplicação.', variant: 'success' });
    });
    document.getElementById('btn-ops-caddy-preview')?.addEventListener('click', opsInfraCaddyPreview);
    document.getElementById('btn-ops-caddy-apply')?.addEventListener('click', opsInfraCaddyApply);
    document.querySelectorAll('.ops-flow-tab').forEach(btn => {
        btn.addEventListener('click', () => opsInfraSwitchFlowTab(btn.dataset.opsFlowTab));
    });
    document.querySelectorAll('[data-ops-command]').forEach(btn => {
        btn.addEventListener('click', () => opsInfraRunCommand(btn.dataset.opsCommand));
    });
    
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

    const copyProdValidatorBtn = document.getElementById('btn-copy-prod-readiness-validator');
    if (copyProdValidatorBtn) {
        copyProdValidatorBtn.addEventListener('click', async () => {
            await loadProdReadinessValidator();
            const text = document.getElementById('prod-readiness-validator-text')?.textContent || '';
            navigator.clipboard.writeText(text).then(() => {
                const originalText = copyProdValidatorBtn.innerHTML;
                copyProdValidatorBtn.innerHTML = '<i class="fa-solid fa-check"></i> Copiado!';
                setTimeout(() => {
                    copyProdValidatorBtn.innerHTML = originalText;
                }, 1500);
            });
        });
    }

    const copySecurityRulesBtn = document.getElementById('btn-copy-security-rules');
    if (copySecurityRulesBtn) {
        copySecurityRulesBtn.addEventListener('click', async () => {
            await loadSecurityRulesPrompt();
            const text = document.getElementById('security-rules-text')?.textContent || '';
            navigator.clipboard.writeText(text).then(() => {
                const originalText = copySecurityRulesBtn.innerHTML;
                copySecurityRulesBtn.innerHTML = '<i class="fa-solid fa-check"></i> Copiado!';
                setTimeout(() => {
                    copySecurityRulesBtn.innerHTML = originalText;
                }, 1500);
            });
        });
    }
    
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
    const btnRefreshOllamaModels = document.getElementById('btn-refresh-ollama-models');
    if (btnRefreshOllamaModels) {
        btnRefreshOllamaModels.addEventListener('click', () => loadOllamaInstalledModels(getSelectedOllamaModel()));
    }
    const ollamaModelSelect = document.getElementById('agent-ollama-model');
    if (ollamaModelSelect) {
        ollamaModelSelect.addEventListener('change', toggleOllamaCustomModel);
    }
    const ollamaUrlInput = document.getElementById('agent-ollama-url');
    if (ollamaUrlInput) {
        ollamaUrlInput.addEventListener('change', () => loadOllamaInstalledModels(getSelectedOllamaModel()));
    }
    const ollamaPerformanceSelect = document.getElementById('agent-ollama-performance');
    if (ollamaPerformanceSelect) {
        ollamaPerformanceSelect.addEventListener('change', applyOllamaPerformancePreset);
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
        btnAgentHistory.addEventListener('click', async () => {
            await loadAgentHistory(true);
            gitideNotify({
                title: 'Histórico carregado',
                message: `${state.agentChatMessages.length} mensagem(ns) em .documents/agent/history.json.`,
                variant: 'info'
            });
        });
    }
    
    const btnClearAgentChat = document.getElementById('btn-clear-agent-chat');
    if (btnClearAgentChat) {
        btnClearAgentChat.addEventListener('click', clearAgentHistory);
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
    const generateBusinessDocsBtn = document.getElementById('btn-generate-business-docs');
    if (generateBusinessDocsBtn) {
        generateBusinessDocsBtn.addEventListener('click', () => generateBusinessDocuments('all'));
    }
    const copyDocPromptBtn = document.getElementById('btn-copy-doc-prompt-instructions');
    if (copyDocPromptBtn) {
        copyDocPromptBtn.addEventListener('click', copyDocPromptInstructions);
    }
    
    // Inicializa suporte a menções via @
    setupChatMentions();
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
    const sourceBranchLabel = document.getElementById('merge-source-branch-name');
    const sourceInline = document.getElementById('merge-source-inline');
    const targetInline = document.getElementById('merge-target-inline');
    const confirmButton = document.getElementById('btn-merge-confirm');
    const updateMergePreview = () => {
        const source = selector.value || '...';
        const target = currentBranchLabel.textContent || '...';
        sourceBranchLabel.textContent = source;
        sourceInline.textContent = source;
        targetInline.textContent = target;
        confirmButton.textContent = source !== '...' && target !== '...' ? `Mesclar em ${target}` : 'Mesclar';
    };
    selector.onchange = updateMergePreview;
    
    // Clear and set loading state
    selector.innerHTML = '<option value="">Carregando branches...</option>';
    currentBranchLabel.textContent = '...';
    sourceBranchLabel.textContent = '...';
    sourceInline.textContent = '...';
    targetInline.textContent = '...';
    
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
                sourceBranchLabel.textContent = 'Nenhuma branch';
                sourceInline.textContent = 'Nenhuma branch';
                targetInline.textContent = current;
                return;
            }
            
            otherBranches.forEach(b => {
                const opt = document.createElement('option');
                opt.value = b;
                opt.textContent = b;
                selector.appendChild(opt);
            });
            selector.value = otherBranches[0] || '';
            updateMergePreview();
        } else {
            selector.innerHTML = '<option value="">Erro ao carregar lista de branches</option>';
            updateMergePreview();
        }
    })
    .catch(err => {
        console.error('Erro ao listar branches:', err);
        selector.innerHTML = '<option value="">Erro ao carregar lista de branches</option>';
        updateMergePreview();
    });
}

async function runGitMerge() {
    const branchSelect = document.getElementById('merge-branch-selector');
    const selectedBranch = branchSelect.value;
    const targetBranch = document.getElementById('merge-current-branch-name')?.textContent?.trim() || 'branch atual';
    
    if (!selectedBranch) {
        alert('Selecione uma branch válida para mesclar.');
        return;
    }
    
    closeCustomModal('modal-merge');
    
    appendGitConsole(`Iniciando mesclagem: "${selectedBranch}" -> "${targetBranch}"...`);
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/git/merge`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ branch: selectedBranch })
        });
        
        const data = await res.json();
        
        if (!res.ok) {
            const detail = normalizeGitErrorDetail(data.detail);
            appendGitConsole(`Erro ao mesclar branch: ${detail.message || 'Erro desconhecido'}`, true);
            await maybeLoadGitConflicts(detail);
            return;
        }
        
        appendGitConsole(`Branch "${selectedBranch}" mesclada com sucesso!\n\n${data.detail || ''}`);
        alert(`Mesclagem realizada com sucesso!`);
        loadGitStatus();
    } catch (err) {
        appendGitConsole(`Erro ao mesclar branch: ${err.message}`, true);
        await loadGitConflicts();
    }
}

// --- DESIGN SYSTEM (TOKENS) MANAGER ---

const COMPONENT_STATE_FIELDS = {
    hover: [
        { key: 'background', label: 'Background', placeholder: 'ex: rgba(255,255,255,.04)' },
        { key: 'border', label: 'Border', placeholder: 'ex: rgba(255,255,255,.16)' },
        { key: 'text', label: 'Text', placeholder: 'ex: #ffffff' },
        { key: 'shadow', label: 'Shadow', placeholder: 'ex: 0 8px 24px rgba(0,0,0,.18)' }
    ],
    focus: [
        { key: 'outline', label: 'Outline', placeholder: 'ex: none' },
        { key: 'ring', label: 'Ring', placeholder: 'ex: rgba(255,255,255,.42)' },
        { key: 'ringWidth', label: 'Ring width', placeholder: 'ex: 1px' },
        { key: 'offset', label: 'Offset', placeholder: 'ex: 2px' }
    ],
    active: [
        { key: 'background', label: 'Background', placeholder: 'ex: rgba(255,255,255,.08)' },
        { key: 'border', label: 'Border', placeholder: 'ex: rgba(255,255,255,.22)' },
        { key: 'text', label: 'Text', placeholder: 'ex: #ffffff' },
        { key: 'scale', label: 'Scale', placeholder: 'ex: .98' }
    ],
    disabled: [
        { key: 'opacity', label: 'Opacity', placeholder: 'ex: .45' },
        { key: 'cursor', label: 'Cursor', placeholder: 'ex: not-allowed' },
        { key: 'background', label: 'Background', placeholder: 'ex: rgba(255,255,255,.02)' },
        { key: 'text', label: 'Text', placeholder: 'ex: rgba(255,255,255,.38)' }
    ]
};

function createDefaultComponentStates() {
    return {
        hover: { background: 'rgba(255,255,255,.04)', border: 'rgba(255,255,255,.16)', text: '#ffffff', shadow: 'none' },
        focus: { outline: 'none', ring: 'rgba(255,255,255,.42)', ringWidth: '1px', offset: '2px' },
        active: { background: 'rgba(255,255,255,.08)', border: 'rgba(255,255,255,.22)', text: '#ffffff', scale: '.98' },
        disabled: { opacity: '.45', cursor: 'not-allowed', background: 'rgba(255,255,255,.02)', text: 'rgba(255,255,255,.38)' }
    };
}

function createDefaultGlobalTokenSet() {
    return {
        $componentStates: createDefaultComponentStates()
    };
}

function ensureGlobalComponentStates() {
    if (!state.designTokens) return;
    if (!state.designTokens.global) {
        state.designTokens.global = createDefaultGlobalTokenSet();
        return;
    }
    const defaults = createDefaultComponentStates();
    const current = state.designTokens.global.$componentStates || {};
    Object.keys(defaults).forEach(stateName => {
        current[stateName] = { ...defaults[stateName], ...(current[stateName] || {}) };
    });
    state.designTokens.global.$componentStates = current;
}

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
                "global": createDefaultGlobalTokenSet(),
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
            if (!state.designTokens.global) {
                state.designTokens.global = createDefaultGlobalTokenSet();
            } else {
                ensureGlobalComponentStates();
            }

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
            <select id="select-active-theme" class="select-input">
                ${options}
            </select>
            <button class="btn btn-secondary btn-sm" id="btn-edit-active-theme">EDITAR</button>
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
    
    let html = activeSet === 'global' ? renderGlobalComponentStatesPanel() : '';
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
    bindGlobalComponentStatesPanel(container);
    
    container.querySelectorAll('.tokens-category-header').forEach(header => {
        header.addEventListener('click', (e) => {
            if (e.target.closest('button, input, select, textarea, a')) return;
            
            const type = header.getAttribute('data-type');
            const card = type
                ? document.getElementById(`cat-card-${type}`)
                : header.closest('.tokens-category-card');
            if (card) {
                card.classList.toggle('expanded');
            }
        });
    });
    
    container.querySelectorAll('.btn-add-token-inline[data-type]').forEach(btn => {
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

function renderGlobalComponentStatesPanel() {
    ensureGlobalComponentStates();
    const states = state.designTokens?.global?.$componentStates || createDefaultComponentStates();
    const labels = {
        hover: 'Hover',
        focus: 'Focus',
        active: 'Active',
        disabled: 'Disabled'
    };

    const cards = Object.keys(COMPONENT_STATE_FIELDS).map(stateName => {
        const fields = COMPONENT_STATE_FIELDS[stateName];
        const inputs = fields.map(field => {
            const value = states[stateName]?.[field.key] || '';
            return `
                <label class="component-state-field">
                    <span>${escapeHtml(field.label)}</span>
                    <input class="text-input component-state-input"
                        data-state="${escapeHtml(stateName)}"
                        data-key="${escapeHtml(field.key)}"
                        value="${escapeHtml(value)}"
                        placeholder="${escapeHtml(field.placeholder)}">
                </label>
            `;
        }).join('');

        return `
            <section class="component-state-row">
                <div class="component-state-row-title">
                    <span class="component-state-dot"></span>
                    <strong>${labels[stateName]}</strong>
                </div>
                <div class="component-state-fields">
                    ${inputs}
                </div>
            </section>
        `;
    }).join('');

    return `
        <div class="tokens-category-card expanded component-states-panel" id="cat-card-component-states">
            <div class="tokens-category-header" data-component-state-header>
                <div class="tokens-category-header-left">
                    <i class="fa-solid fa-arrow-pointer"></i>
                    <span>Pseudoclasses globais</span>
                </div>
                <div class="tokens-category-header-right">
                    <span class="tokens-category-count">4</span>
                    <button type="button" class="component-state-save" id="btn-save-component-states" title="Salvar estados">
                        <i class="fa-solid fa-floppy-disk"></i>
                    </button>
                    <i class="fa-solid fa-chevron-down tokens-category-chevron"></i>
                </div>
            </div>
            <div class="tokens-category-body">
                <div class="component-state-list">
                    ${cards}
                </div>
            </div>
        </div>
    `;
}

function bindGlobalComponentStatesPanel(container) {
    const saveBtn = container.querySelector('#btn-save-component-states');
    if (!saveBtn) return;

    saveBtn.addEventListener('click', async () => {
        ensureGlobalComponentStates();
        container.querySelectorAll('.component-state-input').forEach(input => {
            const stateName = input.getAttribute('data-state');
            const key = input.getAttribute('data-key');
            if (!state.designTokens.global.$componentStates[stateName]) {
                state.designTokens.global.$componentStates[stateName] = {};
            }
            state.designTokens.global.$componentStates[stateName][key] = input.value.trim();
        });
        await saveDesignTokens();
        saveBtn.classList.add('is-saved');
        saveBtn.innerHTML = '<i class="fa-solid fa-check"></i>';
        setTimeout(() => {
            saveBtn.classList.remove('is-saved');
            saveBtn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i>';
        }, 1400);
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
    
    const defaultSets = {};
    const activeSets = state.designTokens?.$metadata?.activeSets || ['global'];
    activeSets.forEach(setName => {
        defaultSets[setName] = 'enabled';
    });
    if (!Object.keys(defaultSets).length) defaultSets.global = 'enabled';
    renderThemeEditorSetsCheckboxes(defaultSets);
    
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
    if (!Object.keys(selectedSets).length && state.designTokens.global) {
        selectedSets.global = 'enabled';
    }
    
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

// --- DISCOVERY TAB ---
function initDiscoveryTab() {
    const dropzone = document.getElementById('discovery-dropzone');
    const fileInput = document.getElementById('discovery-file-input');
    const urlInput = document.getElementById('discovery-url-input');
    const urlBtn = document.getElementById('btn-discovery-url');
    const logDiv = document.getElementById('discovery-log');
    const listDiv = document.getElementById('discovery-files-list');
    const refreshBtn = document.getElementById('btn-discovery-refresh');

    function logStatus(msg, error=false) {
        if (!logDiv) return;
        const line = document.createElement('div');
        line.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
        if (error) line.style.color = 'var(--color-danger)';
        if (logDiv.innerHTML.includes('Aguardando...')) {
            logDiv.innerHTML = '';
        }
        logDiv.appendChild(line);
        logDiv.scrollTop = logDiv.scrollHeight;
    }

    if (logDiv && logDiv.innerHTML.includes('Aguardando arquivos...')) {
        logDiv.innerHTML = '<div style="color:var(--color-success)">[Sistema] Módulo de Discovery pronto. Aguardando...</div>';
    }

    async function reloadDiscoveryFiles() {
        if (!state.activeProjectId || !listDiv) return;
        try {
            const res = await fetch(`/api/projects/${state.activeProjectId}/discovery/files`, { headers: getHeaders() });
            if (res.ok) {
                const files = await res.json();
                listDiv.innerHTML = '';
                if (files.length === 0) {
                    listDiv.innerHTML = '<div style="color: var(--text-muted); text-align: center; padding: 40px;">Nenhum arquivo convertido ainda.</div>';
                }
                files.forEach(f => {
                    const el = document.createElement('div');
                    el.className = 'file-node file-node-file';
                    el.style.padding = '8px';
                    el.style.background = 'rgba(255,255,255,0.02)';
                    el.style.borderRadius = '4px';
                    el.style.cursor = 'pointer';
                    el.innerHTML = `<i data-lucide="file-text"></i> <span>${f.filename}</span> <span style="font-size: 10px; color: gray; float: right;">${(f.size/1024).toFixed(1)} KB</span>`;
                    el.onclick = () => {
                        document.querySelector('[data-tab="tab-files"]').click();
                        state.activeFilepath = f.filepath;
                        openFile(f.filepath, f.size, f.mtime);
                    };
                    listDiv.appendChild(el);
                });
                if (window.lucide) window.lucide.createIcons();
            }
        } catch (e) {
            console.error(e);
        }
    }

    async function uploadFile(file) {
        if (!state.activeProjectId) {
            gitideNotify({title: 'Erro', message: 'Selecione um projeto primeiro!', variant: 'danger'});
            return;
        }
        logStatus(`Enviando ${file.name}...`);
        const formData = new FormData();
        formData.append('file', file);
        try {
            const res = await fetch(`/api/projects/${state.activeProjectId}/discovery/upload`, {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail);
            logStatus(`Sucesso: ${file.name} -> ${data.markdown}`);
            reloadDiscoveryFiles();
            loadFiles();
        } catch(e) {
            logStatus(`Erro: ${e.message}`, true);
        }
    }

    if(dropzone) {
        dropzone.addEventListener('click', (e) => {
            if (e.target.tagName !== 'INPUT') {
                fileInput.click();
            }
        });
        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.style.background = 'rgba(0,153,255,0.1)';
        });
        dropzone.addEventListener('dragleave', () => dropzone.style.background = 'rgba(0,0,0,0.2)');
        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.style.background = 'rgba(0,0,0,0.2)';
            if (e.dataTransfer.files.length) {
                Array.from(e.dataTransfer.files).forEach(uploadFile);
            }
        });
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                Array.from(e.target.files).forEach(uploadFile);
            }
        });
    }

    if(urlBtn) {
        urlBtn.addEventListener('click', async () => {
            const url = urlInput.value.trim();
            if (!url) return;
            if (!state.activeProjectId) {
                gitideNotify({title: 'Erro', message: 'Selecione um projeto primeiro!', variant: 'danger'});
                return;
            }
            logStatus(`Extraindo URL: ${url}...`);
            urlBtn.disabled = true;
            try {
                const res = await fetch(`/api/projects/${state.activeProjectId}/discovery/url`, {
                    method: 'POST',
                    headers: getHeaders(),
                    body: JSON.stringify({url})
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail);
                logStatus(`Sucesso: URL processada -> ${data.markdown}`);
                urlInput.value = '';
                reloadDiscoveryFiles();
                loadFiles();
            } catch(e) {
                logStatus(`Erro: ${e.message}`, true);
            }
            urlBtn.disabled = false;
        });
    }
    
    if(refreshBtn) {
        refreshBtn.addEventListener('click', reloadDiscoveryFiles);
    }
    
    document.querySelector('[data-tab="tab-discovery"]')?.addEventListener('click', reloadDiscoveryFiles);
}

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
    ],
    ollama: [
        { value: 'llama3.1', label: 'llama3.1' },
        { value: 'qwen2.5-coder:7b', label: 'qwen2.5-coder:7b' },
        { value: 'deepseek-coder', label: 'deepseek-coder' },
        { value: 'codellama', label: 'codellama' }
    ]
};

function updateAgentModelOptions() {
    const provider = document.getElementById('agent-provider').value;
    const modelSelect = document.getElementById('agent-model');
    if (!modelSelect) return;
    const apiKeyGroup = document.getElementById('agent-apikey-group');
    const ollamaUrlGroup = document.getElementById('agent-ollama-url-group');
    const ollamaModelGroup = document.getElementById('agent-ollama-model-group');
    const ollamaPerformanceGroup = document.getElementById('agent-ollama-performance-group');
    
    modelSelect.innerHTML = '';
    const models = AGENT_MODELS[provider] || [];
    models.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m.value;
        opt.textContent = m.label;
        modelSelect.appendChild(opt);
    });

    const isOllama = provider === 'ollama';
    modelSelect.parentElement.style.display = isOllama ? 'none' : '';
    if (apiKeyGroup) {
        apiKeyGroup.style.display = '';
        const apiKeyLabel = document.querySelector('label[for="agent-apikey"]');
        const apiKeyInput = document.getElementById('agent-apikey');
        if (isOllama) {
            if (apiKeyLabel) apiKeyLabel.textContent = 'API Key (Cloud):';
            if (apiKeyInput) apiKeyInput.placeholder = 'Chave API (Opcional para local)';
        } else {
            if (apiKeyLabel) apiKeyLabel.textContent = 'API Key:';
            if (apiKeyInput) apiKeyInput.placeholder = 'Cole sua chave API aqui';
        }
    }
    if (ollamaUrlGroup) ollamaUrlGroup.style.display = isOllama ? '' : 'none';
    if (ollamaModelGroup) ollamaModelGroup.style.display = isOllama ? '' : 'none';
    if (ollamaPerformanceGroup) ollamaPerformanceGroup.style.display = isOllama ? '' : 'none';
    const ollamaModelInput = document.getElementById('agent-ollama-model');
    const ollamaUrlInput = document.getElementById('agent-ollama-url');
    if (isOllama && ollamaModelInput && !ollamaModelInput.value.trim()) ollamaModelInput.value = 'llama3.1';
    if (isOllama && ollamaUrlInput && !ollamaUrlInput.value.trim()) ollamaUrlInput.value = 'http://127.0.0.1:11434';
    if (isOllama) loadOllamaInstalledModels(ollamaModelInput?.value || 'llama3.1');
}

function applyOllamaPerformancePreset() {
    const mode = document.getElementById('agent-ollama-performance')?.value || 'balanced';
    const ctx = document.getElementById('agent-ollama-num-ctx');
    const predict = document.getElementById('agent-ollama-num-predict');
    if (!ctx || !predict) return;
    if (mode === 'fast') {
        ctx.value = '2048';
        predict.value = '384';
    } else if (mode === 'deep') {
        ctx.value = '8192';
        predict.value = '1200';
    } else {
        ctx.value = '4096';
        predict.value = '768';
    }
}

function formatModelSize(bytes) {
    const size = Number(bytes || 0);
    if (!size) return '';
    const gb = size / 1024 / 1024 / 1024;
    if (gb >= 1) return `${gb.toFixed(1)} GB`;
    const mb = size / 1024 / 1024;
    return mb >= 1 ? `${mb.toFixed(0)} MB` : '';
}

async function loadOllamaInstalledModels(selectedModel = '') {
    const select = document.getElementById('agent-ollama-model');
    const endpointInput = document.getElementById('agent-ollama-url');
    const hint = document.getElementById('agent-ollama-model-hint');
    if (!select) return;
    const baseUrl = endpointInput?.value.trim() || 'http://127.0.0.1:11434';
    const apiKey = document.getElementById('agent-apikey')?.value.trim() || '';
    const current = selectedModel || select.value || 'llama3.1';
    select.innerHTML = '<option value="">Carregando modelos...</option>';
    try {
        const qs = new URLSearchParams({ base_url: baseUrl });
        if (apiKey) qs.append('api_key', apiKey);
        const res = await fetch(`/api/agent/ollama/models?${qs.toString()}`, { headers: getHeaders() });
        const data = await res.json();
        select.innerHTML = '';
        const models = Array.isArray(data.models) ? data.models : [];
        if (data.status === 'success' && models.length) {
            models.forEach(model => {
                const opt = document.createElement('option');
                opt.value = model.name;
                const size = formatModelSize(model.size);
                opt.textContent = size ? `${model.name} - ${size}` : model.name;
                select.appendChild(opt);
            });
            const customOpt = document.createElement('option');
            customOpt.value = '__custom__';
            customOpt.textContent = 'Outro modelo...';
            select.appendChild(customOpt);
            const hasCurrent = models.some(model => model.name === current);
            select.value = hasCurrent ? current : '__custom__';
            toggleOllamaCustomModel();
            const customInput = document.getElementById('agent-ollama-model-custom');
            if (!hasCurrent && customInput) customInput.value = current;
            if (hint) hint.textContent = `${models.length} modelo(s) instalado(s) encontrados no Ollama.`;
            return;
        }
        const fallbackModels = AGENT_MODELS.ollama || [];
        fallbackModels.forEach(model => {
            const opt = document.createElement('option');
            opt.value = model.value;
            opt.textContent = model.label;
            select.appendChild(opt);
        });
        const customOpt = document.createElement('option');
        customOpt.value = '__custom__';
        customOpt.textContent = 'Outro modelo...';
        select.appendChild(customOpt);
        select.value = fallbackModels.some(model => model.value === current) ? current : '__custom__';
        toggleOllamaCustomModel();
        const customInput = document.getElementById('agent-ollama-model-custom');
        if (select.value === '__custom__' && customInput) customInput.value = current;
        if (hint) hint.textContent = data.message ? `Não foi possível consultar o Ollama: ${data.message}` : 'Ollama sem modelos instalados. Use outro modelo ou instale com ollama pull.';
    } catch (err) {
        select.innerHTML = '<option value="__custom__">Outro modelo...</option>';
        select.value = '__custom__';
        toggleOllamaCustomModel();
        const customInput = document.getElementById('agent-ollama-model-custom');
        if (customInput) customInput.value = current;
        if (hint) hint.textContent = `Falha ao carregar modelos: ${err.message}`;
    }
}

function toggleOllamaCustomModel() {
    const select = document.getElementById('agent-ollama-model');
    const customInput = document.getElementById('agent-ollama-model-custom');
    if (!select || !customInput) return;
    customInput.style.display = select.value === '__custom__' ? '' : 'none';
}

function getSelectedOllamaModel() {
    const select = document.getElementById('agent-ollama-model');
    const customInput = document.getElementById('agent-ollama-model-custom');
    if (!select) return 'llama3.1';
    if (select.value === '__custom__') {
        return customInput?.value.trim() || 'llama3.1';
    }
    return select.value || 'llama3.1';
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
        const ollamaModelInput = document.getElementById('agent-ollama-model');
        const ollamaUrlInput = document.getElementById('agent-ollama-url');
        if (ollamaUrlInput) ollamaUrlInput.value = config.ollama_base_url || 'http://127.0.0.1:11434';
        const perfInput = document.getElementById('agent-ollama-performance');
        const ctxInput = document.getElementById('agent-ollama-num-ctx');
        const predictInput = document.getElementById('agent-ollama-num-predict');
        if (perfInput) perfInput.value = config.ollama_performance_mode || 'balanced';
        if (ctxInput) ctxInput.value = config.ollama_num_ctx || 4096;
        if (predictInput) predictInput.value = config.ollama_num_predict || 768;
        if (ollamaModelInput && config.provider === 'ollama') {
            await loadOllamaInstalledModels(config.model || 'llama3.1');
        }
        document.getElementById('agent-apikey').value = config.api_key || '';
        
        // Habilita inputs se tivermos projeto ativo
        const promptInput = document.getElementById('agent-user-prompt');
        const sendBtn = document.getElementById('btn-send-agent-prompt');
        if (state.activeProjectId) {
            promptInput.disabled = false;
            sendBtn.disabled = false;
            promptInput.placeholder = "O que deseja que o agente faça? (ex: 'Crie um teste unitário para vcs.py' ou 'Corrija o gitignore')";
            await loadAgentHistory();
        } else {
            promptInput.disabled = true;
            sendBtn.disabled = true;
            promptInput.placeholder = "Selecione um projeto ativo para iniciar o agente.";
            state.agentChatMessages = [];
            state.agentWorkflowEvents = [];
            state.agentHistoryLoadedProjectId = null;
            renderAgentChatHistory();
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
    const model = provider === 'ollama'
        ? getSelectedOllamaModel()
        : document.getElementById('agent-model').value;
    const apiKey = document.getElementById('agent-apikey').value.trim();
    const ollamaBaseUrl = document.getElementById('agent-ollama-url')?.value.trim() || 'http://127.0.0.1:11434';
    const ollamaPerformanceMode = document.getElementById('agent-ollama-performance')?.value || 'balanced';
    const ollamaNumCtx = Number(document.getElementById('agent-ollama-num-ctx')?.value || 4096);
    const ollamaNumPredict = Number(document.getElementById('agent-ollama-num-predict')?.value || 768);
    
    const enabled_tools = [];
    document.querySelectorAll('#agent-tools-container input[type="checkbox"]').forEach(cb => {
        if (cb.checked) enabled_tools.push(cb.value);
    });
    
    const payload = {
        provider,
        model,
        api_key: apiKey,
        ollama_base_url: ollamaBaseUrl,
        ollama_performance_mode: ollamaPerformanceMode,
        ollama_num_ctx: ollamaNumCtx,
        ollama_num_predict: ollamaNumPredict,
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

function getAgentWelcomeHtml() {
    return `
        <div class="agent-chat-welcome">
            <i data-lucide="bot"></i>
            <h3>Olá! Eu sou o Agente IA Local do Act IA</h3>
            <p>Dê-me um objetivo e eu usarei as ferramentas locais, Git, Terminal, SQL e Ops Infra seguindo o fluxo Harness. Configure o modelo nas <a href="#" id="link-welcome-settings">Configurações</a> para começar.</p>
        </div>
    `;
}

function bindAgentWelcomeSettingsLink() {
    const link = document.getElementById('link-welcome-settings');
    if (link) {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            switchTab('tab-settings');
        });
    }
}

function renderAgentUserMessage(content) {
    const userMsg = document.createElement('div');
    userMsg.className = 'user-message-wrapper';
    userMsg.style.cssText = 'display: flex; justify-content: flex-end; align-self: flex-end; max-width: 85%; margin-bottom: 14px; margin-left: auto;';
    userMsg.innerHTML = `
        <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border-color); border-radius: 12px; padding: 12px 16px; color: var(--text-light); font-size: 13px; line-height: 1.5; font-family: inherit;">
            ${escapeHtml(content)}
        </div>
    `;
    return userMsg;
}

function renderAgentAssistantMessage(content) {
    const agentMsg = document.createElement('div');
    agentMsg.className = 'agent-message-wrapper agent-assistant-message';
    agentMsg.innerHTML = `
        <div class="agent-message-avatar">
            <i data-lucide="bot"></i>
        </div>
        <div class="agent-message-text">
            ${formatAgentMessage(content)}
        </div>
    `;
    return agentMsg;
}

function renderAgentChatHistory() {
    const chatHistory = document.getElementById('agent-chat-history');
    const monitor = document.getElementById('agent-monitor');
    if (!chatHistory) return;
    
    // Protege o monitor de ser destruido
    if (monitor && monitor.parentNode === chatHistory) {
        document.body.appendChild(monitor);
    }
    
    chatHistory.innerHTML = '';
    if (!state.agentChatMessages.length) {
        chatHistory.innerHTML = getAgentWelcomeHtml();
        bindAgentWelcomeSettingsLink();
    } else {
        state.agentChatMessages.forEach(message => {
            const node = message.role === 'user'
                ? renderAgentUserMessage(message.content)
                : renderAgentAssistantMessage(message.content);
            chatHistory.appendChild(node);
        });
    }
    
    // Insere o monitor sempre no final do fluxo de chat
    if (monitor) {
        chatHistory.appendChild(monitor);
    }
    
    if (window.lucide) lucide.createIcons();
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function renderAgentWorkflowHistory() {
    const monitor = document.getElementById('agent-monitor');
    const monitorLogs = document.getElementById('agent-monitor-logs');
    if (!monitor || !monitorLogs) return;
    monitorLogs.innerHTML = '';
    if (!state.agentWorkflowEvents.length) {
        monitor.style.display = 'none';
        return;
    }
    monitor.style.display = 'block';
    state.agentWorkflowEvents.slice(-12).forEach(event => {
        appendAgentMonitorEvent(monitorLogs, monitor, {
            type: event.type || 'status',
            content: event.body || event.title || '',
            result: event.body || '',
            tool: event.title || ''
        }, false);
    });
}

function getRecentAgentContext() {
    return state.agentChatMessages
        .filter(message => ['user', 'assistant'].includes(message.role) && message.content)
        .slice(-12)
        .map(message => ({ role: message.role, content: message.content }));
}

async function persistAgentHistory() {
    if (!state.activeProjectId) return;
    try {
        await fetch(`/api/projects/${state.activeProjectId}/agent/history`, {
            method: 'PUT',
            headers: {
                ...getHeaders(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                messages: state.agentChatMessages,
                workflow: state.agentWorkflowEvents
            })
        });
    } catch (err) {
        console.warn('Falha ao salvar histórico do agente:', err);
    }
}

async function loadAgentHistory(force = false) {
    if (!state.activeProjectId) return;
    if (!force && state.agentHistoryLoadedProjectId === state.activeProjectId) {
        renderAgentChatHistory();
        return;
    }
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/agent/history`, { headers: getHeaders() });
        const data = await res.json();
        state.agentChatMessages = Array.isArray(data.messages) ? data.messages : [];
        state.agentWorkflowEvents = Array.isArray(data.workflow) ? data.workflow : [];
        state.agentHistoryLoadedProjectId = state.activeProjectId;
        renderAgentChatHistory();
        renderAgentWorkflowHistory();
    } catch (err) {
        console.warn('Falha ao carregar histórico do agente:', err);
        renderAgentChatHistory();
        renderAgentWorkflowHistory();
    }
}

async function clearAgentHistory() {
    state.agentChatMessages = [];
    state.agentWorkflowEvents = [];
    renderAgentChatHistory();
    const monitor = document.getElementById('agent-monitor');
    const monitorLogs = document.getElementById('agent-monitor-logs');
    if (monitorLogs) monitorLogs.innerHTML = '';
    if (monitor) monitor.style.display = 'none';
    if (!state.activeProjectId) return;
    try {
        await fetch(`/api/projects/${state.activeProjectId}/agent/history`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        gitideNotify({ title: 'Histórico limpo', message: 'A conversa do agente foi removida deste projeto.', variant: 'success' });
    } catch (err) {
        gitideNotify({ title: 'Erro ao limpar', message: err.message, variant: 'danger' });
    }
}

function formatAgentMessage(text) {
    if (!text) return '';

    let html = escapeHtml(text.trim());

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
                    <span><i data-lucide="code-2"></i> ${filename}</span>
                    <button class="btn-copy-code" onclick="navigator.clipboard.writeText(\`${escapedCode}\`).then(() => { this.textContent = 'Copiado'; setTimeout(() => this.textContent = 'Copiar', 1500); })">Copiar</button>
                </div>
                <pre style="margin: 0; padding: 16px; overflow-x: hidden; white-space: pre-wrap; overflow-wrap: anywhere; word-break: break-word; font-family: monospace; font-size: 12px; line-height: 1.5; color: #e2e8f0; background: transparent;"><code style="font-family: inherit; white-space: inherit;">${codeToShow}</code></pre>
                <div class="code-block-actions" style="display: flex; gap: 10px; padding: 10px 16px; background: rgba(0,0,0,0.1); border-top: 1px solid var(--border-color);">
                    <button class="action-pill-btn btn-apply"><i data-lucide="check"></i> Aplicar</button>
                    <button class="action-pill-btn btn-test"><i data-lucide="play"></i> Testar</button>
                    <button class="action-pill-btn btn-diff"><i data-lucide="eye"></i> Diff</button>
                </div>
            </div>
        `;
    });

    html = html.replace(/^###\s+(.+)$/gm, '<h5>$1</h5>');
    html = html.replace(/^##\s+(.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^#\s+(.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/`(.*?)`/g, '<code>$1</code>');
    html = html.replace(/^\s*[-*]\s+(.+)$/gm, '<li>$1</li>');
    html = html.replace(/((?:<li>.*?<\/li>\n?)+)/gs, '<ul>$1</ul>');
    html = html.replace(/\n{2,}/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');
    if (!/^<(h3|h4|h5|ul|div|pre|p)/.test(html.trim())) {
        html = `<p>${html}</p>`;
    }
    return html;
}

function getAgentMonitorMeta(event) {
    if (event.type === 'status') return { icon: 'activity', title: 'Status', body: event.content || 'Processando...' };
    if (event.type === 'thought') return { icon: 'brain', title: 'Pensamento', body: event.content || 'Analisando contexto...' };
    if (event.type === 'tool_call') return { icon: 'wrench', title: `Ação: ${event.tool}`, body: formatToolArgs(event.args) };
    if (event.type === 'tool_result') return { icon: 'check-circle-2', title: 'Resultado', body: compactAgentText(event.result || '') };
    if (event.type === 'error') return { icon: 'triangle-alert', title: 'Erro', body: event.content || 'Falha ao executar.' };
    return { icon: 'circle', title: 'Evento', body: JSON.stringify(event) };
}

function compactAgentText(value) {
    const text = String(value || '');
    return text.length > 360 ? `${text.slice(0, 360)}...` : text;
}

function formatToolArgs(args) {
    if (!args || !Object.keys(args).length) return 'Executando sem parâmetros.';
    return Object.entries(args)
        .map(([key, value]) => `${key}: ${typeof value === 'string' ? value : JSON.stringify(value)}`)
        .join(' | ');
}

function appendAgentMonitorEvent(monitorLogs, monitor, event, shouldStore = true) {
    const meta = getAgentMonitorMeta(event);
    const div = document.createElement('div');
    div.className = `agent-workflow-item ${event.type || 'status'}`;
    div.innerHTML = `
        <span class="agent-workflow-icon"><i data-lucide="${meta.icon}"></i></span>
        <span class="agent-workflow-copy">
            <strong>${escapeHtml(meta.title)}</strong>
            <small>${escapeHtml(meta.body)}</small>
        </span>
    `;
    monitorLogs.appendChild(div);
    if (shouldStore) {
        state.agentWorkflowEvents.push({
            type: event.type || 'status',
            title: meta.title,
            body: meta.body,
            created_at: new Date().toISOString()
        });
        state.agentWorkflowEvents = state.agentWorkflowEvents.slice(-120);
    }
    if (window.lucide) lucide.createIcons();
    monitor.scrollTop = monitor.scrollHeight;
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
    
    const historyContext = getRecentAgentContext();
    state.agentChatMessages.push({
        role: 'user',
        content: prompt,
        created_at: new Date().toISOString()
    });
    state.agentChatMessages = state.agentChatMessages.slice(-80);
    renderAgentChatHistory();
    chatHistory.scrollTop = chatHistory.scrollHeight;
    
    // Exibe monitor e limpa logs
    monitor.style.display = 'block';
    monitorLogs.innerHTML = '';
    appendAgentMonitorEvent(monitorLogs, monitor, { type: 'status', content: 'Iniciando execução do agente local...' });
    
    try {
        const response = await fetch(`/api/projects/${state.activeProjectId}/agent/run`, {
            method: 'POST',
            headers: {
                ...getHeaders(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt, history: historyContext })
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
                        
                        if (['status', 'thought', 'tool_call', 'tool_result'].includes(event.type)) {
                            appendAgentMonitorEvent(monitorLogs, monitor, event);
                        }
                        else if (event.type === 'final') {
                            state.agentChatMessages.push({
                                role: 'assistant',
                                content: event.content,
                                created_at: new Date().toISOString()
                            });
                            state.agentChatMessages = state.agentChatMessages.slice(-80);
                            renderAgentChatHistory();
                            chatHistory.scrollTop = chatHistory.scrollHeight;
                        } 
                        else if (event.type === 'error') {
                            appendAgentMonitorEvent(monitorLogs, monitor, event);
                        }
                    } catch (e) {
                        console.error('Erro ao fazer parse do streaming chunk:', e);
                    }
                }
            }
        }
        
    } catch (err) {
        appendAgentMonitorEvent(monitorLogs, monitor, { type: 'error', content: `Falha na conexão: ${err.message}` });
    } finally {
        await persistAgentHistory();
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
            
            // Checkout só faz sentido para alternar para outra branch.
            const branches = (data.all || []).filter(branch => branch !== current);
            if (branches.length === 0) {
                selector.innerHTML = '<option value="">Nenhuma outra branch disponível</option>';
                return;
            }
            
            branches.forEach(b => {
                const opt = document.createElement('option');
                opt.value = b;
                opt.textContent = b;
                selector.appendChild(opt);
            });
            selector.value = branches[0];
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

async function openPRModal() {
    if (!state.activeProjectId) return;

    const defaultTitle = `Pull request ${new Date().toLocaleDateString()}`;
    const title = prompt('Título do Pull Request:', defaultTitle);
    if (!title) return;

    const base = prompt('Branch de destino do Pull Request:', 'main');
    if (!base) return;

    const body = prompt('Descrição do Pull Request (opcional):', '');

    appendGitConsole(`Criando Pull Request para a branch "${base}"...`);
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/git/pullrequest`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                title,
                base,
                body: body || ''
            })
        });

        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || 'Erro desconhecido');
        }

        appendGitConsole(`Pull Request criado com sucesso: ${data.html_url || data.title || ''}`);
        gitideNotify({
            title: 'Pull Request criado',
            message: data.html_url || `PR #${data.pr_number || ''} criado no GitHub.`,
            variant: 'success'
        });
        if (data.html_url) {
            window.open(data.html_url, '_blank', 'noopener,noreferrer');
        }
    } catch (err) {
        appendGitConsole(`Erro ao criar Pull Request: ${err.message}`, true);
        gitideNotify({ title: 'Erro ao criar PR', message: err.message, variant: 'error' });
    }
}

async function runGitAbortMerge() {
    if (!state.activeProjectId) return;
    
    const confirmed = await gitideConfirm({
        title: 'Abortar merge',
        kicker: 'Git conflicts',
        message: 'Todas as alterações não resolvidas do merge serão descartadas.',
        confirmText: 'Abortar merge',
        variant: 'danger'
    });
    if (!confirmed) return;
    
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
        gitideNotify({ title: 'Merge abortado', message: 'O repositório voltou ao estado anterior ao merge.', variant: 'success' });
        state.gitConflicts = [];
        state.gitConflictActiveFile = null;
        renderGitConflictFiles();
        renderGitConflictBlocks([]);
        hideGitConflictsPanelIfEmpty();
        loadGitStatus();
    } catch (err) {
        appendGitConsole(`Erro ao abortar mesclagem: ${err.message}`, true);
        gitideNotify({ title: 'Erro ao abortar merge', message: err.message, variant: 'danger' });
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

    const textWrap = document.createElement('div');
    textWrap.className = 'documents-name-text';

    const filenameText = document.createElement('span');
    filenameText.textContent = doc.title || doc.filename;
    filenameText.title = doc.filename;
    const sourceText = document.createElement('small');
    sourceText.textContent = doc.source || doc.filename;
    sourceText.title = doc.source || doc.filename;

    textWrap.appendChild(filenameText);
    textWrap.appendChild(sourceText);
    nameWrap.appendChild(fileIcon);
    nameWrap.appendChild(textWrap);
    nameCell.appendChild(nameWrap);

    const sizeCell = document.createElement('td');
    sizeCell.className = 'documents-size-cell';
    sizeCell.textContent = doc.exists ? `${(doc.size_bytes / 1024).toFixed(1)} KB` : 'Pendente';

    const actionsCell = document.createElement('td');
    actionsCell.className = 'documents-actions-cell';

    const generateBtn = document.createElement('button');
    generateBtn.className = 'btn-icon btn-generate-business-doc';
    generateBtn.dataset.kind = doc.kind || '';
    // title tooltip for better UX since there's no text
    generateBtn.title = doc.exists ? 'Atualizar' : 'Gerar';
    generateBtn.innerHTML = `<i class="fa-solid fa-file-export"></i>`;

    const downloadBtn = document.createElement('button');
    downloadBtn.className = 'btn-icon btn-download-doc';
    downloadBtn.dataset.filename = doc.filename;
    downloadBtn.title = 'Baixar';
    downloadBtn.innerHTML = '<i class="fa-solid fa-download"></i>';
    downloadBtn.disabled = !doc.exists;

    actionsCell.appendChild(generateBtn);
    actionsCell.appendChild(downloadBtn);

    tr.appendChild(nameCell);
    tr.appendChild(sizeCell);
    tr.appendChild(actionsCell);

    const selectRow = () => {
        if (!doc.exists) return;
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

    generateBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        generateBusinessDocuments(e.currentTarget.dataset.kind);
    });

    downloadBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        downloadDocumentFile(e.currentTarget.dataset.filename);
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
        const res = await fetch(`/api/projects/${state.activeProjectId}/documents/business`);
        const documents = await res.json();
        
        if (!res.ok) {
            throw new Error(documents.detail || 'Erro ao carregar documentos');
        }
        
        if (documents.length === 0) {
            renderDocumentsStateRow(tbody, {
                icon: 'fa-solid fa-folder-open',
                message: 'Nenhum modelo de documento encontrado para este projeto.',
                variant: 'empty'
            });
            resetDocumentPreviewState();
            return;
        }
        
        tbody.innerHTML = '';
        documents.forEach(doc => {
            tbody.appendChild(buildDocumentTableRow(doc, tbody));
        });
        
        let docToSelect = documents.find(doc => doc.exists) || null;
        if (state.selectedDocumentFilename) {
            const found = documents.find(d => d.filename === state.selectedDocumentFilename);
            if (found && found.exists) docToSelect = found;
        }
        
        if (docToSelect) {
            state.selectedDocumentFilename = docToSelect.filename;
            loadDocumentPreview(docToSelect.filename);
            const selectedRow = Array.from(tbody.querySelectorAll('.documents-table-row')).find(row => {
                const filename = row.querySelector('.btn-download-doc')?.dataset.filename;
                return filename === docToSelect.filename;
            });
            if (selectedRow) selectedRow.classList.add('selected');
        } else {
            resetDocumentPreviewState();
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
    
    const instructions = `Você está apoiando o projeto "${state.activeProject.name}" (ID: ${state.activeProjectId}) no Act IA.
Para documentação executiva, NÃO escreva o documento Word diretamente no chat.
Primeiro mantenha os arquivos vivos do Harness Engineering atualizados:
- TAP: .documents/project-charter.md
- Specify: todos os REQs em .documents/requirements/*.md
- Design: .documents/design/design.md
- DRI: .documents/dri/dri.md
- Task List: .documents/task/task.md
- Task Details: .documents/task/task.details.md
- Estimativa: .documents/estimativa.md e .documents/estimativa.json

Nunca sobrescreva ou apague o histórico/conteúdo vivo de .documents/estimativa.md e .documents/estimativa.json para gerar o Word. A aba Documentos (Word) deve apenas ler esses arquivos e derivar o .docx oficial.

Depois, use a aba Documentos (Word) do Act IA para gerar/atualizar os .docx oficiais:
- Termo de Abertura do Projeto
- Specify - Especificação, com cada REQ em uma página
- Design - Planejamento
- DRI - Documento de Requisito de Interface
- Task List - Tarefas + task.details
- Estimativa - Esforço e Custos`;

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
    meta.innerHTML = `Data de Geração: ${new Date().toLocaleString()}<br>Gerado via: Agente Act IA`;
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
                pre.style.overflowX = 'hidden';
                pre.style.whiteSpace = 'pre-wrap';
                pre.style.overflowWrap = 'anywhere';
                pre.style.wordBreak = 'break-word';
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

// =============================================================================
// --- SPEC-DRIVEN DEVELOPMENT (SDD) MODULE ---
// =============================================================================

const sddState = {
    activeFilename: null,
    activeContent: '',
    activeStorageType: null,
    activeFilepath: null,
    projectDocuments: {
        design: '',
        dri: '',
        task: '',
        task_details: ''
    },
    taskFilepath: '.documents/task/task.md',
    allCriteria: [],
    projectCriteria: [],
    projectTaskFilter: 'all',
    taskSelection: {
        current: new Set(),
        project: new Set()
    },
    specs: [],
    executeTask: null,
    charterLoaded: false,
    charterProjectId: null,
    isDraft: false,
    activeReqId: null,
    activeTab: 'sdd-tab-preview'
};

function sddSetButtonLoading(button, loading, loadingText, defaultHtml) {
    if (!button) return;
    button.disabled = loading;
    button.innerHTML = loading
        ? `<i data-lucide="loader-2" style="animation:spin 1s linear infinite;"></i> ${loadingText}`
        : defaultHtml;
    if (window.lucide) lucide.createIcons();
}

async function generateBusinessDocuments(kind = 'all') {
    if (!state.activeProjectId) return;

    const selector = kind && kind !== 'all'
        ? `.btn-generate-business-doc[data-kind="${CSS.escape(kind)}"]`
        : '#btn-generate-business-docs';
    const btn = document.querySelector(selector);
    const originalText = btn?.innerHTML;
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Gerando...';
    }

    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/documents/business/generate`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ kind: kind || 'all' })
        });
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || 'Erro ao gerar documentos Word');
        }
        const generated = data.documents || [];
        if (generated.length) {
            state.selectedDocumentFilename = generated[0].filename;
        }
        gitideNotify({
            title: 'Documentos Word atualizados',
            message: generated.length === 1 ? `${generated[0].filename} foi gerado.` : `${generated.length} documentos foram gerados.`,
            variant: 'success'
        });
        await loadDocuments();
    } catch (err) {
        gitideNotify({ title: 'Erro ao gerar documentos', message: err.message, variant: 'danger' });
    } finally {
        if (btn && originalText) {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }
}

async function sddEnsureProjectStructure() {
    if (!state.activeProjectId) return null;
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/sdd/structure`, {
            method: 'POST',
            headers: getHeaders()
        });
        const data = await res.json();
        if (!res.ok || data.status === 'error') {
            throw new Error(data.detail || data.message || 'Erro ao preparar estrutura Harness');
        }
        return data;
    } catch (e) {
        console.warn('Não foi possível preparar a estrutura Harness:', e);
        gitideNotify({ title: 'Harness Engineering', message: e.message, variant: 'warning' });
        return null;
    }
}

function sddSwitchHarnessPanel(panelId) {
    document.querySelectorAll('.harness-panel').forEach(panel => {
        panel.classList.toggle('active', panel.id === panelId);
    });
    document.querySelectorAll('.harness-top-tab').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.harnessPanel === panelId);
    });

    if (panelId === 'harness-charter-panel') {
        sddLoadCharter();
    } else if (panelId === 'harness-specs-panel') {
        sddSwitchTab('sdd-tab-preview');
        sddLoadSpecs(true);
    } else if (panelId === 'harness-tasks-panel') {
        sddLoadProjectTasks();
    }
}

async function sddWriteCharterFallback(content) {
    const res = await fetch(`/api/projects/${state.activeProjectId}/files/write`, {
        method: 'POST',
        headers: { ...getHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ filepath: '.documents/project-charter.md', content })
    });
    const data = await res.json();
    if (!res.ok || data.status === 'error') {
        throw new Error(data.detail || data.message || 'Erro ao salvar TAP');
    }
    return data;
}

async function sddLoadCharter(force = false) {
    if (!state.activeProjectId) return;
    if (sddState.charterLoaded && sddState.charterProjectId === state.activeProjectId && !force) return;
    const editor = document.getElementById('sdd-charter-editor');
    if (!editor) return;

    editor.value = 'Carregando TAP...';
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/sdd/charter`, { headers: getHeaders() });
        const data = await res.json();
        if (!res.ok) {
            if (res.status === 404) {
                editor.value = `# Termo de Abertura do Projeto - ${state.activeProject?.name || 'Projeto'}\n\n## 1. Contexto\n\n## 2. Objetivo do Projeto\n\n## 3. Escopo Inicial\n\n### Dentro do escopo\n\n- \n\n### Fora do escopo\n\n- \n\n## 4. Stakeholders\n\n- Solicitante:\n- Usuários impactados:\n- Responsável técnico:\n\n## 5. Premissas e Restrições\n\n- \n\n## 6. Riscos Iniciais\n\n- \n\n## 7. Critérios de Sucesso\n\n- [ ] \n\n## 8. Próximo Passo\n\nCrie as especificações funcionais a partir deste TAP.\n`;
                sddState.charterLoaded = true;
                sddState.charterProjectId = state.activeProjectId;
                return;
            }
            throw new Error(data.detail || 'Erro ao carregar TAP');
        }
        editor.value = data.content || '';
        sddState.charterLoaded = true;
        sddState.charterProjectId = state.activeProjectId;
    } catch (e) {
        editor.value = '';
        gitideNotify({ title: 'Erro ao carregar TAP', message: e.message, variant: 'danger' });
    }
}

async function sddSaveCharter() {
    if (!state.activeProjectId) return;
    const editor = document.getElementById('sdd-charter-editor');
    const btn = document.getElementById('btn-sdd-save-charter');
    if (!editor) return;

    sddSetButtonLoading(btn, true, 'Salvando...', '<i data-lucide="save"></i> Salvar TAP');
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/sdd/charter`, {
            method: 'POST',
            headers: { ...getHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: editor.value })
        });
        const data = await res.json();
        if (res.status === 404) {
            await sddWriteCharterFallback(editor.value);
        } else if (!res.ok || data.status !== 'success') {
            throw new Error(data.detail || data.message || 'Erro ao salvar TAP');
        }
        sddState.charterLoaded = true;
        sddState.charterProjectId = state.activeProjectId;
        gitideNotify({ title: 'TAP salvo', message: 'Project Charter atualizado no projeto.', variant: 'success' });
    } catch (e) {
        gitideNotify({ title: 'Erro ao salvar TAP', message: e.message, variant: 'danger' });
    } finally {
        sddSetButtonLoading(btn, false, '', '<i data-lucide="save"></i> Salvar TAP');
    }
}

async function sddGenerateCharterIA() {
    if (!state.activeProjectId) {
        alert('Selecione um projeto primeiro.');
        return;
    }
    const title = document.getElementById('sdd-charter-title')?.value.trim() || '';
    const prompt = document.getElementById('sdd-charter-prompt')?.value.trim() || '';
    const editor = document.getElementById('sdd-charter-editor');
    const btn = document.getElementById('btn-sdd-generate-charter-ia');
    if (!prompt) {
        gitideNotify({ title: 'Contexto obrigatório', message: 'Descreva o projeto para a IA gerar o TAP.', variant: 'warning' });
        return;
    }

    sddSetButtonLoading(btn, true, 'Gerando TAP...', '<i data-lucide="wand-2"></i> Gerar TAP com IA');
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/sdd/generate-charter`, {
            method: 'POST',
            headers: { ...getHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, prompt })
        });
        const data = await res.json();
        if (!res.ok || data.status !== 'success') throw new Error(data.detail || 'Erro ao gerar TAP');
        if (editor) editor.value = data.content || '';
        sddState.charterLoaded = true;
        sddState.charterProjectId = state.activeProjectId;
        gitideNotify({ title: 'TAP gerado', message: 'Project Charter criado e salvo em .documents/project-charter.md.', variant: 'success' });
    } catch (e) {
        gitideNotify({ title: 'Erro ao gerar TAP', message: e.message, variant: 'danger' });
    } finally {
        sddSetButtonLoading(btn, false, '', '<i data-lucide="wand-2"></i> Gerar TAP com IA');
    }
}

// --- Simple Markdown Renderer (lightweight, no external deps) ---
function sddRenderMarkdown(md) {
    if (!md) return '';
    let html = md
        // Escape HTML
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        // Code blocks
        .replace(/```([\s\S]*?)```/g, (_, code) => `<pre><code>${code.trim()}</code></pre>`)
        // Inline code
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        // Bold
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        // H1-H4
        .replace(/^#### (.+)$/gm, '<h4>$1</h4>')
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        // Horizontal rule
        .replace(/^---$/gm, '<hr>')
        // Checkbox list items  - [x] and - [ ]
        .replace(/^\- \[x\] (.+)$/gm, '<li class="md-check checked"><span class="md-checkbox">✓</span> $1</li>')
        .replace(/^\- \[ \] (.+)$/gm, '<li class="md-check"><span class="md-checkbox">○</span> $1</li>')
        // Unordered list items
        .replace(/^\- (.+)$/gm, '<li>$1</li>')
        // Ordered list items
        .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
        // Blockquotes
        .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');

    // Wrap consecutive <li> in <ul>
    html = html.replace(/((<li[^>]*>.*<\/li>\n?)+)/g, '<ul>$1</ul>');
    // Paragraphs: lines that are not html tags
    html = html.split('\n').map(line => {
        const trimmed = line.trim();
        if (!trimmed) return '';
        if (/^<(h[1-4]|ul|ol|li|pre|blockquote|hr)/.test(trimmed)) return trimmed;
        return `<p>${trimmed}</p>`;
    }).join('\n');
    return html;
}

// --- Load & Render Spec List ---
async function sddLoadSpecs(ensureStructure = false) {
    if (!state.activeProjectId) return;
    const list = document.getElementById('sdd-specs-list');
    list.innerHTML = '<div class="specs-empty-state" style="padding:20px;text-align:center;"><span style="color:var(--text-muted)">Carregando...</span></div>';
    try {
        if (ensureStructure) {
            await sddEnsureProjectStructure();
        }
        const res = await fetch(`/api/projects/${state.activeProjectId}/sdd/specs`, { headers: getHeaders() });
        const specs = await res.json();
        sddState.specs = specs;
        sddRenderSpecList(specs);
    } catch (e) {
        list.innerHTML = '<div class="specs-empty-state"><span style="color:#ef4444">Erro ao carregar especificações.</span></div>';
    }
}

async function sddLoadProjectDocuments() {
    if (!state.activeProjectId) return;
    const kinds = ['design', 'dri', 'task', 'task_details'];
    await Promise.all(kinds.map(async (kind) => {
        try {
            const res = await fetch(`/api/projects/${state.activeProjectId}/sdd/project-documents/${kind}`, { headers: getHeaders() });
            const data = await res.json();
            sddState.projectDocuments[kind] = data.content || '';
        } catch (e) {
            console.warn(`Erro ao carregar documento Harness ${kind}:`, e);
            sddState.projectDocuments[kind] = '';
        }
    }));
}

function sddRenderSpecList(specs) {
    const list = document.getElementById('sdd-specs-list');
    const activeListTab = sddGetVisibleHarnessTab();
    if (!specs || specs.length === 0) {
        if (!sddState.isDraft) {
            sddResetWorkspaceEmpty();
        }
        list.innerHTML = `
            <div class="specs-empty-state">
                <i data-lucide="file-question"></i>
                <span>Nenhuma especificação encontrada. Use o assistente ao lado para gerar ou crie uma manual.</span>
            </div>`;
        if (window.lucide) lucide.createIcons();
        return;
    }

    let html = '';
    const isRequirementParent = (spec) => sddGetSpecKind(spec) === 'req';
    const isFunctionalRequirement = (spec) => sddGetSpecKind(spec) === 'rf';
    const renderSpecItem = (spec, isChild = false) => {
        const kind = sddGetSpecKind(spec);
        if (activeListTab === 'sdd-tab-preview' && kind !== 'req') return '';
        if (activeListTab !== 'sdd-tab-preview' && kind !== 'rf') return '';
        const icon = isChild ? 'file-code' : 'file-text';
        return `
        <div class="spec-item ${sddState.activeFilename === spec.filename ? 'active' : ''}" 
             data-filename="${spec.filename}" 
             onclick="sddSelectSpec('${spec.filename}')">
            <i data-lucide="${icon}" style="width:15px;height:15px;flex-shrink:0;"></i>
            <div style="flex:1;min-width:0;">
                <div class="spec-item-title" title="${spec.title}">${spec.title}</div>
            </div>
        </div>`;
    };

    if (activeListTab === 'sdd-tab-preview') {
        // Aba 1 REQ: Mostrar apenas REQs Pai
        const reqs = specs.filter(isRequirementParent);
        if (reqs.length === 0) {
            html = `<div class="specs-empty-state"><span>Nenhum REQ Pai encontrado.</span></div>`;
        } else {
            reqs.forEach(req => { html += renderSpecItem(req, false); });
        }
    } else {
        // Demais abas: Mostrar apenas RFs do REQ selecionado
        if (!sddState.activeReqId) {
            html = `<div class="specs-empty-state"><span>Selecione um REQ na aba 1 REQ primeiro.</span></div>`;
        } else {
            const reqId = sddState.activeReqId;
            const reqNumMatch = reqId ? reqId.match(/REQ-(\d+)/i) : null;
            const reqNum = reqNumMatch ? reqNumMatch[1] : reqId;
            
            const rfs = specs.filter(s => {
                if (!isFunctionalRequirement(s)) return false;
                // Se for a estrutura aninhada antiga, o caminho contém o REQ ID inteiro
                const filepath = String(s.filepath || s.filename || '');
                if (filepath.toLowerCase().includes(reqId.toLowerCase())) return true;
                // Na nova estrutura achatada, o arquivo chama RF-<ID>-<SUBID>
                const fname = s.filename.split('/').pop().toUpperCase();
                return fname.startsWith(`RF-${reqNum}-`);
            });
            
            html += `<div class="spec-item-title" style="padding: 8px 12px; color: var(--text-secondary); font-size: 0.8rem; text-transform: uppercase;">RFs de ${reqId}</div>`;
            if (rfs.length === 0) {
                html += `<div class="specs-empty-state"><span>Nenhum RF encontrado para ${reqId}.</span></div>`;
            } else {
                rfs.forEach(rf => { html += renderSpecItem(rf, true); });
            }
        }
    }

    list.innerHTML = html;
    if (window.lucide) lucide.createIcons();
}

function sddGetVisibleHarnessTab() {
    const activeButton = document.querySelector('#sdd-workspace-nav-tabs .sdd-nav-btn.active');
    if (activeButton?.dataset?.sddTab) return activeButton.dataset.sddTab;

    const activePanel = document.querySelector('.sdd-tab-content.active');
    if (activePanel?.id) return activePanel.id;

    return sddState.activeTab || 'sdd-tab-preview';
}

function sddGetSpecIdentity(specOrFilename) {
    if (typeof specOrFilename === 'string') return specOrFilename;
    if (!specOrFilename) return '';
    return `${specOrFilename.filename || ''} ${specOrFilename.filepath || ''} ${specOrFilename.title || ''} ${specOrFilename.id || ''}`;
}

function sddGetSpecKind(specOrFilename) {
    const identity = sddGetSpecIdentity(specOrFilename).replace(/\\/g, '/');
    const basename = identity.split('/').pop() || identity;
    if (/\bfunctional-requirements\b/i.test(identity) || /\bRF-\d{2,6}(?:-\d{1,4})?\b/i.test(identity) || /^\s*RF[-_\[]/i.test(basename)) {
        return 'rf';
    }
    if (/\bREQ-\d{2,6}\b/i.test(identity)) {
        return 'req';
    }
    if (specOrFilename && typeof specOrFilename === 'object' && specOrFilename.kind) {
        const kind = String(specOrFilename.kind).toLowerCase();
        if (kind === 'req' || kind === 'rf') return kind;
    }
    return 'other';
}

function sddIsFunctionalRequirementFile(filename) {
    return sddGetSpecKind(filename) === 'rf';
}

function sddExtractParentRequirementIdFromRf(specOrFilename) {
    const identity = sddGetSpecIdentity(specOrFilename);
    const rfMatch = identity.match(/\bRF-(\d{2,6})(?:-\d{1,4})?\b/i);
    if (rfMatch) return `REQ-${rfMatch[1]}`;
    return sddExtractRequirementId(identity);
}

// --- Select / Load a Spec ---
async function sddSelectSpec(filename) {
    if (!state.activeProjectId) return;
    sddState.activeFilename = filename;
    sddState.isDraft = false;

    document.querySelectorAll('.spec-item').forEach(el => {
        el.classList.toggle('active', el.dataset.filename === filename);
    });

    document.getElementById('sdd-workspace-nav-tabs').style.display = 'flex';
    sddSetActiveSpecHeader({ filename });

    try {
        const [specRes] = await Promise.all([
            fetch(`/api/projects/${state.activeProjectId}/sdd/specs/${encodeURIComponent(filename)}`, { headers: getHeaders() }),
            sddLoadProjectDocuments()
        ]);
        const data = await specRes.json();
        if (!specRes.ok) throw new Error(data.detail || 'Erro ao carregar Especificação');
        sddState.activeContent = data.content || '';
        sddState.activeStorageType = data.storage_type || 'legacy_markdown';
        sddState.activeFilepath = data.filepath || '';
        sddSetActiveSpecHeader({ filename, content: sddState.activeContent });
        sddPopulatePreview(sddState.activeContent);

        const isRf = sddIsFunctionalRequirementFile(filename);
        const reqId = isRf ? sddExtractParentRequirementIdFromRf(filename) : sddExtractRequirementId(filename);
        if (reqId) {
            sddState.activeReqId = reqId.toUpperCase();
        }

        if (isRf) {
            // It's an RF
            document.getElementById('sdd-rf-editor').value = sddState.activeContent;
            document.getElementById('sdd-edit-filename').value = filename;
            sddSwitchTab('sdd-tab-rfs');
        } else {
            // It's a REQ Pai
            document.getElementById('sdd-specify-editor').value = sddState.activeContent;
            document.getElementById('sdd-edit-filename').value = filename;
            sddSwitchTab('sdd-tab-preview');
        }

        const checklistTab = document.getElementById('sdd-tab-checklist');
        if (checklistTab && checklistTab.classList.contains('active')) {
            await sddLoadCriteria();
        }
    } catch (e) {
        console.error('Erro ao carregar spec:', e);
        gitideNotify({ title: 'Erro ao carregar REQ', message: e.message, variant: 'danger' });
    }
}

function sddExtractTitle(content) {
    const match = content.match(/^#\s+(.+)$/m);
    return match ? match[1].trim() : null;
}

function sddExtractRequirementId(value) {
    const match = (value || '').match(/\bREQ[-_ ]?(\d{3,6})/i);
    return match ? `REQ-${match[1]}` : '';
}

function sddCleanRequirementTitle(title) {
    const cleaned = (title || '').replace(/^\s*REQ[-_ ]?\d{3,6}\s*[-:–—]?\s*/i, '').trim();
    return cleaned || title || '';
}

function sddSetActiveSpecHeader({ title, filename, content }) {
    const rawTitle = title || sddExtractTitle(content || '') || filename || 'Nova Especificação';
    const cleanTitle = sddCleanRequirementTitle(rawTitle);
    const reqId = sddExtractRequirementId(rawTitle) || sddExtractRequirementId(filename);
    const metaParts = [reqId].filter(Boolean);
    const titleEl = document.getElementById('sdd-active-spec-title');
    const filenameEl = document.getElementById('sdd-active-spec-filename');

    if (titleEl) titleEl.textContent = cleanTitle;
    if (filenameEl) {
        filenameEl.textContent = metaParts.join(' · ');
        filenameEl.style.display = metaParts.length ? 'inline' : 'none';
    }
    
    // Atualizar títulos dos editores (REQ e RF)
    const isRf = filename && sddIsFunctionalRequirementFile(filename);
    if (isRf) {
        const rfTitle = document.getElementById('sdd-stage-rf-title');
        const rfSubtitle = document.getElementById('sdd-stage-rf-subtitle');
        if (rfTitle) rfTitle.textContent = cleanTitle;
        if (rfSubtitle) rfSubtitle.textContent = filename;
    } else {
        const reqTitle = document.getElementById('sdd-stage-req-title');
        const reqSubtitle = document.getElementById('sdd-stage-req-subtitle');
        if (reqTitle) reqTitle.textContent = cleanTitle;
        if (reqSubtitle) reqSubtitle.textContent = filename;
    }
}

function sddResetWorkspaceEmpty() {
    sddState.activeFilename = null;
    sddState.activeContent = '';
    sddState.activeStorageType = null;
    sddState.activeFilepath = null;
    sddState.projectDocuments = { design: '', dri: '', task: '', task_details: '' };
    sddState.taskFilepath = '.documents/task/task.md';
    sddState.allCriteria = [];
    sddState.executeTask = null;

    const nav = document.getElementById('sdd-workspace-nav-tabs');
    const title = document.getElementById('sdd-active-spec-title');
    const filename = document.getElementById('sdd-active-spec-filename');
    const editFilename = document.getElementById('sdd-edit-filename');
    const fullEditor = document.getElementById('sdd-spec-editor-textarea');
    const specifyEditor = document.getElementById('sdd-specify-editor');
    const designEditor = document.getElementById('sdd-design-editor');
    const driEditor = document.getElementById('sdd-dri-editor');
    const taskDetailsEditor = document.getElementById('sdd-task-details-editor');
    const executeEditor = document.getElementById('sdd-execute-instructions');
    const resultPanel = document.getElementById('sdd-test-result-panel');

    if (nav) nav.style.display = 'none';
    if (title) title.textContent = 'Nenhuma Especificação Selecionada';
    if (filename) {
        filename.textContent = '';
        filename.style.display = 'none';
    }
    if (editFilename) editFilename.value = '';
    if (fullEditor) fullEditor.value = '';
    if (specifyEditor) specifyEditor.value = '';
    if (designEditor) designEditor.value = '';
    if (driEditor) driEditor.value = '';
    if (executeEditor) executeEditor.value = '';
    if (resultPanel) resultPanel.style.display = 'none';

    sddSwitchTab('sdd-tab-preview');
    sddPopulateStageEditors('');
}

function sddExtractSection(content, sectionNames) {
    const names = Array.isArray(sectionNames) ? sectionNames : [sectionNames];
    const lines = (content || '').split('\n');
    let start = -1;
    let end = lines.length;

    for (let i = 0; i < lines.length; i++) {
        const normalized = lines[i].replace(/^#+\s*\d*\.?\s*/, '').toLowerCase();
        if (names.some(name => normalized.includes(name.toLowerCase()))) {
            start = i;
            break;
        }
    }

    if (start === -1) return '';

    const level = (lines[start].match(/^#+/) || ['##'])[0].length;
    for (let i = start + 1; i < lines.length; i++) {
        const heading = lines[i].match(/^(#+)\s+/);
        if (heading && heading[1].length <= level) {
            end = i;
            break;
        }
    }

    return lines.slice(start, end).join('\n').trim();
}

function sddReplaceSection(content, sectionNames, fallbackHeading, sectionContent) {
    const names = Array.isArray(sectionNames) ? sectionNames : [sectionNames];
    const lines = (content || '').split('\n');
    let start = -1;
    let end = lines.length;

    for (let i = 0; i < lines.length; i++) {
        const normalized = lines[i].replace(/^#+\s*\d*\.?\s*/, '').toLowerCase();
        if (names.some(name => normalized.includes(name.toLowerCase()))) {
            start = i;
            break;
        }
    }

    const cleanSection = (sectionContent || fallbackHeading).trim();
    if (start === -1) {
        return `${(content || '').trim()}\n\n${cleanSection}\n`;
    }

    const level = (lines[start].match(/^#+/) || ['##'])[0].length;
    for (let i = start + 1; i < lines.length; i++) {
        const heading = lines[i].match(/^(#+)\s+/);
        if (heading && heading[1].length <= level) {
            end = i;
            break;
        }
    }

    return [
        ...lines.slice(0, start),
        ...cleanSection.split('\n'),
        ...lines.slice(end)
    ].join('\n').trim() + '\n';
}

function sddPopulateStageEditors(content) {
    const isProjectSpec = sddState.activeStorageType === 'project_spec_file' || sddState.isDraft;
    const specify = isProjectSpec
        ? content
        : (sddExtractSection(content, ['Specify', 'Especificação', 'Requisitos']) || content);
    const design = isProjectSpec
        ? sddState.projectDocuments.design
        : sddExtractSection(content, ['Design', 'Planejamento', 'Arquitetura']);
    const dri = isProjectSpec
        ? sddState.projectDocuments.dri
        : sddExtractSection(content, ['DRI', 'Documento de Requisito de Interface']);
    const specifyEditor = document.getElementById('sdd-specify-editor');
    const designEditor = document.getElementById('sdd-design-editor');
    const driEditor = document.getElementById('sdd-dri-editor');
    const fullEditor = document.getElementById('sdd-spec-editor-textarea');
    if (specifyEditor) specifyEditor.value = specify;
    if (designEditor) designEditor.value = design || '# Design — Planejamento Técnico do Projeto\n\n## 1. Arquitetura Proposta\n\n## 2. Fluxos Técnicos\n\n## 3. Estratégia de Validação\n';
    if (driEditor) driEditor.value = dri || '# DRI — Documento de Requisito de Interface do Projeto\n\n## 1. Interfaces Mapeadas\n\n## 2. Regras de Interface\n\n## 3. Critérios de Aceite da Interface\n\n- [ ] \n';
    if (fullEditor) fullEditor.value = content;
    const empty = document.getElementById('sdd-empty-workspace');
    const emptyRf = document.getElementById('sdd-empty-workspace-rf');
    const previewTab = document.getElementById('sdd-tab-preview');
    const rfsTab = document.getElementById('sdd-tab-rfs');
    
    const hasContent = Boolean(sddState.activeFilename || content);
    const isRf = Boolean(sddState.activeFilename && sddIsFunctionalRequirementFile(sddState.activeFilename));

    if (empty) empty.style.display = hasContent ? 'none' : 'flex';
    if (previewTab) previewTab.classList.toggle('has-content', hasContent);

    if (emptyRf) {
        emptyRf.style.display = isRf ? 'none' : 'flex';
        const p = emptyRf.querySelector('p');
        if (p) {
            if (sddState.activeReqId) {
                p.textContent = 'Selecione um RF na barra lateral ou clique em "+" para criar um novo.';
            } else {
                p.textContent = 'Selecione um REQ na barra lateral (aba 1 REQ) para habilitar a criação de seus RFs aqui.';
            }
        }
    }
    if (rfsTab) rfsTab.classList.toggle('has-content', isRf);
}

function sddPopulatePreview(content) {
    const container = document.getElementById('sdd-spec-markdown-render');
    if (container) container.innerHTML = sddRenderMarkdown(content);
    sddPopulateStageEditors(content);
    if (window.lucide) lucide.createIcons();
}

// --- Workspace Sub-tab Switching ---
function sddSwitchTab(tabId) {
    if (tabId === 'sdd-tab-preview' && sddState.activeFilename && sddIsFunctionalRequirementFile(sddState.activeFilename)) {
        const parentId = sddExtractParentRequirementIdFromRf(sddState.activeFilename);
        const parentReq = (sddState.specs || []).find(spec => {
            if (sddGetSpecKind(spec) !== 'req') return false;
            const identity = sddGetSpecIdentity(spec).toLowerCase();
            return parentId && identity.includes(parentId.toLowerCase());
        });
        if (parentReq) {
            setTimeout(() => sddSelectSpec(parentReq.filename), 0);
        } else {
            sddResetWorkspaceEmpty();
        }
    }
    sddState.activeTab = tabId;
    document.querySelectorAll('.sdd-tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.sdd-nav-btn').forEach(b => b.classList.remove('active'));
    const tab = document.getElementById(tabId);
    if (tab) tab.classList.add('active');
    const btn = document.querySelector(`[data-sdd-tab="${tabId}"]`);
    if (btn) btn.classList.add('active');
    sddUpdateFlowStrip(tabId);

    // Re-render specs list dynamically based on the active tab
    sddRenderSpecList(sddState.specs || []);

    // Load criteria when switching to checklist
    if (tabId === 'sdd-tab-checklist' && sddState.activeFilename) {
        sddLoadCriteria();
    }
}

function sddGetStageGridFromButton(button) {
    return button?.closest('.sdd-stage-grid, .sdd-execute-grid');
}

function sddRefreshStageLayoutButtons(grid) {
    if (!grid) return;
    const asideHidden = grid.classList.contains('is-aside-collapsed') || grid.classList.contains('is-focus-mode');
    const focusMode = grid.classList.contains('is-focus-mode');
    const asideBtn = grid.querySelector('[data-sdd-aside-toggle]');
    const focusBtn = grid.querySelector('[data-sdd-focus-toggle]');

    if (asideBtn) {
        asideBtn.title = asideHidden ? 'Abrir assistente IA' : 'Recolher assistente IA';
        asideBtn.innerHTML = asideHidden ? '<i data-lucide="panel-right-open"></i>' : '<i data-lucide="panel-right-close"></i>';
    }
    if (focusBtn) {
        focusBtn.title = focusMode ? 'Sair do modo foco' : 'Modo foco';
        focusBtn.innerHTML = focusMode ? '<i data-lucide="minimize-2"></i>' : '<i data-lucide="maximize-2"></i>';
    }
    if (window.lucide) lucide.createIcons();
}

function sddToggleStageAside(button) {
    const grid = sddGetStageGridFromButton(button);
    if (!grid) return;
    grid.classList.remove('is-focus-mode');
    grid.classList.toggle('is-aside-collapsed');
    sddRefreshStageLayoutButtons(grid);
}

function sddToggleStageFocus(button) {
    const grid = sddGetStageGridFromButton(button);
    if (!grid) return;
    grid.classList.toggle('is-focus-mode');
    if (grid.classList.contains('is-focus-mode')) {
        grid.classList.remove('is-aside-collapsed');
    }
    sddRefreshStageLayoutButtons(grid);
}

function sddUpdateFlowStrip(tabId = 'sdd-tab-preview') {
    const strip = document.getElementById('sdd-flow-strip');
    if (!strip) return;
    const hasSpecContext = Boolean(sddState.activeFilename) || tabId === 'sdd-tab-edit' || tabId === 'sdd-tab-dri' || tabId === 'sdd-tab-ia-wizard';
    strip.style.display = hasSpecContext ? 'flex' : 'none';

    const breadcrumb = document.getElementById('sdd-flow-breadcrumb');
    if (breadcrumb) {
        const filename = sddState.activeFilename || document.getElementById('sdd-edit-filename')?.value || 'novo-req.md';
        const basePath = sddState.activeFilepath
            ? sddState.activeFilepath.split('/').slice(0, -1).join(' > ')
            : (sddState.activeStorageType === 'legacy_markdown' ? '.documents > specs' : '.documents > spec');
        breadcrumb.textContent = `${basePath} > ${filename} > Harness Engineering`;
    }

    const activeFlowTab = tabId === 'sdd-tab-checklist'
        ? 'sdd-tab-checklist'
        : tabId === 'sdd-tab-tests'
            ? 'sdd-tab-tests'
            : tabId === 'sdd-tab-dri'
                ? 'sdd-tab-dri'
                : tabId === 'sdd-tab-edit'
                    ? 'sdd-tab-edit'
                    : 'sdd-tab-preview';

    document.querySelectorAll('.sdd-flow-step').forEach(step => {
        step.classList.toggle('active', step.dataset.sddFlowTab === activeFlowTab);
    });
}

// --- Criteria Checklist ---
async function sddLoadCriteria() {
    if (!state.activeProjectId || !sddState.activeFilename) return;
    const container = document.getElementById('sdd-criteria-checklist-container');
    container.innerHTML = '<p style="color:var(--text-muted);padding:16px;">Carregando tarefas de .documents/task/task.md...</p>';
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/sdd/specs/${encodeURIComponent(sddState.activeFilename)}/criteria`, { headers: getHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao carregar tarefas');
        sddState.taskFilepath = data.filepath || '.documents/task/task.md';
        sddState.allCriteria = data.criteria || [];
        sddRenderCriteria();
    } catch (e) {
        container.innerHTML = `<p style="color:#ef4444;padding:16px;">Erro ao carregar tarefas de <code>.documents/task/task.md</code>.</p>`;
    }
}

function sddExtractActiveReqCode() {
    const source = [
        sddState.activeFilename || '',
        sddState.activeFilepath || '',
        sddState.activeContent || ''
    ].join('\n');
    const match = source.match(/\bREQ-\d{2,6}/i);
    return match ? match[0].toUpperCase() : '';
}

function sddNormalizeReqSequence(value = '') {
    const match = String(value).match(/\d+/);
    return match ? String(Number.parseInt(match[0], 10)) : '';
}

function sddTaskBelongsToReq(criterion, activeReq) {
    const activeSequence = sddNormalizeReqSequence(activeReq);
    if (!activeSequence) return true;

    const taskCode = String(criterion?.code || '').toUpperCase();
    const linkedReq = taskCode.match(/^TASK-REQ-(\d{2,6})-\d{3}$/i);
    const linkedRf = taskCode.match(/^TASK-RF-(\d{2,6})-\d{1,4}-\d{3}$/i);
    const linkedSequence = linkedReq?.[1] || linkedRf?.[1] || '';
    if (linkedSequence) {
        return sddNormalizeReqSequence(linkedSequence) === activeSequence;
    }

    const haystack = `${criterion?.code || ''} ${criterion?.text || ''} ${criterion?.title || ''}`.toUpperCase();
    return haystack.includes(activeReq.toUpperCase());
}

function sddGetCurrentReqCriteria() {
    const criteria = sddState.allCriteria || [];
    const activeReq = sddExtractActiveReqCode();
    if (!activeReq) return criteria;

    return criteria.filter(c => sddTaskBelongsToReq(c, activeReq));
}

function sddGetTaskSelection(source = 'current') {
    const key = source === 'project' ? 'project' : 'current';
    if (!sddState.taskSelection) {
        sddState.taskSelection = { current: new Set(), project: new Set() };
    }
    if (!(sddState.taskSelection[key] instanceof Set)) {
        sddState.taskSelection[key] = new Set(sddState.taskSelection[key] || []);
    }
    return sddState.taskSelection[key];
}

function sddPruneTaskSelection(source, criteria = []) {
    const selection = sddGetTaskSelection(source);
    const validLines = new Set(criteria.map(c => Number(c.line_no)));
    Array.from(selection).forEach(lineNo => {
        if (!validLines.has(Number(lineNo))) selection.delete(lineNo);
    });
}

function sddGetFilteredProjectCriteria() {
    const criteria = sddState.projectCriteria || [];
    const filter = sddState.projectTaskFilter || 'all';
    return criteria.filter(c => {
        if (filter === 'open') return !c.checked;
        if (filter === 'done') return c.checked;
        return true;
    });
}

function sddToggleTaskSelection(lineNo, source = 'current', checked = true) {
    const selection = sddGetTaskSelection(source);
    const normalizedLine = Number(lineNo);
    if (checked) selection.add(normalizedLine);
    else selection.delete(normalizedLine);
    if (source === 'project') sddRenderProjectTasks();
    else sddRenderCriteria();
}

function sddToggleAllTaskSelection(source = 'current', checked = true) {
    const visibleCriteria = source === 'project' ? sddGetFilteredProjectCriteria() : sddGetCurrentReqCriteria();
    const selection = sddGetTaskSelection(source);
    visibleCriteria.forEach(c => {
        const lineNo = Number(c.line_no);
        if (checked) selection.add(lineNo);
        else selection.delete(lineNo);
    });
    if (source === 'project') sddRenderProjectTasks();
    else sddRenderCriteria();
}

function sddRenderTaskBulkToolbar(criteria = [], source = 'current') {
    const selection = sddGetTaskSelection(source);
    const selectedCount = criteria.filter(c => selection.has(Number(c.line_no))).length;
    const allSelected = criteria.length > 0 && selectedCount === criteria.length;
    const sourceAttr = source === 'project' ? 'project' : 'current';
    return `
        <div class="sdd-task-bulk-toolbar">
            <button type="button"
                    class="sdd-task-bulk-select ${allSelected ? 'is-active' : ''}"
                    aria-pressed="${allSelected ? 'true' : 'false'}"
                    onclick="sddToggleAllTaskSelection('${sourceAttr}', ${allSelected ? 'false' : 'true'})">
                <i data-lucide="${allSelected ? 'check-square' : 'square'}"></i>
                <span>${allSelected ? 'Limpar seleção' : 'Selecionar todas'}</span>
            </button>
            <span class="sdd-task-bulk-count">${selectedCount}/${criteria.length} selecionadas</span>
            <button type="button"
                    class="sdd-task-bulk-delete"
                    ${selectedCount ? '' : 'disabled'}
                    onclick="sddDeleteSelectedTasks('${sourceAttr}')">
                <i data-lucide="trash-2"></i>
                <span>Excluir selecionadas</span>
            </button>
        </div>
    `;
}

function sddRenderCriteria() {
    const container = document.getElementById('sdd-criteria-checklist-container');
    const progressText = document.getElementById('sdd-checklist-progress-text');
    const progressFill = document.getElementById('sdd-progress-fill');
    const criteria = sddGetCurrentReqCriteria();
    sddPruneTaskSelection('current', criteria);

    if (!criteria.length) {
        const activeReq = sddExtractActiveReqCode();
        const hasAllTasks = (sddState.allCriteria || []).length > 0;
        const emptyMessage = hasAllTasks && activeReq
            ? `Nenhuma tarefa vinculada a <code>${escapeHtml(activeReq)}</code>.<br>Use a aba superior <strong>Task List</strong> para visualizar todas as tarefas do projeto.`
            : `Nenhuma tarefa encontrada em <code>${escapeHtml(sddState.taskFilepath || '.documents/task/task.md')}</code>.<br>Use o formato <code>- [ ] TASK-RF-0000-00-001: Título curto</code> ou <code>- [ ] TASK-QA-ID-001: - Título curto</code>.`;
        container.innerHTML = `
            <div style="text-align:center;padding:40px;color:var(--text-muted);">
                <i data-lucide="clipboard-list" style="width:40px;height:40px;margin-bottom:12px;opacity:0.4;"></i>
                <p>${emptyMessage}</p>
            </div>`;
        if (window.lucide) lucide.createIcons();
        progressText.textContent = '0/0 concluídos';
        progressFill.style.width = '0%';
        return;
    }

    const total = criteria.length;
    const done = criteria.filter(c => c.checked).length;
    const pct = total ? Math.round((done / total) * 100) : 0;
    progressText.textContent = `${done}/${total} concluídos (${pct}%)`;
    progressFill.style.width = `${pct}%`;

    const selection = sddGetTaskSelection('current');
    container.innerHTML = `
        ${sddRenderTaskBulkToolbar(criteria, 'current')}
        ${criteria.map(c => {
            const selected = selection.has(Number(c.line_no));
            return `
        <div class="sdd-criteria-row ${c.checked ? 'checked' : ''} ${selected ? 'is-selected' : ''}" data-line="${c.line_no}">
            <button type="button"
                    class="sdd-task-row-select ${selected ? 'is-selected' : ''}"
                    role="checkbox"
                    aria-checked="${selected ? 'true' : 'false'}"
                    aria-label="${selected ? 'Remover task da seleção' : 'Selecionar task para exclusão em massa'}"
                    onclick="sddToggleTaskSelection(${c.line_no}, 'current', ${selected ? 'false' : 'true'})">
                <i data-lucide="${selected ? 'check-square' : 'square'}"></i>
            </button>
            <button type="button"
                    class="sdd-task-toggle ${c.checked ? 'is-checked' : ''}"
                    role="checkbox"
                    aria-checked="${c.checked ? 'true' : 'false'}"
                    aria-label="${c.checked ? 'Marcar tarefa como pendente' : 'Marcar tarefa como concluída'}"
                    onclick="sddToggleCriteria(${c.line_no}, ${c.checked ? 'false' : 'true'}, 'current')">
                <span class="sdd-task-toggle-dot"></span>
            </button>
            <span class="sdd-criteria-text">${escapeHtml(c.text)}</span>
            <div class="sdd-task-actions">
                <button type="button"
                        class="sdd-task-detail-action"
                        title="Visualizar detalhe da task"
                        aria-label="Visualizar detalhe da task"
                        onclick="sddOpenTaskDetail(${c.line_no}, 'current')">
                    <i data-lucide="file-text"></i>
                </button>
                <button type="button"
                        class="sdd-task-detail-action"
                        title="Enviar task para Execute"
                        aria-label="Enviar task para Execute"
                        onclick="sddSetTaskStatus(${c.line_no}, 'execute', 'current')">
                    <i data-lucide="play"></i>
                </button>
                <button type="button"
                        class="sdd-task-detail-action sdd-task-delete-action"
                        title="Excluir task"
                        aria-label="Excluir task"
                        onclick="sddDeleteTask(${c.line_no})">
                    <i data-lucide="trash-2"></i>
                </button>
            </div>
        </div>`;
        }).join('')}
    `;
    if (window.lucide) lucide.createIcons();
}

async function sddLoadProjectTasks() {
    if (!state.activeProjectId) return;
    const container = document.getElementById('sdd-project-tasks-container');
    if (container) {
        container.innerHTML = '<p style="color:var(--text-muted);padding:16px;">Carregando todas as tarefas de .documents/task/task.md...</p>';
    }
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/sdd/tasks`, { headers: getHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao carregar tarefas');
        sddState.taskFilepath = data.filepath || '.documents/task/task.md';
        sddState.projectCriteria = data.criteria || [];
        sddRenderProjectTasks();
    } catch (e) {
        if (container) {
            container.innerHTML = `<p style="color:#ef4444;padding:16px;">Erro ao carregar tarefas de <code>.documents/task/task.md</code>.</p>`;
        }
    }
}

function sddRenderProjectTasks() {
    const container = document.getElementById('sdd-project-tasks-container');
    const progressText = document.getElementById('sdd-project-tasks-progress-text');
    const progressFill = document.getElementById('sdd-project-tasks-progress-fill');
    const criteria = sddState.projectCriteria || [];
    const filter = sddState.projectTaskFilter || 'all';
    if (!container) return;
    sddPruneTaskSelection('project', criteria);

    document.querySelectorAll('[data-sdd-task-filter]').forEach(button => {
        const isActive = button.dataset.sddTaskFilter === filter;
        button.classList.toggle('active', isActive);
        button.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });

    if (!criteria.length) {
        container.innerHTML = `
            <div style="text-align:center;padding:48px;color:var(--text-muted);">
                <i data-lucide="list-checks" style="width:40px;height:40px;margin-bottom:12px;opacity:0.4;"></i>
                <p>Nenhuma tarefa encontrada em <code>${escapeHtml(sddState.taskFilepath || '.documents/task/task.md')}</code>.</p>
            </div>`;
        if (progressText) progressText.textContent = '0/0 concluídos';
        if (progressFill) progressFill.style.width = '0%';
        if (window.lucide) lucide.createIcons();
        return;
    }

    const total = criteria.length;
    const done = criteria.filter(c => c.checked).length;
    const pct = total ? Math.round((done / total) * 100) : 0;
    if (progressText) progressText.textContent = `${done}/${total} concluídos (${pct}%)`;
    if (progressFill) progressFill.style.width = `${pct}%`;

    const filteredCriteria = sddGetFilteredProjectCriteria();

    if (!filteredCriteria.length) {
        const label = filter === 'open' ? 'abertas' : filter === 'done' ? 'concluídas' : 'cadastradas';
        container.innerHTML = `
            <div style="text-align:center;padding:48px;color:var(--text-muted);">
                <i data-lucide="list-filter" style="width:40px;height:40px;margin-bottom:12px;opacity:0.4;"></i>
                <p>Nenhuma tarefa ${label} neste filtro.</p>
            </div>`;
        if (window.lucide) lucide.createIcons();
        return;
    }

    const selection = sddGetTaskSelection('project');
    container.innerHTML = `
        ${sddRenderTaskBulkToolbar(filteredCriteria, 'project')}
        ${filteredCriteria.map(c => {
            const selected = selection.has(Number(c.line_no));
            return `
        <div class="sdd-criteria-row ${c.checked ? 'checked' : ''} ${selected ? 'is-selected' : ''}" data-line="${c.line_no}">
            <button type="button"
                    class="sdd-task-row-select ${selected ? 'is-selected' : ''}"
                    role="checkbox"
                    aria-checked="${selected ? 'true' : 'false'}"
                    aria-label="${selected ? 'Remover task da seleção' : 'Selecionar task para exclusão em massa'}"
                    onclick="sddToggleTaskSelection(${c.line_no}, 'project', ${selected ? 'false' : 'true'})">
                <i data-lucide="${selected ? 'check-square' : 'square'}"></i>
            </button>
            <button type="button"
                    class="sdd-task-toggle ${c.checked ? 'is-checked' : ''}"
                    role="checkbox"
                    aria-checked="${c.checked ? 'true' : 'false'}"
                    aria-label="${c.checked ? 'Marcar tarefa como pendente' : 'Marcar tarefa como concluída'}"
                    onclick="sddToggleCriteria(${c.line_no}, ${c.checked ? 'false' : 'true'}, 'project')">
                <span class="sdd-task-toggle-dot"></span>
            </button>
            <span class="sdd-criteria-text">${escapeHtml(c.text)}</span>
            <div class="sdd-task-actions">
                <button type="button"
                        class="sdd-task-detail-action"
                        title="Visualizar detalhe da task"
                        aria-label="Visualizar detalhe da task"
                        onclick="sddOpenTaskDetail(${c.line_no}, 'project')">
                    <i data-lucide="file-text"></i>
                </button>
                <button type="button"
                        class="sdd-task-detail-action"
                        title="Enviar task para Execute"
                        aria-label="Enviar task para Execute"
                        onclick="sddSetTaskStatus(${c.line_no}, 'execute', 'project')">
                    <i data-lucide="play"></i>
                </button>
                <button type="button"
                        class="sdd-task-detail-action sdd-task-delete-action"
                        title="Excluir task"
                        aria-label="Excluir task"
                        onclick="sddDeleteTask(${c.line_no}, 'project')">
                    <i data-lucide="trash-2"></i>
                </button>
            </div>
        </div>`;
        }).join('')}
    `;
    if (window.lucide) lucide.createIcons();
}

function sddSetProjectTaskFilter(filter) {
    sddState.projectTaskFilter = ['all', 'open', 'done'].includes(filter) ? filter : 'all';
    sddGetTaskSelection('project').clear();
    sddRenderProjectTasks();
}

const SDD_TASK_ID_PATTERN = /\bTASK-(?:REQ-\d{2,6}|RF-\d{2,6}-\d{1,4}|QA-[A-Z0-9-]+)-\d{3}\b/i;

function sddExtractTaskId(taskText = '') {
    const match = taskText.match(SDD_TASK_ID_PATTERN);
    return match ? match[0].toUpperCase() : '';
}

function sddExtractTaskTitle(taskText = '') {
    return taskText
        .replace(SDD_TASK_ID_PATTERN, '')
        .replace(/^:?\s*/, '')
        .replace(/^\s*-\s*/, '')
        .trim();
}

function sddExtractTaskDetailSection(detailsMarkdown = '', taskId = '') {
    if (!detailsMarkdown || !taskId) return '';
    const lines = detailsMarkdown.split(/\r?\n/);
    const startIndex = lines.findIndex(line => line.toUpperCase().includes(taskId.toUpperCase()));
    if (startIndex < 0) return '';

    const startHeading = lines[startIndex].match(/^(#{1,6})\s+/);
    const startLevel = startHeading ? startHeading[1].length : 2;
    let endIndex = lines.length;

    for (let i = startIndex + 1; i < lines.length; i += 1) {
        const heading = lines[i].match(/^(#{1,6})\s+/);
        if (heading && heading[1].length <= startLevel) {
            endIndex = i;
            break;
        }
    }

    return lines.slice(startIndex, endIndex).join('\n').trim();
}

function sddNormalizeTaskDetailMarkdown(section = '', taskId = '') {
    const lines = section.split(/\r?\n/);
    if (lines[0] && lines[0].toUpperCase().includes(taskId.toUpperCase())) {
        lines.shift();
    }
    return lines.join('\n').trim();
}

async function sddEnsureTaskDetailsLoaded(force = false) {
    if (!state.activeProjectId) return '';
    if (!force && sddState.projectDocuments.task_details) {
        return sddState.projectDocuments.task_details;
    }
    const res = await fetch(`/api/projects/${state.activeProjectId}/sdd/project-documents/task_details`, { headers: getHeaders() });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Erro ao carregar task.details.md');
    sddState.projectDocuments.task_details = data.content || '';
    return sddState.projectDocuments.task_details;
}

function sddGetTaskRow(lineNo, source = 'current') {
    const containerId = source === 'project' ? 'sdd-project-tasks-container' : 'sdd-criteria-checklist-container';
    return document.querySelector(`#${containerId} .sdd-criteria-row[data-line="${lineNo}"]`);
}

async function sddOpenTaskDetail(lineNo, source = 'current') {
    const row = sddGetTaskRow(lineNo, source);
    const taskText = row?.querySelector('.sdd-criteria-text')?.textContent?.trim() || '';
    const taskId = sddExtractTaskId(taskText);
    const drawer = document.getElementById('sdd-task-detail-drawer');
    const backdrop = document.getElementById('sdd-task-detail-backdrop');
    const idEl = document.getElementById('sdd-task-detail-id');
    const titleEl = document.getElementById('sdd-task-detail-title');
    const body = document.getElementById('sdd-task-detail-body');
    if (!drawer || !body) return;

    if (idEl) idEl.textContent = taskId || 'TASK';
    if (titleEl) titleEl.textContent = taskText || 'Detalhe da tarefa';
    body.innerHTML = `
        <div class="sdd-task-detail-loading">
            <i class="fa-solid fa-circle-notch fa-spin"></i>
            <span>Carregando detalhe da tarefa...</span>
        </div>
    `;
    drawer.classList.add('is-open');
    backdrop?.classList.add('is-open');
    drawer.setAttribute('aria-hidden', 'false');

    try {
        const details = await sddEnsureTaskDetailsLoaded(true);
        const section = sddExtractTaskDetailSection(details, taskId);
        if (!taskId) {
            body.innerHTML = `
                <div class="sdd-task-detail-empty">
                    <i data-lucide="badge-alert"></i>
                    <h5>ID da task não encontrado</h5>
                    <p>Use o formato <code>TASK-RF-0000-00-001: Título curto</code> ou <code>TASK-QA-ID-001: - Título curto</code> em .documents/task/task.md.</p>
                </div>
            `;
        } else if (!section) {
            body.innerHTML = `
                <div class="sdd-task-detail-empty">
                    <i data-lucide="file-question"></i>
                    <h5>Detalhe não encontrado em task.details.md</h5>
                    <p>Peça para o GPT Action criar ou atualizar a seção <code>## Plano — ${escapeHtml(taskId)}</code> em <code>.documents/task/task.details.md</code>.</p>
                </div>
                <div class="sdd-task-detail-reference">
                    <span>Tarefa selecionada</span>
                    <strong>${escapeHtml(taskText)}</strong>
                </div>
            `;
        } else {
            body.innerHTML = `
                <div class="qa-detail-section">
                    <h5>Resumo</h5>
                    <p>${escapeHtml(sddExtractTaskTitle(taskText) || taskText || 'Sem título.')}</p>
                    <div class="qa-detail-pills">
                        <span class="qa-pill qa-status-open">Task</span>
                        <span class="qa-pill qa-severity-medium">task.details</span>
                        <span class="qa-pill qa-category-functional">${escapeHtml(taskId)}</span>
                    </div>
                </div>
                <div class="qa-detail-section">
                    <h5>Plano detalhado</h5>
                    <div class="markdown-render sdd-task-detail-markdown">
                        ${sddRenderMarkdown(sddNormalizeTaskDetailMarkdown(section, taskId))}
                    </div>
                </div>
                <div class="qa-detail-section">
                    <h5>Origem</h5>
                    <dl class="qa-detail-list">
                        <dt>Task List</dt><dd>.documents/task/task.md</dd>
                        <dt>Detalhe</dt><dd>.documents/task/task.details.md</dd>
                        <dt>Linha</dt><dd>${lineNo}</dd>
                    </dl>
                </div>
            `;
        }
    } catch (err) {
        body.innerHTML = `
            <div class="sdd-task-detail-empty is-error">
                <i data-lucide="triangle-alert"></i>
                <h5>Erro ao carregar detalhe</h5>
                <p>${escapeHtml(err.message)}</p>
            </div>
        `;
    }
    if (window.lucide) lucide.createIcons();
}

function sddCloseTaskDetail() {
    const drawer = document.getElementById('sdd-task-detail-drawer');
    const backdrop = document.getElementById('sdd-task-detail-backdrop');
    drawer?.classList.remove('is-open');
    backdrop?.classList.remove('is-open');
    drawer?.setAttribute('aria-hidden', 'true');
}

function sddSetTaskStatus(lineNo, value, source = 'current') {
    if (value !== 'execute') return;
    const row = sddGetTaskRow(lineNo, source);
    const taskText = row?.querySelector('.sdd-criteria-text')?.textContent?.trim() || '';
    sddState.executeTask = { lineNo, text: taskText };
    sddPopulateExecuteInstructions(taskText);
    if (source === 'project') {
        sddSwitchHarnessPanel('harness-specs-panel');
    }
    sddSwitchTab('sdd-tab-tests');
}

async function sddDeleteTask(lineNo, source = 'current') {
    if (!state.activeProjectId) return;
    const row = sddGetTaskRow(lineNo, source);
    const taskText = row?.querySelector('.sdd-criteria-text')?.textContent?.trim() || '';
    if (!taskText) return;

    const confirmed = await gitideConfirm({
        title: 'Excluir task',
        kicker: 'Task List',
        message: `Tem certeza que deseja excluir <strong>${escapeHtml(taskText)}</strong>?<br><small>A task e seu detalhe correspondente serão removidos.</small>`,
        confirmText: 'Excluir task',
        variant: 'danger'
    });
    if (!confirmed) return;

    const deleteButton = row.querySelector('.sdd-task-delete-action');
    if (deleteButton) {
        deleteButton.disabled = true;
        deleteButton.classList.add('is-loading');
    }

    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/sdd/tasks/${lineNo}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao excluir task');

        sddCloseTaskDetail();
        gitideNotify({
            title: 'Task excluída',
            message: `${data.task_code || 'A tarefa'} foi removida da Task List.`,
            variant: 'success'
        });
        await sddLoadProjectTasks();
        if (sddState.activeFilename) await sddLoadCriteria();
        await sddLoadProjectDocuments();
    } catch (error) {
        if (deleteButton) {
            deleteButton.disabled = false;
            deleteButton.classList.remove('is-loading');
        }
        gitideNotify({ title: 'Falha ao excluir task', message: error.message, variant: 'danger' });
    }
}

async function sddDeleteSelectedTasks(source = 'current') {
    if (!state.activeProjectId) return;
    const selection = sddGetTaskSelection(source);
    const lineNos = Array.from(selection).map(Number).filter(Boolean);
    if (!lineNos.length) return;

    const confirmed = await gitideConfirm({
        title: 'Excluir tasks selecionadas',
        kicker: 'Task List',
        message: `Tem certeza que deseja excluir <strong>${lineNos.length} task(s)</strong>?<br><small>As tasks e seus tópicos correspondentes em task.details.md serão removidos.</small>`,
        confirmText: 'Excluir selecionadas',
        variant: 'danger'
    });
    if (!confirmed) return;

    document.querySelectorAll('.sdd-task-bulk-delete').forEach(button => {
        button.disabled = true;
        button.classList.add('is-loading');
    });

    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/sdd/tasks/bulk`, {
            method: 'DELETE',
            headers: { ...getHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ line_nos: lineNos })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erro ao excluir tasks');

        selection.clear();
        sddGetTaskSelection(source === 'project' ? 'current' : 'project').clear();
        sddCloseTaskDetail();
        gitideNotify({
            title: 'Tasks excluídas',
            message: `${data.tasks?.length || lineNos.length} task(s) removidas da Task List.`,
            variant: 'success'
        });
        await sddLoadProjectTasks();
        if (sddState.activeFilename) await sddLoadCriteria();
        await sddLoadProjectDocuments();
    } catch (error) {
        document.querySelectorAll('.sdd-task-bulk-delete').forEach(button => {
            button.disabled = false;
            button.classList.remove('is-loading');
        });
        gitideNotify({ title: 'Falha ao excluir tasks', message: error.message, variant: 'danger' });
    }
}

function sddPopulateExecuteInstructions(taskText) {
    const textarea = document.getElementById('sdd-execute-instructions');
    if (!textarea) return;
    const isProjectSpec = sddState.activeStorageType === 'project_spec_file' || sddState.isDraft;
    const specify = isProjectSpec
        ? sddState.activeContent
        : sddExtractSection(sddState.activeContent, ['Specify', 'Especificação', 'Requisitos']);
    const design = isProjectSpec
        ? sddState.projectDocuments.design
        : sddExtractSection(sddState.activeContent, ['Design', 'Planejamento', 'Arquitetura']);
    const dri = isProjectSpec
        ? sddState.projectDocuments.dri
        : sddExtractSection(sddState.activeContent, ['DRI', 'Documento de Requisito de Interface', 'Requisito de Interface']);
    const taskDocument = sddState.projectDocuments.task || '';
    textarea.value = `# Execute\n\n## Tarefa selecionada\n${taskText || 'Nenhuma tarefa selecionada.'}\n\n## Instruções para IA/agente\nExecute estritamente esta tarefa contra o REQ selecionado, os documentos vivos do projeto e a Task List abaixo. Não implemente escopo fora da task selecionada. Ao terminar, indique arquivos alterados e testes executados.\n\n## REQ de referência\n${specify || 'REQ não encontrado.'}\n\n## Design vivo de referência\n${design || 'Design não encontrado.'}\n\n## DRI vivo de referência\n${dri || 'DRI não encontrado ou não aplicável.'}\n\n## Task List viva de referência\n${taskDocument || 'Task List não encontrada.'}\n`;
}

async function sddToggleCriteria(lineNo, checked, source = 'current') {
    if (!state.activeProjectId) return;
    if (source !== 'project' && !sddState.activeFilename) return;
    // Optimistic UI update
    const row = sddGetTaskRow(lineNo, source);
    if (row) row.classList.toggle('checked', checked);

    try {
        const url = source === 'project'
            ? `/api/projects/${state.activeProjectId}/sdd/tasks/criteria`
            : `/api/projects/${state.activeProjectId}/sdd/specs/${encodeURIComponent(sddState.activeFilename)}/criteria`;
        await fetch(url, {
            method: 'POST',
            headers: { ...getHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ criteria: [{ line_no: lineNo, checked }] })
        });
        if (source === 'project') {
            await sddLoadProjectTasks();
            if (sddState.activeFilename) await sddLoadCriteria();
        } else {
            await sddLoadCriteria();
        }
        await sddLoadProjectDocuments();
        sddPopulateStageEditors(sddState.activeContent);
    } catch (e) {
        console.error('Erro ao atualizar critério:', e);
    }
}

// --- Save Spec ---
async function sddSaveSpec() {
    if (!state.activeProjectId) return;
    const filename = document.getElementById('sdd-edit-filename').value.trim();
    const content = document.getElementById('sdd-spec-editor-textarea').value;
    if (!filename.endsWith('.md')) {
        alert('O nome do arquivo deve terminar com .md');
        return;
    }
    let btn = null;
    if (sddState.activeTab === 'sdd-tab-preview') btn = document.getElementById('btn-sdd-save-specify');
    else if (sddState.activeTab === 'sdd-tab-rfs') btn = document.getElementById('btn-sdd-save-rf');
    else if (sddState.activeTab === 'sdd-tab-edit') btn = document.getElementById('btn-sdd-save-design');
    else if (sddState.activeTab === 'sdd-tab-dri') btn = document.getElementById('btn-sdd-save-dri');
    else if (sddState.activeTab === 'sdd-tab-task-details') btn = document.getElementById('btn-sdd-save-task-details');
    
    let originalHtml = '';
    if (btn) {
        btn.disabled = true;
        originalHtml = btn.innerHTML;
        btn.innerHTML = '<i data-lucide="loader-2" style="animation:spin 1s linear infinite;"></i> Salvando...';
        if (window.lucide) lucide.createIcons();
    }
    
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/sdd/specs`, {
            method: 'POST',
            headers: { ...getHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename, content, overwrite: !sddState.isDraft })
        });
        const data = await res.json();
        if (res.status === 409) {
            gitideNotify({ title: 'Arquivo já existe', message: 'Crie o requisito com outro título ou gere um novo ID.', variant: 'warning' });
            return;
        }
        if (data.status === 'success') {
            sddState.activeFilename = filename;
            sddState.activeContent = content;
            sddState.activeStorageType = data.storage_type || 'project_spec_file';
            sddState.activeFilepath = data.filepath || `.documents/requirements/${filename}`;
            sddState.isDraft = false;
            sddPopulatePreview(content);
            sddSetActiveSpecHeader({ filename, content });
            await sddLoadSpecs(true);
            sddSwitchTab('sdd-tab-preview');
        } else {
            alert('Erro ao salvar: ' + (data.detail || 'Erro desconhecido'));
        }
    } catch (e) {
        alert('Erro ao salvar especificação: ' + e.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalHtml || '<i data-lucide="save"></i> Salvar';
            if (window.lucide) lucide.createIcons();
        }
    }
}

async function sddSaveStage(stage) {
    if (!state.activeProjectId) return;
    const filenameInput = document.getElementById('sdd-edit-filename');
    let filename = filenameInput?.value.trim() || sddState.activeFilename;
    const specifyEditor = document.getElementById('sdd-specify-editor');
    const designEditor = document.getElementById('sdd-design-editor');
    const driEditor = document.getElementById('sdd-dri-editor');
    const isProjectSpec = sddState.activeStorageType === 'project_spec_file' || sddState.isDraft;

    if (!filename) {
        const title = sddExtractTitle(specifyEditor?.value || '') || 'nova_spec';
        filename = title.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '') + '.md';
        if (filenameInput) filenameInput.value = filename;
    }
    if (!filename.endsWith('.md')) filename += '.md';

    if (isProjectSpec && (stage === 'design' || stage === 'dri')) {
        const content = stage === 'design' ? (designEditor?.value || '') : (driEditor?.value || '');
        try {
            const res = await fetch(`/api/projects/${state.activeProjectId}/sdd/project-documents/${stage}`, {
                method: 'POST',
                headers: { ...getHeaders(), 'Content-Type': 'application/json' },
                body: JSON.stringify({ content })
            });
            const data = await res.json();
            if (!res.ok || data.status !== 'success') throw new Error(data.detail || data.message || 'Erro ao salvar documento');
            sddState.projectDocuments[stage] = content;
            gitideNotify({ title: 'Documento salvo', message: stage === 'design' ? 'design.md salvo com sucesso.' : 'dri.md salvo com sucesso.', variant: 'success' });
            sddPopulateStageEditors(sddState.activeContent);
            sddSwitchTab(stage === 'dri' ? 'sdd-tab-dri' : 'sdd-tab-edit');
        } catch (e) {
            gitideNotify({ title: 'Erro ao salvar documento', message: e.message, variant: 'danger' });
        }
        return;
    }

    let content = sddState.activeContent || `# ${sddExtractTitle(specifyEditor?.value || document.getElementById('sdd-rf-editor')?.value || '') || 'Nova Feature'}\n`;
    if (stage === 'specify') {
        content = isProjectSpec
            ? (specifyEditor?.value || '')
            : sddReplaceSection(content, ['Specify', 'Especificação', 'Requisitos'], '## 1. Specify - Especificação', specifyEditor?.value || '');
        document.getElementById('sdd-spec-editor-textarea').value = content;
    } else if (stage === 'rf') {
        content = document.getElementById('sdd-rf-editor')?.value || '';
        document.getElementById('sdd-spec-editor-textarea').value = content;
    }

    if (!isProjectSpec && stage === 'design') {
        content = sddReplaceSection(content, ['Design', 'Planejamento', 'Arquitetura'], '## 2. Design - Planejamento', designEditor?.value || '');
        document.getElementById('sdd-spec-editor-textarea').value = content;
    }

    if (!isProjectSpec && stage === 'dri') {
        content = sddReplaceSection(content, ['DRI', 'Documento de Requisito de Interface', 'Requisito de Interface'], '## 3. DRI - Documento de Requisito de Interface', driEditor?.value || '');
        document.getElementById('sdd-spec-editor-textarea').value = content;
    }

    if (filenameInput) filenameInput.value = filename;
    await sddSaveSpec();
    sddState.activeContent = content;
    sddPopulateStageEditors(content);
    sddSwitchTab(stage === 'dri' ? 'sdd-tab-dri' : stage === 'design' ? 'sdd-tab-edit' : stage === 'rf' ? 'sdd-tab-rfs' : 'sdd-tab-preview');
}

// --- Delete Spec ---
async function sddDeleteSpec() {
    if (!state.activeProjectId || !sddState.activeFilename) return;
    const confirmed = await gitideConfirm({
        title: 'Excluir requisito',
        kicker: 'Spec-Driven Development',
        message: `Tem certeza que deseja excluir <strong>${sddState.activeFilename}</strong>? Esta ação é irreversível.`,
        confirmText: 'Excluir',
        cancelText: 'Cancelar',
        variant: 'danger'
    });
    if (!confirmed) return;
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/sdd/specs/${encodeURIComponent(sddState.activeFilename)}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        const data = await res.json();
        if (data.status === 'success') {
            sddState.activeFilename = null;
            sddState.activeContent = '';
            sddState.isDraft = false;
            // Reset workspace
            document.getElementById('sdd-workspace-nav-tabs').style.display = 'none';
            document.getElementById('sdd-active-spec-title').textContent = 'Nenhuma Especificação Selecionada';
            document.getElementById('sdd-active-spec-filename').style.display = 'none';
            sddSwitchTab('sdd-tab-preview');
            document.getElementById('sdd-spec-markdown-render').innerHTML = `
                <div class="sdd-empty-workspace">
                    <i data-lucide="sparkles" style="width:48px;height:48px;color:var(--color-primary);opacity:0.6;margin-bottom:12px;"></i>
                    <h3>Desenvolvimento Orientado por Especificação (SDD)</h3>
                    <p>Selecione uma especificação da lista à esquerda ou utilize o assistente para criar uma nova e orientar a IA.</p>
                    <button class="btn btn-primary" id="btn-switch-to-ia-generator"><i data-lucide="plus-circle"></i> Assistente de Especificação IA</button>
                </div>`;
            if (window.lucide) lucide.createIcons();
            // Re-bind wizard button
            const wb = document.getElementById('btn-switch-to-ia-generator');
            if (wb) wb.addEventListener('click', () => sddSwitchTab('sdd-tab-ia-wizard'));
            await sddLoadSpecs(true);
            gitideNotify({ title: 'Requisito excluído', message: 'A especificação foi removida do projeto.', variant: 'success' });
        } else {
            gitideNotify({ title: 'Erro ao excluir', message: data.detail || 'Erro desconhecido', variant: 'danger' });
        }
    } catch (e) {
        gitideNotify({ title: 'Erro ao excluir especificação', message: e.message, variant: 'danger' });
    }
}

// --- New Manual Spec ---
function sddSlugify(value) {
    return (value || '')
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-z0-9]+/g, '_')
        .replace(/^_|_$/g, '')
        .slice(0, 60) || 'requisito';
}

function sddGenerateRequirementId() {
    const sources = [
        ...(sddState.specs || []).map(spec => `${spec.filename || ''} ${spec.title || ''}`),
        sddState.activeFilename || '',
        sddState.activeContent || ''
    ];
    const usedNumbers = sources
        .map(source => String(source || '').match(/\bREQ[-_ ]?(\d{3,6})/i))
        .filter(Boolean)
        .map(match => Number(match[1]))
        .filter(Number.isFinite);

    const next = usedNumbers.length ? Math.max(...usedNumbers) + 1 : 1001;
    return `REQ-${String(next).padStart(4, '0')}`;
}

function sddBuildUniqueRequirementFilename(id, title, kind = 'req', parentId = null) {
    const slug = sddSlugify(title);
    
    let baseFilename = '';
    let folderPath = '';
    
    if (kind === 'rf') {
        // Estrutura achatada: RF-ID-TITLE.md em functional-requirements
        folderPath = `functional-requirements/`;
        baseFilename = `${id.toUpperCase()}-${slug}`;
    } else {
        // Estrutura achatada: REQ-ID-TITLE.md em requirements
        folderPath = `requirements/`;
        baseFilename = `${id.toUpperCase()}-${slug}`;
    }
    
    const existing = new Set((sddState.specs || []).map(spec => (spec.filename || '').toLowerCase()));
    
    let filename = `${folderPath}${baseFilename}.md`;
    let suffix = 2;
    while (existing.has(filename.toLowerCase())) {
        filename = `${folderPath}${baseFilename}_${suffix}.md`;
        suffix += 1;
    }
    return filename;
}

function sddBuildDriTemplate(id, interfaceName) {
    const isPlaceholder = !id || id === 'REQ-XXXX';
    const riCode = isPlaceholder ? 'RI-XX' : `RI-${id.replace(/^REQ-?/i, '')}`;
    const relatedRf = isPlaceholder ? '[Ex.: RF-01 - Gestão de Perfil Profissional]' : id;
    return `## 3. DRI - Documento de Requisito de Interface

### ${riCode} - ${interfaceName}

### 1. Identificação da Interface

| Campo | Valor |
| --- | --- |
| Código | ${riCode} |
| Nome da interface | ${interfaceName} |
| Módulo | [Ex.: Profissionais / Conta] |
| RF relacionado | ${relatedRf} |
| SubRFs relacionados | [Ex.: SubRF-01.01, SubRF-01.02] |
| Tipo de interface | Página \\| Modal \\| Drawer \\| Formulário \\| Grid \\| Dashboard \\| Detalhe |
| Perfil de usuário | [Ex.: Profissional, Admin, Gestor, Cliente] |
| Dispositivo prioritário | Desktop \\| Mobile \\| Responsivo |
| Objetivo da tela | [Descrever em uma frase o resultado operacional esperado] |

### 2. Objetivo da Interface

Descreva o propósito da tela, quais dados ou decisões ela sustenta, qual resultado operacional deve produzir e como se conecta ao requisito ${id}.

### 3. Contexto de Uso

| Campo | Valor |
| --- | --- |
| Quem usa | [Perfil principal de usuário] |
| Quando usa | [Momento do fluxo ou rotina operacional] |
| Por que usa | [Motivação e necessidade do usuário] |
| Gatilho de acesso | [Menu, onboarding, notificação, link, workflow, ação anterior] |
| Resultado esperado | [Estado desejado após uso da interface] |

### 4. Arquitetura da Informação

| Ordem | Seção | Objetivo | Tipo de componente |
| --- | --- | --- | --- |
| 1 | [Nome da seção] | [Objetivo funcional da seção] | [Header, formulário, lista, tabela, card, painel] |
| 2 | [Nome da seção] | [Objetivo funcional da seção] | [Tipo de componente] |
| 3 | [Nome da seção] | [Objetivo funcional da seção] | [Tipo de componente] |

### 5. Mapa de Componentes

| Componente | Tipo | Obrigatório | Editável | Comportamento esperado |
| --- | --- | --- | --- | --- |
| [Nome do campo/ação] | [Input, select, badge, button] | Sim/Não | Sim/Não | [Validação, máscara, permissão, estado ou regra de interação] |
| [Nome do campo/ação] | [Tipo] | Sim/Não | Sim/Não | [Comportamento] |
| [Nome do campo/ação] | [Tipo] | Sim/Não | Sim/Não | [Comportamento] |

### 6. Regras de Exibição

| Código | Regra | Comportamento |
| --- | --- | --- |
| RI-RG-01 | [Nome da regra visual ou condicional] | [Comportamento esperado na interface] |
| RI-RG-02 | [Nome da regra] | [Comportamento esperado] |
| RI-RG-03 | [Nome da regra] | [Comportamento esperado] |

### 7. Estados da Interface

| Estado | Descrição | Comportamento visual |
| --- | --- | --- |
| Loading | Dados sendo carregados. | Skeleton, spinner ou placeholder consistente. |
| Empty | Não há dados ou configuração iniciada. | Mensagem orientativa e CTA pertinente. |
| View | Dados exibidos para leitura. | Campos organizados e ações secundárias discretas. |
| Edit | Usuário editando informações. | Campos habilitados e botões de ação visíveis. |
| Saving | Salvamento em andamento. | Ação principal desabilitada com feedback. |
| Success | Operação concluída. | Toast ou mensagem de confirmação. |
| Error | Falha ao carregar, validar ou salvar. | Mensagem clara e ação de nova tentativa. |
| Read-only | Usuário sem permissão de edição. | Campos bloqueados e aviso de restrição. |

### 8. Fluxo de Interação

| Ação do usuário | Resposta da interface | Resultado esperado |
| --- | --- | --- |
| Acessar interface | Sistema carrega dados e estados | Tela exibe informações atuais |
| Clicar em editar | Campos autorizados são habilitados | Usuário pode alterar dados |
| Preencher campo obrigatório | Sistema valida preenchimento | Dados ficam aptos para salvamento |
| Clicar em salvar | Sistema valida e envia dados | Informação é atualizada |
| Campo inválido | Erro contextual é exibido | Usuário entende o ajuste necessário |
| Cancelar | Alterações são descartadas | Dados anteriores são mantidos |

### 9. Mapeamento de Dados

| Campo na tela | Nome técnico | Origem | Editável | Obrigatório |
| --- | --- | --- | --- | --- |
| [Campo] | [snake_case] | [Collection, API, sistema, usuário] | Sim/Não | Sim/Não |
| [Campo] | [snake_case] | [Origem] | Sim/Não | Sim/Não |
| [Campo] | [snake_case] | [Origem] | Sim/Não | Sim/Não |

### 10. Hierarquia Visual

**Prioridade Alta**

- [Informações críticas, status, ação principal, alertas e pendências.]

**Prioridade Média**

- [Dados de apoio, seções recorrentes, filtros, grupos secundários.]

**Prioridade Baixa**

- [Informações auxiliares, histórico, textos explicativos e suporte.]

### 11. Microcopy da Interface

| Elemento | Texto sugerido | Observação |
| --- | --- | --- |
| Título da tela | [Texto objetivo e operacional] | [Evitar promessa genérica] |
| Descrição curta | [Explicar a finalidade da tela] | [Uma ou duas frases no máximo] |
| CTA principal | [Salvar alterações / Enviar para análise] | [Verbo de ação claro] |
| Erro de validação | [Informe o ajuste necessário] | [Mensagem contextual] |
| Toast de sucesso | [Alterações salvas com sucesso] | [Confirmação curta] |

### 12. Responsividade

| Dispositivo | Comportamento esperado |
| --- | --- |
| Desktop | [Layout, colunas, largura, painéis laterais, tabela ou formulário completo] |
| Tablet | [Reorganização de colunas, navegação e ações] |
| Mobile | [Ordem das seções, ações fixas, campos em uma coluna, estados críticos] |

### 13. Acessibilidade

| Item | Critério |
| --- | --- |
| Labels | [Todos os campos possuem label persistente e claro] |
| Contraste | [Cores atendem leitura confortável e função semântica] |
| Navegação por teclado | [Foco visível e ordem lógica] |
| Mensagens de erro | [Erro próximo ao campo e linguagem acionável] |
| Leitores de tela | [Nomes acessíveis, estados e regiões relevantes] |

### 14. Critérios de Aceite da Interface

| Código | Critério |
| --- | --- |
| CA-RI-01 | A interface deve exibir os dados necessários ao usuário autenticado conforme permissão. |
| CA-RI-02 | A interface deve permitir edição apenas dos campos autorizados. |
| CA-RI-03 | Campos obrigatórios devem exibir validação quando não preenchidos. |
| CA-RI-04 | A ação principal deve responder aos estados de alteração, validação e salvamento. |
| CA-RI-05 | Após sucesso, a interface deve confirmar a operação ao usuário. |
| CA-RI-06 | Em caso de erro, a interface deve informar a falha e permitir nova tentativa. |
| CA-RI-07 | A interface deve exibir status, pendências ou bloqueios relevantes. |
| CA-RI-08 | A interface deve ser responsiva para **desktop**, **tablet** e **mobile** quando aplicável. |

### 15. Lacunas e Premissas

| Item | Tipo | Descrição |
| --- | --- | --- |
| 1 | Lacuna | [Informação ausente que impede decisão completa] |
| 2 | Premissa | [Suposição usada para avançar o RI] |
| 3 | Risco | [Risco de regra, dado, permissão ou experiência] |

### 16. Fora do Escopo

- [Item, comportamento, regra ou integração que não faz parte deste RI.]
- [Item fora do escopo.]

### 17. Possíveis Evoluções Futuras

- [Melhoria futura, automação, componente avançado ou integração adicional.]
- [Evolução futura.]
`;
}

function sddBuildRequirementTemplate({ id, title, owner, kind = 'req', parentId = null }) {
    if (kind === 'rf') {
        const pId = parentId || 'REQ-XX';
        return `# ${id} — ${title}\n
## 1. Identificação\n
| Campo | Valor |
|---|---|
| ID | ${id} |
| REQ Pai | ${pId} |
| Título | ${title} |
| Tipo | Requisito funcional |
| Prioridade | Alta |
| Status | Detalhado |\n
## 2. Objetivo\n
Objetivo específico deste fluxo.\n
## 3. Descrição Funcional\n
Descrição detalhada de como o fluxo funciona.\n
## 4. História do Usuário\n
Como [usuário], quero [ação], para que [benefício].\n
## 5. Regras de Negócio\n
| ID | Regra |
|---|---|
| RN-${id}-01 | Regra específica 1 |\n
## 6. Dados Necessários\n
| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| campo_exemplo | string | Sim | Descrição do dado |\n
## 7. Critérios de Aceite\n
- [ ] Critério de aceite específico 1.\n
## 8. Fora do Escopo\n
- Item fora do escopo deste RF.\n
## 9. Próximo Artefato\n
| Tipo | Arquivo |
|---|---|
| DRI | ../dri/DRI-${id}.md |
| Task List | ../task-lists/TASKLIST-${id}.md |\n`;
    }

    return `# ${id} — ${title}\n
## 1. Identificação\n
| Campo | Valor |
|---|---|
| ID | ${id} |
| Título | ${title} |
| Projeto | A definir |
| Tipo | Requisito Macro |
| Prioridade | Alta |
| Status | Levantado |
| Fonte | .documents/project-charter.md |\n
## 2. Objetivo\n
Descreva o objetivo macro da funcionalidade.\n
## 3. Escopo Macro\n
- Escopo 1
- Escopo 2\n
## 4. Requisitos Funcionais Vinculados\n
| ID | Requisito Funcional | Arquivo | Status |
|---|---|---|---|
| RF-01-01 | Primeiro fluxo de ${title} | functional-requirements/RF-01-01.md | Levantado |\n
## 5. Fontes de Dados\n
| ID | Fonte | Uso no processo |
|---|---|---|
| FD-01-01 | Banco de Dados / API | Descrição |\n
## 6. Regras Gerais\n
| ID | Regra |
|---|---|
| RN-01-01 | Regra macro 1 |\n
## 7. Critérios de Aceite Macro\n
- [ ] Critério 1.\n
## 8. Fora do Escopo\n
- Item fora do escopo.\n
## 9. Rastreabilidade\n
| Origem | Referência |
|---|---|
| TAP | .documents/project-charter.md |\n`;
}

function sddGenerateRfId(parentId) {
    if (!parentId) return 'RF-XX-01';
    const parentNum = parentId.replace('REQ-', '');
    const rfPattern = new RegExp(`\\bRF-${parentNum}-(\\d{2,4})`, 'i');
    
    const sources = [
        ...(sddState.specs || []).map(spec => `${spec.filename || ''} ${spec.title || ''}`),
        sddState.activeFilename || '',
        sddState.activeContent || ''
    ];
    
    const usedNumbers = sources
        .map(source => String(source || '').match(rfPattern))
        .filter(Boolean)
        .map(match => Number(match[1]))
        .filter(Number.isFinite);

    const next = usedNumbers.length ? Math.max(...usedNumbers) + 1 : 1;
    return `RF-${parentNum}-${String(next).padStart(2, '0')}`;
}

async function sddOpenNewRequirementModal() {
    if (state.activeProjectId) {
        try {
            const res = await fetch(`/api/projects/${state.activeProjectId}/sdd/specs`, { headers: getHeaders() });
            if (res.ok) sddState.specs = await res.json();
        } catch (e) {
            console.warn('Não foi possível atualizar a lista antes de criar requisito:', e);
        }
    }
    
    let kind = 'req';
    let parentId = null;

    if (sddState.activeTab === 'sdd-tab-rfs' || sddState.activeTab === 'sdd-tab-edit' || sddState.activeTab === 'sdd-tab-dri' || sddState.activeTab === 'sdd-tab-checklist' || sddState.activeTab === 'sdd-tab-tests') {
        kind = 'rf';
        parentId = sddState.activeReqId;
    }

    const idInput = document.getElementById('sdd-new-requirement-id');
    const titleInput = document.getElementById('sdd-new-requirement-title');
    const authorInput = document.getElementById('sdd-new-requirement-author');
    
    if (idInput) {
        if (kind === 'req') {
            idInput.value = sddGenerateRequirementId();
        } else {
            idInput.value = sddGenerateRfId(parentId);
        }
    }
    
    if (titleInput) titleInput.value = '';
    if (authorInput) authorInput.value = '';
    openCustomModal('modal-sdd-new-requirement');
    setTimeout(() => titleInput?.focus(), 40);
}

async function sddCreateRequirementFromModal() {
    let kind = 'req';
    let parentId = null;

    if (sddState.activeTab === 'sdd-tab-rfs' || sddState.activeTab === 'sdd-tab-edit' || sddState.activeTab === 'sdd-tab-dri' || sddState.activeTab === 'sdd-tab-checklist' || sddState.activeTab === 'sdd-tab-tests') {
        kind = 'rf';
        parentId = sddState.activeReqId;
    }

    if (kind === 'rf' && !parentId) {
        gitideNotify({ title: 'REQ Pai obrigatório', message: 'Selecione um REQ na aba "1 REQ" primeiro.', variant: 'warning' });
        return;
    }
    
    let id = document.getElementById('sdd-new-requirement-id')?.value.trim();
    if (!id) {
        id = kind === 'rf' ? sddGenerateRfId(parentId) : sddGenerateRequirementId();
    }
    
    const title = document.getElementById('sdd-new-requirement-title')?.value.trim();
    const owner = document.getElementById('sdd-new-requirement-author')?.value.trim();
    if (!title) {
        gitideNotify({ title: 'Título obrigatório', message: 'Informe um título para criar o requisito.', variant: 'warning' });
        document.getElementById('sdd-new-requirement-title')?.focus();
        return;
    }

    sddState.activeFilename = null;
    sddState.activeStorageType = 'project_spec_file';
    sddState.activeFilepath = '';
    sddState.isDraft = true;
    await sddLoadProjectDocuments();
    document.getElementById('sdd-workspace-nav-tabs').style.display = 'flex';
    const filename = sddBuildUniqueRequirementFilename(id, title, kind, parentId);
    sddSetActiveSpecHeader({ title: `${id} - ${title}`, filename });
    document.getElementById('sdd-edit-filename').value = filename;
    const template = sddBuildRequirementTemplate({ id, title, owner, kind, parentId });
    sddState.activeContent = template;
    
    if (kind === 'rf') {
        document.getElementById('sdd-rf-editor').value = template;
        sddSwitchTab('sdd-tab-rfs');
    } else {
        document.getElementById('sdd-specify-editor').value = template;
        sddPopulateStageEditors(template);
        sddSwitchTab('sdd-tab-preview');
    }

    // Remove sidebar active
    document.querySelectorAll('.spec-item').forEach(el => el.classList.remove('active'));
    closeCustomModal('modal-sdd-new-requirement');

    // Auto-save immediately upon creation
    await sddSaveStage(kind === 'rf' ? 'rf' : 'specify');
}

// --- AI Spec Generation ---
async function sddGenerateSpecIA(kind = 'req') {
    const isRf = kind === 'rf';
    const titleInputId = isRf ? 'sdd-wizard-rf-title' : 'sdd-wizard-title';
    const promptInputId = isRf ? 'sdd-wizard-rf-prompt' : 'sdd-wizard-prompt';
    const btnId = isRf ? 'btn-sdd-generate-rf-ia' : 'btn-sdd-generate-spec-ia';

    const title = document.getElementById(titleInputId).value.trim();
    const prompt = document.getElementById(promptInputId).value.trim();
    const parent_id = isRf ? sddState.activeReqId : null;

    if (!prompt) {
        alert('Por favor, descreva as funcionalidades para gerar a especificação.');
        return;
    }
    if (isRf && !parent_id) {
        alert('Por favor, selecione um REQ Pai primeiro na aba "1 REQ" antes de gerar um RF.');
        return;
    }
    if (!state.activeProjectId) {
        alert('Selecione um projeto primeiro.');
        return;
    }

    const btn = document.getElementById(btnId);
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i data-lucide="loader-2" style="animation:spin 1s linear infinite;"></i> Gerando com IA...';
        if (window.lucide) lucide.createIcons();
    }
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/sdd/generate-spec`, {
            method: 'POST',
            headers: { ...getHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, prompt, kind, parent_id })
        });
        const data = await res.json();
        const generatedContent = data.content !== undefined ? data.content : data.markdown;
        if (data.filename && generatedContent !== undefined) {
            sddState.activeFilename = data.filename;
            sddState.activeContent = generatedContent;
            sddState.activeStorageType = data.storage_type || 'project_spec_file';
            sddState.activeFilepath = data.filepath || '';
            sddState.isDraft = false;
            
            // Extract activeReqId if REQ
            if (kind === 'req') {
                const match = data.filename.match(/(REQ-\d+)/i);
                if (match) sddState.activeReqId = match[1].toUpperCase();
            }

            await sddLoadProjectDocuments();
            sddSetActiveSpecHeader({ title: data.title, filename: data.filename, content: generatedContent });
            document.getElementById('sdd-workspace-nav-tabs').style.display = 'flex';
            sddPopulatePreview(generatedContent);
            
            if (isRf) {
                document.getElementById('sdd-rf-editor').value = generatedContent;
                document.getElementById('sdd-edit-filename').value = data.filename;
                sddSwitchTab('sdd-tab-rfs');
            } else {
                document.getElementById('sdd-specify-editor').value = generatedContent;
                document.getElementById('sdd-edit-filename').value = data.filename;
                sddSwitchTab('sdd-tab-preview');
            }

            // Clear wizard inputs
            document.getElementById(titleInputId).value = '';
            document.getElementById(promptInputId).value = '';
            await sddLoadSpecs(true);
        } else {
            alert('Erro ao gerar especificação: ' + (data.detail || JSON.stringify(data)));
        }
    } catch (e) {
        alert('Erro na geração por IA: ' + e.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = isRf ? '<i data-lucide="sparkles"></i> Gerar RF com IA' : '<i data-lucide="sparkles"></i> Gerar REQ Pai com IA';
            if (window.lucide) lucide.createIcons();
        }
    }
}

// --- AI Test Generation ---
async function sddGenerateTests() {
    if (!state.activeProjectId || !sddState.activeFilename) {
        alert('Selecione uma especificação primeiro.');
        return;
    }
    const framework = document.getElementById('sdd-test-framework').value;
    const btn = document.getElementById('btn-sdd-generate-tests');
    btn.disabled = true;
    btn.innerHTML = '<i data-lucide="loader-2" style="animation:spin 1s linear infinite;"></i> Gerando testes com IA...';
    if (window.lucide) lucide.createIcons();
    const resultPanel = document.getElementById('sdd-test-result-panel');
    resultPanel.style.display = 'none';
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/sdd/generate-tests`, {
            method: 'POST',
            headers: { ...getHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: sddState.activeFilename, framework })
        });
        const data = await res.json();
        if (data.status === 'success') {
            document.getElementById('sdd-test-result-filepath').textContent = '✓ Salvo em: ' + data.filepath;
            document.getElementById('sdd-test-result-code').textContent = data.code || '';
            resultPanel.style.display = 'flex';
        } else {
            alert('Erro ao gerar testes: ' + (data.detail || JSON.stringify(data)));
        }
    } catch (e) {
        alert('Erro na geração de testes: ' + e.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i data-lucide="play-circle"></i> Gerar Arquivo de Testes com IA';
        if (window.lucide) lucide.createIcons();
    }
}

// --- SDD Event Listener Setup (called from setupEventListeners) ---
function setupSddEventListeners() {
    document.querySelectorAll('.harness-top-tab').forEach(btn => {
        btn.addEventListener('click', () => sddSwitchHarnessPanel(btn.dataset.harnessPanel));
    });

    const btnSaveCharter = document.getElementById('btn-sdd-save-charter');
    if (btnSaveCharter) btnSaveCharter.addEventListener('click', sddSaveCharter);

    const btnGenCharter = document.getElementById('btn-sdd-generate-charter-ia');
    if (btnGenCharter) btnGenCharter.addEventListener('click', sddGenerateCharterIA);

    // Sidebar: Refresh
    const btnRefresh = document.getElementById('btn-refresh-sdd-specs');
    if (btnRefresh) btnRefresh.addEventListener('click', sddLoadSpecs);

    const btnRefreshProjectTasks = document.getElementById('btn-refresh-sdd-project-tasks');
    if (btnRefreshProjectTasks) btnRefreshProjectTasks.addEventListener('click', sddLoadProjectTasks);

    document.querySelectorAll('[data-sdd-task-filter]').forEach(btn => {
        btn.addEventListener('click', () => sddSetProjectTaskFilter(btn.dataset.sddTaskFilter));
    });

    document.getElementById('btn-sdd-task-detail-close')?.addEventListener('click', sddCloseTaskDetail);
    document.getElementById('sdd-task-detail-backdrop')?.addEventListener('click', sddCloseTaskDetail);

    // Sidebar: New Manual
    const btnNew = document.getElementById('btn-new-sdd-spec-manual');
    if (btnNew) btnNew.addEventListener('click', sddOpenNewRequirementModal);

    document.querySelectorAll('.sdd-requirement-close').forEach(btn => {
        btn.addEventListener('click', () => closeCustomModal('modal-sdd-new-requirement'));
    });

    const btnCreateRequirement = document.getElementById('btn-sdd-create-requirement');
    if (btnCreateRequirement) btnCreateRequirement.addEventListener('click', sddCreateRequirementFromModal);

    const requirementTitleInput = document.getElementById('sdd-new-requirement-title');
    if (requirementTitleInput) {
        requirementTitleInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') sddCreateRequirementFromModal();
        });
    }

    // Switch to IA wizard from empty workspace
    const btnToWizard = document.getElementById('btn-switch-to-ia-generator');
    if (btnToWizard) btnToWizard.addEventListener('click', () => sddSwitchTab('sdd-tab-ia-wizard'));

    // Workspace sub-tabs
    document.querySelectorAll('.sdd-nav-btn').forEach(btn => {
        btn.addEventListener('click', () => sddSwitchTab(btn.dataset.sddTab));
    });

    document.querySelectorAll('[data-sdd-aside-toggle]').forEach(btn => {
        btn.addEventListener('click', () => sddToggleStageAside(btn));
    });

    document.querySelectorAll('[data-sdd-focus-toggle]').forEach(btn => {
        btn.addEventListener('click', () => sddToggleStageFocus(btn));
    });

    // Save spec
    // Legacy global save button removed, do nothing here

    const btnSaveSpecify = document.getElementById('btn-sdd-save-specify');
    if (btnSaveSpecify) btnSaveSpecify.addEventListener('click', () => sddSaveStage('specify'));

    const btnSaveRf = document.getElementById('btn-sdd-save-rf');
    if (btnSaveRf) btnSaveRf.addEventListener('click', () => sddSaveStage('rf'));

    const btnSaveDesign = document.getElementById('btn-sdd-save-design');
    if (btnSaveDesign) btnSaveDesign.addEventListener('click', () => sddSaveStage('design'));

    const btnSaveDri = document.getElementById('btn-sdd-save-dri');
    const btnSaveTaskDetails = document.getElementById('btn-sdd-save-task-details');
    if (btnSaveDri) btnSaveDri.addEventListener('click', () => sddSaveStage('dri'));

    // Delete spec
    // Legacy global delete button removed, do nothing here

    const btnDeleteSpecify = document.getElementById('btn-sdd-delete-specify');
    if (btnDeleteSpecify) btnDeleteSpecify.addEventListener('click', sddDeleteSpec);
    
    const btnDeleteRf = document.getElementById('btn-sdd-delete-rf');
    if (btnDeleteRf) btnDeleteRf.addEventListener('click', sddDeleteSpec);

    // Generate spec via IA
    const btnGenSpec = document.getElementById('btn-sdd-generate-spec-ia');
    if (btnGenSpec) btnGenSpec.addEventListener('click', () => sddGenerateSpecIA('req'));

    const btnGenRf = document.getElementById('btn-sdd-generate-rf-ia');
    if (btnGenRf) btnGenRf.addEventListener('click', () => sddGenerateSpecIA('rf'));

    const btnDesignAi = document.getElementById('btn-sdd-design-ai');
    if (btnDesignAi) btnDesignAi.addEventListener('click', () => {
        const prompt = document.getElementById('sdd-design-ai-prompt');
        const specify = sddExtractSection(sddState.activeContent, ['Specify', 'Especificação', 'Requisitos']) || document.getElementById('sdd-specify-editor')?.value || '';
        if (prompt) {
            prompt.value = `Com base no Specify abaixo, gere somente a seção "## 2. Design - Planejamento" com arquitetura proposta, dados, integrações, bibliotecas e contratos técnicos. Não gere tarefas.\n\n${specify}`;
            prompt.focus();
        }
    });

    const btnDriAi = document.getElementById('btn-sdd-dri-ai');
    if (btnDriAi) btnDriAi.addEventListener('click', () => {
        const prompt = document.getElementById('sdd-dri-ai-prompt');
        const specify = sddExtractSection(sddState.activeContent, ['Specify', 'Especificação', 'Requisitos']) || document.getElementById('sdd-specify-editor')?.value || '';
        const design = sddExtractSection(sddState.activeContent, ['Design', 'Planejamento', 'Arquitetura']) || document.getElementById('sdd-design-editor')?.value || '';
        if (prompt) {
            prompt.value = `Com base no Specify e no Design abaixo, gere somente a seção "## 3. DRI - Documento de Requisito de Interface" usando o template RI oficial. Inclua identificação da interface, objetivo, contexto de uso, arquitetura da informação, mapa de componentes, regras de exibição, estados, fluxo de interação, mapeamento de dados, hierarquia visual, microcopy, responsividade, acessibilidade, critérios de aceite da interface, lacunas, fora do escopo e evoluções futuras. Não gere tarefas.\n\n## Specify\n${specify}\n\n## Design\n${design}`;
            prompt.focus();
        }
    });

    // Generate tests via IA
    const btnGenTests = document.getElementById('btn-sdd-generate-tests');
    if (btnGenTests) btnGenTests.addEventListener('click', sddGenerateTests);

    document.querySelectorAll('.sdd-flow-step').forEach(btn => {
        btn.addEventListener('click', () => sddSwitchTab(btn.dataset.sddFlowTab));
    });

    // Copy test code
    const btnCopyTest = document.getElementById('btn-copy-sdd-test-code');
    if (btnCopyTest) btnCopyTest.addEventListener('click', () => {
        const code = document.getElementById('sdd-test-result-code').textContent;
        navigator.clipboard.writeText(code).then(() => {
            btnCopyTest.innerHTML = '<i data-lucide="check"></i>';
            if (window.lucide) lucide.createIcons();
            setTimeout(() => {
                btnCopyTest.innerHTML = '<i data-lucide="copy"></i>';
                if (window.lucide) lucide.createIcons();
            }, 2000);
        });
    });
}

// Inject SDD CSS for markdown items not covered by rebrand.css
(function injectSddStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .spec-item {
            display: flex; align-items: center; gap: 10px;
            min-height: 46px; padding: 8px 10px; cursor: pointer;
            border: 1px solid transparent; border-radius: 10px;
            transition: background 0.15s, border-color 0.15s;
        }
        .spec-item:hover { background: rgba(255,255,255,0.025); border-color: var(--flat-border-soft, var(--border-color)); }
        .spec-item.active { background: rgba(255,255,255,0.04); border-color: rgba(255,255,255,0.10); }
        .spec-item-title { font-size: 13px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .spec-item-meta { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
        .specs-empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center;
            gap: 10px; padding: 40px 20px; color: var(--text-muted); font-size: 13px; text-align: center; }
        .specs-empty-state i { width: 36px; height: 36px; opacity: 0.4; }
        .md-check { list-style: none; }
        .md-checkbox { display: inline-block; width: 16px; margin-right: 6px; color: var(--color-primary); }
        .md-check.checked { color: #10b981; text-decoration: line-through; opacity: 0.7; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    `;
    document.head.appendChild(style);
})();


// --- AUTOCOMPLETE DE MENÇÃO DE ARQUIVOS COM @ ---

let selectedMentionIndex = -1;
let filteredMentionFiles = [];

async function getProjectFiles() {
    if (state.files && state.files.length > 0) {
        return state.files;
    }
    if (!state.activeProjectId) return [];
    try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/files`);
        const data = await res.json();
        if (data.status === 'success') {
            state.files = data.files || [];
            return state.files;
        }
    } catch (e) {
        console.error("Erro ao carregar arquivos para autocomplete:", e);
    }
    return [];
}

function selectMentionFile(input, lastAtIndex, filepath) {
    const text = input.value;
    const beforeMention = text.slice(0, lastAtIndex);
    const afterMention = text.slice(input.selectionStart);
    
    input.value = beforeMention + filepath + ' ' + afterMention;
    
    // Posiciona o cursor após o nome do arquivo + espaço
    const newCursorPos = lastAtIndex + filepath.length + 1;
    input.setSelectionRange(newCursorPos, newCursorPos);
    
    hideMentionDropdown();
    input.focus();
}

function hideMentionDropdown() {
    const dropdown = document.getElementById('agent-mention-dropdown');
    if (dropdown) {
        dropdown.style.setProperty('display', 'none', 'important');
    }
    selectedMentionIndex = -1;
    filteredMentionFiles = [];
}

async function handleMentionInput(e) {
    const input = e.target;
    const cursor = input.selectionStart;
    const text = input.value.slice(0, cursor);
    const lastAtIndex = text.lastIndexOf('@');
    
    if (lastAtIndex !== -1) {
        const beforeAt = lastAtIndex > 0 ? text.charAt(lastAtIndex - 1) : ' ';
        if (beforeAt === ' ' || beforeAt === '\n') {
            const query = text.slice(lastAtIndex + 1);
            if (!query.includes(' ')) {
                const allFiles = await getProjectFiles();
                const queryLower = query.toLowerCase();
                
                filteredMentionFiles = allFiles.filter(file => {
                    const filename = file.path.split('/').pop().split('\\').pop().toLowerCase();
                    const pathLower = file.path.toLowerCase();
                    return filename.includes(queryLower) || pathLower.includes(queryLower);
                }).slice(0, 10);
                
                renderMentionDropdown(input, lastAtIndex, query);
                return;
            }
        }
    }
    hideMentionDropdown();
}

function renderMentionDropdown(input, lastAtIndex, query) {
    let dropdown = document.getElementById('agent-mention-dropdown');
    if (!dropdown) {
        dropdown = document.createElement('ul');
        dropdown.id = 'agent-mention-dropdown';
        dropdown.style.cssText = `
            display: none !important;
            position: absolute !important;
            bottom: 100% !important;
            margin-bottom: 8px !important;
            left: 20px !important;
            right: 20px !important;
            background: rgba(22, 22, 22, 0.98) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.75) !important;
            max-height: 240px !important;
            overflow-y: auto !important;
            z-index: 1000 !important;
            padding: 8px 0 !important;
            margin: 0 !important;
            list-style: none !important;
            scrollbar-width: thin !important;
        `;
        
        const form = document.getElementById('agent-chat-form');
        if (form) {
            form.style.position = 'relative';
            form.appendChild(dropdown);
        }
    }
    
    if (filteredMentionFiles.length === 0) {
        dropdown.style.setProperty('display', 'none', 'important');
        return;
    }
    
    dropdown.innerHTML = '';
    
    // Garante que o index selecionado é válido
    selectedMentionIndex = Math.min(selectedMentionIndex, filteredMentionFiles.length - 1);
    if (selectedMentionIndex < 0 && filteredMentionFiles.length > 0) {
        selectedMentionIndex = 0;
    }
    
    filteredMentionFiles.forEach((file, index) => {
        const parts = file.path.split('/');
        const filename = parts.pop();
        const folder = parts.join('/');
        
        const item = document.createElement('li');
        item.style.cssText = `
            display: flex !important;
            align-items: center !important;
            gap: 10px !important;
            padding: 8px 16px !important;
            cursor: pointer !important;
            transition: background 0.15s ease !important;
            font-size: 13px !important;
            color: rgba(255, 255, 255, 0.9) !important;
            background: ${index === selectedMentionIndex ? 'rgba(255, 255, 255, 0.08) !important' : 'transparent !important'};
            border-radius: 0 !important;
            border: none !important;
        `;
        
        item.addEventListener('mouseenter', () => {
            selectedMentionIndex = index;
            Array.from(dropdown.children).forEach((child, cIdx) => {
                child.style.setProperty('background', cIdx === selectedMentionIndex ? 'rgba(255, 255, 255, 0.08)' : 'transparent', 'important');
            });
        });
        
        const icon = document.createElement('i');
        icon.className = 'fa-solid fa-file-code';
        icon.style.cssText = 'color: var(--color-primary) !important; opacity: 0.8 !important; display: inline-block !important;';
        
        const textWrapper = document.createElement('div');
        textWrapper.style.cssText = `
            display: flex !important;
            flex-direction: column !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            white-space: nowrap !important;
            background: transparent !important;
            border: none !important;
        `;
        
        const nameSpan = document.createElement('span');
        nameSpan.style.cssText = 'font-weight: 500 !important; color: rgba(255, 255, 255, 0.95) !important;';
        nameSpan.textContent = filename;
        
        const pathSpan = document.createElement('span');
        pathSpan.style.cssText = `
            font-size: 11px !important;
            color: var(--text-dark) !important;
            opacity: 0.8 !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        `;
        pathSpan.textContent = folder ? folder : './';
        
        textWrapper.appendChild(nameSpan);
        textWrapper.appendChild(pathSpan);
        
        item.appendChild(icon);
        item.appendChild(textWrapper);
        
        item.addEventListener('mousedown', (ev) => {
            // Usa mousedown para rodar antes do evento blur do input
            ev.preventDefault();
            selectMentionFile(input, lastAtIndex, file.path);
        });
        
        dropdown.appendChild(item);
    });
    
    dropdown.style.setProperty('display', 'block', 'important');
    
    const activeItem = dropdown.children[selectedMentionIndex];
    if (activeItem) {
        activeItem.scrollIntoView({ block: 'nearest' });
    }
}

function handleMentionKeydown(e) {
    const dropdown = document.getElementById('agent-mention-dropdown');
    if (!dropdown || dropdown.style.display === 'none' || filteredMentionFiles.length === 0) {
        return;
    }
    
    const input = e.target;
    const cursor = input.selectionStart;
    const text = input.value.slice(0, cursor);
    const lastAtIndex = text.lastIndexOf('@');
    
    if (e.key === 'ArrowDown') {
        e.preventDefault();
        selectedMentionIndex = (selectedMentionIndex + 1) % filteredMentionFiles.length;
        renderMentionDropdown(input, lastAtIndex, '');
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        selectedMentionIndex = (selectedMentionIndex - 1 + filteredMentionFiles.length) % filteredMentionFiles.length;
        renderMentionDropdown(input, lastAtIndex, '');
    } else if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault();
        if (selectedMentionIndex >= 0 && selectedMentionIndex < filteredMentionFiles.length) {
            selectMentionFile(input, lastAtIndex, filteredMentionFiles[selectedMentionIndex].path);
        }
    } else if (e.key === 'Escape') {
        e.preventDefault();
        hideMentionDropdown();
    }
}

function setupChatMentions() {
    const input = document.getElementById('agent-user-prompt');
    if (!input) return;
    
    input.addEventListener('input', handleMentionInput);
    input.addEventListener('keydown', handleMentionKeydown);
    input.addEventListener('click', handleMentionInput);
    input.addEventListener('blur', () => {
        setTimeout(hideMentionDropdown, 150);
    });
}

// PROJECT ESTIMATION
function estimationCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
        maximumFractionDigits: 2
    }).format(Number(value) || 0);
}

function estimationHours(value) {
    return `${Number(value || 0).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}h`;
}

function estimationComplexityLabel(value) {
    return ({ low: 'Baixa', medium: 'Média', high: 'Alta' })[value] || 'Média';
}

function estimationTaskTypeLabel(value) {
    return ({
        implementation: 'Implementação',
        correction: 'Correção',
        adjustment: 'Ajuste'
    })[value] || 'Implementação';
}

function estimationTechnicalAreaLabel(value) {
    return ({
        frontend: 'Front-end',
        backend: 'Back-end',
        fullstack: 'Full stack',
        infra: 'Infra',
        qa: 'QA',
        docs: 'Docs',
        general: 'Geral'
    })[value] || 'Geral';
}

function setEstimationText(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
}

function setEstimationViewText(view) {
    const isHistory = view === 'history';
    setEstimationText('estimation-task-count-label', isHistory ? 'Tarefas fechadas estimadas' : 'Tarefas abertas analisadas');
    setEstimationText('estimation-table-title', isHistory ? 'Histórico de estimativas fechadas' : 'Estimativa por tarefa');
    setEstimationText(
        'estimation-table-subtitle',
        isHistory
            ? 'Preserva o esforço estimado das tasks concluídas, sem misturar com o backlog aberto.'
            : 'Compare o esforço previsto para a mesma entrega nos dois modos de execução.'
    );
}

function renderEstimationEmpty(message = 'Gere a primeira estimativa para visualizar o painel.') {
    state.estimationReport = null;
    setEstimationViewText(state.estimationView || 'open');
    setEstimationText('estimation-task-count', '-');
    setEstimationText('estimation-updated-at', 'Aguardando primeira análise');
    setEstimationText('estimation-manual-hours', '-');
    setEstimationText('estimation-manual-context', 'Horas, dias e custo');
    setEstimationText('estimation-ai-hours', '-');
    setEstimationText('estimation-ai-context', 'Horas, dias e custo');
    setEstimationText('estimation-saving-percent', '-');
    setEstimationText('estimation-saving-context', 'Economia de esforço e custo');
    const body = document.getElementById('estimation-table-body');
    if (body) {
        body.innerHTML = `<tr><td colspan="8"><div class="estimation-empty"><i data-lucide="calculator"></i><span>${escapeHtml(message)}</span></div></td></tr>`;
    }
    const warning = document.getElementById('estimation-warning');
    if (warning) warning.hidden = true;
    if (window.lucide) lucide.createIcons();
}

function renderEstimationReport(report) {
    if (!report || !Array.isArray(report.tasks) || !report.totals) {
        renderEstimationEmpty();
        return;
    }
    state.estimationReport = report;
    renderCurrentEstimationView();
}

function renderCurrentEstimationView() {
    const report = state.estimationReport;
    if (!report || !Array.isArray(report.tasks) || !report.totals) {
        renderEstimationEmpty();
        return;
    }
    const view = state.estimationView === 'history' ? 'history' : 'open';
    setEstimationViewText(view);
    const tasks = view === 'history' ? (report.history || []) : report.tasks;
    const totals = view === 'history'
        ? (report.history_totals || {
            task_count: tasks.length,
            manual_hours: 0,
            ai_hours: 0,
            manual_days: 0,
            ai_days: 0,
            manual_cost: 0,
            ai_cost: 0,
            saved_hours: 0,
            saved_cost: 0,
            saving_percent: 0
        })
        : report.totals;
    const generatedAt = report.generated_at ? new Date(report.generated_at).toLocaleString('pt-BR') : 'Data não informada';

    setEstimationText('estimation-task-count', totals.task_count ?? tasks.length);
    setEstimationText('estimation-updated-at', view === 'history' ? `Histórico preservado em ${generatedAt}` : `Atualizado em ${generatedAt}`);
    setEstimationText('estimation-manual-hours', estimationHours(totals.manual_hours));
    setEstimationText('estimation-manual-context', `${Number(totals.manual_days || 0).toLocaleString('pt-BR')} dias · ${estimationCurrency(totals.manual_cost)}`);
    setEstimationText('estimation-ai-hours', estimationHours(totals.ai_hours));
    setEstimationText('estimation-ai-context', `${Number(totals.ai_days || 0).toLocaleString('pt-BR')} dias · ${estimationCurrency(totals.ai_cost)}`);
    setEstimationText('estimation-saving-percent', `${Number(totals.saving_percent || 0).toLocaleString('pt-BR')}%`);
    setEstimationText('estimation-saving-context', `${estimationHours(totals.saved_hours)} · ${estimationCurrency(totals.saved_cost)}`);

    const warning = document.getElementById('estimation-warning');
    if (warning) {
        const warningText = view === 'open' ? report.warning : '';
        warning.hidden = !warningText;
        warning.innerHTML = warningText ? `<i data-lucide="triangle-alert"></i><span>${escapeHtml(warningText)}</span>` : '';
    }

    const body = document.getElementById('estimation-table-body');
    if (body) {
        if (!tasks.length) {
            const emptyMessage = view === 'history'
                ? 'Nenhuma task fechada com estimativa preservada ainda.'
                : 'Nenhuma task aberta encontrada para a estimativa atual.';
            body.innerHTML = `<tr><td colspan="8"><div class="estimation-empty"><i data-lucide="${view === 'history' ? 'history' : 'calculator'}"></i><span>${escapeHtml(emptyMessage)}</span></div></td></tr>`;
        } else {
            body.innerHTML = tasks.map((task) => `
            <tr>
                <td class="estimation-task-cell">
                    <strong>${escapeHtml(task.id || '')}</strong>
                    <span>${escapeHtml(task.title || '')}</span>
                    <small>${escapeHtml(task.rationale || '')}</small>
                </td>
                <td><span class="estimation-classification type-${escapeHtml(task.task_type || 'implementation')}">${estimationTaskTypeLabel(task.task_type)}</span></td>
                <td><span class="estimation-classification area-${escapeHtml(task.technical_area || 'general')}">${estimationTechnicalAreaLabel(task.technical_area)}</span></td>
                <td><span class="estimation-complexity ${escapeHtml(task.complexity || 'medium')}">${estimationComplexityLabel(task.complexity)}</span></td>
                <td class="estimation-col-manual"><strong>${estimationHours(task.manual_hours)}</strong></td>
                <td class="estimation-col-ai"><strong>${estimationHours(task.ai_hours)}</strong></td>
                <td class="estimation-col-saving"><strong>${estimationHours(task.saved_hours)}</strong><small>${Number(task.saving_percent || 0).toLocaleString('pt-BR')}%</small></td>
                <td><span class="estimation-source ${task.source === 'ai' ? 'ai' : 'fallback'}">${task.source === 'ai' ? 'IA' : 'Base técnica'}</span></td>
            </tr>
            `).join('');
        }
    }
    applyEstimationMode(state.estimationMode);
    if (window.lucide) lucide.createIcons();
}

function applyEstimationView(view) {
    state.estimationView = view === 'history' ? 'history' : 'open';
    document.querySelectorAll('[data-estimation-view]').forEach(button => {
        button.classList.toggle('active', button.dataset.estimationView === state.estimationView);
    });
    if (state.estimationReport) {
        renderCurrentEstimationView();
    } else {
        renderEstimationEmpty();
    }
}

function applyEstimationMode(mode) {
    state.estimationMode = ['ai', 'manual'].includes(mode) ? mode : 'comparison';
    const table = document.getElementById('estimation-table');
    if (table) table.dataset.mode = state.estimationMode;
    document.querySelectorAll('[data-estimation-mode]').forEach(button => {
        button.classList.toggle('active', button.dataset.estimationMode === state.estimationMode);
    });
}

async function saveEstimationConfig() {
    if (!state.activeProjectId) return;
    const hourlyRate = Math.max(1, Number(document.getElementById('estimation-hourly-rate')?.value) || 150);
    const dailyHours = Math.max(1, Math.min(24, Number(document.getElementById('estimation-daily-hours')?.value) || 8));
    const response = await fetch(`/api/projects/${state.activeProjectId}/pricing/config`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ hourly_rate: hourlyRate, daily_hours: dailyHours })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Não foi possível salvar a configuração.');
}

async function loadEstimationPage() {
    if (!state.activeProjectId) return;
    try {
        const [configResponse, reportResponse] = await Promise.all([
            fetch(`/api/projects/${state.activeProjectId}/pricing/config`, { headers: getHeaders() }),
            fetch(`/api/projects/${state.activeProjectId}/pricing/report`, { headers: getHeaders() })
        ]);
        const config = await configResponse.json();
        const reportPayload = await reportResponse.json();
        if (!configResponse.ok) throw new Error(config.detail || 'Erro ao carregar configuração.');
        if (!reportResponse.ok) throw new Error(reportPayload.detail || 'Erro ao carregar estimativa.');
        const rateInput = document.getElementById('estimation-hourly-rate');
        const hoursInput = document.getElementById('estimation-daily-hours');
        if (rateInput) rateInput.value = config.hourly_rate || 150;
        if (hoursInput) hoursInput.value = config.daily_hours || 8;
        renderEstimationReport(reportPayload.report);
    } catch (error) {
        renderEstimationEmpty(error.message || String(error));
    }
}

async function generateProjectEstimation() {
    if (!state.activeProjectId) return;
    const button = document.getElementById('btn-estimation-generate');
    const original = button?.innerHTML || '';
    try {
        if (button) {
            button.disabled = true;
            button.innerHTML = '<i data-lucide="loader-circle" class="spin"></i> Analisando projeto';
        }
        if (window.lucide) lucide.createIcons();
        await saveEstimationConfig();
        const response = await fetch(`/api/projects/${state.activeProjectId}/pricing/generate`, {
            method: 'POST',
            headers: getHeaders()
        });
        const data = await response.json();
        if (!response.ok || data.status !== 'success') throw new Error(data.detail || 'Erro ao gerar estimativa.');
        renderEstimationReport(data.report);
        gitideNotify({
            title: 'Estimativa atualizada',
            message: 'Painel e documentos .documents/estimativa.json e estimativa.md foram atualizados.',
            variant: 'success'
        });
    } catch (error) {
        gitideNotify({ title: 'Erro na estimativa', message: error.message || String(error), variant: 'danger' });
    } finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = original;
        }
        if (window.lucide) lucide.createIcons();
    }
}
