# Design: `artemishub_orchestration`

**Data:** 2026-11-17 · **Autora:** Amanda (com Claude) · **Status:** rascunho para aprovação

## 1. Intenção e porquê

O Grupo 11 (Camila, Amanda, Ana Julia, Eduarda) desenvolve o Artemis em 5 repositórios na org `ArtemisHubApp` e trabalha com vibecoding, ou seja, boa parte do código é escrita por agentes de IA. Hoje:

- nenhum repo tem `CLAUDE.md` ou `AGENTS.md`, então cada sessão de IA começa sem saber o que é o Artemis, como os repos se ligam ou como a equipe trabalha;
- as regras de SDD (spec-driven development) existem só dentro do `artemishub_rag`, em três cópias (`.agents/skills`, `.claude/skills` com links para ela e `agent/skills` como cópia real);
- a skill `orchestrator` de SDD encaminha para etapas (`grill`, `spec`, `test-evals`, `build`, `review-commit`) que não existem no repo.

**Objetivo:** um repo guarda-chuva, nos moldes do `kyte-ai-orquestration`, que seja **a única fonte das regras de SDD e do contexto do projeto para agentes de IA**, e que deixe qualquer integrante abrir o projeto inteiro com um clone só.

## 2. Metas, não-metas e anti-metas

**Metas**
- Clonar um repo, rodar um comando e ter os 5 repos lado a lado, com as regras carregadas pelo agente.
- Regras de SDD escritas uma vez, num lugar só, e válidas para todos os repos.
- Contexto do produto e dos repos (o que cada um faz, stack e como rodar) disponível para o agente sem ninguém precisar colar texto.
- Ao tocar um arquivo de um submódulo, o agente é lembrado de ler o contexto daquele submódulo.

**Não-metas (por enquanto)**
- `docker-compose`, Supabase ou banco local. Hoje só o RAG roda. O compose entra na semana 6, quando backend e frontend tiverem stack (seção 9).
- Pipeline de RAG do ecossistema (o `/scout` do Kyte), agentes consultivos e templates de issue por tipo.
- Mover código entre repos. O orquestrador não tem código de aplicação.

**Anti-metas (seria fracasso mesmo funcionando)**
- Criar mais uma cópia das skills que diverge das outras.
- Exigir que a equipe aprenda git avançado para trabalhar no dia a dia.
- PRs de feature abertos no orquestrador em vez de no repo do submódulo.
- Caminhos absolutos da máquina de alguém no código (lição do `/sync-main` do Kyte).

## 3. Restrições

- 7 semanas de roadmap, já na metade. Tudo precisa ser simples de entender e manter.
- Repos públicos. Não pode haver segredo em nenhum arquivo versionado.
- **Cada integrante usa um agente diferente: Codex, Gemini, Claude e GPT** (confirmado pela Amanda). Por isso as regras têm que ser texto puro no repo, lido por qualquer agente. Recursos exclusivos de um agente, como hooks e plugins do Claude Code, são só um extra: nada essencial pode depender deles.
- O fluxo do kanban já está definido em `artemishub_docs/docs/guias/kanban.md` (issue → PR com `Closes #` → Done) e deve ser reaproveitado, não reinventado.

## 4. Abordagens consideradas

| | Abordagem | Troca | Decisão |
|---|---|---|---|
| A | **Repo novo `artemishub_orchestration`** com submódulos e camada de IA na raiz | Um clone traz tudo e as regras ficam num lugar só; em troca, a equipe precisa do básico de submódulo | **Escolhida pela Amanda** |
| B | Transformar o `artemishub_docs` no orquestrador | Reaproveita o repo central, mas mistura o site MkDocs com submódulos e deixa o CI de docs mais frágil | Descartada |
| C | Repo de skills como plugin, sem submódulos | As regras chegam a quem abre qualquer repo, mas some a visão "tudo junto" | Descartada como estrutura principal |

## 5. O que foi decidido (pela Amanda)

- Abordagem A.
- Nome: `artemishub_orchestration`, na org `ArtemisHubApp`.
- Foco: facilitar o vibecoding e centralizar as regras de SDD.
- Precisa funcionar com Codex, Gemini, Claude e GPT.
- Superpowers é imprescindível, e no Claude entra como plugin.
- A equipe usa Windows: sem links simbólicos e com scripts multiplataforma.
- PR para limpar as cópias de skills do `artemishub_rag` depois que o orquestrador estiver no ar.
- Esteira de SDD: Superpowers mais a skill `artemis-sdd`. A `orchestrator` do RAG, que aponta para etapas inexistentes, não vem para o orquestrador.

## 6. Design

### 6.1 Estrutura

```
artemishub_orchestration/
├── .gitmodules                 # 5 submódulos, todos por HTTPS, branch = main
├── artemishub_docs/            # submódulo
├── artemishub_frontend/        # submódulo
├── artemishub_backend/         # submódulo
├── artemishub_agents/          # submódulo
├── artemishub_rag/             # submódulo
├── AGENTS.md                   # FONTE ÚNICA: produto, mapa de repos, regras de SDD, fluxo de trabalho (Codex lê nativamente)
├── CLAUDE.md                   # 1 linha: @AGENTS.md (Claude Code importa)
├── GEMINI.md                   # 1 linha: @AGENTS.md (Gemini CLI importa; alternativa: contextFileName em .gemini/settings.json)
├── README.md                   # como começar (humanos) + tabela de repos
├── Makefile                    # atalho opcional (macOS/Linux): make setup → python scripts/setup.py
├── scripts/                    # em Python, não bash, para rodar igual no Windows
│   ├── setup.py                # init dos submódulos na main + checagens básicas
│   ├── sync.py                 # atualiza o orquestrador e cada submódulo na main
│   ├── status.py               # branch e pendências de cada submódulo
│   └── sync_skills.py          # copia .claude/skills/artemis-sdd → .agents/skills/artemis-sdd
├── .claude/
│   ├── settings.json           # hooks + bloqueio de leitura de .venv, node_modules, data/, chroma
│   ├── hooks/
│   │   ├── submodule_context.py      # avisa: "você está em artemishub_X, leia artemishub_X/AGENTS.md"
│   │   └── test_submodule_context.py
│   ├── commands/
│   │   ├── start.md            # /start: setup explicado em português simples
│   │   └── sync.md             # /sync: atualiza tudo e mostra o que mudou
│   └── skills/artemis-sdd      # só a skill do projeto; Superpowers vem pelo plugin (ver 6.3)
├── .agents/skills/             # Superpowers + artemis-sdd para Codex/Gemini/GPT (cópia única)
├── skills-lock.json            # de onde veio cada skill do Superpowers (versão/hash)
├── .github/workflows/
│   ├── gitleaks.yml            # vazamento de segredo
│   ├── validate-skills.yml     # frontmatter das skills válido
│   └── skills-in-sync.yml      # falha se as duas cópias de artemis-sdd divergirem
├── .gitattributes              # * text=auto eol=lf (evita CRLF do Windows em .md/.py)
└── .gitignore                  # .env* (menos .env.example), worktrees, .DS_Store
```

### 6.2 `AGENTS.md`: o coração

Fonte única, em português, com no máximo cerca de 250 linhas. Seções:

1. **O que é o Artemis** (3 a 5 linhas, link para o PDR em `artemishub_docs/docs/01-definicoes`).
2. **Mapa de repos:** tabela com pasta, responsabilidade, stack, como rodar e status. Por exemplo, `rag`: Python 3.11/3.12, ChromaDB, `python -m src.demo`; `backend`/`frontend`: stack a definir.
3. **Regra de ouro:** "Quero mexer em X → leia `X/AGENTS.md` (ou o README de X, se ainda não existir) antes." PRs vão para o repo do submódulo, nunca para o orquestrador.
4. **Regras de SDD (inegociáveis)**, conteúdo detalhado em 6.3:
   - Nada de código sem issue no kanban.
   - Toda mudança passa pelo fluxo de SDD na profundidade do tamanho dela.
   - Spec e plano ficam versionados no repo do submódulo, em `docs/superpowers/specs/` e `docs/superpowers/plans/`.
   - Teste antes do código em mudança de comportamento.
   - PR com `Closes #<n>`, revisado por outra integrante.
   - Documentação atualizada no mesmo PR.
5. **Fluxo do kanban:** resumo e link para `artemishub_docs/docs/guias/kanban.md` (sem duplicar).
6. **Segurança:** nunca commitar `.env`; repos públicos; nenhum dado pessoal real em fixtures (LGPD).
7. **Lições de submódulo:**
   - O checkout local pode estar atrasado. Para saber o estado real, use `git fetch` + `git show origin/main:<arquivo>`.
   - Worktrees ficam fora do repo, em `../artemishub-worktrees/`.
   - Sem caminhos absolutos.

`CLAUDE.md` e `GEMINI.md` contêm só `@AGENTS.md`, para o conteúdo não divergir entre agentes. Quem usa GPT pelo ChatGPT, sem agente com acesso ao repo, cola ou anexa o `AGENTS.md` (o README explica). O `AGENTS.md` também lista as skills disponíveis e diz: "antes de uma tarefa, abra `.agents/skills/<skill>/SKILL.md` e siga". Assim, agentes sem suporte nativo a skills também chegam nelas.

### 6.3 Regras de SDD

Decidido pela Amanda: Superpowers como esteira, mais uma skill do projeto.

- **Superpowers como esteira de SDD:** brainstorming → spec → writing-plans → test-driven-development → subagent-driven-development ou executing-plans → requesting-code-review → finishing-a-development-branch. Ele já é usado pela equipe e está completo.
- **Superpowers é obrigatório** (decisão da Amanda) e chega a cada agente pelo melhor caminho:
  - **Claude:** pelo **plugin oficial**, habilitado no `.claude/settings.json` do repo (`extraKnownMarketplaces` + `enabledPlugins`). Quem abre o repo no Claude Code recebe o pedido de instalação. O plugin já traz o hook de início de sessão que carrega o `using-superpowers`, e a cópia em pasta não faz isso.
  - **Codex, Gemini e GPT:** por uma **cópia única em `.agents/skills/`**, com `skills-lock.json` registrando a origem, no formato que o RAG já usa. Atualizar essa cópia é um PR no orquestrador.
  - **Para o Claude não ver as skills em dobro**, `.claude/skills/` **não** aponta para `.agents/skills/` inteiro: contém só a `artemis-sdd`. O Claude pega o Superpowers pelo plugin e a `artemis-sdd` pela pasta.
  - **Sem links simbólicos.** A equipe usa Windows, onde links do git costumam virar arquivos de texto. A `artemis-sdd` é editada em `.claude/skills/artemis-sdd/`. O `scripts/sync_skills.py` copia a pasta para `.agents/skills/artemis-sdd/`, e as duas cópias são commitadas. O CI `skills-in-sync` falha se elas divergirem, então a duplicação é controlada e não vira drift.
- **Escrever uma skill do projeto, `artemis-sdd`, em `.claude/skills/`**, com o que é só do Artemis:
  - classificação de tamanho (S0 edição direta, S1 plano curto, S2/S3 spec completa);
  - onde salvar spec e plano;
  - ligação com o kanban (issue, `Closes #`, semana);
  - checklist de PR.
  - Reaproveita a ideia de complexidade e risco da `orchestrator` atual, sem apontar para etapas que não existem.

### 6.4 Hook `submodule_context.py`

É um extra só do Claude Code. Para os outros agentes, a regra de ouro do `AGENTS.md` (6.2, item 3) faz o mesmo papel. Roda em `PreToolUse` para `Read|Edit|Write`. Se o caminho tocado estiver dentro de `artemishub_*/`, injeta uma vez por sessão e por submódulo o aviso: "Você está em `artemishub_X`. Leia `artemishub_X/AGENTS.md` (ou o README.md) antes de alterar." Os caminhos são resolvidos a partir de `CLAUDE_PROJECT_DIR`, nunca fixos. Tem testes com pytest.

### 6.5 Comandos e scripts

Todos os scripts são Python 3, só com a biblioteca padrão, e rodam igual em Windows, macOS e Linux (`python scripts/setup.py`). O `Makefile` é só atalho para quem tem `make`. Os hooks no `settings.json` chamam o interpretador de um jeito que funcione no Windows, onde muitas vezes não existe `python3`; quem construir testa isso.

- `scripts/setup.py` (ou `make setup`): confere `git` e Python, roda `git submodule update --init --recursive` e coloca cada submódulo na `main` (`git submodule foreach 'git checkout main && git pull'`). Os submódulos não ficam em *detached HEAD*: quem faz vibecoding não deve tropeçar nisso.
- `scripts/sync.py` (ou `make sync`, ou `/sync`): `git pull` no orquestrador e `pull` na `main` de cada submódulo, avisando quando houver mudança local não commitada (sem descartar nada).
- `scripts/status.py` (ou `make status`): branch e mudanças pendentes de cada submódulo.
- `/start`: roda o setup e explica cada passo em português simples.

**Ponteiros dos submódulos:** a equipe trabalha sempre na `main` de cada repo. O SHA gravado no orquestrador é informativo, atualizado por um commit `chore: bump submodules` quando alguém quiser, sem cobrança. Essa é **minha decisão**, igual ao `--remote` do Kyte.

### 6.6 Mudanças nos repos filhos (PRs separados, depois do orquestrador)

- Cada repo ganha um `AGENTS.md` curto: o que o repo é, como rodar e testar, e a frase "Regras gerais e de SDD: veja o `artemishub_orchestration`."
- `artemishub_rag`: um PR para remover `.agents/skills`, `.claude/skills`, `agent/skills` e `skills-lock.json`, aberto depois que o orquestrador estiver no ar (aprovado pela Amanda; combinar o merge com quem cuida do RAG). O `docs/superpowers/plans/` do RAG fica onde está.

## 7. Deixado para quem constrói

- O texto exato do `AGENTS.md` e da skill `artemis-sdd`, seguindo 6.2 e 6.3.
- O formato do bloqueio de leitura no `settings.json`.
- Os detalhes de CI, que devem ser leves e não bloquear o trabalho.

## 8. Critérios de sucesso

- `git clone --recurse-submodules … && python scripts/setup.py` funciona numa máquina limpa, **inclusive no Windows**, e deixa os 5 repos na `main`.
- Numa sessão nova aberta na raiz, no Claude Code, no Codex e no Gemini CLI, a pergunta "o que é o artemishub_agents e como eu rodo o RAG?" é respondida certo sem colar contexto.
- Editar um arquivo em `artemishub_rag/` dispara o aviso do hook uma vez.
- Pedir "implementa X" leva o agente a criar ou pedir a issue e seguir a esteira de SDD na profundidade certa.
- Existe uma única cópia das regras de SDD na org.

## 9. Futuro (fora do escopo agora)

- Semana 6: `docker-compose.yml` com um serviço por submódulo (pasta montada como volume), `make start/stop/logs-%` e um `.env.example` na raiz.
- ADRs do orquestrador no `artemishub_docs`.
