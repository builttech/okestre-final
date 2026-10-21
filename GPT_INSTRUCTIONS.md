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

  der_migrations["DER / leitura obrigatória das migrations"]@{
    instruction: |-
      Depois do Design e antes do DRI/Task List, localizar e ler todas as migrations relevantes do projeto ativo (em Laravel, por exemplo, database/migrations). Considerar criação, alteração, renomeação, exclusão e remoção de constraints, seguindo a sequência. Apenas inspeção: não executar migrations, SQL, alterar banco ou código antes de aprovação Harness; presença de migration no código não comprova aplicação no ambiente.
  }

  der_inventory["DER / inventário EXISTENTE"]@{
    instruction: |-
      Produzir lista verificável do schema declarado nas migrations atuais: tabelas, campos/tipos, nulabilidade/defaults, PK simples/composta, índices, unique, FKs físicas e referências lógicas; identificar migration de origem e alterações posteriores. Incluir tabelas pivô e objetos equivalentes para evitar duplicar tabelas, campos ou constraints. EXISTENTE significa declarado nas migrations, não necessariamente implantado.
  }

  der_pattern{"Há arquivos DER existentes em .documents/diagramas?"}@{
    instruction: |-
      Inspecionar sempre .documents/diagramas antes de criar DER. SIM se existir exemplo legível; NÃO se a ausência de DER for comprovada. Erro de leitura é bloqueio, não ausência. Respeitar formato, extensão, nomenclatura, estruturas, notação e seções dos arquivos existentes.
  }

  der_reuse["DER / seguir exemplo já existente"]@{
    instruction: "Ao criar ou editar diagramas Mermaid erDiagram, consulte .documents/diagramas/erDiagram-template.mmd como referência de sintaxe."
  }

  der_initial["DER / usar padrão inicial somente se não houver exemplo"]@{
    instruction: |-
      Apenas quando não existir nenhum DER prévio: adotar .documents/diagramas/DER-<escopo>.mmd com identidade, REQs/RFs, migrations, EXISTENTE, PROPOSTO, diagrama Mermaid erDiagram, PK e FK física, referências lógicas, decisões, conflitos e revisão. Não alterar convenções existentes para adotar este padrão inicial.
  }

  der_document["DER / criar ou atualizar diagrama sem duplicidades"]@{
    instruction: |-
      Criar ou revisar arquivos exclusivamente em .documents/diagramas. Apresentar EXISTENTE com evidências em migrations e PROPOSTO somente para estruturas/alterações ausentes justificadas por RF/Design. Identificar PK e distinguir FK física declarada por constraint de associação lógica sem constraint física comprovada; não inferir FK física pelo sufixo _id, ORM ou notação Mermaid. Evitar repetir tabelas/colunas/índices/constraints/diagramas. Se nenhuma mudança for necessária registrar PROPOSTO: nenhuma alteração necessária. Nunca executar migrations nesta etapa.
  }

  der_check{"DER validado contra migrations e sem duplicidades?"}@{
    instruction: |-
      SIM somente quando migrations e arquivos DER existentes foram analisados; inventário EXISTENTE e delta PROPOSTO possuem fontes, PK/FK física e lógica estão distinguídas, padrão de arquivo preservado e não há duplicidades, lacunas críticas nem conflitos com REQ/RF/Design. NÃO quando faltar evidência, houver duplicata, conflito ou leitura insuficiente; impedir passagem ao planejamento das tasks.
  }

  der_block["DER / documentar pendências e impedir liberação"]@{
    instruction: |-
      Registrar migration, tabela/campo/relação afetada, conflito ou ausência de fonte, duplicidade identificada e solução sugerida; não inventar esquemas nem modificar banco. Manter pacote em planejamento para correção documental antes da aprovação única.
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
      Analisar cada RF, Design, DER(s) em .documents/diagramas e DRI aplicável. Criar tasks de migrations apenas para o PROPOSTO necessário, sem repetir estruturas EXISTENTES; registrar todas as tasks justificadas em .documents/task/task.md com - [ ] TASK-RF-0001-01-001: Título. Uma ou mais tasks rastreáveis por RF, sem duplicações, todas abertas inicialmente. Sem plano detalhado aqui. Seção 9.
  }

  task_details["Task Details por task"]@{
    instruction: |-
      Vincular nas tasks de dados os DERs e justificar a reutilização de EXISTENTE versus mudanças PROPOSTAS. Registrar cada task em .documents/task/task.details.md como # TASK-RF-0001-01-001 — Título da Task. Atualizar apenas sua seção; anexar novas ao final e preservar conteúdo anterior. Descrever escopo, entradas/saídas, arquivos [NOVO]/[MODIFICAR]/[DELETAR], APIs, dados, passos, testes, aceite, DoR, DoD, riscos e evidências; não executar. Seção 10.
  }

  estimate["Estimativa realista obrigatória"]@{
    instruction: |-
      Reler GPT_INSTRUCTIONS.md, Task List, Task Details e todos os arquivos de estimativa existentes. Considerar no esforço a reutilização do EXISTENTE e somente o delta PROPOSTO no DER. Estimar task a task apenas as abertas, sem valores fixos 4h/8h, separando esforço manual_hours e humano com IA ai_hours sem redutor percentual fixo. Retornar id, complexity, task_type, technical_area, manual_hours, ai_hours, rationale; Act IA calcula totais/histórico, snapshots, custos e dias. Respeitar contrato JSON exato, hourly_rate>0 e 1<=daily_hours<=24. Preservar items, closed_snapshots, runs, history. Seção 11 e subseções 11.1 a 11.5.3.
  }

  package_ok{"Pacote documentado, estimado e rastreável?"}@{
    instruction: |-
      Verificar TAP, REQs, RFs, Design, DER validado contra migrations e salvo em .documents/diagramas, DRI quando aplicável, Task List, Task Details, Estimativa, lacunas, riscos, vínculos e critérios de aceitação. No QA visual, validar pacote reduzido Task, Details, Estimativa. SIM somente quando pronto para aprovação única; NÃO para inconsistências ou lacunas impeditivas. Seções 1, 2, 11, 12 e 15.
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

  infra_needed{"Git obrigatório: repositório identificado para publicação?"}@{
    instruction: |-
      SIM somente se houver repositório Git identificado para a entrega, remoto configurado e escopo autorizado; toda implementação prevê commit/push em dev. NÃO quando Git não estiver disponível/configurado: bloquear e registrar, sem ignorar publicação. Verificar também VM/SSH/deploy quando relevantes. Seções 14.1 e 20.
  }

  ops_check["Verificar Ops Infra, ambiente e permissões"]@{
    instruction: |-
      Consultar projeto e Ops Infra → VM/Acesso, Git/Acessos e Ambiente. Validar allow_read para consulta/fetch e allow_push para criação/publicação de branches, commits e merges; allow_deploy somente quando houver deploy previsto. Checar permissões reais, tokens via ferramentas integradas e SSH separadamente. Não solicitar segredos no chat, não contornar negativas e não expor arquivos de credenciais ou chaves. Conferir branch, commit, destino e rollback. Seção 20.
  }

  ops_allowed{"Acessos e permissões são suficientes?"}@{
    instruction: |-
      SIM apenas com repositório/remote válido e permissões integradas e reais suficientes para consultar branches e publicar commits/branches no escopo; respeitar proteção e PRs obrigatórios. NÃO se faltar acesso, flag, perfil ou houver negativa; informar o ajuste necessário sem contornar controles. Seção 20.
  }

  git_inspect["Git / inspecionar repositório e branches"]@{
    instruction: |-
      Após a aprovação única e a verificação de Ops Infra, identificar remote/repositório e branch padrão; consultar estado local e lista atualizada das branches remotas (fetch ou ação integrada autorizada), incluindo main, dev, hml, alterações locais, commits e divergências. Não confundir branch local com remota. Não modificar nem inicializar repositório sem escopo/autorização; não inserir token em logs ou comandos. Verificar allow_read, allow_push, credenciais e branch protections.
  }

  git_only_main{"Git remoto possui somente main?"}@{
    instruction: |-
      SIM quando o inventário remoto comprovar que main é a única branch relevante existente (nenhuma dev/hml ou outra branch). NÃO em qualquer outro cenário; não presumir estado do Git sem consulta real.
  }

  git_create_dev_hml["Git / criar somente dev e hml a partir de main"]@{
    instruction: |-
      Quando o remoto contiver somente main, criar dev e hml ambas a partir do commit atual de origin/main, respeitando proteção de branch e permissões. Publicar as duas no origin e verificar a existência remota. Nunca criar backups, branch backup, staging, feature, release, hotfix ou qualquer outra branch sem solicitação explícita; não alterar a main. Se alguma criação/push falhar, registrar bloqueio sem ocultar o estado parcial.
  }

  git_triad{"Git possui main, dev e hml no remoto?"}@{
    instruction: |-
      SIM quando as três branches main, dev e hml existem no remoto. Branches extras preexistentes não devem ser modificadas ou criadas; registrar sua presença. NÃO quando faltar qualquer branch (por exemplo main+dev, main+hml ou somente dev); não completar um cenário parcial sem autorização específica.
  }

  git_select_dev["Git / preparar checkout exclusivamente em dev"]@{
    instruction: |-
      Para toda implementação, garantir checkout da branch local dev rastreando origin/dev. Conferir working tree, alterações de terceiros, divergência do remoto e conflitos antes de trocar ou atualizar branch. Usar atualização segura (fast-forward somente quando cabível). Não usar reset hard, force-push, exclusões, stash, backup ou branch auxiliar. Nunca desenvolver diretamente em main ou hml.
  }

  git_dev_ready{"Git / dev íntegra e pronta para alterações?"}@{
    instruction: |-
      SIM apenas com branch atual dev, tracking remoto confirmado, arquivos existentes preservados e checkout/sincronização segura sem conflitos nem mudanças alheias descartadas. NÃO se alterações locais, divergências, acesso ou proteção impedirem continuidade; registrar bloqueio.
  }

  git_branch_block["Git / bloquear estrutura ou checkout irregular"]@{
    instruction: |-
      Registrar branches encontradas e diferença frente ao padrão main/dev/hml, problemas de leitura/permissão/proteção, alterações locais ou conflito; não criar outras branches, não inventar backups nem resolver com reset/force. Interromper operações modificadoras e informar ação humana necessária.
  }

  git_review_changes["Git / revisar alterações para publicação em dev"]@{
    instruction: |-
      Após execução técnica, QA e atualização documental/testes, confirmar branch dev e verificar status/diff e commits pendentes. Revisar alterações vinculadas ao pacote e arquivos sensíveis, garantir ausência de credenciais, .env e artefatos privados. Não incluir mudanças alheias, arquivos gerados indevidos ou conteúdo fora do escopo. Não criar backup nem branch temporária.
  }

  git_changes{"Git / há alterações novas do pacote para commitar?"}@{
    instruction: |-
      SIM se existem arquivos alterados/adicionados/removidos pertencentes ao escopo e validados; NÃO se não há diff do pacote (não gerar commit vazio). Em ambos os casos, verificar tracking do remoto e se commits locais pendentes precisam ser publicados.
  }

  git_commit_push["Git / commit e push obrigatórios para dev"]@{
    instruction: |-
      Estando em dev e havendo alterações válidas, stage somente arquivos do pacote, criar commit descritivo rastreável por task/RF e executar push para origin/dev pela integração autorizada. Se houver múltiplas tasks concluídas, commitar por unidade coerente após verificação quando viável, e garantir publicação final do pacote. Publicar também commits locais válidos ainda não enviados; não fazer push para main/hml como desenvolvimento. Respeitar allow_push, token, regras de proteção e proibição de force-push. Nunca marcar push realizado sem confirmação remota.
  }

  git_no_diff["Git / sem alterações novas: conferir commits pendentes"]@{
    instruction: |-
      Se não houver diferença de arquivos, não criar commit artificial. Verificar se a dev local contém commits válidos ainda não publicados e enviá-los para origin/dev quando autorizados; se estiver sincronizada, registrar sem alterações a commitar e SHA atual. Sempre verificar remote e tracking.
  }

  git_push_verified{"Git / publicação em origin/dev confirmada?"}@{
    instruction: |-
      SIM só se push autorizado tiver sucesso ou dev estiver comprovadamente sincronizada, com SHA local/remoto compatível e histórico real registrado. NÃO diante de push negado, bloqueio de branch, credencial insuficiente, falha de rede, commits divergentes ou erros sem resolução; não alegar publicação.
  }

  git_publish_block["Git / registrar falha de commit ou push"]@{
    instruction: |-
      Registrar branch, remote sem segredos, SHA local quando disponível, motivo, acesso/permissão/proteção/conflito e ações pendentes. Não contornar bloqueios usando terminal alternativo, force-push, backup branch ou execução em main/hml. A falha impede declarar publicação concluída.
  }

  git_hml_ready{"Git / promoção para hml prevista e autorizada?"}@{
    instruction: |-
      SIM se entrega em dev estiver publicada e houver solicitação/escopo autorizado de homologação e condições mínimas de verificação. NÃO se a solicitação é apenas desenvolvimento, se não houver autorização para promover ou se critérios estiverem incompletos: encerrar com entrega publicada em dev, sem tocar hml/main.
  }

  git_promote_hml["Git / promover dev para hml sem desenvolvimento direto"]@{
    instruction: |-
      Com autorização correspondente, atualizar hml integrando o conteúdo de origin/dev por merge/fast-forward normal permitido pela política do repositório (ou PR exigido), revisar conflitos e preservar histórico. Realizar commit de merge se necessário, push para origin/hml e validar SHA remoto. Proibido criar branches adicionais, backup, rebase destrutivo, reset hard ou force-push. hml é exclusiva de validação pré-produção.
  }

  git_hml_published{"Git / hml publicada e íntegra?"}@{
    instruction: |-
      SIM somente quando integração e push/PR em hml foram concluídos de fato, sem conflito e com SHA verificado. NÃO se houver conflito, aprovação de PR pendente ou push negado; registrar falha, não prosseguir para produção.
  }

  git_validate_hml["Git / homologar aplicação na hml"]@{
    instruction: |-
      Executar validação pré-produção no ambiente ligado à hml quando disponível/autorizado: build, testes automatizados e testes E2E reais de fluxos principais, integração, permissões e regressão; registrar versão/commit, ambiente, evidências, falhas e status. Não equiparar push Git a deploy ou a homologação aprovada; se o ambiente não estiver disponível, registrar bloqueio.
  }

  git_hml_pass{"Git / homologação hml aprovada com evidências?"}@{
    instruction: |-
      SIM exclusivamente com testes/revisão homologados e evidências reais para o commit que será promovido. NÃO para falhas, testes bloqueados, ausência de ambiente ou aceite pendente: manter main intacta e registrar pendências.
  }

  git_prod_auth{"Git / publicação em produção foi autorizada?"}@{
    instruction: |-
      SIM apenas com autorização explícita de promoção da versão homologada para main/produção, no escopo e ambiente correspondentes, respeitando proteções e revisões exigidas. A aprovação única do pacote de desenvolvimento não equivale automaticamente à autorização de release em produção. NÃO: manter main inalterada e registrar hml aprovada aguardando release.
  }

  git_promote_main["Git / publicar exclusivamente versão homologada em main"]@{
    instruction: |-
      Integrar à main somente commit/conteúdo validado em origin/hml usando merge/PR previsto pelo repositório; respeitar aprovação de produção, proteções, testes e direitos de push. Realizar commit de merge quando necessário, push para origin/main e verificar commit remoto. Nunca desenvolver diretamente na main, publicar mudanças não homologadas, criar backup/branch paralela ou usar force-push. Push Git não representa, por si só, deploy concluído.
  }

  git_main_published{"Git / main atualizada e publicação confirmada?"}@{
    instruction: |-
      SIM apenas quando origin/main referenciar a versão homologada e a operação permitida tiver resultado confirmado. NÃO se PR pendente, conflito, proteção, erro de permissão ou push não verificado; informar bloqueio e não declarar publicação em produção.
  }

  git_record["Git / registrar branches, commits, pushes e pendências"]@{
    instruction: |-
      Consolidar estado real de main (produção), dev (desenvolvimento) e hml (pré-produção), SHA/commit por branch, push realizado ou pendente, homologação e autorização de release quando aplicáveis, e eventuais impedimentos. Distinguir push de deploy. Não inventar evidências, backups, aprovações ou Git remoto verificado.
  }

  local_inspect["Local / inspecionar instalação e serviços"]@{
    instruction: |-
      Após aprovação Harness, permissões e seleção segura da branch dev, identificar stack, scripts de inicialização, dependências, runtime e arquitetura real (frontend, backend/API, banco, workers, filas, cache, proxy). Ler README/configuração/Compose/gerenciador de processos e .env de forma segura, sem expor segredos. Verificar portas, saúde dos serviços, alterações locais, aplicações já rodando e se o agente dispõe de terminal/acesso ao host local. Reutilizar instalação e padrão já existentes; não reinstalar, duplicar instâncias ou encerrar processos alheios.
  }

  local_access{"Local / ambiente acessível e inicialização segura?"}@{
    instruction: |-
      SIM quando houver acesso autorizado ao runtime local, recursos/credenciais necessários e procedimento conhecido para iniciar/verificar os serviços, sem conflito de portas ou impacto destrutivo. NÃO se o agente não tiver host/terminal persistente, faltarem dependências indispensáveis, segredos/serviços, houver conflitos ou risco de dados; registrar bloqueio. Não tratar VM remota como instalação local nem inventar acesso.
  }

  local_start["Local / instalar dependências necessárias e iniciar aplicação"]@{
    instruction: |-
      Se já estiver funcionando, preservar a instância. Senão, usar comandos oficiais do projeto para instalar apenas dependências faltantes aprovadas, configurar serviços locais existentes e iniciar frontend, backend, banco, cache, filas/workers e demais componentes necessários. Priorizar execução desacoplada e persistente segundo configuração real (ex.: docker compose up -d, serviço local/gerenciador existente), sem garantir permanência além do que for verificável. Preservar dados e .env; não executar migrations destrutivas, seeders reais, reset, limpeza de volume ou mudanças fora do pacote sem autorização. Documentar endpoint/porta e método de inicialização.
  }

  local_ready{"Local / aplicação completa já está rodando?"}@{
    instruction: |-
      SIM só quando processos/containers indispensáveis estão ativos, portas e dependências prontas, endpoint local responde, frontend carrega e um fluxo crítico de uso/smoke test foi verificado. NÃO para processo que termina, erro no console/log/HTTP, backend indisponível, banco desconectado ou serviço faltante. Evidências devem se referir ao ambiente local real.
  }

  local_fix_start["Local / diagnosticar e recuperar inicialização"]@{
    instruction: |-
      Ler logs e erros locais, corrigir somente configuração/dependências/startup não destrutivos no escopo já aprovado, sem duplicar serviços, apagar volumes, modificar credenciais ou contornar segurança. Testar novamente. Quando exigir alteração de arquitetura, regra ou dados fora do pacote, registrar bloqueio e solicitar inclusão em novo planejamento/aprovação.
  }

  local_recovered{"Local / inicialização recuperada e verificada?"}@{
    instruction: |-
      SIM com aplicação e dependências comprovadamente rodando, endereço local e smoke test válido. NÃO se persistirem erros ou falta de acesso; não prosseguir como se estivesse funcionando.
  }

  local_postchange["Local / atualizar instalação após implementação"]@{
    instruction: |-
      Ao encerrar a execução das tasks e QA técnico, aplicar no ambiente local as modificações aprovadas da branch dev: rebuild/restart/hot reload controlado apenas dos serviços necessários, respeitando scripts e dependências. Executar apenas migrations seguras contempladas no pacote autorizado (preferir planejamento/reversibilidade), jamais resetar banco ou dados. Manter a aplicação disponível para testes; não iniciar segunda instância ou assumir que build aprovado significa serviço funcionando.
  }

  local_postchange_healthy{"Local / versão alterada está funcionando ponta a ponta?"}@{
    instruction: |-
      SIM apenas se versão/commit/worktree de dev atualizado estiver carregado no runtime local, serviços essenciais ativos, saúde HTTP/UI/API/DB validada, logs sem erro impeditivo e smoke tests relevantes à melhoria/correção aprovados. NÃO se versão antiga ainda estiver no processo, reinício falhar, porta indisponível ou rota crítica quebrada.
  }

  local_fix_postchange["Local / corrigir falha de execução após mudanças"]@{
    instruction: |-
      Investigar console, servidor, logs e dependências, aplicar reparos limitados ao escopo autorizado em dev e repetir build/restart/health. Registrar falha e resultado. Não prosseguir como sucesso se houver erro crítico; não fazer alterações destrutivas ou aceitar indisponibilidade silenciosa.
  }

  local_postchange_fixed{"Local / execução pós-mudança recuperada?"}@{
    instruction: |-
      SIM quando as alterações atuais forem servidas pelo runtime local e os smoke tests confirmarem operação funcional. NÃO quando continuar falhando ou ambiente não puder ser validado: bloquear conclusão operacional e registrar evidência/causa.
  }

  local_keep_running["Local / garantir aplicação operacional ao encerrar"]@{
    instruction: |-
      Após commit/push e promoções Git eventualmente autorizadas, confirmar que o workspace local está novamente na dev sem perda de alterações, com versão publicada/entregue correta; conferir frontend, backend, banco, workers e demais serviços ativos, portas, URL local e health/smoke test. Se precisar, reiniciar serviços de modo persistente compatível com o projeto; evitar sessões transitórias e processos duplicados. Registrar PID/container/status quando acessível e instruções de religamento. Não prometer disponibilidade contínua sem mecanismo persistente comprovado.
  }

  local_final_ok{"Local / projeto completo continua rodando?"}@{
    instruction: |-
      SIM somente com evidência atual de processos/containers essenciais saudáveis, URL funcional, integração básica e versão da dev servida localmente após as últimas operações Git. NÃO se qualquer serviço indispensável estiver parado, app estiver inacessível ou saúde não puder ser confirmada; registrar e bloquear declaração de instalação pronta.
  }

  local_block["Local / indisponibilidade ou limitação registrada"]@{
    instruction: |-
      Registrar requisito/serviço ausente, ferramenta/acesso indisponível, logs/resultados, URL/porta esperada, tentativas realizadas, versão/branch e providência exata. Não informar instalação local em execução sem verificação nem mascarar bloqueio como sucesso. Não acessar VM por conta própria como substituto de local, não usar processos ou credenciais indevidos e não eliminar dados.
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
      Conferir sintaxe, build, lint, testes, regressão, Git, arquivos impactados e critérios de aceite. A validação de build não substitui a obrigação de iniciar e comprovar a aplicação local em execução após cada melhoria, implementação, ajuste ou correção de bug. Identificar runtime real; ausência de node/npm/python/docker local em projeto de VM não significa falha da aplicação. Preferir validação na VM/Compose/health quando autorizada; caso inviável, revisão estática e registro do que não foi testado. Seção 14 e 14.1.
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
      Informar tasks e arquivos alterados, testes planejados/executados/aprovados/reprovados/bloqueados, riscos e pendências; confirmar URL/porta local, frontend/backend e dependências saudáveis, versão da dev realmente em execução e mecanismo de persistência verificado (ou indisponibilidade documentada); informar branches main/dev/hml, SHA e confirmação real dos commits/pushes, homologação e eventual autorização de produção, além das evidências. Distinguir validação estática de execução real, configuração de deploy de deploy validado; somente após todas as verificações solicitar validação final do usuário. Seções 14, 20, 21 e Etapa Final E2E.
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
  design --> der_migrations
  der_migrations --> der_inventory
  der_inventory --> der_pattern
  der_pattern -- Sim --> der_reuse
  der_pattern -- Não --> der_initial
  der_reuse --> der_document
  der_initial --> der_document
  der_document --> der_check
  der_check -- Sim --> ui_impact
  der_check -- Não --> der_block
  der_block --> end_revise
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
  infra_needed -- Não --> git_branch_block
  ops_check --> ops_allowed
  ops_allowed -- Sim --> git_inspect
  ops_allowed -- Não --> end_block
  git_inspect --> git_only_main
  git_only_main -- Sim --> git_create_dev_hml
  git_only_main -- Não --> git_triad
  git_create_dev_hml --> git_select_dev
  git_triad -- Sim --> git_select_dev
  git_triad -- Não --> git_branch_block
  git_select_dev --> git_dev_ready
  git_dev_ready -- Sim --> local_inspect
  local_inspect --> local_access
  local_access -- Sim --> local_start
  local_access -- Não --> local_block
  local_start --> local_ready
  local_ready -- Sim --> execution
  local_ready -- Não --> local_fix_start
  local_fix_start --> local_recovered
  local_recovered -- Sim --> execution
  local_recovered -- Não --> local_block
  local_block --> end_block
  git_dev_ready -- Não --> git_branch_block
  git_branch_block --> end_block
  execution --> tasks_valid
  tasks_valid -- Sim --> mark_tasks
  tasks_valid -- Não --> fix_task
  fix_task --> fixed
  fixed -- Sim --> mark_tasks
  fixed -- Não --> end_block
  mark_tasks --> qa_final
  qa_final --> local_postchange
  local_postchange --> local_postchange_healthy
  local_postchange_healthy -- Sim --> e2e_plan
  local_postchange_healthy -- Não --> local_fix_postchange
  local_fix_postchange --> local_postchange_fixed
  local_postchange_fixed -- Sim --> e2e_plan
  local_postchange_fixed -- Não --> local_block
  e2e_plan --> e2e_env
  e2e_env -- Sim --> e2e_run
  e2e_env -- Não --> e2e_blocked
  e2e_run --> git_review_changes
  e2e_blocked --> git_review_changes
  git_review_changes --> git_changes
  git_changes -- Sim --> git_commit_push
  git_changes -- Não --> git_no_diff
  git_commit_push --> git_push_verified
  git_no_diff --> git_push_verified
  git_push_verified -- Sim --> git_hml_ready
  git_push_verified -- Não --> git_publish_block
  git_publish_block --> end_block
  git_hml_ready -- Sim --> git_promote_hml
  git_hml_ready -- Não --> git_record
  git_promote_hml --> git_hml_published
  git_hml_published -- Sim --> git_validate_hml
  git_hml_published -- Não --> git_publish_block
  git_validate_hml --> git_hml_pass
  git_hml_pass -- Sim --> git_prod_auth
  git_hml_pass -- Não --> git_record
  git_prod_auth -- Sim --> git_promote_main
  git_prod_auth -- Não --> git_record
  git_promote_main --> git_main_published
  git_main_published -- Sim --> git_record
  git_main_published -- Não --> git_publish_block
  git_record --> local_keep_running
  local_keep_running --> local_final_ok
  local_final_ok -- Sim --> closing
  local_final_ok -- Não --> local_block
  closing --> end_success
end
