# artemishub_orchestration

Repo guarda-chuva do **Artemis** (Grupo 11, Residência de IA). Reúne os 5 repositórios como submódulos e guarda, num lugar só, as regras para agentes de IA (`AGENTS.md`), as skills de SDD e os scripts do dia a dia. O código do produto mora nos submódulos; aqui não se commita código de aplicação.

| Pasta | O que é |
|---|---|
| `artemishub_docs` | Documentação, ADRs e kanban |
| `artemishub_frontend` | Interface web (em construção) |
| `artemishub_backend` | API: contas, conversas e sessão |
| `artemishub_agents` | Multiagentes LLM e modelos de ML |
| `artemishub_rag` | Base de conhecimento com citações |

**Arquitetura:** a decisão de implantação e dos pipelines de dados está no [ADR-012](https://artemishubapp.github.io/artemishub_docs/adr/012-implantacao-e-pipelines-de-dados/), e os diagramas (contexto, containers, componentes, implantação e a sequência de uma pergunta) estão nas [Visões C4](https://artemishubapp.github.io/artemishub_docs/arquitetura/visoes-c4/). Toda a documentação, com o PDR e os ADRs, fica no [site do projeto](https://artemishubapp.github.io/artemishub_docs/).

## Primeiro uso

Precisa de Git e Python 3.11 ou mais novo (só biblioteca padrão; funciona em Windows, macOS e Linux).

```bash
git clone --recurse-submodules https://github.com/ArtemisHubApp/artemishub_orchestration.git
cd artemishub_orchestration
python scripts/setup.py
```

Abra a pasta no seu agente (Claude Code, Codex, Gemini CLI). Ele lê o `AGENTS.md` sozinho; no Claude Code, aceite o pedido para instalar o plugin Superpowers.

## Comandos

| Comando | Atalho `make` | Para que serve |
|---|---|---|
| `python scripts/setup.py` | `make setup` | Baixa os submódulos e deixa cada um na branch base |
| `python scripts/sync.py` | `make sync` | Atualiza os submódulos sem descartar mudanças locais |
| `python scripts/status.py` | `make status` | Mostra branch, mudanças, adiantamento e worktrees de cada repo |
| `python scripts/worktree.py new <repo> <tipo>/<nº>-<slug>` | `make worktree REPO=<repo> BRANCH=<tipo>/<nº>-<slug>` | Cria uma worktree a partir de `origin/staging` |
| `python scripts/worktree.py list` | - | Lista as worktrees |
| `python scripts/worktree.py prune` | `make prune` | Ensaio: mostra as worktrees de branches já mergeadas que seriam removidas |
| `python scripts/worktree.py prune --yes` | `make prune-yes` | Remove essas worktrees (nunca uma sem commit próprio ou com mudanças) |
| `python scripts/branches.py` | `make branches` | Lista branches mergeadas nos repos (`--delete` apaga, com confirmação) |
| `python scripts/sync_skills.py` | - | Copia `artemis-sdd` de `.agents/skills/` (fonte) para `.claude/skills/` (cópia gerada) |

## Como trabalhar

1. Toda tarefa tem uma issue no [quadro](https://github.com/orgs/ArtemisHubApp/projects/1/views/2). Use os formulários de issue (o padrão está no `AGENTS.md`, seção Kanban). A issue entra no quadro sozinha pelo workflow `Quadro` (ver abaixo).
2. Crie a worktree: `python scripts/worktree.py new rag feat/20-ocr-diretrizes`.
3. Trabalhe lá, com o agente seguindo o `AGENTS.md` (veja abaixo como abrir o agente). No primeiro push, publique a branch com `git push -u origin <tipo>/<nº>-<slug>` e abra o PR para `staging` com `Closes #<nº>`.
4. Depois do merge, `python scripts/worktree.py prune --yes` (sem `--yes` é um ensaio que só lista).

## Branches e release

Todos os repos têm `staging`, que é a branch padrão; a `main` é produção (o site do docs publica a partir dela). Os PRs vão para `staging` com squash. Quando a `staging` estiver estável, abra o PR `release: <data>` de `staging` para `main` e mescle com **merge commit**. O workflow `Release` cria sozinho a tag `vAAAA.MM.DD` e a release no GitHub, apontando para a `main`.

## Workflows deste repo

| Workflow | Quando roda | O que faz |
|---|---|---|
| `CI` | PRs e pushes | Testes do orquestrador e validação das skills |
| `Gitleaks` | PRs e pushes | Procura segredos commitados |
| `Python CI` | chamado pelos repos filhos | CI reutilizável: lint, testes, título do PR, sem cópia de skills |
| `Release` | merge de um PR `release:` na `main`, e à mão | Cria a tag `vAAAA.MM.DD` (sufixo `b`, `c`… no mesmo dia) e a release com as notas dos PRs |
| `Quadro` | a cada 30 minutos e à mão | Inclui no quadro as issues abertas da org; à mão, com `incluir_fechadas`, inclui também as fechadas em Done. Usa o secret da org `ADD_TO_PROJECT_PAT` |

## Como abrir o agente numa tarefa

A worktree fica fora do orquestrador, em `../artemishub-worktrees/<repo>/<branch>/`. Abra o agente na raiz do orquestrador (assim ele lê o `AGENTS.md` e as skills) e dê acesso à pasta da worktree:

- Claude Code: `claude --add-dir <caminho>` ou `/add-dir <caminho>` dentro da sessão.
- Gemini CLI: `gemini --include-directories <caminho>`.
- Codex CLI: `codex --add-dir <caminho>`.

As opções mudam entre versões: confira a opção na documentação da sua versão.

## Docker (opcional)

Sem Python, uv nem torch na máquina: só o Docker. `docker compose run --rm rag` e `docker compose run --rm agents` usam a pasta do submódulo como volume. `backend` e `frontend` ficam no profile `app` até o compose do sistema completo ([backend#11](https://github.com/ArtemisHubApp/artemishub_backend/issues/11)); por enquanto, rode-os como explica o README de cada um.

| Comando (funciona em qualquer sistema, inclusive Windows) | Atalho `make` | O que faz |
|---|---|---|
| `docker compose run --rm rag uv run python -m artemis_rag.query "pergunta"` | `make rag-query Q="pergunta"` | Consulta o RAG |
| `docker compose run --rm rag uv run python -m artemis_rag.demo` | `make rag-demo` | Roda a demo do RAG |
| `docker compose run --rm rag uv run pytest -q` (ou `agents`) | `make test-rag` / `make test-agents` | Roda os testes do serviço |
| `docker compose run --rm rag sh` (ou `agents`) | `make shell-rag` / `make shell-agents` | Abre um shell no serviço |
| - | `make help` | Lista todos os atalhos |

As regras completas estão no [AGENTS.md](AGENTS.md).

## Usa ChatGPT no navegador? Anexe o AGENTS.md

O ChatGPT no navegador não enxerga o repo. No começo da conversa, anexe (ou cole) o [AGENTS.md](AGENTS.md) e, se a tarefa pedir, o `SKILL.md` da skill relevante em `.agents/skills/`. Peça: "siga o AGENTS.md anexado".

## Mexendo nas regras ou nas skills

Skills e regras só existem aqui; repos filhos não guardam cópias. Mudou o `AGENTS.md` ou uma skill? Abra um PR neste repo, rode `python scripts/sync_skills.py` e os testes (`python -m pytest`).
