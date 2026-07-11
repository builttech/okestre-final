import builtins

path = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/main.py'
content = builtins.open(path, 'r', encoding='utf-8').read()

anchor = '@app.get("/", response_class=HTMLResponse, tags=["Dashboard UI"])'

new_code = '''class PricingConfigIn(BaseModel):
    hourly_rate: float
    daily_hours: int

@app.get("/api/projects/{project_id}/pricing/config", tags=["Pricing"])
def get_pricing_config(project: Project = Depends(get_project_or_404)):
    config_path = os.path.join(project.path, ".documents", "pricing_config.json")
    if os.path.exists(config_path):
        import json
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"hourly_rate": 150, "daily_hours": 8}

@app.post("/api/projects/{project_id}/pricing/config", tags=["Pricing"])
def save_pricing_config(config: PricingConfigIn, project: Project = Depends(get_project_or_404)):
    config_path = os.path.join(project.path, ".documents", "pricing_config.json")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    import json
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config.dict(), f, ensure_ascii=False, indent=4)
    return {"status": "success"}

@app.get("/api/projects/{project_id}/pricing/report", tags=["Pricing"])
def get_pricing_report(project: Project = Depends(get_project_or_404)):
    pricing_md_path = os.path.join(project.path, ".documents", "pricing.md")
    if os.path.exists(pricing_md_path):
        with open(pricing_md_path, "r", encoding="utf-8") as f:
            return {"markdown": f.read()}
    return {"markdown": ""}

@app.post("/api/projects/{project_id}/pricing/generate", tags=["Pricing"])
def generate_pricing_report(project: Project = Depends(get_project_or_404)):
    config_path = os.path.join(project.path, ".documents", "pricing_config.json")
    hourly_rate = 150
    daily_hours = 8
    if os.path.exists(config_path):
        import json
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            hourly_rate = data.get("hourly_rate", 150)
            daily_hours = data.get("daily_hours", 8)
            
    # Read task.md and task.details.md
    task_md_path = os.path.join(project.path, ".documents", "task", "task.md")
    task_details_md_path = os.path.join(project.path, ".documents", "task", "task.details.md")
    
    task_content = ""
    if os.path.exists(task_md_path):
        with open(task_md_path, "r", encoding="utf-8") as f:
            task_content += "=== task.md ===\\n" + f.read() + "\\n\\n"
            
    if os.path.exists(task_details_md_path):
        with open(task_details_md_path, "r", encoding="utf-8") as f:
            task_content += "=== task.details.md ===\\n" + f.read() + "\\n\\n"
            
    # Read RFs if they exist
    rf_dir = os.path.join(project.path, ".documents", "functional-requirements")
    rf_content = ""
    if os.path.exists(rf_dir):
        import os
        for file in os.listdir(rf_dir):
            if file.endswith(".md"):
                with open(os.path.join(rf_dir, file), "r", encoding="utf-8") as f:
                    rf_content += f"=== {file} ===\\n" + f.read() + "\\n\\n"
                    
    context = task_content + rf_content
    
    if not task_content.strip():
        raise HTTPException(status_code=400, detail="task.md está vazio ou não existe. Gere as tarefas primeiro.")
        
    system_prompt = (
        f"Você é um Especialista em Estimativas e Engenheiro de Software Sênior.\\n"
        f"O usuário deseja uma estimativa de prazo e custo baseada nas tarefas e requisitos do projeto.\\n\\n"
        f"Métricas a considerar:\\n"
        f"- Valor da Hora: R$ {hourly_rate}\\n"
        f"- Horas dedicadas por dia: {daily_hours} horas\\n\\n"
        f"Analise o contexto fornecido (lista de tarefas e RFs) e crie um relatório Markdown estruturado com:\\n"
        f"1. Uma tabela detalhada que liste cada Tarefa encontrada, com duas colunas de estimativa de tempo (em horas): "
        f"'Tempo Manual' (programação 100% manual) e 'Tempo com IA' (usando copilot/assistentes avançados).\\n"
        f"2. Um resumo em formato de Cards ou painel visual (usando markdown e tabelas) com os TOTAIS de:\\n"
        f"   - Total de Horas (Manual vs IA)\\n"
        f"   - Total de Dias (baseado em {daily_hours} horas/dia) (Manual vs IA)\\n"
        f"   - Valor Total do Projeto (baseado em R$ {hourly_rate}/hora) (Manual vs IA)\\n"
        f"Retorne APENAS o Markdown limpo da estimativa, sem cabeçalhos de bloco de código adicionais. Foco em UX visual via Markdown."
    )
    
    try:
        from gitide_server.agent import call_llm
        result = call_llm([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Contexto do projeto:\\n\\n{context}"}
        ], temperature=0.3)
        
        # Save the result
        pricing_md_path = os.path.join(project.path, ".documents", "pricing.md")
        with open(pricing_md_path, "w", encoding="utf-8") as f:
            f.write(result)
            
        return {"status": "success", "markdown": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

'''

if new_code not in content:
    content = content.replace(anchor, new_code + anchor)
    builtins.open(path, 'w', encoding='utf-8').write(content)
    print("Backend endpoints inserted successfully.")
else:
    print("Backend endpoints already exist.")
