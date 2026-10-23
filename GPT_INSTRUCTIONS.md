agentflow TB

flow protocolo_engenharia["GPT_INSTRUCTIONS"]@{
  model: "reasoning"
  instruction: |-
    Diretrizes de Engenharia e Protocolo E2E da Builtt OS. Aplicar a Regra de Ouro, os contratos de arquivos, a aprovação única e o processo ponta a ponta.
    Esta modelagem converte o documento original em tarefas, decisões e caminhos explícitos, sem substituir nem revogar qualquer regra do texto integral preservado abaixo.
    Se houver divergência entre uma síntese do nó e uma regra do documento original, prevalece a regra original mais específica.
}
  start["Início / solicitação"]@{
    instruction: |-
      Identificar projeto ativo, solicitação, limites e contexto. Aplicar a Regra de Ouro (seção 1) e o fluxo oficial (seção 2). Proibido modificar código, infraestrutura, banco ou interface antes do pacote documental e da aprovação única. A execução só começa no escopo autorizado.
  }

  read_flow["Consultar fluxo visual ativo"]@{
    instruction: |-
      Antes de planejar ou executar, ler .documents/flow/flow.mmd e .documents/flow/flow.editor.json. A fonte dos metadados, permissões e condições é o JSON; Mermaid é representação visual. Seguir somente flow active e validado; não criar fluxos alternativos. Ausência de arquivos não é erro, falha de leitura deve ser informada. Observar todas as regras da seção 21.
  }

  flow_ok{"Fluxo válido ou ausente sem erro?"}@{
    instruction: |-
      SIM se não houver fluxo personalizado ou se os dois arquivos existentes forem consistentes, válidos e o fluxo aplicável estiver active. NÃO diante de erro de leitura, inconsistência ou metadados obrigatórios ausentes: bloquear e comunicar, sem sobrescrever ou executar.
  }

  classify{"Solicitação é exclusivamente QA visual?"}@{
    instruction: |-
      SIM somente se for correção estética pura sem impacto em regra de negócio, funcionalidade, API, dados, arquitetura ou permissões. Caso contrário, NÃO: seguir Harness completo. Referência: seção 15.
  }

  qa_source["Ler anotações de QA"]@{
    instruction: |-
      Ler obrigatoriamente .documents/qa/annotations.json antes de criar tasks; filtrar exclusivamente status Abertas. Selecionar os IDs informados pelo usuário. Não inventar QA nem consolidar problemas distintos, salvo ordem explícita. Se não houver IDs, resumir QAs abertos e pedir definição de escopo. Seção 15.1.
  }

  qa_scope{"QAs abertos e escopo definido?"}@{
    instruction: |-
      SIM quando os IDs existirem, estiverem abertos e o escopo estiver claro. NÃO quando faltar ID/escopo, anotação ou status aberto; não criar tasks fora do escopo.
  }

  qa_pure{"Impacto estritamente visual confirmado?"}@{
    instruction: |-
      SIM só se todas as anotações selecionadas forem puramente visuais. NÃO quando alguma revelar impacto funcional, arquitetural, de dados, integração, API, permissão ou regra de negócio: cancelar exceção e retomar Harness completo para o item.
  }

  qa_tasks["Criar Task List para QA"]@{
    instruction: |-
      Criar uma task por anotação QA, salvo consolidação explicitamente solicitada. Usar - [ ] TASK-QA-<ID-DO-QA>-001: Título; incrementos -002 etc apenas para intervenções independentes. Registrar em .documents/task/task.md; não marcar conclusão na criação. Seção 15.1.
  }

  qa_details["Detalhar cada Task QA"]@{
    instruction: |-
      Em .documents/task/task.details.md, incluir seção # TASK-QA-<ID-DO-QA>-001 — Título da Task. Registrar origem, URL/tela, elemento, evidência, problema, resultado esperado, escopo, arquivos, plano, critérios, validação e riscos; preservar as demais seções. Seções 10 e 15.1.
  }

  qa_estimate["Estimar QA no Act IA"]@{
    instruction: |-
      Estimar individualmente somente tasks QA abertas, com cenários Sem IA e Com IA e justificativa. Usar store canônico .documents/estimativa/estimativas.json e espelhos .documents/estimativa.json e .documents/estimativa.md, preservando histórico e snapshots. Seções 11 e 15.
  }

  discovery_exists{"Existem artefatos em .discovery/saida?"}@{
    instruction: |-
      Se SIM, consultar somente para leitura. Se NÃO, a etapa Discovery pode ser pulada. Não confundir ausência com falha de acesso. Seções 2 e 3.
  }

  discovery["Discovery / análise dos artefatos"]@{
    instruction: |-
      Ler .discovery/saida sem editar, sobrescrever ou excluir. Identificar contexto, regras, escopo, premissas, fontes, riscos e lacunas. Reconsultar quando houver dúvidas ou divergências. Nunca inventar informações. Seção 3.
  }

  tap["TAP / Termo de Abertura"]@{
    instruction: |-
      Criar ou atualizar exclusivamente .documents/project-charter.md segundo template oficial. Incluir identificação, histórico, sumário, contexto, problema, objetivos, escopo, stakeholders, premissas, restrições, benefícios, regras, fluxos, integrações, indicadores, aceite, riscos e rastreabilidade. Registrar ausências; sem aprovação isolada. Seção 4.
  }

  reqs["REQs / Requirements"]@{
    instruction: |-
      Derivar todos os REQs da TAP; cada REQ corresponde a necessidade macro rastreável. Criar .documents/requirements/REQ-0001-titulo.md conforme template oficial e seus campos. Não duplicar, não inventar e não solicitar aprovação individual. Seção 5.
  }

  rfs["RFs / requisitos funcionais"]@{
    instruction: |-
      Analisar cada REQ e criar todos os RFs necessários, vinculados ao REQ pai, sem genéricos ou duplicados. Usar .documents/functional-requirements/RF-0001-01-titulo.md com história, regras, fluxos, dados, validações, permissões, integrações e aceite. Sem aprovação intermediária. Seção 6.
  }

  design["Design / planejamento técnico"]@{
    instruction: |-
      Ler antes de atualizar .documents/design/design.md, único e acumulativo. Registrar arquitetura, módulos, dados, serviços, APIs, segurança, frontend/backend, integrações, observabilidade, QA, riscos e rastreabilidade. Se estiver aderente, declarar revisão sem alteração. Não usar Design como Task List. Seção 7.
  }

  ui_impact{"Há RFs com interface de usuário?"}@{
    instruction: |-
      SIM para tela, modal, drawer, formulário, grid, dashboard, wizard, painel, card ou componente interativo. NÃO quando não existir impacto de UI: registrar DRI não aplicável com justificativa. Seção 8.
  }

  dri["DRI / requisitos de interface"]@{
    instruction: |-
      Criar/revisar exclusivamente .documents/dri/dri.md, usando o template RI, uma seção # RI-0001 — Nome da Interface por interface. Incluir arquitetura de informação, estados, interações, dados, acessibilidade, responsividade, microcopy, critérios de aceite e rastreabilidade. Não incluir tasks. Seção 8.
  }

  dri_na["Registrar DRI não aplicável"]@{
    instruction: |-
      Registrar DRI: Não aplicável e justificar a inexistência de requisitos de interface. Não inventar telas nem alterar desnecessariamente o documento vivo. Seção 8.
  }

  task_list["Task List por RF"]@{
    instruction: |-
      Analisar cada RF, Design e DRI aplicável; registrar todas as tasks justificadas em .documents/task/task.md com - [ ] TASK-RF-0001-01-001: Título. Uma ou mais tasks rastreáveis por RF, sem duplicações, todas abertas inicialmente. Sem plano detalhado aqui. Seção 9.
  }

  task_details["Task Details por task"]@{
    instruction: |-
      Registrar cada task em .documents/task/task.details.md como # TASK-RF-0001-01-001 — Título da Task. Atualizar apenas sua seção; anexar novas ao final e preservar conteúdo anterior. Descrever escopo, entradas/saídas, arquivos [NOVO]/[MODIFICAR]/[DELETAR], APIs, dados, passos, testes, aceite, DoR, DoD, riscos e evidências; não executar. Seção 10.
  }

  estimate["Estimativa realista obrigatória"]@{
    instruction: |-
      Reler GPT_INSTRUCTIONS.md, Task List, Task Details e todos os arquivos de estimativa existentes. Estimar task a task apenas as abertas, sem valores fixos 4h/8h, separando esforço manual_hours e humano com IA ai_hours sem redutor percentual fixo. Retornar id, complexity, task_type, technical_area, manual_hours, ai_hours, rationale; Act IA calcula totais/histórico, snapshots, custos e dias. Respeitar contrato JSON exato, hourly_rate>0 e 1<=daily_hours<=24. Preservar items, closed_snapshots, runs, history. Seção 11 e subseções 11.1 a 11.5.3.
  }

  package_ok{"Pacote documentado, estimado e rastreável?"}@{
    instruction: |-
      Verificar TAP, REQs, RFs, Design, DRI quando aplicável, Task List, Task Details, Estimativa, lacunas, riscos, vínculos e critérios de aceitação. No QA visual, validar pacote reduzido Task, Details, Estimativa. SIM somente quando pronto para aprovação única; NÃO para inconsistências ou lacunas impeditivas. Seções 1, 2, 11, 12 e 15.
  }

  fix_docs["Corrigir apenas artefatos necessários"]@{
    instruction: |-
      Ajustar somente arquivos/seções afetados, sem recriar nem perder versões, histórico ou conteúdo. Reapresentar o pacote quando estiver consistente em nova interação; não executar e não afirmar aprovação. Seções 5, 10, 12.
  }

  approval["Apresentar pacote e solicitar aprovação única"]@{
    instruction: |-
      Apresentar todos os documentos do pacote, estimativa, pendências e riscos. Para Harness exigir a frase literal: Para autorizar a execução de todas as tasks planejadas, responda: "Aprovado executar o pacote Harness". Para pacote QA reduzido, solicitar aprovação única de escopo QA, preservando restrição de não executar antes da aprovação. Não pedir aprovação por documento nem task. Seções 12, 15, 18.
  }

  approved{"Aprovação explícita recebida?"}@{
    instruction: |-
      SIM somente com aprovação explícita do pacote no escopo documentado; para o Harness, frase literal Aprovado executar o pacote Harness. NÃO se ausente, negada ou pendente: permanecer em planejamento. Não considerar criação do pacote como autorização. Seções 1, 12 e 18.
  }

  infra_needed{"Há operação Git privado, VM, SSH ou deploy?"}@{
    instruction: |-
      SIM se execução exige infraestrutura remota, acesso Git, deploy ou comandos em VM. NÃO para execução puramente local sem esses acessos. Toda operação exige escopo previamente aprovado. Seções 14.1 e 20.
  }

  ops_check["Verificar Ops Infra, ambiente e permissões"]@{
    instruction: |-
      Consultar projeto e Ops Infra → VM/Acesso, Git/Acessos e Ambiente. Validar allow_read/allow_push/allow_deploy conforme operação; checar permissões reais, tokens via ferramentas integradas e SSH separadamente. Não solicitar segredos no chat, não contornar negativas e não expor arquivos de credenciais ou chaves. Conferir branch, commit, destino e rollback. Seção 20.
  }

  ops_allowed{"Acessos e permissões são suficientes?"}@{
    instruction: |-
      SIM apenas com perfil, credenciais e flags adequados para ação autorizada. NÃO quando faltar acesso, houver erro, permissão negada ou inconsistência; relatar ajuste necessário sem burlar os controles. Seção 20.
  }

  execution["Executar tasks sequencialmente"]@{
    instruction: |-
      Executar uma task por vez, na ordem de .documents/task/task.md e conforme .documents/task/task.details.md; sem nova aprovação intermediária. Aplicar alterações cirúrgicas/PATCH, evitar sobrescritas grandes; após cada task, revisar sintaxe, runtime real, dependências, teste e evidência. Tratar falhas antes de avançar. Se surgir impacto funcional num QA visual, parar exceção e retomar Harness completo para o item. Seção 13 e 15.1.
  }

  tasks_valid{"Todas as tasks executadas e verificadas?"}@{
    instruction: |-
      SIM apenas quando cada task autorizada tiver execução e verificação técnica documentadas. NÃO quando alguma falhar, não puder ser verificada ou depender de acesso/ambiente ausente. Seções 13 e 14.
  }

  fix_task["Corrigir falha sem avançar indevidamente"]@{
    instruction: |-
      Registrar erro, causa e evidências; corrigir pontualmente quando viável e testar de novo, sem avançar para outra task com falha crítica não tratada. Se não houver ambiente de execução, mudar para validação estática ou VM e declarar limites. Seção 13 e 14.1.
  }

  fixed{"Falha corrigida e verificada?"}@{
    instruction: |-
      SIM se o resultado técnico foi verificado com evidência; caso contrário NÃO, registrar bloqueio e riscos residuais sem marcar conclusão ou inventar testes. Seção 13.
  }

  mark_tasks["Marcar conclusão das tasks validadas"]@{
    instruction: |-
      Somente após executar e verificar, alterar checkbox de - [ ] para - [x] no mesmo ID de .documents/task/task.md; sincronizar os snapshots de estimativas via Act IA sem perder histórico. Preservar as seções do Task Details. Seções 9 a 13.
  }

  qa_final["QA consolidado e validação do runtime"]@{
    instruction: |-
      Conferir sintaxe, build, lint, testes, regressão, Git, arquivos impactados e critérios de aceite. Identificar runtime real; ausência de node/npm/python/docker local em projeto de VM não significa falha da aplicação. Preferir validação na VM/Compose/health quando autorizada; caso inviável, revisão estática e registro do que não foi testado. Seção 14 e 14.1.
  }

  e2e_plan["Criar/atualizar testes E2E reais"]@{
    instruction: |-
      Criar casos em .documents/test/test.md com - [ ] TEST-E2E-001: Título e detalhes em .documents/test/test.details.md com # TEST-E2E-001 — Título. Cada ID único, estável e idêntico nos dois arquivos. Preservar históricos, vincular task/RF e escrever Status, Task relacionada, RF / Requisito, Resultado obtido e Evidências em sintaxe exata. Planejar fluxo principal, falhas, permissão, persistência, integração e regressão. Referência: Etapa Final Testes E2E e subseções 13.1-13.5 (após seção 19 do documento original).
  }

  e2e_env{"Ambiente autorizado e teste executável?"}@{
    instruction: |-
      SIM quando ambiente, credencial, versão, pré-condições e massa sintética permitirem executar o fluxo real. NÃO quando ausentes; registrar Bloqueado, motivo, pendências e não afirmar aprovação. Etapa Final E2E.
  }

  e2e_run["Executar testes E2E e registrar evidências"]@{
    instruction: |-
      Executar passos reproduzíveis no ambiente correto. Atualizar Status com somente Não executado, Em execução, Aprovado, Reprovado ou Bloqueado; checkbox [x] exclusivamente para Aprovado com evidência real. Preservar datas ISO com fuso, versões, resultados, histórico, defeitos e reexecuções. Validar renderização na interface Qualidade → Testes E2E quando possível. Não tratar build/lint como teste E2E aprovado. Etapa Final E2E subseções 13.1-13.5.
  }

  e2e_blocked["Registrar testes bloqueados ou não executados"]@{
    instruction: |-
      Manter checkbox [ ] e Status Bloqueado ou Não executado conforme situação real; explicitar ambiente, dependência, acesso e risco residual. Não criar evidência fictícia nem marcar aprovado. Etapa Final E2E.
  }

  closing["Relatório final e validação do usuário"]@{
    instruction: |-
      Informar tasks e arquivos alterados, testes planejados/executados/aprovados/reprovados/bloqueados, riscos, pendências, ambiente, branch/commit e evidências. Distinguir validação estática de execução real, configuração de deploy de deploy validado; somente após todas as verificações solicitar validação final do usuário. Seções 14, 20, 21 e Etapa Final E2E.
  }

  end_success["Fim / entrega e pendências reais"]@{
    instruction: |-
      Finalizar o ciclo do pacote com relato factual, rastreabilidade, evidências e pendências. Não inventar aprovação de testes, resultados, deploy ou comprovação.
  }

  end_hold["Fim / aguardando aprovação"]@{
    instruction: |-
      Parar em planejamento. A execução deve aguardar aprovação única explícita do pacote.
  }

  end_scope["Fim / escopo QA pendente"]@{
    instruction: |-
      Resumir QAs abertos e solicitar escopo claro; não criar task nem executar até definição.
  }

  end_revise["Fim / revisão documental necessária"]@{
    instruction: |-
      Deixar pacote em planejamento, registrar divergências e reparos específicos; apresentar para aprovação em nova execução após correção.
  }

  end_block["Fim / bloqueio técnico documentado"]@{
    instruction: |-
      Registrar motivo, evidência disponível, ação necessária e risco residual; não burlar Ops Infra, não marcar tasks não verificadas como concluídas.
  }

  end_flow["Fim / inconsistência do fluxo visual"]@{
    instruction: |-
      Registrar erro de leitura, divergência do flow.mmd/editor.json ou flow inválido. Não sobrescrever os arquivos nem executar sequência não validada.
  }

  start --> read_flow
  read_flow --> flow_ok
  flow_ok -- Sim --> classify
  flow_ok -- Não --> end_flow
  classify -- Sim --> qa_source
  classify -- Não --> discovery_exists
  qa_source --> qa_scope
  qa_scope -- Sim --> qa_pure
  qa_scope -- Não --> end_scope
  qa_pure -- Sim --> qa_tasks
  qa_pure -- Não --> discovery_exists
  qa_tasks --> qa_details
  qa_details --> qa_estimate
  qa_estimate --> package_ok
  discovery_exists -- Sim --> discovery
  discovery_exists -- Não --> tap
  discovery --> tap
  tap --> reqs
  reqs --> rfs
  rfs --> design
  design --> ui_impact
  ui_impact -- Sim --> dri
  ui_impact -- Não --> dri_na
  dri --> task_list
  dri_na --> task_list
  task_list --> task_details
  task_details --> estimate
  estimate --> package_ok
  package_ok -- Sim --> approval
  package_ok -- Não --> fix_docs
  fix_docs --> end_revise
  approval --> approved
  approved -- Sim --> infra_needed
  approved -- Não --> end_hold
  infra_needed -- Sim --> ops_check
  infra_needed -- Não --> execution
  ops_check --> ops_allowed
  ops_allowed -- Sim --> execution
  ops_allowed -- Não --> end_block
  execution --> tasks_valid
  tasks_valid -- Sim --> mark_tasks
  tasks_valid -- Não --> fix_task
  fix_task --> fixed
  fixed -- Sim --> mark_tasks
  fixed -- Não --> end_block
  mark_tasks --> qa_final
  qa_final --> e2e_plan
  e2e_plan --> e2e_env
  e2e_env -- Sim --> e2e_run
  e2e_env -- Não --> e2e_blocked
  e2e_run --> closing
  e2e_blocked --> closing
  closing --> end_success
end

%% Ao criar ou editar diagramas Mermaid erDiagram, consulte .documents/diagramas/erDiagram-template.mmd como referência de sintaxe.
