# AGENTS.md: regras para agentes de IA no Artemis

Fonte única de regras para Codex, Gemini, Claude e GPT. `CLAUDE.md` e `GEMINI.md` só importam este arquivo. Vale para pessoas e agentes. Em português.

## O que é o Artemis

Plataforma que usa IA para apoiar mulheres em STEM com análise de currículo, inteligência salarial, oportunidades, desenvolvimento de carreira, simulação de negociação e orientação sobre direitos, sempre citando as fontes. O Grupo 11 (Camila, Amanda, Ana Julia, Eduarda) constrói tudo em 5 repositórios da org `ArtemisHubApp`. Este repo (`artemishub_orchestration`) só guarda regras, skills e scripts; o código mora nos submódulos. Definição do produto: [PDR](artemishub_docs/docs/01-definicoes/README.md).

## Repositórios

| Pasta | Responsabilidade | Stack | Como rodar |
|---|---|---|---|
| `artemishub_docs` | Documentação, ADRs e kanban | MkDocs | `pip install -r requirements.txt` e `mkdocs serve` |
| `artemishub_frontend` | Interface web | React 19, Vite, TypeScript, Tailwind 4 (em construção, [frontend#2](https://github.com/ArtemisHubApp/artemishub_frontend/issues/2)) | ver o README do repo |
| `artemishub_backend` | API, contas, conversas e sessão | Python 3.12, FastAPI, Postgres 16, uv | `uv run pytest -q` (Docker ligado); para rodar, ver o README |
| `artemishub_agents` | Sistema multiagentes LLM e modelos de ML | Python 3.12+, uv, DVC | `uv run pytest` |
| `artemishub_rag` | Base de conhecimento com citações | Python 3.11 a 3.13, ChromaDB, uv | `python -m artemis_rag.demo` e `python -m artemis_rag.query "<pergunta>"` (com `uv run` na frente) |

Fluxo dos dados: frontend → backend → agents → rag.

## Regra de ouro

Quer mexer em `X`? Leia `X/AGENTS.md` (ou o `X/README.md`, se ainda não existir) antes. O PR vai para o repo do submódulo, nunca para o orquestrador (exceto regras, skills e scripts daqui). Em dúvida sobre o estado de um repo, rode `python scripts/status.py`.

Mudança no próprio orquestrador (regras, skills, scripts): issue e branch `<tipo>/<nº>-<slug>` a partir de `staging` neste repo, e PR para `staging`.

## Regras de SDD

Inegociáveis. Antes de qualquer tarefa, abra `.agents/skills/artemis-sdd/SKILL.md` e siga. Claude recebe o Superpowers pelo plugin; os demais agentes abrem `.agents/skills/<skill>/SKILL.md` e seguem.

1. **Toda tarefa tem uma issue associada** (rastreabilidade). Nada de código, doc ou configuração sem issue no kanban. Se não existir, crie (`gh issue create`) ou peça o número antes de começar.
2. Classifique a tarefa (S0 a S3) e diga o porquê em uma linha. Siga o fluxo na profundidade do tamanho: `brainstorming` → spec → `writing-plans` → `test-driven-development` → `subagent-driven-development` ou `executing-plans` → `requesting-code-review` → `finishing-a-development-branch`.
3. Spec e plano ficam no repo do submódulo afetado, em `docs/superpowers/specs/` e `docs/superpowers/plans/`, no mesmo PR. Nunca aqui.
4. Teste antes do código quando o comportamento muda.
5. PR com `Closes #<nº>`, revisado por outra integrante.
6. **Docs sempre atualizadas** quando algo relevante muda (comportamento, comando, configuração, arquitetura, dependência): README e `AGENTS.md` do repo, `artemishub_docs` e ADR quando couber, no mesmo PR. Isso inclui o **site no GitHub Pages**: se a mudança altera algo que o site descreve (arquitetura, RAG, como trabalhamos, guias), abra também um PR no `artemishub_docs` atualizando a página, e cite os dois PRs um no outro. O site publica a partir da `main` do `docs`. PR que muda algo relevante sem tocar em doc diz por quê na descrição.
7. **Skills só no orquestrador.** Repo filho não guarda cópia de skills. Skill nova ou alterada é PR aqui. A fonte editável da `artemis-sdd` é `.agents/skills/artemis-sdd/`; depois de editar, rode `python scripts/sync_skills.py`.

Skills disponíveis (`.agents/skills/`): `artemis-sdd`, `brainstorming`, `writing-plans`, `test-driven-development`, `subagent-driven-development`, `executing-plans`, `dispatching-parallel-agents`, `requesting-code-review`, `receiving-code-review`, `systematic-debugging`, `verification-before-completion`, `using-git-worktrees`, `finishing-a-development-branch`, `writing-skills`, `using-superpowers`, `diagnosing-superpowers`.

## Branches e worktrees

Todo trabalho nasce numa worktree com branch própria, criada a partir de `origin/staging`. O PR vai para `staging`. A `main` é produção e só recebe o PR `release: <data>` de `staging` para `main`.

```
python scripts/worktree.py new <repo> <tipo>/<nº>-<slug>
```

- Exemplo: `python scripts/worktree.py new rag feat/20-ocr-diretrizes`.
- Nome da branch: `feat|fix|chore|docs|refactor|test|ci` + `/<nº da issue>-<slug em minúsculas>`.
- A worktree fica fora de qualquer repo, em `../artemishub-worktrees/<repo>/<branch>/`.
- Nunca commite direto em `staging` nem em `main`.
- Se o repo ainda não tem `staging`, o script avisa e usa `main`.
- A branch nova não segue nenhuma remota. No primeiro push, publique com `git push -u origin <tipo>/<nº>-<slug>`; depois, `git push` e `git pull` simples funcionam.

## Como abrir o agente numa tarefa

Abra o agente na raiz do orquestrador (para ele ler este `AGENTS.md` e as skills) e dê acesso à pasta da worktree, `../artemishub-worktrees/<repo>/<branch>/`:

- Claude Code: `claude --add-dir <caminho>` ou, já dentro da sessão, `/add-dir <caminho>`.
- Gemini CLI: `gemini --include-directories <caminho>`.
- Codex CLI: `codex --add-dir <caminho>`.

Os nomes das opções mudam entre versões: confira a opção na documentação da sua versão. Peça ao agente para editar e rodar comandos só dentro da worktree.

## Higiene do GitHub

1. Uma issue, uma branch, um PR. Renomeie branches de nome automático (`claude/...`, `codex/...`) antes de abrir o PR.
2. Commits e título de PR em Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`, `ci:`; `release:` só no PR `staging → main`), em português depois dos dois-pontos.
3. Merge: squash nos PRs para `staging`; a release `staging` → `main` usa merge commit, nunca squash.
4. PR pequeno, idealmente abaixo de uns 400 linhas alteradas (sem lockfiles e dados). Abra como draft enquanto estiver em andamento.
5. Nunca `push --force` em `staging` ou `main`, nunca commitar `.env`, dados pessoais reais ou arquivos grandes fora do DVC.
6. Depois do merge, apague a branch e a worktree: `python scripts/worktree.py prune --yes` (sem `--yes` é só um ensaio; worktree sem commit próprio nunca é removida). Faxina de branches antigas: `python scripts/branches.py`.
7. Formulários de issue, template de PR e labels padrão vêm do repo da org `ArtemisHubApp/.github`; não crie cópias nos repos. Sincronize as labels com `python3 scripts/labels.py --apply` a partir de um clone dele (sem `--apply` é só um ensaio).

## Código limpo

Regras completas, com os 4 princípios (pense antes, simplicidade, mudança cirúrgica, guiado por objetivo) e a clean architecture hexagonal, em [codigo-limpo.md](.agents/skills/artemis-sdd/references/codigo-limpo.md). Resumo:

- Nomes que dizem a intenção, funções curtas, type hints em funções públicas, erros explícitos, sem código morto.
- Camadas `adapters` → `application` → `domain`; dependências só apontam para dentro.
- Mudança cirúrgica: só migre módulo antigo quando a tarefa já precisa mexer nele.
- A revisão usa esse documento como critério.

## Decisões (ADR)

Toda decisão que muda arquitetura, stack ou processo gera um ADR em `artemishub_docs/docs/adr/` (`NNN-titulo.md` com o próximo número livre, 3 dígitos, no formato do ADR-002: contexto, decisão, alternativas, consequências, status; entrada no `nav` do `mkdocs.yml` e na tabela de `docs/adr/index.md`), no mesmo ciclo da mudança. O agente propõe o rascunho; a equipe aprova no PR. O orquestrador não guarda ADRs.

## Kanban

Toda issue, de qualquer repo, entra no mesmo quadro: <https://github.com/orgs/ArtemisHubApp/projects/1/views/2>. Colunas: Backlog → Ready Todo → In Progress → In Review → Testing → Done.

Antes de criar uma issue, procure duplicata em todos os repos, abertas e fechadas, com mais de uma palavra-chave (a tarefa pode estar em outro repo ou com outro nome):

```
gh search issues --owner ArtemisHubApp "<palavras-chave>"
```

- Se já existe uma aberta, use-a: comente o que faltar em vez de criar outra.
- Se já existe uma fechada, leia-a antes: pode já estar pronta. Se for continuação, crie a nova e cite a antiga.
- Em dúvida, pergunte antes de criar. Achou duplicata já criada? Avise as responsáveis; não feche issue de outra pessoa por conta própria.

Ao criar uma issue, inclua no quadro e confira se entrou (não conte com a inclusão automática):

```
gh project item-add 1 --owner ArtemisHubApp --url <URL da issue>
```

Marque a Semana no card, mova para In Progress ao começar e use `Closes #<nº>` no PR. Detalhes em [kanban.md](artemishub_docs/docs/guias/kanban.md).

## Segurança

- Nunca commite `.env`, chaves ou tokens. Os repos são públicos.
- Nenhum dado pessoal real em fixtures, exemplos ou logs (LGPD).
- Não cole segredo em prompt nem em issue.

## Submódulos: cuidados

- O checkout local do submódulo pode estar atrasado. Para ver o estado real: `git fetch` e `git show origin/staging:<arquivo>` (ou `origin/main` para produção).
- Atualize tudo com `python scripts/sync.py`; nunca descarte mudança local (sem `reset --hard`, `checkout -- .` nem `clean`). O sync pula repo sujo, em outra branch ou com commit só local.
- Depois do sync, o `git status` do orquestrador mostra os submódulos com "new commits". É normal: não commite esses ponteiros sem querer (evite `git add -A` e `git commit -a` aqui; adicione só os arquivos que você mudou).
- Não crie worktree dentro de um repo; use sempre `scripts/worktree.py`.
- Sem caminhos absolutos e sem links simbólicos (a equipe usa Windows).
- Primeiro uso: `git clone --recurse-submodules https://github.com/ArtemisHubApp/artemishub_orchestration.git` e `python scripts/setup.py`.
