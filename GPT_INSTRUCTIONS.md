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

  der_pattern{"Template erDiagram-template.mmd acessível?"}@{
    instruction: |-
      Antes de criar ou atualizar qualquer DER, ler obrigatoriamente .documents/diagramas/erDiagram-template.mmd, que é a referência canônica de estrutura e sintaxe. SIM somente quando o arquivo estiver acessível, legível e sua sintaxe puder ser analisada. NÃO quando estiver ausente, ilegível ou inconsistente: registrar bloqueio e não gerar diagrama por aproximação. Também listar os DERs já existentes em .documents/diagramas para evitar duplicidades e preservar o padrão real de organização dos arquivos.
  }

  der_reuse["DER / utilizar erDiagram-template.mmd como referência"]@{
    instruction: |-
      OBRIGATÓRIO: antes de produzir ou alterar qualquer DER, abrir e ler integralmente o arquivo .documents/diagramas/erDiagram-template.mmd (equivalente Windows .documents\\diagramas\\erDiagram-template.mmd) e utilizar sua estrutura, sintaxe Mermaid erDiagram, notação, organização, comentários, convenções e estilo como referência principal. Criar ou atualizar arquivos DER SEMPRE dentro de .documents/diagramas, preferindo reutilizar o arquivo existente do domínio e sem duplicar o mesmo diagrama; preservar o template e históricos. Identificar CADA campo/atributo com o status explícito EXISTENTE (comprovado nas migrations atuais) ou PROPOSTO (ausente e justificado por REQ/RF), usando a representação e os comentários previstos no template; nunca deixar campo sem classificação. Diferenciar FK FÍSICA, confirmada por constraint efetivamente declarada nas migrations, de RELACIONAMENTO LÓGICO, associado por ORM/convenção/regra sem constraint física comprovada. Indicar a distinção na legenda ou comentários com sintaxe válida conforme o template; não inferir FK física pelo nome *_id nem por uma linha no gráfico. Rastrear PK e FK físicas, referência lógica, migrations fonte e mudanças propostas. Se o template não puder ser consultado, BLOQUEAR a geração; não inventar ou substituir silenciosamente sua estrutura.
  }

  der_initial["DER / template ausente ou ilegível: bloquear"]@{
    instruction: |-
      Se o arquivo obrigatório .documents/diagramas/erDiagram-template.mmd estiver ausente ou não puder ser lido, não criar DER com estrutura alternativa, não gerar arquivo .md genérico e não modificar DER existente. Registrar erro, caminho exato, situação de acesso e providência necessária; encaminhar a der_block até que o template esteja disponível. Nunca presumir conteúdo de template não consultado.
  }

  der_document["DER / criar ou atualizar diagrama sem duplicidades"]@{
    instruction: |-
      Criar ou revisar DERs somente dentro de .documents/diagramas e obrigatoriamente usar a estrutura/sintaxe do arquivo .documents/diagramas/erDiagram-template.mmd previamente lido. Identificar INDIVIDUALMENTE CADA campo como EXISTENTE (comprovado nas migrations) ou PROPOSTO (ausente e fundamentado por REQ/RF), conforme convenção do template, incluindo legenda/comentários válidos quando necessário. Registrar PK e diferenciar FK física efetivamente declarada nas migrations de relacionamento lógico sem constraint comprovada; jamais deduzir FK física somente por *_id, ORM ou linha Mermaid. Apresentar migrations e justificativas, evitar duplicar tabelas/colunas/constraints/arquivos; se não houver mudanças registrar PROPOSTO: nenhuma alteração necessária. Não modificar o template nem executar migrations nesta etapa.
  }

  der_check{"DER validado contra migrations e sem duplicidades?"}@{
    instruction: |-
      SIM somente após leitura efetiva de .documents/diagramas/erDiagram-template.mmd, uso fiel de sua estrutura e sintaxe, análise das migrations/DERs existentes e identificação explícita de CADA campo como EXISTENTE ou PROPOSTO; PK e FK física declarada nas migrations diferenciadas de relacionamento lógico; rastreabilidade REQ/RF e ausência de duplicidades, conflitos ou lacunas críticas. NÃO quando faltar evidência, houver duplicata, conflito ou leitura insuficiente; impedir passagem ao planejamento das tasks.
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
      Após execução técnica, QA e atualização documental/testes, confirmar branch dev, verificar status/diff e commits pendentes, e auditar os comprovantes de commit e push individual de CADA TASK antes da próxima. Esta revisão final complementa, mas não substitui, o checkpoint obrigatório por task. Revisar alterações vinculadas ao pacote e arquivos sensíveis, garantir ausência de credenciais, .env e artefatos privados. Não incluir mudanças alheias, arquivos gerados indevidos ou conteúdo fora do escopo. Não criar backup nem branch temporária.
  }

  git_changes{"Git / há alterações novas do pacote para commitar?"}@{
    instruction: |-
      SIM se existem arquivos alterados/adicionados/removidos pertencentes ao escopo e validados; NÃO se não há diff do pacote (não gerar commit vazio). Em ambos os casos, verificar tracking do remoto e se commits locais pendentes precisam ser publicados.
  }

  git_commit_push["Git / commit e push obrigatórios para dev"]@{
    instruction: |-
      Estando em dev e havendo alterações válidas, stage somente arquivos do pacote, criar commit descritivo rastreável por task/RF e executar push para origin/dev pela integração autorizada. Para cada task, commit e push já devem ter ocorrido antes da task seguinte; esta etapa FINAL deve apenas conferir SHAs de todas as tasks e commitar/pushar alterações complementares de QA, relatórios ou testes gerados depois dos commits individuais, sem usá-la para substituir commits por task. Publicar também commits locais válidos ainda não enviados; não fazer push para main/hml como desenvolvimento. Respeitar allow_push, token, regras de proteção e proibição de force-push. Nunca marcar push realizado sem confirmação remota.
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
      Executar a homologação funcional do commit da branch Git hml EXCLUSIVAMENTE na MESMA instalação local preexistente; não provisionar outro ambiente, banco temporário, container adicional ou dados de usuários paralelos. Confirmar versão candidata e testes reais de frontend/backend, autenticação, permissões (incluindo admin/super-admin), persistência, responsividade, integrações e regressão, com dados preservados e evidência. Branch hml não significa ambiente físico adicional, push Git não equivale a deploy nem a teste aprovado. Se a mesma instalação não permitir teste seguro da versão, registrar bloqueio.
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
      Consolidar estado real de main (produção), dev (desenvolvimento) e hml (pré-produção), relacionar CADA ID de task ao seu commit específico e respectivo push/SHA em origin/dev (ou justificativa verificável de ausência de alterações), informar pushes realizados ou pendentes, homologação, autorização de release e impedimentos. Distinguir push de deploy. Não inventar evidências, backups, aprovações ou Git remoto verificado.
  }

  local_inspect["Local / inspecionar instalação e serviços"]@{
    instruction: |-
      Após aprovação Harness, permissões e branch dev, identificar a instalação local EXISTENTE usada para TODAS as atividades de desenvolvimento, testes e homologação funcional. Inspecionar stack, frontend, backend, banco, containers/volumes, arquivos .env sem revelar segredos, usuários admin/super-admin preexistentes, portas e serviços. A instalação única deve permanecer entre TODAS as tasks; é proibido criar segundo ambiente, containers extras ou banco temporário de teste/hml. Não reinstalar/inicializar novamente o projeto quando já estiver operacional.
  }

  local_access{"Local / ambiente acessível e inicialização segura?"}@{
    instruction: |-
      SIM quando houver acesso autorizado ao runtime local, recursos/credenciais necessários e procedimento conhecido para iniciar/verificar os serviços, sem conflito de portas ou impacto destrutivo. NÃO se o agente não tiver host/terminal persistente, faltarem dependências indispensáveis, segredos/serviços, houver conflitos ou risco de dados; registrar bloqueio. Não tratar VM remota como instalação local nem inventar acesso.
  }

  local_single_instance["Local / inventariar e reutilizar instalação única"]@{
    instruction: |-
      Esta instalação preexistente é O ÚNICO ambiente físico autorizado para desenvolvimento, testes funcionais e homologação deste projeto. Identificar e reutilizar exatamente seu projeto, processo frontend/backend, banco, containers/volumes/portas e configurações atuais. Inspecionar sem duplicar: é proibido criar ambiente paralelo, banco temporário de homologação, container adicional, nova stack, outro diretório de instalação, banco de teste descartável ou reinicializar instalação sem necessidade. Branches Git dev/hml/main representam estágios de código, não autorização para novas instalações. Registrar recursos existentes, versões, volume/banco e usuários admin/super-admin provisionados pelo instalador sem expor credenciais.
  }

  local_single_ready{"Local / instalação e dados originais estão preservados?"}@{
    instruction: |-
      SIM somente após confirmar que a instalação única foi identificada, seus dados persistem, existem os usuários admin/super-admin esperados (ou sua situação foi documentada e validada), e nenhuma segunda instância, banco, volume ou container está sendo criado. NÃO em caso de risco aos dados, instalação incerta, perda de credencial/acesso ou dúvida sobre ambiente. Não contornar criando outro ambiente; bloquear e relatar.
  }

  local_start["Local / instalar dependências necessárias e iniciar aplicação"]@{
    instruction: |-
      Se a instância LOCAL PREEXISTENTE estiver funcionando, apenas reutilizar. Se serviços dela estiverem parados, iniciar SOMENTE os mesmos serviços/containers já previstos pela instalação, sem criar containers adicionais, bancos temporários, ambientes de homologação separados ou nova instalação. Preservar banco e dados existentes, especialmente admin e super-admin criados pelo instalador. Não rodar install/reinstall, seeders, resets, migrate:fresh, db:wipe, recriação de volumes ou operações destrutivas. Usar configuração/porta atual, registrar URL e estado real; migrations necessárias passam obrigatoriamente pelo gate de segurança e aplicam-se ao mesmo banco local.
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

  local_migration_needed{"Local / mudança exige migration no banco existente?"}@{
    instruction: |-
      SIM somente se a implementação aprovada introduzir mudança real de esquema e existir migration necessária documentada no DER/Task Details; NÃO se não há alteração de esquema ou se as migrations relevantes já foram aplicadas. Consultar o histórico real de migrations do banco local existente antes de executar, evitar reaplicação e duplicidades; não criar outro banco para testes.
  }

  local_migration_review["Local / revisar segurança e compatibilidade das migrations"]@{
    instruction: |-
      Antes de aplicar qualquer migration no MESMO banco local existente, comparar esquema atual, histórico de migrations, estado dos dados, usuários admin/super-admin, constraints e índices; avaliar dependências, migração de dados, risco de bloqueio/indisponibilidade, compatibilidade/reversibilidade e necessidade de backup ou plano de recuperação. Não criar backup automático, branch backup, snapshot/volume paralelo ou novo banco; se a proteção dos dados exigir backup prévio não existente, ação destrutiva, risco não mitigado ou autorização específica, BLOQUEAR e obter encaminhamento explícito antes de modificar. Nunca executar migrate:fresh, db:wipe, drop all, reset, limpeza de volumes ou recriar banco/containers.
  }

  local_migration_safe{"Local / migration necessária é segura e autorizada?"}@{
    instruction: |-
      SIM só se migration faz parte da task/pacote previamente aprovados, é compatível com o esquema e dados atuais e todos os controles de preservação/recuperação necessários estão atendidos sem ações destrutivas. NÃO quando faltarem evidências de segurança, houver risco aos admin/super-admin ou necessidade não atendida de backup/rollback; interromper e registrar. Não inferir autorização para migração destrutiva.
  }

  local_migration_apply["Local / aplicar migrations apenas no banco existente"]@{
    instruction: |-
      Executar somente migrations seguras e aprovadas, no banco LOCAL PREEXISTENTE e na conexão correta do projeto; usar comandos oficiais do framework que preservam tabelas/dados existentes. Não criar banco, schema de homologação, container, volume ou ambiente extra. Nunca rodar migrate:fresh, db:wipe, reset de DB, truncates, seeders que recriem admin/super-admin, exclusão de volumes, migrations destrutivas ou ações fora do escopo. Registrar IDs/arquivos executados, resultados e logs sem credenciais.
  }

  local_migration_preserved{"Local / dados e administradores preservados?"}@{
    instruction: |-
      SIM somente após verificar tabelas e registros existentes, integridade/persistência, presença e login/permissões dos usuários admin e super-admin provisionados pelo instalador, estado das migrations e ausência de perda de dados. NÃO se houver falha, incompatibilidade ou usuário/registro comprometido: bloquear, registrar evidência, não reinicializar banco e não encobrir perdas.
  }

  local_real_validation["Local / validar frontend e backend reais na mesma instalação"]@{
    instruction: |-
      Executar na mesma instalação local existente, sem ambientes paralelos e sem duplicar containers/bancos, os testes funcionais da alteração na aplicação REAL: frontend e backend/API, autenticação com contas autorizadas (incluindo fluxos admin/super-admin pertinentes sem expor senhas), permissões/roles, CRUD e persistência com dados de teste controlados sem sobrescrever dados de usuários, responsividade nas larguras/telas pertinentes, integrações reais disponíveis, filas/workers, validações negativas, regressão e saúde de serviços/logs. Não considerar build/lint suficientes; preservar dados preexistentes e não desligar/reinstalar a aplicação entre tasks.
  }

  local_real_valid{"Local / testes reais completos passaram?"}@{
    instruction: |-
      SIM apenas se testes executados no ÚNICO ambiente local comprovarem frontend, backend, autenticação, autorização, persistência, responsividade e integrações aplicáveis sem perda de dados/usuários; registrar evidências, versão e URL. NÃO diante de falhas ou teste crítico não executável: declarar bloqueio/resultado real e não validar artificialmente. Não criar banco temporário para contornar.
  }

  local_hml_single["Homologação / usar a MESMA instalação local"]@{
    instruction: |-
      Após promoção Git dev para hml autorizada, executar a validação da versão candidata usando EXCLUSIVAMENTE a mesma aplicação, banco local, containers e volumes preexistentes. Branch hml é referência Git de pré-produção, NÃO segundo ambiente físico. Quando necessário representar a versão homologada, usar atualização de código controlada na instalação existente, verificando ausência de alterações locais pendentes e compatibilidade de banco; não criar checkout/instalação paralela, outro banco, container adicional ou seed de usuários. Se não for seguro atualizar sem risco para dados/processo, BLOQUEAR e documentar. Depois restaurar operação normal da dev na mesma instalação com validação, sem reinstalar ou perder dados.
  }

  local_hml_prepared{"Homologação / versão pronta sem criar outro ambiente?"}@{
    instruction: |-
      SIM quando a versão candidata da hml estiver disponível para testes na mesma instalação local (ou os testes da versão exata já forem válidos e rastreáveis), com dados, serviços e usuários do instalador preservados, sem outro ambiente/BD/container e sem troca destrutiva. NÃO quando houver risco aos dados ou não for possível usar a instalação única com segurança; registrar bloqueio e não afirmar homologação.
  }

  local_postchange["Local / atualizar instalação após implementação"]@{
    instruction: |-
      Para CADA task e após o QA técnico consolidado, aplicar atualizações diretamente na MESMA instalação local preexistente: preferir hot reload e rebuild/restart SOMENTE se tecnicamente necessário, sem reinstalar ou encerrar serviços desnecessariamente. Manter frontend/backend e banco/volumes únicos. Toda migration aprovada será aplicada exclusivamente no banco local existente, somente após revisão de esquema, compatibilidade, segurança, impacto em admin/super-admin e necessidade de backup/recuperação. É proibido usar migrate:fresh, db:wipe, limpar/recriar volumes, resetar dados ou criar banco/ambiente/container paralelo.
  }

  local_postchange_healthy{"Local / versão alterada está funcionando ponta a ponta?"}@{
    instruction: |-
      SIM somente com versão atual da dev carregada na MESMA instalação local, serviços essenciais ativos, URLs saudáveis, banco e admin/super-admin preservados, e validação real da aplicação incluindo autenticação, permissões, persistência, responsividade e integrações pertinentes. NÃO para versão antiga, serviço falho, dado alterado indevidamente, reinstalação ou ambiente paralelo.
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
      Após commits/push e eventuais homologações Git, devolver a MESMA instalação local preexistente à versão da dev quando necessário/seguro, sem reinstall, bancos/containers paralelos ou perda de alterações/dados. Validar novamente frontend, backend, banco, autenticação/permissões admin e super-admin, persistência, responsividade e integrações pertinentes, incluindo URL/portas e health. Manter serviços operacionais entre as tasks e ao concluir, com reinício apenas se necessário. Registrar o que foi observado; não prometer disponibilidade futura indefinida sem suporte de persistência.
  }

  local_final_ok{"Local / projeto completo continua rodando?"}@{
    instruction: |-
      SIM apenas se a MESMA instalação local persistente estiver rodando versão dev após as últimas operações, com serviços e URL acessíveis, dados e usuários admin/super-admin do instalador preservados, e autenticação, permissões, persistência, responsividade e integrações pertinentes validadas na aplicação real. NÃO para falhas ou evidências indisponíveis, reinstalação, ambiente paralelo ou banco/container adicional. Registrar e bloquear se não comprovado.
  }

  local_block["Local / indisponibilidade ou limitação registrada"]@{
    instruction: |-
      Registrar requisito/serviço ausente, ferramenta/acesso indisponível, logs/resultados, URL/porta esperada, tentativas realizadas, versão/branch e providência exata. Não informar instalação local em execução sem verificação nem mascarar bloqueio como sucesso. Não acessar VM por conta própria como substituto de local, não usar processos ou credenciais indevidos e não eliminar dados.
  }

  git_task_checkpoint["Git / checkpoint obrigatório por TASK"]@{
    instruction: |-
      Contrato repetido DENTRO da execução sequencial, para cada TASK-RF ou TASK-QA do pacote aprovado: implementar apenas a tarefa atual na branch dev; validar tecnicamente na MESMA instalação local preexistente sem reinstalar, criar ambiente/banco/container adicional ou perder usuários admin/super-admin; revisar e aplicar migrations seguras no banco local existente quando necessárias; verificar frontend/backend, autenticação, permissões, persistência, responsividade e integrações pertinentes; registrar evidência; marcar [x] no ID da task em task.md somente após sucesso; conferir git status e diff para separar alterações da própria task; criar commit automático específico com ID da TASK; realizar push obrigatório imediato para origin/dev; conferir SHA no remoto. Somente após push confirmado iniciar a próxima task. Não agrupar tasks distintas em um commit do pacote e não esperar o fim da sprint/pacote. Se task não modifica arquivos, não criar commit vazio: registrar por ID que não houve diff e SHA remoto já sincronizado. Se erro ou acesso negado, bloquear; não avançar, não usar force-push ou branch alternativa. Esta instrução governa a iteração INTERNA do nó execution; o grafo não introduz ciclos.
  }

  git_each_task_audit["Git / auditar publicação individual de cada TASK"]@{
    instruction: |-
      Após a sequência interna de execução, validar para CADA ID de task aprovada e executada o vínculo ID -> evidência de execução/teste -> checkbox [x] -> commit específico na dev -> push realizado -> SHA confirmado em origin/dev. Verificar que commits realmente existem no remoto e que nenhuma próxima task foi iniciada antes da publicação da anterior. Não confundir commit local com push; não substituir commits por tarefa por um único commit final do pacote. Tasks sem mudanças de arquivos devem apresentar registro explícito sem diff, justificado, com SHA remoto sincronizado. Relatar qualquer falta/erro como bloqueio de publicação.
  }

  git_each_task_ok{"Git / cada tarefa foi publicada antes da próxima?"}@{
    instruction: |-
      SIM somente quando todas as tasks executadas têm commit específico e push individual confirmado em origin/dev, ou registro justificado sem alterações e SHA remoto sincronizado, sem avanço indevido após falhas. NÃO se algum ID estiver sem rastreabilidade, push não verificado, commit agregado após várias tasks ou falta de permissão; bloquear e não declarar tasks/pacote publicados.
  }

  execution["Executar tasks sequencialmente"]@{
    instruction: |-
      Executar uma task por vez, na ordem de .documents/task/task.md e conforme .documents/task/task.details.md, sem nova aprovação intermediária. Para CADA task, obrigatoriamente: (1) implementar em dev de forma cirúrgica; (2) verificar código/testes e aplicação local; (3) registrar evidência e marcar o próprio ID [x] somente após validação; (4) revisar diff e stage apenas arquivos da tarefa; (5) criar commit automático específico, com ID TASK e descrição objetiva; (6) executar push IMEDIATO para origin/dev e confirmar SHA remoto; (7) somente então começar a próxima task. Este nó repete o subfluxo inteiro por task internamente para manter o grafo externo acíclico. Nenhuma task seguinte pode iniciar com push anterior pendente ou falho. Exceção: task sem mudanças reais em arquivos não recebe commit vazio; registrar ausência de diff e sincronização comprovada. Nunca esperar a conclusão de todas as tasks para fazer os primeiros commits/pushes; o passo Git do final é auditoria/complemento. Se surgir impacto funcional em QA visual, parar exceção e retomar Harness completo. Seções 13, 15.1 e adendo Git 3.2.6.
  }

  tasks_valid{"Todas as tasks executadas e verificadas?"}@{
    instruction: |-
      SIM apenas quando cada task autorizada tiver execução, verificação técnica e publicação individual em origin/dev documentadas, sem pendências de push da task anterior. NÃO se alguma falhar, não puder ser verificada/publicada ou depender de acesso/ambiente. Seções 13 e 14 e adendo Git 3.2.6.
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
      Marcar checkbox de - [ ] para - [x] na seção/linha da PRÓPRIA task assim que execução e verificação individual forem concluídas, ANTES do commit/push obrigatório daquela task; incluir essa mudança no commit quando aplicável e preservar histórico do Task Details e snapshots da estimativa. Este nó confere a sincronização final do que já foi atualizado task a task; não postergar todas as marcações até o fim do pacote. Não marcar task sem verificação. Seções 9 a 13 e adendo Git 3.2.6.
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
      SIM somente quando a MESMA instalação local existente, credencial autorizada, versão real, pré-condições e massa sintética controlada permitirem executar o fluxo real, preservando todos os dados e admin/super-admin. NÃO se exigir ambiente paralelo, banco temporário ou houver indisponibilidade; registrar Bloqueado, motivo e pendências. Etapa Final E2E.
  }

  e2e_run["Executar testes E2E e registrar evidências"]@{
    instruction: |-
      Executar os passos reproduzíveis na MESMA instalação local real, validando frontend/backend, autenticação, permissões, persistência, responsividade e integração conforme escopo. Preservar dados preexistentes e contas admin/super-admin, sem criar bancos/ambientes/containers extras. Atualizar Status com somente Não executado, Em execução, Aprovado, Reprovado ou Bloqueado; checkbox [x] exclusivamente para Aprovado com evidência real. Preservar datas ISO com fuso, versões, resultados, histórico, defeitos e reexecuções. Validar renderização na interface Qualidade → Testes E2E quando possível. Não tratar build/lint como teste E2E aprovado. Etapa Final E2E subseções 13.1-13.5.
  }

  e2e_blocked["Registrar testes bloqueados ou não executados"]@{
    instruction: |-
      Manter checkbox [ ] e Status Bloqueado ou Não executado conforme situação real; explicitar ambiente, dependência, acesso e risco residual. Não criar evidência fictícia nem marcar aprovado. Etapa Final E2E.
  }

  closing["Relatório final e validação do usuário"]@{
    instruction: |-
      Informar por task concluída: ID, validação, commit e SHA remoto origin/dev confirmado após a tarefa, ou justificativa sem diff; listar qualquer task cujo push falhou ou ficou pendente. Informar tasks e arquivos alterados, testes planejados/executados/aprovados/reprovados/bloqueados, riscos e pendências; confirmar URL/porta local, frontend/backend e dependências saudáveis, versão da dev realmente em execução e mecanismo de persistência verificado (ou indisponibilidade documentada); informar branches main/dev/hml, SHA e confirmação real dos commits/pushes, homologação e eventual autorização de produção, além das evidências. Distinguir validação estática de execução real, configuração de deploy de deploy validado; somente após todas as verificações solicitar validação final do usuário. Seções 14, 20, 21 e Etapa Final E2E.
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
  der_initial --> der_block
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
  local_access -- Sim --> local_single_instance
  local_single_instance --> local_single_ready
  local_single_ready -- Sim --> local_start
  local_single_ready -- Não --> local_block
  local_access -- Não --> local_block
  local_start --> local_ready
  local_ready -- Sim --> git_task_checkpoint
  local_ready -- Não --> local_fix_start
  local_fix_start --> local_recovered
  local_recovered -- Sim --> git_task_checkpoint
  local_recovered -- Não --> local_block
  local_block --> end_block
  git_dev_ready -- Não --> git_branch_block
  git_branch_block --> end_block
  git_task_checkpoint --> execution
  execution --> git_each_task_audit
  git_each_task_audit --> git_each_task_ok
  git_each_task_ok -- Sim --> tasks_valid
  git_each_task_ok -- Não --> git_publish_block
  tasks_valid -- Sim --> mark_tasks
  tasks_valid -- Não --> fix_task
  fix_task --> fixed
  fixed -- Sim --> mark_tasks
  fixed -- Não --> end_block
  mark_tasks --> qa_final
  qa_final --> local_postchange
  local_postchange --> local_migration_needed
  local_migration_needed -- Sim --> local_migration_review
  local_migration_needed -- Não --> local_postchange_healthy
  local_migration_review --> local_migration_safe
  local_migration_safe -- Sim --> local_migration_apply
  local_migration_safe -- Não --> local_block
  local_migration_apply --> local_migration_preserved
  local_migration_preserved -- Sim --> local_postchange_healthy
  local_migration_preserved -- Não --> local_block
  local_postchange_healthy -- Sim --> local_real_validation
  local_postchange_healthy -- Não --> local_fix_postchange
  local_fix_postchange --> local_postchange_fixed
  local_postchange_fixed -- Sim --> local_real_validation
  local_real_validation --> local_real_valid
  local_real_valid -- Sim --> e2e_plan
  local_real_valid -- Não --> local_block
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
  git_hml_published -- Sim --> local_hml_single
  local_hml_single --> local_hml_prepared
  local_hml_prepared -- Sim --> git_validate_hml
  local_hml_prepared -- Não --> local_block
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
