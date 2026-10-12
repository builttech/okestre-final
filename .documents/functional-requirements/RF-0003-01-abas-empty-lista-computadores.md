# RF-0003-01 — Abas, empty state e múltiplos computadores

## Identificação
- REQ pai: `REQ-0003` | Projeto: `act-ide-teste`
- Interface: `RI-0003` | Status: aprovado/em execução

## Objetivo e história do usuário
Como usuário, quero encontrar separadamente meus computadores e as pastas ligadas a eles, para localizar e adicionar dispositivos sem confusão.

## Descrição e fluxo funcional
1. Abrir `local-devices`, mantendo a navegação global do produto.
2. Exibir exatamente as abas **Computador** e **Dispositivos e pastas**.
3. Carregar computadores do usuário autenticado; enquanto carrega, mostrar placeholder, sem estado vazio falso.
4. Se nenhum estiver cadastrado, apresentar ilustração/ícone, título curto, explicação e CTA **Adicionar dispositivo**.
5. Com um ou mais, apresentar cards com nome, status da credencial, expiração e ação de incluir outro.
6. Selecionar um computador para contextualizar a aba de pastas; após troca de aba, preservar seleção nesta sessão.
7. Erro no carregamento: mostrar mensagem e ação de tentar novamente sem fingir lista vazia.

## Regras, permissões e validações
- Lista filtrada por usuário/escopo autorizado; sem número máximo rígido de computadores.
- Seleção por `computer.id`; ausência/remoção remota da seleção deve ser tratada.
- Aba Pastas não acessa registros enquanto não houver computador selecionado.
- Todos os controles devem funcionar com teclado, foco visível e `aria-selected`/roles correspondentes.

## Dados e integrações
- `GET /api/local/devices` (contrato existente, incluindo computadores pareados e pendentes).
- ID, nome, estado de credencial, datas não sensíveis.
- Tela/rota exata depende do inventário da base real.

## Critérios de aceite
- Zero computadores: estado vazio e CTA funcional.
- Dois computadores cadastrados: ambos visíveis; ao selecionar cada um, o contexto visual acompanha a seleção.
- Troca de abas não descarta estado legítimo; erro tem retry e loading distinto de empty.
- Textos do empty state em pt-BR e sem chaves expostas.

## Fora do escopo
Novo tipo de dispositivo ou exclusão de computadores.

## Dependências, riscos e rastreabilidade
- Depende da API e persistência de RF-0003-02.
- Risco: a tela `local-devices` não foi localizada no projeto 46.
- REQ-0003; Design; RI-0003; tasks TASK-RF-0003-01-*.
- Histórico: 2026-10-11 — criado.
