import builtins

path = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/static/app.js'
content = builtins.open(path, 'r', encoding='utf-8').read()

new_js = '''
// PRICING TAB LOGIC
async function sddLoadPricingTab() {
    if (!currentProjectId) return;
    try {
        const configRes = await fetch(/api/projects//pricing/config);
        if (configRes.ok) {
            const config = await configRes.json();
            document.getElementById('sdd-pricing-hourly-rate').value = config.hourly_rate || 150;
            document.getElementById('sdd-pricing-daily-hours').value = config.daily_hours || 8;
        }
        
        const reportRes = await fetch(/api/projects//pricing/report);
        if (reportRes.ok) {
            const report = await reportRes.json();
            if (report.markdown) {
                const container = document.getElementById('sdd-pricing-markdown-container');
                container.innerHTML = window.marked ? marked.parse(report.markdown) : report.markdown;
            }
        }
    } catch (e) {
        console.error('Error loading pricing tab', e);
    }
}

async function sddSavePricingConfig() {
    if (!currentProjectId) return;
    const rate = parseFloat(document.getElementById('sdd-pricing-hourly-rate').value) || 150;
    const hours = parseInt(document.getElementById('sdd-pricing-daily-hours').value) || 8;
    try {
        await fetch(/api/projects//pricing/config, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ hourly_rate: rate, daily_hours: hours })
        });
    } catch (e) {
        console.error('Error saving pricing config', e);
    }
}

async function sddGeneratePricing() {
    if (!currentProjectId) return;
    
    await sddSavePricingConfig();
    
    const btn = document.getElementById('btn-sdd-generate-pricing');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i data-lucide="loader-2" style="animation:spin 1s linear infinite;"></i> Gerando estimativa...';
    if (window.lucide) lucide.createIcons();
    
    const container = document.getElementById('sdd-pricing-markdown-container');
    container.innerHTML = '<div class="specs-empty-state" style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;"> <i data-lucide="brain" style="width:48px;height:48px;color:var(--primary-color);margin-bottom:16px;animation:pulse 2s infinite;"></i> <span style="font-size:16px;color:var(--text-primary);margin-bottom:8px;">Agente analisando projeto...</span> <span style="font-size:12px;color:var(--text-muted);">Lendo tarefas e requisitos para calcular o esforço total.</span> </div>';
    if (window.lucide) lucide.createIcons();

    try {
        const res = await fetch(/api/projects//pricing/generate, { method: 'POST' });
        const data = await res.json();
        
        if (res.ok && data.status === 'success') {
            container.innerHTML = window.marked ? marked.parse(data.markdown) : data.markdown;
            gitideNotify({ title: 'Estimativa gerada', message: 'Relatório salvo com sucesso em .documents/pricing.md.', variant: 'success' });
        } else {
            container.innerHTML = <div class="specs-empty-state"><span style="color:var(--danger-color)">Erro: </span></div>;
        }
    } catch (e) {
        container.innerHTML = <div class="specs-empty-state"><span style="color:var(--danger-color)">Erro de conexão: </span></div>;
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
        if (window.lucide) lucide.createIcons();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const rateInput = document.getElementById('sdd-pricing-hourly-rate');
    const hoursInput = document.getElementById('sdd-pricing-daily-hours');
    if (rateInput) rateInput.addEventListener('change', sddSavePricingConfig);
    if (hoursInput) hoursInput.addEventListener('change', sddSavePricingConfig);
    
    const btnGen = document.getElementById('btn-sdd-generate-pricing');
    if (btnGen) btnGen.addEventListener('click', sddGeneratePricing);
});
'''

if 'sddLoadPricingTab' not in content:
    content += new_js
    
    # Also inject sddLoadPricingTab into sddSwitchTab
    old_switch = 'function sddSwitchTab(tabId) {\n    sddState.activeTab = tabId;'
    new_switch = 'function sddSwitchTab(tabId) {\n    sddState.activeTab = tabId;\n    if (tabId === "sdd-tab-pricing") sddLoadPricingTab();'
    content = content.replace(old_switch, new_switch)
    
    builtins.open(path, 'w', encoding='utf-8').write(content)
    print("app.js updated successfully.")
else:
    print("Logic already exists in app.js")

