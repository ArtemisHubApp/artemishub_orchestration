# artemishub_orchestration

Repo guarda-chuva do **Artemis** (Grupo 11, Residência de IA). Reúne os 5 repositórios como submódulos e guarda, num lugar só, as regras para agentes de IA (`AGENTS.md`), as skills de SDD e os scripts do dia a dia. O código do produto mora nos submódulos; aqui não se commita código de aplicação.

| Pasta | O que é |
|---|---|
| `artemishub_docs` | Documentação, ADRs e kanban |
| `artemishub_frontend` | Interface web (em construção) |
| `artemishub_backend` | API: contas, conversas e sessão |
| `artemishub_agents` | Multiagentes LLM e modelos de ML |
| `artemishub_rag` | Base de conhecimento com citações |

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
| `python scripts/worktree.py new <repo> <tipo>/<nº>-<slug>` | `make worktree REPO=<repo> BRANCH=<tipo>/<nº>-<slug>` | Cria uma worktree a partir da branch base (`staging` aqui; `main` nos repos filhos, que ainda não têm `staging`) |
| `python scripts/worktree.py list` | - | Lista as worktrees |
| `python scripts/worktree.py prune` | `make prune` | Ensaio: mostra as worktrees de branches já mergeadas que seriam removidas |
| `python scripts/worktree.py prune --yes` | `make prune-yes` | Remove essas worktrees (nunca uma sem commit próprio ou com mudanças) |
| `python scripts/branches.py` | `make branches` | Lista branches mergeadas nos repos (`--delete` apaga, com confirmação) |
| `python scripts/sync_skills.py` | - | Copia `artemis-sdd` de `.agents/skills/` (fonte) para `.claude/skills/` (cópia gerada) |

## Como trabalhar

1. Toda tarefa tem uma issue no kanban.
2. Crie a worktree: `python scripts/worktree.py new rag feat/20-ocr-diretrizes`.
3. Trabalhe lá, com o agente seguindo o `AGENTS.md` (veja abaixo como abrir o agente). No primeiro push, publique a branch com `git push -u origin <tipo>/<nº>-<slug>` e abra o PR para a branch base (`staging` neste repo, `main` nos repos filhos) com `Closes #<nº>`.
4. Depois do merge, `python scripts/worktree.py prune --yes` (sem `--yes` é um ensaio que só lista).

## Como abrir o agente numa tarefa

A worktree fica fora do orquestrador, em `../artemishub-worktrees/<repo>/<branch>/`. Abra o agente na raiz do orquestrador (assim ele lê o `AGENTS.md` e as skills) e dê acesso à pasta da worktree:

- Claude Code: `claude --add-dir <caminho>` ou `/add-dir <caminho>` dentro da sessão.
- Gemini CLI: `gemini --include-directories <caminho>`.
- Codex CLI: `codex --add-dir <caminho>`.

As opções mudam entre versões: confira a opção na documentação da sua versão.

## Docker (opcional)

Sem Python, uv nem torch na máquina: só o Docker. `docker compose run --rm rag` e `docker compose run --rm agents` usam a pasta do submódulo como volume. `backend` e `frontend` ficam no profile `app` até terem scaffold.

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
