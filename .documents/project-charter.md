# Termo de Abertura do Projeto - act-ide-teste

## 1. Contexto

O projeto **act-ide-teste** evolui o GitIDE/Act IA como ambiente local integrado para desenvolvimento assistido por IA, com foco em produtividade, rastreabilidade e segurança operacional. O objetivo é centralizar em uma única interface recursos que normalmente ficam distribuídos entre editor de código, terminal, Git, banco de dados, documentação, agente de IA, gestão de especificações e ferramentas visuais de design.

Atualmente, fluxos de desenvolvimento com IA exigem múltiplas ferramentas e podem gerar riscos quando não há controle claro sobre arquivos modificados, comandos executados, credenciais, histórico de alterações e validação das entregas. O GitIDE busca resolver esse problema fornecendo uma ponte segura entre o usuário, o workspace local e agentes de IA, permitindo que tarefas técnicas sejam planejadas, executadas e auditadas com mais previsibilidade.

A evolução atual adiciona capacidade de **Auto Layout Flexível na aba Design**, baseada no discovery `.discovery/saida/Feat_ Auto Layout Flexível na Aba Design.md`. O Design Canvas existente usa Konva.js e já permite criar, selecionar, mover, redimensionar e persistir frames e elementos. A nova funcionalidade deve permitir que frames organizem automaticamente seus filhos com conceitos equivalentes ao Flexbox, sem introduzir Grid Layout.

## 2. Objetivo do Projeto

Construir e evoluir uma plataforma web local chamada **GitIDE/Act IA**, capaz de atuar como um IDE assistido por IA para gerenciamento de projetos de software e design, integrando edição de arquivos, terminal, Git, banco de dados, documentação, especificações funcionais, agentes de IA, automações de desenvolvimento e canvas visual em uma experiência unificada, segura e rastreável.

O resultado esperado é permitir que o usuário conduza atividades de engenharia de software e prototipação visual com apoio de IA sem perder controle sobre decisões, alterações, comandos, branches, histórico e validações.

## 3. Escopo Inicial

### Dentro do escopo

- Interface web local para seleção e gerenciamento de projetos/workspaces.
- Navegação, leitura, edição e versionamento de arquivos do projeto.
- Integração com Git para status, branches, pull, merge, deploy, commit e push.
- Terminal integrado para execução controlada de comandos aprovados.
- Painel de banco de dados para consulta SQL, conexão e exploração de tabelas.
- Configuração de credenciais e parâmetros do agente de IA.
- Integração com provedores de LLM para apoio ao desenvolvimento.
- Módulo de documentação Word para criação, listagem e download de documentos técnicos.
- Módulo de Spec-Driven Development (SDD) para especificações Markdown, critérios de aceitação e geração de testes.
- Registro de atividades, snapshots e rastreabilidade de alterações.
- Padrão visual dark, moderno, premium e consistente com a identidade do GitIDE.
- Fluxo de segurança baseado em planejamento, aprovação explícita, execução controlada e verificação.
- Design Canvas em Konva.js para composição visual de frames, layers e protótipos.
- Auto Layout Flexível em frames do Design Canvas, com direção, wrap, alinhamentos, distribuição, gaps, padding, sizing fixo/hug, elementos absolutos e persistência local.

### Fora do escopo

- Substituir completamente IDEs tradicionais como VS Code, JetBrains ou similares.
- Hospedar aplicações de terceiros em produção diretamente pelo GitIDE.
- Executar deploys sem aprovação explícita do usuário.
- Manipular credenciais sem autorização ou fora dos arquivos/configurações definidos.
- Automatizar decisões críticas sem revisão humana.
- Garantir compatibilidade universal com todos os frameworks existentes sem adaptação específica.
- Fornecer um sistema completo de CI/CD corporativo independente de ferramentas externas.
- Implementar Grid Layout, CSS Grid, áreas nomeadas, unidades fracionárias ou posicionamento manual em células na feature de Auto Layout.
- Criar backend novo para persistência do Design Canvas nesta etapa; a persistência permanece local no modelo atual do canvas.

## 4. Stakeholders

- **Solicitante:** Augusto Nascimento.
- **Usuários impactados:** Desenvolvedores, operadores técnicos, designers/prototipadores, usuários que trabalham com agentes de IA conectados ao workspace local e responsáveis por manter projetos de software no GitIDE.
- **Responsável técnico:** Equipe/operador técnico responsável pela evolução do GitIDE e pela manutenção das integrações locais.
- **Partes interessadas adicionais:** Usuários finais dos projetos gerenciados pelo GitIDE, mantenedores de repositórios Git, responsáveis por homologação, responsáveis por ambientes locais/remotos e revisores de interface.

## 5. Premissas e Restrições

- O GitIDE será executado em ambiente local ou controlado pelo usuário.
- Cada workspace deve estar associado a um projeto identificado internamente pelo GitIDE.
- Operações sensíveis, como escrita em arquivos, execução de comandos, merge, push e deploy, devem exigir aprovação explícita.
- O projeto deve preservar URLs remotas e tokens já configurados pelo usuário.
- Arquivos devem ser manipulados pelos endpoints próprios do GitIDE/Act IA, evitando comandos de shell para leitura ou escrita direta.
- Credenciais de banco de dados devem ser lidas de arquivos/configurações existentes quando disponíveis, sem suposições manuais.
- A branch `dev` deve ser tratada como branch principal de desenvolvimento quando definida pelo fluxo do usuário.
- A interface deve preservar a identidade visual existente, evitando estilos inline novos e mantendo consistência com os arquivos CSS do projeto.
- O sistema deve ser portável entre ambientes Windows e Linux sempre que possível.
- A integração com IA depende da configuração correta de provedor, modelo e API Key.
- O Auto Layout deve usar o modelo de dados do Design Canvas como fonte oficial; os nós Konva refletem o resultado calculado.
- O Auto Layout deve ser baseado em comportamento Flexbox e não deve incluir Grid Layout.
- A primeira entrega do Auto Layout deve preservar o modelo flat com `parentId`, adicionando propriedades `layout` em frames e `layoutItem` em filhos quando necessário.

## 6. Riscos Iniciais

- Execução indevida de comandos no terminal se não houver fluxo rígido de aprovação.
- Sobrescrita acidental de arquivos caso alterações não sejam planejadas e verificadas.
- Conflitos Git entre branches locais e remotas durante merges, pulls ou pushes.
- Vazamento ou exposição acidental de tokens e credenciais em logs, mensagens ou commits.
- Inconsistência visual caso novas telas não sigam o design system existente.
- Dependência de provedores externos de IA para funcionalidades de geração de especificações, código e testes.
- Falhas de compatibilidade em projetos com stacks muito diferentes.
- Dificuldade de rastrear decisões se atividades não forem registradas corretamente.
- Risco de comandos ou validações não estarem disponíveis no ambiente local, como ausência de Node.js, Python ou ferramentas específicas.
- Complexidade do Auto Layout aninhado no canvas Konva, especialmente durante drag, resize e sizing hug.
- Risco de regressão em seleção, camada, inspector e persistência local do Design Canvas.
- Risco de divergência entre comportamento esperado do discovery e limitações da primeira implementação incremental.

## 7. Critérios de Sucesso

- [ ] O usuário consegue cadastrar, selecionar e alternar projetos/workspaces com clareza.
- [ ] O usuário consegue navegar, ler e editar arquivos do projeto com rastreabilidade.
- [ ] O GitIDE mostra status Git, branches, arquivos alterados e histórico de forma compreensível.
- [ ] Operações Git críticas exigem aprovação e não são executadas automaticamente sem consentimento.
- [ ] O terminal integrado executa comandos de forma controlada e auditável.
- [ ] O módulo de banco de dados permite configurar conexão, listar tabelas e executar queries com feedback visual.
- [ ] O agente de IA consegue usar ferramentas locais de forma segura, seguindo planejamento e aprovação.
- [ ] O módulo de documentação gera documentos físicos no workspace.
- [ ] O módulo SDD permite criar, editar, visualizar e acompanhar especificações versionáveis.
- [ ] Critérios de aceitação e testes podem ser documentados a partir das especificações.
- [ ] A interface mantém padrão visual consistente, dark-themed e premium.
- [ ] O projeto mantém compatibilidade com o fluxo Git definido pelo usuário, especialmente branches `dev` e `homolog`.
- [ ] As alterações podem ser validadas por status Git, testes, builds ou verificações manuais documentadas.
- [ ] Na aba Design do Design Canvas, um frame pode receber Auto Layout Flexível.
- [ ] Frames com Auto Layout organizam filhos por direção, gap, padding, alinhamento e distribuição.
- [ ] O Auto Layout preserva configurações após salvar/recarregar o documento local.
- [ ] O usuário consegue remover Auto Layout sem perder a aparência visual atual.
- [ ] A implementação não introduz Grid Layout ou contratos backend novos.

## 8. Próximo Passo

A partir deste TAP, o projeto deve evoluir suas especificações funcionais no fluxo Harness:

1. **Specify:** detalhar o REQ de Auto Layout Flexível na aba Design.
2. **RFs:** decompor a feature em requisitos funcionais de modelo, motor de layout, interface, persistência e histórico.
3. **Design:** descrever arquitetura, componentes de UI, modelo de dados local, motor de layout e integração com Konva.
4. **DRI:** mapear a interface da seção Auto Layout na aba Design.
5. **Tasks:** quebrar cada RF em tarefas técnicas pequenas, rastreáveis e aprováveis.
6. **Execute:** implementar as tarefas com aprovação explícita, validação técnica e relatório final.

## 9. Rastreabilidade

- Discovery de origem: `.discovery/saida/Feat_ Auto Layout Flexível na Aba Design.md`.
- REQ principal: `REQ-0001-auto-layout-flexivel-aba-design`.
- Tela impactada: `/design-canvas`.
- Arquivos técnicos previstos: `gitide_server/static/konva-designer.html`, `gitide_server/static/konva-designer.js`, `gitide_server/static/rebrand.css`.
